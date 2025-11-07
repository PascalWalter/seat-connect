"""Seat Connect API abstraction."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

import async_timeout
from aiohttp import ClientError, ClientResponseError
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL, LOGGER_NAME

_LOGGER = logging.getLogger(LOGGER_NAME)


class SeatApiError(Exception):
    """General Seat API error."""


class SeatApiAuthError(SeatApiError):
    """Raised when authentication fails."""


class SeatApiRateLimitError(SeatApiError):
    """Raised when the Seat backend returns HTTP 429."""


@dataclass(slots=True)
class SeatVehicleData:
    """Normalized vehicle representation."""

    vin: str
    name: str
    model: str
    battery_soc: float | None = None
    battery_range_km: float | None = None
    charging_power_kw: float | None = None
    charging_state: str | None = None
    plug_connected: bool | None = None
    doors_closed: bool | None = None
    windows_closed: bool | None = None
    is_locked: bool | None = None
    climate_active: bool | None = None
    capabilities: set[str] = field(default_factory=set)


class SeatApiClientProtocol(Protocol):
    """Protocol describing the Seat API client."""

    async def async_get_vehicle_data(self) -> dict[str, SeatVehicleData]:
        """Return the latest vehicle data indexed by VIN."""

    async def async_lock_vehicle(self, vin: str) -> None:
        """Lock the vehicle."""

    async def async_unlock_vehicle(self, vin: str) -> None:
        """Unlock the vehicle."""

    async def async_start_climate(self, vin: str) -> None:
        """Start pre-conditioning."""

    async def async_stop_climate(self, vin: str) -> None:
        """Stop pre-conditioning."""


class SeatApiClient(SeatApiClientProtocol):
    """Seat Connect API client with retry/backoff handling."""

    def __init__(
        self,
        oauth_session: OAuth2Session,
        *,
        base_url: str = API_BASE_URL,
        request_timeout: float = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        concurrency: int = 4,
    ) -> None:
        self._oauth_session = oauth_session
        self._base_url = base_url.rstrip("/")
        self._request_timeout = request_timeout
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._semaphore = asyncio.Semaphore(concurrency)

    async def async_get_vehicle_data(self) -> dict[str, SeatVehicleData]:
        """Return normalized vehicle data for the account."""

        payload = await self._request("GET", "/vehicles")
        if isinstance(payload, dict):
            vehicles_raw = payload.get("vehicles", payload)
        elif isinstance(payload, list):
            vehicles_raw = payload
        else:
            raise SeatApiError("Unexpected payload from Seat Connect")
        vehicles: list[dict[str, Any]] = list(vehicles_raw)
        tasks = [self._async_build_vehicle(entry) for entry in vehicles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        data: dict[str, SeatVehicleData] = {}
        for result in results:
            if isinstance(result, Exception):
                raise SeatApiError("Failed to refresh vehicle data") from result
            data[result.vin] = result
        return data

    async def async_lock_vehicle(self, vin: str) -> None:
        await self._execute_command(vin, "lock")

    async def async_unlock_vehicle(self, vin: str) -> None:
        await self._execute_command(vin, "unlock")

    async def async_start_climate(self, vin: str) -> None:
        await self._execute_command(vin, "start_climate")

    async def async_stop_climate(self, vin: str) -> None:
        await self._execute_command(vin, "stop_climate")

    async def _async_build_vehicle(self, vehicle: dict[str, Any]) -> SeatVehicleData:
        vin: str = vehicle["vin"]
        status = await self._request("GET", f"/vehicles/{vin}/status")
        battery = status.get("battery", {})
        charging = status.get("charging", {})
        locks = status.get("locks", {})
        climate = status.get("climate", {})
        doors = status.get("doors", {})

        return SeatVehicleData(
            vin=vin,
            name=vehicle.get("nickname") or vehicle.get("name") or vin,
            model=vehicle.get("model", "Unknown"),
            battery_soc=_coerce_float(battery.get("stateOfCharge")),
            battery_range_km=_coerce_float(battery.get("remainingRangeKm")),
            charging_power_kw=_coerce_float(charging.get("powerKw")),
            charging_state=charging.get("state"),
            plug_connected=bool(charging.get("plugConnected")) if "plugConnected" in charging else None,
            doors_closed=doors.get("allClosed"),
            windows_closed=doors.get("windowsClosed"),
            is_locked=locks.get("locked"),
            climate_active=climate.get("active"),
            capabilities=set(vehicle.get("capabilities", [])),
        )

    async def _execute_command(self, vin: str, command: str) -> None:
        endpoint = f"/vehicles/{vin}/actions/{command}"
        await self._request("POST", endpoint)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        attempt = 0
        while True:
            attempt += 1
            try:
                async with self._semaphore:
                    async with async_timeout.timeout(self._request_timeout):
                        response = await self._oauth_session.async_request(method, url, **kwargs)
                        try:
                            if response.content_type == "application/json":
                                return await response.json()
                            if response.content_length == 0:
                                return None
                            return await response.text()
                        finally:
                            response.release()
            except ClientResponseError as err:
                if err.status == 401:
                    raise SeatApiAuthError("Authentication failed") from err
                if err.status == 429:
                    if attempt > self._max_retries:
                        raise SeatApiRateLimitError("Seat Connect rate limit exceeded") from err
                    await asyncio.sleep(self._backoff_factor * attempt)
                    continue
                if 500 <= err.status < 600 and attempt <= self._max_retries:
                    await asyncio.sleep(self._backoff_factor * attempt)
                    continue
                raise SeatApiError(f"Seat Connect request failed: {err.status}") from err
            except ClientError as err:
                if attempt > self._max_retries:
                    raise SeatApiError("Seat Connect network error") from err
                await asyncio.sleep(self._backoff_factor * attempt)
            except asyncio.TimeoutError as err:
                if attempt > self._max_retries:
                    raise SeatApiError("Seat Connect request timed out") from err
                await asyncio.sleep(self._backoff_factor * attempt)


def _coerce_float(value: Any) -> float | None:
    """Return a float if possible."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

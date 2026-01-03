"""Seat Connect API abstraction."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import base64
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from http import HTTPStatus
from typing import Any, Protocol
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp
import async_timeout
from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE_URL,
    API_HOMEREGION_URL,
    AUTH_AUTHORIZE_URL,
    AUTH_TOKEN_URL,
    CLIENT_ID,
    LOGGER_NAME,
    REDIRECT_URI,
    SCOPES,
    UI_LOCALES,
    USER_AGENT,
    X_APP_NAME,
    X_APP_VERSION,
    CAP_CLIMATISATION,
    CAP_CHARGING,
)

_LOGGER = logging.getLogger(LOGGER_NAME)


class SeatApiError(Exception):
    """General Seat API error."""


class SeatApiAuthError(SeatApiError):
    """Raised when authentication fails."""


class SeatApiRateLimitError(SeatApiError):
    """Raised when the Seat backend returns HTTP 429."""


class SeatApiCommunicationError(SeatApiError):
    """Raised on network communication errors."""


@dataclass(slots=True)
class SeatVehiclePosition:
    """GPS position of the vehicle."""
    latitude: float | None = None
    longitude: float | None = None
    timestamp: datetime | None = None
    parking_time: datetime | None = None


@dataclass(slots=True)
class SeatVehicleOdometer:
    """Odometer data."""
    value: float | None = None
    unit: str = "km"


@dataclass(slots=True)
class SeatVehicleStatus:
    """Detailed vehicle status."""
    # Doors
    door_front_left_open: bool | None = None
    door_front_right_open: bool | None = None
    door_rear_left_open: bool | None = None
    door_rear_right_open: bool | None = None
    trunk_open: bool | None = None
    hood_open: bool | None = None

    # Windows
    window_front_left_open: bool | None = None
    window_front_right_open: bool | None = None
    window_rear_left_open: bool | None = None
    window_rear_right_open: bool | None = None
    sunroof_open: bool | None = None

    # Lights
    lights_left: bool | None = None
    lights_right: bool | None = None


@dataclass(slots=True)
class SeatChargingStatus:
    """Charging status information."""
    state: str | None = None
    mode: str | None = None
    power_kw: float | None = None
    remaining_time_min: int | None = None
    target_soc: int | None = None
    max_current_a: int | None = None
    plug_connected: bool | None = None
    plug_locked: bool | None = None
    external_power: bool | None = None


@dataclass(slots=True)
class SeatClimatisationStatus:
    """Climatisation status."""
    active: bool = False
    target_temp_c: float | None = None
    remaining_time_min: int | None = None
    window_heating_front: bool | None = None
    window_heating_rear: bool | None = None
    steering_wheel_heating: bool | None = None
    seat_heating_front_left: int | None = None
    seat_heating_front_right: int | None = None


@dataclass(slots=True)
class SeatTripStatistics:
    """Trip statistics."""
    average_speed_kmh: float | None = None
    average_consumption_kwh: float | None = None
    average_consumption_l: float | None = None
    total_distance_km: float | None = None
    total_time_min: int | None = None


@dataclass(slots=True)
class SeatVehicleData:
    """Normalized vehicle representation."""

    vin: str
    name: str
    model: str
    model_year: str | None = None
    color: str | None = None
    engine_type: str | None = None  # electric, hybrid, combustion

    # Battery / Electric
    battery_soc: float | None = None
    battery_range_km: float | None = None
    battery_capacity_kwh: float | None = None

    # Fuel (for hybrid/combustion)
    fuel_level: float | None = None
    fuel_range_km: float | None = None
    total_range_km: float | None = None

    # Charging
    charging: SeatChargingStatus = field(default_factory=SeatChargingStatus)

    # Status
    status: SeatVehicleStatus = field(default_factory=SeatVehicleStatus)

    # Climate
    climatisation: SeatClimatisationStatus = field(default_factory=SeatClimatisationStatus)

    # Position
    position: SeatVehiclePosition = field(default_factory=SeatVehiclePosition)

    # Odometer
    odometer: SeatVehicleOdometer = field(default_factory=SeatVehicleOdometer)

    # Trip statistics
    trip_statistics: SeatTripStatistics = field(default_factory=SeatTripStatistics)

    # Lock status
    is_locked: bool | None = None

    # Capabilities
    capabilities: set[str] = field(default_factory=set)

    # Computed properties
    @property
    def doors_closed(self) -> bool | None:
        """Return True if all doors are closed."""
        doors = [
            self.status.door_front_left_open,
            self.status.door_front_right_open,
            self.status.door_rear_left_open,
            self.status.door_rear_right_open,
            self.status.trunk_open,
            self.status.hood_open,
        ]
        if all(d is None for d in doors):
            return None
        return all(d is False for d in doors if d is not None)

    @property
    def windows_closed(self) -> bool | None:
        """Return True if all windows are closed."""
        windows = [
            self.status.window_front_left_open,
            self.status.window_front_right_open,
            self.status.window_rear_left_open,
            self.status.window_rear_right_open,
            self.status.sunroof_open,
        ]
        if all(w is None for w in windows):
            return None
        return all(w is False for w in windows if w is not None)

    @property
    def plug_connected(self) -> bool | None:
        """Return plug connected state."""
        return self.charging.plug_connected

    @property
    def charging_state(self) -> str | None:
        """Return charging state."""
        return self.charging.state

    @property
    def charging_power_kw(self) -> float | None:
        """Return charging power in kW."""
        return self.charging.power_kw

    @property
    def climate_active(self) -> bool | None:
        """Return True if climatisation is active."""
        return self.climatisation.active


class SeatApiClientProtocol(Protocol):
    """Protocol describing the Seat API client."""

    async def async_get_vehicle_data(self) -> dict[str, SeatVehicleData]:
        """Return the latest vehicle data indexed by VIN."""

    async def async_lock_vehicle(self, vin: str) -> None:
        """Lock the vehicle."""

    async def async_unlock_vehicle(self, vin: str, spin: str | None = None) -> None:
        """Unlock the vehicle."""

    async def async_start_climate(self, vin: str, target_temp: float | None = None) -> None:
        """Start pre-conditioning."""

    async def async_stop_climate(self, vin: str) -> None:
        """Stop pre-conditioning."""

    async def async_start_charging(self, vin: str) -> None:
        """Start charging."""

    async def async_stop_charging(self, vin: str) -> None:
        """Stop charging."""

    async def async_set_charge_limit(self, vin: str, limit: int) -> None:
        """Set charging limit percentage."""

    async def async_set_charge_current(self, vin: str, current: str) -> None:
        """Set maximum charge current."""

    async def async_honk_flash(self, vin: str, honk: bool = True, flash: bool = True) -> None:
        """Trigger horn and/or flash lights."""

    async def async_trigger_request(self, vin: str) -> None:
        """Trigger a data refresh request to the vehicle."""


class SeatConnectAuth:
    """Handle Seat Connect authentication via VW Group Identity Provider."""

    # VW Group Login-specific URLs
    LOGIN_BASE = "https://identity.vwgroup.io"

    def __init__(self, username: str, password: str, session: ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._id_token: str | None = None
        self._token_expires: float | None = None
        # Use a cookie jar for maintaining session
        self._jar = aiohttp.CookieJar()

    @property
    def access_token(self) -> str | None:
        """Return current access token."""
        return self._access_token

    async def async_login(self) -> bool:
        """Perform full login flow via VW Group Identity Provider."""
        import re
        import html as html_module

        try:
            _LOGGER.debug("Starting Seat Connect authentication flow")

            # First, check if we can reach the identity server
            try:
                async with self._session.get(
                    AUTH_AUTHORIZE_URL.rsplit("/", 1)[0],  # Base URL
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    _LOGGER.debug("Identity server reachable, status: %s", resp.status)
            except aiohttp.ClientError as e:
                _LOGGER.error("Cannot reach VW Group identity server: %s", e)
                raise SeatApiCommunicationError(f"Cannot reach authentication server: {e}") from e

            # Generate PKCE challenge
            code_verifier = secrets.token_urlsafe(64)[:64]
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip("=")

            state = secrets.token_urlsafe(16)
            nonce = secrets.token_urlsafe(16)

            # Step 1: Initialize authorization request
            auth_params = {
                "response_type": "code id_token",
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "scope": " ".join(SCOPES),
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "ui_locales": UI_LOCALES,
                "prompt": "login",
            }

            headers = self._get_browser_headers()

            _LOGGER.debug("Step 1: Getting authorization page from %s", AUTH_AUTHORIZE_URL)

            # Create a dedicated connector with cookie jar
            connector = aiohttp.TCPConnector(ssl=True)

            async with aiohttp.ClientSession(
                connector=connector,
                cookie_jar=self._jar,
                headers=headers
            ) as login_session:

                async with login_session.get(
                    AUTH_AUTHORIZE_URL,
                    params=auth_params,
                    allow_redirects=True
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Authorization page request failed: %s", resp.status)
                        raise SeatApiAuthError(f"Authorization page request failed with status {resp.status}")

                    html = await resp.text()
                    current_url = str(resp.url)
                    _LOGGER.debug("Landed on URL: %s", current_url)

                # Step 2: Parse the login form
                _LOGGER.debug("Step 2: Parsing login form")

                # The VW Group uses Auth0, form fields are: username, password, state
                # Look for the form action (may be handled by JavaScript)
                form_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', html, re.I)

                if form_match:
                    form_action = html_module.unescape(form_match.group(1))
                else:
                    # Auth0 forms often POST to the same URL
                    form_action = current_url
                    _LOGGER.debug("No form action found, using current URL")

                # Make absolute URL
                if form_action.startswith("/"):
                    parsed = urlparse(current_url)
                    form_action = f"{parsed.scheme}://{parsed.netloc}{form_action}"
                elif not form_action.startswith("http"):
                    base = current_url.rsplit("/", 1)[0]
                    form_action = f"{base}/{form_action}"

                _LOGGER.debug("Form action: %s", form_action)

                # Extract hidden fields (especially 'state' for Auth0)
                hidden_fields = {}
                for match in re.finditer(r'<input[^>]*type=["\']hidden["\'][^>]*>', html, re.I):
                    input_html = match.group(0)
                    name_match = re.search(r'name=["\']([^"\']+)["\']', input_html)
                    value_match = re.search(r'value=["\']([^"\']*)["\']', input_html)
                    if name_match:
                        name = name_match.group(1)
                        value = html_module.unescape(value_match.group(1)) if value_match else ""
                        hidden_fields[name] = value

                _LOGGER.debug("Found hidden fields: %s", list(hidden_fields.keys()))

                # Step 3: Submit credentials
                # Auth0/VW Group uses 'username' field (not 'email')
                _LOGGER.debug("Step 3: Submitting credentials")

                login_data = {
                    **hidden_fields,
                    "username": self._username,  # Auth0 uses 'username'
                    "password": self._password,
                }

                post_headers = self._get_browser_headers()
                post_headers["Content-Type"] = "application/x-www-form-urlencoded"
                post_headers["Origin"] = self.LOGIN_BASE
                post_headers["Referer"] = current_url

                async with login_session.post(
                    form_action,
                    data=login_data,
                    headers=post_headers,
                    allow_redirects=False
                ) as resp:
                    _LOGGER.debug("Login response status: %s", resp.status)

                    if resp.status == 200:
                        # Check for error in response
                        error_html = await resp.text()
                        if "error" in error_html.lower() or "incorrect" in error_html.lower() or "falsch" in error_html.lower() or "wrong" in error_html.lower():
                            _LOGGER.error("Login failed - invalid credentials")
                            raise SeatApiAuthError("Invalid username or password")
                        # May need another redirect
                        redirect_url = str(resp.url)
                    elif resp.status == 400:
                        # Auth0 returns 400 for authentication errors
                        error_html = await resp.text()
                        if "incorrect" in error_html.lower() or "wrong" in error_html.lower() or "falsch" in error_html.lower():
                            _LOGGER.error("Login failed - invalid credentials (400)")
                            raise SeatApiAuthError("Invalid username or password")
                        _LOGGER.error("Login submission failed: %s", error_html[:200])
                        raise SeatApiAuthError("Login failed - bad request")
                    elif resp.status in (301, 302, 303, 307):
                        redirect_url = resp.headers.get("Location", "")
                    else:
                        _LOGGER.error("Login submission failed with status: %s", resp.status)
                        raise SeatApiAuthError(f"Login submission failed with status {resp.status}")

                # Step 4: Follow redirects until we get the authorization code
                _LOGGER.debug("Step 4: Following redirects to get auth code")

                max_redirects = 15
                for i in range(max_redirects):
                    if not redirect_url:
                        break

                    _LOGGER.debug("Redirect %d: %s", i + 1, redirect_url[:150] if len(redirect_url) > 150 else redirect_url)

                    # Check if we have the authorization code (check for app scheme or code parameter)
                    if (REDIRECT_URI.split("://")[0] + "://" in redirect_url or
                        "#code=" in redirect_url or
                        "?code=" in redirect_url or
                        "&code=" in redirect_url):
                        break

                    # Make absolute URL if needed
                    if redirect_url.startswith("/"):
                        parsed = urlparse(current_url)
                        redirect_url = f"{parsed.scheme}://{parsed.netloc}{redirect_url}"

                    try:
                        async with login_session.get(
                            redirect_url,
                            allow_redirects=False,
                            headers=self._get_browser_headers()
                        ) as resp:
                            current_url = redirect_url

                            if resp.status in (301, 302, 303, 307):
                                redirect_url = resp.headers.get("Location", "")
                            elif resp.status == 200:
                                # Check for JavaScript or meta redirect
                                html = await resp.text()
                                meta_match = re.search(r'http-equiv=["\']refresh["\'][^>]*content=["\'][^"\']*url=([^"\']+)', html, re.I)
                                if meta_match:
                                    redirect_url = html_module.unescape(meta_match.group(1))
                                else:
                                    # Look for JavaScript redirect
                                    js_match = re.search(r'window\.location\s*=\s*["\']([^"\']+)["\']', html)
                                    if js_match:
                                        redirect_url = html_module.unescape(js_match.group(1))
                                    else:
                                        break
                            else:
                                _LOGGER.debug("Unexpected status %s during redirect", resp.status)
                                break
                    except aiohttp.ClientResponseError as e:
                        # Custom URI scheme redirects may cause an error
                        error_str = str(e)
                        app_scheme = REDIRECT_URI.split("://")[0]
                        if app_scheme in error_str or "code=" in error_str:
                            # Try to extract the URL from the error
                            redirect_url = error_str
                            break
                        raise
                    except aiohttp.InvalidURL as e:
                        # Custom URI scheme like seatconnect:// may trigger InvalidURL
                        error_str = str(e)
                        app_scheme = REDIRECT_URI.split("://")[0]
                        if app_scheme in error_str:
                            redirect_url = error_str
                            break
                        raise

            # Step 5: Extract authorization code
            _LOGGER.debug("Step 5: Extracting authorization code")

            if not redirect_url:
                _LOGGER.error("No final redirect URL received")
                raise SeatApiAuthError("Authentication failed - no redirect URL received")

            # Parse the code from fragment or query
            parsed = urlparse(redirect_url)

            # Try fragment first (common for implicit flow)
            if parsed.fragment:
                params = parse_qs(parsed.fragment)
            else:
                params = parse_qs(parsed.query)

            auth_code = params.get("code", [None])[0]

            if not auth_code:
                _LOGGER.error("No authorization code found in URL: %s", redirect_url)
                raise SeatApiAuthError("Authentication failed - no authorization code received")

            _LOGGER.debug("Got authorization code, exchanging for tokens")

            # Step 6: Exchange code for tokens
            token_data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier,
            }

            async with self._session.post(
                AUTH_TOKEN_URL,
                data=token_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                }
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    _LOGGER.error("Token exchange failed: %s - %s", resp.status, error_text)
                    raise SeatApiAuthError(f"Token exchange failed with status {resp.status}")

                tokens = await resp.json()
                self._access_token = tokens.get("access_token")
                self._refresh_token = tokens.get("refresh_token")
                self._id_token = tokens.get("id_token")

                expires_in = tokens.get("expires_in", 3600)
                self._token_expires = datetime.now().timestamp() + expires_in

                _LOGGER.info("Seat Connect authentication successful")
                return True

        except SeatApiAuthError:
            raise
        except Exception as err:
            _LOGGER.exception("Login error: %s", err)
            raise SeatApiAuthError(f"Login failed due to unexpected error: {err}") from err


    def _get_browser_headers(self) -> dict[str, str]:
        """Return browser-like request headers."""
        return {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    async def async_refresh_tokens(self) -> bool:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            return await self.async_login()

        try:
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": CLIENT_ID,
            }

            async with self._session.post(
                AUTH_TOKEN_URL,
                data=token_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                }
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Token refresh failed, trying full login")
                    return await self.async_login()

                tokens = await resp.json()
                self._access_token = tokens.get("access_token")
                self._refresh_token = tokens.get("refresh_token", self._refresh_token)

                expires_in = tokens.get("expires_in", 3600)
                self._token_expires = datetime.now().timestamp() + expires_in

                return True

        except Exception as err:
            _LOGGER.exception("Token refresh error: %s", err)
            return await self.async_login()

    async def async_ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self._access_token:
            result = await self.async_login()
            if not result:
                raise SeatApiAuthError("Failed to authenticate with Seat Connect")
            return result

        if self._token_expires and datetime.now().timestamp() > self._token_expires - 60:
            result = await self.async_refresh_tokens()
            if not result:
                raise SeatApiAuthError("Failed to refresh authentication token")
            return result

        return True

    def _get_headers(self) -> dict[str, str]:
        """Return common request headers."""
        return {
            "User-Agent": USER_AGENT,
            "X-App-Name": X_APP_NAME,
            "X-App-Version": X_APP_VERSION,
            "Accept": "application/json",
        }


class SeatApiClient(SeatApiClientProtocol):
    """Seat Connect API client with full functionality."""

    def __init__(
        self,
        session: ClientSession,
        username: str | None = None,
        password: str | None = None,
        oauth_session: Any | None = None,
        spin: str | None = None,
        *,
        request_timeout: float = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        concurrency: int = 4,
    ) -> None:
        self._session = session
        self._oauth_session = oauth_session
        self._spin = spin
        self._request_timeout = request_timeout
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._semaphore = asyncio.Semaphore(concurrency)

        # Initialize auth if credentials provided
        self._auth: SeatConnectAuth | None = None
        if username and password:
            self._auth = SeatConnectAuth(username, password, session)

        # Cache for vehicle homeregions
        self._homeregions: dict[str, str] = {}

        # Cache for vehicles list
        self._vehicles_cache: dict[str, dict[str, Any]] = {}

    async def async_get_vehicle_data(self) -> dict[str, SeatVehicleData]:
        """Return normalized vehicle data for the account."""
        vehicles = await self._async_get_vehicles()

        tasks = [self._async_build_vehicle(v) for v in vehicles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: dict[str, SeatVehicleData] = {}
        for result in results:
            if isinstance(result, SeatVehicleData):
                data[result.vin] = result
            elif isinstance(result, BaseException):
                _LOGGER.error("Failed to get vehicle data: %s", result)

        return data

    async def _async_get_vehicles(self) -> list[dict[str, Any]]:
        """Get list of vehicles from the account."""
        # Try VW Car-Net API first
        try:
            payload = await self._request("GET", f"{API_BASE_URL}/usermanagement/users/v1/SEAT/ES/vehicles")
            if isinstance(payload, dict) and "userVehicles" in payload:
                vehicles = payload["userVehicles"].get("vehicle", [])
                if isinstance(vehicles, dict):
                    vehicles = [vehicles]
                for v in vehicles:
                    vin = v.get("vin")
                    if vin:
                        self._vehicles_cache[vin] = v
                return vehicles
        except Exception as err:
            _LOGGER.debug("Primary vehicle endpoint failed: %s", err)

        # Fallback endpoint
        try:
            payload = await self._request("GET", f"{API_HOMEREGION_URL}/cs/vds/v1/vehicles")
            if isinstance(payload, dict) and "data" in payload:
                vehicles = payload["data"]
                for v in vehicles:
                    vin = v.get("vin")
                    if vin:
                        self._vehicles_cache[vin] = v
                return vehicles
        except Exception as err:
            _LOGGER.error("Vehicle list fetch failed: %s", err)
            raise SeatApiError("Failed to get vehicle list") from err

        return []

    async def _async_get_homeregion(self, vin: str) -> str:
        """Get home region for a vehicle."""
        if vin in self._homeregions:
            return self._homeregions[vin]

        try:
            payload = await self._request(
                "GET",
                f"{API_HOMEREGION_URL}/cs/vds/v1/vehicles/{vin}/homeRegion"
            )
            if isinstance(payload, dict):
                uri = payload.get("homeRegion", {}).get("baseUri", {}).get("content", "")
                if uri:
                    self._homeregions[vin] = uri
                    return uri
        except Exception:
            pass

        # Default region
        self._homeregions[vin] = API_BASE_URL
        return API_BASE_URL

    async def _async_build_vehicle(self, vehicle: dict[str, Any]) -> SeatVehicleData:
        """Build complete vehicle data."""
        vin: str = vehicle.get("vin", "")

        # Get home region for this vehicle
        base_url = await self._async_get_homeregion(vin)

        # Fetch all data concurrently
        status_task = self._async_get_vehicle_status(vin, base_url)
        charging_task = self._async_get_charging_status(vin, base_url)
        climate_task = self._async_get_climatisation_status(vin, base_url)
        position_task = self._async_get_position(vin, base_url)
        capabilities_task = self._async_get_capabilities(vin, base_url)

        results = await asyncio.gather(
            status_task, charging_task, climate_task, position_task, capabilities_task,
            return_exceptions=True
        )

        status_data = results[0] if not isinstance(results[0], Exception) else {}
        charging_data = results[1] if not isinstance(results[1], Exception) else {}
        climate_data = results[2] if not isinstance(results[2], Exception) else {}
        position_data = results[3] if not isinstance(results[3], Exception) else {}
        capabilities = results[4] if not isinstance(results[4], Exception) else set()

        # Parse vehicle info
        vehicle_info = vehicle.get("vehicle", vehicle)

        return SeatVehicleData(
            vin=vin,
            name=vehicle_info.get("nickname") or vehicle_info.get("model", vin),
            model=vehicle_info.get("model", "Unknown"),
            model_year=vehicle_info.get("modelYear"),
            color=vehicle_info.get("color"),
            engine_type=self._determine_engine_type(vehicle_info, capabilities),
            battery_soc=self._extract_battery_soc(status_data, charging_data),
            battery_range_km=self._extract_battery_range(status_data, charging_data),
            fuel_level=self._extract_fuel_level(status_data),
            fuel_range_km=self._extract_fuel_range(status_data),
            total_range_km=self._extract_total_range(status_data),
            charging=self._build_charging_status(charging_data),
            status=self._build_vehicle_status(status_data),
            climatisation=self._build_climatisation_status(climate_data),
            position=self._build_position(position_data),
            odometer=self._build_odometer(status_data),
            is_locked=self._extract_lock_status(status_data),
            capabilities=capabilities if isinstance(capabilities, set) else set(),
        )

    async def _async_get_vehicle_status(self, vin: str, base_url: str) -> dict[str, Any]:
        """Get vehicle status."""
        try:
            return await self._request(
                "GET",
                f"{base_url}/bs/vsr/v1/SEAT/ES/vehicles/{vin}/status"
            )
        except Exception as err:
            _LOGGER.debug("Vehicle status fetch failed for %s: %s", vin, err)
            return {}

    async def _async_get_charging_status(self, vin: str, base_url: str) -> dict[str, Any]:
        """Get charging status."""
        try:
            return await self._request(
                "GET",
                f"{base_url}/bs/batterycharge/v1/SEAT/ES/vehicles/{vin}/charger"
            )
        except Exception as err:
            _LOGGER.debug("Charging status fetch failed for %s: %s", vin, err)
            return {}

    async def _async_get_climatisation_status(self, vin: str, base_url: str) -> dict[str, Any]:
        """Get climatisation status."""
        try:
            return await self._request(
                "GET",
                f"{base_url}/bs/climatisation/v1/SEAT/ES/vehicles/{vin}/climater"
            )
        except Exception as err:
            _LOGGER.debug("Climatisation status fetch failed for %s: %s", vin, err)
            return {}

    async def _async_get_position(self, vin: str, base_url: str) -> dict[str, Any]:
        """Get vehicle position."""
        try:
            return await self._request(
                "GET",
                f"{base_url}/bs/cf/v1/SEAT/ES/vehicles/{vin}/position"
            )
        except Exception as err:
            _LOGGER.debug("Position fetch failed for %s: %s", vin, err)
            return {}

    async def _async_get_capabilities(self, vin: str, base_url: str) -> set[str]:
        """Get vehicle capabilities."""
        try:
            payload = await self._request(
                "GET",
                f"{base_url}/bs/vsr/v1/SEAT/ES/vehicles/{vin}/capabilities"
            )
            if isinstance(payload, dict):
                caps = payload.get("capabilities", {})
                return {
                    cap.get("id") or cap.get("name", "")
                    for cap in caps.get("capabilityList", [])
                    if cap.get("status") == "enabled"
                }
        except Exception as err:
            _LOGGER.debug("Capabilities fetch failed for %s: %s", vin, err)
        return set()

    # Data extraction helpers
    def _determine_engine_type(self, info: dict, caps: set) -> str:
        """Determine engine type from vehicle info."""
        fuel_type = info.get("fuelType", "").lower()
        if "electric" in fuel_type or "ev" in fuel_type:
            return "electric"
        if "hybrid" in fuel_type or "phev" in fuel_type:
            return "hybrid"
        if CAP_CHARGING in caps:
            return "electric" if "FUEL" not in caps else "hybrid"
        return "combustion"

    def _extract_battery_soc(self, status: dict, charging: dict) -> float | None:
        """Extract battery state of charge."""
        # Try charging endpoint first
        charger = charging.get("charger", {})
        soc = charger.get("status", {}).get("batteryStatusData", {}).get("stateOfCharge", {})
        if "content" in soc:
            return _coerce_float(soc["content"])

        # Try status endpoint
        battery = status.get("vehicleStatusData", {}).get("batteryStatus", {})
        if "stateOfCharge" in battery:
            return _coerce_float(battery["stateOfCharge"])

        return None

    def _extract_battery_range(self, status: dict, charging: dict) -> float | None:
        """Extract electric range."""
        charger = charging.get("charger", {})
        range_data = charger.get("status", {}).get("cruisingRangeStatusData", {})
        if "primaryEngineRange" in range_data:
            return _coerce_float(range_data["primaryEngineRange"].get("content"))
        return None

    def _extract_fuel_level(self, status: dict) -> float | None:
        """Extract fuel level."""
        fuel = status.get("vehicleStatusData", {}).get("fuelStatus", {})
        return _coerce_float(fuel.get("fuelLevel"))

    def _extract_fuel_range(self, status: dict) -> float | None:
        """Extract fuel range."""
        fuel = status.get("vehicleStatusData", {}).get("fuelStatus", {})
        return _coerce_float(fuel.get("remainingRange"))

    def _extract_total_range(self, status: dict) -> float | None:
        """Extract total combined range."""
        range_data = status.get("vehicleStatusData", {}).get("rangeStatus", {})
        return _coerce_float(range_data.get("totalRange"))

    def _extract_lock_status(self, status: dict) -> bool | None:
        """Extract lock status."""
        access = status.get("vehicleStatusData", {}).get("accessStatus", {})
        lock_state = access.get("overallStatus")
        if lock_state == "locked":
            return True
        if lock_state == "unlocked":
            return False

        # Check door lock states
        doors = access.get("doorLockStatus", [])
        if doors:
            return all(d.get("lockState") == "locked" for d in doors)
        return None

    def _build_charging_status(self, charging: dict) -> SeatChargingStatus:
        """Build charging status from API response."""
        charger = charging.get("charger", {})
        status = charger.get("status", {})
        charging_data = status.get("chargingStatusData", {})
        plug_data = status.get("plugStatusData", {})

        return SeatChargingStatus(
            state=charging_data.get("chargingState", {}).get("content"),
            mode=charging_data.get("chargingMode", {}).get("content"),
            power_kw=_coerce_float(charging_data.get("chargingPower", {}).get("content")),
            remaining_time_min=_coerce_int(charging_data.get("remainingChargingTime", {}).get("content")),
            target_soc=_coerce_int(charger.get("settings", {}).get("targetSOC", {}).get("content")),
            max_current_a=_coerce_int(charger.get("settings", {}).get("maxChargeCurrent", {}).get("content")),
            plug_connected=plug_data.get("plugState", {}).get("content") == "connected",
            plug_locked=plug_data.get("lockState", {}).get("content") == "locked",
            external_power=plug_data.get("externalPower", {}).get("content") == "available",
        )

    def _build_vehicle_status(self, status: dict) -> SeatVehicleStatus:
        """Build vehicle status from API response."""
        vsd = status.get("vehicleStatusData", {})
        doors = {d.get("name"): d.get("status") for d in vsd.get("doorStatus", [])}
        windows = {w.get("name"): w.get("status") for w in vsd.get("windowStatus", [])}

        return SeatVehicleStatus(
            door_front_left_open=doors.get("frontLeft") == "open",
            door_front_right_open=doors.get("frontRight") == "open",
            door_rear_left_open=doors.get("rearLeft") == "open",
            door_rear_right_open=doors.get("rearRight") == "open",
            trunk_open=doors.get("trunk") == "open",
            hood_open=doors.get("hood") == "open",
            window_front_left_open=windows.get("frontLeft") == "open",
            window_front_right_open=windows.get("frontRight") == "open",
            window_rear_left_open=windows.get("rearLeft") == "open",
            window_rear_right_open=windows.get("rearRight") == "open",
            sunroof_open=windows.get("sunroof") == "open",
        )

    def _build_climatisation_status(self, climate: dict) -> SeatClimatisationStatus:
        """Build climatisation status from API response."""
        climater = climate.get("climater", {})
        status = climater.get("status", {})
        climate_status = status.get("climatisationStatusData", {})
        settings = climater.get("settings", {})

        state = climate_status.get("climatisationState", {}).get("content", "off")

        return SeatClimatisationStatus(
            active=state in ("heating", "cooling", "ventilation", "on"),
            target_temp_c=self._parse_temp(settings.get("targetTemperature", {}).get("content")),
            remaining_time_min=_coerce_int(climate_status.get("remainingClimatisationTime", {}).get("content")),
            window_heating_front=status.get("windowHeatingStatusData", {}).get("windowHeatingStateFront", {}).get("content") == "on",
            window_heating_rear=status.get("windowHeatingStatusData", {}).get("windowHeatingStateRear", {}).get("content") == "on",
        )

    def _parse_temp(self, value: Any) -> float | None:
        """Parse temperature from various formats."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            # API often returns in decikelvin (2730 = 0°C)
            if value > 273:
                return round((value / 10) - 273.15, 1)
            return float(value)
        return None

    def _build_position(self, position: dict) -> SeatVehiclePosition:
        """Build position from API response."""
        find_car = position.get("findCarResponse", {})
        pos = find_car.get("Position", {})
        car_coord = pos.get("carCoordinate", {})

        lat = car_coord.get("latitude")
        lon = car_coord.get("longitude")

        # Coordinates are often in microdegrees
        if lat and abs(lat) > 90:
            lat = lat / 1000000
        if lon and abs(lon) > 180:
            lon = lon / 1000000

        return SeatVehiclePosition(
            latitude=_coerce_float(lat),
            longitude=_coerce_float(lon),
            timestamp=self._parse_timestamp(find_car.get("carLocatedAt")),
            parking_time=self._parse_timestamp(find_car.get("parkingTimeUTC")),
        )

    def _parse_timestamp(self, value: Any) -> datetime | None:
        """Parse timestamp from API response."""
        if not value:
            return None
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            pass
        return None

    def _build_odometer(self, status: dict) -> SeatVehicleOdometer:
        """Build odometer from API response."""
        vsd = status.get("vehicleStatusData", {})
        odometer = vsd.get("odometerStatus", {})

        return SeatVehicleOdometer(
            value=_coerce_float(odometer.get("odometer")),
            unit=odometer.get("unit", "km"),
        )

    # Vehicle control methods
    async def async_lock_vehicle(self, vin: str) -> None:
        """Lock the vehicle."""
        base_url = await self._async_get_homeregion(vin)
        await self._execute_rlu_action(vin, base_url, "lock")

    async def async_unlock_vehicle(self, vin: str, spin: str | None = None) -> None:
        """Unlock the vehicle."""
        base_url = await self._async_get_homeregion(vin)
        await self._execute_rlu_action(vin, base_url, "unlock", spin or self._spin)

    async def _execute_rlu_action(
        self, vin: str, base_url: str, action: str, spin: str | None = None
    ) -> None:
        """Execute remote lock/unlock action."""
        endpoint = f"{base_url}/bs/rlu/v1/SEAT/ES/vehicles/{vin}/actions"

        body: dict[str, Any] = {
            "rluAction": {
                "action": action
            }
        }

        # SPIN required for unlock
        if spin and action == "unlock":
            body["rluAction"]["spin"] = spin

        await self._request("POST", endpoint, json=body)

    async def async_start_climate(self, vin: str, target_temp: float | None = None) -> None:
        """Start climatisation."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/climatisation/v1/SEAT/ES/vehicles/{vin}/climater/actions"

        action: dict[str, Any] = {
            "action": {
                "type": "startClimatisation"
            }
        }

        if target_temp is not None:
            # Convert Celsius to decikelvin
            temp_dk = int((target_temp + 273.15) * 10)
            action["action"]["settings"] = {
                "targetTemperature": temp_dk
            }

        await self._request("POST", endpoint, json=action)

    async def async_stop_climate(self, vin: str) -> None:
        """Stop climatisation."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/climatisation/v1/SEAT/ES/vehicles/{vin}/climater/actions"

        action = {
            "action": {
                "type": "stopClimatisation"
            }
        }

        await self._request("POST", endpoint, json=action)

    async def async_start_charging(self, vin: str) -> None:
        """Start charging."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/batterycharge/v1/SEAT/ES/vehicles/{vin}/charger/actions"

        await self._request("POST", endpoint, json={"action": {"type": "start"}})

    async def async_stop_charging(self, vin: str) -> None:
        """Stop charging."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/batterycharge/v1/SEAT/ES/vehicles/{vin}/charger/actions"

        await self._request("POST", endpoint, json={"action": {"type": "stop"}})

    async def async_set_charge_limit(self, vin: str, limit: int) -> None:
        """Set target state of charge."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/batterycharge/v1/SEAT/ES/vehicles/{vin}/charger/settings"

        await self._request("PUT", endpoint, json={
            "settings": {
                "targetSOC": {"content": min(max(limit, 0), 100)}
            }
        })

    async def async_set_charge_current(self, vin: str, current: str) -> None:
        """Set maximum charge current (reduced, max)."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/batterycharge/v1/SEAT/ES/vehicles/{vin}/charger/settings"

        await self._request("PUT", endpoint, json={
            "settings": {
                "maxChargeCurrent": {"content": current}
            }
        })

    async def async_honk_flash(
        self, vin: str, honk: bool = True, flash: bool = True
    ) -> None:
        """Trigger horn and/or flash lights."""
        base_url = await self._async_get_homeregion(vin)

        # Get current position first
        position = await self._async_get_position(vin, base_url)
        pos = position.get("findCarResponse", {}).get("Position", {})

        endpoint = f"{base_url}/bs/rhf/v1/SEAT/ES/vehicles/{vin}/honkAndFlash"

        action = {
            "honkAndFlashRequest": {
                "serviceOperationCode": "HONK_AND_FLASH" if honk and flash else
                                       ("HONK" if honk else "FLASH"),
                "position": pos
            }
        }

        await self._request("POST", endpoint, json=action)

    async def async_trigger_request(self, vin: str) -> None:
        """Request vehicle to update its status."""
        base_url = await self._async_get_homeregion(vin)
        endpoint = f"{base_url}/bs/vsr/v1/SEAT/ES/vehicles/{vin}/requests"

        await self._request("POST", endpoint)

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make an authenticated API request with retry logic."""
        attempt = 0

        while True:
            attempt += 1

            try:
                # Ensure valid authentication
                if self._auth:
                    await self._auth.async_ensure_valid_token()
                    headers = kwargs.pop("headers", {})
                    headers["Authorization"] = f"Bearer {self._auth.access_token}"
                    headers["User-Agent"] = USER_AGENT
                    headers["Accept"] = "application/json"
                    headers["Content-Type"] = "application/json"
                    kwargs["headers"] = headers
                elif self._oauth_session:
                    # Use Home Assistant OAuth session
                    async with self._semaphore, async_timeout.timeout(self._request_timeout):
                        response = await self._oauth_session.async_request(method, url, **kwargs)
                        try:
                            if response.content_type == "application/json":
                                return await response.json()
                            if response.content_length == 0:
                                return None
                            return await response.text()
                        finally:
                            response.release()

                # Make request with aiohttp session
                async with self._semaphore, async_timeout.timeout(self._request_timeout):
                    async with self._session.request(method, url, **kwargs) as response:
                        if response.status == HTTPStatus.UNAUTHORIZED:
                            if self._auth:
                                await self._auth.async_login()
                                if attempt <= self._max_retries:
                                    continue
                            raise SeatApiAuthError("Authentication failed")

                        if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                            if attempt > self._max_retries:
                                raise SeatApiRateLimitError("Rate limit exceeded")
                            await asyncio.sleep(self._backoff_factor * attempt)
                            continue

                        if response.status >= 500 and attempt <= self._max_retries:
                            await asyncio.sleep(self._backoff_factor * attempt)
                            continue

                        if response.status >= 400:
                            raise SeatApiError(f"API request failed: {response.status}")

                        if response.content_type == "application/json":
                            return await response.json()
                        if response.content_length == 0:
                            return None
                        return await response.text()

            except ClientError as err:
                if attempt > self._max_retries:
                    raise SeatApiCommunicationError("Network error") from err
                await asyncio.sleep(self._backoff_factor * attempt)
            except asyncio.TimeoutError as err:
                if attempt > self._max_retries:
                    raise SeatApiCommunicationError("Request timed out") from err
                await asyncio.sleep(self._backoff_factor * attempt)


def _coerce_float(value: Any) -> float | None:
    """Return a float if possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    """Return an int if possible."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

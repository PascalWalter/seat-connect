"""DataUpdateCoordinator for SEAT Connect."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SeatApiClientProtocol, SeatVehicleData, SeatApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SeatDataUpdateCoordinator(DataUpdateCoordinator[dict[str, SeatVehicleData]]):
    """Coordinator responsible for polling the Seat API."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: SeatApiClientProtocol,
        entry_id: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Seat Connect ({entry_id})",
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, SeatVehicleData]:
        try:
            return await self.client.async_get_vehicle_data()
        except SeatApiError as err:
            raise UpdateFailed(str(err)) from err

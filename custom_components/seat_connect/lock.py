"""Lock entity for Seat Connect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator
    entities = [SeatConnectLockEntity(coordinator, vin) for vin in coordinator.data or {}]
    async_add_entities(entities)


class SeatConnectLockEntity(SeatConnectEntity[SeatVehicleData], LockEntity):
    """Vehicle door lock."""

    _attr_translation_key = "vehicle_lock"

    def __init__(self, coordinator: "SeatDataUpdateCoordinator", vin: str) -> None:
        super().__init__(coordinator, vin, "lock")

    @property
    def is_locked(self) -> bool | None:
        return self._vehicle.is_locked

    async def async_lock(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_lock_vehicle(self._vin)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_unlock_vehicle(self._vin)
        await self.coordinator.async_request_refresh()

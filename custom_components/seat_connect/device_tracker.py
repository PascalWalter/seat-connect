"""Device tracker platform for Seat Connect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_PARKING_POSITION
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Seat device tracker entities."""
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        # Only add tracker if position capability is available or position data exists
        if _supports_position(vehicle):
            entities.append(SeatConnectDeviceTracker(coordinator, vin))

    if entities:
        async_add_entities(entities)


def _supports_position(vehicle: SeatVehicleData) -> bool:
    """Check if vehicle supports position tracking."""
    if CAP_PARKING_POSITION in vehicle.capabilities:
        return True
    if vehicle.position.latitude is not None and vehicle.position.longitude is not None:
        return True
    return False


class SeatConnectDeviceTracker(SeatConnectEntity[SeatVehicleData], TrackerEntity):
    """Seat Connect device tracker."""

    _attr_translation_key = "vehicle_position"
    _attr_icon = "mdi:car-marker"

    def __init__(self, coordinator: "SeatDataUpdateCoordinator", vin: str) -> None:
        """Initialize device tracker."""
        super().__init__(coordinator, vin, "position")

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._vehicle.position.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._vehicle.position.longitude

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return extra state attributes."""
        attrs = {}

        if self._vehicle.position.timestamp:
            attrs["last_updated"] = self._vehicle.position.timestamp.isoformat()

        if self._vehicle.position.parking_time:
            attrs["parking_time"] = self._vehicle.position.parking_time.isoformat()

        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self._vehicle.position.latitude is not None
            and self._vehicle.position.longitude is not None
        )

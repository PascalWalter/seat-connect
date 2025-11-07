"""Binary sensor platform for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN
from .entity import SeatConnectEntity


@dataclass(frozen=True, kw_only=True)
class SeatBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Binary sensor description for Seat Connect."""

    value_fn: Callable[[SeatVehicleData], bool | None]


BINARY_SENSORS: tuple[SeatBinarySensorEntityDescription, ...] = (
    SeatBinarySensorEntityDescription(
        key="plug_connected",
        translation_key="plug_connected",
        name="Charging plug",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda vehicle: vehicle.plug_connected,
    ),
    SeatBinarySensorEntityDescription(
        key="doors_windows_open",
        translation_key="doors_windows_open",
        name="Doors or windows open",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda vehicle: _derive_open_state(vehicle),
    ),
)


def _derive_open_state(vehicle: SeatVehicleData) -> bool | None:
    if vehicle.doors_closed is None and vehicle.windows_closed is None:
        return None
    if vehicle.doors_closed is False or vehicle.windows_closed is False:
        return True
    if vehicle.doors_closed is True and vehicle.windows_closed is True:
        return False
    return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id].coordinator
    entities = [
        SeatConnectBinarySensorEntity(coordinator, vin, description)
        for vin in coordinator.data or {}
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class SeatConnectBinarySensorEntity(SeatConnectEntity[SeatVehicleData], BinarySensorEntity):
    """Seat binary sensor."""

    entity_description: SeatBinarySensorEntityDescription

    def __init__(
        self,
        coordinator,
        vin: str,
        description: SeatBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._vehicle)

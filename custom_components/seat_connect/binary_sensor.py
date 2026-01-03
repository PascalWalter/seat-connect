"""Binary sensor platform for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_CHARGING
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SeatBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Binary sensor description for Seat Connect."""

    value_fn: Callable[[SeatVehicleData], bool | None]
    available_fn: Callable[[SeatVehicleData], bool] = lambda _: True


BINARY_SENSORS: tuple[SeatBinarySensorEntityDescription, ...] = (
    # Charging sensors
    SeatBinarySensorEntityDescription(
        key="plug_connected",
        translation_key="plug_connected",
        name="Charging plug",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda vehicle: vehicle.charging.plug_connected,
        available_fn=lambda v: v.charging.plug_connected is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="plug_locked",
        translation_key="plug_locked",
        name="Charging plug locked",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda vehicle: not vehicle.charging.plug_locked if vehicle.charging.plug_locked is not None else None,
        available_fn=lambda v: v.charging.plug_locked is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="external_power",
        translation_key="external_power",
        name="External power",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda vehicle: vehicle.charging.external_power,
        available_fn=lambda v: v.charging.external_power is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="charging_active",
        translation_key="charging_active",
        name="Charging active",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda vehicle: vehicle.charging.state == "charging",
        available_fn=lambda v: v.charging.state is not None,
    ),
    # Door sensors
    SeatBinarySensorEntityDescription(
        key="doors_closed",
        translation_key="doors_closed",
        name="All doors closed",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: not vehicle.doors_closed if vehicle.doors_closed is not None else None,
        available_fn=lambda v: v.doors_closed is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="door_front_left",
        translation_key="door_front_left",
        name="Door front left",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.door_front_left_open,
        available_fn=lambda v: v.status.door_front_left_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="door_front_right",
        translation_key="door_front_right",
        name="Door front right",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.door_front_right_open,
        available_fn=lambda v: v.status.door_front_right_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="door_rear_left",
        translation_key="door_rear_left",
        name="Door rear left",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.door_rear_left_open,
        available_fn=lambda v: v.status.door_rear_left_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="door_rear_right",
        translation_key="door_rear_right",
        name="Door rear right",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.door_rear_right_open,
        available_fn=lambda v: v.status.door_rear_right_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="trunk",
        translation_key="trunk",
        name="Trunk",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.trunk_open,
        available_fn=lambda v: v.status.trunk_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="hood",
        translation_key="hood",
        name="Hood",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda vehicle: vehicle.status.hood_open,
        available_fn=lambda v: v.status.hood_open is not None,
    ),
    # Window sensors
    SeatBinarySensorEntityDescription(
        key="windows_closed",
        translation_key="windows_closed",
        name="All windows closed",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: not vehicle.windows_closed if vehicle.windows_closed is not None else None,
        available_fn=lambda v: v.windows_closed is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="window_front_left",
        translation_key="window_front_left",
        name="Window front left",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: vehicle.status.window_front_left_open,
        available_fn=lambda v: v.status.window_front_left_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="window_front_right",
        translation_key="window_front_right",
        name="Window front right",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: vehicle.status.window_front_right_open,
        available_fn=lambda v: v.status.window_front_right_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="window_rear_left",
        translation_key="window_rear_left",
        name="Window rear left",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: vehicle.status.window_rear_left_open,
        available_fn=lambda v: v.status.window_rear_left_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="window_rear_right",
        translation_key="window_rear_right",
        name="Window rear right",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: vehicle.status.window_rear_right_open,
        available_fn=lambda v: v.status.window_rear_right_open is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="sunroof",
        translation_key="sunroof",
        name="Sunroof",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda vehicle: vehicle.status.sunroof_open,
        available_fn=lambda v: v.status.sunroof_open is not None,
    ),
    # Climate sensors
    SeatBinarySensorEntityDescription(
        key="climate_active",
        translation_key="climate_active",
        name="Climatisation active",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda vehicle: vehicle.climatisation.active,
        available_fn=lambda v: True,
    ),
    SeatBinarySensorEntityDescription(
        key="window_heating_front",
        translation_key="window_heating_front",
        name="Window heating front",
        icon="mdi:car-defrost-front",
        value_fn=lambda vehicle: vehicle.climatisation.window_heating_front,
        available_fn=lambda v: v.climatisation.window_heating_front is not None,
    ),
    SeatBinarySensorEntityDescription(
        key="window_heating_rear",
        translation_key="window_heating_rear",
        name="Window heating rear",
        icon="mdi:car-defrost-rear",
        value_fn=lambda vehicle: vehicle.climatisation.window_heating_rear,
        available_fn=lambda v: v.climatisation.window_heating_rear is not None,
    ),
    # Lock sensor
    SeatBinarySensorEntityDescription(
        key="vehicle_locked",
        translation_key="vehicle_locked",
        name="Vehicle locked",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda vehicle: not vehicle.is_locked if vehicle.is_locked is not None else None,
        available_fn=lambda v: v.is_locked is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        for description in BINARY_SENSORS:
            if description.available_fn(vehicle):
                entities.append(SeatConnectBinarySensorEntity(coordinator, vin, description))

    async_add_entities(entities)


class SeatConnectBinarySensorEntity(SeatConnectEntity[SeatVehicleData], BinarySensorEntity):
    """Seat binary sensor."""

    entity_description: SeatBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: "SeatDataUpdateCoordinator",
        vin: str,
        description: SeatBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._vehicle)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.entity_description.available_fn(self._vehicle)

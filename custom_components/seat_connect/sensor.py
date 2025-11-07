"""Sensor entities for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfPower

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN
from .entity import SeatConnectEntity


@dataclass(frozen=True, kw_only=True)
class SeatSensorEntityDescription(SensorEntityDescription):
    """Seat sensor metadata."""

    value_fn: Callable[[SeatVehicleData], float | int | str | None]


SENSOR_DESCRIPTIONS: tuple[SeatSensorEntityDescription, ...] = (
    SeatSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        name="Battery SoC",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.battery_soc,
    ),
    SeatSensorEntityDescription(
        key="range",
        translation_key="range",
        name="Electric range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:road-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.battery_range_km,
    ),
    SeatSensorEntityDescription(
        key="charging_power",
        translation_key="charging_power",
        name="Charging power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.charging_power_kw,
    ),
    SeatSensorEntityDescription(
        key="charging_state",
        translation_key="charging_state",
        name="Charging state",
        icon="mdi:ev-station",
        value_fn=lambda vehicle: vehicle.charging_state,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Seat sensors."""

    coordinator = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id].coordinator
    entities = [
        SeatConnectSensorEntity(coordinator, vin, description)
        for vin in coordinator.data or {}
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class SeatConnectSensorEntity(SeatConnectEntity[SeatVehicleData], SensorEntity):
    """Representation of a Seat sensor."""

    entity_description: SeatSensorEntityDescription

    def __init__(
        self,
        coordinator,
        vin: str,
        description: SeatSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self._vehicle)

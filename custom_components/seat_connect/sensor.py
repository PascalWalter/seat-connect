"""Sensor entities for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTime,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_CHARGING
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SeatSensorEntityDescription(SensorEntityDescription):
    """Seat sensor metadata."""

    value_fn: Callable[[SeatVehicleData], float | int | str | None]
    available_fn: Callable[[SeatVehicleData], bool] = lambda _: True


SENSOR_DESCRIPTIONS: tuple[SeatSensorEntityDescription, ...] = (
    # Battery sensors
    SeatSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        name="Battery SoC",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.battery_soc,
        available_fn=lambda v: v.battery_soc is not None,
    ),
    SeatSensorEntityDescription(
        key="battery_range",
        translation_key="battery_range",
        name="Electric range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:road-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.battery_range_km,
        available_fn=lambda v: v.battery_range_km is not None,
    ),
    # Fuel sensors
    SeatSensorEntityDescription(
        key="fuel_level",
        translation_key="fuel_level",
        name="Fuel level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gas-station",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.fuel_level,
        available_fn=lambda v: v.fuel_level is not None,
    ),
    SeatSensorEntityDescription(
        key="fuel_range",
        translation_key="fuel_range",
        name="Fuel range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:gas-station-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.fuel_range_km,
        available_fn=lambda v: v.fuel_range_km is not None,
    ),
    SeatSensorEntityDescription(
        key="total_range",
        translation_key="total_range",
        name="Total range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:map-marker-distance",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.total_range_km,
        available_fn=lambda v: v.total_range_km is not None,
    ),
    # Charging sensors
    SeatSensorEntityDescription(
        key="charging_power",
        translation_key="charging_power",
        name="Charging power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.charging.power_kw,
        available_fn=lambda v: v.charging.power_kw is not None,
    ),
    SeatSensorEntityDescription(
        key="charging_state",
        translation_key="charging_state",
        name="Charging state",
        icon="mdi:ev-station",
        value_fn=lambda vehicle: vehicle.charging.state,
        available_fn=lambda v: v.charging.state is not None,
    ),
    SeatSensorEntityDescription(
        key="charging_time_remaining",
        translation_key="charging_time_remaining",
        name="Charging time remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.charging.remaining_time_min,
        available_fn=lambda v: v.charging.remaining_time_min is not None,
    ),
    SeatSensorEntityDescription(
        key="target_soc",
        translation_key="target_soc",
        name="Target SoC",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-charging-high",
        value_fn=lambda vehicle: vehicle.charging.target_soc,
        available_fn=lambda v: v.charging.target_soc is not None,
    ),
    SeatSensorEntityDescription(
        key="max_charge_current",
        translation_key="max_charge_current",
        name="Max charge current",
        icon="mdi:current-ac",
        value_fn=lambda vehicle: vehicle.charging.max_current_a,
        available_fn=lambda v: v.charging.max_current_a is not None,
    ),
    # Climate sensors
    SeatSensorEntityDescription(
        key="climate_target_temp",
        translation_key="climate_target_temp",
        name="Climate target temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer",
        value_fn=lambda vehicle: vehicle.climatisation.target_temp_c,
        available_fn=lambda v: v.climatisation.target_temp_c is not None,
    ),
    SeatSensorEntityDescription(
        key="climate_remaining_time",
        translation_key="climate_remaining_time",
        name="Climate remaining time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        value_fn=lambda vehicle: vehicle.climatisation.remaining_time_min,
        available_fn=lambda v: v.climatisation.remaining_time_min is not None,
    ),
    # Odometer
    SeatSensorEntityDescription(
        key="odometer",
        translation_key="odometer",
        name="Odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda vehicle: vehicle.odometer.value,
        available_fn=lambda v: v.odometer.value is not None,
    ),
    # Trip statistics
    SeatSensorEntityDescription(
        key="average_speed",
        translation_key="average_speed",
        name="Average speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.trip_statistics.average_speed_kmh,
        available_fn=lambda v: v.trip_statistics.average_speed_kmh is not None,
    ),
    SeatSensorEntityDescription(
        key="average_consumption_kwh",
        translation_key="average_consumption_kwh",
        name="Average consumption (electric)",
        native_unit_of_measurement="kWh/100km",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.trip_statistics.average_consumption_kwh,
        available_fn=lambda v: v.trip_statistics.average_consumption_kwh is not None,
    ),
    SeatSensorEntityDescription(
        key="average_consumption_l",
        translation_key="average_consumption_l",
        name="Average consumption (fuel)",
        native_unit_of_measurement="L/100km",
        icon="mdi:gas-station",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.trip_statistics.average_consumption_l,
        available_fn=lambda v: v.trip_statistics.average_consumption_l is not None,
    ),
    # Engine type
    SeatSensorEntityDescription(
        key="engine_type",
        translation_key="engine_type",
        name="Engine type",
        icon="mdi:engine",
        value_fn=lambda vehicle: vehicle.engine_type,
        available_fn=lambda v: v.engine_type is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Seat sensors."""
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        for description in SENSOR_DESCRIPTIONS:
            if description.available_fn(vehicle):
                entities.append(SeatConnectSensorEntity(coordinator, vin, description))

    async_add_entities(entities)


class SeatConnectSensorEntity(SeatConnectEntity[SeatVehicleData], SensorEntity):
    """Representation of a Seat sensor."""

    entity_description: SeatSensorEntityDescription

    def __init__(
        self,
        coordinator: "SeatDataUpdateCoordinator",
        vin: str,
        description: SeatSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self._vehicle)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.entity_description.available_fn(self._vehicle)

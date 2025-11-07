"""Climate entity exposing Seat pre-conditioning."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator

SUPPORTED_HVAC_MODES: list[HVACMode] = [HVACMode.OFF, HVACMode.HEAT]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator
    entities = [
        SeatConnectClimateEntity(coordinator, vin)
        for vin, vehicle in (coordinator.data or {}).items()
        if _supports_climate(vehicle)
    ]
    if entities:
        async_add_entities(entities)


def _supports_climate(vehicle: SeatVehicleData) -> bool:
    if vehicle.capabilities and "CLIMATE" in {cap.upper() for cap in vehicle.capabilities}:
        return True
    return vehicle.climate_active is not None


class SeatConnectClimateEntity(SeatConnectEntity[SeatVehicleData], ClimateEntity):
    """Seat climate entity."""

    _attr_hvac_modes = SUPPORTED_HVAC_MODES
    _attr_translation_key = "preconditioning"

    def __init__(self, coordinator: "SeatDataUpdateCoordinator", vin: str) -> None:
        super().__init__(coordinator, vin, "climate")

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if self._vehicle.climate_active else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.async_stop_climate(self._vin)
        elif hvac_mode == HVACMode.HEAT:
            await self.coordinator.client.async_start_climate(self._vin)
        else:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        return super().available and _supports_climate(self._vehicle)

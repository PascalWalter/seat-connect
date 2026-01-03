"""Number platform for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatApiClientProtocol, SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_CHARGING
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SeatNumberEntityDescription(NumberEntityDescription):
    """Number entity description for Seat Connect."""

    value_fn: Callable[[SeatVehicleData], float | None]
    set_value_fn: Callable[[SeatApiClientProtocol, str, int], Coroutine[Any, Any, None]]
    available_fn: Callable[[SeatVehicleData], bool] = lambda _: True


NUMBER_DESCRIPTIONS: tuple[SeatNumberEntityDescription, ...] = (
    SeatNumberEntityDescription(
        key="target_soc",
        translation_key="target_soc",
        name="Target state of charge",
        icon="mdi:battery-charging-100",
        native_min_value=10,
        native_max_value=100,
        native_step=10,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        value_fn=lambda v: v.charging.target_soc,
        set_value_fn=lambda c, vin, val: c.async_set_charge_limit(vin, val),
        available_fn=lambda v: CAP_CHARGING in v.capabilities or v.charging.target_soc is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Seat number entities."""
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        for description in NUMBER_DESCRIPTIONS:
            if description.available_fn(vehicle):
                entities.append(SeatConnectNumberEntity(coordinator, vin, description))

    if entities:
        async_add_entities(entities)


class SeatConnectNumberEntity(SeatConnectEntity[SeatVehicleData], NumberEntity):
    """Seat Connect number entity."""

    entity_description: SeatNumberEntityDescription

    def __init__(
        self,
        coordinator: "SeatDataUpdateCoordinator",
        vin: str,
        description: SeatNumberEntityDescription,
    ) -> None:
        """Initialize number entity."""
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_fn(self._vehicle)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.entity_description.set_value_fn(
            self.coordinator.client, self._vin, int(value)
        )
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.entity_description.available_fn(self._vehicle)

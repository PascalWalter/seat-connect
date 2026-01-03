"""Switch platform for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatApiClientProtocol, SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_CHARGING
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SeatSwitchEntityDescription(SwitchEntityDescription):
    """Switch entity description for Seat Connect."""

    is_on_fn: Callable[[SeatVehicleData], bool | None]
    turn_on_fn: Callable[[SeatApiClientProtocol, str], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[SeatApiClientProtocol, str], Coroutine[Any, Any, None]]
    available_fn: Callable[[SeatVehicleData], bool] = lambda _: True


SWITCH_DESCRIPTIONS: tuple[SeatSwitchEntityDescription, ...] = (
    SeatSwitchEntityDescription(
        key="charging",
        translation_key="charging",
        name="Charging",
        icon="mdi:ev-station",
        is_on_fn=lambda v: v.charging.state == "charging",
        turn_on_fn=lambda c, vin: c.async_start_charging(vin),
        turn_off_fn=lambda c, vin: c.async_stop_charging(vin),
        available_fn=lambda v: CAP_CHARGING in v.capabilities or v.charging.plug_connected is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Seat switch entities."""
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        for description in SWITCH_DESCRIPTIONS:
            if description.available_fn(vehicle):
                entities.append(SeatConnectSwitchEntity(coordinator, vin, description))

    if entities:
        async_add_entities(entities)


class SeatConnectSwitchEntity(SeatConnectEntity[SeatVehicleData], SwitchEntity):
    """Seat Connect switch entity."""

    entity_description: SeatSwitchEntityDescription

    def __init__(
        self,
        coordinator: "SeatDataUpdateCoordinator",
        vin: str,
        description: SeatSwitchEntityDescription,
    ) -> None:
        """Initialize switch entity."""
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        return self.entity_description.is_on_fn(self._vehicle)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.entity_description.turn_on_fn(self.coordinator.client, self._vin)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.entity_description.turn_off_fn(self.coordinator.client, self._vin)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.entity_description.available_fn(self._vehicle)

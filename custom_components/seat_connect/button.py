"""Button platform for Seat Connect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SeatApiClientProtocol, SeatVehicleData
from .const import DATA_ENTRIES, DOMAIN, CAP_HONK_FLASH
from .entity import SeatConnectEntity

if TYPE_CHECKING:
    from .coordinator import SeatDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SeatButtonEntityDescription(ButtonEntityDescription):
    """Button entity description for Seat Connect."""

    press_fn: Callable[[SeatApiClientProtocol, str], Coroutine[Any, Any, None]]
    available_fn: Callable[[SeatVehicleData], bool] = lambda _: True


BUTTON_DESCRIPTIONS: tuple[SeatButtonEntityDescription, ...] = (
    SeatButtonEntityDescription(
        key="honk_flash",
        translation_key="honk_flash",
        name="Honk and Flash",
        icon="mdi:bullhorn",
        press_fn=lambda c, vin: c.async_honk_flash(vin, honk=True, flash=True),
        available_fn=lambda v: CAP_HONK_FLASH in v.capabilities,
    ),
    SeatButtonEntityDescription(
        key="honk",
        translation_key="honk",
        name="Honk",
        icon="mdi:bullhorn-outline",
        press_fn=lambda c, vin: c.async_honk_flash(vin, honk=True, flash=False),
        available_fn=lambda v: CAP_HONK_FLASH in v.capabilities,
    ),
    SeatButtonEntityDescription(
        key="flash",
        translation_key="flash",
        name="Flash lights",
        icon="mdi:car-light-high",
        press_fn=lambda c, vin: c.async_honk_flash(vin, honk=False, flash=True),
        available_fn=lambda v: CAP_HONK_FLASH in v.capabilities,
    ),
    SeatButtonEntityDescription(
        key="refresh",
        translation_key="refresh",
        name="Force refresh",
        icon="mdi:refresh",
        press_fn=lambda c, vin: c.async_trigger_request(vin),
        available_fn=lambda _: True,  # Always available
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Seat button entities."""
    coordinator: SeatDataUpdateCoordinator = hass.data[DOMAIN][DATA_ENTRIES][
        entry.entry_id
    ].coordinator

    entities = []
    for vin, vehicle in (coordinator.data or {}).items():
        for description in BUTTON_DESCRIPTIONS:
            if description.available_fn(vehicle):
                entities.append(SeatConnectButtonEntity(coordinator, vin, description))

    if entities:
        async_add_entities(entities)


class SeatConnectButtonEntity(SeatConnectEntity[SeatVehicleData], ButtonEntity):
    """Seat Connect button entity."""

    entity_description: SeatButtonEntityDescription

    def __init__(
        self,
        coordinator: "SeatDataUpdateCoordinator",
        vin: str,
        description: SeatButtonEntityDescription,
    ) -> None:
        """Initialize button entity."""
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Press the button."""
        await self.entity_description.press_fn(self.coordinator.client, self._vin)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.entity_description.available_fn(self._vehicle)

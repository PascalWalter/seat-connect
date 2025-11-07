"""Entity helpers for Seat Connect."""

from __future__ import annotations

from typing import Generic, TypeVar

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SeatVehicleData
from .const import DOMAIN
from .coordinator import SeatDataUpdateCoordinator

T = TypeVar("T", bound=SeatVehicleData)


class SeatConnectEntity(CoordinatorEntity[SeatDataUpdateCoordinator], Generic[T]):
    """Base entity for Seat Connect devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SeatDataUpdateCoordinator, vin: str, key: str) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._key = key
        self._attr_unique_id = f"{vin}_{key}"

    @property
    def _vehicle(self) -> SeatVehicleData:
        data = self.coordinator.data or {}
        vehicle = data.get(self._vin)
        if not vehicle:
            raise RuntimeError(f"Vehicle {self._vin} missing from coordinator data")
        return vehicle

    @property
    def device_info(self) -> DeviceInfo:
        vehicle = self._vehicle
        return DeviceInfo(
            identifiers={(DOMAIN, self._vin)},
            manufacturer="SEAT",
            name=vehicle.name,
            model=vehicle.model,
        )

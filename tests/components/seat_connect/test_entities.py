"""Entity tests for Seat Connect."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.components.climate import HVACMode

from custom_components.seat_connect.binary_sensor import (
    BINARY_SENSORS,
    SeatConnectBinarySensorEntity,
)
from custom_components.seat_connect.climate import SeatConnectClimateEntity
from custom_components.seat_connect.coordinator import SeatDataUpdateCoordinator
from custom_components.seat_connect.lock import SeatConnectLockEntity
from custom_components.seat_connect.sensor import (
    SENSOR_DESCRIPTIONS,
    SeatConnectSensorEntity,
)

VIN = "VIN123"


@pytest.fixture
async def coordinator(hass, vehicle_data):
    client = AsyncMock()
    client.async_get_vehicle_data.return_value = vehicle_data
    client.async_lock_vehicle = AsyncMock()
    client.async_unlock_vehicle = AsyncMock()
    client.async_start_climate = AsyncMock()
    client.async_stop_climate = AsyncMock()

    coordinator = SeatDataUpdateCoordinator(
        hass,
        client=client,
        entry_id="123",
        update_interval=timedelta(seconds=60),
    )
    await coordinator.async_config_entry_first_refresh()
    return coordinator


def test_sensor_reports_soc(coordinator):
    sensor = SeatConnectSensorEntity(coordinator, VIN, SENSOR_DESCRIPTIONS[0])
    assert sensor.native_value == 80


def test_binary_sensor_reports_plug_state(coordinator):
    entity = SeatConnectBinarySensorEntity(coordinator, VIN, BINARY_SENSORS[0])
    assert entity.is_on is True


@pytest.mark.asyncio
async def test_lock_entity_triggers_client_commands(coordinator):
    entity = SeatConnectLockEntity(coordinator, VIN)
    await entity.async_lock()
    coordinator.client.async_lock_vehicle.assert_awaited_with(VIN)
    await entity.async_unlock()
    coordinator.client.async_unlock_vehicle.assert_awaited_with(VIN)


@pytest.mark.asyncio
async def test_climate_entity_starts_preconditioning(coordinator):
    entity = SeatConnectClimateEntity(coordinator, VIN)
    assert entity.hvac_mode == HVACMode.OFF
    await entity.async_set_hvac_mode(HVACMode.HEAT)
    coordinator.client.async_start_climate.assert_awaited_with(VIN)

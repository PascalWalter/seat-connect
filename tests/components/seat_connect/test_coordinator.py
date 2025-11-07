"""Coordinator tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.seat_connect.coordinator import SeatDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_fetches_vehicle_data(hass, vehicle_data, config_entry):
    config_entry.add_to_hass(hass)
    client = AsyncMock()
    client.async_get_vehicle_data.return_value = vehicle_data

    coordinator = SeatDataUpdateCoordinator(
        hass,
        client=client,
        entry=config_entry,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_refresh()

    assert coordinator.data == vehicle_data
    client.async_get_vehicle_data.assert_awaited()

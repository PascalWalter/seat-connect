"""Coordinator tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.seat_connect.coordinator import SeatDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_fetches_vehicle_data(hass, vehicle_data):
    client = AsyncMock()
    client.async_get_vehicle_data.return_value = vehicle_data

    coordinator = SeatDataUpdateCoordinator(
        hass,
        client=client,
        entry_id="123",
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data == vehicle_data
    client.async_get_vehicle_data.assert_awaited()

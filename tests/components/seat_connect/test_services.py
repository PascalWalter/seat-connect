"""Tests for Seat Connect services."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.seat_connect import async_setup_entry
from custom_components.seat_connect.const import (
    DATA_ENTRIES,
    DOMAIN,
    SERVICE_LOCK,
    SERVICE_VIN,
)

VIN = "VIN123"


@pytest.mark.asyncio
async def test_lock_service_invokes_api(hass, config_entry, vehicle_data):
    config_entry.add_to_hass(hass)
    mock_client = AsyncMock()
    mock_client.async_get_vehicle_data.return_value = vehicle_data

    hass.config_entries.async_forward_entry_setups = AsyncMock()

    impl_mock = AsyncMock()
    get_impl_mock = AsyncMock(return_value=impl_mock)
    oauth_session = AsyncMock()

    with (
        patch("custom_components.seat_connect.__init__.SeatApiClient", return_value=mock_client),
        patch(
            "custom_components.seat_connect.__init__.config_entry_oauth2_flow.async_get_config_entry_implementation",
            get_impl_mock,
        ),
        patch(
            "custom_components.seat_connect.__init__.config_entry_oauth2_flow.OAuth2Session",
            return_value=oauth_session,
        ),
        patch(
            "custom_components.seat_connect.coordinator.SeatDataUpdateCoordinator.async_config_entry_first_refresh",
            AsyncMock(),
        ),
    ):
        assert await async_setup_entry(hass, config_entry)

    runtime = hass.data[DOMAIN][DATA_ENTRIES][config_entry.entry_id]
    runtime.client = mock_client
    runtime.coordinator.client = mock_client
    runtime.coordinator.async_request_refresh = AsyncMock()
    runtime.coordinator.data = vehicle_data

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOCK,
        {SERVICE_VIN: VIN},
        blocking=True,
    )

    mock_client.async_lock_vehicle.assert_awaited_with(VIN)


@pytest.mark.asyncio
async def test_service_raises_for_unknown_vin(hass, config_entry, vehicle_data):
    config_entry.add_to_hass(hass)
    mock_client = AsyncMock()
    mock_client.async_get_vehicle_data.return_value = vehicle_data

    hass.config_entries.async_forward_entry_setups = AsyncMock()

    impl_mock = AsyncMock()
    get_impl_mock = AsyncMock(return_value=impl_mock)
    oauth_session = AsyncMock()

    with (
        patch("custom_components.seat_connect.__init__.SeatApiClient", return_value=mock_client),
        patch(
            "custom_components.seat_connect.__init__.config_entry_oauth2_flow.async_get_config_entry_implementation",
            get_impl_mock,
        ),
        patch(
            "custom_components.seat_connect.__init__.config_entry_oauth2_flow.OAuth2Session",
            return_value=oauth_session,
        ),
        patch(
            "custom_components.seat_connect.coordinator.SeatDataUpdateCoordinator.async_config_entry_first_refresh",
            AsyncMock(),
        ),
    ):
        assert await async_setup_entry(hass, config_entry)

    runtime = hass.data[DOMAIN][DATA_ENTRIES][config_entry.entry_id]
    runtime.client = mock_client
    runtime.coordinator.client = mock_client
    runtime.coordinator.async_request_refresh = AsyncMock()
    runtime.coordinator.data = vehicle_data

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LOCK,
            {SERVICE_VIN: "UNKNOWN"},
            blocking=True,
        )

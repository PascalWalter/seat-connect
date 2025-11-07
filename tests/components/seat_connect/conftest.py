"""Common fixtures for Seat Connect tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.seat_connect.api import SeatVehicleData
from custom_components.seat_connect.const import DOMAIN


@pytest.fixture
def vehicle_data() -> dict[str, SeatVehicleData]:
    return {
        "VIN123": SeatVehicleData(
            vin="VIN123",
            name="Born",
            model="Born",
            battery_soc=80,
            battery_range_km=360,
            charging_power_kw=7.2,
            charging_state="charging",
            plug_connected=True,
            doors_closed=True,
            windows_closed=True,
            is_locked=False,
            climate_active=False,
            capabilities={"CLIMATE"},
        )
    }


@pytest.fixture
def config_entry() -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-123",
        data={"token": {"access_token": "token", "refresh_token": "refresh"}},
        options={}
    )
    return entry

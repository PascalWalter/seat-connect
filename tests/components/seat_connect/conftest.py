"""Common fixtures for Seat Connect tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.seat_connect.api import (
    SeatChargingStatus,
    SeatClimatisationStatus,
    SeatVehicleData,
    SeatVehicleStatus,
)
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
            charging=SeatChargingStatus(
                power_kw=7.2,
                state="charging",
                plug_connected=True,
            ),
            status=SeatVehicleStatus(
                door_front_left_open=False,
                door_front_right_open=False,
                door_rear_left_open=False,
                door_rear_right_open=False,
                trunk_open=False,
                hood_open=False,
                window_front_left_open=False,
                window_front_right_open=False,
                window_rear_left_open=False,
                window_rear_right_open=False,
            ),
            is_locked=False,
            climatisation=SeatClimatisationStatus(active=False),
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

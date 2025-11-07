"""Tests for the Seat Connect config and options flow."""

from __future__ import annotations

from homeassistant.data_entry_flow import FlowResultType

from custom_components.seat_connect.config_flow import (
    SeatConnectOptionsFlowHandler,
    _extract_unique_id,
)
from custom_components.seat_connect.const import CONF_UPDATE_INTERVAL, MIN_UPDATE_INTERVAL


async def test_options_flow_allows_updating_interval(hass, config_entry):
    """Ensure the options flow updates the polling interval."""

    config_entry.add_to_hass(hass)
    flow = SeatConnectOptionsFlowHandler(config_entry)

    result = await flow.async_step_init()
    assert result["type"] == FlowResultType.FORM

    result = await flow.async_step_init({CONF_UPDATE_INTERVAL: MIN_UPDATE_INTERVAL})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UPDATE_INTERVAL] == MIN_UPDATE_INTERVAL


def test_extract_unique_id_prefers_userinfo():
    token = {"userinfo": {"sub": "abc"}}
    assert _extract_unique_id({"token": token}) == "abc"


def test_extract_unique_id_falls_back_to_sub():
    token = {"sub": "user"}
    assert _extract_unique_id({"token": token}) == "user"

"""Config and options flow for Seat Connect."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)


class SeatConnectFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle the OAuth2 config flow."""

    DOMAIN = DOMAIN

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        unique_id = _extract_unique_id(data)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        title = data.get("title") or "SEAT Connect"
        return self.async_create_entry(title=title, data=data)

class SeatConnectOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL]})

        default = self._entry.options.get(
            CONF_UPDATE_INTERVAL, int(DEFAULT_UPDATE_INTERVAL.total_seconds())
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL, default=default): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def _extract_unique_id(data: Mapping[str, Any]) -> str:
    token_data = data.get("token", {})
    unique_keys = ("user_id", "sub")
    for key in unique_keys:
        value = token_data.get(key)
        if isinstance(value, str):
            return value
    profile = token_data.get("userinfo", {})
    for key in ("sub", "id"):
        value = profile.get(key)
        if isinstance(value, str):
            return value
    return data.get("implementation_id", "seat_connect_account")

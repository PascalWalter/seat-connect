"""Config and options flow for Seat Connect."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import ConfigFlowResult
else:  # pragma: no cover - runtime fallback for older HA versions
    ConfigFlowResult = FlowResult  # type: ignore[misc, assignment]

from .api import SeatApiClient, SeatApiAuthError, SeatApiError, SeatApiCommunicationError
from .const import (
    CONF_SPIN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class SeatConnectFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Seat Connect."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._spin: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiated setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._spin = user_input.get(CONF_SPIN)

            # Validate credentials
            try:
                session = async_get_clientsession(self.hass)
                client = SeatApiClient(
                    session=session,
                    username=self._username,
                    password=self._password,
                    spin=self._spin,
                )

                _LOGGER.debug("Attempting to authenticate with Seat Connect API")

                # Try to authenticate and get vehicle data
                vehicles = await client.async_get_vehicle_data()

                if not vehicles:
                    _LOGGER.warning("Authentication successful but no vehicles found")
                    errors["base"] = "no_vehicles"
                else:
                    _LOGGER.info("Found %d vehicle(s)", len(vehicles))
                    # Create unique ID from username
                    await self.async_set_unique_id(self._username.lower())
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"SEAT Connect ({self._username})",
                        data={
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                            CONF_SPIN: self._spin,
                        },
                    )

            except SeatApiAuthError as err:
                _LOGGER.error("Authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except SeatApiCommunicationError as err:
                _LOGGER.error("Communication error: %s", err)
                errors["base"] = "cannot_connect"
            except SeatApiError as err:
                _LOGGER.error("API error: %s", err)
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during setup: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_SPIN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "docs_url": "https://www.seat.de/service-zubehoer/connect"
            },
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth flow."""
        self._username = entry_data.get(CONF_USERNAME)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._password = user_input[CONF_PASSWORD]
            self._spin = user_input.get(CONF_SPIN)

            try:
                session = async_get_clientsession(self.hass)
                client = SeatApiClient(
                    session=session,
                    username=self._username,
                    password=self._password,
                    spin=self._spin,
                )

                await client.async_get_vehicle_data()

                # Update the config entry
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                            CONF_SPIN: self._spin,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            except SeatApiAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_SPIN): str,
                }
            ),
            errors=errors,
            description_placeholders={"username": self._username or ""},
        )


class SeatConnectOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return cast(
                FlowResult,
                self.async_create_entry(
                    data={
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                        CONF_SPIN: user_input.get(CONF_SPIN, self._entry.data.get(CONF_SPIN)),
                    }
                ),
            )

        default_interval = self._entry.options.get(
            CONF_UPDATE_INTERVAL, int(DEFAULT_UPDATE_INTERVAL.total_seconds())
        )
        default_spin = self._entry.options.get(CONF_SPIN) or self._entry.data.get(CONF_SPIN, "")

        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL, default=default_interval): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Optional(CONF_SPIN, default=default_spin): str,
            }
        )
        return cast(FlowResult, self.async_show_form(step_id="init", data_schema=schema))


def _extract_unique_id(data: Mapping[str, Any]) -> str:
    token_data = cast(Mapping[str, Any], data.get("token", {}))
    unique_keys = ("user_id", "sub")
    for key in unique_keys:
        value = token_data.get(key)
        if isinstance(value, str):
            return value
    profile = cast(Mapping[str, Any], token_data.get("userinfo", {}))
    for key in ("sub", "id"):
        value = profile.get(key)
        if isinstance(value, str):
            return value
    fallback = data.get("implementation_id", "seat_connect_account")
    if isinstance(fallback, str):
        return fallback
    return "seat_connect_account"

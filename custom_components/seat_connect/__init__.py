"""The SEAT Connect integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import SeatApiClient, SeatApiClientProtocol
from .config_flow import SeatConnectOptionsFlowHandler
from .const import (
    CONF_SPIN,
    CONF_UPDATE_INTERVAL,
    DATA_ENTRIES,
    DATA_SERVICES_REGISTERED,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_HONK,
    SERVICE_FLASH,
    SERVICE_LOCK,
    SERVICE_SET_CHARGE_CURRENT,
    SERVICE_SET_CHARGE_LIMIT,
    SERVICE_START_CHARGING,
    SERVICE_START_CLIMATE,
    SERVICE_STOP_CHARGING,
    SERVICE_STOP_CLIMATE,
    SERVICE_TRIGGER_REQUEST,
    SERVICE_UNLOCK,
    SERVICE_VIN,
    SERVICE_TARGET_SOC,
    SERVICE_CHARGE_CURRENT,
)
from .coordinator import SeatDataUpdateCoordinator


@dataclass(slots=True)
class SeatConnectRuntimeData:
    """Container for runtime objects."""

    client: SeatApiClientProtocol
    coordinator: SeatDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML (unused)."""

    store = hass.data.setdefault(DOMAIN, {})
    store.setdefault(DATA_ENTRIES, {})
    store.setdefault(DATA_SERVICES_REGISTERED, False)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configuration entry."""

    store = hass.data.setdefault(DOMAIN, {})
    store.setdefault(DATA_ENTRIES, {})
    store.setdefault(DATA_SERVICES_REGISTERED, False)

    session = async_get_clientsession(hass)

    # Check if using OAuth or username/password authentication
    if "auth_implementation" in entry.data:
        # OAuth2 flow
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
        oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
        client = SeatApiClient(
            session=session,
            oauth_session=oauth_session,
            spin=entry.data.get(CONF_SPIN),
        )
    else:
        # Username/password authentication
        client = SeatApiClient(
            session=session,
            username=entry.data.get(CONF_USERNAME),
            password=entry.data.get(CONF_PASSWORD),
            spin=entry.data.get(CONF_SPIN),
        )

    update_interval = _async_get_update_interval(entry)
    coordinator = SeatDataUpdateCoordinator(
        hass,
        client=client,
        entry=entry,
        update_interval=update_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id] = SeatConnectRuntimeData(
        client=client, coordinator=coordinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configuration entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    hass.data[DOMAIN][DATA_ENTRIES].pop(entry.entry_id, None)
    if not hass.data[DOMAIN][DATA_ENTRIES]:
        await _async_unregister_services(hass)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""

    runtime = hass.data[DOMAIN][DATA_ENTRIES].get(entry.entry_id)
    if not runtime:
        return
    runtime.coordinator.update_interval = _async_get_update_interval(entry)
    await runtime.coordinator.async_request_refresh()


def _async_get_update_interval(entry: ConfigEntry) -> timedelta:
    seconds = entry.options.get(CONF_UPDATE_INTERVAL)
    if seconds is None:
        return DEFAULT_UPDATE_INTERVAL
    return timedelta(seconds=seconds)


async def _async_register_services(hass: HomeAssistant) -> None:
    data = hass.data[DOMAIN]
    if data.get(DATA_SERVICES_REGISTERED):
        return

    vin_schema = vol.Schema({vol.Required(SERVICE_VIN): cv.string})

    charge_limit_schema = vol.Schema({
        vol.Required(SERVICE_VIN): cv.string,
        vol.Required(SERVICE_TARGET_SOC): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })

    charge_current_schema = vol.Schema({
        vol.Required(SERVICE_VIN): cv.string,
        vol.Required(SERVICE_CHARGE_CURRENT): vol.In(["reduced", "max"]),
    })

    async def _async_call_service(call: ServiceCall, action: str) -> None:
        vin = call.data[SERVICE_VIN]
        runtime = _async_get_runtime_for_vin(hass, vin)
        if not runtime:
            raise HomeAssistantError(f"Unknown VIN: {vin}")

        if action == SERVICE_LOCK:
            await runtime.client.async_lock_vehicle(vin)
        elif action == SERVICE_UNLOCK:
            await runtime.client.async_unlock_vehicle(vin)
        elif action == SERVICE_START_CLIMATE:
            await runtime.client.async_start_climate(vin)
        elif action == SERVICE_STOP_CLIMATE:
            await runtime.client.async_stop_climate(vin)
        elif action == SERVICE_START_CHARGING:
            await runtime.client.async_start_charging(vin)
        elif action == SERVICE_STOP_CHARGING:
            await runtime.client.async_stop_charging(vin)
        elif action == SERVICE_HONK:
            await runtime.client.async_honk_flash(vin, honk=True, flash=False)
        elif action == SERVICE_FLASH:
            await runtime.client.async_honk_flash(vin, honk=False, flash=True)
        elif action == SERVICE_TRIGGER_REQUEST:
            await runtime.client.async_trigger_request(vin)
        elif action == SERVICE_SET_CHARGE_LIMIT:
            target_soc = call.data[SERVICE_TARGET_SOC]
            await runtime.client.async_set_charge_limit(vin, target_soc)
        elif action == SERVICE_SET_CHARGE_CURRENT:
            current = call.data[SERVICE_CHARGE_CURRENT]
            await runtime.client.async_set_charge_current(vin, current)

        await runtime.coordinator.async_request_refresh()

    async def _handle_lock(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_LOCK)

    async def _handle_unlock(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_UNLOCK)

    async def _handle_start_climate(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_START_CLIMATE)

    async def _handle_stop_climate(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_STOP_CLIMATE)

    async def _handle_start_charging(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_START_CHARGING)

    async def _handle_stop_charging(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_STOP_CHARGING)

    async def _handle_honk(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_HONK)

    async def _handle_flash(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_FLASH)

    async def _handle_trigger_request(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_TRIGGER_REQUEST)

    async def _handle_set_charge_limit(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_SET_CHARGE_LIMIT)

    async def _handle_set_charge_current(call: ServiceCall) -> None:
        await _async_call_service(call, SERVICE_SET_CHARGE_CURRENT)

    hass.services.async_register(DOMAIN, SERVICE_LOCK, _handle_lock, schema=vin_schema)
    hass.services.async_register(DOMAIN, SERVICE_UNLOCK, _handle_unlock, schema=vin_schema)
    hass.services.async_register(
        DOMAIN, SERVICE_START_CLIMATE, _handle_start_climate, schema=vin_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_CLIMATE, _handle_stop_climate, schema=vin_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_START_CHARGING, _handle_start_charging, schema=vin_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_CHARGING, _handle_stop_charging, schema=vin_schema
    )
    hass.services.async_register(DOMAIN, SERVICE_HONK, _handle_honk, schema=vin_schema)
    hass.services.async_register(DOMAIN, SERVICE_FLASH, _handle_flash, schema=vin_schema)
    hass.services.async_register(
        DOMAIN, SERVICE_TRIGGER_REQUEST, _handle_trigger_request, schema=vin_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_CHARGE_LIMIT, _handle_set_charge_limit, schema=charge_limit_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_CHARGE_CURRENT, _handle_set_charge_current, schema=charge_current_schema
    )

    data[DATA_SERVICES_REGISTERED] = True


async def _async_unregister_services(hass: HomeAssistant) -> None:
    data = hass.data.get(DOMAIN)
    if not data or not data.get(DATA_SERVICES_REGISTERED):
        return

    services = [
        SERVICE_LOCK,
        SERVICE_UNLOCK,
        SERVICE_START_CLIMATE,
        SERVICE_STOP_CLIMATE,
        SERVICE_START_CHARGING,
        SERVICE_STOP_CHARGING,
        SERVICE_HONK,
        SERVICE_FLASH,
        SERVICE_TRIGGER_REQUEST,
        SERVICE_SET_CHARGE_LIMIT,
        SERVICE_SET_CHARGE_CURRENT,
    ]

    for service in services:
        hass.services.async_remove(DOMAIN, service)

    data[DATA_SERVICES_REGISTERED] = False


def _async_get_runtime_for_vin(hass: HomeAssistant, vin: str) -> SeatConnectRuntimeData:
    entries: dict[str, SeatConnectRuntimeData] = hass.data[DOMAIN][DATA_ENTRIES]
    for runtime in entries.values():
        if runtime.coordinator.data and vin in runtime.coordinator.data:
            return runtime
    raise HomeAssistantError(f"No runtime loaded for VIN {vin}")


async def async_get_options_flow(entry: ConfigEntry) -> Any:
    """Return the options flow handler."""

    return SeatConnectOptionsFlowHandler(entry)

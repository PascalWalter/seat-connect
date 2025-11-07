"""Constants for the SEAT Connect integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "seat_connect"
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.LOCK,
    Platform.CLIMATE,
]

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=90)
CONF_UPDATE_INTERVAL = "update_interval"
MIN_UPDATE_INTERVAL = 30
MAX_UPDATE_INTERVAL = 600
DATA_ENTRIES = "entries"
DATA_SERVICES_REGISTERED = "services_registered"

API_BASE_URL = "https://my-seat.apps.emea.vwapps.io"
AUTH_AUTHORIZE_URL = "https://identity.vwgroup.io/signin-service/v1/authorize"
AUTH_TOKEN_URL = "https://identity.vwgroup.io/signin-service/v1/token"

SERVICE_LOCK = "lock"
SERVICE_UNLOCK = "unlock"
SERVICE_START_CLIMATE = "start_climate"
SERVICE_STOP_CLIMATE = "stop_climate"

SERVICE_VIN = "vin"

LOGGER_NAME = "custom_components.seat_connect"

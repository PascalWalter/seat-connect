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
    Platform.DEVICE_TRACKER,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=90)
CONF_UPDATE_INTERVAL = "update_interval"
CONF_SPIN = "spin"  # S-PIN for vehicle operations
MIN_UPDATE_INTERVAL = 30
MAX_UPDATE_INTERVAL = 600
DATA_ENTRIES = "entries"
DATA_SERVICES_REGISTERED = "services_registered"

# Seat Connect API Endpoints (VW Group ecosystem)
API_BASE_URL = "https://msg.volkswagen.de/fs-car"
API_HOMEREGION_URL = "https://mal-1a.prd.ece.vwg-connect.com/api"
API_VEHICLE_URL = "https://msg.volkswagen.de"

# OAuth2 Configuration for Seat Connect
# Uses VW Group Identity Provider with Seat-specific client
AUTH_BASE_URL = "https://identity.vwgroup.io"
AUTH_AUTHORIZE_URL = f"{AUTH_BASE_URL}/oidc/v1/authorize"
AUTH_TOKEN_URL = f"{AUTH_BASE_URL}/oidc/v1/token"
AUTH_REVOKE_URL = f"{AUTH_BASE_URL}/oidc/v1/revoke"

# Seat Connect App Client Configuration
CLIENT_ID = "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com"
USER_AGENT = "SEATConnect/2.11.0 (Android)"
X_APP_NAME = "SEATConnect"
X_APP_VERSION = "2.11.0"

# API Scopes
SCOPES = [
    "openid",
    "profile",
    "address",
    "phone",
    "email",
    "birthdate",
    "nationalIdentifier",
    "mbb",
    "cars",
    "dealers",
    "vin",
]

# Service Actions
SERVICE_LOCK = "lock"
SERVICE_UNLOCK = "unlock"
SERVICE_START_CLIMATE = "start_climate"
SERVICE_STOP_CLIMATE = "stop_climate"
SERVICE_HONK = "honk"
SERVICE_FLASH = "flash"
SERVICE_START_CHARGING = "start_charging"
SERVICE_STOP_CHARGING = "stop_charging"
SERVICE_SET_CHARGE_LIMIT = "set_charge_limit"
SERVICE_SET_CHARGE_CURRENT = "set_charge_current"
SERVICE_REFRESH = "refresh"
SERVICE_TRIGGER_REQUEST = "trigger_request"

SERVICE_VIN = "vin"
SERVICE_TARGET_SOC = "target_soc"
SERVICE_CHARGE_CURRENT = "charge_current"

# Vehicle capabilities
CAP_CLIMATISATION = "CLIMATISATION"
CAP_CHARGING = "CHARGING"
CAP_PARKING_POSITION = "PARKING_POSITION"
CAP_HONK_FLASH = "HONK_AND_FLASH"
CAP_LOCK_UNLOCK = "LOCK_UNLOCK"
CAP_WINDOW_HEATING = "WINDOW_HEATING"
CAP_AUXILIARY_HEATING = "AUXILIARY_HEATING"
CAP_STATE = "STATE"
CAP_TRIP_STATISTICS = "TRIP_STATISTICS"

# Charging states
CHARGING_STATE_OFF = "off"
CHARGING_STATE_READY = "readyForCharging"
CHARGING_STATE_CHARGING = "charging"
CHARGING_STATE_ERROR = "error"
CHARGING_STATE_CONSERVATION = "conservation"

LOGGER_NAME = "custom_components.seat_connect"

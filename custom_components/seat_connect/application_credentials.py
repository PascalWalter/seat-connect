"""Application Credentials for Seat Connect."""

from __future__ import annotations

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.helpers import config_entry_oauth2_flow

from .const import AUTH_AUTHORIZE_URL, AUTH_TOKEN_URL, DOMAIN


async def async_get_authorization_server(_hass):
    """Return the Seat Connect authorization server metadata."""

    return AuthorizationServer(
        authorize_url=AUTH_AUTHORIZE_URL,
        token_url=AUTH_TOKEN_URL,
    )


async def async_get_auth_implementation(
    hass, domain, client_id, client_secret, **kwargs
):
    """Return the OAuth2 implementation bound to application credentials."""

    return config_entry_oauth2_flow.LocalOAuth2Implementation(
        hass,
        DOMAIN,
        client_id,
        client_secret,
        AUTH_AUTHORIZE_URL,
        AUTH_TOKEN_URL,
    )

"""The Husqvarna Automower integration."""
import logging

import voluptuous as vol

import aioautomower
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.helpers.typing import ConfigType

from . import config_flow
from .const import (
    DOMAIN,
    HUSQVARNA_URL,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): vol.All(str, vol.Length(min=36, max=36)),
                vol.Required(CONF_CLIENT_SECRET): vol.All(
                    str, vol.Length(min=36, max=36)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Husqvarna Automower component for Authorization Code Grant."""

    if DOMAIN not in config:
        return True

    if CONF_CLIENT_ID in config[DOMAIN]:
        config_flow.HusqvarnaConfigFlowHandler.async_register_implementation(
            hass,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                hass,
                DOMAIN,
                config[DOMAIN][CONF_CLIENT_ID],
                config[DOMAIN][CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )
        conf = config.get(DOMAIN, {})
        hass.data[DOMAIN] = conf

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    api_key = entry.unique_id
    access_token = entry.data.get(CONF_TOKEN)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    session = aioautomower.AutomowerSession(api_key, access_token)
    session.register_token_callback(
        lambda token: hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_TOKEN: token,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            },
        )
    )

    try:
        await session.connect()
    except Exception:
        # If we haven't used the refresh_token (ie. been offline) for 10 days,
        # we need to login using username and password in the config flow again.
        username = entry.data.get(CONF_USERNAME)
        password = entry.data.get(CONF_PASSWORD)
        if not (username and password):
            raise ConfigEntryAuthFailed from Exception
        if username and password:
            get_token = aioautomower.GetAccessToken(
                api_key,
                username,
                password,
            )
            access_token = await get_token.async_get_access_token()
            _LOGGER.debug("access_token: %s", access_token)
            hass.config_entries.async_update_entry(
                entry,
                data={
                    CONF_TOKEN: access_token,
                    CONF_USERNAME: username,
                    CONF_PASSWORD: password,
                },
            )
            try:
                session = aioautomower.AutomowerSession(api_key, access_token)
                await session.connect()
            except Exception:
                raise ConfigEntryAuthFailed from Exception

    if "amc:api" not in access_token["scope"]:
        raise ConfigEntryAuthFailed(
            f"Your API-Key is not compatible to websocket, please renew it on {HUSQVARNA_URL}"
        )

    hass.data[DOMAIN][entry.entry_id] = session
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unload of an entry."""
    session = hass.data[DOMAIN][entry.entry_id]
    await session.close()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

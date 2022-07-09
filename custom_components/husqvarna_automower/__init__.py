"""The Husqvarna Automower integration."""
import logging

import voluptuous as vol

import aioautomower
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
    DEFAULT_IMPORT_NAME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_TOKEN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.typing import ConfigType

from . import config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, PLATFORMS, STARTUP_MESSAGE

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
        await async_import_client_credential(
            hass,
            DOMAIN,
            ClientCredential(
                config[DOMAIN][CONF_CLIENT_ID],
                config[DOMAIN][CONF_CLIENT_SECRET],
                DEFAULT_IMPORT_NAME,
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
    try:
        hass.data.get(DOMAIN)[CONF_CLIENT_ID] and hass.data.get(DOMAIN)[
            CONF_CLIENT_SECRET
        ]
    except KeyError:
        _LOGGER.warning(
            "Log-in with password/username is depracated. Please set-up client_id and client_secret in your configuration.yaml"
        )
    session = aioautomower.AutomowerSession(api_key, access_token)
    session.register_token_callback(
        lambda token: hass.config_entries.async_update_entry(
            entry,
            data={CONF_TOKEN: token},
        )
    )

    try:
        await session.connect()
    except Exception:
        # If we haven't used the refresh_token (ie. been offline) for 10 days,
        # we need to login using username and password in the config flow again.
        raise ConfigEntryAuthFailed from Exception

    hass.data[DOMAIN][entry.entry_id] = session
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
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


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.CAMERA]
    )
    if unload_ok:
        hass.config_entries.async_setup_platforms(entry, [Platform.CAMERA])
        entry.async_on_unload(entry.add_update_listener(update_listener))

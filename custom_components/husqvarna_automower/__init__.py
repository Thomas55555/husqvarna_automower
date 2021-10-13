"""The Husqvarna Automower integration."""
import logging

import aioautomower

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, PLATFORMS, STARTUP_MESSAGE

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:

        entry.title = entry.data.get(CONF_API_KEY)
        username = entry.data.get(CONF_USERNAME)
        password = entry.data.get(CONF_PASSWORD)
        api_key = entry.data.get(CONF_API_KEY)

        get_token = aioautomower.GetAccessToken(api_key, username, password)
        access_token = await get_token.async_get_access_token()
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_TOKEN: access_token,
            },
        )
        entry.version = 2

        _LOGGER.debug("Migration to version %s successful", entry.version)

        return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    api_key = entry.unique_id
    access_token = entry.data.get(CONF_TOKEN)

    session = aioautomower.AutomowerSession(api_key, access_token)
    session.register_token_callback(
        lambda token: hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_TOKEN: token,
            },
        )
    )

    try:
        await session.connect()
    except Exception as e:
        # If we haven't used the refresh_token (ie. been offline) for 10 days,
        # we need to login using username and password in the config flow again.
        raise ConfigEntryAuthFailed(e)

    if "amc:api" not in access_token["scope"]:
        raise ConfigEntryAuthFailed(
            "Your API-Key is not compatible to websocket, please renew it on https://developer.husqvarnagroup.cloud/"
        )

    hass.data[DOMAIN][entry.entry_id] = session
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle unload of an entry."""
    session = hass.data[DOMAIN].pop(entry.entry_id)
    try:
        await session.invalidate_token()
    except Exception as exception:
        _LOGGER.warning("Failed to invalidate token: %s", exception)
        pass

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""

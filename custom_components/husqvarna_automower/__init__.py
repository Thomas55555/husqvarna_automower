"""The Husqvarna Automower integration."""
import logging

import voluptuous as vol

import aioautomower
from homeassistant.components.application_credentials import DATA_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, STARTUP_MESSAGE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)
    api_key = None
    ap_storage = hass.data.get("application_credentials")[DATA_STORAGE]
    ap_storage_data = ap_storage.__dict__["data"]
    for k in ap_storage_data:
        api_key = ap_storage_data[k]["client_id"]
    access_token = entry.data.get(CONF_TOKEN)
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

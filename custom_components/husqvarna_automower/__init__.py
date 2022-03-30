"""The Husqvarna Automower integration."""
import logging

import aioautomower
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, HUSQVARNA_URL, PLATFORMS, STARTUP_MESSAGE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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
    except Exception:
        # If we haven't used the refresh_token (ie. been offline) for 10 days,
        # we need to login using username and password in the config flow again.
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

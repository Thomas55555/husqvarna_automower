"""The Husqvarna Automower integration."""
import logging

import async_timeout
import voluptuous as vol

import aioautomower
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_TOKEN, Platform
from asyncio.exceptions import TimeoutError
from homeassistant.components.application_credentials import DATA_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, PLATFORMS, STARTUP_MESSAGE, DISABLE_LE

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
    low_energy = not entry.options.get(DISABLE_LE)
    automower_api = aioautomower.AutomowerSession(api_key, access_token, low_energy)
    coordinator = AutomowerCoordinator(hass, api=automower_api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
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
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.CAMERA])
        entry.async_on_unload(entry.add_update_listener(update_listener))


class AutomowerCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, *, api):
        self.session = api
        self.hass = hass


        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        self.session.register_token_callback(
            lambda token: self.hass.config_entries.async_update_entry(
                self.entry,
                data={"auth_implementation": DOMAIN, CONF_TOKEN: token},
            )
        )
        try:
            data = await self.session.connect()
        except TimeoutError as error:
            _LOGGER.debug("Asyncio timeout: %s", error)
            raise ConfigEntryNotReady from error
        except Exception as error:
            _LOGGER.debug("Exception in async_setup_entry: %s", error)
            # If we haven't used the refresh_token (ie. been offline) for 10 days,
            # we need to login using username and password in the config flow again.
            raise ConfigEntryAuthFailed from Exception
        _LOGGER.debug("session:%s", self.session.data)
        return self.session.data

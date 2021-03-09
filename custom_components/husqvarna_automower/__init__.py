import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.husqvarna_automower.const import (
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from husqvarna_automower import GetAccessToken, GetMowerData, RefreshAccessToken

SCAN_INTERVAL = timedelta(seconds=300)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    api_key = entry.data.get(CONF_API_KEY)

    coordinator = AuthenticationUpdateCoordinator(
        hass, username=username, password=password, api_key=api_key
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


class AuthenticationUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, username, password, api_key):
        """Initialize."""
        _LOGGER.info("Inizialising UpdateCoordiantor")
        self.platforms = []
        self.username = username
        self.password = password
        self.api_key = api_key
        self.access_token = None
        self.token_expires_at = 0

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.info("Updating data")
        if (self.access_token is None):
            self.auth_api = GetAccessToken(self.api_key, self.username, self.password)
            _LOGGER.debug("Getting new token, because Null")
            try:
                self.access_token_raw = await self.auth_api.async_get_access_token()
                _LOGGER.debug(f"Acces token raw: {self.access_token_raw}")
                self.access_token = self.access_token_raw["access_token"]
                self.provider = self.access_token_raw["provider"]
                self.token_type = self.access_token_raw["token_type"]
                self.refresh_token = self.access_token_raw["refresh_token"]
                self.token_expires_at = (
                    self.access_token_raw["expires_in"] + time.time()
                )
                _LOGGER.debug(f"Token expires at {self.token_expires_at} UTC")
            except Exception:
                _LOGGER.debug(
                    f"Error message for UpdateFailed: {self.access_token_raw['status']}"
                )
                raise UpdateFailed("Error communicating with API")
        elif self.token_expires_at < time.time():
            self.auth_api = RefreshAccessToken(self.api_key, self.refresh_token)
            _LOGGER.debug("Getting new token, because expired")
            try:
                self.access_token_raw = await self.auth_api.async_refresh_access_token()
                _LOGGER.debug(f"Acces token raw: {self.access_token_raw}")
                self.access_token = self.access_token_raw["access_token"]
                self.refresh_token = self.access_token_raw["refresh_token"]
                self.token_expires_at = (
                    self.access_token_raw["expires_in"] + time.time()
                )
                _LOGGER.debug(f"Token expires at {self.token_expires_at} UTC")
            except Exception:
                _LOGGER.debug(
                    f"Error message for UpdateFailed: {self.access_token_raw['status']}"
                )
                raise UpdateFailed("Error communicating with API")

        self.mower_api = GetMowerData(
            self.api_key, self.access_token, self.provider, self.token_type
        )

        try:
            data = await self.mower_api.async_mower_state()
            data["token"] = self.access_token_raw
            data["api_key"] = self.api_key
            return data
        except Exception as exception:
            raise UpdateFailed(exception)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

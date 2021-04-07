"""The Husqvarna Automower integration."""
import asyncio
import logging
import time
from datetime import timedelta

from aioautomower import (
    DeleteAccessToken,
    GetAccessToken,
    GetMowerData,
    RefreshAccessToken,
    Return,
    TokenError,
    ValidateAccessToken,
)
from aiohttp import ClientError
from async_timeout import timeout

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_registry import async_migrate_entries
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ACCESS_TOKEN_RAW,
    CONF_PROVIDER,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_TYPE,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=300)

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:

        config_entry.title = config_entry.data.get(CONF_API_KEY)
        username = config_entry.data.get(CONF_USERNAME)
        password = config_entry.data.get(CONF_PASSWORD)
        api_key = config_entry.data.get(CONF_API_KEY)

        get_token = GetAccessToken(api_key, username, password)
        access_token_raw = await get_token.async_get_access_token()
        hass.config_entries.async_update_entry(
            config_entry,
            data={
                CONF_TOKEN: access_token_raw,
            },
        )
        config_entry.version = 2

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    api_key = entry.title
    access_token_raw = entry.data.get(CONF_TOKEN)

    coordinator = AuthenticationUpdateCoordinator(
        hass,
        entry,
        api_key=api_key,
        access_token_raw=access_token_raw,
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
    return True


class AuthenticationUpdateCoordinator(DataUpdateCoordinator):
    """Update Coordinator."""

    def __init__(
        self,
        hass,
        entry,
        api_key,
        access_token_raw,
    ):
        """Initialize."""
        _LOGGER.info("Inizialising UpdateCoordiantor")
        self.hass = hass
        self.entry = entry
        self.platforms = []
        self.api_key = api_key
        self.access_token_raw = access_token_raw
        self.mower_api = None
        self.update_config_entry = hass.config_entries
        self.api_refresh_token = RefreshAccessToken(
            self.api_key, self.access_token_raw["refresh_token"]
        )
        self.mower_id = None
        self.payload = None
        self.mower_command = None
        self.token_valid = None
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("Updating mower data")
        if self.access_token_raw["expires_at"] < time.time():
            await self.async_update_token()

        await self.async_validate_token()

        self.mower_api = GetMowerData(
            self.api_key,
            self.access_token_raw["access_token"],
            self.access_token_raw["provider"],
            self.access_token_raw["token_type"],
        )
        try:
            data = await self.mower_api.async_mower_state()
            _LOGGER.debug("Mower data: %s", data)
            return data
        except TimeoutError as exception:
            raise UpdateFailed() from exception

    async def async_update_token(self):
        """Update token via library."""

        _LOGGER.debug("Getting new token, because expired")
        try:
            self.access_token_raw = (
                await self.api_refresh_token.async_refresh_access_token()
            )
        except Exception as exception:
            raise UpdateFailed(exception) from exception

        _LOGGER.debug("Token expires at %i UTC", self.access_token_raw["expires_at"])

        self.update_config_entry.async_update_entry(
            self.entry,
            data={
                CONF_TOKEN: self.access_token_raw,
            },
        )

    async def async_validate_token(self):
        """Validating the token."""

        _LOGGER.debug("Validating the token")
        self.token_valid = ValidateAccessToken(
            self.api_key,
            self.access_token_raw["access_token"],
            self.access_token_raw["provider"],
        )
        try:
            async with timeout(10):
                await self.token_valid.async_validate_access_token()
        except TokenError as error:
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_REAUTH},
                    data=self.entry,
                )
            )
            return False
        except TimeoutError as error:
            raise UpdateFailed(error) from error

    async def async_send_command(self, payload, mower_id):
        """Send command to the mower."""
        self.mower_id = mower_id
        self.payload = payload
        self.mower_command = Return(
            self.api_key,
            self.access_token_raw["access_token"],
            self.access_token_raw["provider"],
            self.access_token_raw["token_type"],
            self.mower_id,
            self.payload,
        )
        try:
            await self.mower_command.async_mower_command()
            await self.async_request_refresh()
        except Exception as exception:
            raise UpdateFailed(exception) from exception


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


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    api_key = entry.title
    access_token_raw = entry.data.get(CONF_TOKEN)
    delete_token = DeleteAccessToken(
        api_key, access_token_raw["provider"], access_token_raw["access_token"]
    )
    try:
        await delete_token.async_delete_access_token()
    except Exception as exception:
        raise UpdateFailed(exception) from exception

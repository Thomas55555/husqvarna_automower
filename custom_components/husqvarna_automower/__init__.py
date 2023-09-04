"""The Husqvarna Automower integration."""
import logging
import os
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError

import aioautomower
from homeassistant.components.application_credentials import DATA_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    async_get_config_entry_implementation,
)
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    GPS_TOP_LEFT,
    GPS_BOTTOM_RIGHT,
    MOWER_IMG_PATH,
    MAP_IMG_PATH,
    MAP_IMG_ROTATION,
    MAP_PATH_COLOR,
    HOME_LOCATION,
)

_LOGGER = logging.getLogger(__name__)


class AutomowerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Husqvarna data."""

    def __init__(self, hass: HomeAssistant, *, entry: ConfigEntry) -> None:
        """Initialize data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        api_key = None
        ap_storage = hass.data.get("application_credentials")[DATA_STORAGE]
        ap_storage_data = ap_storage.__dict__["data"]
        for k in ap_storage_data:
            api_key = ap_storage_data[k]["client_id"]
        access_token = entry.data.get(CONF_TOKEN)
        if not "amc:api" in access_token["scope"]:
            async_create_issue(
                hass,
                DOMAIN,
                "wrong_scope",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="wrong_scope",
            )
        low_energy = False
        self.session = aioautomower.AutomowerSession(api_key, access_token, low_energy)
        self.session.register_token_callback(
            lambda token: hass.config_entries.async_update_entry(
                entry,
                data={"auth_implementation": DOMAIN, CONF_TOKEN: token},
            )
        )

    async def _async_update_data(self) -> None:
        """Fetch data from Husqvarna."""
        try:
            await self.session.connect()
        except AsyncioTimeoutError as error:
            _LOGGER.debug("Asyncio timeout: %s", error)
            raise ConfigEntryNotReady from error
        except Exception as error:
            _LOGGER.debug("Exception in async_setup_entry: %s", error)
            # If we haven't used the refresh_token (ie. been offline) for 10 days,
            # we need to login using username and password in the config flow again.
            raise ConfigEntryAuthFailed from Exception


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)
    coordinator = AutomowerDataUpdateCoordinator(
        hass,
        entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unload of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    try:
        await coordinator.session.close()
    except Exception:
        pass
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:  # Todo: Add test
    """Handle options update."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.IMAGE]
    )
    if unload_ok:
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.IMAGE])
        entry.async_on_unload(entry.add_update_listener(update_listener))


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    if config_entry.version == 2:
        new_options = {**config_entry.options}
        base_path = os.path.dirname(__file__)

        # Update options to match new style
        mower_idx = []
        coordinator = AutomowerDataUpdateCoordinator(
            hass,
            entry=config_entry,
        )
        await coordinator.async_config_entry_first_refresh()
        # pylint: disable=unused-variable
        for idx, ent in enumerate(coordinator.session.data["data"]):
            mower_idx.append(ent["id"])

        for mower_id in mower_idx:
            new_options[mower_id] = {
                "enable_camera": new_options.get("enable_camera", False),
                GPS_TOP_LEFT: new_options.get(GPS_TOP_LEFT, ""),
                GPS_BOTTOM_RIGHT: new_options.get(GPS_BOTTOM_RIGHT, ""),
                MOWER_IMG_PATH: new_options.get(
                    MOWER_IMG_PATH, os.path.join(base_path, "resources/mower.png")
                ),
                MAP_IMG_PATH: new_options.get(
                    MAP_IMG_PATH, os.path.join(base_path, "resources/map_image.png")
                ),
                MAP_IMG_ROTATION: 0,
                MAP_PATH_COLOR: [255, 0, 0],
                HOME_LOCATION: "",
            }

        for opt_key in [
            "enable_camera",
            GPS_TOP_LEFT,
            GPS_BOTTOM_RIGHT,
            MOWER_IMG_PATH,
            MAP_IMG_PATH,
        ]:
            new_options.pop(opt_key, None)

        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, options=new_options)

    if config_entry.version == 3:
        new_options = {**config_entry.options}
        for mwr_id in new_options.keys():
            try:
                enable_img = new_options[mwr_id].pop("enable_camera", None)
                if enable_img:
                    new_options[mwr_id]["enable_image"] = enable_img
            except AttributeError:
                pass

        config_entry.version = 4
        hass.config_entries.async_update_entry(config_entry, options=new_options)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True

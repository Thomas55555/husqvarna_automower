"""
Custom integration to integrate blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/blueprint
"""
import asyncio
from datetime import timedelta
import logging
import requests
import json
from typing import List
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sampleclient.client import Client
from custom_components.husqvarna_automower.api_get_token import GetAccessToken, GetMowerData

from custom_components.husqvarna_automower.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_API_KEY,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

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
    
    ###
    #access_token = coordinator_authentication.data['access_token']
    # provider = coordinator_authentication.data['provider']
    # token_type = coordinator_authentication.data['token_type']
    
    # coordinator_mower = MowerDataUpdateCoordinator(
    #     hass, username=username, password=password
    # )
    # await coordinator_mower.async_refresh()

    # if not coordinator_mower.last_update_success:
    #     raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


# class HusqvarnaApi():

#     def __init__(self, hass, username, password):
     
#         return None


#     async def async_get_data(self):

#         self.auth = requests.post(url=auth_api_url, headers=auth_headers, data=self.auth_data)
#         self.full_auth_respone = json.loads(self.auth.content.decode('utf-8'))

#         if self.auth.status_code == 200:

#             self.mower_headers = {'Authorization': '{0} {1}'.format(self.full_auth_respone['token_type'],self.full_auth_respone['access_token']),
#                             'Authorization-Provider': '{0}'.format(self.full_auth_respone['provider']),
#                             'Content-Type': 'application/vnd.api+json',
#                             'X-Api-Key': '{0}'.format(api_key)}     
            
#             self.mower = requests.get(mower_api_base_url, headers=self.mower_headers)
#             self.full_mower_respone = json.loads(self.mower.content.decode('utf-8'))
#             self.auth_and_mower_respone = self.full_auth_respone
#             self.auth_and_mower_respone['mower_respone'] = self.full_mower_respone
#             self.auth_and_mower_respone['api_status_code'] = self.auth.status_code

#         else:
#             self.auth_and_mower_respone = 0
#             self.auth_and_mower_respone['api_status_code'] = self.auth.status_code

#         return self.auth_and_mower_respone



class AuthenticationUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""


    def __init__(self, hass, username, password, api_key):
        """Initialize."""

        self.platforms = []
        self.username = username
        self.password = password
        self.api_key = api_key
        self.access_token = None
        self.token_expires_at = 0

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)



    async def _async_update_data(self):
        """Update data via library."""
        try:
            self.access_token
        except NameError:
            self.access_token = None
        if self.access_token is None:
            self.auth_api = GetAccessToken(self.api_key, self.username, self.password)
            _LOGGER.info(f"{self.auth_api}")
            self.access_token_raw = await self.auth_api.async_get_access_token()
            _LOGGER.info(f"{self.access_token_raw}")
            self.access_token = self.access_token_raw['access_token']
            self.provider = self.access_token_raw['provider']
            self.token_type = self.access_token_raw['token_type']
            self.token_expires_at = self.access_token_raw['expires_at']


        if self.token_expires_at < time.time():
            self.auth_api = GetAccessToken(self.api_key, self.username, self.password)
            _LOGGER.info(f"{self.auth_api}")
            self.access_token_raw = await self.auth_api.async_get_access_token()
            _LOGGER.info(f"{self.access_token_raw}")
            self.access_token = self.access_token_raw['access_token']
            self.provider = self.access_token_raw['provider']
            self.token_type = self.access_token_raw['token_type']
            self.token_expires_at = self.access_token_raw['expires_at']

        # self.auth_api = GetAccessToken(self.api_key, self.username, self.password)
        # _LOGGER.info(f"{self.auth_api}")
        # self.access_token_raw = await self.auth_api.async_get_access_token()
        # _LOGGER.info(f"{self.access_token_raw}")
        # self.access_token = self.access_token_raw['access_token']
        # self.provider = self.access_token_raw['provider']
        # self.token_type = self.access_token_raw['token_type']
        # self.token_expires_at = self.access_token_raw['expires_at']
        self.mower_api = GetMowerData(self.api_key, self.access_token, self.provider, self.token_type)

        try:
            data = await self.mower_api.async_mower_state()
            data['token'] = self.access_token_raw
            data['api_key'] = self.api_key
            #data = await self.api.async_get_data(self)
            return data
        except Exception as exception:
            raise UpdateFailed(exception)


    # class MowerDataUpdateCoordinator(DataUpdateCoordinator):
    #     """Class to manage fetching data from the API."""


    #     def __init__(self, hass, username, password):
    #         """Initialize."""
    #         self.auth_api = GetAccessToken(api_key, username, password)
    #         self.access_token_raw = self.auth_api.async_get_access_token()
    #         self.access_token = self.access_token_raw['access_token']
    #         self.provider = self.access_token_raw['provider']
    #         self.token_type = self.access_token_raw['token_type']
    #         self.mower_api = GetMowerData(api_key, self.access_token, self.provider, self.token_type)
    #         self.platforms = []

    #         super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)



    #     async def _async_update_data(self):
    #         """Update data via library."""
    #         try:
    #             data = await self.auth_api.async_get_access_token()
    #             #data = await self.api.async_get_data(self)
    #             return data
    #         except Exception as exception:
    #             raise UpdateFailed(exception)



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

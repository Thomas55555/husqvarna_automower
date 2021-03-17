"""Config flow to add the integration via the UI."""
import logging
import time
from collections import OrderedDict

import voluptuous as vol
from aioautomower import GetAccessToken, GetMowerData
from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_TOKEN,
)
from homeassistant.core import callback

from .const import DOMAIN, HUSQVARNA_URL, CONF_PROVIDER, CONF_TOKEN_TYPE, CONF_REFRESH_TOKEN, CONF_TOKEN_EXPIRES_AT, ACCESS_TOKEN_RAW

CONF_ID = "unique_id"

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    """Handle a config flow."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        _LOGGER.debug("""Show the setup form to the user.""")
        errors = {}

        fields = OrderedDict()
        fields[vol.Required(CONF_USERNAME)] = str
        fields[vol.Required(CONF_PASSWORD)] = str
        fields[vol.Required(CONF_API_KEY)] = str

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return await self._show_setup_form()

        errors = {}
        try:
            config_data = await try_connection(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_API_KEY],
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "auth"
            return await self._show_setup_form(errors)

        unique_id = user_input[CONF_API_KEY]
        access_token_raw = None
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Husqvarna Automower Integration",
            data={
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_API_KEY: user_input[CONF_API_KEY],
                CONF_TOKEN: config_data,
            },
        )


async def try_connection(username, password, api_key):
    """Try to connect to Husqvarna with the given inputs."""
    _LOGGER.debug("Trying to connect to Husqvarna")
    auth_api = GetAccessToken(api_key, username, password)
    access_token_raw = await auth_api.async_get_access_token()
    _LOGGER.debug("Access token status: %s", access_token_raw["status"])
    if access_token_raw["status"] == 200:
        _LOGGER.debug("Connected with the Authentication API")
        access_token = access_token_raw["access_token"]
        provider = access_token_raw["provider"]
        token_type = access_token_raw["token_type"]
    if access_token_raw["status"] == 400:
        _LOGGER.error("Error 400 - Bad request, check your credentials")
        raise Exception
    if access_token_raw["status"] == 401:
        _LOGGER.error("Error 401 - Unauthorized check your credentials")
        raise Exception
    if access_token_raw["status"] != 200:
        _LOGGER.error("Error %s", access_token_raw["status"])
        raise Exception
    automower_api = GetMowerData(api_key, access_token, provider, token_type)
    mower_data = await automower_api.async_mower_state()
    if mower_data["status"] == 200:
        _LOGGER.debug("Connected with the Automower Connect API")
    elif mower_data["status"] == 403:
        _LOGGER.error(
            "Error 403 - Make sure that you are connected to the Authentication API and the Automower Connect API on %s",
            HUSQVARNA_URL,
        )
        raise Exception
    else:
        _LOGGER.error("Error %s", mower_data["status"])
        raise Exception

    _LOGGER.debug("Mower data: %s", mower_data)
    _LOGGER.debug("Successfully connected Authentication and Automower Connect API")
    return access_token_raw

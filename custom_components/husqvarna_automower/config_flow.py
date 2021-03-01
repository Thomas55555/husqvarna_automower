import logging
import time
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from custom_components.husqvarna_automower.const import (  # pylint: disable=unused-import
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)
from husqvarna_automower import GetAccessToken, GetMowerData

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
            await try_connection(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_API_KEY],
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "auth"
            return await self._show_setup_form(errors)

        unique_id = user_input[CONF_API_KEY]

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="",
            data={
                CONF_ID: unique_id,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_API_KEY: user_input[CONF_API_KEY],
            },
        )


async def try_connection(username, password, api_key):
    errors = {}
    _LOGGER.debug("Trying to connect to Husqvarna")
    auth_api = GetAccessToken(api_key, username, password)
    access_token_raw = await auth_api.async_get_access_token()
    _LOGGER.debug(f"Access token raw: {access_token_raw}")
    if "access_token" in access_token_raw:
        _LOGGER.info("Connected with the Authentication API")
        access_token = access_token_raw["access_token"]
        _LOGGER.debug(f"Access token: {access_token}")
        provider = access_token_raw["provider"]
        _LOGGER.debug(f"Provider: {provider}")
        token_type = access_token_raw["token_type"]
        _LOGGER.debug(f"Token type: {token_type}")
    elif access_token_raw == 400:
        _LOGGER.error("Error 400 - Bad request")
        raise Exception
    elif access_token_raw == 401:
        _LOGGER.error("Error 401 - Unauthorized check your credentials")
        raise Exception
    else:
        _LOGGER.error("Unknown Error")
        raise Exception
    automower_api = GetMowerData(api_key, access_token, provider, token_type)
    mower_data = await automower_api.async_mower_state()
    if "data" in mower_data:
        _LOGGER.info("Connected with the Automower Connect API")
    else:
        _LOGGER.error(
            "Make sure, that you have connected to the Automower Connect API on https://developer.husqvarnagroup.cloud/"
        )
        raise Exception
    _LOGGER.debug(f"Mower data: {mower_data}")
    _LOGGER.info("Successfully connected Authentication and Automower Connect API")
    time.sleep(5)

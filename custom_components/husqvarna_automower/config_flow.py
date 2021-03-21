"""Config flow to add the integration via the UI."""
import logging
import time
from collections import OrderedDict
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp import ClientError
import voluptuous as vol
from aioautomower import GetAccessToken, GetMowerData

from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import callback

from .const import (
    ACCESS_TOKEN_RAW,
    CONF_PROVIDER,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    CONF_TOKEN_TYPE,
    DOMAIN,
    HUSQVARNA_URL,
)

CONF_ID = "unique_id"

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    """Handle a config flow."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _show_setup_form(self, errors):
        """Show the setup form to the user."""
        _LOGGER.debug("""Show the setup form to the user.""")

        fields = OrderedDict()
        fields[vol.Required(CONF_API_KEY)] = vol.All(str, vol.Length(min=36, max=36))
        fields[vol.Required(CONF_USERNAME)] = str
        fields[vol.Required(CONF_PASSWORD)] = str

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is None:
            return await self._show_setup_form(errors)
        try:
            get_token = GetAccessToken(
                user_input[CONF_API_KEY],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            access_token_raw = await get_token.async_get_access_token()
        except (ClientConnectorError, ClientError):
            errors["base"] = "auth"
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "auth"
            return await self._show_setup_form(errors)

        try:
            get_mower_data = GetMowerData(
                user_input[CONF_API_KEY],
                access_token_raw["access_token"],
                access_token_raw["provider"],
                access_token_raw["token_type"],
            )
            mower_data = await get_mower_data.async_mower_state()
            _LOGGER.debug("config: %s", mower_data)
        except (ClientConnectorError, ClientError):
            errors["base"] = "mower"
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)
        unique_id = user_input[CONF_API_KEY]
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_API_KEY],
            data={
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_API_KEY: user_input[CONF_API_KEY],
                CONF_TOKEN: access_token_raw,
            },
        )

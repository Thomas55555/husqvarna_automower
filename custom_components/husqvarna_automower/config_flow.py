"""Config flow to add the integration via the UI."""
import logging
from collections import OrderedDict

import voluptuous as vol
from aioautomower import GetAccessToken, GetMowerData, TokenError
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_UNIQUE_ID,
    CONF_USERNAME,
)

from .const import CONF_PROVIDER, CONF_TOKEN_TYPE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    """Handle a config flow."""

    VERSION = 2

    async def _show_setup_form(self, errors):
        """Show the setup form to the user."""
        _LOGGER.debug("Show the setup form to the user")

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
        except (ClientConnectorError, TokenError):
            errors["base"] = "auth"
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "auth"
            return await self._show_setup_form(errors)

        try:
            get_mower_data = GetMowerData(
                user_input[CONF_API_KEY],
                access_token_raw[CONF_ACCESS_TOKEN],
                access_token_raw[CONF_PROVIDER],
                access_token_raw[CONF_TOKEN_TYPE],
            )
            mower_data = await get_mower_data.async_mower_state()
            _LOGGER.debug("config: %s", mower_data)
        except (ClientConnectorError, ClientResponseError):
            errors["base"] = "mower"
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)
        CONF_UNIQUE_ID = user_input[CONF_API_KEY]
        data = {
            CONF_API_KEY: user_input[CONF_API_KEY],
            CONF_TOKEN: access_token_raw,
        }
        existing_entry = await self.async_set_unique_id(CONF_UNIQUE_ID)

        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=user_input[CONF_API_KEY],
            data=data,
        )

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

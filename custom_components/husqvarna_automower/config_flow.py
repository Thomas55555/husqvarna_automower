"""Config flow to add the integration via the UI."""
import logging

import voluptuous as vol
from aioautomower import GetAccessToken, GetMowerData, TokenError
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_TOKEN,
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

        data_schema = {
            vol.Required(CONF_API_KEY): vol.All(str, vol.Length(min=36, max=36)),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
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
            # On 400 credentials could be wrong, or (Authentication API && Automower Connect API) are not connected.
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
            if "amc:api" in access_token_raw["scope"]:
                errors["base"] = "api_key"  ## Something's wrong with the key
            else:
                errors["base"] = "mower"  ## Automower Connect API not connected
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)

        if "amc:api" not in access_token_raw["scope"]:
            # If the API-Key is old
            errors["base"] = "api_key"
            return await self._show_setup_form(errors)

        unique_id = user_input[CONF_API_KEY]
        data = {
            CONF_API_KEY: user_input[CONF_API_KEY],
            CONF_TOKEN: access_token_raw,
        }

        existing_entry = await self.async_set_unique_id(unique_id)

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

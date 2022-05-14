"""Config flow to add the integration via the UI."""
import logging

from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
import voluptuous as vol

from aioautomower import GetAccessToken, GetMowerData, TokenError
from homeassistant import data_entry_flow
from homeassistant.const import (
    ATTR_CREDENTIALS,
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import get_url

from .const import CONF_PROVIDER, CONF_TOKEN_TYPE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    data_entry_flow.FlowHandler,
    domain=DOMAIN,
):

    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = 2

    async def _show_setup_form(self, errors):
        """Show the setup form to the user."""

        data_schema = {
            vol.Required(CONF_API_KEY): vol.All(str, vol.Length(min=36, max=36)),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(ATTR_CREDENTIALS): bool,
        }

        return self.async_show_form(
            step_id="password", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        _LOGGER.debug("URL: %s", get_url(self.hass))
        return self.async_show_menu(
            step_id="user",
            menu_options=["oauth2", "password"],
            description_placeholders={
                "model": "Example model",
            },
        )

    async def async_step_oauth2(self, user_input=None):
        """Handle the config-flow for Authorization Code Grant."""

        return await super().async_step_user(user_input)

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an entry for the flow."""

        data["token"]["status"] = 200
        await self.async_test_mower(
            self.hass.data[DOMAIN][CONF_CLIENT_ID], data[CONF_TOKEN]
        )
        return await self.async_step_finish(
            self.hass.data[DOMAIN][CONF_CLIENT_ID], data
        )

    async def async_step_password(self, user_input=None):
        """Handle the config-flow with api-key, username and password."""

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

        await self.async_test_mower(user_input[CONF_API_KEY], access_token_raw)

        unique_id = user_input[CONF_API_KEY]
        data = {
            CONF_TOKEN: access_token_raw,
        }

        if user_input[ATTR_CREDENTIALS] is True:
            data[CONF_USERNAME] = user_input[CONF_USERNAME]
            data[CONF_PASSWORD] = user_input[CONF_PASSWORD]

        return await self.async_step_finish(unique_id, data)

    async def async_step_finish(self, unique_id, data):
        """Complete the config entries."""

        existing_entry = await self.async_set_unique_id(unique_id)

        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=unique_id,
            data=data,
        )

    async def async_test_mower(self, api_key, access_token_raw):
        """Test if mower data can be fetched with Rest, and also check websocket capabilities."""
        errors = {}
        try:
            get_mower_data = GetMowerData(
                api_key,
                access_token_raw[CONF_ACCESS_TOKEN],
                access_token_raw[CONF_PROVIDER],
                access_token_raw[CONF_TOKEN_TYPE],
            )
            mower_data = await get_mower_data.async_mower_state()
            _LOGGER.debug("config: %s", mower_data)
        except (ClientConnectorError, ClientResponseError):
            if "amc:api" in access_token_raw["scope"]:
                errors["base"] = "api_key"  ## Something's wrong with the key
                _LOGGER.warning("Something's wrong with the API-key")
            else:
                errors["base"] = "mower"  ## Automower Connect API not connected
                _LOGGER.warning("Automower Connect API not connected")
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)

        if "amc:api" not in access_token_raw["scope"]:
            # If the API-Key is old
            _LOGGER.warning("The API-key is too old. Renew it")
            errors["base"] = "api_key"
            return await self._show_setup_form(errors)

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            _LOGGER.debug("USER INPUT NONE")
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        _LOGGER.debug("user_input: %s", user_input)
        return await self.async_step_user()

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

"""Config flow to add the integration via the UI."""
import logging

from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
import voluptuous as vol

from aioautomower import GetAccessToken, GetMowerData, TokenError
from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.helpers.typing import ConfigType

from .const import CONF_PROVIDER, CONF_TOKEN_TYPE, DOMAIN
from .oauth_impl import OndiloOauth2Implementation

OAUTH2_CLIENTID = "572bef0c-6e2f-4dd0-b7f6-2c96ea7de3b5"
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):

    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = 2

    async def _show_setup_form(self, errors):
        """Show the setup form to the user."""

        data_schema = {
            vol.Required(CONF_API_KEY): vol.All(str, vol.Length(min=36, max=36)),
            vol.Required(OAUTH2_CLIENTID): vol.All(str, vol.Length(min=36, max=36)),
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}

        await self.async_set_unique_id(OAUTH2_CLIENTID)

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        self.async_register_implementation(
            self.hass, OndiloOauth2Implementation(self.hass)
        )

        return await super().async_step_user(user_input)



    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {"Content-Type": "application/x-www-form-urlencoded"}

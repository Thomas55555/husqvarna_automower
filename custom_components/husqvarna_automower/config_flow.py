from homeassistant import config_entries
from homeassistant.core import callback
from collections import OrderedDict
import voluptuous as vol
import logging
from husqvarna_automower import GetAccessToken

from custom_components.husqvarna_automower.const import (  # pylint: disable=unused-import
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_API_KEY,
    DOMAIN,
    PLATFORMS,
)


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
            await try_connection (user_input[CONF_USERNAME], user_input[CONF_PASSWORD], user_input[CONF_API_KEY])
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
            })

    
async def try_connection(username, password, api_key):
    _LOGGER.debug("Trying to connect to Husqvarna")
    auth_api = GetAccessToken(api_key, username, password)
    access_token_raw = await auth_api.async_get_access_token()
    if access_token_raw in [400,401,402,403]:
        raise Exception
    _LOGGER.debug("Successfully connected to Gardena during setup")

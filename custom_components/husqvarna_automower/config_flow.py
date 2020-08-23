from homeassistant import config_entries
from homeassistant.core import callback
from collections import OrderedDict
import voluptuous as vol
import logging
from husqvarna_automower import GetAccessToken, GetMowerData

from custom_components.husqvarna_automower.const import (  # pylint: disable=unused-import
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_API_KEY,
    DOMAIN,
    PLATFORMS,
)


CONF_ID = "unique_id"

_LOGGER = logging.getLogger(__name__)

class GardenaSmartSystemConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gardena."""

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
            await self.hass.async_add_executor_job(
                try_connection,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_API_KEY])
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GardenaSmartSystemOptionsFlowHandler(config_entry)


class GardenaSmartSystemOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize Gardena Smart Sytem options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            # TODO: Validate options (min, max values)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(fields), errors=errors)


def try_connection(username, password, api_key):
    _LOGGER.debug("Trying to connect to Gardena during setup")
    smart_system = GetAccessToken(api_key = api_key, username = username, password = password)
    _LOGGER.debug("Successfully connected to Gardena during setup")



# class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
#     """Config flow for HusqvranaAutomower."""

#     VERSION = 1
#     CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

#     def __init__(self):
#         """Initialize."""
#         self._errors = {}

#     async def async_step_user(
#         self, user_input=None  # pylint: disable=bad-continuation
#     ):
#         """Handle a flow initialized by the user."""
#         self._errors = {}

#         # Uncomment the next 2 lines if only a single instance of the integration is allowed:
#         # if self._async_current_entries():
#         #     return self.async_abort(reason="single_instance_allowed")

#         if user_input is not None:
#             valid = await self._test_credentials(
#                 user_input[CONF_USERNAME], user_input[CONF_PASSWORD], user_input[CONF_API_KEY]
#             )
#             if valid:
#                 return self.async_create_entry(
#                     title=user_input[CONF_USERNAME], data=user_input
#                 )
#             else:
#                 self._errors["base"] = "auth"

#             return await self._show_config_form(user_input)

#         return await self._show_config_form(user_input)

#     @staticmethod
#     @callback
#     def async_get_options_flow(config_entry):
#         return BlueprintOptionsFlowHandler(config_entry)

#     async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
#         """Show the configuration form to edit location data."""
#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str, vol.Required(CONF_API_KEY): str}
#             ),
#             errors=self._errors,
#         )

#     async def _test_credentials(self, api_key, username, password):
#         """Return true if credentials is valid."""
#         # try:
#         #     client = GetAccessToken(api_key, username, password)
#         #     await client.async_get_access_token()
#         #     return True
#         # except Exception:  # pylint: disable=broad-except
#         #     pass
#         # return False
#         return True

# class BlueprintOptionsFlowHandler(config_entries.OptionsFlow):
#     """Husqvarna config flow options handler."""

#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)

#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(x, default=self.options.get(x, True)): bool
#                     for x in sorted(PLATFORMS)
#                 }
#             ),
#         )

#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(CONF_USERNAME), data=self.options
#         )

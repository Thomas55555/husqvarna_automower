"""Config flow to add the integration via the UI."""
import logging
import os
import json

from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
import voluptuous as vol

from aioautomower import GetAccessToken, GetMowerData, TokenError
from homeassistant import data_entry_flow, config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector


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
from homeassistant.core import callback

from .const import (
    CONF_PROVIDER,
    CONF_TOKEN_TYPE,
    DOMAIN,
    ENABLE_CAMERA,
    GPS_TOP_LEFT,
    GPS_BOTTOM_RIGHT,
    MOWER_IMG_PATH,
    MAP_IMG_PATH,
    CONF_ZONES,
    ZONE_COORD,
    ZONE_NAME,
    ZONE_DEL,
    ZONE_SEL,
    ZONE_NEW,
    CONF_ZONES,
)

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        super().__init__()
        self.base_path = os.path.dirname(__file__)
        self.config_entry = config_entry

        self.user_input = dict(config_entry.options)
        if self.user_input.get(CONF_ZONES, False):
            self.user_input[CONF_ZONES] = json.loads(self.user_input[CONF_ZONES])

        self.configured_zones = self.user_input.get(CONF_ZONES, {})

        self.camera_enabled = self.user_input.get(ENABLE_CAMERA, False)
        self.map_top_left_coord = self.user_input.get(GPS_TOP_LEFT, "")
        if self.map_top_left_coord != "":
            self.map_top_left_coord = ",".join(
                [str(x) for x in self.map_top_left_coord]
            )

        self.map_bottom_right_coord = self.user_input.get(GPS_BOTTOM_RIGHT, "")
        if self.map_bottom_right_coord != "":
            self.map_bottom_right_coord = ",".join(
                [str(x) for x in self.map_bottom_right_coord]
            )

        self.mower_image_path = self.user_input.get(
            MOWER_IMG_PATH, os.path.join(self.base_path, "resources/mower.png")
        )
        self.map_img_path = self.user_input.get(
            MAP_IMG_PATH, os.path.join(self.base_path, "resources/map_image.png")
        )

    async def async_step_init(self, user_input=None):
        """Manage option flow"""
        return await self.async_step_select()

    async def async_step_select(self, user_input=None):
        """Select Configuration Item"""

        return self.async_show_menu(
            step_id="select",
            menu_options=["geofence_init", "camera_init"],
        )

    async def async_step_geofence_init(self, user_input=None):
        """Configure the geofence"""

        if user_input:
            self.sel_zone_id=user_input.get(ZONE_SEL, ZONE_NEW)
            return await self.async_step_zone_edit()
        configured_zone_keys = [ZONE_NEW] + list(self.configured_zones.keys())
        data_schema = {}
        data_schema[ZONE_SEL] = selector(
            {
                "select": {
                    "options": configured_zone_keys,
                }
            }
        )
        return self.async_show_form(
            step_id="geofence_init", data_schema=vol.Schema(data_schema)
        )

    async def async_step_zone_edit(self, user_input=None):
        """Update the selected zone configuration."""
        if user_input:
            if user_input.get(ZONE_DEL) == True:
                self.configured_zones.pop(self.sel_zone_id, None)
            else:
                zone_coord = []
                if user_input.get(ZONE_COORD):
                    for coord in user_input.get(ZONE_COORD).split(";"):
                        if coord != "":
                            coord_split = coord.split(",")
                            zone_coord.append(
                                (float(coord_split[0]), float(coord_split[1]))
                            )
                    if self.sel_zone_id == ZONE_NEW:
                        self.sel_zone_id = user_input.get(ZONE_NAME).lower().strip().replace(' ', '_')

                    self.configured_zones[self.sel_zone_id] = {
                        ZONE_COORD: zone_coord,
                        ZONE_NAME: user_input.get(ZONE_NAME).strip()
                    }

            self.user_input.update({CONF_ZONES: self.configured_zones})
            return await self._update_options()
            # Trying to do this kills the config flow
            # return await self.async_step_geofence_init()

        sel_zone = self.configured_zones.get(self.sel_zone_id, {})
        current_coordinates = sel_zone.get(ZONE_COORD, "")

        str_zone = ""
        sel_zone_name = sel_zone.get(ZONE_NAME,"")

        for coord in current_coordinates:
            str_zone += ",".join([str(x) for x in coord])
            str_zone += ";"

        sel_zone_coordinates = str_zone


        data_schema = vol.Schema(
            {
                vol.Required(ZONE_NAME, default=sel_zone_name): str,
                vol.Required(ZONE_COORD, default=sel_zone_coordinates): str,
                vol.Required(ZONE_DEL, default=False): bool,
            }
        )
        return self.async_show_form(step_id="zone_edit", data_schema=data_schema)


    async def async_step_camera_init(self, user_input=None):
        """Enable / Disable the camera."""

        if user_input:
            if user_input.get(ENABLE_CAMERA):
                self.user_input[ENABLE_CAMERA] = True
                return await self.async_step_camera_config()
            self.user_input[ENABLE_CAMERA] = False
            return await self._update_options()

        data_schema = vol.Schema(
            {
                vol.Required(ENABLE_CAMERA, default=self.camera_enabled): bool,
            }
        )
        return self.async_show_form(step_id="camera_init", data_schema=data_schema)

    async def async_step_camera_config(self, user_input=None):
        """Update the camera configuration."""
        if user_input:
            if user_input.get(GPS_TOP_LEFT):
                self.user_input[GPS_TOP_LEFT] = [
                    float(x.strip())
                    for x in user_input.get(GPS_TOP_LEFT).split(",")
                    if x
                ]
            if user_input.get(GPS_BOTTOM_RIGHT):
                self.user_input[GPS_BOTTOM_RIGHT] = [
                    float(x.strip())
                    for x in user_input.get(GPS_BOTTOM_RIGHT).split(",")
                    if x
                ]

            self.user_input[MOWER_IMG_PATH] = user_input.get(MOWER_IMG_PATH)
            self.user_input[MAP_IMG_PATH] = user_input.get(MAP_IMG_PATH)
            return await self._update_options()

        data_schema = vol.Schema(
            {
                vol.Required(GPS_TOP_LEFT, default=self.map_top_left_coord): str,
                vol.Required(
                    GPS_BOTTOM_RIGHT, default=self.map_bottom_right_coord
                ): str,
                vol.Required(MOWER_IMG_PATH, default=self.mower_image_path): str,
                vol.Required(MAP_IMG_PATH, default=self.map_img_path): str,
            }
        )
        return self.async_show_form(step_id="camera_config", data_schema=data_schema)

    async def _update_options(self):
        """Update config entry options."""

        self.user_input[CONF_ZONES] = json.dumps(self.user_input.get(CONF_ZONES, {}))
        return self.async_create_entry(title="", data=self.user_input)

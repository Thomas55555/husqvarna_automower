"""Config flow to add the integration via the UI."""
import logging
import os

import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers.selector import selector

from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    DOMAIN,
    ENABLE_CAMERA,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    MAP_IMG_PATH,
    MOWER_IMG_PATH,
    HOME_LOCATION,
)

from .map_utils import ValidatePointString, validate_image

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    data_entry_flow.FlowHandler,
    domain=DOMAIN,
):
    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = 2

    async def async_step_oauth2(self, user_input=None) -> data_entry_flow.FlowResult:
        """Handle the config-flow for Authorization Code Grant."""
        return await super().async_step_user(user_input)

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an entry for the flow."""
        if "amc:api" not in data[CONF_TOKEN]["scope"]:
            _LOGGER.warning(
                "The scope of your API-key is `%s`, but should be `iam:read amc:api`",
                data[CONF_TOKEN]["scope"],
            )
        return await self.async_step_finish(DOMAIN, data)

    async def async_step_finish(self, unique_id, data) -> data_entry_flow.FlowResult:
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

    async def async_step_reauth(self, user_input=None) -> data_entry_flow.FlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input=None
    ) -> data_entry_flow.FlowResult:
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

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.base_path = os.path.dirname(__file__)
        self.config_entry = config_entry

        self.user_input = dict(config_entry.options)

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

        self.home_location = self.user_input.get(HOME_LOCATION, "")
        if self.home_location != "":
            self.home_location = ",".join([str(x) for x in self.home_location])

        self.sel_zone_id = None

    async def async_step_init(self, user_input=None):
        """Manage option flow"""
        return await self.async_step_select()

    async def async_step_select(self, user_input=None):
        """Select Configuration Item"""

        return self.async_show_menu(
            step_id="select",
            menu_options=["camera_init", "home_init"],
        )

    async def async_step_home_init(self, user_input=None):
        """Configure the home location."""
        errors = {}
        if user_input:
            if user_input.get(HOME_LOCATION):
                pnt_validator = ValidatePointString(user_input.get(HOME_LOCATION))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.user_input[HOME_LOCATION] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                    return await self._update_options()
                errors[HOME_LOCATION] = pnt_error

        data_schema = vol.Schema(
            {
                vol.Required(HOME_LOCATION, default=self.home_location): str,
            }
        )
        return self.async_show_form(
            step_id="home_init", data_schema=data_schema, errors=errors
        )

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
        errors = {}

        if user_input:
            if user_input.get(GPS_TOP_LEFT):
                pnt_validator = ValidatePointString(user_input.get(GPS_TOP_LEFT))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.user_input[GPS_TOP_LEFT] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                else:
                    errors[GPS_TOP_LEFT] = pnt_error

            if user_input.get(GPS_BOTTOM_RIGHT):
                pnt_validator = ValidatePointString(user_input.get(GPS_BOTTOM_RIGHT))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.user_input[GPS_BOTTOM_RIGHT] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                else:
                    errors[GPS_BOTTOM_RIGHT] = pnt_error

            if self.user_input.get(GPS_BOTTOM_RIGHT) == self.user_input.get(
                GPS_TOP_LEFT
            ):
                errors[GPS_BOTTOM_RIGHT] = "points_match"

            if user_input.get(MOWER_IMG_PATH):
                if os.path.isfile(user_input.get(MOWER_IMG_PATH)):
                    if validate_image(user_input.get(MOWER_IMG_PATH)):
                        self.user_input[MOWER_IMG_PATH] = user_input.get(MOWER_IMG_PATH)
                    else:
                        errors[MOWER_IMG_PATH] = "not_image"
                else:
                    errors[MOWER_IMG_PATH] = "not_file"

            if user_input.get(MAP_IMG_PATH):
                if os.path.isfile(user_input.get(MAP_IMG_PATH)):
                    if validate_image(user_input.get(MOWER_IMG_PATH)):
                        self.user_input[MAP_IMG_PATH] = user_input.get(MAP_IMG_PATH)
                    else:
                        errors[MOWER_IMG_PATH] = "not_image"
                else:
                    errors[MAP_IMG_PATH] = "not_file"

            if not errors:
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
        return self.async_show_form(
            step_id="camera_config", data_schema=data_schema, errors=errors
        )

    async def _update_options(self):
        """Update config entry options."""

        return self.async_create_entry(title="", data=self.user_input)

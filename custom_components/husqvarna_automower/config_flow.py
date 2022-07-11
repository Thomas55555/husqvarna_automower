"""Config flow to add the integration via the UI."""
import logging
import os

import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
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

        self.camera_enabled = self.config_entry.options.get(ENABLE_CAMERA, False)
        self.map_top_left_coord = self.config_entry.options.get(GPS_TOP_LEFT, "")
        if self.map_top_left_coord != "":
            self.map_top_left_coord = ",".join(
                [str(x) for x in self.map_top_left_coord]
            )

        self.map_bottom_right_coord = self.config_entry.options.get(
            GPS_BOTTOM_RIGHT, ""
        )
        if self.map_bottom_right_coord != "":
            self.map_bottom_right_coord = ",".join(
                [str(x) for x in self.map_bottom_right_coord]
            )

        self.mower_image_path = self.config_entry.options.get(
            MOWER_IMG_PATH, os.path.join(self.base_path, "resources/mower.png")
        )
        self.map_img_path = self.config_entry.options.get(
            MAP_IMG_PATH, os.path.join(self.base_path, "resources/map_image.png")
        )
        self.options = self.config_entry.options.copy()

    async def async_step_init(self, user_input=None):
        """Enable / Disable the camera."""
        if user_input:
            if user_input.get(ENABLE_CAMERA):
                self.options[ENABLE_CAMERA] = True
                return await self.async_step_config()
            self.options[ENABLE_CAMERA] = False
            return await self._update_camera_config()

        data_schema = vol.Schema(
            {
                vol.Required(ENABLE_CAMERA, default=self.camera_enabled): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def async_step_config(self, user_input=None):
        """Update the camera configuration."""
        if user_input:
            if user_input.get(GPS_TOP_LEFT):
                self.options[GPS_TOP_LEFT] = [
                    float(x.strip())
                    for x in user_input.get(GPS_TOP_LEFT).split(",")
                    if x
                ]
            if user_input.get(GPS_BOTTOM_RIGHT):
                self.options[GPS_BOTTOM_RIGHT] = [
                    float(x.strip())
                    for x in user_input.get(GPS_BOTTOM_RIGHT).split(",")
                    if x
                ]

            self.options[MOWER_IMG_PATH] = user_input.get(MOWER_IMG_PATH)
            self.options[MAP_IMG_PATH] = user_input.get(MAP_IMG_PATH)
            return await self._update_camera_config()

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
        return self.async_show_form(step_id="config", data_schema=data_schema)

    async def _update_camera_config(self):
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)

"""Config flow to add the integration via the UI."""
import json
import logging
import os

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_TOKEN
from homeassistant.core import async_get_hass, callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv


from .const import (
    ADD_IMAGES,
    CONF_ZONES,
    DOMAIN,
    ENABLE_IMAGE,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    HOME_LOCATION,
    MAP_IMG_PATH,
    MAP_IMG_ROTATION,
    MAP_PATH_COLOR,
    MOWER_IMG_PATH,
    SEL_IMAGE,
    ZONE_COLOR,
    ZONE_COORD,
    ZONE_DEL,
    ZONE_DISPLAY,
    ZONE_FINISH,
    ZONE_MOWERS,
    ZONE_NAME,
    ZONE_NEW,
    ZONE_SEL,
    CURRENT_CONFIG_VER,
)
from .map_utils import (
    ValidatePointString,
    ValidateRGB,
    validate_image,
    validate_rotation,
)

_LOGGER = logging.getLogger(__name__)


class HusqvarnaConfigFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    data_entry_flow.FlowHandler,
    domain=DOMAIN,
):
    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = CURRENT_CONFIG_VER

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

    async def async_step_reauth(
        self, user_input=None  # pylint: disable=unused-argument
    ) -> data_entry_flow.FlowResult:
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

        self.hass = async_get_hass()
        self.mower_idx = []
        for entity in self.hass.data[DOMAIN].keys():
            # pylint: disable=unused-variable
            for idx, ent in enumerate(
                self.hass.data[DOMAIN][entity].session.data["data"]
            ):
                self.mower_idx.append(
                    {"name": ent["attributes"]["system"]["name"], "id": ent["id"]}
                )
        self.options = self.config_entry.options.copy()

        self.configured_zones = json.loads(self.options.get(CONF_ZONES, "{}"))
        if not isinstance(self.configured_zones, dict):
            self.configured_zones = {}

        mower_configurations = {}
        for mower in self.mower_idx:
            mwr_id = mower["id"]
            mower_configurations[mwr_id] = {}
            cfg_options = self.options.get(mwr_id, {})

            mower_configurations[mwr_id][ENABLE_IMAGE] = cfg_options.get(
                ENABLE_IMAGE, False
            )
            mower_configurations[mwr_id][GPS_TOP_LEFT] = cfg_options.get(
                GPS_TOP_LEFT, ""
            )
            mower_configurations[mwr_id][GPS_BOTTOM_RIGHT] = cfg_options.get(
                GPS_BOTTOM_RIGHT, ""
            )
            mower_configurations[mwr_id][MOWER_IMG_PATH] = cfg_options.get(
                MOWER_IMG_PATH, os.path.join(self.base_path, "resources/mower.png")
            )
            mower_configurations[mwr_id][MAP_IMG_PATH] = cfg_options.get(
                MAP_IMG_PATH, os.path.join(self.base_path, "resources/map_image.png")
            )
            mower_configurations[mwr_id][MAP_PATH_COLOR] = cfg_options.get(
                MAP_PATH_COLOR, [255, 0, 0]
            )
            mower_configurations[mwr_id][MAP_IMG_ROTATION] = cfg_options.get(
                MAP_IMG_ROTATION, 0
            )
            mower_configurations[mwr_id][HOME_LOCATION] = cfg_options.get(
                HOME_LOCATION, ""
            )
            mower_configurations[mwr_id][ADD_IMAGES] = cfg_options.get(ADD_IMAGES, [])

            self.options.update(mower_configurations)

        self.sel_zone_id = None
        self.sel_mower_id = self.mower_idx[0]["id"]

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage option flow."""
        return await self.async_step_select()

    async def async_step_select(
        self, user_input=None
    ):  # pylint: disable=unused-argument
        """Select Configuration Item."""
        return self.async_show_menu(
            step_id="select", menu_options=["image_select", "geofence_init"]
        )

    async def async_step_geofence_init(self, user_input=None):
        """Configure the geofence."""
        if user_input:
            self.sel_zone_id = user_input.get(ZONE_SEL, ZONE_FINISH)
            if self.sel_zone_id == ZONE_FINISH:
                return await self._update_config()
            return await self.async_step_zone_edit()

        configured_zone_keys = [{"label": ZONE_NEW, "value": ZONE_NEW}]
        for zone_id, zone_values in self.configured_zones.items():
            configured_zone_keys.append(
                {"label": zone_values["name"], "value": zone_id}
            )

        configured_zone_keys.append({"label": ZONE_FINISH, "value": ZONE_FINISH})

        data_schema = {}
        data_schema = vol.Schema(
            {
                vol.Optional(ZONE_SEL, default=ZONE_FINISH): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=configured_zone_keys,
                        translation_key="geofence_init",
                    )
                )
            }
        )

        return self.async_show_form(step_id="geofence_init", data_schema=data_schema)

    async def async_step_zone_edit(self, user_input=None):
        """Update the selected zone configuration."""
        errors = {}

        if user_input:
            if user_input.get(ZONE_DEL) is True:
                self.configured_zones.pop(self.sel_zone_id, None)
            else:
                zone_coord = []
                if user_input.get(ZONE_COORD):
                    for coord in user_input.get(ZONE_COORD).split(";"):
                        if coord != "":
                            pnt_validator = ValidatePointString(coord)
                            pnt_valid, pnt_error = pnt_validator.is_valid()

                            if pnt_valid:
                                zone_coord.append(
                                    (pnt_validator.point.x, pnt_validator.point.y)
                                )
                            else:
                                errors[ZONE_COORD] = pnt_error
                                break

                    if not errors:
                        if self.sel_zone_id == ZONE_NEW:
                            self.sel_zone_id = (
                                user_input.get(ZONE_NAME)
                                .lower()
                                .strip()
                                .replace(" ", "_")
                            )

                        if len(zone_coord) < 3:
                            errors[ZONE_COORD] = "too_few_points"

                        zone_color = ValidateRGB(user_input.get(ZONE_COLOR))

                        zone_int_colors = [255, 255, 255]
                        if zone_color.is_valid():
                            zone_int_colors = zone_color.rgb_val
                        else:
                            errors[ZONE_COLOR] = "color_error"

                        if len(user_input.get(ZONE_MOWERS, [])) < 1:
                            errors[ZONE_MOWERS] = "need_one_mower"

                        if not errors:
                            self.configured_zones[self.sel_zone_id] = {
                                ZONE_COORD: zone_coord,
                                ZONE_NAME: user_input.get(ZONE_NAME).strip(),
                                ZONE_COLOR: zone_int_colors,
                                ZONE_DISPLAY: user_input.get(ZONE_DISPLAY),
                                ZONE_MOWERS: user_input.get(ZONE_MOWERS),
                            }

            if not errors:
                self.options.update({CONF_ZONES: self.configured_zones})
                if isinstance(self.options.get(CONF_ZONES), dict):
                    json_options = self.options.copy()
                    json_options[CONF_ZONES] = json.dumps(json_options.get(CONF_ZONES))

                self.hass.config_entries.async_update_entry(
                    self.config_entry, options=json_options
                )
                return await self.async_step_geofence_init()

            sel_zone_name = user_input.get(ZONE_NAME, "")
            sel_mowers = user_input.get(ZONE_MOWERS, [])
            sel_zone_coordinates = user_input.get(ZONE_COORD, "")
            display_zone = user_input.get(ZONE_DISPLAY, False)
            display_color = user_input.get(ZONE_COLOR, "255, 255, 255")

        else:
            sel_zone = self.configured_zones.get(self.sel_zone_id, {})
            sel_mowers = sel_zone.get(ZONE_MOWERS, [])

            current_coordinates = sel_zone.get(ZONE_COORD, "")

            str_zone = ""
            sel_zone_name = sel_zone.get(ZONE_NAME, "")

            for coord in current_coordinates:
                str_zone += ",".join([str(x) for x in coord])
                str_zone += ";"

            sel_zone_coordinates = str_zone

            display_zone = sel_zone.get(ZONE_DISPLAY, False)
            display_color = sel_zone.get(ZONE_COLOR, [255, 255, 255])
            display_color = ",".join([str(i) for i in display_color])

        mwr_options_dict = {}
        for mwr in self.mower_idx:
            mwr_options_dict[mwr["id"]] = mwr["name"]

        data_schema = {
            vol.Required(ZONE_NAME, default=sel_zone_name): str,
            vol.Required(ZONE_COORD, default=sel_zone_coordinates): str,
            vol.Required(ZONE_DISPLAY, default=display_zone): bool,
            vol.Required(ZONE_COLOR, default=display_color): str,
            vol.Required(ZONE_DEL, default=False): bool,
            vol.Optional(
                ZONE_MOWERS,
                default=sel_mowers,
            ): cv.multi_select(mwr_options_dict),
        }

        return self.async_show_form(
            step_id="zone_edit", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_image_select(self, user_input=None):
        """Select image to configure."""
        if user_input:
            sel_mower_name = user_input.get(SEL_IMAGE)
            self.sel_mower_id = next(
                (mwr["id"] for mwr in self.mower_idx if mwr["name"] == sel_mower_name),
                None,
            )
            return await self.async_step_image_config()

        configured_image_keys = [m["name"] for m in self.mower_idx]

        data_schema = {}
        data_schema[SEL_IMAGE] = selector.selector(
            {
                "select": {
                    "options": configured_image_keys,
                }
            }
        )
        return self.async_show_form(
            step_id="image_select", data_schema=vol.Schema(data_schema)
        )

    async def async_step_image_config(self, user_input=None):
        """Update the image configuration."""
        errors = {}

        if user_input:
            if user_input.get(ENABLE_IMAGE):
                self.options[self.sel_mower_id][ENABLE_IMAGE] = True
            else:
                self.options[self.sel_mower_id][ENABLE_IMAGE] = False
                return await self._update_config()

            if user_input.get(GPS_TOP_LEFT):
                pnt_validator = ValidatePointString(user_input.get(GPS_TOP_LEFT))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.options[self.sel_mower_id][GPS_TOP_LEFT] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                else:
                    errors[GPS_TOP_LEFT] = pnt_error

            if user_input.get(GPS_BOTTOM_RIGHT):
                pnt_validator = ValidatePointString(user_input.get(GPS_BOTTOM_RIGHT))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.options[self.sel_mower_id][GPS_BOTTOM_RIGHT] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                else:
                    errors[GPS_BOTTOM_RIGHT] = pnt_error

            if self.options[self.sel_mower_id].get(GPS_BOTTOM_RIGHT) == self.options[
                self.sel_mower_id
            ].get(GPS_TOP_LEFT):
                errors[GPS_BOTTOM_RIGHT] = "points_match"

            if user_input.get(MOWER_IMG_PATH):
                if os.path.isfile(user_input.get(MOWER_IMG_PATH)):
                    if validate_image(user_input.get(MOWER_IMG_PATH)):
                        self.options[self.sel_mower_id][
                            MOWER_IMG_PATH
                        ] = user_input.get(MOWER_IMG_PATH)
                    else:
                        errors[MOWER_IMG_PATH] = "not_image"
                else:
                    errors[MOWER_IMG_PATH] = "not_file"

            if user_input.get(MAP_IMG_PATH):
                if os.path.isfile(user_input.get(MAP_IMG_PATH)):
                    if validate_image(user_input.get(MAP_IMG_PATH)):
                        self.options[self.sel_mower_id][MAP_IMG_PATH] = user_input.get(
                            MAP_IMG_PATH
                        )
                    else:
                        errors[MAP_IMG_PATH] = "not_image"
                else:
                    errors[MAP_IMG_PATH] = "not_file"

            if user_input.get(MAP_PATH_COLOR):
                path_color = ValidateRGB(user_input.get(MAP_PATH_COLOR))
                if path_color.is_valid():
                    self.options[self.sel_mower_id][MAP_PATH_COLOR] = path_color.rgb_val
                else:
                    errors[MAP_PATH_COLOR] = "color_error"

            if validate_rotation(user_input.get(MAP_IMG_ROTATION, 0)):
                self.options[self.sel_mower_id][MAP_IMG_ROTATION] = int(
                    user_input.get(MAP_IMG_ROTATION, 0)
                )
            else:
                errors[MAP_IMG_ROTATION] = "rotation_error"

            if user_input.get(HOME_LOCATION):
                pnt_validator = ValidatePointString(user_input.get(HOME_LOCATION))
                pnt_valid, pnt_error = pnt_validator.is_valid()

                if pnt_valid:
                    self.options[self.sel_mower_id][HOME_LOCATION] = [
                        pnt_validator.point.x,
                        pnt_validator.point.y,
                    ]
                else:
                    errors[HOME_LOCATION] = pnt_error
            self.options[self.sel_mower_id][ADD_IMAGES] = user_input.get(ADD_IMAGES, [])

            if not errors:
                return await self._update_config()
            _LOGGER.debug("Errors: %s", errors)

        path_color_str = ",".join(
            [str(i) for i in self.options[self.sel_mower_id].get(MAP_PATH_COLOR)]
        )

        gps_top_left = ""
        gps_bottom_right = ""
        home_location = ""
        if self.options[self.sel_mower_id][GPS_BOTTOM_RIGHT] != "":
            gps_bottom_right = ",".join(
                [str(x) for x in self.options[self.sel_mower_id][GPS_BOTTOM_RIGHT]]
            )

        if self.options[self.sel_mower_id][GPS_TOP_LEFT] != "":
            gps_top_left = ",".join(
                [str(x) for x in self.options[self.sel_mower_id][GPS_TOP_LEFT]]
            )

        if self.options[self.sel_mower_id][HOME_LOCATION] != "":
            home_location = ",".join(
                [str(x) for x in self.options[self.sel_mower_id][HOME_LOCATION]]
            )

        mwr_options_dict = {}
        for mwr in self.mower_idx:
            if mwr["id"] != self.sel_mower_id:
                mwr_options_dict[mwr["id"]] = mwr["name"]

        data_schema = {
            vol.Required(
                ENABLE_IMAGE,
                default=self.options[self.sel_mower_id].get(ENABLE_IMAGE),
            ): bool,
            vol.Required(GPS_TOP_LEFT, default=gps_top_left): str,
            vol.Required(GPS_BOTTOM_RIGHT, default=gps_bottom_right): str,
            vol.Required(
                MAP_IMG_ROTATION,
                default=self.options[self.sel_mower_id].get(MAP_IMG_ROTATION),
            ): int,
            vol.Required(
                MOWER_IMG_PATH,
                default=self.options[self.sel_mower_id].get(MOWER_IMG_PATH),
            ): str,
            vol.Required(
                MAP_IMG_PATH,
                default=self.options[self.sel_mower_id].get(MAP_IMG_PATH),
            ): str,
            vol.Required(MAP_PATH_COLOR, default=path_color_str): str,
            vol.Optional(HOME_LOCATION, default=home_location): str,
            vol.Optional(
                ADD_IMAGES,
                default=self.options[self.sel_mower_id].get(ADD_IMAGES, []),
            ): cv.multi_select(mwr_options_dict),
        }

        return self.async_show_form(
            step_id="image_config", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def _update_config(self):
        """Update config entry options."""
        if isinstance(self.options.get(CONF_ZONES), dict):
            self.options[CONF_ZONES] = json.dumps(self.options.get(CONF_ZONES))

        return self.async_create_entry(title="", data=self.options)

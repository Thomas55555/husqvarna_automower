"""Tests for config flow module."""
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from homeassistant.data_entry_flow import FlowResultType

from ..const import (
    ADD_IMAGES,
    ENABLE_IMAGE,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    HOME_LOCATION,
    MAP_IMG_PATH,
    MAP_IMG_ROTATION,
    MAP_PATH_COLOR,
    MOWER_IMG_PATH,
    ZONE_COLOR,
    ZONE_COORD,
    ZONE_DEL,
    ZONE_DISPLAY,
    ZONE_FINISH,
    ZONE_MOWERS,
    ZONE_NAME,
    ZONE_NEW,
    ZONE_SEL,
)
from .const import (
    AUTOMER_DM_CONFIG,
    MWR_ONE_ID,
    MWR_TWO_ID,
)

from .test_common import setup_entity


def get_suggested(schema, key):
    """Get suggested value for key in voluptuous schema."""
    for k in schema:
        if k == key:
            if k.description is None or "suggested_value" not in k.description:
                return None
            return k.description["suggested_value"]
    # Wanted key absent from schema
    raise KeyError


async def test_options_init(hass: HomeAssistant) -> None:
    """Test option flow init"""

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        {},
    ):
        config_entry = await setup_entity(hass, dual_mower=True)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"


async def test_options_image_config_existing_options(hass: HomeAssistant) -> None:
    """Test Image Config option flow."""
    config_entry = await setup_entity(hass, dual_mower=True)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "image_select"}
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"selected_image": "Test Mower 1"}
    )


async def test_options_image_config_existing_options_bad_zone(
    hass: HomeAssistant,
) -> None:
    """Test Image Config option flow where the configured zones is not a dict."""
    options = AUTOMER_DM_CONFIG.copy()
    options["configured_zones"] = "[]"

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass, dual_mower=True)

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "image_select"}
        )

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_image": "Test Mower 1"}
        )


async def test_options_image_config(hass: HomeAssistant) -> None:
    """Test Image Config option flow."""

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        {},
    ):
        config_entry = await setup_entity(hass, dual_mower=True)

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "image_select"}
        )
        await hass.async_block_till_done()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "image_select"

        assert result["data_schema"].schema["selected_image"].config["options"] == [
            "Test Mower 1",
            "Test Mower 2",
        ]
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_image": "Test Mower 1"}
        )
        await hass.async_block_till_done()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "image_config"

        # Get Mower One
        schema = result["data_schema"].schema
        assert get_suggested(schema, MAP_IMG_ROTATION) is None
        assert get_suggested(schema, ENABLE_IMAGE) is None
        assert get_suggested(schema, MOWER_IMG_PATH) is None
        assert get_suggested(schema, MAP_IMG_PATH) is None
        assert schema[ADD_IMAGES].options == {MWR_TWO_ID: "Test Mower 2"}

        # Disable Image, nothing else
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ENABLE_IMAGE: False}
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY

        # Restart flow
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "image_select"}
        )

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_image": "Test Mower 1"}
        )

        # Enable Image, nothing else
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ENABLE_IMAGE: True}
        )
        await hass.async_block_till_done()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "image_config"
        assert result["errors"][GPS_BOTTOM_RIGHT] == "points_match"

        # Enable Image, provide invalid top left point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "235.5411008,-82.5527418",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {GPS_TOP_LEFT: "not_wgs84"}

        # Enable Image, provide invalid bottom right point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "235.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {GPS_BOTTOM_RIGHT: "not_wgs84"}

        # Enable Image, provide valid points, bad path for mower
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MOWER_IMG_PATH: "custom_components/husqvarna_automower"
                "/tests/resources/missing.png",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MOWER_IMG_PATH: "not_file"}

        # Enable Image, provide valid points, bad image for mower
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MOWER_IMG_PATH: "custom_components/husqvarna_automower"
                "/tests/resources/bad_image.png",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MOWER_IMG_PATH: "not_image"}

        # Enable Image, provide valid points, bad path for map
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_PATH: "custom_components/husqvarna_automower"
                "/tests/resources/missing.png",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MAP_IMG_PATH: "not_file"}

        # Enable Image, provide valid points, bad image for map
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_PATH: "custom_components/husqvarna_automower/"
                "tests/resources/bad_image.png",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MAP_IMG_PATH: "not_image"}

        # Enable Image, provide valid points, bad color
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_PATH_COLOR: "-100, 0, 0",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MAP_PATH_COLOR: "color_error"}

        # Enable Image, provide valid points, bad rotation
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_ROTATION: -500,
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {MAP_IMG_ROTATION: "rotation_error"}

        # Enable Image, provide valid corner points, bad home point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                HOME_LOCATION: "35.54028774,-282.5526962",
            },
        )
        await hass.async_block_till_done()
        assert result["errors"] == {HOME_LOCATION: "not_wgs84"}

        # Enable Image, provide valid points
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_IMAGE: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                HOME_LOCATION: "35.54028774,-82.5526962",
            },
        )
        await hass.async_block_till_done()
        assert "errors" not in result


async def test_options_zone_config(hass: HomeAssistant) -> None:
    """Test Zone Config option flow (geofence_init)."""
    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        {},
    ):
        config_entry = await setup_entity(hass, dual_mower=True)

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "geofence_init"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "geofence_init"

        assert result["data_schema"].schema[ZONE_SEL].config["options"] == [
            {"label": ZONE_NEW, "value": ZONE_NEW},
            {"label": ZONE_FINISH, "value": ZONE_FINISH},
        ]

        # Add a new zone
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ZONE_SEL: ZONE_NEW}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zone_edit"
        schema = result["data_schema"].schema
        assert schema[ZONE_MOWERS].options == {
            MWR_ONE_ID: "Test Mower 1",
            MWR_TWO_ID: "Test Mower 2",
        }

        # Create Zone, invalid point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ZONE_COORD: "35.5408367,-82.5524521 35.5403893,-82.552613;35.5399462,"
                "-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "255,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [MWR_TWO_ID],
            },
        )

        assert result["errors"] == {"zone_coordinates": "invalid_str"}

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zone_edit"

        # Create Zone, less than 4 points
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "255,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [MWR_TWO_ID],
            },
        )

        assert result["errors"] == {"zone_coordinates": "too_few_points"}

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zone_edit"

        # Create Zone, bad RGB
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613;35.5399462,"
                "-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "500,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [MWR_TWO_ID],
            },
        )

        assert result["errors"] == {ZONE_COLOR: "color_error"}

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zone_edit"

        # Create Zone, no mower selected
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,"
                "-82.552613;35.5399462,-82.5506738;35.5403827,"
                "-82.5505236;35.5408367,-82.5524521",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "255,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [],
            },
        )

        assert result["errors"] == {ZONE_MOWERS: "need_one_mower"}

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zone_edit"

        # Create Zone, provide valid points
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613;35.5399462,"
                "-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "255,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [MWR_TWO_ID],
            },
        )

        assert result["errors"] is None

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "geofence_init"

        # Ensure zone was created
        assert result["data_schema"].schema[ZONE_SEL].config["options"] == [
            {"label": ZONE_NEW, "value": ZONE_NEW},
            {"label": "Front Garden", "value": "front_garden"},
            {"label": ZONE_FINISH, "value": ZONE_FINISH},
        ]

        # Save Zone
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ZONE_SEL: ZONE_FINISH}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY

        # Verify Zone was created

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "geofence_init"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "geofence_init"

        assert result["data_schema"].schema[ZONE_SEL].config["options"] == [
            {"label": ZONE_NEW, "value": ZONE_NEW},
            {"label": "Front Garden", "value": "front_garden"},
            {"label": ZONE_FINISH, "value": ZONE_FINISH},
        ]

        # Edit zone
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ZONE_SEL: "front_garden"}
        )

        # Delete Zone
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {ZONE_DEL: True},
        )

        assert result["errors"] is None

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "geofence_init"

        # Ensure zone was deleted
        assert result["data_schema"].schema[ZONE_SEL].config["options"] == [
            {"label": ZONE_NEW, "value": ZONE_NEW},
            {"label": ZONE_FINISH, "value": ZONE_FINISH},
        ]

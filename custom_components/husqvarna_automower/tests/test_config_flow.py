"""Tests for config flow module."""
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import (
    ADD_CAMERAS,
    DOMAIN,
    ENABLE_CAMERA,
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
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_DM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_TWO_ID,
)


def get_suggested(schema, key):
    """Get suggested value for key in voluptuous schema."""
    for k in schema:
        if k == key:
            if k.description is None or "suggested_value" not in k.description:
                return None
            return k.description["suggested_value"]
    # Wanted key absent from schema
    raise Exception


async def test_options_init(hass: HomeAssistant) -> None:
    """Test option flow init"""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options={},
        entry_id="automower_test",
        title="Automower Test",
    )
    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"


async def test_options_camera_config_existing_options(hass: HomeAssistant) -> None:
    """Test Camera Config option flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=AUTOMER_DM_CONFIG,
        entry_id="automower_test",
        title="Automower Test",
    )
    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "camera_select"}
        )

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_camera": "Test Mower 1"}
        )


async def test_options_camera_config(hass: HomeAssistant) -> None:
    """Test Camera Config option flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options={},
        entry_id="automower_test",
        title="Automower Test",
    )
    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "camera_select"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "camera_select"

        assert result["data_schema"].schema["selected_camera"].config["options"] == [
            "Test Mower 1",
            "Test Mower 2",
        ]
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_camera": "Test Mower 1"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "camera_config"

        # Get Mower One
        schema = result["data_schema"].schema
        assert get_suggested(schema, MAP_IMG_ROTATION) is None
        assert get_suggested(schema, ENABLE_CAMERA) is None
        assert get_suggested(schema, MOWER_IMG_PATH) is None
        assert get_suggested(schema, MAP_IMG_PATH) is None
        assert schema[ADD_CAMERAS].options == {MWR_TWO_ID: "Test Mower 2"}

        # Disable Camera, nothing else
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ENABLE_CAMERA: False}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY

        # Restart flow
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "select"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "camera_select"}
        )

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"selected_camera": "Test Mower 1"}
        )

        # Enable Camera, nothing else
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {ENABLE_CAMERA: True}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "camera_config"
        assert result["errors"][GPS_BOTTOM_RIGHT] == "points_match"

        # Enable Camera, provide invalid top left point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "235.5411008,-82.5527418",
            },
        )

        assert result["errors"] == {GPS_TOP_LEFT: "not_wgs84"}

        # Enable Camera, provide invalid bottom right point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "235.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
            },
        )

        assert result["errors"] == {GPS_BOTTOM_RIGHT: "not_wgs84"}

        # Enable Camera, provide valid points, bad path for mower
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MOWER_IMG_PATH: "custom_components/husqvarna_automower/tests/resources/missing.png",
            },
        )

        assert result["errors"] == {MOWER_IMG_PATH: "not_file"}

        # Enable Camera, provide valid points, bad image for mower
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MOWER_IMG_PATH: "custom_components/husqvarna_automower/tests/resources/bad_image.png",
            },
        )

        assert result["errors"] == {MOWER_IMG_PATH: "not_image"}

        # Enable Camera, provide valid points, bad path for map
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_PATH: "custom_components/husqvarna_automower/tests/resources/missing.png",
            },
        )

        assert result["errors"] == {MAP_IMG_PATH: "not_file"}

        # Enable Camera, provide valid points, bad image for map
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_PATH: "custom_components/husqvarna_automower/tests/resources/bad_image.png",
            },
        )

        assert result["errors"] == {MAP_IMG_PATH: "not_image"}

        # Enable Camera, provide valid points, bad color
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_PATH_COLOR: "-100, 0, 0",
            },
        )

        assert result["errors"] == {MAP_PATH_COLOR: "color_error"}

        # Enable Camera, provide valid points, bad rotation
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                MAP_IMG_ROTATION: -500,
            },
        )

        assert result["errors"] == {MAP_IMG_ROTATION: "rotation_error"}

        # Enable Camera, provide valid corner points, bad home point
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                HOME_LOCATION: "35.54028774,-282.5526962",
            },
        )

        assert result["errors"] == {HOME_LOCATION: "not_wgs84"}

        # Enable Camera, provide valid points
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                ENABLE_CAMERA: True,
                GPS_BOTTOM_RIGHT: "35.539442,-82.5504646",
                GPS_TOP_LEFT: "35.5411008,-82.5527418",
                HOME_LOCATION: "35.54028774,-82.5526962",
            },
        )

        assert "errors" not in result


async def test_options_zone_config(hass: HomeAssistant) -> None:
    """Test Zone Config option flow (geofence_init)."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options={},
        entry_id="automower_test",
        title="Automower Test",
    )
    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

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
                ZONE_COORD: "35.5408367,-82.5524521 35.5403893,-82.552613;35.5399462,-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
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
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613;35.5399462,-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
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
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613;35.5399462,-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
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
                ZONE_COORD: "35.5408367,-82.5524521;35.5403893,-82.552613;35.5399462,-82.5506738;35.5403827,-82.5505236;35.5408367,-82.5524521",
                ZONE_NAME: "Front Garden",
                ZONE_COLOR: "255,0,0",
                ZONE_DISPLAY: True,
                ZONE_MOWERS: [MWR_TWO_ID],
            },
        )

        assert result["errors"] == None

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

        assert result["errors"] == None

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "geofence_init"

        # Ensure zone was deleted
        assert result["data_schema"].schema[ZONE_SEL].config["options"] == [
            {"label": ZONE_NEW, "value": ZONE_NEW},
            {"label": ZONE_FINISH, "value": ZONE_FINISH},
        ]

"""Tests for init module."""
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import GetMowerData, MowerApiConnectionsError


from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import async_get

from .. import async_reload_entry, update_listener
from ..const import DOMAIN, MAP_IMG_ROTATION, MAP_PATH_COLOR, HOME_LOCATION
from .const import (
    AUTOMOWER_CONFIG_DATA_BAD_SCOPE,
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_TWO_ID,
)

from .test_common import setup_entity, configure_application_credentials


@pytest.mark.asyncio
async def test_load_unload(hass: HomeAssistant):
    """test automower initialization"""

    await configure_application_credentials(hass)

    config_entry = await setup_entity(hass)
    assert config_entry.state == ConfigEntryState.LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            data=AUTOMOWER_SM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        with patch(
            "aioautomower.GetMowerData",
            return_value=AsyncMock(name="GetMowerMock", model=GetMowerData, data={}),
        ):
            # Reload entry - No real test, just calling the function
            await async_reload_entry(hass, config_entry)
            assert config_entry.state == ConfigEntryState.LOADED

            # Update Listner - No real test, just calling the function
            await update_listener(hass, config_entry)
            assert config_entry.state == ConfigEntryState.LOADED

            assert await config_entry.async_unload(hass)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.NOT_LOADED

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            ws_and_token_session=AsyncMock(side_effect=AsyncioTimeoutError),
        ),
    ):
        # Timeout Error
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.SETUP_RETRY

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            ws_and_token_session=AsyncMock(side_effect=Exception("Test Exception")),
        ),
    ):
        with patch(
            "aioautomower.GetMowerData",
            return_value=AsyncMock(name="GetMowerMock", model=GetMowerData, data={}),
        ):
            # Genric Error
            await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.SETUP_ERROR

            assert await config_entry.async_unload(hass)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.NOT_LOADED

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            ws_and_token_session=AsyncMock(),
        ),
    ):
        with patch(
            "aioautomower.GetMowerData",
            return_value=AsyncMock(
                name="GetMowerMock",
                model=GetMowerData,
                async_mower_state=AsyncMock(
                    side_effect=MowerApiConnectionsError("test")
                ),
            ),
        ):
            await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.SETUP_ERROR


@pytest.mark.asyncio
async def test_load_unload_wrong_scope(hass: HomeAssistant):
    """test automower initialization, wrong token scope"""

    await configure_application_credentials(hass)

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMOWER_CONFIG_DATA",
        AUTOMOWER_CONFIG_DATA_BAD_SCOPE,
    ):
        config_entry = await setup_entity(hass)

        issue_registry = async_get(hass)
        issue = issue_registry.async_get_issue(DOMAIN, "wrong_scope")
        assert issue is not None

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_async_migrate_entry_2_to_4(hass: HomeAssistant):
    """test automower migration from version 2 to 4"""

    await configure_application_credentials(hass)

    old_options_fmt = {
        "enable_camera": True,
        "gps_top_left": [35.5411008, -82.5527418],
        "gps_bottom_right": [35.539442, -82.5504646],
        "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
        "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
    }

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        old_options_fmt,
    ):
        config_entry = await setup_entity(hass, dual_mower=True, conf_version=2)

        assert config_entry.version == 4
        assert config_entry.options.get("enable_camera") is None
        assert config_entry.options.get("gps_top_left") is None
        assert config_entry.options.get("gps_bottom_right") is None
        assert config_entry.options.get("mower_img_path") is None
        assert config_entry.options.get("map_img_path") is None

        # pylint: disable=unused-variable
        for mwr, config in config_entry.options.items():
            for opt_key in old_options_fmt:  # pylint: disable=consider-using-dict-items
                if opt_key != "enable_camera":
                    assert config[opt_key] == old_options_fmt[opt_key]
                if opt_key == "enable_camera":
                    assert config["enable_image"] == old_options_fmt["enable_camera"]

            assert config[MAP_IMG_ROTATION] == 0
            assert config[MAP_PATH_COLOR] == [255, 0, 0]
            assert config[HOME_LOCATION] == ""

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_async_migrate_entry_3_to_4(hass: HomeAssistant):
    """test automower migration from version 3 to 4"""

    await configure_application_credentials(hass)

    old_options_fmt = {
        "configured_zones": '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521],'
        " [35.5403893, -82.552613], [35.5399462, -82.5506738], [35.5403827, -82.5505236],"
        ' [35.5408367, -82.5524521]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0",'
        ' "1c7aec7b-06ff-462e-b307-7c6ae4469047"], "color": [255, 0, 0], "name": "Front Garden",'
        ' "display": true}, "west_italian_garden": {"zone_coordinates": [[35.5402452, -82.552951],'
        " [35.540075, -82.5530073], [35.5399943, -82.5526425], [35.5401536, -82.5525835],"
        ' [35.5402452, -82.552951]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"],'
        ' "color": [0, 255, 0], "name": "West Italian Garden", "display": true},'
        ' "east_italian_garden": {"zone_coordinates": [[35.5398415, -82.5512532],'
        " [35.5396822, -82.5513122], [35.5395927, -82.550942], [35.5397498, -82.5508803],"
        ' [35.5398415, -82.5512532]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"],'
        ' "color": [0, 0, 255], "name": "East Italian Garden", "display": true}, "shrub_garden":'
        ' {"zone_coordinates": [[35.5397978, -82.5531334], [35.539357, -82.553289],'
        " [35.5393198, -82.553128], [35.5394028, -82.5530529], [35.5394443, -82.5529751],"
        " [35.5394639, -82.5528866], [35.5394901, -82.5528303], [35.539645, -82.5529242],"
        ' [35.5397629, -82.5529698], [35.5397978, -82.5531334]], "sel_mowers": '
        '["c7233734-b219-4287-a173-08e3643f89f0"], "color": [100, 100, 0], "name": "Shrub Garden",'
        ' "display": true}}',
        MWR_ONE_ID: {
            "enable_camera": True,
            "gps_top_left": [35.5411008, -82.5527418],
            "gps_bottom_right": [35.539442, -82.5504646],
            "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
            "map_img_path": "custom_components/husqvarna_automower"
            "/tests/resources/biltmore-min.png",
            "map_path_color": [255, 0, 0],
            "map_img_rotation": -16.10,
            "home_location": [35.54028774, -82.5526962],
            "additional_mowers": [MWR_TWO_ID],
        },
        MWR_TWO_ID: {
            "enable_camera": True,
            "gps_top_left": [35.5411008, -82.5527418],
            "gps_bottom_right": [35.539442, -82.5504646],
            "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
            "map_img_path": "custom_components/husqvarna_automower/"
            "tests/resources/biltmore-min.png",
            "map_path_color": [0, 0, 255],
            "map_img_rotation": -16.10,
            "home_location": [35.5409924, -82.5525482],
            "additional_mowers": [],
        },
    }

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        old_options_fmt,
    ):
        config_entry = await setup_entity(hass, dual_mower=True, conf_version=3)

        assert config_entry.version == 4

        for mwr, config in config_entry.options.items():
            if mwr in [MWR_ONE_ID, MWR_TWO_ID]:
                assert "enable_camera" not in config
                assert "enable_image" in config

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED

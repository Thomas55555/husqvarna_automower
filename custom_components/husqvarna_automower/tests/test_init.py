"""Tests for init module."""
from asyncio.exceptions import TimeoutError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import async_get
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .. import async_reload_entry, update_listener
from ..const import DOMAIN, MAP_IMG_ROTATION, MAP_PATH_COLOR, HOME_LOCATION
from .const import (
    AUTOMER_SM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_CONFIG_DATA_BAD_SCOPE,
    AUTOMOWER_SM_SESSION_DATA,
    AUTOMOWER_DM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_TWO_ID,
)


async def configure_application_credentials(hass: HomeAssistant):
    """Configure application credentials"""
    app_cred_config_entry = MockConfigEntry(
        domain="application_credentials",
        data={},
        entry_id="application_credentials",
        title="Application Credentials",
    )
    app_cred_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(app_cred_config_entry.entry_id)

    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(
            "test_client_id",
            "test_config_secret",
        ),
    )


@pytest.mark.asyncio
async def test_load_unload(hass: HomeAssistant):
    """test automower initialization"""

    await configure_application_credentials(hass)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=AUTOMER_SM_CONFIG,
        entry_id="automower_test",
        title="Automower Test",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            close=AsyncMock(),
            data=AUTOMOWER_SM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

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
            connect=AsyncMock(side_effect=TimeoutError),
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
            close=AsyncMock(side_effect=Exception),
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            register_token_callback=MagicMock(),
            connect=AsyncMock(side_effect=Exception("Test Exception")),
        ),
    ):
        # Genric Error
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.SETUP_ERROR


@pytest.mark.asyncio
async def test_load_unload_wrong_scope(hass: HomeAssistant):
    """test automower initialization, wrong token scope"""

    await configure_application_credentials(hass)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA_BAD_SCOPE,
        options=AUTOMER_SM_CONFIG,
        entry_id="automower_test",
        title="Automower Test",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(register_token_callback=MagicMock()),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        issue_registry = async_get(hass)
        issue = issue_registry.async_get_issue(DOMAIN, "wrong_scope")
        assert issue is not None

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_async_migrate_entry_2_to_4(hass: HomeAssistant):
    """test automower migration from version 2 to 3"""

    await configure_application_credentials(hass)

    old_options_fmt = {
        "enable_camera": True,
        "gps_top_left": [35.5411008, -82.5527418],
        "gps_bottom_right": [35.539442, -82.5504646],
        "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
        "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=old_options_fmt,
        entry_id="automower_test",
        title="Automower Test",
        version=2,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            name="AutomowerMockSession",
            model=AutomowerSession,
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            close=AsyncMock(),
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        assert config_entry.version == 4
        assert config_entry.options.get("enable_camera") is None
        assert config_entry.options.get("gps_top_left") is None
        assert config_entry.options.get("gps_bottom_right") is None
        assert config_entry.options.get("mower_img_path") is None
        assert config_entry.options.get("map_img_path") is None

        for mwr, config in config_entry.options.items():
            for opt_key in old_options_fmt:
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
        "configured_zones": '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521], [35.5403893, -82.552613], [35.5399462, -82.5506738], [35.5403827, -82.5505236], [35.5408367, -82.5524521]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0", "1c7aec7b-06ff-462e-b307-7c6ae4469047"], "color": [255, 0, 0], "name": "Front Garden", "display": true}, "west_italian_garden": {"zone_coordinates": [[35.5402452, -82.552951], [35.540075, -82.5530073], [35.5399943, -82.5526425], [35.5401536, -82.5525835], [35.5402452, -82.552951]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 255, 0], "name": "West Italian Garden", "display": true}, "east_italian_garden": {"zone_coordinates": [[35.5398415, -82.5512532], [35.5396822, -82.5513122], [35.5395927, -82.550942], [35.5397498, -82.5508803], [35.5398415, -82.5512532]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 0, 255], "name": "East Italian Garden", "display": true}, "shrub_garden": {"zone_coordinates": [[35.5397978, -82.5531334], [35.539357, -82.553289], [35.5393198, -82.553128], [35.5394028, -82.5530529], [35.5394443, -82.5529751], [35.5394639, -82.5528866], [35.5394901, -82.5528303], [35.539645, -82.5529242], [35.5397629, -82.5529698], [35.5397978, -82.5531334]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [100, 100, 0], "name": "Shrub Garden", "display": true}}',
        MWR_ONE_ID: {
            "enable_camera": True,
            "gps_top_left": [35.5411008, -82.5527418],
            "gps_bottom_right": [35.539442, -82.5504646],
            "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
            "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
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
            "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
            "map_path_color": [0, 0, 255],
            "map_img_rotation": -16.10,
            "home_location": [35.5409924, -82.5525482],
            "additional_mowers": [],
        },
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=old_options_fmt,
        entry_id="automower_test",
        title="Automower Test",
        version=3,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            name="AutomowerMockSession",
            model=AutomowerSession,
            data=AUTOMOWER_DM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            close=AsyncMock(),
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        assert config_entry.version == 4

        for mwr, config in config_entry.options.items():
            if mwr in [MWR_ONE_ID, MWR_TWO_ID]:
                assert "enable_camera" not in config
                assert "enable_image" in config

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.NOT_LOADED

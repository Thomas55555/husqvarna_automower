"""Tests for camera module."""
import asyncio
import io
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import PIL.Image as Image
import pytest
from aioautomower import AutomowerSession
from homeassistant.components.camera import SUPPORT_ON_OFF
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..camera import AutomowerCamera
from ..const import CONF_ZONES, DOMAIN, ENABLE_CAMERA
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_DM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
    MWR_TWO_ID,
    MWR_TWO_IDX,
)


@pytest.mark.asyncio
async def setup_camera(
    hass: HomeAssistant,
    mwr_id: int,
    mwr_idx: str,
    enable_camera: bool = True,
    replacement_conf_zones: str = "",
):
    """Set up camera and config entry"""

    options = AUTOMER_DM_CONFIG.copy()

    if replacement_conf_zones != "":
        options[CONF_ZONES] = replacement_conf_zones

    options[mwr_id]["enable_camera"] = enable_camera

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=options,
        entry_id="automower_test",
        title="Automower Test",
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
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        camera = AutomowerCamera(automower_coordinator_mock, mwr_idx, config_entry)
    return camera, automower_coordinator_mock


@pytest.mark.asyncio
async def test_load_camera_enabled(hass: HomeAssistant):
    """test automower initialization"""
    camera_one, automower_coordinator_mock = await setup_camera(
        hass, MWR_ONE_ID, MWR_ONE_IDX
    )
    camera_two, automower_coordinator_mock = await setup_camera(
        hass, MWR_TWO_ID, MWR_TWO_IDX
    )

    assert camera_one.model == "450XH-TEST"
    assert camera_one.options.get(ENABLE_CAMERA) is True

    assert camera_two.model == "450XH-TEST"
    assert camera_two.options.get(ENABLE_CAMERA) is True

    # Enabled Camera call register_data_callback
    automower_coordinator_mock.session.register_data_callback.assert_called_once()

    # Generate Image
    await asyncio.to_thread(camera_one._generate_image, {})
    await asyncio.to_thread(camera_two._generate_image, {})

    # Generate Image, with freq calc - Mower One
    camera_one._last_update = datetime.now() - timedelta(seconds=60)
    await asyncio.to_thread(camera_one._generate_image, {})
    assert camera_one._update_frequency == 60
    assert camera_one._avg_update_frequency == 30.0

    # Generate Image, with freq calc - Mower Two
    camera_two._last_update = datetime.now() - timedelta(seconds=60)
    await asyncio.to_thread(camera_two._generate_image, {})
    assert camera_two._update_frequency == 60
    assert camera_two._avg_update_frequency == 30.0

    # Ensure output directory is present
    output_path = Path("custom_components/husqvarna_automower/tests/output/")
    output_path.mkdir(parents=True, exist_ok=True)

    # Image to bytes, no resize - Mower One
    image_bytes = await camera_one.async_camera_image()
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_one_out.png").as_posix())

    # Image to bytes, resize - Mower One
    image_bytes = await camera_one.async_camera_image(300, 300)
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_one_out_300.png").as_posix())

    # Image to bytes, no resize - Mower Two
    image_bytes = await camera_two.async_camera_image()
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_two_out.png").as_posix())

    # Image to bytes, resize - Mower Two
    image_bytes = await camera_two.async_camera_image(300, 300)
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_two_out_300.png").as_posix())

    # Mower at home
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "CHARGING"
    assert camera_one._is_home is True
    await asyncio.to_thread(camera_one._generate_image, {})

    # Mower not at home
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "MOWING"
    assert camera_one._is_home is False
    await asyncio.to_thread(camera_one._generate_image, {})

    # Mower, no home location
    camera_one.home_location = None
    await asyncio.to_thread(camera_one._generate_image, {})

    # Single position history
    exp_result = [
        automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
            "positions"
        ][0]
    ] + automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
        "positions"
    ]
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
        "positions"
    ] = [
        automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
            "positions"
        ][0]
    ]
    await asyncio.to_thread(camera_one._generate_image, {})
    assert camera_one._position_history[MWR_ONE_ID] == exp_result

    # Single position history, but it's the first position update
    exp_result = [
        automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
            "positions"
        ][0]
    ]
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
        "positions"
    ] = exp_result
    camera_one._position_history = {}
    await asyncio.to_thread(camera_one._generate_image, {})
    assert camera_one._position_history[MWR_ONE_ID] == exp_result


@pytest.mark.asyncio
async def test_load_camera_disabled(hass: HomeAssistant):
    """test automower initialization"""
    camera, automower_coordinator_mock = await setup_camera(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_camera=False
    )

    assert camera.model == "450XH-TEST"
    assert camera.supported_features == SUPPORT_ON_OFF
    assert camera.options.get(ENABLE_CAMERA) is False
    await asyncio.to_thread(camera.turn_on)
    automower_coordinator_mock.session.register_data_callback.assert_called_once()
    await asyncio.to_thread(camera.turn_off)
    automower_coordinator_mock.session.unregister_data_callback.assert_called_once()


@pytest.mark.asyncio
async def test_load_camera_enabled_bad_zone(hass: HomeAssistant):
    """test automower initialization bad zone, not a dict"""
    camera, automower_coordinator_mock = await setup_camera(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_camera=True, replacement_conf_zones="[]"
    )


@pytest.mark.asyncio
async def test_load_camera_enabled_empty_zone(hass: HomeAssistant):
    """test automower initialization empty zone dict"""
    camera, automower_coordinator_mock = await setup_camera(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_camera=True, replacement_conf_zones="{}"
    )


@pytest.mark.asyncio
async def test_load_camera_enabled_zone_without_mower(hass: HomeAssistant):
    """test automower initialization with a zone, but no mower selected"""
    replacement_zones = '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521], [35.5403893, -82.552613], [35.5399462, -82.5506738]], "sel_mowers": [], "color": [255, 0, 0], "name": "Front Garden", "display": true}}'
    camera, automower_coordinator_mock = await setup_camera(
        hass,
        MWR_ONE_ID,
        MWR_ONE_IDX,
        enable_camera=True,
        replacement_conf_zones=replacement_zones,
    )


@pytest.mark.asyncio
async def test_load_camera_enabled_zone_no_coordinates(hass: HomeAssistant):
    """test automower initialization with a zone, but no coordinates in zone"""
    replacement_zones = '{"front_garden": {"zone_coordinates": [], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [255, 0, 0], "name": "Front Garden", "display": true}}'
    camera, automower_coordinator_mock = await setup_camera(
        hass,
        MWR_ONE_ID,
        MWR_ONE_IDX,
        enable_camera=True,
        replacement_conf_zones=replacement_zones,
    )

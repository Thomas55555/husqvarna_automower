"""Tests for camera module."""
import asyncio
import io
import logging
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

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def setup_camera(
    hass: HomeAssistant,
    mwr_id: int,
    mwr_idx: str,
    enable_camera: bool = True,
    include_zones: bool = True,
):
    """Set up camera and config entry"""

    options = AUTOMER_DM_CONFIG.copy()

    if not include_zones:
        options[CONF_ZONES] = "[]"

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
async def test_load_camera_disabled_no_zone(hass: HomeAssistant):
    """test automower initialization no zones"""
    camera, automower_coordinator_mock = await setup_camera(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_camera=True, include_zones=False
    )

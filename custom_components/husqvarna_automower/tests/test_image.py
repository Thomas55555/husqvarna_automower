"""Tests for image module."""
import asyncio
import io
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import pytest
from homeassistant.core import HomeAssistant

from ..image import AutomowerImage
from ..const import CONF_ZONES, DOMAIN, ENABLE_IMAGE
from .const import (
    AUTOMER_SM_CONFIG,
    AUTOMER_DM_CONFIG,
    MWR_ONE_ID,
    MWR_ONE_IDX,
    MWR_TWO_ID,
    MWR_TWO_IDX,
    ENABLE_IMAGE,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_load_image_disabled(hass: HomeAssistant):
    """test automower initialization"""

    options = AUTOMER_DM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = False
    options[MWR_TWO_ID][ENABLE_IMAGE] = False

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass, dual_mower=True)

    coordinator = hass.data[DOMAIN]["automower_test"]
    register_data_call_count = coordinator.session.register_data_callback.call_count

    image_one = AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)
    image_two = AutomowerImage(coordinator, MWR_TWO_IDX, config_entry, hass)

    assert image_one.options.get(ENABLE_IMAGE) is False
    assert image_two.options.get(ENABLE_IMAGE) is False

    # Disabled image call register_data_callback
    assert (
        coordinator.session.register_data_callback.call_count
        == register_data_call_count
    )

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_load_image_enabled(hass: HomeAssistant):
    """test automower initialization"""

    options = AUTOMER_DM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = True
    options[MWR_TWO_ID][ENABLE_IMAGE] = True

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_DM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass, dual_mower=True)

    coordinator = hass.data[DOMAIN]["automower_test"]
    register_data_call_count = coordinator.session.register_data_callback.call_count

    image_one = AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)
    image_two = AutomowerImage(coordinator, MWR_TWO_IDX, config_entry, hass)

    assert image_one.options.get(ENABLE_IMAGE) is True
    assert image_two.options.get(ENABLE_IMAGE) is True

    # Enable image call register_data_callback
    assert (
        coordinator.session.register_data_callback.call_count
        == register_data_call_count + 2
    )

    # Generate Image
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})
    # pylint: disable=protected-access
    await asyncio.to_thread(image_two._generate_image, {})

    # Ensure output directory is present
    output_path = Path("custom_components/husqvarna_automower/tests/output/")
    output_path.mkdir(parents=True, exist_ok=True)

    # Image to bytes - Mower One
    image_bytes = await image_one.async_image()
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_one_out.png").as_posix())

    # Image to bytes - Mower Two
    image_bytes = await image_two.async_image()
    image = Image.open(io.BytesIO(image_bytes))
    image.save(output_path.joinpath("mower_two_out.png").as_posix())

    # Ensure image to bytes could resize bytes if width/height was passed
    image_bytes = await image_one._image_to_bytes(400, 600)
    image = Image.open(io.BytesIO(image_bytes))
    assert image.width == 400
    assert image.height == 195  # Resize maintains aspect ratio

    # Mower at home
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "CHARGING"
    assert image_one.is_home is True
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})

    # Mower not at home
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"]["activity"] = "MOWING"
    assert image_one.is_home is False
    # pylint: disable=protected-access
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})

    # Mower, no home location
    image_one.home_location = None
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})

    # Single position history
    exp_result = [
        coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0]
    ] + coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"]
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"] = [
        coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0]
    ]
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})
    assert image_one._position_history[MWR_ONE_ID] == exp_result

    # Single position history, but it's the first position update
    exp_result = [coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0]]
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["positions"] = exp_result
    image_one._position_history = {}
    # pylint: disable=protected-access
    await asyncio.to_thread(image_one._generate_image, {})
    assert image_one._position_history[MWR_ONE_ID] == exp_result


@pytest.mark.asyncio
async def test_load_image_enabled_bad_zone(hass: HomeAssistant):
    """test automower initialization bad zone, not a dict"""
    options = AUTOMER_SM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = True
    options[CONF_ZONES] = "[]"

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_SM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass)

    coordinator = hass.data[DOMAIN]["automower_test"]
    AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)


@pytest.mark.asyncio
async def test_load_image_enabled_empty_zone(hass: HomeAssistant):
    """test automower initialization empty zone dict"""
    options = AUTOMER_SM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = True
    options[CONF_ZONES] = "{}"

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_SM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass)

    coordinator = hass.data[DOMAIN]["automower_test"]
    AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)


@pytest.mark.asyncio
async def test_load_image_enabled_zone_without_mower(hass: HomeAssistant):
    """test automower initialization with a zone, but no mower selected"""
    options = AUTOMER_SM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = True
    options[CONF_ZONES] = (
        '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521],'
        ' [35.5403893, -82.552613], [35.5399462, -82.5506738]], "sel_mowers": [],'
        ' "color": [255, 0, 0], "name": "Front Garden", "display": true}}'
    )

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_SM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass)

    coordinator = hass.data[DOMAIN]["automower_test"]
    AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)


@pytest.mark.asyncio
async def test_load_image_enabled_zone_no_coordinates(hass: HomeAssistant):
    """test automower initialization with a zone, but no coordinates in zone"""
    options = AUTOMER_SM_CONFIG.copy()
    options[MWR_ONE_ID][ENABLE_IMAGE] = True
    options[CONF_ZONES] = (
        '{"front_garden": {"zone_coordinates": [], "sel_mowers": '
        '["c7233734-b219-4287-a173-08e3643f89f0"], "color": [255, 0, 0],'
        ' "name": "Front Garden", "display": true}}'
    )

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_SM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass)

    coordinator = hass.data[DOMAIN]["automower_test"]
    AutomowerImage(coordinator, MWR_ONE_IDX, config_entry, hass)

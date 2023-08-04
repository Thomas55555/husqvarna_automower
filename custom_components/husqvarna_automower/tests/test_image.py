"""Tests for image module."""
import asyncio
import io
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import PIL.Image as Image
import pytest
from aioautomower import AutomowerSession
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..image import AutomowerImage
from ..const import CONF_ZONES, DOMAIN, ENABLE_IMAGE
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_DM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
    MWR_TWO_ID,
    MWR_TWO_IDX,
    ENABLE_IMAGE,
)


@pytest.mark.asyncio
async def setup_image(
    hass: HomeAssistant,
    mwr_id: int,
    mwr_idx: str,
    enable_image: bool = True,
    replacement_conf_zones: str = "",
):
    """Set up image and config entry"""

    options = AUTOMER_DM_CONFIG.copy()

    if replacement_conf_zones != "":
        options[CONF_ZONES] = replacement_conf_zones

    options[mwr_id][ENABLE_IMAGE] = enable_image

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

        mwr_img = AutomowerImage(
            automower_coordinator_mock, mwr_idx, config_entry, hass
        )
    return mwr_img, automower_coordinator_mock


@pytest.mark.asyncio
async def test_load_image_enabled(hass: HomeAssistant):
    """test automower initialization"""

    image_one, automower_coordinator_mock = await setup_image(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_image=False
    )
    image_two, automower_coordinator_mock = await setup_image(
        hass, MWR_TWO_ID, MWR_TWO_IDX, enable_image=False
    )

    assert image_one.options.get(ENABLE_IMAGE) is False

    assert image_two.options.get(ENABLE_IMAGE) is False

    # Disabled image call register_data_callback
    automower_coordinator_mock.session.register_data_callback.assert_not_called()

    image_one, automower_coordinator_mock = await setup_image(
        hass, MWR_ONE_ID, MWR_ONE_IDX
    )
    image_two, automower_coordinator_mock = await setup_image(
        hass, MWR_TWO_ID, MWR_TWO_IDX
    )

    assert image_one.options.get(ENABLE_IMAGE) is True

    assert image_two.options.get(ENABLE_IMAGE) is True

    # Enabled image call register_data_callback
    automower_coordinator_mock.session.register_data_callback.assert_called_once()

    # Generate Image
    await asyncio.to_thread(image_one._generate_image, {})
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
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "CHARGING"
    assert image_one.is_home is True
    await asyncio.to_thread(image_one._generate_image, {})

    # Mower not at home
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "MOWING"
    assert image_one.is_home is False
    await asyncio.to_thread(image_one._generate_image, {})

    # Mower, no home location
    image_one.home_location = None
    await asyncio.to_thread(image_one._generate_image, {})
    image_one._position_history = {}


@pytest.mark.asyncio
async def test_load_image_enabled_bad_zone(hass: HomeAssistant):
    """test automower initialization bad zone, not a dict"""
    image, automower_coordinator_mock = await setup_image(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_image=True, replacement_conf_zones="[]"
    )


@pytest.mark.asyncio
async def test_load_image_enabled_empty_zone(hass: HomeAssistant):
    """test automower initialization empty zone dict"""
    image, automower_coordinator_mock = await setup_image(
        hass, MWR_ONE_ID, MWR_ONE_IDX, enable_image=True, replacement_conf_zones="{}"
    )


@pytest.mark.asyncio
async def test_load_image_enabled_zone_without_mower(hass: HomeAssistant):
    """test automower initialization with a zone, but no mower selected"""
    replacement_zones = '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521], [35.5403893, -82.552613], [35.5399462, -82.5506738]], "sel_mowers": [], "color": [255, 0, 0], "name": "Front Garden", "display": true}}'
    image, automower_coordinator_mock = await setup_image(
        hass,
        MWR_ONE_ID,
        MWR_ONE_IDX,
        enable_image=True,
        replacement_conf_zones=replacement_zones,
    )


@pytest.mark.asyncio
async def test_load_image_enabled_zone_no_coordinates(hass: HomeAssistant):
    """test automower initialization with a zone, but no coordinates in zone"""
    replacement_zones = '{"front_garden": {"zone_coordinates": [], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [255, 0, 0], "name": "Front Garden", "display": true}}'
    image, automower_coordinator_mock = await setup_image(
        hass,
        MWR_ONE_ID,
        MWR_ONE_IDX,
        enable_image=True,
        replacement_conf_zones=replacement_zones,
    )

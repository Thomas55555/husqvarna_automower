"""Tests for device tracker module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from homeassistant.components.device_tracker import SourceType
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from ..device_tracker import AutomowerTracker, async_setup_entry
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
)
from .test_init import configure_application_credentials


@pytest.mark.asyncio
async def setup_device_tracker(hass: HomeAssistant, empty_positions: bool = False):
    """Set up device tracker and config entry"""

    await configure_application_credentials(hass)

    options = AUTOMER_DM_CONFIG

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=options,
        entry_id="automower_test",
        title="Automower Test",
    )

    config_entry.add_to_hass(hass)

    session_data = deepcopy(AUTOMOWER_SM_SESSION_DATA)

    if empty_positions:
        session_data["data"][MWR_ONE_IDX]["attributes"]["positions"] = []

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            name="AutomowerMockSession",
            model=AutomowerSession,
            data=session_data,
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_device_tracker_setup_no_pos(hass: HomeAssistant):
    """test device tracker without positions."""

    # Without positions
    await setup_device_tracker(hass, empty_positions=True)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    coordinator = hass.data[DOMAIN]["automower_test"]
    device_tracker = AutomowerTracker(coordinator, MWR_ONE_IDX)


@pytest.mark.asyncio
async def test_device_tracker_pos(hass: HomeAssistant):
    """test device tracker with positions."""
    await setup_device_tracker(hass, empty_positions=False)
    coordinator = hass.data[DOMAIN]["automower_test"]
    device_tracker = AutomowerTracker(coordinator, MWR_ONE_IDX)
    assert device_tracker._attr_unique_id == f"{MWR_ONE_ID}_dt"
    assert device_tracker.source_type == SourceType.GPS
    assert (
        device_tracker.latitude
        == AUTOMOWER_SM_SESSION_DATA["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
            "latitude"
        ]
    )
    assert (
        device_tracker.longitude
        == AUTOMOWER_SM_SESSION_DATA["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
            "longitude"
        ]
    )

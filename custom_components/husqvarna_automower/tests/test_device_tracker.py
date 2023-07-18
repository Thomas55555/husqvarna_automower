"""Tests for device tracker module."""
from copy import deepcopy
from unittest.mock import patch

import pytest
from homeassistant.components.device_tracker import SourceType
from homeassistant.core import HomeAssistant

from ..const import DOMAIN
from ..device_tracker import AutomowerTracker
from .const import (
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_device_tracker_setup_no_pos(hass: HomeAssistant):
    """test device tracker without positions."""

    # Without positions
    session = deepcopy(AUTOMOWER_SM_SESSION_DATA)
    session["data"][MWR_ONE_IDX]["attributes"]["positions"] = []

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMOWER_SM_SESSION_DATA",
        session,
    ):
        await setup_entity(hass)
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    coordinator = hass.data[DOMAIN]["automower_test"]
    AutomowerTracker(coordinator, MWR_ONE_IDX)


@pytest.mark.asyncio
async def test_device_tracker_pos(hass: HomeAssistant):
    """test device tracker with positions."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    device_tracker = AutomowerTracker(coordinator, MWR_ONE_IDX)
    # pylint: disable=protected-access
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

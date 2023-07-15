"""Tests for entity module."""

from copy import deepcopy
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from dateutil import tz
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from ..entity import AutomowerEntity
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
    AUTOMOWER_ERROR_SESSION_DATA,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_entity_datetime_object(hass: HomeAssistant):
    """test entity datetime object."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    entity = AutomowerEntity(coordinator, MWR_ONE_IDX)

    assert entity.idx == MWR_ONE_IDX
    assert entity.mower_id == MWR_ONE_ID

    assert entity.datetime_object(1685991600000) == datetime(
        2023, 6, 5, 19, 0, tzinfo=tz.gettz("US/Pacific")
    )
    assert entity.datetime_object(0) is None


@pytest.mark.asyncio
async def test_load_no_data(hass: HomeAssistant):
    """test automower initialization, not data returned"""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    coordinator.session.data = AUTOMOWER_ERROR_SESSION_DATA
    with pytest.raises(KeyError):
        entity = AutomowerEntity(coordinator, MWR_ONE_IDX)

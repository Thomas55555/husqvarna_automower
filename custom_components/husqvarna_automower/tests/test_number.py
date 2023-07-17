"""Tests for number module."""
from unittest.mock import MagicMock

import pytest
from aiohttp import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from ..const import DOMAIN
from ..number import (
    NUMBER_SENSOR_TYPES,
    AutomowerNumber,
    AutomowerParkStartNumberEntity,
)
from .const import (
    MWR_ONE_ID,
    MWR_ONE_IDX,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_number_cut_height(hass: HomeAssistant):
    """test number set cut height."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    number = AutomowerNumber(coordinator, MWR_ONE_IDX)

    assert number._attr_unique_id == f"{MWR_ONE_ID}_cuttingheight"

    # Success
    await number.async_set_native_value(4.0)
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID,
        '{"data": {"type": "settings", "attributes": {"cuttingHeight": 4}}}',
        "settings",
    )

    # Raises UpdateFailed
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = TypeError
    with pytest.raises(UpdateFailed):
        await number.async_set_native_value(4.0)


@pytest.mark.asyncio
async def test_number_park_start(hass: HomeAssistant):
    """test number set park start."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    number = AutomowerParkStartNumberEntity(
        coordinator, MWR_ONE_IDX, NUMBER_SENSOR_TYPES[0]
    )

    assert number._attr_unique_id == f"{MWR_ONE_ID}_Park"

    # Success
    await number.async_set_native_value(4.0)
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID,
        '{"data": {"type": "Park", "attributes": {"duration": 4}}}',
        "actions",
    )

    # Raises UpdateFailed
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await number.async_set_native_value(4.0)

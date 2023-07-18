"""Tests for select module."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from ..const import DOMAIN, HEADLIGHTMODES
from ..select import AutomowerSelect
from .const import (
    MWR_ONE_ID,
    MWR_ONE_IDX,
)


from .test_common import setup_entity


@pytest.mark.asyncio
async def test_number_cut_height(hass: HomeAssistant):
    """test select."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    select = AutomowerSelect(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert select._attr_unique_id == f"{MWR_ONE_ID}_headlight_mode"

    # Not connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = False

    assert select.available is False

    # Connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = True

    assert select.available is True

    # Current Option
    assert select.current_option == "evening_only"

    # Select Option
    await select.async_select_option(HEADLIGHTMODES[0])
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID,
        '{"data": {"type": "settings", "attributes": {"headlight": {"mode": "ALWAYS_ON"}}}}',
        "settings",
    )

    # Raises UpdateFailed
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = TypeError
    with pytest.raises(UpdateFailed):
        await select.async_select_option(HEADLIGHTMODES[1])

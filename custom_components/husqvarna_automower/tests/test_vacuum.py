"""Tests for sensor module."""
from copy import deepcopy
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from aiohttp import ClientResponseError
from dateutil import tz
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionErrorMessage, HomeAssistantError
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from ..vacuum import HusqvarnaAutomowerEntity
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
)


@pytest.mark.asyncio
async def setup_entity(hass: HomeAssistant):
    """Set up entity and config entry"""

    options = deepcopy(AUTOMER_DM_CONFIG)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=options,
        entry_id="automower_test",
        title="Automower Test",
    )

    config_entry.add_to_hass(hass)

    session = deepcopy(AUTOMOWER_SM_SESSION_DATA)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            name="AutomowerMockSession",
            model=AutomowerSession,
            data=session,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            action=AsyncMock(),
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    return config_entry


@pytest.mark.asyncio
async def test_vacuum_extra_state_attributes(hass: HomeAssistant):
    """test vacuum extra state attributes."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)

    assert vacuum._attr_unique_id == MWR_ONE_ID
    assert vacuum.extra_state_attributes == {"action": None}

    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["planner"] = {
        "override": {"action": "Test_Action"}
    }

    assert vacuum.extra_state_attributes == {"action": "test_action"}


@pytest.mark.asyncio
async def test_vacuum_state(hass: HomeAssistant):
    """test vacuum state."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)

    def set_state(state: str):
        """Set new state"""
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
            "state"
        ] = state

    def set_activity(activity: str):
        """Set new state"""
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
            "activity"
        ] = activity

    assert vacuum._attr_unique_id == MWR_ONE_ID
    set_activity("")

    set_state("PAUSED")
    assert vacuum.state == STATE_PAUSED

    set_state("WAIT_UPDATING")
    assert vacuum.state == STATE_IDLE

    set_state("WAIT_POWER_UP")
    assert vacuum.state == STATE_IDLE

    set_state("")
    set_activity("MOWING")
    assert vacuum.state == STATE_CLEANING

    set_activity("LEAVING")
    assert vacuum.state == STATE_CLEANING

    set_activity("GOING_HOME")
    assert vacuum.state == STATE_RETURNING

    set_activity("")
    set_state("RESTRICTED")
    assert vacuum.state == STATE_DOCKED

    set_state("")
    set_activity("PARKED_IN_CS")
    assert vacuum.state == STATE_DOCKED

    set_activity("CHARGING")
    assert vacuum.state == STATE_DOCKED

    set_activity("")
    set_state("FATAL_ERROR")
    assert vacuum.state == STATE_ERROR

    set_state("ERROR")
    assert vacuum.state == STATE_ERROR

    set_state("ERROR_AT_POWER_UP")
    assert vacuum.state == STATE_ERROR

    set_state("NOT_APPLICABLE")
    assert vacuum.state == STATE_ERROR

    set_state("UNKNOWN")
    assert vacuum.state == STATE_ERROR

    set_state("STOPPED")
    assert vacuum.state == STATE_ERROR

    set_state("OFF")
    assert vacuum.state == STATE_ERROR

    set_state("")
    set_activity("STOPPED_IN_GARDEN")
    assert vacuum.state == STATE_ERROR

    set_activity("UNKNOWN")
    assert vacuum.state == STATE_ERROR

    set_activity("NOT_APPLICABLE")
    assert vacuum.state == STATE_ERROR


@pytest.mark.asyncio
async def test_vacuum_error(hass: HomeAssistant):
    """test vacuum state."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)

    def set_state(state: str):
        """Set new state"""
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
            "state"
        ] = state

    def set_activity(activity: str):
        """Set new state"""
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
            "activity"
        ] = activity

    def set_error_code(code: str):
        """Set new state"""
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
            "errorCode"
        ] = code

    assert vacuum._attr_unique_id == MWR_ONE_ID

    set_state("STOPPED_IN_GARDEN")
    set_activity("UNKNOWN")
    set_error_code(0)
    assert vacuum.state == STATE_ERROR


@pytest.mark.asyncio
async def test_vacuum_commands(hass: HomeAssistant):
    """test vacuum commands."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)
    assert vacuum._attr_unique_id == MWR_ONE_ID

    # Start
    # Success
    await vacuum.async_start()
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, '{"data": {"type": "ResumeSchedule"}}', "actions"
    )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await vacuum.async_start()

    # Pause
    # Success
    coordinator.session.action.reset_mock()
    await vacuum.async_pause()
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, '{"data": {"type": "Pause"}}', "actions"
    )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await vacuum.async_pause()

    # Stop
    # Success
    coordinator.session.action.reset_mock()
    await vacuum.async_stop()
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, '{"data": {"type": "ParkUntilNextSchedule"}}', "actions"
    )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await vacuum.async_stop()

    # Return to base
    # Success
    coordinator.session.action.reset_mock()
    await vacuum.async_return_to_base()
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, '{"data": {"type": "ParkUntilFurtherNotice"}}', "actions"
    )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await vacuum.async_return_to_base()

    # Custom Command
    # Success
    coordinator.session.action = AsyncMock()
    await vacuum.async_custom_command("action", '{"data": {"type": "CustomCommand"}}')
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, '{"data": {"type": "CustomCommand"}}', "action"
    )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    with pytest.raises(HomeAssistantError):
        await vacuum.async_custom_command(
            "action", '{"data": {"type": "CustomCommand"}}'
        )

    # Calendar Command
    # Success
    coordinator.session.action = AsyncMock()
    await vacuum.async_custom_calendar_command(
        datetime(2023, 6, 1, 10),
        datetime(2023, 6, 1, 11),
        True,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    exp_payload = '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 600, "duration": 60, "monday": true, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": false}]}}}'
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID, exp_payload, "calendar"
    )

    # Raises ConditionErrorMessage
    coordinator.session.action.reset_mock()
    with pytest.raises(ConditionErrorMessage):
        await vacuum.async_custom_calendar_command(
            datetime(2023, 6, 1, 12),
            datetime(2023, 6, 1, 11),
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        )

    # Raises ClientResponseError
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    with pytest.raises(HomeAssistantError):
        await vacuum.async_custom_calendar_command(
            datetime(2023, 6, 1, 10),
            datetime(2023, 6, 1, 11),
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        )


@pytest.mark.asyncio
async def test_vacuum_schedule_selector_success(hass: HomeAssistant):
    """test vacuum schedule selector."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)
    assert vacuum._attr_unique_id == MWR_ONE_ID

    mock_async_load = AsyncMock(
        return_value={
            "items": [
                {
                    "id": "test_schedule",
                    "name": "Test schedule",
                    "monday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "tuesday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "wednesday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "thursday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "friday": [{"from": "17:00:00", "to": "23:00:00"}],
                    "saturday": [
                        {"from": "07:00:00", "to": "10:00:00"},
                        {"from": "16:00:00", "to": "23:00:00"},
                    ],
                    "sunday": [{"from": "07:00:00", "to": "21:00:00"}],
                }
            ]
        }
    )
    storage_mock = AsyncMock(name="storage mock", async_load=mock_async_load)
    with patch(
        "custom_components.husqvarna_automower.vacuum.Store",
        MagicMock(name="store mock", spec=Store, return_value=storage_mock),
    ) as store_mock:
        await vacuum.async_schedule_selector("schedule.test_schedule")
        coordinator.session.action.assert_called_once_with(
            "c7233734-b219-4287-a173-08e3643f89f0",
            '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 1020, "duration": 240, "monday": true, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": true, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": false, "wednesday": true, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": false, "wednesday": false, "thursday": true, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 360, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": true, "saturday": false, "sunday": false}, {"start": 420, "duration": 180, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": true, "sunday": false}, {"start": 960, "duration": 420, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": true, "sunday": false}, {"start": 420, "duration": 840, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": true}]}}}',
            "calendar",
        )


@pytest.mark.asyncio
async def test_vacuum_schedule_selector_fail(hass: HomeAssistant):
    """test vacuum schedule selector fail."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    vacuum = HusqvarnaAutomowerEntity(coordinator, MWR_ONE_IDX)
    assert vacuum._attr_unique_id == MWR_ONE_ID

    mock_async_load = AsyncMock(
        return_value={
            "items": [
                {
                    "id": "test_schedule",
                    "name": "Test schedule",
                    "monday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "tuesday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "wednesday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "thursday": [{"from": "17:00:00", "to": "21:00:00"}],
                    "friday": [{"from": "17:00:00", "to": "23:00:00"}],
                    "saturday": [
                        {"from": "07:00:00", "to": "10:00:00"},
                        {"from": "16:00:00", "to": "23:00:00"},
                    ],
                    "sunday": [{"from": "07:00:00", "to": "21:00:00"}],
                }
            ]
        }
    )
    storage_mock = AsyncMock(name="storage mock", async_load=mock_async_load)
    with patch(
        "custom_components.husqvarna_automower.vacuum.Store",
        MagicMock(name="store mock", spec=Store, return_value=storage_mock),
    ) as store_mock:
        # Raises ClientResponseError
        coordinator.session.action.reset_mock()
        coordinator.session.action.side_effect = ClientResponseError(
            MagicMock(), MagicMock()
        )

        with pytest.raises(HomeAssistantError):
            await vacuum.async_schedule_selector("schedule.test_schedule")
            coordinator.session.action.assert_called_once_with(
                "c7233734-b219-4287-a173-08e3643f89f0",
                '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 1020, "duration": 240, "monday": true, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": true, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": false, "wednesday": true, "thursday": false, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 240, "monday": false, "tuesday": false, "wednesday": false, "thursday": true, "friday": false, "saturday": false, "sunday": false}, {"start": 1020, "duration": 360, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": true, "saturday": false, "sunday": false}, {"start": 420, "duration": 180, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": true, "sunday": false}, {"start": 960, "duration": 420, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": true, "sunday": false}, {"start": 420, "duration": 840, "monday": false, "tuesday": false, "wednesday": false, "thursday": false, "friday": false, "saturday": false, "sunday": true}]}}}',
                "calendar",
            )

"""Tests for binary sensor module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..binary_sensor import (
    AutomowerBatteryChargingBinarySensor,
    AutomowerErrorBinarySensor,
    AutomowerLeavingDockBinarySensor,
)
from ..const import DOMAIN, ERROR_STATES
from .const import (
    AUTOMER_SM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
    MWR_ONE_ID,
    MWR_ONE_IDX,
)


@pytest.mark.asyncio
async def setup_binary_sensor(hass: HomeAssistant, sensor_class):
    """Set up binary sensor and config entry"""

    options = deepcopy(AUTOMER_SM_CONFIG)

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
            data=AUTOMOWER_SM_SESSION_DATA,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
        ),
    ) as automower_session_mock:
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        binary_sensor = sensor_class(automower_coordinator_mock, MWR_ONE_IDX)
        return binary_sensor, automower_coordinator_mock


@pytest.mark.asyncio
async def test_battery_charging_sensor(hass: HomeAssistant):
    """test AutomowerBatteryChargingBinarySensor"""
    battery_sensor, automower_coordinator_mock = await setup_binary_sensor(
        hass, AutomowerBatteryChargingBinarySensor
    )

    assert battery_sensor._attr_unique_id == f"{MWR_ONE_ID}_battery_charging"

    assert battery_sensor.is_on is False
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "CHARGING"

    assert battery_sensor.is_on is True


@pytest.mark.asyncio
async def test_leaving_dock_sensor(hass: HomeAssistant):
    """test AutomowerLeavingDockBinarySensor"""
    leaving_sensor, automower_coordinator_mock = await setup_binary_sensor(
        hass, AutomowerLeavingDockBinarySensor
    )

    assert leaving_sensor._attr_unique_id == f"{MWR_ONE_ID}_leaving_dock"

    assert leaving_sensor.is_on is False
    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "LEAVING"

    assert leaving_sensor.is_on is True


@pytest.mark.asyncio
async def test_error_sensor(hass: HomeAssistant):
    """test AutomowerErrorBinarySensor"""
    error_sensor, automower_coordinator_mock = await setup_binary_sensor(
        hass, AutomowerErrorBinarySensor
    )

    assert error_sensor._attr_unique_id == f"{MWR_ONE_ID}_error"

    assert error_sensor.is_on is False
    assert error_sensor.extra_state_attributes == {
        "error_code": -1,
        "description": "No Error",
    }

    automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "errorCode"
    ] = 0

    assert error_sensor.extra_state_attributes == {
        "error_code": -1,
        "description": "No Error",
    }

    for e_state in ERROR_STATES:
        automower_coordinator_mock.session.data["data"][MWR_ONE_IDX]["attributes"][
            "mower"
        ]["state"] = e_state

        assert error_sensor.is_on is True
        assert error_sensor.extra_state_attributes == {
            "error_code": 0,
            "description": "Unexpected error",
        }

"""Tests for binary sensor module."""
import pytest
from homeassistant.core import HomeAssistant

from ..binary_sensor import (
    AutomowerBatteryChargingBinarySensor,
    AutomowerErrorBinarySensor,
    AutomowerLeavingDockBinarySensor,
)
from ..const import DOMAIN, ERROR_STATES
from .const import (
    MWR_ONE_ID,
    MWR_ONE_IDX,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_battery_charging_sensor(hass: HomeAssistant):
    """test AutomowerBatteryChargingBinarySensor"""

    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]

    battery_sensor = AutomowerBatteryChargingBinarySensor(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert battery_sensor._attr_unique_id == f"{MWR_ONE_ID}_battery_charging"

    assert battery_sensor.is_on is False
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "CHARGING"

    assert battery_sensor.is_on is True


@pytest.mark.asyncio
async def test_leaving_dock_sensor(hass: HomeAssistant):
    """test AutomowerLeavingDockBinarySensor"""

    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]

    leaving_sensor = AutomowerLeavingDockBinarySensor(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert leaving_sensor._attr_unique_id == f"{MWR_ONE_ID}_leaving_dock"

    assert leaving_sensor.is_on is False
    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"]["activity"] = "LEAVING"

    assert leaving_sensor.is_on is True


@pytest.mark.asyncio
async def test_error_sensor(hass: HomeAssistant):
    """test AutomowerErrorBinarySensor"""

    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]

    error_sensor = AutomowerErrorBinarySensor(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert error_sensor._attr_unique_id == f"{MWR_ONE_ID}_error"

    assert error_sensor.is_on is False
    assert error_sensor.extra_state_attributes == {
        "error_code": -1,
        "description": "No Error",
    }

    coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"]["errorCode"] = 0

    assert error_sensor.extra_state_attributes == {
        "error_code": -1,
        "description": "No Error",
    }

    for e_state in ERROR_STATES:
        coordinator.data["data"][MWR_ONE_IDX]["attributes"]["mower"]["state"] = e_state

        assert error_sensor.is_on is True
        assert error_sensor.extra_state_attributes == {
            "error_code": 0,
            "description": "Unexpected error",
        }

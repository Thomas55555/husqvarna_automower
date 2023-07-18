"""Tests for sensor module."""
from copy import deepcopy
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT, ZONE_ID
from ..sensor import SENSOR_TYPES, AutomowerZoneSensor, get_problem
from .const import (
    AUTOMER_SM_CONFIG,
    AUTOMOWER_SM_SESSION_DATA,
    DEFAULT_ZONES,
    FRONT_GARDEN_PNT,
    MWR_ONE_ID,
    MWR_ONE_IDX,
    NO_ZONE_PNT,
)
from .test_common import setup_entity


@pytest.mark.asyncio
async def test_zone_sensor(hass: HomeAssistant):
    """test zone."""
    config_entry = await setup_entity(hass, dual_mower=True)
    coordinator = hass.data[DOMAIN]["automower_test"]
    zone_sensor = AutomowerZoneSensor(coordinator, MWR_ONE_IDX, config_entry)

    # pylint: disable=protected-access
    assert zone_sensor._attr_unique_id == f"{MWR_ONE_ID}_zone_sensor"

    # Load zones works
    # pylint: disable=protected-access
    assert zone_sensor.zones == DEFAULT_ZONES

    # Mower is home
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "PARKED_IN_CS"
    assert zone_sensor.native_value == "Home"
    assert zone_sensor.extra_state_attributes == {ZONE_ID: "home"}

    # Mower is in front garden
    # Mower is still home, but point would be in the front garden
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
        "latitude"
    ] = FRONT_GARDEN_PNT[0]
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
        "longitude"
    ] = FRONT_GARDEN_PNT[1]
    assert zone_sensor.native_value == "Home"
    assert zone_sensor.extra_state_attributes == {ZONE_ID: "home"}

    # Mower state is mowing
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["mower"][
        "activity"
    ] = "MOWING"
    assert zone_sensor.native_value == "Front Garden"
    assert zone_sensor.extra_state_attributes == {ZONE_ID: "front_garden"}

    # Mower is mowing but not in a zone
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
        "latitude"
    ] = NO_ZONE_PNT[0]
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["positions"][0][
        "longitude"
    ] = NO_ZONE_PNT[1]
    assert zone_sensor.native_value == "Unknown"
    assert zone_sensor.extra_state_attributes == {ZONE_ID: "unknown"}


@pytest.mark.asyncio
async def test_zone_sensor_bad_json(hass: HomeAssistant):
    """test zone sensor if zones aren't a dict"""
    options = deepcopy(AUTOMER_SM_CONFIG)
    options["configured_zones"] = "[]"
    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMER_SM_CONFIG",
        options,
    ):
        config_entry = await setup_entity(hass)
        coordinator = hass.data[DOMAIN]["automower_test"]
        zone_sensor = AutomowerZoneSensor(coordinator, MWR_ONE_IDX, config_entry)

        # Zone JSON isn't a dict
        # pylint: disable=protected-access
        zone_sensor._load_zones()

        # pylint: disable=use-implicit-booleaness-not-comparison
        assert zone_sensor.zones == {}


@pytest.mark.asyncio
async def test_sensors_no_cut(hass: HomeAssistant):
    """test sensors if cutting height is missing."""
    session = deepcopy(AUTOMOWER_SM_SESSION_DATA)
    session["data"][MWR_ONE_IDX]["attributes"]["system"][
        "model"
    ] = NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT[0]

    with patch(
        "custom_components.husqvarna_automower.tests.test_common.AUTOMOWER_SM_SESSION_DATA",
        session,
    ):
        await setup_entity(hass)


@pytest.mark.asyncio
async def test_statistics_sensors(hass: HomeAssistant):
    """test statistics sensors."""
    test_sensor_types = deepcopy(SENSOR_TYPES)
    for sensor in test_sensor_types:
        sensor.entity_registry_enabled_default = True
    with patch(
        "custom_components.husqvarna_automower.sensor.SENSOR_TYPES", test_sensor_types
    ):
        await setup_entity(hass)


@pytest.mark.asyncio
async def test_get_problem(hass: HomeAssistant):  # pylint: disable=unused-argument
    """Test get_problem function."""
    mower_attributes = {
        "mower": {
            "mode": "MAIN_AREA",
            "activity": "PARKED_IN_CS",
            "state": "RESTRICTED",
            "errorCode": 0,
            "errorCodeTimestamp": 0,
        },
        "planner": {
            "nextStartTimestamp": 1685991600000,
            "override": {"action": None},
            "restrictedReason": "NOT_APPLICABLE",
        },
    }

    assert get_problem(mower_attributes) == "parked_until_further_notice"

    mower_attributes["planner"]["restrictedReason"] = "WEEK_SCHEDULE"
    assert get_problem(mower_attributes) == "WEEK_SCHEDULE"

    # Error State
    mower_attributes["mower"]["state"] = "ERROR"
    assert get_problem(mower_attributes) == "Unexpected error"

    # Unkown State
    mower_attributes["mower"]["state"] = "UNKNOWN"
    assert get_problem(mower_attributes) == "UNKNOWN"

    # Stopped in Garden State
    mower_attributes["mower"]["state"] = "OTHER"
    mower_attributes["mower"]["activity"] = "STOPPED_IN_GARDEN"
    assert get_problem(mower_attributes) == "STOPPED_IN_GARDEN"

    # Charging
    mower_attributes["mower"]["activity"] = "CHARGING"
    assert get_problem(mower_attributes) == "charging"

    # None
    mower_attributes["mower"]["activity"] = "MISSING"
    assert get_problem(mower_attributes) is None

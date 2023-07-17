"""Tests for calendar module."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from aiohttp import ClientResponseError
from geopy import Location
from homeassistant.core import HomeAssistant

from ..calendar import AutomowerCalendar
from ..const import DOMAIN
from .const import (
    MWR_ONE_ID,
    MWR_ONE_IDX,
)

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_calendar(hass: HomeAssistant):
    """test select."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    calendar = AutomowerCalendar(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert calendar._attr_unique_id == f"{MWR_ONE_ID}_calendar"

    # Not connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = False

    assert calendar.available is False

    # Connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = True

    assert calendar.available is True

    # Get calendar events
    location_result = Location(
        "Italian Garden, Biltmore Estate Path, Buncombe County,"
        " North Carolina, 28803, United States",
        (35.5399226, -82.55193188763246, 0.0),
        {
            "place_id": 266519807,
            "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
            "osm_type": "way",
            "osm_id": 830192286,
            "lat": "35.5399226",
            "lon": "-82.55193188763246",
            "display_name": "Italian Garden, Biltmore Estate Path, "
            "Buncombe County, North Carolina, 28803, United States",
            "address": {
                "leisure": "Italian Garden",
                "road": "Biltmore Estate Path",
                "county": "Buncombe County",
                "state": "North Carolina",
                "ISO3166-2-lvl4": "US-NC",
                "postcode": "28803",
                "country": "United States",
                "country_code": "us",
                "house_number": "1",
                "town": "Asheville",
            },
            "boundingbox": ["35.5395166", "35.5403093", "-82.5530644", "-82.550742"],
        },
    )
    with patch.object(
        calendar,
        "geolocator",
        MagicMock(reverse=MagicMock(return_value=location_result)),
    ) as mock_geo:
        result = await calendar.async_get_events_data(
            hass, datetime(2023, 6, 9, 7), datetime(2023, 6, 9, 16)
        )
        mock_geo.reverse.assert_called_once()
        assert len(result) == 6

        # No house number in return address
        location_result = Location(
            "Italian Garden, Biltmore Estate Path, Buncombe County,"
            " North Carolina, 28803, United States",
            (35.5399226, -82.55193188763246, 0.0),
            {
                "place_id": 266519807,
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
                "osm_type": "way",
                "osm_id": 830192286,
                "lat": "35.5399226",
                "lon": "-82.55193188763246",
                "display_name": "Italian Garden, Biltmore Estate Path, Buncombe County,"
                " North Carolina, 28803, United States",
                "address": {
                    "leisure": "Italian Garden",
                    "road": "Biltmore Estate Path",
                    "county": "Buncombe County",
                    "state": "North Carolina",
                    "ISO3166-2-lvl4": "US-NC",
                    "postcode": "28803",
                    "country": "United States",
                    "country_code": "us",
                    "town": "Asheville",
                },
                "boundingbox": [
                    "35.5395166",
                    "35.5403093",
                    "-82.5530644",
                    "-82.550742",
                ],
            },
        )
        mock_geo.reverse.reset_mock()
        mock_geo.reverse.return_value = location_result
        result = await calendar.async_get_events_data(
            hass, datetime(2023, 6, 9, 7), datetime(2023, 6, 9, 16)
        )
        mock_geo.reverse.assert_called_once()
        assert len(result) == 6

        # No postions, Index error
        location_result = Location(
            "Italian Garden, Biltmore Estate Path, Buncombe County,"
            " North Carolina, 28803, United States",
            (35.5399226, -82.55193188763246, 0.0),
            {
                "place_id": 266519807,
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
                "osm_type": "way",
                "osm_id": 830192286,
                "lat": "35.5399226",
                "lon": "-82.55193188763246",
                "display_name": "Italian Garden, Biltmore Estate Path, Buncombe County,"
                " North Carolina, 28803, United States",
                "address": {
                    "leisure": "Italian Garden",
                    "road": "Biltmore Estate Path",
                    "county": "Buncombe County",
                    "state": "North Carolina",
                    "ISO3166-2-lvl4": "US-NC",
                    "postcode": "28803",
                    "country": "United States",
                    "country_code": "us",
                    "house_number": "1",
                    "town": "Asheville",
                },
                "boundingbox": [
                    "35.5395166",
                    "35.5403093",
                    "-82.5530644",
                    "-82.550742",
                ],
            },
        )
        mock_geo.reverse.reset_mock()
        mock_geo.reverse.return_value = location_result
        coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["positions"] = []

        result = await calendar.async_get_events_data(
            hass, datetime(2023, 6, 9, 7), datetime(2023, 6, 9, 16)
        )
        mock_geo.reverse.assert_not_called()
        assert len(result) == 6

    # Get next event
    assert len(calendar.get_next_event()) == 2

    # Get events data
    result = await calendar.async_get_events(
        hass, datetime(2023, 6, 9, 7), datetime(2023, 6, 9, 16)
    )
    assert len(result) == 6


@pytest.mark.asyncio
async def test_async_parse_to_husqvarna_string(hass: HomeAssistant):
    """test Parse to Husqvarna String."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    calendar = AutomowerCalendar(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert calendar._attr_unique_id == f"{MWR_ONE_ID}_calendar"

    # Parse to Husqvarna String
    # Not a recurring event
    with pytest.raises(vol.Invalid) as exception:
        await calendar.async_parse_to_husqvarna_string({})
    assert exception.value.args[0] == "Only reccuring events are allowed"

    # Not a weekly event
    with pytest.raises(vol.Invalid) as exception:
        await calendar.async_parse_to_husqvarna_string({"rrule": ""})
    assert exception.value.args[0] == "Please select weekly"

    # No Days
    with pytest.raises(vol.Invalid) as exception:
        await calendar.async_parse_to_husqvarna_string({"rrule": "FREQ=WEEKLY;"})
    assert exception.value.args[0] == "Please select day(s)"

    # With Days
    result = await calendar.async_parse_to_husqvarna_string(
        {
            "rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,THU;",
            "dtstart": datetime(2023, 6, 9, 8),
            "dtend": datetime(2023, 6, 9, 9),
        }
    )
    assert result == [
        {
            "start": 480,
            "duration": 60,
            "friday": False,
            "monday": True,
            "saturday": False,
            "sunday": False,
            "wednesday": True,
            "thursday": False,
            "tuesday": True,
        }
    ]


@pytest.mark.asyncio
async def test_aysnc_send_command_to_mower(hass: HomeAssistant):
    """test send command to mower."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    calendar = AutomowerCalendar(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert calendar._attr_unique_id == f"{MWR_ONE_ID}_calendar"

    task_list = [
        {
            "start": 480,
            "duration": 60,
            "friday": False,
            "monday": True,
            "saturday": False,
            "sunday": False,
            "wednesday": True,
            "thursday": False,
            "tuesday": True,
        }
    ]

    # Success
    await calendar.aysnc_send_command_to_mower(task_list)
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID,
        '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 480, "duration": 60,'
        ' "friday": false, "monday": true, "saturday": false, "sunday": false, "wednesday":'
        ' true, "thursday": false, "tuesday": true}]}}}',
        "calendar",
    )

    # Raises UpdateFailed
    coordinator.session.action.reset_mock()
    coordinator.session.action.side_effect = ClientResponseError(
        MagicMock(), MagicMock()
    )
    await calendar.aysnc_send_command_to_mower(task_list)


@pytest.mark.asyncio
async def test_aysnc_edit_events(hass: HomeAssistant):
    """test create, update, and delete events."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    calendar = AutomowerCalendar(coordinator, MWR_ONE_IDX)

    # pylint: disable=protected-access
    assert calendar._attr_unique_id == f"{MWR_ONE_ID}_calendar"

    event = {
        "rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,THU;",
        "dtstart": datetime(2023, 6, 9, 8),
        "dtend": datetime(2023, 6, 9, 9),
    }

    # Create event
    await calendar.async_create_event(**event)
    coordinator.session.action.assert_awaited_once_with(
        MWR_ONE_ID,
        '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 1140,'
        ' "duration": 300, "monday": true, "tuesday": false, "wednesday": true,'
        ' "thursday": false, "friday": true, "saturday": false, "sunday": false},'
        ' {"start": 0, "duration": 480, "monday": false, "tuesday": true, '
        '"wednesday": false, "thursday": true, "friday": false, "saturday": true,'
        ' "sunday": false}, {"start": 480, "duration": 60, "monday": true,'
        ' "tuesday": true, "wednesday": true, "thursday": false, "friday": false,'
        ' "saturday": false, "sunday": false}]}}}',
        "calendar",
    )

    # Update event
    coordinator.session.action.reset_mock()
    with patch.object(calendar, "async_update_ha_state", AsyncMock()):
        await calendar.async_update_event("0", event)
        coordinator.session.action.assert_awaited_once_with(
            MWR_ONE_ID,
            '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 480,'
            ' "duration": 60, "monday": true, "tuesday": true, "wednesday": true,'
            ' "thursday": false, "friday": false, "saturday": false, "sunday": false},'
            ' {"start": 0, "duration": 480, "monday": false, "tuesday": true,'
            ' "wednesday": false, "thursday": true, "friday": false, '
            '"saturday": true, "sunday": false}]}}}',
            "calendar",
        )

    # Delete event
    coordinator.session.action.reset_mock()
    with patch.object(calendar, "async_update_ha_state", AsyncMock()):
        await calendar.async_delete_event("0")
        coordinator.session.action.assert_awaited_once_with(
            MWR_ONE_ID,
            '{"data": {"type": "calendar", "attributes": {"tasks": [{"start": 0, "duration": 480,'
            ' "monday": false, "tuesday": true, "wednesday": false, "thursday": true,'
            ' "friday": false, "saturday": true, "sunday": false}]}}}',
            "calendar",
        )

    # Delete event, too few events
    coordinator.session.action.reset_mock()
    with pytest.raises(vol.Invalid) as exception:
        await calendar.async_delete_event("0")
    assert exception.value.args[0] == "You need at least one schedule"

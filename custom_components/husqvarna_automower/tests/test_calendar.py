"""Tests for calendar module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from datetime import datetime
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from geopy import Location

from ..const import DOMAIN
from ..calendar import AutomowerCalendar
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
async def test_calendar(hass: HomeAssistant):
    """test select."""
    await setup_entity(hass)
    coordinator = hass.data[DOMAIN]["automower_test"]
    calendar = AutomowerCalendar(coordinator, MWR_ONE_IDX)

    assert calendar._attr_unique_id == f"{MWR_ONE_ID}_calendar"

    # Not connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = False

    assert calendar.available == False

    # Connected
    coordinator.session.data["data"][MWR_ONE_IDX]["attributes"]["metadata"][
        "connected"
    ] = True

    assert calendar.available == True

    # Get calendar events
    location_result = Location(
        "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
        (35.5399226, -82.55193188763246, 0.0),
        {
            "place_id": 266519807,
            "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
            "osm_type": "way",
            "osm_id": 830192286,
            "lat": "35.5399226",
            "lon": "-82.55193188763246",
            "display_name": "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
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
            "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
            (35.5399226, -82.55193188763246, 0.0),
            {
                "place_id": 266519807,
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
                "osm_type": "way",
                "osm_id": 830192286,
                "lat": "35.5399226",
                "lon": "-82.55193188763246",
                "display_name": "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
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
            "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
            (35.5399226, -82.55193188763246, 0.0),
            {
                "place_id": 266519807,
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
                "osm_type": "way",
                "osm_id": 830192286,
                "lat": "35.5399226",
                "lon": "-82.55193188763246",
                "display_name": "Italian Garden, Biltmore Estate Path, Buncombe County, North Carolina, 28803, United States",
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

    # Create event

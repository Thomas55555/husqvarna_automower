"""Platform for Husqvarna Automower calendar integration."""
import copy
import logging

from geopy.geocoders import Nominatim

import homeassistant.util.dt as dt_util
from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.const import ENTITY_CATEGORY_DIAGNOSTIC
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, WEEKDAYS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Setup sensor platform."""
    _LOGGER.debug("entry: %s", entry)
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerCalendar(hass, session, idx)
        for idx, ent in enumerate(session.data["data"])
    )


class AutomowerCalendar(CalendarEventDevice):
    """Representation of a Demo Calendar element."""

    def __init__(self, hass, session, idx) -> None:
        """Initialize demo calendar."""
        self.hass = hass
        self.session = session
        self.idx = idx
        self.mower = self.session.data["data"][self.idx]
        mower_attributes = self.__get_mower_attributes()
        self.mower_id = self.mower["id"]
        self._name = mower_attributes["system"]["name"]
        self.session.register_cb(
            lambda _: self.async_write_ha_state(), schedule_immediately=True
        )

        self._event = None
        self._next_event = None

    def __get_mower_attributes(self) -> dict:
        return self.session.data["data"][self.idx]["attributes"]

    async def async_get_events_data(self, hass) -> dict:
        """Get all events in a specific time frame."""
        mower_attributes = self.__get_mower_attributes()
        lat = mower_attributes["positions"][0]["latitude"]
        long = mower_attributes["positions"][0]["longitude"]
        position = f"{lat}, {long}"
        geolocator = Nominatim(user_agent=self._name)
        result = await hass.async_add_executor_job(geolocator.reverse, position)
        try:
            location = f"{result.raw['address']['road']} {result.raw['address']['house_number']}, {result.raw['address']['town']}"
        except Exception:
            location = None
        event_list = []
        self._next_event = {
            "start": {
                "dateTime": (
                    dt_util.start_of_local_day() + dt_util.dt.timedelta(days=7)
                ).isoformat()
            },
            "end": {"dateTime": ""},
            "summary": "",
        }
        mower_attributes = self.__get_mower_attributes()
        for task, tasks in enumerate(mower_attributes["calendar"]["tasks"]):
            calendar = mower_attributes["calendar"]["tasks"][task]
            start_of_day = dt_util.start_of_local_day()
            start_mowing = start_of_day + dt_util.dt.timedelta(
                minutes=calendar["start"]
            )
            end_mowing = start_of_day + dt_util.dt.timedelta(
                minutes=calendar["start"] + calendar["duration"]
            )

            for days in range(7):
                today = (start_of_day + dt_util.dt.timedelta(days=days)).weekday()
                today_as_string = WEEKDAYS[today]
                if calendar[today_as_string] is True:
                    self._event = {
                        "start": {
                            "dateTime": (
                                start_mowing + dt_util.dt.timedelta(days=days)
                            ).isoformat()
                        },
                        "end": {
                            "dateTime": (
                                end_mowing + dt_util.dt.timedelta(days=days)
                            ).isoformat()
                        },
                        "summary": f"Mowing schedule {task + 1}",
                        "location": location,
                    }
                    if (
                        self._event["start"]["dateTime"]
                        < self._next_event["start"]["dateTime"]
                    ):
                        self._next_event = copy.deepcopy(self._event)
                        _LOGGER.debug("self._next_event %s", self._next_event)
                    event_list.append(self._event)
        return event_list

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.mower_id)})

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._name} Schedule"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_calendar"

    @property
    def entity_category(self) -> str:
        """Return a unique identifier for this entity."""
        return ENTITY_CATEGORY_DIAGNOSTIC

    async def async_get_events(self, hass, start_date, end_date) -> dict:
        """Return calendar events within a datetime range."""
        events = await self.async_get_events_data(hass)
        return events

    @property
    def event(self) -> dict:
        """Return the next upcoming event."""
        return self._next_event

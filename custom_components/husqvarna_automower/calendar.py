"""Platform for Husqvarna Automower calendar integration."""
import logging

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


class AutomowerCalendarData:
    """Supplies AutomowerCalendar with CalendarData."""

    event = None

    def __init__(self, session, idx) -> None:
        """Initialize demo calendar."""
        self.session = session
        self.idx = idx
        self.mower = self.session.data["data"][self.idx]
        mower_attributes = self.__get_mower_attributes()
        self.mower_id = self.mower["id"]
        self._name = mower_attributes["system"]["name"]

    async def async_get_events(self, hass, start_date, end_date) -> dict:
        """Get all events in a specific time frame."""
        event_list = []
        self.event = {}
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
                    self.event = {
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
                    }

                    event_list.append(self.event)
        return event_list

    def __get_mower_attributes(self) -> dict:
        return self.session.data["data"][self.idx]["attributes"]


class AutomowerCalendar(CalendarEventDevice):
    """Representation of a Demo Calendar element."""

    def __init__(self, hass, session, idx) -> None:
        """Initialize demo calendar."""
        self.data = AutomowerCalendarData(session, idx)
        self.session = session
        self.idx = idx
        self.mower = self.session.data["data"][self.idx]
        mower_attributes = self.__get_mower_attributes()
        self.mower_id = self.mower["id"]
        self._name = mower_attributes["system"]["name"]
        self.session.register_cb(
            lambda _: self.async_write_ha_state(), schedule_immediately=True
        )

    def __get_mower_attributes(self) -> dict:
        return self.session.data["data"][self.idx]["attributes"]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.mower_id)})

    @property
    def event(self) -> dict:
        """Return the next upcoming event."""
        return self.data.event

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

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
        return await self.data.async_get_events(hass, self.session, self.idx)

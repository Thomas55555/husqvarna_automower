"""Platform for Husqvarna Automower calendar integration."""
from datetime import datetime
import logging

from geopy.geocoders import Nominatim

from homeassistant.backports.enum import StrEnum
from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DOMAIN, WEEKDAYS
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup calendar platform."""
    _LOGGER.debug("entry: %s", entry)
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerCalendar(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class AutomowerCalendar(CalendarEntity, AutomowerEntity):
    """Representation of the Automower Calendar element."""

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._event = None
        self._next_event = None
        self.loc = None

    async def async_get_events_data(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        lat = mower_attributes["positions"][0]["latitude"]
        long = mower_attributes["positions"][0]["longitude"]
        position = f"{lat}, {long}"
        geolocator = Nominatim(user_agent=self.name)
        result = await hass.async_add_executor_job(geolocator.reverse, position)
        try:
            self.loc = f"{result.raw['address']['road']} {result.raw['address']['house_number']}, {result.raw['address']['town']}"
        except Exception:
            self.loc = None

        even_list, next_event = self.get_next_event()
        return even_list

    def get_next_event(self):
        """Get the current or next event."""
        self._next_event = CalendarEvent(
            summary="",
            start=dt_util.start_of_local_day() + dt_util.dt.timedelta(days=7),
            end="",
            location="",
            description="",
        )
        event_list = []
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
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
                    self._event = CalendarEvent(
                        summary=f"Mowing schedule {task + 1}",
                        start=start_mowing + dt_util.dt.timedelta(days=days),
                        end=end_mowing + dt_util.dt.timedelta(days=days),
                        location=self.loc,
                    )
                    if self._event.start < self._next_event.start:
                        self._next_event = self._event
                        _LOGGER.debug("self._next_event %s", self._next_event)

                    event_list.append(self._event)

        return event_list, self._next_event

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self.mower_name}"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_calendar"

    @property
    def entity_category(self) -> StrEnum:
        """Return a unique identifier for this entity."""
        return EntityCategory.DIAGNOSTIC

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return await self.async_get_events_data(hass, start_date, end_date)

    @property
    def event(self) -> CalendarEvent:
        """Return the next upcoming event."""
        even_list, next_event = self.get_next_event()
        return next_event

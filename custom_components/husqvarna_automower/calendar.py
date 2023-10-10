"""Platform for Husqvarna Automower calendar integration."""
import json
import logging
from datetime import datetime

import homeassistant.util.dt as dt_util
import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityFeature,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WEEKDAYS, WEEKDAYS_TO_RFC5545
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up calendar platform."""
    _LOGGER.debug("entry: %s", entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerCalendar(coordinator, idx)
        for idx, ent in enumerate(coordinator.session.data["data"])
    )


class AutomowerCalendar(CalendarEntity, AutomowerEntity):
    """Representation of the Automower Calendar element."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_name: str | None = None
    _attr_supported_features = (
        CalendarEntityFeature.CREATE_EVENT
        | CalendarEntityFeature.DELETE_EVENT
        | CalendarEntityFeature.UPDATE_EVENT
    )

    def __init__(self, session, idx) -> None:
        """Initialize AutomowerCalendar."""
        super().__init__(session, idx)
        self._event = None
        self._next_event = None
        self.loc = None
        self._attr_unique_id = f"{self.mower_id}_calendar"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    # pylint: disable=unused-argument
    async def async_get_events_data(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        even_list, next_event = self.get_next_event()
        return even_list

    def get_next_event(self) -> tuple[list[CalendarEvent], CalendarEvent]:
        """Get the current or next event."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        self._next_event = CalendarEvent(
            summary="",
            start=dt_util.start_of_local_day() + dt_util.dt.timedelta(days=7),
            end=dt_util.start_of_local_day() + dt_util.dt.timedelta(days=7, hours=2),
        )
        event_list = []
        # pylint: disable=unused-variable
        for task, tasks in enumerate(mower_attributes["calendar"]["tasks"]):
            calendar = mower_attributes["calendar"]["tasks"][task]
            start_of_day = dt_util.start_of_local_day()
            start_mowing = start_of_day + dt_util.dt.timedelta(
                minutes=calendar["start"]
            )
            end_mowing = start_of_day + dt_util.dt.timedelta(
                minutes=calendar["start"] + calendar["duration"]
            )
            day_list = ""
            for days in range(7):
                today = (start_of_day + dt_util.dt.timedelta(days=days)).weekday()
                today_as_string = WEEKDAYS[today]
                if calendar[today_as_string] is True:
                    today_rfc = WEEKDAYS_TO_RFC5545[today_as_string]
                    if day_list == "":
                        day_list = today_rfc
                    else:
                        day_list += "," + str(today_rfc)

            for days in range(7):
                today = (start_of_day + dt_util.dt.timedelta(days=days)).weekday()
                today_as_string = WEEKDAYS[today]
                if calendar[today_as_string] is True:
                    self._event = CalendarEvent(
                        summary=f"{self.mower_name} Mowing schedule {task + 1}",
                        start=start_mowing + dt_util.dt.timedelta(days=days),
                        end=end_mowing + dt_util.dt.timedelta(days=days),
                        description="Description can't be changed",
                        rrule=f"FREQ=WEEKLY;BYDAY={day_list}",
                        uid=task,
                        recurrence_id=f"Recure{task}",
                    )
                    if self._event.start < self._next_event.start:
                        self._next_event = self._event

                    event_list.append(self._event)

        return event_list, self._next_event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return await self.async_get_events_data(hass, start_date, end_date)

    @property
    def event(self) -> CalendarEvent:
        """Return the next upcoming event."""
        # pylint: disable=unused-variable
        event_list, next_event = self.get_next_event()
        return next_event

    async def async_create_event(self, **kwargs) -> None:
        """Add a new event to calendar."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        current_event_list = mower_attributes["calendar"]["tasks"]
        task_list = await self.async_parse_to_husqvarna_string(kwargs)
        await self.aysnc_send_command_to_mower(current_event_list + task_list)

    async def async_update_event(
        self,
        uid: str,
        event: dict[str],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Update an existing event on the calendar."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        current_event_list = mower_attributes["calendar"]["tasks"]
        task_list = await self.async_parse_to_husqvarna_string(event)
        current_event_list[int(uid)] = task_list[0]
        await self.aysnc_send_command_to_mower(current_event_list)
        await self.async_update_ha_state(force_refresh=True)

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete an event on the calendar."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        current_event_list = mower_attributes["calendar"]["tasks"]
        amount_of_tasks = len(current_event_list)
        if amount_of_tasks < 2:
            raise vol.Invalid("You need at least one schedule")
        current_event_list.pop(int(uid))
        await self.aysnc_send_command_to_mower(current_event_list)

    async def async_parse_to_husqvarna_string(
        self,
        event: dict,
    ) -> list:
        """Parse from calendar rrule to mower compatible string."""
        try:
            event["rrule"]
        except KeyError as exc:
            raise vol.Invalid("Only reccuring events are allowed") from exc
        if not "WEEKLY" in event["rrule"]:
            raise vol.Invalid("Please select weekly")
        if not "BYDAY" in event["rrule"]:
            raise vol.Invalid("Please select day(s)")
        rr_list = event["rrule"].split(";")
        days = rr_list[1].lstrip("BYDAY=")
        day_list = days.split(",")
        task_list = []
        start_time_minutes = int(event["dtstart"].hour) * 60 + int(
            event["dtstart"].minute
        )
        end_time_minutes = int(event["dtend"].hour) * 60 + int(event["dtend"].minute)
        duration = end_time_minutes - start_time_minutes
        addition = {
            "start": start_time_minutes,
            "duration": duration,
        }
        for day in WEEKDAYS:
            if WEEKDAYS_TO_RFC5545[day] in day_list:
                addition[day] = True
            else:
                addition[day] = False
        task_list.append(addition)
        return task_list

    async def aysnc_send_command_to_mower(
        self,
        task_list: str,
    ) -> None:
        """Send command to mower."""
        command_type = "calendar"
        string = {
            "data": {
                "type": "calendar",
                "attributes": {"tasks": task_list},
            }
        }
        payload = json.dumps(string)
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

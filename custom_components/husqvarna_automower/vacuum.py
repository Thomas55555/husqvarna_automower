"""Creates a vacuum entity for the mower."""
import json
import logging

from aiohttp import ClientResponseError
import voluptuous as vol

from homeassistant.components.schedule import DOMAIN as SCHEDULE_DOMAIN
from homeassistant.components.vacuum import (
    ATTR_STATUS,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionErrorMessage
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, ERRORCODES, WEEKDAYS
from .entity import AutomowerEntity

SUPPORT_STATE_SERVICES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.STOP
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up vacuum platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HusqvarnaAutomowerEntity(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        "calendar",
        {
            vol.Required("start"): cv.time,
            vol.Required("end"): cv.time,
            vol.Required("monday"): cv.boolean,
            vol.Required("tuesday"): cv.boolean,
            vol.Required("wednesday"): cv.boolean,
            vol.Required("thursday"): cv.boolean,
            vol.Required("friday"): cv.boolean,
            vol.Required("saturday"): cv.boolean,
            vol.Required("sunday"): cv.boolean,
        },
        "async_custom_calendar_command",
    )

    platform.async_register_entity_service(
        "schedule_selector",
        {
            vol.Required("schedule_selector"): cv.string,
        },
        "async_schedule_selector",
    )

    platform.async_register_entity_service(
        "custom_command",
        {
            vol.Required("command_type"): cv.string,
            vol.Required("json_string"): cv.string,
        },
        "async_custom_command",
    )


class HusqvarnaAutomowerStateMixin(object):
    """Don't know, what this is."""

    @property
    def state(self) -> str:
        """Return the state of the mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["state"] in ["PAUSED"]:
            return STATE_PAUSED
        if mower_attributes["mower"]["state"] in [
            "WAIT_UPDATING",
            "WAIT_POWER_UP",
        ]:
            return STATE_IDLE
        if mower_attributes["mower"]["activity"] in ["MOWING", "LEAVING"]:
            return STATE_CLEANING
        if mower_attributes["mower"]["activity"] == "GOING_HOME":
            return STATE_RETURNING
        if (mower_attributes["mower"]["state"] == "RESTRICTED") or (
            mower_attributes["mower"]["activity"] in ["PARKED_IN_CS", "CHARGING"]
        ):
            return STATE_DOCKED
        if (
            mower_attributes["mower"]["state"]
            in [
                "FATAL_ERROR",
                "ERROR",
                "ERROR_AT_POWER_UP",
                "NOT_APPLICABLE",
                "UNKNOWN",
                "STOPPED",
                "OFF",
            ]
        ) or mower_attributes["mower"]["activity"] in [
            "STOPPED_IN_GARDEN",
            "UNKNOWN",
            "NOT_APPLICABLE",
        ]:
            return STATE_ERROR

    @property
    def error(self) -> str:
        """Define an error message if the vacuum is in STATE_ERROR."""
        if self.state == STATE_ERROR:
            mower_attributes = AutomowerEntity.get_mower_attributes(self)
            return ERRORCODES.get(mower_attributes["mower"]["errorCode"])
        return None


class HusqvarnaAutomowerEntity(
    HusqvarnaAutomowerStateMixin, StateVacuumEntity, AutomowerEntity
):
    """Defining each mower Entity."""

    _attr_device_class = f"{DOMAIN}__mower"
    _attr_icon = "mdi:robot-mower"
    _attr_supported_features = SUPPORT_STATE_SERVICES

    def __init__(self, session, idx):
        """Set up HusqvarnaAutomowerEntity."""
        super().__init__(session, idx)
        self._attr_unique_id = self.session.data["data"][self.idx]["id"]

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    @property
    def battery_level(self) -> int:
        """Return the current battery level of the mower."""
        return max(
            0,
            min(
                100,
                AutomowerEntity.get_mower_attributes(self)["battery"]["batteryPercent"],
            ),
        )

    def __get_status(self) -> str:
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        next_start_short = ""
        if mower_attributes["planner"]["nextStartTimestamp"] != 0:
            next_start_dt_obj = AutomowerEntity.datetime_object(
                self, mower_attributes["planner"]["nextStartTimestamp"]
            )
            next_start_short = next_start_dt_obj.strftime(", next start: %a %H:%M")
        if mower_attributes["mower"]["state"] == "UNKNOWN":
            return "Unknown"
        if mower_attributes["mower"]["state"] == "NOT_APPLICABLE":
            return "Not applicable"
        if mower_attributes["mower"]["state"] == "PAUSED":
            return "Paused"
        if mower_attributes["mower"]["state"] == "IN_OPERATION":
            if mower_attributes["mower"]["activity"] == "UNKNOWN":
                return "Unknown"
            if mower_attributes["mower"]["activity"] == "NOT_APPLICABLE":
                return "Not applicable"
            if mower_attributes["mower"]["activity"] == "MOWING":
                return "Mowing"
            if mower_attributes["mower"]["activity"] == "GOING_HOME":
                return "Going to charging station"
            if mower_attributes["mower"]["activity"] == "CHARGING":
                return f"Charging{next_start_short}"
            if mower_attributes["mower"]["activity"] == "LEAVING":
                return "Leaving charging station"
            if mower_attributes["mower"]["activity"] == "PARKED_IN_CS":
                return "Parked"
            if mower_attributes["mower"]["activity"] == "STOPPED_IN_GARDEN":
                return "Stopped"
        if mower_attributes["mower"]["state"] == "WAIT_UPDATING":
            return "Updating"
        if mower_attributes["mower"]["state"] == "WAIT_POWER_UP":
            return "Powering up"
        if mower_attributes["mower"]["state"] == "RESTRICTED":
            if mower_attributes["planner"]["restrictedReason"] == "WEEK_SCHEDULE":
                return f"Schedule{next_start_short}"
            if mower_attributes["planner"]["restrictedReason"] == "PARK_OVERRIDE":
                return "Park override"
            if mower_attributes["planner"]["restrictedReason"] == "SENSOR":
                return "Weather timer"
            if mower_attributes["planner"]["restrictedReason"] == "DAILY_LIMIT":
                return "Daily limit"
            if mower_attributes["planner"]["restrictedReason"] == "NOT_APPLICABLE":
                return "Parked until further notice"
        if mower_attributes["mower"]["state"] == "OFF":
            return "Off"
        if mower_attributes["mower"]["state"] == "STOPPED":
            return "Stopped"
        if mower_attributes["mower"]["state"] in [
            "ERROR",
            "FATAL_ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            return ERRORCODES.get(mower_attributes["mower"]["errorCode"])
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the specific state attributes of this mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return {
            ATTR_STATUS: self.__get_status(),
            "action": mower_attributes["planner"]["override"]["action"],
        }

    async def async_start(self) -> None:
        """Resume schedule."""
        command_type = "actions"
        payload = '{"data": {"type": "ResumeSchedule"}}'
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_pause(self) -> None:
        """Pauses the mower."""
        command_type = "actions"
        payload = '{"data": {"type": "Pause"}}'
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_stop(self, **kwargs) -> None:
        """Parks the mower until next schedule."""
        command_type = "actions"
        payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_return_to_base(self, **kwargs) -> None:
        """Parks the mower until further notice."""
        command_type = "actions"
        payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_custom_calendar_command(
        self,
        start,
        end,
        monday,
        tuesday,
        wednesday,
        thursday,
        friday,
        saturday,
        sunday,
        **kwargs,
    ) -> None:
        """Send a custom calendar command to the mower."""
        start_in_minutes = start.hour * 60 + start.minute
        _LOGGER.debug("start in minutes int: %i", start_in_minutes)
        end_in_minutes = end.hour * 60 + end.minute
        _LOGGER.debug("end in minutes: %i", end_in_minutes)
        duration = end_in_minutes - start_in_minutes
        if duration <= 0:
            raise ConditionErrorMessage("<", "StartingTime must be before EndingTime")
        command_type = "calendar"
        string = {
            "data": {
                "type": "calendar",
                "attributes": {
                    "tasks": [
                        {
                            "start": start_in_minutes,
                            "duration": duration,
                            "monday": monday,
                            "tuesday": tuesday,
                            "wednesday": wednesday,
                            "thursday": thursday,
                            "friday": friday,
                            "saturday": saturday,
                            "sunday": sunday,
                        }
                    ]
                },
            }
        }
        payload = json.dumps(string)
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_schedule_selector(
        self,
        schedule_selector,
        **kwargs,
    ) -> None:
        """Send a schedule created by the schedule helper to the mower."""
        schedule_list = schedule_selector.split(".")
        schedule_id = schedule_list[1]
        _LOGGER.debug("schedule_selector: %s", schedule_id)
        schedule_storage = Store(self.hass, 1, SCHEDULE_DOMAIN)
        schedule_storage_list = await schedule_storage.async_load()
        for ent, schedules in enumerate(schedule_storage_list["items"]):
            _LOGGER.debug("schedule: %s, ent %i", schedules, ent)
            if schedules["id"] == schedule_id:
                schedules.pop("name")
                schedules.pop("id")
                _LOGGER.debug("relevant schedule: %s", schedules)
                task_list = []
                for day, schedule in schedules.items():
                    for daily_task in schedule:
                        if daily_task:
                            start_time = daily_task["from"].split(":")
                            start_time_minutes = int(start_time[0]) * 60 + int(
                                start_time[1]
                            )
                            end_time = daily_task["to"].split(":")
                            end_time_minutes = int(end_time[0]) * 60 + int(end_time[1])
                            duration = end_time_minutes - start_time_minutes
                            addition = {}
                            relevant_day = False
                            addition = {
                                "start": start_time_minutes,
                                "duration": duration,
                            }
                            for relevant_day in WEEKDAYS:
                                if day == relevant_day:
                                    addition[relevant_day] = True
                                else:
                                    addition[relevant_day] = False
                            task_list.append(addition)
                    _LOGGER.debug("task_list: %s", task_list)
                command_type = "calendar"
                string = {
                    "data": {
                        "type": "calendar",
                        "attributes": {"tasks": task_list},
                    }
                }
                payload = json.dumps(string)
                try:
                    await self.session.action(self.mower_id, payload, command_type)
                except ClientResponseError as exception:
                    _LOGGER.error(
                        "Command couldn't be sent to the command que: %s", exception
                    )

    async def async_custom_command(self, command_type, json_string, **kwargs) -> None:
        """Send a custom command to the mower."""
        try:
            await self.session.action(self.mower_id, json_string, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

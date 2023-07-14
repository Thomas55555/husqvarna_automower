"""Creates a vacuum entity for the mower."""
import json
import logging

import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant.components.schedule import DOMAIN as SCHEDULE_DOMAIN
from homeassistant.components.vacuum import (
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
from homeassistant.exceptions import ConditionErrorMessage, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, ERROR_ACTIVITIES, WEEKDAYS
from .entity import AutomowerEntity

SUPPORT_STATE_SERVICES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STOP
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up vacuum platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HusqvarnaAutomowerEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.session.data["data"])
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


class HusqvarnaAutomowerEntity(StateVacuumEntity, AutomowerEntity):
    """Defining each mower Entity."""

    _attr_icon = "mdi:robot-mower"
    _attr_name: str | None = None
    _attr_supported_features = SUPPORT_STATE_SERVICES
    _attr_translation_key = "mower"

    def __init__(self, session, idx):
        """Set up HusqvarnaAutomowerEntity."""
        super().__init__(session, idx)
        self._attr_unique_id = self.coordinator.session.data["data"][self.idx]["id"]

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

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
        ) or mower_attributes["mower"]["activity"] in ERROR_ACTIVITIES:
            return STATE_ERROR

    @property
    def extra_state_attributes(self) -> dict:
        """Return the specific state attributes of this mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        action = mower_attributes["planner"]["override"]["action"]
        action = action.lower() if action is not None else action
        return {
            "action": action,
        }

    async def async_start(self) -> None:
        """Resume schedule."""
        command_type = "actions"
        payload = '{"data": {"type": "ResumeSchedule"}}'
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_pause(self) -> None:
        """Pauses the mower."""
        command_type = "actions"
        payload = '{"data": {"type": "Pause"}}'
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_stop(self, **kwargs) -> None:
        """Parks the mower until next schedule."""
        command_type = "actions"
        payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def async_return_to_base(self, **kwargs) -> None:
        """Parks the mower until further notice."""
        command_type = "actions"
        payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
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
        **kwargs,  # pylint: disable=unused-argument
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
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)
            raise HomeAssistantError("Command not allowed") from exception

    async def async_schedule_selector(
        self,
        schedule_selector,
        **kwargs,  # pylint: disable=unused-argument
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
                    await self.coordinator.session.action(
                        self.mower_id, payload, command_type
                    )
                except ClientResponseError as exception:
                    _LOGGER.error(
                        "Command couldn't be sent to the command que: %s", exception
                    )
                    raise HomeAssistantError("Command not allowed.") from exception

    # pylint: disable=unused-argument
    async def async_custom_command(self, command_type, json_string, **kwargs) -> None:
        """Send a custom command to the mower."""
        try:
            await self.coordinator.session.action(
                self.mower_id, json_string, command_type
            )
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)
            raise HomeAssistantError("Command not allowed.") from exception

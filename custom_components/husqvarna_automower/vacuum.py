"""Creates a vacuum entity for the mower"""
import json
import logging
import time

import voluptuous as vol
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_SEND_COMMAND,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STOP,
    StateVacuumEntity,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform, service
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed

from .const import DOMAIN, ERRORCODES, ICON

SUPPORT_STATE_SERVICES = (
    SUPPORT_STATE
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_RETURN_HOME
    | SUPPORT_BATTERY
    | SUPPORT_START
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        HusqvarnaAutomowerEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data["data"])
    )
    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        "park_and_start",
        {
            vol.Required("command"): cv.string,
            vol.Required("duration"): vol.Coerce(int),
        },
        "async_custom_command",
    )


class HusqvarnaEntity(Entity):
    """Defining the Husqvarna Entity."""

    def __init__(self, coordinator):
        """Pass the coordinator to the class."""
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()


class HusqvarnaAutomowerEntity(HusqvarnaEntity, StateVacuumEntity, CoordinatorEntity):
    """Defining each mower Entity."""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx
        self.mower = self.coordinator.data["data"][self.idx]
        self.mower_attributes = self.mower["attributes"]
        self.connected = self.mower_attributes["metadata"]["connected"]
        self.mower_id = self.mower["id"]
        self.mower_command = None
        self.state_time = None
        self.error_code = None
        self.error_message = None
        self.error_time = None
        self.next_start = None
        self.attributes = None
        self.payload = None
        self.communication_not_possible_already_sent = False
        self.mower_name = f"{self.mower_attributes['system']['model']}_{self.mower_attributes['system']['name']}"
        self.model_string_splited = self.mower_attributes["system"]["model"].split(" ")
        try:
            self.model = (
                f"{self.model_string_splited[1]} {self.model_string_splited[2]}"
            )
        except IndexError:
            self.model = self.mower_attributes["system"]["model"]
        self.mower_name = f"{self.model}_{self.mower_attributes['system']['name']}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.mower_id)},
            "name": self.mower_attributes["system"]["name"],
            "manufacturer": "Husqvarna",
            "model": self.model,
        }

    @property
    def available(self):
        """Return True if the device is available."""
        self._connected = self.coordinator.data["data"][self.idx]["attributes"][
            "metadata"
        ]["connected"]
        if not self._connected and not self.communication_not_possible_already_sent:
            self.communication_not_possible_already_sent = True
            _LOGGER.warning("Connection to %s lost", self.mower_name)
        if self._connected and self.communication_not_possible_already_sent:
            self.communication_not_possible_already_sent = False
            _LOGGER.info("Connected to %s again", self.mower_name)
        return self._connected

    @property
    def name(self):
        """Return the name of the mower."""
        return self.mower_name

    @property
    def unique_id(self):
        """Return a unique ID to use for this mower."""
        return self.coordinator.data["data"][self.idx]["id"]

    @property
    def state(self):
        """Return the state of the mower."""
        self.mower_attributes = self.coordinator.data["data"][self.idx]["attributes"]
        if self.mower_attributes["mower"]["state"] in ["PAUSED"]:
            return STATE_PAUSED
        if self.mower_attributes["mower"]["state"] in [
            "WAIT_UPDATING",
            "WAIT_POWER_UP",
        ]:
            return STATE_IDLE
        if (self.mower_attributes["mower"]["state"] == "RESTRICTED") or (
            self.mower_attributes["mower"]["activity"] in ["PARKED_IN_CS", "CHARGING"]
        ):
            return STATE_DOCKED
        if self.mower_attributes["mower"]["activity"] in ["MOWING", "LEAVING"]:
            return STATE_CLEANING
        if self.mower_attributes["mower"]["activity"] == "GOING_HOME":
            return STATE_RETURNING
        if (
            self.mower_attributes["mower"]["state"]
            in [
                "FATAL_ERROR",
                "ERROR",
                "ERROR_AT_POWER_UP",
                "NOT_APPLICABLE",
                "UNKNOWN",
                "STOPPED",
                "OFF",
            ]
        ) or self.mower_attributes["mower"]["activity"] in [
            "STOPPED_IN_GARDEN",
            "UNKNOWN",
            "NOT_APPLICABLE",
        ]:
            return STATE_ERROR

    @property
    def icon(self):
        """Return the icon of the mower."""
        return ICON

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_STATE_SERVICES

    @property
    def battery_level(self):
        """Return the current battery level of the mower."""
        return max(
            0,
            min(
                100,
                self.coordinator.data["data"][self.idx]["attributes"]["battery"][
                    "batteryPercent"
                ],
            ),
        )

    @property
    def extra_state_attributes(self):
        """Return the specific state attributes of this mower."""
        self.mower_attributes = self.coordinator.data["data"][self.idx]["attributes"]
        self.state_time = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(
                (self.mower_attributes["metadata"]["statusTimestamp"]) / 1000
            ),
        )
        if self.mower_attributes["mower"]["errorCode"] != 0:
            self.error_message = ERRORCODES.get(
                self.mower_attributes["mower"]["errorCode"]
            )
            self.error_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(
                    (self.mower_attributes["mower"]["errorCodeTimestamp"]) / 1000
                ),
            )
        if self.mower_attributes["mower"]["errorCode"] == 0:
            self.error_message = None
            self.error_time = None

        if self.mower_attributes["planner"]["nextStartTimestamp"] != 0:
            self.next_start = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(
                    (self.mower_attributes["planner"]["nextStartTimestamp"]) / 1000
                ),
            )
        if self.mower_attributes["planner"]["nextStartTimestamp"] == 0:
            self.next_start = None

        self.attributes = {
            "mode": self.mower_attributes["mower"]["mode"],
            "activity": self.mower_attributes["mower"]["activity"],
            "state": self.mower_attributes["mower"]["state"],
            "errorMessage": self.error_message,
            "errorTime": self.error_time,
            "nextStart": self.next_start,
            "action": self.mower_attributes["planner"]["override"]["action"],
            "restrictedReason": self.mower_attributes["planner"]["restrictedReason"],
            "statusTimestamp": self.state_time
            # "all_data": self.coordinator.data
        }

        return self.attributes

    async def async_start(self):
        """Resume schedule."""
        self.payload = '{"data": {"type": "ResumeSchedule"}}'
        try:
            await self.coordinator.async_send_command(self.payload, self.mower_id)
        except Exception as exception:
            raise UpdateFailed(exception) from exception

    async def async_pause(self):
        """Pauses the mower."""
        self.payload = '{"data": {"type": "Pause"}}'
        try:
            await self.coordinator.async_send_command(self.payload, self.mower_id)
        except Exception as exception:
            raise UpdateFailed(exception) from exception

    async def async_stop(self, **kwargs):
        """Parks the mower until next schedule."""
        self.payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        try:
            await self.coordinator.async_send_command(self.payload, self.mower_id)
        except Exception as exception:
            raise UpdateFailed(exception) from exception

    async def async_return_to_base(self, **kwargs):
        """Parks the mower until further notice."""
        self.payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        try:
            await self.coordinator.async_send_command(self.payload, self.mower_id)
        except Exception as exception:
            raise UpdateFailed(exception) from exception

    async def async_custom_command(self, command, duration, **kwargs):
        """Parks the mower until further notice."""
        self.command = command
        self.duration = duration
        self.string = {
            "data": {
                "type": self.command,
                "attributes": {"duration": self.duration},
            }
        }
        self.payload = json.dumps(self.string)
        try:
            await self.coordinator.async_send_command(self.payload, self.mower_id)
        except Exception as exception:
            raise UpdateFailed(exception) from exception

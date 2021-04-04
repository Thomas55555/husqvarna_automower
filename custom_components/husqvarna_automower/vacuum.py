"""Creates a vacuum entity for the mower"""
import logging
import time

from homeassistant.components.vacuum import (
    STATE_DOCKED,
    STATE_ERROR,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_SEND_COMMAND,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_STOP,
    StateVacuumEntity,
)
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
        self.mower_timestamp = None
        self.mower_local_timestamp = None
        self.readable_mower_local_timestamp = None
        self.error_code = None
        self.error_code_timestamp = None
        self.next_start_timestamp = None
        self.attributes = None
        self.payload = None
        self.communication_not_possible_already_sent = False
        self.mower_name = f"{self.mower_attributes['system']['model']}_{self.mower_attributes['system']['name']}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.mower_id)},
            "name": self.mower_attributes["system"]["name"],
            "manufacturer": "Husqvarna",
            "model": self.mower_attributes["system"]["model"],
        }

    @property
    def available(self):
        """Return True if the device is available."""
        if not self.connected and not self.communication_not_possible_already_sent:
            self.communication_not_possible_already_sent = True
            _LOGGER.warning("Connection to %s lost", self.mower_name)
        if self.connected and self.communication_not_possible_already_sent:
            self.communication_not_possible_already_sent = False
            _LOGGER.info("Connected to %s again", self.mower_name)
        return self.connected

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
        self.mower_timestamp = (
            self.mower_attributes["metadata"]["statusTimestamp"]
        ) / 1000
        self.mower_local_timestamp = time.localtime(self.mower_timestamp)
        self.readable_mower_local_timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S", self.mower_local_timestamp
        )
        if self.mower_attributes["mower"]["state"] == "IN_OPERATION":
            return f"{self.mower_attributes['mower']['activity']}"
        if self.mower_attributes["mower"]["state"] in [
            "FATAL_ERROR",
            "ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            self.error_code = self.mower_attributes["mower"]["errorCode"]
            return ERRORCODES.get(self.error_code)
        if self.mower_attributes["mower"]["state"] == "RESTRICTED":
            if self.mower_attributes["planner"]["restrictedReason"] == "NOT_APPLICABLE":
                return "Parked until further notice"
            return f"{self.mower_attributes['planner']['restrictedReason']}"
        return f"{self.mower_attributes['mower']['state']}"

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
        if (
            self.coordinator.data["data"][self.idx]["attributes"]["mower"][
                "errorCodeTimestamp"
            ]
            == 0
        ):
            self.error_code_timestamp = "-"
        else:
            self.error_code_timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(
                    (
                        self.coordinator.data["data"][self.idx]["attributes"]["mower"][
                            "errorCodeTimestamp"
                        ]
                    )
                    / 1000
                ),
            )

        if (
            self.coordinator.data["data"][self.idx]["attributes"]["planner"][
                "nextStartTimestamp"
            ]
            == 0
        ):
            self.next_start_timestamp = "-"
        else:
            self.next_start_timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(
                    (
                        self.coordinator.data["data"][self.idx]["attributes"][
                            "planner"
                        ]["nextStartTimestamp"]
                    )
                    / 1000
                ),
            )

        self.attributes = {
            "mode": self.mower_attributes["mower"]["mode"],
            "activity": self.mower_attributes["mower"]["activity"],
            "state": self.mower_attributes["mower"]["state"],
            "errorCode": self.mower_attributes["mower"]["errorCode"],
            "errorCodeTimestamp": self.error_code_timestamp,
            "nextStartTimestamp": self.next_start_timestamp,
            "action": self.mower_attributes["planner"]["override"]["action"],
            "restrictedReason": self.mower_attributes["planner"]["restrictedReason"],
            "statusTimestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(
                    (self.mower_attributes["metadata"]["statusTimestamp"]) / 1000
                ),
            ),
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

import time

from homeassistant.components.vacuum import (
    STATE_CLEANING,
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
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    StateVacuumEntity,
)
from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed

from custom_components.husqvarna_automower.const import DOMAIN, ERRORCODES, ICON
from husqvarna_automower import Return

SUPPORT_STATE_SERVICES = (
    SUPPORT_STATE
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_RETURN_HOME
    | SUPPORT_BATTERY
    | SUPPORT_START
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices(
        HusqvarnaAutomowerEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data["data"])
    )


class HusqvarnaEntity(entity.Entity):
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
        self.access_token = self.coordinator.data["token"]["access_token"]
        self.provider = self.coordinator.data["token"]["provider"]
        self.token_type = self.coordinator.data["token"]["token_type"]
        self.mower_id = self.mower["id"]
        self.api_key = self.coordinator.data["api_key"]

    @property
    def available(self):
        """Return True if the device is available."""
        return self.coordinator.data["data"][self.idx]["attributes"]["metadata"][
            "connected"
        ]

    @property
    def name(self):
        """Return the name of the mower."""
        return f"{self.coordinator.data['data'][self.idx]['attributes']['system']['model']}_{self.coordinator.data['data'][self.idx]['attributes']['system']['name']}"

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
        elif self.mower_attributes["mower"]["state"] in [
            "FATAL_ERROR",
            "ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            self.error_code = self.mower_attributes["mower"]["errorCode"]
            return ERRORCODES.get(self.error_code)
        elif self.mower_attributes["mower"]["state"] == "RESTRICTED":
            if self.mower_attributes["planner"]["restrictedReason"] == "NOT_APPLICABLE":
                return "Parked until further notice"
            else:
                return f"{self.mower_attributes['planner']['restrictedReason']}"
        else:
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
    def device_state_attributes(self):
        """Return the specific state attributes of this mower."""
        self.mower_attributes = self.coordinator.data["data"][self.idx]["attributes"]
        if (
            self.coordinator.data["data"][self.idx]["attributes"]["mower"][
                "errorCodeTimestamp"
            ]
            == 0
        ):
            self.attr_errorCodeTimestamp = "-"
        else:
            self.attr_errorCodeTimestamp = time.strftime(
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
            self.attr_nextStartTimestamp = "-"
        else:
            self.attr_nextStartTimestamp = time.strftime(
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
            "errorCodeTimestamp": self.attr_errorCodeTimestamp,
            "nextStartTimestamp": self.attr_nextStartTimestamp,
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

    async def async_start(self, **kwargs):
        """Resume schedule."""
        self.payload = '{"data": {"type": "ResumeSchedule"}}'
        self.mower_command = Return(
            self.api_key,
            self.access_token,
            self.provider,
            self.token_type,
            self.mower_id,
            self.payload,
        )
        try:
            await self.mower_command.async_mower_command()
            await self.coordinator.async_request_refresh()
        except Exception as exception:
            raise UpdateFailed(exception)

    async def async_pause(self, **kwargs):
        """Pauses the mower."""
        self.payload = '{"data": {"type": "Pause"}}'
        self.mower_command = Return(
            self.api_key,
            self.access_token,
            self.provider,
            self.token_type,
            self.mower_id,
            self.payload,
        )
        try:
            await self.mower_command.async_mower_command()
            await self.coordinator.async_request_refresh()
        except Exception as exception:
            raise UpdateFailed(exception)

    async def async_stop(self, **kwargs):
        """Parks the mower until next schedule."""
        self.payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        self.mower_command = Return(
            self.api_key,
            self.access_token,
            self.provider,
            self.token_type,
            self.mower_id,
            self.payload,
        )
        try:
            await self.mower_command.async_mower_command()
            await self.coordinator.async_request_refresh()
        except Exception as exception:
            raise UpdateFailed(exception)

    async def async_return_to_base(self, **kwargs):
        """Parks the mower until further notice."""
        self.payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        self.mower_command = Return(
            self.api_key,
            self.access_token,
            self.provider,
            self.token_type,
            self.mower_id,
            self.payload,
        )
        try:
            await self.mower_command.async_mower_command()
            await self.coordinator.async_request_refresh()
        except Exception as exception:
            raise UpdateFailed(exception)

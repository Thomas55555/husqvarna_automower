from custom_components.husqvarna_automower.const import DOMAIN, ICON, ERRORCODES
from husqvarna_automower import Return
from homeassistant.helpers import entity
import time
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    UpdateFailed,
)

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_ERROR,
    STATE_DOCKED,
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
    StateVacuumEntity
)


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
        husqvarna_automowerVacuum(coordinator, idx) for idx, ent in enumerate(coordinator.data['data'])
    )


class HusqvarnaEntity(entity.Entity):
    
    """Defining the Husqvarna Entity"""
    def __init__(self, coordinator):
        """Pass the coordinator to the class"""
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()


class husqvarna_automowerVacuum(HusqvarnaEntity, StateVacuumEntity, CoordinatorEntity):

    """Defining each mower Entity"""
    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx

    @property
    def available(self):
        """Return True if the device is available."""
        return self.coordinator.data['data'][self.idx]['attributes']['metadata']['connected']

    @property
    def name(self):
        """Return the name of the vacuum."""
        return f"{self.coordinator.data['data'][self.idx]['attributes']['system']['model']}_{self.coordinator.data['data'][self.idx]['attributes']['system']['name']}"

    @property
    def unique_id(self):
        """Return a unique ID to use for this vacuum."""
        return self.coordinator.data['data'][self.idx]['id']

    @property
    def state(self):
        """Return the state of the vacuum."""
        self.mower_attributes = self.coordinator.data['data'][self.idx]['attributes']
        self.api_key = self.coordinator.data['api_key']
        self.mower_timestamp = (self.mower_attributes['metadata']['statusTimestamp'])/1000
        self.mower_local_timestamp = time.localtime(self.mower_timestamp)
        self.readable_mower_local_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", self.mower_local_timestamp)
        if self.mower_attributes['mower']['state'] == "IN_OPERATION":
            return f"{self.mower_attributes['mower']['activity']}"
        elif self.mower_attributes['mower']['state'] == "FATAL_ERROR":
            self.error_code = self.mower_attributes['mower']['errorCode']
            return ERRORCODES.get(self.error_code)
        elif self.mower_attributes['mower']['state'] == "ERROR":
            self.error_code = self.mower_attributes['mower']['errorCode']
            return ERRORCODES.get(self.error_code)
        elif self.mower_attributes['mower']['state'] == "ERROR_AT_POWER_UP":
            self.error_code = self.mower_attributes['mower']['errorCode']
            return ERRORCODES.get(self.error_code)
        elif self.mower_attributes['mower']['state'] == "RESTRICTED":
            if self.mower_attributes['planner']['restrictedReason'] == "NOT_APPLICABLE":
                return "Parked until further notice"
            else:
                return f"{self.mower_attributes['planner']['restrictedReason']}"
        else:
            return f"{self.mower_attributes['mower']['state']}"


    @property
    def icon(self):
        """Return the icon of the vacuum."""
        return ICON


    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_STATE_SERVICES

    @property
    def battery_level(self):
        """Return the current battery level of the vacuum."""
        return max(0, min(100, self.mower_attributes['battery']['batteryPercent']))

    @property
    def device_state_attributes(self):
        """Return the specific state attributes of this vacuum."""
        self.mower_attributes = self.coordinator.data['data'][self.idx]['attributes']
        if self.mower_attributes['mower']['errorCodeTimestamp'] == 0:
            self.attr_errorCodeTimestamp = "-"
        else:
            self.attr_errorCodeTimestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((self.mower_attributes['mower']['errorCodeTimestamp'])/1000))

        if self.mower_attributes['planner']['nextStartTimestamp'] == 0:
            self.attr_nextStartTimestamp = "-"
        else:
            self.attr_nextStartTimestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((self.mower_attributes['planner']['nextStartTimestamp'])/1000))

        self.attributes = {
            "mode": self.mower_attributes['mower']['mode'],
            "activity": self.mower_attributes['mower']['activity'],
            "state": self.mower_attributes['mower']['state'],
            "errorCode": self.mower_attributes['mower']['errorCode'],
            "errorCodeTimestamp": self.attr_errorCodeTimestamp,
            "nextStartTimestamp": self.attr_nextStartTimestamp,
            "action": self.mower_attributes['planner']['override']['action'],
            "restrictedReason": self.mower_attributes['planner']['restrictedReason'],
            "statusTimestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((self.mower_attributes['metadata']['statusTimestamp'])/1000)),
            #"all_data": self.coordinator.data
        }

        return self.attributes


    def pause(self, **kwargs):
        """Pauses the mower"""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][self.idx]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_pause()
        self._state = "Pausing"

    def stop(self, **kwargs):
        """Parks the mower until next schedule."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][self.idx]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_parkuntilnextschedule()
        self._state = "WEEK_SCHEDULE"


    def return_to_base(self, **kwargs):
        """Parks the mower until further notice."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][self.idx]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_parkuntilfurthernotice()
        self._state = "Parked until further notice"

    def start(self, **kwargs):
        """Resume schedule."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][self.idx]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_resumeschedule()
        self.schedule_update_ha_state()
        self._state = "WEEK_SCHEDULE"

    def __set_state_to_dock(self):
        self._state = STATE_DOCKED
        self.schedule_update_ha_state()

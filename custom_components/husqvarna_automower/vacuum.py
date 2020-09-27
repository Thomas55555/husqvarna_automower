from custom_components.husqvarna_automower.const import DOMAIN, ICON, ERRORCODES
from custom_components.husqvarna_automower.entity import HusqvarnaEntity
from husqvarna_automower import Return
import time

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_CLEAN_SPOT,
    SUPPORT_FAN_SPEED,
    SUPPORT_LOCATE,
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
    VacuumEntity,
)


SUPPORT_STATE_SERVICES = (
    SUPPORT_STATE
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_RETURN_HOME
    | SUPPORT_BATTERY
    | SUPPORT_START
)

FAN_SPEEDS = ["min", "medium", "high", "max"]

async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([husqvarna_automowerVacuum(coordinator, entry)])

class husqvarna_automowerVacuum(HusqvarnaEntity, StateVacuumEntity):

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.coordinator.data['data'][0]['attributes']['system']['name']

    @property
    def state(self):
        # """Return the state of the sensor."""
        # if self.coordinator.data['data'][0]['api_status_code'] == 200:
        #     """Return the state, if api respone is positive"""
        self.api_key = self.coordinator.data['api_key']
        self.mower_attributes = self.coordinator.data['data'][0]['attributes']
        self.mower_timestamp = (self.mower_attributes['metadata']['statusTimestamp'])/1000
        self.mower_local_timestamp = time.localtime(self.mower_timestamp)
        self.readable_mower_local_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", self.mower_local_timestamp)
        if self.mower_attributes['metadata']['connected'] == False:
            return "Not connected"
        elif self.mower_attributes['metadata']['connected'] == True:
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
        # else:
        #     """return the state, if api respone is not 200""""
        #     return self.coordinator.data['data'][0]['api_status_code']



    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON


    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_STATE_SERVICES

    @property
    def battery_level(self):
        """Return the current battery level of the vacuum."""
        return max(0, min(100, self.coordinator.data['data'][0]['attributes']['battery']['batteryPercent']))


    def pause(self, **kwargs):
        """pause."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][0]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_pause()
        self._state = "Pausing"

    def stop(self, **kwargs):
        """park until next schedule."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][0]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_parkuntilnextschedule()
        self._state = "WEEK_SCHEDULE"


    def return_to_base(self, **kwargs):
        """park until further notice."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][0]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_parkuntilfurthernotice()
        self._state = "Parked until further notice"

    def start(self, **kwargs):
        """resume schedule."""
        self.access_token = self.coordinator.data['token']['access_token']
        self.provider = self.coordinator.data['token']['provider']
        self.token_type = self.coordinator.data['token']['token_type']
        self.mower_id = self.coordinator.data['data'][0]['id']
        self.mower_command = Return(self.api_key, self.access_token, self.provider, self.token_type, self.mower_id)
        self.mower_command.mower_resumeschedule()
        self.schedule_update_ha_state()
        self._state = "WEEK_SCHEDULE"

    def __set_state_to_dock(self):
        self._state = STATE_DOCKED
        self.schedule_update_ha_state()

"""HusqvarnaEntity class"""
from homeassistant.helpers import entity
import json
import time
from custom_components.husqvarna_automower.const import DEFAULT_NAME, DOMAIN, ICON, ERRORCODES, VERSION, NAME




class HusqvarnaEntity(entity.Entity):
    def __init__(self, coordinator, config_entry):
        self.coordinator = coordinator
        self.config_entry = config_entry

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
        }


    @property
    def device_state_attributes(self):
        """Return the specific state attributes of this vacuum cleaner."""
        if self.coordinator.data['attributes']['mower']['errorCodeTimestamp'] == 0:
            self.attr_errorCodeTimestamp = "-"
        else:
            self.attr_errorCodeTimestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((self.coordinator.data['attributes']['mower']['errorCodeTimestamp'])/1000))

        if self.coordinator.data['attributes']['planner']['nextStartTimestamp'] == 0:
            self.attr_nextStartTimestamp = "-"
        else:
            self.attr_nextStartTimestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((self.coordinator.data['attributes']['planner']['nextStartTimestamp'])/1000))

        self.attributes = { 
            "type": self.coordinator.data['type'],
            "id": self.coordinator.data['id'],
            "models": self.coordinator.data['attributes']['system']['model'],
            "mode": self.coordinator.data['attributes']['mower']['mode'],
            "activity": self.coordinator.data['attributes']['mower']['activity'],
            "state": self.coordinator.data['attributes']['mower']['state'],
            "errorCode": self.coordinator.data['attributes']['mower']['errorCode'],
            "errorCodeTimestamp": self.attr_errorCodeTimestamp,
            "nextStartTimestamp": self.attr_nextStartTimestamp,
            "action": self.coordinator.data['attributes']['planner']['override']['action'],
            "restrictedReason": self.coordinator.data['attributes']['planner']['restrictedReason'],
            "connected": self.coordinator.data['attributes']['metadata']['connected'],
            "statusTimestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((self.coordinator.data['attributes']['metadata']['statusTimestamp'])/1000)),
            "all_data": self.coordinator.data
        }

        # self.attributes = { 
        #     "type": self.coordinator.data['type'],
        #     "id": self.coordinator.data['id'],
        #     "model": self.coordinator.data['attributes']['system']['model'],
        #     "mode": self.coordinator.data['attributes']['mower']['mode'],
        #     "activity": self.coordinator.data['attributes']['mower']['activity'],
        #     "state": self.coordinator.data['attributes']['mower']['state'],
        #     "errorCode": self.coordinator.data['attributes']['mower']['errorCode'],
        #     "errorCodeTimestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((self.coordinator.data['attributes']['mower']['errorCodeTimestamp'])/1000)),
        #     "nextStartTimestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((self.coordinator.data['attributes']['planner']['nextStartTimestamp'])/1000)),
        #     "action": self.coordinator.data['attributes']['planner']['override']['action'],
        #     "restrictedReason": self.coordinator.data['attributes']['planner']['restrictedReason'],
        #     "connected": self.coordinator.data['attributes']['metadata']['connected'],
        #     "statusTimestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((self.coordinator.data['attributes']['metadata']['statusTimestamp'])/1000)),
        # }

        return self.attributes
# type: mower
# id: b2bc3443-b31a-4c7f-834e-d6e408c53f1b
# attributes:
#   system:
#     name: Haffi
#     model: 315X
#     serialNumber: 181309473
#   battery:
#     batteryPercent: 88
#   mower:
#     mode: MAIN_AREA
#     activity: MOWING
#     state: IN_OPERATION
#     errorCode: 0
#     errorCodeTimestamp: 0
#   calendar:
#     tasks:
#       - start: 660
#         duration: 540
#         monday: true
#         tuesday: true
#         wednesday: false
#         thursday: true
#         friday: false
#         saturday: false
#         sunday: true
#   planner:
#     nextStartTimestamp: 0
#     override:
#       action: NO_SOURCE
#     restrictedReason: NOT_APPLICABLE
#   metadata:
#     connected: true
#     statusTimestamp: 1597073066000

                
    # @property_bisher
    # def device_state_attributes(self):
    #     """Return the state attributes."""
    #     # return {
    #     #     "api_error_code:": self.coordinator.data
    #     #     }


    #     if self.coordinator.data['api_status_code'] == 200:
    #         return self.coordinator.data
            
    #         # {
    #         #     "api_status_code:": self.coordinator.data['api_status_code'],
    #         #     "scope:": self.coordinator.data['scope'],
    #         #     "token_type": self.coordinator.data['token_type'],
    #         #     "access_token": self.coordinator.data['access_token'],
    #         #     "refresh_token": self.coordinator.data['refresh_token'],
    #         #     "mower": self.coordinator.data['mower_respone']['data']
    #         #     }
    #     else:
    #         return {
    #             "api_error_code:": self.coordinator.data
    #             }

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()

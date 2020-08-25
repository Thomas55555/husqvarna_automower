from homeassistant.helpers import entity
import time
from custom_components.husqvarna_automower.const import DOMAIN, VERSION, NAME


class HusqvarnaEntity(entity.Entity):
    """Defining the Entity"""
    
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
            #"all_data": self.coordinator.data
        }

        return self.attributes

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()

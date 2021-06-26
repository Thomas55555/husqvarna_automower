"""Platform for Husqvarna Automower device tracker integration."""
import logging

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        AutomowerTracker(coordinator, idx)
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


class AutomowerTracker(TrackerEntity, HusqvarnaEntity, CoordinatorEntity):
    """Defining the Device Tracker Entity."""

    def __init__(self, coordinator, idx):
        super().__init__(coordinator)
        self.idx = idx
        self.mower = self.coordinator.data["data"][self.idx]
        self.mower_attributes = self.mower["attributes"]
        self.connected = self.mower_attributes["metadata"]["connected"]
        self.mower_id = self.mower["id"]
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
    def name(self):
        """Return the name of the entity."""
        return f"{self.mower_name}_Device Tracker"

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return "{self.coordinator.data['data'][self.idx]['id']}_dt"

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def latitude(self):
        """Return latitude value of the device."""
        self.lat = self.coordinator.data["data"][self.idx]["attributes"]["positions"][
            0
        ]["latitude"]
        return self.lat

    @property
    def longitude(self):
        """Return longitude value of the device."""
        self.long = self.coordinator.data["data"][self.idx]["attributes"]["positions"][
            0
        ]["longitude"]
        return self.long

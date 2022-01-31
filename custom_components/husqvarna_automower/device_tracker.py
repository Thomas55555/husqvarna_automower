"""Platform for Husqvarna Automower device tracker integration."""
from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AutomowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup device_tracker platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerTracker(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class AutomowerTracker(TrackerEntity, AutomowerEntity):
    """Defining the Device Tracker Entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self.mower_name

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_dt"

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        lat = AutomowerEntity.get_mower_attributes(self)["positions"][0]["latitude"]
        return lat

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        lon = AutomowerEntity.get_mower_attributes(self)["positions"][0]["longitude"]
        return lon

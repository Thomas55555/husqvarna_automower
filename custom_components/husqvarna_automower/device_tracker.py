"""Platform for Husqvarna Automower device tracker integration."""
from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AutomowerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device_tracker platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerTracker(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class AutomowerTracker(TrackerEntity, AutomowerEntity):
    """Defining the Device Tracker Entity."""

    def __init__(self, session, idx):
        """Initialize AutomowerDeviceTracker."""
        super().__init__(session, idx)
        self._attr_unique_id = f"{self.mower_id}_dt"

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

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

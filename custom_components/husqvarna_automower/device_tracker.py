"""Platform for Husqvarna Automower device tracker integration."""
import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device_tracker platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list = []
    # pylint: disable=unused-variable
    for idx, ent in enumerate(coordinator.session.data["data"]):
        try:
            assert (
                coordinator.session.data["data"][idx]["attributes"]["positions"][0][
                    "latitude"
                ]
                is not None
            )
            entity_list.append(AutomowerTracker(coordinator, idx))
        except (IndexError, AssertionError):
            pass

    async_add_entities(entity_list)


class AutomowerTracker(TrackerEntity, AutomowerEntity):
    """Defining the Device Tracker Entity."""

    _attr_name: str | None = None

    def __init__(self, session, idx):
        """Initialize AutomowerDeviceTracker."""
        super().__init__(session, idx)
        self._attr_unique_id = f"{self.mower_id}_dt"

    @property
    def source_type(self) -> SourceType:
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

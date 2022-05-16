"""Creates a sesnor entity for the mower"""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ERRORCODES
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup select platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerSensor(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class AutomowerSensor(SensorEntity, AutomowerEntity):
    """Defining the Sensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self.mower_name} Problem Sensor"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_problem_sensor"

    @property
    def native_value(self) -> str:
        """Return a the current problem of the mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["state"] == "WAIT_UPDATING":
            return "Updating"
        if mower_attributes["mower"]["state"] == "WAIT_POWER_UP":
            return "Powering up"
        if mower_attributes["mower"]["state"] == "RESTRICTED":
            return mower_attributes["planner"]["restrictedReason"]
        if mower_attributes["mower"]["state"] == "OFF":
            return "Off"
        if mower_attributes["mower"]["state"] == "STOPPED":
            return "Stopped"
        if mower_attributes["mower"]["state"] in [
            "ERROR",
            "FATAL_ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            return ERRORCODES.get(mower_attributes["mower"]["errorCode"])
        return None

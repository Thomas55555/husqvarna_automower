"""Creates a binary sesnor entity for the mower"""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
        AutomowerBatteryChargingBinarySensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerLeavingDockBinarySensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerErrorBinarySensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )


class AutomowerBatteryChargingBinarySensor(BinarySensorEntity, AutomowerEntity):
    """Defining the AutomowerProblemSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Battery Charging"
        self._attr_unique_id = f"{self.mower_id}_battery_charging"

    @property
    def is_on(self) -> bool:
        """Return if the mower is charging."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["activity"] == "CHARGING":
            return True
        if mower_attributes["mower"]["activity"] != "CHARGING":
            return False


class AutomowerLeavingDockBinarySensor(BinarySensorEntity, AutomowerEntity):
    """Defining the AutomowerProblemSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Leaving Dock"
        self._attr_unique_id = f"{self.mower_id}_leaving_dock"

    @property
    def is_on(self) -> bool:
        """Return if the mower is leaving the dock."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["activity"] == "LEAVING":
            return True
        if mower_attributes["mower"]["activity"] != "LEAVING":
            return False


class AutomowerErrorBinarySensor(BinarySensorEntity, AutomowerEntity):
    """Defining the AutomowerErrorSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Error"
        self._attr_unique_id = f"{self.mower_id}_error"

    @property
    def is_on(self) -> bool:
        """Return if the mower is in an error status."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["state"] in [
            "ERROR",
            "FATAL_ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            return True
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the specific state attributes of this mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if self.is_on:
            return {
                "error_code": int(mower_attributes["mower"]["errorCode"]),
                "description": ERRORCODES.get(mower_attributes["mower"]["errorCode"]),
            }

        return {"ERROR_CODE": -1, "DESCRIPTION": "No Error"}

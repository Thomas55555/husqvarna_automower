"""Creates a sesnor entity for the mower"""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DOMAIN, ERRORCODES
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


TIME_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="cuttingBladeUsageTime",
        name="Cutting Blade Usage Time",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="totalChargingTime",
        name="Total Charging Time",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="totalCuttingTime",
        name="Total Cutting Time",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="totalRunningTime",
        name="Total Running Time",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="totalSearchingTime",
        name="Total Searching Time",
        icon="mdi:clock-outline",
    ),
)

CYCLE_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="numberOfChargingCycles",
        name="Number Of Charging Cycles",
        icon="mdi:battery-sync-outline",
    ),
    SensorEntityDescription(
        key="numberOfCollisions",
        name="Number Of Collisions",
        icon="mdi:counter",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup select platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerProblemSensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerBatterySensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerNextStartSensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerModeSensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerTimeStatisticsSensor(session, idx, description)
        for idx, ent in enumerate(session.data["data"])
        for description in TIME_SENSOR_TYPES
    )
    async_add_entities(
        AutomowerCycleStatisticsSensor(session, idx, description)
        for idx, ent in enumerate(session.data["data"])
        for description in CYCLE_SENSOR_TYPES
    )


class AutomowerProblemSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerProblemSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Problem Sensor"
        self._attr_unique_id = f"{self.mower_id}_problem_sensor"

    @property
    def native_value(self) -> str:
        """Return a the current problem of the mower."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["mower"]["state"] == "RESTRICTED":
            if mower_attributes["planner"]["restrictedReason"] == "NOT_APPLICABLE":
                return None
            return mower_attributes["planner"]["restrictedReason"]
        if mower_attributes["mower"]["state"] in [
            "ERROR",
            "FATAL_ERROR",
            "ERROR_AT_POWER_UP",
        ]:
            return ERRORCODES.get(mower_attributes["mower"]["errorCode"])
        if mower_attributes["mower"]["state"] in [
            "UNKNOWN",
            "STOPPED",
            "OFF",
        ]:
            return mower_attributes["mower"]["state"]
        if mower_attributes["mower"]["activity"] in [
            "STOPPED_IN_GARDEN",
            "UNKNOWN",
            "NOT_APPLICABLE",
        ]:
            return mower_attributes["mower"]["activity"]
        return None


class AutomowerBatterySensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerBatterySensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Battery Level"
        self._attr_unique_id = f"{self.mower_id}_battery_level"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return AutomowerEntity.get_mower_attributes(self)["battery"]["batteryPercent"]


class AutomowerNextStartSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerNextStartSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Next Start"
        self._attr_unique_id = f"{self.mower_id}_next_start"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        next_start = None
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        if mower_attributes["planner"]["nextStartTimestamp"] != 0:
            next_start = AutomowerEntity.datetime_object(
                self, mower_attributes["planner"]["nextStartTimestamp"]
            )
            return next_start
        return None


class AutomowerModeSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerModeSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Mode"
        self._attr_unique_id = f"{self.mower_id}_mode"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["mower"]["mode"]


class AutomowerTimeStatisticsSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerTimeStatisticsSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, session, idx, description: SensorEntityDescription):
        super().__init__(session, idx)
        self.entity_description = description
        self._attr_name = f"{self.mower_name} {description.name}"
        self._attr_unique_id = f"{self.mower_id}_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return dt_util.dt.timedelta(
            seconds=mower_attributes["statistics"][self.entity_description.key]
        )


class AutomowerCycleStatisticsSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerCycleStatictisSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, session, idx, description: SensorEntityDescription):
        super().__init__(session, idx)
        self.entity_description = description
        self._attr_name = f"{self.mower_name} {description.name}"
        self._attr_unique_id = f"{self.mower_id}_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["statistics"][self.entity_description.key]

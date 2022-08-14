"""Creates a sensor entity for the mower."""
from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TIME_SECONDS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ERRORCODES, NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class AutomowerSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[AutomowerEntity], int]


@dataclass
class AutomowerSensorEntityDescription(
    SensorEntityDescription, AutomowerSensorRequiredKeysMixin
):
    """Describes a sensor sensor entity."""


SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    AutomowerSensorEntityDescription(
        key="cuttingBladeUsageTime",
        name="Cutting blade usage time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_SECONDS,
        value_fn=lambda data: data["statistics"]["cuttingBladeUsageTime"],
    ),
    AutomowerSensorEntityDescription(
        key="totalChargingTime",
        name="Total charging time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_SECONDS,
        value_fn=lambda data: data["statistics"]["totalChargingTime"],
    ),
    AutomowerSensorEntityDescription(
        key="totalCuttingTime",
        name="Total cutting time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_SECONDS,
        value_fn=lambda data: data["statistics"]["totalCuttingTime"],
    ),
    AutomowerSensorEntityDescription(
        key="totalRunningTime",
        name="Total running time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_SECONDS,
        value_fn=lambda data: data["statistics"]["totalRunningTime"],
    ),
    AutomowerSensorEntityDescription(
        key="totalSearchingTime",
        name="Total searching time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_SECONDS,
        value_fn=lambda data: data["statistics"]["totalSearchingTime"],
    ),
    AutomowerSensorEntityDescription(
        key="numberOfChargingCycles",
        name="Number of charging cycles",
        icon="mdi:battery-sync-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["statistics"]["numberOfChargingCycles"],
    ),
    AutomowerSensorEntityDescription(
        key="numberOfCollisions",
        name="Number of collisions",
        icon="mdi:counter",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["statistics"]["numberOfCollisions"],
    ),
    AutomowerSensorEntityDescription(
        key="totalSearchingTime_percentage",
        name="Searching time percent",
        icon="mdi:percent",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: round(
            data["statistics"]["totalSearchingTime"]
            / data["statistics"]["totalRunningTime"]
            * 100,
            2,
        ),
    ),
    AutomowerSensorEntityDescription(
        key="totalCuttingTime_percentage",
        name="Cutting time percent",
        icon="mdi:percent",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: round(
            data["statistics"]["totalCuttingTime"]
            / data["statistics"]["totalRunningTime"]
            * 100,
            2,
        ),
    ),
    AutomowerSensorEntityDescription(
        key="battery_level",
        name="Battery level",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data["battery"]["batteryPercent"],
    ),
    AutomowerSensorEntityDescription(
        key="next_start",
        name="Next start",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: AutomowerEntity.datetime_object(
            data, data["planner"]["nextStartTimestamp"]
        ),
    ),
    AutomowerSensorEntityDescription(
        key="mode",
        name="Mode",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["mower"]["mode"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerProblemSensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
    )
    async_add_entities(
        AutomowerStatisticsSensor(session, idx, description)
        for idx, ent in enumerate(session.data["data"])
        for description in SENSOR_TYPES
    )
    async_add_entities(
        AutomowerCuttingHeightSensor(session, idx)
        for idx, ent in enumerate(session.data["data"])
        if any(
            ele in session.data["data"][idx]["attributes"]["system"]["model"]
            for ele in NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT
        )
    )


class AutomowerProblemSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerProblemSensor Entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Problem sensor"

    def __init__(self, session, idx):
        """Set up AutomowerProblemSensor."""
        super().__init__(session, idx)
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


class AutomowerStatisticsSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerTimeStatisticsSensor Entity."""

    def __init__(self, session, idx, description: AutomowerSensorEntityDescription):
        """Set up AutomowerStatisticsSensors."""
        super().__init__(session, idx)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{self.mower_id}_{description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return self.entity_description.value_fn(mower_attributes)


class AutomowerCuttingHeightSensor(SensorEntity, AutomowerEntity):
    """Defining the AutomowerPercentageTimeSensor Entity."""

    _attr_entity_category: EntityCategory = EntityCategory.CONFIG
    _attr_icon = "mdi:grass"
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _attr_name = "Cutting height"

    def __init__(self, session, idx):
        """Initialize AutomowerNumber."""
        super().__init__(session, idx)
        self._attr_unique_id = f"{self.mower_id}_cuttingheight_sensor"

    @property
    def native_value(self) -> int:
        """Return the entity value."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["cuttingHeight"]

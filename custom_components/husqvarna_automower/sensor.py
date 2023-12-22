"""Creates a sensor entity for the mower."""
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, fields
from aioautomower.model import MowerAttributes
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import AutomowerDataUpdateCoordinator

from .const import (
    DOMAIN,
)
from .entity import AutomowerBaseEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class AutomowerSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[AutomowerBaseEntity], int]
    available_fn: Callable[[AutomowerBaseEntity], bool]


@dataclass
class AutomowerSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor sensor entity."""


SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    # AutomowerSensorEntityDescription(
    #     key="cuttingBladeUsageTime",
    #     translation_key="cutting_blade_usage_time",
    #     icon="mdi:clock-outline",
    #     entity_registry_enabled_default=True,
    #     entity_category=EntityCategory.DIAGNOSTIC,
    #     state_class=SensorStateClass.TOTAL,
    #     device_class=SensorDeviceClass.DURATION,
    #     native_unit_of_measurement=UnitOfTime.SECONDS,
    #     value_fn=lambda data: data["statistics"]["cuttingBladeUsageTime"],
    #     available_fn=lambda data: True,
    # ),
    AutomowerSensorEntityDescription(
        key="total_charging_time",
        translation_key="total_charging_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    AutomowerSensorEntityDescription(
        key="total_cutting_time",
        translation_key="total_cutting_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    AutomowerSensorEntityDescription(
        key="total_running_time",
        translation_key="total_running_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    AutomowerSensorEntityDescription(
        key="total_searching_time",
        translation_key="total_searching_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    AutomowerSensorEntityDescription(
        key="number_of_charging_cycles",
        translation_key="number_of_charging_cycles",
        icon="mdi:battery-sync-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    AutomowerSensorEntityDescription(
        key="number_of_collisions",
        translation_key="number_of_collisions",
        icon="mdi:counter",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # AutomowerSensorEntityDescription(
    #     key="battery_level",
    #     translation_key="battery_level",
    #     entity_registry_enabled_default=True,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=SensorDeviceClass.BATTERY,
    #     native_unit_of_measurement=PERCENTAGE,
    #     value_fn=lambda data: data["battery"]["batteryPercent"],
    #     available_fn=lambda data: False
    #     if (data["battery"]["batteryPercent"] == 0)
    #     and (data["metadata"]["connected"] is False)
    #     else True,
    # ),
    # AutomowerSensorEntityDescription(
    #     key="mode",
    #     translation_key="mode_list",
    #     entity_registry_enabled_default=False,
    #     device_class=SensorDeviceClass.ENUM,
    #     options=["main_area", "secondary_area", "home", "demo", "unknown"],
    #     value_fn=lambda data: data["mower"]["mode"].lower(),
    #     available_fn=lambda data: True,
    # ),
    # AutomowerSensorEntityDescription(
    #     key="cuttingHeight",
    #     translation_key="cutting_height",
    #     entity_registry_enabled_default=True,
    #     icon="mdi:grass",
    #     state_class=SensorStateClass.MEASUREMENT,
    #     value_fn=lambda data: data["cuttingHeight"],
    #     available_fn=lambda data: True,
    # ),
    AutomowerSensorEntityDescription(
        key="total_drive_distance",
        translation_key="total_drive_distance",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    coordinator: AutomowerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerSensorEntity(mower_id, coordinator, description)
        for mower_id in coordinator.data
        for description in SENSOR_TYPES
    )
    # for description in SENSOR_TYPES:
    #     _LOGGER.debug(description)
    #     try:
    #         async_add_entities(
    #             AutomowerSensorEntity(mower_id, coordinator, description)
    #             for mower_id in coordinator.data
    #         )
    #     except KeyError:
    #         pass


class AutomowerSensorEntity(SensorEntity, AutomowerBaseEntity):
    """Defining the Automower Sensors with AutomowerSensorEntityDescription."""

    def __init__(
        self,
        mower_id: str,
        coordinator: AutomowerDataUpdateCoordinator,
        description: AutomowerSensorEntityDescription,
    ) -> None:
        """Set up AutomowerSensors."""
        super().__init__(mower_id, coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.mower_id}_{description.key}"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        mower_attributes = self.mower_attributes
        value = self.mower_attributes.statistics
        return getattr(self.mower_attributes.statistics, self.entity_description.key)

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self.mower_attributes.metadata.connected

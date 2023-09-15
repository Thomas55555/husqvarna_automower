"""Creates a sensor entity for the mower."""
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

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
from shapely.geometry import Point, Polygon

from .const import (
    CONF_ZONES,
    DOMAIN,
    ERROR_ACTIVITIES,
    ERROR_STATES,
    ERRORCODES,
    HOME_LOCATION,
    NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT,
    ZONE_COORD,
    ZONE_ID,
    ZONE_MOWERS,
    ZONE_NAME,
)
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class AutomowerSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[AutomowerEntity], int]
    available_fn: Callable[[AutomowerEntity], bool]


@dataclass
class AutomowerSensorEntityDescription(
    SensorEntityDescription, AutomowerSensorRequiredKeysMixin
):
    """Describes a sensor sensor entity."""


def get_problem(mower_attributes) -> dict:
    """Get the mower attributes of the current mower."""
    if mower_attributes["mower"]["activity"] == "CHARGING":
        return "charging"
    if mower_attributes["mower"]["state"] == "RESTRICTED":
        if mower_attributes["planner"]["restrictedReason"] == "NOT_APPLICABLE":
            return "parked_until_further_notice"
        return mower_attributes["planner"]["restrictedReason"]
    if mower_attributes["mower"]["state"] in ERROR_STATES:
        return ERRORCODES.get(mower_attributes["mower"]["errorCode"])
    if mower_attributes["mower"]["state"] in [
        "UNKNOWN",
        "STOPPED",
        "OFF",
    ]:
        return mower_attributes["mower"]["state"]
    if mower_attributes["mower"]["activity"] in ERROR_ACTIVITIES:
        return mower_attributes["mower"]["activity"]
    return None


def problem_list() -> list:
    """Get a list with possible problems for the current mower."""
    error_list = list(ERRORCODES.values())
    error_list_low = [x.lower() for x in error_list]
    other_reasons = [
        "off",
        "unknown",
        "stopped",
        "stopped_in_garden",
        "not_applicable",
        "none",
        "week_schedule",
        "park_override",
        "sensor",
        "daily_limit",
        "fota",
        "frost",
        "parked_until_further_notice",
        "charging",
    ]
    return error_list_low + other_reasons


SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    AutomowerSensorEntityDescription(
        key="cuttingBladeUsageTime",
        translation_key="cutting_blade_usage_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["statistics"]["cuttingBladeUsageTime"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalChargingTime",
        translation_key="total_charging_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["statistics"]["totalChargingTime"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalCuttingTime",
        translation_key="total_cutting_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["statistics"]["totalCuttingTime"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalRunningTime",
        translation_key="total_running_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["statistics"]["totalRunningTime"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalSearchingTime",
        translation_key="total_searching_time",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["statistics"]["totalSearchingTime"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="numberOfChargingCycles",
        translation_key="number_of_charging_cycles",
        icon="mdi:battery-sync-outline",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["statistics"]["numberOfChargingCycles"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="numberOfCollisions",
        translation_key="number_of_collisions",
        icon="mdi:counter",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["statistics"]["numberOfCollisions"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalSearchingTime_percentage",
        translation_key="searching_time_percent",
        icon="mdi:percent",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda data: data["statistics"]["totalSearchingTime"]
        / data["statistics"]["totalRunningTime"]
        * 100,
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalCuttingTime_percentage",
        translation_key="cutting_time_percent",
        icon="mdi:percent",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda data: data["statistics"]["totalCuttingTime"]
        / data["statistics"]["totalRunningTime"]
        * 100,
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data["battery"]["batteryPercent"],
        available_fn=lambda data: False
        if (data["battery"]["batteryPercent"] == 0)
        and (data["metadata"]["connected"] is False)
        else True,
    ),
    AutomowerSensorEntityDescription(
        key="next_start",
        translation_key="next_start",
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: AutomowerEntity.datetime_object(
            data, data["planner"]["nextStartTimestamp"]
        ),
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="mode",
        translation_key="mode_list",
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=["main_area", "secondary_area", "home", "demo", "unknown"],
        value_fn=lambda data: data["mower"]["mode"].lower(),
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="problem_sensor",
        translation_key="problem_list",
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.ENUM,
        options=problem_list(),
        value_fn=lambda data: None
        if get_problem(data) is None
        else get_problem(data).lower(),
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="cuttingHeight",
        translation_key="cutting_height",
        entity_registry_enabled_default=True,
        icon="mdi:grass",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["cuttingHeight"],
        available_fn=lambda data: True,
    ),
    AutomowerSensorEntityDescription(
        key="totalDriveDistance",
        translation_key="total_drive_distance",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        value_fn=lambda data: data["statistics"]["totalDriveDistance"],
        available_fn=lambda data: True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list = []

    # pylint: disable=unused-variable
    for idx, ent in enumerate(coordinator.session.data["data"]):
        if entry.options.get(CONF_ZONES):
            entity_list.append(AutomowerZoneSensor(coordinator, idx, entry))
        for description in SENSOR_TYPES:
            try:
                description.value_fn(
                    coordinator.session.data["data"][idx]["attributes"]
                )
                if description.key == "cuttingHeight":
                    if (
                        any(
                            ele
                            in coordinator.session.data["data"][idx]["attributes"][
                                "system"
                            ]["model"]
                            for ele in NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT
                        )
                        and coordinator.session.data["data"][idx]["attributes"][
                            "cuttingHeight"
                        ]
                        is not None
                    ):
                        entity_list.append(
                            AutomowerSensor(coordinator, idx, description)
                        )
                if description.key != "cuttingHeight":
                    entity_list.append(AutomowerSensor(coordinator, idx, description))
            except KeyError:
                pass
    async_add_entities(entity_list)


class AutomowerZoneSensor(SensorEntity, AutomowerEntity):
    """Define the AutomowerZoneSensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "zone"

    def __init__(self, coordinator, idx, entry):
        """Initialize the zone object."""
        super().__init__(coordinator, idx)
        self._attr_unique_id = f"{self.mower_id}_zone_sensor"
        self.entry = entry
        self.zones = self._load_zones()
        self.home_location = self.entry.options.get(self.mower_id, {}).get(
            HOME_LOCATION, None
        )
        self.zone = {ZONE_NAME: "Unknown"}
        self.zone_id = "unknown"

    def _load_zones(self):
        """Load zones from a config entry."""
        zones = json.loads(self.entry.options.get(CONF_ZONES, "{}"))
        if not isinstance(zones, dict):
            return {}
        sel_zones = {}
        for zone_id, zone in zones.items():
            if self.mower_id in zone.get(ZONE_MOWERS):
                sel_zones[zone_id] = zone

        return sel_zones

    def _find_current_zone(self):
        """Find current zone."""
        if self.is_home and self.home_location:
            self.zone = {ZONE_NAME: "Home"}
            self.zone_id = "home"
            return

        lat = AutomowerEntity.get_mower_attributes(self)["positions"][0]["latitude"]
        lon = AutomowerEntity.get_mower_attributes(self)["positions"][0]["longitude"]
        location = Point(lat, lon)
        for zone_id, zone in self.zones.items():
            zone_poly = Polygon(zone.get(ZONE_COORD))
            if zone_poly.contains(location):
                self.zone = zone
                self.zone_id = zone_id
                return
        self.zone = {ZONE_NAME: "Unknown"}
        self.zone_id = "unknown"

    @property
    def native_value(self) -> str:
        """Return a the current zone of the mower."""
        self._find_current_zone()
        return self.zone.get(ZONE_NAME)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the specific state attributes of this mower."""
        return {ZONE_ID: self.zone_id}


class AutomowerSensor(SensorEntity, AutomowerEntity):
    """Defining the Automower Sensors with AutomowerSensorEntityDescription."""

    def __init__(
        self, session, idx, description: AutomowerSensorEntityDescription
    ) -> None:
        """Set up AutomowerSensors."""
        super().__init__(session, idx)
        self.entity_description = description
        self._attr_unique_id = f"{self.mower_id}_{description.key}"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return self.entity_description.value_fn(mower_attributes)

    @property
    def available(self):
        """Return the availability of the sensor."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return self.entity_description.available_fn(mower_attributes)

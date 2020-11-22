# Base component constants
NAME = "husqvarna_automower"
DOMAIN = "husqvarna_automower"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.6.1"

ISSUE_URL = "https://github.com/Thomas55555/husqvarna_automower"

# Icons
ICON = "mdi:robot-mower"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
##SENSOR = "sensor"
VACUUM = "vacuum"
PLATFORMS = [VACUUM]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_API_KEY = "api_key"


# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# Errorcodes
ERRORCODES = {
    0: "Unexpected error",
    1: "Outside working area",
    2: "No loop signal",
    3: "Wrong loop signal",
    4: "Loop sensor problem, front",
    5: "Loop sensor problem, rear",
    6: "Loop sensor problem, left",
    7: "Loop sensor problem, right",
    8: "Wrong PIN code",
    9: "Trapped",
    10: "Upside down",
    11: "Low battery",
    12: "Empty battery",
    13: "No drive",
    14: "Mower lifted",
    15: "Lifted",
    16: "Stuck in charging station",
    17: "Charging station blocked",
    18: "Collision sensor problem, rear",
    19: "Collision sensor problem, front",
    20: "Wheel motor blocked, right",
    21: "Wheel motor blocked, left",
    22: "Wheel drive problem, right",
    23: "Wheel drive problem, left",
    24: "Cutting system blocked",
    25: "Cutting system blocked",
    26: "Invalid sub-device combination",
    27: "Settings restored",
    28: "Memory circuit problem",
    29: "Slope too steep",
    30: "Charging system problem",
    31: "STOP button problem",
    32: "Tilt sensor problem",
    33: "Mower tilted",
    34: "Cutting stopped - slope too steep",
    35: "Wheel motor overloaded, right",
    36: "Wheel motor overloaded, left",
    37: "Charging current too high",
    38: "Electronic problem",
    39: "Cutting motor problem",
    40: "Limited cutting height range",
    41: "Unexpected cutting height adj",
    42: "Limited cutting height range",
    43: "Cutting height problem, drive",
    44: "Cutting height problem, curr",
    45: "Cutting height problem, dir",
    46: "Cutting height blocked",
    47: "Cutting height problem",
    48: "No response from charger",
    49: "Ultrasonic problem",
    50: "Guide 1 not found",
    51: "Guide 2 not found",
    52: "Guide 3 not found",
    53: "GPS navigation problem",
    54: "Weak GPS signal",
    55: "Difficult finding home",
    56: "Guide calibration accomplished",
    57: "Guide calibration failed",
    58: "Temporary battery problem",
    59: "Temporary battery problem",
    60: "Temporary battery problem",
    61: "Temporary battery problem",
    62: "Temporary battery problem",
    63: "Temporary battery problem",
    64: "Temporary battery problem",
    65: "Temporary battery problem",
    66: "Battery problem",
    67: "Battery problem",
    68: "Temporary battery problem",
    69: "Alarm! Mower switched off",
    70: "Alarm! Mower stopped",
    71: "Alarm! Mower lifted",
    72: "Alarm! Mower tilted",
    73: "Alarm! Mower in motion",
    74: "Alarm! Outside geofence",
    75: "Connection changed",
    76: "Connection NOT changed",
    77: "Com board not available",
    78: "Slipped - Mower has Slipped.Situation not solved with moving pattern",
    79: "Invalid battery combination - Invalid combination of different battery types.",
    80: "Cutting system imbalance    Warning",
    81: "Safety function faulty",
    82: "Wheel motor blocked, rear right",
    83: "Wheel motor blocked, rear left",
    84: "Wheel drive problem, rear right",
    85: "Wheel drive problem, rear left",
    86: "Wheel motor overloaded, rear right",
    87: "Wheel motor overloaded, rear left",
    88: "Angular sensor problem",
    89: "Invalid system configuration",
}

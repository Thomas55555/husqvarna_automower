"""The constants for the Husqvarna Automower integration."""
from homeassistant.const import Platform

# Base component constants
NAME = "husqvarna_automower"
DOMAIN = "husqvarna_automower"
DOMAIN_DATA = f"{DOMAIN}_data"
INTEGRATION_VERSION = "master"
ISSUE_URL = "https://github.com/Thomas55555/husqvarna_automower"
HUSQVARNA_URL = "https://developer.husqvarnagroup.cloud/login"
OAUTH2_AUTHORIZE = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/authorize"
OAUTH2_TOKEN = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/token"
DISABLE_LE = "disable_le"

# Platforms
PLATFORMS = [
    # Platform.DEVICE_TRACKER,
    # Platform.VACUUM,
    Platform.SELECT,
    # Platform.NUMBER,
    # Platform.CALENDAR,
    # Platform.SENSOR,
    Platform.BINARY_SENSOR,
    # Platform.CAMERA,
]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_API_KEY = "api_key"
CONF_PROVIDER = "provider"
CONF_TOKEN_TYPE = "token_type"
CONF_REFRESH_TOKEN = "refresh_token"
ACCESS_TOKEN_RAW = "access_token_raw"
POSITIONS = "positions"

# Camera configuration
ENABLE_CAMERA = "enable_camera"
GPS_TOP_LEFT = "gps_top_left"
GPS_BOTTOM_RIGHT = "gps_bottom_right"
MOWER_IMG_PATH = "mower_img_path"
MAP_IMG_PATH = "map_img_path"


# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {INTEGRATION_VERSION}
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
    90: "No power in charging station",
    91: "Switch cord problem",
    92: "Work area not valid",
    93: "No accurate position from satellites",
    94: "Reference station communication problem",
    95: "Folding sensor activated",
    96: "Right brush motor overloaded",
    97: "Left brush motor overloaded",
    98: "Ultrasonic Sensor 1 defect",
    99: "Ultrasonic Sensor 2 defect",
    100: "Ultrasonic Sensor 3 defect",
    101: "Ultrasonic Sensor 4 defect",
    102: "Cutting drive motor 1 defect",
    103: "Cutting drive motor 2 defect",
    104: "Cutting drive motor 3 defect",
    105: "Lift Sensor defect",
    106: "Collision sensor defect",
    107: "Docking sensor defect",
    108: "Folding cutting deck sensor defect",
    109: "Loop sensor defect",
    110: "Collision sensor error",
    111: "No confirmed position",
    112: "Cutting system major imbalance",
    113: "Complex working area",
    114: "Too high discharge current",
    115: "Too high internal current",
    116: "High charging power loss",
    117: "High internal power loss",
    118: "Charging system problem",
    119: "Zone generator problem",
    120: "Internal voltage error",
    121: "High internal temperature",
    122: "CAN error",
    123: "Destination not reachable",
    701: "Connectivity problem",
    702: "Connectivity settings restored",
    703: "Connectivity problem",
    704: "Connectivity problem",
    705: "Connectivity problem",
    706: "Poor signal quality",
    707: "SIM card requires PIN",
    708: "SIM card locked",
    709: "SIM card not found",
    710: "SIM card locked",
    711: "SIM card locked",
    712: "SIM card locked",
    713: "Geofence problem",
    714: "Geofence problem",
    715: "Connectivity problem",
    716: "Connectivity problem",
    717: "SMS could not be sent",
    724: "Communication circuit board SW must be updated",
}

# Headlight modes
HEADLIGHTMODES = ["ALWAYS_ON", "ALWAYS_OFF", "EVENING_ONLY", "EVENING_AND_NIGHT"]

# Weekdays
WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


WEEKDAYS_TO_RFC5545 = {
    "monday": "MO",
    "tuesday": "TU",
    "wednesday": "WE",
    "thursday": "TH",
    "friday": "FR",
    "saturday": "SA",
    "sunday": "SU",
}


# Models that support electronic cutting height
ELECTRONIC_CUTTING_HEIGHT_SUPPORT = [
    "320",
    "330",
    "405",
    "415",
    "420",
    "430",
    "435",
    "440",
    "450",
    "520",
    "535",
    "544",
    "546",
    "550",
    "550 EPOS",
]

# Models that support electronic cutting height, but are not changeable with this APII
NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT = ["405", "415", "435", "544", "546", "550 EPOS"]

# Models that are able to change the cutting height with this API
CHANGING_CUTTING_HEIGHT_SUPPORT = list(
    set(ELECTRONIC_CUTTING_HEIGHT_SUPPORT) - set(NO_SUPPORT_FOR_CHANGING_CUTTING_HEIGHT)
)

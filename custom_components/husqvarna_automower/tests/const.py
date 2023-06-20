"""Helpers for testing Husqvarana Automower."""

MWR_ONE_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MWR_ONE_IDX = 0
MWR_TWO_ID = "1c7aec7b-06ff-462e-b307-7c6ae4469047"
MWR_TWO_IDX = 1


MWR_ONE_CONFIG = {
    "enable_camera": True,
    "gps_top_left": [35.5411008, -82.5527418],
    "gps_bottom_right": [35.539442, -82.5504646],
    "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
    "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
    "map_path_color": [255, 0, 0],
    "map_img_rotation": -16.10,
    "home_location": [35.54028774, -82.5526962],
    "additional_mowers": [MWR_TWO_ID],
}

MWR_TWO_CONFIG = {
    "enable_camera": True,
    "gps_top_left": [35.5411008, -82.5527418],
    "gps_bottom_right": [35.539442, -82.5504646],
    "mower_img_path": "custom_components/husqvarna_automower/resources/mower.png",
    "map_img_path": "custom_components/husqvarna_automower/tests/resources/biltmore-min.png",
    "map_path_color": [0, 0, 255],
    "map_img_rotation": -16.10,
    "home_location": [35.5409924, -82.5525482],
    "additional_mowers": [],
}

# Single Mower Options
AUTOMER_SM_CONFIG = {
    "configured_zones": '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521], [35.5403893, -82.552613], [35.5399462, -82.5506738], [35.5403827, -82.5505236], [35.5408367, -82.5524521]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [255, 0, 0], "name": "Front Garden", "display": true}, "west_italian_garden": {"zone_coordinates": [[35.5402452, -82.552951], [35.540075, -82.5530073], [35.5399943, -82.5526425], [35.5401536, -82.5525835], [35.5402452, -82.552951]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 255, 0], "name": "West Italian Garden", "display": true}, "east_italian_garden": {"zone_coordinates": [[35.5398415, -82.5512532], [35.5396822, -82.5513122], [35.5395927, -82.550942], [35.5397498, -82.5508803], [35.5398415, -82.5512532]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 0, 255], "name": "East Italian Garden", "display": true}, "shrub_garden": {"zone_coordinates": [[35.5397978, -82.5531334], [35.539357, -82.553289], [35.5393198, -82.553128], [35.5394028, -82.5530529], [35.5394443, -82.5529751], [35.5394639, -82.5528866], [35.5394901, -82.5528303], [35.539645, -82.5529242], [35.5397629, -82.5529698], [35.5397978, -82.5531334]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [100, 100, 0], "name": "Shrub Garden", "display": true}}',
    MWR_ONE_ID: MWR_ONE_CONFIG,
}

# Dual Mower Options
AUTOMER_DM_CONFIG = {
    "configured_zones": '{"front_garden": {"zone_coordinates": [[35.5408367, -82.5524521], [35.5403893, -82.552613], [35.5399462, -82.5506738], [35.5403827, -82.5505236], [35.5408367, -82.5524521]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0", "1c7aec7b-06ff-462e-b307-7c6ae4469047"], "color": [255, 0, 0], "name": "Front Garden", "display": true}, "west_italian_garden": {"zone_coordinates": [[35.5402452, -82.552951], [35.540075, -82.5530073], [35.5399943, -82.5526425], [35.5401536, -82.5525835], [35.5402452, -82.552951]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 255, 0], "name": "West Italian Garden", "display": true}, "east_italian_garden": {"zone_coordinates": [[35.5398415, -82.5512532], [35.5396822, -82.5513122], [35.5395927, -82.550942], [35.5397498, -82.5508803], [35.5398415, -82.5512532]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [0, 0, 255], "name": "East Italian Garden", "display": true}, "shrub_garden": {"zone_coordinates": [[35.5397978, -82.5531334], [35.539357, -82.553289], [35.5393198, -82.553128], [35.5394028, -82.5530529], [35.5394443, -82.5529751], [35.5394639, -82.5528866], [35.5394901, -82.5528303], [35.539645, -82.5529242], [35.5397629, -82.5529698], [35.5397978, -82.5531334]], "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"], "color": [100, 100, 0], "name": "Shrub Garden", "display": true}}',
    MWR_ONE_ID: MWR_ONE_CONFIG,
    MWR_TWO_ID: MWR_TWO_CONFIG,
}

MOWER_ONE_SESSION_DATA = {
    "attributes": {
        "system": {
            "name": "Test Mower 1",
            "model": "450XH-TEST",
        },
        "metadata": {"connected": True, "statusTimestamp": 1685899526195},
        "calendar": {
            "tasks": [
                {
                    "start": 1140,
                    "duration": 300,
                    "monday": True,
                    "tuesday": False,
                    "wednesday": True,
                    "thursday": False,
                    "friday": True,
                    "saturday": False,
                    "sunday": False,
                },
                {
                    "start": 0,
                    "duration": 480,
                    "monday": False,
                    "tuesday": True,
                    "wednesday": False,
                    "thursday": True,
                    "friday": False,
                    "saturday": True,
                    "sunday": False,
                },
            ]
        },
        "planner": {
            "nextStartTimestamp": 1685991600000,
            "override": {"action": None},
            "restrictedReason": "WEEK_SCHEDULE",
        },
        "positions": [
            {"latitude": 35.5402913, "longitude": -82.5527055},
            {"latitude": 35.5407693, "longitude": -82.5521503},
            {"latitude": 35.5403241, "longitude": -82.5522924},
            {"latitude": 35.5406973, "longitude": -82.5518579},
            {"latitude": 35.5404659, "longitude": -82.5516567},
            {"latitude": 35.5406318, "longitude": -82.5515709},
            {"latitude": 35.5402477, "longitude": -82.5519437},
            {"latitude": 35.5403503, "longitude": -82.5516889},
            {"latitude": 35.5401429, "longitude": -82.551536},
            {"latitude": 35.5405489, "longitude": -82.5512195},
            {"latitude": 35.5404005, "longitude": -82.5512115},
            {"latitude": 35.5405969, "longitude": -82.551418},
            {"latitude": 35.5403437, "longitude": -82.5523917},
            {"latitude": 35.5403481, "longitude": -82.5520054},
        ],
        "battery": {"batteryPercent": 100},
        "mower": {
            "mode": "MAIN_AREA",
            "activity": "PARKED_IN_CS",
            "state": "RESTRICTED",
            "errorCode": 0,
            "errorCodeTimestamp": 0,
        },
        "statistics": {
            "numberOfChargingCycles": 231,
            "numberOfCollisions": 48728,
            "totalChargingTime": 813600,
            "totalCuttingTime": 3945600,
            "totalRunningTime": 4078800,
            "totalSearchingTime": 133200,
        },
        "cuttingHeight": 4,
        "headlight": {"mode": "EVENING_ONLY"},
    },
    "id": MWR_ONE_ID,
}

MOWER_TWO_SESSION_DATA = {
    "attributes": {
        "system": {
            "name": "Test Mower 2",
            "model": "450XH-TEST",
        },
        "metadata": {"connected": True, "statusTimestamp": 1685899526195},
        "calendar": {
            "tasks": [
                {
                    "start": 1140,
                    "duration": 300,
                    "monday": True,
                    "tuesday": False,
                    "wednesday": True,
                    "thursday": False,
                    "friday": True,
                    "saturday": False,
                    "sunday": False,
                },
                {
                    "start": 0,
                    "duration": 480,
                    "monday": False,
                    "tuesday": True,
                    "wednesday": False,
                    "thursday": True,
                    "friday": False,
                    "saturday": True,
                    "sunday": False,
                },
            ]
        },
        "planner": {
            "nextStartTimestamp": 1685991600000,
            "override": {"action": None},
            "restrictedReason": "WEEK_SCHEDULE",
        },
        "positions": [
            {"latitude": 35.5409916, "longitude": -82.5525433},
            {"latitude": 35.5408149, "longitude": -82.5523743},
            {"latitude": 35.5402976, "longitude": -82.5521544},
            {"latitude": 35.5406534, "longitude": -82.5516823},
            {"latitude": 35.5404788, "longitude": -82.5516287},
            {"latitude": 35.5406053, "longitude": -82.5514785},
            {"latitude": 35.5402692, "longitude": -82.5520417},
            {"latitude": 35.5403369, "longitude": -82.5516716},
            {"latitude": 35.5401448, "longitude": -82.5515697},
            {"latitude": 35.5402605, "longitude": -82.5512907},
            {"latitude": 35.5405551, "longitude": -82.5512532},
            {"latitude": 35.5404504, "longitude": -82.5514329},
        ],
        "battery": {"batteryPercent": 100},
        "mower": {
            "mode": "MAIN_AREA",
            "activity": "PARKED_IN_CS",
            "state": "RESTRICTED",
            "errorCode": 0,
            "errorCodeTimestamp": 0,
        },
        "statistics": {
            "numberOfChargingCycles": 231,
            "numberOfCollisions": 48728,
            "totalChargingTime": 813600,
            "totalCuttingTime": 3945600,
            "totalRunningTime": 4078800,
            "totalSearchingTime": 133200,
        },
        "cuttingHeight": 4,
        "headlight": {"mode": "EVENING_ONLY"},
    },
    "id": MWR_TWO_ID,
}

AUTOMOWER_ERROR_SESSION_DATA = {
    "errors": [
        {
            "id": MWR_ONE_ID,
            "status": "403",
            "code": "invalid.credentials",
            "title": "Invalid credentials",
            "detail": "The supplied credentials are invalid.",
        }
    ]
}


AUTOMOWER_SM_SESSION_DATA = {
    "data": [MOWER_ONE_SESSION_DATA],
}

AUTOMOWER_DM_SESSION_DATA = {
    "data": [MOWER_ONE_SESSION_DATA, MOWER_TWO_SESSION_DATA],
}

AUTOMOWER_CONFIG_DATA = {
    "auth_implementation": "husqvarna_automower",
    "token": {
        "access_token": "f8f1983d-d88a-4ef1-91ab-af54fefaa9d0",
        "scope": "iam:read amc:api",
        "expires_in": 86399,
        "refresh_token": "ab152f21-811b-4417-a75f-4c8fe518644c",
        "provider": "husqvarna",
        "user_id": "d582fe49-80a5-417b-bf97-29ce20818712",
        "token_type": "Bearer",
        "expires_at": 1685908387.3688,
        "status": 200,
    },
}

AUTOMOWER_CONFIG_DATA_BAD_SCOPE = {
    "auth_implementation": "husqvarna_automower",
    "token": {
        "access_token": "f8f1983d-d88a-4ef1-91ab-af54fefaa9d0",
        "scope": "iam:read",
        "expires_in": 86399,
        "refresh_token": "ab152f21-811b-4417-a75f-4c8fe518644c",
        "provider": "husqvarna",
        "user_id": "d582fe49-80a5-417b-bf97-29ce20818712",
        "token_type": "Bearer",
        "expires_at": 1685908387.3688,
        "status": 200,
    },
}

DEFAULT_ZONES = {
    "front_garden": {
        "zone_coordinates": [
            [35.5408367, -82.5524521],
            [35.5403893, -82.552613],
            [35.5399462, -82.5506738],
            [35.5403827, -82.5505236],
            [35.5408367, -82.5524521],
        ],
        "sel_mowers": [
            "c7233734-b219-4287-a173-08e3643f89f0",
            "1c7aec7b-06ff-462e-b307-7c6ae4469047",
        ],
        "color": [255, 0, 0],
        "name": "Front Garden",
        "display": True,
    },
    "west_italian_garden": {
        "zone_coordinates": [
            [35.5402452, -82.552951],
            [35.540075, -82.5530073],
            [35.5399943, -82.5526425],
            [35.5401536, -82.5525835],
            [35.5402452, -82.552951],
        ],
        "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"],
        "color": [0, 255, 0],
        "name": "West Italian Garden",
        "display": True,
    },
    "east_italian_garden": {
        "zone_coordinates": [
            [35.5398415, -82.5512532],
            [35.5396822, -82.5513122],
            [35.5395927, -82.550942],
            [35.5397498, -82.5508803],
            [35.5398415, -82.5512532],
        ],
        "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"],
        "color": [0, 0, 255],
        "name": "East Italian Garden",
        "display": True,
    },
    "shrub_garden": {
        "zone_coordinates": [
            [35.5397978, -82.5531334],
            [35.539357, -82.553289],
            [35.5393198, -82.553128],
            [35.5394028, -82.5530529],
            [35.5394443, -82.5529751],
            [35.5394639, -82.5528866],
            [35.5394901, -82.5528303],
            [35.539645, -82.5529242],
            [35.5397629, -82.5529698],
            [35.5397978, -82.5531334],
        ],
        "sel_mowers": ["c7233734-b219-4287-a173-08e3643f89f0"],
        "color": [100, 100, 0],
        "name": "Shrub Garden",
        "display": True,
    },
}
FRONT_GARDEN_PNT = [35.540520981627665, -82.5519580864446]
NO_ZONE_PNT = [35.539645783988995, -82.55221826069203]

# Home Assistant integration for Husqvarna Automower

![Maintenance](https://img.shields.io/maintenance/yes/2020.svg)


Custom component to support Automower.


- [About](#about)
- [Installation](#installation)
  - [Installation through HACS](#installation-through-hacs)
  - [Manual installation](#manual-installation)
- [Configuration](#configuration)
  - [Home Assistant](#home-assistant)
  - [Gardena Application Key / Client ID](#gardena-application-key--client-id)
- [Supported devices](#supported-devices)
- [Services](#services)
  - [Smart Irrigation Control services](#smart-irrigation-control-services)
  - [Smart Mower services](#smart-mower-services)
  - [Smart Power Socket services](#smart-power-socket-services)
  - [Smart Sensor services](#smart-sensor-services)
  - [Smart Water Control services](#smart-water-control-services)
- [Development](#development)
  - [Debugging](#debugging)
  - [TODO](#todo)

## About

The idea for this component ist coming from the https://github.com/walthowd/ha-automower integration. As this integration doesn't use the offical API, I decided to create a
integration, which is based on the offical API: https://developer.husqvarnagroup.cloud/
There are some disatvanteges between, the offical API and the unoffical API:

- Offical API doesn't support GSP data
- Offical API is limited is limited to 10,000 accesses per 30 days
- API-Key is needed

But the adavantage is, that Husqvarna won't close the offical API suddenly


## Installation

Requires Home Assistant 0.113 or newer.

### Installation through HACS

Not provided yet.

### Manual installation

Copy the sub-path `/custom_components/husqvarna_automower` of this repo into the path `/config/custom_components/husqvarna_automower` of your HA installation. 

## Configuration


### Home Assistant

Setup under Integrations in Home Assistant, search for "husqvarna_automower". You need to enter e-mail, password and your API-Key. 

### Gardena Application Key / Client ID

In order to use this integration you must get a client ID /
Application Key from Gardena/Husqvarna.

1. Go to https://developer.husqvarnagroup.cloud/

2. Create an account if needed, otherwise sign in with your Gardena
   account.

3. After signing in you will be automatically redirected to "Your
   applications". (Otherwise go to: https://developer.husqvarnagroup.cloud/apps)

4. Create an new application, name it for example "My Home Assistant"
   (doesn't matter), leave the other fields empty.

5. Click on "+Connect new API" and connect the Authentication API and
   the GARDENA smart system API.

6. Copy your Application Key, this is what you need when you add the integration in Home Assistant.


## Supported devices

The following devices are supported :

* Gardena Smart Irrigation Control (as switch)
* Gardena Smart Mower (as vacuum)
* Gardena Smart Sensor (as sensor)
* Gardena Smart Water Control (as switch)
* Gardena Smart Power Socket (as switch)

## Services

### Smart Irrigation Control services

> [TODO: document services]

### Smart Mower services

`vacuum.start`  
Start the mower using the Gardena API command START_SECONDS_TO_OVERRIDE.  
The mower switches to manual operation for a defined duration of time.   The duration is taken from the integration option "*Mower Duration (minutes)*" (see *Configuration -> Integrations* in HA).

`vacuum.stop`  
Stop the mower using the Gardena API command PARK_UNTIL_FURTHER_NOTICE.  
The mower cancels the current operation, returns to charging station and ignores schedule.

`vacuum.return_to_base`  
Stop the mower using Gardena API command PARK_UNTIL_NEXT_TASK.  
The mower cancels the current operation and returns to charging station. It will reactivate with the next schedule.

### Smart Power Socket services

> [TODO: document services]

### Smart Sensor services

> [TODO: document services]

### Smart Water Control services

> [TODO: document services]

## Development

### Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```
logger:
  default: info
  logs:
    custom_components.gardena_smart_system: debug
    custom_components.gardena_smart_system.mower : debug
    custom_components.gardena_smart_system.sensor : debug
    custom_components.gardena_smart_system.switch : debug
    custom_components.gardena_smart_system.config_flow : debug

    gardena: debug
    gardena.smart_system: debug
    websocket: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.

### TODO

* Do we need support for more than one location? Should we make it
  possible to configure it?

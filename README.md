# Home Assistant integration for Husqvarna Automower

![Maintenance](https://img.shields.io/maintenance/yes/2022.svg)
[![buy me a coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoffee.com/Thomas55555)
[![downloads](https://img.shields.io/github/downloads/Thomas55555/husqvarna_automower/total.svg)](https://img.shields.io/github/downloads/Thomas55555/husqvarna_automower/total.svg)

Custom component to support Automower.


- [About](#about)
- [Supported devices](#supported-devices)
- [Installation](#installation)
  - [Installation through HACS](#installation-through-hacs)
  - [Manual installation](#manual-installation)
- [Configuration](#configuration)
  - [Husqvarna API-Key](#husqvarna-api-key)
  - [Home Assistant](#home-assistant)
- [Usage](#usage)

## About

This integration is based on the offical
[API](https://developer.husqvarnagroup.cloud/). The integration is using the
Husqvarna websocket API for pushed updates, so no polling is performed. You
need a API key to use this integration, refer to [this
guide](https://developer.husqvarnagroup.cloud/docs/getting-started) on how to
get one.

![Screenshot of the integration](https://github.com/Thomas55555/husqvarna_automower/blob/master/screenshot_husqvarna_automower.PNG)

## Supported devices

Only mowers with built-in Automower® Connect or with the Automower® Connect Module are supported. e.g.

- AUTOMOWER® 315X
- AUTOMOWER® 405X
- AUTOMOWER® 415X
- AUTOMOWER® 430X
- AUTOMOWER® 435X AWD
- AUTOMOWER® 450X


## Installation

Requires Home Assistant 2022.5.0 or newer.

### Installation through HACS

If you have not yet installed HACS, go get it at https://hacs.xyz/ and walk through the installation and configuration.

Then find the Husqvarna Automower integration in HACS and install it.

Restart Home Assistant!

Install the new integration through Configuration -> Integrations in HA (see below).

### Manual installation

Download the `husqvarna_automower.zip` file from the [release section](https://github.com/Thomas55555/husqvarna_automower/releases). Extract it and copy the content into the path `/config/custom_components/husqvarna_automower` of your HA installation. Do **not** download directly from the `main` branch.

## Configuration


### Husqvarna API-Key

In order to use this integration you must get a API-Key from Husqvarna.

1.  Go to <https://developer.husqvarnagroup.cloud/>

2.  Create an account if needed, otherwise sign in with your Husqvarna account.

3.  After signing in you will be automatically redirected to "Your applications". (Otherwise go to: <https://developer.husqvarnagroup.cloud/apps>)

4.  Create an new application, name it for example "My Home Assistant" (doesn't matter), leave the other fields empty.

5.  Click on "**+ Connect new API**" and connect the **Authentication API** and the **Husqvarna Automower API**.

6.  Copy your Application Key, this is what you need when you add the integration in Home Assistant.

### Home Assistant

Setup under Integrations in Home Assistant, search for "husqvarna_automower" and click on it, or use the My button:
[![my_button](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=husqvarna_automower)

If the integration is not shown, try to refresh your browser (F5) or (Shift+F5). Maybe you need to reopen your browser.

You have two options to login.
1.  Login with API-Key and Application Secret. You can find them on the Husqvarna site
    [![Screenshot](https://user-images.githubusercontent.com/59625598/165815612-e52ad1b1-1e4f-44eb-ac18-e10a5f2db293.png)
    On the Husqvrana site edit your Application and add your Home Assistant instance as redirect URL. Use My HomeAssistant https://my.home-assistant.io/redirect/oauth
    Additionally add your credentials to the `configuration.yaml`:
    ```
    husqvarna_automower:
      client_id: !secret husqvarna_apikey
      client_secret: !secret husqvarna_client_secret
    ```
    You will be re-directed to the Husqvarna site and have to login there with username and password to authorize Home Assistant.
2.  Login with API-key, username and password.

### Configuring the camera sensor

The optional camera entity is disabled by default.  The camera entity will plot the current coordinates and location history of the mower on a user provided image. To configure the entity you need to upload your desired map image and determine the coordinates of the top left corner and the bottom right corner of your selected image.

The camera entity is configured via the configure option on the integration. To enter the coordinates, ensure that they are in Signed Degree format and seperated by a comma for example ```40.689209, -74.044661```

You can then provide the path to the image you would like to use for the map and mower, this has been tested with the PNG format, other formats may work.


### Configuring the zone sensor

The optional zone sensor allows zones to be designated by coorinates, this sensor will then return the name of the zone the mower is currently located.

To create a Zone, select new then enter a name for the zone and the coordinates of the zone.  Coordinates are entered in Signed Degree format with latitude and lognitude seperated by a comma and each coordinate seperated by a semi colon. You must enter at least three coordinates to define a zone. For example: ```40.689209, -74.044661; 40.689210, -74.044652; 40.689211, -74.044655``` You must select save and then submit, exiting the flow in another manner will cause any entered zones to be lost.

If a Home Zone is set, the sensor will return Home when the mower is charging or at the docking station.

## Usage

`vacuum.start`
The mower continues to mow, within the specifed schedule

`vacuum.pause`
Pauses the mower until a new command

`vacuum.stop`
The mower returns to the base and parks there until the next schedule starts

`vacuum.return_to_base`
The mower returns to the base and parks there until it gets a new start command

`husqvarna_automower.park_and_start`
With the this command you can override the curent schedule for a specific time. For more details see the [Services](https://github.com/Thomas55555/husqvarna_automower#services) chapter

### Services

| Name          | Type          | Possible values   | Description
| ------------- | ------------- | -------------     | -------------
| command       | string        | `Start` \| `Park` | Start or park the mower
| duration      | int           | `1...60480`       | Duration for this command in minutes
| target        | string        |                 | The `entity_id` of your mower

Example for starting without the schedule for 120 minutes:
```
service: husqvarna_automower.park_and_start
data:
  command: Start
  duration: 120
target:
  entity_id: vacuum.automower_r_315x_haffi
```

Example for parking indepentend from the schedule for 5 minutes:
```
service: husqvarna_automower.park_and_start
data:
  command: Park
  duration: 5
target:
  entity_id: vacuum.automower_r_315x_haffi
```

## Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```
logger:
  default: info
  logs:
    custom_components.husqvarna_automower: debug
    aioautomower: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.

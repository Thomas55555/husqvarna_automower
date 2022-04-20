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

Requires Home Assistant 2021.11.0 or newer.

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

You need to enter e-mail, password and your API-Key.
If the integration is not shown, try to refresh your browser (F5) or (Shift+F5). Maybe you need to reopen your browser.

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
    husqvarna_automower: debug
    aioautomower: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.

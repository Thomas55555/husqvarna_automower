# Home Assistant integration for Husqvarna Automower

![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)
[![buy me a coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoffee.com/Thomas55555)
[![downloads](https://img.shields.io/github/downloads/Thomas55555/husqvarna_automower/total.svg)](https://img.shields.io/github/downloads/Thomas55555/husqvarna_automower/total.svg)

Custom component to support Automower.


- [About](#about)
- [Installation](#installation)
  - [Installation through HACS](#installation-through-hacs)
  - [Manual installation](#manual-installation)
- [Configuration](#configuration)
  - [Husqvarna API-Key](#husqvarna-api-key)
  - [Home Assistant](#home-assistant)
- [Usage](#usage)
- [TODO](#todo)

## About

The idea for this component ist coming from the <https://github.com/walthowd/ha-automower> integration. As this integration doesn't use the offical API, I decided to create a
integration, which is based on the offical API: <https://developer.husqvarnagroup.cloud/>. There are some disatvanteges between, the offical API and the unoffical API:

- Offical API doesn't support GPS position
- Offical API is limited to 10,000 accesses per 30 days. So state of the mower is only update every 5 minutes
- API-Key is needed

But the adavantage is, that Husqvarna won't close the offical API suddenly.

![Screenshot of the integration](https://github.com/Thomas55555/husqvarna_automower/blob/master/screenshot_husqvarna_automower.PNG)


## Installation

Requires Home Assistant 0.113 or newer.

### Installation through HACS

If you have not yet installed HACS, go get it at https://hacs.xyz/ and walk through the installation and configuration.

Then find the Husqvarna Automower integration in HACS and install it.

Restart Home Assistant!

Install the new integration through Configuration -> Integrations in HA (see below).

### Manual installation

Copy the sub-path `/custom_components/husqvarna_automower` of this repo into the path `/config/custom_components/husqvarna_automower` of your HA installation.

## Configuration


### Husqvarna API-Key

In order to use this integration you must get a API-Key from Husqvarna.

1.  Go to <https://developer.husqvarnagroup.cloud/>

2.  Create an account if needed, otherwise sign in with your Husqvarna account.

3.  After signing in you will be automatically redirected to "Your applications". (Otherwise go to: <https://developer.husqvarnagroup.cloud/apps>)

4.  Create an new application, name it for example "My Home Assistant" (doesn't matter), leave the other fields empty.

5.  Click on "+Connect new API" and connect the Authentication API and the Husqvarna Automower API.

6.  Copy your Application Key, this is what you need when you add the integration in Home Assistant.

### Home Assistant

Setup under Integrations in Home Assistant, search for "husqvarna_automower". You need to enter e-mail, password and your API-Key.
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


## Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```
logger:
  default: info
  logs:
    custom_components.husqvarna_automower: debug
    custom_components.husqvarna_automower.vacuum: debug
    custom_components.husqvarna_automower.config_flow: debug
    aioautomower: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.
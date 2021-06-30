# Domoticz plugin for the Ween thermostat
This is a first draft of a Domoticz plugin for the Ween thermostat based on the undocumented WiFi local API.
Minimal firmware version for the API to be available on the device is 1.6.10.

## Installation
First, go to the plugin directory of your Domoticz installation and simply clone this repository.

```
$ git clone git@github.com:joggee-fr/domoticz-ween-thermostat.git
```

Now, use the Domoticz Web interface to add the Ween thermostat plugin in the hardware tab.

## Parameters
* __IP address__ of the Ween Thermostat on the LAN network. As the IPv4 address is retrieved using DHCP, you may have to configure your router to ensure the address to be fixed.
* __Token__ is the key used for the Ween WiFi access point used for configuration. You may retrieve it temporarily switching to WiFi configuration mode. In this mode, the token is displayed on the thermostat screen. Don't forget to go back to normal mode for your thermostat to be part of the LAN network.
* __Debug__ boolean simply adds more logs.

## Usage
Once added, two devices are created. The first one retrieves periodically the measured temperature and humidity values. The second one is able to edit the current setpoint.

## Limitations
As the proposed API is still incomplete, current displayed setpoint may not be aligned with real value.

The working modes (smart, basic, frost protection) are also missing.

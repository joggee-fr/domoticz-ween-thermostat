# Ween thermostat plugin for Domoticz
# Author: Joggee Software
#
"""
<plugin key="WeenThermostat" name="Ween Thermostat" author="joggee-fr" version="0.0.1" externallink="https://gitlab.com/joggee-fr/ween-thermostat-domoticz">
    <description>
        <h2>Ween Thermostat</h2><br/>
        This plugin add devices for the Ween Thermostat based on the WiFi local API.
    </description>
    <params>
        <param field="Address" label="IP address" width="600px" required="true"/>
        <param field="Mode2" label="Token" width="600px" required="true"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="false" value="0" default="true"/>
                <option label="true" value="1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz 
import json
import time


class BasePlugin:
    _ipAddress               = ""
    _token                   = ""

    _conditionsConnection    = None
    _lastConditionsTimestamp = None

    _setpointConnection      = None
    _pendingSetpoint         = 0

    # Constants
    _conditionsPeriod = 120 # seconds
    _conditionsUnit   = 1
    _setpointUnit     = 2


    def __init__(self):
        return


    def _updateDevice(self, Unit, nValue, sValue):
        if (Unit in Devices):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Debug("Updated device " + str(nValue) + " with value: " + str(sValue))


    def _disconnect(self, Connection):
        if (Connection != None and (Connection.Connected() or Connection.Connecting())):
            self.__connection.Disconnect()


    def _setSetpoint(self):
        Domoticz.Debug("Init setpoint connection")
        self._setpointConnection = Domoticz.Connection(Name="Ween", Transport="TCP/IP", Protocol="HTTP", Address=self._ipAddress, Port="80")
        self._setpointConnection.Connect()


    def _getBaseConnectionData(self, method, endpoint):
        return {
                    "Verb" : method,
                    "URL"  : "/" + endpoint + ".cgi?token=" + self._token,
                    "Headers" : {
                        "Host"      : self._ipAddress,
                        "User-Agent": 'Domoticz/1.0'
                    }
                }
    

    def _getHumidityStatus(self, humidity):
        if humidity < 30:
            return 2

        if humidity > 70:
            return 3
        
        return 1


    def onStart(self):
        # Debug mode
        Domoticz.Debugging(int(Parameters["Mode6"]))
        Domoticz.Debug("onStart called")

        self._ipAddress = Parameters["Address"]
        self._token     = Parameters["Mode2"]

        # Create devices
        if (1 not in Devices):
            Domoticz.Device(Name="Conditions", Unit=self._conditionsUnit, TypeName="Temp+Hum").Create()
            Domoticz.Debug("Creating Conditions device")

        if (2 not in Devices):
            Domoticz.Device(Name="Thermostat", Unit=self._setpointUnit, Type=242, Subtype=1).Create()
            Domoticz.Debug("Creating Thermostat device")


    def onStop(self):
        Domoticz.Debug("onStop called")
        self._disconnect(self._setpointConnection)
        self._disconnect(self._conditionsConnection)


    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

        if (Status == 0):
            if (Connection == self._conditionsConnection):
                Domoticz.Debug("Conditions connection succeed")
                data = self._getBaseConnectionData("GET", "conditions") 
                Connection.Send(data)

            elif (Connection == self._setpointConnection):
                Domoticz.Debug("Conditions connection succeed")
                data = self._getBaseConnectionData("GET", "setpoint")
                data["URL"] = data["URL"] + "&value=" + str(self._pendingSetpoint)
                Connection.Send(data)

        else:
            Domoticz.Error("Failed to connect (" + str(Status) + ") to " + self._ipAddress + " with error: " + Description)


    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

        receivedData = Data["Data"].decode("utf-8", "ignore")
        status       = int(Data["Status"])

        # Always reset setpoint
        if (Connection == self._setpointConnection):
            self._pendingSetpoint = 0

        if (status == 200):
            if (Connection == self._conditionsConnection):
                conditions = json.loads(receivedData)

                if ("temperature" in conditions) and ("humidity" in conditions):
                    temperature = round(conditions["temperature"], 1)
                    humidity    = int(conditions["humidity"])

                    value = str(temperature) + ';' + str(humidity) + ';' + str(self._getHumidityStatus(humidity))
                    self._updateDevice(Unit=self._conditionsUnit, nValue=0, sValue=value)
                    self._lastConditionsTimestamp = time.monotonic()
                else:
                    Domoticz.Error("Invalid received format for conditions")

            elif (Connection == self._setpointConnection):
                success = json.loads(receivedData)

                if ("success" in success):
                    if (success["success"] != True):
                        Domoticz.Error("Error setting setpoint")

                else:
                    Domoticz.Error("Invalid received format for setpoint")

        else:
            Domoticz.Error("Connection returned error status: " + str(status))


    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        if (Unit == self._setpointUnit) and (Command == "Set Level"):
            self._disconnect(self._setpointConnection)
            self._pendingSetpoint = int(Level)

            if (self._setpointConnection == None):
                self._setSetpoint()


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)


    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

        if (Connection == self._conditionsConnection):
            self._conditionsConnection = None

        elif (Connection == self._setpointConnection):
            self._setpointConnection = None

            if (self._pendingSetpoint > 0):
                self._setSetpoint()


    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")

        if (self._conditionsConnection == None or self._conditionsConnection.Connected() != True):
            now     = time.monotonic()
            elapsed = now - self._lastConditionsTimestamp if self._lastConditionsTimestamp != None else None

            # Get current conditions every two minutes should be enough
            if (self._lastConditionsTimestamp == None or elapsed >= (self._conditionsPeriod - 1)):
                Domoticz.Debug("Init conditions connection")
                self._conditionsConnection = Domoticz.Connection(Name="Ween", Transport="TCP/IP", Protocol="HTTP", Address=self._ipAddress, Port="80")
                self._conditionsConnection.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

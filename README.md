As part of the Roadmap project between NCDMM, AMT, the MTConnect Institute, and MAYA Design, this Agent-Adapter for a Makerbot was created to examine the process of one possible type of MTConnect implementer. As a result of this effort, a prototype Makerbot Agent-Adapter was created.

This prototype was written in Python, specifically Python 2.7, and uses Makerbot's Python implementation of the s3g protocol over USB to interface with a Makerbot. This code was tested with a Makerbot Replicator 2 and exposes the following data items from it:
-Axes: X, Y, Z, A, B
-Toolhead:
  *Temperature
  *Toolhead Ready (Boolean)
  *Extruder Sensor
    +Extruder Ready (Boolean)
-Platform:
  *Temperature
  *Platform Ready (Boolean)
-Motherboard
  *Power Error (Boolean)
  *Wait For Button (Boolean)
  *Heat Shutdown (Boolean)
  *Preheat (Boolean)
  *Build Canceling (Boolean)

Some terse installation instructions are provided in "rough install instructions.txt".

Basic dependencies are:
-A version of Python (Python 2.7 was used).
-A version of PySerial that works with your version of Python.
-The s3g protocol (provided in this repo).

Application configuration:
-Located in the /Makebot Agent-Adapter/config.json.
-Configuration settings are:
  *DeviceConfigurationFile: a reference to the XML file containing the device(s) to be monitored by this Agent-Adapter.
  *ErrorReference: a reference to the file containing the XML error template.
  *HTTPHost: the IP and Port on which the application should serve the device data.

DeviceConfigurationFile:
-The XML file that structures the device(s) to be monitored by this Agent-Adapter. The structure takes the form described by the MTConnect Standard (at least version 1.2).
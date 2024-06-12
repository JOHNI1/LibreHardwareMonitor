# fan-speed-controller
this project uses LibreHardwareMonitor to get the processors temperature(GPU's) and controls (sends in serial numbers) the arduino's pwm that goes to the fan.


create a file with 
in task scheduler set it to run the FanArduinoController.pyw
event of the launching should be "At log in of any user"


https://github.com/snip3rnick/PyHardwareMonitor


PyHardwareMonitor
Python Harware Monitor is a thin package layer for LibreHardwareMonitorLib using pythonnet. Libre Hardware Monitor, a fork of Open Hardware Monitor, is free software that can monitor the temperature sensors, fan speeds, voltages, load and clock speeds of your computer. This package is mostly auto generated using the pythonstubs generator tool for .NET libraries. Scripts for generating, altering and extending package resources are located in the scripts folder.

The purpose of this layer is the ability to provide extensive typing information and additional utilities around the LibreHardwareMonitorLib.

Note: Python must have admin privileges for HardwareMonitor to be able to access all available sensors properly!

Prerequisites
- Python 3.6+
- pythonnet
- .NET 4.7

Installation
- git clone https://github.com/snip3rnick/PyHardwareMonitor   <= just do this in some randon location, go to that directory and when you do pip3 install it builds the file and adds it as library.
- cd PyHardwareMonitor
- pip3 install .

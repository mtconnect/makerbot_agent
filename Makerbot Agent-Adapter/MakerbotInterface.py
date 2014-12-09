"""
author: Kent Vasko
company: MAYA Design
"""

# Import the serial and makerbot modules.
import serial, makerbot_driver, sys
# Import threading for the condition parameter of makerbot.
import threading
# Import the list_ports module to enable picking the port through which the Makerbot is connected.
from serial.tools import list_ports

# @class: MakerbotInterface
class MakerbotInterface:
    # @function: init
    def __init__(self):
        # Instance variables.
        self.available = True
        self.axes = {"x":0.0, "y": 0.0, "z":0.0, "a":0.0, "b":0.0}
        # Makerbot Tool (Head, Extruder, Platform)
        self.tool = MakerbotTool()
        # Makerbot Motherboard
        self.motherboard = MakerbotMotherboard()
    # end init
    
    # @function: pollMakerbot
    def pollMakerbot(self):
        # Structure to hold data.
        makerbotData = {"availability":"UNAVAILABLE",
                        "xPos":"UNAVAILABLE","yPos":"UNAVAILABLE","zPos":"UNAVAILABLE",
                        "aPos":"UNAVAILABLE","bPos":"UNAVAILABLE",
                        "toolheadTemp":"UNAVAILABLE", "toolheadReady":"UNAVAILABLE",
                        "extruderTemp":"UNAVAILABLE", "extruderReady":"UNAVAILABLE",
                        "platformTemp":"UNAVAILABLE", "platformReady":"UNAVAILABLE",
                        "powerError":"UNAVAILABLE", "waitForButton":"UNAVAILABLE",
                        "heatShutdown":"UNAVAILABLE", "preheat":"UNAVAILABLE",
                        "buildCancel":"UNAVAILABLE"
                        }
        
        # Variable to hold the port that will be determined.
        makerbotPort = None
        # Find the port on which the makerbot is connected, if it is.
        for port in list_ports.comports():
            # If it is a Replicator.
            if "Replicator" in port[1]:
                # Set the port.
                makerbotPort = port[0]
            # end if
        # end for
        
        # If the makerbot was found.
        if makerbotPort != None:
            # Get values from the makerbot.
            try:
                # Create the dictionary to hold the data to be collected from the makerbot.
                makerbotData = {}
                # Create the makerbot s3g interface object.
                replicator = makerbot_driver.s3g()
                # Open the port to the makerbot.
                makerbotStream = serial.Serial(makerbotPort, 115200, timeout=1)
                # Create the condition.
                condition = threading.Condition()
                # Set the stream writer to the opened stream.
                replicator.writer = makerbot_driver.Writer.StreamWriter(makerbotStream, condition)
                
                # ***Make the queries***
                
                # Availability
                makerbotData["availability"] = "AVAILABLE"
                
                # Axes
                axes = replicator.get_extended_position()
                makerbotData["xPos"] = axes[0][0]
                makerbotData["yPos"] = axes[0][1]
                makerbotData["zPos"] = axes[0][2]
                makerbotData["aPos"] = axes[0][3]
                makerbotData["bPos"] = axes[0][4]
                
                # Toolhead
                makerbotData["toolheadTemp"] = replicator.get_toolhead_temperature(0)
                toolheadReady = str(replicator.is_tool_ready(0))
                if toolheadReady:
                     makerbotData["toolheadReady"] = "READY"
                else:
                    makerbotData["toolheadReady"] = "STOPPED"
                
                # Extruder
                status = replicator.get_tool_status(0)
                extruderReady = status["ExtruderReady"]
                if extruderReady:
                    makerbotData["extruderReady"] = "READY"
                else:
                    makerbotData["extruderReady"] = "STOPPED"
                
                # Platform
                makerbotData["platformTemp"] = replicator.get_platform_temperature(0)
                platformReady = replicator.is_platform_ready(0)
                if platformReady:
                    makerbotData["platformReady"] = "READY"
                else:
                    makerbotData["platformReady"] = "STOPPED"
                
                # Motherboard
            except:
                print "MakerbotInterface.pollMakerbot, Error getting data from Makerbot: "+str(sys.exc_info())
            # end try-catch
        # end if
        # Otherwise, set things accordingly.
        else:
            self.available = False
        # end else
        
        # Return the reslts.
        return makerbotData
    # end pollMakerbot
    
    # @function: setAvailability
    def setAvailability(self, availability):
        self.available = availability
    # end setAvailability
    
    # @function: isAvailable
    def isAvailable(self):
        return self.available
    # end isAvailable
# end MakerbotInterface

# @class: MakerbotTool
class MakerbotTool:
    # @function: init
    def __init__(self):
        self.toolhead = MakerbotToolPiece()
        self.extruder = MakerbotToolPiece()
        self.platform = MakerbotToolPiece()
    # end init
# end MakerbotTool

# @class: MakerbotToolPiece
class MakerbotToolPiece:
    # @function: init
    def __init__(self):
        self.temperature = 0.0
        self.readyState = "READY" # Can be: READY, ACTIVE, STOPPED
    # end init
    
    # @function: setReadyState
    # @param: toolReady, boolean
    # @param: errorPresent, boolean
    def setReadyState(self, toolReady, errorPresent):
        # If the tool is ready.
        if toolReady == True:
            # Set to ready.
            self.readyState = "READY"
        # end if
        # If the toolhead is not ready.
        else:
            # If an error is present:
            if errorPresent == True:
                # Set to stopped.
                self.readyState = "STOPPED"
            # end if error
            # Otherwise.
            else:
                # Set to active.
                self.readyState = "ACTIVE"
            # end else
        # end else
    # end setReadyState
    
    # @function: getReadyState
    def getReadyState(self):
        return self.readyState
    # end getReadyState
    
    # @function: setTemperature
    def setTemperature(self, newTemp):
        self.temperature = newTemp
    # end setTemperature
    
    # @function: getTemperature
    def getTemperature(self):
        return self.temperature
    # end getTemperature
# end MakerbotToolhead

# @class: MakerbotMotherboard
class MakerbotMotherboard:
    # @function: init
    def __init__(self):
        self.powerError = False
        self.waitForButton = False
        self.heatShutdown = False
        self.preheat = False
        self.buildCancel = False
    # end init
# end MakerbotMotherboard
"""
author: Kent Vasko
company: MAYA Design
"""

import BaseHTTPServer
import time
from datetime import datetime
import socket
import json
import sys
import threading
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
# MTC
from MTCHeader import MTCHeader
from MTCDevice import MTCDevice
from MTCError import MTCError
from MTCAdapter import *
# For keeping snapshots of the machine states (sequences).
import copy
import traceback

# @class: MTCAgent
class MTCAgent:
    # @function: init
    def __init__(self, config, errorTemplate, hostName, sequenceBufferSize=10, sampleRate=1):
        # Instance variables
        self.devices = {} # Dictionary of devices {"deviceName":deviceObject"}
        self.sequences = {}
        self.sequenceBufferSize = sequenceBufferSize
        self.sampleRate = sampleRate
        # The sequences.
        self.lastSequenceNumber = 0
        self.firstSequenceNumber = 1
        self.nextSequenceNumber = 1
        # Device representation.
        self.deviceTree = None # ElementTree object
        # Error xml.
        self.errorTree = MTCError(ElementTree.parse(errorTemplate))
        # Header.
        self.header = None
        
        # Load the machine and server from the configuration data.
        self.loadDeviceFromConfig(config, hostName)
        
        # Start polling the machine.
        self.isRunning = True
        threading.Thread(target=self.pollDevices).start()
    # end init
    
    # @function: pollDevices
    def pollDevices(self):
        while self.isRunning:
            # For each device.
            for deviceName in self.devices:
                # Poll the makerbot.
                adapterData = self.devices[deviceName].adapter.pollDevice()

                # Pass the data along.
                self.propagateData(adapterData, deviceName)

                # Deep copy the interface as a new sequence.
                newSequence = copy.deepcopy(self.devices[deviceName])
                # Add it to the sequences.
                self.addSequence(newSequence, deviceName)
            # end for each device
            
            # Wait for the sample rate
            time.sleep(self.sampleRate)
        # end while
    # end pollDevices
    
    # @function: propagateData
    def propagateData(self, adapterData, deviceName):
        self.devices[deviceName].updateData(adapterData)
    # end propagateData
    
    # @function: loadDeviceFromConfig
    def loadDeviceFromConfig(self, configFilePath, hostName):
        # Set the namespace of the element tree.
        ElementTree.register_namespace('', "http://"+str(hostName))
        # Parse the xml document to an element tree.
        self.deviceTree = ElementTree.parse(configFilePath)
        # Load the header and device information by parsing the children
        for childElement in self.deviceTree.getroot():
            # If the child is a header element.
            if "Header" in childElement.tag:
                self.header = MTCHeader(childElement)
                # Set the buffer size to be the one specified by the config header.
                self.sequenceBufferSize = int(self.header.attributes["bufferSize"])
            # end if
            # Otherwise, if the child is a devices element.
            elif "Devices" in childElement.tag:
                # For each child element, which has to be a device.
                for device in childElement:
                    # Create a new device from the element.
                    newDevice = MTCDevice(device)
                    # Add it to the Agent's devices list.
                    self.addDevice(newDevice)
                # end for device in childElement
            # end elif
    # end loadDeviceFromConfig
    
    # @function: addDevice
    # Only one device right now.
    def addDevice(self, newDevice):
        self.devices[newDevice.attributes["name"]] = newDevice
    # end addDevice
    
    # @function: getNumDevices
    def getNumDevices(self):
        return len(self.devices)
    # end getNumDecives
    
    # @function: getNumericallySortedKeys
    def getNumericallySortedKeys(self, unsortedDict):
        # Get the keys of the sequences dictionary.
        keysList = unsortedDict.keys()
        # Convert them all to integer values.
        keysAsInts = []
        for key in keysList:
            keysAsInts.append(int(key))
        # end for
        keysAsInts.sort()
        
        return keysAsInts
    # end getNumericallySortedKeys
    
    # @function: addSequence
    def addSequence(self, newSequence, deviceName):
        """ Delete Excess Sequences """
        # Calculate the difference between the expected buffer size and the number of sequences.
        diff = len(self.sequences) - (self.sequenceBufferSize-1)
        
        # If the difference is a number greater than zero.
        if diff > 0:
            # Keep track of which item to take off next.
            itemToRemove = (diff+self.firstSequenceNumber)
            # While the item to remove is greater than -1.
            while(itemToRemove >= self.firstSequenceNumber):
                # Delete the item at the index.
                del self.sequences[str(itemToRemove)]
                
                # For each device, send the delete request for this sequence number.
                for tempDeviceName in self.devices:
                    self.devices[tempDeviceName].deleteSequence(itemToRemove)
                # end for device
                
                # Decrement the itemToRemove.
                itemToRemove -= 1
            # end while
            
            # Set the first sequence number to be the first one on the "queue".
            self.firstSequenceNumber = self.getNumericallySortedKeys(self.sequences)[0]
        # end if
        
        # Add the new sequence to the list.
        # Generate the timestamp.
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        # Increment the next sequence number.
        self.lastSequenceNumber = self.lastSequenceNumber + 1
        
        # Hold the new sequence.
        myNewSequence = {"sequence":newSequence, "timestamp":timestamp, "deviceName":deviceName}
        
        # Add the new sequence to the overall sequences.
        self.sequences[str(self.lastSequenceNumber)] = myNewSequence
        # Add the new sequence to the devices sequences.
        self.devices[deviceName].addDeviceSequence(self.lastSequenceNumber)
        
        #print "keys: "+str(self.getNumericallySortedKeys(self.sequences))
    # end init
    
    # @function: deviceEncode
    def deviceEncode(self):
        # Grab the string version of the element tree.
        eTreeString = ElementTree.tostring(self.deviceTree.getroot())
        # Remove the "ns0" that seems to be forced by the element tree object.
        eTreeString = eTreeString.replace(":ns0", "")
        eTreeString = eTreeString.replace("ns0:", "")
        return eTreeString
    # end deviceEncode
    
    # **** Streams
    
     # @function: buildMTCStreamsElement
    def buildMTCStreamsElement(self):
        # Create the MTCStreams element.
        mtcStreams = Element("MTConnectStreams")
        # Add the typical attributes to it.
        mtcStreams.attrib = {"xmlns:m":"urn:mtconnect.org:MTConnectStreams:1.2",
                             "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
                             "xmlns":"urn:mtconnect.org:MTConnectStreams:1.2",
                             "xsi:schemaLocation":"urn:mtconnect.org:MTConnectStreams:1.2 http://www.mtconnect.org/schemas/MTConnectStreams_1.2.xsd"
                             }
        return mtcStreams
    # end buildMTCStreamsElement
    
    # @function: buildStreamHeader
    def buildStreamHeader(self):
        # Create the Header element.
        header = Element("Header")
        # Add the needed attributes to it.
        header.attrib = {"creationTime":self.header.attributes["creationTime"],
                         "sender":self.header.attributes["sender"],
                         "instanceId":self.header.attributes["instanceId"],
                         "bufferSize":self.header.attributes["bufferSize"],
                         "version":self.header.attributes["version"],
                         "nextSequence":str(self.nextSequenceNumber),
                         "firstSequence":str(self.firstSequenceNumber),
                         "lastSequence":str(self.lastSequenceNumber)
                         }
        return header
    # end buildStreamHeader
    
    # @function: currentStreamEncode
    def currentStreamEncode(self, deviceName=None, details=None):
        # List of devices to encode (initializing).
        devicesToEncode = {}
        
        # Sequence number, default to the latest.
        sequenceNumber = self.lastSequenceNumber
        
        # Next sequence number, defaults to the current sequence number + 1.
        self.nextSequenceNumber = sequenceNumber + 1
        
        # Make streams root element.
        mtcStreams = self.buildMTCStreamsElement()
        
        # Build a steam header.
        header = self.buildStreamHeader()
        
        # Attach the header to the MTConnectStreams element.
        mtcStreams.append(header)
        
        # Create the Streams element.
        streams = Element("Streams")
        
        # If the details variable is not empty.
        if details != None:
            # Parse the url for the parameters.
            parsedArgs = self.separateArgs(details, deviceName=deviceName)
            
            # If the interval param is included.
            if "interval" in parsedArgs["params"]:
                self.sampleRate = float(parsedArgs["params"]["interval"])/1000
            # end if interval
            
            """ Error Checking """
            # Get a potential list of devices being looked for, based on the passed name.
            devicesToEncode = self.devicesWithName(parsedArgs["deviceName"])
            
            # If the desired device name does not refer any device found here.
            if devicesToEncode == None:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", parsedArgs["deviceName"]+" is not the device monitored by this Agent.")
            # end if

            # If there is "at" and "interval" are present.
            if "at" in parsedArgs["params"] and "interval" in parsedArgs["params"]:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", "Parameters \"at\" and \"interval\" should be passed together for a Current request.")
            # end if

            # If the "from" or "count" attributes are present.
            if "count" in parsedArgs["params"] or "from" in parsedArgs["params"]:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", "Parameters \"from\" and \"count\" are not relevant to the Current request.")
            # end if
            """ Error Checking """
            
            # Variables to keep track of the devices found at the given sequence.
            numOfDevicesAtSequence = 0
            # Sequence number.
            
            # For each device.
            for device in devicesToEncode:
                # Initialize the device to encode as the device's latest sequence.
                deviceToEncode = devicesToEncode[device]
                # Flag used to determine if device should be encoded.
                shouldEncodeDevice = True
                
                """ Parameter Checking """
                # If the "at" param is included.
                if "at" in parsedArgs["params"]:
                    # Get the sequence number.
                    sequenceNumber = parsedArgs["params"]["at"]
                    
                    # If there are no devices that were at the given sequence.
                    if not ((int(sequenceNumber) >= self.firstSequenceNumber) and (int(sequenceNumber) <= self.lastSequenceNumber)):
                        # Return an error indicating no sequence is available.
                        return self.errorEncode("SEQUENCE_UNAVAILABLE", "Sequence "+str(parsedArgs["params"]["at"])+" is not available in the buffer.")
                    # end if zero devices at sequence
                    
                    # If the device has a sequence at the given "at" value.
                    if devicesToEncode[device].hasSequence(sequenceNumber):
                        # Set the device to encode to be the device at this sequence.
                        deviceToEncode = self.sequences[str(sequenceNumber)]["sequence"]
                        # Increment the number of devices at the sequence.
                        numOfDevicesAtSequence += 1
                    # end if device has sequence.
                    # Otherwise,
                    else:
                        # Set the flag not to encode the device.
                        shouldEncodeDevice = False
                    # end else
                # end if
                # Otherwise,
                else:
                    deviceToEncode = self.sequences[str(devicesToEncode[device].latestSequence)]["sequence"]
                    numOfDevicesAtSequence += 1
                # end else
                """ Parameter Checking """
                
                # If the device should be encoded.
                if shouldEncodeDevice:
                    # Encode it.
                    deviceToEncode.encodeStream(streams, str(sequenceNumber),
                                                self.sequences[str(sequenceNumber)]["timestamp"], extraArgs=parsedArgs)
                # end if should encode
            # end for each device
            
            # If there are no devices that were at the given sequence.
            if numOfDevicesAtSequence == 0:
                # Return an error indicating no sequence is available.
                return self.errorEncode("SEQUENCE_UNAVAILABLE", "No devices found at requested sequence.")
            # end if zero devices at sequence
        # end if
        # Otherwise, if the device name is specified.
        elif deviceName != None:
            """ Error Checking """
            # Get a potential list of devices being looked for.
            devicesToEncode = self.devicesWithName(deviceName)
            
            # If the desired device name does not refer any device found here.
            if devicesToEncode == None:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", parsedArgs["deviceName"]+" is not the device monitored by this Agent.")
            # end if
            """ Error Checking """
            
            # Encode the device data for the latest item.
            devicesToEncode[deviceName].encodeStream(streams, str(devicesToEncode[deviceName].latestSequence),
                                     self.sequences[str(devicesToEncode[deviceName].latestSequence)]["timestamp"])
        # end if device name specified.
        # Otherwise,
        else:
            # For each device.
            for device in self.devices:
                # Get the device's latest sequence number.
                deviceLatestSequenceNumber = self.devices[device].latestSequence

                # Encode the device data for the device.
                self.devices[device].encodeStream(streams, str(deviceLatestSequenceNumber),
                                         self.sequences[str(deviceLatestSequenceNumber)]["timestamp"])
            # end for
        # end else
        
        # Attach the streams element to the MTConnectStreams element.
        mtcStreams.append(streams)
        
        # Create a new element tree.
        streamTree = ElementTree.ElementTree()
        # Attach the mtcStreams as the root.
        streamTree._setroot(mtcStreams)
        eTreeString = ElementTree.tostring(streamTree.getroot())
        # Remove the "ns0" that seems to be forced by the element tree object.
        eTreeString = eTreeString.replace(":ns0", "")
        eTreeString = eTreeString.replace("ns0:", "")
        return eTreeString
    # end currentStreamEncode
    
    # @function: sampleStreamEncode
    def sampleStreamEncode(self, deviceName=None, details=None):
        # Create the Streams element.
        streams = Element("Streams")
        
        # If the details variable is not empty.
        if details != None:
            # Parse the url for the parameters.
            parsedArgs = self.separateArgs(details, deviceName=deviceName)
            
            """ Error Checking """
            # If a device is specified but it is not one monitored by this agent.
            if deviceName != None and self.devicesWithName(deviceName) == None:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", deviceName+" is not the device monitored by this Agent.")
            # end if
            
            # If there is "at" and "interval" are present.
            if "at" in parsedArgs["params"]:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", "\"at\" parameter not used for a Sample Request")
            # end if
            """ Error Checking """
            
            """ Parameter Checking """
            # Generate the from and count values.
            fromParam, countParam = self.generateFromAndCount(parsedArgs)
            
            # If the from parameter returned as None.
            if fromParam == None:
                return self.errorEncode("INVALID_REQUEST", "\"from\" parameter, "+str(parsedArgs["params"]["from"])+", is not a sequence number within the buffer.")
                # Return an error.
            # end if from is None
            
            # If the count parameter returned as None.
            if countParam == None:
                return self.errorEncode("INVALID_REQUEST", "\"count\" parameter, "+str(parsedArgs["params"]["count"])+", is not a sequence number within the buffer.")
                # Return an error.
            # end if count is None
            
            # If the interval param is included.
            if "interval" in parsedArgs["params"]:
                self.sampleRate = float(parsedArgs["params"]["interval"])/1000
            # end if interval
            """ Parameter Checking """
            
            # If a device name is specified.
            if deviceName != None:
                # Keep track of the number of sequences added to the stream.
                numSequencesAdded = 0
                
                # Keep track of the iterations through the loop.
                numIterationsThroughLoop = 0
                
                # Flag to determine if the loop should still run.
                keepRunning = True
                
                while keepRunning:
                    # If the number of sequences added is less than count and
                    # the next attempted sequence number is less than the "last sequence."
                    if (numSequencesAdded < countParam) and (fromParam + numIterationsThroughLoop <= self.lastSequenceNumber):
                        # If the device has the current sequence indexed.
                        if self.devices[deviceName].hasSequence(fromParam+numIterationsThroughLoop):
                            # Add the sequence to the stream.
                            self.sequences[str(fromParam+numIterationsThroughLoop)]["sequence"].encodeStream(streams, 
                                                                                                             str(fromParam+numIterationsThroughLoop),
                                                                                                             self.sequences[str(fromParam+numIterationsThroughLoop)]["timestamp"],
                                                                                                             extraArgs=parsedArgs)
                            # Increment the number of sequences added.
                            numSequencesAdded += 1
                        # end if has sequence
                        
                        # Update the next sequence number.
                        self.nextSequenceNumber = fromParam+numIterationsThroughLoop + 1
                        # Increment the number of iterations through the loop.
                        numIterationsThroughLoop += 1
                    # end if
                    # Otherwise,
                    else:
                        keepRunning = False
                    # end else
                # end while
            # end if device name specified
            # Otherwise,
            else:
                # Clamp the count to the from and count parameters combined or the lastSequence
                endSequenceNumber = min(fromParam+countParam-1, self.lastSequenceNumber)
                # Set the next sequence number to be one after the end sequence number.
                self.nextSequenceNumber = endSequenceNumber + 1

                # For the number of sequences to check.
                for i in range(0, endSequenceNumber-fromParam+1):
                    # Grab the current device to encode.
                    deviceToEncode = self.sequences[str(fromParam+i)]["sequence"]
                    # Encode each sequence's stream.
                    deviceToEncode.encodeStream(streams, str(fromParam+i), self.sequences[str(fromParam+i)]["timestamp"], extraArgs=parsedArgs)
                # end for
            # end else
            
            # Merge each element.
            deviceStreams = {}
            for deviceStream in streams.findall(".//DeviceStream"):
                if deviceStream.attrib["name"] not in deviceStreams.keys():
                    deviceStreams[deviceStream.attrib["name"]] = deviceStream
                # end if
                # Otherwise,
                else:
                    # The stream is already in the dictionary, so just add this stream to the one already retained.
                    self.combineComponents(deviceStreams[deviceStream.attrib["name"]], deviceStream)
                    # Delete the extras.
                    streams.remove(deviceStream)
                # end else
            # end for device stream
        # end if
        # Otherwise, if the device name is specified.
        elif deviceName != None:
            """ Error Checking """
            # If the desired name does not exist in the list of devices.
            if self.devicesWithName(deviceName) == None:
                # Return an error.
                return self.errorEncode("INVALID_REQUEST", deviceName+" is not the device monitored by this Agent.")
            # end if
            """ Error Checking """
            
            # Generate the from and count values.
            fromParam, countParam = self.generateFromAndCount()
            
            # Keep track of the number of sequences added to the stream.
            numSequencesAdded = 0

            # Keep track of the iterations through the loop.
            numIterationsThroughLoop = 0

            # Flag to determine if the loop should still run.
            keepRunning = True

            while keepRunning:
                # If the number of sequences added is less than count and
                # the next attempted sequence number is less than the "last sequence."
                if (numSequencesAdded < countParam) and (fromParam + numIterationsThroughLoop <= self.lastSequenceNumber):
                    # If the device has the current sequence indexed.
                    if self.devices[deviceName].hasSequence(fromParam+numIterationsThroughLoop):
                        # Add the sequence to the stream.
                        self.sequences[str(fromParam+numIterationsThroughLoop)]["sequence"].encodeStream(streams, 
                                                                                                         str(fromParam+numIterationsThroughLoop),
                                                                                                         self.sequences[str(fromParam+numIterationsThroughLoop)]["timestamp"])
                        # Increment the number of sequences added.
                        numSequencesAdded += 1
                    # end if has sequence

                    # Update the next sequence number.
                    self.nextSequenceNumber = fromParam+numIterationsThroughLoop + 1
                    # Increment the number of iterations through the loop.
                    numIterationsThroughLoop += 1
                # end if
                # Otherwise,
                else:
                    keepRunning = False
                # end else
            # end while
            
            # Merge each element.
            deviceStreams = {}
            for deviceStream in streams.findall(".//DeviceStream"):
                if deviceStream.attrib["name"] not in deviceStreams.keys():
                    deviceStreams[deviceStream.attrib["name"]] = deviceStream
                # end if
                # Otherwise,
                else:
                    # The stream is already in the dictionary, so just add this stream to the one already retained.
                    self.combineComponents(deviceStreams[deviceStream.attrib["name"]], deviceStream)
                    # Delete the extras.
                    streams.remove(deviceStream)
                # end else
            # end for device stream
        # end if device name specified.
        # Otherwise,
        else:
            # Generate the from and count values.
            fromParam, countParam = self.generateFromAndCount()
            
            # Clamp the count to the from and count parameters combined or the lastSequence
            endSequenceNumber = min(fromParam+countParam-1, self.lastSequenceNumber)
            # Set the next sequence number to be one after the end sequence number.
            self.nextSequenceNumber = endSequenceNumber + 1
            
            # For the number of sequences to check.
            for i in range(0, endSequenceNumber-fromParam+1):
                # Grab the current device to encode.
                deviceToEncode = self.sequences[str(fromParam+i)]["sequence"]
                # Encode each sequence's stream.
                deviceToEncode.encodeStream(streams, str(fromParam+i), self.sequences[str(fromParam+i)]["timestamp"])
            # end for
            # Merge each element.
            deviceStreams = {}
            for deviceStream in streams.findall(".//DeviceStream"):
                if deviceStream.attrib["name"] not in deviceStreams.keys():
                    deviceStreams[deviceStream.attrib["name"]] = deviceStream
                # end if
                # Otherwise,
                else:
                    # The stream is already in the dictionary, so just add this stream to the one already retained.
                    self.combineComponents(deviceStreams[deviceStream.attrib["name"]], deviceStream)
                    # Delete the extras.
                    streams.remove(deviceStream)
                # end else
            # end for device stream
        # end else
        
        # Make streams root element.
        mtcStreams = self.buildMTCStreamsElement()
        
        # Build a steam header.
        header = self.buildStreamHeader()
        
        # Attach the header to the MTConnectStreams element.
        mtcStreams.append(header)
        
        # Attach the streams element to the MTConnectStreams element.
        mtcStreams.append(streams)
        
        # Create a new element tree.
        streamTree = ElementTree.ElementTree()
        # Attach the mtcStreams as the root.
        streamTree._setroot(mtcStreams)
        eTreeString = ElementTree.tostring(streamTree.getroot())
        # Remove the "ns0" that seems to be forced by the element tree object.
        eTreeString = eTreeString.replace(":ns0", "")
        eTreeString = eTreeString.replace("ns0:", "")
        return eTreeString
    # end sampleStreamEncode
    
    # **** End Streams
    
    # **** Xml Combining
    # @function: combineElements
    def combineComponents(self, elementOne, elementTwo):
        # For each component stream in element one.
        for primaryComponentStream in elementOne.findall(".//ComponentStream"):
            # For each component stream in element two.
            for secondaryComponentStream in elementTwo.findall(".//ComponentStream"):
                # If the component ids match.
                if primaryComponentStream.attrib["componentId"] == secondaryComponentStream.attrib["componentId"]:
                    # Combine samples.
                    self.combineDataItems(primaryComponentStream, secondaryComponentStream, "Samples")
                    # Combine events.
                    self.combineDataItems(primaryComponentStream, secondaryComponentStream, "Events")
                    # Combine condition.
                    self.combineDataItems(primaryComponentStream, secondaryComponentStream, "Condition")
                # end if
            # end for
        # end for
    # end combineElements
    
    # @function: combineDataItems
    def combineDataItems(self, primaryComponentStream, secondaryComponentStream, category):
        # For each data item in the given category for the second component stream.
        # If the category is present in these streams.
        if primaryComponentStream.find(category) != None and secondaryComponentStream.find(category) != None:
            for dataItem in secondaryComponentStream.find(category):
                # Add it to the primary component stream, at the element with the given category, the data item.
                primaryComponentStream.find(category).append(dataItem)
            # end for
        # end if
    # end combineDataItems
    # **** Xml Combining
    
    # @function: assetEncode
    def assetEncode(self):
        # There are no assets, so return an error.
        return self.errorEncode("INVALID_REQUEST", "No Assets Attached.")
    # end assetEncode
    
    # @function: errorEncode
    def errorEncode(self, errorCode, errorText):
        # Set the agent's error code and error.
        self.errorTree.element.attrib["errorCode"] = errorCode
        self.errorTree.element.text = errorText
        # Convert the error to a string.
        errorString = ElementTree.tostring(self.errorTree.root)
        # Remove the bloody namespace prefixes.
        errorString = errorString.replace(":ns0", "")
        errorString = errorString.replace("ns0:", "")
        
        return errorString
    # end errorEncode
    
    # @function: generateFromAndCount
    def generateFromAndCount(self, parsedArgs={"params":{}}):
        # Default values for the possible arguments.
        fromParam = 0
        countParam = 100
        # If the "from" attribute is present.
        if "from" in parsedArgs["params"]:
            fromParam = int(parsedArgs["params"]["from"])
            # If the from parameter is less than zero.
            if fromParam < 0:
                # Set the from parameter to 0.
                fromParam = None
            # end if from parameter is less than zero
            # Otherwise, if the from parameter is not equal to a sequence within the buffer and is not 0.
            elif not ((self.firstSequenceNumber <= fromParam) and (fromParam <= self.lastSequenceNumber)) and fromParam > 0:
                # Set the from parameter to 0.
                fromParam = None
            # end if from parameter in range
        # end if from
        # If the "count" attribute is present.
        if "count" in parsedArgs["params"]:
            countParam = int(parsedArgs["params"]["count"])
        # end if count

        # If the from parameter is less than the first sequence.
        #if fromParam < self.firstSequenceNumber:
            # Set it to the same as the first sequence number.
            #fromParam = self.firstSequenceNumber
        # end if
        
        # If the from parameter is within the buffer.
        if fromParam != None and countParam > 0:
            # If the from parameter is zero.
            if fromParam == 0:
                # Set it to the same as the first sequence number.
                fromParam = self.firstSequenceNumber
            # end if
            
            # Clamp the from to the available sequence number.
            fromParam = min(fromParam, self.lastSequenceNumber)
            
            # Return the adjusted from parameter and the end sequence number.
            return fromParam, countParam
        # end if
        # Otherwise,
        else:
            # Return empty values.
            return None, None
        # end else
    # end generateFromAndCount
    
    # @function: separateArgs
    def separateArgs(self, argsString, deviceName=None):
        # Be sure to replace any %22 with ".
        argsString = argsString.replace("%22","\"")
        argsString = argsString.replace("%20","")
        # Construct the empty arguments.
        args = {"deviceName":deviceName, "components":[], "attributes":{}, "params":{}}
        
        """ Finding the Device/Component/DataItem Path """
        
        # Grab the device/components portion.
        deviceComponentsPath = ""
        # If there are any attributes included.
        if "[" in argsString and not "//Device" in argsString:
            # Get the path (from the equal sign to the opening square bracket).
            deviceComponentsPath = argsString[argsString.index("=")+1:argsString.index("[")]
            
            # Grab any attributes.
            attributesString = argsString[argsString.index("[")+1:argsString.index("]")]
            
            # Split the attributes apart by "and".
            splitAttributes = attributesString.split("and")
            
            # For each attribute.
            for attr in splitAttributes:
                # Trim whitespace.
                trimmedAttr = attr.strip()
                # Grab the attribute name.
                attrName = trimmedAttr[trimmedAttr.index("@")+1:trimmedAttr.index("=")]
                # Grab the attribute type.
                attrType = trimmedAttr[trimmedAttr.index("=")+1:]
                
                # Remove all quotes from the attribute value.
                attrType = attrType.replace("\"", "")
                
                # Add it to the arguments' attributes.
                args["attributes"][attrName] = attrType
            # end for
        # end if
        # Otherwise, if a device or path are specified.
        elif "//" in argsString:
            # Get the path (from the equal sign to the end of the string).
            deviceComponentsPath = argsString[argsString.index("=")+1:]
        # end else
        
        """ Path Parameter """
        
        # If the deviceComponentsPath refers to a device.
        if "//Device" in deviceComponentsPath:
            # Grab the name attribute of the device.
            attributes = argsString[argsString.index("[")+1:argsString.index("]")]
            foundDeviceName = attributes[attributes.index("\"")+1:len(attributes)-1]
            # Set the args device name attribute.
            args["deviceName"] = foundDeviceName
        # end if
        # Otherwise, if other arguments are in the path.
        elif "&" in deviceComponentsPath:
            # Adjust the device path.
            deviceComponentsPath = deviceComponentsPath[0:deviceComponentsPath.index("&")]
            # Get each component.
            components = deviceComponentsPath.split("//")
            # For each component.
            for component in components:
                # If component is not empty.
                if component != "" and component != None: # and component != "DataItem":
                    args["components"].append(component)
                # end if
            # end for
        # end if arguments
        # Otherwise, if there are components.
        else:
            # Get each component.
            components = deviceComponentsPath.split("//")
            # For each component.
            for component in components:
                # If component is not empty.
                if component != "" and component != None: # and component != "DataItem":
                    args["components"].append(component)
                # end if
            # end for
        # end else
        
        """ Other Parameters """
        
        # If there are parameters given.
        if "&" in argsString:
            # Grab the parameters.
            parameters = argsString[argsString.index("&")+1:]
            parameters = parameters.split("&")
            
            # For each parameter.
            for parameter in parameters:
                # Grab the attribute and value.
                attributeValuePair = parameter.split("=")
                args["params"][attributeValuePair[0]] = attributeValuePair[1]
            # end for
        # end if
        # Otherwise, if there is a single argument provided.
        elif argsString != "":
            # Grab the attribute and value.
            attributeValuePair = argsString.split("=")
            args["params"][attributeValuePair[0]] = attributeValuePair[1]
        # end if single argument
        return args
    # end separateArgs
    
    # @function: devicesWithName
    # @description: Function that returns True if the given device name is that of one that is being monitored by this Agent, None if not.
    def devicesWithName(self, deviceName):
        # If deviceName is empty.
        if deviceName == None:
            # Return all of the devices.
            return self.devices
        # end if
        
        # Otherwise, for each device.
        for device in self.devices:
            # If the device has the device name.
            if device == deviceName:
                # Return this device.
                return {deviceName: self.devices[device]}
            # end if
        # end for device
        
        # If no device has been returned, it does not exist. So, return None.
        return None
    # end devicesWithName
# end MTCAgent

""" Configuration settings and file loading. """

# Default IP and Port settings.
HOST_NAME = '127.0.0.1'
PORT_NUMBER = 1080

# Load the configuration data for this agent.
config = json.load(open("config.json", "r"))
print str(config)

# Grab the host name and port number from the config.
HOST_NAME = config["HTTPHost"]["IP"]
PORT_NUMBER = int(config["HTTPHost"]["Port"])

agent = MTCAgent(config["DeviceConfigurationFile"], config["ErrorReference"], HOST_NAME)

""" Webserver classes. """

# @class: MTCAgentHandler
class MTCAgentHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # end createMTCHook
    # @function: do_HEAD
    def do_HEAD(s):
        # Send a success response.
        s.send_response(200)
        # Send the content type.
        s.send_header("Content-type", "text/xml")
        # End the headers.
        s.end_headers()
    # end do_HEAD
    
    # @function: do_GET
    def do_GET(s):
        # Send the header information (success, content type)
        s.send_response(200)
        s.send_header("Content-type", "text/xml")
        s.end_headers()
        
        try:
            # Split up the path to be easier to parse or analyze.
            splitPath = s.path.split("?")
            # Grab the command, possibly the machine name too.
            command = splitPath[0]

            # Grab the parameters.
            params = None
            if len(splitPath) > 1:
                params = splitPath[1]
            # end if

            # Take off the leading "/".
            command = command.lstrip("/")

            # Device, if specified.
            specifiedDevice = None
            # If the command contains a "/".
            if "/" in command:
                # Split on that character
                splitCommand = command.split("/")
                # The first parameter will be the specified device.
                specifiedDevice = splitCommand[0]
                # The command is the second element.
                command = splitCommand[1]
            # end if

            # If the probe has been requested.
            if command == "probe":
                # Write the data.
                s.wfile.write(agent.deviceEncode())
            # end if probe
            # If current status has been requested.
            elif command == "current":
                # If there is a question mark, then grab the rest of the path for parsing the desired details.
                if params != None:
                    # Grab the other desired details.
                    desiredDetails = s.path[s.path.index("?")+1:]
                    #print "desired details: "+str(desiredDetails)
                    # Write the current desired data.
                    s.wfile.write(agent.currentStreamEncode(deviceName=specifiedDevice, details=desiredDetails))
                # end if
                # If the device is specified in the path.
                elif specifiedDevice != None:
                    # Write the current desired data.
                    s.wfile.write(agent.currentStreamEncode(deviceName=specifiedDevice))
                # end elif
                # Otherwise, just call a generic current request.
                else:
                    # Write all of the current data.
                    s.wfile.write(agent.currentStreamEncode())
                # end if
            # end if current
            # If a sample status has been requested.
            elif command == "sample":
                # If there is a question mark, then grab the rest of the path for parsing the desired details.
                if params != None:
                    # Grab the other desired details.
                    desiredDetails = s.path[s.path.index("?")+1:]
                    
                    # Write the current desired data.
                    result = agent.sampleStreamEncode(deviceName=specifiedDevice, details=desiredDetails)
                    #s.wfile.write(agent.sampleStreamEncode(deviceName=specifiedDevice, details=desiredDetails))
                    s.wfile.write(result)
                # end if
                # Otherwise, if the device name is specified.
                elif specifiedDevice != None:
                    # Write all of the current data.
                    s.wfile.write(agent.sampleStreamEncode(deviceName=specifiedDevice))
                # end if device name specified
                # Otherwise, just call a generic current request.
                else:
                    # Write all of the current data.
                    s.wfile.write(agent.sampleStreamEncode())
                # end if
            # end if sample
            # If assets have been requested.
            elif "asset" in s.path:
                # Return an error... because there are no assets.
                s.wfile.write(agent.assetEncode())
            # end if assets
        # end try
        except Exception as ex:
            # If an error occurred, write it.
            error = traceback.format_exc(sys.exc_info()[2])
            s.wfile.write(agent.errorEncode("INVALID_REQUEST", error))
        # end except
        
        # Write the content to the page.
        #s.wfile.write("<html>\n\t<head>\n\t\t<title>MTConnect Agent</title>\n\t</head>")
        #s.wfile.write("\t<body>\n\t\t<p>Just testing web serving.</p>")
        #s.wfile.write("\t\t<p>Page path: "+s.path+"</p></body>\n</html>")
    # end do_GET
# end MTCAgentHandler

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MTCAgentHandler)
    #print time.asctime() + "Server starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        agent.isRunning = False
        pass
    
    httpd.server_close()
    #print time.asctime() + "server stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
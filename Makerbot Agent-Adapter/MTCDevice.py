"""
author: Kent Vasko
company: MAYA Design
"""

from xml.etree.ElementTree import Element
from MTCDataItem import MTCDataItem
from MTCComponent import MTCComponent, MTCControllerComponent
from MTCAdapter import *

# @class: MTCDevice
class MTCDevice:
    # @function: init
    def __init__(self, deviceElement):
        self.element = deviceElement
        self.attributes = {"id":deviceElement.attrib["id"],
                           "uuid":deviceElement.attrib["uuid"],
                           "name":deviceElement.attrib["name"]
                           }
        self.components = []
        self.dataItems = []
        # Keep track of the sequences specific to this device.
        self.deviceSequences = []
        # Latest Sequence.
        self.latestSequence = None
        
        # Initialie the adapter.
        self.adapter = MTCAdapter(self.attributes["id"])
        
        # Parse the child elements of the device element.
        for child in deviceElement:
            # If the child element is DataItems
            if "DataItems" in child.tag:
                # For each data item.
                for dataItem in child:
                    # Create a new DataItem
                    newDataItem = MTCDataItem(dataItem)
                    # Add it to the data items list.
                    self.dataItems.append(newDataItem)
                # end for
            # end if
            # If the child element is Components.
            elif "Components" in child.tag:
                # For each component.
                for component in child:
                    # If the component is a Controller.
                    if "Controller" in component.tag:
                        # Create a new controller component.
                        newController = MTCControllerComponent(component)
                        # Add it to the components list.
                        self.components.append(newController)
                    # end if
                    # Otherwise, it is a generic component.
                    else:
                        # Create a new component.
                        newComponent = MTCComponent(component)
                        # Add it to the components list.
                        self.components.append(newComponent)
                    # end else
                # end for
            # end if
        # end for
    # end init
    
    # @function: addDeviceSequence
    def addDeviceSequence(self, index):
        self.deviceSequences.append(index)
        self.latestSequence = index
    # end addDeviceSequence
    
    # @function: hasSequence
    def hasSequence(self, index):
        # If the index exists.
        if int(index) in self.deviceSequences:
            return True
        # end if index is found.
        # Otherwise,
        else:
            return False
        # end else
    # end hasSequence
    
    # @function: deleteDeviceSequence
    def deleteSequence(self, deviceSequenceNumber):
        # If the sequence is in the list of sequences.
        if int(deviceSequenceNumber) in self.deviceSequences:
            # Delete it.
            del self.deviceSequences[self.deviceSequences.index(int(deviceSequenceNumber))]
        # end if device sequence in list of sequences
    # end deleteSequence
    
    # @function: getEncodedDataItems
    def getEncodedDataItems(self, componentStream, sequence, timestamp, desiredAttributes=None):
        # First, organize the data items into events, samples, and conditions.
        events = []
        samples = []
        conditions = []
        
        # For each data item.
        for dataItem in self.dataItems:
            # Flag used to determine which data items to include.
            includeDataItem = True
            # If the data item has the specified attribute needs and desires.
            if desiredAttributes != None:
                # For each desired attribute.
                for attributeName in desiredAttributes:
                    # If the attribute is not in the data item's attributes.
                    if attributeName not in dataItem.attributes:
                        # Do not include this data item.
                        includeDataItem = False
                    # end if
                    # Otherwise, if the attribute's value does not match the desired one.
                    elif desiredAttributes[attributeName] != dataItem.attributes[attributeName]:
                        # Do not include this data item.
                        includeDataItem = False
                    # end elif
                # end for
            # end if
            
            # If this data item should be included.
            if includeDataItem:
                # If the dataItem's category is event.
                if dataItem.attributes["category"] == "EVENT":
                    events.append(dataItem)
                # end if
                # If the dataItem's category is sample.
                elif dataItem.attributes["category"] == "SAMPLE":
                    samples.append(dataItem)
                # end if
                # If the dataItem's category is category.
                elif dataItem.attributes["category"] == "CONDITION":
                    conditions.append(dataItem)
                # end if
            # end if included data item
        # end for
        
        # If there are any samples.
        if len(samples) > 0:
            # Create an Samples element.
            samplesElement = Element("Samples")
            # For each sample.
            for sample in samples:
                # Encode its stream and add it to the samples element.
                sample.encodeStream(samplesElement, sequence, timestamp)
            # end for
            # Add the samples element to the component stream element.
            componentStream.append(samplesElement)
        # end if
        # If there are any events.
        if len(events) > 0:
            # Create an Events element.
            eventsElement = Element("Events")
            # For each event.
            for event in events:
                # Encode its stream and add it to the events element.
                event.encodeStream(eventsElement, sequence, timestamp)
            # end for
            # Add the events element to the component stream element.
            componentStream.append(eventsElement)
        # end if
        # If there are any conditions.
        if len(conditions) > 0:
            # Create an Events element.
            conditionsElement = Element("Conditions")
            # For each condition.
            for condition in conditions:
                # Encode its stream and add it to the conditions element.
                condition.encodeStream(conditionsElement, sequence, timestamp)
            # end for
            # Add the conditions element to the component stream element.
            componentStream.append(conditionsElement)
        # end if
    # end getEncodedDataItems
    
    # @function: encodeStream
    # @param: parentElement, ElementTree.Element, The parent node to which the device and any children will be parented.
    # @param: sequence, MTCDevice, A snapshot of the MTC device being requested.
    # @param: timestamp, DateTime, The timestamp to be associated with the request.
    # @param: extraArgs, Dictionary, Potential other arguments to narrow down the items returned by this encode request.
    # extraArgs = {"deviceName":deviceName, "components":[], "attributes":{}, "params":{}}
    def encodeStream(self, parentElement, sequence, timestamp, extraArgs=None):
        # Create a device stream element.
        deviceElement = Element("DeviceStream")
        # Add the attributes to it.
        deviceElement.attrib["uuid"] = self.attributes["uuid"]
        deviceElement.attrib["name"] = self.attributes["name"]
        
        """ Data Items """
        # If there are no arguments.
        if extraArgs == None:
            # Create a new element for the component stream of the device.
            dataItemStream = Element("ComponentStream")
            # Add attributes to it.
            dataItemStream.attrib["component"] = "Device"
            dataItemStream.attrib["name"] = self.attributes["name"]
            dataItemStream.attrib["componentId"] = self.attributes["id"]

            # Add the data items to the component stream, based on the category of the item ("sample", "event", "condition").
            self.getEncodedDataItems(dataItemStream, sequence, timestamp)

            # Add the component stream to the device stream.
            deviceElement.append(dataItemStream)
        # end if
        # Otherwise, if there are arguments, and no components are given.
        elif extraArgs["components"] == []:
            # Create a new element for the component stream of the device.
            dataItemStream = Element("ComponentStream")
            # Add attributes to it.
            dataItemStream.attrib["component"] = "Device"
            dataItemStream.attrib["name"] = self.attributes["name"]
            dataItemStream.attrib["componentId"] = self.attributes["id"]

            # Add the data items to the component stream, based on the category of the item ("sample", "event", "condition").
            self.getEncodedDataItems(dataItemStream, sequence, timestamp, desiredAttributes=extraArgs["attributes"])

            # Add the component stream to the device stream.
            deviceElement.append(dataItemStream)
        # end elif
        # Otherwise, if this device's data items are being requested.
        elif extraArgs["components"][0] == "DataItem":
            # Create a new element for the component stream of the device.
            dataItemStream = Element("ComponentStream")
            # Add attributes to it.
            dataItemStream.attrib["component"] = "Device"
            dataItemStream.attrib["name"] = self.attributes["name"]
            dataItemStream.attrib["componentId"] = self.attributes["id"]

            # Add the data items to the component stream, based on the category of the item ("sample", "event", "condition").
            self.getEncodedDataItems(dataItemStream, sequence, timestamp, desiredAttributes=extraArgs["attributes"])

            # Add the component stream to the device stream.
            deviceElement.append(dataItemStream)
        # end if data item request
        """ Data Items """
        
        """ Components """
        # For each component of this device.
        for component in self.components:
            # If all components are desired.
            if extraArgs == None:
                # Encode each component and attach it to the device stream element.
                component.encodeStream(deviceElement, sequence, timestamp)
            # end if
            # Otherwise.
            else:
                # If the components list is given, but empty.
                if "components" in extraArgs and extraArgs["components"] == []:
                    component.encodeStream(deviceElement, sequence, timestamp, desiredAttributes=extraArgs["attributes"])
                # end if
                # Otherwise, if the component is the one being requested, and the current component is not a data item specification.
                elif len(extraArgs["components"]) > 0 and not (extraArgs["components"][0] == "DataItem"):
                    # If the component is the first elment in the components arguments.
                    if extraArgs["components"][0] in component.attributes["type"]:
                        # If there are more components specified in the arguments.
                        if len(extraArgs["components"]) > 1:
                            componentsToPass = extraArgs["components"][1:]
                            component.encodeStream(deviceElement, sequence, timestamp, desiredComponents=componentsToPass, desiredAttributes=extraArgs["attributes"])
                        # end if
                        # Otherwise.
                        else :
                            component.encodeStream(deviceElement, sequence, timestamp, desiredAttributes=extraArgs["attributes"])
                        # end else
                    # end if component matches name
                # end if at least one component
            # end else
        # end for
        """ Components """
        
        # Add the newly created element to the parentElement.
        parentElement.append(deviceElement)
    # end encodeStream
    
    # @function: addToStream
    def addToStream(self, parentElement, sequence, timestamp, extraArgs=None):
        """ Data Items """
        # If there are no arguments.
        if extraArgs == None:
            # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                # If the given component stream has the same name as this device.
                if componentStream.attrib["componentId"] == self.attributes["id"]:
                    # Add the data item to component.
                    self.getEncodedDataItems(componentStream, sequence, timestamp)
                # end if
            # end for
        # end if
        # Otherwise, if there are arguments, and no components are given.
        elif extraArgs["components"] == []:
            # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                # If the given component stream has the same name as this device.
                if componentStream.attrib["componentId"] == self.attributes["id"]:
                    # Add the data item to component.
                    self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=extraArgs["attributes"])
                # end if
            # end for
        # end elif
        # Otherwise, if this device's data items are being requested.
        elif extraArgs["components"][0] == "DataItem":
           # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                # If the given component stream has the same name as this device.
                if componentStream.attrib["componentId"] == self.attributes["id"]:
                    # Add the data item to component.
                    self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=extraArgs["attributes"])
                # end if
            # end for
        # end if data item request
        # """ Data Items """
        
        # """ Components """
        # Otherwise.
        else:
            # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                print "first for"
                # For each of this device's components.
                for component in self.components:
                    print str(componentStream.attrib["componentId"])+", "+str(component.attributes["id"])
                    # If the given component stream has the same name as this device.
                    if componentStream.attrib["componentId"] == component.attributes["id"]:
                        print str("components: "+str(componentStream.attrib))
                        # Add the compoment to the already existing component stream.
                        component.addToStream(componentStream, sequence, timestamp, desiredAttributes=extraArgs["attributes"])
                    # end if
                # end for component
            # end for component stream
        # end else
        """ Components """
    # end addToStream
    
    # @function: updateData
    def updateData(self, makerbotData):
        # For each data item of this device.
        for dataItem in self.dataItems:
            # If the data item's id is in the new data.
            if dataItem.attributes["id"] in makerbotData:
                # Update the value of the data item.
                dataItem.currentData = makerbotData[dataItem.attributes["id"]]
            # end if
        # end for
        
        # Send the update to the device's components.
        for component in self.components:
            component.updateData(makerbotData)
        # end for
    # end updateData
# end MTCDevice
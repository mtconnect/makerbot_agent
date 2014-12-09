"""
author: Kent Vasko
company: MAYA Design
"""

from xml.etree.ElementTree import Element
from MTCDataItem import MTCDataItem

# @class: MTCComponent
class MTCComponent:
    # @function: init
    def __init__(self, componentElement):
        self.element = componentElement
        self.attributes = {"id":componentElement.attrib["id"],
                           "type":componentElement.tag,
                           "name":componentElement.attrib["name"]
                           }
        self.subComponents = []
        self.dataItems = []
        # Parse the child elements of the device element.
        for child in componentElement:
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
                    # Create a new component.
                    newComponent = MTCComponent(component)
                    # Add it to the components list.
                    self.subComponents.append(newComponent)
                # end for
            # end if
        # end for
    # end init
    
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
    def encodeStream(self, deviceStreamElement, sequence, timestamp, desiredComponents=None, desiredAttributes=None):
        # Create a new element for the component stream of the device.
        componentStream = Element("ComponentStream")
        # Add attributes to it.
        # Get the component name, which is the tag name.
        componentName = self.element.tag
        # Remove the annoying {urn:mtconnect.org:MTConnectDevices:1.2} junk.
        componentName = componentName[componentName.index("}")+1:]
        # Set the attributes.
        componentStream.attrib["component"] = componentName
        componentStream.attrib["name"] = self.attributes["name"]
        componentStream.attrib["componentId"] = self.attributes["id"]
        
        """ Data Items """
        # If there are no desired components pass.
        if desiredComponents == None:
            # Add the data items to the component stream, based on the category of the item ("sample", "event", "condition").
            self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=desiredAttributes)
        # end if
        # Otherwise, if this component's data items are specifically desired.
        elif desiredComponents[0] == "DataItem":
            # Add the data items to the component stream, based on the category of the item ("sample", "event", "condition").
            self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=desiredAttributes)
        # end if data item
        """ Data Items """
        
        """ Subcomopnents """
        for subComponent in self.subComponents:
            # If all sub components are desired.
            if desiredComponents == None:
                # Add the subcomponent to the stream at the same level as this component.
                subComponent.encodeStream(deviceStreamElement, sequence, timestamp, desiredAttributes=desiredAttributes)
            # end if
            # Otherwise, if the subcomponent is the one being requested, it is not a data item specification.
            elif len(desiredComponents) > 0 and not (desiredComponents[0] == "DataItem"):
                # If the subcomponent is the first element in the desired components list.
                print "component text: "+str(subComponent.attributes["type"])
                if desiredComponents[0] in subComponent.attributes["type"]:
                    # If there are more subcomponents specified in the arguments.
                    if len(desiredComponents) > 1:
                        componentsToPass = desiredComponents[1:]
                        subComopnent.encodeStream(deviceStreamElement, sequence, timestamp, desiredCompnents=componentsToPass, desiredAttributes=desiredAttributes)
                    # end if
                    # Otherwise.
                    else:
                        subComponent.encodeStream(deviceStreamElement, sequence, timestamp, desiredAttributes=desiredAttributes)
                    # end else
                # end if
            # end elif
        # end for
        """ Subcomponents """
        
        # If there the new component stream has children.
        if len(componentStream) > 0:
            # Attach the component stream to the device stream.
            deviceStreamElement.append(componentStream)
        # end if
    # end encodeStream
    
    # @function: addToStream
    def addToStream(self, parentElement, sequence, timestamp, desiredAttributes=None):
        print "ADD TO STREAM - component"
        """ Data Items """
        # If there are no arguments.
        if extraArgs == None:
            # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                # If the given component stream has the same name as this device.
                if componentStream.attrib["componentId"] == self.attributes["id"]:
                    print str(componentStream.attrib)
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
                    print str(componentStream.attrib)
                    # Add the data item to component.
                    self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=desiredAttributes)
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
                    self.getEncodedDataItems(componentStream, sequence, timestamp, desiredAttributes=desiredAttributes)
                # end if
            # end for
        # end if data item request
        # """ Data Items """
        # """ Sub Components """
        # Otherwise.
        else:
            # For all component streams in the device stream's path.
            for componentStream in parentElement.findall(".//ComponentStream"):
                # For each of this device's components.
                for subComponent in self.subComponents:
                    # If the given component stream has the same name as this device.
                    if componentStream.attrib["componentId"] == subComponent.attributes["id"]:
                        print str("components: "+str(componentStream.attrib))
                        # Add the compoment to the already existing component stream.
                        subComponent.addToStream(componentStream, sequence, timestamp, desiredAttributes=desiredAttributes)
                    # end if
                # end for sub component
            # end for component stream
        # end else
        """ Sub Components """
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
        
        # Send the update to the component's components.
        for component in self.subComponents:
            component.updateData(makerbotData)
        # end for
    # end updateData
# end MTCComponent

# @class: MTCControllerComponent
class MTCControllerComponent(MTCComponent):
    # @function: init
    def __init__(self, componentElement):
        MTCComponent.__init__(self, componentElement)
        # Get the path element.
        for child in componentElement:
            # If it is a path element.
            if "Path" in child.tag:
                # Save reference to the path.
                self.path = child
                # Parse through its children to get the data items.
                for grandchild in child:
                    # If it is a data items tag.
                    if "DataItems" in grandchild.tag:
                        # For each data item.
                        for dataItem in grandchild:
                            # Create a new data item.
                            newDataItem = MTCDataItem(grandchild)
                            # Save it to the dataitems
                            self.dataItems.append(newDataItem)
                        # end for
                    # end if
                # end for
            # end if
        # end for
    # end init
    
    # @function: encode
    # end encode
# end MTCControllerComponent
"""
author: Kent Vasko
company: MAYA Design
"""

from xml.etree.ElementTree import Element

# @class: MTCDataItem
# @description: Object representing the basic MTConnect Data Item.
class MTCDataItem:
    # @function: init
    def __init__(self, dataItemElement):
        # Instance variables.
        self.element = dataItemElement
        self.attributes = {"id":dataItemElement.attrib["id"],
                           "name":dataItemElement.attrib["name"],
                           "type":dataItemElement.attrib["type"]
                           }
        # If subtype is provided.
        if "subType" in dataItemElement.attrib:
            self.attributes["subType"] = dataItemElement.attrib["subType"]
        # end if
        # If category is provided.
        if "category" in dataItemElement.attrib:
            self.attributes["category"] = dataItemElement.attrib["category"]
        # end if
        
        # If the data item's type is POSITION.
        if self.attributes["type"] == "POSITION":
            # Set a coordinate system attribute.
            self.attributes["coordinateSystem"] = dataItemElement.attrib.get("coordinateSystem", "MACHINE")
        # end if 
        
        self.currentData = None
    # end init
    
    # @function: encodeStream
    def encodeStream(self, parentElement, sequence, timestamp):
        # Create a new element of the data item's type.
        elementName = self.attributes["type"]
        elementName = elementName.lower()
        elementName = elementName[0].upper()+elementName[1:]
        newElement = Element(elementName)
        
        # Add the attributes.
        newElement.attrib["dataItemId"] = self.attributes["id"]
        newElement.attrib["name"] = self.attributes["name"]
        newElement.attrib["sequence"] = sequence
        newElement.attrib["timestamp"] = timestamp
        # If there is a subType.
        if "subType" in self.attributes:
            newElement.attrib["subType"] = self.attributes["subType"]
        # end if
        
        # Give it the data.
        newElement.text = str(self.currentData)
        
        # Attach it to the parent element.
        parentElement.append(newElement)
    # end encodeStream
# end MTCDataItem
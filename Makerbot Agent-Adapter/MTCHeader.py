"""
author: Kent Vasko
company: MAYA Design
"""

from xml.etree.ElementTree import Element
# @class MTCHeader
class MTCHeader:
    # @function: init
    def __init__(self, headerElement):
        # Instance variables.
        self.element = headerElement
        self.attributes = {"bufferSize":headerElement.attrib["bufferSize"],
                           "instanceId":headerElement.attrib["instanceId"],
                           "creationTime":headerElement.attrib["creationTime"],
                           "sender":headerElement.attrib["sender"],
                           "version":headerElement.attrib["version"]
                           }
        # If there is an asset count and buffer (if Devices).
        if "assetCount" in headerElement.attrib:
            self.attributes["assetCount"] = headerElement.attrib["assetCount"]
            self.attributes["assetBufferSize"] = headerElement.attrib["assetBufferSize"]
    # end init
# end MTCHeader
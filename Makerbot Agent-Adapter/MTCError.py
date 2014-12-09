"""
author: Kent Vasko
company: MAYA Design
"""

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ElementTree

from MTCHeader import MTCHeader

# @class: MTCError
class MTCError:
    # @function: init
    def __init__(self, errorElementTree):
        self.root = errorElementTree.getroot()
        # Parse the children to get the header and error elements.
        for child in self.root:
            # If the child is a header.
            if "Header" in child.tag:
                self.header = MTCHeader(child)
            # end if
            # If the child is errors.
            elif "Errors" in child.tag:
                # For each child element of the errors element (should only be one).
                for error in child:
                    # Grab a reference to the element.
                    self.element = error
                    # Grab the error code attribute.
                    self.errorCode = self.element.attrib["errorCode"]
                    # Grab the CDATA.
                    self.text = self.element.text;
                # end for
            # end elif
        # end for
    # end init
# end MTCError
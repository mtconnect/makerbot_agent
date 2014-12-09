"""
author: Kent Vasko
company: MAYA Design
"""

# @class MTCDeviceStream
class MTCDeviceStream:
    # @function: init
    def __init__(self, name, uuid):
        self.attributes = {"name":name
                           "uuid":uuid
                           }
        self.componentStreams = {}
    # end init
    
    # @function: addComponentStream
    def addComponentStream(self, componentStream):
        self.componentStream[componentStream.attributes["componentId"]] = componentStream
    # end addComponentStream
    
    # @function: Encode
    def encode(self):
        print "MTC Device Stream.encode"
    # end encode
# end MTCDeviceStream

# @class MTCComponentStream
class MTCComponentStream:
    # @function: init
    def __init__(self, componentId, name, component, nativeName=None, uuid=None):
        self.attributes = {"componentId":componentId, "name":name,
                           "component":component, "nativeName":nativeName,
                           "uuid":uuid
                           }
        self.events = []
        self.samples = []
        self.conditions = []
    # end init
    
    # @function: addEvent
    def addEvent(self, event):
        self.events.append(event)
    # end addEvent
    
    # @function: addSample
    def addSample(self, sample):
        self.samples.append(sample)
    # end addSample
    
    # @function: addCondition
    def addCondition(self, condition):
        self.conditions.append(condition)
    # end addEvent
    
    # @function: Encode
    def encode(self):
        print "MTC Component Stream.encode"
    # end encode
# end MTCComponentStream

# @class MTCStreamSample
class MTCStreamSample:
    # @function: init
    def __init__(self, value, dataItemId, sequence, timestamp, sampleRate=10, name=None, subType=None, statistic=None, duration=None):
        # Attributes dictionary.
        self.attributes = {"dataItemId":dataItemId,
                           "sequence":sequence,
                           "timestamp":timestamp,
                           "sampleRate":sampleRate,
                           "name":name, "subType":subType,
                           "statistic":statistic,
                           "duration":duration
                          }
        self.value = value
    # end init
    
    # @function: Encode
    def encode(self):
        print "MTC Stream Sample.encode"
    # end encode
# end MTCStreamSample

# @class MTCStreamEvent
class MTCStreamEvent:
    # @function: init
    def __init__(self, elementName, value, dataItemId, timestamp, sequence, name=None, subType=None):
        # Attributes dictionary.
        self.attributes = {"elementName":elementName,
                           "dataItemId":dataItemId,
                           "sequence":sequence,
                           "timestamp":timestamp,
                           "name":name, "subType":subType
                          }
        self.value = value
    # end init
    
    # @function: 
    def encode(self):
        print "MTC Stream Event.encode"
    # end encode
# end MTCStreamEvent

# @class MTCStreamCondition
class MTCStreamCondition:
    # @function: init
    def __init__(self, cdata, dataItemId, type, sequence, timestamp, name=None, subType=None, nativeCode=None, navtiveSeverity=None, qualifier=None, statistic=None):
         # Attributes dictionary.
        self.attributes = {"dataItemId":dataItemId,
                           "sequence":sequence,
                           "timestamp":timestamp,
                           "name":name, "subType":subType,
                           "nativeCode":nativeCode,
                           "nativeSeverity":nativeSeverity,
                           "qualifier":qualifier,
                           "statistic":statistic
                          }
        self.cdata = cdata
    # end init
    
    # @function: 
    def encode(self):
        print "MTC Stream Condition.encode"
    # end encode
# end MTCStreamCondition
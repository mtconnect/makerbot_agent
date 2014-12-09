#Processor
There are many flavors of gcode created by many programs.  To keep makerbot_driver manageable, we can only handle a subset of those commands well.  In order to allow greater compatiblity, makerbot_driver has a set of processors to convert many common gcode flavors into a gcode twhich makerbot_driver can easily use. 

##Adding Processors
We encourage users to add processors of their own into s3g.  We will accept any processor with 'example_' as a name, with without tests.  We will only accept as processor as'ProcessorX' if it has excellent unit test coverage, comparbile to other Processors.

##Callbacks
GcodeProcessors support callback functions!  The process_gcode function takes a callback function as an optional keyword parameter.  If set, the GcodeProcessor will call that function periodically with an updated percent value as an integer.

##Architecture
All processors should inherit from the Processor python class in makerbot_driver/GcodeProcessors/.  For processors without strong test coverage, please name them example_ProcessorXYZ. With complete coverage, we will upgrade them to simply ProcessorXYZ.  See tests directory for unit test examples. 

The processor class has only two functions which all inheritors must implement:

###__init__(self)
The main constructor.

###process_gcode(self, gcodes)
The main function for a Processor.  Takes one parameter: a list of gcodes to process.
Returns a list of processed gcodes.

    * @param gcodes: The list of gcodes to process
    * @return output: The processed gcodes

#Inheritance Relationships
While all GcodeProcessors inherit from the main Processor, there are several additional Inheritance Relationships that current Preprocessors descend from (that a user could invoke).
##LineTransformProcessor
The Processor uses a dictionary named "code_map" that maps regular expressions to functions.  When process_gcode is called, the Procssor will iterate over all lines of gcode and, if a regex match is found, passes the current line into the mapped function.

NB: Only the first regex match is found, subsequent ones will not be executed.
##BundleProcessor
Inherits from LineTransformProcessor.  Processors that inherit this are expected to define a list (self.processors).  The super class will then compile those processors into one single processor that will do one pass and transform all lines.  This processor also has the option to insert ProgressUpdates.

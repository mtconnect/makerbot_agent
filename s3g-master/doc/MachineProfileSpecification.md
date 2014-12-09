#Maching Profiles
Machine Profiles are how we learn information about the machine at run time.  Differing machines have differing attributes, such as their dimensions and defined axes; these attributes will be defined in their machine profiles.

##Contents
Machine profiles are stored as .json files.  As such, all information is stored in one of two ways: as a dictionary or as an array.  Dictionaries are comprised of keys, where each key has a value, or definition.  Arrays are lists of items that can be accessed individually.  Arrays can store dictionaries; values can be their own separate dictionaries as well.

NB: All of the following items are considered on the same 'level' (as in, they are not nested within each other).

###Machine Type:
  The type of maching you are using (i.e. The Replicator Dual, Thing-O-Matic Dual, etc)

    Key:  "type"
    Value:  Name of the Machine This Profile Describes as a string

###Axes Listing:
  A listing of all axes on this machine.

    Key: "axes"
    Value: A Dictionary Comprised of Different Axes (see "Axis").

###Axis:
  A description for an axis.
  
    Key: Name of this Axis (i.e. "X", "Y", "A")
    Value: A Dictionary of the Following Keys with appropriate Values:
        * Key: "platform_length" 
          Value: The Length of the platform for this axis (NB:It is not necessary for A/B axes to have these values defined
        * Key:"max_feedrate"
          Value: The maximum feedrate this axis can use in mm/min as an integer
        * Key: "steps_per_mm" 
          Value: The number of steps the machine takes to travel 1 mm as an integer

###Tool Listing:
  A Listing of all Tools the Machine can use for Extrusion.

    Key: "tools"
    Value: A Dictonary Comprised of Different Tools (see "Tool")

###Tool:
  A Description for a Tool

    Key: A String of the Index of this Tool (i.e. "0", "1")
    Value: A Dictionary of the Following Keys with appropriate values:
        * Key: "name"
          Value: The name of the tool as a string
        * Key: "model"
          Value: The model number of the tool (i.e. "Mk8") as a string
        * Key: "stepper_axis"
          Value: The stepper axis this tool uses to extrude (i.e. "A', "B") as a string

###Heated Platforms Listing:
  A Listing of all Heated Platforms this Machine can use.

    Key: "heated_platforms"
    Value: A Dictionary Comprised of Different Heated Platforms (see "Heated Platform")

###Heated Platform:
  A Description for a Heated Platform

    Key: A String of the Index of this Heated Platform (i.e. "0")
    Value: A Dictionary of the Following Keys with appropriate values:
        * Key: "name"
          Value: The name of the heated platform as a string

###Baudrate:
  The Baudrate that this machine communicates at

    Key: "baudrate"
    Value: An Integer Value this Machine Communicates At

###Print Start Sequence:
  The Gcode Commands that will be Executed Immediately Prior to Printing

    Key: "print_start_sequence"
    Value: An Array of Strings that are Gcode Commands

###Print End Sequence:
  The Gcode Commands that will be Executed Immediately After Printing

    Key: "print_end_sequence"
    Value: An Array of Strings that are Gcode Commands

###Find Axis Minimum Timeout:
  The Timeout used when the Machine Attempts to Find the Axis Minimum.

    Key: "find_axis_minimum_timeout"
    Value: An Integer Value of this timeout in seconds 

###Find Axis Maximum Timeout:
  The Timeout used when the Machine Attempts to Find the Axis Maximum.

    Key: "find_axis_maximum_timeout"
    Value: An Integer Value of this timeout in seconds

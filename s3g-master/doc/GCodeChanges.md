#GCode changes
There have been several changes made to the Makerbot Flavor of GCode that need to be enumerated for sanity's sake.

##State Machine Changes
###Losing The Location
The following commands will make the Gcode Parser lose its location:

    * G161
    * G162
    * M132

###Tool Changes
Previously, whenever the Gcode Parser encountered a T command, the internal Gcode State Machine would be updated with that tool_index, and a change_tool command would be sent to the machine.  This caused an excessive amount of bloat to the parser, so we now only change the tool_index and send a change_tool command to the machine is we receive the new M135 change_tool command.  However, due to our need to support E commands, we still update the Gcode State Machine's tool_index.

###Mandatory T codes
All G and M codes that include a T code must now include that code.  If excluded, a MissingCodeError will be thrown.

##Gcode Changes
###M161 Find Axes Minimums
Change

    When executing a G161 command, the F code is compared against each maximum feedrate thats being moved.  If any maximum feedrate is less than the desired feedrate, we use that maximum feedrate and associated steps_per_mm constant to calculate the DDA speed.


###M126 Enable Extra Output

Addition

    This command was previously called Enable Valve.  There has been a general namespace change, and there are no longer 'valves' on machines, but instead extra outputs.  Thus, this command has been renamed to Enable Extra Output.

Removal

    None.

###M127 Disable Extra Output 

Addition

    This command was previously called Disable Valve.  There has been a general namespace change, and there are no longer 'valves' on machines, but instead extra outputs.  Thus, this command has been renamed to Disable Extra Output.

Removal

    None.

###M162 Find Axes Maximums
Change

    When executing a G162 command, the F code is compared against each maximum feedrate thats being moved.  If any maximum feedrate is less than the desired feedrate, we use that maximum feedrate and associated steps_per_mm constant to calculate the DDA speed.

##Gcode Command Additions
###M133 Wait For Tool Ready
Reason for Addition:

    The M6 code is a generic Wait For Tool command that will wait for all tools with a given index to heat up.  This command was deemed too open ended, and bifurcated into a Wait For Tool command and a Wait For Platform command.

###M134 Wait For Platform Ready
Reason for Addition:

    The M6 code is a generic Wait For Tool command, that will wait for all tools with a given index.  This command was deemed too open ended, and bifurcated into a Wait For Tool command and a Wait For Platform command.

###M135 Change Tool
Reason For Addition:

    There was never an explicit Change Tool command, so this needed to be added.

##Gcode Command Removals
###G0 Rapid Positioning
Status:

    This code has been totally removed, and will throw an error if used.

Funtionality:

    This code moved the machine to a specified position at the axis' maximum feedrate.

Reason for Removal:

    This code took the same code path as the G1 command, and only differed by using a baked in constant written into the machine profile.  Due to its redundancy, it was removed.

###G21 Programming in Milimteres
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    S3g's parser only supports programming in milimeters, so this code was not necessary.

###G90 Absolute Programming
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    S3g's parser only supports absolute programming, so this code was not necessary.

###M6 Wait For Toolhead
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This code used to be a generic Wait For Toolhead command, that would wait for both a platform and a toolhead.  This funcationality was broken out into two separate commands (M133/134), which will wait for a Tool or a Platform, respectively.

###M101 Extruder On Forward
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This command is an RPM command.  We do not support RPM commands.

###M102 Extruder On Reverse
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This command is an RPM command.  We do not support RPM commands.

###M103 Extruder Off
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This command is an RPM command.  We do not support RPM commands.

###M105 Get Temperature
Status:

    This code has been totally removed, and will throw an error if used.

Reason for Removal:

    This code is a query command, and should never have been implemented.  It was kept in for skeinforge compatability.

###M108 Set Extruder Speed
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This code used to be the goto method for changing the tool_index (as in, if we wanted to change from tool_index 0 to 1, we would add an M108 command with a defined T code.  This is using the code for an unintended purpose, so after moving away from that paradigm, this command was reduced to an RPM command.  S3g's parser can only handle 5d commands and not RPM commands, so this command was removed.


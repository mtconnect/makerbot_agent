# GCODE engine

We support a limited GCODE interpreter, for the purpose of printing files generated from Skeingforge and Miracle Grue. There are many possible ways that gcode files can be mapped into s3g, and this interpreter aims for simplicity and testability.

These are the rules for this interpreter:

* At most 1 G or M Code per Command
* Codes are only applied to the Command that they belong to.
* Commands may update the interpreter state machine
* Commands must not include extraneous Codes (checking is not yet implemented)
* Only absolute positioning in milimeter mode are supported

The interpreter state machine stores these states:

* Machine position (x,y,z,a,b)
* Offset register (1, 2)
* Toolhead index (0, 1)
* Toolhead RPM
* Toolhead direction
* Toolhead enable state
* Last Feedrate Given (This is done because skeinforge has a weird quirk where it specified a feedrate on one line, then gives an E command on another without a feedrate)
* Last Timeout Used for WaitForPlatform or WaitForToolhead

## Definitions

Here is some vocabulary, that should be used when talking about the protocol:

<table>
<tr>
 <th>Name</th>
 <th>Definition</th>
 <th>Example</th>
</tr>
<tr>
 <td>Command</td>
 <td>A command is a single line of gcode. Commands consist of 0 or more codes, and 0 or more comments</td>
 <td>G1 X23 Y10 (Move to new position)</td>
</tr>
<tr>
 <td>Code</td>
 <td>Codes are letter-value pairs that occur in a command. The meaning of each code is specific to the command being parsed. They differ from flags in that flags do not have a value associated with them.</td>
 <td>T1</td>
</tr>
<tr>
 <td>Flag</td>
 <td>Flags are standalone letters that occur in a command. Flags are used to signal which parameters should be affected by a command. They are primarily used to enable or disable axes.</td>
 <td>X</td>
</tr>
<tr>
 <td>Comment</td>
 <td>A comment is a user readable block of text used to clarify what a section of code does. Comments are also used by some commands to specify a filename or message that should be displayed on a machine's interface LCD.
 <td>(embedded comment) G1 ;This G1 is a comment</td>
</tr>
<tr>
 <td>Variable</td>
 <td>A variable is a placeholder in a line of gcode that can be replaced by a value during run time.  Variables can be anywhere in the entirety of the line of Gcode.  A variable can be a string of any size, but must be prefixed by a '#' sign.<td>
<td>#0, #TEMPERATURE, #FOO</td>
</tr>
</table>

## References
Supported commands were extracted from [gcode files](https://github.com/makerbot/s3g/tree/master/doc/gcode_samples) that were created in both Skeinforge and Miracle Grue.

Hints about what the commands are expected to do were extracted from ReplicatorG's [gcode parser](https://github.com/makerbot/ReplicatorG/blob/master/src/replicatorg/app/gcode/GCodeParser.java).

State Diagram of GCode Parsing:

![gcode state diragram](https://github.com/makerbot/s3g/raw/master/doc/GcodeStateMachine.png)

State Diagram of MCode Parsing:

![mcode state diagram](https://github.com/makerbot/s3g/raw/master/doc/MCodeStateMachine.png)

# Parser

## Comments
Both semicolon ; and parens () style comments are supported. If multiple comments are present on a line, they are extracted and combined into a single comment. Comments are parsed using the following rules:

* Semicolons are evaluated first; anything to the right of the semicolon in unconditionally considered a comment (including additional semicolons, and parentheses)
* Nested parentheses are accepted. The data inside of the nested parentheses are added to the comment, while the parentheses characters are not.
* An unclosed opening parenthesis is accepted. Everything to the right of the parenthesis is treated as a comment.
* A closing paren that was not preceeded by an opening parenthesis is an error.
* Properly formatted comments are allowed at any place in a command.

## Commands
These are the rules used to parse commands:

* Each line must have either a G or M code, 0 or more other codes, 0 or more flags, and 0 or more comment sections.
* Comments are parsed and extracted before evaluating the codes and flags.
* Each code and flag must be separated by whitespace.
* If a code value contains a decimal place, it must use a period to demarcate this.
* Upper and lower case codes and flag names are accepted, and will silently be converted to uppercase.
* Each G and M code has a list of required and optional codes and flags. Codes and flags that are not supported by the G or M code are considered an error.

## Variable Substitution
The gcode parser has an internal variable, called an environemnt.  The environment is a python dict that defines all variables encased in a Gcode File.  During Line Execution, prior to parsing out the comments/commands, all variables defined in the environment are replaced by their defined value.  If any variables present in a line of Gcode are undefined in the environment, the parser will throw an UndefinedVariableError.  While variables contained within the line of Gcode must be prefixed by a '#', the variables defined in the environment do not need to be delineated (i.e. The variable '#FOO' is defined as 'FOO' in the environment).

NB: The environment defaults to an empty python dict.

# Supported G Codes

## G1 - Linear interpolation
Move to the specified position at the current or specified feedrate.
NB: There are two methods of forming the G1 command:

    XYZABF: This gives explicit axes positions for XYZAB, in mm
    XYZE: This gives explicit axes positions for XYZ, and an E command which is mapped
      to either A or B, depending on the current tool index being used.

We should only accept one form or the other.  A mixture will result in an error being thrown.

XYZABF Form:

NB: While we _can_ accept both A and B axes, because they both have their own
unique offsets, we can only process one of these commands.  We will throw an
error if receive both an A and B command.

Registers

     X: (code, optional) If present, new X axis position, in mm
     Y: (code, optional) If present, new Y axis position, in mm
     Z: (code, optional) If present, new Z axis position, in mm
     A: (code, optional) If present, new A axis position, in mm
     B: (code, optional) If present, new B axis position, in mm
     F: (code, optional) Feedrate, in mm/min

S3g Output

    queue_extended_point(point, rate)

Parameters

    point = [x, y, z, a, b]
    rate = F

XYZEF Form:

Registers

    X: (code, optional) If present, new X axis position, in mm
    Y: (code, optional) If present, new Y axis position, in mm
    Z: (code, optional) If present, new Z axis position, in mm
    E: (code, optional) If present, new A/B (depending on internal state machine) axis position, in mm 
    F: (code, optional) Feedrate, in mm/min

S3g Output

    queue_extended_point(point, rate)

Parameters

    point = [x, y, z]
    rate = F

## G4 - dwell
Tells the machine to pause for a certain amount of time.

Registers

    P: (code) dwell time, in ms

S3g Output

    delay(delay)

Parameters
    
    delay = P

## G92 - Position register: Set the specified axes positions to the given position
Sets the position of the state machine and the bot.
NB: There are two methods of forming the G92 command:

    XYZAB: This gives explicit axes positions for XYZAB, in mm
    XYZE: This gives explicit axes positions for XYZ, and an E command which is mapped
      to either A or B, depending on the current tool index being used.

We should only accept one form or the other.  A mixture will result in an error being thrown.

XYZAB Form:

Registers

    X: (code, optional) If present, new X axis position, in mm
    Y: (code, optional) If present, new Y axis position, in mm
    Z: (code, optional) If present, new Z axis position, in mm
    A: (code, optional) If present, new A axis position, in mm
    B: (code, optional) If present, new B axis position, in mm

S3g Output

    set_extended_position(position)

Parameters

    position = [x, y, z, a, b]

XYZE Form:

Registers

    X: (code, optional) If present, new X axis position, in mm
    Y: (code, optional) If present, new Y axis position, in mm
    Z: (code, optional) If present, new Z axis position, in mm
    E: (code, optional) If present, new A/B (depending on internal state machine) axis position, in mm 

S3g Output

    set_extended_position(position)

Parameters

    position = [x, y, z, a, b]


## G130 - Set digital potentiometer value
Set the digital potentiometer value for the given axes. This is used to configure the current applied to each stepper axis. The value is specified as a value from 0-127; the mapping from current to potentimeter value is machine specific. (TODO: Specify what it is for the MightyBoard)

Registers

    X: (code, optional) If present, X axis potentimeter value
    Y: (code, optional) If present, Y axis potentimeter value
    Z: (code, optional) If present, Z axis potentimeter value
    A: (code, optional) If present, A axis potentimeter value
    B: (code, optional) If present, B axis potentimeter value

S3g Output

    set_potentiometer_value(axes, val)

Parameters

    For Each Set Of Different Pot Values:
      val = Value
      axes = Axes With The Same Value

## G161 - Home given axes to minimum
Instruct the machine to home the specified axes to their minimum position.

Registers

    F: (code) Desired feedrate (mm/min) for this command
    X: (flag, optional) If present, home the x axis to its minimum position
    Y: (flag, optional) If present, home the y axis to its minimum position
    Z: (flag, optional) If present, home the z axis to its minimum position

S3g Output

    find_axes_minimums(axes, feedrate, timeout)

Parameters

    axes = List Of All Present Axes
    feedrate = The calculated DDA speed for F.  We always use the minimum feedrate (relative to the desired feedrate and maximum feedrates of all homing axes) and the limiting axis' spm constant.  If no limiting axis is present, we default to the first axis' spm constant.
    timeout = Timeout specified in the machine profile

## G162 - Home given axes to maximum
Instruct the machine to home the specified axes to their maximum position.

Registers

    F: (code) Desired feedrate (mm/min) for this command
    X: (flag, optional) If present, home the x axis to its maximum position
    Y: (flag, optional) If present, home the y axis to its maximum position
    Z: (flag, optional) If present, home the z axis to its maximum position

S3g Output

    find_axes_maximums(axes, feedrate, timeout)

Parameters

    axes = List Of All Present Axes
    feedrate = The calculated DDA speed for F.  We always use the minimum feedrate (relative to the desired feedrate and maximum feedrates of all homing axes) and the limiting axis' spm constant.  If no limiting axis is present, we default to the first axis' spm constant.
    timeout = Timeout specified in the machine profile

# Supported M Codes

## M18 - Disable axes stepper motors
Instruct the machine to disable the stepper motors for the specifed axes.

Registers

    X: (flag, optional) If present, disable the X axis stepper motor
    Y: (flag, optional) If present, disable the Y axis stepper motor
    Z: (flag, optional) If present, disable the Z axis stepper motor
    A: (flag, optional) If present, disable the A axis stepper motor
    B: (flag, optional) If present, disable the B axis stepper motor

S3g Output

    toggle_axes(axes, False)

Parameters

    axes = List Of All PresentAxes

## M70 - Display message on machine
Instruct the machine to display a message on it's interface LCD.
TODO: Should this generate multiple s3g calls for a long message?

Registers

    P: (code) Time to display message for (TODO: Units?)
    comment: Message to display

S3g Output

    display_message(row, col, message, timeout, clear_existing, last_in_group, wait_for_button)

Parameters

    row = 0
    col = 0
    message = Comment
    timeout = P
    clear_existing = True
    last_in_group = True
    wait_for_button = False

## M72 - Play a tone or song
Instruct the machine to play a preset song. Acceptable song IDs are machine specific.

Registers

    P: (code) ID of the song to play

S3g Output

    queue_song(song_id)

Parameter

    song_id = P

## M73 - Set build percentage
Instruct the machine that the build has progressed to the specified percentage. The machine is expected to display this on it's interface board. If the percentage is exactly 0, then a Build Start Notification is sent. If the percentage is exactly 100, then a Build End notification is sent.

Registers

   P: (code) Build percentage (0 - 100)

S3g Output

    set_build_percent(percent)

Parameters

    percent = P

If Build percentage is exactly 0, the following command is also sent:

Registers (none)

S3g Output

    build_start_notification(build name)

Parameters

    build name

If Build percentage is exactly 100, the following command is also sent:

Registers (none)

S3g Output

    build_end_notification()

Parameters (none)


## M104 - Set toolhead temperature
Set the target temperature for the current toolhead

Registers

    S: (code) Temperature to set the toolhead to, in degrees C
    T: (code) The toolhead to heat

S3g Output

    set_toolhead_temperature(tool_index, temperature)

Parameters

    tool_index = toolhead
    temperature = s

## M109 - Set build platform temperature
Sets the target temperature for the current build platform

Registers

    S: (code) Temperature to set the platform to, in degrees C
    T: (code) The platform to heat

S3g Output

    set_platform_temperature(tool_index, temperature)

Parameters

    tool_index = 0
    temperature = S

## M126 - Enable Extra Output
Enables an extra output attached to a specific toolhead.

Registers

    T: (code) The toolhead that the extra output we want to enable is attached to.

S3g Output

    toggle_extra_output(tool_index, True)

Parameters

    tool_index = T

## M127 - Disable Extra Output 
Disables an extra output attached to a specific toolhead.

Registers

    T: (code) The toolhead that the extra output we want to disable is attached to

S3g Output

    toggle_extra_output(tool_index, False)

Parameters

    tool_index = T

## M132 - Load current home position from EEPROM
Recalls current home position from the EEPROM and waits for the buffer to empty

Registers

    X:  (flag, optional) If present, loads the X offset from the EEPROM
    Y:  (flag, optional) If present, loads the Y offset from the EEPROM
    Z:  (flag, optional) If present, loads the Z offset from the EEPROM
    A:  (flag, optional) If present, loads the A offset from the EEPROM
    B:  (flag, optional) If present, loads the B offset from the EEPROM

S3g Output

    recall_home_positions(axes)

Parameters

    axes = [x, y, z, a, b]

## M133 - Wait For Toolhead
Instruct the machine to wait for the toolhead to reach its target temperature

Registers

    T: (code) The extruder to wait for.
    P: (code, optional) If present, sets the time limit that we wait for.  Otherwise, use a timeout coded into the Gcode State Machine.

S3g Output

    wait_for_tool_ready(tool_index, delay, timeout)

Parameters

    tool_index = T
    delay = 100
    timeout = P

## M134 - Wait For Platform
Instruct the machine to wait for the platform to reach its target temperature

Registers

    T: (code) The platform to wait for.
    P: (code, optional) If present, sets the time limit that we wait for.  Otherwise, use a timeout coded into the Gcode State Machine.

S3g Output

    wait_for_platform_ready(tool_index, delay, timeout)

Parameters

    tool_index = T
    delay = 100
    timeout = P

## M135 - Tool Change
Instructs the machine to change its toolhead.  Also updates the State Machine's current
tool_index.

Registers

    T: (code) The toolhead for the machine to switch to and the new tool_index for
        the state machine to use.

S3g Output

    change_tool(tool_index)

Parameters

    tool_index = T

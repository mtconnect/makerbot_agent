#Deprecated Commands
Here is a list of commands I've found that were in the googledoc specification for the firmware, but have since been deprecated.

##34 - Get Firmware build Name
Retrieve the firmware build name, which is a human-readable string describing the build.  Names should be chosen with an eye towards disambiguating builds targeted for different tools.
Payload length limitations restrict the field to 31 characters
Payload (0 bytes)
Response (N+1)
char[N+1]: a nullterminated string representing the buildname

##36 - Get Tool Status
While the command is implemented, the PORF, EXTRF, BORF, WDRF flags are now deprecated

##23 - Get Motherboard Status
While the command is implemented, the PORF, EXTRF, BORF, WDRF flags are now deprecated

##8 - Set Motor Direction
This command has been superseded by Enable/Disable stepper motor

##38 - Set Motor 1 Speed DDA
We are considering this command deprecated, but some folks with stepper motors on gen 3 systems use it, so we are keeping it in as a reminder

##15 - Set Servo 2 Position
Set the position of a servo connected to the second servo output
uint8: Desired angle 0-180

##40 - LightIndicatorLED
This command was only used on the assembly lines for TOMs, so we are going to deprecate it

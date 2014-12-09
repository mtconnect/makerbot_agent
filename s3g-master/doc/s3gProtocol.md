# S3G protocol (formerly RepRap Generation 3 Protocol Specification)

## Overview

This document describes the s3g protocol, which is used to communicate with Makerbots and similar CNC machines. It is intended to help developers who wish to communicate with a machine directly, or create their own devices that speak over the protocol. If all you want to do is control a machine, we recommend using the [s3g library](http://github.com/makerbot/s3g), which is a Python implementation of the protocol.

The first part of the document covers some definitions that are used to describe this system. We recommend you at least skim through them, so we can be sure we are talking about the same things.

The second part of the document talks about the architecture that the s3g protocol was designed for. It's useful for understanding how the different pieces of hardware are connected, and what each part does.

The third part of the document talks about the fine details of how commands are routed through the system, and what happens if there is an error when sending one. It's useful for understanding how to make your own 

The final portion of the document is a catalog of all of the commands that the Host and Tools can implement.

## Implementations of this protocol

Firmware repositories:

* For Gen3 and Gen4 electronics (Cupcake, Thing-O-Matic, Reprap): [G3Firmware](http://github.com/makerbot/G3Firmware)
* For Mightyboard (Replicator): [MightyBoardFirmware](http://github.com/makerbot/MightyBoardFirmware)

Host software:

* [ReplicatorG](http://github.com/makerbot/ReplicatorG)
* [pyS3g](http://github.com/makerbot/s3g)

## Definitions

Here is some vocabulary that should be used when talking about the protocol:

<table>
<tr>
 <th>Name</th>
 <th>Definition</th>
</tr>
<tr>
 <td>PC</td>
 <td>A computer, that is connected to the Host over the host network.</td>
</tr>
<tr>
 <td>Host</td>
 <td>The motherboard on the machine. This communicates with the PC over the host network, and with 0 or more tools over the tool network. The host can control 3-5 stepper motors, read endstops, read and write to an SD card, and control an interface board.</td>
</tr>
<tr>
 <td>Tool</td>
 <td>An auxiliary motherboard on the machine, This communicates with the Host over the tool network, and controls one toolhead (extruder). The Tool can have a toolhead heater, platform heater, fan, extruder motor, and other things attached to it. On the Mightyboard, the Tool is simulated inside of the motherboard, and doesn't exist as a separate piece.</td>
</tr>
<tr>
 <td>Host network</td>
 <td>The host network is the serial connection between the PC and the Host. The physical bus is RS232 (using a USB<->serial adaptor), running at 115200 baud (Gen4, MightyBoard) or 38400 baud (Gen3).</td>
</tr>
<tr>
 <td>Tool network</td>
 <td>The tool network is the serial connection between the Host and 0 or more Tools. The physical bus is RS485, half-duplex, running at xxx baud (Gen3, Gen4), or virtual (MightyBoard).</td>
</tr>
<tr>
 <td>Tool ID</td>
 <td>A unique address that is assigned to each Tool, that allows it to be addressed individually by the Host. Valid Tool IDs are 0-126. It is recommended to use 0 for the first Tool, and 1 for the second Tool.</td>
</tr>
<tr>
 <td>Query Command</td>
 <td>A query command is a command that should be evaluated and acknowledged immediately. They are used for things such as setting or reading temperatures.</td>
</tr>
<tr>
 <td>Buffered Command</td>
 <td>A buffered command should be acknowledged immediately, but the Host or Tool may choose to store it in a buffer for later execution. These should be used for commands that could take a long time to execute, such as motion commands.
</tr>
</table>

# Architecture

An s3g system looks like this:

![block diagram of system architecture](https://github.com/makerbot/s3g/raw/master/doc/SystemArchitecture.png)

There are two networks, the host network and the tool network. Both networks (host, tool) have a single network master. On the host network, this is a PC, and on the tool network, this is the Host. The host network must have one slave device (the Host), and the tool network can have one or more slave devices (Tool N).

_Note: On the MightyBoard, the tool bus is emulated in software in order to be backwards compatible._

## Normal communication

All communication is initiated by the network master sending a single packet over the network, which contains either a query command or buffered command. If the slave device receives the packet, it must respond with a single packet, containing a response code and any response data.

This is what a normal communication over the host network looks like:

![host command success](https://github.com/makerbot/s3g/raw/master/doc/HostCommandSuccess.png)

Communication over the tool network works similarly:

![tool command success](https://github.com/makerbot/s3g/raw/master/doc/ToolCommandSuccess.png)

Finally, a PC may communicate with a Tool by forwarding a packet through the Host:

![host tool command success](https://github.com/makerbot/s3g/raw/master/doc/HostToolCommandSuccess.png)

The slave device is expected to begin responding to a master command within 40ms of receiving it. This is currently broken for a number of commands in actual systems. If a slave takes too long to respond to a command, then the trasmission is to be considered a timeout. _Note: Many commands in the current implementation break this requirement, and no known PC implementation enforces it._

## Handling Errors

Of course, communication is not always so rosy. There are a number of things that could prevent a successful transmission, such as electrical noise or busy firmware. The protocol uses two methods to protect against this: a CRC check at the end of every packet, and a timeout counter while receiving data.

The master is allowed to attemt re-transmission if and only if it receives two specific types of errors.  The first type of error is the Retryable error.  If the master receives a Retryable Error, it may retry sending the current packet up to 5 times.  Several types of errors are considered "Retryable": transmission timeouts, Packet Decode errors (indicative of a malformed packet), CRC Errors indicating a discrepency between master and machine, and Generic Machine errors all inherit from Retryable Error.  After 5 Retryable Errors are raised, s3g throws a Transmission Error and terminates.  The second type of error that allows for re-transmission is the BufferOverflowError.  There is no limit to the number of Buffer Overflow Errors a machine can receive.

Here is a reference implementation of a packet send state machine:

![send_command state machine diagram](https://github.com/makerbot/s3g/raw/master/doc/send_command.png)


# Packet formats

## Packet Structure
All packets have the following structure:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Start Byte</td>
 <td>This byte always has the value 0xD5 and is used to ensure synchronization.</td>
</tr>
<tr>
 <td>1</td>
 <td>Length</td>
 <td>The length of the payload, in bytes</td>
</tr>
<tr>
 <td>2..(1+N)</td>
 <td>Payload</td>
 <td>The packet payload. The payload can be N bytes long (TODO: maximum length?).</td>
</tr>
<tr>
 <td>2+N</td>
 <td>CRC</td>
 <td>The <a href="http://www.maxim-ic.com/app-notes/index.mvp/id/27">8-bit iButton/Maxim CRC</a> of the payload</td>
</tr>
</table>

## Host Network Payload Structure
The payload of a packet sent over the master network contains one command. Each command consists of a command code, and 0 or more arguments:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Host Command Code</td>
 <td>A byte representing the host command to be executed. Codes with a value from 0-127 are considered query commands, and codes with a value from 128-255 are considered action commands.</td>
</tr>
<tr>
 <td>1..(1+N)</td>
 <td>Arguments</td>
 <td>(optional) Command arguments, such as a position to move to, or a flag to set. Command specific.</td>
</tr>
</table>

## Tool Network Payload Structure
The payload of a packet sent over the tool network contains one command. Each command consists of a Tool ID, a command code, and 0 or more arguments:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Tool ID</td>
 <td>The ID of the tool device being addressed (see below)</td>
</tr>
<tr>
 <td>1</td>
 <td>Command Code</td>
 <td>A byte representing the command to be executed. Unlike host commands, tool command values have no special meaning.</td>
</tr>
<tr>
 <td>2..(2+N)</td>
 <td>Arguments</td>
 <td>(Optional) Command arguments, such as a position to move to, or a flag to set. Command specific.</td>
</tr>
</table>

A note about Tool IDs:

The tool ID is the ID number of a toolhead. A toolhead may only respond to commands that are directed at its ID. If the packet is corrupt, the tool should *not* respond with an error message to avoid collisions.

The exception to this is the tool ID 127. This represents any listening device. The address 127 should only be used when setting the ID of a tool.

_Note: Before firmware version 2.92, the broadcast address was 255._

## Response Packet Structure (both Host and Tool Networks)
The response payload contains the response to a single command:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Response Code</td>
 <td>A byte representing the completion status of the command (see below)
</tr>
<tr>
 <td>1..(1+N)</td>
 <td>Arguments</td>
 <td>(Optional) Response arguments, such as current machine position or toolhead temperature. Command specific.</td>
</tr>
</table>

Response code values can be as follows:

<table>
<tr>
 <th>Response Code</th>
 <th>Details</th>
 <th>Can be retried?</th>
</tr>
<tr>
 <td>0x80</td>
 <td>Generic Packet error, packet discarded</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x81</td>
 <td>Success</td>
 <td>No</td>
</tr>
<tr>
 <td>0x82</td>
 <td>Action buffer overflow, entire packet discarded</td>
 <td>No</td>
</tr>
<tr>
 <td>0x83</td>
 <td>CRC mismatch, packet discarded.</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x84</td>
 <td>Query packet too big, packet discarded </td>
 <td>No</td>
</tr>
<tr>
 <td>0x85</td>
 <td>Command not supported/recognized</td>
 <td>No</td>
</tr>
<tr>
 <td>0x87</td>
 <td>Downstream timeout</td>
 <td>No</td>
</tr>
<tr>
 <td>0x88</td>
 <td>Tool lock timeout</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x89</td>
 <td>Cancel build</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x8A</td>
 <td>Bot is Building from SD</td>
 <td>No</td>
</tr>
<tr>
 <td>0x8B</td>
 <td>Bot is shutdown due to Overheat</td>
 <td>No</td>
</tr>
<tr>
 <td>0x8C</td>
 <td>Packet timeout error, packet discarded</td>
 <td>Yes</td>
</tr>

</table>

_Historical note: Firmware versions prior to 2.9 did not have the high bit set for error codes. This was changed to avoid having the response code conflict with tool indexes on the tool network_ 

# Data formats

## Integer
Integers represent numbers. All integers are in little endian format.

<table>
<tr>
 <th>Type</th>
 <th>Size</th>
 <th>Range</th>
</tr>
<tr>
 <td>uint8</td>
 <td>1 byte</td>
 <td>0 to 255</td>
</tr>
<tr>
 <td>uint16</td>
 <td>2 bytes</td>
 <td>0 to 65535</td>
</tr>
<tr>
 <td>int16</td>
 <td>2 bytes</td>
 <td>-32768 to 32767</td>
</tr>
<tr>
 <td>uint32</td>
 <td>4 bytes</td>
 <td>0 to 4294967296</td>
</tr>
<tr>
 <td>int32</td>
 <td>4 bytes</td>
 <td>-−2147483648 to 2147483647</td>
</tr>
</table>

## Axes bitfield
An axes bitfield structure is used to represent a selection of axes.

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>5</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>4</td>
 <td>B axis</td>
</tr>
<tr>
 <td>3</td>
 <td>A axis</td>
</tr>
<tr>
 <td>2</td>
 <td>Z axis</td>
</tr>
<tr>
 <td>1</td>
 <td>Y axis</td>
</tr>
<tr>
 <td>0</td>
 <td>X axis</td>
</tr>
</table>

## SD Response codes
<table>
<tr>
 <th>Response Code</th>
 <th>Details</th>
</tr>
<tr>
 <td>0x00</td>
 <td>Operation successful</td>
</tr>
<tr>
 <td>0x01</td>
 <td>SD Card not present</td>
</tr>
<tr>
 <td>0x02</td>
 <td>SD Card initialization failed</td>
</tr>
<tr>
 <td>0x03</td>
 <td>Partition table could not be read</td>
</tr>
<tr>
 <td>0x04</td>
 <td>Filesystem could not be opened</td>
</tr>
<tr>
 <td>0x05</td>
 <td>Root directory could not be opened</td>
</tr>
<tr>
 <td>0x06</td>
 <td>SD Card is locked</td>
</tr>
</table>

# Host Query Commands

## 00 - Get version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.  If the returned version number is greater than 5.5, the host has the option of requesting advanced version information with command #27

Payload

    uint16: Host Version

Response

    uint16: Firmware Version

## 01 - init: Initialize firmware to boot state
Initialization consists of:

    * Resetting all axes positions to 0
    * Clearing command buffer

Payload (0 bytes)

Response (0 bytes)

## 02 - Get available buffer size: Determine how much free memory is available for buffering commands
This command will let us know how much buffer space we have available for action commands. It can be used to determine if and when the buffer is available for writing. If we are writing to the SD card, it will generally always report the maximum number of bytes available.

Payload (0 bytes)

Response

    uint32: Number of bytes availabe in the command buffer

## 03 - Clear buffer: Empty the command buffer
This command will empty our buffer, and reset all pointers, etc to the beginning of the buffer. If writing to an SD card, it will reset the file pointer back to the beginning of the currently open file. Obviously, it should halt all execution of action commands as well.

Payload (0 bytes)

Response (0 bytes)

## 07 - Abort immediately: Stop machine, shut down job permanently
This function is intended to be used to terminate a print during printing. Disables steppers, heaters, and any toolheads, and clears all command buffers.

Payload (0 bytes)

Response (0 bytes)

## 08 - pause/resume: Halt execution temporarily
This function is inteded to be called infrequently by the end user in order to make build-time adjustments during a print. It differs from 'Abort Immediately', in that the command buffers and heaters are not disabled.

On pause, it stops all stepper movement and halts extrusion.
On Resume, it restarts extrusion and resumes movement.

Payload (0 bytes)

Response (0 bytes)

## 10 - Tool query: Query a tool for information
This command is for sending a query command to the tool. The host firmware will then pass the query along to the appropriate tool, wait for a response from the tool, and pass the response back to the host. TODO: Does the master handle retries?

Payload

    uint8: Tool index 
    0-N bytes: Payload containing the query command to send to the tool.

Response

    0-N bytes: Response payload from the tool query command, if any.

## 11 - Is finished: See if the machine is currently busy
This command queries the machine to determine if it currently executing commands from a command queue.

Payload (0 bytes)

Response

    uint8: 0 if busy, 1 if finished.

## 12 - Read from EEPROM
Read the specified number of bytes from the given offset in the EEPROM, and return them in a response packet. The maximum read size is 31 bytes.

Payload

    uint16: EEPROM memory offset to begin reading from
    uint8: Number of bytes to read, N.

Response

    N bytes: Data read from the EEPROM

## 13 - Write to EEPROM
Write the given bytes to the EEPROM, starting at the given offset.

Payload

    uint16: EEPROM memory offset to begin writing to
    uint8: Number of bytes to write
    N bytes: Data to write to EEPROM

Response

    uint8: Number of bytes successfully written to the EEPROM

## 14 - Capture to file
Capture all subsequent commands up to the 'end capture' command to a file with the given name on the SD card. The file will be stored in the root of the fat16 filesystem on the SD card. The maximum file name length permitted is 12 characters, including the '.' and file name extension.

Payload

    1+N bytes: Filename to write to, in ASCII, terminated with a null character. N can be 1-12 bytes long, not including the null character.

Response

    uint8: SD response code

## 15 - End capture to file
Complete an ongoing file capture by closing the file, and return to regular operation.

Payload (0 bytes)

Response

    uint32: Number of bytes captured to file.

## 16 - Play back capture
Play back a file containing a stream of captured commands. While the macine is in playback mode, it will only respond to pause, unpause, and stop commands.

Payload

    1+N bytes: Filename to play back, in ASCII, terminated with a null character. N can be 1-12 bytes long, not including the null character.

Response

    uint8: SD response code

## 17 - reset
Call a soft reset. This calls all reset functions on the bot. Same as abort.

Payload (0 bytes)

Response (0 bytes)

## 18 - Get next filename
Retrieve the volume name of the SD card or the next valid filename from the SD card. If a non-zero value is passed to the 'restart' parameter, the file list will begin again from the start of the directory. The file list state will be reset if any other SD operations are performed. 
If all the filenames have been retrieved, an empty string is returned.

Payload

    uint8: 0 if file listing should continue, 1 to restart listing.

Response

    uint8: SD Response code
    1+N bytes: Name of the next file, in ASCII, terminated with a null character. If the operation was unsuccessful, this will be a null character.

## 20 - Get build name
Retrieve the name of the file currently being built. If the machine is not currently printing, a null terminated string of length 0 is returned. If the bot has finished a print and has not been reset (hard or soft), it will return the name of the last file built.

Payload (0 bytes)

Response

    1+N bytes: A null terminated string representing the filename of the current build.

## 21 - Get extended position: Get the current 
Retrieve the curent position of all axes that the machine supports. Unsupported axes will return 0

Payload (0 bytes)

Response

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    int32: A position, in steps
    int32: B position, in steps
    uint16: bitfield corresponding to the endstop status:

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>15</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>14</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>13</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>12</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>11</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>10</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>9</td>
 <td>B min switch pressed</td>
</tr>
<tr>
 <td>8</td>
 <td>B max switch pressed</td>
</tr>
<tr>
 <td>7</td>
 <td>A max switch pressed</td>
</tr>
<tr>
 <td>6</td>
 <td>A min switch pressed</td>
</tr>
<tr>
 <td>5</td>
 <td>Z max switch pressed</td>
</tr>
<tr>
 <td>4</td>
 <td>Z min switch pressed</td>
</tr>
<tr>
 <td>3</td>
 <td>Y max switch pressed</td>
</tr>
<tr>
 <td>2</td>
 <td>Y min switch pressed</td>
</tr>
<tr>
 <td>1</td>
 <td>X max switch pressed</td>
</tr>
<tr>
 <td>0</td>
 <td>X min switch pressed</td>
</tr>
</table>

## 22 - Extended stop: Stop a subset of systems
Stop the stepper motor motion and/or reset the command buffer. This differs from the reset and abort commands in that a soft reset of all functions is not called

Payload

    uint8: Bitfield indicating which subsystems to shut down. If bit 0 is set, halt all stepper motion. If bit 1 is set, clear the command queue.

Response

    int8: 0 (reserved for future use)


## 23 - Get motherboard status
Retrieve some status information from the motherboard

Payload (0 bytes)

Response

    uint8: Bitfield containing status information (see below)

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>POWER_ERRPR</td>
 <td>An error was detected with the system power. For Gen4 electronics, this means ATX_5V is not present</td>
</tr>
<tr>
 <td>6</td>
 <td>HEAT_SHUTDOWN</td>
 <td>Heaters were shutdown after 30 minutes of inactivity</td>
</tr>
<tr>
 <td>5</td>
 <td>BUILD_CANCELLING</td>
 <td>Watchdog reset flag was set at restart</td>
</tr>
<tr>
 <td>4</td>
 <td>WAIT_FOR_BUTTON</td>
 <td>BotUI is waiting for button push by user</td>
</tr>
<tr>
 <td>3</td>
 <td>ONBOARD_PROCESS</td>
 <td>Bot is running an onboard process (the difference between an onboard script and an onboard process is important to the bot, but is not important to the s3g host)</td>
</tr>
<tr>
 <td>2</td>
 <td>ONBOARD_SCRIPT</td>
 <td>Bot is running an onboard script</td>
</tr>
<tr>
 <td>1</td>
 <td>MANUAL_MODE</td>
 <td>Manual move mode active</td>
</tr>
<tr>
 <td>0</td>
 <td>PREHEAT</td>
 <td>Onboard preheat active</td>
</tr>
</table>

## 24 - Get build statistics
Gathers statistics about the currently building print if a build is active, or the last print if there is no active build

Payload (1 byte)

Response

    uint8 : Build State (paused, running, finished_normally, canceled, none)
    uint8 : Hours elapsed on print
    uint8 : Minutes elapsed on print (add hours for total time)
    uint32: Line Number (number of commands processed)
    uint32: Reserved for Future Use

Build State Return Values are as follows
<table>
<tr>
  <td>0</td>
  <td>no build initialized (boot up state)</td>
</tr>
<tr>
  <td>1</td>
  <td>build running</td>
</tr>
<tr>
  <td>2</td>
  <td>build finished normally</td>
</tr>
<tr>
  <td>3</td>
  <td>build paused</td>
</tr>
<tr>
  <td>4</td>
  <td>build cancelled</td>
</tr>
<tr>
  <td>5</td>
  <td>build sleeping</td>
</tr>
</table>

## 25 - Get communication statistics
Gathers statistics about communication over the tool network. This was intended for use while troubleshooting Gen3/4 machines.

Payload (0 bytes)

Response

    uint32: Packets received from the host network
    uint32: Packets sent over the tool network
    uint32: Number of packets sent over the tool network that were not repsonded to
    uint32: Number of packet retries on the tool network 
    uint32: Number of bytes received over the tool network that were discarded as noise

## 27 - Get advanced version number
returns the main version numbers along with an internal version number

Payload

    uint16: Host Version

Response

    uint16_t Firmware Version
    uint16_t Internal Version
    uint8_t Software Variant, see software variant table for valid IDs
    uint8_t Reserved for future use
    uint16_t Reserved for future use

Sofware Variant IDs are as follows
<table>
<tr>
  <td>0x00</td>
  <td>unknown</td>
</tr>
<tr>
  <td>0x01</td>
  <td>MBI Official</td>
</tr>
<tr>
  <td>0x02-0x7F</td>
  <td>reserved</td>
</tr>
<tr>
  <td>0x80</td>
  <td>Sailfish</td>
</tr>
<tr>
  <td>0x81-0xBF</td>
  <td>unassigned variants</td>
</tr>
<tr>
  <td>0xC0-0xFF</td>
  <td>reserved</td>
</tr>
</table>


# Host Buffered Commands

## 131 - Find axes minimums: Move specified axes in the negative direction until their limit switch is triggered.
This function will find the minimum position that the hardware can travel to, then stop. Note that all axes are moved syncronously. If one of the axes (Z, for example) should be moved separately, then a seperate command should be sent to move that axis. Note that a minimum endstop is required for each axis that is to be moved.

Payload

    uint8: Axes bitfield. Axes whose bits are set will be moved.
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)
    uint16: Timeout, in seconds.

Response (0 bytes)

## 132 - Find axes maximums: Move specified axes in the positive direction until their limit switch is triggered.
This function will find the maximum position that the hardware can travel to, then stop. Note that all axes are moved syncronously. If one of the axes (Z, for example) should be moved separately, then a seperate command should be sent to move that axis. Note that a maximum endstop is required for each axis that is to be moved.

Payload

    uint8: Axes bitfield. Axes whose bits are set will be moved.
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)
    uint16: Timeout, in seconds.

Response (0 bytes)

## 133 - delay: pause all motion for the specified time
Halt all motion for the specified amount of time.

Payload

    uint32: delay, in milliseconds

Response (0 bytes)

## 134 - Change Tool
Instruct the host to select the given tool as active

_Note: This is important to use on dual-head Replicators, because the machine needs to know the current toolhead in order to apply a calibration offset._

Payload

    uint8: Tool ID of the tool to switch to

Response (0 bytes)

## 135 - Wait for tool ready: Wait until a tool is ready before proceeding
This command halts machine motion until the specified toolhead reaches a ready state. A tool is ready when its temperature is within range of the setpoint.

Payload

    uint8: Tool ID of the tool to wait for
    uint16: delay between query packets sent to the tool, in ms (nominally 100 ms)
    uint16: Timeout before continuing without tool ready, in seconds (nominally 1 minute)

Response (0 bytes)

## 136 - Tool action command: Send an action command to a tool for execution
This command is for sending an action command to the tool. The host firmware will then pass the query along to the appropriate tool, wait for a response from the tool, and pass the response back to the host. TODO: Does the master handle retries?

Payload

    uint8: Tool ID of the tool to query
    uint8: Action command to send to the tool
    uint8: Length of the tool command payload (N)
    N bytes: Tool command payload, 0-? bytes.

Response (0 bytes)

## 137 - Enable/disable axes: Explicitly enable or disable stepper motor controllers
This command is used to explicitly power steppers on or off. Generally, it is used to shut down the steppers after a build to save power and avoid generating excessive heat.

Payload

    uint8: Bitfield codifying the command (see below)

Response (0 bytes)

<table>
<tr>
 <th>Bit</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>If set to 1, enable all selected axes. Otherwise, disable all selected axes.</td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>5</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>4</td>
 <td>B axis select</td>
</tr>
<tr>
 <td>3</td>
 <td>A axis select</td>
</tr>
<tr>
 <td>2</td>
 <td>Z axis select</td>
</tr>
<tr>
 <td>1</td>
 <td>Y axis select</td>
</tr>
<tr>
 <td>0</td>
 <td>X axis select</td>
</tr>
</table>

## 139 - Queue extended point
This queues an absolute point to move to.

_Historical note: This implementation is much more wordy than an incremental solution, which likely impacts processing time and buffer sizes on the resource-constrained firmware_

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    int32: A coordinate, in steps
    int32: B coordinate, in steps
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)

Response (0 bytes)

## 140 - Set extended position
reset the current position of the axes to the given values.

Payload

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    int32: A position, in steps
    int32: B position, in steps

Response (0 bytes)

## 141 - Wait for platform ready: Wait until a build platform is ready before proceeding
This command halts machine motion until the specified tool device reaches a ready state. A build platform is ready when it's temperature is within range of the setpoint.

Payload

    uint8: Tool ID of the build platform to wait for
    uint16: delay between query packets sent to the tool, in ms (nominally 100 ms)
    uint16: Timeout before continuing without tool ready, in seconds (nominally 1 minute)

Response (0 bytes)

## 142 - Queue extended point, new style
This queues a point to move to.

_Historical note: It differs from old-style point queues (see command 139 et. al.) in that it no longer uses the DDA abstraction and instead specifies the total move time in microseconds. Additionally, each axis can be specified as relative or absolute. If the 'relative' bit is set on an axis, then the motion is considered to be relative; otherwise, it is absolute._

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    int32: A coordinate, in steps
    int32: B coordinate, in steps
    uint32: Duration of the movement, in microseconds
    uint8: Axes bitfield to specify which axes are relative. Any axis with a bit set should make a relative movement.

Response (0 bytes)

## 143 - Store home positions
Record the positions of the selected axes to device EEPROM

Payload

    uint8: Axes bitfield to specify which axes' positions to store. Any axis with a bit set should have its position stored.

Response (0 bytes)

## 144 - Recall home positions
Recall the positions of the selected axes from device EEPROM

Payload

    uint8: Axes bitfield to specify which axes' positions to recall. Any axis with a bit set should have its position recalled.

Response (0 bytes)

## 145 - Set digital potentiometer value
Set the value of the digital potentiometers that control the voltage reference for the botsteps

Payload

    uint8: axis value (valid range 0-4) which axis pot to set
    uint8: value (valid range 0-127), values over max will be capped at max

Response (0 bytes)

## 146 - Set RGB LED value
Set Brightness levels for RGB led strip

Payload

    uint8: red value (all pix are 0-255)
    uint8: green 
    uint8: blue
    uint8: blink rate (0-255 valid)
    uint8: 0 (reserved for future use)

Response (0 bytes)

## 147 - Set Beep
Set a buzzer frequency and buzz time

Payload

    uint16: frequency
    uint16: buzz length in ms
    uint8: 0 (reserved for future use)

Response (0 bytes)

## 148 - Wait for button
Wait until either a user presses a button on the interface board, or a timeout occurs.

Payload

    uint8: Bit field of buttons to wait for (see below)
    uint16: Timeout, in seconds. A value of 0 indicates that the command should not time out.
    uint8: Options bitfield (see below)

Response (0 bytes)

Button field
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>5</td>
 <td>RESET</td>
</tr>
<tr>
 <td>4</td>
 <td>UP</td>
</tr>
<tr>
 <td>3</td>
 <td>DOWN</td>
</tr>
<tr>
<td>2</td>
 <td>LEFT</td>
</tr>
<tr>
 <td>1</td>
 <td>RIGHT</td>
</tr>
<tr>
 <td>0</td>
 <td>CENTER</td>
</tr>
</table>

Options Field
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>5</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>4</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>3</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
<td>2</td>
 <td>clear screen on button press</td>
</tr>
<tr>
 <td>1</td>
 <td>reset bot on timeout</td>
</tr>
<tr>
 <td>0</td>
 <td>change to ready state on timeout</td>
</tr>
</table>

## 149 - Display message to LCD
This command is used to display a message to the LCD board.
The maximum buffer size is larger than the maximum package size, so a full screen cannot be written with one command.
Messages are stored in a buffer and the full buffer is displayed when the "last message in group" flag is 1.
If the "last message in group" is not sent, the message will never be displayed

if the "clear message" flag is 0, the message buffer will be cleared and any existing timeout out will be cleared.

If the "wait on button" flag is 1, the message screen will _not_ clear after a users presses the center button.  The display will linger until something else is drawn. The timeout field is still relevant if the button press is never received.

Text will auto-wrap at end of line. \n is recognized as new line start. \r is ignored.

Payload

    uint8: Options bitfield (see below)
    uint8: Horizontal position to display the message at (commonly 0-19)
    uint8: Vertical position to display the message at (commonly 0-3)
    uint8: Timeout, in seconds. If 0, this message will left on the screen
    1+N bytes: Message to write to the screen, in ASCII, terminated with a null character.

Response (0 bytes)

Options Field
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>5</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>4</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
 <td>3</td>
 <td>0 (reserved for future use)</td>
</tr>
<tr>
<td>2</td>
 <td>wait for button press</td>
</tr>
<tr>
 <td>1</td>
 <td>last message in group</td>
</tr>
<tr>
 <td>0</td>
 <td>clear existing message</td>
</tr>
</table>

## 150 - Set Build Percentage
Set the percent done for the current build. This value will be displayed on the Monitor screen

Payload
 
    uint8: percent (0-100)
    uint8: 0 (reserved for future use) (reserved for future use)

Response (0 bytes)

## 151 - Queue Song
Play predefined songs on the piezo buzzer

Payload

    uint8: songID: select from a predefined list of songs

Response (0 bytes)

    song ID 0: error tone with 4 cycles
    song ID 1: done tone
    song ID 2: error tone with 2 cycles


## 152 - reset to Factory
Calls a factory reset on the eeprom. Resets all values to their "factory" settings. A soft reset of the board is also called.

This function resets all eeprom values to defaults except those that are considered "Factory" settings.   Factory settings are:

    Toolhead Calibration Settings
    Axis Inversion Settings
    Tool Count (single or dual)

These settings will not be cleared by reset to Factory.  A full eeprom reset must be called to clear these settings.

Payload

    uint8: 0 (reserved for future use)

Response (0 bytes)

## 153 - Build start notification
Tells the motherboard that a build is starting. This allows the motherboard to be state aware and to display and track build statistics.   Builds that do not include this command will not have the full mightyboard feature set enabled.

Payload

    uint32: 0 (reserved for future use)
    1+N bytes: Name of the build, in ASCII, null terminated

Response (0 bytes)

## 154 - Build end notification
Tells the motherboard that a build has been completed or aborted.

Payload (1 byte)

    uint8: 0 (reserved for future use)

Response (0 bytes)

## 155 - Queue extended point x3g
This queues an absolute point to move to.

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    int32: A coordinate, in steps
    int32: B coordinate, in steps
    uint32: DDA Feedrate, in steps/s
    uint8: Axes bitfield to specify which axes are relative. Any axis with a bit set should make a relative movement.
    float (single precision, 32 bit): mm distance for this move.  normal of XYZ if any of these axes are active, and AB for extruder only moves
    uint16: feedrate in mm/s, multiplied by 64 to assist fixed point calculation on the bot   

Response (0 bytes)

## 157 - Stream Version
Used at the start of a build to tell the bot the active x3g version.
The bot can use this information to provide feedback on compatibility to the user. 

Payload

    uint8: x3g version high byte
    uint8: x3g version low byte
    uint8: not implemented
    uint32: not implemented
    uint16: bot type: PID for the intended bot is sent 
<table>
<tr>
 <th>Bot Type</th>
 <th>PID</th>
</tr>
<tr>
 <td>Replicator</td>
 <td>0xD314</td>
</tr>
<tr>
 <td>Repliator 2</td>
 <td>0xB015</td>
</tr>
</table>
    uint16: not implemented
    uint32: not implemented
    uint32: not implemented
    uint8: not implemented

Response (0 bytes)

# Tool Query Commands

## 00 - Get version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.

Payload

    uint16: Host Version

Response

    uint16: Firmware Version

## 02 - Get toolhead temperature
This returns the last recorded temperature of the toolhead. It's important for speed purposes that it does not actually trigger a temperature reading, but rather returns the last reading. The tool firmware should be constantly monitoring its temperature and keeping track of the latest readings.

Payload (0 bytes)

Response

    int16: Current temperature, in Celsius

## 17 - Get motor speed (RPM)

Payload (0 bytes)

Response

    uint32: Duration of each rotation, in microseconds

## 22 - Is tool ready?
Query the tool to determine if it has reached target temperature. Note that this only queries the toolhead, not the build platform.

Payload (0 bytes)

Response

    uint8: 1 if the tool is ready, 0 otherwise.

## 25 - Read from EEPROM
Read the specified number of bytes from the given offset in the EEPROM, and return them in a response packet. The maximum read size is 31 bytes.

Payload

    uint16: EEPROM memory offset to begin reading from
    uint8: Number of bytes to read, N.

Response

    N bytes: Data read from the EEPROM

## 26 - Write to EEPROM
Write the given bytes to the EEPROM, starting at the given offset.

Payload

    uint16: EEPROM memory offset to begin writing to
    uint8: Number of bytes to write
    N bytes: Data to write to EEPROM

Response

    uint8: Number of bytes successfully written to the EEPROM

## 30 - Get build platform temperature
This returns the last recorded temperature of the build platform. It's important for speed purposes that it does not actually trigger a temperature reading, but rather returns the last reading. The tool firmware should be constantly monitoring its temperature and keeping track of the latest readings.

Payload (0 bytes)

Response

    int16: Current temperature, in Celsius

## 32 - Get toolhead target temperature
This returns the target temperature (setpoint) of the toolhead.

Payload (0 bytes)

Response

    int16: Target temperature, in Celsius

## 33 - Get build platform target temperature
This returns the target temperature (setpoint) of the build platform.

Payload (0 bytes)

Response

    int16: Target temperature, in Celsius

## 35 - Is build platform ready?
Query the build platform to determine if it has reached target temperature. Note that this only queries the build platform, not the toolhead.

Payload (0 bytes)

Response

    uint8: 1 if the tool is ready, 0 otherwise.

## 36 - Get tool status
Retrieve some status information from the tool

Payload (0 bytes)

Response

    uint8: Bitfield containing status information (see below)

DEPRECATED BITFIELD TABLE
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>EXTRUDER_ERROR</td>
 <td>An error was detected with the extruder heater (if the tool supports one). The extruder heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</td>
</tr>
<tr>
 <td>6</td>
 <td>PLATFORM_ERROR</td>
 <td>An error was detected with the platform heater (if the tool supports one). The platform heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</td>
</tr>
<tr>
 <td>5</td>
 <td>WDRF *Deprecated*</td>
 <td>Watchdog reset flag was set at restart</td>
</tr>
<tr>
 <td>4</td>
 <td>BORF *Deprecated*</td>
 <td>Brownout reset flag was set at restart</td>
</tr>
<tr>
 <td>3</td>
 <td>EXTRF *Deprecated*</td>
 <td>External reset flag was set at restart</td>
</tr>
<tr>
 <td>2</td>
 <td>PORF *Deprecated*</td>
 <td>Power-on reset flag was set at restart</td>
</tr>
<tr>
 <td>1</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>0</td>
 <td>EXTRUDER_READY</td>
 <td>The extruder has reached target temperature</td>
</tr>
</table>

NEW BITFIELD TABLE
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>EXTRUDER_ERROR</td>
 <td>An error was detected with the extruder heater (if the tool supports one). The extruder heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</td>
</tr>
<tr>
 <td>6</td>
 <td>PLATFORM_ERROR</td>
 <td>An error was detected with the platform heater (if the tool supports one). The platform heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</td>
</tr>
<tr>
<td>5</td>
<td>0 (reserved for future use)></td>
<td></td>
</tr>
<tr>
 <td>4</td>
 <td>Temperature Dropping</td>
 <td>Heater reached temperature but temperature subsequently dropped 30 degrees below target temp. </td>
</tr>
<tr>
 <td>3</td>
 <td>Not Heating</td>
 <td>Heater is not heating up as expected, flagged if improper after heating for 40 seconds.</td>
</tr>
<tr>
 <td>2</td>
 <td>Software Cutoff</td>
 <td>Temperature was recorded above maximum allowable.  Heater shutdown for safety.</td>
</tr>
<tr>
 <td>1</td>
 <td>Not Plugged In</td>
 <td>The tool or platform is not plugged in.</td>
</tr>
<tr>
 <td>0</td>
 <td>EXTRUDER_READY</td>
 <td>The extruder has reached target temperature</td>
</tr>
</table>

## 37 - Get PID state
Retrieve the state variables of the PID controller. This is intended for tuning the PID constants.

Payload (0 bytes)

Response

    int16: Extruder heater error term
    int16: Extruder heater delta term
    int16: Extruder heater last output
    int16: Platform heater error term
    int16: Platform heater delta term
    int16: Platform heater last output

# Tool Action Commands

## 01 - init: Initialize firmware to boot state
Initialization resets the toolhead and all processes it controls to the boot state.  some examples of processes that will be reset are:

    * Resetting target temperatures to 0
    * Turning off all outputs (fan, motor, etc)
    * Detaching all servo devices
    * Resetting motor speed to 0

Payload (0 bytes)

Response (0 bytes)

## 03 - Set toolhead target temperature
This sets the desired temperature for the heating element. The tool firmware will then attempt to maintain this temperature as closely as possible.

Payload

    int16: Desired target temperature, in Celsius

Response (0 bytes)

## 06 - Set motor speed (RPM)
This sets the motor speed as an RPM value, but does not enable/disable it.

Payload

    uint32: Duration of each rotation, in microseconds

Response (0 bytes)

## 10 - Enable/disable motor
This command can be used to turn the motor on or off. The motor direction must be specified when enabling the motor.

Payload

    uint8: Bitfield codifying the command (see below)

Response (0 bytes)

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>6</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>5</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>4</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>3</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>2</td>
 <td>0 (reserved for future use)</td>
 <td></td>
</tr>
<tr>
 <td>1</td>
 <td>DIR</td>
 <td>If set, motor should be turned in a clockwise direciton. Otherwise, it should be turned in a counterclockwise direction</td>
</tr>
<tr>
 <td>0</td>
 <td>ENABLE</td>
 <td>If set, enable the motor. If unset, disable the motor</td>
</tr>
</table>

## 12 - Enable/disable fan
Turn the fan output on or off.  Note that the extruder fan does not turn on until a temperature threshold is reached (currently set to 50C).  

Payload

    uint8: 1 to enable, 0 to disable.

Response (0 bytes)

## 13 - Enable/disable extra output
Turn the extra output attached to a toolhead on or off

Payload

    uint8: 1 to enable, 0 to disable.

Response (0 bytes)

## 14 - Set servo 1 position
Set the position of a servo connected to the first servo output.

Payload

    uint8: Desired angle, from 0 - 180

Response (0 bytes)

## 23 - pause/resume: Halt execution temporarily
This function is inteded to be called infrequently by the end user in order to make build-time adjustments during a print.

Payload (0 bytes)

Response (0 bytes)

## 24 - Abort immediately: Terminate all operations and reset
This function is intended to be used to terminate a print during printing. Disables any engaged heaters and motors. 

Payload (0 bytes)

Response (0 bytes)

## 31 - Set build platform target temperature
This sets the desired temperature for the build platform. The tool firmware will then attempt to maintain this temperature as closely as possible.

Payload

    int16: Desired target temperature, in Celsius

Response (0 bytes)


class ConnectionError(IOError):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    print self.value

import os
import sys

lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse
import struct
import array
import threading

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")

(options, args) = parser.parse_args()

condition = threading.Condition()
s = makerbot_driver.s3g.from_filename(options.port, condition)
print "---Clearing Buffer---"
s.clear_buffer()
print "---Success---"
print "---Getting Version---"
s.get_version()
print "---SUCCESS---"
print "---Reading VID Off EEPROM---"
read_VID = s.read_from_EEPROM(68, 2)
read_VID = makerbot_driver.Encoder.decode_uint16(read_VID)
actual_VID = int('23C1', 16)
if not read_VID == actual_VID:
  raise ConnectionError("Reading VID")
print "---SUCCESS---"
print "---Reading PID off EEPROM---"
read_PID = s.read_from_EEPROM(70, 2)
read_PID = makerbot_driver.Encoder.decode_uint16(read_PID)
actual_PID = int('D314', 16)
if not read_PID == actual_PID:
  raise ConnectionError("Reading PID")
print "---SUCCESS---"
print "---Homing Bot---"
s.find_axes_maximums(['X', 'Y'], 800, 20)
s.find_axes_minimums(['Z'], 800, 20)
print "---SUCCESS---"

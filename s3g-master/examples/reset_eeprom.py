import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports
import struct
import optparse
import threading

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="The port you want to connect to (OPTIONAL)", default=None)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="The Replicator")
parser.add_option("-v", "--version", dest="version",
                 help="version you want to upload to", default="5.5")
(options, args) = parser.parse_args()

if options.port is None:
    md = makerbot_driver.MachineDetector()
    md.scan()
    port = md.get_first_machine()
    if port is None:
        print "Cant Find %s" % ("A Printer")
        sys.exit()
else:
    port = options.port

print '\nPORT: ' + port
print "Fully reseting EEPROM, this will take a couple seconds"
print "------------------------------------------------------"
condition = threading.Condition()
r = makerbot_driver.s3g.from_filename(port, condition)
eeprom_length = 4000
value = struct.pack('<B', 0xFF)
for i in range(eeprom_length):
    r.write_to_EEPROM(i, value)
r.reset()

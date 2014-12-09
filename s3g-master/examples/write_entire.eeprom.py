import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial.tools.list_ports
import optparse
import json

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="The port you want to connect to (OPTIONAL)", default=None)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="The Replicator")
parser.add_option("-v", "--version", dest="version",
                  help="The version of eeprom you want to read",
                  default="5.6"
                  )
parser.add_option("-i", "--input_file", dest="input_file",
                  help="The file you want to write from")
(options, args) = parser.parse_args()

if options.port is None:
    md = makerbot_driver.MachineDetector()
    md.scan(options.machine)
    port = md.get_first_machine()
    if port is None:
        print "Cant Find %s" % (options.machine)
        sys.exit()
else:
    port = options.port
factory = makerbot_driver.MachineFactory()
returnobj = factory.build_from_port(port)
r = getattr(returnobj, 's3g')

writer = makerbot_driver.EEPROM.EepromWriter.factory(
    r, firmware_version=options.version)

with open(options.input_file) as f:
    eeprom_map = json.load(f)

writer.write_entire_map(eeprom_map)

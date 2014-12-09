import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports
import optparse

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="The port you want to connect to (OPTIONAL)", default=None)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="The Replicator")
parser.add_option("-v", "--version", dest="version",
                  help="version you want to upload to", default="5.5")
parser.add_option("-e", "--eeprom_entry", dest="eeprom_entry",
                  help="eeprom entry to read from")
parser.add_option("-c", "--context", dest="context",
                  help="context for the eeprom_entry, as comma separated values surrounded by quotes",
                  default="")
(options, args) = parser.parse_args()

context = options.context.replace(' ', '')
context = context.split(',')
for c in context:
    if c == '':
        context.remove(c)

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

reader = makerbot_driver.EEPROM.EepromReader.factory(
    r, firmware_version=options.version)

print reader.read_data(options.eeprom_entry, context)

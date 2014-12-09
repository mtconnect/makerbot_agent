"""
Lists all current Replicators connected to
the computer via USB ports.
"""
import sys
import serial.tools.list_ports
import optparse

parser = optparse.OptionParser()
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Return all port information instead of the port address.")
(options, args) = parser.parse_args()

vid = int('23c1', 16)
pid = int('d314', 16)

port = list(serial.tools.list_ports.list_ports_by_vid_pid(vid, pid))[0]
if options.verbose:
  return_info = port
else:
  return_info = port['port']
print return_info
sys.exit()

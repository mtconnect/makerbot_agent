"""
A connection test that tests if either no 
bots are plugged in or if a certain port has a 
replicator plugged into it.
"""
import sys
import serial.tools.list_ports
import optparse

parser = optparse.OptionParser()
parser.add_option("-n", "--none", dest="none", action="store_true", default=False, help="Run the connection test expecting no machine attached")
parser.add_option("-e", "--expecting", dest="expecting", default=None, help="The port we are expecting a maching to be attached to.")
(options, args) = parser.parse_args()

vid = int('23c1', 16)
pid = int('d314', 16)

if options.none and options.expecting:
  print "You cant run both the Expecting Port test and the Expecting None test simultaneously."
  sys.exit(1)
elif options.none:
  ports = list(serial.tools.list_ports.list_ports_by_vid_pid(vid, pid))
  if len(ports) == 0:
    print "No Bots Detected. Exiting."
    sys.exit()
  else:
    print "Bot detected when expecting None, exiting."
    sys.exit(1) 
elif options.expecting:
  ports = serial.tools.list_ports.list_ports_by_vid_pid(vid, pid)
  for port in ports:
    if port['port'] == options.expecting:
      print "Bot Detected at port %s, exiting." %(options.expecting)
      sys.exit()
  else:
    print "Bot in wrong port detected.  Exiting"
    sys.exit(1)

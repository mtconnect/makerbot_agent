import platform
import os
import shutil
import optparse
import sys

parser = optparse.OptionParser()
parser.add_option('-p', '--platform', dest='platform',
                  help='The platform you are you', default=None)
(options, args) = parser.parse_args()


tool_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'submodule',
    'conveyor_bins'
    )
path_to_firmware = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'makerbot_driver',
    'Firmware'
    )

#Lets do some os detection!
if not options.platform:
  if platform.system() == "Windows": 
    platform_folder = 'windows'
    avrdude_name = "avrdude.exe"
    files = [avrdude_name, "avrdude.conf", "libusb0.dll"]
  elif platform.system() == "Darwin":
    platform_folder = 'mac'
    avrdude_name = "avrdude"
    files = [avrdude_name, "avrdude.conf"]
  elif platform.system() == 'Linux':
    print "Nothing to copy; use distribution utility to obtain AVRDude."
    sys.exit(0)
else:
  #Lets use the user specified args!
  acceptable_platforms = ['windows', 'mac']
  if options.platform not in acceptable_platforms:
    print "Please enter a platform as: %s" %(str(acceptable_platforms))
    sys.exit(1)
  platform_folder = options.platform

if not os.path.isfile(os.path.join(path_to_firmware, avrdude_name)):
  print 'Copying avrdude files into %s' %(path_to_firmware)
  for file in files:
    print file
    shutil.copy(os.path.join(tool_path, platform_folder, file), path_to_firmware)
  sys.exit(0)
else:
  print 'AVRDude detected in %s, exiting' %(path_to_firmware)
  sys.exit(0)

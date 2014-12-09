#Machine Detector
The Machine Detector is a python object used to discover different types of bots.

##Purpose
The Machine Detector is a utility that is meant to be run in the background of another service with the sole purpose of reporting the current machines plugged in, and any machines that have been added or removed from the host computer.

##Instructions
The Machine Detector can be initialized with:

    mb = s3g.MachineDetector()

To begin scanning for just one type of machine, put one machine name in a python list and pass it into the begin_scanning function:

    mb.begin_scanning(['ReplicatorDual'])

To begin scanning for multiple types of machines, put two machine names in a python list and pass it into the begin_scanning function:

    mb.begin_scanning(['ReplicatorDual', 'Thing-O-Matic'])

##Information Storage
The Machine Detector stores all information in an internal python dictionary called 'ports'.  To access this dictionary:

    myports = mb.ports

Each type of machine being scanned for is a separate key.  That key is defined by an additional dict, which stores three specific values:

* 'current_ports'
* 'added_ports'
* 'removed_ports'

For instance, if we wanted to scan for a 'ReplicatorDual' and a 'Thing-O-Matic', the architecture of the ports dict would be:

    {
    "ReplicatorDual"  :   {
          "current_ports" : [],
          "added_ports"   : [],
          "removed_ports" : [],
          },
    "Thing-O-Matic"   :   {
          "current_ports" : [],
          "added_ports"   : [],
          "removed_ports" : [],
          }
    }

##Scanning by VID/PID
It is possible to scan for a specific VID/PID.  To do this:

    md = s3g.MachineDetector()
    current_ports = []
    vid = <some_vid>
    pid = <some_pid>
    current_ports, added_ports, removed_ports = md.scan_serial_ports(current_ports, vid, pid)

scan_serial_ports requires a python list of currently connected ports as its first parameter.  The function checks the newly ascertained ports against the parametized port list to find added and removed ports.

##Find VID/PID of a machine
To find the VID/PID information from a specific machine that has a fully defined machine profile:

    md = s3g.MachineDetector()
    vid, pid = md.get_vid_pid('ReplicatorDual')

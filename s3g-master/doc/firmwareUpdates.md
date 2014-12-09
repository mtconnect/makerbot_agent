#Firmware Update
The s3g driver has the capability of uploading firmware to a machine via AVRDude, an external firmware uploading utility.  No AVRDude utility is packaged with this driver, so it is up to the user to satisfy this requirement.

To download AVRDude, goto: www.nongnu.org/avrdude

##Uploading
To upload firmware, an uploader object must first be created and updated:

    uploader = s3g.Firmware.Uploader()
    uploader.update()

To actually upload firmware, call

    uploader.upload(<port>, <machine name>, <version>)

This will create the command line arguments and invoke AVRDude with the correct .hex file relative to the passed version. 

##AVRDude Parameters
S3G's uploader has access to several machine board profiles, each with a set of predefined defaults that are passed to AVRDude.  The machine board profile also has a dictionary of all firmware versions and their associated .hex files.

##File exploring
The uploader can explore and report back different bits of information related to the boards it knows about.  To get a list of boards the uploader and talk to:

    uploader.list_machines()

To get a list of possible firmware versions the uploader can upload to:

    uploader.list_versions(<machine name>)

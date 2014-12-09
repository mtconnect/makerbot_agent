# Import the serial and makerbot modules.
import serial, makerbot_driver
# Import threading for the condition parameter of makerbot.
import threading
# Import the list_ports module to enable picking the port through which the Makerbot is connected.
from serial.tools import list_ports

# Variable to hold the makerbot port.
makerbotPort = None

# Find the port on which the maker bot is connected.
for port in list_ports.comports():
    # If it is a Replicator.
    if "Replicator" in port[1]:
        # Set the port.
        makerbotPort = port[0]
    # end if
# end for

# If the makerbot port was found (if it is connected).
if makerbotPort != None:
    # Create the makerbot s3g interface object.
    replicator = makerbot_driver.s3g()
    # Open the port to the makerbot.
    makerbotFile = serial.Serial(makerbotPort, 115200, timeout=1)
    # Create the condition.
    condition = threading.Condition()
    # Set the stream writer to the opened port/stream.
    replicator.writer = makerbot_driver.Writer.StreamWriter(makerbotFile,condition)
    
    # *** Other Queries ***
    
    print "\n**************\n"
    
    # name: string
    print "Name: "+str(replicator.get_name())
    
    # Version
    print "version: "+str(replicator.get_version())
    print "advanced version: "+str(replicator.get_advanced_version())
    
    # Is Finished
    print "Is Finished: "+str(replicator.is_finished())
    
    # Buffer Size
    print "Buffer Size: "+str(replicator.get_available_buffer_size())
    
    # Next File Name
    #print "Next File Name: "+str(replicator.get_next_filename())
    
    # Build Name
    print "Build Name: "+str(replicator.get_build_name())
    
    # Axes Data
    print "Axes values (x, y, z, a, b): "+str(replicator.get_extended_position())
    
    # Axes Minimums and Maximums
    #print "Axes minimums (x, y, z, a, b): "+str(replicator.find_axes_minimums(['x', 'y', 'z', 'a', 'b'], moveRate, timeoutSeconds)
    #print "Axes maximums (x, y, z, a, b): "+str(replicator.find_axes_minimums(['x', 'y', 'z', 'a', 'b'], moveRate, timeoutSeconds)
    
    # toolhead count: integer
    numTools = replicator.get_toolhead_count()
    print "Toolhead count: "+str(numTools)
    
    # Verified status (is firmware verified)
    #print "Is firmware verified: "+str(replicator.get_verified_status())
    
    """ build stats: {'BuildState': buildstate, 'BuildHours': buildhours,
                       'BuildMinutes': buildminutes, 'LineNumber': linenumber,
                       'Reserved': reserved}
    """
    print "Current or last build stats: "+str(replicator.get_build_stats())
    
    """ communication stats: {'PacketsRecieved', 'PacketsSent', 'NonResponsivePacketsSent'
                               'PacketRetries', 'NoiseBytes'}
    """ # Not supported
    #print "Communication stats: "+str(replicator.get_communication_stats())
    
    """ motherboard stats: {'preheat', 'manual_mode', 'onboard_script', 'onboard_process',
                            'wait_for_button', 'build_cancelling', 'heat_shutdown',
                            'power_error'}
    """
    print "Motherboard status: "+str(replicator.get_motherboard_status())
    
    # *** Tool Queries ***
    for i in range(0, numTools):
        # Toolhead version
        print "tool "+str(i)+" version:"+str(replicator.get_toolhead_version(i))
        # Toolhead Temperature
        print "tool "+str(i)+" temp: "+str(replicator.get_toolhead_temperature(i))
        # Is the tool ready
        print "tool "+str(i)+" is ready?: "+str(replicator.is_tool_ready(i))
        # Tool Status
        print "tool "+str(i)+" status: "+str(replicator.get_tool_status(i))
        # Platform Temperature
        print "Platform temperature: "+str(replicator.get_platform_temperature(i))
        # Toolhead Target temperature.
        print "tool "+str(i)+" target temp: "+str(replicator.get_toolhead_target_temperature(i))
        # Platform Target Temperature.
        print "tool "+str(i)+" platform target temp: "+str(replicator.get_platform_target_temperature(i))
        # Is Platform Ready
        print "tool "+str(i)+" platform ready: "+str(replicator.is_platform_ready(i))
    # end for
    
# end if
# Otherwise...
else:
    print "No MakerBot connected."
# end else

"""r = makerbot_driver.s3g()
file = serial.Serial(port, 115200, timeout=1)
r.writer = makerbot_driver.Writer.StreamWriter(file)"""

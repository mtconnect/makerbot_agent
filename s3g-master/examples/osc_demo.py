"""
Control an makerbot_driver device (Makerbot, etc) using osc!

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
* pyOSC: https://trac.v2.nl/wiki/pyOSC

"""

# To use this example without installing makerbot_driver, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import serial
import time
import optparse
import OSC
import threading

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-o", "--oscport", dest="oscport",
                  help="OSC port to listen on", default="10000")
(options, args) = parser.parse_args()


rLock = threading.Lock()
r = makerbot_driver.s3g()

file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)
condition = threading.Condition()
r.writer = makerbot_driver.Writer.StreamWriter(file, condition)

# TODO: Remove this hack.
r.velocity = 1600

def velocity_handler(addr, tags, stuff, source):
    """
    Allow an external program to modify the movement rate
    """
    print stuff[0]
    with rLock:
        r.velocity = stuff[0]

def move_handler(addr, tags, stuff, source):
    #print addr, tags, stuff, source
#    print r.velocity

    #target = [stuff[0], stuff[1], stuff[2], stuff[3], stuff[4]]
    #velocity = stuff[5]
    x = (1 - stuff[0]) * 3000
    y = stuff[1] * 3000

    target = [x, y, 0, 0, 0]

    try:
        with rLock:
            r.queue_extended_point(target, int(r.velocity))
    except makerbot_driver.TransmissionError as e:
        print 'error moving:', e

def led_handler(addr, tags, stuff, source):
    print addr, tags, stuff, source

    with rLock:
        r.ToggleValve(0, stuff[0] == 1)

def pen_handler(addr, tags, stuff, source):
    print addr, tags, stuff, source

    with rLock:
        r.toggle_fan(0, stuff[0] == 1)

print "starting client"
t = OSC.OSCMultiClient()
t.setOSCTarget(('127.0.0.1', 10001))

print "starting server"
s = OSC.OSCServer(('127.0.0.1', int(options.oscport)))
s.addDefaultHandlers()
s.addMsgHandler("/move", move_handler)
s.addMsgHandler("/velocity", velocity_handler)
s.addMsgHandler("/led", led_handler)
s.addMsgHandler("/pen", pen_handler)

st = threading.Thread(target=s.serve_forever)
st.start()


try:
    while True:
        try:
            time.sleep(1)
            msg = OSC.OSCMessage("/temps")
            with rLock:
                msg.append(r.get_toolhead_temperature(0))
                msg.append(r.get_toolhead_temperature(1))
                msg.append(r.get_platform_temperature(0))
                t.send(msg)
        except makerbot_driver.TransmissionError as e:
            print 'error getting temperature: ', e

except KeyboardInterrupt:
    exit(1)
    pass

s.close()
st.join()

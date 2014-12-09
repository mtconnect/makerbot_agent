"""
Start a web server that can proxy requests to the machine

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
"""
# To use this example without installing makerbot_driver, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import serial
import optparse
import json
import SimpleHTTPServer
import SocketServer
import threading
import time

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-a", "--httpaddress", dest="httpaddress",
                  help="http address", default="0.0.0.0")
parser.add_option("-o", "--httpport", dest="httpport",
                  help="http port", default=8080)
(options, args) = parser.parse_args()

TEMPERATURE_HISTORY_LENGTH = 30 # Numper of previous temperature measurements to keep around
MACHINE_UPDATE_INTERVAL = 2 # Number of seconds between updating the machine state

bots = []

class Bot(object):
    """ Representation of a single s3g bot. Currently only tracks temperature """
    _data_lock = threading.Lock()
    _tool_0_temp_data = []
    _tool_1_temp_data = []
    _platform_temp_data = []
    _sample_count = 0

    def __init__(self, port, baud):
        """ Create a new connection to an s3g machine

        @param string port Serial port to connect to
        @param string baud Baud rate to communicate at
        """
        self.r = makerbot_driver.s3g()
        file = serial.Serial(port, baud, timeout=.2)
        self.r.writer = makerbot_driver.Writer.StreamWriter(file)

    def update(self):
        """ Update the machine temperature data- call this periodically. """
        self._data_lock.acquire()

        self._tool_0_temp_data.append(  [self._sample_count, self.r.get_toolhead_temperature(0)])
        self._tool_1_temp_data.append(  [self._sample_count, self.r.get_toolhead_temperature(1)])
        self._platform_temp_data.append([self._sample_count, self.r.get_platform_temperature(1)])
        self._sample_count += 1
 
        self._tool_0_temp_data =   self._tool_0_temp_data[  -TEMPERATURE_HISTORY_LENGTH:]
        self._tool_1_temp_data =   self._tool_1_temp_data[  -TEMPERATURE_HISTORY_LENGTH:]
        self._platform_temp_data = self._platform_temp_data[-TEMPERATURE_HISTORY_LENGTH:]

        self._data_lock.release()

    def get_temperature_data(self):
        """ Get the temperature data from the machine

        @return tuple of the tool 0 temperatures, tool 1 temperatures, and platform temperatures.
        """
        self._data_lock.acquire()

        tool_0_data =   self._tool_0_temp_data
        tool_1_data =   self._tool_1_temp_data
        platform_data = self._platform_temp_data

        self._data_lock.release()
 
        return tool_0_data, tool_1_data, platform_data

class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """ Field requests for bots """
    def do_GET(s):
        """Respond to a GET request."""
        global bots

        if s.path == '/temp':
            """ Return the history for each temperature sensor """

            # TODO: not threadsafe in case of adding/subtracting bot.
            tool_0, tool_1, platform = bots[0].get_temperature_data()

            response = {
                "tool_0_temp" :   {"label" : "Toolhead 0 Temperature", "data" : tool_0},
                "tool_1_temp" :   {"label" : "Toolhead 1 Temperature", "data" : tool_1},
                "platform_temp" : {"label" : "Platform Temperature",   "data" : platform}
            }

            content = json.dumps(response)
         
            s.send_response(200)
            s.send_header("Content-Type",   "application/json")
            s.end_headers()
            s.wfile.write(content)
            return
         
        # Otherwise pass it to the file server
        s.path = '/web_server/' + s.path 
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(s)

    def log_message(self, format, *args):
        """ Suppress console messages """
        return

class UpdateBotThread(threading.Thread):
    """ Thread to update the state machine for each bot """
    running = True

    def run(self):
        """ Once every MACHINE_UPDATE_INTERVAL, update each bot """
        global bots

        while(self.running):
            # TODO: Not threadsafe in case of adding/subtracting bot.
            for bot in bots:
                bot.update()

            time.sleep(MACHINE_UPDATE_INTERVAL)

    def shutdown(self):
        self.running = False

class HttpServerThread(threading.Thread):
    """ Thread to serve HTTP requests """
    def __init__(self, httpaddress, httpport):
        super(HttpServerThread, self).__init__()

        self._httpd = SocketServer.TCPServer((httpaddress, httpport), Handler)

    def run(self):
        """ Once every MACHINE_UPDATE_INTERVAL, update each bot """
        self._httpd.serve_forever()

    def shutdown(self):
        self._httpd.shutdown()


if __name__ == '__main__':
    # Initialize a single bot to monitor
    bots.append(Bot(options.serialportname, options.serialbaud))

    # Start a thread to update status of each bot
    updater = UpdateBotThread()
    updater.start()

    # Start the HTTP server
    http = HttpServerThread(options.httpaddress, options.httpport)
    http.start()

    # Finally, run until an interrupt is received
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass

    print "Shutting down"
    http.shutdown()
    updater.shutdown()

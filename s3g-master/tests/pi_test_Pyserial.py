from __future__ import (absolute_import, print_function, unicode_literals)
import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import io
import struct
import unittest
import threading
import time

import serial

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestIsCorrectVariant(unittest.TestCase):

    def test_isMbVariant(self):
        self.assertTrue(serial.__version__.index('mb2') > 0)

    def test_hasScanEndpoints(self):
        import serial.tools.list_ports as lp
        scan = lp.list_ports_by_vid_pid

    '''
    # This test is commented out because it requires an actual serial port.
    def test_variantDoesBlocking(self):
      #grab a port
      #try to grab it again
      import serial.tools.list_ports as lp
      scan = lp.list_ports_by_vid_pid
      print('autograbbing a port')
      comports = lp.comports()
      if( len(list(comports)) < 1):
          print('no comport availabe')
          self.assertFalse(True, "no comports, cannot execute test")
      portname = comports[-1][0] #item 0 in last comport as the port to test
      print("Connecting to serial" +  portname)
      s = serial.Serial(portname)
      with self.assertRaises(serial.SerialException) as ex:
          s = serial.Serial(portname)
     '''


if __name__ == '__main__':
    unittest.main()

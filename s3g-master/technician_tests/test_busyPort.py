from __future__ import (absolute_import, print_function, unicode_literals)
import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import io
import struct
import unittest
import threading
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest


import makerbot_driver

class PortBusyTechnicianTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_port_busy(self):
    return
    port = raw_input("specify a real active port on your OS to test>")
    r1 = makerbot_driver.s3g.from_filename( port )
    r2 = makerbot_driver.s3g.from_filename( port )
    #r1.get_version()
    #r2.get_version()
    r1.find_axes_maximums(['x', 'y'], 500, 60)
    r2.find_axes_maximums(['x', 'y'], 500, 60) 
    r1.close()
    r2.close()

class InUseTechnicianTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_inuse_port(self):
    port = raw_input("specify a real active port on your OS to test>")
    r1 = makerbot_driver.s3g.from_filename( port )
    s = r1.is_open()
    self.assertTrue(s, "open expcted post construction")
    r1.close()
    s = r1.is_open()
    self.assertFalse(s, "close expcted.")
    r1.open()
    s = r1.is_open()
    self.assertTrue(s, "reopened. open expcted")
    r1.close()
    s = r1.is_open()
    self.assertFalse(s, "close expcted.")
	
if __name__ == '__main__':
  unittest.main()

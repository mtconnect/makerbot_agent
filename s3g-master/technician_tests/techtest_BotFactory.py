from __future__ import (absolute_import, print_function, unicode_literals)

from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
import uuid
lib_path = os.path.abspath('../')
sys.path.append(lib_path)


try:
    import unittest2 as unittest
except ImportError:
    import unittest
import mock

import makerbot_driver

class TestLiveBotConnected(unittest.TestCase):

  def setUp(self):
    pass

  def test_leaves_bot_open(self):
    ignore= raw_input("Please Verify a valid MakerBot is connected(Y/n)>")
    self.assertEqual(ignore.lower(),'Y'.lower())
    md = makerbot_driver.MachineDetector()
    md.scan()
    availMachine = md.get_first_machine()
    self.assertTrue(availMachine != None)
    print(availMachine)
    bFact = makerbot_driver.BotFactory()
    s3gObj, profile = bFact.build_from_port(availMachine, False)
	# re-opening s3g here fails
    self.assertFalse(s3gObj.is_open())

if __name__ == '__main__':
  unittest.main()


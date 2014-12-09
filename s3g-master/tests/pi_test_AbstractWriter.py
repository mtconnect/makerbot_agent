import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import makerbot_driver
import threading


class AbstractWriterTests(unittest.TestCase):
    """
    Emulate a machine
    """
    def setUp(self):
        condition = threading.Condition()
        self.w = makerbot_driver.Writer.AbstractWriter("stream", condition)

    def test_not_implemented_raises(self):
        #none of these should be implemented in the base class
        payload = ''
        with self.assertRaises(NotImplementedError) as a_raise:
            self.w.send_action_payload(payload)
        with self.assertRaises(NotImplementedError) as a_raise:
            self.w.send_query_payload(payload)
        with self.assertRaises(NotImplementedError) as a_raise:
            self.w.open()
        with self.assertRaises(NotImplementedError) as a_raise:
            self.w.close()
        with self.assertRaises(NotImplementedError) as a_raise:
            self.w.is_open()


if __name__ == "__main__":
    unittest.main()

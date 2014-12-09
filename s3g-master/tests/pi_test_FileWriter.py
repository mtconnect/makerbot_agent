import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import makerbot_driver

import unittest
import threading
import tempfile


class s3gFileWriterTests(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=True, suffix='.gcode') as f:
            self.the_file = f.name
        condition = threading.Condition()
        self.w = makerbot_driver.Writer.FileWriter(open(self.the_file, 'wb'), condition)

    def tearDown(self):
        self.w = None

    def test_build_and_send_query_packet_not_implemented(self):
        self.assertRaises(NotImplementedError, self.w.send_query_payload, [42])

    def test_build_and_send_action_payload(self):
        data = 'abcde'
        expected_payload = bytearray(data)

        self.w.send_action_payload(data)
        self.w.close()
        with open(self.the_file, 'r') as f:
            self.assertEqual(expected_payload, f.read())

    def test_write_external_stop(self):
        self.w.external_stop = True
        self.assertRaises(makerbot_driver.ExternalStopError,
                          self.w.send_action_payload, 'asdf')

    def test_is_open(self):
        self.assertTrue(self.w.is_open())
        self.w.file.close()
        self.assertFalse(self.w.is_open())

    def test_close(self):
        self.assertFalse(self.w.file.closed)
        self.w.close()
        self.assertTrue(self.w.file.closed)

    def test_init_non_binary_mode(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gcode') as f:
            the_file = f.name
        condition = threading.Condition()
        with self.assertRaises(makerbot_driver.Writer.NonBinaryModeFileError):
            makerbot_driver.Writer.FileWriter(open(the_file, 'w'), condition)

    def test_write_non_binary_mode(self):
        self.w.close()
        self.w.file = open(self.w.file.name, 'w')
        with self.assertRaises(makerbot_driver.Writer.NonBinaryModeFileError):
            self.w.send_action_payload('asdf')

    def test_check_check_binary_mode_non_binary(self):
        with tempfile.NamedTemporaryFile(delete=True, suffix='.gcode') as f:
            path = f.name
        self.w.file = open(path, 'w')
        with self.assertRaises(makerbot_driver.Writer.NonBinaryModeFileError):
            self.w.check_binary_mode()

if __name__ == "__main__":
    unittest.main()

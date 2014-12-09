import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver
import tempfile
import re


class TestSingletonTProcessor(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.SingletonTProcessor()

    def tearDown(self):
        self.p = None

    def test_regex(self):
        cases = [
            ["T0", ["M135 T0\n"]],
            [";T0", [";T0"]],
            ["t0", ["M135 T0\n"]],
            ["(comment) T0", ["(comment) T0"]],
            ["G1 X0 Y0", ["G1 X0 Y0"]],
            ["T0;asdf", ["M135 T0\n"]],
            ["T0(asdf", ["M135 T0\n"]],
            ["        T0", ['M135 T0\n']],
            ["THIS IS NOT GCODE", ["THIS IS NOT GCODE"]],
        ]
        for case in cases:
            self.assertEqual(case[1], self.p._transform_code(case[0]))

    def test_process_file(self):
        gcodes = ["T0", "\n", "G1 X8 Y9", "\n", "T1", "\n",
                  "G92 X0 Y0", "\n", "T7", "\n"]
        expected_output = ["M135 T0\n", "\n", "G1 X8 Y9", "\n",
                           "M135 T1\n", "\n", "G92 X0 Y0", "\n", "M135 T7\n", "\n"]
        got_output = self.p.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
    unittest.main()

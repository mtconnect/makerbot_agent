import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile

import makerbot_driver


class RemoveRepGStartEnd(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.RemoveRepGStartEndGcode()

    def tearDown(self):
        self.p = None

    def test_process_gcode_no_input(self):
        the_input = []
        expected_output = []
        got_output = self.p.process_gcode(the_input)
        self.assertEqual(expected_output, got_output)

    def test_process_gcode_with_only_start(self):
        the_input = [
            "(**** start.gcode\n",
            "G1 X0 Y0 Z0\n",
            "G92 X0 Y0 Z0\n",
            "(end of start.gcode\n",
            "G1 X1 Y2 Z3 A4 B5\n",
        ]
        expected_output = ["G1 X1 Y2 Z3 A4 B5\n"]
        got_output = self.p.process_gcode(the_input)
        self.assertEqual(expected_output, got_output)

    def test_process_gcode_with_only_end(self):
        the_input = [
            "(**** End.gcode\n",
            "G1 X0 Y0 Z0\n",
            "G92 X0 Y0 Z0\n",
            "(end End.gcode\n",
            "G1 X1 Y2 Z3 A4 B5\n",
        ]
        expected_output = ["G1 X1 Y2 Z3 A4 B5\n"]
        got_output = self.p.process_gcode(the_input)
        self.assertEqual(expected_output, got_output)

    def test_process_gcode_with_start_and_end(self):
        the_input = [
            "(**** start.gcode\n",
            "G1 X0 Y0 Z0\n",
            "G92 X0 Y0 Z0\n",
            "(end of start.gcode\n",
            "G1 X1 Y2 Z3 A4 B5\n",
            "(**** End.gcode\n",
            "G1 X0 Y0 Z0\n",
            "G92 X0 Y0 Z0\n",
            "(end End.gcode\n",
        ]
        expected_output = ["G1 X1 Y2 Z3 A4 B5\n"]
        got_output = self.p.process_gcode(the_input)
        self.assertEqual(expected_output, got_output)

if __name__ == "__main__":
    unittest.main()

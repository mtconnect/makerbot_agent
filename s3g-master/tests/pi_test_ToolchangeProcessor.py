import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile
import makerbot_driver


class TestToolchangeProcessor(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.ToolchangeProcessor()

    def tearDown(self):
        self.p = None

    def test_insert_tool_change_from_a(self):
        cases = [
            [["G1 X0"], 'G1 X0'],
            [["G0"], 'G0'],
            [["G1 X0 E0"], 'G1 X0 E0'],
            [[self.p.extruders['B'], "G1 B0"], 'G1 B0'],
            [[self.p.extruders['B'], "G1 b0"], 'G1 b0'],
            [[self.p.extruders['B'], "G1 X0 Y0 Z0 B50"], "G1 X0 Y0 Z0 B50"],
            [[self.p.extruders['B'], '(comments)    G1 X0 Y0 Z0 B50'],
             "(comments)    G1 X0 Y0 Z0 B50"],
            [[self.p.extruders['B'], '(comments) (comments) (comments)     G1 X0 Y0 Z0 B50'], "(comments) (comments) (comments)     G1 X0 Y0 Z0 B50"],
            [[self.p.extruders['B'], '     G1 X0 B50'], '     G1 X0 B50'],
        ]
        for case in cases:
            self.p.current_extruder = 'A'
            self.assertEqual(case[0], self.p._transform_code(case[1]))

    def test_insert_tool_change_from_b(self):
        cases = [
            [["G1 X0"], 'G1 X0'],
            [["G0"], 'G0'],
            [["G1 X0 E0"], 'G1 X0 E0'],
            [[self.p.extruders['A'], "G1 A0"], 'G1 A0'],
            [[self.p.extruders['A'], "G1 a0"], 'G1 a0'],
            [[self.p.extruders['A'], "G1 X0 Y0 Z0 A50"], "G1 X0 Y0 Z0 A50"],
            [[self.p.extruders['A'], "G1 X0 Y0 Z0 A50 B60"],
             "G1 X0 Y0 Z0 A50 B60"],
        ]
        for case in cases:
            self.p.current_extruder = 'B'
            self.assertEqual(case[0], self.p._transform_code(case[1]))

    def test_process_file(self):
        gcodes = [
            "G1 X50 Y50\n",
            "G1 X0 Y0 A50\n",
            "G1 X0 Y0 B50\n",
            "G1 X0 Y0 B50\n",
            "G1 X0 Y0 B50\n",
            "G1 X0 Y0 A50\n",
            "G1 X0 Y0 B50\n"
        ]
        expected_output = [
            "G1 X50 Y50\n",
            "G1 X0 Y0 A50\n",
            "M135 T1\n",
            "G1 X0 Y0 B50\n",
            "G1 X0 Y0 B50\n",
            "G1 X0 Y0 B50\n",
            "M135 T0\n",
            "G1 X0 Y0 A50\n",
            "M135 T1\n",
            "G1 X0 Y0 B50\n"
        ]
        got_output = self.p.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
    unittest.main()

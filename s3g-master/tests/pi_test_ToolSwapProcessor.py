import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile
import re

import makerbot_driver


class TestToolSwapProcessor(unittest.TestCase):

    def setUp(self):
        self.tsp = makerbot_driver.GcodeProcessors.ToolSwapProcessor()

    def tearDown(self):
        self.tsp = None

    def test_regex(self):
        cases = [
            ['(This Swaps Toolhead 0)', ['(This Swaps Toolhead 0)']],
            ['(This Swaps Toolhead A)', ['(This Swaps Toolhead A)']],
            ['(comment) (comment) M132 T0', ['(comment) (comment) M132 T0']],
            ['M132 T0', ['M132 T1']],
            ['G1 A50', ['G1 B50']],
            ['G1 E50', ['G1 E50']],
            ['G1 X0 Y0 Z0', ['G1 X0 Y0 Z0']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.tsp._transform_code(case[0]))

    def test_toolswap(self):
        cases = [
            ['G92 X0 Y0 Z0 A1 B2', 'G92 X0 Y0 Z0 B1 A2'],
            ['G1 A0', 'G1 B0'],
            ['G1 B0', 'G1 A0'],
            ['M132 T0', 'M132 T1'],
            ['M132 T2', 'M132 T2'],
        ]
        regex = re.compile("[^(;]*([(][^)]*[)][^(;]*)*([aAbB])|[^(;]*([(][^)]*[)][^(;]*)*[tT]([0-9])")
        for case in cases:
            self.assertEqual(case[1], self.tsp._transform_tool_swap(
                re.match(regex, case[0])))

    def test_process_file(self):
        gcodes = [
            'M132 T0\n',
            'G1 X0 Y0 Z0 E50\n',
            'G1 A50\n',
            'G1 A50\n',
            'G92 A0\n',
            'G92 E0\n',
        ]
        expected_gcodes = [
            'M132 T1\n',
            'G1 X0 Y0 Z0 E50\n',
            'G1 B50\n',
            'G1 B50\n',
            'G92 B0\n',
            'G92 E0\n',
        ]
        output = self.tsp.process_gcode(gcodes)
        self.assertEqual(expected_gcodes, output)

if __name__ == "__main__":
    unittest.main()

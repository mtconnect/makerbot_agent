import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import mock

import makerbot_driver


class TestLineTransformProcessor(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.LineTransformProcessor()

    def tearDown(self):
        self.p = None

    def test_transform_code(self):
        tg1 = "G1_TRANSFORMED"

        def _transform_g1(*args, **kwargs):
            return tg1
        tg2 = "G2_TRANSFORMED"

        def _transform_g2(*args, **kwargs):
            return [tg2]
        self.p.code_map.update({"G1": _transform_g1, "G2": _transform_g2})
        cases = [
            ["G1 X0 Y0", [tg1]],
            ["G2 X0 Y0", [tg2]],
            ["G3 X0 Y0", ["G3 X0 Y0"]],
        ]
        for case in cases:
            result = self.p._transform_code(case[0])
            self.assertEqual(result, case[1])

    def test_process_file_no_code_map(self):
        lines = [
            "G0 X0 Y0 Z0",
            "G1 X1 Y1 Z1",
            "G2 X2 Y2 Z2",
        ]
        gcodes = lines
        outlines = self.p.process_gcode(gcodes)
        self.assertEqual(gcodes, outlines)

    def test_process_file_code_map(self):
        tg1 = "G1_TRANSFORMED"

        def _transform_g1(*args, **kwargs):
            return tg1
        gcodes = [
            "G0 X0 Y0 Z0",
            "G1 X0 Y0 Z0",
            "G2 X2 Y2 Z2",
        ]
        expected_output = [
            gcodes[0],
            tg1,
            gcodes[2],
        ]
        self.p.code_map.update({"G1": _transform_g1})
        got_output = self.p.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file_empty_iter(self):
        lines = []
        expected_output = []
        got_output = self.p.process_gcode(lines)
        self.assertEqual(got_output, expected_output)


if __name__ == "__main__":
    unittest.main()

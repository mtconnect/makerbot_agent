import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile
import re

import makerbot_driver


class RpmProcessor(unittest.TestCase):

    def setUp(self):
        self.rp = makerbot_driver.GcodeProcessors.RpmProcessor()

    def tearDown(self):
        self.rp = None

    def test_regexs(self):
        cases = [
            ["M101", []],
            ["m101", []],
            [";M101", [";M101"]],
            ["(M101", ["(M101"]],
            ['       M101', []],
            ['(comment) M101', ['(comment) M101']],
            ['(comment) ; M101', ['(comment) ; M101']],
            ["M102", []],
            ["m102", []],
            [";M102", [";M102"]],
            ['       M102', []],
            ["(M102", ["(M102"]],
            ['(comment) M102', ['(comment) M102']],
            ['(comment) ; M102', ['(comment) ; M102']],
            ["M103", []],
            ["m103", []],
            [";M103", [";M103"]],
            ["(M103", ["(M103"]],
            ['       M103', []],
            ['(comment) M103', ['(comment) M103']],
            ['(comment) ; M103', ['(comment) ; M103']],
            ["G1 X0 Y0", ["G1 X0 Y0"]],
            ["G92 X0 Y0", ["G92 X0 Y0"]],
            ["THIS IS A TEST", ["THIS IS A TEST"]],
        ]
        for case in cases:
            self.assertEqual(case[1], self.rp._transform_code(case[0]))

    def test_transform_m108(self):
        input_output_dict = {
            'M108\n': '',
            'M108 R25.1\n': '',
            'M108;comment\n': '',
            'M108 T0\n': 'M135 T0\n',
            'M108 T0 R25.1\n': 'M135 T0\n',
            'M108 T0 R25.1;superCOMMENT\n': 'M135 T0; superCOMMENT\n',
            'M108 T0 (heres a comment) T0\n': 'M135 T0; heres a comment) T0\n',
        }
        for key in input_output_dict:
            match_obj = re.search('.*', key)
            self.assertEqual(
                input_output_dict[key], self.rp._transform_m108(match_obj)
            )

    def test_process_file_can_proces_parsable_file(self):
        #Make input temp file
        gcodes = ["M103\n", "M101\n", "M108 R2.51 T0\n", "M105\n"]
        got_output = self.rp.process_gcode(gcodes)
        expected_output = ["M135 T0\n", "M105\n"]
        self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
    unittest.main()

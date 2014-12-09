import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import makerbot_driver

import unittest
import re

class TestDualProgressUpdater(unittest.TestCase):

    def setUp(self):
        self.dpu = makerbot_driver.GcodeProcessors.DualstrusionProgressProcessor()
        self.prog_regex = self.dpu.code_map.keys()[0]

    def tearDown(self):
        self.dpu = None

    def test_process_gcodes(self):
        incodes = [
            'M135 T0',
            'M73 P1',
            'G1 X0 Y0 Z0',
            'M73 P2',
            'M73 P3', 
            'G1 X1 Y1 Z1',
            'M73 P4',
            'G92 X Y Z',
            'M73 P5',
            'M135 T1',
            'M73 P1',
            'G1 X0 Y0',
            'M73 P2',
            'G92 X Y Z',
            'G92 X Y Z',
            'M73 P3',
            'G1 X0 Y0 Z0',
            'M73 P4',
            'G1 X50 Y50 Z50',
            'M73 P5',
        ]
        expected_codes = [
            'M135 T0',
            'M73 P0.5 (progress (0.5%))\n',
            'G1 X0 Y0 Z0',
            'M73 P1.0 (progress (1.0%))\n',
            'M73 P1.5 (progress (1.5%))\n', 
            'G1 X1 Y1 Z1',
            'M73 P2.0 (progress (2.0%))\n',
            'G92 X Y Z',
            'M73 P2.5 (progress (2.5%))\n',
            'M135 T1',
            'M73 P3.0 (progress (3.0%))\n',
            'G1 X0 Y0',
            'M73 P3.5 (progress (3.5%))\n',
            'G92 X Y Z',
            'G92 X Y Z',
            'M73 P4.0 (progress (4.0%))\n',
            'G1 X0 Y0 Z0',
            'M73 P4.5 (progress (4.5%))\n',
            'G1 X50 Y50 Z50',
            'M73 P5.0 (progress (5.0%))\n',
        ]
        got_codes = self.dpu.process_gcode(incodes)
        self.assertEqual(expected_codes, got_codes)

    def test_transform_progress_all_whole_numbers(self):
        # First tool's progress
        m = re.match(self.prog_regex, 'M73 P1')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes) == 1)
        self.assertEqual('M73 P0.5 (progress (0.5%))\n', got_codes[0])

        m = re.match(self.prog_regex, 'M73 P2')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes) == 1)
        self.assertEqual('M73 P1.0 (progress (1.0%))\n', got_codes[0])

        # Second tool's progress
        m = re.match(self.prog_regex, 'M73 P1')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes) == 1)
        self.assertEqual('M73 P1.5 (progress (1.5%))\n', got_codes[0])

        m = re.match(self.prog_regex, 'M73 P2')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes) == 1)
        self.assertEqual('M73 P2.0 (progress (2.0%))\n', got_codes[0])

    def test_transform_progress_decimal(self):
        m = re.match(self.prog_regex, 'M73 P2.5')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes) == 0)

    def test_transform_progress_good_decimal(self):
        m = re.match(self.prog_regex, 'M73 P2.0')
        got_codes = self.dpu._transform_progress_update(m)
        self.assertTrue(len(got_codes), 1)
        expected_code = 'M73 P0.5 (progress (0.5%))\n'
        self.assertEqual(expected_code, got_codes[0])
    
if __name__ == "__main__":
    unittest.main()

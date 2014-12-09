import sys
import os

sys.path.insert(0, './')

import unittest

import makerbot_driver

class TestFanProcessor(unittest.TestCase):

    def setUp(self):
        self.fan_processor = makerbot_driver.GcodeProcessors.FanProcessor()
        self.long_raft_command = "(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: True </setting>)"

    def tearDown(self):
        self.fan_processor = None

    def test_gather_stats_no_fan_no_raft(self):
        cases = [
            [],
            ['(M126)'],
            ['(M127)'],
            ['G1 X0 Y0 Z0, G92 X1 Y1, G92 X0 Y0 Z0'],
        ]
        expected = {
            'raft': False,
            'fan_codes_exist': False
        }
        for case in cases:
            self.assertEqual(self.fan_processor.gather_stats(case), expected) 

    def test_gather_stats_fan_code_no_raft(self):
        cases = [
            ['M126'],
            ['M127'],
            ['G1 X0 Y0 Z0', 'M126'],
            ['G92 X50 Y68', 'M127'],
            ['(M126', 'M126'],
        ]
        expected = {
            'raft': False,
            'fan_codes_exist': True
        }
        for case in cases:
            self.assertEqual(self.fan_processor.gather_stats(case), expected)

    def test_gather_stats_no_fan_code_raft(self):
        cases = [
            [self.long_raft_command],
            ['G1 X0 Y0 Z0', self.long_raft_command],
            [self.long_raft_command, 'G1 X0 Y0 Z0'],
        ]
        expected = {
            'raft': True,
            'fan_codes_exist': False
        }
        for case in cases:
            self.assertEqual(self.fan_processor.gather_stats(case), expected)

    def test_gather_stats_fan_code_and_raft(self):
        cases = [
            [self.long_raft_command, 'M126'],
            [self.long_raft_command, 'M127'],
            ['M126', self.long_raft_command],
            ['M127', self.long_raft_command],
            ['M126', self.long_raft_command, 'M126'],
            ['M127', self.long_raft_command, 'M127'],
            ['M126', 'G1 X0 Y0 Z0', 'M127', self.long_raft_command],
        ]
        expected = {
            'raft': True,
            'fan_codes_exist': True
        }
        for case in cases:
            self.assertEqual(self.fan_processor.gather_stats(case), expected)

    def test_get_raft_end_location_no_end_tag(self):
        codes = [
            'G1 X0 Y0 Z0',
            'G92 X1 Y1 Z1',
            'M126',
            'M100',
            'M101',
        ]
        got_loc = self.fan_processor.get_raft_end_location(codes)
        expected_loc = 5
        self.assertEqual(expected_loc, got_loc)

    def test_get_raft_end_location_raft_and_print(self):
        codes = [
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z50',
            'G1 X100 Y100 Z100',
            self.fan_processor.expected_raft_tag,
            'G92 X-50 Y-50 Z-50',
            'M126',
            'G1 X50 Y50',
            'G162 X Y Z',
            'G163 X Z A',
            'M127',
            '(lol comment)',
        ]
        got_loc = self.fan_processor.get_raft_end_location(codes)
        expected_loc = 4
        self.assertEqual(expected_loc, got_loc)

    def test_get_raft_end_loc_only_raft(self):
        codes = [
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z50',
            'G1 X100 Y100 Z100',
            'G92 X-50 Y-50 Z-50',
            'G1 X100 Y100 Z100',
            'G92 X-50 Y-50 Z-50',
            self.fan_processor.expected_raft_tag,
        ]
        got_loc = self.fan_processor.get_raft_end_location(codes)
        expected_loc = 7
        self.assertEqual(expected_loc, got_loc)

    def test_get_layer_location_start_beginning(self):
        codes = [
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            'M126',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            'M127',
            'M126',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        cases = [
            [0, 0, 0],
            [3, 0, 3],
            [0, 1, 6],
            [3, 1, 6],
            [6, 1, 9],
            [0, 2, 9],
            [0, 500, 19],
            [500, 0, 19],
            [500, 500, 19],
        ]
        for case in cases:
            self.assertEqual(case[2], self.fan_processor.get_layer_location(case[0], case[1], codes))

    def test_process_gcode_no_raft(self):
        codes = [
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        expected_codes.insert(8, 'M126 T0 (Fan On)\n')
        expected_codes.append('M127 T0 (Fan Off)\n')
        got_codes = self.fan_processor.process_gcode(codes)
        self.assertEqual(expected_codes, got_codes)

    def test_process_gcode_raft(self):
        codes = [
            self.long_raft_command,
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G92 X0 Y0 Z0',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            self.fan_processor.expected_raft_tag,
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        expected_codes.insert(18, 'M126 T0 (Fan On)\n')
        expected_codes.append('M127 T0 (Fan Off)\n')
        got_codes = self.fan_processor.process_gcode(codes)
        self.assertEqual(expected_codes, got_codes)

    def test_process_gcode_fan_codes(self):
        codes = [
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            'M126',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            'M127',
            'M126',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        got_codes = self.fan_processor.process_gcode(codes)
        self.assertEqual(expected_codes, got_codes)

    def test_process_gcode_raft(self):
        codes = [
            self.long_raft_command,
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G92 X0 Y0 Z0',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            self.fan_processor.expected_raft_tag,
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        expected_codes.insert(18, 'M126 T0 (Fan On)\n')
        expected_codes.append('M127 T0 (Fan Off)\n')
        got_codes = self.fan_processor.process_gcode(codes)
        self.assertEqual(expected_codes, got_codes)

if __name__ == "__main__":
    unittest.main()

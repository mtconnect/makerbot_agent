import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import math
import unittest
import tempfile

import makerbot_driver


class TestAnchorProcessor(unittest.TestCase):

    def setUp(self):
        self.ap = makerbot_driver.GcodeProcessors.AnchorProcessor()

    def tearDown(self):
        self.ap = None

    def test_calc_euclidean_distance(self):
        cases = [
            [[0, 0, 0], [0, 0, 0], 0],
            [[1, 1, 1], [0, 0, 0], math.sqrt(3)],
            [[1, 2, 3], [0, 0, 0], math.sqrt(14)],
            [[-1, -2, -3], [0, 0, 0], math.sqrt(14)],
            [[1, 1, 1], [1, 1, 1], 0],
        ]
        for case in cases:
            self.assertEqual(
                self.ap.calc_euclidean_distance(case[0], case[1]), case[2])

    def test_get_start_position(self):
        expected_start_position = 'G1 X-112 Y-73 Z150 F3300.0 (move to waiting position)'
        got_start_position = self.ap.get_start_position()
        self.assertEqual(expected_start_position, got_start_position)

    def test_get_start_position_with_profile(self):
        expected_start_position = 'G1 X0 Y0 Z1 F3300.0 (move to waiting position)'
        # quick, mock profile
        class profile():
            def __init__(self):
                self.values = {
                    'print_start_sequence' : {
                        'start_position' : {
                            'start_x' : 0,
                            'start_y' : 0,
                            'start_z' : 1
                        }
                    }
                }
        self.ap.profile = profile()
        got_start_position = self.ap.get_start_position()
        self.assertEqual(expected_start_position, got_start_position)

    def test_get_extruder(self):
        cases = [
            [['G', 'A', 'X'], 'A'],
            [['G', 'B', 'X'], 'B'],
            [['G', 'E', 'X'], 'E'],
            [['G'], 'A'],
        ]
        for case in cases:
            got_extruder = self.ap.get_extruder(case[0])
            self.assertEqual(case[1], got_extruder)

    def test_find_extrusion_distance_no_distance(self):
        codes = {
            'X': 0,
            'Y': 0,
            'Z': 1,
        }
        expected_distance = 0
        got_distance = self.ap.find_extrusion_distance(codes, codes)
        self.assertEqual(expected_distance, got_distance)

    def test_find_extrusion_distance_distance_is_one(self):
        layer_height = 1
        start_codes = {
            'X': 0,
            'Y': 0,
            'Z': layer_height,
        }
        end_codes = {
            'X': 1,
            'Y': 0,
            'Z': layer_height,
        }
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height)
        got_distance = self.ap.find_extrusion_distance(start_codes, end_codes)
        self.assertEqual(expected_distance, got_distance)

    def test_find_extrusion_distance_is_two(self):
        layer_height = 1
        start_codes = {
            'X': 0,
            'Y': 0,
            'Z': layer_height,
        }
        end_codes = {
            'X': 2,
            'Y': 0,
            'Z': layer_height,
        }
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height) * 2
        got_distance = self.ap.find_extrusion_distance(start_codes, end_codes)
        self.assertEqual(expected_distance, got_distance)

    def test_create_anchor_command_no_distance_no_extruder_axis(self):
        start_position = "G1 X0 Y0 Z1"
        end_position = "G1 X0 Y0 Z1"
        expected_anchor_commands = ["G1 X0 Y0 Z1 F1000 E0.0\n", "G92 E0\n"]

        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_create_anchor_command_no_distance_e_extruder_axis(self):
        start_position = "G1 X0 Y0 Z1"
        end_position = "G1 X0 Y0 Z1 E10"
        expected_anchor_commands = ["G1 X0 Y0 Z1 F1000 E0.0\n", "G92 E0\n"]
        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_create_anchor_command_no_distance_b_extruder_axis(self):
        start_position = "G1 X0 Y0 Z1"
        end_position = "G1 X0 Y0 Z1 B10"
        expected_anchor_commands = ["G1 X0 Y0 Z1 F1000 E0.0\n", "G92 E0\n"]
        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_create_anchor_command_distance_is_one(self):
        start_position = "G1 X0 Y0 Z1"
        end_position = "G1 X0 Y1 Z1"
        layer_height = 1
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height)
        # Do a str concatenation since %i rounds to 6 places
        expected_anchor_commands = [
            "G1 X0 Y1 Z1 F1000 E" + str(expected_distance) + "\n", "G92 E0\n"]
        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_create_anchor_command_distance_is_two(self):
        start_position = "G1 X0 Y0 Z1"
        end_position = "G1 X0 Y2 Z1"
        distance = 2
        layer_height = 1
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height) * distance
        # Do a str concatenation since %i rounds to 6 places
        expected_anchor_commands = [
            "G1 X0 Y2 Z1 F1000 E" + str(expected_distance) + "\n", "G92 E0\n"]
        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_create_anchor_command_distance_is_two_z_distance_greater_than_0(self):
        start_position = "G1 X0 Y0 Z100"
        end_position = "G1 X0 Y2 Z1"
        distance = 2
        layer_height = 1
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height) * distance
        # Do a str concatenation since %i rounds to 6 places
        expected_anchor_commands = [
            "G1 Z%f F1000\n" % (1),
            "G1 X0 Y2 Z1 F1000 E" + str(expected_distance) + "\n",
            "G92 E0\n"
        ]
        got_anchor_commands = self.ap.create_anchor_command(
            start_position, end_position)
        self.assertEqual(expected_anchor_commands, got_anchor_commands)

    def test_process_file(self):
        distance = self.ap.calc_euclidean_distance(
            [-112, -73], [0, 5])
        layer_height = .5
        expected_distance = self.ap.feed_cross_section_area(
            layer_height, self.ap.width_over_height) * distance
        gcodes = [
            "G1 X0 Y5 Z0.5 F5000\n",
            "G1 X50 Y100 Z200"
        ]
        got_gcodes = self.ap.process_gcode(gcodes)
        expected_codes = [
            "G1 Z%f F1000\n" % (.5),
            "G1 X0 Y5 Z0.5 F1000 E" + str(expected_distance) + "\n",
            "G92 E0\n",
            "G1 X0 Y5 Z0.5 F5000\n",
            "G1 X50 Y100 Z200"
        ]
        self.assertEqual(expected_codes, got_gcodes)

    def test_create_z_move_if_necessary_no_delta(self):
        start_codes = {'Z': 0}
        end_codes = {'Z': 0}
        self.assertEqual(
            [], self.ap.create_z_move_if_necessary(start_codes, end_codes))

    def test_create_z_move_if_necessary_delta(self):
        d = .5
        start_codes = {'Z': 100}
        end_codes = {'Z': d}
        expected_codes = ['G1 Z%f F1000\n' % (d)]
        self.assertEqual(expected_codes, self.ap.create_z_move_if_necessary(
            start_codes, end_codes))

if __name__ == "__main__":
    unittest.main()

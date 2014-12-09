import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import time

import makerbot_driver


class s3gHelperFunctionTests(unittest.TestCase):
    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()

    def tearDown(self):
        self.g = None

    def test_get_position_unspecified_axis_location(self):
        setattr(self.g.position, 'X', None)
        self.assertRaises(makerbot_driver.Gcode.UnspecifiedAxisLocationError,
                          self.g.get_position)

    def test_get_position_no_offsets(self):
        position = {
            'X': 0,
            'Y': 1,
            'Z': 2,
            'A': 3,
            'B': 4,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        self.g.ofset_register = None
        expectedPosition = [0, 1, 2, 3, 4]
        self.assertEqual(expectedPosition, self.g.get_position())

    def test_lose_position(self):
        position = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = ['X', 'Y', 'Z', 'A', 'B']
        self.g.lose_position(axes)
        for axis in axes:
            self.assertEqual(getattr(self.g.position, axis), None)

    def test_lose_position_no_axes(self):
        position = {
            'X': 0,
            'Y': 0,
            'Z': 0,
            'A': 0,
            'B': 0,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = []
        self.g.lose_position(axes)
        for axis in ['X', 'Y', 'Z', 'A', 'B']:
            self.assertEqual(getattr(self.g.position, axis), 0)

    def test_lose_position_minimal_codes(self):
        position = {
            'X': 0,
            'Y': 0,
            'Z': 0,
            'A': 0,
            'B': 0,
        }
        for key in position:
            setattr(self.g.position, key, position[key])
        axes = ['X']
        self.g.lose_position(axes)
        self.assertEqual(None, getattr(self.g.position, 'X'))
        for axis in ['Y', 'Z', 'A', 'B']:
            self.assertEqual(0, getattr(self.g.position, axis))

    def test_set_build_name(self):
        build_name = 'test'
        self.g.set_build_name(build_name)
        self.assertEqual(self.g.values['build_name'], build_name)

    def test_set_build_name_non_string(self):
        build_name = 9
        self.assertRaises(TypeError, self.g.set_build_name, build_name)

    def test_set_position_no_axes(self):
        codes = {}
        self.g.set_position(codes)
        expected_position = [None, None, None, None, None]
        self.assertEqual(expected_position, self.g.position.ToList())

    def test_set_position_e_and_a_codes(self):
        codes = {
            'E': 0,
            'A': 0,
        }
        self.assertRaises(makerbot_driver.Gcode.ConflictingCodesError,
                          self.g.set_position, codes)

    def test_set_position_e_and_b_codes(self):
        codes = {
            'E': 0,
            'B': 0,
        }
        self.assertRaises(makerbot_driver.Gcode.ConflictingCodesError,
                          self.g.set_position, codes)

    def test_set_position_e_and_a_and_b_codes(self):
        codes = {
            'E': 0,
            'A': 0,
            'B': 0,
        }
        self.assertRaises(makerbot_driver.Gcode.ConflictingCodesError,
                          self.g.set_position, codes)

    def test_set_position_e_code_no_tool_index(self):
        codes = {'E': 0}
        self.assertRaises(makerbot_driver.Gcode.NoToolIndexError,
                          self.g.set_position, codes)

    def test_set_position_e_code_tool_index_1(self):
        codes = {'E': 2}
        self.g.values['tool_index'] = 1
        self.g.set_position(codes)
        expected_position = [None, None, None, None, 2]
        self.assertEqual(expected_position, self.g.position.ToList())

    def test_set_position_e_code_tool_index_2(self):
        codes = {'E': 2}
        self.g.values['tool_index'] = 0
        self.g.set_position(codes)
        expected_position = [None, None, None, 2, None]
        self.assertEqual(expected_position, self.g.position.ToList())

    def test_set_position_a_and_b_codes(self):
        codes = {
            'A': 3,
            'B': 4,
        }
        self.g.set_position(codes)
        expected_position = [None, None, None, 3, 4]
        self.assertEqual(expected_position, self.g.position.ToList())

    def test_set_position_x_y_z(self):
        codes = {
            'X': 0,
            'Y': 1,
            'Z': 2,
        }
        self.g.set_position(codes)
        expected_position = [0, 1, 2, None, None]
        self.assertEqual(expected_position, self.g.position.ToList())

    def test_set_position_extra_codes(self):
        codes = {
            'X': 0,
            'Y': 1,
            'Z': 2,
            'A': 3,
            'B': 4,
            'Q': -1,
        }
        self.g.set_position(codes)
        expected_position = [0, 1, 2, 3, 4]
        self.assertEqual(expected_position, self.g.position.ToList())


class TestProfileInformationParsing(unittest.TestCase):

    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorDual')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_values_key_error(self):
        key = 'this_is_going_to_fail_;('
        self.assertRaises(KeyError, self.g.get_axes_values, key)

    def test_get_axes_values(self):
        key = 'steps_per_mm'
        expected_values = [
            94.139704,
            94.139704,
            400,
            -96.275,
            -96.275,
        ]
        self.assertEqual(expected_values, self.g.get_axes_values(key))


class MachineProfileWith4Axes(unittest.TestCase):
    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorSingle')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_values_with_one_0(self):
        key = 'steps_per_mm'
        expected_values = [
            94.139704,
            94.139704,
            400,
            -96.275,
            0,
        ]
        self.assertEqual(expected_values, self.g.get_axes_values(key))


class GetAxesFeedrateSPM(unittest.TestCase):

    def setUp(self):
        self.g = makerbot_driver.Gcode.GcodeStates()
        profile = makerbot_driver.Profile('ReplicatorDual')
        self.g.profile = profile

    def tearDown(self):
        self.g = None

    def test_get_axes_feedrate_and_spm_non_listed_axes(self):
        axes = 'XYZ'
        self.assertRaises(ValueError, self.g.get_axes_feedrate_and_SPM, axes)

    def test_get_axes_feedrate_and_spm_no_axes(self):
        axes = []
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        for l in (feedrate, spm):
            self.assertEqual(l, [])

    def test_get_axes_feedrate_and_spm_bad_axes(self):
        axes = ['q']
        self.assertRaises(KeyError, self.g.get_axes_feedrate_and_SPM, axes)

    def test_get_axes_feedrate_and_spm_one_axis(self):
        axes = ['X']
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        expected_feedrate = [12450]
        expected_spm = [94.139704]
        self.assertEqual(expected_feedrate, feedrate)
        self.assertEqual(expected_spm, spm)

    def test_get_axes_feedrate_and_spm_many_axes(self):
        axes = ['X', 'Y', 'Z']
        feedrate, spm = self.g.get_axes_feedrate_and_SPM(axes)
        expected_feedrate = [12450, 12450, 1170]
        expected_spm = [94.139704, 94.139704, 400]
        self.assertEqual(expected_feedrate, feedrate)
        self.assertEqual(expected_spm, spm)


if __name__ == "__main__":
    unittest.main()

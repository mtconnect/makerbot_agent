import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io

import makerbot_driver


class TestPoint(unittest.TestCase):

    def test_to_list_no_changes(self):
        expected_position = [None, None, None, None, None]
        p = makerbot_driver.Gcode.Point()
        self.assertEqual(expected_position, p.ToList())

    def test_to_list_position_chagned(self):
        p = makerbot_driver.Gcode.Point()
        setattr(p, 'X', 10)
        expected_position = [10, None, None, None, None]
        self.assertEqual(expected_position, p.ToList())

    def test_set_point_no_codes(self):
        expected_position = [None, None, None, None, None]
        p = makerbot_driver.Gcode.Point()
        p.SetPoint({})
        self.assertEqual(expected_position, p.ToList())

    def test_set_point_extraneous_codes(self):
        expected_position = [None, None, None, None, None]
        p = makerbot_driver.Gcode.Point()
        codes = {
            'Q': 0,
            'R': 1,
            'S': 2,
        }
        p.SetPoint(codes)
        self.assertEqual(expected_position, p.ToList())

    def test_set_point_one_axis(self):
        expected_position = [0, None, None, None, None]
        p = makerbot_driver.Gcode.Point()
        codes = {'X': 0}
        p.SetPoint(codes)
        self.assertEqual(expected_position, p.ToList())

    def test_set_point_all_axis(self):
        expected_position = [1, 2, 3, 4, 5]
        p = makerbot_driver.Gcode.Point()
        codes = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        p.SetPoint(codes)
        self.assertEqual(expected_position, p.ToList())

    def test_copy(self):
        point = makerbot_driver.Gcode.Point()
        copy_point = point.copy()
        self.assertEqual(point.ToList(), copy_point.ToList())
        copy_point.X = 50
        self.assertNotEqual(point.ToList(), copy_point.ToList())

if __name__ == '__main__':
    unittest.main()

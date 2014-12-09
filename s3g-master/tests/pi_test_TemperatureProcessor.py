import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestGetTemperatureProcessor(unittest.TestCase):

    def setUp(self):
        self.gp = makerbot_driver.GcodeProcessors.GetTemperatureProcessor()

    def tearDown(self):
        self.gp = None

    def test_regex(self):
        cases = [
            ["     M105", []],
            ["M105\n", []],
            ["M105(comments)\n", []],
            ["(comments comments)   M105", ["(comments comments)   M105"]],
            ["G1 X0 Y0", ["G1 X0 Y0"]],
            ["G92 X0 Y0", ["G92 X0 Y0"]],
            ["THIS IS A TEST", ["THIS IS A TEST"]],
        ]
        for case in cases:
            self.assertEqual(case[1], self.gp._transform_code(case[0]))

class TestSetTemperatureProcessor(unittest.TestCase):

    def setUp(self):
        self.sp = makerbot_driver.GcodeProcessors.SetTemperatureProcessor()

    def tearDown(self):
        self.sp = None

    def test_regex(self):
        cases = [
            ["M104 S500\n", []],
            ["M104\n", []],
            ["M104(comments)\n", []],
            ["", []],
            ["(comments comments)   M104", ["(comments comments)   M104"]],
            ["G1 X0 Y0", ["G1 X0 Y0"]],
            ["G92 X0 Y0", ["G92 X0 Y0"]],
            ["THIS IS A TEST", ["THIS IS A TEST"]],
        ]
        
        for case in cases:
            self.assertEqual(case[1], self.sp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()

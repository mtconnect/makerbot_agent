import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestABPProcessor(unittest.TestCase):

    def setUp(self):
        self.abp = makerbot_driver.GcodeProcessors.AbpProcessor()

    def tearDown(self):
        self.abp = None

    def test_regexs(self):
        cases = [
            ['M107\n', []],
            ['M107', []],
            ['m107', []],
            ['    m107', []],
            ['(M107', ['(M107']],
            [';M107', [';M107']],
            ['(comments)    M107', ['(comments)    M107']],
            ['M106\n', []],
            ['M106', []],
            ['m106', []],
            ['     m106', []],
            ['(M106', ['(M106']],
            [';M106', [';M106']],
            ['(comments)M106', ['(comments)M106']],
            ['G1 X0 Y0', ['G1 X0 Y0']],
            ['G92 X0 Y0', ['G92 X0 Y0']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.abp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()

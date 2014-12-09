import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestRemoveProgressProcessor(unittest.TestCase):

    def setUp(self):
        self.abp = makerbot_driver.GcodeProcessors.RemoveProgressProcessor()

    def tearDown(self):
        self.abp = None

    def test_regexs(self):
        cases = [
            ['M73\n', []],
            ['M73', []],
            ['m73', []],
            ['(M73', ['(M73']],
            [';M73', [';M73']],
            ['       M73', []],
            ['(comment) M73', ['(comment) M73']],
            ['(comment) ; M73', ['(comment) ; M73']],
            ['M136\n', []],
            ['M136', []],
            ['m136', []],
            ['       M136', []],
            ['(M136', ['(M136']],
            [';M136', [';M136']],
            ['(comment) M136', ['(comment) M136']],
            ['(comment) ; M136', ['(comment) ; M136']],
            ['M137\n', []],
            ['M137', []],
            ['m137', []],
            ['       M137', []],
            ['(M137', ['(M137']],
            [';M137', [';M137']],
            ['(comment) M137', ['(comment) M137']],
            ['(comment) ; M137', ['(comment) ; M137']],
            ['G1 X0 Y0', ['G1 X0 Y0']],
            ['G92 X0 Y0', ['G92 X0 Y0']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.abp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()

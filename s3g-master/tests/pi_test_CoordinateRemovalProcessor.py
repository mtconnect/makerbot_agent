import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestCoordinateRemovalProcessor(unittest.TestCase):

    def setUp(self):
        self.cp = makerbot_driver.GcodeProcessors.CoordinateRemovalProcessor()

    def tearDown(self):
        self.cp = None

    def test_regexs(self):
        cases = [
            ['G54\n', [], ],
            [';G54', [';G54']],
            ['(G54', ['(G54']],
            ['g54', []],
            ['(comment)    G54', ['(comment)    G54']],
            ['       G54', []],
            ['G55\n', []],
            [';G55', [';G55']],
            ['(G55', ['(G55']],
            ['g55', []],
            ['       G55', []],
            ['(comment) G55', ['(comment) G55']],
            [';G10', [';G10']],
            ['(G10', ['(G10']],
            ['g10', []],
            ["G10\n", []],
            ['       G10', []],
            ['(comment) G10', ['(comment) G10']],
            ["G90\n", []],
            [';G90', [';G90']],
            ['(G90', ['(G90']],
            ['g90', []],
            ['       G90', []],
            ['(comment) G90', ['(comment) G90']],
            ["G11\n", ["G11\n"]],
            ["G21\n", []],
            [';G21', [';G21']],
            ['(G21', ['(G21']],
            ['g21', []],
            ['       G21', []],
            ['(comment) G21', ['(comment) G21']],
            ['G1 X0 Y0', ['G1 X0 Y0']],
            ['G92 X0 Y0', ['G92 X0 Y0']],
            ['THIS IS A TEST', ['THIS IS A TEST']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.cp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()

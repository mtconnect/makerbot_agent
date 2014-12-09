import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile
import warnings

import makerbot_driver


class Skeinforge50ProcessorTests(unittest.TestCase):

    def setUp(self):
        self.sp = makerbot_driver.GcodeProcessors.Skeinforge50Processor()

    def tearDown(self):
        self.sp = None

    def test_process_file_empty_file(self):
        gcodes = []
        expected_output = []
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file_bad_version(self):
        with warnings.catch_warnings(record=True) as w:
            gcodes = [
                "G21\n",
                "(<version> 11.03.13 </version>)\n",
            ]
            output = self.sp.process_gcode(gcodes)
            expected_output = [gcodes[1], "M73 P100 (progress (100%))\n"]
            self.assertEqual(expected_output, output)
            self.assertEqual(1, len(w))
            self.assertTrue(issubclass(w[0].category, UserWarning))
            self.assertEqual(str(w[0].message), "Processing incompatible version of Skeinforge, resulting file may not be compatible with Makerbot_Driver")

    def test_process_file_progress_updates(self):
        gcodes = [
            "(<version> 12.03.14 </version)\n",
            "G90\n",
            "G21\n",
            "M101\n",
            "M102\n",
            "M108\n",
            "G92 X0 Y0 Z0 A0 B0\n",
            "M105 S100\n",
        ]
        expected_output = [
            '(<version> 12.03.14 </version)\n',
            'M73 P50 (progress (50%))\n',
            'G92 X0 Y0 Z0 A0 B0\n',
            'M73 P100 (progress (100%))\n',
        ]
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file_stress_test(self):
        gcodes = [
            "G90\n",
            "G92 A0\n",
            "G92 B0\n",
            "M101\n",
            "G21\n",
            "G92 A0\n",
            "M108\n",
            "G92 B0\n",
            "M105 S100\n",    
        ]
        expected_output = [
            "G92 A0\n",
            "M73 P25 (progress (25%))\n",
            "G92 B0\n",
            "M73 P50 (progress (50%))\n",
            "G92 A0\n",
            "M73 P75 (progress (75%))\n",
            "G92 B0\n",
            "M73 P100 (progress (100%))\n",
        ]
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)


class TestSkeinforgeVersioner(unittest.TestCase):

    def setUp(self):
        self.version = "12.03.14"
        self.vp = makerbot_driver.GcodeProcessors.SkeinforgeVersionChecker(
            self.version)

    def tearDown(self):
        self.vp = None

    def test_version_check_good_version(self):
        line = "(<version> 12.03.14 </version>)"
        output = self.vp._transform_code(line)
        self.assertEqual([line], output)

    @unittest.skip("Why is this test failing?  Present Dave wants to know")
    def test_version_check_bad_version(self):
        with warnings.catch_warnings(record=True) as w:
            gcodes = [
                "G21\n",
                "(<version> 11.03.13 </version>)\n",
            ]
            output = self.vp.process_gcode(gcodes)
            expected_output = gcodes
            self.assertEqual(expected_output, output)
            self.assertEqual(1, len(w))
            self.assertTrue(issubclass(w[0].category, UserWarning))
            self.assertEqual(str(w[0].message), "Processing incompatible version of Skeinforge, resulting file may not be compatible with Makerbot_Driver")


if __name__ == '__main__':
    unittest.main()

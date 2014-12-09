import os
import sys
import unittest
import re

sys.path.append(os.path.abspath('../../s3g'))
import makerbot_driver

class TestEmptyLayerProcessor(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.EmptyLayerProcessor()
    
    def tearDown(self):
        self.p = None

    def test_regex(self):
        self.test_layer_start()
        self.test_move_gcode()
        self.test_SF_layer_end_gcode()
        self.test_MG_nominal_comment_gcode()

    #simple smoke tests for RegExes
    def test_layer_start(self):
        layer_start_cases = [
            ["(Slice 266 adfdafdf)", True, "(Slice 266 adfdafdf)"],
            ["(<layer> 12.8675 adkkfj)", True, "(<layer> 12.8675 adkkfj)"],
            ["(<layer> 12.8675", False, None],
            ["(Slice)", False, None],
            ["(layer 12.8675)", False, None],
            ["(Slice<layer> 12.65)", False, None],
            ["(12)", False, None],
            ["(Slice 2.678 hellothere))))))))", True, "(Slice 2.678 hellothere))))))))"]
        ]
        for case in layer_start_cases:
            match = re.match(self.p.layer_start, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_move_gcode(self):
        move_gcode_cases = [
            ["G1 X0 Y0 Z0 F600 A1200", True, "G1 X0 Y0 Z0 F600 A1200"],
            [";M135 T9", False, None],
            ["G1 F1200 E3600", True, "G1 F1200 E3600"],
            ["G1 T0", True, "G1 T0"],
            ["G1 ", True, "G1 "],
            ["M135", False, None],
            ["H12", False, None],
            ["Harvey", False, None]
        ]
        for case in move_gcode_cases:
            match = re.match(self.p.move_gcode, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_SF_layer_end_gcode(self):
        SF_layer_end_cases = [
            ["(</layer>)", True, "(</layer>)"],
            ["(</layer>)()()()()()", True, "(</layer>)"],
            ["t(</layer>)", False, None],
            ["M135", False, None],
            ["(</layer>", False, None],
        ]
        for case in SF_layer_end_cases:
            match = re.match(self.p.SF_layer_end, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_MG_nominal_comment_gcode(self):
        MG_nominal_comment_cases = [
            ["(Slowing to 0% of nominal speeds)", True, "(Slowing to 0% of nominal speeds)"],
            ["(Slowing to 0\% of nominal speeds)", False, None],
            ["t(Slowing to 0% of nominal speeds)", False, None],
            ["M135", False, None],
            ["(Slowing to 0% of nominal speeds)$", True, "(Slowing to 0% of nominal speeds)"]
        ]
        for case in MG_nominal_comment_cases:
            match = re.match(self.p.MG_nominal_comment, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])


    def test_process_file(self):
    #TODO update this to work with new formatting
        pass
    '''
        #SKEINFORGE TEST
        gcode_file = open(os.path.abspath('tests/test_files/sf_empty_slice_input.gcode'), 'r')
        in_gcodes = list(gcode_file)
        expected_out =  open(os.path.abspath('tests/test_files/sf_empty_slice_expect.gcode'), 'r')
        expected_gcodes = list(expected_out)

        got_gcodes = self.p.process_gcode(in_gcodes)
        self.assertEqual(expected_gcodes, got_gcodes)
        #MIRACLE GRUE TEST
        gcode_in_path = os.path.abspath('tests/test_files/mg_test_in.gcode')
        gcode_emptied_path = os.path.abspath('tests/test_files/mg_test_postempty.gcode')
        gcode_expected_path = os.path.abspath('tests/test_files/mg_test_emptied.gcode')

        self.p.process_gcode(gcode_in_path, outfile=gcode_emptied_path)

        gcode_out = open(gcode_emptied_path, 'r')
        out_gcodes = list(gcode_out)
        expected_out =  open(gcode_expected_path, 'r')
        expected_gcodes = list(expected_out)

        self.assertEqual(expected_gcodes, out_gcodes)
    '''


if __name__ == '__main__':
    unittest.main()

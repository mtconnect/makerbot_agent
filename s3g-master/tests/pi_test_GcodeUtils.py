import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import glob
import unittest
import string
import mock
import math

import makerbot_driver


class ExtractCommentsTests(unittest.TestCase):
    def test_empty_string(self):
        line = ''
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert '' == comment

    def test_semicolon_only(self):
        line = ';'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert '' == comment

    def test_semicolon_with_data(self):
        line = ';;asdf'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        self.assertEqual('', command)
        self.assertEqual(';asdf', comment)

    def test_parens_after_semicolon_ignored(self):
        line = ';)))'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert ')))' == comment

    def test_right_paren_only(self):
        line = '('
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert '' == comment

    def test_right_paren_with_comment(self):
        line = '(comment'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        self.assertEqual('', command)
        self.assertEqual('comment', comment)

    def test_closed_parens(self):
        line = '()'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert ')' == comment

    def test_closed_parens_with_nested_parens(self):
        line = '(())'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        assert '' == command
        assert '())' == comment

    def test_command_closed_parens_with_comment(self):
        line = 'commanda(comment)commandb'

        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        self.assertEqual('commanda', command)
        self.assertEqual('comment)commandb', comment)

    def test_comment_left_and_semicolon(self):
        line = 'asdf(qwer);testing'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        self.assertEqual('asdf', command)
        self.assertEqual('qwer)testing', comment)

    def test_command_right(self):
        line = 'asdf (qwer)'
        [command, comment] = makerbot_driver.Gcode.extract_comments(line)
        self.assertEqual('asdf ', command)
        self.assertEqual('qwer)', comment)


class ParseCommandTests(unittest.TestCase):
    def test_empty_string(self):
        command = ''

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        assert {} == codes
        assert [] == flags

    def test_garbage_code(self):
        cases = [
            '1',
            '~',
        ]

        for command in cases:
            self.assertRaises(makerbot_driver.Gcode.InvalidCodeError,
                              makerbot_driver.Gcode.parse_command, command)

    def test_single_code_garbage_value(self):
        cases = [
            'Ga',
            'G1a',
            'G12345a',
            'G1..0',
            'G1,0',
        ]

        for command in cases:
            self.assertRaises(
                ValueError, makerbot_driver.Gcode.parse_command, command)

    def test_single_flag_accepts_lowercase(self):
        command = 'g'
        expected_codes = {}
        expected_flags = ['G']

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)

    def test_single_flag(self):
        command = 'G'
        expected_codes = {}
        expected_flags = ['G']

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)

    def test_single_integer_code(self):
        command = 'G0'
        expected_codes = {'G': 0}
        expected_flags = []

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)
        self.assertEquals(int, type(codes['G']))

    def test_single_float_code(self):
        command = 'G0.1234'
        expected_codes = {'G': 0.1234}
        expected_flags = []

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)
        self.assertEquals(float, type(codes['G']))

    def test_single_integer_code_leading_whitespace(self):
        command = '\t\t\t G0'
        expected_codes = {'G': 0}
        expected_flags = []

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)
        self.assertEquals(int, type(codes['G']))

    def test_repeated_code(self):
        command = 'G0 G0'
        self.assertRaises(makerbot_driver.Gcode.RepeatCodeError,
                          makerbot_driver.Gcode.parse_command, command)

    def test_reject_both_g_and_m_code_g_then_m(self):
        command = 'G0 M0'
        self.assertRaises(makerbot_driver.Gcode.MultipleCommandCodeError,
                          makerbot_driver.Gcode.parse_command, command)

    def test_reject_both_g_and_m_code_m_then_g(self):
        command = 'M0 G0'
        self.assertRaises(makerbot_driver.Gcode.MultipleCommandCodeError,
                          makerbot_driver.Gcode.parse_command, command)

    def test_many_codes_and_flags(self):
        command = 'M0 X1.1 Y2.2 Z3.3 F4.4 A B'
        expected_codes = {
            'M': 0,
            'X': 1.1,
            'Y': 2.2,
            'Z': 3.3,
            'F': 4.4,
        }
        expected_flags = ['A', 'B']

        codes, flags = makerbot_driver.Gcode.parse_command(command)
        self.assertEquals(expected_codes, codes)
        self.assertEquals(expected_flags, flags)
        for code in zip(expected_codes.values(), codes.values()):
            self.assertEquals(type(code[0]), type(code[1]))


class CheckForExtraneousCodesTests(unittest.TestCase):
    def test_no_codes(self):
        codes = {}
        allowed_codes = ''
        makerbot_driver.Gcode.check_for_extraneous_codes(codes, allowed_codes)

    def test_extra_code_with_g_code(self):
        codes = {'G': 0, 'X': 0}
        allowed_codes = 'X'
        makerbot_driver.Gcode.check_for_extraneous_codes(
            codes.keys(), allowed_codes)

    def test_extra_code_With_m_code(self):
        codes = {'M': 0, 'X': 0}
        allowed_codes = 'X'
        makerbot_driver.Gcode.check_for_extraneous_codes(
            codes.keys(), allowed_codes)

    def test_extra_code_no_allowed_codes(self):
        codes = {'X': 0}
        allowed_codes = ''
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError, makerbot_driver.Gcode.check_for_extraneous_codes, codes.keys(), allowed_codes)

    def test_extra_code_some_allowed_codes(self):
        codes = {'X': 0, 'A': 2}
        allowed_codes = 'XYZ'
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError, makerbot_driver.Gcode.check_for_extraneous_codes, codes.keys(), allowed_codes)

    def test_all_allowed_codes(self):
        codes = {'X': 0, 'Y': 2, 'Z': 3}
        allowed_codes = 'XYZ'
        makerbot_driver.Gcode.check_for_extraneous_codes(
            codes.keys(), allowed_codes)

    def test_fewer_than_all_allowed_codes(self):
        codes = {'X': 0, 'Y': 2}
        allowed_codes = 'XYZ'
        makerbot_driver.Gcode.check_for_extraneous_codes(
            codes.keys(), allowed_codes)


class ParseOutAxesTests(unittest.TestCase):
    def test_empty_set(self):
        codes = {}
        parsed_axes = makerbot_driver.Gcode.parse_out_axes(codes)
        self.assertEqual([], parsed_axes)

    def test_parse_out_axes_reject_non_axis(self):
        non_axes = set(string.uppercase) - set('XYZAB')

        for non_axis in non_axes:
            parsed_axes = makerbot_driver.Gcode.parse_out_axes([non_axis])
            self.assertEquals(parsed_axes, [])

    def test_parse_out_axes_single_axis(self):
        codes = {'X': True}
        parsed_axes = makerbot_driver.Gcode.parse_out_axes(codes)
        self.assertEqual(['X'], parsed_axes)

    def test_parse_out_axes(self):
        codes = {'X': True, 'Y': True, 'Z': True, 'A': True, 'B': True}
        parsedAxes = makerbot_driver.Gcode.parse_out_axes(codes)
        self.assertEqual(['A', 'B', 'X', 'Y', 'Z'], parsedAxes)


class CalculateVectorMagnitudeTests(unittest.TestCase):
    def test_reject_non_5d_lists(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.calculate_vector_magnitude, range(0, 4))

    def test_makes_good_results(self):
        cases = [
            [[0, 0, 0, 0, 0], 0],
            [[1234.1, 0, 0, 0, 0], 1234.1],
            [[1, -2, 3, -4, 5], pow(55, .5)],
        ]

        for case in cases:
            self.assertEquals(case[1], makerbot_driver.Gcode.calculate_vector_magnitude(case[0]))


class CalculateVectorDifferenceTests(unittest.TestCase):
    def test_reject_non_5d_list_4_and_5(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.calculate_vector_difference, range(4), range(5))

    def test_reject_non_5d_list_5_and_4(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.calculate_vector_difference, range(5), range(4))

    def test_good_result(self):
        cases = [
            [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
            [[1, 2, 3, 4, 5], [-1, -2, -3, -4, -5], [2, 4, 6, 8, 10]],
            [[6, 7, 8, 9, 10], [1, 2, 3, 4, 5], [5, 5, 5, 5, 5]],
        ]

        for case in cases:
            diff = makerbot_driver.Gcode.calculate_vector_difference(
                case[0], case[1])
            self.assertEqual(case[2], diff)


class CalculateUnitVectorTests(unittest.TestCase):
    def test_reject_non_5d_list(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.calculate_unit_vector, range(4))

    def test_null_vector(self):
        vector = [0, 0, 0, 0, 0]
        expected_unit_vector = [0, 0, 0, 0, 0]

        unit_vector = makerbot_driver.Gcode.calculate_unit_vector(vector)
        self.assertEquals(expected_unit_vector, unit_vector)

    def test_good_result(self):
        cases = [
            [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0]],
            [[-1, 0, 0, 0, 0], [-1, 0, 0, 0, 0]],
            [[1, -2, 3, -4, 5], [1 / pow(55, .5), -2 / pow(
                                 55, .5), 3 / pow(
                                     55, .5), -4 / pow(
                                         55, .5), 5 / pow(55, .5)]],
        ]

        for case in cases:
            unit_vector = makerbot_driver.Gcode.calculate_unit_vector(case[0])
            self.assertEqual(case[1], unit_vector)


class GetSafeFeedrateTests(unittest.TestCase):
    def test_reject_non_5d_list(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.get_safe_feedrate, range(4), range(5), 0)

    def test_zero_displacement(self):
        point = [0, 0, 0, 0, 0]
        max_feedrates = [1, 1, 1, 1, 1]
        feedrate = 1
        self.assertRaises(makerbot_driver.Gcode.VectorLengthZeroError, makerbot_driver.Gcode.get_safe_feedrate, point, max_feedrates, feedrate)

    def test_negative_feedrate(self):
        point = [1, 1, 1, 1, 1]
        max_feedrates = [1, 1, 1, 1, 1]
        feedrate = -1
        self.assertRaises(makerbot_driver.Gcode.InvalidFeedrateError, makerbot_driver.Gcode.get_safe_feedrate, point, max_feedrates, feedrate)

    def test_zero_feedrate(self):
        point = [1, 1, 1, 1, 1]
        max_feedrates = [1, 1, 1, 1, 1]
        feedrate = 0
        self.assertRaises(makerbot_driver.Gcode.InvalidFeedrateError, makerbot_driver.Gcode.get_safe_feedrate, point, max_feedrates, feedrate)

    def test_good_result(self):
        # Note: All of these cases use integers, and would fail if the float() casts
        #       were to be remvoed from get_safe_feedrate. Try it.
        cases = [
            [[1, 0, 0, 0, 0],    # Single axis: Move under the max feedrate
             [10, 0, 0, 0, 0],
             1, 1],
            [[11, 0, 0, 0, 0],    # Single axis: Move at the max feedrate
             [2, 0, 0, 0, 0],
             2, 2],
            [[-12, 0, 0, 0, 0],    # Single axis: Move in negative direction at the max feedrate
             [1, 0, 0, 0, 0],
             1, 1],
            [[13, 0, 0, 0, 0],    # Single axis: Move faster than the max feedrate
             [1, 0, 0, 0, 0],
             10, 1],
            [[1, -1, 1, -1, 1],    # Multi axis: Move in negative direction at the max feedrate
             [1, 1, 1, 1, 1],
             pow(5, .5), pow(5, .5)],
            [[1, -2, 3, -4, 5],    # Multi axis: Move faster than the max feedrate
             [1, 1, 1, 1, 1],
             10, pow(55, .5) / 5],
        ]
        for case in cases:
            self.assertEquals(case[3], makerbot_driver.Gcode.get_safe_feedrate(
                case[0], case[1], case[2]))


class FindLongestAxisTests(unittest.TestCase):
    def test_reject_non_5d_list(self):
        self.assertRaises(makerbot_driver.PointLengthError,
                          makerbot_driver.Gcode.find_longest_axis, range(4))

    def test_good_result(self):
        cases = [
            [[0, 0, 0, 0, 0], 0],
            [[1, 0, 0, 0, 0], 0],
            [[-1, 0, 0, 0, 0], 0],
            [[1, -2, 3, -4, 5], 4],
            [[-1, 2, -3, 4, -5], 4],
        ]

        for case in cases:
            self.assertEqual(
                case[1], makerbot_driver.Gcode.find_longest_axis(case[0]))


class CalculateDDASpeedTestsWithReplicatorDual(unittest.TestCase):
    def setUp(self):
        self.profile = makerbot_driver.Profile("ReplicatorDual")
        self.g = makerbot_driver.Gcode.GcodeStates()
        self.g.profile = self.profile

    def tearDown(self):
        self.profile = None
        self.g = None

    def test_zero_move(self):
        self.assertRaises(makerbot_driver.Gcode.VectorLengthZeroError,
                          generic_zero_move_test, self.g)

    def test_calculate_dda_speed_good_result(self):
        cases = generic_calculate_dda_speed_good_result(self.g)
        for case in cases:
            self.assertAlmostEqual(case[0], case[1], 7)


class DDASpeedTestsWithReplicatorSingle(unittest.TestCase):
    """Because the parser is desinged to support a 5d machine,
    the ReplicatorSingle may pose a problem (since it lacks a
    B axis).  This problem becomes apparent when we query the
    machine profile for information about its axes.  To fix
    this probem, we always append a 0 when we encounter a missing
    axis in the machine profile.  This fix could damage the DDA
    speec calculating functions, so these tests will help us
    track down any problems if they arise.
    """

    def setUp(self):
        self.profile = makerbot_driver.Profile('ReplicatorSingle')
        self.g = makerbot_driver.Gcode.GcodeStates()
        self.g.profile = self.profile

    def tearDown(self):
        self.profile = None
        self.g = None

    def test_zero_move(self):
        self.assertRaises(makerbot_driver.Gcode.VectorLengthZeroError,
                          generic_zero_move_test, self.g)

    def test_calculate_dda_speed_good_result(self):
        cases = generic_calculate_dda_speed_good_result(self.g)
        for case in cases:
            self.assertAlmostEqual(case[0], case[1], 7)


def generic_zero_move_test(state):
    """This function is used to test both replicator single and dual profiles
    while calculating DDA speeds
    """
    initial_position = [0, 0, 0, 0, 0]
    target_position = [0, 0, 0, 0, 0]
    target_feedrate = 0

    makerbot_driver.Gcode.calculate_DDA_speed(
        initial_position,
        target_position,
        target_feedrate,
        state.get_axes_values('max_feedrate'),
        state.get_axes_values('steps_per_mm')
    )


def generic_calculate_dda_speed_good_result(state):
    """This function is used to test both replicator single and dual profiles
    while calculating DDA speeds

    @param state state: A state machine that houses either a replicator single or
        dual profile.
    """
    # TODO: These cases assume a replicator with specific steps_per_mm
    cases = [
        [[100, 0, 0, 0, 0], [200, 0, 0, 0, 0], 200, 30000000 / (state.profile.values['axes']['X']['steps_per_mm'] * 100)],    # Single axis, forward motion
        [[0, 100, 0, 0, 0], [0, 200, 0, 0, 0], 300, 20000000 / (
         state.profile.values['axes']['Y']['steps_per_mm'] * 100)],
        [[0, 0, 100, 0, 0], [0, 0, 200, 0, 0], 300, 20000000 / (
         state.profile.values['axes']['Z']['steps_per_mm'] * 100)],
        [[200, 0, 0, 0, 0], [100, 0, 0, 0, 0], 200, 30000000 / (state.profile.values['axes']['X']['steps_per_mm'] * 100)],    # Single axis, reverse motion
        [[0, 0, 0, 0, 0], [1, 1, 1, 0, 0], 100,
         2598.0762113533156],        # Multiple axis, forward motion
    ]

    for case in cases:
        dda_speed = makerbot_driver.Gcode.calculate_DDA_speed(
            case[0],
            case[1],
            case[2],
            state.get_axes_values('max_feedrate'),
            state.get_axes_values('steps_per_mm'))
        #Return a generator of the expected and calculated DDA speed
        yield case[3], dda_speed


class calculate_DDA_speed(unittest.TestCase):
    def test_calculate_dda_speed(self):
        feedrate = 100
        spm = 100.0
        secondConst = 60
        microSecondConst = 1000000
        expected_dda_speed = secondConst * microSecondConst / (
            feedrate * abs(spm))
        self.assertEqual(expected_dda_speed, makerbot_driver.Gcode.compute_DDA_speed(feedrate, spm))


class VariableSubstituteTest(unittest.TestCase):

    def test_blank_line_no_environment(self):
        environment = {}
        line = ''
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(line, replaced_line)

    def test_no_variables_no_environment(self):
        environment = {}
        line = "161 X Y Z"
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(line, replaced_line)

    def test_can_read_multiple_variable_types(self):
        environment = {
            '1': '-1',
            'foo': '-2',
        }
        line = '#1 #foo'
        expected_line = '-1 -2'
        self.assertEqual(expected_line, makerbot_driver.Gcode.variable_substitute(line, environment))

    def test_no_variables_has_environment(self):
        environment = {
            '0': '-1'
        }
        line = "G161 X Y Z"
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(line, replaced_line)

    def test_variables_has_environment_no_matching_variables(self):
        environment = {'1': '-1'}
        line = '#2'
        self.assertRaises(makerbot_driver.Gcode.UndefinedVariableError, makerbot_driver.Gcode.variable_substitute, line, environment)

    def test_line_and_environment_has_variables(self):
        environment = {'1': '-1'}
        line = '#1'
        expected_line = '-1'
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(expected_line, replaced_line)

    def test_line_has_less_variables_than_environment(self):
        environment = {
            '1': '-1',
            '2': '-2',
        }
        line = '#1'
        expected_line = '-1'
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(expected_line, replaced_line)

    def test_can_substitute_multiple_lines(self):
        environment = {
            '1': '-1',
        }
        line = '#1 #1'
        expected_line = '-1 -1'
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(expected_line, replaced_line)

    def test_can_substitute_multiple_variables(self):
        environment = {
            '1': '-1',
            '2': '-2',
        }
        line = '#1 #2'
        expected_line = '-1 -2'
        replaced_line = makerbot_driver.Gcode.variable_substitute(
            line, environment)
        self.assertEqual(expected_line, replaced_line)

    def test_can_substitute_multiple_variables_multiple_times(self):
        environment = {
            'FOO': '-1',
            '42': '-2',
        }
        line = '#FOO #42 #FOO #42'
        expected_line = '-1 -2 -1 -2'
        self.assertEqual(expected_line, makerbot_driver.Gcode.variable_substitute(line, environment))


class calculate_homing_DDA_speed(unittest.TestCase):
    def test_calculate_homing_dda_speed_max_feedrates_empty(self):
        feedrate = 10
        max_feedrates = []
        spm_list = [1, 2, 3, 4, 5]
        self.assertRaises(makerbot_driver.Gcode.CalculateHomingDDAError, makerbot_driver.Gcode.calculate_homing_DDA_speed, feedrate, max_feedrates, spm_list)

    def test_calculate_homing_dda_speed_spm_list_empty(self):
        feedrate = 10
        max_feedrates = [1, 2, 3, 4, 5]
        spm_list = []
        self.assertRaises(makerbot_driver.Gcode.CalculateHomingDDAError, makerbot_driver.Gcode.calculate_homing_DDA_speed, feedrate, max_feedrates, spm_list)

    def test_calculate_homing_dda_speed_uneven_lists(self):
        feedrate = 10
        max_feedrates = [1, 2, 3, 4, 5]
        spm_list = [1, 2, 3, 4]
        self.assertRaises(makerbot_driver.Gcode.CalculateHomingDDAError, makerbot_driver.Gcode.calculate_homing_DDA_speed, feedrate, max_feedrates, spm_list)

    def test_calculate_homing_dda_speed_safe_feedrate(self):
        feedrate = 10
        max_feedrates = [100, 200, 300, 400, 500]
        spm_list = [1, 2, 3, 4, 5]
        expected_dda = makerbot_driver.Gcode.compute_DDA_speed(
            feedrate, spm_list[0])
        self.assertEqual(expected_dda, makerbot_driver.Gcode.calculate_homing_DDA_speed(feedrate, max_feedrates, spm_list))

    def test_calculate_homing_dda_speed_unsafe_feedrate(self):
        feedrate = 600
        max_feedrates = [100, 200, 300, 400, 500]
        spm_list = [1, 2, 3, 4, 5]
        expected_dda = makerbot_driver.Gcode.compute_DDA_speed(
            max_feedrates[0], spm_list[0])
        self.assertEqual(expected_dda, makerbot_driver.Gcode.calculate_homing_DDA_speed(feedrate, max_feedrates, spm_list))

    def test_calculate_euclidean_distance(self):
        cases = [
            [[0, 0, 0], [0, 0, 0], 0],
            [[1, 1, 1], [0, 0, 0], math.sqrt(3)],
            [[1, 2, 3], [0, 0, 0], math.sqrt(14)],
            [[-1, -2, -3], [0, 0, 0], math.sqrt(14)],
            [[1, 1, 1], [1, 1, 1], 0],
        ]
        for case in cases:
            self.assertEqual(case[2], makerbot_driver.Gcode.calculate_euclidean_distance(case[0], case[1]))

    def test_calculate_euclidean_distance_bad_lengths(self):
        self.assertRaises(makerbot_driver.PointLengthError, makerbot_driver.Gcode.calculate_euclidean_distance, [0], [])


if __name__ == "__main__":
    unittest.main()

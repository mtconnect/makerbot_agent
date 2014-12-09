import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import time
import mock
import copy

import makerbot_driver


class TestFindAxesMinMax(unittest.TestCase):
    def setUp(self):
        self.mock = mock.Mock(makerbot_driver.s3g())

        self.g = makerbot_driver.Gcode.GcodeParser()
        self.g.s3g = self.mock
        profile = makerbot_driver.Profile("ReplicatorDual")
        self.g.state.profile = profile
        for axis in ['X', 'Y', 'Z', 'A', 'B']:
            setattr(self.g.state.position, axis, 0)
        self.initial_position = [0, 0, 0, 0, 0]

    def tearDown(self):
        self.mock = None
        self.g = None

    def test_find_axes_minimums_all_codes_accounted_for(self):
        """
        Tests to make sure that throwing all registers in a command doesnt raise an
        extra register error.
        """
        codes = 'F'
        flags = 'XYZ'
        self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[161][1])
        self.assertEqual(
            sorted(flags), sorted(self.g.GCODE_INSTRUCTIONS[161][2]))

    def test_find_axes_minimum(self):
        feedrate = 512
        codes = {'F': feedrate}
        flags = ['X', 'Y', 'Z']
        expected_position = [None, None, None, 0, 0]
        axes = flags
        timeout = self.g.state.profile.values['find_axis_minimum_timeout']
        self.g.find_axes_minimums(codes, flags, '')
        params = self.mock.mock_calls[0][1]
        self.assertEqual(params[0], flags)
        self.assertEqual(expected_position, self.g.state.position.ToList())

    def test_find_axes_minimum_no_axes(self):
        feedrate = 5
        codes = {'F': feedrate}
        axes = []
        timeout = self.g.state.profile.values['find_axis_minimum_timeout']
        self.g.find_axes_minimums(codes, [], '')
        self.assertTrue(len(self.mock.mock_calls) == 0)

    def test_find_axes_minimum_no_F_code(self):
        codes = {}
        flags = ['X', 'Y']
        comments = ''
        self.assertRaises(
            KeyError, self.g.find_axes_minimums, codes, flags, comments)

    def test_find_axes_maximums_all_codes_accounted_for(self):
        codes = 'F'
        flags = 'XYZ'
        self.assertEqual(
            sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[162][1]))
        self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[162][2])

    def test_find_axes_maximum(self):
        feedrate = 5
        codes = {'F': feedrate}
        flags = ['X', 'Y', 'Z']
        expected_position = [None, None, None, 0, 0]
        axes = flags
        feedrate = 0
        timeout = self.g.state.profile.values['find_axis_maximum_timeout']
        self.g.find_axes_maximums(codes, flags, '')
        params = self.mock.mock_calls[0][1]
        self.assertEqual(params[0], flags)
        self.assertEqual(expected_position, self.g.state.position.ToList())

    def test_find_axes_maximum_no_axes(self):
        feedrate = 5
        codes = {'F': feedrate}
        axes = []
        timeout = self.g.state.profile.values['find_axis_minimum_timeout']
        self.g.find_axes_maximums(codes, [], '')
        calls = self.mock.mock_calls
        self.assertTrue(len(calls) == 0)

    def test_find_axes_maximum_no_f_code(self):
        codes = {}
        flags = ['X', 'Y']
        comments = ''
        self.assertRaises(
            KeyError, self.g.find_axes_maximums, codes, flags, comments)


class test_linear_interpolation(unittest.TestCase):

    def setUp(self):
        self.mock = mock.Mock(makerbot_driver.s3g())
        self.g = makerbot_driver.Gcode.GcodeParser()
        self.g.s3g = self.mock
        profile = makerbot_driver.Profile("ReplicatorDual")
        self.g.state.profile = profile
        for axis in ['X', 'Y', 'Z', 'A', 'B']:
            setattr(self.g.state.position, axis, 0)
        self.initial_position = [0, 0, 0, 0, 0]

    def tearDown(self):
        self.mock = None
        self.g = None

    def test_linear_interpolation_all_codes_accounted_for(self):
        codes = 'XYZABEF'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[1][1]))
        self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[1][2])

    def test_linear_interpolation_doesnt_call_s3g_with_no_codes_axis_codes(self):
        codes = {'F': 0}
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)
        calls = self.mock.mock_calls
        self.assertEqual(0, len(calls))

    def test_linear_interpolation_no_feedrate_specified_error(self):
        codes = {}
        flags = []
        comments = ''
        with self.assertRaises(makerbot_driver.Gcode.NoFeedrateSpecifiedError):
            self.g.linear_interpolation(codes, flags, comments)

    def test_linear_interpolation_doesnt_call_s3g_with_only_feedrate(self):
        codes = {'F': 10}
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)
        calls = self.mock.mock_calls
        self.assertEqual(0, len(calls))

    def test_linear_interpolation_no_point_sets_feedrate(self):
        feedrate = 405
        codes = {'F': feedrate}
        self.g.linear_interpolation(codes, [], '')
        self.assertEqual(feedrate, self.g.state.values['feedrate'])

    def test_linear_interpolation_no_feedrate_code_last_feedrate_set(self):
        feedrate = 50
        tool_index = 0
        xOff = 5

        self.g.state.values['feedrate'] = feedrate
        self.g.state.values['tool_index'] = tool_index

        codes = {
            'X': xOff
        }
        expectedPoint = self.initial_position[:]
        expectedPoint[0] += xOff

        self.g.linear_interpolation(codes, [], '')
        #We want to be sure it used the correct feedrate, so we must check for it
        actual_params = self.mock.mock_calls[0][1]
        ddaFeedrate = makerbot_driver.Gcode.calculate_DDA_speed(
            self.initial_position,
            expectedPoint,
            feedrate,
            self.g.state.get_axes_values('max_feedrate'),
            self.g.state.get_axes_values('steps_per_mm'),
        )
        e_distance = 5
        expected_feedrate_mm_sec = self.g.state.values['feedrate'] * (1 / 60.0)
        self.assertAlmostEquals(ddaFeedrate, actual_params[1])
        self.assertEqual(e_distance, actual_params[2])
        self.assertEqual(expected_feedrate_mm_sec, actual_params[3])
        self.assertEqual(feedrate, self.g.state.values['feedrate'])

    def test_linear_interpolation_f_code_no_feedrate_set(self):
        self.assertTrue('feedrate' not in self.g.state.values)
        feedrate = 50
        xOff = 10
        codes = {
            'F': feedrate,
            'X': xOff,
        }
        expectedPoint = self.initial_position[:]
        expectedPoint[0] += xOff
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)
        #We want to be sure it used the correct feedrate, so we must check for it
        actual_params = self.mock.mock_calls[0][1]
        ddaFeedrate = makerbot_driver.Gcode.calculate_DDA_speed(
            self.initial_position,
            expectedPoint,
            feedrate,
            self.g.state.get_axes_values('max_feedrate'),
            self.g.state.get_axes_values('steps_per_mm'),
        )
        expected_feedrate_mm_sec = self.g.state.values['feedrate'] * (1 / 60.0)
        e_distance = 10
        self.assertAlmostEquals(ddaFeedrate, actual_params[1])
        self.assertEqual(e_distance, actual_params[2])
        self.assertEqual(expected_feedrate_mm_sec, actual_params[3])
        self.assertEqual(feedrate, self.g.state.values['feedrate'])

    def test_linear_interpolation_f_code_set_feedrate(self):
        state_feedrate = 5
        self.g.state.values['feedrate'] = state_feedrate
        code_feedrate = 10
        xOff = 10
        codes = {
            'F': code_feedrate,
            'X': xOff,
        }
        expectedPosition = self.initial_position[:]
        expectedPosition[0] += xOff
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)

        #We want to be sure it used the correct feedrate, so we must check for it
        ddaFeedrate = makerbot_driver.Gcode.calculate_DDA_speed(
            self.initial_position,
            expectedPosition,
            code_feedrate,
            self.g.state.get_axes_values('max_feedrate'),
            self.g.state.get_axes_values('steps_per_mm'),
        )
        actual_params = self.mock.mock_calls[0][1]
        expected_feedrate_mm_sec = self.g.state.values['feedrate'] * (1 / 60.0)
        e_distance = 10
        self.assertAlmostEquals(ddaFeedrate, actual_params[1])
        self.assertEqual(e_distance, actual_params[2])
        self.assertEqual(expected_feedrate_mm_sec, actual_params[3])
        self.assertEqual(self.g.state.values['feedrate'], code_feedrate)

    def test_linear_interpolation_a_code_doesnt_throw_conflicting_codes_error(self):
        codes = {
            'A': 10,
            'F': 100,
        }
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)

    def test_linear_interpolation_b_code_doesnt_throw_conflicting_codes_error(self):
        codes = {
            'B': 10,
            'F': 100,
        }
        flags = []
        comments = ''
        self.g.linear_interpolation(codes, flags, comments)

    def test_linear_interpolation_good_input(self):
        feedrate = 10
        codes = {
            'X': 10,
            'Y': 20,
            'Z': 30,
            'A': 40,
            'F': feedrate,
        }
        flags = []
        comments = ''
        expectedPoint = [10, 20, 30, 40, 0]
        e_distance = makerbot_driver.Gcode.calculate_euclidean_distance(
            expectedPoint[:3], self.g.state.get_position()[:3])
        self.g.linear_interpolation(codes, flags, comments)
        # Gcode works in steps, so we need to convert the expected position to steps
        spmList = self.g.state.get_axes_values('steps_per_mm')
        for i in range(len(expectedPoint)):
            expectedPoint[i] *= spmList[i]
        actual_params = self.mock.mock_calls[0][1]
        for expected, actual in zip(expectedPoint, actual_params[0]):
            self.assertAlmostEqual(expected, actual)
        expected_feedrate_mm_sec = self.g.state.values['feedrate'] * (1 / 60.0)
        self.assertEqual(e_distance, actual_params[2])
        self.assertEqual(expected_feedrate_mm_sec, actual_params[3])


class gcodeTests(unittest.TestCase):
    def setUp(self):
        self.mock = mock.Mock(makerbot_driver.s3g())

        self.g = makerbot_driver.Gcode.GcodeParser()
        self.g.s3g = self.mock
        profile = makerbot_driver.Profile("ReplicatorDual")
        self.g.state.profile = profile

    def tearDown(self):
        self.mock = None
        self.g = None

    def test_unrecognized_command_test_g_command(self):
        cmd = 999
        command = 'G' + str(cmd)
        try:
            self.g.execute_line(command)
        except makerbot_driver.Gcode.UnrecognizedCommandError as e:
            self.assertEqual(e.values['UnrecognizedCommand'], cmd)

    def test_unrecognized_command_test_m_command(self):
        cmd = 999
        command = 'M' + str(cmd)
        try:
            self.g.execute_line(command)
        except makerbot_driver.Gcode.UnrecognizedCommandError as e:
            self.assertEqual(e.values['UnrecognizedCommand'], cmd)

    def test_check_cant_read_non_unicde_non_ascii(self):
        command = 92
        self.assertRaises(makerbot_driver.Gcode.ImproperGcodeEncodingError,
                          self.g.execute_line, command)

    def test_check_can_read_unicode(self):
        command = "G92 X0 Y0 Z0 A0 B0"
        command = unicode(command)
        self.g.execute_line(command)
        self.mock.set_extended_position.assert_called_once_with(
            [0, 0, 0, 0, 0])

    def test_check_can_read_ascii(self):
        command = "G92 X0 Y0 Z0 A0 B0"
        self.g.execute_line(command)
        self.mock.set_extended_position.assert_called_once_with(
            [0, 0, 0, 0, 0])

    def test_check_gcode_errors_are_recorded_correctly(self):
        command = "G161 Q1"  # NOTE: this assumes that G161 does not accept a Q code
        expectedValues = {
            'LineNumber': 1,
            'Command': command,
            'InvalidCodes': 'Q',
        }

        try:
            self.g.execute_line(command)
        except makerbot_driver.Gcode.GcodeError as e:
            self.assertEqual(expectedValues, e.values)
        else:
            self.fail('ExpectedException not thrown')

    def test_check_gcode_extraneous_codes_gets_called(self):
        command = "G161 Q1"  # Note: this assumes that G161 does not accept a Q code
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError,
                          self.g.execute_line, command)

    def test_check_gcode_extraneous_flags_gets_called(self):
        command = "G161 Q"  # Note: this assumes that G161 does not accept a Q flag
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError,
                          self.g.execute_line, command)

    def test_check_mcode_extraneous_codes_gets_called(self):
        command = "M18 Q4"  # Note: This assumes that M6 does not accept an X code
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError,
                          self.g.execute_line, command)

    def test_check_mcode_extraneous_flags_gets_called(self):
        command = "M18 Q"  # Note: This assumes that M6 does not accept an X flag
        self.assertRaises(makerbot_driver.Gcode.InvalidCodeError,
                          self.g.execute_line, command)

    def test_disable_axes(self):
        flags = ['A', 'B', 'X', 'Y', 'Z']

        self.g.disable_axes({}, flags, '')
        self.mock.toggle_axes.assert_called_once_with(flags, False)

    def test_display_message_missing_timeout(self):
        codes = {}
        flags = []
        comment = 'asdf'
        self.assertRaises(
            KeyError, self.g.display_message, codes, flags, comment)

    def test_display_message(self):
        row = 0  # As specified in the gcode protocol
        col = 0  # As specified in the gcode protocol
        message = 'ABCDEFG123'
        timeout = 123
        clear_existing = False
        last_in_group = True
        wait_for_button = False

        codes = {'P': timeout}
        comment = message

        self.g.display_message(codes, [], comment)
        self.mock.display_message.assert_called_once_with(
            row,
            col,
            message,
            timeout,
            clear_existing,
            last_in_group,
            wait_for_button)

    def test_play_song_missing_song_id(self):
        codes = {}

        self.assertRaises(KeyError, self.g.play_song, codes, [], '')

    def test_play_song(self):
        song_id = 2
        codes = {'P': song_id}

        self.g.play_song(codes, [], '')
        self.mock.queue_song.assert_called_once_with(song_id)

    def test_set_build_percentage_missing_percent(self):
        codes = {}
        self.assertRaises(KeyError, self.g.set_build_percentage, codes, [], '')

    def test_set_build_percentage_negative_percent(self):
        build_percentage = -1
        codes = {'P': build_percentage}
        flags = []
        comments = ''
        self.assertRaises(makerbot_driver.Gcode.BadPercentageError,
                          self.g.set_build_percentage, codes, flags, comments)

    def test_set_build_percentage_too_high_percent(self):
        build_percentage = 100.1
        codes = {'P': build_percentage}
        flags = []
        comments = ''
        self.assertRaises(makerbot_driver.Gcode.BadPercentageError,
                          self.g.set_build_percentage, codes, flags, comments)

    def test_set_build_percentage_0_percent(self):
        build_percentage = 0
        codes = {'P': build_percentage}

        self.g.state.values['build_name'] = 'test'

        self.g.set_build_percentage(codes, [], '')
        self.assertEqual(0, self.g.state.percentage)
        self.mock.set_build_percent.assert_called_once_with(build_percentage)

    def test_set_build_percentage_100_percent(self):
        build_percentage = 100
        codes = {'P': build_percentage}
        flags = []
        comments = ''

        self.g.set_build_percentage(codes, flags, comments)
        self.assertEqual(100, self.g.state.percentage)
        self.mock.set_build_percent.assert_called_once_with(build_percentage)

    def test_build_start_notification(self):
        codes = {}
        flags = []
        comments = ""
        b_name = "test"

        self.g.state.values['build_name'] = b_name
        self.g.build_start_notification(codes, flags, comments)
        self.mock.build_start_notification.assert_called_once_with(b_name)

    def test_build_start_notification_no_build_name_set(self):
        codes = {}
        flags = []
        comments = ''
        self.assertRaises(
            makerbot_driver.Gcode.NoBuildNameError,
            self.g.build_start_notification,
            codes,
            flags,
            comments,
        )

    def test_build_end_notification(self):
        codes = {}
        flags = []
        comments = ''
        self.g.state.values['build_name'] = "test"
        self.g.build_end_notification(codes, flags, comments)
        self.assertEqual(self.g.state.values['build_name'], None)
        self.mock.build_end_notification.assert_called_once_with()

    def test_set_position_all_codes_accounted_for(self):
        codes = 'XYZABE'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[92][1]))
        self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[92][2])

    def test_set_position(self):
        expected_position = [0, 1, 2, 3, 4]
        codes = {
            'X': 0,
            'Y': 1,
            'Z': 2,
            'A': 3,
            'B': 4,
        }
        self.g.set_position(codes, [], '')
        self.assertEqual(expected_position, self.g.state.get_position())
        spmList = self.g.state.get_axes_values('steps_per_mm')
        for i in range(len(spmList)):
            expected_position[i] *= spmList[i]
        self.mock.set_extended_position.assert_called_once_with(
            expected_position)

    def test_set_potentiometer_values_all_codes_accounted_for(self):
        codes = 'XYZAB'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[130][1]))
        self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[130][2])

    def test_set_potentiometer_values_no_codes(self):
        codes = {'G': 130}
        self.g.set_potentiometer_values(codes, [], '')
        self.assertEqual(self.mock.call_count, 0)

    def test_set_potentiometer_values_one_axes(self):
        codes = {'X': 5}
        expected = [
            (0, 5),
        ]
        self.g.set_potentiometer_values(codes, [], '')
        calls = self.mock.mock_calls
        self.assertEqual(len(calls), len(expected))
        got_calls = [
            calls[0][1],
        ]
        got_calls.sort()
        expected.sort()
        self.assertEqual(got_calls, expected)

    def test_set_potentiometer_values_all_axes(self):
        codes = {'X': 5, 'Y': 4, 'Z': 3, 'A': 2, 'B': 1}
        expected = [
            (0, 5),
            (1, 4),
            (2, 3),
            (3, 2),
            (4, 1),
        ]
        self.g.set_potentiometer_values(codes, [], '')
        calls = self.mock.mock_calls
        self.assertEqual(len(calls), len(expected))
        got_calls = [
            calls[0][1],
            calls[1][1],
            calls[2][1],
            calls[3][1],
            calls[4][1],
        ]
        got_calls.sort()
        expected.sort()
        self.assertEqual(got_calls, expected)

    def test_dwell_all_codes_accounted_for(self):
        codes = 'P'
        flags = ''
        self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[4][1])
        self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[4][2])

    def test_dwell_no_p(self):
        codes = {}
        self.assertRaises(KeyError, self.g.dwell, codes, [], '')

    def test_dwell(self):
        codes = {'P': 10}
        miliConstant = 1000
        microConstant = 1000000
        d = 10 * microConstant / miliConstant
        self.g.dwell(codes, [], '')
        self.mock.delay.assert_called_once_with(d)

    def test_set_toolhead_temperature_all_codes_accounted_for(self):
        codes = 'ST'
        flags = ''
        self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[104][1])
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[104][2])

    def test_set_toolhead_temperature_no_s_code(self):
        codes = {'T': 2}
        self.assertRaises(
            KeyError, self.g.set_toolhead_temperature, codes, [], '')

    def test_set_toolhead_temperature_no_t_code(self):
        codes = {'S': 100}
        self.assertRaises(
            KeyError, self.g.set_toolhead_temperature, codes, [], '')

    def test_set_toolhead_temperature_all_code_defined(self):
        tool_index = 0
        temperature = 100

        codes = {'S': temperature, 'T': tool_index}
        self.g.set_toolhead_temperature(codes, [], '')
        self.mock.set_toolhead_temperature.assert_called_once_with(
            tool_index, temperature)

    def test_set_toolhead_temperature_no_t_code_no_saved_toolhead_index(self):
        codes = {'S': 100}
        self.assertRaises(
            KeyError, self.g.set_toolhead_temperature, codes, [], '')

    def test_set_toolhead_temperature_no_t_code_saved_toolhead_index(self):
        toolhead_index = 2
        temperature = 100
        self.g.state.values['last_toolhead_index'] = toolhead_index
        codes = {
            'S': temperature
        }
        self.g.set_toolhead_temperature(codes, [], '')
        self.mock.set_toolhead_temperature.assert_called_once_with(toolhead_index, temperature)
        self.assertEqual(self.g.state.values['last_toolhead_index'], toolhead_index)

    def test_set_toolhead_temperature_t_code_no_saved_toolhead_index(self):
        toolhead_index = 2
        temperature = 100
        self.assertFalse('last_toolhead_index' in self.g.state.values)
        codes = {
            'S': temperature,
            'T': toolhead_index
        }
        self.g.set_toolhead_temperature(codes, [], '')
        self.assertEqual(self.g.state.values['last_toolhead_index'], toolhead_index)
        self.mock.set_toolhead_temperature.assert_called_once_with(toolhead_index, temperature)

    def test_set_toolhead_temperature_t_code_saved_toolhead_index(self):
        toolhead_index = 2
        temperature = 100
        self.g.state.values['last_toolhead_index'] = toolhead_index + 1
        codes = {
            'S': temperature,
            'T': toolhead_index,
        }
        self.g.set_toolhead_temperature(codes, [], '')
        self.assertEqual(self.g.state.values['last_toolhead_index'], toolhead_index)
        self.mock.set_toolhead_temperature.assert_called_once_with(toolhead_index, temperature)

    def test_set_platform_temperature_all_codes_accounted_for(self):
        codes = 'ST'
        flags = ''

        self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[109][1])
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[109][2])

    def test_set_platform_temperature_no_s_code(self):
        codes = {'T': 2}
        self.assertRaises(
            KeyError, self.g.set_platform_temperature, codes, [], '')

    def test_set_platform_temperature_no_t_code_no_saved_platform_index(self):
        codes = {'S': 100}
        self.assertRaises(
            KeyError, self.g.set_platform_temperature, codes, [], '')

    def test_set_platform_temperature_no_t_code_saved_platform_index(self):
        platform_index = 2
        temperature = 100
        self.g.state.values['last_platform_index'] = platform_index
        codes = {
            'S': temperature
        }
        self.g.set_platform_temperature(codes, [], '')
        self.mock.set_platform_temperature.assert_called_once_with(platform_index, temperature)
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index)

    def test_set_platform_temperature_t_code_no_saved_platform_index(self):
        platform_index = 2
        temperature = 100
        self.assertFalse('last_platform_index' in self.g.state.values)
        codes = {
            'S': temperature,
            'T': platform_index
        }
        self.g.set_platform_temperature(codes, [], '')
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index)
        self.mock.set_platform_temperature.assert_called_once_with(platform_index, temperature)

    def test_set_platform_temperature_t_code_saved_platfor_index(self):
        platform_index = 2
        temperature = 100
        self.g.state.values['last_platform_index'] = platform_index + 1
        codes = {
            'S': temperature,
            'T': platform_index,
        }
        self.g.set_platform_temperature(codes, [], '')
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index)
        self.mock.set_platform_temperature.assert_called_once_with(platform_index, temperature)

    def test_set_platform_temperature_all_code_defined(self):
        tool_index = 0
        temperature = 42
        codes = {'S': temperature, 'T': tool_index}
        self.g.set_platform_temperature(codes, [], '')
        self.mock.set_platform_temperature.assert_called_once_with(
            tool_index, temperature)

    def test_set_platform_temperature_doesnt_update_state_machine(self):
        tool_index = 0
        temperature = 42
        codes = {'S': temperature, 'T': tool_index}
        flags = []
        comments = ''
        self.g.set_platform_temperature(codes, flags, comments)
        self.assertTrue('tool_index' not in self.g.state.values)

    def test_load_position_all_codes_accounted_for(self):
        codes = ''
        flags = 'XYZAB'
        self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[132][1])
        self.assertEqual(
            sorted(flags), sorted(self.g.MCODE_INSTRUCTIONS[132][2]))

    def test_load_position(self):
        position = {
            'X': 1,
            'Y': 2,
            'Z': 3,
            'A': 4,
            'B': 5,
        }
        for key in position:
            setattr(self.g.state.position, key, position[key])
        self.g.load_position({}, ['X', 'Y', 'Z', 'A', 'B'], '')
        expectedPosition = [None, None, None, None, None]
        self.assertEqual(expectedPosition, self.g.state.position.ToList())
        self.mock.recall_home_positions.assert_called_once_with(
            sorted(['X', 'Y', 'Z', 'A', 'B']))

    def test_tool_change_all_codes_accounted_for(self):
        codes = 'T'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.MCODE_INSTRUCTIONS[135][1]))
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[135][2])

    def test_tool_change_no_t_code_no_toolhead_index(self):
        self.assertFalse('last_toolhead_index' in self.g.state.values)
        codes = {}
        flags = []
        comments = ''
        self.assertRaises(KeyError, self.g.change_tool, codes, flags, comments)

    def test_tool_change_no_t_code_saved_toolhead_index(self):
        tool_index = 2
        self.g.state.values['last_toolhead_index'] = tool_index
        self.g.change_tool({}, [], '')
        self.mock.change_tool.assert_called_once_with(tool_index)
        self.assertEqual(self.g.state.values['tool_index'], tool_index)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index)

    def test_tool_change_t_code_no_toolhead_index(self):
        tool_index = 2
        self.assertFalse('last_toolhead_index' in self.g.state.values)
        codes = {'T': tool_index}
        flags = []
        comments = ''
        self.g.change_tool(codes, flags, comments)
        self.mock.change_tool.assert_called_once_with(tool_index)
        self.assertEqual(self.g.state.values['tool_index'], tool_index)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index)

    def test_tool_change_t_code_saved_toolhead_index(self):
        tool_index = 2
        self.g.state.values['last_toolhead_index'] = tool_index
        codes = {
            'T': tool_index
        }
        self.g.change_tool(codes, [], '')
        self.mock.change_tool.assert_called_once_with(tool_index)
        self.assertEqual(self.g.state.values['tool_index'], tool_index)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index)

    def test_wait_for_tool_ready_all_codes_accounted_for(self):
        codes = 'PT'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.MCODE_INSTRUCTIONS[133][1]))
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[133][2])

    def test_wait_for_tool_ready_no_p_or_t_codes(self):
        codes = {}
        flags = []
        comment = ''
        self.assertRaises(
            KeyError, self.g.wait_for_tool_ready, codes, flags, comment)

    def test_wait_for_tool_ready_no_p_code(self):
        tool_index = 0
        codes = {'T': tool_index}
        flags = []
        comment = ''
        self.g.wait_for_tool_ready(codes, flags, comment)
        self.mock.wait_for_tool_ready.assert_called_once_with(
            tool_index,
            self.g.state.wait_for_ready_packet_delay,
            self.g.state.wait_for_ready_timeout
        )

    def test_wait_for_tool_ready_no_t_code(self):
        timeout = 42
        codes = {'P': timeout}
        flags = []
        comment = ''
        self.assertRaises(
            KeyError, self.g.wait_for_tool_ready, codes, flags, comment)

    def test_wait_for_tool_ready_all_codes_defined(self):
        tool_index = 0
        timeout = 42
        codes = {
            'T': tool_index,
            'P': timeout,
        }
        flags = []
        comments = ''
        self.g.wait_for_tool_ready(codes, flags, comments)
        self.mock.wait_for_tool_ready.assert_called_once_with(
            tool_index,
            self.g.state.wait_for_ready_packet_delay,
            timeout
        )

    def test_wait_for_tool_ready_no_t_code_no_saved_tool_index(self):
        self.assertFalse('last_toolhead_index' in self.g.state.values)
        with self.assertRaises(KeyError):
            self.g.wait_for_tool_ready({}, [], '')

    def test_wait_for_tool_ready_no_t_code_saved_tool_index(self):
        tool_index = 2
        self.g.state.values['last_toolhead_index'] = tool_index
        codes = {}
        self.g.wait_for_tool_ready(codes, [], '')
        self.mock.wait_for_tool_ready.assert_called_once_with(tool_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index) 

    def test_wait_for_tool_ready_t_code_no_saved_tool_index(self):
        tool_index = 2
        self.assertFalse('last_toolhead_index' in self.g.state.values)
        codes = {
            'T': tool_index
        }
        self.g.wait_for_tool_ready(codes, [], '')
        self.mock.wait_for_tool_ready.assert_called_once_with(tool_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index)

    def test_wait_for_tool_ready_t_code_saved_tool_index(self):
        tool_index = 2
        self.g.state.values['last_toolhead_index'] = tool_index + 1
        codes = {
            'T': tool_index
        }
        self.g.wait_for_tool_ready(codes, [], '')
        self.mock.wait_for_tool_ready.assert_called_once_with(tool_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_toolhead_index'], tool_index)

    def test_wait_for_platform_ready_all_codes_accounted_for(self):
        codes = 'PT'
        flags = ''
        self.assertEqual(
            sorted(codes), sorted(self.g.MCODE_INSTRUCTIONS[134][1]))
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[134][2])

    def test_wait_for_platform_ready_no_p_or_t_codes(self):
        codes = {}
        flags = []
        comments = ''
        self.assertRaises(
            KeyError,
            self.g.wait_for_platform_ready,
            codes,
            flags,
            comments
        )

    def test_wait_for_platform_ready_no_t_code_no_saved_platform_index(self):
        self.assertFalse('last_platform_index' in self.g.state.values)
        with self.assertRaises(KeyError):
            self.g.wait_for_platform_ready({}, [], '')

    def test_wait_for_platform_ready_no_t_code_saved_platform_index(self):
        platform_index = 2
        self.g.state.values['last_platform_index'] = platform_index
        codes = {}
        self.g.wait_for_platform_ready(codes, [], '')
        self.mock.wait_for_platform_ready.assert_called_once_with(platform_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index) 

    def test_wait_for_platform_ready_t_code_no_saved_platform_index(self):
        platform_index = 2
        self.assertFalse('last_platform_index' in self.g.state.values)
        codes = {
            'T': platform_index
        }
        self.g.wait_for_platform_ready(codes, [], '')
        self.mock.wait_for_platform_ready.assert_called_once_with(platform_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index)

    def test_wait_for_platform_ready_t_code_saved_platform_index(self):
        platform_index = 2
        self.g.state.values['last_platform_index'] = platform_index + 1
        codes = {
            'T': platform_index
        }
        self.g.wait_for_platform_ready(codes, [], '')
        self.mock.wait_for_platform_ready.assert_called_once_with(platform_index, self.g.state.wait_for_ready_packet_delay, self.g.state.wait_for_ready_timeout)
        self.assertEqual(self.g.state.values['last_platform_index'], platform_index)

    def test_wait_for_platform_no_p_code_defined(self):
        tool_index = 0
        codes = {'T': tool_index}
        flags = []
        comments = ''
        self.g.wait_for_platform_ready(codes, flags, comments)
        self.mock.wait_for_platform_ready.assert_called_once_with(
            tool_index,
            self.g.state.wait_for_ready_packet_delay,
            self.g.state.wait_for_ready_timeout
        )

    def test_wait_for_platform_no_t_code_defined(self):
        timeout = 42
        codes = {'P': timeout}
        flags = []
        comments = ''
        self.assertRaises(
            KeyError,
            self.g.wait_for_platform_ready,
            codes,
            flags,
            comments
        )

    def test_wait_for_platform_all_codes_defined(self):
        timeout = 42
        tool_index = 0
        codes = {
            'T': tool_index,
            'P': timeout,
        }
        flags = []
        comments = ''
        self.g.wait_for_platform_ready(codes, flags, comments)
        self.mock.wait_for_platform_ready.assert_called_once_with(
            tool_index,
            self.g.state.wait_for_ready_packet_delay,
            timeout,
        )

    def test_wait_for_platform_doesnt_update_state_machine(self):
        tool_index = 0
        timeout = 42
        codes = {'T': tool_index, 'P': timeout}
        flags = []
        comments = ''
        self.g.wait_for_platform_ready(codes, flags, comments)
        self.assertTrue('tool_index' not in self.g.state.values)

    def test_enable_extra_device_all_codes_accounted_for(self):
        codes = 'T'
        flags = ''
        self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[126][1])
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[126][2])

    def test_enable_extra_device_no_t_code_no_extra_index(self):
        codes = {}
        flags = []
        comments = ''
        self.assertFalse('last_extra_index' in self.g.state.values)
        self.assertRaises(
            KeyError, self.g.enable_extra_output, codes, flags, comments)

    def test_enable_extra_device_no_t_code_saved_extra_index(self):
        tool_index = 2
        self.g.state.values['last_extra_index'] = tool_index
        self.g.enable_extra_output({}, [], '')
        self.mock.toggle_extra_output.assert_called_once_with(self.g.state.values['last_extra_index'], True)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

    def test_enable_extra_device_t_code_defined_no_saved_extra_index(self):
        self.assertFalse('last_extra_index' in self.g.state.values)
        tool_index = 2
        codes = {'T': tool_index}
        flags = []
        comments = ''
        self.g.enable_extra_output(codes, flags, comments)
        self.mock.toggle_extra_output.assert_called_once_with(tool_index, True)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

    def test_enable_extra_device_t_code_defined_saved_extra_index(self):
        tool_index = 2
        self.g.state.values['last_extra_index'] = tool_index + 1
        codes = {
            'T': tool_index
        }
        self.g.enable_extra_output(codes, [], '')
        self.mock.toggle_extra_output.assert_called_once_with(tool_index, True)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

    def test_disable_extra_device_all_codes_accounted_for(self):
        codes = 'T'
        flags = ''
        self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[127][1])
        self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[127][2])

    def test_disable_extra_device_no_t_code_no_extra_index(self):
        codes = {}
        flags = []
        comments = ''
        self.assertFalse('last_extra_index' in self.g.state.values)
        self.assertRaises(
            KeyError, self.g.disable_extra_output, codes, flags, comments)

    def test_disable_extra_device_no_t_code_saved_extra_index(self):
        tool_index = 2
        self.g.state.values['last_extra_index'] = tool_index
        self.g.disable_extra_output({}, [], '')
        self.mock.toggle_extra_output.assert_called_once_with(self.g.state.values['last_extra_index'], False)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

    def test_disable_extra_device_t_code_defined_no_saved_extra_index(self):
        self.assertFalse('last_extra_index' in self.g.state.values)
        tool_index = 2
        codes = {'T': tool_index}
        flags = []
        comments = ''
        self.g.disable_extra_output(codes, flags, comments)
        self.mock.toggle_extra_output.assert_called_once_with(tool_index, False)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

    def test_disable_extra_device_t_code_defined_saved_extra_index(self):
        tool_index = 2
        self.g.state.values['last_extra_index'] = tool_index + 1
        codes = {
            'T': tool_index
        }
        self.g.disable_extra_output(codes, [], '')
        self.mock.toggle_extra_output.assert_called_once_with(tool_index, False)
        self.assertEqual(self.g.state.values['last_extra_index'], tool_index)

if __name__ == "__main__":
    unittest.main()

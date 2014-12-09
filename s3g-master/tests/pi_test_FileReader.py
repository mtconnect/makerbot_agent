import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import mock
import io
import struct
import array
import tempfile
import threading

import makerbot_driver


class FileReaderTestsInputStream(unittest.TestCase):
    def setUp(self):
        self.d = makerbot_driver.FileReader.FileReader()

        self.inputstream = io.BytesIO()
        self.d.file = self.inputstream

    def tearDown(self):
        self.r = None
        self.d = None

    def test_ReadBytes_zero_data(self):
        self.d.ReadBytes(0)

    def test_ReadBytes_too_little_data(self):
        self.assertRaises(makerbot_driver.FileReader.InsufficientDataError,
                          self.d.ReadBytes, 1)

    def test_ReadBytes_enough_data(self):
        data = '1234567890'
        self.inputstream.write(data)
        self.inputstream.seek(0)
        self.assertEqual(data, self.d.ReadBytes(len(data)))


class FileReaderTestsWithS3g(unittest.TestCase):
    def setUp(self):
        self.r = makerbot_driver.s3g()
        with tempfile.NamedTemporaryFile(delete=True, suffix='.gcode') as f:
            self.path = f.name

        condition = threading.Condition()
        self.r.writer = makerbot_driver.Writer.FileWriter(
            open(self.path, 'wb'), condition)

        self.d = makerbot_driver.FileReader.FileReader()
        self.d.file = open(self.path, 'rb')

    def tearDown(self):
        self.r = None
        self.d = None

    def test_ReadFile(self):
        point = [1, 2, 3, 4, 5]
        duration = 42
        relativeAxes = 0

        self.r.queue_extended_point_new(point, duration, [])
        self.r.set_extended_position(point)
        self.r.set_build_percent(0)

        self.d.file.seek(0)
        self.r.writer.file.seek(0)

        payloads = self.d.ReadFile()
        cmdNumbers = [
            makerbot_driver.host_action_command_dict[
                'QUEUE_EXTENDED_POINT_NEW'],
            makerbot_driver.host_action_command_dict['SET_EXTENDED_POSITION'],
            makerbot_driver.host_action_command_dict['SET_BUILD_PERCENT']
        ]

        for readCmd, cmd in zip([payloads[0][0], payloads[1][0], payloads[2][0]], cmdNumbers):
            self.assertEqual(readCmd, cmd)


class MockTests(unittest.TestCase):
    def setUp(self):
        self.inputstream = io.BytesIO()
        self.d = makerbot_driver.FileReader.FileReader()
        self.d.file = self.inputstream
        self.mock = mock.Mock()

    def tearDown(self):
        self.d = None
        self.mock = None

    def test_get_string_always_read_empty_string(self):
        b = ''
        self.d.ReadBytes = mock.Mock(return_value=b)
        self.assertRaises(makerbot_driver.FileReader.InsufficientDataError,
                          self.d.GetStringBytes)

    def test_get_string_bytes_string_too_long(self):
        b = 'a'
        self.d.ReadBytes = mock.Mock(return_value=b)
        self.assertRaises(makerbot_driver.FileReader.StringTooLongError,
                          self.d.GetStringBytes)

    def test_get_string_bytes_empty_string(self):
        b = '\x00'
        self.d.ReadBytes = mock.Mock(return_value=b)
        expectedVal = '\x00'
        readVal = self.d.GetStringBytes()
        self.assertEqual(expectedVal, readVal)

    def test_get_string_good_value(self):
        b = ['a', 's', 'd', 'f', '\x00']
        b.reverse()

        def side_effect(val):
            return b.pop()
        self.d.ReadBytes = mock.Mock(side_effect=side_effect)
        expectedVal = 'asdf\x00'
        readVal = self.d.GetStringBytes()
        self.assertEqual(expectedVal, readVal)

    def test_parse_next_payload_tool_action(self):
        toolAction = ['ParseToolAction']
        hostAction = ['ParseHostAction']
        cmd = makerbot_driver.host_action_command_dict['TOOL_ACTION_COMMAND']
        self.d.ParseToolAction = mock.Mock(return_value=toolAction)
        self.d.ParseHostAction = mock.Mock(return_value=hostAction)
        self.d.GetNextCommand = mock.Mock(return_value=cmd)
        response = self.d.ParseNextPayload()
        expectedResponse = [cmd] + toolAction
        self.assertEqual(expectedResponse, response)

    def test_parse_next_payload_host_action(self):
        toolAction = ['ParseToolAction']
        hostAction = ['ParseHostAction']
        cmd = makerbot_driver.host_action_command_dict['QUEUE_EXTENDED_POINT']
        self.d.ParseToolAction = mock.Mock(return_value=toolAction)
        self.d.ParseHostAction = mock.Mock(return_value=hostAction)
        self.d.GetNextCommand = mock.Mock(return_value=cmd)
        response = self.d.ParseNextPayload()
        expectedResponse = [cmd] + hostAction
        self.assertEqual(expectedResponse, response)

    def test_read_file_end_of_file(self):
        self.d.ReadBytes = mock.Mock(
            side_effect=makerbot_driver.FileReader.InsufficientDataError)
        expectedPayloads = []
        self.assertEqual(expectedPayloads, self.d.ReadFile())

    def test_read_file_good_data(self):
        expected_data = [1, 2, 3, 4, 5]
        parse_next_payload_data = [1, 2, 3, 4, 5]
        parse_next_payload_data.reverse()

        def parse_next_payload_side_effect(*args):
            try:
                return parse_next_payload_data.pop()
            except:
                raise makerbot_driver.FileReader.EndOfFileError
        self.d.ParseNextPayload = mock.Mock(
            side_effect=parse_next_payload_side_effect)
        data = self.d.ReadFile()
        self.assertEqual(expected_data, data)

    def test_get_next_command_no_commands_left(self):
        self.d.ReadBytes = self.mock.ReadBytes
        self.mock.ReadBytes.side_effect = makerbot_driver.FileReader.InsufficientDataError
        self.assertRaises(
            makerbot_driver.FileReader.EndOfFileError, self.d.GetNextCommand)

    def test_get_next_command_bad_command(self):
        command = bytearray()  # Assume that 0xff is not a valid command
        command.append(0xFF)
        self.d.ReadBytes = mock.Mock(return_value=command)

        self.assertRaises(
            makerbot_driver.FileReader.BadCommandError, self.d.GetNextCommand)

    def test_get_next_command_host_action_command(self):
        cmd = makerbot_driver.host_action_command_dict['QUEUE_EXTENDED_POINT']
        reply = bytearray()
        reply.append(cmd)
        self.d.ReadBytes = mock.Mock(return_value=reply)

        self.assertEquals(cmd, self.d.GetNextCommand())

    def test_get_next_command_slave_action_command(self):
        cmd = makerbot_driver.slave_action_command_dict[
            'SET_TOOLHEAD_TARGET_TEMP']
        reply = bytearray()
        reply.append(cmd)
        self.d.ReadBytes = mock.Mock(return_value=reply)

        self.assertEquals(cmd, self.d.GetNextCommand())

    def test_parse_out_parameters_empty_format_string(self):
        formatString = ''
        data = self.d.ParseOutParameters(formatString)
        expectedData = []
        self.assertEqual(expectedData, data)

    def test_parse_out_parameters_string(self):
        formatString = 's'
        toWrite = 'asdf\x00'
        self.d.GetStringBytes = mock.Mock(return_value=toWrite)
        parsedParam = 'asdf'
        self.d.ParseParameter = mock.Mock(return_value=parsedParam)
        data = self.d.ParseOutParameters(formatString)
        expectedData = ['asdf']
        self.assertEqual(expectedData, data)

    def test_parse_out_parameters_read_right_ammount(self):
        formatString = 'III'
        expected_data = [1, 2, 3]
        read_bytes_side_effect_data = []
        for data in expected_data:
            read_bytes_side_effect_data.append(
                [makerbot_driver.Encoder.encode_uint32(data)])
        read_bytes_side_effect_data.reverse()

        def read_bytes_side_effect(*args):
            return read_bytes_side_effect_data.pop()
        self.d.ReadBytes = mock.Mock(side_effect=read_bytes_side_effect)

        parse_parameter_side_effect_data = [1, 2, 3]
        parse_parameter_side_effect_data.reverse()

        def parse_parameter_side_effect(*args):
            return parse_parameter_side_effect_data.pop()
        self.d.ParseParameter = mock.Mock(
            side_effect=parse_parameter_side_effect)

        data = self.d.ParseOutParameters(formatString)

        self.assertEqual(expected_data, data)

    def test_parse_out_parameters_strings_and_ints(self):
        formatString = 'sI'
        expected_data = ['asdf', 1]
        self.d.ReadBytes = mock.Mock(return_value=makerbot_driver.Encoder.encode_uint32(expected_data[1]))
        self.d.GetStringBytes = mock.Mock(
            return_value=expected_data[0] + '\x00')

        parse_parameter_side_effect_data = [expected_data[1], expected_data[0]]

        def parse_parameter_side_effect(*args):
            return parse_parameter_side_effect_data.pop()

        data = self.d.ParseOutParameters(formatString)
        self.assertEqual(expected_data, data)

    def test_parse_parameter_bad_format_string(self):
        formatString = 'z'
        self.assertRaises(
            struct.error, self.d.ParseParameter, formatString, '')

    def test_parse_parameter(self):
        cases = [
            [256, makerbot_driver.Encoder.encode_uint32(256), '<i'],
            ['asdf', array.array('B', 'asdf'), '<4s'],
            ['asdf', array.array('B', 'asdf\x00'), '<5s'],
        ]
        for case in cases:
            self.assertEqual(case[0], self.d.ParseParameter(case[2], case[1]))

    def test_parse_tool_action_bad_hot_cmd(self):
        cmd = makerbot_driver.host_action_command_dict[
            'QUEUE_EXTENDED_POINT_NEW']
        self.assertRaises(makerbot_driver.FileReader.NotToolActionCmdError,
                          self.d.ParseToolAction, cmd)

    def test_parse_tool_action_unknown_tool_action_command(self):
        cmd = makerbot_driver.host_action_command_dict['TOOL_ACTION_COMMAND']
        data = [0, 255, 0]
        self.d.ParseOutParameters = mock.Mock(return_value=data)
        self.assertRaises(makerbot_driver.FileReader.BadSlaveCommandError,
                          self.d.ParseToolAction, cmd)

    def test_parse_tool_action(self):
        cmd = makerbot_driver.host_action_command_dict['TOOL_ACTION_COMMAND']
        toolId = 2
        actionCmd = makerbot_driver.slave_action_command_dict[
            'SET_TOOLHEAD_TARGET_TEMP']
        length = 2
        temp = 100
        data = [
            [toolId, actionCmd, length, ],
            [temp, ],
        ]
        data.reverse()

        def parse_out_parameters_side_effect(*args):
            return data.pop()
        self.d.ParseOutParameters = mock.Mock(
            side_effect=parse_out_parameters_side_effect)
        expectedData = [toolId, actionCmd, length, temp]
        data = self.d.ParseToolAction(cmd)
        self.assertEqual(expectedData, data)

    def test_parse_host_action_bad_command(self):
        cmd = 255
        self.assertRaises(makerbot_driver.FileReader.BadHostCommandError,
                          self.d.ParseHostAction, cmd)

    def test_parse_host_action(self):
        cmd = makerbot_driver.host_action_command_dict['QUEUE_EXTENDED_POINT']
        point = [1, 2, 3, 4, 5]
        feedrate = 500
        data = point + [feedrate]
        self.d.ParseOutParameters = mock.Mock(return_value=data)
        expectedData = point + [feedrate]
        data = self.d.ParseHostAction(cmd)
        self.assertEqual(expectedData, data)

if __name__ == "__main__":
    unittest.main()

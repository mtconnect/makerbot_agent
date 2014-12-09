import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import uuid
import unittest
import io
import struct
import mock
import threading

import serial
from makerbot_driver import Writer, constants, s3g, errors, Encoder


class TestS3gPrintToFileType(unittest.TestCase):
    def test_print_to_file_type_s3g(self):
        print_to_file_type = 's3g'
        r = s3g()
        r.set_print_to_file_type(print_to_file_type)
        r.writer = mock.Mock()
        r.queue_extended_point_classic = mock.Mock()

        point = [0, 1, 2, 3, 4]
        dda_speed = 50
        dda_rate = 1000000.0 / float(dda_speed)
        e_distance = 100
        feedrate = 200
        relative_axes = []
        r.queue_extended_point(point, dda_speed, e_distance, feedrate)
        r.queue_extended_point_classic.assert_called_once_with(
            point, dda_speed)

    def test_print_to_file_type_x3g(self):
        print_to_file_type = 'x3g'
        r = s3g()
        r.set_print_to_file_type(print_to_file_type)
        r.queue_extended_point_x3g = mock.Mock()

        point = [0, 1, 2, 3, 4]
        dda_speed = 50
        dda_rate = 1000000.0 / float(dda_speed)
        e_distance = 100
        feedrate = 200
        relative_axes = []
        r.queue_extended_point(point, dda_speed, e_distance, feedrate)
        r.queue_extended_point_x3g.assert_called_once_with(
            point, dda_rate, relative_axes, e_distance, feedrate)


class TestFromFileName(unittest.TestCase):
    def setUp(self):
        self.condition = threading.Condition()
        self.obj = s3g.from_filename(None, self.condition)

    def tearDown(self):
        self.obj = None

    def test_from_filename_gets_correct_objects(self):
        self.assertTrue(isinstance(self.obj, s3g))
        self.assertTrue(isinstance(self.obj.writer, Writer.StreamWriter))
        self.assertTrue(isinstance(self.obj.writer.file, serial.Serial))

    def test_from_filename_minimal_constructor(self):
        self.assertEqual(self.obj.writer.file.port, None)
        self.assertEqual(self.obj.writer.file.baudrate, 115200)
        self.assertEqual(self.obj.writer.file.timeout, .2)

    def test_from_filename_use_all_parameters(self):
        baudrate = 9800
        timeout = 5
        self.obj = s3g.from_filename(None, self.condition, baudrate=9800, timeout=5)
        self.assertEqual(self.obj.writer.file.baudrate, baudrate)
        self.assertEqual(self.obj.writer.file.timeout, timeout)
        self.assertEqual(self.condition, self.obj.writer._condition)

    def test_from_filename_none_case(self):
        """ test the from_filename s3g factory."""
        self.assertRaises(serial.serialutil.SerialException, s3g.from_filename,
                          "/dev/this_is_hopefully_not_a_real_port", self.condition)


class S3gTestsFirmwareX3g(unittest.TestCase):
    """
    Emulate a machine
    """
    def setUp(self):
        self.r = s3g()
        self.r.set_print_to_file_type('x3g')
        self.outputstream = io.BytesIO(
        )  # Stream that we will send responses on
        self.inputstream = io.BytesIO(
        )  # Stream that we will receive commands on

        file = io.BufferedRWPair(self.outputstream, self.inputstream)
        self.condition = threading.Condition()
        writer = Writer.StreamWriter(file, self.condition)
        self.r.writer = writer

    def tearDown(self):
        self.r = None
        self.outputstream = None
        self.inputstream = None
        self.file = None

    def test_queue_extended_point(self):
        point = [1, 2, 3, 4, 5]
        dda = 50
        dda_rate = 1000000 / dda
        relative_axes = ['X']
        distance = 123.0
        feedrate = 100
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.queue_extended_point(
            point, dda, distance, feedrate, relative_axes=relative_axes)
        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'QUEUE_EXTENDED_POINT_ACCELERATED'])
        self.assertEqual(payload[1:5], Encoder.encode_int32(point[0]))
        self.assertEqual(payload[5:9], Encoder.encode_int32(point[1]))
        self.assertEqual(payload[9:13], Encoder.encode_int32(point[2]))
        self.assertEqual(payload[13:17], Encoder.encode_int32(point[3]))
        self.assertEqual(payload[17:21], Encoder.encode_int32(point[4]))
        self.assertEqual(payload[21:25], Encoder.encode_uint32(dda_rate))
        self.assertEqual(payload[25], Encoder.encode_axes(relative_axes))
        self.assertEqual(payload[26:30], struct.pack('<f', float(distance)))
        self.assertEqual(
            payload[30:32], Encoder.encode_int16(int(float(feedrate * 64.0))))


class S3gTestsFirmwareClassic(unittest.TestCase):
    """
    Emulate a machine
    """
    def setUp(self):
        self.r = s3g()
        self.r.set_print_to_file_type('s3g')
        self.outputstream = io.BytesIO(
        )  # Stream that we will send responses on
        self.inputstream = io.BytesIO(
        )  # Stream that we will receive commands on

        file = io.BufferedRWPair(self.outputstream, self.inputstream)
        self.condition = threading.Condition()
        writer = Writer.StreamWriter(file, self.condition)
        self.r.writer = writer

    def tearDown(self):
        self.r = None
        self.outputstream = None
        self.inputstream = None
        self.file = None

    def test_queue_extended_point_x3g(self):
        point = [1, 2, 3, 4, 5]
        dda = 50
        relative_axes = ['X']
        distance = 123.0
        feedrate = 100
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.queue_extended_point_x3g(
            point, dda, relative_axes, distance, feedrate)
        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'QUEUE_EXTENDED_POINT_ACCELERATED'])
        self.assertEqual(payload[1:5], Encoder.encode_int32(point[0]))
        self.assertEqual(payload[5:9], Encoder.encode_int32(point[1]))
        self.assertEqual(payload[9:13], Encoder.encode_int32(point[2]))
        self.assertEqual(payload[13:17], Encoder.encode_int32(point[3]))
        self.assertEqual(payload[17:21], Encoder.encode_int32(point[4]))
        self.assertEqual(payload[21:25], Encoder.encode_uint32(dda))
        self.assertEqual(payload[25], Encoder.encode_axes(relative_axes))
        self.assertEqual(payload[26:30], struct.pack('<f', float(distance)))
        self.assertEqual(
            payload[30:32], Encoder.encode_int16(int(float(feedrate * 64.0))))

    def test_set_servo_2_position(self):
        tool = 2
        theta = 50
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_servo2_position(tool, theta)
        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], tool)
        self.assertEqual(payload[2], constants.slave_action_command_dict[
                         'SET_SERVO_2_POSITION'])
        self.assertEqual(payload[3], 1)
        self.assertEqual(payload[4], theta)

    def test_toggle_abp(self):
        tool = 2
        state = True
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toggle_ABP(tool, state)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], tool)
        self.assertEqual(
            payload[2], constants.slave_action_command_dict['TOGGLE_ABP'])
        self.assertEqual(payload[3], 1)
        self.assertEqual(payload[4], 1)

    def set_motor1_speed_pwm(self):
        tool = 2
        pwm = 128
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_motor1_speed_pwm(tool, pwm)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], tool)
        self.assertEqual(payload[2], constants.slave_action_command_dict[
                         'SET_MOTOR_1_SPEED_PWM'])
        self.assertEqual(payload[3], 1)
        self.assertEqual(payload[4], 128)

    def test_set_motor1_direction(self):
        tool = 2
        direction = True
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_motor1_direction(tool, direction)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], tool)
        self.assertEqual(payload[2], constants.slave_action_command_dict[
                         'SET_MOTOR_1_DIRECTION'])
        self.assertEqual(payload[3], 1)
        self.assertEqual(payload[4], direction)

        def test_get_vid_pid_iface(self):
            vid = 0x0000
            pid = 0xFFFF
            port = '/dev/tty.ACM0'
            gMachineDetector = makerbot_driver.get_gMachineDetector()
            gMachineDetector.get_available_machines = mock.Mock(return_value={
                port: {
                    'VID': vid,
                    'PID': pid,
                }
            })
            some_port = mock.Mock()
            some_port.port = port
            self.r.writer = makerbot_driver.Writer.StreamWriter(some_port)
            got_vid_pid = self.r.get_vid_pid_iface()
            self.assertEqual(got_vid_pid, (vid, pid))

        def test_get_verified_status_unverified(self):
            vid = 0x0000
            pid = 0xFFFF
            self.r.get_vid_pid = mock.Mock(return_value=(vid, pid))
            self.assertFalse(self.r.get_verified_status())

        def test_get_verified_status_verified(self):
            vid = makerbot_driver.vid_pid[0]
            pid = makerbot_driver.vid_pid[1]
            self.r.get_vid_pid = mock.Mock(return_value=(vid, pid))
            self.assertTrue(self.r.get_verified_status())

    def test_get_toolcount(self):
        toolcount = 3
        eeprom_offset_toolcount = 0x0042
        eeprom_length_toolcount = 1
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(toolcount)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEqual(self.r.get_toolhead_count(), toolcount)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['READ_FROM_EEPROM'])
        self.assertEqual(
            payload[1:3], Encoder.encode_uint16(eeprom_offset_toolcount))
        self.assertEqual(payload[3], eeprom_length_toolcount)

    def test_get_version(self):
        version = 0x5DD5

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(version))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEqual(self.r.get_version(), version)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['GET_VERSION'])
        self.assertEqual(
            payload[1:3], Encoder.encode_uint16(constants.s3g_version))

    def test_get_advanced_version(self):
        info = {
            'Version': 0x5DD5,
            'InternalVersion': 0x0110,
            'SoftwareVariant': 10,
            'ReservedA': 0,
            'ReservedB': 0
        }

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(info['Version']))
        response_payload.extend(Encoder.encode_uint16(info['InternalVersion']))
        response_payload.append(info['SoftwareVariant'])
        response_payload.append(info['ReservedA'])
        response_payload.extend(Encoder.encode_uint16(info['ReservedB']))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        version_info = self.r.get_advanced_version()
        self.assertEqual(version_info, info)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_query_command_dict[
                         'GET_ADVANCED_VERSION'])
        self.assertEqual(
            payload[1:3], Encoder.encode_uint16(constants.s3g_version))

    def test_get_name(self):
        import array
        name = 'The Replicator'
        n = array.array('B', name)
        n.append(0)
        n.append(0)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(n)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        version_info = self.r.get_name()
        self.assertEqual(version_info, name)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['READ_FROM_EEPROM'])

    def test_reset(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])

        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.reset()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
            payload[0], constants.host_query_command_dict['RESET'])

    def test_is_finished(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(0)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEqual(self.r.is_finished(), 0)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['IS_FINISHED'])

    def test_clear_buffer(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.clear_buffer()

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['CLEAR_BUFFER'])

    def test_pause(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.pause()

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEqual(
            payload[0], constants.host_query_command_dict['PAUSE'])

    def test_tool_query_negative_tool_index(self):
        self.assertRaises(
            errors.ToolIndexError,
            self.r.tool_query,
            -1,
            constants.slave_query_command_dict['GET_VERSION']
        )

    def test_tool_query_too_high_tool_index(self):
        self.assertRaises(
            errors.ToolIndexError,
            self.r.tool_query,
            constants.max_tool_index + 1,
            constants.slave_query_command_dict['GET_VERSION']
        )

    def test_tool_query_no_payload(self):
        tool_index = 2
        command = 0x12
        response = 'abcdef'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(response)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(
            self.r.tool_query(tool_index, command), response_payload)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], command)

    def test_tool_query_payload(self):
        tool_index = 2
        command = 0x12
        command_payload = 'ABCDEF'
        response = 'abcdef'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(response)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.tool_query(
                          tool_index, command, command_payload), response_payload)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], command)
        self.assertEquals(payload[3:], command_payload)

    def test_read_from_eeprom_bad_length(self):
        offset = 1234
        length = constants.maximum_payload_length

        self.assertRaises(
            errors.EEPROMLengthError, self.r.read_from_EEPROM, offset, length)

    def test_read_from_eeprom(self):
        offset = 1234
        length = constants.maximum_payload_length - 1
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(data)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.read_from_EEPROM(offset, length), data)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['READ_FROM_EEPROM'])
        self.assertEquals(payload[1:3], Encoder.encode_uint16(offset))
        self.assertEquals(payload[3], length)

    def test_write_to_eeprom_too_much_data(self):
        offset = 1234
        length = constants.maximum_payload_length - 3
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        self.assertRaises(
            errors.EEPROMLengthError, self.r.write_to_EEPROM, offset, data)

    def test_write_to_eeprom_bad_response_length(self):
        offset = 1234
        length = constants.maximum_payload_length - 4
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(length + 1)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertRaises(
            errors.EEPROMMismatchError, self.r.write_to_EEPROM, offset, data)

    def test_write_to_eeprom(self):
        offset = 1234
        length = constants.maximum_payload_length - 4
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(length)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.write_to_EEPROM(offset, data)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['WRITE_TO_EEPROM'])
        self.assertEquals(payload[1:3], Encoder.encode_uint16(offset))
        self.assertEquals(payload[3], length)
        self.assertEquals(payload[4:], data)

    def test_get_available_buffer_size(self):
        buffer_size = 0xDEADBEEF

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint32(buffer_size))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.get_available_buffer_size(), buffer_size)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_query_command_dict[
                          'GET_AVAILABLE_BUFFER_SIZE'])

    def test_abort_immediately(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.abort_immediately()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_query_command_dict[
                          'ABORT_IMMEDIATELY'])

    def test_playback_capture_error_codes(self):
        filename = 'abcdefghijkl'

        for error_code in constants.sd_error_dict:
            if error_code != 'SUCCESS':
                self.outputstream.seek(0)
                self.outputstream.truncate(0)

                response_payload = bytearray()
                response_payload.append(
                    constants.response_code_dict['SUCCESS'])
                response_payload.append(constants.sd_error_dict[error_code])
                self.outputstream.write(
                    Encoder.encode_payload(response_payload))
                self.outputstream.seek(0)

                self.assertRaises(
                    errors.SDCardError, self.r.playback_capture, filename)

    def test_playback_capture(self):
        filename = 'abcdefghijkl'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(constants.sd_error_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.playback_capture(filename)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['PLAYBACK_CAPTURE'])
        self.assertEquals(payload[1:-1], filename)
        self.assertEquals(payload[-1], 0x00)

    def test_get_next_filename_error_codes(self):
        for error_code in constants.sd_error_dict:
            if error_code != 'SUCCESS':
                self.outputstream.seek(0)
                self.outputstream.truncate(0)

                response_payload = bytearray()
                response_payload.append(
                    constants.response_code_dict['SUCCESS'])
                response_payload.append(constants.sd_error_dict[error_code])
                response_payload.append('\x00')
                self.outputstream.write(
                    Encoder.encode_payload(response_payload))
                self.outputstream.seek(0)

                self.assertRaises(
                    errors.SDCardError, self.r.get_next_filename, False)

    def test_get_next_filename_reset(self):
        filename = 'abcdefghijkl\x00'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(constants.sd_error_dict['SUCCESS'])
        response_payload.extend(filename)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.get_next_filename(True), filename)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_query_command_dict[
                          'GET_NEXT_FILENAME'])
        self.assertEquals(payload[1], 1)

    def test_get_next_filename_no_reset(self):
        filename = 'abcdefghijkl\x00'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(constants.sd_error_dict['SUCCESS'])
        response_payload.extend(filename)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.get_next_filename(False), filename)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_query_command_dict[
                          'GET_NEXT_FILENAME'])
        self.assertEquals(payload[1], 0)

    def test_get_build_name(self):
        build_name = 'abcdefghijklmnop\x00'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(build_name)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.get_build_name(), build_name)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_query_command_dict['GET_BUILD_NAME'])

    def test_get_extended_position(self):
        position = [1, -2, 3, -4, 5]
        endstop_states = 0x1234

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_int32(position[0]))
        response_payload.extend(Encoder.encode_int32(position[1]))
        response_payload.extend(Encoder.encode_int32(position[2]))
        response_payload.extend(Encoder.encode_int32(position[3]))
        response_payload.extend(Encoder.encode_int32(position[4]))
        response_payload.extend(Encoder.encode_uint16(endstop_states))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        [returned_position,
         returned_endstop_states] = self.r.get_extended_position()
        self.assertEquals(returned_position, position)
        self.assertEquals(returned_endstop_states, endstop_states)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_query_command_dict[
                          'GET_EXTENDED_POSITION'])

    def test_wait_for_button_bad_button(self):
        button = 'bad'
        self.assertRaises(errors.ButtonError, self.r.wait_for_button,
                          button, 0, False, False, False)

    def test_wait_for_button(self):
        button = 0x10
        options = 0x02 + 0x04  # reset on timeout, Clear screen
        timeout = 0

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.wait_for_button('up', timeout, False, True, True)
        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
            payload[0], constants.host_action_command_dict['WAIT_FOR_BUTTON'])
        self.assertEqual(payload[1], button)
        self.assertEqual(payload[2:4], Encoder.encode_uint16(timeout))
        self.assertEqual(payload[4], options)

    def test_queue_song(self):
        song_id = 1

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.queue_song(song_id)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
            payload[0], constants.host_action_command_dict['QUEUE_SONG'])
        self.assertEqual(payload[1], song_id)

    def test_reset_to_factory(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.reset_to_factory()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'RESET_TO_FACTORY'])
        self.assertEqual(payload[1], 0x00)  # Reserved byte

    def test_set_build_percent(self):
        percent = 42

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_build_percent(percent)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                         'SET_BUILD_PERCENT'])
        self.assertEqual(payload[1], percent)
        self.assertEqual(payload[2], 0x00)  # Reserved byte

    def test_display_message(self):
        row = 0x12
        col = 0x34
        timeout = 5
        message = 'abcdefghij'
        clear_existing = True
        last_in_group = True
        wait_for_button = True

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.display_message(row, col, message, timeout,
                               clear_existing, last_in_group, wait_for_button)

        expectedBitfield = 0x01 + 0x02 + \
            0x04  # Clear existing, last in group, wait for button

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
            payload[0], constants.host_action_command_dict['DISPLAY_MESSAGE'])
        self.assertEquals(payload[1], expectedBitfield)
        self.assertEquals(payload[2], col)
        self.assertEquals(payload[3], row)
        self.assertEquals(payload[4], timeout)
        self.assertEquals(payload[5:-1], message)
        self.assertEquals(payload[-1], 0x00)

    def test_build_start_notification_long_name(self):
        build_name = 'abcdefghijklmnopqrstuvwzyx0123456789'
        max_build_name_length = constants.maximum_payload_length - 7
        expected_build_name = build_name[:max_build_name_length]

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.build_start_notification(build_name)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'BUILD_START_NOTIFICATION'])
        self.assertEquals(
            payload[1:5], Encoder.encode_uint32(0))  # Reserved uint32
        self.assertEquals(payload[5:-1], expected_build_name)
        self.assertEquals(payload[-1], 0x00)

    def test_build_start_notification(self):
        build_name = 'abcdefghijkl'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.build_start_notification(build_name)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'BUILD_START_NOTIFICATION'])
        self.assertEquals(
            payload[1:5], Encoder.encode_uint32(0))  # Reserved uint32
        self.assertEquals(payload[5:-1], build_name)
        self.assertEquals(payload[-1], 0x00)

    def test_build_end_notification(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.build_end_notification()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'BUILD_END_NOTIFICATION'])
        self.assertEquals(payload[1], 0)

    def test_find_axes_minimums(self):
        axes = ['x', 'y', 'z', 'b']
        rate = 2500
        timeout = 45

        self.outputstream.write(
            Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.find_axes_minimums(axes, rate, timeout)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'FIND_AXES_MINIMUMS'])
        self.assertEquals(payload[1], Encoder.encode_axes(axes))
        self.assertEquals(payload[2:6], Encoder.encode_uint32(rate))
        self.assertEquals(payload[6:8], Encoder.encode_uint16(timeout))

    def test_find_axes_maximums(self):
        axes = ['x', 'y', 'z', 'b']
        rate = 2500
        timeout = 45

        self.outputstream.write(
            Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.find_axes_maximums(axes, rate, timeout)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'FIND_AXES_MAXIMUMS'])
        self.assertEquals(payload[1], Encoder.encode_axes(axes))
        self.assertEquals(payload[2:6], Encoder.encode_uint32(rate))
        self.assertEquals(payload[6:8], Encoder.encode_uint16(timeout))

    def test_tool_action_command_negative_tool_index(self):
        self.assertRaises(
            errors.ToolIndexError,
            self.r.tool_action_command,
            -1,
            constants.slave_action_command_dict['INIT']
        )

    def test_tool_action_command_too_high_tool_index(self):
        self.assertRaises(
            errors.ToolIndexError,
            self.r.tool_action_command,
            constants.max_tool_index + 1,
            constants.slave_action_command_dict['INIT']
        )

    def test_tool_action_command(self):
        tool_index = 2
        command = 0x12
        command_payload = 'abcdefghij'

        self.outputstream.write(
            Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.tool_action_command(tool_index, command, command_payload)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'TOOL_ACTION_COMMAND'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], command)
        self.assertEquals(payload[3], len(command_payload))
        self.assertEquals(payload[4:], command_payload)

    def test_queue_extended_point_long_length(self):
        point = [1, 2, 3, 4, 5, 6]
        rate = 500
        self.assertRaises(errors.PointLengthError,
                          self.r.queue_extended_point, point, rate, 0, 0)

    def test_queue_extended_point_short_length(self):
        point = [1, 2, 3, 4]
        rate = 500
        self.assertRaises(errors.PointLengthError,
                          self.r.queue_extended_point, point, rate, 0, 0)

    def test_queue_extended_point_classic(self):
        target = [1, -2, 3, -4, 5]
        velocity = 6

        self.outputstream.write(
            Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.queue_extended_point_classic(target, velocity)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'QUEUE_EXTENDED_POINT'])
        for i in range(0, 5):
            self.assertEquals(payload[(
                                      i * 4 + 1):(i * 4 + 5)], Encoder.encode_int32(target[i]))
        self.assertEquals(payload[21:25], Encoder.encode_int32(velocity))

    def test_queue_extended_point(self):
        target = [1, -2, 3, -4, 5]
        velocity = 6

        self.outputstream.write(
            Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.queue_extended_point(target, velocity, 0, 0)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                          'QUEUE_EXTENDED_POINT'])
        for i in range(0, 5):
            self.assertEquals(payload[(
                                      i * 4 + 1):(i * 4 + 5)], Encoder.encode_int32(target[i]))
        self.assertEquals(payload[21:25], Encoder.encode_int32(velocity))

    def test_set_extended_position_short_length(self):
        self.assertRaises(errors.PointLengthError,
                          self.r.set_extended_position, [1, 2, 3, 4])

    def test_set_extended_position_long_length(self):
        self.assertRaises(errors.PointLengthError,
                          self.r.set_extended_position, [1, 2, 3, 4, 5, 6])

    def test_set_extended_position(self):
        target = [1, -2, 3, -4, 5]

        self.outputstream.write(
          Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.set_extended_position(target)

        packet = bytearray(self.inputstream.getvalue())

        payload = Encoder.decode_packet(packet)
        self.assertEquals(payload[0], constants.host_action_command_dict[
                  'SET_EXTENDED_POSITION'])
        for i in range(0, 5):
            self.assertEquals(Encoder.encode_int32(
              target[i]), payload[(i * 4 + 1):(i * 4 + 5)])

    def test_get_toolhead_version(self):
        tool_index = 2
        version = 0x5DD5

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(version))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.get_toolhead_version(tool_index), version)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(
          payload[2], constants.slave_query_command_dict['GET_VERSION'])
        self.assertEquals(
          payload[3:5], Encoder.encode_uint16(constants.s3g_version))

    def test_capture_to_file(self):
        filename = 'test'

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(constants.sd_error_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.capture_to_file(filename)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_query_command_dict['CAPTURE_TO_FILE'])
        self.assertEqual(payload[1:-1], filename)
        self.assertEqual(payload[-1], 0x00)

    def test_capture_to_file_errors(self):
        filename = 'test'

        for error_code in constants.sd_error_dict:
            if error_code != 'SUCCESS':
                response_payload = bytearray()
                response_payload.append(
                  constants.response_code_dict['SUCCESS'])
                response_payload.append(constants.sd_error_dict[error_code])
                self.outputstream.write(
                  Encoder.encode_payload(response_payload))
                self.outputstream.seek(0)

                self.assertRaises(
                  errors.SDCardError, self.r.capture_to_file, filename)

    def test_end_capture_to_file(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint32(0))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        sdResponse = self.r.end_capture_to_file()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_query_command_dict['END_CAPTURE'])

    def test_store_home_positions(self):
        axes = ['x', 'z', 'b']

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.store_home_positions(axes)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'STORE_HOME_POSITIONS'])
        self.assertEqual(payload[1], Encoder.encode_axes(axes))

    def test_set_beep(self):
        frequency = 1
        duration = 2

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_beep(frequency, duration)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['SET_BEEP'])
        self.assertEqual(payload[1:3], Encoder.encode_uint16(frequency))
        self.assertEqual(payload[3:5], Encoder.encode_uint16(duration))
        self.assertEqual(payload[5], 0x00)  # reserved byte

    def test_set_rgb_led(self):
        r = 255
        g = 254
        b = 253
        blink = 252

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_RGB_LED(r, g, b, blink)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['SET_RGB_LED'])
        self.assertEqual(payload[1], r)
        self.assertEqual(payload[2], g)
        self.assertEqual(payload[3], b)
        self.assertEqual(payload[4], blink)
        self.assertEqual(payload[5], 0x00)  # reserved byte

    def test_set_potentiometer_value_capped(self):
        axes = 0
        value = 128
        capped_value = 127

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_potentiometer_value(axes, value)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['SET_POT_VALUE'])
        self.assertEqual(payload[1], axes)
        self.assertEqual(payload[2], capped_value)

    def test_set_potentiometer_value(self):
        axes = 0
        value = 2

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_potentiometer_value(axes, value)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['SET_POT_VALUE'])
        self.assertEqual(payload[1], axes)
        self.assertEqual(payload[2], value)

    def test_recall_home_positions(self):
        axes = ['x', 'z', 'b']

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.recall_home_positions(axes)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'RECALL_HOME_POSITIONS'])
        self.assertEqual(payload[1], Encoder.encode_axes(axes))

    def test_queue_extended_point_new_short_length(self):
        point = [1, 2, 3, 4]
        duration = 0
        relative_axes = ['x']

        self.assertRaises(errors.PointLengthError, self.r.queue_extended_point_new, point, duration, relative_axes)

    def test_queue_extended_point_new_long_length(self):
        point = [1, 2, 3, 4, 5, 6]
        duration = 0
        relative_axes = ['x']

        self.assertRaises(errors.PointLengthError, self.r.queue_extended_point_new, point, duration, relative_axes)

    def test_queue_extended_point_new(self):
        point = [1, -2, 3, -4, 5]
        duration = 10
        relative_axes = ['x', 'z', 'b']

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.queue_extended_point_new(point, duration, relative_axes)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'QUEUE_EXTENDED_POINT_NEW'])
        self.assertEqual(payload[1:5], Encoder.encode_int32(point[0]))
        self.assertEqual(payload[5:9], Encoder.encode_int32(point[1]))
        self.assertEqual(payload[9:13], Encoder.encode_int32(point[2]))
        self.assertEqual(payload[13:17], Encoder.encode_int32(point[3]))
        self.assertEqual(payload[17:21], Encoder.encode_int32(point[4]))
        self.assertEqual(payload[21:25], Encoder.encode_uint32(duration))
        self.assertEqual(payload[25], Encoder.encode_axes(relative_axes))

    def test_wait_for_platform_ready(self):
        toolhead = 0
        delay = 100
        timeout = 60

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.wait_for_platform_ready(toolhead, delay, timeout)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'WAIT_FOR_PLATFORM_READY'])
        self.assertEqual(payload[1], toolhead)
        self.assertEqual(payload[2:4], Encoder.encode_uint16(delay))
        self.assertEqual(payload[4:], Encoder.encode_uint16(timeout))

    def test_wait_for_tool_ready(self):
        toolhead = 0
        delay = 100
        timeout = 60

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.wait_for_tool_ready(toolhead, delay, timeout)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'WAIT_FOR_TOOL_READY'])
        self.assertEqual(payload[1], toolhead)
        self.assertEqual(payload[2:4], Encoder.encode_uint16(delay))
        self.assertEqual(payload[4:], Encoder.encode_uint16(timeout))

    def test_toggle_axes(self):
        axes = ['x', 'y', 'b']
        enable_flag = True

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toggle_axes(axes, enable_flag)

        bitfield = Encoder.encode_axes(axes)
        bitfield |= 0x80  # because 'enable_flag is set

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['ENABLE_AXES'])
        self.assertEqual(payload[1], bitfield)

    def test_delay(self):
        delay = 50

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.delay(delay)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
          payload[0], constants.host_action_command_dict['DELAY'])
        self.assertEqual(payload[1:], Encoder.encode_uint32(delay))

    def test_change_tool(self):
        tool_index = 2

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.change_tool(tool_index)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
          payload[0], constants.host_action_command_dict['CHANGE_TOOL'])
        self.assertEqual(payload[1], tool_index)

    def test_get_build_stats(self):
        stats = {
          'BuildState': 0,
          'BuildHours': 1,
          'BuildMinutes': 2,
          'LineNumber': 3,
          'Reserved': 4,
        }

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(stats['BuildState'])
        response_payload.append(stats['BuildHours'])
        response_payload.append(stats['BuildMinutes'])
        response_payload.extend(Encoder.encode_uint32(stats['LineNumber']))
        response_payload.extend(Encoder.encode_uint32(stats['Reserved']))

        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        info = self.r.get_build_stats()
        self.assertEqual(info, stats)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(
          payload[0], constants.host_query_command_dict['GET_BUILD_STATS'])

    def test_get_communication_stats(self):
        stats = {
          'PacketsReceived': 0,
          'PacketsSent': 1,
          'NonResponsivePacketsSent': 2,
          'PacketRetries': 3,
          'NoiseBytes': 4,
        }

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(
          Encoder.encode_uint32(stats['PacketsReceived']))
        response_payload.extend(Encoder.encode_uint32(stats['PacketsSent']))
        response_payload.extend(
          Encoder.encode_uint32(stats['NonResponsivePacketsSent']))
        response_payload.extend(Encoder.encode_uint32(stats['PacketRetries']))
        response_payload.extend(Encoder.encode_uint32(stats['NoiseBytes']))

        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        info = self.r.get_communication_stats()
        self.assertEqual(info, stats)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_query_command_dict[
                 'GET_COMMUNICATION_STATS'])

    def test_get_motherboard_status(self):
        flags = {
            'preheat': True,
            'manual_mode': False,
            'onboard_script': True,
            'onboard_process': False,
            'wait_for_button': True,
            'build_cancelling': False,
            'heat_shutdown': True,
            'power_error': False,
        }
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        flagValues = [0 == i % 2 for i in range(8)]
        bitfield = 0
        for i in range(len(flagValues)):
            if flagValues[i]:
                bitfield += 1 << i
        response_payload.append(bitfield)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        responseFlags = self.r.get_motherboard_status()

        self.assertEqual(flags, responseFlags)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEqual(payload[0], constants.host_query_command_dict[
                 'GET_MOTHERBOARD_STATUS'])

    def test_extended_stop_error(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(1)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertRaises(
          errors.ExtendedStopError, self.r.extended_stop, True, True)

    def test_extended_stop(self):
        expected_states = [
          [False, False, 0x00],
          [True, False, 0x01],
          [False, True, 0x02],
          [True, True, 0x03],
        ]

        for expected_state in expected_states:
            response_payload = bytearray()
            response_payload.append(constants.response_code_dict['SUCCESS'])
            response_payload.append(0)
            self.outputstream.write(Encoder.encode_payload(response_payload))
            self.outputstream.seek(0)
            self.inputstream.seek(0)

            self.r.extended_stop(expected_state[0], expected_state[1])

            packet = bytearray(self.inputstream.getvalue())
            payload = Encoder.decode_packet(packet)

            self.assertEqual(payload[0], constants.host_query_command_dict[
                     'EXTENDED_STOP'])
            self.assertEqual(payload[1], expected_state[2])

    def test_get_pid_state(self):
        expectedDict = {
          "ExtruderError": 1,
          "ExtruderDelta": 2,
          "ExtruderLastTerm": 3,
          "PlatformError": 4,
          "PlatformDelta": 5,
          "PlatformLastTerm": 6,
        }

        toolIndex = 0
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        for i in range(6):
            response_payload.extend(Encoder.encode_uint16(i + 1))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(expectedDict, self.r.get_PID_state(toolIndex))

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_query_command_dict['GET_PID_STATE'])

    def test_toolhead_init(self):
        toolIndex = 0

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toolhead_init(toolIndex)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        expectedPayload = bytearray()
        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_action_command_dict['INIT'])

    def test_toolhead_abort(self):
        toolIndex = 0

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toolhead_abort(toolIndex)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_action_command_dict['ABORT'])
        self.assertEqual(payload[3], len(bytearray()))
        self.assertEqual(payload[4:], bytearray())

    def test_toolhead_pause(self):
        toolIndex = 0
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toolhead_pause(toolIndex)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_action_command_dict['PAUSE'])
        self.assertEqual(payload[3], len(bytearray()))
        self.assertEqual(payload[4:], bytearray())

    def test_set_servo_1_position(self):
        toolIndex = 0
        theta = 90
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)
        self.r.set_servo1_position(toolIndex, theta)

        expectedPayload = bytearray()
        expectedPayload.append(theta)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(payload[2], constants.slave_action_command_dict[
                 'SET_SERVO_1_POSITION'])
        self.assertEqual(payload[3], len(expectedPayload))
        self.assertEqual(payload[4:], expectedPayload)

    def test_toggle_motor_1(self):
        toolIndex = 0
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.toggle_motor1(toolIndex, True, True)

        expectedPayload = bytearray()
        bitfield = 0
        bitfield |= 0x01 + 0x02
        expectedPayload.append(bitfield)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_action_command_dict['TOGGLE_MOTOR_1'])
        self.assertEqual(payload[3], len(expectedPayload))
        self.assertEqual(payload[4:], expectedPayload)

    def test_set_motor_1_speed_rpm(self):
        toolIndex = 0
        duration = 50
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.set_motor1_speed_RPM(toolIndex, duration)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        expectedPayload = bytearray()
        expectedPayload.extend(Encoder.encode_uint32(duration))

        self.assertEqual(payload[0], constants.host_action_command_dict[
                 'TOOL_ACTION_COMMAND'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(payload[2], constants.slave_action_command_dict[
                 'SET_MOTOR_1_SPEED_RPM'])
        self.assertEqual(payload[3], len(expectedPayload))
        self.assertEqual(payload[4:], expectedPayload)

    def test_get_tool_status(self):
        toolIndex = 0
        expectedDict = {
          "ExtruderReady": True,
          "ExtruderNotPluggedIn": True,
          "ExtruderOverMaxTemp": True,
          "ExtruderNotHeating": True,
          "ExtruderDroppingTemp": True,
          "PlatformError": True,
          "ExtruderError": True,
        }

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        returnBitfield = 0xFF

        response_payload.append(returnBitfield)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEqual(expectedDict, self.r.get_tool_status(toolIndex))

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(
          payload[2], constants.slave_query_command_dict['GET_TOOL_STATUS'])

    def test_get_motor_speed(self):
        toolIndex = 0
        speed = 100

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint32(speed))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEqual(speed, self.r.get_motor1_speed(toolIndex))

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEqual(payload[1], toolIndex)
        self.assertEqual(payload[2], constants.slave_query_command_dict[
                 'GET_MOTOR_1_SPEED_RPM'])

    def test_init(self):
        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.init()

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['INIT'])

    def test_get_toolhead_temperature(self):
        tool_index = 2
        temperature = 1234

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(temperature))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(
          self.r.get_toolhead_temperature(tool_index), temperature)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_query_command_dict[
                  'GET_TOOLHEAD_TEMP'])

    # TODO: also test for bad codes, both here and in platform.
    def test_is_tool_ready_bad_response(self):
        tool_index = 2
        ready_state = 2

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(ready_state)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertRaises(
          errors.HeatElementReadyError, self.r.is_tool_ready, tool_index)

    def test_is_tool_ready(self):
        tool_index = 2
        ready_states = [
          [True, 1],
          [False, 0]
        ]

        for ready_state in ready_states:
            self.outputstream.seek(0)
            self.outputstream.truncate(0)

            response_payload = bytearray()
            response_payload.append(constants.response_code_dict['SUCCESS'])
            response_payload.append(ready_state[1])
            self.outputstream.write(Encoder.encode_payload(response_payload))
            self.outputstream.seek(0)
            self.inputstream.seek(0)

            self.assertEquals(self.r.is_tool_ready(tool_index), ready_state[0])

            packet = bytearray(self.inputstream.getvalue())
            payload = Encoder.decode_packet(packet)
            self.assertEquals(
              payload[0], constants.host_query_command_dict['TOOL_QUERY'])
            self.assertEquals(payload[1], tool_index)
            self.assertEquals(payload[2], constants.slave_query_command_dict[
                      'IS_TOOL_READY'])

    def test_read_from_toolhead_eeprom_bad_length(self):
        tool_index = 2
        offset = 1234
        length = constants.maximum_payload_length

        self.assertRaises(errors.EEPROMLengthError, self.r.read_from_toolhead_EEPROM, tool_index, offset, length)

    def test_read_from_toolhead_eeprom(self):
        tool_index = 2
        offset = 1234
        length = constants.maximum_payload_length - 1
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(data)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(self.r.read_from_toolhead_EEPROM(
          tool_index, offset, length), data)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_query_command_dict[
                  'READ_FROM_EEPROM'])
        self.assertEquals(payload[3:5], Encoder.encode_uint16(offset))
        self.assertEquals(payload[5], length)

    def test_write_to_toolhead_eeprom_too_much_data(self):
        tool_index = 2
        offset = 1234
        length = constants.maximum_payload_length - 5
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        self.assertRaises(errors.EEPROMLengthError, self.r.write_to_toolhead_EEPROM, tool_index, offset, data)

    def test_write_to_toolhead_eeprom_bad_response_length(self):
        tool_index = 2
        offset = 1234
        length = constants.maximum_payload_length - 6
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(length + 1)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertRaises(errors.EEPROMMismatchError, self.r.write_to_toolhead_EEPROM, tool_index, offset, data)

    def test_write_to_toolhead_eeprom(self):
        tool_index = 2
        offset = 1234
        length = constants.maximum_payload_length - 6
        data = bytearray()
        for i in range(0, length):
            data.append(i)

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(length)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.write_to_toolhead_EEPROM(tool_index, offset, data)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(
          payload[2], constants.slave_query_command_dict['WRITE_TO_EEPROM'])
        self.assertEquals(payload[3:5], Encoder.encode_uint16(offset))
        self.assertEquals(payload[6:], data)

    def test_get_platform_temperature(self):
        tool_index = 2
        temperature = 1234

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(temperature))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(
          self.r.get_platform_temperature(tool_index), temperature)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_query_command_dict[
                  'GET_PLATFORM_TEMP'])

    def test_get_toolhead_target_temperature(self):
        tool_index = 2
        temperature = 1234

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(temperature))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(
          self.r.get_toolhead_target_temperature(tool_index), temperature)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_query_command_dict[
                  'GET_TOOLHEAD_TARGET_TEMP'])

    def test_get_platform_target_temperature(self):
        tool_index = 2
        temperature = 1234

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.extend(Encoder.encode_uint16(temperature))
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertEquals(
          self.r.get_platform_target_temperature(tool_index), temperature)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)
        self.assertEquals(
          payload[0], constants.host_query_command_dict['TOOL_QUERY'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_query_command_dict[
                  'GET_PLATFORM_TARGET_TEMP'])

    def test_is_platform_ready_bad_response(self):
        tool_index = 2
        ready_state = 2

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        response_payload.append(ready_state)
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.assertRaises(errors.HeatElementReadyError,
                  self.r.is_platform_ready, tool_index)

    def test_is_platform_ready(self):
        tool_index = 2
        ready_states = [
          [True, 1],
          [False, 0],
        ]

        for ready_state in ready_states:
            self.outputstream.seek(0)
            self.outputstream.truncate(0)

            response_payload = bytearray()
            response_payload.append(constants.response_code_dict['SUCCESS'])
            response_payload.append(ready_state[1])
            self.outputstream.write(Encoder.encode_payload(response_payload))
            self.outputstream.seek(0)
            self.inputstream.seek(0)

            self.assertEquals(
              self.r.is_platform_ready(tool_index), ready_state[0])

            packet = bytearray(self.inputstream.getvalue())
            payload = Encoder.decode_packet(packet)
            self.assertEquals(
              payload[0], constants.host_query_command_dict['TOOL_QUERY'])
            self.assertEquals(payload[1], tool_index)
            self.assertEquals(payload[2], constants.slave_query_command_dict[
                      'IS_PLATFORM_READY'])

    def test_toggle_fan(self):
        tool_index = 2
        fan_states = [True, False]

        for fan_state in fan_states:
            self.outputstream.seek(0)
            self.outputstream.truncate(0)

            self.outputstream.write(Encoder.encode_payload(
              [constants.response_code_dict['SUCCESS']]))
            self.outputstream.seek(0)
            self.inputstream.seek(0)

            self.r.toggle_fan(tool_index, fan_state)

            packet = bytearray(self.inputstream.getvalue())
            payload = Encoder.decode_packet(packet)

            self.assertEquals(payload[0], constants.host_action_command_dict[
                      'TOOL_ACTION_COMMAND'])
            self.assertEquals(payload[1], tool_index)
            self.assertEquals(
              payload[2], constants.slave_action_command_dict['TOGGLE_FAN'])
            self.assertEquals(payload[3], 1)
            self.assertEquals(payload[4], fan_state)

    def test_toggle_valve(self):
        tool_index = 2
        fan_states = [True, False]

        for fan_state in fan_states:
            self.outputstream.seek(0)
            self.outputstream.truncate(0)

            self.outputstream.write(Encoder.encode_payload(
              [constants.response_code_dict['SUCCESS']]))
            self.outputstream.seek(0)
            self.inputstream.seek(0)

            self.r.toggle_extra_output(tool_index, fan_state)

            packet = bytearray(self.inputstream.getvalue())
            payload = Encoder.decode_packet(packet)

            self.assertEquals(payload[0], constants.host_action_command_dict[
                      'TOOL_ACTION_COMMAND'])
            self.assertEquals(payload[1], tool_index)
            self.assertEquals(payload[2], constants.slave_action_command_dict[
                      'TOGGLE_EXTRA_OUTPUT'])
            self.assertEquals(payload[3], 1)
            self.assertEquals(payload[4], fan_state)

    def test_set_toolhead_temp(self):
        tool_index = 2
        temp = 1024

        self.outputstream.seek(0)
        self.outputstream.truncate(0)

        self.outputstream.write(
          Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.set_toolhead_temperature(tool_index, temp)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEquals(payload[0], constants.host_action_command_dict[
                  'TOOL_ACTION_COMMAND'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_action_command_dict[
                  'SET_TOOLHEAD_TARGET_TEMP'])
        self.assertEquals(payload[3], 2)  # Temp is a byte of len 2
        self.assertEquals(payload[4:6], Encoder.encode_int16(temp))

    def test_set_platform_temp(self):
        tool_index = 2
        temp = 1024

        self.outputstream.seek(0)
        self.outputstream.truncate(0)

        self.outputstream.write(
          Encoder.encode_payload([constants.response_code_dict['SUCCESS']]))
        self.outputstream.seek(0)

        self.r.set_platform_temperature(tool_index, temp)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEquals(payload[0], constants.host_action_command_dict[
                  'TOOL_ACTION_COMMAND'])
        self.assertEquals(payload[1], tool_index)
        self.assertEquals(payload[2], constants.slave_action_command_dict[
                  'SET_PLATFORM_TEMP'])
        self.assertEquals(payload[3], 2)  # Temp is a byte of len 2
        self.assertEquals(payload[4:6], Encoder.encode_int16(temp))

    def test_x3g_version(self):
        checksum = 0x0000
        high_bite = 6
        low_bite = 1
        extra_byte = 0
        the_pid = 0xD314

        response_payload = bytearray()
        response_payload.append(constants.response_code_dict['SUCCESS'])
        self.outputstream.write(Encoder.encode_payload(response_payload))
        self.outputstream.seek(0)

        self.r.x3g_version(high_bite, low_bite, checksum, pid=the_pid)

        packet = bytearray(self.inputstream.getvalue())
        payload = Encoder.decode_packet(packet)

        self.assertEqual(
          payload[0], constants.host_action_command_dict['X3G_VERSION'])
        self.assertEqual(payload[1], high_bite)
        self.assertEqual(payload[2], low_bite)
        self.assertEqual(payload[3], extra_byte)
        self.assertEqual(payload[4:8], struct.pack('<I', checksum))
        self.assertEqual(payload[8:10], struct.pack('<H', the_pid))
        for i in range(10, 21):
            self.assertEqual(payload[i], extra_byte)

if __name__ == "__main__":
    unittest.main()

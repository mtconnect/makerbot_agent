import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import struct
import json
import mock
import struct

import makerbot_driver


class TestResetEEPROMCompletely(unittest.TestCase):
    def setUp(self):
        self.s3g = mock.Mock()
        self.eeprom_writer = makerbot_driver.EEPROM.EepromWriter()
        self.eeprom_writer.s3g = self.s3g

    def tearDown(self):
        self.eeprom_writer = None

    def test_reset_eeprom_completely(self):
        self.eeprom_writer.reset_eeprom_completely()
        expected_num_commands = makerbot_driver.EEPROM.total_eeprom_size
        self.assertEqual(expected_num_commands, len(self.s3g.mock_calls))
        for command in self.s3g.mock_calls:
            command = command[1]
            self.assertEqual(struct.unpack('>B', command[1])[0], 0xff)


class TestEepromWriterUseTestEepromMap(unittest.TestCase):
    def setUp(self):
        wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        map_name = 'eeprom_writer_test_map.json'
        self.writer = makerbot_driver.EEPROM.EepromWriter(
            map_name=map_name,
            working_directory=wd,
        )
        with open(os.path.join(wd, map_name)) as f:
            self.map_vals = json.load(f)
        self.writer.s3g = makerbot_driver.s3g()
        self.write_to_eeprom_mock = mock.Mock()
        self.writer.s3g.write_to_EEPROM = self.write_to_eeprom_mock

    def tearDown(self):
        self.writer = None

    def test_cant_find_eeprom_map(self):
        wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        map_name = 'this map better not be in WD.some fake extension'
        with self.assertRaises(makerbot_driver.EEPROM.MissingEepromMapError):
            self.writer = makerbot_driver.EEPROM.EepromWriter(
                map_name=map_name,
                working_directory=wd,
            )

    def test_flush_data_no_data(self):
        self.writer.flush_data()
        self.assertEqual(0, len(self.write_to_eeprom_mock.mock_calls))

    def test_flush_data(self):
        values = [
            ['a', 1],
            ['b', 2],
            ['c', 3],
        ]
        for value in values:
            self.writer.data_buffer.append(value)
        self.writer.flush_data()
        calls = self.write_to_eeprom_mock.mock_calls
        self.assertEqual(len(values), len(calls))
        for call, value in zip(calls, values):
            params = call[1]
            self.assertEqual(value[0], params[0])
            self.assertEqual(value[1], params[1])

    def test_write_value_no_flush_toolhead(self):
        name = 'foobar'
        value = 252645135
        context = ['T0_DATA_BASE']
        offset = 0x0016 + 0x0000
        expected_value = struct.pack('<i', value)
        expected_buffer = [[offset, expected_value]]
        self.writer.write_data(name, value, context)
        self.assertEqual(expected_buffer, self.writer.data_buffer)
        self.assertEqual(len(self.write_to_eeprom_mock.mock_calls), 0)

    def test_write_value_flush_no_toolhead(self):
        name = 'foo'
        value = 120
        offset = 0x0000
        expected_packed_data = []
        expected_packed_data.append([offset, struct.pack('<b', value)])
        self.writer.write_data(name, value)
        #add second value
        name = 'unus'
        values = [128.5, 256]
        context = ['barfoo']
        offset = 0xaabb + 0x0004
        data = ''
        for value in values:
            bits = self.writer.calculate_floating_point(value)
            data += struct.pack('<BB', bits[0], bits[1])
        expected_packed_data.append([offset, data])
        self.writer.write_data(name, values, context, flush=True)
        self.assertEqual(expected_packed_data, self.writer.data_buffer)
        calls = self.write_to_eeprom_mock.mock_calls
        self.assertEqual(calls[0][1], tuple(expected_packed_data[0]))
        self.assertEqual(calls[1][1], tuple(expected_packed_data[1]))

    def test_write_value_no_flush_no_toolhead(self):
        name = 'foo'
        offset = 0x0000
        value = 120
        expected_packed_data = []
        expected_packed_data.append([offset, struct.pack('<b', value)])
        self.writer.write_data(name, value)
        #add second value
        name = 'unus'
        values = [128.5, 256]
        offset = 0x0004 + 0xaabb
        context = ['barfoo']
        data = ''
        for value in values:
            bits = self.writer.calculate_floating_point(value)
            data += struct.pack('<BB', bits[0], bits[1])
        expected_packed_data.append([offset, data])
        self.writer.write_data(name, values, context)
        self.assertEqual(expected_packed_data, self.writer.data_buffer)
        self.assertEqual(len(self.write_to_eeprom_mock.mock_calls), 0)


class TestEepromWriter(unittest.TestCase):
    def setUp(self):
        self.writer = makerbot_driver.EEPROM.EepromWriter()

    def tearDown(self):
        self.writer = None

    def test_encode_data_mult(self):
        mult = 10
        t = 'H'
        offset = 0x0000
        input_dict = {
            'mult': mult,
            'type': t,
            'offset': offset,
        }
        value = [10] * mult
        expected = ''
        for i in range(mult):
            expected += struct.pack('<H', value[0])
        got = self.writer.encode_data(value, input_dict)
        self.assertEqual(expected, got)

    def test_good_floating_point_type(self):
        cases = [
            [False, ''],
            [False, 'BBI'],
            [False, 'B'],
            [False, 'HI'],
            [True, 'H'],
            [True, 'HH'],
        ]
        for case in cases:
            self.assertEqual(
                case[0], self.writer.good_floating_point_type(case[1]))

    def test_good_string_type(self):
        cases = [
            [False, ''],
            [False, 'si'],
            [False, 'b'],
            [False, 'ss'],
            [True, 's'],
        ]
        for case in cases:
            self.assertEqual(case[0], self.writer.good_string_type(case[1]))

    def test_terminate_string(self):
        string = 'The Replicator'
        expected_string = string + '\x00'
        self.assertEqual(expected_string, self.writer.terminate_string(string))

    def test_encode_string(self):
        string = 'The Replicator'
        terminated_string = string + '\x00'
        code = '<%is' % (len(terminated_string))
        expected_payload = struct.pack(code, terminated_string)
        self.assertEqual(expected_payload, self.writer.encode_string(string))

    def test_encode_data_string_with_other_types(self):
        value = ['fail', 'fail', 'fail']
        input_dict = {
            'type': 'sBB',
        }
        self.assertRaises(makerbot_driver.EEPROM.IncompatableTypeError,
                          self.writer.encode_data, value, input_dict)

    def test_encode_data_floating_point_with_non_short_types(self):
        value = ['fail', 'fail', 'fail']
        input_dict = {
            'type': 'HHI',
            'floating_point': True
        }
        self.assertRaises(makerbot_driver.EEPROM.IncompatableTypeError,
                          self.writer.encode_data, value, input_dict)

    def test_encode_data_string(self):
        input_dict = {
            'type': 's'
        }
        string = 'TheReplicator'
        terminated_string = string + '\x00'
        code = '<%is' % (len(terminated_string))
        expected_payload = struct.pack(code, terminated_string)
        self.assertEqual(
            expected_payload, self.writer.encode_data([string], input_dict))

    def test_encode_data_floating_point(self):
        input_dict = {
            'floating_point': True,
            'type': 'H',
        }
        value = [128.5]
        bits = self.writer.calculate_floating_point(value[0])
        expected = struct.pack('<BB', bits[0], bits[1])
        self.assertEqual(expected, self.writer.encode_data(value, input_dict))

    def test_encode_data_floating_point_multiple(self):
        input_dict = {
            'floating_point': True,
            'type': 'HHH'
        }
        values = [0, 128.5, 256]
        expected = ''
        for value in values:
            bits = self.writer.calculate_floating_point(value)
            expected += struct.pack('<BB', bits[0], bits[1])
        self.assertEqual(expected, self.writer.encode_data(values, input_dict))

    def test_encode_data_normal_value(self):
        t = 'B'
        input_dict = {
            'type': t
        }
        value = [128]
        expected_value = struct.pack('<%s' % (t), value[0])
        self.assertEqual(
            expected_value, self.writer.encode_data(value, input_dict))

    def test_encode_data_multiple_values(self):
        t = 'BIH'
        input_dict = {
            'type': t
        }
        values = [128, 252645135, 3855]
        expected_value = struct.pack(
            '<%s' % (t), values[0], values[1], values[2])
        self.assertEqual(
            expected_value, self.writer.encode_data(values, input_dict))

    def test_encode_data_non_matching_type_and_values_more_types(self):
        t = 'BIH'
        values = [1, 2]
        input_dict = {
            'type': t
        }
        self.assertRaises(makerbot_driver.EEPROM.MismatchedTypeAndValueError,
                          self.writer.encode_data, values, input_dict)

    def test_encode_data_non_matching_type_and_values_more_values(self):
        t = 'BI'
        values = [1, 2, 3]
        input_dict = {
            'type': t
        }
        self.assertRaises(makerbot_driver.EEPROM.MismatchedTypeAndValueError,
                          self.writer.encode_data, values, input_dict)

    def test_calculate_floating_point(self):
        cases = [
            [0.0, 0, 0],
            [256, 255, 255],
            [128.5, 128, 128],
            [.5, 0, 128],
            [33, 33, 0],
            [.69, 0, 176],
        ]
        for case in cases:
            self.assertEqual(tuple(
                case[1:]), self.writer.calculate_floating_point(case[0]))

    def test_calculate_floating_point_value_too_high(self):
        cases = [-1, 257]
        for case in cases:
            self.assertRaises(FloatingPointError,
                              self.writer.calculate_floating_point, case)

    def test_bifurcate_data_even(self):
        data = range(100)
        a, b = self.writer._bifurcate_data(data)
        self.assertEqual(a + b, data)
        self.assertEqual(len(a), len(b))

    def test_bifurcate_data_off(self):
        data = range(101)
        a, b = self.writer._bifurcate_data(data)
        self.assertEqual(a + b, data)
        self.assertEqual(abs(len(a) - len(b)), 1)

    def test_bifurcate_data_1(self):
        data = range(1)
        a, b = self.writer._bifurcate_data(data)
        self.assertEqual(a + b, data)
        self.assertEqual(len(a), 0)
        self.assertEqual(len(b), 1)

    def test_bifurcate_data_0(self):
        data = range(0)
        a, b = self.writer._bifurcate_data(data)
        self.assertEqual(a + b, data)
        self.assertEqual(len(a), 0)
        self.assertEqual(len(b), 0)

    def test_flush_out_data_first_is_fine(self):
        data = range(15)
        offset = 0
        s3g_mock = mock.Mock()
        self.writer.s3g = s3g_mock
        self.writer._flush_out_data(offset, data)
        calls = s3g_mock.mock_calls
        self.assertEqual(1, len(calls))
        params = calls[0][1]
        self.assertEqual(params[0], offset)
        self.assertEqual(params[1], data)

    def test_flush_out_data_first_is_too_big(self):
        """
        This is kinda a weird test, since the function actually
        gets called three times, but the firt time it returns an error.
        """
        data = range(makerbot_driver.maximum_payload_length)
        offset = 0
        s3g_mock = mock.Mock()

        def mock_write_to_EEPROM(*args, **kwards):
            if len(args[1]) > makerbot_driver.maximum_payload_length - 4:
                raise makerbot_driver.EEPROMLengthError(len(args[1]))
        the_func = mock.Mock(side_effect=mock_write_to_EEPROM)
        s3g_mock.write_to_EEPROM = the_func
        s3g_mock.side_effect = mock_write_to_EEPROM
        self.writer.s3g = s3g_mock
        a, b = self.writer._bifurcate_data(data)
        expect_a_offset = offset
        expect_b_offset = offset + len(a)
        self.writer._flush_out_data(offset, data)
        calls = the_func.mock_calls
        self.assertEqual(len(calls), 3)
        first_params = calls[0][1]
        second_params = calls[1][1]
        third_params = calls[2][1]
        #check first params (this would have raised an error)
        self.assertEqual(first_params[0], offset)
        self.assertEqual(first_params[1], data)
        #Check second params
        self.assertEqual(second_params[0], expect_a_offset)
        self.assertEqual(second_params[1], a)
        #Chcek third params
        self.assertEqual(third_params[0], expect_b_offset)
        self.assertEqual(third_params[1], b)

    def test_flush_data_too_big(self):
        """
        This is kinda a weird test, since the function actually
        gets called three times, but the firt time it returns an error.
        """
        data = range(makerbot_driver.maximum_payload_length)
        offset = 0
        self.writer.data_buffer.append([offset, data])
        s3g_mock = mock.Mock()

        def mock_write_to_EEPROM(*args, **kwards):
            if len(args[1]) > makerbot_driver.maximum_payload_length - 4:
                raise makerbot_driver.EEPROMLengthError(len(args[1]))
        the_func = mock.Mock(side_effect=mock_write_to_EEPROM)
        s3g_mock.write_to_EEPROM = the_func
        s3g_mock.side_effect = mock_write_to_EEPROM
        self.writer.s3g = s3g_mock
        a, b = self.writer._bifurcate_data(data)
        expect_a_offset = offset
        expect_b_offset = offset + len(a)
        self.writer.flush_data()
        calls = the_func.mock_calls
        self.assertEqual(len(calls), 3)
        first_params = calls[0][1]
        second_params = calls[1][1]
        third_params = calls[2][1]
        #check first params (this would have raised an error)
        self.assertEqual(first_params[0], offset)
        self.assertEqual(first_params[1], data)
        #Check second params
        self.assertEqual(second_params[0], expect_a_offset)
        self.assertEqual(second_params[1], a)
        #Chcek third params
        self.assertEqual(third_params[0], expect_b_offset)
        self.assertEqual(third_params[1], b)

if __name__ == '__main__':
    unittest.main()

import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import json
import tempfile
import mock
import struct
import array


import makerbot_driver


class TestInit(unittest.TestCase):

    def test_init(self):
        eeprom_map = {'foo': 'bar'}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(json.dumps(eeprom_map))
        total_path = f.name
        name = total_path.split('/')[-1]
        path = tempfile.tempdir
        reader = makerbot_driver.EEPROM.EepromReader(
            map_name=name, working_directory=path)
        self.assertEqual(reader.eeprom_map, eeprom_map)
        self.assertEqual(path, reader.working_directory)


class TestReadEepromMap(unittest.TestCase):
    def setUp(self):
        self.wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        self.m = 'eeprom_reader_test_map.json'
        self.reader = makerbot_driver.EEPROM.EepromReader(
            map_name=self.m, working_directory=self.wd)

    def tearDown(self):
        self.reader = None


class TestReadFromEeprom(unittest.TestCase):

    def setUp(self):
        self.read_from_eeprom_mock = mock.Mock()
        self.reader = makerbot_driver.EEPROM.EepromReader()
        self.reader.s3g = makerbot_driver.s3g()
        self.reader.s3g.read_from_EEPROM = self.read_from_eeprom_mock
        with open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
            'eeprom_map.json',
        )) as f:
            self.reader.eeprom_map = json.load(f)

    def tearDown(self):
        self.reader = None

    def test_cant_find_eeprom_map(self):
        wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        map_name = 'this map better not be in WD.some fake extension'
        with self.assertRaises(makerbot_driver.EEPROM.MissingEepromMapError):
            self.writer = makerbot_driver.EEPROM.EepromReader(
                map_name=map_name,
                working_directory=wd,
            )

    def test_get_dict_by_contect_first_level(self):
        expected_dict = self.reader.eeprom_map[
            self.reader.main_map]['ACCELERATION_SETTINGS']
        expected_offset = int(expected_dict['offset'], 16)
        (got_dict, got_offset) = self.reader.get_dict_by_context(
            'ACCELERATION_SETTINGS')
        self.assertEqual(expected_dict, got_dict)
        self.assertEqual(expected_offset, got_offset)

    def test_get_dict_by_context_sub_level(self):
        expected_dict = self.reader.eeprom_map[self.reader.main_map]['T0_DATA_BASE']['sub_map']['EXTRUDER_PID_BASE']['sub_map']['D_TERM_OFFSET']
        expected_offset = int(self.reader.eeprom_map[self.reader.main_map]
                              ['T0_DATA_BASE']['offset'], 16)
        expected_offset += int(self.reader.eeprom_map[self.reader.main_map]['T0_DATA_BASE']['sub_map']['EXTRUDER_PID_BASE']['offset'], 16)
        expected_offset += int(expected_dict['offset'], 16)
        (got_dict, got_offset) = self.reader.get_dict_by_context(
            'D_TERM_OFFSET', ['T0_DATA_BASE', 'EXTRUDER_PID_BASE'])
        self.assertEqual(expected_dict, got_dict)
        self.assertEqual(expected_offset, got_offset)

    def test_read_from_eeprom_floating_point_missing_information(self):
        dicts = [
            {
                'floating_point': 'True',
            }
        ]
        for d in dicts:
            self.assertRaises(KeyError, self.reader.read_from_eeprom, d, 0)

    def test_read_from_eeprom_floating_point_good_value(self):
        offset = '0xaabb'
        t = 'H'
        #We get size of b because we read the individual bytes that
        #make up the short
        size = struct.calcsize('B')
        input_dict = {
            'floating_point': 'True',
            'offset': offset,
            'type': t,
        }
        expected = [128.5]
        self.read_from_eeprom_mock.return_value = struct.pack('<B', 128)
        got_value = self.reader.read_from_eeprom(input_dict, 0xaabb)
        self.assertEqual(expected, got_value)
        calls = self.read_from_eeprom_mock.mock_calls
        self.assertEqual(calls[0][1], (int(offset, 16), 1))
        self.assertEqual(calls[1][1], (int(offset, 16) + 1, 1))

    def test_read_from_eeprom_string_missing_info(self):
        input_dicts = [
            {
                'offset': '0xaabb',
                'type': 's',
            }
        ]
        for d in input_dicts:
            self.assertRaises(
                KeyError, self.reader.read_from_eeprom, d, 0xaabb)

    def test_read_from_eeprom_string(self):
        offset = '0xaabb'
        length = 10
        input_dict = {
            'offset': '0xaabb',
            'type': 's',
            'length': 10
        }
        expected_string = ['abcdefghi']
        return_value = array.array("B", expected_string[0] + '\x00')
        self.read_from_eeprom_mock.return_value = return_value
        got_value = self.reader.read_from_eeprom(input_dict, 0xaabb)
        self.assertEqual(expected_string, got_value)
        self.read_from_eeprom_mock.assert_called_once_with(
            int(offset, 16), length)

    def test_read_from_eeprom_value(self):
        offset = '0xaabb'
        t = 'BIH'
        input_dict = {
            'offset': offset,
            'type': t,
        }
        vals = [128, 4294967295, 43690]
        reversed_vals = vals[:]
        reversed_vals.reverse()
        reversed_type = list(t)
        reversed_type.reverse()
        packed_vals = []
        for code, val in zip(reversed_type, reversed_vals):
            packed_vals.append(struct.pack('<%s' % (code), val))

        def return_mock_func(*args, **kwards):
            return packed_vals.pop()
        self.read_from_eeprom_mock.side_effect = return_mock_func
        got_values = self.reader.read_from_eeprom(input_dict, 0)
        self.assertEqual(vals, got_values)
        calls = self.read_from_eeprom_mock.mock_calls
        self.assertEqual(3, len(calls))


class TestEepromReader(unittest.TestCase):

    def setUp(self):
        self.reader = makerbot_driver.EEPROM.EepromReader()
        self.reader.s3g = makerbot_driver.s3g()

    def tearDown(self):
        self.reader = None

    def test_get_floating_point_number(self):
        cases = [
            ['0x00', '0x00', 0],
            ['0xff', '0x00', 255.0],
            ['0x00', '0x80', .5],
            ['0x80', '0x80', 128.5],
            ['0x01', '0xfe', 2.0],
        ]
        for case in cases:
            self.assertEqual(
                self.reader.decode_floating_point(
                    int(case[0], 16), int(case[1], 16)),
                case[2]
            )

    def test_read_eeprom_sub_map(self):
        input_dict = {
            'offset': '0x0000',
            'sub_map': {
                'offset': '0x0000',
                'floating_point': 'True'
            }
        }
        offset = 0x0000
        self.assertRaises(makerbot_driver.EEPROM.SubMapReadError,
                          self.reader.read_from_eeprom, input_dict, offset)

    def test_read_floating_point_from_eeprom_bad_size(self):
        input_dict = {
            'floating_point': True,
            'type': 'HHB',
        }
        offset = 0
        self.assertRaises(makerbot_driver.EEPROM.PoorlySizedFloatingPointError, self.reader.read_floating_point_from_eeprom, input_dict, offset)

    def test_read_floating_point_from_eeprom(self):
        input_dict = {
            'floating_point': True,
            'type': 'h',
            'offset': '0x0000',
        }
        expected = [128.50]
        offset = int(input_dict['offset'], 16)
        read_from_eeprom_mock = mock.Mock()
        read_from_eeprom_mock.return_value = struct.pack('<B', 128)
        self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
        self.assertEqual(expected, self.reader.read_floating_point_from_eeprom(
            input_dict, offset))

    def test_read_and_unpack_floating_point(self):
        offset = 0
        expected = [128.5]
        read_from_eeprom_mock = mock.Mock()
        read_from_eeprom_mock.return_value = struct.pack('<B', 128)
        self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
        got = self.reader.read_and_unpack_floating_point(offset)
        calls = read_from_eeprom_mock.mock_calls
        for i in range(len(calls)):
            self.assertEqual(calls[i][1], (offset + i, 1))

    def test_read_value_from_eeprom_mult(self):
        input_dict = {
            'type': 'B',
            'mult': '10',
        }
        expected_values = range(int(input_dict['mult']))
        reversed_values = expected_values[:]
        reversed_values.reverse()

        def return_mock_func(*args, **kwards):
            return struct.pack('<%s' % (input_dict['type']), reversed_values.pop())
        read_from_eeprom_mock = mock.Mock()
        read_from_eeprom_mock.side_effect = return_mock_func
        self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
        self.assertEqual(expected_values,
                         self.reader.read_value_from_eeprom(input_dict, 0))

    def test_read_value_from_eeprom_one_value(self):
        input_dict = {
            'type': 'B',
        }
        value = 120
        packed_value = struct.pack('<%s' % (input_dict['type']), value)
        read_from_eeprom_mock = mock.Mock()
        read_from_eeprom_mock.return_value = packed_value
        self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
        expected_value = struct.unpack(
            '<%s' % (input_dict['type']), packed_value)
        self.assertEqual(list(expected_value),
                         self.reader.read_value_from_eeprom(input_dict, 0))

    def test_read_value_from_eeprom_multiple_values(self):
        input_dict = {
            'type': 'BHi',
        }
        expected_values = [255, 1, 65535]
        reversed_values = expected_values[:]
        reversed_values.reverse()
        reversed_type = list(input_dict['type'])
        reversed_type.reverse()
        packed_values = []
        for the_type, the_value in zip(reversed_type, reversed_values):
            packed_values.append(struct.pack('<%s' % (the_type), the_value))

        def return_mock_func(*args, **kwards):
            return packed_values.pop()
        read_from_eeprom_mock = mock.Mock()
        read_from_eeprom_mock.side_effect = return_mock_func
        self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
        self.assertEqual(expected_values,
                         self.reader.read_value_from_eeprom(input_dict, 0))

    def test_read_string_from_eeprom(self):
        input_dict = {
            'offset': '0x0000',
            'type': 's',
            'length': 16,
        }
        read_eeprom_mock = mock.Mock()
        #We pack the string into an array to mimick the way
        #the actual function call reads in the value.
        read_eeprom_mock.return_value = array.array('B', 'asdf\x00')
        self.reader.s3g.read_from_EEPROM = read_eeprom_mock
        self.reader.read_string_from_eeprom(
            input_dict, int(input_dict['offset'], 16))
        expected_offset = int(input_dict['offset'], 16)
        read_eeprom_mock.assert_called_once_with(
            expected_offset, input_dict['length'])

    def test_read_values_from_eeprom_string_missing_variables(self):
        input_dict = {
            'offset': '0x0000',
            'type': 's',
        }
        self.assertRaises(
            KeyError, self.reader.read_from_eeprom, input_dict, 0)

    @unittest.skip("we no longer throw errors, we instead report an error value")
    def test_decode_string_no_null_terminator(self):
        #We pack the string into an array to mimick the way
        #the actual function call reads in the value.
        carray = array.array("B", 'iasef')
        with self.assertRaises(makerbot_driver.EEPROM.NonTerminatedStringError):
            self.reader.decode_string(carray)

    def test_decode_string_no_null_terminator(self):
        #We pack the string into an array to mimick the way
        #the actual function call reads in the value.
        carray = array.array("B", 'iasef')
        value = self.reader.decode_string(carray, 'err_default')
        self.assertEqual(value, 'err_default')

    def test_decode_string_good_string(self):
        #We pack the string into an array to mimick the way
        #the actual function call reads in the value.
        expected = 'asdf'
        string = array.array("B", expected + '\x00')
        self.assertEqual(expected, self.reader.decode_string(string))

    def test_unpack_value(self):
        cases = [
            ['B', 255],
            ['I', 252645135],
            ['H', 3855],
        ]
        for case in cases:
            val = struct.pack('<%s' % (case[0]), case[1])
            got_val = self.reader.unpack_value(val, case[0])[0]
            self.assertEqual(case[1], got_val)


if __name__ == '__main__':
    unittest.main()

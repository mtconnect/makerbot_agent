import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver
import tempfile

class testEepromVerifier(unittest.TestCase):

    def setUp(self):
        self.mock_hex = ":20000000010617FF9FFF7676287676FF1BFF97340000E91800000000000000000000000040\n:20002000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF40\n"
        with tempfile.NamedTemporaryFile(suffix='.hex', delete=False) as f:
            f.write(self.mock_hex)
            self.hex_path = f.name
        self.ev = makerbot_driver.EEPROM.EepromVerifier(self.hex_path)

    def tearDown(self):
        self.ev = None

    def test_cant_find_eeprom_map(self):
        self.mock_hex = ":20000000010617FF9FFF7676287676FF1BFF97340000E91800000000000000000000000040\n:20002000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF40\n"
        with tempfile.NamedTemporaryFile(suffix='.hex', delete=False) as f:
            f.write(self.mock_hex)
            hex_path = f.name
        wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        map_name = 'this map better not be in WD.some fake extension'
        with self.assertRaises(makerbot_driver.EEPROM.MissingEepromMapError):
            self.verifier= makerbot_driver.EEPROM.EepromVerifier(
                hex_path,        
                map_name=map_name,
                working_directory=wd,
            )

    def test_parse_hex_file(self):
        usable_hex = self.mock_hex[9:-3]
        the_bytes = {
            0: "01",
            1: "06",
            2: "17",
            3: "FF",
            4: "9F",
            5: "FF",
            6: "76",
            7: "76",
            8: "28",
            9: "76",
            10: "76",
            11: "FF",
            12: "1B",
            13: "FF",
            14: "97",
            15: "34",
            16: "00",
            17: "00",
            18: "E9",
            19: "18",
            20: "00",
            21: "00",
            22: "00",
            23: "00",
            24: "00",
            25: "00",
            26: "00",
            27: "00",
            28: "00",
            29: "00",
            30: "00",
            31: "00",
            32: "FF",
            33: "FF",
            34: "FF",
            35: "FF",
            36: "FF",
            37: "FF",
            38: "FF",
            39: "FF",
            40: "FF",
            41: "FF",
            42: "FF",
            43: "FF",
            44: "FF",
            45: "FF",
            46: "FF",
            47: "FF",
            48: "FF",
            49: "FF",
            50: "FF",
            51: "FF",
            52: "FF",
            53: "FF",
            54: "FF",
            55: "FF",
            56: "FF",
            57: "FF",
            58: "FF",
            59: "FF",
            60: "FF",
            61: "FF",
            62: "FF",
            63: "FF",
        }
        self.assertTrue(len(usable_hex) % 2 == 0)
        got_bytes, flags = self.ev.parse_hex_file(self.hex_path)
        self.assertEqual(the_bytes, got_bytes)
        for value in flags.values():
            self.assertFalse(value)
        self.assertEqual(len(got_bytes), len(flags))

    def test_get_number_byte_unsigned(self):
        expected_value = 0x7F
        the_type = 'B'
        self.ev.hex_map = {
            0: "7F",
            1: "FF"
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
        }
        offset = 0
        self.assertEqual(self.ev.get_number(offset, the_type), expected_value)
        self.assertTrue(self.ev.hex_flags[offset])
        self.assertFalse(self.ev.hex_flags[1])

    def test_get_number_byte_signed(self):
        expected_value = -128
        the_type = 'b'
        self.ev.hex_map = {
            0: "80",
            1: "FF"
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
        }
        offset = 0
        self.assertEqual(self.ev.get_number(offset, the_type), expected_value)
        self.assertTrue(self.ev.hex_flags[offset])
        self.assertFalse(self.ev.hex_flags[1])

    def test_get_number_short_unsigned(self):
        expected_value = 2720
        offset = 0
        the_type = 'H'
        self.ev.hex_map = {
            0: "A0",
            1: "0A",
            2: "FF",
            3: "FF",
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
            2: False,
            3: False,
        }
        self.assertEqual(self.ev.get_number(offset, the_type), expected_value)
        for i in [0, 1]:
            self.assertTrue(self.ev.hex_flags[i])
        for i in [2, 3]:
            self.assertFalse(self.ev.hex_flags[i])

    def test_get_number_short_signed(self):
        expected_value = 128
        offset = 0
        the_type = 'h'
        self.ev.hex_map = {
            0: "80",
            1: "00",
            2: "FF",
            3: "FF",
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
            2: False,
            3: False,
        }
        self.assertEqual(self.ev.get_number(offset, the_type), expected_value)
        for i in [0, 1]:
            self.assertTrue(self.ev.hex_flags[i])
        for i in [2, 3]:
            self.assertFalse(self.ev.hex_flags[i])

    def test_get_number_multiple_types(self):
        the_type = 'BB'
        with self.assertRaises(AssertionError):
            self.ev.get_number(0, the_type)

    def test_get_float(self):
        offset = 0
        expected_value = 128.5
        self.ev.hex_map = {
            0: "80",
            1: "80",
            2: "FF",
            3: "00",
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
            2: False,
            3: False,
        }
        self.assertAlmostEqual(expected_value, self.ev.get_float(offset), 1)
        for i in [0, 1]:
            self.assertTrue(self.ev.hex_flags[i])
        for i in [2, 3]:
            self.assertFalse(self.ev.hex_flags[i])

    def test_get_float_multiple_floats(self):
        the_type = 'HH'
        with self.assertRaises(AssertionError):
            self.ev.get_number(0, the_type)

    def test_get_string(self):
        offset = 0
        length = 16
        name = "The Replicatorzz"
        for i in range(len(name)):
            the_hex = hex(ord(name[i]))
            self.ev.hex_map[i] = the_hex[2:]
            self.ev.hex_flags[i] = False
        for i in range(len(name), 100):
            self.ev.hex_map[i] = "FF"
            self.ev.hex_flags[i] = False

        self.assertEqual(name, self.ev.get_string(offset, length))

        for i in range(len(name)):
            self.assertTrue(self.ev.hex_flags[i])
        for i in range(len(name), 100):
            self.assertFalse(self.ev.hex_flags[i])

    def test_check_unread_values_all_good(self):
        self.ev.hex_map = {
            0: "FF",
            1: "FF",
            2: "FF",
            3: "FF",
            4: "FF",
            5: "FF",
            6: "FF",
            7: "FF",
            8: "FF",
            9: "FF",
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
        }
        status, val = self.ev.check_unread_values()
        self.assertTrue(status)
        self.assertTrue(len(val['unmapped_entries']) == 0)

    def test_check_unread_values_one_bad(self):
        self.ev.hex_map = {
            0: "00",
            1: "FF",
            2: "FF",
            3: "FF",
            4: "FF",
            5: "FF",
            6: "FF",
            7: "FF",
            8: "FF",
            9: "FF",
        }
        self.ev.hex_flags = {
            0: False,
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
        }
        status, val = self.ev.check_unread_values()
        self.assertFalse(status)
        self.assertEqual([0], val['unmapped_entries'])

    def test_check_unread_values_bad_one_was_read(self):
        self.ev.hex_map = {
            0: "00",
            1: "FF",
            2: "FF",
            3: "FF",
            4: "FF",
            5: "FF",
            6: "FF",
            7: "FF",
            8: "FF",
            9: "FF",
        }
        self.ev.hex_flags = {
            0: True,
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
        }
        status, val = self.ev.check_unread_values()
        self.assertTrue(status)
        self.assertTrue(len(val['unmapped_entries']) == 0)

    def test_check_unread_values_all_read(self):
        self.ev.hex_map = {
            0: "00",
            1: "FF",
            2: "FF",
            3: "FF",
            4: "FF",
            5: "FF",
            6: "FF",
            7: "FF",
            8: "FF",
            9: "FF",
        }
        self.ev.hex_flags = {
            0: True,
            1: True,
            2: True,
            3: True,
            4: True,
            5: True,
            6: True,
            7: True,
            8: True,
            9: True,
        }
        status, val = self.ev.check_unread_values()
        self.assertTrue(status)
        self.assertTrue(len(val['unmapped_entries']) == 0)

    def test_check_value_validity_list(self):
        constraint = "l,0,1,2,3"
        value = 0
        self.ev.check_value_validity_list = mock.Mock()
        self.ev.check_value_validity(value, constraint)
        self.ev.check_value_validity_list.assert_called_once_with(value, constraint)

    def test_check_value_validity_min_max(self):
        constraint = 'm,0,100'
        value = 50
        self.ev.check_value_validity_min_max = mock.Mock()
        self.ev.check_value_validity(value, constraint)
        self.ev.check_value_validity_min_max.assert_called_once_with(value, constraint)

    def test_check_value_validity_any(self):
        constraint = 'a'
        value = 'who cares'
        self.assertTrue(self.ev.check_value_validity(value, constraint))

    def test_check_value_validity_list(self):
        cases = [
            ['a', ['l', 'a', 'b', 1, 2], True],
            ['a', ['l', 'b', 'c', 'd'], False],
            [1, ['l', 1, 2, 3], True],
            [1, ['l'], False],
        ]
        for case in cases:
            self.assertEqual(case[2], self.ev.check_value_validity_list(case[0], case[1]))

    def test_check_value_validity_min_max(self):
        cases = [
            [50, ['m', 0, 100], True],
            [0, ['m', 0, 100], True],
            [100, ['m', 0, 100], True],
            [-50, ['m', 0, 100], False],
            [-50, ['m', -100, 100], True],
        ]
        for case in cases:
            self.assertEqual(case[2], self.ev.check_value_validity_min_max(case[0], case[1]))


if __name__ == "__main__":
    unittest.main()

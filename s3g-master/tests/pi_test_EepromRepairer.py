import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import mock
import struct

import makerbot_driver

class TestEepromRepairer(unittest.TestCase):

    def setUp(self):
        self.er = makerbot_driver.EEPROM.EepromRepairer()

    def tearDown(self):
        self.er = None

    def test_cant_find_eeprom_map(self):
        wd = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        map_name = 'this map better not be in WD.some fake extension'
        with self.assertRaises(makerbot_driver.EEPROM.MissingEepromMapError):
            self.repairer = makerbot_driver.EEPROM.EepromRepairer(
                map_name=map_name,
                working_directory=wd,
            )


    def test_repair_mapped_region_list(self):
        sub_dict = {
            'constraints': 'l,1,2,3',
            'offset': 0xff,
            'type': 'B',
        }
        self.er.repair_mapped_region_list = mock.Mock()
        self.er.repair_mapped_region(sub_dict)
        self.er.repair_mapped_region_list.assert_called_once_with(sub_dict)

    def test_repair_mapped_region_min_max(self):
        sub_dict = {
            'constraints': 'm,-50,50',
            'offset': 0xff,
            'type': 'B',
        }
        self.er.repair_mapped_region_min_max = mock.Mock()
        self.er.repair_mapped_region(sub_dict)
        self.er.repair_mapped_region_min_max.assert_called_once_with(sub_dict)

    def test_repair_mapped_region_any(self):
        sub_dict = {
            'constraints': 'a',
            'offset': 0xff,
            'type': 'B',
        }
        self.er.repair_mapped_region_any = mock.Mock()
        self.er.repair_mapped_region(sub_dict)
        self.er.repair_mapped_region_any.assert_called_once_with(sub_dict)

    def test_build_packed_data(self):
        length = 10
        expected_data = struct.pack('<%s' % ('B'*length), 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff)
        got_data = self.er.build_packed_data(length)
        self.assertEqual(expected_data, got_data)

    def test_repair_unmapped_region(self):
        unmapped = range(100, 110)
        expected_offset = 100
        expected_data = struct.pack('<%s' % ('B'*len(unmapped)), 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff)
        self.er.s3g = mock.Mock()
        self.er.repair_unmapped_region(unmapped)
        self.er.s3g.write_to_EEPROM.assert_called_once_with(expected_offset, expected_data)

    def test_bifurcate_date(self):
        cases = [
            [[1, 2, 3, 4, 5], [1, 2], [3, 4, 5]],
            [[1, 2, 3, 4], [1, 2], [3, 4]],
        ]
        for case in cases:
            left, right = self.er._bifurcate_data(case[0])
            for a, b in zip([left, right], [case[1], case[2]]):
                self.assertEqual(a, b)

    def test_build_sequences(self):
        cases = [
            [[1, 2, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15], [range(1, 3), range(5, 8), range(9, 16)]],
            [[], []],
            [[1, 3, 5, 7, 9], [[1], [3], [5], [7], [9]]],
            [[-1, 0, 1, 50, 51, 52], [[-1, 0, 1], [50, 51, 52]]],
        ]
        for case in cases:
            got_sequences = self.er.build_sequences(case[0])
            self.assertEqual(case[1], got_sequences)

    def test_flush_out_data_first_is_fine(self):
        data = range(15)
        offset = 0
        s3g_mock = mock.Mock()
        self.er.s3g = s3g_mock
        self.er._flush_out_data(offset, data)
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
        self.er.s3g = s3g_mock
        a, b = self.er._bifurcate_data(data)
        expect_a_offset = offset
        expect_b_offset = offset + len(a)
        self.er._flush_out_data(offset, data)
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

if __name__ == "__main__":
    unittest.main()

from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
import threading
import uuid
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock

import makerbot_driver


class TestMachineFactor(unittest.TestCase):

    def setUp(self):
        self.factory = makerbot_driver.MachineFactory()

    def tearDown(self):
        self.factory = None

    def test_get_profile_regex_bot_not_found(self):
        bot_dict = {
            'vid': -1,
            'pid': -1,
            'tool_count': -1,
        }
        expected_regex = None
        self.assertEqual(
            expected_regex, self.factory.get_profile_regex(bot_dict))

#  def test_get_profile_regex_hax_vid_pid_bot_found(self):
#    bot_dict = {
#        'fw_version' : 506,
#        'vid' : 0x23c1,
#        'pid' : 0xd314,
#        'tool_count'  : 1,
#        }
#    expected_regex = '.*ReplicatorSingle.*'
#    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

    def test_get_profile_regex_had_vid_pid_rep2_tool_count1(self):
        bot_dict = {
            'vid': 0x23C1,
            'pid': 0xB015,
            'tool_count': 1,
        }
        expected_regex = '.*Replicator2'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_had_vid_pid_rep2_tool_count2(self):
        bot_dict = {
            'vid': 0x23C1,
            'pid': 0xB015,
            'tool_count': 2,
        }
        expected_regex = '.*Replicator2X'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tom_tool_count_1(self):
        bot_dict = {
            'vid': 0x0403,
            'pid': 0x6001,
            'tool_count': 1,
        }
        expected_regex = '.*TOMStepstruderSingle'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tom_tool_count_2(self):
        bot_dict = {
            'vid': 0x0403,
            'pid': 0x6001,
            'tool_count': 2,
        }
        expected_regex = '.*TOMStepstruderDual'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tool_count_1(self):
        bot_dict = {
            'vid': 0x23c1,
            'pid': 0xd314,
            'tool_count': 1,
        }
        expected_regex = '.*ReplicatorSingle'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tool_count_2(self):
        bot_dict = {
            'vid': 0x23c1,
            'pid': 0xd314,
            'tool_count': 2,
        }
        expected_regex = '.*ReplicatorDual'
        match = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, match)


class TestBuildFromPortMockedMachineInquisitor(unittest.TestCase):
    def setUp(self):
        self.s3g_mock = mock.Mock(makerbot_driver.s3g)
        self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
        self.inquisitor.create_s3g = mock.Mock()
        self.inquisitor.create_s3g.return_value = self.s3g_mock
        self.factory = makerbot_driver.MachineFactory()
        self.factory.create_inquisitor = mock.Mock()
        self.factory.create_inquisitor.return_value = self.inquisitor

    def test_build_from_port_invalid_vid_pid(self):
        vid, pid = 0,0
        tool_count = 1
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_version = mock.Mock(return_value=701)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        expected_s3g = None
        expected_profile = None
        expected_parser = None
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertEqual(expected_s3g, getattr(return_obj, 's3g'))
        self.assertEqual(expected_profile, getattr(return_obj, 'profile'))
        self.assertEqual(expected_parser, getattr(return_obj, 'gcodeparser'))

    def test_build_from_port_invalid_tool_count(self):
        # result here is a replicator Dual - this is the default for valid replicator vid pid
        # we don't want a situation where the eeprom is corrupt and the bot cannot be recognized
        tool_count = -1
        vid, pid = 0x23C1, 0xD314
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        expected_mock_s3g_obj = 'SUCCESS500'
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorSingle')
        expected_profile.values['print_to_file_type'] = ['s3g']
        expected_profile.values['software_variant'] = '0x00'
        expected_profile.values['tool_count_error'] = True
        expected_parser = makerbot_driver.Gcode.GcodeParser()
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

#    @unittest.skip("This functionality has been disabled for now")
    def test_build_from_port_tool_count_1_Replicator(self):
        #Time to mock all of s3g's version!
        tool_count = 1
        vid, pid = 0x23C1, 0xD314
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS500'
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorSingle')
        expected_profile.values['print_to_file_type'] = ['s3g']
        expected_profile.values['software_variant'] = '0x00'
        expected_profile.values['tool_count_error'] = False
        expected_parser = makerbot_driver.Gcode.GcodeParser()
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_tool_count_2_mightyboard(self):
        #Time to mock all of s3g's version!
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS500'
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type'] = ['s3g']
        expected_profile.values['software_variant'] = '0x00'
        expected_profile.values['tool_count_error'] = False
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_x3g_version(self):
        #Time to mock all of s3g's version!
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        advanced_version_info = {
            'Version': 700,
            'InternalVersion': 0,
            'SoftwareVariant': 1,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS500'
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type']=['x3g']
        expected_profile.values['software_variant'] = '0x01'
        expected_profile.values['tool_count_error'] = False
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.s3g_mock.set_print_to_file_type.assert_called_once_with('x3g')
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_s3g_version(self):
        #Time to mock all of s3g's version!
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        advanced_version_info = {
            'Version': 500,
            'InternalVersion': 0,
            'SoftwareVariant': 0,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS500'
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type']=['s3g']
        expected_profile.values['software_variant'] = '0x00'
        expected_profile.values['tool_count_error'] = False
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.s3g_mock.set_print_to_file_type.assert_called_once_with('s3g')
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)


class TestMachineInquisitor(unittest.TestCase):
    def setUp(self):
        self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
        self.s3g_mock = mock.Mock(makerbot_driver.s3g)
        self.inquisitor.create_s3g = mock.Mock(return_value=self.s3g_mock)
        self.condition = threading.Condition()

    def tearDown(self):
        self.inquisitor = None

    def test_no_advanced_version(self):
        vid, pid = 0x23C1, 0xB404
        tool_count = 1
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_version = mock.Mock(return_value=500)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        self.s3g_mock.set_print_to_file_type('s3g')
        expected_settings = {'vid':vid, 'pid':pid, 'tool_count':tool_count, 'tool_count_error':False, 'print_to_file_type':'s3g', 'software_variant':'0x00'}
        s3g, got_settings = self.inquisitor.query(self.condition)
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

    def test_TOM_firmware_version(self):
        vid, pid = 0x2341, 0x0010
        tool_count = 1
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_version = mock.Mock(return_value=401)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        self.s3g_mock.set_print_to_file_type('s3g')
        expected_settings = {'vid':vid, 'pid':pid, 'tool_count':tool_count, 'tool_count_error':False, 'print_to_file_type':'s3g', 'software_variant':'0x00'}
        s3g, got_settings = self.inquisitor.query(self.condition)
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

    def test_TOM_firmware_old_version(self):
        vid, pid = 0x2341, 0x0010
        tool_count = 1
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_version = mock.Mock(return_value=304)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        self.s3g_mock.set_print_to_file_type('s3g')
        expected_settings = {'vid':vid, 'pid':pid, 'tool_count':tool_count, 'tool_count_error':False, 'print_to_file_type':'s3g', 'software_variant':'0x00'}
        s3g, got_settings = self.inquisitor.query(self.condition)
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

    def test_s3g_with_advanced_version(self):
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        advanced_version_info = {
            'Version': 600,
            'InternalVersion': 0,
            'SoftwareVariant': 0,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=701)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        self.s3g_mock.set_print_to_file_type('s3g')
        expected_settings = {'vid':vid, 'pid':pid, 'tool_count':tool_count, 'tool_count_error':False, 'print_to_file_type':'s3g', 'software_variant':'0x00'}
        s3g, got_settings = self.inquisitor.query(self.condition)
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

    def test_x3g_with_advanced_version(self):
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        advanced_version_info = {
            'Version': 700,
            'InternalVersion': 0,
            'SoftwareVariant': 1,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=701)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        self.s3g_mock.set_print_to_file_type('x3g')
        expected_settings = {'vid':vid, 'pid':pid, 'tool_count':tool_count, 'tool_count_error':False, 'print_to_file_type':'x3g', 'software_variant':'0x01'}
        s3g, got_settings = self.inquisitor.query(self.condition)
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

if __name__ == '__main__':
    unittest.main()

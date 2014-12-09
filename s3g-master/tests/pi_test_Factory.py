import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import mock
import tempfile

import makerbot_driver


class TestFactory(unittest.TestCase):

    def setUp(self):
        self.real_from_filename = makerbot_driver.s3g.from_filename
        self.from_filename_mock = mock.Mock()
        makerbot_driver.s3g.from_filename = self.from_filename_mock

    def tearDown(self):
        makerbot_driver.s3g.from_filename = self.real_from_filename

    def test_create_parser_legacy(self):
        machine_name = 'TOMStepstruderSingle'
        parser = makerbot_driver.create_parser(machine_name, legacy=True)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertEqual(getattr(parser, 's3g'), None)
        self.assertTrue(parser.state.__class__.__name__ == 'LegacyGcodeStates')
        self.assertTrue(parser.state.profile.values['type']
                        == "Thing-O-Matic Single, Stepstruder Mk6+")

    def test_create_parser(self):
        machine_name = 'ReplicatorSingle'
        parser = makerbot_driver.create_parser(machine_name, legacy=False)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertEqual(getattr(parser, 's3g'), None)
        self.assertTrue(parser.state.__class__.__name__ == 'GcodeStates')
        self.assertTrue(
            parser.state.profile.values['type'] == "The Replicator Single")

    def test_create_print_to_file_legacy(self):
        machine_name = 'TOMStepstruderSingle'
        with tempfile.NamedTemporaryFile(suffix='.s3g', delete=True) as f:
            path = f.name
        parser = makerbot_driver.create_print_to_file_parser(
            path, machine_name, legacy=True)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.s3g.__class__.__name__ == 's3g')
        self.assertTrue(parser.s3g.writer.__class__.__name__ == 'FileWriter')
        self.assertTrue(parser.s3g.writer.file.name == path)
        self.assertTrue(parser.state.__class__.__name__ == 'LegacyGcodeStates')
        self.assertTrue(parser.state.profile.values['type']
                        == 'Thing-O-Matic Single, Stepstruder Mk6+')

    def test_create_print_to_file(self):
        machine_name = 'ReplicatorSingle'
        with tempfile.NamedTemporaryFile(suffix='.s3g', delete=True) as f:
            path = f.name
        parser = makerbot_driver.create_print_to_file_parser(
            path, machine_name)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.s3g.__class__.__name__ == 's3g')
        self.assertTrue(parser.s3g.writer.__class__.__name__ == 'FileWriter')
        self.assertTrue(parser.s3g.writer.file.name == path)
        self.assertTrue(parser.state.__class__.__name__ == 'GcodeStates')
        self.assertTrue(
            parser.state.profile.values['type'] == 'The Replicator Single')

if __name__ == "__main__":
    unittest.main()

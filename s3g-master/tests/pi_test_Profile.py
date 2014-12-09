import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import json
import shutil
import tempfile

import makerbot_driver
#Import this to test _getprofiledir
import makerbot_driver.profile


class ProfileInitTests(unittest.TestCase):

    def test_bad_profile_name(self):
        bad_name = 'this_is_going_to_fail :('

        with self.assertRaises(IOError):
            makerbot_driver.Profile(bad_name)

    def test_good_profile_name(self):
        name = "ReplicatorSingle"
        p = makerbot_driver.Profile(name)
        path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'makerbot_driver',
            'profiles',
            name + '.json',
        )
        with open(path) as f:
            expected_vals = json.load(f)
        self.assertEqual(expected_vals, p.values)

    def test_Profile_profiledir(self):
        profiledir = tempfile.mkdtemp()
        try:
            path = os.path.join(profiledir, 'Test.json')
            with open(path, 'w') as fp:
                values = {'key': 'value'}
                json.dump(values, fp)
            profile = makerbot_driver.Profile('Test', profiledir)
            self.assertEqual(values, profile.values)
        finally:
            shutil.rmtree(profiledir)

    def test_profile_access(self):
        """
        Make sure we have no issues accessing the information in the machine profile
        """
        expected_name = "The Replicator Dual"
        name = "ReplicatorDual"
        p = makerbot_driver.Profile(name)
        self.assertEqual(p.values['type'], expected_name)

    def test_list_profiles(self):
        expected_profiles = [
            'ReplicatorDual',
            'ReplicatorSingle',
            'TOMStepstruderSingle',
            'TOMStepstruderDual',
            'Replicator2',
            'Replicator2X',
        ]
        for profile in expected_profiles:
            self.assertTrue(profile in makerbot_driver.list_profiles())

    def test_list_profiles_profiledir(self):
        profiledir = tempfile.mkdtemp()
        try:
            self.assertEqual(
                [], list(makerbot_driver.list_profiles(profiledir)))
            path = os.path.join(profiledir, 'Test.json')
            with open(path, 'w') as fp:
                values = {'key': 'value'}
                json.dump(values, fp)
            self.assertEqual(
                ['Test'], list(makerbot_driver.list_profiles(profiledir)))
        finally:
            shutil.rmtree(profiledir)

    def test__getprofiledir(self):
        '''Make sure that _getprofiledir returns its argument when that argument is
        not None.

        '''
        profiledir = 'x'
        self.assertEqual(
            profiledir, makerbot_driver.profile._getprofiledir(profiledir))

    def test__getprofiledir_default(self):
        '''Make sure that _getprofiledir returns the default profile directory when
        its argument is None.

        '''
        profiledir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'makerbot_driver', 'profiles'))
        self.assertEqual(
            profiledir, makerbot_driver.profile._getprofiledir(None))

    def test_search_profiles_with_regex(self):
        cases = [
            ['.*Dual.*', ['ReplicatorDual.json', 'TOMStepstruderDual.json']],
            ['.*Single.*', ['ReplicatorSingle.json', 'TOMStepstruderSingle.json']],
            ['.*Replicator.*', ['Replicator2.json',
                                'ReplicatorDual.json',
                                'ReplicatorSingle.json',
                                'Replicator2X.json',
                                ]],
            ['.*FAIL*', []],
        ]
        for case in cases:
            self.assertEqual(
                sorted(case[1]), sorted(makerbot_driver.search_profiles_with_regex(case[0])))

if __name__ == '__main__':
    unittest.main()

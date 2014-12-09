import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver


class TestProcessorFactory(unittest.TestCase):

    def setUp(self):
        self.f = makerbot_driver.GcodeProcessors.ProcessorFactory()

    def tearDown(self):
        self.f = None

    def test_list_processors(self):
        pros = makerbot_driver.GcodeProcessors.all
        self.assertEqual(pros, self.f.list_processors())

    def test_create_processor_from_name_not_a_processor(self):
        pro = 'THIS ISNT A VALID PREPROCESSOR NAME'
        self.assertRaises(makerbot_driver.GcodeProcessors.ProcessorNotFoundError, self.f.create_processor_from_name, pro)

    def test_create_processor_from_name(self):
        skeinforge_pro = makerbot_driver.GcodeProcessors.Skeinforge50Processor(
        )
        expected_class = skeinforge_pro.__class__
        got_pro = self.f.create_processor_from_name('Skeinforge50Processor')
        got_class = got_pro.__class__
        self.assertEqual(expected_class, got_class)

    def test_create_multiple_pros_no_pros(self):
        got_pros = list(self.f.get_processors([]))
        self.assertEqual(0, len(got_pros))

    def test_get_processors_one_pro(self):
        skeinforge_pro = makerbot_driver.GcodeProcessors.Skeinforge50Processor(
        )
        expected_class = skeinforge_pro.__class__
        desired_pro = 'Skeinforge50Processor'
        got_pros = list(self.f.get_processors(desired_pro))
        self.assertEqual(1, len(got_pros))
        self.assertEqual(expected_class, got_pros[0].__class__)

    def test_process_list_with_commas(self):
        cases = [
            ['a, b, c, d, ', ['a', 'b', 'c', 'd']],
            ['a,b,c,d,e,', ['a', 'b', 'c', 'd', 'e']],
            ['a, b, c, d,e', ['a', 'b', 'c', 'd', 'e']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.f.process_list_with_commas(case[0]))

    def test_get_processors_multiple_pros(self):
        desired_pros = 'Skeinforge50Processor, RpmProcessor, SlicerProcessor'
        got_pros = list(self.f.get_processors(desired_pros))
        expected_pros = [
            makerbot_driver.GcodeProcessors.Skeinforge50Processor(),
            makerbot_driver.GcodeProcessors.RpmProcessor(),
            makerbot_driver.GcodeProcessors.SlicerProcessor(),
        ]
        self.assertEqual(len(expected_pros), len(got_pros))
        for expect, got in zip(expected_pros, got_pros):
            self.assertEqual(expect.__class__, got.__class__)

if __name__ == '__main__':
    unittest.main()

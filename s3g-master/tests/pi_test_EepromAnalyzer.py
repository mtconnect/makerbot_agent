import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import io
import json
import tempfile

import makerbot_driver


class TestLineReader(unittest.TestCase):

    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix='.hh', delete=False) as f:
            input_file = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = f.name
        self.reader = makerbot_driver.EEPROM.eeprom_analyzer(
            open(input_file), open(output_file, 'w'))

    def tearDown(self):
        self.reader = None

    def test_parse_out_name_and_location(self):
        line = 'const static uint16_t    <name> = <location>;'
        expected_return = ('<name>', '<location>')
        for s in ['', '\r', '\n']:
            got_return = self.reader.parse_out_name_and_location(line + s)
            self.assertEqual(expected_return, got_return)

    def test_parse_out_namespace_name(self):
        lines = [
            'namespace toolhead_eeprom {\n',
            'namespace toolhead_eeprom {\r',
            'namespace toolhead_eeprom {',
            '   namespace toolhead_eeprom {',
            'namespace  toolhead_eeprom {         ',
            'namespace      toolhead_eeprom {',
            'namespace toolhead_eeprom     {',
        ]
        expected_name = 'toolhead_eeprom'
        for line in lines:
            got_name = self.reader.parse_out_namespace_name(line)
            self.assertEqual(expected_name, got_name)

    def test_parse_out_variables_good_line(self):
        line = '       //$S:1 $B:2 $C:3 $D:here are some spaces                   \n'
        expected = ['S:1', 'B:2', 'C:3', 'D:here are some spaces']
        self.assertEqual(expected, self.reader.parse_out_variables(line))

    def testDumpJSON(self):
        test_dic = {
            'a': 1,
            'b': 2,
            'c': 3,
        }
        self.reader.dump_json(test_dic)
        output_file = self.reader.output_fh.name
        self.reader.output_fh.close()
        with open(output_file, 'r') as f:
            written_vals = json.load(f)
        self.assertEqual(test_dic, written_vals)

if __name__ == '__main__':
    unittest.main()

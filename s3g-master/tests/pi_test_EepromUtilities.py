import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver
import tempfile

class testEepromUtilities(unittest.TestCase):

    def test_get_eeprom_map_constraints(self):
        eeprom_map = {
            'a': {
                'constraints': ['l', 1, 2],
            },
            'b': {
                'constraints': ['m', 0, 100],
            },
            'c': {
                'sub_map': {
                    'd': {
                        'constraints': ['l', 'a', 'b'],
                    },
                    'e': {
                        'sub_map': {
                            'f': {
                                'constraints': ['m', -10, 10],
                            }
                        }
                    }
                }
            }
        }

        expected_contexts = [
            ['a'],
            ['b'],
            ['c', 'sub_map', 'd'],
            ['c', 'sub_map', 'e', 'sub_map', 'f'],
        ]
        expected_contexts.sort()
        got_values = makerbot_driver.EEPROM.get_eeprom_map_contexts(eeprom_map)
        self.assertEqual(expected_contexts, got_values)

    def test_get_dict_by_context(self):
        dct = {
            'a': {'aa': 0},
            'b': {
                'sub_map': {
                    'c': {'cc': 0},
                    'd': {
                        'sub_map': {
                            'e': {'ee': 0},
                            'f': {'ff': 0},
                            'h': {
                                'sub_map': {
                                    'g': {'gg': 0},
                                }
                            }
                        }
                    }
                }
            }
        }
        cases = [
            [['a'], dct['a']],
            [['b', 'sub_map', 'c'], dct['b']['sub_map']['c']],
            [['b', 'sub_map', 'd', 'sub_map', 'e'], dct['b']['sub_map']['d']['sub_map']['e']],
            [['b', 'sub_map', 'd', 'sub_map', 'h', 'sub_map', 'g'], dct['b']['sub_map']['d']['sub_map']['h']['sub_map']['g']]
        ]
        for case in cases:
            self.assertEqual(makerbot_driver.EEPROM.get_dict_by_context(dct, case[0]), case[1])

    def test_get_offset_by_context(self):
        dct = {
            'a': {'offset': hex(0)},
            'b': {
                'offset': hex(100),
                'sub_map': {
                    'c': {'offset': hex(1)},
                    'd': {
                        'offset': hex(20),
                        'sub_map': {
                            'e': {'offset': hex(1)},
                            'f': {'offset': hex(2)},
                            'h': {
                                'offset': hex(10),
                                'sub_map': {
                                    'g': {'offset': hex(3)},
                                }
                            }
                        }
                    }
                }
            }
        }
        cases = [
            [['a'], 0],
            [['b', 'sub_map', 'c'], 101],
            [['b', 'sub_map', 'd', 'sub_map', 'e'], 121],
            [['b', 'sub_map', 'd', 'sub_map', 'h', 'sub_map', 'g'], 133]
        ]
        for case in cases:
            self.assertEqual(makerbot_driver.EEPROM.get_offset_by_context(dct, case[0]), case[1])

    def test_parse_out_constraints(self):
        cases = [
            ['l,a,b,1,2', ['l', 'a', 'b', 1, 2]],
            ['l,1,2,3,0xFF', ['l', 1, 2, 3, 255]],
            ['m,0x00,0xFF', ['m', 0, 255]],
            ['m,50,0xA0', ['m', 50, 160]],
            ['a', ['a']],
        ]
        for case in cases:
            self.assertEqual(makerbot_driver.EEPROM.parse_out_constraints(case[0]), case[1])

if __name__ == "__main__":
    unittest.main()

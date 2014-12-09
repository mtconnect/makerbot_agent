import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver


class CRCTests(unittest.TestCase):
    def test_cases(self):
        # Calculated using the processing tool 'ibutton_crc'
        cases = [
            [b'', 0],
            [b'abcdefghijk', 0xb4],
            [b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f',
              0x3c],
        ]
        for case in cases:
            assert makerbot_driver.Encoder.CalculateCRC(case[0]) == case[1]

if __name__ == "__main__":
    unittest.main()

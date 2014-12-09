# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import makerbot_driver

class TimeoutTest(unittest.TestCase):
    def test_timeout(self):
        '''Test that the pyserial layer can correctly connect to a bot without
        getting any timeout errors.

        '''

        port = raw_input('specify a real active port on your OS to test> ')
        s3g = makerbot_driver.s3g.from_filename(port)
        s3g.get_version()

if '__main__' == __name__:
    unittest.main()

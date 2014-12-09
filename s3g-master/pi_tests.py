#!/usr/bin/python
import sys

"""
Runs tests in the form of ./tests/*.py
Supposed to be super short, so we skip the longer
tests of gcodeFileReading
"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import logging

#Configure logging (This should only be done for testing, nowhere else)
logging.basicConfig()
#Disable logging
logging.disable(100)

if __name__ == "__main__":
  all_tests = unittest.TestLoader().discover('tests', pattern='*.py') 
  for test in all_tests:
    pi_pattern = 'pi_test_'
    if pi_pattern in str(test):
      unittest.TextTestRunner(verbosity=0).run(test)
sys.exit()

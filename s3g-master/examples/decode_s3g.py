"""
Decode an s3g file into commands and registers.
"""

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse

parser = optparse.OptionParser()
parser.add_option("-i", "--input_file", dest="input_file",
                  help="input file to parse")
parser.add_option("-o", "--output_file", dest="output_file",
                  help="output file with decoded information")
(options, args) = parser.parse_args()

reader = makerbot_driver.FileReader.FileReader()
#reader.file = open(options.input_file, 'rb')
def callback(percent):
    print percent
with open(options.input_file, 'rb') as reader.file:
    payloads = reader.ReadFile(callback)
with open(options.output_file, 'w') as f:
  for payload in payloads:
    f.write(str(payload) + '\n')

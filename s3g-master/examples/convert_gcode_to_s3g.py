"""
Given a gcode file as input, transform that 
file into s3g commands for a makerbot printer.
"""

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse
import tempfile
import threading

parser = optparse.OptionParser()
parser.add_option("-i", "--inputfile", dest="input_file",
                  help="gcode file to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-s", "--sequences", dest="sequences",
                  help="Flag to not use makerbot_driver's start/end sequences",
                  default=True, action="store_false")
(options, args) = parser.parse_args()

condition = threading.Condition()
s = makerbot_driver.s3g()
s.writer = makerbot_driver.Writer.FileWriter(open(options.output_file, 'wb'), condition)

profile = makerbot_driver.Profile(options.machine)

filename = os.path.basename(options.input_file)
filename = os.path.splitext(filename)[0]

parser = makerbot_driver.Gcode.GcodeParser()
parser.state.values["build_name"] = filename
parser.state.profile = profile
parser.s3g = s

ga = makerbot_driver.GcodeAssembler(profile)
start, end, variables = ga.assemble_recipe(tool_0=True, tool_1=True, material='PLA')
start_gcode = ga.assemble_start_sequence(start)
end_gcode = ga.assemble_end_sequence(end)
parser.environment.update(variables)

if options.sequences:
  for line in start_gcode:
    parser.execute_line(line)

with open(options.input_file) as f:
  for line in f:
    parser.execute_line(line)

if options.sequences:
  for line in end_gcode:
    parser.execute_line(line)

s.writer.file.close()

finito = makerbot_driver.Gcode.FileComplete()
finito.finish(options.output_file)

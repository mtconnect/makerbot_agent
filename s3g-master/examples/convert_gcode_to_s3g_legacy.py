import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports as lp
import optparse

parser = optparse.OptionParser()
parser.add_option("-i", "--inputfile", dest="input_file",
                  help="gcode file to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
parser.add_option("-s", "--sequences", dest="sequences",
                  help="Flag to not use makerbot_driver's start/end sequences",
                  default=True, action="store_false")
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
(options, args) = parser.parse_args()

parser = makerbot_driver.create_print_to_file_parser(options.output_file, 'TOMStepstruderSingle', legacy=True)

assembler = makerbot_driver.GcodeAssembler(parser.state.profile)
start, end, variables = assembler.assemble_recipe(
    material='ABS',
    begin_print='tom_begin',
    homing='tom_homing',
    start_position='tom_start_position',
    end_start_sequence='tom_end_start_sequence',
    end_position='tom_end_position',
    end_print='tom_end',
)
start_gcode = assembler.assemble_start_sequence(start)
end_gcode = assembler.assemble_end_sequence(end)

filename = os.path.basename(options.input_file)
filename = os.path.splitext(filename)[0]

parser.environment.update(variables)
parser.state.values["build_name"] = filename[:15]

parser.s3g.print_to_file_type = ['x3g']

parser.s3g.clear_buffer()
parser.s3g.reset()
if options.sequences:
    for line in start_gcode:
        parser.execute_line(line)
with open(options.input_file) as f:
    for line in f:
        print line
        parser.execute_line(line)
if options.sequences:
    for line in end_gcode:
        print line
        parser.execute_line(line)

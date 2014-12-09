"""
Given a gcode file as input, transform that 
file into s3g commands for a makerbot printer.
"""

import os
import sys
# assume examples are run at the base directory of the project
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import makerbot_driver
import optparse
import tempfile
import threading

parser = optparse.OptionParser(usage="use this to check if a gcode file is compatible with makerbot_driver")
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-s", "--sequences", dest="sequences",
                  help="Flag to not use makerbot_driver's start/end sequences",
                  default=True, action="store_false")

(options, args) = parser.parse_args()

for input_file in args: 
  validGcode = True
  fh = tempfile.NamedTemporaryFile() 

  s = makerbot_driver.s3g()
  condition = threading.Condition()
  s.writer = makerbot_driver.Writer.FileWriter(fh, condition) 

  profile = makerbot_driver.Profile(options.machine)

  filename = os.path.basename(input_file)
  filename = os.path.splitext(filename)[0]

  parser = makerbot_driver.Gcode.GcodeParser()
  parser.state.values["build_name"] = filename
  parser.state.profile = profile
  parser.s3g = s

  ga = makerbot_driver.GcodeAssembler(profile)
  start, end, variables = ga.assemble_recipe()
  start_gcode = ga.assemble_start_sequence(start)
  end_gcode = ga.assemble_end_sequence(end)
  parser.environment.update(variables)

  try: 
    if options.sequences:
      for line in start_gcode:
        parser.execute_line(line)
  except Exception, e: 
      validGcode = False
      print(e)


  try:
    with open(input_file) as f:
      for line in f:
        parser.execute_line(line)
  except Exception, e: 
    validGcode = False
    print(e)

  try: 
    if options.sequences:
      for line in end_gcode:
        parser.execute_line(line)
  except Exception, e: 
      validGcode = False
      print(e)


  finito = makerbot_driver.Gcode.FileComplete()
  finito.finish_fh(fh)
  
  s.writer.close()

  if not validGcode:
    print("Invalid Gcode in file "+ input_file) 
    exit(-1) 

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse

parser = optparse.OptionParser()
parser.add_option('-i', '--input_file', dest='input_file',
                  help='the file you want to process')
parser.add_option('-o', '--output_file', dest='output_file',
                  help='name of the file after processing')
parser.add_option('-p', '--processor', dest='processor',
                  help='the name of the processor')
parser.add_option('-l', '--list_processors', dest='list',
                  help='If desired, lists processors', 
                  default=False, action='store_true')
(options, args) = parser.parse_args()

prepro_fact = makerbot_driver.GcodeProcessors.ProcessorFactory()
if options.list:
  print '-----Here are the processors you can choose from-----' 
  prepros = prepro_fact.list_processors()
  for p in prepros:
    print p
  sys.exit(0)
prepro = prepro_fact.create_processor_from_name(options.processor)

output = prepro.process_gcode(list(open(options.input_file)))
with open(options.output_file, 'w') as f:
  for o in output:
    f.write(o)

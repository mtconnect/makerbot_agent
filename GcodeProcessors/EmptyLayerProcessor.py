from __future__ import absolute_import

import re

from . import Processor
import makerbot_driver

class EmptyLayerProcessor(Processor):

    def __init__(self):
        super(EmptyLayerProcessor, self).__init__()
        self.is_bundleable = True
        self.layer_start = re.compile("^\((Slice|<layer>) [0-9.]+.*\)")
        self.MG_nominal_comment = re.compile("^\(Slowing to 0\% of nominal speeds\)")
        self.move_gcode = re.compile("^G1 .*")
        self.SF_layer_end = re.compile("^\(</layer>\)")
        self.empty_line = re.compile("^\\n")


    def process_gcode(self, gcode_in, outfile = None):
        if outfile != None:
            return self.process_gcode_file(gcode_in, outfile)
        elif(isinstance(gcode_in, list)):
            return self.process_gcode_list(gcode_in)


    def process_gcode_file(self, gcode_file_path, output_file_path,callback=None): 
    #process gcode from a file, and output to a file     
        self.code_index = 0
        self.gcodes = self.index_file(gcode_file_path)

        self.max_index = (len(self.gcodes)-1) 

        self.gcode_fp = open(gcode_file_path, 'r')
        self.output_fp = open(output_file_path, 'w')
        print(str(self.output_fp))

        while(self.code_index <= self.max_index):

            self.gcode_fp.seek(self.gcodes[self.code_index])
            current_code = self.gcode_fp.readline()
            self.match = re.match(self.layer_start, current_code)
            if self.match is not None:
                print self.match.group()
                if self.match.group(1) == '<layer>':
                    self.is_empty, new_code_index = self._layer_test_if_empty(slicer='SF')
                elif self.match.group(1) == 'Slice':
                    self.is_empty, new_code_index = self._layer_test_if_empty(slicer='MG')
                #layer_test_if_empty alters the seeked location so reseek current offset
                self.gcode_fp.seek(self.gcodes[self.code_index])
                if(self.is_empty ==  True):
                    self.code_index = new_code_index
                    continue #skip appending
                elif((self.is_empty == -1) and (new_code_index == 'MG')):
                #Hacky way to remove final empty slice for Miracle Grue 
                    self.code_index += 7

            if(self.code_index <= self.max_index):
                self.gcode_fp.seek(self.gcodes[self.code_index])
                current_code = self.gcode_fp.readline()
                self.output_fp.write(current_code)
                self.code_index += 1
            else:
                print ("CODE_INDEX GREATER THAN MAX_INDEX")
                break
        return True


    def process_gcode_list(self, gcodes, callback=None):
    #This processes gcode in the form of a list of gcodes, and the processed gcode is returned
        self.gcodes = gcodes  
        self.max_index = (len(self.gcodes)-1)      
        self.output = []
        self.code_index = 0

        while(self.code_index <= self.max_index):
            self.match = re.match(self.layer_start, self.gcodes[self.code_index])
            if self.match is not None:
                if self.match.group(1) == '<layer>':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(slicer='SF')
                elif self.match.group(1) == 'Slice':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(slicer='MG')
                if(self.is_empty ==  True):
                    self.code_index = self.new_code_index
                    continue #skip appending
                print(str(self.new_code_index))
                if((self.is_empty == -1) and (self.new_code_index == 'MG')):
                #Hacky way to remove final empty slice for Miracle Grue 
                    self.code_index += 7

            if(self.code_index <= self.max_index):
                self.output.append(self.gcodes[self.code_index])
                self.code_index += 1
            else:
                print ("CODE_INDEX GREATER THAN MAX_INDEX")
                break
        return self.output
                
      
    def _layer_test_if_empty(self, slicer):
        code_index = self.code_index+1
        moves_in_layer = 0
        comments_in_layer = 0

        self.gcode_fp.seek(self.gcodes[code_index])
        current_code = self.gcode_fp.readline()
        while(code_index <= self.max_index):
            #Checks for a specific comment or G1 commands
            if(slicer == 'MG'):
                if(re.match(self.empty_line, current_code)):
                    break
                if(re.match(self.move_gcode, current_code)):
                    moves_in_layer += 1
                if(re.match(self.MG_nominal_comment, current_code)):
                    comments_in_layer += 1
            elif(slicer == 'SF'):
                if(re.match(self.SF_layer_end, current_code)):
                    break
                if(re.match(self.move_gcode, current_code)):
                    moves_in_layer += 1
 
            code_index += 1
            self.gcode_fp.seek(self.gcodes[code_index])
            current_code = self.gcode_fp.readline()

        if(slicer == 'MG'):
            if((moves_in_layer <= 2) and (comments_in_layer >= 1)):
                return (True, code_index)
            else:
                return (False, None)
        elif(slicer == 'SF'):
            if(moves_in_layer <= 1):
                return (True, code_index+1) #avoids adding the </layer> tag
            else:
                return (False, None)


    def index_file(self, filename):

        line_indexes = []
        offset = 0
        with open(filename, 'r') as f:
            for line in f:
                line_indexes.append(offset)    
                offset += len(line)
        return line_indexes

        

from __future__ import absolute_import
import re

from . import Processor
import makerbot_driver


class FanProcessor(Processor):

    def __init__(self):
        self.expected_raft_tag = "(<raftLayerEnd> </raftLayerEnd>)"
        self.raft_on = re.compile("\(\<setting\> raft Add_Raft,_Elevate_Nozzle,_Orbit: True \</setting\>\)")
        self.raft_end = re.compile("\(\<raftLayerEnd\> \<\/raftLayerEnd\>\)")

        self.layer_end = re.compile("\(\</layer\>\)")
        self.fan_codes = re.compile("[^(;]*[mM]126|[^(;]*[mM]127")
        self.layer_count = 2 # Turn on fan at this layer AFTER The raft
        self.fan_on = "M126 T0 (Fan On)\n"
        self.fan_off = "M127 T0 (Fan Off)\n"

    def gather_stats(self, gcodes):
        """
        Iterate over all 
        
        @param list gcodes: List of gcodes to check
        @return bool: True if codes exist, false otherwise
        """
        vals = {
            'fan_codes_exist': False,
            'raft': False
        }
        for code in gcodes:
            if re.match(self.fan_codes, code):
                vals['fan_codes_exist']= True
            if re.match(self.raft_on, code):
                vals['raft'] = True
            if all(vals.values()):
                break
        return vals

    def get_raft_end_location(self, gcodes):
        """
        Separates the raft code from the rest of the GCodes. 

        @param list gcodes: List of gcodes to iterate over
        @return dict: Hash table containing "raft" gcodes and "print" gcodes
        """
        location = len(gcodes)
        for i in range(len(gcodes)):
            if re.match(self.raft_end, gcodes[i]):
                location = i+1 # +1 since this is the last code for the raft
                break
        return location 

    def get_layer_location(self, start, num_layers, codes):
        layer_loc = len(codes)
        layers_seen = 0
        if num_layers == 0:
            layer_loc = min(start, len(codes))
        else:
            for i in range(start, len(codes)):
                if re.match(self.layer_end, codes[i]):
                    layers_seen += 1 
                if layers_seen >= num_layers:
                    layer_loc = i + 1
                    break
        return layer_loc

    def process_gcode(self, gcodes, callback=None):
        stats = self.gather_stats(gcodes)
        if not stats['fan_codes_exist']:
            start_loc = 0
            if stats['raft']:
                start_loc = self.get_raft_end_location(gcodes)
            layer_loc = self.get_layer_location(start_loc, self.layer_count, gcodes)
            gcodes.insert(layer_loc, self.fan_on)
            gcodes.append(self.fan_off)
        return gcodes 

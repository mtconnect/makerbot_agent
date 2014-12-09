import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import mock

import tempfile
import threading
import warnings

import makerbot_driver


class TOMReading(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.Gcode.GcodeParser()
        self.p.state = makerbot_driver.Gcode.LegacyGcodeStates()
        self.p.state.values['build_name'] = 'test'
        self.p.state.profile = makerbot_driver.Profile('TOMStepstruderSingle')
        start_pos = self.p.state.profile.values['print_start_sequence']['start_position']
        start_position = {
            'START_X' : start_pos['start_x'],
            'START_Y' : start_pos['start_y'],
            'START_Z' : start_pos['start_z']
        }
        self.p.environment.update(start_position)
        self.s3g = makerbot_driver.s3g()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
            path = f.name
        condition = threading.Condition()
        self.s3g.writer = makerbot_driver.Writer.FileWriter(open(path, 'wb'), condition)
        self.p.s3g = self.s3g

    def tearDown(self):
        self.p = None
        self.s3g = None

    def test_single_head_miracle_grue(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'miracle_grue_single_extrusion_20_mm_box.gcode'
        )
        execute_file(the_file, self.p)


class SingleHeadReading(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.Gcode.GcodeParser()
        self.s = makerbot_driver.Gcode.GcodeStates()
        self.s.values['build_name'] = 'test'
        self.profile = makerbot_driver.Profile('ReplicatorSingle')
        start_pos = self.profile.values['print_start_sequence']['start_position']
        start_position = {
            'START_X' : start_pos['start_x'],
            'START_Y' : start_pos['start_y'],
            'START_Z' : start_pos['start_z']
        }
        self.p.environment.update(start_position)
        self.s.profile = self.profile
        self.p.state = self.s
        self.s3g = makerbot_driver.s3g()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
            pass
        input_path = input_file.name
        os.unlink(input_path)
        condition = threading.Condition()
        self.writer = makerbot_driver.Writer.FileWriter(open(input_path, 'wb'), condition)
        self.s3g.writer = self.writer
        self.p.s3g = self.s3g

    def tearDown(self):
        self.profile = None
        self.s = None
        self.writer = None
        self.s3g = None
        self.p = None

    def test_single_head_slicer(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'slic3r_single_extrusion_20mm_box.gcode'
        )
        the_file = process_file_with_pro(the_file, 'SlicerProcessor')
        execute_file(the_file, self.p)

    def test_single_head_skeinforge_single_20mm_box(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_single_extrusion_20mm_box.gcode'
        )
        the_file = process_file_with_pro(the_file, 'Skeinforge50Processor')
        the_file = process_file_with_pro(the_file, 'SetTemperatureProcessor')
        execute_file(the_file, self.p)

    def test_single_head_skeinforge_single_snake(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_single_extrusion_snake.gcode'
        )
        the_file = process_file_with_pro(the_file, 'Skeinforge50Processor')
        the_file = process_file_with_pro(the_file, 'SetTemperatureProcessor')
        execute_file(the_file, self.p)

    def test_single_head_miracle_grue(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'miracle_grue_single_extrusion_20_mm_box.gcode'
        )
        execute_file(the_file, self.p)


class DualHeadReading(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.Gcode.GcodeParser()
        self.s = makerbot_driver.Gcode.GcodeStates()
        self.s.values['build_name'] = 'test'
        self.profile = makerbot_driver.Profile('ReplicatorDual')
        start_pos = self.profile.values['print_start_sequence']['start_position']
        start_position = {
            'START_X' : start_pos['start_x'],
            'START_Y' : start_pos['start_y'],
            'START_Z' : start_pos['start_z']
        }
        self.p.environment.update(start_position)
        self.s.profile = self.profile
        self.p.state = self.s
        self.s3g = makerbot_driver.s3g()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
            pass
        input_path = input_file.name
        os.unlink(input_path)
        condition = threading.Condition()
        self.writer = makerbot_driver.Writer.FileWriter(open(input_path, 'wb'), condition)
        self.s3g.writer = self.writer
        self.p.s3g = self.s3g

    def tearDown(self):
        self.profile = None
        self.s = None
        self.writer = None
        self.s3g = None
        self.p = None

    def test_dual_head_skeinforge_hilbert_cube(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_dual_extrusion_hilbert_cube.gcode')
        the_file = process_file_with_pro(the_file, 'Skeinforge50Processor')
        the_file = process_file_with_pro(the_file, 'SetTemperatureProcessor')
        the_file = process_file_with_pro(
            the_file, 'CoordinateRemovalProcessor')
        execute_file(the_file, self.p)

    def test_single_head_skeinforge_single_20mm_box(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_single_extrusion_20mm_box.gcode'
        )
        the_file = process_file_with_pro(the_file, 'Skeinforge50Processor')
        the_file = process_file_with_pro(the_file, 'SetTemperatureProcessor')
        execute_file(the_file, self.p)

    def test_single_head_skeinforge_single_snake(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_single_extrusion_snake.gcode')
        the_file = process_file_with_pro(the_file, 'Skeinforge50Processor')
        the_file = process_file_with_pro(the_file, 'SetTemperatureProcessor')
        execute_file(the_file, self.p)

    def test_single_head_miracle_grue(self):
        the_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'miracle_grue_single_extrusion_20_mm_box.gcode',
        )
        execute_file(the_file, self.p)


def process_file_with_pro(the_file, pro):
    factory = makerbot_driver.GcodeProcessors.ProcessorFactory()
    pro = factory.create_processor_from_name(pro)
    f = open(the_file)
    lines = list(f)
    output = pro.process_gcode(lines)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gcode') as f:
        processed_file_path = f.name
        for line in output:
            f.write(line)
    return processed_file_path


def execute_file(the_file, parser):
    ga = makerbot_driver.GcodeAssembler(parser.state.profile)
    if "Thing-O-Matic" in parser.state.profile.values['machinenames']:
        start, end, variables = ga.assemble_recipe(
            begin_print='tom_begin',
            homing='tom_homing',
            start_position='tom_start_position',
            end_start_sequence='tom_end_start_sequence',
            end_position='tom_end_position',
            end_print='tom_end',
        )
    else:
        start, end, variables = ga.assemble_recipe()
    start_gcode = ga.assemble_start_sequence(start)
    end_gcode = ga.assemble_end_sequence(end)
    parser.environment.update(variables)
    for line in start_gcode:
        parser.execute_line(line)
    with open(the_file) as f:
        for line in f:
            parser.execute_line(line)
    for line in end_gcode:
        parser.execute_line(line)

if __name__ == '__main__':
    unittest.main()

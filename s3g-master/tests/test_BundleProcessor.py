import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import threading
import time
import mock
import makerbot_driver


class TestBundleProcessorCallbackAssignment(unittest.TestCase):

    def setUp(self):
        self.bp = makerbot_driver.GcodeProcessors.BundleProcessor()
        self.bp._super_process_gcode = mock.Mock(return_value=[])
        self.bp.progress_processor.process_gcode = mock.Mock()

    def tearDown(self):
        self.bp = None

    def test_not_do_progress_no_callback(self):
        self.bp.do_progress = False
        callback = None
        gcodes = []
        self.bp.process_gcode(gcodes, callback)
        self.bp._super_process_gcode.assert_called_once_with([], None)
        self.assertEqual(
            len(self.bp.progress_processor.process_gcode.mock_calls), 0)

    def test_not_do_progress_callback(self):
        self.bp.do_progress = False

        def callback(percent):
            pass
        gcodes = []
        self.bp.process_gcode(gcodes, callback)
        self.bp._super_process_gcode.assert_called_once_with([], callback)
        self.assertEqual(
            len(self.bp.progress_processor.process_gcode.mock_calls), 0)

    def test_do_progress_no_callback(self):
        self.bp.do_progress = True
        callback = None
        gcodes = []
        self.bp.process_gcode(gcodes, callback)
        self.bp._super_process_gcode.assert_called_once_with([], callback)
        self.bp.progress_processor.process_gcode.assert_called_once_with(
            [], None)

    def test_do_progress_callback(self):
        self.bp.do_progress = True

        def callback(percent):
            pass
        gcodes = []
        self.bp.process_gcode(gcodes, callback)
        self.bp._super_process_gcode.assert_called_once_with(
            [], self.bp.new_callback)
        self.bp.progress_processor.process_gcode.assert_called_once_with(
            [], self.bp.progress_callback)


class TestBundleProcessorCallbacks(unittest.TestCase):

    def setUp(self):
        self.bp = makerbot_driver.GcodeProcessors.BundleProcessor()
        self.the_percent = 0
        self.percents = []
        self.done_process = False

    def tearDown(self):
        self.bp = None
        self.the_percent = None
        self.percents = None
        self.done_process = None

    def get_percent(self):
        time.sleep(1)
        runner = 0
        while not self.done_process:
            if runner % 1000 == 0:
                self.percents.append(self.the_percent)
            if runner % 10000000 == 0:
                print "."
            runner += 1

    def test_callbacks_with_do_progress(self):
        def test_callback(p):
            self.the_percent = p
        t = threading.Thread(target=self.get_percent)
        path_to_gcode = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
        with open(path_to_gcode) as f:
            lines = list(f)
        self.bp.processors = [
            makerbot_driver.GcodeProcessors.RpmProcessor(),
            makerbot_driver.GcodeProcessors.SingletonTProcessor(),
            makerbot_driver.GcodeProcessors.SetTemperatureProcessor(),
            makerbot_driver.GcodeProcessors.GetTemperatureProcessor(),
        ]
        t.start()
        self.bp.process_gcode(lines, callback=test_callback)
        self.done_process = True
        t.join()
        discrete_percents = set(self.percents)
        cur_percent = -1
        for percent in discrete_percents:
            self.assertTrue(percent > cur_percent)
            cur_percent = percent

    def test_callbacks_dont_do_progress(self):
        def test_callback(p):
            self.the_percent = p
        t = threading.Thread(target=self.get_percent)
        path_to_gcode = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
        with open(path_to_gcode) as f:
            lines = list(f)
        self.bp.processors = [
            makerbot_driver.GcodeProcessors.RpmProcessor(),
            makerbot_driver.GcodeProcessors.SingletonTProcessor(),
            makerbot_driver.GcodeProcessors.SetTemperatureProcessor(),
            makerbot_driver.GcodeProcessors.GetTemperatureProcessor(),
        ]
        t.start()
        self.bp.do_progress = False
        self.bp.process_gcode(lines, callback=test_callback)
        self.done_process = True
        t.join()
        discrete_percents = set(self.percents)
        cur_percent = -1
        for percent in discrete_percents:
            self.assertTrue(percent > cur_percent)
            cur_percent = percent

    def set_external_stop(self):
        time.sleep(.5)
        self.bp.set_external_stop()

    def test_external_stop(self):
        t = threading.Thread(target=self.set_external_stop)
        path_to_gcode = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
        with open(path_to_gcode) as f:
            lines = list(f)
        self.bp.processors = [
            makerbot_driver.GcodeProcessors.RpmProcessor(),
            makerbot_driver.GcodeProcessors.SingletonTProcessor(),
            makerbot_driver.GcodeProcessors.SetTemperatureProcessor(),
            makerbot_driver.GcodeProcessors.GetTemperatureProcessor(),
        ]
        t.start()
        try:
            self.bp.process_gcode(lines)
            self.assertTrue(False)
        except makerbot_driver.ExternalStopError:
            pass
        t.join()

if __name__ == "__main__":
    unittest.main()

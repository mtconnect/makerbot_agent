import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import mock

import makerbot_driver


class TestMachineDetector(unittest.TestCase):

    def setUp(self):
        self.md = makerbot_driver.MachineDetector()

    def tearDown(self):
        self.md = None

    def test_get_tty_and_cu_not_tty_or_cu(self):
        cases = [
            'COM04',
            'ACM0',
            '/dev/lolnotttyorcu.usbmodemfa131'
        ]
        for case in cases:
            expected_ports = set([case])
            got_ports = self.md.get_tty_and_cu(case)
            self.assertEqual(expected_ports, got_ports)

    def test_get_tty_and_cu_is_cu(self):
        the_port = '/dev/cu.acm0'
        expected_ports = set([the_port, the_port.replace('cu', 'tty')])
        got_ports = self.md.get_tty_and_cu(the_port)
        self.assertEqual(expected_ports, got_ports)

    def test_get_tty_and_cu_is_tty(self):
        the_port = '/dev/tty.acm0'
        expected_ports = set([the_port, the_port.replace('tty', 'cu')])
        got_ports = self.md.get_tty_and_cu(the_port)
        self.assertEqual(expected_ports, got_ports)

    def test_get_vidpid_by_machine(self):
        expectedRep2 = (0x23C1, 0xB015)
        expectedRep = (0x23C1, 0xD314)
        expectedMighty = (0x23C1, 0xB404)
        rep = makerbot_driver.get_vid_pid_by_name('The Replicator')
        rep2 = makerbot_driver.get_vid_pid_by_name('The Replicator 2')
        mighty = makerbot_driver.get_vid_pid_by_name('MightyBoard')
        self.assertEqual(expectedRep2, rep2)
        self.assertEqual(expectedRep, rep)
        self.assertEqual(expectedMighty, mighty)

    def test_get_machine_name_from_vid_pid(self):
        cases = [
            [0x23C1, 0xB016, "The Replicator 2"],
            [0x23C1, 0xB015, "The Replicator 2"],
            [0x23C1, 0xD314, "The Replicator"],
            [0x23C1, 0xB404, "MightyBoard"],
            [0x0403, 0x6001, "TOM FTDI"],
            [0x2341, 0x0010, "TOM 8U2"],
            [0x0000, 0xFFFF, None],
        ]
        for case in cases:
            self.assertEqual(case[2], self.md.get_machine_name_from_vid_pid(
                case[0], case[1]))

#  def test_identify_replicator_one_toolhead(self):
#    s3g_mock = mock.Mock()
#    s3g_mock.get_toolhead_count.return_value = 1
#    expected_profile = makerbot_driver.Profile('ReplicatorSingle')
#    got_profile = self.md.identify_replicator(s3g_mock)
#    self.assertEqual(expected_profile.values, got_profile.values)
#  def test_identify_replicator_two_toolheads(self):
#    s3g_mock = mock.Mock()
#    s3g_mock.get_toolhead_count.return_value = 2
#    expected_profile = makerbot_driver.Profile('ReplicatorDual')
#    got_profile = self.md.identify_replicator(s3g_mock)
#    self.assertEqual(expected_profile.values, got_profile.values)
#  def test_identify_machine_is_replicator(self):
#    iSerial = '1234567890'
#    blob = {
#        'port'  : '/dev/dummy_port',
#        'iSerial' : iSerial,
#        }
#    s3g_mock = mock.Mock()
#    s3g_mock.get_toolhead_count.return_value = 1
#    s3g_mock.get_version.return_value = 500
#    self.md.create_s3g = mock.Mock()
#    self.md.create_s3g.return_value = s3g_mock
#    expected_profile = makerbot_driver.Profile('ReplicatorSingle')
#    expected_profile.values['uuid'] = iSerial
#    got_profile, got_s3g = self.md.identify_machine(blob)
#    self.assertEqual(s3g_mock, got_s3g)
#    self.assertEqual(expected_profile.values, got_profile.values)
#  def test_identify_machine_is_not_replicator(self):
#    blob = {
#        'port'  : '/dev/dummy_port',
#        }
#    s3g_mock = mock.Mock()
#    s3g_mock.get_version.return_value = 300
#    self.md.create_s3g = mock.Mock()
#    self.md.create_s3g.return_value = s3g_mock
#    expected_profile = None
#    got_profile, got_s3g = self.md.identify_machine(blob)
#    self.assertEqual(expected_profile, got_profile)
#    self.assertEqual(s3g_mock, got_s3g)


class TestMachineDetectorScanTests(unittest.TestCase):
    def setUp(self):
        self.md = makerbot_driver.MachineDetector()
        self.list_ports_mock = mock.Mock()
        self.md.list_ports_by_vid_pid = self.list_ports_mock

    def tearDown(self):
        self.list_ports_mock = None
        self.md = None

    def test_vid_pid_from_portname_windows_not_seen(self):
        portname = 'COM99'
        self.md.get_available_machines = mock.Mock(return_value={})
        expected_pair = (None, None)
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_windows_has_seen(self):
        portname = 'COM99'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname: {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_unix_not_seen(self):
        portname = '/dev/ttyACM0'
        self.md.get_available_machines = mock.Mock(return_value={})
        expected_pair = (None, None)
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_unix_tty_has_seen(self):
        portname = '/dev/ttyACM0'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname: {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_mac_tty_has_seen_cu(self):
        portname = '/dev/tty.usbmodemfa131'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname.replace('tty', 'cu'): {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_mac_tty_has_seen_tty(self):
        portname = '/dev/tty.usbmodemfa131'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname: {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_mac_cu_has_seen_tty(self):
        portname = '/dev/cu.usbmodemfa131'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname.replace('cu', 'tty'): {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_vid_pid_from_portname_mac_cu_has_seen_cu(self):
        portname = '/dev/cu.usbmodemfa131'
        expected_pair = (0x0000, 0xFFFF)
        self.md.get_available_machines = mock.Mock(return_value={
            portname: {
                'VID': expected_pair[0],
                'PID': expected_pair[1],
            }
        })
        got_pair = self.md.vid_pid_from_portname(portname)
        self.assertEqual(expected_pair, got_pair)

    def test_scan_no_new_bots(self):
        self.list_ports_mock.return_value = []
        self.md.scan()
        expected_recently_seen = {}
        expected_just_seen = {}
        self.assertEqual(
            self.md.machines_recently_seen, expected_recently_seen)
        self.assertEqual(self.md.machines_just_seen, expected_just_seen)

    def test_scan_new_bots(self):
        blob = {
            'port': '/dev/dummy',
            'vid': 0x23C1,
            'pid': 0xD314,
            'iSerail': '1234567890',
        }
        self.list_ports_mock.return_value = [blob]
        self.md.scan()
        expected_recent = {blob['port']: blob}
        expected_just = expected_recent
        self.assertEqual(expected_recent, self.md.machines_recently_seen)
        self.assertEqual(expected_just, self.md.machines_just_seen)

    def test_scan_new_bots_additional_bot(self):
        blob1 = {
            'port': '/dev/dummy1',
            'vid': 0x23C1,
            'pid': 0xD314,
            'iSerail': '1234567890',
        }
        blob2 = {
            'port': '/dev/dummy2',
            'vid': 0x23C1,
            'pid': 0xD314,
            'iSerail': '0987654321',
        }

        #mock finding 1 bot
        blobs = [blob1]
        self.list_ports_mock.return_value = blobs
        self.md.list_ports_by_vid_pid = self.list_ports_mock
        expected_just = {blob1['port']: blob1}
        expected_recent = {blob1['port']: blob1}

        self.md.scan()
        self.assertEqual(self.md.machines_just_seen, expected_just)
        self.assertEqual(self.md.machines_recently_seen, expected_recent)

        #mock up finding a 2nd bot
        blobs = [blob2, blob1]
        expected_just = {blob1['port']: blob1, blob2['port']: blob2}
        expected_recent = {blob1['port']: blob1, blob2['port']: blob2}
        self.list_ports_mock.return_value = blobs

        self.md.scan()
        self.assertEqual(self.md.machines_just_seen, expected_just)
        self.assertEqual(self.md.machines_recently_seen, expected_recent)

    def test_scan_new_bots_bot_removed(self):
        blob1 = {
            'port': '/dev/dummy1',
            'vid': 0x23C1,
            'pid': 0xD314,
            'iSerail': '1234567890',
        }
        blob2 = {
            'port': '/dev/dummy2',
            'vid': 0x23C1,
            'pid': 0xD314,
            'iSerail': '0987654321',
        }
        #mock up finding  2 bot
        blobs = [blob2, blob1]
        expected_just = {blob1['port']: blob1, blob2['port']: blob2}
        expected_recent = {blob1['port']: blob1, blob2['port']: blob2}
        self.list_ports_mock.return_value = blobs

        self.md.scan()
        self.assertEqual(self.md.machines_just_seen, expected_just)
        self.assertEqual(self.md.machines_recently_seen, expected_recent)

        #mock up finding 1  bot
        blobs = [blob1]
        expected_just = {blob1['port']: blob1}
        expected_recent = {blob1['port']: blob1, blob2['port']: blob2}
        self.list_ports_mock.return_value = blobs

        self.md.scan()
        self.assertEqual(self.md.machines_just_seen, expected_just)
        self.assertEqual(self.md.machines_recently_seen, expected_recent)


class TestMachineDetectorMockedPySerial(unittest.TestCase):

    def setUp(self):
        self.md = makerbot_driver.MachineDetector()
        self.list_ports_mock = mock.Mock()
        self.md.list_ports_by_vid_pid = self.list_ports_mock
        self.s3g_mock = mock.Mock()
        self.md.create_s3g = mock.Mock()
        self.md.create_s3g.return_value = self.s3g_mock

    def tearDown(self):
        self.list_ports_mock = None
        self.md = None

#  def test_get_available_machines_no_just_seen_machines(self):
#    expected_machines = {}
#    return_ports = []
#    self.list_ports_mock.return_value = return_ports
#    got_machines = self.md.get_available_machines()
#    self.assertEqual(expected_machines, got_machines)

#  def test_get_available_machines_one_replicator_seen(self):
#    port = '/dev/dummy'
#    iSerial = '1234567890'
#    vid = 0x23C1
#    pid = 0xD314
#    version = 500
#    tool_count = 1
#    blob = {
#        'port'  : port,
#        'iSerial' : iSerial,
#        'vid' : vid,
#        'pid' : pid,
#        }
#    self.list_ports_mock.return_value = [blob]
#    self.s3g_mock.get_version.return_value = version
#    self.s3g_mock.get_toolhead_count.return_value = tool_count
#    expected_profile = makerbot_driver.Profile('ReplicatorSingle')
#    expected_s3g = self.s3g_mock
#    expected_dict = {port:(expected_profile, expected_s3g)}
#    got_dict = self.md.get_available_machines()
#    self.assertEqual(got_dict.keys(), expected_dict.keys())
#    self.assertEqual(got_dict.values(), expected_dict.values())


if __name__ == '__main__':
    unittest.main()

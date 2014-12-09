import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import json
import mock
import subprocess
import tempfile
import platform

import makerbot_driver


class TestGetProducts(unittest.TestCase):
    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url, dest_path=dest)

    def tearDown(self):
        self.uploader = None

    def test_pathjoin(self):
        base, f = './base', 'x.txt'
        path = os.path.normpath(os.path.join(base, f))
        self.assertEquals(self.uploader.pathjoin(base, f), path)
        base, f = 'http://base', 'x.txt'
        self.assertEquals(self.uploader.pathjoin(base, f), "http://base/x.txt")

    def test_pull_products(self):
        expected_products_url = self.uploader.pathjoin(
            self.uploader.source_url, self.uploader.product_filename)
        wget_mock = mock.Mock()
        wget_mock.return_value = expected_products_url
        self.uploader.wget = wget_mock
        get_machine_json_files_mock = mock.Mock()
        self.uploader.get_machine_json_files = get_machine_json_files_mock
        self.uploader._pull_products()
        wget_mock.assert_called_once_with(expected_products_url)
        get_machine_json_files_mock.assert_called_once_with()


class TestWget(unittest.TestCase):
    def setUp(self):
        self.source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=self.source_url,
            dest_path=dest,
        )

    def tearDown(self):
        self.uploader = None

    def test_wget_local_file(self):
        string = '1234567890asdf'

        class file_like_object(object):
            def __init__(self):
                pass

            def read(self):
                return string
        filename = 'Example.json'
        url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
            filename,
        )
        self.assertTrue(os.path.isfile(os.path.join(
            self.uploader.dest_path, filename)))

    def test_wget_internet_file(self):
        url = 'http://firmware.makerbot.com/foobar.json'
        string = '1234567890asdf'

        class file_like_object(object):
            """
            A file-like-object in place of the one returned by
            urlopen
            """
            def __init__(self):
                pass

            def read(self):
                return string
        #We mock urlopen so we dont actually pull something down from the internets
        #Our return value is a mocked file-like object (see above)
        urlopen_mock = mock.Mock()
        self.uploader.urlopen = urlopen_mock
        urlopen_mock.return_value = file_like_object()
        self.uploader.wget(url)
        #This is where the new tempfile should be
        temp_file = os.path.join(
            self.uploader.dest_path,
            url.split('/')[-1],
        )
        #Read the tempfile, and see if its correct
        with open(temp_file) as f:
            self.assertEqual(string, f.read())


class TestGetMachineJsonFiles(unittest.TestCase):
    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files', )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url,
            dest_path=dest,
        )

    def tearDown(self):
        self.uploader = None

    def test_get_machine_json_files_no_products(self):
        uploader = makerbot_driver.Firmware.Uploader(autoUpdate=False)
        self.assertRaises(AttributeError, uploader.get_machine_json_files)

    def test_get_machine_json_files_products_pulled_and_loaded(self):
        #Mock wget so we dont copy things fromt he internets
        self.wget_mock = mock.Mock()
        self.uploader.wget = self.wget_mock
        calls = self.wget_mock.mock_calls
        machines = self.uploader.products['ExtrusionPrintersV2']
        for machine, call in zip(machines, calls):
            filename = self.uploader.products['ExtrusionPrintersV2'][machine]
            firmware_url = urlparse.urljoin(self.uploader.source_url, filename)
            self.assertEqual(firmware_url, call[1][0])


class TestGetFirmwareVersions(unittest.TestCase):

    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files', )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url,
            dest_path=dest,
        )

    def tearDown(self):
        self.uploader = None

    def test_list_firmware_versions_bad_machine_name(self):
        machine = 'I HOPE THIS ISNT A MACHINE NAME'
        pid = 'pid_example'
        self.assertRaises(
            KeyError,
            self.uploader.list_firmware_versions,
            machine,
            pid
        )

    def test_list_firmware_versions_bad_pid_value(self):
        machine = 'Example'
        pid = 'pid_bad_example'
        self.assertRaises(
            KeyError,
            self.uploader.list_firmware_versions,
            machine,
            pid
        )

    def test_list_firmware_versions_good_machine_name(self):
        machine = 'Example'
        pid = 'pid_example'
        with open(os.path.join(
            self.uploader.source_url,
            machine + '.json',
        )) as f:
            vals = json.load(f)
        expected_versions = []
        #The version is the key, then the descriptor is the 1st element
        #in the key's value
        for version in vals['PID'][pid]['versions']:
            descriptor = vals['PID'][pid]['versions'][version][1]
            expected_versions.append([version, descriptor])
        got_versions = self.uploader.list_firmware_versions(machine, pid)
        self.assertEqual(expected_versions, got_versions)


class TestGetFirmwareValues(unittest.TestCase):
    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url,
            dest_path=dest,
        )

    def tearDown(self):
        self.uploader = None

    def test_get_firmware_values_bad_machine(self):
        machine = "i really hope you dont have a file with this exact name"
        with self.assertRaises(KeyError) as err:
            self.uploader.get_firmware_values(machine)

    def test_get_firmware_values_good_machine_name(self):
        machine = "Example"
        with open(os.path.join(
            self.uploader.source_url,
            machine + '.json',
        )) as f:
            expected_values = json.load(f)
        self.assertEqual(
            expected_values, self.uploader.get_firmware_values(machine))


class TestListVersions(unittest.TestCase):
    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url,
            dest_path=dest,
            autoUpdate=False,
        )

    def test_list_machines_no_products(self):
        self.assertRaises(AttributeError, self.uploader.list_machines)

    def test_list_machines(self):
        self.uploader.update()
        with open(os.path.join(
            self.uploader.source_url,
            'products.json',
        )) as f:
            values = json.load(f)
        expected_machines = []
        for machine in values['ExtrusionPrintersV2']:
            expected_machines.append(machine)
        self.assertEqual(expected_machines, self.uploader.list_machines())


class TestUploader(unittest.TestCase):
    def setUp(self):
        self.uploader = makerbot_driver.Firmware.Uploader(autoUpdate=False)

    def tearDown(self):
        self.uploader = None

    """
    This test assumes firmware version 6.0, 6.1 and 6.2 are in makerbot_driver/EEPROM
    """
    def test_compatible_firmware_version(self):
        cases = [
            ['6.0', '0x00'],
            ['6.1', '0x00'],
            ['6.2', '0x00'],
        ]
        for case in cases:
            self.assertTrue(self.uploader.compatible_firmware(case[0], case[1])) 

    def test_update(self):
        pull_products_mock = mock.Mock()
        self.uploader._pull_products = pull_products_mock
        self.uploader.update()
        pull_products_mock.assert_called_once_with()

    def test_load_json_values_good_file(self):
        path_to_json = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
            'products.json'
        )
        with open(path_to_json) as f:
            expected_vals = json.load(f)
        got_vals = self.uploader.load_json_values(path_to_json)
        self.assertEqual(expected_vals, got_vals)

    def test_load_json_values_bad_file(self):
        filename = 'I HOPE THIS ISNT A FILENAME'
        self.assertRaises(IOError, self.uploader.load_json_values, filename)


class TestParseAvrdudeCommand(unittest.TestCase):
    def setUp(self):
        source_url = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'test_files',
        )
        dest = tempfile.mkdtemp()
        self.uploader = makerbot_driver.Firmware.Uploader(
            source_url=source_url,
            dest_path=dest,
        )
        toggle_machine_mock = mock.Mock()
        self.uploader.toggle_machine = toggle_machine_mock

    def tearDown(self):
        self.uploader = None

    def test_parse_avrdude_command_no_products(self):
        uploader = makerbot_driver.Firmware.Uploader(autoUpdate=False)
        port = '/dev/tty.usbmodemfa121'
        machine = "Example"
        pid = 'pid_example'
        version = '0.1'
        self.assertRaises(AttributeError, uploader.parse_avrdude_command,
                          port, machine, pid, version)

    def test_parse_avrdude_command_cant_find_machine(self):
        port = '/dev/tty.usbmodemfa121'
        machine = "i really hope you dont have a file with this exact name"
        pid = 'pid_example'
        version = '5.2'
        self.assertRaises(KeyError, self.uploader.parse_avrdude_command,
                          port, machine, pid, version)

    def test_parse_avrdude_command_cant_find_pid(self):
        port = '/dev/tty.usbmodemfa121'
        machine = "Example"
        pid = 'pid_bad_example'
        version = '5.2'
        self.assertRaises(KeyError, self.uploader.parse_avrdude_command,
                          port, machine, pid, version)

    def test_parse_avrdude_command_cant_find_version(self):
        port = '/dev/tty.usbmodemfa121'
        machine = 'Example'
        pid = 'pid_example'
        version = 'x.x'
        self.assertRaises(makerbot_driver.Firmware.UnknownVersionError,
                          self.uploader.download_firmware, machine, pid, version)

    def test_parse_avrdude_command_local(self):
        machine = 'Example'
        pid = 'pid_example'
        wget_mock = mock.Mock()
        self.uploader.wget = wget_mock
        with open(os.path.join(self.uploader.source_url, machine + '.json')) as f:
            example_profile = json.load(f)
        example_values = example_profile['PID'][pid]
        port = '/dev/tty.usbmodemfa121'
        version = '0.1'
        hex_url = example_values['versions'][version][0]
        hex_path = os.path.join(
            self.uploader.dest_path,
            hex_url,
        )
        #Mock up the actual path to the hex_file
        wget_mock.return_value = hex_path
        avrdude = "avrdude"
        if platform.system() == "Windows":
            avrdude += ".exe"
        avrdude_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'makerbot_driver',
            'Firmware',
            avrdude
        )
        avrdude_conf_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'makerbot_driver',
            'Firmware',
            'avrdude.conf',
        )
        if platform.system() == "Windows":
            expected_call = "%s -C%s -p%s -b%i -c%s -P\\\\.\\/dev/tty.usbmodemfa121 -Uflash:w:%s:i" % (avrdude_path, avrdude_conf_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
        else:
            expected_call = "%s -C%s -p%s -b%i -c%s -P/dev/tty.usbmodemfa121 -Uflash:w:%s:i" % (avrdude_path, avrdude_conf_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
        expected_call = expected_call.split(' ')
        got_call = self.uploader.parse_avrdude_command(port, machine, pid, version)
        #expected_call = expected_call.split(' ')
        expected_avrdude = expected_call[0]
        self.assertEqual(
            os.path.abspath(expected_avrdude), os.path.abspath(avrdude_path))
        expected_conf = expected_call[1]
        got_conf = got_call[1]
        expected_conf = expected_conf.replace('-C', '')
        got_conf = got_conf.replace('-C', '')
        self.assertEqual(
            os.path.abspath(expected_conf), os.path.abspath(got_conf))
        for i in range(2, 5):
            self.assertEqual(expected_call[i], got_call[i])
        #DO something really hacky, since windows paths have colons in them
        #and splitting at each colon will result in the test failing on windows
        #DUMB
        expected_op = expected_call[-1]
        expected_op_parts = []
        expected_op_parts.extend(expected_op[:9].split(':'))
        expected_op_parts.append(expected_op[10:-2])
        expected_op_parts.append(expected_op[-1])
        #Get the path relative from here
        expected_op_parts[2] = os.path.relpath(expected_op_parts[2])
        got_op = got_call[-1]
        got_op_parts = []
        got_op_parts.extend(expected_op[:9].split(':'))
        got_op_parts.append(expected_op[10:-2])
        got_op_parts.append(expected_op[-1])
        #Get the path relative from here
        got_op_parts[2] = os.path.relpath(expected_op_parts[2])
        for i in range(len(expected_op_parts)):
            self.assertEqual(expected_op_parts[i], got_op_parts[i])

    def test_update_firmware(self):
        machine = 'Example'
        pid = 'pid_example'
        wget_mock = mock.Mock()
        self.uploader.wget = wget_mock
        with open(os.path.join(self.uploader.source_url, machine + '.json')) as f:
            example_profile = json.load(f)
        example_values = example_profile['PID'][pid]
        port = '/dev/tty.usbmodemfa121'
        version = '0.1'
        hex_url = example_values['versions'][version][0]
        hex_path = os.path.join(
            self.uploader.dest_path,
            hex_url,
        )
        #Mock up the actual path to the hex_file
        wget_mock.return_value = hex_path

        check_output_mock = mock.Mock()
        self.uploader.run_subprocess = check_output_mock
        expected_call = self.uploader.parse_avrdude_command(
            port, machine, pid, version)
        self.uploader.upload_firmware(port, machine, pid, version)
        check_output_mock.assert_called_once_with(
            expected_call, stderr=subprocess.STDOUT)
        self.uploader.toggle_machine.assert_called_once_with(port)

    def test_parse_avrdude_command_global(self):
        machine = 'Example'
        pid = 'pid_example'
        wget_mock = mock.Mock()
        self.uploader.wget = wget_mock
        with open(os.path.join(self.uploader.source_url, machine + '.json')) as f:
            example_profile = json.load(f)
        example_values = example_profile['PID'][pid]
        port = '/dev/tty.usbmodemfa121'
        version = '0.1'
        hex_url = example_values['versions'][version][0]
        hex_path = os.path.join(
            self.uploader.dest_path,
            hex_url,
        )
        #Mock up the actual path to the hex_file
        wget_mock.return_value = hex_path
        avrdude_path = 'avrdude'
        avrdude_conf_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'makerbot_driver',
            'Firmware',
            'avrdude.conf',
        )
        if platform.system() == "Windows":
            expected_call = "%s -C%s -p%s -b%i -c%s -P\\\\.\\/dev/tty.usbmodemfa121 -Uflash:w:%s:i" % (avrdude_path, avrdude_conf_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
        else:
            expected_call = "%s -C%s -p%s -b%i -c%s -P/dev/tty.usbmodemfa121 -Uflash:w:%s:i" % (avrdude_path, avrdude_conf_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
        expected_call = expected_call.split(' ')
        got_call = self.uploader.parse_avrdude_command(
            port, machine, pid, version, local_avr=False)
        #expected_call = expected_call.split(' ')
        expected_avrdude = expected_call[0]
        self.assertEqual(expected_avrdude, avrdude_path)
        expected_conf = expected_call[1]
        got_conf = got_call[1]
        expected_conf = expected_conf.replace('-C', '')
        got_conf = got_conf.replace('-C', '')
        self.assertEqual(
            os.path.abspath(expected_conf), os.path.abspath(got_conf))
        for i in range(2, 5):
            self.assertEqual(expected_call[i], got_call[i])
        #DO something really hacky, since windows paths have colons in them
        #and splitting at each colon will result in the test failing on windows
        #DUMB
        expected_op = expected_call[-1]
        expected_op_parts = []
        expected_op_parts.extend(expected_op[:9].split(':'))
        expected_op_parts.append(expected_op[10:-2])
        expected_op_parts.append(expected_op[-1])
        #Get the path relative from here
        expected_op_parts[2] = os.path.relpath(expected_op_parts[2])
        got_op = got_call[-1]
        got_op_parts = []
        got_op_parts.extend(expected_op[:9].split(':'))
        got_op_parts.append(expected_op[10:-2])
        got_op_parts.append(expected_op[-1])
        #Get the path relative from here
        got_op_parts[2] = os.path.relpath(expected_op_parts[2])
        for i in range(len(expected_op_parts)):
            self.assertEqual(expected_op_parts[i], got_op_parts[i])

if __name__ == "__main__":
    unittest.main()

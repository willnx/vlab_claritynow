# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_claritynow_api.lib.worker import vmware


class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_show_claritynow(self, fake_vCenter, fake_consume_task, fake_get_info):
        """``claritynow`` returns a dictionary when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'ClarityNow'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'worked': True, 'note': 'ClarityNow=1.0.0'}

        output = vmware.show_claritynow(username='alice')
        expected = {'ClarityNow': {'note': 'ClarityNow=1.0.0', 'worked': True}}

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_claritynow(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_claritynow`` returns None when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'ClarityNowBox'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'note' : 'ClarityNow=1.0.0'}

        output = vmware.delete_claritynow(username='bob', machine_name='ClarityNowBox')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_claritynow_value_error(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_claritynow`` raises ValueError when unable to find requested vm for deletion"""
        fake_vm = MagicMock()
        fake_vm.name = 'win10'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'note' : 'ClarityNow=1.0.0'}

        with self.assertRaises(ValueError):
            vmware.delete_claritynow(username='bob', machine_name='myOtherClarityNowBox')

    @patch.object(vmware, '_setup_vm')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_create_claritynow(self, fake_vCenter, fake_consume_task, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_setup_vm):
        """``create_claritynow`` returns a dictionary upon success"""
        fake_get_info.return_value = {'worked': True}
        fake_Ova.return_value.networks = ['someLAN']
        fake_vCenter.return_value.__enter__.return_value.networks = {'someLAN' : vmware.vim.Network(moId='1')}

        output = vmware.create_claritynow(username='alice',
                                       machine_name='ClarityNowBox',
                                       image='1.0.0',
                                       network='someLAN')
        expected = {'worked': True}

        self.assertEqual(output, expected)

    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_create_claritynow_invalid_network(self, fake_vCenter, fake_consume_task, fake_deploy_from_ova, fake_get_info, fake_Ova):
        """``create_claritynow`` raises ValueError if supplied with a non-existing network"""
        fake_get_info.return_value = {'worked': True}
        fake_Ova.return_value.networks = ['someLAN']
        fake_vCenter.return_value.__enter__.return_value.networks = {'someLAN' : vmware.vim.Network(moId='1')}

        with self.assertRaises(ValueError):
            vmware.create_claritynow(username='alice',
                                  machine_name='ClarityNowBox',
                                  image='1.0.0',
                                  network='someOtherLAN')

    @patch.object(vmware.os, 'listdir')
    def test_list_images(self, fake_listdir):
        """``list_images`` - Returns a list of available ClarityNow versions that can be deployed"""
        fake_listdir.return_value = ['2.11.0']

        output = vmware.list_images()
        expected = ['2.11.0']

        # set() avoids ordering issue in test
        self.assertEqual(set(output), set(expected))

    def test_convert_name(self):
        """``convert_name`` - defaults to converting to the OVA file name"""
        output = vmware.convert_name(name='2.11.0')
        expected = 'ClarityNow-2.11.0.ova'

        self.assertEqual(output, expected)

    def test_convert_name_to_version(self):
        """``convert_name`` - can take a OVA file name, and extract the version from it"""
        output = vmware.convert_name('', to_version=True)
        expected = ''

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'run_command')
    def test_setup_vm(self, fake_run_command):
        """``_setup_vm`` returns None when everything works as expected"""
        fake_vcenter = MagicMock()
        fake_vm = MagicMock()
        fake_run_command.return_value.exitCode = None

        output = vmware._setup_vm(fake_vcenter, fake_vm)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'run_command')
    def test_setup_vm_cmd1_failure(self, fake_run_command):
        """``_setup_vm`` Raises RuntimeError if the 1st command fails"""
        fake_vcenter = MagicMock()
        fake_vm = MagicMock()
        fake_run_command.side_effect = [RuntimeError("testing"), RuntimeError("testing")]

        with self.assertRaises(RuntimeError):
            vmware._setup_vm(fake_vcenter, fake_vm)

    @patch.object(vmware.virtual_machine, 'run_command')
    def test_setup_vm_cmd2_failure(self, fake_run_command):
        """``_setup_vm`` Raises RuntimeError if the 2nd command fails"""
        fake_vcenter = MagicMock()
        fake_vm = MagicMock()
        fake_result1 = MagicMock()
        fake_result1.exitCode = None
        fake_result2 = RuntimeError('testing')
        fake_run_command.side_effect = [fake_result1, fake_result2]

        with self.assertRaises(RuntimeError):
            vmware._setup_vm(fake_vcenter, fake_vm)


if __name__ == '__main__':
    unittest.main()

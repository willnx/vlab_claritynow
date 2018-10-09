# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import random
import os.path
from celery.utils.log import get_task_logger
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_claritynow_api.lib import const


logger = get_task_logger(__name__)
logger.setLevel(const.VLAB_CLARITYNOW_LOG_LEVEL.upper())


def show_claritynow(username):
    """Obtain basic information about ClarityNow

    :Returns: Dictionary

    :param username: The user requesting info about their ClarityNow
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        claritynow_vms = {}
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm)
            kind, version = info['note'].split('=')
            if kind == 'ClarityNow':
                claritynow_vms[vm.name] = info
    return claritynow_vms


def delete_claritynow(username, machine_name):
    """Unregister and destroy a user's ClarityNow

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param machine_name: The name of the VM to delete
    :type machine_name: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity)
                kind, version = info['note'].split('=')
                if kind == 'ClarityNow':
                    logger.debug('powering off VM')
                    virtual_machine.power(entity, state='off')
                    delete_task = entity.Destroy_Task()
                    logger.debug('blocking while VM is being destroyed')
                    consume_task(delete_task)
                    break
        else:
            raise ValueError('No {} named {} found'.format('claritynow', machine_name))


def create_claritynow(username, machine_name, image, network):
    """Deploy a new instance of ClarityNow

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new ClarityNow
    :type username: String

    :param machine_name: The name of the new instance of ClarityNow
    :type machine_name: String

    :param image: The image/version of ClarityNow to create
    :type image: String

    :param network: The name of the network to connect the new ClarityNow instance up to
    :type network: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        image_name = convert_name(image)
        logger.info(image_name)
        ova = Ova(os.path.join(const.VLAB_CLARITYNOW_IMAGES_DIR, image_name))
        try:
            network_map = vim.OvfManager.NetworkMapping()
            network_map.name = ova.networks[0]
            try:
                network_map.network = vcenter.networks[network]
            except KeyError:
                raise ValueError('No such network named {}'.format(network))
            the_vm = virtual_machine.deploy_from_ova(vcenter, ova, [network_map],
                                                     username, machine_name, logger)
        finally:
            ova.close()
        spec = vim.vm.ConfigSpec()
        spec.annotation = 'ClarityNow={}'.format(image)
        task = the_vm.ReconfigVM_Task(spec)
        consume_task(task)
        _setup_vm(vcenter, the_vm)
        return virtual_machine.get_info(vcenter, the_vm)


def _setup_vm(vcenter, the_vm):
    """Configure the ClarityNow server

    The license is only good for 60 days, so we have to perform a time hack
    on the new VM until ClarityNow is able to produce a persistent license.

    :Returns: None

    :Raises: RuntimeError

    :param vcenter: The instantiated connection to vCenter
    :type vcenter: vlab_inf_common.vmware.vCenter

    :param the_vm: The new ClarityNow server
    :type the_vm: vim.VirtualMachine
    """
    cmd1 = '/usr/bin/sudo'
    args1 = '/usr/bin/timedatectl set-ntp 0'
    logger.info('Disabling NTP on server')
    result1 = virtual_machine.run_command(vcenter,
                                         the_vm,
                                         cmd1,
                                         user='administrator',
                                         password='a',
                                         arguments=args1)
    if result1.exitCode:
        error = 'Failed to disable NTP on the server'
        logger.error('{}: ExitCode {}, CMD {},'.format(error, result1.exitCode, result1.cmdLine))
        raise RuntimeError(error)

    logger.info('Setting date to 2018-09-28')
    cmd2 = '/usr/bin/sudo'
    args2 = '/usr/bin/timedatectl set-time 2018-09-28'
    result2 = virtual_machine.run_command(vcenter,
                                         the_vm,
                                         cmd2,
                                         user='administrator',
                                         password='a',
                                         arguments=args2)
    if result2.exitCode:
        error = 'Failed to set the date to 2018-09-28'
        logger.error('{}: ExitCode {}, CMD {},'.format(error, result2.exitCode, result2.cmdLine))
        raise RuntimeError(error)


def list_images():
    """Obtain a list of available versions of ClarityNow that can be created

    :Returns: List
    """
    images = os.listdir(const.VLAB_CLARITYNOW_IMAGES_DIR)
    images = [convert_name(x, to_version=True) for x in images]
    return images


def convert_name(name, to_version=False):
    """This function centralizes converting between the name of the OVA, and the
    version of software it contains.

    TODO - State the naming convention

    :param name: The thing to covert
    :type name: String

    :param to_version: Set to True to covert the name of an OVA to the version
    :type to_version: Boolean
    """
    if to_version:
        return name.split('-')[-1].replace('.ova', '')
    else:
        return 'ClarityNow-{}.ova'.format(name)

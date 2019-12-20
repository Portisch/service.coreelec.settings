# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2020-present Team CoreELEC (https://coreelec.org)

import log
import oe
import os
import re
import glob
import xbmc
import xbmcgui
import oeWindows
import threading
import subprocess
import shutil


class hardware:

    ENABLED = False
    menu = {'8': {
        'name': 32004,
        'menuLoader': 'load_menu',
        'listTyp': 'list',
        'InfoText': 780,
        }}

    remotes = [
        {
            "name": "Hardkernel",
            "remotewakeup": "0x23dc4db2",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Minix",
            "remotewakeup": "0xe718fe01",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Beelink",
            "remotewakeup": "0xa659ff00",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Khadas",
            "remotewakeup": "0xeb14ff00",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Khadas VTV",
            "remotewakeup": "0xff00fe01",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "MCE",
            "remotewakeup": "0x800f040c",
            "decode_type": "0x5",
            "remotewakeupmask": "0xffff7fff"
        },
    ]

    @log.log_function()
    def __init__(self, oeMain):
        self.oe = oeMain
        self.struct = {
            'fan': {
                'order': 1,
                'name': 32500,
                'not_supported': [],
                'settings': {
                    'fan_mode': {
                        'order': 1,
                        'name': 32501,
                        'InfoText': 781,
                        'value': 'off',
                        'action': 'initialize_fan',
                        'type': 'multivalue',
                        'values': ['off', 'auto', 'manual'],
                        },
                    'fan_level': {
                        'order': 2,
                        'name': 32502,
                        'InfoText': 782,
                        'value': '0',
                        'action': 'set_fan_level',
                        'type': 'multivalue',
                        'values': ['0','1','2','3'],
                        'parent': {
                            'entry': 'fan_mode',
                            'value': ['manual'],
                            },
                        },
                    },
                },
            'power': {
                'order': 1,
                'name': 32503,
                'not_supported': [],
                'settings': {
                    'inject_bl301': {
                        'order': 1,
                        'name': 32504,
                        'InfoText': 785,
                        'value': '0',
                        'action': 'set_bl301',
                        'type': 'button',
                        },
                    'remote_power': {
                        'order': 2,
                        'name': 32505,
                        'InfoText': 786,
                        'value': '',
                        'action': 'set_remote_power',
                        'type': 'multivalue',
                        'values': ['Unknown'],
                        },
                    'wol': {
                        'order': 3,
                        'name': 32506,
                        'InfoText': 787,
                        'value': '0',
                        'action': 'set_wol',
                        'type': 'bool',
                        },
                    'usbpower': {
                        'order': 4,
                        'name': 32507,
                        'InfoText': 788,
                        'value': '0',
                        'action': 'set_usbpower',
                        'type': 'bool',
                        },
                    },
                },
            }

    @log.log_function()
    def start_service(self):
        self.load_values()
        self.initialize_fan()

    @log.log_function()
    def stop_service(self):
        return

    @log.log_function()
    def do_init(self):
        self.load_values()

    @log.log_function()
    def exit(self):
        pass

    @log.log_function()
    def load_values(self):
        value = oe.read_setting('hardware', 'fan_mode')
        if not value is None:
            self.struct['fan']['settings']['fan_mode']['value'] = value
        value = oe.read_setting('hardware', 'fan_level')
        if not value is None:
            self.struct['fan']['settings']['fan_level']['value'] = value

        if not os.path.exists('/usr/sbin/inject_bl301'):
            self.struct['power']['settings']['inject_bl301']['hidden'] = 'true'
            self.struct['power']['settings']['inject_bl301']['value'] = '0'

        remotewakeup = oe.get_config_ini('remotewakeup')

        remote_names = []
        remote_is_known = 0
        for remote in self.remotes:
            remote_names.append(remote["name"])
            if remote["remotewakeup"] in remotewakeup:
                self.struct['power']['settings']['remote_power']['value'] = remote["name"]
                remote_is_known = 1

        if remotewakeup == '':
            self.struct['power']['settings']['remote_power']['value'] = ''
        if remotewakeup != '' and remote_is_known == 0:
            self.struct['power']['settings']['remote_power']['value'] = 'Custom'

        self.struct['power']['settings']['remote_power']['values'] = remote_names

        wol = oe.get_config_ini('wol', '0')
        if wol == '' or "0" in wol:
            self.struct['power']['settings']['wol']['value'] = '0'
        if "1" in wol:
            self.struct['power']['settings']['wol']['value'] = '1'

        usbpower = oe.get_config_ini('usbpower', '0')
        if usbpower == '' or "0" in usbpower:
            self.struct['power']['settings']['usbpower']['value'] = '0'
        if "1" in usbpower:
            self.struct['power']['settings']['usbpower']['value'] = '1'


    @log.log_function()
    def initialize_fan(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)
        if os.access('/sys/class/fan/enable', os.W_OK) and os.access('/sys/class/fan/mode', os.W_OK):
            if self.struct['fan']['settings']['fan_mode']['value'] == 'off':
                fan_enable = open('/sys/class/fan/enable', 'w')
                fan_enable.write('0')
                fan_enable.close()
            if self.struct['fan']['settings']['fan_mode']['value'] == 'manual':
                fan_enable = open('/sys/class/fan/enable', 'w')
                fan_enable.write('1')
                fan_enable.close()
                fan_mode_ctl = open('/sys/class/fan/mode', 'w')
                fan_mode_ctl.write('0')
                fan_mode_ctl.close()
                self.set_fan_level()
            if self.struct['fan']['settings']['fan_mode']['value'] == 'auto':
                fan_enable = open('/sys/class/fan/enable', 'w')
                fan_enable.write('1')
                fan_enable.close()
                fan_mode_ctl = open('/sys/class/fan/mode', 'w')
                fan_mode_ctl.write('1')
                fan_mode_ctl.close()

    @log.log_function()
    def set_fan_level(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)
        if os.access('/sys/class/fan/level', os.W_OK):
            if not self.struct['fan']['settings']['fan_level']['value'] is None and not self.struct['fan']['settings']['fan_level']['value'] == '':
                fan_level_ctl = open('/sys/class/fan/level', 'w')
                fan_level_ctl.write(self.struct['fan']['settings']['fan_level']['value'])
                fan_level_ctl.close()

    @log.log_function()
    def set_remote_power(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

        for remote in self.remotes:
            if self.struct['power']['settings']['remote_power']['value'] == remote["name"]:
                oe.set_config_ini("remotewakeup", "\'" + remote["remotewakeup"] + "\'")
                oe.set_config_ini("decode_type", "\'" + remote["decode_type"] + "\'")
                oe.set_config_ini("remotewakeupmask" , "\'" + remote["remotewakeupmask"] + "\'")

    @log.log_function()
    def set_bl301(self, listItem=None):
        xbmcDialog = xbmcgui.Dialog()
        ynresponse = xbmcDialog.yesno(oe._(33515), oe._(33516), yeslabel=oe._(33511), nolabel=oe._(32212))

        if ynresponse == 1:
            IBL = subprocess.Popen(["/usr/sbin/inject_bl301", "-Y"], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            IBL.wait()
            IBL_Code = IBL.returncode
            f = open("/storage/inject_bl301.log",'w')
            f.writelines(IBL.stdout.readlines())
            f.close()

            if IBL_Code == 0:
                response = xbmcDialog.ok(oe._(33512), oe._(33517))
            elif IBL_Code == 1:
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(oe._(33513), oe._(33520))
            elif IBL_Code == (-2 & 0xff):
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(oe._(33514), oe._(33519))
            else:
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(oe._(33514), oe._(33518) % IBL_Code)

            if IBL_Code != 0:
                oe.dbg_log('hardware::set_bl301', 'ERROR: (%d)' % IBL_Code, 4)

    @log.log_function()
    def set_wol(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

            if self.struct['power']['settings']['wol']['value'] == '1':
                oe.set_config_ini("wol", "1")
            else:
                oe.set_config_ini("wol", "0")

    @log.log_function()
    def set_usbpower(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

            if self.struct['power']['settings']['usbpower']['value'] == '1':
                oe.set_config_ini("usbpower", "1")
            else:
                oe.set_config_ini("usbpower", "0")

    @log.log_function()
    def load_menu(self, focusItem):
        oe.winOeMain.build_menu(self.struct)

    @log.log_function()
    def set_value(self, listItem):
        self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
        oe.write_setting('hardware', listItem.getProperty('entry'), str(listItem.getProperty('value')))

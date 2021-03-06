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
import platform
import random

# CEC Wake Up flags from u-boot(bl301)
CEC_FUNC_MASK = 0
AUTO_POWER_ON_MASK = 3
STREAMPATH_POWER_ON_MASK = 4
ACTIVE_SOURCE_MASK = 6

class hardware:
    ENABLED = False
    need_inject = False
    check_for_reboot = False
    menu = {'8': {
        'name': 32004,
        'menuLoader': 'load_menu',
        'listTyp': 'list',
        'InfoText': 780,
        }}

    power_compatible_devices = [
        'odroid_n2',
        'odroid_c4',
    ]

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
            "name": "Beelink 2",
            "remotewakeup": "0xae517f80",
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

    disk_idle_times = [
        {
            "name": "Disabled",
            "value": "0"
        },
        {
            "name": "5 Minutes",
            "value": "300"
        },
        {
            "name": "10 Minutes",
            "value": "600"
        },
        {
            "name": "20 Minutes",
            "value": "1200"
        },
        {
            "name": "30 Minutes",
            "value": "1800"
        },
        {
            "name": "1 Hour",
            "value": "3600"
        },
        {
            "name": "2 Hours",
            "value": "7200"
        },
        {
            "name": "5 Hours",
            "value": "18000"
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
                'order': 2,
                'name': 32503,
                'not_supported': [],
                'compatible_model': self.power_compatible_devices,
                'settings': {
                    'inject_bl301': {
                        'order': 1,
                        'name': 32504,
                        'InfoText': 785,
                        'value': '0',
                        'action': 'set_bl301',
                        'type': 'bool',
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
            'dtb_settings': {
                'order': 3,
                'name': 32523,
                'not_supported': [],
                'settings': {
                    'sys_led': {
                        'order': 1,
                        'name': 32518,
                        'InfoText': 789,
                        'value': '',
                        'xml_node': 'sys_led',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'red_led': {
                        'order': 2,
                        'name': 32527,
                        'InfoText': 789,
                        'value': '',
                        'xml_node': 'red_led',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'spicc0': {
                        'order': 3,
                        'name': 32528,
                        'InfoText': 902,
                        'value': '',
                        'xml_node': 'spicc0',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'spicc1': {
                        'order': 4,
                        'name': 32528,
                        'InfoText': 902,
                        'value': '',
                        'xml_node': 'spicc1',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'remote_type': {
                        'order': 5,
                        'name': 32529,
                        'InfoText': 903,
                        'value': 'NEC',
                        'xml_node': 'remote_type',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'dvb': {
                        'order': 6,
                        'name': 32532,
                        'InfoText': 904,
                        'value': '',
                        'xml_node': 'dvb',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    'emmc': {
                        'order': 7,
                        'name': 32525,
                        'InfoText': 900,
                        'value': '',
                        'xml_node': 'emmc',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        'dangerous': True,
                        },
                    'slowsdio': {
                        'order': 8,
                        'name': 32526,
                        'InfoText': 901,
                        'value': '',
                        'xml_node': 'slowsdio',
                        'action': 'set_value_xml',
                        'type': 'multivalue',
                        },
                    },
                },
            'cec': {
                'order': 4,
                'name': 32512,
                'not_supported': [],
                'settings': {
                    'cec_name': {
                        'order': 1,
                        'name': 32513,
                        'InfoText': 792,
                        'value': 'CoreELEC',
                        'action': 'set_cec',
                        'type': 'text',
                        },
                    'cec_all': {
                        'order': 2,
                        'name': 32514,
                        'InfoText': 793,
                        'value': '0',
                        'bit': CEC_FUNC_MASK,
                        'action': 'set_cec',
                        'type': 'bool',
                        },
                    'cec_auto_power': {
                        'order': 3,
                        'name': 32515,
                        'InfoText': 794,
                        'value': '0',
                        'bit': AUTO_POWER_ON_MASK,
                        'action': 'set_cec',
                        'type': 'bool',
                        },
                    'cec_streaming': {
                        'order': 4,
                        'name': 32516,
                        'InfoText': 795,
                        'value': '0',
                        'bit': STREAMPATH_POWER_ON_MASK,
                        'action': 'set_cec',
                        'type': 'bool',
                        },
                    'cec_active_route': {
                        'order': 5,
                        'name': 32517,
                        'InfoText': 796,
                        'value': '0',
                        'bit': ACTIVE_SOURCE_MASK,
                        'action': 'set_cec',
                        'type': 'bool',
                        },
                    },
                },
            'display': {
                'order': 5,
                'name': 32508,
                'not_supported': [],
                'settings': {
                    'vesa_enable': {
                        'order': 1,
                        'name': 32509,
                        'InfoText': 790,
                        'value': '0',
                        'action': 'set_vesa_enable',
                        'type': 'bool',
                        },
                    },
                },
            'performance': {
                'order': 6,
                'name': 32510,
                'not_supported': [],
                'settings': {
                    'cpu_governor': {
                        'order': 1,
                        'name': 32511,
                        'InfoText': 791,
                        'value': '',
                        'action': 'set_cpu_governor',
                        'type': 'multivalue',
                        'values': ['ondemand', 'performance'],
                        },
                    },
                },
            'hdd': {
                'order': 7,
                'name': 32519,
                'not_supported': [],
                'settings': {
                    'disk_park': {
                        'order': 1,
                        'name': 32520,
                        'InfoText': 797,
                        'value': '0',
                        'action': 'set_disk_park',
                        'type': 'bool',
                        },
                    'disk_park_time': {
                        'order': 2,
                        'name': 32521,
                        'InfoText': 798,
                        'value': '10',
                        'action': 'set_disk_park',
                        'type': 'text',
                        },
                    'disk_idle': {
                        'order': 3,
                        'name': 32522,
                        'InfoText': 799,
                        'value': '',
                        'action': 'set_disk_idle',
                        'type': 'multivalue',
                        'values': ['Disabled'],
                        },
                    },
                },
            }

    @log.log_function()
    def start_service(self):
        self.load_values()
        if not 'hidden' in self.struct['fan']:
            self.initialize_fan()
        self.set_cpu_governor()
        self.set_disk_park()
        self.set_disk_idle()

    @log.log_function()
    def stop_service(self):
        return

    @log.log_function()
    def do_init(self):
        self.load_values()

    @log.log_function()
    def exit(self):
        suppress_dialog = False
        xbmcDialog = xbmcgui.Dialog()
        if self.struct['power']['settings']['inject_bl301']['value'] == '1':

            if hardware.need_inject:
                IBL_Code = self.run_inject_bl301('-Y')

                if IBL_Code == 0:
                    self.load_values()
                    response = xbmcDialog.ok(oe._(33512), oe._(33517))
                    suppress_dialog = True
                elif IBL_Code == 1:
                    response = xbmcDialog.ok(oe._(33513), oe._(33520))
                    suppress_dialog = True
                elif IBL_Code == (-2 & 0xff):
                    response = xbmcDialog.ok(oe._(33514), oe._(33519))
                else:
                    response = xbmcDialog.ok(oe._(33514), oe._(33518) % IBL_Code)

                if IBL_Code != 0:
                    oe.dbg_log('hardware::set_bl301', 'ERROR: (%d)' % IBL_Code, 4)

        if hardware.check_for_reboot:
            ret = subprocess.call("/usr/lib/coreelec/dtb-xml", shell=True)
            if ret == 1 and not suppress_dialog:
                response = xbmcDialog.ok(oe._(33512), oe._(33523))

        hardware.need_inject = False
        hardware.check_for_reboot = False
        pass

    @log.log_function()
    def check_compatibility(self):
        ret = False
        dtname = oe.execute('/usr/bin/dtname', get_result=1).rstrip('\x00\n')
        ret = any(substring in dtname for substring in self.struct['power']['compatible_model'])
        oe.dbg_log('hardware::check_compatibility', 'exit_function, ret: %s' % ret, 0)
        return ret

    @log.log_function()
    def get_SoC_id(self):
        ret = 0xFF
        cpu_serial = [line for line in open("/proc/cpuinfo", 'r') if 'Serial' in line]
        cpu_id = [x.strip() for x in cpu_serial[0].split(':')][1]
        ret = int(cpu_id[:2], 16)
        return ret

    @log.log_function()
    def run_inject_bl301(self, parameter=''):
        IBL = subprocess.Popen(["/usr/sbin/inject_bl301", parameter], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        IBL.wait()
        lines = IBL.stdout.readlines()
        if len(lines) > 0:
            f = open("/storage/inject_bl301.log",'w')
            f.writelines([line.decode('utf-8') for line in lines])
            f.close()
        return IBL.returncode

    @log.log_function()
    def inject_check_compatibility(self):
        ret = False
        platform_version = platform.release().split('.')
        if int(platform_version[0]) >= 4 and int(platform_version[1]) >= 9 and \
            os.path.exists('/usr/sbin/inject_bl301'):
            if self.run_inject_bl301('-c') == 0:
                ret = True
        return ret

    @log.log_function()
    def load_values(self):
        hide_power_section = True

        if not os.path.exists('/sys/class/fan'):
            self.struct['fan']['hidden'] = 'true'
        else:
            value = oe.read_setting('hardware', 'fan_mode')
            if not value is None:
                self.struct['fan']['settings']['fan_mode']['value'] = value
            value = oe.read_setting('hardware', 'fan_level')
            if not value is None:
                self.struct['fan']['settings']['fan_level']['value'] = value

        if not os.path.exists('/run/use-meson-remote'):
            self.struct['dtb_settings']['settings']['remote_type']['hidden'] = 'true'
        else:
            if 'hidden' in self.struct['dtb_settings']['settings']['remote_type']:
                del self.struct['dtb_settings']['settings']['remote_type']['hidden']
            self.fill_values_by_xml(self.struct['dtb_settings']['settings']['remote_type'])

        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['sys_led'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['red_led'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['spicc0'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['spicc1'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['dvb'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['emmc'])
        self.fill_values_by_xml(self.struct['dtb_settings']['settings']['slowsdio'])

        if not self.inject_check_compatibility():
            self.struct['power']['settings']['inject_bl301']['hidden'] = 'true'
            self.struct['power']['settings']['inject_bl301']['value'] = '0'
        else:
            if os.path.exists('/run/bl301_injected'):
                hide_power_section = False
                if 'hidden' in self.struct['power']['settings']['inject_bl301']:
                    del self.struct['power']['settings']['inject_bl301']['hidden']
                self.struct['power']['settings']['inject_bl301']['value'] = '1'
            else:
                self.struct['power']['settings']['inject_bl301']['value'] = '0'

        power_setting_visible = bool(int(self.struct['power']['settings']['inject_bl301']['value'])) or self.check_compatibility()

        if not power_setting_visible:
            self.struct['cec']['hidden'] = 'true'
        else:
            if 'hidden' in self.struct['cec']:
                del self.struct['cec']['hidden']

            if not self.struct['power']['settings']['inject_bl301']['value'] == '1':
                self.struct['cec']['settings']['cec_name']['hidden'] = 'true'
            else:
                if 'hidden' in self.struct['cec']['settings']['cec_name']:
                    del self.struct['cec']['settings']['cec_name']['hidden']
                self.struct['cec']['settings']['cec_name']['value'] = oe.get_config_ini('cec_osd_name', 'CoreELEC')

            cec_func_config = int(oe.get_config_ini('cec_func_config', '7f'), 16)
            bit = self.struct['cec']['settings']['cec_all']['bit']
            self.struct['cec']['settings']['cec_all']['value'] = str((cec_func_config & (1 << bit)) >> bit)

            if self.struct['cec']['settings']['cec_all']['value'] == '1':
                bit = self.struct['cec']['settings']['cec_auto_power']['bit']
                self.struct['cec']['settings']['cec_auto_power']['value'] = str((cec_func_config & (1 << bit)) >> bit)
                bit = self.struct['cec']['settings']['cec_streaming']['bit']
                self.struct['cec']['settings']['cec_streaming']['value'] = str((cec_func_config & (1 << bit)) >> bit)
                bit = self.struct['cec']['settings']['cec_active_route']['bit']
                self.struct['cec']['settings']['cec_active_route']['value'] = str((cec_func_config & (1 << bit)) >> bit)

        if not power_setting_visible:
            self.struct['power']['settings']['remote_power']['hidden'] = 'true'
        else:
            hide_power_section = False
            if 'hidden' in self.struct['power']['settings']['remote_power']:
                del self.struct['power']['settings']['remote_power']['hidden']

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
        if any("stmmac" in s for s in os.listdir('/sys/bus/mdio_bus/drivers/RTL8211F Gigabit Ethernet')):
            hide_power_section = False
            if wol == '' or "0" in wol:
                self.struct['power']['settings']['wol']['value'] = '0'
            if "1" in wol:
                self.struct['power']['settings']['wol']['value'] = '1'
        else:
            self.struct['power']['settings']['wol']['hidden'] = 'true'
            if "1" in wol:
                oe.set_config_ini("wol", "0")

        if not power_setting_visible or self.get_SoC_id() < 0x28:
            self.struct['power']['settings']['usbpower']['hidden'] = 'true'
        else:
            hide_power_section = False
            if 'hidden' in self.struct['power']['settings']['usbpower']:
                del self.struct['power']['settings']['usbpower']['hidden']

            usbpower = oe.get_config_ini('usbpower', '0')
            if usbpower == '' or "0" in usbpower:
                self.struct['power']['settings']['usbpower']['value'] = '0'
            if "1" in usbpower:
                self.struct['power']['settings']['usbpower']['value'] = '1'

        if os.path.exists('/flash/vesa.enable'):
            self.struct['display']['settings']['vesa_enable']['value'] = '1'
        else:
            self.struct['display']['settings']['vesa_enable']['value'] = '0'

        cpu_clusters = ["", "cpu0/"]
        for cluster in cpu_clusters:
            sys_device = '/sys/devices/system/cpu/' + cluster + 'cpufreq/'
            if not os.path.exists(sys_device):
                continue

            if os.path.exists(sys_device + 'scaling_available_governors'):
                available_gov = oe.load_file(sys_device + 'scaling_available_governors')
                self.struct['performance']['settings']['cpu_governor']['values'] = available_gov.split()

            value = oe.read_setting('hardware', 'cpu_governor')
            if value is None:
                value = oe.load_file(sys_device + 'scaling_governor')

            self.struct['performance']['settings']['cpu_governor']['value'] = value

        value = oe.read_setting('hardware', 'disk_park')
        if not value is None:
            self.struct['hdd']['settings']['disk_park']['value'] = value

        value = oe.read_setting('hardware', 'disk_park_time')
        if not value is None:
            self.struct['hdd']['settings']['disk_park_time']['value'] = value
        else:
            self.struct['hdd']['settings']['disk_park_time']['value'] = '10'

        value = oe.read_setting('hardware', 'disk_idle')
        if value is None or value == '':
            value = 'Disabled'

        disk_idle_times_names = []
        self.struct['hdd']['settings']['disk_idle']['value'] = 'Disabled'
        for disk_idle_time in self.disk_idle_times:
          disk_idle_times_names.append(disk_idle_time["name"])
          if disk_idle_time["name"] in value:
            self.struct['hdd']['settings']['disk_idle']['value'] = disk_idle_time["name"]

        self.struct['hdd']['settings']['disk_idle']['values'] = disk_idle_times_names

        if hide_power_section:
            self.struct['power']['hidden'] = 'true'

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

        hardware.need_inject = True

    @log.log_function()
    def set_bl301(self, listItem=None):
        xbmcDialog = xbmcgui.Dialog()

        if listItem.getProperty('value') == '1':
            ynresponse = xbmcDialog.yesno(oe._(33515), oe._(33516), yeslabel=oe._(33511), nolabel=oe._(32212))

            if ynresponse == 1:
                IBL_Code = self.run_inject_bl301('-Y')

                if IBL_Code == 0:
                    self.struct['power']['settings']['inject_bl301']['value'] = '1'
                    subprocess.call("touch /run/bl301_injected", shell=True)
                    self.load_values()
                    response = xbmcDialog.ok(oe._(33512), oe._(33517))
                elif IBL_Code == 1:
                    response = xbmcDialog.ok(oe._(33513), oe._(33520))
                elif IBL_Code == (-2 & 0xff):
                    response = xbmcDialog.ok(oe._(33514), oe._(33519))
                else:
                    response = xbmcDialog.ok(oe._(33514), oe._(33518) % IBL_Code)

                if IBL_Code != 0:
                    oe.dbg_log('hardware::set_bl301', 'ERROR: (%d)' % IBL_Code, 4)
        else:
            ynresponse = xbmcDialog.yesno(oe._(33515), oe._(33521), yeslabel=oe._(33511), nolabel=oe._(32212))

            if ynresponse == 1:
                IBL = subprocess.Popen(["cat", "/proc/cpuinfo"], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                IBL.wait()
                cpu_serial = [line for line in open("/proc/cpuinfo", 'r') if 'Serial' in line]
                if cpu_serial != '':
                    filename = '/flash/{0}_bl301.bin'.format([x.strip() for x in cpu_serial[0].split(':')][1])
                    if os.path.exists(filename) and os.path.exists('/dev/bootloader'):
                        oe.dbg_log('hardware::set_bl301', 'write %s to /dev/bootloader' % filename, 0)
                        with open(filename, 'rb') as fr:
                            with open('/dev/bootloader', 'wb') as fw:
                                fw.write(fr.read())
                        self.struct['power']['settings']['inject_bl301']['value'] = '0'
                        subprocess.call("rm -rf /run/bl301_injected", shell=True)
                        self.load_values()
                        response = xbmcDialog.ok(oe._(33512), oe._(33522))

    @log.log_function()
    def set_cec(self, listItem=None):
        if not listItem == None:
            if not listItem.getProperty('entry') == 'cec_name':
                bit = self.struct['cec']['settings'][listItem.getProperty('entry')]['bit']
                cec_func_config = int(oe.get_config_ini('cec_func_config', '7f'), 16)

                if bit == CEC_FUNC_MASK:
                    if listItem.getProperty('value') == '0':
                        cec_func_config &= ~(1 << self.struct['cec']['settings']['cec_all']['bit'])
                        for item in self.struct['cec']['settings']:
                            if 'bit' in self.struct['cec']['settings'][item]:
                                self.struct['cec']['settings'][item]['value'] = '0'
                    else:
                        cec_func_config |= 1 << self.struct['cec']['settings']['cec_all']['bit']
                        self.struct['cec']['settings']['cec_all']['value'] = '1'
                        for item in self.struct['cec']['settings']:
                            if 'bit' in self.struct['cec']['settings'][item]:
                                bit = self.struct['cec']['settings'][item]['bit']
                                self.struct['cec']['settings'][item]['value'] = str((cec_func_config & (1 << bit)) >> bit)
                else:
                    if self.struct['cec']['settings']['cec_all']['value'] == '1':
                        self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
                        if listItem.getProperty('value') == '0':
                            cec_func_config &= ~(1 << bit)
                        else:
                            cec_func_config |= 1 << bit

                oe.set_config_ini("cec_func_config", hex(cec_func_config)[2:])
            else:
                old_name = self.struct['cec']['settings'][listItem.getProperty('entry')]['value']
                if not old_name == listItem.getProperty('value')[:14]:
                    self.struct['cec']['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')[:14]
                    oe.set_config_ini("cec_osd_name", self.struct['cec']['settings'][listItem.getProperty('entry')]['value'])

                    hardware.need_inject = True

    @log.log_function()
    def set_wol(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

            if self.struct['power']['settings']['wol']['value'] == '1':
                oe.set_config_ini("wol", "1")
            else:
                oe.set_config_ini("wol", "0")

            hardware.need_inject = True

    @log.log_function()
    def set_usbpower(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

            if self.struct['power']['settings']['usbpower']['value'] == '1':
                oe.set_config_ini("usbpower", "1")
            else:
                oe.set_config_ini("usbpower", "0")

            hardware.need_inject = True

    @log.log_function()
    def set_vesa_enable(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

            if self.struct['display']['settings']['vesa_enable']['value'] == '1':
              ret = subprocess.call("mount -o remount,rw /flash", shell=True)
              ret = subprocess.call("touch /flash/vesa.enable", shell=True)
              ret = subprocess.call("mount -o remount,ro /flash", shell=True)
            else:
              if os.path.exists("/flash/vesa.enable"):
                ret = subprocess.call("mount -o remount,rw /flash", shell=True)
                os.remove("/flash/vesa.enable")
                ret = subprocess.call("mount -o remount,ro /flash", shell=True)

    @log.log_function()
    def set_cpu_governor(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

        value = self.struct['performance']['settings']['cpu_governor']['value']
        if not value is None and not value == '':
            cpu_clusters = ["", "cpu0/", "cpu4/"]
            for cluster in cpu_clusters:
                sys_device = '/sys/devices/system/cpu/' + cluster + 'cpufreq/scaling_governor'
                if os.access(sys_device, os.W_OK):
                    cpu_governor_ctl = open(sys_device, 'w')
                    cpu_governor_ctl.write(value)
                    cpu_governor_ctl.close()

    @log.log_function()
    def set_disk_park(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

        if self.struct['hdd']['settings']['disk_park']['value'] == '1':
            value = self.struct['hdd']['settings']['disk_park_time']['value']
            subprocess.call(("echo -e 'PARK_HDD=\"yes\"\nPARK_WAIT=\"%s\"' > /run/disk-park.dat") % value, shell=True)
        else:
            subprocess.call("rm -rf /run/disk-park.dat", shell=True)

    @log.log_function()
    def set_disk_idle(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)

        subprocess.call("killall hd-idle &> /dev/null", shell=True)
        if not self.struct['hdd']['settings']['disk_idle']['value'] == 'Disabled':
            for disk_idle_time in self.disk_idle_times:
                if self.struct['hdd']['settings']['disk_idle']['value'] == disk_idle_time["name"]:
                    subprocess.call(("hd-idle -i %s") % disk_idle_time["value"], shell=True)

    @log.log_function()
    def load_menu(self, focusItem):
        oe.winOeMain.build_menu(self.struct)

    @log.log_function()
    def set_value_xml(self, listItem=None):
        if not listItem == None:
            num = random.randint(1000, 9999)
            response = str(num)
            if 'dangerous' in self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]:
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.input(oe._(33524) % str(num), type=xbmcgui.INPUT_NUMERIC)
            if str(num) == response:
                self.set_value(listItem)
                oe.set_dtbxml_value(listItem.getProperty('entry'), listItem.getProperty('value'))
                hardware.check_for_reboot = True

    @log.log_function()
    def fill_values_by_xml(self, var):
        values = oe.get_dtbxml_multivalues(var['xml_node'])
        value = oe.get_dtbxml_value(var['xml_node'])
        if not values is None and not value is None:
            if not value == 'migrated':
                if 'hidden' in var:
                    del var['hidden']
                var['values'] = values
                var['value'] = value
            else:
                var['hidden'] = 'true'
        else:
            oe.dbg_log('hardware::fill_values_by_xml', '"%s" could not be read from dtb.xml' % var['xml_node'], 0)

    @log.log_function()
    def set_value(self, listItem):
        self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
        oe.write_setting('hardware', listItem.getProperty('entry'), str(listItem.getProperty('value')))

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

            }

    @log.log_function()
    def start_service(self):
        self.load_values()
        self.set_fan_level()
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


    @log.log_function()
    def initialize_fan(self, listItem=None):
        if not listItem == None:
            self.set_value(listItem)
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
        if not self.struct['fan']['settings']['fan_level']['value'] is None and not self.struct['fan']['settings']['fan_level']['value'] == '':
            fan_level_ctl = open('/sys/class/fan/level', 'w')
            fan_level_ctl.write(self.struct['fan']['settings']['fan_level']['value'])
            fan_level_ctl.close()

    @log.log_function()
    def load_menu(self, focusItem):
        oe.winOeMain.build_menu(self.struct)

    @log.log_function()
    def set_value(self, listItem):
        self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
        oe.write_setting('hardware', listItem.getProperty('entry'), str(listItem.getProperty('value')))

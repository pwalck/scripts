#!/usr/bin/env python
# Copyright (c) 2012-2014 Erik Johansson <erik@ejohansson.se>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# Modified by Pontus Walck, 2015-03-07, to call external scripts
# to react to events.

import argparse
import sys
import os
import re

import tellcore.telldus as td
import tellcore.constants as const

from subprocess import call

callback_dir = os.environ["HOME"] + "/bin/telldus"

METHODS = {const.TELLSTICK_TURNON: 'turn on',
           const.TELLSTICK_TURNOFF: 'turn off',
           const.TELLSTICK_BELL: 'bell',
           const.TELLSTICK_TOGGLE: 'toggle',
           const.TELLSTICK_DIM: 'dim',
           const.TELLSTICK_LEARN: 'learn',
           const.TELLSTICK_EXECUTE: 'execute',
           const.TELLSTICK_UP: 'up',
           const.TELLSTICK_DOWN: 'down',
           const.TELLSTICK_STOP: 'stop'}

EVENTS = {const.TELLSTICK_DEVICE_ADDED: "added",
          const.TELLSTICK_DEVICE_REMOVED: "removed",
          const.TELLSTICK_DEVICE_CHANGED: "changed",
          const.TELLSTICK_DEVICE_STATE_CHANGED: "state changed"}

CHANGES = {const.TELLSTICK_CHANGE_NAME: "name",
           const.TELLSTICK_CHANGE_PROTOCOL: "protocol",
           const.TELLSTICK_CHANGE_MODEL: "model",
           const.TELLSTICK_CHANGE_METHOD: "method",
           const.TELLSTICK_CHANGE_AVAILABLE: "available",
           const.TELLSTICK_CHANGE_FIRMWARE: "firmware"}

TYPES = {const.TELLSTICK_CONTROLLER_TELLSTICK: 'tellstick',
         const.TELLSTICK_CONTROLLER_TELLSTICK_DUO: "tellstick duo",
         const.TELLSTICK_CONTROLLER_TELLSTICK_NET: "tellstick net"}


def device_event(id_, method, data, cid):
    method_string = METHODS.get(method, "UNKNOWN METHOD {0}".format(method))
    string = "[DEVICE] {0} -> {1}".format(id_, method_string)
    if method == const.TELLSTICK_DIM:
        string += " [{0}]".format(data)
    print(string)
    
    # TODO: Find device name and pass to scripts, or use to find script.
    
    if os.path.exists("{}/device/any".format(callback_dir)):
        call(["{}/device/any".format(callback_dir),
              "--id", str(id_),
              "--action", method_string])
    
    if os.path.exists("{}/device/{}".format(callback_dir, id_)):
        call(["{}/device/{}".format(callback_dir, id_),
              "--action", method_string])


def device_change_event(id_, event, type_, cid):
    event_string = EVENTS.get(event, "UNKNOWN EVENT {0}".format(event))
    string = "[DEVICE_CHANGE] {0} {1}".format(event_string, id_)
    if event == const.TELLSTICK_DEVICE_CHANGED:
        type_string = CHANGES.get(type_, "UNKNOWN CHANGE {0}".format(type_))
        string += " [{0}]".format(type_string)
    print(string)


def raw_event(data, controller_id, cid):
    m = re.search(r'^class:command;protocol:arctech;model:codeswitch;house:([A-Z]);method:bell;$', data)
    
    # TODO: Call a bell function instead of doing these things here.
    if m:
      house = m.group(1)
      
      if os.path.exists("{}/bell/any".format(callback_dir)):
        call(["{}/bell/any".format(callback_dir),
              "--house", house])
      
      if os.path.exists("{}/bell/{}".format(callback_dir, house)):
        call(["{}/bell/{}".format(callback_dir, house)])
    
    string = "[RAW] {0} <- {1}".format(controller_id, data)
    
    print(string)


def sensor_event(protocol, model, id_, dataType, value, timestamp, cid):
    string = "[SENSOR] {0} [{1}/{2}] ({3}) @ {4} <- {5}".format(
        id_, protocol, model, dataType, timestamp, value)
    print(string)
    
    if os.path.exists("{}/sensor/any".format(callback_dir)):
        call(["{}/sensor/any".format(callback_dir),
              "--id", str(id_),
              "--protocol", protocol,
              "--timestamp", str(timestamp),
              "--value", str(value),
              "--model", model,
              "--cid", str(cid),
              "--type", str(dataType)])
    
    if os.path.exists("{}/sensor/{}".format(callback_dir, id_)):
        call(["{}/sensor/{}".format(callback_dir, id_),
              "--action", method_string])


def controller_event(id_, event, type_, new_value, cid):
    event_string = EVENTS.get(event, "UNKNOWN EVENT {0}".format(event))
    string = "[CONTROLLER] {0} {1}".format(event_string, id_)
    if event == const.TELLSTICK_DEVICE_ADDED:
        type_string = TYPES.get(type_, "UNKNOWN TYPE {0}".format(type_))
        string += " {0}".format(type_string)
    elif (event == const.TELLSTICK_DEVICE_CHANGED
          or event == const.TELLSTICK_DEVICE_STATE_CHANGED):
        type_string = CHANGES.get(type_, "UNKNOWN CHANGE {0}".format(type_))
        string += " [{0}] -> {1}".format(type_string, new_value)
    print(string)


parser = argparse.ArgumentParser(description='Listen for Telldus events.')

parser.add_argument(
    '--all', action='store_true', help='Trace all events')
parser.add_argument(
    '--change', action='store_true', help='Trace device change events')
parser.add_argument(
    '--controller', action='store_true', help='Trace controller events')

args = vars(parser.parse_args())

try:
    import asyncio
    loop = asyncio.get_event_loop()
    dispatcher = td.AsyncioCallbackDispatcher(loop)
except ImportError:
    loop = None
    dispatcher = td.QueuedCallbackDispatcher()

core = td.TelldusCore(callback_dispatcher=dispatcher)
callbacks = []

callbacks.append(core.register_device_event(device_event))
callbacks.append(core.register_raw_device_event(raw_event))
callbacks.append(core.register_sensor_event(sensor_event))

for arg in args:
    if not (args[arg] or args['all']):
        continue
    try:
        if arg == 'change':
            callbacks.append(
                core.register_device_change_event(device_change_event))
        elif arg == 'controller':
            callbacks.append(core.register_controller_event(controller_event))
        else:
            assert arg == 'all'
    except AttributeError:
        if not args['all']:
            raise

if len(callbacks) == 0:
    print("Must enable at least one event")
    parser.print_usage()
    sys.exit(1)

try:
    import time
    
    bookkeeping_run = 0
    
    while True:
        core.callback_dispatcher.process_pending_callbacks()
        if (os.path.exists("{}/bookkeeping".format(callback_dir)) and
            time.time() - bookkeeping_run > 5):
          call(["{}/bookkeeping".format(callback_dir)])
          bookkeeping_run = time.time()
        time.sleep(0.5)
except KeyboardInterrupt:
    pass

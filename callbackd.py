#!/usr/bin/env python3
# vim: fileencoding=utf-8
#
# Copyright (C) 2022
#                   David Hobach <tripleh@hackingthe.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

'''
Simple daemon to react to Qubes OS events (VM started etc.) with configurable commands.

Configure the [event] --> [command] mapping inside the `callbackd.json'.

Executed commands will receive the following arguments:
1. subject (VM name or None)
2. event name
3. additional keyword arguments related to the event as json

Relevant doc:
- https://github.com/QubesOS/qubes-core-admin-client/blob/master/qubesadmin/events/utils.py
- https://dev.qubes-os.org/projects/core-admin-client/en/latest/_modules/qubesadmin/events.html
- https://www.qubes-os.org/doc/admin-api/
'''

import asyncio
import signal
import sys
import subprocess
import os
import functools
import json
import traceback
import shlex

import qubesadmin.events
import qubesadmin.tools

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CONF_FILE = os.path.join(SCRIPT_DIR, 'callbackd.json')
BACKGROUND_TASKS = set()

def error_out(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

async def acommand_handler(command, subject, event_name, **kwargs):
    try:
        cmd_arg = shlex.split(command, comments=True)
        proc = await asyncio.create_subprocess_exec(*cmd_arg, str(subject), str(event_name), json.dumps(kwargs), stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr)
        ret = await proc.wait()
        if ret != 0:
            print(f'The command {command} returned a non-zero exit code {ret}.', file=sys.stderr)
    except Exception:
        traceback.print_exc()

def command_handler(command, subject, event_name, **kwargs):
    task = asyncio.create_task(acommand_handler(command, subject, event_name, **kwargs))
    #without this reference, tasks may be garbage collected, even if still running
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)

def main():
    parser = qubesadmin.tools.QubesArgumentParser()
    args = parser.parse_args()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        events = qubesadmin.events.EventsDispatcher(args.app)

        #load config
        with open(CONF_FILE, encoding='utf-8') as json_file:
            conf = json.load(json_file)
        if ( not isinstance(conf, dict) ) or len(conf) == 0:
            error_out('The configuration file %s needs to define a dict of [event] --> [command].' % CONF_FILE)
        for event, command in conf.items():
            events.add_handler(event, functools.partial(command_handler, command))
        events_listener = asyncio.ensure_future(events.listen_for_events())
        loop.add_signal_handler(signal.SIGINT, events_listener.cancel)
        loop.add_signal_handler(signal.SIGTERM, events_listener.cancel)
        loop.add_signal_handler(signal.SIGPIPE, events_listener.cancel)
        loop.run_until_complete(events_listener)
    except Exception:
        traceback.print_exc()
    finally:
        loop.close()

if __name__ == '__main__':
    sys.exit(main())

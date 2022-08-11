# qubes-callbackd

Simple daemon to react to [Qubes OS](https://www.qubes-os.org/) events (VM started etc.) with configurable commands.

## Installation

1. Clone this repository and copy it to a directory of your liking in `dom0`, let's assume `/usr/share/qubes-callbackd`.
2. (Optional): To identify the event that you want to execute a callback command on, you can observe the events that
   Qubes OS generates with the default `callbackd.json` configuration. Just execute `/usr/share/qubes-callbackd/callbackd.py`
   and watch the events whilst using Qubes OS.
3. Configure `/usr/share/qubes-callbackd/callbackd.json` according to your needs. Each entry must map an event name to a
   command, binary or script to execute. The special event name `*` can be used to handle all events.
4. Use `systemd` or some other way to start `/usr/share/qubes-callbackd/callbackd.py` on boot. An exemplary `systemd` config
   is included in this repository.

## Uninstall

Just remove the directory created during the installation.

## Copyright

© 2022 David Hobach

qubes-callbackd is released under the GPLv3 license; see `LICENSE` for details.

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Record native dependencies and installed integration files, without activation."""
from pathlib import Path
import json
import os
import platform
import subprocess
import xml.etree.ElementTree as ET
import PySide6
from PySide6.QtCore import qVersion
import gi
from gi.repository import Gio


def main():
    if os.geteuid() == 0:
        raise RuntimeError('Compatibility tests must run as a regular user')
    units = {}
    for name in ('usbguard.service', 'usbguard-dbus.service'):
        path = next((p for base in ('/usr/lib/systemd/system', '/lib/systemd/system')
                     if (p := Path(base) / name).is_file()), None)
        if path is None:
            raise RuntimeError('Missing native systemd unit: ' + name)
        units[name] = str(path)
    actions = {action.attrib['id'] for path in Path('/usr/share/polkit-1/actions').glob('*usbguard*.policy')
               for action in ET.parse(path).getroot().findall('action')}
    expected = {'org.usbguard.Policy1.listRules', 'org.usbguard.Policy1.appendRule',
                'org.usbguard.Policy1.removeRule', 'org.usbguard.Devices1.listDevices',
                'org.usbguard.Devices1.applyDevicePolicy'}
    if not expected <= actions:
        raise RuntimeError('Native USBGuard Polkit contract missing: ' + repr(expected - actions))
    print(json.dumps({
        'scope': 'isolated source/UI tests; no live desktop, Polkit dialog or USB hardware',
        'os_release': Path('/etc/os-release').read_text(), 'uid': os.geteuid(),
        'python': platform.python_version(), 'pyside6': PySide6.__version__,
        'qt': qVersion(), 'pygobject': gi.__version__, 'gio_available': hasattr(Gio, 'DBusConnection'),
        'usbguard': subprocess.check_output(['usbguard', '--version'], text=True).strip(),
        'units': units, 'polkit_actions': sorted(actions),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

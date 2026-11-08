#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORMTHEME=generic
export QT_QUICK_BACKEND=software
export USBGUARD_TEST_BUS=1
dbus-run-session -- python3 -m pytest -q
python3 -m usbguard_control --demo --language es-419 --screenshot docs/images/usbguard-control-demo.png
python3 -m usbguard_control --demo --language en-US --screenshot docs/images/usbguard-control-demo-en.png
desktop-file-validate packaging/io.github.LupoSysAdmin.USBGuardControl.desktop
python3 scripts/build_deb.py

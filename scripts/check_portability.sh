#!/bin/sh
# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
# Source/UI compatibility only: never starts system services or accesses USB.
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORMTHEME=generic
export QT_QUICK_BACKEND=software
export USBGUARD_TEST_BUS=1
report_dir=.qa-evidence/portability
mkdir -p "$report_dir"
python3 scripts/portability_inventory.py > "$report_dir/environment.json"
cat "$report_dir/environment.json"
if dbus-run-session -- python3 -m pytest -q --junitxml="$report_dir/tests.xml" > "$report_dir/tests.log" 2>&1; then
  cat "$report_dir/tests.log"
else
  cat "$report_dir/tests.log"
  exit 1
fi
python3 -m usbguard_control --demo --language es-419 --screenshot "$report_dir/demo-es.png"
python3 -m usbguard_control --demo --language en-US --screenshot "$report_dir/demo-en.png"
desktop-file-validate packaging/io.github.LupoSysAdmin.USBGuardControl.desktop

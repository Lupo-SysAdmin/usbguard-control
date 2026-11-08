#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only diagnostics: no USB identifiers, secrets or configuration contents."""
import importlib.util
import json
import platform
import shutil
import subprocess


def check(args):
    if not shutil.which(args[0]): return "not installed"
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return {"exit_code": result.returncode, "output": (result.stdout + result.stderr).strip()[:3000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return str(error)


print(json.dumps({
    "python": platform.python_version(),
    "modules": {name: bool(importlib.util.find_spec(name)) for name in ("PySide6", "gi")},
    "usbguard": check(["usbguard", "--version"]),
    "apt": check(["apt-cache", "policy", "usbguard"]),
    "services": check(["systemctl", "show", "usbguard.service", "usbguard-dbus.service", "--property=ActiveState,SubState,LoadState"]),
}, indent=2))

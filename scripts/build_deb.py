#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an unprivileged, architecture-independent Debian package."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.0"


def main():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="usbguard-control-build-") as directory:
        stage = Path(directory)
        app_dir = stage / "usr/share/usbguard-control"
        app_dir.mkdir(parents=True)
        shutil.copytree(ROOT / "src/usbguard_control", app_dir / "usbguard_control", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (app_dir / "launch.py").write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent))\nfrom usbguard_control.app import main\nraise SystemExit(main())\n')
        binary = stage / "usr/bin/usbguard-control"
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nexec /usr/bin/python3 -B -I /usr/share/usbguard-control/launch.py "$@"\n')
        binary.chmod(0o755)
        desktop = stage / "usr/share/applications"
        desktop.mkdir(parents=True)
        shutil.copy2(ROOT / "packaging/io.github.LupoSysAdmin.USBGuardControl.desktop", desktop)
        icons = stage / "usr/share/icons/hicolor/scalable/apps"
        icons.mkdir(parents=True)
        shutil.copy2(ROOT / "src/usbguard_control/assets/shield.svg", icons / "usbguard-control.svg")
        docs = stage / "usr/share/doc/usbguard-control"
        docs.mkdir(parents=True)
        for file in ("LICENSE", "README.md", "README.en.md", "AUTHORS", "NOTICE", "SECURITY.md"):
            shutil.copy2(ROOT / file, docs)
        shutil.copytree(ROOT / "docs", docs / "docs")
        shutil.copy2(ROOT / "packaging/copyright", docs / "copyright")
        metadata = stage / "DEBIAN"
        metadata.mkdir()
        (metadata / "control").write_text(f'''Package: usbguard-control
Version: {VERSION}-1
Section: utils
Priority: optional
Architecture: all
Maintainer: Jan Herrera
Homepage: https://github.com/Lupo-SysAdmin
Depends: python3 (>= 3.11), python3-gi, python3-pyside6.qtcore (>= 6.6), python3-pyside6.qtgui, python3-pyside6.qtqml, python3-pyside6.qtquick, python3-pyside6.qtquickcontrols2, qml6-module-qtquick, qml6-module-qtquick-window, qml6-module-qtquick-layouts, qml6-module-qtquick-controls, qml6-module-qtquick-dialogs, qml6-module-qtquick-templates, qml6-module-qtqml-workerscript
Suggests: usbguard (>= 1.1.4)
Description: Independent desktop interface for USBGuard
 Modern Qt Quick interface with a safe demonstration mode, device details,
 explicit authorization and session activity. USBGuard setup is separate.
''', encoding="utf-8")
        destination = output / f"usbguard-control_{VERSION}-1_all.deb"
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage), str(destination)], check=True)
        print(destination)


if __name__ == "__main__": main()

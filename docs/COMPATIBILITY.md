[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](COMPATIBILITY.es.md)

<a id="compatibilidad-de-050--compatibility"></a>

# Compatibility of 0.5.0

Checked on **November 21, 2026**. An automated containerized test is not equivalent to a desktop session with authentication and hardware.

| System | Result and scope |
|---|---|
| Kali 2026.3/Xfce/X11 | Package installed, real interface, editor with Polkit and virtual USB reconnection |
| Parrot 7.4 / KDE / Wayland | Package installed, real interface, editor with Polkit and virtual USB reconnection |
| Debian trixie | 117 CI tests, QML captures and construction of `.deb` |
| Ubuntu 26.04 | 117 tests as a normal user, QML ES/EN and native dependencies; installation, integrity and opening of `.deb` in demo mode |
| Fedora 45 | 117 tests as a normal user and QML ES/EN with native dependencies; execution from source code |
| Arch Linux rolling | 117 tests as a normal user and QML ES/EN with native dependencies; execution from source code |

The last three rows were run on official distribution images within GitHub Actions machines. The [initial matrix run](https://github.com/Lupo-SysAdmin/usbguard-control/actions/runs/44949137231) and [permanent workflow](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml) preserve the results. CI artifacts include inventory, JUnit report, test log, and screenshots; are subject to GitHub retention.

| CI environment | Python | PySide6 / Qt | PyGObject | USBGuard installed |
|---|---|---|---|---|
| Ubuntu 26.04 | 3.14.4 | 6.10.2 | 3.56.2 | 1.1.4 |
| Fedora 45 | 3.15.2 | 6.11.2 | 3.58.1 | 1.1.4 |
| Arch rolling | 3.14.10 | 6.12.0 | 3.58.1 | 1.1.4 |

The inventory checks for the presence of GIO, units `usbguard.service` and `usbguard-dbus.service`, and the Polkit actions used. It does not start those services: the suite uses an isolated bus and a test service. Therefore, **no actual Polkit, Reboot, Tray, SELinux, or USB dialogs have been validated in Ubuntu/Fedora/Arch**. There were three PyGObject/asyncio deprecation notices on Fedora/Arch and four on Ubuntu; no test failed.

<a id="instalación-y-límites"></a>

## Installation and limits

- The distributed installer is `.deb`. It is not a package for Fedora or Arch, and no RPM, PKGBUILD, or AUR package has been released.
- The code/wheel requires **Python ≥ 3.11, PySide6 ≥ 6.6 and < 7, PyGObject/GIO**, and for system functions, USBGuard with D-Bus bridge, systemd and Polkit. Modules and package names change by distribution.
- The automatic start of this GUI requires the provision of the installed package (`/usr/share/usbguard-control` and `/usr/bin/usbguard-control`); a run from code or isolated wheel installation does not enable that option.
- The initial installation/configuration of USBGuard is independent. APT instructions should not be copied from Kali to Fedora or Arch.
- `.deb` is not guaranteed in older versions of Ubuntu or compatibility with all derivatives, architectures or distributions without systemd. Just because two systems share a desktop does not certify its packaging or permissions.
- GNOME/Wayland test belongs to 0.3.0; the host is still installed with 0.2.0. See [0.5.0 validation](VALIDATION-0.5.md) for evidence separation.

Package references: [PySide6 on Ubuntu 26.04](https://packages.ubuntu.com/resolute/python3-pyside6.qtquickcontrols2), [PySide6 on Fedora](https://packages.fedoraproject.org/pkgs/python-pyside6/python3-pyside6/), [D-Bus bridge on Fedora](https://packages.fedoraproject.org/pkgs/usbguard/usbguard-dbus/), [PySide6 on Arch](https://archlinux.org/packages/extra/x86_64/pyside6/) and [USBGuard files on Arch](https://archlinux.org/packages/extra/x86_64/usbguard/files/).

<a id="english"></a>

## Summary

Version 0.5.0 passed **117 tests per distribution** on Ubuntu 26.04, Fedora 45 and Arch rolling using native dependencies in GitHub Actions containers as a regular user. ES/EN offscreen QML rendering also passed. Ubuntu additionally installed, verified and launched the Debian package in demo mode. Fedora/Arch coverage is from source; no RPM or pacman/AUR package is distributed.

The inventory checks installed USBGuard/systemd/Polkit integration files, not running services. These jobs do not validate live desktop authentication, reboot, tray behavior, SELinux or physical USB. Native Polkit and kernel USB gadget testing belong to Kali/Xfce and Parrot/KDE. Source/wheel use requires system dependencies and does not enable the packaged-layout-only GUI autostart. Other releases, architectures and non-systemd distributions are not universally certified.

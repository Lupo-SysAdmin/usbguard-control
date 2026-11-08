# USBGuard Control

**A Linux desktop interface for deciding what you connect.**

UI developer: **Jan Herrera** · [Lupo-SysAdmin](https://github.com/Lupo-SysAdmin)

[Español](README.md) · [Kali setup](docs/INSTALL.md) · [Architecture](docs/ARCHITECTURE.md)

![USBGuard Control running with simulated devices](docs/images/usbguard-control-demo-en.png)

An independent Python / PySide6 / Qt Quick client for USBGuard. USBGuard remains responsible for device authorization and policy enforcement. This application is not affiliated with the upstream USBGuard project.

## Status

**0.1.0 alpha.** Functional demo, real D-Bus client, isolated integration tests and a Debian package. The client targets the USBGuard 1.1.4 API. Real daemon/hardware/Polkit behavior and GNOME, Plasma, Xfce, Wayland and X11 sessions still require validation. Tested headlessly in Kali 2026.3 with Python 3.14 and PySide6 6.10.3. Available in Latin American Spanish and US English.

## Features

- Searchable device list, authorization filters and device details.
- Instant **ES / EN** language switch with a saved preference, including existing session activity.
- Explicit temporary allow, persistent allow and temporary block actions.
- Protected HID/hub handling and device identity revalidation before changes.
- D-Bus events, reconnect attempts and grouped desktop notifications.
- Session activity export (up to 200 events; not a complete audit log).
- Standalone demo with simulated hotplug and policy persistence.
- No root GUI, shell commands, direct system policy writes or service activation.

## Run

Install distribution dependencies using the [setup guide](docs/INSTALL.md), then:

```bash
PYTHONPATH=src python3 -m usbguard_control --demo --language en-US
```

Use **ES / EN** in the toolbar to switch between `es-419` and `en-US` and save your preference. `--language` overrides the language for that launch only. Hardware names are never translated. External system dialogs such as Polkit follow the desktop language.

Omit `--demo` only when USBGuard is already configured. Run as a regular user. The app relies on the existing USBGuard D-Bus bridge and its Polkit policy; it never changes permissions to bypass authentication.

Kali's USBGuard package may start services during installation. Prepare and review initial rules to avoid disabling input devices; see the setup guide before installing the daemon.

## Validate and package

```bash
sh scripts/check.sh
python3 scripts/diagnose.py
python3 scripts/build_deb.py
```

Tests use an isolated bus and a mock service, never USB hardware. The package is written to `dist/usbguard-control_0.1.0-1_all.deb`. USBGuard is a suggested dependency, intentionally installed and configured separately. A GitHub Actions workflow is included but has not yet run remotely.

The [validation checklist](docs/VALIDATION.md) distinguishes completed checks from pending physical and desktop-session tests.

## Credits and license

**Jan Herrera — USBGuard Control UI developer.** Copyright © 2026 Jan Herrera.

GPL-3.0-or-later. See [LICENSE](LICENSE), [AUTHORS](AUTHORS), [NOTICE](NOTICE) and the [license rationale](docs/LICENSING.md). Attribution applies to this independent interface; USBGuard, Qt, PySide6 and their dependencies retain their respective ownership and licensing. Distributed without warranty.

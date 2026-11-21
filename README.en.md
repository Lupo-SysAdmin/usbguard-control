# USBGuard Control

[![Linux validation](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml/badge.svg)](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml)

**A Linux desktop interface for deciding what you connect.**

UI developer: **Jan Herrera** · [Lupo-SysAdmin](https://github.com/Lupo-SysAdmin)

[Download stable release](https://github.com/Lupo-SysAdmin/usbguard-control/releases/latest) · [Español](README.md) · [Kali setup](docs/INSTALL.md) · [Architecture](docs/ARCHITECTURE.md)

![USBGuard Control running with simulated devices](docs/images/usbguard-control-demo-en.png)

An independent Python / PySide6 / Qt Quick client for USBGuard. USBGuard remains responsible for device authorization and policy enforcement. This application is not affiliated with the upstream USBGuard project.

## Status

**Stable version 0.5.0.** Combines the features introduced in 0.3.0 with validated text editing and before/after matching for device-specific rules. Download the `.deb` from [Releases](https://github.com/Lupo-SysAdmin/usbguard-control/releases/latest).

Validated on real **Kali 2026.3 / Xfce 4.20.4 / X11**, and **Parrot 7.4 / KDE Plasma 6.3.6 / Wayland** desktops. Version 0.5.0 checks covered package upgrades, the UI, native authenticated text editing and test USB reconnects. Observer startup after reboot/sign-in and GNOME UI/observer coverage belong to 0.3.0 and remain documented separately; the host package is still 0.2.0. The VM named “Kali 2026.1” now runs 2026.3; previous 0.2.0 results on 2026.1 remain historical evidence.

See [0.5.0 validation and scope](docs/VALIDATION-0.5.md) and [features and limits](docs/FEATURES-0.5.md).

## Features

- Searchable device list, authorization filters and device details.
- Instant **ES / EN** language switch with a saved preference, including existing session activity.
- Explicit temporary allow, persistent allow and temporary block actions.
- Protected HID/Bluetooth/hub handling and device identity revalidation before changes.
- D-Bus events, reconnect attempts and grouped desktop notifications.
- Ordered policy browser, custom names, guided allow/block editing and revocation of device-specific rules.
- Device-specific text editor with normalized previews, before/after matches, stable drafts and fixed identity attributes.
- Previews, policy revalidation, mandatory backups and selective recovery of missing device-specific rules.
- Persistent local history with 7/30/90-day retention, search/date filters and JSON/CSV export with optional detail redaction.
- Service and connection diagnostics, optional iPhone pairing validation, and a guided setup checklist.
- Light/dark/system themes, saved preferences and window size.
- Optional background observer, notification activation, single instance and packaged-app sign-in startup.
- Standalone demo with simulated hotplug and policy persistence.
- Settings with wrapped text and scrolling, explicit service start/stop, and optional startup persistence through systemd and Polkit.
- No root GUI, shell commands, direct system policy writes, or implicit service activation.

## Run

Install distribution dependencies using the [setup guide](docs/INSTALL.md), then:

```bash
PYTHONPATH=src python3 -m usbguard_control --demo --language en-US
```

Use **ES / EN** in the toolbar to switch between `es-419` and `en-US` and save your preference. `--language` overrides the language for that launch only. Hardware names are never translated. External system dialogs such as Polkit follow the desktop language.

Omit `--demo` only when USBGuard is already configured. Run as a regular user. The app relies on the existing USBGuard D-Bus bridge and its Polkit policy; it never changes permissions to bypass authentication.

In Settings, **Remember this choice at system startup** makes Start enable both USBGuard services at boot and Stop disable their automatic startup. Uncheck it to change only the current state. Every operation requires confirmation and may request desktop authentication. Current and startup states are read from systemd, including after partial failures. Masked, missing, or specially configured units require manual setup. Stopping USBGuard preserves saved rules and does not necessarily unblock connected devices. Opening or closing the app does not change the service state.

Kali's USBGuard package may start services during installation. Prepare and review initial rules to avoid disabling input devices; see the setup guide before installing the daemon.

## Validate and package

```bash
sh scripts/check.sh
python3 scripts/diagnose.py
python3 scripts/build_deb.py
```

Tests use an isolated bus and a mock service, never USB hardware. The package is written to `dist/usbguard-control_0.5.0-1_all.deb`. USBGuard is a suggested dependency, intentionally installed and configured separately. GitHub Actions runs tests and packaging on Debian for each push. See the [CI results](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml).

The [0.5.0 validation report](docs/VALIDATION-0.5.md) distinguishes automated, real-desktop, VM USB, and historical physical-device evidence.

## Credits and license

**Jan Herrera — USBGuard Control UI developer.** Copyright © 2026 Jan Herrera.

GPL-3.0-or-later. See [LICENSE](LICENSE), [AUTHORS](AUTHORS), [NOTICE](NOTICE) and the [license rationale](docs/LICENSING.md). Attribution applies to this independent interface; USBGuard, Qt, PySide6 and their dependencies retain their respective ownership and licensing. Distributed without warranty.

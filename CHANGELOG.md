[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](CHANGELOG.es.md)

# Changelog

## 0.5.0 — 2026-11-21

- Consolidates the history, diagnostics, background, guided assistant and backup functions introduced in 0.3.0.
- Text editor for specific rules: normalized formatting, before/after comparison of current matches, stable draft and restoration of initial text.
- Preserves VID:PID, serial number, fingerprint and interfaces; rejects broad rules, conditions, unknown syntax, controls, and reserved tags.
- Revalidate both matches before confirming; maintains mandatory backup, priority and partial change notices.
- The demo also evaluates port, parent, name, serial, interfaces and connection type. The connection type is incorporated into the verified identity.
- 117 automated tests, documentation and ES/EN captures. The actual scope of this version is recorded in docs/VALIDATION-0.5.md.
- CI matrix with native dependencies and normal user in Ubuntu 26.04, Fedora 45 and Arch rolling: 117 tests per system. Ubuntu also verifies installation and startup of `.deb`; Fedora/Arch are validated from code, without promising native packages or desktop/hardware testing.

## 0.3.0 — 2026-11-21

- Guided rule management over D-Bus with preview, policy identity checking and mandatory backup.
- Selective recovery of specific rules; advanced rules, HID, Bluetooth and protected hubs.
- Local aliases, device composite functions and explanation of the origin only when it was observed.
- Private SQLite history, configurable retention, filters and JSON/CSV export with privacy.
- Guided diagnosis and pairing verification of the iPhone without modifying it.
- Light/Dark/System themes, persistent preferences, background watcher, single instance and optional startup at sign-in.
- New dependency on QtWidgets and QtNetwork for desktop integration.
- Real validation in GNOME/Wayland, Xfce/X11 and KDE/Wayland; authenticated policy operations, test USB reconnection, reboot/login, single instance and package reinstallation on VMs.
- Advance warning about various operations and possible partial changes when canceling a subsequent authentication. Release 0.2.0 is preserved as history.

## 0.2.0 — 2026-11-09

- First stable release, promoted from `v0.2.0-rc.1` with no changes to the app code. Updated documentation and metadata; The documented scope and validation limits are preserved.

- Publishing on GitHub and CI on Debian minimum; Qt SVG dependency explicitly declared upon first remote execution.

- Unicode/escaped USB descriptors interpreted according to the daemon protocol; without double decoding of literal backslashes and with regressions for malformed inputs.
- Rows of devices accessible via Tab/Space, moving to focus and error messages accessible via keyboard.
- Automatic queries preserve action errors so they can be read; connection recovery and manual update clean them up.
- Basic style also initialized for the Qt file selector.
- Additional KDE authentication validation, 40 USB events grouped into 10 notifications and special names using USB emulated in the kernel.

- Validation in KVM VMs: Kali 2026.1/Xfce/X11 and Parrot 7.4/KDE/Wayland, installation/uninstallation, real service controls, reboots and recovery.
- QML controls with explicit Basic style to avoid geometry loops introduced by Breeze in KDE.
- Accessible box labels and improved contrast of main buttons; keyboard regressions and accessibility in ES/EN.
- Debian launcher with `-B`: does not generate root-owned Python cache left after uninstall.
- Silent auto-query every five seconds, without fading controls or re-notifying details that haven't changed; Clicks during the query are processed in order.

- Configuration with multi-line boxes, limited width and scrolling in small windows.
- Explicit controls for starting and stopping USBGuard and its D-Bus bridge, with systemd/Polkit confirmation and authentication.
- Optional choice persistent on boot; execution and boot states consulted separately.
- Verification of jobs, detection of external changes and partial errors, without removing masks or modifying USB rules.
- Complete simulated service flow, ES/EN translations and isolated D-Bus transport tests.

## 0.1.0 — 2026-11-08

- First Qt Quick interface in Latin American Spanish and American English authored by Jan Herrera.
- ES / EN selector with immediate change and saved preference.
- Isolated demo, filters, details, confirmations and exportable activity.
- D-Bus client for USBGuard 1.1.4 and integration tests with simulated service.
- Restrictions for sensitive devices and identity revalidation.
- Additional restriction for Bluetooth adapters that can carry keyboard or mouse.
- Success notices expire and are removed when they no longer match the current status; Disconnecting one device does not automatically select another.
- Bilingual documentation, GPL-3.0-or-later, Debian package and CI flow.
- First physical validation in Kali/GNOME with iPhone and mouse receiver: temporary authorization, persistence and reconnections.
- Alpha status: full reboot, recovery, other desktops and publishing pending.

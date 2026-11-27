[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](VALIDATION.es.md)

<a id="validación-y-límites-de-la-versión-020"></a>

# Validation and limits of version 0.2.0

<a id="publicación-estable--9-de-noviembre-de-2026"></a>

## Stable publication — November 9, 2026

Release `v0.2.0` promotes candidate `v0.2.0-rc.1` with the same application code, tests, CI configuration, and packaging logic. Changed release documentation and Python package rating to stable. The scope and limitations described herein remain unchanged; This promotion does not add new physical tests or modify the installation on the development computer.

<a id="resultado-local--8-de-noviembre-de-2026"></a>

## Local result — November 8, 2026

- **62 automated tests passed** with the `scripts/check.sh` suite on Kali 2026.3, Python 3.14.8 and PySide6 6.10.3; They include Bluetooth regressions, outdated prompts, keyboard, accessible names, and main button contrast.
- Refresh regression: identical queries without visual changes, manual prompt preserved, device/service/update clicks during query, actual changes, disconnection and recovery from errors.
- Measuring two automatic cycles against real USBGuard, on an invisible instance: five second interval, 100% button opacity, same selected data, and no redundant visual notifications. No rules or services were changed.
- Verified service controls against a simulated systemd on a private bus: real signatures, interactive authentication, start/stop order, optional persistence, cancel/deny, external changes, failed jobs and partial failures.
- Configuration rendered in ES/EN at 1040x780 and 900x620; checking the width and height of the text in the boxes, and the stop/start flow with the simulated connection closed.
- Screenshots rendered from QML in Latin American Spanish and American English; Visual overhaul of normal, compact window and dialogs.
- `.desktop` launcher validated and `.deb` built without privileges.
- Open demo from content extracted from `.deb` using isolated Python; package not installed on the system.
- Built source and wheel distributions; sums in `dist/SHA256SUMS`.
- Three deprecation warnings come from PyGObject/asyncio in Python 3.14; There were no test failures or QML warnings in the tested flow.

Isolated testing is not a substitute for the physical validation described below. GitHub Actions runs the suite and packaging on Debian trixie; its status is available at [CI](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml). The first run found that declaring `qt6-svg-plugins` was missing to load the SVG icon in a minimal install. Added to CI, `.deb` and guide; testing was not relaxed.

<a id="primera-instalación-en-el-equipo-de-desarrollo"></a>

### First installation on the development computer

On November 8, 2026, the `0.1.0-1` interface was installed using APT along with USBGuard `1.1.4+ds-10`, with Polkit authentication. Four packages were added, with no updates or removals. The `inactive/masked` services were first maintained to prepare the rules. The interface was opened as a normal user in GNOME Shell 50.4/Wayland.

With explicit user approval, GNOME USB management was delegated to USBGuard (`usb-protection=false`; previous value `true`, level `lockscreen`). The configuration was backed up outside the repository and device-specific rules were installed for internal devices. No Polkit exceptions were added. Corrected misplaced recovery conditions on the packaged unit via drop-in. Services ended up `active/enabled`.

Results observed by the real API and confirmed by the user:

| Test | Result |
|---|---|
| New iPhone, no rule | Blocked |
| “Allow now” from the interface | Allowed |
| Reconnect after temporary authorization | Blocked again |
| Mouse receiver, device-specific permanent rule | Automatically allowed on reconnect |
| iPhone, permanent rule requested after temporary test | Automatically allowed on reconnect |
| Internal Bluetooth adapter | It remained authorized; blocking it is now restricted in the GUI |
| Effective policy | New devices: evaluate rules; no match: block |
| GNOME General Rules | GNOME General Authorization Rule Not Found |

The keyboard mentioned works over Bluetooth and was not listed as a USB keyboard because of its cable; It is not presented as a USB keyboard test. The physical equipment was not restarted. Reboots, recovery, and install/uninstall were then tested on VMs, as described below. No personal hardware serial numbers, hashes, or rules are published in the repository.

<a id="acceso-a-documentos-del-iphone"></a>

### Access to iPhone documents

After testing permanent authorization, Files displayed `Unhandled Lockdown error (-21)` when opening the phone's documents. The actual check confirmed the device and its interfaces authorized, with USBGuard and usbmuxd active. `libimobiledevice-utils` and its dependency `libtatsu0` were installed, without updating or removing existing packages.

With the phone unlocked, `idevicepair validate` finished successfully and GVfs responded to the document root folder query. The user confirmed that he was able to open it again without the error. No USB rules were changed and no unpairing was performed. This check distinguishes USB authorization from document access; It does not show access to all files or persistence of pairing after reboot.

<a id="automatizable-sin-hardware"></a>

## Automated checks without hardware

- Analyze snapshots with names in quotes and composite interfaces.
- Restrict HID blocking, Bluetooth adapters, hubs and unknown interfaces.
- Reject different identities, obsolete IDs and disconnected devices.
- Distinguish persistence and temporary authorization in the simulation.
- Verify real D-Bus signatures, interactive authentication flag and denials.
- Receive presence signals on a private bus.
- Do not assume a blocking policy when it cannot be consulted.
- Load QML and complete search, confirmation, authorization, reconnection and export.
- Switch between Latin American Spanish and American English without restarting; check translations, variables and saved preference.
- Render a real screenshot of demo mode.
- Build and inspect the `.deb` and validate the desktop launcher.

Run `sh scripts/check.sh`. The D-Bus test uses a simulated service; it does not validate actual kernel decisions or authentication of a Polkit agent.

<a id="pruebas-en-máquinas-virtuales-kvm--8-de-noviembre-de-2026"></a>

## Testing on KVM virtual machines — November 8, 2026

Created a Kali snapshot and a verified full backup of the Parrot UEFI disk and firmware before modifying the VMs. Physical equipment protection remained active. Empty virtual USB disks were used; the host's mouse, keyboard, and iPhone were not redirected.

| Real environment | Verified versions | Result |
|---|---|---|
| Kali 2026.1, Xfce 4.20.3, X11 | Python 3.13.9; PySide6 6.11.2; USBGuard 1.1.4+ds-10 | Passed Installation, GUI, Authentication, Virtual USB and Recovery |
| Parrot 7.4, KDE Plasma 6.3.6, Wayland | Python 3.13.5; PySide6 6.8.2.1; USBGuard 1.1.3+ds-3 | Passed Installation, GUI, Actual API, Boot, Events and Connection Recovery |

The name of the Parrot VM was "Parrot 7.2", but `/etc/os-release` reports 7.4. The Kali VM retains its 2026.1 identity; installing dependencies from kali-rolling is not equivalent to validating a clean installation of Kali 2026.3.

| Test | Observed evidence |
|---|---|
| `.deb` without daemon, both VMs | The interface opens and shows absence of the service without installing or starting it |
| Uninstall/reinstall, both VMs | Launcher, menu and application files are removed; no rules or daemon are modified |
| Complete installer | Both services are inactive/masked before reviewing the rules |
| Installer over existing USBGuard | Explicit rejection; preserved configuration |
| Xfce Graphics Controls with Real Polkit | Start/stop with and without remembering: four combinations verified as a normal user |
| KDE Graphics Controls with Real Polkit | Start/stop with and without remember: four verified combinations; When both services are finished, they remain active/enabled |
| Polkit Xfce Cancellation | Native dialog is cancelled; both services retain `active/enabled` |
| Startup after reboot, both VMs | Units active/enabled after reboot |
| Boot disabled, Kali | Units inactive/disabled after reboot |
| Recovery, Kali | With the correct drop-in conditions and `usbguard=0`, the daemon does not start; parameter removed, restart normally |
| Virtual USB, Kali | New locked in kernel; temporary permission expires upon reconnection; persistent permission survives reconnection and four reboots |
| Revocation, Kali | Only the rule is removed from the test disk; reconnect produces again `authorized=0` |
| Daemon restart, Kali | A confirmation with old D-Bus owner is rejected; persistent rule remains |
| Two simultaneous clients, Parrot | Both see connection, external authorization and disconnection from the same virtual USB |
| Withdrawal with open confirmation, Parrot | The operation is rejected; does not apply to another device or preserve an obsolete selection |
| Bridge disruption, Parrot | Both clients detect the loss and recover connection when restoring `usbguard-dbus` |
| Notifications, Parrot | The native service accepts connect/disconnect notifications without errors |
| Real background refresh, Parrot | Two initial automatic queries without selection changes or busy status |
| ES/EN and scale | 900x620 logical window at 100%, 150% and 200%; KDE tested with virtual 1920x1440 output to avoid compositor clipping |
| Accessibility | Names/roles/checkbox and keyboard status in Qt; checkbox exposed by AT-SPI from another process in both languages ​​|
| Orca 48.1 Reader, Parrot | Its voice output register announces the checkbox name and state when focusing/changing it in ES/EN; also processes the Settings |

The daemon read must be run from an active local session. A process administratively launched with `runuser` can be considered dead by Polkit even though it has `DISPLAY`: it was verified for rejection and then for successful access from the real Xfce and KDE launchers, without changing authorization policies. The Orca test checked recorded speech generation, not a human evaluation of pronunciation; the reader's terms followed desktop English.

<a id="pruebas-adicionales-de-eventos-y-nombres-usb"></a>

### Additional testing of USB events and names

Four emulated USB storage devices were created in Parrot with `dummy_hcd` and `libcomposite`, empty read-only images and unique test serial numbers. The path was USB descriptor → kernel → USBGuard daemon → D-Bus → GUI; no backend responses were simulated. No permanent rules were added for these devices. When finished, the four gadgets and `dummy_hcd` were removed; the three initial virtual USBs were checked, rules intact and both services active/enabled.

- Five cycles of disconnecting/reconnecting four devices produced **40 presence events and 10 grouped notifications**, accepted by the desktop service without errors. Two clients observed the correct states and removed the disconnected selections.
- Checked accents, eñe, CJK characters, quotes, backslashes, HTML-like text and a bidirectional control. The names match the descriptors; the HTML remains literal and the two-way control is removed from the presentation only. The original identity is preserved to revalidate operations.
- Testing found that the previous parser preserved USBGuard `\xHH` escapes as text. Fixed to reconstruct the UTF-8 bytes exactly once, without interpreting literal escapes again. Thirteen regression cases cover valid and malformed inputs.

<a id="recorrido-completo-de-teclado-y-orca"></a>

### Full Keyboard and Orca Walkthrough

Completed nine sets of checks in each language using Orca 48.1 and the GUI as a normal user in KDE: Search, Selection/Filters, Temporary Allow and Cancel, Block/Persistent Allow, Device Removal Failed, Activity, File Picker Export, Service Configuration/Confirmations, and About. The actions in this review use demo mode; actual service and USB operations were validated separately above.

The walkthrough uses Tab, Space, Escape, Ctrl+F, and file name editing. The exported JSONs were checked for content and language. The voice logs contain device names, controls, confirmations, error, preferences and dialogs in both languages. It is not an accessibility certification nor a human evaluation of pronunciation or of each text flat review. Orca's file selector and terms follow the desktop language; In Qt 6.8 its name field was announced as "text", without repeating the visual label.

Orca and Qt 6.8's AT-SPI bridge issued warnings about accessible object paths removed during model changes; walkthroughs and voice checks completed successfully. This limit is preserved, without presenting the logs as warning-free. There were no QML warnings on the final runs.

<a id="correcciones-detectadas-por-estas-pruebas"></a>

### Fixes detected by these tests

- The launcher now avoids generating Python bytecode; uninstalling leaves the application directory clean even after trying to run it as root.
- Explicitly importing `QtQuick.Controls.Basic` preserves the layout and removes the Breeze theme geometry loops seen in KDE. [Qt Style Selection](https://doc.qt.io/qt-6.8/qtquickcontrols-styles.html).
- Device rows now receive Tab focus and scroll until visible. Errors retain their text during automated queries and can be focused; Qt 6.8 or higher also receives an accessibility announcement. Manual update and connection recovery clears the error.
- `QQuickStyle.setStyle("Basic")` is applied after creating the application: KDE was overriding the environment preference and mixing Breeze in the file chooser. Added dependency `python3-pyside6.qtquickcontrols2` to package, installation, and CI.
- Custom checkboxes expose their accessible names. Main button text contrast changed from 3.67:1 to 4.68:1; The test measures the colors of the rendered control. This verifies that pair of colors, it does not certify the entire application. [W3C Contrast Criterion](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum).

There were no QML warnings in the final walkthroughs after fixing KDE; AT-SPI warnings are detailed above. The Parrot VM issued EGL warnings for its virtual adapter and rendered correctly; It is not presented as a validation of all GPUs. The recovery tested breaks the USBGuard bridge, it does not restart the entire desktop D-Bus. Parrot's systemd operations were also tested by the administrative API; interactive positive authentication of buttons was verified in Xfce and KDE, as a normal user and without Polkit exceptions.

<a id="cobertura-y-comprobaciones-adicionales"></a>

## Coverage and additional checks

- [x] Install and uninstall `.deb` in VMs without USBGuard prior control (Kali 2026.1 and Parrot 7.4).
- [x] Support for Kali 2026.3 (host) and Kali 2026.1 (VM), accepted as the scope of this release; another clean VM 2026.3 is not required.
- [x] Check basic flow in GNOME Shell 50.4/Wayland with real devices.
- [x] Verify KDE Plasma/Wayland and Xfce/X11 in real sessions.
- [x] Validate scaling 100%, 150% and 200%, keyboard navigation and main button contrast.
- [x] Check names, roles and states accessible in ES/EN using Qt and AT-SPI.
- [x] Test focus and launch box announcement with real Orca in ES/EN.
- [x] Browse search, selection, confirmation/cancel, errors, activity/export, configuration/services and About with keyboard and Orca in ES/EN, within the scope described below.
- [x] Prepare rules and run authorizations with real USBGuard 1.1.4 and Polkit policy installed.
- [x] Verify temporary and persistent permission through physical reconnections.
- [x] Verify full boot after reboot, recovery and subsequent revocation in VM.
- [x] Deny/cancel Polkit, remove the device with the dialog open and restart the daemon.
- [x] Check for explicit delegation from GNOME to USBGuard without general authorization rule.
- [x] Verify external authorization changes and two simultaneous clients in a session.
- [x] Confirm delivery of notifications and recovery after interruptions of the D-Bus bridge.
- [x] Validation on three computers: Kali host and Kali/Parrot VMs. Sessions of different users are outside the agreed scope; They are not confused with different equipment.
- [x] Check multiple device connect/disconnect bursts and notification grouping.
- [x] Check unicode/escaped names using emulated USB descriptors in the kernel and real USBGuard; it is not attributed to physical hardware with those names.
- [x] Verify positive authentication of service buttons in KDE with the four run/boot combinations.
- [x] Review screenshots, README, licenses, corresponding source and sums before uploading artifacts.

<a id="alcance"></a>

## Scope

The window shows session activity, not a persistent audit history. It does not contain a rule editor, global authorization, graphical revocation or automatic privilege configuration. Explicit service controls are not the same as allowing all devices. Demo mode does not test the daemon. HID protection of this interface cannot prevent another tool from modifying the same device.

Real authenticated stop/start and restarts were verified within the VMs. Protection on the development computer was not restarted or stopped during these tests. Unicode/escaped name checks use emulated USB descriptors that traverse the actual kernel and daemon; They are not attributed to physical hardware with Unicode names.

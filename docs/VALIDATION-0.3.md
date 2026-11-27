[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](VALIDATION-0.3.es.md)

<a id="usbguard-control-030--validación--validation"></a>

# USBGuard Control 0.3.0 — Validation

Date: **November 21, 2026**. Developer: **Jan Herrera**.

<a id="entornos-y-alcance"></a>

## Environments and scope

| Real environment | Execution | Result |
|---|---|---|
| Host Kali 2026.3, GNOME Shell 50.4, Wayland | New version code, normal user, separate configuration/test history | Navigation, ES/EN, light/dark, close to background and reopen with single instance |
| VM Kali 2026.3, Xfce 4.20.4, X11, USBGuard 1.1.4, PySide6 6.11.2 | Debian package installed, active user session | Interface, policy with Polkit, test USB, persistence, installation and session boot |
| VM Parrot 7.4, KDE Plasma 6.3.6, Wayland, USBGuard 1.1.3, PySide6 6.8.2.1 | Debian package installed, active user session | Interface, policy with Polkit, test USB, persistence, installation and session boot |

The VM name "Kali 2026.1" was retained, but `/etc/os-release` reports **2026.3** after its updates. It is not presented as a new test of 0.3.0 on Kali 2026.1. The physical and compatibility results from 0.2.0 are preserved in [VALIDATION.md](VALIDATION.md).

<a id="pruebas-completadas"></a>

## Tests completed

- **91 automated tests**: demonstration and isolated D-Bus; contracts and API errors, identity, sensitive rules, stale policy, failed backup, partial change, recovery, preferences, retention, export privacy, single instance and translations. The CI runs on Debian trixie.
- Visual tour of the four pages in Latin American Spanish and American English, with light and dark themes. No QML errors in the tours. Revised captures and scrollable controls.
- Installing the package over 0.2.0 preserved the policy. Uninstalling and reinstalling preserved rules, preferences, and history and left both services active. `dpkg --verify usbguard-control` passed.
- Each VM used four test USB storage devices created with `dummy_hcd`/`libcomposite`, with empty read-only images and names with Unicode, quotes, backslash, HTML-like text, and bidirectional control. Its reading and visual sanitation were verified.
- From the normal user application, **editing, removing, and restoring a device-specific rule** requested native authentication. The password was entered into the VM. Polkit rules were not changed to grant access without authentication.
- The allow→block edit was saved to disk, kept the current authorization and blocked when reconnecting the device. Removal and recovery from JSON preserved the connected state; after recovering, reconnection allowed it again.
- Backups were created before each write. Canceling Polkit in Xfce preserved the policy and showed the authorization error. A cancellation after the first editing stage also exercised the case of partial change; the interface warns of this limit before confirming.
- History and preferences survived closure and reopening. The SQLite file had `0600` permissions. Retention, filtering by date and hiding exports are additionally checked in the automated suite.
- Closing to background and reopening did not create two observers. Verified in GNOME/Wayland, Xfce/X11 and KDE/Wayland.
- On both VMs, after **reboot and login**, the XDG entry booted the package with `--background` as the normal user. Reopening it reused the same PID. USBGuard and the D-Bus bridge remained active.
- Test rules and gadgets removed. The content of `/etc/usbguard/rules.conf` again exactly matched its previous hash. The autostart input created for the test was removed, retaining the previous choice.

<a id="límites-y-observaciones"></a>

## Limits and observations

- The host's stable package was not replaced nor were its services or rules modified. The GNOME test used the code from the new version; installing and starting XDG after reboot was tested on Xfce and KDE.
- The USBs in this round are kernel devices inside the VMs, not a repeat of physical tests with iPhone, keyboard or mouse. iPhone file integration also requires unlocking, trust, and mounting support.
- Available trays were verified in these sessions. Notification actions and a GNOME without a tray extension may vary with the notification server; reopening from the launcher remains available.
- Compatibility with all desktops/versions or a full security audit is not promised. The editor protects input/infrastructure rules and advanced syntax; see [functions and limits](FEATURES-0.3.md).
- D-Bus writes are not atomic. Canceling a subsequent authentication may leave an added rule; partial changes are reported and the backup is preserved. An automatic rollback that can overwrite external changes is not applied.
- Observed non-fatal Xfce portal warnings and EGL warnings in the KDE VM in the test harness. Windows rendered and normal package opened after login. The local suite retains three PyGObject/asyncio deprecation notices.

<a id="english"></a>

## Summary

Version 0.3.0 was tested in real GNOME/Wayland, Xfce/X11, and KDE/Wayland sessions. GNOME used the new source with separate test data and did not replace the host package. Installed Debian-package tests ran on Kali 2026.3/Xfce and Parrot 7.4/KDE, including native Polkit rule editing/removal/recovery, kernel USB gadget reconnects, private persistent history, remove/reinstall, and automatic observer startup after reboot and sign-in. Launching again reused the same process. Test gadgets/rules were removed and original policy hashes restored.

The automated suite contains 91 tests and runs in Debian CI. VM USB gadgets are not new physical iPhone/keyboard/mouse certification. The VM still named “Kali 2026.1” now runs Kali 2026.3. Notification behavior and unsupported desktops are not universally certified. Multi-step D-Bus operations can leave partial changes when later authentication is canceled; previews warn of this and backups are retained. Prior physical-device evidence belongs to the separately documented 0.2.0 release.

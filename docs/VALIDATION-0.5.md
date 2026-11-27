[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](VALIDATION-0.5.es.md)

<a id="usbguard-control-050--validación--validation"></a>

# USBGuard Control 0.5.0 — Validation

Date: **November 21, 2026**. Developer: **Jan Herrera**.

<a id="entornos-de-esta-versión"></a>

## Environments of this version

| Environment | Package and session | New tests |
|---|---|---|
| Kali 2026.3, Xfce 4.20.4, X11, USBGuard 1.1.4, PySide6 6.11.2 | Update 0.3.0 → 0.5.0, normal user | Interface, editor with Polkit, scope change, reconnection and recovery |
| Parrot 7.4, KDE Plasma 6.3.6, Wayland, USBGuard 1.1.3, PySide6 6.8.2.1 | Update 0.3.0 → 0.5.0, normal user | Interface, editor with Polkit, scope change, reconnection and recovery |

The VM named “Kali 2026.1” is currently running Kali 2026.3. No new test is declared regarding 2026.1. The host maintains package 0.2.0: its policy has not been replaced or changed.

<a id="automatización"></a>

## Automation

- **117 tests passed** in the local suite, with three existing PyGObject/asyncio deprecation notices. The tests do not use the system bus or physical USB.
- New cases for normalization, UTF-8 escapes, fixed identity attributes, broad or invalid rules, checks, reserved tags, and formatting-only changes.
- Read-only preview, before and after matches, switching sensitive devices between preview and commit, stale policy, mandatory backup, position and partial changes.
- Isolated D-Bus contract for the replacement operation.
- Complete QML flow: validation error, draft preserved during update/language/theme/selection change, captured ID, cancel comparison and commit. No QML warnings at 900×620.
- ES/EN demos, launcher validation and construction of the `.deb`. GitHub Actions runs the same suite on Debian trixie; its results are in [CI](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml).

<a id="pruebas-con-el-paquete-y-escritorios-reales"></a>

## Testing with the package and real desktops

In addition to the Debian suite, **Ubuntu 26.04, Fedora 45 and Arch rolling passed 117 tests each** on GitHub Actions with native dependencies and unprivileged user. Ubuntu passed installation, integrity and opening of `.deb` in demo mode. These containers are not desktops or hardware: see [inventory and compatibility scope](COMPATIBILITY.md).

- The update preserved the policy of both VMs. All four pages rendered in ES/EN and light/dark without QML errors. Closing to background, reopening with single instance, creation/removal of XDG entry and backup export were checked.
- Used kernel USB storage devices with `dummy_hcd`/`libcomposite`, empty read-only images and special names. They are not physical peripherals.
- The editor rejected a wildcarded VID:PID before writing. The valid draft added a port restriction and a label. The preview showed one matching device before and none after, without changing the policy.
- Saving from the normal session prompted Polkit to add the substitution and remove the old rule. The text returned by USBGuard matched the normalized format in both versions of the daemon. Position, number of rules and authorization of the connected device were preserved.
- When reconnecting the test USB, the persisted restriction blocked it. On both VMs, removing that restriction from the editor preserved the current locked state and re-allowed it upon reconnection. Backups of every edit were preserved.
- Both VMs were left without test rules or gadgets; their original policy hashes matched exactly and both services remained active and enabled. The autostart entries created by the test were removed.
- The first recovery attempt on Parrot showed a partial changes notice during authentication. Subsequent checking found replacement complete and reconnection correct. That evidence was preserved and only the recovery was repeated: it finished without errors with native authentication and successful reconnection. The first interface result was not hidden or declared successful.

<a id="evidencia-heredada-y-límites"></a>

## Legacy evidence and limits

History, diagnostics, guided assistant, backups and background functions come from 0.3.0. Its testing of **GNOME/Wayland, uninstall/reinstall, reboot, and automatic startup at sign-in** is documented in [VALIDATION-0.3.md](VALIDATION-0.3.md); They are not presented as new tests of 0.5.0. iPhone, keyboard and mouse physical tests belong to [0.2.0](VALIDATION.md).

The new editor supports only specific rules with fixed identity; not all USBGuard grammar. The comparison considers the devices connected at that time. D-Bus add/remove operations are not atomic and a subsequent denial may leave partial changes. The wizard remains a guide and backups recover rules selectively, without replacing the entire system configuration. See [functions and limits](FEATURES-0.5.md).

<a id="english"></a>

## Summary

The local suite passed **117 tests**, including bounded rule text validation, read-only before/after previews, stale-policy and sensitive-device checks, mandatory backups, partial-write handling and the full bilingual QML editor flow. Three existing PyGObject/asyncio deprecation warnings remain. Debian CI runs the same checks.

Installed-package upgrade and UI checks ran in real Kali 2026.3/Xfce/X11 and Parrot 7.4/KDE/Wayland sessions. Both daemons accepted the normalized replacement through native Polkit, preserved the connected device authorization and blocked the kernel USB test device on reconnect when its new port constraint did not match. Both VMs also passed authenticated constraint removal, allowed reconnect and exact baseline-policy restoration. The first Parrot recovery attempt reported partial changes during authentication, although the final policy was later found complete. That evidence was retained; a focused repeat passed without errors.

GNOME, remove/reinstall and reboot/sign-in evidence belongs to 0.3.0, and physical peripherals to 0.2.0. The host package remains unchanged. No universal desktop, full-grammar, atomic-edit or automatic system-setup guarantee is implied.

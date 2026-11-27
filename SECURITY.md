[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](SECURITY.es.md)

<a id="seguridad"></a>

# Security

USBGuard Control is a standalone USBGuard client. It does not certify devices, detect malware, or replace USBGuard. USB attributes can be spoofed. Authorizing a device allows its interfaces to interact with the computer.

The GUI process runs without root. It does not directly modify rules or install general Polkit exceptions. The upstream engine preserves authorization and persistence. Service controls use systemd D-Bus and your existing Polkit policy, only for `usbguard.service` and `usbguard-dbus.service`, after explicit confirmation. Opening the application or checking statuses does not start USBGuard.

Service and boot changes require multiple operations and are not atomic. A cancellation or error may leave partial changes; the interface queries the status again and does not report success without checking the result. It does not remove administrative masks, generate initial rules, or replace units. Stopping the daemon does not guarantee unlocking devices; starting it applies existing rules and may affect peripherals without an appropriate rule.

Decisions require confirmation and a new identity query. The USBGuard API does not offer atomic comparison and application; There is a window between both operations. Blocking input devices, USB Bluetooth adapters and hubs is restricted from this version.

Since version 0.3, the observer saves a local SQLite history (file 0600), with retention of 7/30/90 days and up to 10000 records; the view shows up to 2000. Rule backups are saved before each edit and may contain personal identifiers. Demo mode does not create persistent history. Exports offer to hide event details; backups retain the entire policy loaded and are not anonymous. There is no telemetry or automatic network connection. External links are opened only from explicit buttons. Exports can contain device names.

Before reporting a problem, remove serial numbers, hashes, and personal data from the logs. The repository does not yet have a private reporting channel configured. Don't post exploitable details or secrets in public issues; coordinate a channel with maintainer [Jan Herrera](https://github.com/Lupo-SysAdmin) before sharing them.

<a id="gestión-guiada-de-reglas-03"></a>

## Guided rule management (0.3)

Only specific rules with VID:PID, fingerprint and known interfaces are edited, excluding HID, Bluetooth and hubs. The D-Bus policy and service owner are re-read before writing. This is not an atomic transaction: other administrators can modify the policy between operations. An error after a write is reported as a partial change and preserves the backup; success is not declared without rereading the result.

Recovery adds the missing specific rules to the end as permanent, skipping protected/advanced rules. It does not replace the entire policy or restore daemon configuration, permissions, or systemd units. The previous rules retain priority. The D-Bus listing does not report the persistence of each rule: it is presented as a loaded policy, not as proof that all its entries are saved on disk.

Login creates only the user's XDG entry for this application. The single instance uses a local user access socket and a process lock. Closing the observer does not modify services or rules. iPhone integration only runs `idevicepair validate`, without pairing or installing packages; its detailed output is not exported.

<a id="editor-de-texto-05"></a>

## Text editor 0.5

The editor normalizes only specific rules with fixed identity (VID:PID, serial number, fingerprint and interfaces). It does not support conditions, wildcards or various rules. The previous rule and the proposed rule are checked for matches and revalidated before writing. The predicate is queried to the daemon without mutation; writes maintain authentication, mandatory backup, and partial change detection. An atomic transaction is not promised.

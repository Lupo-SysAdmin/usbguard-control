[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](INSTALL.es.md)


<a id="instalación-y-prueba-en-kali"></a>

# Installation and testing in Kali

Initial objective: Kali 2026.3. The candidate revision observed on November 8, 2026 is `usbguard 1.1.4+ds-10`; always check `apt policy usbguard` on your computer. The package includes `usbguard-dbus` and its systemd unit; There is no need to install another package called `usbguard-dbus` in this revision.

Historical testing of 0.2.0 included install/uninstall on Kali 2026.1/Xfce and Parrot 7.4/KDE. The Kali VM is now running 2026.3. The 0.5.0 update and editor were tested on both VMs; see [current validation](VALIDATION-0.5.md). Parrot retains `1.1.3+ds-3`; Their packages were not replaced with Kali ones. The [compatibility matrix](COMPATIBILITY.md) distinguishes additional automated testing on Ubuntu, Fedora, and Arch. These APT instructions are for supported Kali/Debian systems. For scaling, reserve at least 900x620 logical pixels of usable area: at 200% that's 1800x1240 physical pixels, plus the desktop panels.

<a id="1-probar-solo-la-interfaz"></a>

## 1. Test only the interface

Install the graphical dependencies, without installing the daemon yet:

```bash
sudo apt update
sudo apt install python3 python3-gi \
  python3-pyside6.qtcore python3-pyside6.qtgui \
  python3-pyside6.qtqml python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtwidgets python3-pyside6.qtnetwork \
  qt6-svg-plugins qml6-module-qtquick qml6-module-qtquick-window \
  qml6-module-qtquick-layouts qml6-module-qtquick-controls \
  qml6-module-qtquick-dialogs qml6-module-qtquick-templates \
  qml6-module-qtqml-workerscript
PYTHONPATH=src python3 -m usbguard_control --demo
```

For automated tests: `sudo apt install python3-pytest dbus-daemon desktop-file-utils`.

Or build and install the interface package:

```bash
python3 scripts/build_deb.py
sudo apt install ./dist/usbguard-control_0.5.0-1_all.deb
usbguard-control --demo
```

USBGuard is listed as `Suggests`, not as a dependency that is installed automatically. `.deb` does not contain postinst scripts, services, or Polkit changes. The applications menu offers an “Open Demo” action.

Do not mix `sudo pip` with system packages. For development in a virtual environment, use `python3 -m venv --system-site-packages .venv` to retain access to PyGObject installed by APT. `pip install -e . --no-deps` can register the command if the dependencies are already installed.

<a id="2-preparar-usbguard-en-una-instalación-nueva"></a>

## 2. Prepare USBGuard on a fresh installation

Perform this stage on a VM with a snapshot or with recovery access that does not depend on the USBs you are going to filter. Only connect trusted devices. Do not use this sequence to override a configuration that you already manage.

The `postinst` in the official package can generate a policy and start services. For a **first time installation**, the included installer installs the interface and USBGuard and leaves both services masked until you review the rules:

```bash
sudo sh scripts/install_kali.sh
```

Stops if USBGuard is already installed or finds pre-existing administrative units. To do the same steps manually, prevent startup during preparation:

```bash
sudo systemctl mask usbguard.service usbguard-dbus.service
sudo apt install usbguard
```

Check with `systemctl is-active usbguard.service usbguard-dbus.service` that they are not running. Service masks persist after reboot until you explicitly remove them. Do not activate the service while the policy is pending.

Back up the existing directory before editing it. Generate a candidate policy in a private file:

```bash
umask 077
policy_candidate=$(mktemp)
sudo usbguard generate-policy > "$policy_candidate"
less "$policy_candidate"
```

Check that the keyboard, mouse, hubs and necessary internal devices are included. The generated policy relies on what is connected at that moment; it does not determine whether the devices are benign. Confirm `RuleFile` and `RuleFolder` in `/etc/usbguard/usbguard-daemon.conf` and review pre-existing rules in both places.

Only after reviewing and backing up, install the candidate:

```bash
sudo install -m 0600 -o root -g root "$policy_candidate" /etc/usbguard/rules.conf
rm -- "$policy_candidate"
sudo systemctl unmask usbguard.service usbguard-dbus.service
sudo systemctl start usbguard.service usbguard-dbus.service
```

Test the devices and a dispensable USB. Check `systemctl is-enabled usbguard.service usbguard-dbus.service`: the package may have enabled them during installation. Retain autostart only after validation. Do not grant general access to the `users` group or add Polkit rules that allow all actions.

<a id="3-conectar-la-interfaz"></a>

## 3. Connect the interface

```bash
usbguard-control
```

From source code: `PYTHONPATH=src python3 -m usbguard_control`.

Run as a normal user in an active local session with Polkit agent. Administrative actions can display desktop authentication. The app does not ask for or save passwords.

“Allow now” does not save a rule: reconnecting or rebooting reevaluates the policy. “Always allow” asks USBGuard to save a rule; will fail if your rule storage is not writable or configured. “Block now” also does not remove persistent rules. To revoke a specific rule, open **Rules**, select the entry, and use **Remove Rule** after reviewing the preview. The application saves a backup before changing it. Sensitive or advanced rules require review with official tools. Removing a rule does not change the current authorization: reconnect the device to evaluate the resulting policy.

Before blocking a storage device, unmount the volume. Blocking USB authorization is not a secure eject operation. This version does not manage mounts.

<a id="iniciar-detener-y-recordar-la-elección"></a>

### Start, stop and remember the choice

In **Settings**, the cards separately show the current status and automatic start of USB protection and its connection to the interface.

- **Start Service** starts both components with the existing rules.
- **Stop Service** stops both components without deleting the rules. It is not equivalent to unlocking all USBs: some devices may remain unauthorized.
- **Remember this choice when starting the system**, checked by default, causes Start to enable both services at startup and Stop to disable their automatic startup. Uncheck it to change only the current state.

The dialog confirms the scope before requesting systemd permissions using Polkit. More than one authentication request may appear. The preference lives in systemd and does not depend on keeping the interface open. Other administrators can still start the services or change these settings.

These checks require a configured installation, systemd, and a Polkit agent. They do not remove masks from the first installation or modify special settings such as static units or enabled only in `/run`. If an operation fails midway, the re-queried states and the error are displayed; check both before retrying. Stopping USBGuard does not disable other USB protection mechanisms, such as GNOME.

<a id="diagnóstico-y-recuperación"></a>

## Diagnosis and recovery

```bash
python3 scripts/diagnose.py
systemctl status usbguard.service usbguard-dbus.service
journalctl -u usbguard -u usbguard-dbus -b
```

If service exists but authorization is missing, review the Polkit agent and the policies provided by USBGuard. Don't run the GUI with sudo to resolve it. If GNOME manages USB protection, its policy can coexist or change: inspects `gsettings get org.gnome.desktop.privacy usb-protection` and, if it exists, `usb-protection-level`; We do not change these values ​​automatically.

In GNOME, the protection manager can add a rule that authorizes all devices in `lockscreen` mode. To manage an explicit list with a standalone client, coordinate that manager before the first boot and check the resulting rules. Changing `usb-protection` to `false` while the daemon is active can also cause GNOME to insert a general authorization rule. It is not enough to change the preference without reviewing the status. [Debian GNOME manager code](https://browse.dgit.debian.org/gnome-settings-daemon.git/tree/plugins/usb-protection/gsd-usb-protection-manager.c).

If you lose access to the keyboard, use the prepared recovery access. The README.Debian of the examined package documents the `usbguard=0` or `usbguard=false` boot parameters to prevent USBGuard from starting. Check these instructions at `/usr/share/doc/usbguard/README.Debian` for your version before you need them. Stopping a service does not guarantee instantly restoring all devices; A reconnection or reboot may be required after repairing the policy.

In unit `usbguard.service` of package `1.1.4+ds-10` examined, `ConditionKernelCommandLine` and `ConditionPathExists` are under `[Service]`; systemd ignores them there. Their equivalents in `[Unit]` were added in the test installation using `/etc/systemd/system/usbguard.service.d/10-usbguard-control-conditions.conf`, preserving the package file. Do not trust the recovery parameters until you verify that the conditions apply to your installation.

Uninstalling the interface with `sudo apt remove usbguard-control` leaves the daemon and its rules under separate management.

<a id="iphone-permitido-pero-archivos-muestra-lockdown--21"></a>

### iPhone allowed, but Files shows “Lockdown (-21)”

"Allowed" indicates USB authorization; Accessing iPhone documents additionally requires iOS pairing and GVFS mounting. The code `-21` corresponds to `LOCKDOWN_E_INVALID_HOST_ID`: the phone rejects the identity of the device in that session. [Definition in libimobiledevice](https://github.com/libimobiledevice/libimobiledevice/blob/1.4.0/include/libimobiledevice/lockdown.h).

With the iPhone authorized in USBGuard, unlock it and keep it connected. Accept “Trust this computer” if it appears on your phone. To verify the pairing, install the optional utilities and run validation as a normal user:

```bash
sudo apt install --no-install-recommends libimobiledevice-utils
idevicepair validate
```

If validation indicates that it is not paired, run `idevicepair pair`, confirm trust on the iPhone, and validate again. With multiple Apple devices connected, select the correct one using `-u` based on `idevicepair --help`. These tools can show the phone's identifier: hide it before sharing its outputs.

After successful validation, close the previous Files prompt and open “Documents on…” again. There is no need to change a USB rule that already authorizes the device. This location shows documents shared by supported apps, not the entire iOS file system. The USBGuard Control interface does not handle pairing or mounts.

Sources: [USBGuard 1.1.4](https://github.com/USBGuard/usbguard/releases/tag/usbguard-1.1.4), [Kali packages](https://http.kali.org/pool/main/u/usbguard/) and README.Debian/postinst files from the `1.1.4+ds-10` package inspected without installing it.

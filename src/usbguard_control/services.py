# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit systemd operations, restricted to USBGuard and its D-Bus bridge."""
import time

UNITS = ("usbguard.service", "usbguard-dbus.service")
DEST = "org.freedesktop.systemd1"
ROOT = "/org/freedesktop/systemd1"
MANAGER = DEST + ".Manager"


def manageable(state):
    units = state.get("units", [])
    return (len(units) == 2 and tuple(u["name"] for u in units) == UNITS
            and all(u["load"] == "loaded" and u["boot"] in
                    ("enabled", "disabled")
                    and u["active"] in ("active", "inactive", "failed") for u in units))


def fingerprint(state):
    return state.get("owner"), tuple((u["name"], u["load"], u["active"], u["boot"])
                                    for u in state.get("units", []))


class ServiceManager:
    def __init__(self, connection=None, cancellable=None):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.cancel = cancellable or Gio.Cancellable()
        self.bus = connection or Gio.bus_get_sync(Gio.BusType.SYSTEM, self.cancel)

    def call(self, owner, method, signature, args, reply, interactive=False,
             path=ROOT, interface=MANAGER):
        flags = self.Gio.DBusCallFlags.NO_AUTO_START
        if interactive:
            flags |= self.Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION
        return self.bus.call_sync(owner, path, interface, method,
            self.GLib.Variant(signature, args), self.GLib.VariantType.new(reply), flags,
            120000 if interactive else 5000, self.cancel).unpack()

    def snapshot(self):
        owner = self.call("org.freedesktop.DBus", "GetNameOwner", "(s)", (DEST,), "(s)",
                          path="/org/freedesktop/DBus", interface="org.freedesktop.DBus")[0]
        units = []
        for name in UNITS:
            path = self.call(owner, "LoadUnit", "(s)", (name,), "(o)")[0]
            props = self.call(owner, "GetAll", "(s)", (DEST + ".Unit",), "(a{sv})",
                              path=path, interface="org.freedesktop.DBus.Properties")[0]
            units.append({"name": name, "load": props.get("LoadState", "unknown"),
                          "active": props.get("ActiveState", "unknown"),
                          "boot": props.get("UnitFileState", "unknown")})
        return {"owner": owner, "units": units}

    def wait_job(self, owner, job):
        # A queued job is not success. Wait for removal, then verify unit states.
        deadline = time.monotonic() + 30
        job_id = int(job.rsplit("/", 1)[1])
        while time.monotonic() < deadline:
            if self.cancel.is_cancelled():
                raise ValueError("Operación cancelada. Comprueba el estado de los servicios.")
            try:
                self.call(owner, "GetJob", "(u)", (job_id,), "(o)")
            except self.GLib.Error as error:
                if self.Gio.DBusError.get_remote_error(error) == DEST + ".NoSuchJob":
                    return
                raise
            time.sleep(0.1)
        raise ValueError("La operación sigue pendiente. Comprueba el estado de los servicios.")

    def apply(self, action, remember, expected):
        if action not in ("start", "stop") or type(remember) is not bool:
            raise ValueError("Acción no admitida")
        state = self.snapshot()
        if fingerprint(state) != fingerprint(expected):
            raise ValueError("El estado del servicio cambió. Revisa la configuración y vuelve a confirmar.")
        if not manageable(state):
            raise ValueError("Revisa la guía de instalación: los servicios deben estar instalados, sin máscaras ni configuraciones de arranque especiales.")
        owner = state["owner"]
        target = "active" if action == "start" else "inactive"
        names = UNITS if action == "start" else tuple(reversed(UNITS))
        for name in names:
            current = self.snapshot()
            if current["owner"] != owner:
                raise ValueError("El estado del servicio cambió. Revisa la configuración y vuelve a confirmar.")
            unit = next(u for u in current["units"] if u["name"] == name)
            if unit["active"] == target:
                continue
            job = self.call(owner, "StartUnit" if action == "start" else "StopUnit",
                            "(ss)", (name, "fail"), "(o)", True)[0]
            self.wait_job(owner, job)
            actual = self.snapshot()
            if actual["owner"] != owner or next(u for u in actual["units"] if u["name"] == name)["active"] != target:
                raise ValueError("El servicio no alcanzó el estado solicitado. Revisa el registro del sistema.")
        if remember:
            boot = "enabled" if action == "start" else "disabled"
            if any(u["boot"] != boot for u in self.snapshot()["units"]):
                if action == "start":
                    self.call(owner, "EnableUnitFiles", "(asbb)", (list(UNITS), False, False), "(ba(sss))", True)
                else:
                    self.call(owner, "DisableUnitFiles", "(asb)", (list(UNITS), False), "(a(sss))", True)
                self.call(owner, "Reload", "()", (), "()", True)
        actual = self.snapshot()
        if actual["owner"] != owner or any(u["active"] != target for u in actual["units"]):
            raise ValueError("El servicio no alcanzó el estado solicitado. Revisa el registro del sistema.")
        if remember and any(u["boot"] != boot for u in actual["units"]):
            raise ValueError("No se pudo verificar la preferencia de arranque. Revisa el estado actual.")
        return actual


class DemoServiceManager:
    """No GIO import and no system access in the demonstration."""
    def __init__(self):
        self.state = {"owner": "demo", "units": [
            {"name": name, "load": "loaded", "active": "active", "boot": "enabled"} for name in UNITS]}

    def snapshot(self):
        return {"owner": "demo", "units": [dict(u) for u in self.state["units"]]}

    def apply(self, action, remember, expected):
        if action not in ("start", "stop") or type(remember) is not bool:
            raise ValueError("Acción no admitida")
        if fingerprint(expected) != fingerprint(self.state):
            raise ValueError("El estado del servicio cambió. Revisa la configuración y vuelve a confirmar.")
        for unit in self.state["units"]:
            unit["active"] = "active" if action == "start" else "inactive"
            if remember:
                unit["boot"] = "enabled" if action == "start" else "disabled"
        return self.snapshot()

# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""USBGuard 1.1.4 D-Bus client. Calls never activate a stopped service."""
from .domain import TARGETS, parse_device, validate_action

SERVICE = "org.usbguard1"
ROOT = "/org/usbguard1"
DEVICES = ROOT + "/Devices"
INTERFACE = "org.usbguard.Devices1"


class SystemBackend:
    def __init__(self, event_callback=None, connection=None, cancellable=None):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.cancel = cancellable or Gio.Cancellable()
        self.bus = connection or Gio.bus_get_sync(Gio.BusType.SYSTEM, self.cancel)
        self.subscriptions = []
        if event_callback:
            def changed(_bus, _sender, _path, _interface, member, parameters, _data):
                event_callback(member, parameters.unpack())
            for path, interface in ((DEVICES, INTERFACE), (ROOT, SERVICE)):
                self.subscriptions.append(self.bus.signal_subscribe(
                    SERVICE, interface, None, path, None, Gio.DBusSignalFlags.NONE, changed, None))

    def close(self):
        for subscription in self.subscriptions:
            self.bus.signal_unsubscribe(subscription)
        self.subscriptions.clear()

    def owner(self):
        return self.bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus",
            "org.freedesktop.DBus", "GetNameOwner", self.GLib.Variant("(s)", (SERVICE,)),
            self.GLib.VariantType.new("(s)"), self.Gio.DBusCallFlags.NO_AUTO_START,
            3000, self.cancel).unpack()[0]

    def call(self, owner, path, interface, method, signature, args, reply, interactive=False):
        flags = self.Gio.DBusCallFlags.NO_AUTO_START
        if interactive:
            flags |= self.Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION
        return self.bus.call_sync(owner, path, interface, method,
            self.GLib.Variant(signature, args), self.GLib.VariantType.new(reply), flags,
            120000 if interactive else 5000, self.cancel).unpack()

    def devices(self, owner):
        rows = self.call(owner, DEVICES, INTERFACE, "listDevices", "(s)", ("match",), "(a(us))")[0]
        return [parse_device(device_id, rule) for device_id, rule in rows]

    def snapshot(self):
        owner = self.owner()
        devices = self.devices(owner)
        parameters = {}
        for key, name in (("implicit", "ImplicitPolicyTarget"), ("inserted", "InsertedDevicePolicy")):
            try:
                parameters[key] = self.call(owner, ROOT, SERVICE, "getParameter", "(s)", (name,), "(s)")[0]
            except self.GLib.Error:
                parameters[key] = "unknown"
        return {"devices": devices, "owner": owner, **parameters}

    def apply(self, expected, target, permanent, owner):
        if self.owner() != owner:
            raise ValueError("USBGuard se reinició. Actualiza la lista antes de continuar.")
        current = next((d for d in self.devices(owner) if d.id == expected.id), None)
        if current is None:
            raise ValueError("El dispositivo ya no está conectado.")
        validate_action(current, expected, target)
        # USBGuard owns policy serialization, persistence and authorization.
        return self.call(owner, DEVICES, INTERFACE, "applyDevicePolicy", "(uub)",
                         (current.id, TARGETS[target], bool(permanent)), "(u)", True)[0]


def friendly_error(error):
    text = str(error)
    if any(word in text for word in ("NameHasNoOwner", "ServiceUnknown")):
        return "USBGuard no está disponible. Revisa el servicio y su puente D-Bus en la guía de instalación."
    if any(word in text.lower() for word in ("accessdenied", "not authorized", "authorization", "permission denied")):
        return "Operación no autorizada. Revisa el agente Polkit de tu sesión y los permisos de USBGuard."
    return text[:400]

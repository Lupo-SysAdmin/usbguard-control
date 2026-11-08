"""Isolated D-Bus contract fixture; never accesses the system bus or USB."""
from gi.repository import Gio, GLib
from usbguard_control.demo import FIXTURES

XML = '''<node>
<interface name="org.usbguard1"><method name="getParameter"><arg type="s" direction="in"/><arg type="s" direction="out"/></method></interface>
<interface name="org.usbguard.Devices1">
<method name="listDevices"><arg type="s" direction="in"/><arg type="a(us)" direction="out"/></method>
<method name="applyDevicePolicy"><arg type="u" direction="in"/><arg type="u" direction="in"/><arg type="b" direction="in"/><arg type="u" direction="out"/></method>
<signal name="DevicePresenceChanged"><arg type="u"/><arg type="u"/><arg type="u"/><arg type="s"/><arg type="a{ss}"/></signal>
</interface>
<interface name="org.example.Test"><method name="change"><arg type="s" direction="in"/></method></interface>
</node>'''
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
rows = list(FIXTURES)
mode = ""


def handle(connection, sender, path, interface, method, parameters, invocation):
    global mode, rows
    args = parameters.unpack()
    if method == "change":
        mode = args[0]
        if mode == "swap": rows[0] = (12, rows[0][1].replace("demo-storage", "replacement-device"))
        if mode == "disconnect": rows = [r for r in rows if r[0] != 12]
        if mode == "event":
            bus.emit_signal(None, "/org/usbguard1/Devices", "org.usbguard.Devices1", "DevicePresenceChanged",
                            GLib.Variant("(uuusa{ss})", (12, 1, 1, rows[0][1], {})))
        invocation.return_value(None)
    elif method == "listDevices": invocation.return_value(GLib.Variant("(a(us))", (rows,)))
    elif method == "getParameter":
        if mode == "no-parameters": invocation.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied", "denied")
        else: invocation.return_value(GLib.Variant("(s)", ("block" if args[0] == "ImplicitPolicyTarget" else "apply-policy",)))
    elif method == "applyDevicePolicy":
        if mode == "deny":
            invocation.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied", "not authorized")
        elif not invocation.get_message().get_flags() & Gio.DBusMessageFlags.ALLOW_INTERACTIVE_AUTHORIZATION:
            invocation.return_dbus_error("org.example.MissingFlag", "interactive auth required")
        else:
            device_id, target, permanent = args
            rows = [(i, ("allow" if target == 0 else "block") + " " + r.split(" ", 1)[1]) if i == device_id else (i, r) for i, r in rows]
            invocation.return_value(GLib.Variant("(u)", (42 if permanent else 0,)))


info = Gio.DBusNodeInfo.new_for_xml(XML)
bus.register_object("/org/usbguard1", info.interfaces[0], handle, None, None)
bus.register_object("/org/usbguard1/Devices", info.interfaces[1], handle, None, None)
bus.register_object("/test", info.interfaces[2], handle, None, None)
bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
              GLib.Variant("(su)", ("org.usbguard1", 0)), None, Gio.DBusCallFlags.NONE, 3000, None)
print("ready", flush=True)
GLib.MainLoop().run()

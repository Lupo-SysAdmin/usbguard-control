"""Isolated D-Bus contract fixture; never accesses the system bus or USB."""
from gi.repository import Gio, GLib
from usbguard_control.demo import FIXTURES
from usbguard_control.policy import PolicyRule, concrete_rule, LAST_RULE

XML = '''<node>
<interface name="org.usbguard1"><method name="getParameter"><arg type="s" direction="in"/><arg type="s" direction="out"/></method></interface>
<interface name="org.usbguard.Devices1">
<method name="listDevices"><arg type="s" direction="in"/><arg type="a(us)" direction="out"/></method>
<method name="applyDevicePolicy"><arg type="u" direction="in"/><arg type="u" direction="in"/><arg type="b" direction="in"/><arg type="u" direction="out"/></method>
<signal name="DevicePresenceChanged"><arg type="u"/><arg type="u"/><arg type="u"/><arg type="s"/><arg type="a{ss}"/></signal>
</interface>
<interface name="org.usbguard.Policy1">
<method name="listRules"><arg type="s" direction="in"/><arg type="a(us)" direction="out"/></method>
<method name="appendRule"><arg type="s" direction="in"/><arg type="u" direction="in"/><arg type="b" direction="in"/><arg type="u" direction="out"/></method>
<method name="removeRule"><arg type="u" direction="in"/></method>
</interface>
<interface name="org.example.Test"><method name="change"><arg type="s" direction="in"/></method></interface>
</node>'''
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
rows = list(FIXTURES)
mode = ""
rules = [(51, FIXTURES[3][1])]
next_rule = 1000


def handle(connection, sender, path, interface, method, parameters, invocation):
    global mode, rows, rules, next_rule
    args = parameters.unpack()
    if method == "change":
        mode = args[0]
        if mode == "swap": rows[0] = (12, rows[0][1].replace("demo-storage", "replacement-device"))
        if mode == "disconnect": rows = [r for r in rows if r[0] != 12]
        if mode == "policy-swap": rules = [(51, rules[0][1].replace('demo-kingston', 'replacement'))]
        if mode == "event":
            bus.emit_signal(None, "/org/usbguard1/Devices", "org.usbguard.Devices1", "DevicePresenceChanged",
                            GLib.Variant("(uuusa{ss})", (12, 1, 1, rows[0][1], {})))
        invocation.return_value(None)
    elif method == "listRules":
        if mode == "no-rules": invocation.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied", "denied")
        else: invocation.return_value(GLib.Variant("(a(us))", (rules,)))
    elif method in ("appendRule", "removeRule"):
        if mode == "deny" or (mode == "deny-remove" and method == "removeRule"):
            invocation.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied", "not authorized")
        elif not invocation.get_message().get_flags() & Gio.DBusMessageFlags.ALLOW_INTERACTIVE_AUTHORIZATION:
            invocation.return_dbus_error("org.example.MissingFlag", "interactive auth required")
        elif method == "appendRule":
            text, parent, temporary = args
            if temporary:
                invocation.return_dbus_error("org.example.WrongPersistence", "must be persistent")
                return
            next_rule += 1
            pos = next((i + 1 for i, r in enumerate(rules) if r[0] == parent), len(rules))
            rules.insert(pos, (next_rule, text))
            invocation.return_value(GLib.Variant("(u)", (next_rule,)))
        else:
            rules = [r for r in rules if r[0] != args[0]]
            invocation.return_value(None)
    elif method == "listDevices":
        matching = rows
        if args[0] != 'match':
            target = concrete_rule('allow ' + args[0].split(' ', 1)[1])
            matching = [r for r in rows if concrete_rule(r[1]).digest == target.digest]
        invocation.return_value(GLib.Variant("(a(us))", (matching,)))
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
bus.register_object("/org/usbguard1/Policy", info.interfaces[2], handle, None, None)
bus.register_object("/test", info.interfaces[3], handle, None, None)
bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
              GLib.Variant("(su)", ("org.usbguard1", 0)), None, Gio.DBusCallFlags.NONE, 3000, None)
print("ready", flush=True)
GLib.MainLoop().run()

"""Private-bus systemd contract fixture. Never calls the system bus."""
import json
from gi.repository import Gio, GLib
from usbguard_control.services import DEST, ROOT, MANAGER, UNITS

XML = '''<node><interface name="org.freedesktop.systemd1.Manager">
<method name="LoadUnit"><arg type="s" direction="in"/><arg type="o" direction="out"/></method>
<method name="StartUnit"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="o" direction="out"/></method>
<method name="StopUnit"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="o" direction="out"/></method>
<method name="GetJob"><arg type="u" direction="in"/><arg type="o" direction="out"/></method>
<method name="EnableUnitFiles"><arg type="as" direction="in"/><arg type="b" direction="in"/><arg type="b" direction="in"/><arg type="b" direction="out"/><arg type="a(sss)" direction="out"/></method>
<method name="DisableUnitFiles"><arg type="as" direction="in"/><arg type="b" direction="in"/><arg type="a(sss)" direction="out"/></method>
<method name="Reload"/>
</interface><interface name="org.freedesktop.DBus.Properties">
<method name="GetAll"><arg type="s" direction="in"/><arg type="a{sv}" direction="out"/></method>
</interface><interface name="org.example.Test">
<method name="Change"><arg type="s" direction="in"/></method>
<method name="Calls"><arg type="as" direction="out"/></method>
</interface></node>'''
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
paths = {name: ROOT + '/unit/test' + str(i) for i, name in enumerate(UNITS)}
states = {name: {"LoadState": "loaded", "ActiveState": "inactive", "UnitFileState": "disabled"} for name in UNITS}
calls, jobs = [], {}
mode = ""
counter = 0


def handle(connection, sender, path, interface, method, parameters, invocation):
    global mode, counter
    args = parameters.unpack()
    if method == "Change":
        mode = args[0]
        for state in states.values():
            if mode == "running": state.update(ActiveState="active", UnitFileState="enabled")
            if mode == "masked": state.update(LoadState="masked", UnitFileState="masked")
            if mode == "missing": state.update(LoadState="not-found", UnitFileState="")
        invocation.return_value(None)
        return
    if method == "Calls":
        invocation.return_value(GLib.Variant("(as)", ([json.dumps(c) for c in calls],)))
        return
    if method == "LoadUnit":
        assert args[0] in UNITS
        invocation.return_value(GLib.Variant("(o)", (paths[args[0]],)))
        return
    if method == "GetAll":
        assert args[0] == DEST + '.Unit'
        state = states[next(n for n, p in paths.items() if p == path)]
        invocation.return_value(GLib.Variant("(a{sv})", ({k: GLib.Variant('s', v) for k, v in state.items()},)))
        return
    if method == "GetJob":
        job = jobs[args[0]]
        if not job[2]:
            job[2] = True
            invocation.return_value(GLib.Variant("(o)", (ROOT + '/job/' + str(args[0]),)))
        else:
            if mode != 'condition-failed': states[job[0]]["ActiveState"] = job[1]
            invocation.return_dbus_error(DEST + '.NoSuchJob', 'Job completed')
        return
    calls.append([method, args])
    if not invocation.get_message().get_flags() & Gio.DBusMessageFlags.ALLOW_INTERACTIVE_AUTHORIZATION:
        invocation.return_dbus_error('org.example.MissingFlag', 'Interactive auth required')
        return
    if mode == 'deny' or (mode == 'deny-enable' and method == 'EnableUnitFiles'):
        invocation.return_dbus_error('org.freedesktop.DBus.Error.AccessDenied', 'Authorization canceled')
        return
    if method in ('StartUnit', 'StopUnit'):
        assert args[0] in UNITS and args[1] == 'fail'
        counter += 1
        jobs[counter] = [args[0], 'active' if method == 'StartUnit' else 'inactive', False]
        invocation.return_value(GLib.Variant('(o)', (ROOT + '/job/' + str(counter),)))
    elif method in ('EnableUnitFiles', 'DisableUnitFiles'):
        assert tuple(args[0]) == UNITS and args[1] is False
        if method == 'EnableUnitFiles': assert args[2] is False
        for state in states.values(): state['UnitFileState'] = 'enabled' if method == 'EnableUnitFiles' else 'disabled'
        invocation.return_value(GLib.Variant('(ba(sss))', (True, [])) if method == 'EnableUnitFiles' else GLib.Variant('(a(sss))', ([],)))
    elif method == 'Reload': invocation.return_value(None)


info = Gio.DBusNodeInfo.new_for_xml(XML)
bus.register_object(ROOT, info.interfaces[0], handle, None, None)
for path in paths.values(): bus.register_object(path, info.interfaces[1], handle, None, None)
bus.register_object('/test', info.interfaces[2], handle, None, None)
bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'RequestName',
              GLib.Variant('(su)', (DEST, 0)), None, Gio.DBusCallFlags.NONE, 3000, None)
print('ready', flush=True)
GLib.MainLoop().run()

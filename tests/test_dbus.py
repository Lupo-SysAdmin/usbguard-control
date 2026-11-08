"""Run with dbus-run-session; no real USBGuard daemon is touched."""
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from gi.repository import Gio, GLib
from usbguard_control.backend import SystemBackend, friendly_error

pytestmark = pytest.mark.skipif(os.environ.get("USBGUARD_TEST_BUS") != "1", reason="requires an explicitly isolated D-Bus session")


@pytest.fixture
def backend():
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("fake_service.py"))], stdout=subprocess.PIPE, text=True)
    assert process.stdout.readline().strip() == "ready"
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    client = SystemBackend(connection=connection)
    client.test_process = process
    yield client
    client.close()
    process.terminate()
    process.wait(timeout=5)


def change(backend, mode):
    backend.bus.call_sync("org.usbguard1", "/test", "org.example.Test", "change", GLib.Variant("(s)", (mode,)), None, Gio.DBusCallFlags.NONE, 3000, None)


def test_real_transport_signatures_and_interactive_authorization(backend):
    snapshot = backend.snapshot()
    assert snapshot["implicit"] == "block"
    assert len(snapshot["devices"]) == 5
    assert backend.apply(snapshot["devices"][0], "allow", True, snapshot["owner"]) == 42
    assert backend.snapshot()["devices"][0].target == "allow"


@pytest.mark.parametrize("mode", ["swap", "disconnect"])
def test_hot_unplug_or_replaced_id_is_not_authorized(backend, mode):
    snapshot = backend.snapshot()
    change(backend, mode)
    with pytest.raises(ValueError): backend.apply(snapshot["devices"][0], "allow", False, snapshot["owner"])


def test_changed_service_owner_is_not_authorized(backend):
    snapshot = backend.snapshot()
    with pytest.raises(ValueError, match="reinició"):
        backend.apply(snapshot["devices"][0], "allow", False, ":old-owner")


def test_polkit_denial_is_not_reported_as_success(backend):
    snapshot = backend.snapshot()
    change(backend, "deny")
    with pytest.raises(GLib.Error) as error:
        backend.apply(snapshot["devices"][0], "allow", False, snapshot["owner"])
    assert "no autorizada" in friendly_error(error.value)
    assert backend.snapshot()["devices"][0].target == "block"


def test_unreadable_policy_is_not_assumed_to_be_block(backend):
    change(backend, "no-parameters")
    assert backend.snapshot()["implicit"] == "unknown"


def test_device_signals_reach_subscriber(backend):
    seen = []
    subscriber = SystemBackend(lambda member, args: seen.append((member, args)), connection=backend.bus)
    try:
        change(backend, "event")
        deadline = time.monotonic() + 2
        while not seen and time.monotonic() < deadline:
            GLib.MainContext.default().iteration(False)
            time.sleep(0.01)
        assert seen[0][0] == "DevicePresenceChanged"
        assert seen[0][1][:3] == (12, 1, 1)
    finally:
        subscriber.close()


def test_service_loss_is_reported_without_activation(backend):
    assert backend.snapshot()["devices"]
    backend.test_process.terminate()
    backend.test_process.wait(timeout=5)
    with pytest.raises(GLib.Error) as error:
        backend.snapshot()
    assert "no está disponible" in friendly_error(error.value)


def test_worker_receives_real_bus_events_and_shuts_down(backend, monkeypatch):
    from PySide6.QtGui import QGuiApplication
    from usbguard_control import backend as backend_module
    from usbguard_control.controller import Controller
    real_backend = backend_module.SystemBackend
    monkeypatch.setattr(backend_module, "SystemBackend", lambda callback, cancellable:
        real_backend(callback, connection=Gio.bus_get_sync(Gio.BusType.SESSION, None), cancellable=cancellable))
    app = QGuiApplication.instance() or QGuiApplication([])
    control = Controller(demo=False)
    control.setNotifications(False)

    def wait_for(predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert predicate()

    try:
        wait_for(lambda: control.connected and not control.busy)
        change(backend, "event")
        wait_for(lambda: any(e["category"] == "Dispositivo" for e in control.events))
        control.select(12)
        control.prepare("allow", False)
        control.confirm()
        wait_for(lambda: not control.busy and control.selected.get("target") == "allow")
    finally:
        control.shutdown()
        assert not control.thread.isRunning()

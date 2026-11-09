"""UI regressions: background reads stay quiet and never swallow a user action."""
from dataclasses import replace
from pathlib import Path
from threading import Event
import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # Register QML window wrappers.
from shiboken6 import delete

from usbguard_control.controller import Controller
from usbguard_control.demo import DemoBackend


def spin(app, predicate):
    deadline = time.monotonic() + 3
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    assert predicate()


@pytest.fixture
def ui():
    app = QGuiApplication.instance() or QGuiApplication([])
    control = Controller(demo=True)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('control', control)
    engine.rootContext().setContextProperty('language', control.language)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / 'src/usbguard_control/qml/Main.qml')))
    window = engine.rootObjects()[0]
    spin(app, lambda: control.connected and not control.busy)
    refresh = next(o for o in window.findChildren(QObject)
                   if 'ActionButton' in o.metaObject().className() and o.property('text') == '↻  Actualizar')
    try:
        yield app, control, window, refresh
    finally:
        control.shutdown()
        delete(engine)
        app.processEvents()


@pytest.fixture
def slow_read(monkeypatch):
    entered, release = Event(), Event()
    original = DemoBackend.snapshot

    def snapshot(backend):
        result = original(backend)
        entered.set()
        assert release.wait(2), 'Test must release the simulated read'
        return result

    monkeypatch.setattr(DemoBackend, 'snapshot', snapshot)
    try:
        yield entered, release
    finally:
        release.set()


def click(button):
    QMetaObject.invokeMethod(button, 'clicked', Qt.DirectConnection)


def test_unchanged_poll_keeps_buttons_and_details_stable(ui, slow_read):
    app, control, window, refresh = ui
    entered, release = slow_read
    changes, selections = [], []
    control.changed.connect(lambda: changes.append(True))
    window.pickedChanged.connect(lambda: selections.append(True))
    details = window.findChild(QObject, 'allowAlwaysButton')
    assert control.poll.interval() == 5000
    control.poll.timeout.emit()
    spin(app, entered.is_set)
    assert control._polling and not control.busy
    assert refresh.property('text') == '↻  Actualizar'
    assert refresh.property('enabled') and refresh.property('opacity') == 1
    assert details.property('enabled') and details.property('opacity') == 1
    release.set()
    spin(app, lambda: not control._polling)
    assert changes == [] and selections == []
    click(refresh)
    assert control.busy
    assert refresh.property('text') == 'Consultando…'
    spin(app, lambda: not control.busy)
    assert refresh.property('text') == '↻  Actualizar'
    assert selections == [], 'Manual refresh must also preserve unchanged details'


def test_device_action_clicked_during_poll_is_processed(ui, slow_read):
    app, control, window, _refresh = ui
    entered, release = slow_read
    control.select(12)
    control.pollBackground()
    spin(app, entered.is_set)
    click(window.findChild(QObject, 'allowAlwaysButton'))
    assert control.confirmation['permanent'] is True
    click(window.findChild(QObject, 'confirmActionButton'))
    assert control.busy
    busy_when_poll_finished = []
    control.worker.done.connect(lambda op, _result:
                                busy_when_poll_finished.append(control.busy) if op == 'poll' else None)
    release.set()
    spin(app, lambda: not control._polling and not control.busy and control.selected['target'] == 'allow')
    assert busy_when_poll_finished == [True], 'Background completion must not unlock a pending action'
    assert any('regla guardada' in e['message'] for e in control.events)


def test_manual_refresh_clicked_during_poll_is_processed(ui, slow_read):
    app, control, _window, refresh = ui
    entered, release = slow_read
    completed = []
    control.worker.done.connect(lambda op, _result: completed.append(op))
    control.pollBackground()
    spin(app, entered.is_set)
    click(refresh)
    assert control.busy and refresh.property('text') == 'Consultando…'
    release.set()
    spin(app, lambda: not control._polling and not control.busy)
    assert [op for op in completed if op != 'services'] == ['poll', 'refresh']


def test_service_action_clicked_during_poll_is_processed(ui, slow_read):
    app, control, window, _refresh = ui
    entered, release = slow_read
    control.pollBackground()
    spin(app, entered.is_set)
    click(window.findChild(QObject, 'stopServiceButton'))
    assert control.serviceConfirmation == {'action': 'stop', 'remember': True}
    click(window.findChild(QObject, 'confirmServiceButton'))
    assert control.busy and control.serviceWorking
    release.set()
    spin(app, lambda: not control._polling and not control.busy and not control.connected)
    assert not control.serviceWorking
    assert all(u['active'] == 'inactive' and u['boot'] == 'disabled' for u in control.serviceState['units'])


def test_poll_updates_changed_device_and_clears_disconnected_selection(ui, monkeypatch):
    app, control, window, _refresh = ui
    original = DemoBackend.snapshot
    control.select(12)
    selections = []
    window.pickedChanged.connect(lambda: selections.append(True))
    state = {'connected': True}

    def snapshot(backend):
        result = original(backend)
        result['devices'] = [replace(d, target='allow') if d.id == 12 else d
                             for d in result['devices'] if state['connected'] or d.id != 12]
        return result

    monkeypatch.setattr(DemoBackend, 'snapshot', snapshot)
    control.pollBackground()
    spin(app, lambda: not control._polling)
    assert control.selected['target'] == 'allow' and len(selections) == 1
    state['connected'] = False
    control.pollBackground()
    spin(app, lambda: not control._polling)
    assert control.selected == {} and len(selections) == 2


def test_failed_poll_clears_stale_data_and_can_recover(ui, monkeypatch):
    app, control, _window, _refresh = ui
    original = DemoBackend.snapshot

    def fail(_backend):
        raise ValueError('USBGuard unavailable in test')

    monkeypatch.setattr(DemoBackend, 'snapshot', fail)
    control.pollBackground()
    spin(app, lambda: not control._polling)
    assert not control.connected and control.selected == {} and control.devices == []
    assert control.error == 'USBGuard unavailable in test'
    monkeypatch.setattr(DemoBackend, 'snapshot', original)
    control.pollBackground()
    spin(app, lambda: not control._polling)
    assert control.connected and not control.error and control.devices

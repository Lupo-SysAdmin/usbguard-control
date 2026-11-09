"""Keyboard operation and the accessible names exposed by the real QML controls."""
from pathlib import Path
import time

import pytest
from PySide6.QtCore import QEvent, QObject, Qt, QUrl
from PySide6.QtGui import QAccessible, QGuiApplication, QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from shiboken6 import delete

from usbguard_control.controller import Controller
from usbguard_control.localization import Language, Translator


def settle(app, seconds=.1):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        app.processEvents()
        time.sleep(.005)


def luminance(color):
    channels = (color.redF(), color.greenF(), color.blueF())
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
              for c in channels]
    return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))


def key_click(window, key):
    for event_type in (QEvent.KeyPress, QEvent.KeyRelease):
        QGuiApplication.sendEvent(window, QKeyEvent(event_type, key, Qt.NoModifier))


@pytest.mark.parametrize('locale', ['es-419', 'en-US'])
def test_device_rows_reachable_by_tab_and_scrolled_into_view(locale):
    app = QGuiApplication.instance() or QGuiApplication([])
    language = Language(locale)
    translator = Translator(language)
    app.installTranslator(translator)
    control = Controller(demo=True, language=language)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('control', control)
    engine.rootContext().setContextProperty('language', language)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / 'src/usbguard_control/qml/Main.qml')))
    try:
        window = engine.rootObjects()[0]
        window.resize(900, 620)
        settle(app, .3)
        device_list = window.findChild(QObject, 'deviceList')
        window.findChild(QObject, 'searchField').forceActiveFocus()
        visited = []
        for _ in range(20):
            key_click(window, Qt.Key_Tab)
            settle(app, .03)
            focused = window.activeFocusItem()
            if 'ItemDelegate' not in focused.metaObject().className():
                continue
            interface = QAccessible.queryAccessibleInterface(focused)
            expected = control.devices[len(visited)]
            assert interface.text(QAccessible.Name).startswith(expected['name'] + ', ')
            # The focused row must be inside the clipped list, even at 900x620.
            top = focused.mapToItem(device_list, 0, 0).y()
            assert top >= -1
            assert top + focused.height() <= device_list.height() + 1
            key_click(window, Qt.Key_Space)
            settle(app, .03)
            assert control.selected['id'] == expected['id']
            visited.append(expected['id'])
            if len(visited) == len(control.devices):
                break
        assert visited == [device['id'] for device in control.devices]
        # A failed export must expose its localized error without moving focus.
        before_error = window.activeFocusItem()
        control.exportActivity('https://example.invalid/activity.json')
        settle(app)
        assert window.activeFocusItem() == before_error
        message = window.findChild(QObject, 'statusMessage')
        for _ in range(30):
            key_click(window, Qt.Key_Tab)
            settle(app, .01)
            if message.hasActiveFocus():
                break
        assert message.hasActiveFocus()
        interface = QAccessible.queryAccessibleInterface(message)
        assert interface.text(QAccessible.Name) == language.text('Selecciona un archivo local.')
    finally:
        control.shutdown()
        delete(engine)
        app.removeTranslator(translator)
        app.processEvents()


@pytest.mark.parametrize('locale,settings_name', [('es-419', 'Configuración'),
                                                 ('en-US', 'Settings')])
def test_keyboard_settings_accessible_labels_and_primary_contrast(locale, settings_name):
    app = QGuiApplication.instance() or QGuiApplication([])
    language = Language(locale)
    translator = Translator(language)
    app.installTranslator(translator)
    control = Controller(demo=True, language=language)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('control', control)
    engine.rootContext().setContextProperty('language', language)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / 'src/usbguard_control/qml/Main.qml')))
    try:
        window = engine.rootObjects()[0]
        assert isinstance(window, QQuickWindow)
        settle(app, .3)
        settings = window.findChild(QObject, 'settingsButton')
        interface = QAccessible.queryAccessibleInterface(settings)
        assert interface.text(QAccessible.Name) == settings_name
        assert interface.role() == QAccessible.Button
        settings.forceActiveFocus()
        key_click(window, Qt.Key_Space)
        settle(app)
        dialog = window.findChild(QObject, 'settingsDialog')
        assert dialog.property('visible'), 'Settings must open using the keyboard'
        remember = window.findChild(QObject, 'rememberService')
        interface = QAccessible.queryAccessibleInterface(remember)
        assert interface.text(QAccessible.Name) == remember.property('text')
        assert interface.role() == QAccessible.CheckBox
        assert interface.state().checked
        remember.forceActiveFocus()
        key_click(window, Qt.Key_Space)
        settle(app)
        assert not remember.property('checked')
        assert not interface.state().checked
        key_click(window, Qt.Key_Tab)
        settle(app)
        start = window.findChild(QObject, 'startServiceButton')
        assert start.hasActiveFocus(), 'Tab must reach Start from the boot preference'
        fg = luminance(start.property('contentItem').property('color'))
        bg = luminance(start.property('background').property('color'))
        assert (max(fg, bg) + .05) / (min(fg, bg) + .05) >= 4.5
        key_click(window, Qt.Key_Space)
        settle(app)
        assert control.serviceConfirmation == {'action': 'start', 'remember': False}
        key_click(window, Qt.Key_Escape)
        settle(app)
        assert not control.serviceConfirmation
        assert all(u['active'] == 'active' for u in control.serviceState['units'])
    finally:
        control.shutdown()
        delete(engine)
        app.removeTranslator(translator)
        app.processEvents()

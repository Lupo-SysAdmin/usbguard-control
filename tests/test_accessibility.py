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

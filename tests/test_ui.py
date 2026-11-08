import json
from pathlib import Path
import time
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from shiboken6 import delete
from usbguard_control.controller import Controller
from usbguard_control.localization import Language, Translator
from PySide6.QtCore import QSettings


def spin(app, predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert predicate()


def test_qml_workflow_search_authorize_reconnect_export_and_credit(tmp_path):
    app = QGuiApplication.instance() or QGuiApplication([])
    language = Language(settings=QSettings(str(tmp_path / "preferences.ini"), QSettings.IniFormat))
    translator = Translator(language)
    app.installTranslator(translator)
    control = Controller(demo=True, language=language)
    engine = QQmlApplicationEngine()
    messages = []
    engine.warnings.connect(lambda warnings: messages.extend(w.toString() for w in warnings))
    engine.rootContext().setContextProperty("control", control)
    engine.rootContext().setContextProperty("language", language)
    language.changed.connect(engine.retranslate)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "src/usbguard_control/qml/Main.qml")))
    try:
        assert engine.rootObjects()
        window = engine.rootObjects()[0]
        assert isinstance(window, QQuickWindow)
        spin(app, lambda: control.connected and not control.busy)
        assert len(control.devices) == 4
        QMetaObject.invokeMethod(window.findChild(QObject, "englishButton"), "clicked", Qt.DirectConnection)
        app.processEvents()
        assert language.locale == "en-US"
        assert window.findChild(QObject, "allowAlwaysButton").property("text") == "Always allow"
        assert control.selected["status"] == "Blocked"
        assert control.selected["name"] == "Crucial X8 SSD"
        assert "Demo mode started" in control.events[0]["message"]
        control.search("Crucial")
        assert len(control.devices) == 1
        control.search("")
        control.select(12)
        app.processEvents()
        button = window.findChild(QObject, "allowAlwaysButton")
        assert button.property("enabled")
        QMetaObject.invokeMethod(button, "clicked", Qt.DirectConnection)
        assert control.confirmation["permanent"]
        QMetaObject.invokeMethod(window.findChild(QObject, "confirmActionButton"), "clicked", Qt.DirectConnection)
        spin(app, lambda: not control.busy and control.selected.get("target") == "allow")
        control.simulate()
        spin(app, lambda: not control.busy and not any(d["id"] == 12 for d in control.devices))
        control.simulate()
        spin(app, lambda: not control.busy and any(d["id"] == 12 for d in control.devices))
        assert next(d for d in control.devices if d["id"] == 12)["target"] == "allow"
        control.select(9)
        app.processEvents()
        assert not window.findChild(QObject, "blockButton").property("enabled")
        control.showInfrastructure(True)
        assert len(control.devices) == 5
        control.exportActivity(QUrl.fromLocalFile(str(tmp_path / "events.json")).toString())
        assert json.loads((tmp_path / "events.json").read_text())["demo"] is True
        assert json.loads((tmp_path / "events.json").read_text())["locale"] == "en-US"
        QMetaObject.invokeMethod(window.findChild(QObject, "spanishButton"), "clicked", Qt.DirectConnection)
        app.processEvents()
        assert window.findChild(QObject, "allowAlwaysButton").property("text") == "Permitir siempre"
        assert any("regla guardada" in e["message"] for e in control.events)
        window.setWidth(900)
        window.setHeight(620)
        app.processEvents()
        assert not window.grabWindow().isNull()
        assert not messages
    finally:
        control.shutdown()
        delete(engine)
        app.removeTranslator(translator)
        app.processEvents()

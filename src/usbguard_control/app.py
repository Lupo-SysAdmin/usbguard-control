# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import os
from pathlib import Path
import sys

from PySide6.QtCore import QSettings, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # Registers the window type for QML roots.
from shiboken6 import delete
from . import __version__
from .controller import Controller
from .localization import Language, Translator


def main(argv=None):
    parser = argparse.ArgumentParser(description="USBGuard Control — Jan Herrera")
    parser.add_argument("--demo", action="store_true", help="Simulación sin acceso a USBGuard")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--language", choices=("es-419", "en-US"), help="Idioma inicial de esta ejecución")
    parser.add_argument("--screenshot", type=Path, help="Captura de la demostración y termina")
    args = parser.parse_args(argv)
    if args.screenshot and not args.demo:
        parser.error("--screenshot requiere --demo")
    if os.geteuid() == 0 and not args.demo:
        parser.error("Ejecuta la interfaz como usuario normal; USBGuard gestiona los privilegios.")
    if not args.demo:
        try:
            from gi.repository import Gio  # noqa: F401
        except ImportError:
            parser.error("Falta PyGObject. En Kali: sudo apt install python3-gi")
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("USBGuard Control")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Lupo-SysAdmin")
    app.setDesktopFileName("io.github.LupoSysAdmin.USBGuardControl")
    language = Language(args.language, QSettings())
    translator = Translator(language)
    app.installTranslator(translator)
    directory = Path(__file__).parent
    app.setWindowIcon(QIcon(str(directory / "assets/shield.svg")))
    engine = QQmlApplicationEngine()
    controller = Controller(args.demo, language)
    engine.rootContext().setContextProperty("control", controller)
    engine.rootContext().setContextProperty("language", language)
    language.changed.connect(engine.retranslate)
    engine.load(QUrl.fromLocalFile(str(directory / "qml/Main.qml")))
    if not engine.rootObjects():
        controller.shutdown()
        return 1
    app.aboutToQuit.connect(controller.shutdown)
    if args.screenshot:
        def capture():
            try:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                window = engine.rootObjects()[0]
                ok = isinstance(window, QQuickWindow) and window.grabWindow().save(str(args.screenshot))
                app.exit(0 if ok else 1)
            except Exception as error:
                print(f"No se pudo guardar la captura: {error}", file=sys.stderr)
                app.exit(1)
        QTimer.singleShot(1400, capture)
    result = app.exec()
    delete(engine)  # Destroy QML bindings while the context object is still alive.
    return result


if __name__ == "__main__":
    raise SystemExit(main())

# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import os
from pathlib import Path
import sys

from PySide6.QtCore import QSettings, QTimer, QUrl, QStandardPaths
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # Registers the window type for QML roots.
from PySide6.QtQuickControls2 import QQuickStyle
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
    parser.add_argument('--background', action='store_true', help='Observar en segundo plano; vuelve a abrir la aplicación para mostrarla')
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
    app = QApplication([sys.argv[0]])
    # The desktop platform theme may override environment style preferences.
    QQuickStyle.setStyle('Basic')
    app.setApplicationName("USBGuard Control")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Lupo-SysAdmin")
    app.setDesktopFileName("io.github.LupoSysAdmin.USBGuardControl")
    server = None
    desktop_holder = []
    if not args.demo:
        from .desktop import claim_instance
        try:
            server = claim_instance(app, lambda: desktop_holder[0].activate() if desktop_holder else None)
        except RuntimeError as error:
            parser.error(str(error))
        if server is None: return 0
    settings = None if args.demo else QSettings()
    language = Language(args.language, settings)
    translator = Translator(language)
    app.installTranslator(translator)
    directory = Path(__file__).parent
    app.setWindowIcon(QIcon(str(directory / "assets/shield.svg")))
    engine = QQmlApplicationEngine()
    directory_data = None if args.demo else Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
    controller = Controller(args.demo, language, directory_data)
    engine.rootContext().setContextProperty("control", controller)
    engine.rootContext().setContextProperty("language", language)
    language.changed.connect(engine.retranslate)
    engine.load(QUrl.fromLocalFile(str(directory / "qml/Main.qml")))
    if not engine.rootObjects():
        controller.shutdown()
        return 1
    window = engine.rootObjects()[0]
    desktop = None
    if not args.demo:
        from .desktop import DesktopIntegration
        desktop = DesktopIntegration(app, controller, window)
        desktop_holder.append(desktop)
        desktop.server = server
        app.setQuitOnLastWindowClosed(False)
        if args.background:
            controller.workspace.setBackground(True)
            window.hide()
    app.styleHints().colorSchemeChanged.connect(lambda _scheme: controller.workspace.changed.emit())
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

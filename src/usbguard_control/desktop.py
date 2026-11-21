# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""User-session integration. No system services or USB policy writes."""
import os
from pathlib import Path
from PySide6.QtCore import QObject, QStandardPaths, QLockFile
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from .storage import private_write


class DesktopIntegration(QObject):
    def __init__(self, app, control, window):
        super().__init__(app)
        self.app, self.control, self.window = app, control, window
        self.tray = None
        self.socket = None
        self.server = None
        self.path = Path(QStandardPaths.writableLocation(QStandardPaths.ConfigLocation)) / 'autostart/io.github.LupoSysAdmin.USBGuardControl.desktop'
        control.workspace.showWindow.connect(self.activate)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(app.windowIcon(), self)
            self.menu = QMenu()
            show_action = self.menu.addAction(control.language.text('Abrir USBGuard Control'), self.activate)
            quit_action = self.menu.addAction(control.language.text('Salir de la interfaz'), app.quit)
            def translate_menu():
                show_action.setText(control.language.text('Abrir USBGuard Control'))
                quit_action.setText(control.language.text('Salir de la interfaz'))
            control.language.changed.connect(translate_menu)
            self.tray.setContextMenu(self.menu)
            self.tray.activated.connect(lambda reason: self.activate() if reason == QSystemTrayIcon.Trigger else None)
            self.tray.setToolTip('USBGuard Control')
            self.tray.show()
        control.workspace.desktop = self
        control.workspace.background_available = True
        control.workspace.changed.emit()

    def activate(self):
        self.window.showNormal()
        self.window.raise_()
        self.window.requestActivate()

    def set_autostart(self, enabled):
        # Only the packaged launcher is a stable target across user sessions.
        if not str(Path(__file__).resolve()).startswith('/usr/share/usbguard-control/'):
            raise ValueError('El inicio de sesión requiere instalar el paquete de esta versión.')
        if enabled:
            private_write(self.path, '[Desktop Entry]\nType=Application\nName=USBGuard Control\nExec=/usr/bin/usbguard-control --background\nIcon=usbguard-control\nTerminal=false\nX-GNOME-Autostart-enabled=true\n')
        elif self.path.exists():
            self.path.unlink()


def claim_instance(app, activate):
    """Return server for first instance, None after activating the existing one."""
    directory = QStandardPaths.writableLocation(QStandardPaths.RuntimeLocation)
    if not directory:
        raise RuntimeError('No se encontró el directorio de la sesión de usuario.')
    name = str(Path(directory) / 'usbguard-control-desktop.sock')
    socket = QLocalSocket()
    socket.connectToServer(name)
    if socket.waitForConnected(300):
        socket.write(b'activate\n'); socket.waitForBytesWritten(300); socket.disconnectFromServer()
        return None
    lock = QLockFile(name + '.lock')
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        socket.connectToServer(name)
        if socket.waitForConnected(1000):
            socket.write(b'activate\n'); socket.waitForBytesWritten(300)
            return None
        raise RuntimeError('USBGuard Control ya se está iniciando. Vuelve a abrirlo en un momento.')
    server = QLocalServer(app)
    server.instance_lock = lock
    server.setSocketOptions(QLocalServer.UserAccessOption)
    QLocalServer.removeServer(name)
    if not server.listen(name): raise RuntimeError(server.errorString())
    def connected():
        while server.hasPendingConnections():
            client = server.nextPendingConnection()
            activate()
            client.disconnectFromServer()
            client.deleteLater()
    server.newConnection.connect(connected)
    return server

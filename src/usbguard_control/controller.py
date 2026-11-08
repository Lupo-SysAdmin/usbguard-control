# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, QTimer, QUrl, Signal, Slot
from .backend import friendly_error
from .demo import DemoBackend
from .domain import display_text
from .localization import Language
from .translations import message


class Worker(QObject):
    done = Signal(str, object)
    failed = Signal(str, str)
    event = Signal(str, object)

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self.backend = None
        self.context = None
        self.cancel = None

    @Slot()
    def start(self):
        if not self.demo:
            from gi.repository import Gio, GLib
            self.cancel = Gio.Cancellable()
            self.context = GLib.MainContext.new()
            self.context.push_thread_default()
            self.pump = QTimer(self)
            self.pump.timeout.connect(self.drain)
            self.pump.start(80)

    def drain(self):
        for _ in range(32):
            if not self.context.pending():
                break
            self.context.iteration(False)

    @Slot(str, object)
    def run(self, operation, arguments):
        try:
            if self.backend is None:
                if self.demo:
                    self.backend = DemoBackend()
                else:
                    from .backend import SystemBackend
                    self.backend = SystemBackend(self.event.emit, cancellable=self.cancel)
            if operation == "refresh":
                result = self.backend.snapshot()
            elif operation == "apply":
                result = self.backend.apply(*arguments)
            elif operation == "simulate":
                result = self.backend.toggle_connection()
            elif operation == "notify":
                self.notify(arguments)
                result = None
            else:
                raise ValueError("Operación desconocida")
            self.done.emit(operation, result)
        except Exception as error:
            self.failed.emit(operation, friendly_error(error))

    def notify(self, content):
        if self.demo:
            return
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, self.cancel)
        bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications", "Notify", GLib.Variant("(susssasa{sv}i)",
            ("USBGuard Control", 0, "usbguard-control", content[0], content[1], [], {}, 5000)),
            GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NO_AUTO_START, 1000, self.cancel)

    @Slot()
    def stop(self):
        if self.backend and hasattr(self.backend, "close"):
            self.backend.close()
        if self.context:
            self.pump.stop()
            self.context.pop_thread_default()
        QThread.currentThread().quit()


class Controller(QObject):
    changed = Signal()
    confirmationChanged = Signal()
    request = Signal(str, object)
    stopping = Signal()

    def __init__(self, demo=False, language=None):
        super().__init__()
        self.language = language or Language()
        self.language.changed.connect(self.changed.emit)
        self.language.saveFailed.connect(lambda error: self.failed("language", error))
        self._demo = demo
        self._devices = []
        self._events = []
        self._selected = -1
        self._selection_initialized = False
        self._query = ""
        self._filter = "all"
        self._advanced = False
        self._connected = False
        self._busy = False
        self._error = ""
        self._notice = ""
        self._notice_context = None
        self._policy = "Consultando política…"
        self._owner = ""
        self._pending = None
        self._notifications = True
        self._event_count = 0
        self._last_error = ""
        self.notice_timer = QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.setInterval(6000)
        self.notice_timer.timeout.connect(self.clearNotice)
        self.thread = QThread(self)
        self.worker = Worker(demo)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(self.worker.deleteLater)
        self.request.connect(self.worker.run)
        self.stopping.connect(self.worker.stop)
        self.worker.done.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker.event.connect(self.device_event)
        self.thread.start()
        self.poll = QTimer(self)
        self.poll.setInterval(5000)
        self.poll.timeout.connect(self.refresh)
        self.poll.start()
        self.coalesce = QTimer(self)
        self.coalesce.setSingleShot(True)
        self.coalesce.setInterval(900)
        self.coalesce.timeout.connect(self.flush_events)
        self.add_event("Sesión", "Modo demostración iniciado · los cambios son simulados" if demo else "Conectando con USBGuard")
        QTimer.singleShot(0, self.refresh)

    @Property(bool, constant=True)
    def demo(self): return self._demo
    @Property(bool, notify=changed)
    def connected(self): return self._connected
    @Property(bool, notify=changed)
    def busy(self): return self._busy
    @Property(str, notify=changed)
    def error(self): return self.language.text(self._error)
    @Property(str, notify=changed)
    def notice(self): return self.language.text(self._notice)
    @Property(str, notify=changed)
    def policy(self): return self.language.text(self._policy)
    @Property(bool, notify=changed)
    def advanced(self): return self._advanced
    @Property(bool, notify=changed)
    def notifications(self): return self._notifications
    @Property(int, notify=changed)
    def allowedCount(self): return sum(d.target == "allow" and not d.infrastructure for d in self._devices)
    @Property(int, notify=changed)
    def blockedCount(self): return sum(d.target != "allow" and not d.infrastructure for d in self._devices)
    @Property(int, notify=changed)
    def infrastructureCount(self): return sum(d.infrastructure for d in self._devices)
    @Property("QVariantList", notify=changed)
    def devices(self):
        return [self.localize_device(d) for d in self._devices
                if (self._advanced or not d.infrastructure)
                and (self._filter == "all" or (d.target == "allow") == (self._filter == "allow"))
                and self._query.casefold() in (d.name + " " + d.usb_id + " " + self.language.text(d.kind)).casefold()]
    @Property("QVariantMap", notify=changed)
    def selected(self):
        return next((self.localize_device(d) for d in self._devices if d.id == self._selected), {})
    @Property("QVariantList", notify=changed)
    def events(self):
        return [{**event, "category": self.language.text(event["category"]),
                 "message": self.language.text(event["message"])} for event in self._events]
    @Property("QVariantMap", notify=confirmationChanged)
    def confirmation(self):
        if not self._pending: return {}
        device, target, permanent, _owner = self._pending
        return {"name": display_text(device.name), "target": target, "permanent": permanent,
                "sensitive": device.sensitive}

    def localize_device(self, device):
        result = device.as_dict()
        for key in ("kind", "status"):
            result[key] = self.language.text(result[key])
        for key, absent in (("name", not display_text(device.name)), ("serial", not display_text(device.serial)),
                            ("port", not device.port), ("interfaces", not device.interfaces)):
            if absent:
                result[key] = self.language.text(result[key])
        return result

    def add_event(self, category, message):
        self._events.insert(0, {"time": datetime.now().astimezone().isoformat(timespec="seconds"),
                                "category": category, "message": message})
        del self._events[200:]
        self.changed.emit()

    def dispatch(self, operation, args=None):
        if self._busy: return
        self._busy = True
        self.changed.emit()
        self.request.emit(operation, args)

    @Slot()
    def refresh(self):
        self.dispatch("refresh")

    @Slot(int)
    def select(self, device_id):
        self._selected = device_id
        self._selection_initialized = True
        self.changed.emit()

    @Slot(str)
    def search(self, query):
        self._query = query
        self.changed.emit()

    @Slot(str)
    def filter(self, value):
        if value in ("all", "allow", "block"):
            self._filter = value
            self.changed.emit()

    @Slot(bool)
    def showInfrastructure(self, value):
        self._advanced = value
        self.changed.emit()

    @Slot(bool)
    def setNotifications(self, value):
        self._notifications = value
        self.changed.emit()

    @Slot(str, bool)
    def prepare(self, target, permanent):
        if not self._connected or self._busy: return
        device = next((d for d in self._devices if d.id == self._selected), None)
        if device is None: return
        from .domain import validate_action
        try:
            validate_action(device, device, target)
        except ValueError as error:
            self._error = str(error)
            self.changed.emit()
            return
        self._pending = (device, target, permanent, self._owner)
        self.confirmationChanged.emit()

    @Slot()
    def confirm(self):
        if not self._pending or self._busy: return
        args = self._pending
        self._action = args
        self._pending = None
        self.confirmationChanged.emit()
        self.dispatch("apply", args)

    @Slot()
    def cancel(self):
        self._pending = None
        self.confirmationChanged.emit()

    @Slot()
    def simulate(self):
        if self._demo: self.dispatch("simulate")

    @Slot()
    def clearNotice(self):
        self._notice = ""
        self._notice_context = None
        self.notice_timer.stop()
        self.changed.emit()

    def show_notice(self, text, context=None):
        self._notice = text
        self._notice_context = context
        self.notice_timer.start()

    @Slot(str)
    def exportActivity(self, url):
        path = QUrl(url).toLocalFile()
        if not path:
            self._error = "Selecciona un archivo local."
        else:
            try:
                Path(path).write_text(json.dumps({"application": "USBGuard Control", "demo": self._demo,
                    "scope": "current session only", "locale": self.language.locale, "events": self.events}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                self.show_notice("Actividad exportada.")
            except OSError as error:
                self._error = str(error)
        self.changed.emit()

    @Slot(str, object)
    def completed(self, operation, result):
        self._busy = False
        if operation == "refresh":
            self._connected = True
            self._error = ""
            self._last_error = ""
            self._devices = result["devices"]
            self._owner = result["owner"]
            if self._notice_context:
                expected, target, owner = self._notice_context
                current = next((d for d in self._devices if d.id == expected.id), None)
                if (owner != self._owner or current is None
                        or current.identity != expected.identity or current.target != target):
                    self.clearNotice()
            values = {"block": "bloquear", "allow": "permitir", "reject": "rechazar", "apply-policy": "evaluar reglas", "unknown": "no disponible"}
            self._policy = message("Nuevos: {inserted} · Sin coincidencia: {implicit}",
                inserted=message(values.get(result['inserted'], result['inserted'])),
                implicit=message(values.get(result['implicit'], result['implicit'])))
            if not self._selection_initialized and self._devices:
                self._selected = next((d.id for d in self._devices if not d.infrastructure), self._devices[0].id)
                self._selection_initialized = True
            elif not any(d.id == self._selected for d in self._devices):
                self._selected = -1
        elif operation == "apply":
            device, target, permanent, owner = self._action
            verb = "Permitido" if target == "allow" else "Bloqueado"
            scope = message("regla guardada #{id}", id=result) if permanent else message("decisión temporal")
            self.show_notice(message("{status}: {name} · {scope}", status=message(verb), name=display_text(device.name), scope=scope),
                             (device, target, owner))
            self.add_event("Simulación" if self._demo else "Acción", self._notice)
            self.refresh()
        elif operation == "simulate":
            self.add_event("Simulación", result)
            self.refresh()
        self.changed.emit()

    @Slot(str, str)
    def failed(self, operation, message):
        self._busy = False
        if operation == "notify": return
        self._error = message
        if operation == "refresh":
            self.clearNotice()
            self._connected = False
            self._devices = []
            self._selected = -1
            self._policy = "Política no disponible"
        if message != self._last_error:
            self.add_event("Error", message)
            self._last_error = message
        self.changed.emit()

    @Slot(str, object)
    def device_event(self, member, args):
        if member == "DevicePresenceChanged":
            self._event_count += 1
            action = {0: "Presente · ID {id}", 1: "Conectado · ID {id}", 2: "Actualizado · ID {id}", 3: "Desconectado · ID {id}"}.get(args[1], "Cambio · ID {id}")
            self.add_event("Dispositivo", message(action, id=args[0]))
        elif member in ("DevicePolicyChanged", "DevicePolicyApplied"):
            self.add_event("Política", message("Decisión de USBGuard actualizada · ID {id}", id=args[0]))
        elif member == "ExceptionMessage":
            self.add_event("Error", "USBGuard notificó una excepción. Revisa el registro del servicio.")
        self.coalesce.start()

    def flush_events(self):
        if self._busy:
            self.coalesce.start()
            return
        count, self._event_count = self._event_count, 0
        if count and self._notifications and not self._demo:
            self.dispatch("notify", (self.language.text("Actividad USB"), self.language.text(message(
                "{count} cambios detectados. Abre USBGuard Control para revisarlos.", count=count))))
            QTimer.singleShot(1200, self.refresh)
        else:
            self.refresh()

    def shutdown(self):
        self.poll.stop()
        self.coalesce.stop()
        self.notice_timer.stop()
        if self.worker.cancel:
            self.worker.cancel.cancel()
        self.stopping.emit()
        self.thread.wait()

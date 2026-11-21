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
from .services import DemoServiceManager, manageable
from .workspace import Workspace
from .storage import private_json
from .policy import backup_document


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
        self.services = None
        self.notification_bus = None
        self.notification_subscription = None
        self.notification_ids = set()

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
            if self.services is None:
                if self.demo:
                    self.services = DemoServiceManager()
                else:
                    from .services import ServiceManager
                    self.services = ServiceManager(connection=self.backend.bus, cancellable=self.cancel)
            if operation in ("refresh", "poll"):
                try:
                    state = self.services.snapshot()
                except Exception as error:
                    state = {"units": [], "error": friendly_error(error)}
                self.done.emit("services", state)
                if self.demo and state["units"][0]["active"] != "active":
                    raise ValueError("El servicio está detenido.")
                result = self.backend.snapshot()
            elif operation == "service":
                result = self.services.apply(*arguments)
            elif operation == "apply":
                result = self.backend.apply(*arguments)
            elif operation == 'policy-preview':
                result = self.backend.preview_policy(*arguments)
            elif operation == 'policy-commit':
                preview, directory = arguments
                if directory is None and self.demo:
                    import tempfile
                    with tempfile.TemporaryDirectory(prefix='usbguard-demo-') as temporary:
                        result = self.backend.commit_policy(preview, temporary)
                        result['backup'] = ''
                else:
                    result = self.backend.commit_policy(preview, directory)
            elif operation == 'policy-backup':
                snapshot = self.backend.policy_snapshot()
                private_json(arguments, backup_document(snapshot['rules']))
                result = arguments
            elif operation == 'diagnose-phone':
                import shutil
                import subprocess
                if self.demo:
                    result = 'Diagnóstico simulado. No se consultó ningún teléfono.'
                elif not shutil.which('idevicepair'):
                    result = 'Falta idevicepair (paquete libimobiledevice-utils).'
                else:
                    check = subprocess.run(['idevicepair', 'validate'], capture_output=True, timeout=12)
                    result = ('Emparejamiento válido. Si Archivos falla, revisa GVfs y vuelve a abrir el dispositivo.' if check.returncode == 0
                              else 'No se confirmó el emparejamiento. Desbloquea el iPhone y revisa el aviso Confiar y la conexión USB.')
            elif operation == "simulate":
                result = self.backend.toggle_connection()
            elif operation == "notify":
                self.notify(arguments)
                result = None
            else:
                raise ValueError("Operación desconocida")
            self.done.emit(operation, result)
        except Exception as error:
            detail = friendly_error(error)
            if operation == "service" and any(word in str(error).lower() for word in
                    ("accessdenied", "not authorized", "authorization", "permission denied")):
                detail = "Operación no autorizada o cancelada. Comprueba el agente de autenticación del escritorio."
            self.failed.emit(operation, detail)

    def notify(self, content):
        if self.demo:
            return
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, self.cancel)
        if self.notification_subscription is None:
            self.notification_bus = bus
            def action(_bus, _sender, _path, _interface, _member, parameters, _data):
                notification_id, key = parameters.unpack()
                if notification_id in self.notification_ids and key == 'open':
                    self.event.emit('NotificationOpen', ())
            self.notification_subscription = bus.signal_subscribe('org.freedesktop.Notifications',
                'org.freedesktop.Notifications', 'ActionInvoked', '/org/freedesktop/Notifications',
                None, Gio.DBusSignalFlags.NONE, action, None)
        result = bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications", "Notify", GLib.Variant("(susssasa{sv}i)",
            ("USBGuard Control", 0, "usbguard-control", content[0], content[1], ['open', content[2]], {}, 5000)),
            GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NO_AUTO_START, 1000, self.cancel)
        # Bound memory; only notifications emitted by this observer activate it.
        self.notification_ids = {result.unpack()[0]}

    @Slot()
    def stop(self):
        if self.notification_bus and self.notification_subscription is not None:
            self.notification_bus.signal_unsubscribe(self.notification_subscription)
        if self.backend and hasattr(self.backend, "close"):
            self.backend.close()
        if self.context:
            self.pump.stop()
            self.context.pop_thread_default()
        QThread.currentThread().quit()


class Controller(QObject):
    changed = Signal()
    selectedChanged = Signal()
    confirmationChanged = Signal()
    serviceConfirmationChanged = Signal()
    request = Signal(str, object)
    stopping = Signal()

    def __init__(self, demo=False, language=None, data_dir=None):
        super().__init__()
        self.language = language or Language()
        self.language.changed.connect(self.changed.emit)
        self.language.saveFailed.connect(lambda error: self.failed("language", error))
        self._demo = demo
        self._devices = []
        self._events = []
        self._selected = -1
        self._selected_view = {}
        self._selection_initialized = False
        self._query = ""
        self._filter = "all"
        self._advanced = False
        self._connected = False
        self._busy = False
        self._polling = False
        self._error = ""
        self._notice = ""
        self._notice_context = None
        self._policy = "Consultando política…"
        self._owner = ""
        self._pending = None
        self._service = {"units": []}
        self._service_error = ""
        self._pending_service = None
        self._service_working = False
        self._notifications = True
        self._event_count = 0
        self._last_error = ""
        self._workspace = Workspace(self, data_dir)
        self._advanced = self._workspace.pref_bool('advanced', False)
        self._notifications = self._workspace.pref_bool('notifications', True)
        saved_filter = self._workspace.pref('filter', 'all')
        self._filter = saved_filter if saved_filter in ('all', 'allow', 'block') else 'all'
        self._workspace.changed.connect(self.sync_selected)
        self.changed.connect(self._workspace.changed.emit)
        self.changed.connect(self.sync_selected)
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
        self.poll.timeout.connect(self.pollBackground)
        self.poll.start()
        self.coalesce = QTimer(self)
        self.coalesce.setSingleShot(True)
        self.coalesce.setInterval(900)
        self.coalesce.timeout.connect(self.flush_events)
        self.add_event("Sesión", "Modo demostración iniciado · los cambios son simulados" if demo else "Conectando con USBGuard")
        QTimer.singleShot(0, self.refresh)

    @Property(bool, constant=True)
    def demo(self): return self._demo
    @Property(QObject, constant=True)
    def workspace(self): return self._workspace
    @Property(str, notify=changed)
    def activeFilter(self): return self._filter
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
    @Property(bool, notify=changed)
    def serviceWorking(self): return self._service_working
    @Property("QVariantMap", notify=changed)
    def serviceState(self):
        labels = {"active": "Activo", "inactive": "Detenido", "failed": "Falló",
                  "activating": "Iniciando…", "deactivating": "Deteniendo…",
                  "enabled": "Inicio automático", "disabled": "Sin inicio automático",
                  "enabled-runtime": "Habilitado solo en esta sesión", "masked": "Enmascarado",
                  "masked-runtime": "Enmascarado", "not-found": "No instalado"}
        units = [{**u, "activeLabel": self.language.text(labels.get(u["active"], "Desconocido")),
                  "bootLabel": self.language.text(labels.get(u["boot"], "Desconocido"))}
                 for u in self._service.get("units", [])]
        return {"units": units, "manageable": manageable(self._service),
                "error": self.language.text(self._service_error or self._service.get("error", ""))}
    @Property("QVariantMap", notify=serviceConfirmationChanged)
    def serviceConfirmation(self):
        if not self._pending_service: return {}
        action, remember, _expected = self._pending_service
        return {"action": action, "remember": remember}
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
                and self._query.casefold() in (d.name + " " + self._workspace.device_alias(d) + " " + d.usb_id + " " + self.language.text(d.kind)).casefold()]
    @Property("QVariantMap", notify=selectedChanged)
    def selected(self):
        return self._selected_view
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
        result['originalName'] = result['name']
        result['alias'] = self._workspace.device_alias(device)
        if result['alias']: result['name'] = result['alias']
        result['functions'] = ' · '.join(self.language.text(f) for f in device.functions)
        result['explanation'] = self._workspace.explanation(device)
        for key in ("kind", "status"):
            result[key] = self.language.text(result[key])
        for key, absent in (("name", not display_text(device.name)), ("serial", not display_text(device.serial)),
                            ("port", not device.port), ("interfaces", not device.interfaces)):
            if absent:
                result[key] = self.language.text(result[key])
        return result

    def sync_selected(self):
        selected = next((self.localize_device(d) for d in self._devices if d.id == self._selected), {})
        if selected != self._selected_view:
            self._selected_view = selected
            self.selectedChanged.emit()

    def add_event(self, category, message):
        self._events.insert(0, {"time": datetime.now().astimezone().isoformat(timespec="seconds"),
                                "category": category, "message": message})
        del self._events[200:]
        self._workspace.record(self._events[0])
        self.changed.emit()

    def dispatch(self, operation, args=None):
        if self._busy: return
        self._busy = True
        self.changed.emit()
        self.request.emit(operation, args)

    @Slot()
    def refresh(self):
        self.dispatch("refresh")

    @Slot()
    def pollBackground(self):
        if self._busy or self._polling: return
        self._polling = True
        # The worker serializes requests. User actions may queue behind this
        # read without disabling their controls or losing the click.
        self.request.emit("poll", None)

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
            self._workspace.save('filter', value)
            self.changed.emit()

    @Slot(bool)
    def showInfrastructure(self, value):
        self._advanced = value
        self._workspace.save('advanced', value)
        self.changed.emit()

    @Slot(bool)
    def setNotifications(self, value):
        self._notifications = value
        self._workspace.save('notifications', value)
        self.changed.emit()

    @Slot(str, bool)
    def prepareService(self, action, remember):
        if self._busy or not manageable(self._service) or action not in ("start", "stop"):
            return
        self._service_error = ""
        self._pending_service = (action, remember, self._service)
        self.serviceConfirmationChanged.emit()
        self.changed.emit()

    @Slot()
    def cancelService(self):
        self._pending_service = None
        self.serviceConfirmationChanged.emit()

    @Slot()
    def confirmService(self):
        if self._busy or not self._pending_service: return
        args = self._pending_service
        self._service_action = args
        self.cancelService()
        self._service_working = True
        self.dispatch("service", args)

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
        if operation == "services":
            if self._service != result:
                self._service = result
                self.changed.emit()
            return
        if operation == "poll":
            self._polling = False
        else:
            self._busy = False
        if operation in ("refresh", "poll"):
            before = (self._connected, self._error, self._devices, self._owner, self._policy, self._selected)
            if operation == "refresh" or not self._connected:
                self._error = ""
                self._last_error = ""
            self._connected = True
            self._devices = result["devices"]
            self._owner = result["owner"]
            self._workspace.update_snapshot(result)
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
            after = (self._connected, self._error, self._devices, self._owner, self._policy, self._selected)
            if operation == "poll" and before == after:
                return
        elif operation == "apply":
            device, target, permanent, owner = self._action
            verb = "Permitido" if target == "allow" else "Bloqueado"
            scope = message("regla guardada #{id}", id=result) if permanent else message("decisión temporal")
            reason = message('Regla guardada por esta aplicación: #{id}.', id=result) if permanent else 'Decisión temporal tomada en esta sesión.'
            self._workspace.decisions[device.id] = (device.identity, target, owner, reason)
            self.show_notice(message("{status}: {name} · {scope}", status=message(verb), name=display_text(device.name), scope=scope),
                             (device, target, owner))
            self.add_event("Simulación" if self._demo else "Acción", self._notice)
            self.refresh()
        elif operation == 'policy-preview':
            self._workspace.pending = result
            self._workspace.confirmationChanged.emit()
        elif operation == 'policy-commit':
            self._workspace.decisions.clear()
            self.show_notice('Reglas actualizadas. Los dispositivos conectados conservan su estado actual.')
            self.add_event('Política', self._notice)
            if result['backup']:
                self._workspace.storage_error = ''
            self.refresh()
        elif operation == 'policy-backup':
            self.show_notice('Respaldo de reglas exportado.')
        elif operation == 'diagnose-phone':
            self._workspace.diagnostic_result = result
            self._workspace.changed.emit()
        elif operation == "simulate":
            self.add_event("Simulación", result)
            self.refresh()
        elif operation == "service":
            self._service_working = False
            self._service = result
            self._service_error = ""
            self._error = ""
            action, remember, _expected = self._service_action
            text = ("Servicios iniciados; inicio automático habilitado." if remember else "Servicios iniciados; arranque sin cambios.") if action == "start" else (
                    "Servicios detenidos; inicio automático deshabilitado." if remember else "Servicios detenidos; arranque sin cambios.")
            self.show_notice(text)
            self.add_event("Simulación" if self._demo else "Servicio", text)
            self.refresh()
        self.changed.emit()

    @Slot(str, str)
    def failed(self, operation, message):
        if operation == "poll":
            self._polling = False
        else:
            self._busy = False
        if operation == "notify": return
        self._error = message
        if operation == 'policy-commit':
            self._workspace.cancelRule()
            self.add_event('Error', message)
            self.pollBackground()
        if operation == "service":
            self._service_working = False
            self._service_error = message
            self.add_event("Error", message)
            self.changed.emit()
            self.refresh()
            return
        if operation in ("refresh", "poll"):
            if self._notice_context: self.clearNotice()
            self._connected = False
            self._devices = []
            self._workspace.update_snapshot({'rulesError': message})
            self._workspace.decisions.clear()
            self._selected = -1
            self._policy = "Política no disponible"
            if self._service.get("units") and all(u["active"] == "inactive" for u in self._service["units"]):
                self._error = ""
                self.changed.emit()
                return
        if message != self._last_error:
            self.add_event("Error", message)
            self._last_error = message
        self.changed.emit()

    @Slot(str, object)
    def device_event(self, member, args):
        if member == 'NotificationOpen':
            self._workspace.showWindow.emit()
            return
        self._workspace.observe(member, args)
        self.sync_selected()
        if member == "DevicePresenceChanged":
            self._event_count += 1
            action = {0: "Presente · ID {id}", 1: "Conectado · ID {id}", 2: "Actualizado · ID {id}", 3: "Desconectado · ID {id}"}.get(args[1], "Cambio · ID {id}")
            try:
                from .domain import parse_device
                name = display_text(parse_device(args[0], args[3]).name)
            except (ValueError, IndexError): name = ''
            self.add_event("Dispositivo", message('{event} · {name}', event=message(action, id=args[0]), name=name))
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
                "{count} cambios detectados. Abre USBGuard Control para revisarlos.", count=count)),
                self.language.text('Abrir USBGuard Control')))
            QTimer.singleShot(1200, self.refresh)
        else:
            self.refresh()

    def shutdown(self):
        if self._workspace.closed: return
        self.add_event('Sesión', 'Observación finalizada. No se registran eventos mientras la aplicación está cerrada.')
        self.poll.stop()
        self.coalesce.stop()
        self.notice_timer.stop()
        if self.worker.cancel:
            self.worker.cancel.cancel()
        self.stopping.emit()
        self.thread.wait()
        self._workspace.close()

# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Desktop workspace: rule previews, preferences, observed decisions and activity."""
from datetime import datetime
import csv
import io
import json
from pathlib import Path
import sqlite3
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QSettings
from .domain import display_text, parse_device
from .policy import alias_key, concrete_rule, backup_document, read_backup
from .storage import ActivityStore, private_json, private_write
from .translations import message
from .appearance import LIGHT


class Workspace(QObject):
    changed = Signal()
    confirmationChanged = Signal()
    openSettings = Signal()
    showWindow = Signal()

    def __init__(self, control, data_dir=None):
        super().__init__(control)
        self.control = control
        self.settings = control.language.settings
        self.data_dir = Path(data_dir) if data_dir else None
        self.rows = []
        self.rules_error = ''
        self.rule_query = ''
        self.selected_id = -1
        self.pending = None
        self.decisions = {}
        self.history = []
        self.history_query = ''
        self.history_day = ''
        self.store = None
        self.storage_error = ''
        self.diagnostic_result = ''
        self.background_available = False
        self.desktop = None
        self.closed = False
        self._theme = str(self.pref('theme', 'dark'))
        self._background = self.pref_bool('background', False)
        try: self._retention = int(self.pref('retention', 30))
        except (TypeError, ValueError): self._retention = 30
        if self._retention not in (7, 30, 90): self._retention = 30
        self.aliases = {}
        try:
            self.aliases = json.loads(str(self.pref('aliases', '{}')))
            if not isinstance(self.aliases, dict): self.aliases = {}
        except (TypeError, ValueError): pass
        if self.data_dir:
            try:
                self.store = ActivityStore(self.data_dir, self._retention)
                self.history = self.store.read()
            except (OSError, sqlite3.Error, ValueError):
                self.storage_error = 'No se pudo abrir el historial local. La actividad se conserva solo en esta sesión.'
        control.language.changed.connect(self.changed.emit)

    def text(self, value): return self.control.language.text(value)

    def pref(self, key, default):
        return self.settings.value('workspace/' + key, default) if self.settings else default

    def pref_bool(self, key, default):
        return str(self.pref(key, default)).lower() in ('true', '1')

    def save(self, key, value):
        if self.settings:
            self.settings.setValue('workspace/' + key, value)
            self.settings.sync()
            if self.settings.status() != QSettings.NoError:
                self.control.failed('preferences', 'No se pudieron guardar las preferencias.')

    @Property(str, notify=changed)
    def theme(self): return self._theme if self._theme in ('dark', 'light', 'system') else 'dark'

    @Property('QVariantMap', notify=changed)
    def colors(self):
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtCore import Qt
        light = self.theme == 'light' or (self.theme == 'system' and QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Light)
        return {color: value if light else color for color, value in LIGHT.items()}

    @Property(bool, notify=changed)
    def autostart(self): return self.desktop is not None and self.desktop.path.exists()

    @Slot(bool)
    def setAutostart(self, value):
        try:
            if self.control.demo or self.desktop is None:
                raise ValueError('El inicio de sesión requiere instalar el paquete de esta versión.')
            self.desktop.set_autostart(value)
            if value: self.setBackground(True)
        except (OSError, ValueError) as error:
            self.control.failed('preferences', str(error))
        self.changed.emit()

    @Slot(str)
    def setTheme(self, value):
        if value in ('dark', 'light', 'system'):
            self._theme = value; self.save('theme', value); self.changed.emit()

    @Property(bool, notify=changed)
    def background(self): return self._background and self.background_available

    @Property(bool, notify=changed)
    def backgroundAvailable(self): return self.background_available

    @Slot(bool)
    def setBackground(self, value):
        self._background = bool(value) and self.background_available
        self.save('background', self._background); self.changed.emit()

    @Property(int, notify=changed)
    def retention(self): return self._retention

    @Slot(int)
    def setRetention(self, days):
        if days not in (7, 30, 90): return
        self._retention = days; self.save('retention', days)
        if self.store:
            try:
                self.store.prune(days); self.history = self.store.read()
            except sqlite3.Error: self.storage_error = 'No se pudo actualizar el historial local.'
        self.changed.emit()

    @Property(int, constant=True)
    def initialWidth(self):
        try: return max(900, min(2400, int(self.pref('width', 1040))))
        except (TypeError, ValueError): return 1040

    @Property(int, constant=True)
    def initialHeight(self):
        try: return max(620, min(1600, int(self.pref('height', 780))))
        except (TypeError, ValueError): return 780

    @Slot(int, int)
    def saveGeometry(self, width, height):
        self.save('width', width); self.save('height', height)

    def device_alias(self, device):
        value = self.aliases.get(alias_key(device), '')
        return display_text(value)[:80] if isinstance(value, str) else ''

    @Slot(str)
    def renameSelected(self, name):
        device = next((d for d in self.control._devices if d.id == self.control._selected), None)
        if not device: return
        key = alias_key(device)
        name = display_text(name.strip())[:80]
        if name: self.aliases[key] = name
        else: self.aliases.pop(key, None)
        self.save('aliases', json.dumps(self.aliases, ensure_ascii=False))
        self.changed.emit(); self.control.changed.emit()

    @Slot(str)
    def renameRule(self, name):
        rule = next((r for r in self.rows if r.id == self.selected_id), None)
        if rule is None: return
        try:
            device = concrete_rule(rule.text)
        except ValueError: return
        key = alias_key(device)
        name = display_text(name.strip())[:80]
        if name: self.aliases[key] = name
        else: self.aliases.pop(key, None)
        self.save('aliases', json.dumps(self.aliases, ensure_ascii=False))
        self.changed.emit(); self.control.changed.emit()

    @Slot()
    def openBackups(self):
        from PySide6.QtGui import QDesktopServices
        if self.data_dir is None:
            self.control.show_notice('En demostración, los respaldos automáticos son temporales.')
            self.control.changed.emit()
            return
        try:
            path = self.data_dir / 'backups'
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                raise ValueError('No se pudo abrir la carpeta de respaldos.')
        except (OSError, ValueError) as error:
            self.control.failed('backup', str(error))

    def explanation(self, device):
        known = self.decisions.get(device.id)
        if known and known[:3] == (device.identity, device.target, self.control._owner):
            return self.text(known[3])
        return self.text('Origen no observado en esta sesión. El estado actual lo informa USBGuard.')

    def observe(self, member, args):
        try:
            if member == 'DevicePresenceChanged' and args[1] == 3:
                self.decisions.pop(args[0], None)
            elif member in ('DevicePolicyApplied', 'DevicePolicyChanged'):
                offset = 1 if member == 'DevicePolicyApplied' else 2
                device = parse_device(args[0], args[offset + 1])
                rid = args[offset + 2]
                reason = ('Decisión observada de la política implícita del servicio.' if rid == 4294967294
                          else message('Decisión observada de la regla #{id}. Su persistencia no está indicada por D-Bus.', id=rid)
                          if rid < 4294967293 else 'Decisión observada sin regla identificable.')
                self.decisions[device.id] = (device.identity, device.target, self.control._owner, reason)
        except (IndexError, TypeError, ValueError): pass

    def update_snapshot(self, result):
        devices = {d.id: d for d in result.get('devices', [])}
        for device_id, known in list(self.decisions.items()):
            device = devices.get(device_id)
            if device is None or known[:3] != (device.identity, device.target, result.get('owner')):
                self.decisions.pop(device_id, None)
        rules = result.get('rules', [])
        error = result.get('rulesError', '')
        if rules != self.rows or error != self.rules_error:
            self.rows, self.rules_error = list(rules), error
            if not any(r.id == self.selected_id for r in rules): self.selected_id = -1
            self.changed.emit()

    @Property(str, notify=changed)
    def rulesError(self): return self.text(self.rules_error)

    @Property('QVariantList', notify=changed)
    def rules(self):
        result = []
        for index, rule in enumerate(self.rows):
            row = rule.view()
            row['order'] = index + 1
            row['targetLabel'] = self.text({'allow':'Permitido', 'block':'Bloqueado', 'reject':'Rechazado'}.get(row['target'], 'Desconocido'))
            row['alias'] = ''
            row['canRename'] = False
            if row['name'] == 'Regla avanzada': row['name'] = self.text(row['name'])
            try:
                alias = self.device_alias(concrete_rule(rule.text))
                row['alias'], row['canRename'] = alias, True
                if alias: row['name'] = alias
            except ValueError: pass
            row['duplicate'] = sum(r.text == rule.text for r in self.rows) > 1
            if self.rule_query.casefold() in (row['name'] + ' ' + row['raw']).casefold(): result.append(row)
        return result

    @Property('QVariantMap', notify=changed)
    def selectedRule(self):
        return next((r for r in self.rules if r['id'] == self.selected_id), {})

    @Slot(int)
    def selectRule(self, rule_id): self.selected_id = rule_id; self.changed.emit()

    @Slot(str)
    def searchRules(self, text): self.rule_query = text; self.changed.emit()

    @Slot(str, str)
    def prepareRule(self, operation, target):
        if self.control.busy or not self.control.connected or self.rules_error: return
        self.control.dispatch('policy-preview', (operation, self.selected_id, target, None))

    @Slot(str)
    def loadBackup(self, url):
        if self.control.busy or not self.control.connected: return
        try:
            path = QUrl(url).toLocalFile()
            if not path: raise ValueError('Selecciona un archivo local.')
            rows = read_backup(Path(path))
            self.control.dispatch('policy-preview', ('restore', 0, '', rows))
        except (OSError, ValueError) as error: self.control.failed('backup', str(error))

    @Property('QVariantMap', notify=confirmationChanged)
    def confirmation(self):
        if self.pending is None: return {}
        p = self.pending
        return {'operation': p['operation'], 'before': p['selected'].text if p['selected'] else '',
                'after': p.get('replacement', '\n'.join(p['additions'])),
                'affected': [display_text(d.name) for d in p['affected']], 'count': len(p['additions']),
                'skipped': p['skipped']}

    @Slot()
    def cancelRule(self): self.pending = None; self.confirmationChanged.emit()

    @Slot()
    def confirmRule(self):
        if not self.pending or self.control.busy: return
        if not self.data_dir and not self.control.demo:
            self.control.failed('policy', 'No hay almacenamiento disponible para respaldar las reglas.'); return
        pending = self.pending
        self.cancelRule()
        self.control.dispatch('policy-commit', (pending, str(self.data_dir / 'backups') if self.data_dir else None))

    @Slot(str)
    def exportBackup(self, url):
        path = QUrl(url).toLocalFile()
        if not path: self.control.failed('backup', 'Selecciona un archivo local.'); return
        if not self.control.busy and self.control.connected:
            self.control.dispatch('policy-backup', path)

    @Property('QVariantList', notify=changed)
    def activity(self):
        result = []
        for event in self.history:
            row = {**event, 'category': self.text(event['category']), 'message': self.text(event['message'])}
            if self.history_query.casefold() in (row['message'] + ' ' + row['category']).casefold() and row['time'].startswith(self.history_day):
                result.append(row)
        return result

    @Property(str, notify=changed)
    def storageError(self): return self.text(self.storage_error)

    @Property(bool, constant=True)
    def persistentHistory(self): return self.store is not None

    def record(self, event):
        self.history.insert(0, dict(event)); del self.history[2000:]
        if self.store:
            try:
                self.store.append(event)
                if len(self.history) % 100 == 0: self.store.prune(self._retention)
            except (sqlite3.Error, OSError): self.storage_error = 'No se pudo guardar un evento en el historial local.'
        self.changed.emit()

    @Slot(str, str)
    def searchActivity(self, query, day):
        self.history_query = query; self.history_day = day; self.changed.emit()

    @Slot(str, bool)
    def exportHistory(self, url, redact):
        path = QUrl(url).toLocalFile()
        if not path: self.control.failed('export', 'Selecciona un archivo local.'); return
        events = self.activity
        if redact: events = [{**e, 'message': self.text('Detalles omitidos por privacidad.')} for e in events]
        try:
            if Path(path).suffix.lower() == '.csv':
                stream = io.StringIO()
                writer = csv.writer(stream); writer.writerow(['time','category','message'])
                for e in events:
                    # Spreadsheet formula neutralization includes leading whitespace.
                    values = [str(e[k]) for k in ('time','category','message')]
                    writer.writerow(["'" + v if v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v for v in values])
                private_write(path, stream.getvalue())
            else:
                private_json(path, {'application':'USBGuard Control', 'scope':'observed-client-events-only',
                                    'demo':self.control.demo, 'redacted':redact, 'locale':self.control.language.locale, 'events':events})
            self.control.show_notice('Actividad exportada.'); self.control.changed.emit()
        except OSError as error: self.control.failed('export', str(error))

    @Slot()
    def clearHistory(self):
        try:
            if self.store: self.store.clear()
            self.history = []; self.changed.emit()
        except sqlite3.Error: self.control.failed('history', 'No se pudo borrar el historial local.')

    @Property('QVariantList', notify=changed)
    def diagnostics(self):
        rows = []
        for unit in self.control.serviceState['units']:
            good = unit['active'] == 'active'
            rows.append({'title':self.text('Protección USB' if unit['name']=='usbguard.service' else 'Conexión con la interfaz'),
                         'detail':unit['activeLabel'] + ' · ' + unit['bootLabel'], 'ok':good})
        rows.append({'title':self.text('Comunicación D-Bus'), 'detail':self.text('Disponible' if self.control.connected else
                     'Abre Configuración para comprobar el servicio. Si está activo, revisa Polkit y el puente D-Bus.'), 'ok':self.control.connected})
        rows.append({'title':self.text('Lectura de reglas'), 'detail':self.text(self.rules_error or ('Disponible' if self.control.connected else 'No disponible')), 'ok':self.control.connected and not self.rules_error})
        rows.append({'title':self.text('Acceso a archivos del teléfono'), 'detail':self.text('Permitir un USB no monta sus archivos. Desbloquea el teléfono y acepta Confiar si lo solicita; comprueba el soporte de archivos de tu escritorio.'), 'ok':True})
        if self.diagnostic_result: rows.append({'title':self.text('Emparejamiento del iPhone'), 'detail':self.text(self.diagnostic_result), 'ok':False})
        return rows

    @Slot()
    def checkPhone(self):
        if not self.control.busy: self.control.dispatch('diagnose-phone', None)

    @Slot(str)
    def exportDiagnostics(self, url):
        path = QUrl(url).toLocalFile()
        if not path: self.control.failed('export', 'Selecciona un archivo local.'); return
        try:
            private_json(path, {'application':'USBGuard Control', 'connected':self.control.connected,
                               'services':self.control.serviceState['units'], 'rule_count':len(self.rows),
                               'rules_readable':not self.rules_error and self.control.connected})
            self.control.show_notice('Diagnóstico exportado sin identificadores USB.'); self.control.changed.emit()
        except OSError as error: self.control.failed('export', str(error))

    def close(self):
        if self.closed: return
        self.closed = True
        if self.store: self.store.close()

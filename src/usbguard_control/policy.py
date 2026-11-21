# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Conservative rule editing: unknown grammar stays visible and read-only."""
from dataclasses import dataclass
import hashlib
import json
import re
from .domain import rule_tokens, parse_device, display_text, RULE_TOKEN

LAST_RULE = 4294967293


def quote(value):
    # USBGuard strings encode non-ASCII bytes, not Python or shell escapes.
    return '"' + ''.join(chr(b) if 32 <= b < 127 and b not in (34, 92)
                         else ('\\' + chr(b) if b in (34, 92) else f'\\x{b:02x}')
                         for b in value.encode('utf-8')) + '"'


@dataclass(frozen=True)
class PolicyRule:
    id: int
    text: str

    def view(self):
        result = dict(id=self.id, text=display_text(self.text), raw=self.text,
                      name="Regla avanzada", target=self.text.split(' ', 1)[0],
                      editable=False, digest="", sensitive=True, usbId="")
        try:
            device = concrete_rule(self.text)
            result.update(name=display_text(device.name) or device.usb_id,
                          digest=device.digest, usbId=device.usb_id,
                          sensitive=device.sensitive, editable=not device.sensitive)
        except ValueError:
            pass
        return result


def concrete_rule(text):
    if not isinstance(text, str) or len(text) > 8192 or '\n' in text or '\r' in text:
        raise ValueError("La regla no admite edición guiada.")
    tokens = rule_tokens(text)
    if not tokens or tokens[0] not in ('allow', 'block'):
        raise ValueError("La regla no admite edición guiada.")
    single = {'id', 'serial', 'name', 'hash', 'parent-hash', 'via-port', 'with-connect-type', 'label'}
    seen = set()
    i = 1
    while i < len(tokens):
        key = tokens[i]; i += 1
        if key in seen:
            raise ValueError("La regla no admite edición guiada.")
        seen.add(key)
        if key in single:
            if i >= len(tokens): raise ValueError("Regla incompleta.")
            i += 1
        elif key == 'with-interface':
            if i < len(tokens) and tokens[i] == 'equals': i += 1
            if i < len(tokens) and tokens[i] == '{':
                i += 1
                start = i
                while i < len(tokens) and tokens[i] != '}':
                    if not re.fullmatch(r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}', tokens[i]):
                        raise ValueError("La regla no admite edición guiada.")
                    i += 1
                if i == start or i == len(tokens): raise ValueError("Regla incompleta.")
                i += 1
            elif i < len(tokens) and re.fullmatch(r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}', tokens[i]):
                i += 1
            else: raise ValueError("La regla no admite edición guiada.")
        else: raise ValueError("La regla no admite edición guiada.")
    device = parse_device(0, text)
    if not re.fullmatch(r'[0-9a-fA-F]{4}:[0-9a-fA-F]{4}', device.usb_id) or not device.digest or not device.interfaces:
        raise ValueError("Solo se editan reglas específicas con huella e interfaces conocidas.")
    return device


def validate_edit(rule):
    device = concrete_rule(rule.text)
    if device.sensitive:
        raise ValueError("Las reglas de entrada, Bluetooth y concentradores requieren revisión administrativa.")
    return device


def replace_target(rule, target):
    validate_edit(rule)
    if target not in ('allow', 'block'): raise ValueError("Acción no admitida")
    return target + rule.text[len(rule.text.split(' ', 1)[0]):]


def canonical_rule(text):
    """Normalize only the supported concrete grammar, never arbitrary policy.

    Order and set formatting follow USBGuard RulePrivate::toString and
    Rule::Attribute::toRuleString (1.1.3/1.1.4). The daemon validates the
    normalized predicate again through the read-only listDevices call.
    """
    concrete_rule(text)
    raw = RULE_TOKEN.findall(text)
    tokens = rule_tokens(text)
    if raw[0].startswith('"'):
        raise ValueError('La decisión de la regla no debe ir entre comillas.')
    if any(not c.isprintable() and c != '\t' for c in text):
        raise ValueError('La regla debe ocupar una línea y no contener caracteres de control.')
    attrs = {}
    i = 1
    while i < len(tokens):
        key = tokens[i]
        if raw[i].startswith('"'):
            raise ValueError('Los atributos de la regla no deben ir entre comillas.')
        i += 1
        if key == 'with-interface':
            if tokens[i] == 'equals': i += 1
            if tokens[i] == '{':
                i += 1; values = []
                while tokens[i] != '}':
                    if raw[i].startswith('"'): raise ValueError('Interfaz USB inválida')
                    values.append(tokens[i].lower()); i += 1
                i += 1
            else:
                if raw[i].startswith('"'): raise ValueError('Interfaz USB inválida')
                values = [tokens[i].lower()]; i += 1
            attrs[key] = tuple(values)
        else:
            if key == 'id':
                if raw[i].startswith('"'): raise ValueError('El identificador USB no debe ir entre comillas.')
                value = tokens[i].lower()
            else:
                if not raw[i].startswith('"'):
                    raise ValueError('Los valores de texto deben ir entre comillas dobles.')
                value = tokens[i]
                if any(not c.isprintable() for c in value):
                    raise ValueError('La regla debe ocupar una línea y no contener caracteres de control.')
            attrs[key] = value; i += 1
    parts = [tokens[0]]
    for key in ('id', 'serial', 'name', 'hash', 'parent-hash', 'via-port', 'with-interface', 'with-connect-type', 'label'):
        if key not in attrs: continue
        value = attrs[key]
        if key == 'with-interface': value = value[0] if len(value) == 1 else '{ ' + ' '.join(value) + ' }'
        elif key != 'id': value = quote(value)
        parts.extend((key, value))
    return ' '.join(parts), attrs


def validate_replacement(rule, text):
    """Keep the original device anchor and exact interface set in text edits."""
    validate_edit(rule)
    before, old = canonical_rule(rule.text)
    normalized, new = canonical_rule(text)
    validate_edit(PolicyRule(rule.id, normalized))
    if any(old.get(key) != new.get(key) for key in ('id', 'serial', 'hash', 'with-interface')):
        raise ValueError('Conserva VID:PID, serie, huella e interfaces de la regla original.')
    if new.get('label', '').startswith('GNOME_SETTINGS_DAEMON'):
        raise ValueError('Esa etiqueta está reservada para la gestión USB del escritorio.')
    if before == normalized:
        raise ValueError('No hay cambios en la regla.')
    return normalized


def device_rule(device, target='allow'):
    if target not in ('allow', 'block') or not device.digest or not device.interfaces:
        raise ValueError("No se pudo verificar la identidad del dispositivo.")
    return (f'{target} id {device.usb_id} serial {quote(device.serial)} name {quote(device.name)} '
            f'hash {quote(device.digest)} parent-hash {quote(device.parent)} '
            f'via-port {quote(device.port)} with-interface {{ ' + ' '.join(device.interfaces) + ' }')


def alias_key(device):
    return hashlib.sha256(json.dumps([device.usb_id, device.serial, device.digest], ensure_ascii=True).encode()).hexdigest()


def backup_document(rules):
    return {'format': 'usbguard-control-policy', 'version': 1, 'scope': 'loaded-rules-not-daemon-configuration',
            'rules': [r.text for r in rules]}


def read_backup(path):
    if path.stat().st_size > 2_000_000: raise ValueError("El respaldo es demasiado grande.")
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('format') != 'usbguard-control-policy' or value.get('version') != 1:
        raise ValueError("Formato de respaldo no admitido.")
    rows = value.get('rules')
    if not isinstance(rows, list) or len(rows) > 2000:
        raise ValueError("Formato de respaldo no admitido.")
    if any(not isinstance(r, str) or not r.strip() or len(r) > 8192 or any(c in r for c in '\r\n\0') for r in rows):
        raise ValueError("Formato de respaldo no admitido.")
    return rows

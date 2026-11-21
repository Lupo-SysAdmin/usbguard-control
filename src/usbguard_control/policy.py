# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Conservative rule editing: unknown grammar stays visible and read-only."""
from dataclasses import dataclass
import hashlib
import json
import re
from .domain import rule_tokens, parse_device, display_text

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

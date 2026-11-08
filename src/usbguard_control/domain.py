# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Device snapshots. No privileged operations or GUI dependencies."""
from dataclasses import dataclass
import re
import shlex

TARGETS = {"allow": 0, "block": 1}
INTERFACE = re.compile(r"^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$")


def display_text(text: str) -> str:
    """USB names are untrusted; remove controls including bidi formatting."""
    return "".join(c for c in text if c.isprintable())[:160]


@dataclass(frozen=True)
class Device:
    id: int
    target: str
    name: str
    usb_id: str
    serial: str
    digest: str
    parent: str
    port: str
    interfaces: tuple[str, ...]

    @property
    def infrastructure(self) -> bool:
        return any(i.startswith("09:") for i in self.interfaces)

    @property
    def sensitive(self) -> bool:
        return not self.interfaces or any(i.startswith(("03:", "09:")) for i in self.interfaces)

    @property
    def kind(self) -> str:
        classes = {i[:2] for i in self.interfaces}
        if "09" in classes:
            return "Concentrador USB"
        if "03" in classes:
            return "Entrada · HID"
        if "08" in classes:
            return "Almacenamiento"
        if "e0" in classes:
            return "Conectividad"
        if "0e" in classes:
            return "Cámara"
        if "01" in classes:
            return "Audio"
        return "Dispositivo USB"

    @property
    def identity(self) -> tuple:
        return (self.usb_id, self.serial, self.digest, self.parent, self.port, self.interfaces)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "target": self.target,
            "name": display_text(self.name) or "Dispositivo sin nombre",
            "usbId": self.usb_id, "serial": display_text(self.serial) or "No informado",
            "digest": self.digest, "port": self.port or "No informado",
            "interfaces": ", ".join(self.interfaces) or "No informadas",
            "kind": self.kind, "infrastructure": self.infrastructure,
            "sensitive": self.sensitive,
            "canBlock": not self.sensitive and bool(self.digest),
            "canAllow": not self.infrastructure and bool(self.digest),
            "status": {"allow": "Permitido", "block": "Bloqueado", "reject": "Rechazado"}.get(self.target, "Desconocido"),
        }


def parse_device(device_id: int, rule: str) -> Device:
    """Parse concrete listDevices rules, not arbitrary policy expressions."""
    lexer = shlex.shlex(rule, posix=True, punctuation_chars="{}")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)
    if not tokens or tokens[0] not in ("allow", "block", "reject"):
        raise ValueError("Estado de dispositivo no reconocido")
    values = {}
    interfaces = []
    index = 1
    while index < len(tokens):
        key = tokens[index]
        index += 1
        if key == "with-interface":
            if index < len(tokens) and tokens[index] in ("one-of", "all-of", "equals", "equals-ordered", "match-all"):
                index += 1
            if index < len(tokens) and tokens[index] == "{":
                index += 1
                while index < len(tokens) and tokens[index] != "}":
                    interfaces.append(tokens[index])
                    index += 1
                if index == len(tokens):
                    raise ValueError("Lista de interfaces incompleta")
                index += 1
            elif index < len(tokens):
                interfaces.append(tokens[index])
                index += 1
        elif index < len(tokens):
            values[key] = tokens[index]
            index += 1
    if any(not INTERFACE.fullmatch(i) for i in interfaces):
        raise ValueError("Interfaz USB inválida")
    return Device(int(device_id), tokens[0], values.get("name", ""), values.get("id", ""),
                  values.get("serial", ""), values.get("hash", ""), values.get("parent-hash", ""),
                  values.get("via-port", ""), tuple(i.lower() for i in interfaces))


def validate_action(current: Device, expected: Device, target: str) -> None:
    if target not in TARGETS:
        raise ValueError("Acción no admitida")
    if current.id != expected.id or current.identity != expected.identity:
        raise ValueError("El dispositivo cambió. Actualiza la lista y vuelve a seleccionarlo.")
    if not current.digest:
        raise ValueError("No se pudo verificar la identidad del dispositivo.")
    if current.infrastructure or (target == "block" and current.sensitive):
        raise ValueError("Por seguridad, esta versión no bloquea entradas HID, concentradores ni interfaces desconocidas.")

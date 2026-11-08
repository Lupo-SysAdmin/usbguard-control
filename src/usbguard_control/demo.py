# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""In-memory simulation; never imports a system transport."""
from dataclasses import replace
from .domain import parse_device, validate_action

FIXTURES = [
    (12, 'block id 0634:5600 serial "DEMO-X8-001" name "Crucial X8 SSD" hash "demo-storage" parent-hash "demo-root" via-port "1-3" with-interface 08:06:50'),
    (9, 'allow id 046d:c534 serial "" name "Logitech USB Receiver" hash "demo-receiver" parent-hash "demo-root" via-port "1-2" with-interface { 03:01:01 03:01:02 }'),
    (11, 'allow id 8087:0033 serial "" name "Intel Bluetooth" hash "demo-bluetooth" parent-hash "demo-root" via-port "1-10" with-interface { e0:01:01 }'),
    (15, 'allow id 0951:1666 serial "DEMO-DT-002" name "Kingston DataTraveler" hash "demo-kingston" parent-hash "demo-root" via-port "1-4" with-interface 08:06:50'),
    (7, 'allow id 1d6b:0002 serial "" name "Linux USB 2.0 Root Hub" hash "demo-root" via-port "usb1" with-interface 09:00:00'),
]


class DemoBackend:
    def __init__(self):
        self.devices = [parse_device(*row) for row in FIXTURES]
        self.saved = {}

    def snapshot(self):
        return {"devices": list(self.devices), "owner": "demo", "implicit": "block", "inserted": "apply-policy"}

    def apply(self, expected, target, permanent, owner):
        current = next((d for d in self.devices if d.id == expected.id), None)
        if current is None:
            raise ValueError("El dispositivo ya no está conectado.")
        validate_action(current, expected, target)
        self.devices = [replace(d, target=target) if d.id == current.id else d for d in self.devices]
        if permanent:
            self.saved[current.identity] = target
        return 100 + current.id if permanent else 0

    def toggle_connection(self):
        if any(d.id == 12 for d in self.devices):
            self.devices = [d for d in self.devices if d.id != 12]
            return "Crucial X8 SSD desconectado"
        device = parse_device(*FIXTURES[0])
        self.devices.insert(0, replace(device, target=self.saved.get(device.identity, "block")))
        return "Crucial X8 SSD conectado"

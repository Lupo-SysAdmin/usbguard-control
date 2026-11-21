# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private local storage, explicit retention and atomic export writes."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from .translations import Message


def encode(value):
    if isinstance(value, Message):
        return {'_message': value.source, 'values': {k: encode(v) for k, v in value.values.items()}}
    if isinstance(value, dict): return {k: encode(v) for k, v in value.items()}
    return value


def decode(value):
    if isinstance(value, dict):
        if '_message' in value: return Message(value['_message'], {k: decode(v) for k, v in value['values'].items()})
        return {k: decode(v) for k, v in value.items()}
    return value


def private_json(path, data):
    private_write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def private_write(path, content):
    path = Path(path)
    if not path.parent.exists(): path.parent.mkdir(parents=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix='.usbguard-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


class ActivityStore:
    def __init__(self, directory, days=30):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = directory / 'activity.sqlite3'
        # No journal sidecars containing device data; one GUI writer at a time.
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        os.chmod(path, 0o600)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=MEMORY')
        self.db.execute('PRAGMA secure_delete=ON')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT, payload TEXT)')
        self.prune(days)

    def prune(self, days):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        self.db.execute('DELETE FROM events WHERE julianday(time) < julianday(?)', (cutoff,))
        self.db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 10000)')
        self.db.commit()

    def append(self, event):
        self.db.execute('INSERT INTO events(time,payload) VALUES (?,?)', (event['time'], json.dumps(encode(event), ensure_ascii=False)))
        self.db.commit()

    def read(self):
        return [decode(json.loads(row[0])) for row in self.db.execute('SELECT payload FROM events ORDER BY id DESC LIMIT 2000')]

    def clear(self):
        self.db.execute('DELETE FROM events')
        self.db.commit()

    def close(self):
        self.db.close()

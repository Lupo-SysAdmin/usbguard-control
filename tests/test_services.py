"""Exercise real GIO signatures on a private bus, with no physical service changes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from gi.repository import Gio, GLib
from usbguard_control.services import ServiceManager, UNITS, DEST, manageable

pytestmark = pytest.mark.skipif(os.environ.get('USBGUARD_TEST_BUS') != '1', reason='private D-Bus session required')


@pytest.fixture
def manager():
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('fake_systemd.py'))], stdout=subprocess.PIPE, text=True)
    assert process.stdout.readline().strip() == 'ready'
    client = ServiceManager(connection=Gio.bus_get_sync(Gio.BusType.SESSION, None))
    yield client
    process.terminate()
    process.wait(timeout=5)


def change(manager, mode):
    manager.call(DEST, 'Change', '(s)', (mode,), '()', path='/test', interface='org.example.Test')


def calls(manager):
    return [json.loads(v) for v in manager.call(DEST, 'Calls', '()', (), '(as)', path='/test', interface='org.example.Test')[0]]


def test_read_only_snapshot_and_start_then_stop_persisted(manager):
    before = manager.snapshot()
    assert manageable(before)
    assert calls(manager) == []
    after = manager.apply('start', True, before)
    assert all(u['active'] == 'active' and u['boot'] == 'enabled' for u in after['units'])
    assert [c[0] for c in calls(manager)] == ['StartUnit', 'StartUnit', 'EnableUnitFiles', 'Reload']
    after = manager.apply('stop', True, after)
    assert all(u['active'] == 'inactive' and u['boot'] == 'disabled' for u in after['units'])
    assert [c[1][0] for c in calls(manager) if c[0] == 'StopUnit'] == list(reversed(UNITS))


def test_temporary_change_preserves_boot_and_can_be_persisted_later(manager):
    state = manager.apply('start', False, manager.snapshot())
    assert all(u['boot'] == 'disabled' for u in state['units'])
    assert [c[0] for c in calls(manager)] == ['StartUnit', 'StartUnit']
    manager.apply('start', True, state)
    assert [c[0] for c in calls(manager)] == ['StartUnit', 'StartUnit', 'EnableUnitFiles', 'Reload']


@pytest.mark.parametrize('mode', ['masked', 'missing'])
def test_unprepared_service_cannot_be_started(manager, mode):
    change(manager, mode)
    state = manager.snapshot()
    assert not manageable(state)
    with pytest.raises(ValueError, match='guía'): manager.apply('start', True, state)
    assert calls(manager) == []


def test_external_state_change_invalidates_confirmation(manager):
    state = manager.snapshot()
    change(manager, 'running')
    with pytest.raises(ValueError, match='cambió'): manager.apply('stop', True, state)
    assert calls(manager) == []


def test_cancelled_auth_does_not_change_state(manager):
    change(manager, 'deny')
    state = manager.snapshot()
    with pytest.raises(GLib.Error): manager.apply('start', True, state)
    assert manager.snapshot() == state


def test_partial_failure_is_not_reported_as_success(manager):
    change(manager, 'deny-enable')
    with pytest.raises(GLib.Error): manager.apply('start', True, manager.snapshot())
    state = manager.snapshot()
    assert all(u['active'] == 'active' and u['boot'] == 'disabled' for u in state['units'])


def test_skipped_or_failed_job_is_not_success(manager):
    change(manager, 'condition-failed')
    with pytest.raises(ValueError, match='no alcanzó'): manager.apply('start', True, manager.snapshot())
    assert [c[0] for c in calls(manager)] == ['StartUnit']


def test_action_is_restricted_and_repeated_request_has_no_side_effects(manager):
    before = manager.snapshot()
    with pytest.raises(ValueError): manager.apply('restart ssh.service', True, before)
    assert calls(manager) == []
    after = manager.apply('stop', True, before)
    assert after == before
    assert calls(manager) == []

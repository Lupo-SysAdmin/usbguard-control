"""User-session integration tests use temporary runtime/config directories."""
from pathlib import Path
import subprocess
import sys
import time
from PySide6.QtGui import QGuiApplication
from usbguard_control.desktop import claim_instance, DesktopIntegration


def test_existing_instance_is_activated_without_second_observer(tmp_path, monkeypatch):
    runtime=tmp_path/'runtime';runtime.mkdir(mode=0o700)
    monkeypatch.setenv('XDG_RUNTIME_DIR',str(runtime))
    app=QGuiApplication.instance() or QGuiApplication([])
    seen=[]
    server=claim_instance(app,lambda:seen.append(True))
    assert server is not None
    program='from PySide6.QtGui import QGuiApplication; from usbguard_control.desktop import claim_instance; app=QGuiApplication([]); assert claim_instance(app,lambda:None) is None'
    process=subprocess.Popen([sys.executable,'-c',program])
    deadline=time.monotonic()+5
    while time.monotonic()<deadline and (process.poll() is None or not seen):
        app.processEvents();time.sleep(.01)
    try:
        assert process.wait(timeout=2)==0 and seen
        assert server.isListening()
    finally:
        server.close();server.instance_lock.unlock()


def test_autostart_writes_only_this_apps_user_entry(tmp_path,monkeypatch):
    import usbguard_control.desktop as module
    class Subject:
        path=tmp_path/'autostart/io.github.LupoSysAdmin.USBGuardControl.desktop'
    unrelated=tmp_path/'autostart/other.desktop';unrelated.parent.mkdir();unrelated.write_text('other')
    monkeypatch.setattr(module,'__file__','/usr/share/usbguard-control/usbguard_control/desktop.py')
    DesktopIntegration.set_autostart(Subject(),True)
    content=Subject.path.read_text()
    assert 'Exec=/usr/bin/usbguard-control --background' in content
    assert 'sudo' not in content and 'systemctl' not in content
    DesktopIntegration.set_autostart(Subject(),False)
    assert not Subject.path.exists() and unrelated.read_text()=='other'

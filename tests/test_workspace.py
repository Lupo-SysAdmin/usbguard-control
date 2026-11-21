from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import pytest
from PySide6.QtCore import QSettings, QUrl, QMetaObject, Qt, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from shiboken6 import delete
from usbguard_control.controller import Controller
from usbguard_control.localization import Language, Translator
from usbguard_control.storage import ActivityStore
from usbguard_control.translations import message


def spin(app, predicate, timeout=4):
    deadline=time.monotonic()+timeout
    while not predicate() and time.monotonic()<deadline:
        app.processEvents();time.sleep(.01)
    assert predicate()


def new_control(tmp_path, persistent=False):
    language=Language(settings=QSettings(str(tmp_path/'prefs.ini'),QSettings.IniFormat))
    return Controller(demo=True,language=language,data_dir=tmp_path/'data' if persistent else None)


def test_preferences_alias_and_history_survive_restart(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    control=new_control(tmp_path,True)
    try:
        spin(app,lambda:control.connected and not control.busy)
        control.select(12)
        control.workspace.renameSelected('Disco de Jan')
        control.showInfrastructure(True);control.setNotifications(False);control.filter('block')
        control.workspace.setTheme('light');control.workspace.saveGeometry(1100,800)
        control.add_event('Acción',message('Regla guardada por esta aplicación: #{id}.',id=99))
    finally: control.shutdown()
    control=new_control(tmp_path,True)
    try:
        spin(app,lambda:control.connected and not control.busy)
        assert control.advanced and not control.notifications and control.activeFilter=='block'
        assert control.workspace.theme=='light' and control.workspace.initialWidth==1100
        control.select(12);assert control.selected['name']=='Disco de Jan'
        control.language.setLocale('en-US')
        assert any('Rule saved by this application: #99' in e['message'] for e in control.workspace.activity)
        assert any('Monitoring ended' in e['message'] for e in control.workspace.activity)
        control.search('Disco de Jan');assert len(control.devices)==1
    finally: control.shutdown()


def test_retention_and_private_storage(tmp_path):
    store=ActivityStore(tmp_path/'data')
    old=(datetime.now(timezone.utc)-timedelta(days=40)).isoformat()
    now=datetime.now(timezone.utc).isoformat()
    store.append({'time':old,'category':'old','message':'old'})
    store.append({'time':now,'category':'new','message':'new'})
    store.prune(30)
    assert len(store.read())==1 and store.read()[0]['category']=='new'
    assert (tmp_path/'data/activity.sqlite3').stat().st_mode & 0o777==0o600
    store.clear();assert store.read()==[]
    store.close()


def test_activity_filter_redaction_and_csv_formula_escape(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    control=new_control(tmp_path)
    try:
        control.add_event('Acción','=HYPERLINK("secret-serial")')
        control.workspace.searchActivity('secret-serial','')
        assert len(control.workspace.activity)==1
        path=tmp_path/'redacted.json'
        control.workspace.exportHistory(QUrl.fromLocalFile(str(path)).toString(),True)
        assert 'secret-serial' not in path.read_text()
        assert json.loads(path.read_text())['redacted']
        path=tmp_path/'events.csv'
        control.workspace.exportHistory(QUrl.fromLocalFile(str(path)).toString(),False)
        assert "'=HYPERLINK" in path.read_text()
        control.workspace.searchActivity('', '1900-01-01');assert control.workspace.activity==[]
    finally:control.shutdown()


def test_gui_policy_workflow_themes_languages_and_diagnostics(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    control=new_control(tmp_path)
    translator=Translator(control.language);app.installTranslator(translator)
    engine=QQmlApplicationEngine();warnings=[]
    engine.warnings.connect(lambda items:warnings.extend(w.toString() for w in items))
    engine.rootContext().setContextProperty('control',control)
    engine.rootContext().setContextProperty('language',control.language)
    control.language.changed.connect(engine.retranslate)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1]/'src/usbguard_control/qml/Main.qml')))
    try:
        window=engine.rootObjects()[0]
        spin(app,lambda:control.connected and not control.busy)
        control.workspace.selectRule(115)
        window.setProperty('page',2)
        for locale in ('es-419','en-US'):
            control.language.setLocale(locale)
            for theme in ('dark','light'):
                control.workspace.setTheme(theme)
                for page in (0,1,2,3):
                    window.setProperty('page',page)
                    window.resize(900,620)
                    for _ in range(12):app.processEvents()
                    assert not window.grabWindow().isNull()
        window.setProperty('page',2)
        control.workspace.prepareRule('remove','')
        spin(app,lambda:bool(control.workspace.confirmation))
        assert control.workspace.confirmation['affected']==['Kingston DataTraveler']
        control.workspace.cancelRule()
        assert len(control.workspace.rules)==4
        control.workspace.prepareRule('edit','block')
        spin(app,lambda:bool(control.workspace.confirmation))
        QMetaObject.invokeMethod(window.findChild(QObject,'confirmRuleButton'),'clicked',Qt.DirectConnection)
        spin(app,lambda:not control.busy and any(r['target']=='block' for r in control.workspace.rules))
        assert next(d for d in control.devices if d['id']==15)['target']=='allow'
        control.workspace.checkPhone()
        spin(app,lambda:not control.busy and bool(control.workspace.diagnostic_result))
        assert 'Simulated' in control.workspace.diagnostics[-1]['detail']
        path=tmp_path/'diagnostic.json';control.workspace.exportDiagnostics(QUrl.fromLocalFile(str(path)).toString())
        assert 'DEMO-DT' not in path.read_text()
        assert not warnings
    finally:
        control.shutdown();delete(engine);app.removeTranslator(translator);app.processEvents()


def test_decision_explanation_never_guesses_policy_origin(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    control=new_control(tmp_path)
    try:
        spin(app,lambda:control.connected and not control.busy)
        assert 'no observado' in control.selected['explanation']
        control.select(12);control.prepare('allow',False);control.confirm()
        spin(app,lambda:not control.busy and control.selected['target']=='allow')
        assert 'temporal' in control.selected['explanation']
        control.simulate();spin(app,lambda:not control.busy)
        control.simulate();spin(app,lambda:not control.busy)
        control.select(12)
        assert control.selected['target']=='block' and 'no observado' in control.selected['explanation']
    finally:control.shutdown()


def test_text_editor_keeps_draft_and_captured_rule_during_refresh_and_selection(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    control=new_control(tmp_path,True)
    translator=Translator(control.language);app.installTranslator(translator)
    engine=QQmlApplicationEngine();warnings=[]
    engine.warnings.connect(lambda items:warnings.extend(w.toString() for w in items))
    engine.rootContext().setContextProperty('control',control)
    engine.rootContext().setContextProperty('language',control.language)
    control.language.changed.connect(engine.retranslate)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1]/'src/usbguard_control/qml/Main.qml')))
    try:
        window=engine.rootObjects()[0]
        spin(app,lambda:control.connected and not control.busy)
        window.setProperty('page',2);control.workspace.selectRule(115)
        raw=control.workspace.selectedRule['raw']
        QMetaObject.invokeMethod(window.findChild(QObject,'advancedRuleButton'),'clicked',Qt.DirectConnection)
        editor=window.findChild(QObject,'ruleEditorDialog');draft=window.findChild(QObject,'ruleDraft')
        button=window.findChild(QObject,'previewRuleTextButton')
        assert editor.property('visible') and editor.property('ruleId')==115
        bad=raw.replace('demo-kingston','changed-identity')
        draft.setProperty('text',bad)
        QMetaObject.invokeMethod(button,'clicked',Qt.DirectConnection)
        spin(app,lambda:not control.busy and bool(control.workspace.editorError))
        assert not control.workspace.confirmation and len(control.workspace.rules)==4
        for locale in ('en-US','es-419'):
            control.language.setLocale(locale)
            for theme in ('light','dark'):
                control.workspace.setTheme(theme);window.resize(900,620)
                for _ in range(12):app.processEvents()
                assert not window.grabWindow().isNull()
                assert draft.property('text')==bad
        control.refresh();spin(app,lambda:not control.busy)
        control.workspace.selectRule(109)  # Moving selection cannot redirect the editor.
        assert draft.property('text')==bad and editor.property('ruleId')==115
        draft.setProperty('text',raw+' label "QA editor"')
        QMetaObject.invokeMethod(button,'clicked',Qt.DirectConnection)
        spin(app,lambda:bool(control.workspace.confirmation))
        assert not control.workspace.editorError
        assert control.workspace.confirmation['before']==raw
        assert control.workspace.confirmation['after'].endswith('label "QA editor"')
        control.workspace.cancelRule()
        assert editor.property('visible') and draft.property('text').endswith('label "QA editor"')
        QMetaObject.invokeMethod(button,'clicked',Qt.DirectConnection)
        spin(app,lambda:bool(control.workspace.confirmation))
        QMetaObject.invokeMethod(window.findChild(QObject,'confirmRuleButton'),'clicked',Qt.DirectConnection)
        spin(app,lambda:not control.busy and any('QA editor' in r['raw'] for r in control.workspace.rules))
        assert not editor.property('visible')
        assert next(r for r in control.workspace.rules if r['id']==109)['raw'].startswith('allow ')
        assert list((tmp_path/'data/backups').glob('*.json'))
        assert not warnings,warnings
    finally:
        control.shutdown();delete(engine);app.removeTranslator(translator);app.processEvents()

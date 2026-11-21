"""Text editor guardrails, canonical serialization and real preview contracts."""
from dataclasses import replace
import json
import pytest
from usbguard_control.policy import PolicyRule, canonical_rule, validate_replacement
from usbguard_control.demo import DemoBackend


def original(): return next(r for r in DemoBackend().rules if r.id == 115)


def test_normalizes_supported_grammar_without_changing_identity():
    old=original()
    draft=old.text.replace('allow ', 'block  ',1).replace('with-interface { 08:06:50 }','with-interface equals { 08:06:50 }')+' label "Respaldo de José"'
    text=validate_replacement(old,draft)
    assert text.startswith('block id 0951:1666')
    assert 'with-interface 08:06:50' in text and 'equals' not in text
    assert text.endswith('label "Respaldo de Jos\\xc3\\xa9"')
    assert canonical_rule(text)[1]['label']=='Respaldo de José'


@pytest.mark.parametrize('old,new',[
    ('0951:1666','0951:*'),('0951:1666','1111:2222'),
    ('serial "DEMO-DT-002"',''),('DEMO-DT-002','another-device'),
    ('demo-kingston','another-hash'),('08:06:50','08:06:51'),
    ('08:06:50','03:01:01'),('08:06:50','08:*:*'),
    ('allow','reject'),('allow','"allow"'),
    ('name "Kingston DataTraveler"','name Kingston'),
    ('id 0951:1666','id "0951:1666"'),
])
def test_rejects_broadening_identity_changes_sensitive_interfaces_and_bad_grammar(old,new):
    rule=original()
    with pytest.raises(ValueError):validate_replacement(rule,rule.text.replace(old,new))


@pytest.mark.parametrize('suffix',['\nallow', ' if true', ' hash "duplicate"',' label "x\\x00y"',' label "x\u202ey"',' label "GNOME_SETTINGS_DAEMON_RULE"'])
def test_conditions_multiple_rules_controls_and_reserved_labels_rejected(suffix):
    rule=original()
    with pytest.raises(ValueError):validate_replacement(rule,rule.text+suffix)


def test_only_formatting_is_not_a_policy_change():
    rule=original()
    with pytest.raises(ValueError,match='No hay cambios'):
        validate_replacement(rule,'  '+rule.text.replace('with-interface { 08:06:50 }','with-interface 08:06:50')+'  ')


def test_text_preview_checks_old_and_new_matches_and_revalidates_before_write(tmp_path,monkeypatch):
    backend=DemoBackend();old=original();disk=next(d for d in backend.devices if d.id==15)
    monkeypatch.setattr(backend,'matching_devices',lambda owner,text: [] if 'via-port "9-9"' in text else [disk])
    draft=old.text.replace('via-port "1-4"','via-port "9-9"')+' label "lab"'
    preview=backend.preview_policy('replace',old.id,draft=draft)
    assert preview['affectedBefore']==[disk] and preview['affectedAfter']==[]
    assert preview['affected']==[disk] and len(backend.rules)==4
    assert not list(tmp_path.iterdir())  # Preview is read-only.
    before=list(backend.rules);result=backend.commit_policy(preview,tmp_path)
    assert [r.text for r in result['rules']][2]==preview['replacement']
    assert [r for r in result['rules'] if r.text!=preview['replacement']]==[r for r in before if r.id!=old.id]
    assert backend.devices[3]==disk  # No immediate device authorization change.
    assert json.loads(next(tmp_path.glob('*.json')).read_text())['rules']==[r.text for r in before]


def test_new_matching_input_device_aborts_preview_and_commit(tmp_path,monkeypatch):
    backend=DemoBackend();old=original();draft=old.text+' label "lab"'
    preview=backend.preview_policy('replace',old.id,draft=draft)
    hid=next(d for d in backend.devices if d.id==9)
    monkeypatch.setattr(backend,'matching_devices',lambda owner,text:[hid] if 'label' in text else [])
    before=list(backend.rules)
    with pytest.raises(ValueError,match='entrada'):backend.commit_policy(preview,tmp_path)
    assert backend.rules==before and not list(tmp_path.iterdir())


def test_replace_denial_partial_write_and_stale_policy_keep_backup(tmp_path,monkeypatch):
    backend=DemoBackend();old=original();p=backend.preview_policy('replace',old.id,draft=old.text+' label "lab"')
    def denied(*args):raise PermissionError('authorization canceled')
    monkeypatch.setattr(backend,'remove_rule',denied)
    with pytest.raises(ValueError,match='Cambios parciales'):backend.commit_policy(p,tmp_path)
    assert old in backend.rules and len(backend.rules)==5
    assert list(tmp_path.glob('*.json'))
    with pytest.raises(ValueError,match='política cambió'):backend.commit_policy(p,tmp_path)


def test_demo_preview_and_reconnect_obey_port_and_connection_constraints(tmp_path):
    backend=DemoBackend();old=original()
    p=backend.preview_policy('replace',115,draft=old.text.replace('via-port "1-4"','via-port "9-9"'))
    assert p['affectedBefore'] and not p['affectedAfter']
    p=backend.preview_policy('replace',115,draft=old.text+' with-connect-type "hotplug"')
    assert p['affectedBefore'] and not p['affectedAfter']
    d=next(d for d in backend.devices if d.id==15)
    from usbguard_control.domain import validate_action
    with pytest.raises(ValueError,match='cambió'):validate_action(replace(d,connect_type='hotplug'),d,'allow')

"""Policy safety and ordering without touching the host daemon."""
from dataclasses import replace
import json
import pytest
from usbguard_control.demo import DemoBackend, FIXTURES
from usbguard_control.domain import parse_device, rule_tokens
from usbguard_control.policy import PolicyRule, concrete_rule, quote, read_backup, backup_document


def test_quotes_roundtrip_without_shell_or_unicode_reinterpretation():
    for text in ('Mouse de Jan', '漢字 "hola" \\x41', 'áéíóú', '$(touch /tmp/no)'):
        assert rule_tokens(quote(text)) == [text]


@pytest.mark.parametrize('text', ['allow', 'allow id *:*', 'allow id 0951:1666',
    FIXTURES[3][1] + ' if true', FIXTURES[3][1] + ' hash "other"',
    FIXTURES[3][1].replace('08:06:50', '*:*:*'), FIXTURES[3][1] + '\nallow'])
def test_broad_advanced_and_ambiguous_rules_are_read_only(text):
    assert not PolicyRule(1, text).view()['editable']
    with pytest.raises(ValueError): concrete_rule(text)


@pytest.mark.parametrize('device_id',[9,11,7])
def test_sensitive_rules_cannot_be_removed_or_edited(device_id):
    backend = DemoBackend()
    with pytest.raises(ValueError): backend.preview_policy('remove', 100+device_id)
    with pytest.raises(ValueError): backend.preview_policy('edit', 100+device_id, 'block')


def test_revocation_saves_backup_and_preserves_connected_state(tmp_path):
    backend=DemoBackend()
    preview=backend.preview_policy('remove',115)
    before=list(backend.devices)
    result=backend.commit_policy(preview,tmp_path)
    assert backend.devices==before
    assert not any(r.id==115 for r in backend.rules)
    data=json.loads(next(tmp_path.glob('*.json')).read_text())
    assert data['rules']==[r.text for r in preview['rules']]
    assert next(tmp_path.glob('*.json')).stat().st_mode & 0o777 == 0o600


def test_edit_preserves_priority_and_cannot_reuse_stale_preview(tmp_path):
    backend=DemoBackend()
    preview=backend.preview_policy('edit',115,'block')
    index=next(i for i,r in enumerate(backend.rules) if r.id==115)
    backend.commit_policy(preview,tmp_path)
    assert backend.rules[index].text.startswith('block ')
    with pytest.raises(ValueError,match='política cambió'): backend.commit_policy(preview,tmp_path)


def test_external_policy_change_aborts_before_backup_or_write(tmp_path):
    backend=DemoBackend(); preview=backend.preview_policy('remove',115)
    backend.rules.append(PolicyRule(555,'block'))
    before=list(backend.rules)
    with pytest.raises(ValueError,match='política cambió'): backend.commit_policy(preview,tmp_path)
    assert backend.rules==before and not list(tmp_path.iterdir())


def test_backup_failure_prevents_mutation(tmp_path):
    backend=DemoBackend(); preview=backend.preview_policy('remove',115)
    path=tmp_path/'file'; path.write_text('not a directory')
    before=list(backend.rules)
    with pytest.raises(OSError): backend.commit_policy(preview,path)
    assert backend.rules==before


def test_selective_restore_omits_protected_rules_and_deduplicates(tmp_path):
    backend=DemoBackend(); original=list(backend.rules)
    restore=[r.text for r in original]+[original[-2].text]
    backend.rules=[]
    preview=backend.preview_policy('restore',restore=restore)
    assert preview['skipped']==3 and len(preview['additions'])==1
    backend.commit_policy(preview,tmp_path)
    assert len(backend.rules)==1 and backend.rules[0].text==original[-2].text


def test_partial_edit_is_explicit_and_retains_backup(tmp_path,monkeypatch):
    backend=DemoBackend(); preview=backend.preview_policy('edit',115,'block')
    def deny(*args): raise PermissionError('canceled')
    monkeypatch.setattr(backend,'remove_rule',deny)
    with pytest.raises(ValueError,match='Cambios parciales'): backend.commit_policy(preview,tmp_path)
    assert any(r.id==115 for r in backend.rules)
    assert len(backend.rules)==len(preview['rules'])+1
    assert list(tmp_path.glob('*.json'))


def test_backup_validation_rejects_wrong_schema_and_multiline(tmp_path):
    path=tmp_path/'backup.json'
    for data in ({'rules':[]}, {'format':'usbguard-control-policy','version':1,'rules':['allow\nallow']}):
        path.write_text(json.dumps(data))
        with pytest.raises(ValueError): read_backup(path)
    data=backup_document(DemoBackend().rules)
    path.write_text(json.dumps(data))
    assert read_backup(path)==data['rules']

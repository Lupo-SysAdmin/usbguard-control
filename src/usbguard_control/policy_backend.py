# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
"""Policy operations with optimistic revalidation and mandatory local backups."""
from datetime import datetime, timezone
from pathlib import Path
from .policy import PolicyRule, LAST_RULE, validate_edit, replace_target, validate_replacement, backup_document
from .storage import private_json


class PolicyOperations:
    def policy_snapshot(self):
        owner = self.owner()
        return {'owner': owner, 'rules': self.list_rules(owner)}

    def preview_policy(self, operation, rule_id=0, target='', restore=None, draft=None):
        snapshot = self.policy_snapshot()
        rules = snapshot['rules']
        selected = next((r for r in rules if r.id == rule_id), None)
        result = dict(snapshot, operation=operation, selected=selected, target=target, additions=[], affected=[],
                      sources=list(restore or []), skipped=0, draft=draft)
        if operation in ('remove', 'edit', 'replace'):
            if selected is None: raise ValueError('La regla cambió. Actualiza la lista.')
            validate_edit(selected)
            result['affected'] = self.matching_devices(snapshot['owner'], selected.text)
            if any(d.sensitive for d in result['affected']):
                raise ValueError('La regla afecta dispositivos de entrada o infraestructura.')
            if operation == 'edit':
                result['replacement'] = replace_target(selected, target)
                if result['replacement'] == selected.text: raise ValueError('La regla ya tiene esa decisión.')
            elif operation == 'replace':
                result['replacement'] = validate_replacement(selected, draft)
                result['affectedBefore'] = list(result['affected'])
                result['affectedAfter'] = self.matching_devices(snapshot['owner'], result['replacement'])
                if any(d.sensitive for d in result['affectedAfter']):
                    raise ValueError('La regla afecta dispositivos de entrada o infraestructura.')
                result['affected'].extend(d for d in result['affectedAfter'] if d not in result['affected'])
                if any(r.id != selected.id and r.text == result['replacement'] for r in rules):
                    raise ValueError('Ya existe una regla idéntica. Revisa las reglas antes de continuar.')
        elif operation == 'restore':
            existing = {r.text for r in rules}
            for text in restore or []:
                if text in existing: continue
                rule = PolicyRule(0, text)
                try:
                    validate_edit(rule)
                except ValueError:
                    result['skipped'] += 1
                    continue
                matches = self.matching_devices(snapshot['owner'], text)
                if any(d.sensitive for d in matches):
                    raise ValueError('La regla afecta dispositivos de entrada o infraestructura.')
                result['additions'].append(text)
                result['affected'].extend(d for d in matches if d not in result['affected'])
                existing.add(text)
            if not result['additions']: raise ValueError('No hay reglas faltantes para recuperar.')
        else: raise ValueError('Acción no admitida')
        result['affected'].sort(key=lambda d: d.id)
        return result

    def assert_policy(self, owner, rules):
        if self.owner() != owner or self.list_rules(owner) != rules:
            raise ValueError('La política cambió. Revisa una nueva vista previa.')

    def commit_policy(self, preview, backup_dir):
        owner, expected = preview['owner'], list(preview['rules'])
        self.assert_policy(owner, expected)
        # Recompute every constraint, including affected sensitive devices.
        fresh = self.preview_policy(preview['operation'], preview['selected'].id if preview['selected'] else 0,
                                    preview['target'], preview['sources'], preview.get('draft'))
        if fresh != preview:
            raise ValueError('La política cambió. Revisa una nueva vista previa.')
        backup = Path(backup_dir) / ('policy-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        private_json(backup, backup_document(expected))
        self.assert_policy(owner, expected)
        changed = False
        try:
            if preview['operation'] == 'remove':
                self.remove_rule(owner, preview['selected'].id)
                changed = True
                expected.remove(preview['selected'])
            elif preview['operation'] in ('edit', 'replace'):
                old = preview['selected']
                new_id = self.append_rule(owner, preview['replacement'], old.id)
                changed = True
                index = expected.index(old)
                expected.insert(index + 1, PolicyRule(new_id, preview['replacement']))
                self.assert_policy(owner, expected)
                self.remove_rule(owner, old.id)
                expected.remove(old)
            else:
                for text in preview['additions']:
                    self.assert_policy(owner, expected)
                    new_id = self.append_rule(owner, text, LAST_RULE)
                    changed = True
                    expected.append(PolicyRule(new_id, text))
            self.assert_policy(owner, expected)
        except Exception as error:
            if changed:
                raise ValueError('Cambios parciales. Revisa las reglas y el respaldo antes de continuar.') from error
            raise
        return {'backup': str(backup), 'rules': expected}

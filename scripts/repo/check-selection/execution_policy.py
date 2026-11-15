# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.check-selection.execution-policy
#   version: 2
#   status: active
#   created_on: "2026-11-07"
#   updated_on: "2026-11-15"
#   layer: 06.shared
#   domain: testing
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Validate feedback declarations and retain safe non-authoritative execution observations.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.compiler.check-selection
#     path: scripts/repo/check-selection/script.py
"""Scheduling observations only; selector/cache remain the execution/proof owners."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path


def validate_feedback(identity: str, check: dict) -> list[dict]:
    if 'feedback' not in check:
        return []
    value = check['feedback']
    invalid = [{'code': 'check-feedback-invalid', 'check_id': identity}]
    if type(value) is not dict or set(value) != {'development', 'expected_seconds', 'isolation', 'rationale'}:
        return invalid
    if type(value['development']) is not bool or type(value['expected_seconds']) is not int or not 1 <= value['expected_seconds'] <= 86400:
        return invalid
    if value['isolation'] not in ('worktree', 'disposable-fixture'):
        return invalid
    reason = value['rationale']
    if type(reason) is not str or not reason.strip() or len(reason) > 400 or any(ord(c) < 32 for c in reason):
        return invalid
    if value['development'] and (check.get('stage') != 'local' or check.get('members')):
        return invalid
    return []


def feedback_for(check: dict) -> dict:
    value = check.get('feedback')
    return value if isinstance(value, dict) and not validate_feedback('', check) else {}


def development_check(item: dict) -> bool:
    entries = item.get('catalog_entries', {})
    return bool(entries) and all(feedback_for(check).get('development') is True for check in entries.values())


def execution_view(results: list[dict], checks: dict, *, development: bool, explicit: bool) -> dict:
    selected = {identity for item in results for identity in item['catalog_entries']}
    rows = []
    for item in results:
        feedback = feedback_for(checks[item['check_id']])
        rows.append({
            'check_id': item['check_id'], 'owner': checks[item['check_id']].get('owner'),
            'boundary': item['boundary'], 'stage': item['stage'], 'status': item['status'],
            'feedback': feedback, 'development_eligible': development_check(item),
            'selection_basis': 'explicit-request' if explicit else 'declared-impact-or-prerequisite',
            'required_by': sorted(parent['check_id'] for parent in results if item['check_id'] in parent['dependency_ids']),
            'prerequisites': item['dependency_ids'],
            'elapsed_seconds': item.get('elapsed_seconds'), 'evidence_source': item.get('evidence_source'),
            'source_inputs': sorted(checks[item['check_id']].get('inputs', [])),
            'budget_exceeded': bool(feedback and item.get('elapsed_seconds', 0) > feedback['expected_seconds']),
        })
    pending = sorted(item['check_id'] for item in results if item['status'] != 'passed')
    return {
        'mode': 'development' if development else 'explicit' if explicit else 'impact',
        'coverage': 'integration-pending' if development else 'requested-checks-only' if explicit else 'selected-boundary-only',
        'pending_check_ids': pending,
        'estimated_execution_seconds': sum(feedback_for(checks[item['check_id']]).get('expected_seconds', 0)
                                           for item in results if not development or development_check(item)),
        'estimates_complete': all('feedback' in checks[item['check_id']] for item in results if not development or development_check(item)),
        'checks': rows,
        'not_selected': [{'check_id': identity, 'reason': 'not-in-selected-impact'} for identity, check in sorted(checks.items())
                         if 'feedback' in check and identity not in selected],
    }


def inventory(checks: dict) -> dict:
    findings = [finding for identity, check in checks.items() if isinstance(check, dict) for finding in validate_feedback(identity, check)]
    return {'schema': 'repo/check-feedback-inventory/v1', 'verdict': 'gap' if findings else 'planned', 'findings': findings,
            'checks': [{'check_id': identity, 'owner': check.get('owner'), 'boundary': check.get('boundary', 'commit'),
                        'stage': check.get('stage'), 'effects': check.get('effects'), 'feedback': check.get('feedback')}
                       for identity, check in sorted(checks.items()) if isinstance(check, dict)],
            'limitation': 'Missing feedback is unclassified; existing gates are unchanged. This inventory executes no checks.'}


def evidence_summary(report: dict, *, all_inputs: bool = False) -> dict:
    """Project this invocation's evidence, never qualify another stage or run."""
    policy = report['execution_policy']
    stale_codes = {'check-input-changed-before-execution', 'check-input-changed-during-execution',
                   'check-input-changed-before-completion', 'check-catalog-changed-before-execution',
                   'check-catalog-changed-during-execution'}
    stale = {item.get('check_id') for item in report['findings'] if item['code'] in stale_codes}
    catalog_drift = any(item['code'] in {'check-catalog-changed-during-planning', 'check-catalog-changed-during-invocation'}
                        for item in report['findings'])

    def observed(items):
        rows = []
        for item in items:
            outcome = ('interrupted' if type(item.get('exit_code')) is int and item['exit_code'] < 0
                       else 'stale' if item['check_id'] in stale or
                       (catalog_drift and item['stage'] == 'local' and item['status'] not in {'failed', 'deferred'})
                       else 'absent' if item['status'] == 'pending' else item['status'])
            rows.append({'check_id': item['check_id'], 'status': item['status'], 'observation': outcome})
        outcomes = {item['observation'] for item in rows}
        status = next((value for value in ('interrupted', 'failed', 'stale', 'uncertain', 'blocked', 'absent', 'deferred')
                       if value in outcomes), 'passed' if rows and outcomes == {'passed'} else 'not-selected')
        return {'status': status, 'checks': rows}

    local = [item for item in report['checks'] if item['stage'] == 'local']
    eligibility = {item['check_id']: item['development_eligible'] for item in policy['checks']}
    requested = [item for item in local if (report['boundary'] == 'integration' or item['boundary'] == 'commit')
                 and (policy['mode'] != 'development' or eligibility[item['check_id']])]
    affected = observed(local)
    complete_selection = (policy['mode'] == 'impact' and report['boundary'] == 'integration'
                          and bool(report['changed_inputs'] or all_inputs) and not report['findings'])
    affected['coverage'] = ('complete-declared-impact' if complete_selection and affected['status'] == 'passed'
                            else 'not-established')
    summary = {'requested_local': observed(requested), 'affected_local_integration': affected}
    for name, stage in (('package_qualification', 'package'), ('live_target_proof', 'deploy'), ('acceptance', 'acceptance')):
        summary[name] = {**observed([item for item in report['checks'] if item['stage'] == stage]),
                         'coverage': 'not-evaluated', 'authority': 'owning-stage-controller'}
    return summary


def safe_run(report: dict, run_id: str) -> dict:
    """Allowlist observation fields; no child output, runtime values or imported proof."""
    return {
        'schema': 'repo/test-run-observation/v1', 'run_id': run_id,
        'source_revision': report['source_revision'], 'verdict': report['verdict'], 'boundary': report['boundary'],
        'selection_mode': report['execution_policy']['mode'],
        'integration_claim': False if report['execution_policy']['mode'] in ('development', 'explicit') else None,
        'changed_inputs': report['changed_inputs'],
        'checks': [{**{key: item[key] for key in ('check_id', 'stage', 'boundary', 'status', 'exit_code', 'elapsed_seconds',
                                                   'input_digest', 'evidence_key', 'evidence_source', 'cache_invalidation_reasons') if key in item},
                    'runtime_digest': hashlib.sha256(json.dumps(item['runtime_identity'], sort_keys=True).encode()).hexdigest() if item.get('runtime_identity') else None}
                   for item in report['checks']],
        'pending_check_ids': report['execution_policy']['pending_check_ids'],
        'execution_policy': report['execution_policy'],
        **({'evidence_summary': report['evidence_summary']} if 'evidence_summary' in report else {}),
        'timings': report['execution_summary']['timings'],
        'findings': [{'code': item['code'], **({'check_id': item['check_id']} if 'check_id' in item else {})} for item in report['findings']],
        'authority': 'historical-observation-only; cannot seed trusted reuse or live acceptance',
    }


def render(report: dict) -> str:
    policy = report.get('execution_policy', {})
    lines = [f"Verdict: {report['verdict']} — {policy.get('coverage', 'inventory-only')}"]
    for name, item in report.get('evidence_summary', {}).items():
        lines.append(f"Evidence {name}: {item['status']}" + (f"; {item['coverage']}" if 'coverage' in item else ''))
    if policy:
        lines.append(f"Estimated command seconds: {policy['estimated_execution_seconds']} (advisory; complete estimates: {policy['estimates_complete']})")
    for item in policy.get('checks', report.get('checks', [])):
        feedback = feedback_for(item)
        rationale = feedback['rationale'] if feedback else 'Feedback unclassified; existing gate retained.'
        lines.append(f"{item['check_id']}: {item.get('status', 'declared')} | {item.get('boundary')} / {item.get('stage')} | {rationale}")
        if item.get('prerequisites'):
            lines.append('  prerequisites: ' + ', '.join(item['prerequisites']))
        if 'selection_basis' in item:
            lines.append('  selected: ' + item['selection_basis'] + '; required by: ' + (', '.join(item['required_by']) or 'impact seed'))
        if item.get('evidence_source'):
            lines.append(f"  result: {item['evidence_source']}; command seconds: {item.get('elapsed_seconds')}; estimate exceeded: {item['budget_exceeded']}")
    if policy.get('pending_check_ids'):
        lines.append('Pending: ' + ', '.join(policy['pending_check_ids']))
    if report.get('findings'):
        lines.append('Findings: ' + ', '.join(sorted({item['code'] for item in report['findings']})))
    if report.get('run_report_path'):
        lines.append('Run observation: ' + report['run_report_path'])
    return '\n'.join(lines) + '\n'


def retain_run(root: Path, report: dict) -> str:
    """Create new owned run files only. No cleanup or arbitrary output destination."""
    for directory in (root / '.cache', root / '.cache/test-runs'):
        if directory.is_symlink():
            raise ValueError('test-run-directory-unsafe')
        directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('test-run-directory-unsafe')
    parent = root / '.cache/test-runs'
    if parent.stat().st_mode & 0o077:
        raise ValueError('test-run-directory-unsafe')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex
    directory = parent / run_id
    directory.mkdir(mode=0o700)
    for name, contents in (('report.json', json.dumps(safe_run(report, run_id), sort_keys=True, indent=2) + '\n'),
                           ('summary.txt', render(report))):
        descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
    return str(directory.relative_to(root) / 'report.json')

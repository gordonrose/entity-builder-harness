# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.check-selection.execution-policy
#   version: 1
#   status: active
#   created_on: "2026-11-07"
#   updated_on: "2026-11-09"
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
        'timings': report['execution_summary']['timings'],
        'findings': [{'code': item['code'], **({'check_id': item['check_id']} if 'check_id' in item else {})} for item in report['findings']],
        'authority': 'historical-observation-only; cannot seed trusted reuse or live acceptance',
    }


def render(report: dict) -> str:
    policy = report.get('execution_policy', {})
    lines = [f"Verdict: {report['verdict']} — {policy.get('coverage', 'inventory-only')}"]
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

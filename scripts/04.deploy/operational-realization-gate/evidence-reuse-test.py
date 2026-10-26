#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.operational-realization-evidence-reuse
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [security, sre]
#   kind: test
#   purpose: Exercise current proof freshness, transitive input invalidation and unaffected immutable proof reuse through the real realization CLI.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh
from __future__ import annotations
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import yaml

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
spec = importlib.util.spec_from_file_location('realization', BASE / 'script.py')
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
contract = yaml.safe_load((BASE / 'fixtures/valid-contract.yml').read_text())
facts = yaml.safe_load((BASE / 'fixtures/preflight-normalized-facts.yml').read_text())
summary = yaml.safe_load((BASE / 'fixtures/valid-normalized-change-summary.yml').read_text())
now = datetime.now(timezone.utc)
stamp = lambda time: time.strftime('%Y-%m-%dT%H:%M:%SZ')
for item in facts['gate_evidence'] + facts['component_evidence']:
    item['timestamp'] = stamp(now)
summary['timestamp'] = stamp(now)
count = 0


def bind(selected_contract, selected_facts, selected_summary):
    bindings = module.evidence_bindings(selected_contract, selected_facts)
    for item in selected_facts['gate_evidence']:
        item['input_sha256'] = bindings['gates'][item['gate']]
    for item in selected_facts['component_evidence']:
        item['input_sha256'] = bindings['components'][item['component_id']]
    selected_summary['input_sha256'] = bindings['gates']['change-set']


def run(root, selected_contract, selected_facts, selected_summary, code=None):
    global count
    for name, value in [('contract', selected_contract), ('facts', selected_facts), ('summary', selected_summary)]:
        (root / (name + '.yml')).write_text(yaml.safe_dump(value))
    result = subprocess.run(['bash', str(BASE / 'script.sh'), '--contract', str(root / 'contract.yml'), '--facts', str(root / 'facts.yml'), '--change-summary', str(root / 'summary.yml'), '--through', 'execution-preflight', '--json'], cwd=ROOT, capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert result.returncode == (1 if code else 0), (result.returncode, report, result.stderr)
    if code: assert report['findings'] == [{'code': code}], report
    count += 1


with tempfile.TemporaryDirectory(prefix='realization-reuse-') as directory:
    root = Path(directory)
    run(root, contract, facts, summary)
    historical = copy.deepcopy(facts)
    for item in historical['gate_evidence'][:3]: item['timestamp'] = stamp(now - timedelta(days=120))
    historical['component_evidence'][0]['timestamp'] = stamp(now - timedelta(days=120))
    run(root, contract, historical, summary)
    for field, code in [('gate_evidence', 'normalized-facts-current-evidence-stale'), ('component_evidence', 'component-current-evidence-stale')]:
        stale = copy.deepcopy(historical)
        stale[field][3 if field == 'gate_evidence' else 1]['timestamp'] = stamp(now - timedelta(hours=1))
        run(root, contract, stale, summary, code)
    substituted = copy.deepcopy(facts); substituted['gate_evidence'][0]['check_id'] = 'unrelated-check'
    run(root, contract, substituted, summary, 'normalized-facts-check-not-declared')
    reordered = copy.deepcopy(facts); reordered['gate_evidence'][1], reordered['gate_evidence'][2] = reordered['gate_evidence'][2], reordered['gate_evidence'][1]
    run(root, contract, reordered, summary, 'normalized-facts-evidence-sequence-invalid')
    changed = copy.deepcopy(contract); changed['identities'][0]['permissions'].append('read-new-state')
    run(root, changed, facts, summary, 'gate-evidence-input-mismatch')
    # Reuse the actual package gate receipt byte-for-byte, including its old
    # timestamp, while source revalidation and target permission checks are new.
    # Preserving only the component receipt would not prove package-check reuse.
    rebound = copy.deepcopy(historical); refreshed_summary = copy.deepcopy(summary)
    old_artifact = copy.deepcopy(rebound['component_evidence'][0])
    old_package_gate = yaml.safe_dump(rebound['gate_evidence'][1]).encode()
    rebound['gate_evidence'][0]['timestamp'] = stamp(now)
    new_bindings = module.evidence_bindings(changed, rebound)
    for item in rebound['gate_evidence']:
        if item['gate'] != 'artifact': item['input_sha256'] = new_bindings['gates'][item['gate']]
    refreshed_summary['input_sha256'] = new_bindings['gates']['change-set']
    run(root, changed, rebound, refreshed_summary, 'component-evidence-input-mismatch')
    for item in rebound['component_evidence']: item['input_sha256'] = new_bindings['components'][item['component_id']]
    assert rebound['component_evidence'][0] == old_artifact
    assert yaml.safe_dump(rebound['gate_evidence'][1]).encode() == old_package_gate
    assert rebound['gate_evidence'][1]['input_sha256'] == new_bindings['gates']['artifact']
    run(root, changed, rebound, refreshed_summary)
    configuration = copy.deepcopy(contract); configuration['configuration_inputs'][0]['required_fields'].append('second-setting')
    run(root, configuration, facts, summary, 'gate-evidence-input-mismatch')
    # Retain that same actual gate receipt while refreshing all other bindings.
    # Changed package bytes, entrypoint, qualification configuration, or enabled
    # workload composition must specifically invalidate the retained artifact gate.
    for change in ('image', 'entrypoint', 'configuration', 'composition'):
        package_contract = copy.deepcopy(contract)
        if change == 'image': package_contract['artifacts'][0]['immutable_reference'] = 'sha256:' + 'd' * 64
        elif change == 'entrypoint': package_contract['artifacts'][0]['entrypoint'] = 'updated-entrypoint'
        elif change == 'configuration': package_contract['configuration_inputs'][0]['required_fields'].append('package-setting')
        else:
            package_contract['configuration_inputs'].append({'id': 'optional-package-setting', 'required_fields': [], 'optional_fields': [], 'sensitivity': 'internal'})
            package_contract['execution_units'][0]['configuration_inputs'].append('optional-package-setting')
            package_contract['edges'].append({'from': 'delivery-worker', 'to': 'optional-package-setting', 'purpose': 'reads-configuration'})
        package_facts = copy.deepcopy(facts); package_summary = copy.deepcopy(summary)
        if change == 'composition':
            package_facts['component_evidence'].append({'component_id': 'optional-package-setting', 'component_kind': 'configuration', 'check_id': 'configuration-check', 'timestamp': stamp(now), 'verdict': 'passed'})
        bind(package_contract, package_facts, package_summary)
        package_facts['gate_evidence'][1] = yaml.safe_load(old_package_gate)
        run(root, package_contract, package_facts, package_summary, 'gate-evidence-input-mismatch')
    backwards = copy.deepcopy(facts)
    backwards['gate_evidence'][4]['timestamp'] = stamp(now - timedelta(seconds=30))
    run(root, contract, backwards, summary, 'normalized-facts-evidence-time-order-invalid')
    stale_summary = copy.deepcopy(summary); stale_summary['timestamp'] = stamp(now - timedelta(hours=1))
    run(root, contract, facts, stale_summary, 'normalized-change-summary-stale')
    wrong_summary = copy.deepcopy(summary); wrong_summary['input_sha256'] = 'sha256:' + '0' * 64
    run(root, contract, facts, wrong_summary, 'normalized-change-summary-input-mismatch')
    runtime_contract = copy.deepcopy(contract); runtime_contract['artifacts'][0].pop('immutable_reference'); runtime_contract['artifacts'][0]['immutable_reference_mode'] = 'runtime-bound-sha256'
    runtime_facts = copy.deepcopy(facts); runtime_summary = copy.deepcopy(summary)
    runtime_facts['artifact_bindings'] = [{'component_id': 'delivery-artifact', 'immutable_reference': 'sha256:' + 'b' * 64, 'check_id': 'artifact-check', 'timestamp': stamp(now), 'verdict': 'passed'}]
    bind(runtime_contract, runtime_facts, runtime_summary)
    run(root, runtime_contract, runtime_facts, runtime_summary)
    runtime_facts['artifact_bindings'][0]['immutable_reference'] = 'sha256:' + 'c' * 64
    run(root, runtime_contract, runtime_facts, runtime_summary, 'gate-evidence-input-mismatch')
print(json.dumps({'schema': 'deploy/realization-evidence-reuse-test/v1', 'verdict': 'passed', 'evidence_class': 'simulated', 'checks': count}))

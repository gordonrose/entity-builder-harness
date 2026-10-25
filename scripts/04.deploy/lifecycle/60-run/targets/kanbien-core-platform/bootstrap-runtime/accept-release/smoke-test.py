#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.bootstrap-acceptance-writer
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove acceptance input parsing, retained rehearsal binding and validation-before-write using explicitly simulated temporary records.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.bootstrap-acceptance-writer.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/smoke-test.sh
import contextlib
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[8]
SOURCE = Path(__file__).with_name('script.py')
spec = importlib.util.spec_from_file_location('bootstrap_writer', SOURCE)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
SCOPE = Path('infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime')
original_bytes = writer.RECORD.read_bytes()

def invoke(arguments):
    output = io.StringIO()
    with patch.object(sys, 'argv', ['writer', *map(str, arguments)]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        code = writer.main()
    return code, json.loads(output.getvalue())

with patch.object(writer, 'receipt', side_effect=AssertionError('parser must not load proof')):
    assert invoke(['--inputs', '/tmp/future-inputs.yml', '--write', '--validate-arguments'])[0] == 0
    for args in ([], ['--inputs'], ['--inputs', 'x', '--receipt', 'y'], ['--receipt', 'x']):
        code, report = invoke(args)
        assert code == 1 and report['findings'] == [{'code': 'accepted-release-arguments-invalid'}], report

# Exercise the real verifier main path with controlled provider observations.
# A reused proof still reobserves the exact running task; stale proof starts one
# fresh verifier and cannot be relabelled as a reused current observation.
verify_spec = importlib.util.spec_from_file_location('bootstrap_verifier', SOURCE.parent.parent / 'verify-candidate/verify.py')
verifier = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(verifier)
TASK_PREFIX = 'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
DEFINITION_PREFIX = 'arn:aws:ecs:eu-west-1:337159794548:task-definition/'
runtime_arn, previous_arn, fresh_arn = (TASK_PREFIX + char * 32 for char in ('1', '2', '3'))
runtime_definition = DEFINITION_PREFIX + 'kanbien-core-platform-bootstrap-runtime:10'
verifier_definition = DEFINITION_PREFIX + 'kanbien-core-platform-release-verifier:11'
image = 'sha256:' + 'a' * 64
repository = '337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server'

def run_verifier(prior_age=1, runtime_change=None):
    now = datetime.now(timezone.utc)
    def stamp(value): return value.isoformat().replace('+00:00', 'Z')
    def completed(arn, age):
        return {'taskArn': arn, 'taskDefinitionArn': verifier_definition, 'lastStatus': 'STOPPED', 'startedAt': stamp(now - timedelta(minutes=age, seconds=2)), 'stoppedAt': stamp(now - timedelta(minutes=age)), 'containers': [{'name': 'private-release-verifier', 'exitCode': 0}]}
    prior, fresh = completed(previous_arn, prior_age), completed(fresh_arn, 0)
    runtime = {'taskArn': runtime_arn, 'taskDefinitionArn': runtime_definition, 'lastStatus': 'RUNNING', 'healthStatus': 'HEALTHY', 'group': 'service:' + verifier.SERVICE, 'containers': [{'name': 'kanbien-core-server', 'image': repository + '@' + image}]}
    if runtime_change: runtime.update(runtime_change)
    calls = []
    def aws(*parts):
        calls.append(parts)
        if parts[:2] == ('cloudformation', 'describe-stacks'):
            outputs = {'BootstrapRuntimeTaskDefinitionArn': runtime_definition, 'ReleaseVerifierTaskDefinitionArn': verifier_definition} if parts[-1] == verifier.RUNTIME else {'PrivateSubnetIds': 'subnet-fixture', 'VerifierSecurityGroupId': 'sg-fixture'}
            return True, {'Stacks': [{'LastUpdatedTime': stamp(now - timedelta(hours=1)), 'Outputs': [{'OutputKey': key, 'OutputValue': value} for key, value in outputs.items()]}]}, 'ok'
        if parts[:2] == ('ecs', 'describe-services'): return True, {'services': [{'runningCount': 1, 'taskDefinition': runtime_definition, 'deployments': [{'rolloutState': 'COMPLETED'}]}]}, 'ok'
        if parts[:2] == ('ecs', 'describe-task-definition'): return True, {'taskDefinition': {'containerDefinitions': [{'name': 'kanbien-core-server', 'image': repository + '@' + image}]}}, 'ok'
        if parts[:2] == ('ecs', 'list-tasks'): return True, {'taskArns': [runtime_arn if '--service-name' in parts else previous_arn]}, 'ok'
        if parts[:2] == ('ecs', 'describe-tasks'): return True, {'tasks': [{runtime_arn: runtime, previous_arn: prior, fresh_arn: fresh}[parts[-1]]]}, 'ok'
        if parts[:2] == ('logs', 'get-log-events'): return True, {'events': [{'message': '{"verdict":"accepted","code":"KANBIEN_CORE_RELEASE_VERIFIED"}'}]}, 'ok'
        if parts[:2] == ('ecs', 'run-task'): return True, {'tasks': [fresh]}, 'ok'
        raise AssertionError('Unexpected provider action: ' + str(parts))
    output = io.StringIO()
    with patch.object(sys, 'argv', ['verifier', '--receipt', '/tmp/simulated-package.json', '--json']), patch.object(verifier, 'candidate', return_value={'image_digest': image, 'source_revision': 'a' * 40}), patch.object(verifier, 'aws', side_effect=aws), contextlib.redirect_stdout(output):
        code = verifier.main()
    return code, json.loads(output.getvalue()), calls

for age, mode, task_arn, mutations in ((1, 'reused-completed-private-task', previous_arn, 0), (20, 'fresh-private-task', fresh_arn, 1)):
    code, report, calls = run_verifier(age)
    assert code == 0 and report['verdict'] == 'accepted', report
    facts = report['facts']
    assert facts['runtime_task_arn'] == runtime_arn and facts['verifier_task_arn'] == task_arn
    assert facts['verification_mode'] == mode and writer.observation_valid(facts)
    assert sum(parts[:2] == ('ecs', 'run-task') for parts in calls) == mutations
    assert sum(parts[:2] == ('ecs', 'describe-tasks') and parts[-1] == runtime_arn for parts in calls) == 1
for changed in ({'taskArn': TASK_PREFIX + '4' * 32}, {'taskDefinitionArn': 'unrelated'}, {'healthStatus': 'UNKNOWN'}, {'group': 'service:unrelated'}, {'containers': None}, {'containers': [{'name': 'kanbien-core-server', 'image': repository + '@sha256:' + 'b' * 64}]}):
    code, report, calls = run_verifier(runtime_change=changed)
    assert code == 1 and report['verdict'] == 'blocked', report
    assert not any(parts[:2] == ('ecs', 'run-task') for parts in calls)

with tempfile.TemporaryDirectory(prefix='bootstrap-acceptance-writer-') as directory:
    root = Path(directory)
    shutil.copytree(ROOT / SCOPE, root / SCOPE)
    record = root / SCOPE / '30-release-evidence/accepted-release.yml'
    record.chmod(0o640)
    accepted = yaml.safe_load(record.read_text())
    prior_metadata = writer.record_metadata(record.read_text())
    references = accepted['acceptance']
    for name in ('last_rehearsal', 'last_restoration_rehearsal'):
        evidence_path = record.parent / references[name]
        evidence = yaml.safe_load(evidence_path.read_text())
        evidence['evidence_class'] = 'simulated'
        evidence_path.write_text(yaml.safe_dump(evidence))
    release = accepted['release']
    candidate = {'source_revision': release['source_revision'], 'image_digest': release['image_digest'], 'receipt_reference': 'simulated-package-custody'}
    verification = {'schema': 'deploy/private-runtime-verification-report/v1', 'target': 'kanbien-core-platform', 'verdict': 'accepted', 'evidence_class': 'simulated', 'findings': [{'code': 'runtime-digest-and-private-verifier-accepted'}], 'facts': {name: release[name] for name in ('source_revision', 'image_digest', 'runtime_task_definition', 'verifier_task_definition')}}
    verification['facts'].update(observed_at=(datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat().replace('+00:00', 'Z'), runtime_task_arn=runtime_arn, verifier_task_arn=previous_arn)
    candidate_path, verification_path, inputs_path = (root / name for name in ('candidate.json', 'verification.json', 'inputs.yml'))
    candidate_path.write_text('{}')
    verification_path.write_text(json.dumps(verification))
    values = {'candidate_receipt': str(candidate_path), 'verification_report': str(verification_path), 'rehearsal': str(record.parent / references['last_rehearsal']), 'restoration_rehearsal': str(record.parent / references['last_restoration_rehearsal'])}
    inputs_path.write_text(yaml.safe_dump({'schema': 'deploy/acceptance-inputs/v1', 'target': 'kanbien-core-platform', 'scope': 'bootstrap-runtime', 'values': values}))
    with patch.object(writer, 'ROOT', root), patch.object(writer, 'RECORD', record), patch.object(writer, 'EVIDENCE_CLASS', 'simulated'), patch.object(writer, 'receipt', return_value=candidate):
        code, report = invoke(['--inputs', inputs_path, '--write'])
        assert code == 0 and report['verdict'] == 'rehearsed', report
        written = yaml.safe_load(record.read_text())
        assert written['status'] == 'rehearsed' and written['evidence_class'] == 'simulated'
        retained = written['release']['private_verification']
        assert retained['verified_at'] == verification['facts']['observed_at']
        assert retained['runtime_task_arn'] == runtime_arn and retained['verifier_task_arn'] == previous_arn
        current_metadata = writer.record_metadata(record.read_text())
        assert current_metadata['version'] == prior_metadata['version'] + 1
        assert current_metadata['created_on'] == prior_metadata['created_on']
        assert current_metadata['updated_on'] == written['acceptance']['accepted_at'][:10]
        assert written['cost_condition'] == accepted['cost_condition']
        assert record.stat().st_mode & 0o777 == 0o640
        metadata_check = subprocess.run(['bash', str(ROOT / 'scripts/01.harness/check-artifact-metadata-headers.sh'), '--proposed'], input=json.dumps({str(SCOPE / '30-release-evidence/accepted-release.yml'): record.read_text()}), text=True, capture_output=True, cwd=ROOT)
        assert metadata_check.returncode == 0, metadata_check.stdout + metadata_check.stderr
        assert all(written['acceptance'][name] == references[name] for name in ('last_rehearsal', 'last_restoration_rehearsal'))
        writer.validate_rendered(record.read_text())
        # The existing direct CLI can preserve valid rehearsals only for the
        # same immutable identity; rendered evidence still receives validation.
        assert invoke(['--receipt', candidate_path, '--verification-report', verification_path])[0] == 0
        prior = record.read_bytes()
        changed = {**candidate, 'image_digest': 'sha256:' + 'a' * 64}
        wrong = copy.deepcopy(verification)
        wrong['facts']['image_digest'] = changed['image_digest']
        verification_path.write_text(json.dumps(wrong))
        with patch.object(writer, 'receipt', return_value=changed):
            code, report = invoke(['--receipt', candidate_path, '--verification-report', verification_path, '--write'])
            assert code == 1 and report['findings'][0]['code'] == 'accepted-release-matching-rehearsal-required', report
            code, report = invoke(['--inputs', inputs_path, '--write'])
            assert code == 1 and report['findings'][0]['code'] == 'accepted-release-rehearsal-invalid', report
        assert record.read_bytes() == prior
        for field, invalid in (
            ('observed_at', None), ('observed_at', []), ('observed_at', {}), ('observed_at', True), ('observed_at', float('nan')),
            ('observed_at', 'not-a-timestamp'), ('observed_at', datetime.now().isoformat()),
            ('observed_at', (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()),
            ('observed_at', (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()),
            ('runtime_task_arn', None), ('runtime_task_arn', []), ('runtime_task_arn', 'arn:task/synthetic'),
            ('runtime_task_arn', runtime_arn.replace('337159794548', '111122223333')),
            ('runtime_task_arn', runtime_arn.replace('/kanbien-core-platform/', '/unrelated/')),
            ('verifier_task_arn', runtime_arn), ('verifier_task_arn', previous_arn[:-1]),
        ):
            invalid_report = copy.deepcopy(verification)
            invalid_report['facts'][field] = invalid
            verification_path.write_text(json.dumps(invalid_report))
            with patch.object(writer, 'write_record', side_effect=AssertionError('invalid observation must not write')):
                code, report = invoke(['--inputs', inputs_path, '--write'])
            assert code == 1 and report['findings'][0]['code'] == 'private-verification-observation-stale-or-invalid', (field, invalid, report)
            assert record.read_bytes() == prior
        for field in ('observed_at', 'runtime_task_arn', 'verifier_task_arn'):
            invalid_report = copy.deepcopy(verification)
            del invalid_report['facts'][field]
            verification_path.write_text(json.dumps(invalid_report))
            assert invoke(['--inputs', inputs_path, '--write'])[0] == 1 and record.read_bytes() == prior
        verification_path.write_text(json.dumps(verification))
        missing = root / 'missing.yml'
        code, report = invoke(['--receipt', candidate_path, '--verification-report', verification_path, '--rehearsal', missing, '--write'])
        assert code == 1 and record.read_bytes() == prior, report
        for invalid in (None, [], 'accepted', 0, False, {}, {**verification, 'schema': 'other/v1'}, {**verification, 'target': 'other'}):
            verification_path.write_text(json.dumps(invalid))
            code, report = invoke(['--inputs', inputs_path, '--write'])
            assert code == 1 and report['findings'][0]['code'] == 'private-verification-report-invalid', report
            assert record.read_bytes() == prior
        verification_path.write_text('{')
        code, report = invoke(['--inputs', inputs_path, '--write'])
        assert code == 1 and report['findings'][0]['code'] == 'private-verification-report-unreadable', report
        verification_path.write_text(json.dumps({**verification, 'facts': []}))
        code, report = invoke(['--inputs', inputs_path, '--write'])
        assert code == 1 and report['findings'][0]['code'] == 'private-verification-not-accepted', report
        verification_path.write_text(json.dumps(verification))
        for operation in ('fsync', 'replace'):
            with patch.object(writer.os, operation, side_effect=OSError('simulated write failure')):
                code, report = invoke(['--inputs', inputs_path, '--write'])
                assert code == 1 and report['findings'][0]['code'] == 'accepted-release-record-write-failed', report
            assert record.read_bytes() == prior
            assert not list(record.parent.glob('.accepted-release.yml.*.tmp'))
        # A failure from the owning validator must occur before any writer call.
        with patch.object(writer, 'validate_rendered', side_effect=ValueError('accepted-release-injected-validation-gap')), patch.object(writer, 'write_record', side_effect=AssertionError('must not write')):
            assert invoke(['--inputs', inputs_path, '--write'])[0] == 1
        with patch.object(writer, 'EVIDENCE_CLASS', 'live'):
            code, report = invoke(['--inputs', inputs_path, '--write'])
            assert code == 1 and report['findings'][0]['code'] == 'private-verification-report-invalid'
        assert record.read_bytes() == prior
        record.write_text('schema: invalid\n')
        code, report = invoke(['--inputs', inputs_path, '--write'])
        assert code == 1 and report['findings'][0]['code'] == 'accepted-release-record-invalid', report
        assert record.read_text() == 'schema: invalid\n'
    # Preserve the actual custody validator and exact validated-document capture
    # regression independently of the simulated acceptance integration above.
    qualified = {'schema': 'deploy/package-custody-receipt/v1', 'target': 'kanbien-core-platform', 'environment_class': 'private-bootstrap', 'provider_region_alias': 'aws-eu-west-1', 'candidate_id': 'kanbien-core-server-candidate', 'package_contract_id': 'kanbien-core-server-image', 'program_id': 'kanbien-core-server', 'source_revision': candidate['source_revision'], 'image_digest': candidate['image_digest'], 'release_identity': 'source-' + candidate['source_revision'], 'checked_at': datetime.now(timezone.utc).isoformat(), 'checks': {key: 'passed' for key in ('runnable_program_contract', 'dependency_boundary', 'delivery_access_static', 'delivery_access_live', 'local_image_smoke', 'ecr_scan', 'sbom', 'provenance_attestation')}, 'verdict': 'qualified', 'receipt_reference': 'github-actions-run:39464882266'}
    candidate_path.write_text(json.dumps(qualified))
    assert writer.receipt(candidate_path) == qualified
    real_run = subprocess.run
    def replace_original_after_validation(command, **kwargs):
        assert command[command.index('--receipt') + 1] != str(candidate_path)
        result = real_run(command, **kwargs)
        candidate_path.write_text(json.dumps({**qualified, 'receipt_reference': 'invalid'}))
        return result
    with patch.object(writer.subprocess, 'run', side_effect=replace_original_after_validation):
        assert writer.receipt(candidate_path) == qualified
    assert writer.receipt(candidate_path) is None
assert writer.RECORD.read_bytes() == original_bytes
print('Bootstrap acceptance writer passed: actual input contract, matching retained rehearsals, immutable identity changes, validation-before-write, metadata/mode preservation, atomic-write failures, exact custody capture, malformed arguments, fresh/reused exact-task observations, stale/future/missing observation rejection, and production rejection of simulation; canonical record unchanged.')

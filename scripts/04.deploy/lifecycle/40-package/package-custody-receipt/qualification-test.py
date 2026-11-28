#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.package-qualification-binding
#   version: 6
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise publication qualification, authenticated custody acquisition and immutable artifact binding through real CLIs.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/smoke-test.sh
#   - id: deploy.test.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment-sessions-test.py
"""Exercise artifact/configuration binding and actual publication guard CLIs."""
import copy
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml
import zipfile

ROOT=Path(__file__).resolve().parents[5]
HELPER=ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py'


class CustodyAcquisitionFixture:
    """Reusable real fake-gh process replies; never a qualified-success callback."""
    def __init__(self, directory, publication=None, source_revision='a'*40, run_id=123):
        self.root = Path(directory) / 'custody-acquisition'
        self.root.mkdir()
        self.state_path, self.calls_path = self.root / 'state.json', self.root / 'calls.jsonl'
        self.state = {'api': {}, 'binary': {}, 'verify': {}, 'sequences': {}, 'fail': {}, 'repositories': {}, 'images': {}}
        self.publications, self.receipts, self.requests = {}, {}, []
        executable = self.root / 'gh'
        executable.write_text('#!' + sys.executable + '\n' + '''import base64,json,os,sys
from pathlib import Path
state=json.loads(Path(os.environ['CUSTODY_FIXTURE_STATE']).read_text())
path=Path(os.environ['CUSTODY_FIXTURE_CALLS']);args=sys.argv[1:]
previous=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
with path.open('a') as stream:stream.write(json.dumps(args)+'\\n')
if args==['attestation','verify','--help']:
 key='help';value=state.get('help','--bundle-from-oci --source-ref --source-digest --signer-workflow --signer-digest --format --deny-self-hosted-runners')
elif args[:1]==['api']:
 key=args[-1];value=state['api'].get(key)
elif args[:2]==['attestation','verify']:
 key=args[2];value=state['verify'].get(key)
else:sys.exit(90)
if key in state['fail']:
 print('credential-canary-value',file=sys.stderr);sys.exit(state['fail'][key])
if key in state['sequences']:
 index=sum(1 for call in previous if call==args);values=state['sequences'][key];value=values[min(index,len(values)-1)]
if key in state['binary']:sys.stdout.buffer.write(base64.b64decode(state['binary'][key]))
elif key=='help':print(value)
elif value is not None:print(json.dumps(value))
else:sys.exit(91)
''')
        executable.chmod(0o755)
        self.environment = {'PATH': str(self.root) + os.pathsep + os.environ['PATH'],
                            'CUSTODY_FIXTURE_STATE': str(self.state_path), 'CUSTODY_FIXTURE_CALLS': str(self.calls_path)}
        if publication is None:
            workflow = b'name: controlled custody fixture\n'
            publication = {'target': 'example-target', 'account': '123456789012', 'region': 'eu-west-1',
                'candidate': 'example-candidate', 'package': 'example-package', 'program': 'example-program', 'pipeline': 'example-custody',
                'repository': 'example/package', 'repository_uri': '123456789012.dkr.ecr.eu-west-1.amazonaws.com/example/package',
                'repository_arn': 'arn:aws:ecr:eu-west-1:123456789012:repository/example/package',
                'source_repository': 'example/source', 'workflow': '.github/workflows/publish-example.yml', 'source_ref': 'refs/heads/main',
                'artifact_prefix': 'example-custody-', 'receipt_member': 'package-custody-receipt.json', 'workflow_sha256': hashlib.sha256(workflow).hexdigest()}
        else:
            workflow = (ROOT / publication['workflow']).read_bytes()
        self.publication = copy.deepcopy(publication)
        self.receipt = self.add(publication, source_revision, run_id, workflow_bytes=workflow)

    def add(self, publication, source_revision='a'*40, run_id=123, *, workflow_bytes=None):
        p = copy.deepcopy(publication)
        workflow_bytes = (ROOT / p['workflow']).read_bytes() if workflow_bytes is None else workflow_bytes
        repository_id = int(hashlib.sha256(p['source_repository'].encode()).hexdigest()[:8], 16) + 1
        workflow_id = int(hashlib.sha256(p['workflow'].encode()).hexdigest()[:8], 16) + 1
        digest = 'sha256:' + hashlib.sha256(('qualified:' + p['pipeline']).encode()).hexdigest()
        runnable = 'sha256:' + hashlib.sha256(('runnable:' + p['pipeline']).encode()).hexdigest()
        receipt = {'schema': 'deploy/package-custody-receipt/v1', 'target': p['target'], 'environment_class': 'private-fixture',
            'provider_region_alias': 'aws-' + p['region'], 'candidate_id': p['candidate'], 'package_contract_id': p['package'],
            'program_id': p['program'], 'source_revision': source_revision, 'image_digest': digest,
            'release_identity': 'source-' + source_revision, 'checked_at': '2026-11-27T00:00:00+00:00',
            'checks': {name: 'passed' for name in ('runnable_program_contract', 'dependency_boundary', 'delivery_access_static',
                'delivery_access_live', 'local_image_smoke', 'sbom', 'provenance_attestation', 'ecr_scan')},
            'verdict': 'qualified', 'receipt_reference': 'github-actions-run:' + str(run_id)}
        self.publications[run_id], self.receipts[run_id] = p, receipt
        base = 'repos/' + p['source_repository']
        repository = {'id': repository_id, 'full_name': p['source_repository']}
        run = {'id': run_id, 'run_attempt': 1, 'workflow_id': workflow_id, 'path': p['workflow'], 'head_sha': source_revision,
               'head_branch': p['source_ref'].removeprefix('refs/heads/'), 'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success',
               'repository': repository, 'head_repository': repository}
        self.state['api'].update({base: repository, base + '/actions/runs/' + str(run_id): run,
            base + '/actions/workflows/' + str(workflow_id): {'id': workflow_id, 'path': p['workflow']},
            base + '/contents/' + p['workflow'] + '?ref=' + source_revision:
                {'type': 'file', 'path': p['workflow'], 'encoding': 'base64', 'size': len(workflow_bytes),
                 'content': base64.b64encode(workflow_bytes).decode()}})
        self.state['api'][base + '/actions/runs/' + str(run_id) + '/artifacts?per_page=100&page=1'] = {'total_count': 1, 'artifacts': [
            {'id': run_id + 10000, 'name': p['artifact_prefix'] + str(run_id), 'expired': False,
             'workflow_run': {'id': run_id, 'repository_id': repository_id, 'head_repository_id': repository_id,
                              'head_branch': p['source_ref'].removeprefix('refs/heads/'), 'head_sha': source_revision}}]}
        repository_url = 'https://github.com/' + p['source_repository']
        workflow_url = repository_url + '/' + p['workflow'] + '@' + p['source_ref']
        certificate = {'issuer': 'https://token.actions.githubusercontent.com', 'sourceRepositoryURI': repository_url,
            'sourceRepositoryIdentifier': str(repository_id), 'sourceRepositoryDigest': source_revision, 'sourceRepositoryRef': p['source_ref'],
            'buildSignerURI': workflow_url, 'buildSignerDigest': source_revision, 'buildConfigURI': workflow_url, 'buildConfigDigest': source_revision,
            'buildTrigger': 'workflow_dispatch', 'runnerEnvironment': 'github-hosted',
            'runInvocationURI': repository_url + '/actions/runs/' + str(run_id) + '/attempts/1'}
        self.state['verify']['oci://' + p['repository_uri'] + '@' + digest] = [{'verificationResult': {
            'signature': {'certificate': certificate}, 'verifiedTimestamps': [{'type': 'Tlog', 'timestamp': '2026-11-27T00:00:00Z'}],
            'statement': {'predicateType': 'https://slsa.dev/provenance/v1',
                          'subject': [{'name': p['repository_uri'], 'digest': {'sha256': digest[7:]}}]}}}]
        self.state['repositories'][p['repository']] = {'repositories': [{'repositoryName': p['repository'], 'repositoryUri': p['repository_uri'],
            'imageTagMutability': 'IMMUTABLE', 'imageScanningConfiguration': {'scanOnPush': True}}]}
        self.state['images'][p['repository']] = {'qualified': digest, 'runnable': runnable}
        self.set_archive(run_id)
        return copy.deepcopy(receipt)

    def set_archive(self, run_id=123, entries=None):
        p = self.publications[run_id]
        contents = [(p['receipt_member'], json.dumps(self.receipts[run_id]).encode())] if entries is None else entries
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in contents: archive.writestr(name, value)
        raw = stream.getvalue()
        base = 'repos/' + p['source_repository']
        row = self.state['api'][base + '/actions/runs/' + str(run_id) + '/artifacts?per_page=100&page=1']['artifacts'][0]
        row.update(size_in_bytes=len(raw), digest='sha256:' + hashlib.sha256(raw).hexdigest())
        self.state['binary'][base + '/actions/artifacts/' + str(run_id + 10000) + '/zip'] = base64.b64encode(raw).decode()
        self.write()

    def write(self):
        self.state_path.write_text(json.dumps(self.state))

    def calls(self):
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()] if self.calls_path.exists() else []

    def aws(self, service, operation, **arguments):
        self.requests.append((service, operation, copy.deepcopy(arguments)))
        if service != 'ecr': raise AssertionError('unexpected provider service')
        if operation == 'describe-repositories': return copy.deepcopy(self.state['repositories'][arguments['repositoryNames'][0]])
        image = self.state['images'][arguments['repositoryName']]
        if operation == 'batch-get-image':
            if arguments['imageIds'] != [{'imageDigest': image['qualified']}]: raise AssertionError('wrong qualified image')
            manifest = {'mediaType': 'application/vnd.oci.image.index.v1+json', 'manifests': [
                {'mediaType': 'application/vnd.oci.image.manifest.v1+json', 'digest': image['runnable'], 'platform': {'architecture': 'amd64', 'os': 'linux'}}]}
            return {'images': [{'imageId': {'imageDigest': image['qualified']}, 'imageManifest': json.dumps(manifest)}]}
        if operation == 'describe-image-scan-findings':
            return {'repositoryName': arguments['repositoryName'], 'imageId': arguments['imageId'],
                    'imageScanStatus': {'status': 'COMPLETE'}, 'imageScanFindings': {'findingSeverityCounts': image.get('severity', {})}}
        raise AssertionError('unexpected provider operation')


class CustodyAcquisitionTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('custody_acquisition_fixture', HELPER.with_name('acquire.py'))
        self.owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.owner)
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.fixture = CustodyAcquisitionFixture(self.temporary.name)
        self.patch = patch.dict(os.environ, self.fixture.environment); self.patch.start(); self.addCleanup(self.patch.stop)
        self.p = self.fixture.publication
        self.base = 'repos/' + self.p['source_repository']
        self.run_path = self.base + '/actions/runs/123'
        self.artifacts_path = self.run_path + '/artifacts?per_page=100&page=1'
        self.image = 'oci://' + self.p['repository_uri'] + '@' + self.fixture.receipt['image_digest']

    def acquire(self, **changes):
        return self.owner.acquire_custody(**{'publication': self.p, 'run_id': 123, 'expected_source_revision': 'a'*40,
                                           'aws_provider': self.fixture.aws, **changes})

    def failure(self, reason, **changes):
        with self.assertRaises(self.owner.AcquisitionFailure) as raised: self.acquire(**changes)
        self.assertEqual(raised.exception.code, 'custody-acquisition-' + reason)
        self.assertNotIn('credential-canary', str(raised.exception))

    def test_actual_transport_receipt_certificate_and_distinct_manifest_handoff(self):
        result = self.acquire()
        self.assertEqual(result['receipt'], self.fixture.receipt)
        evidence = dict(result['evidence'])
        self.assertIsInstance(result['evidence'], tuple)
        with self.assertRaises(TypeError): result['evidence'][0][1] = 'changed'
        self.assertEqual(evidence['image_digest'], self.fixture.receipt['image_digest'])
        self.assertNotEqual(evidence['image_digest'], evidence['runnable_digest'])
        self.assertEqual((evidence['run_id'], evidence['run_attempt']), (123, 1))
        calls = self.fixture.calls()
        self.assertEqual(sum(call[-1] == self.run_path for call in calls), 2)
        self.assertEqual(sum(call[-1] == self.artifacts_path for call in calls), 2)
        verify = next(call for call in calls if call[:3] == ['attestation', 'verify', self.image])
        self.assertIn('--bundle-from-oci', verify)
        self.assertEqual(verify[verify.index('--source-digest') + 1], 'a'*40)
        self.assertEqual(verify[verify.index('--signer-workflow') + 1], self.p['source_repository'] + '/' + self.p['workflow'])
        self.assertEqual(self.fixture.requests[-1][2]['imageId'], {'imageDigest': evidence['runnable_digest']})
        self.assertFalse(any('https://' in str(value) or 'credential' in str(value) for value in evidence.values()))

    def test_closed_selection_and_missing_verifier_fail_before_remote_or_provider_use(self):
        for changes in ({'run_id': True}, {'run_id': 0}, {'run_id': '123'}, {'expected_source_revision': 'private-canary'},
                        {'publication': {**self.p, 'extra': 'private-canary'}}, {'publication': {**self.p, 'source_ref': 'refs/tags/task'}},
                        {'publication': {**self.p, 'receipt_member': '../receipt.json'}}, {'publication': {**self.p, 'repository_uri': 'foreign'}},
                        {'aws_provider': None}):
            self.failure('selection-invalid', **changes)
        self.assertEqual(self.fixture.calls(), [])
        self.fixture.state['fail']['help'] = 1; self.fixture.write()
        self.failure('verifier-unavailable')
        self.assertEqual(self.fixture.requests, [])

    def test_transport_limits_json_and_provider_failures_have_finite_private_causes(self):
        baseline = copy.deepcopy(self.fixture.state)
        for raw, reason in ((b'{"id":1,"id":2}', 'json-invalid'), (b'NaN', 'json-invalid'),
                            (b'credential-canary-value', 'json-invalid'), (b' ' * (self.owner.JSON_LIMIT + 1), 'response-too-large')):
            self.fixture.state = copy.deepcopy(baseline)
            self.fixture.state['binary'][self.base] = base64.b64encode(raw).decode(); self.fixture.write()
            self.failure(reason)
        self.fixture.state = copy.deepcopy(baseline); self.fixture.state['fail'][self.base] = 71; self.fixture.write()
        self.failure('github-unavailable'); self.assertEqual(self.fixture.requests, [])
        self.fixture.state = baseline; self.fixture.write()
        class ProviderFailure(Exception):
            def __init__(self, code): self.code = code
        for code, reason in (('aws-access-denied', 'aws-access-denied'), ('credential-canary-value', 'provider-unavailable')):
            def unavailable(*_args, **_kwargs): raise ProviderFailure(code)
            self.failure(reason, aws_provider=unavailable)
        self.assertIsInstance(self.owner.FAILURE_CODES, frozenset)
        self.assertEqual(str(self.owner.AcquisitionFailure('credential-canary-value')), 'custody-acquisition-observation-invalid')

    def test_two_publications_share_transport_without_sharing_digest_or_run_identity(self):
        second = {**self.p, 'pipeline': 'other-custody', 'repository': 'other/package',
                  'repository_uri': self.p['repository_uri'].replace('example/package', 'other/package'),
                  'repository_arn': self.p['repository_arn'].replace('example/package', 'other/package')}
        receipt = self.fixture.add(second, run_id=124, workflow_bytes=b'name: controlled custody fixture\n')
        first = self.acquire()
        result = self.acquire(publication=second, run_id=124)
        self.assertEqual(result['receipt'], receipt)
        self.assertNotEqual(result['receipt']['image_digest'], first['receipt']['image_digest'])
        self.assertEqual(dict(result['evidence'])['run_id'], 124)
        for run_id in (123, 124):
            self.assertEqual(sum(call[-1] == self.base + '/actions/runs/' + str(run_id) for call in self.fixture.calls()), 2)

    def test_exact_task_ref_survives_real_transport_and_rejects_relabelled_main(self):
        self.p['source_ref'] = 'refs/heads/chat/2026-11-26-22-09-reducing-aws-bill'
        self.fixture.add(self.p, workflow_bytes=b'name: controlled custody fixture\n')
        result = self.acquire()
        self.assertEqual(result['receipt'], self.fixture.receipt)
        verify = next(call for call in self.fixture.calls() if call[:3] == ['attestation', 'verify', self.image])
        self.assertEqual(verify[verify.index('--source-ref') + 1], self.p['source_ref'])
        baseline = copy.deepcopy(self.fixture.state)
        mutations = [
            (lambda s: s['api'][self.run_path].update(head_branch='main'), 'run-unconfirmed'),
            (lambda s: s['api'][self.artifacts_path]['artifacts'][0]['workflow_run'].update(head_branch='main'), 'artifact-unconfirmed'),
            (lambda s: s['verify'][self.image][0]['verificationResult']['signature']['certificate'].update(sourceRepositoryRef='refs/heads/main'), 'provenance-origin-mismatch'),
            (lambda s: s['verify'][self.image][0]['verificationResult']['signature']['certificate'].update(buildSignerURI='https://github.com/' + self.p['source_repository'] + '/' + self.p['workflow'] + '@refs/heads/main'), 'provenance-origin-mismatch'),
        ]
        for mutate, reason in mutations:
            self.fixture.state = copy.deepcopy(baseline); mutate(self.fixture.state); self.fixture.write()
            self.fixture.requests.clear()
            self.failure(reason)
            self.assertEqual(self.fixture.requests, [])
        with patch.object(self.owner.PUBLICATION, 'source_ref', side_effect=self.owner.PUBLICATION.PublicationFailure('publication-source-policy-invalid')) as checked:
            self.failure('selection-invalid')
            self.assertEqual(checked.call_count, 1)

    def test_run_repository_workflow_and_source_predicates_are_observed(self):
        baseline = copy.deepcopy(self.fixture.state)
        changes = [(self.base, 'id', 0, 'repository-unconfirmed'),
            (self.run_path, 'conclusion', 'failure', 'run-unconfirmed'), (self.run_path, 'event', 'push', 'run-unconfirmed'),
            (self.run_path, 'status', 'in_progress', 'run-unconfirmed'), (self.run_path, 'head_branch', 'task', 'run-unconfirmed'),
            (self.run_path, 'head_sha', 'b'*40, 'run-unconfirmed'), (self.run_path, 'path', '.github/workflows/other.yml', 'run-unconfirmed'),
            (self.run_path, 'head_repository', {'id': 1, 'full_name': self.p['source_repository']}, 'run-unconfirmed')]
        workflow_id = baseline['api'][self.run_path]['workflow_id']
        changes.append((self.base + '/actions/workflows/' + str(workflow_id), 'path', '.github/workflows/foreign.yml', 'workflow-unconfirmed'))
        for path, key, value, reason in changes:
            self.fixture.state = copy.deepcopy(baseline); self.fixture.state['api'][path][key] = value; self.fixture.write()
            with self.subTest(key=key): self.failure(reason)
        self.fixture.state = baseline; self.fixture.write()
        self.failure('workflow-source-mismatch', publication={**self.p, 'workflow_sha256': '0'*64})
        self.assertEqual(self.fixture.requests, [])

    def test_complete_pagination_and_unique_unexpired_bound_artifact(self):
        original = copy.deepcopy(self.fixture.state)
        row = original['api'][self.artifacts_path]['artifacts'][0]
        changes = [({'total_count': 1, 'artifacts': []}, 'artifacts-incomplete'),
                   ({'total_count': 0, 'artifacts': []}, 'artifact-unconfirmed'),
                   ({'total_count': 2, 'artifacts': [row, {**row, 'id': 999}]}, 'artifact-unconfirmed'),
                   ({'total_count': 2, 'artifacts': [row, row]}, 'artifacts-incomplete')]
        for key, value in (('expired', True), ('digest', None), ('size_in_bytes', True), ('workflow_run', {})):
            changes.append(({'total_count': 1, 'artifacts': [{**row, key: value}]}, 'artifact-unconfirmed'))
        for document, reason in changes:
            self.fixture.state = copy.deepcopy(original); self.fixture.state['api'][self.artifacts_path] = document; self.fixture.write()
            self.failure(reason)
        self.fixture.state = original
        self.fixture.state['api'][self.artifacts_path] = {'total_count': 2, 'artifacts': [{'id': 1, 'name': 'unrelated'}]}
        self.fixture.state['api'][self.artifacts_path.removesuffix('1') + '2'] = {'total_count': 2, 'artifacts': [row]}
        self.fixture.write(); self.acquire()

    def test_archive_digest_member_safety_and_receipt_bindings(self):
        original = copy.deepcopy(self.fixture.state)
        self.fixture.state['binary'][self.base + '/actions/artifacts/10123/zip'] = base64.b64encode(b'changed').decode()
        self.fixture.write(); self.failure('archive-digest-mismatch')
        self.fixture.state = original
        archive_path = self.base + '/actions/artifacts/10123/zip'
        corrupt = bytearray(base64.b64decode(self.fixture.state['binary'][archive_path]))
        with zipfile.ZipFile(io.BytesIO(corrupt)) as archive:
            entry = archive.getinfo(self.p['receipt_member'])
            corrupt[entry.header_offset + 30 + len(entry.filename.encode()) + len(entry.extra)] = 255
        self.fixture.state['binary'][archive_path] = base64.b64encode(corrupt).decode()
        self.fixture.state['api'][self.artifacts_path]['artifacts'][0]['digest'] = 'sha256:' + hashlib.sha256(corrupt).hexdigest()
        self.fixture.write(); self.failure('archive-invalid')
        raw = json.dumps(self.fixture.receipt).encode()
        link = zipfile.ZipInfo('linked.json'); link.create_system = 3; link.external_attr = 0o120777 << 16
        for entries, reason in (([('../escape.json', raw)], 'archive-invalid'),
                                ([('./receipt.json', raw)], 'archive-invalid'),
                                ([('C:/receipt.json', raw)], 'archive-invalid'),
                                ([(link, raw)], 'archive-invalid'),
                                ([(self.p['receipt_member'], b'{' )], 'json-invalid'),
                                ([('missing.json', raw)], 'receipt-missing'),
                                ([(self.p['receipt_member'], b'x' * 65537)], 'receipt-invalid')):
            self.fixture.set_archive(entries=entries); self.failure(reason)
        for field, value, reason in (('provider_region_alias', 'aws-eu-west-2', 'receipt-region-mismatch'),
                                    ('source_revision', 'b'*40, 'receipt-origin-mismatch'),
                                    ('receipt_reference', 'github-actions-run:999', 'receipt-origin-mismatch'),
                                    ('target', 'other-target', 'receipt-invalid')):
            receipt = {**self.fixture.receipt, field: value}
            self.fixture.set_archive(entries=[(self.p['receipt_member'], json.dumps(receipt).encode())]); self.failure(reason)

    def test_verified_certificate_origin_cannot_be_replaced_by_predicate_claims(self):
        baseline = copy.deepcopy(self.fixture.state)
        for field in ('issuer', 'sourceRepositoryURI', 'sourceRepositoryIdentifier', 'sourceRepositoryDigest', 'sourceRepositoryRef',
                      'buildSignerURI', 'buildSignerDigest', 'buildConfigURI', 'buildConfigDigest', 'buildTrigger', 'runnerEnvironment', 'runInvocationURI'):
            self.fixture.state = copy.deepcopy(baseline)
            result = self.fixture.state['verify'][self.image][0]['verificationResult']
            result['statement']['predicate'] = copy.deepcopy(result['signature']['certificate'])
            result['signature']['certificate'][field] = 'credential-canary-value'
            self.fixture.write(); self.failure('provenance-origin-mismatch')
        for value in ([], {}, None, [{'verificationResult': {}}]):
            self.fixture.state = copy.deepcopy(baseline); self.fixture.state['verify'][self.image] = value; self.fixture.write()
            self.failure('provenance-origin-mismatch' if value == [{'verificationResult': {}}] else 'provenance-unconfirmed')
        self.fixture.state = baseline
        self.fixture.state['verify'][self.image][0]['verificationResult']['statement']['subject'][0]['digest']['sha256'] = 'c'*64
        self.fixture.write(); self.failure('provenance-subject-mismatch')
        self.assertEqual(self.fixture.requests, [])

    def test_repository_scan_and_final_origin_reobservation_are_required(self):
        baseline = copy.deepcopy(self.fixture.state)
        for change in (lambda row: row.update(imageTagMutability='MUTABLE'), lambda row: row.update(repositoryUri='foreign'),
                       lambda row: row.update(imageScanningConfiguration=None), lambda row: row['imageScanningConfiguration'].update(scanOnPush=False)):
            self.fixture.state = copy.deepcopy(baseline); change(self.fixture.state['repositories'][self.p['repository']]['repositories'][0]); self.fixture.write()
            self.failure('publication-repository-not-confirmed')
        self.fixture.state = copy.deepcopy(baseline); self.fixture.state['images'][self.p['repository']]['severity'] = {'HIGH': 1}; self.fixture.write()
        self.failure('ecr-scan-blocked-severity')
        self.fixture.state = copy.deepcopy(baseline)
        first = self.fixture.state['api'][self.run_path]
        self.fixture.state['sequences'][self.run_path] = [first, {**first, 'run_attempt': 2}]
        self.fixture.calls_path.unlink(missing_ok=True); self.fixture.write(); self.failure('origin-changed')
        self.fixture.state = copy.deepcopy(baseline)
        first = self.fixture.state['api'][self.artifacts_path]
        self.fixture.state['sequences'][self.artifacts_path] = [first, {**first, 'artifacts': [{**first['artifacts'][0], 'digest': 'sha256:' + 'f'*64}]}]
        self.fixture.calls_path.unlink(missing_ok=True); self.fixture.write(); self.failure('origin-changed')


class QualificationTests(unittest.TestCase):
    def test_shell_later_container_and_node_boundaries(self):
        fake=r'''import json,os,sys
from pathlib import Path
name=Path(sys.argv[0]).name;args=sys.argv[1:];stage=name
state_path=Path(os.environ['FIXTURE_COUNTS']);state=json.loads(state_path.read_text()) if state_path.exists() else {}
def ordinal(key):
 state[key]=state.get(key,0)+1;state_path.write_text(json.dumps(state));return state[key]
if name=='git':print(os.environ['FIXTURE_ROOT']);sys.exit()
if name=='node':stage='http-'+str(ordinal('http'))
if name=='python3':
 if any(x.endswith('relational-package-test.py') for x in args):stage='relational'
 else:os.execv(os.environ['REAL_PYTHON'],[os.environ['REAL_PYTHON'],*args])
if name=='docker':
 if args[:2]==['container','inspect']:print('Error response from daemon: No such container: '+args[-1],file=sys.stderr);sys.exit(1)
 if args[0]=='info':stage='info'
 elif args[0]=='run':
  if any('entrypoints/kanbien-platform-postgresql-' in x for x in args):print('{"outcome":"failed"}');sys.exit(1)
  stage='server-'+str(ordinal('server'))
 elif args[0]=='exec':stage='receiver' if '--detach' in args else 'probe'
 elif args[:2]==['image','inspect']:stage='image-observation'
with open(os.environ['FIXTURE_CALLS'],'a') as stream:stream.write(stage+'\n')
if stage==os.environ['FAIL_STAGE']:print('credential-canary-value',file=sys.stderr);sys.exit(59 if name=='node' else 67 if name=='python3' else 41)
if stage=='image-observation':print('sha256:'+'a'*64)
'''
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);calls=root/'calls';counts=root/'counts'
            for name in ['git','docker','node','python3']:
                binary=root/name;binary.write_text('#!'+sys.executable+'\n'+fake);binary.chmod(0o755)
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'DOCKER_CONFIG':str(root/'docker-config'),'REAL_PYTHON':sys.executable,'FIXTURE_ROOT':str(ROOT),'FIXTURE_CALLS':str(calls),'FIXTURE_COUNTS':str(counts)}
            for stage,status,code in [('',0,None),('server-1',41,'CONTAINER_START_FAILED'),('http-1',59,'HTTP_OBSERVATION_FAILED'),('server-2',41,'CONTAINER_START_FAILED'),('receiver',41,'METRIC_RECEIVER_START_FAILED'),('http-2',59,'HTTP_OBSERVATION_FAILED'),('relational',67,'RELATIONAL_PACKAGE_FAILED')]:
                calls.write_text('');counts.unlink(missing_ok=True)
                result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy/legacy/kanbien-staging/smoke-test-platform-shell-image/script.sh'),'--image','sha256:'+'a'*64],cwd=ROOT,env={**env,'FAIL_STAGE':stage},capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,status,(stage,result.stdout,result.stderr));self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
                if code:self.assertIn('DIAGNOSTIC_CODE=SHELL_QUALIFICATION_'+code,result.stderr);self.assertIn('LIFECYCLE_STAGE=package',result.stderr)
                seen=calls.read_text().splitlines()
                if stage:self.assertEqual(seen[-1],stage)
                else:self.assertIn('Platform shell image smoke test passed.',result.stdout)

    def test_persistence_and_retained_later_boundary_matrix(self):
        fake=r'''import json,os,sys
from pathlib import Path
args=sys.argv[1:];name=Path(sys.argv[0]).name;stage=name
counts=Path(os.environ['FIXTURE_COUNTS'])
state=json.loads(counts.read_text()) if counts.exists() else {}
def ordinal(key):
 state[key]=state.get(key,0)+1;counts.write_text(json.dumps(state));return state[key]
if name=='git':print(os.environ['FIXTURE_ROOT']);sys.exit()
if name=='python3':os.execv(os.environ['REAL_PYTHON'],[os.environ['REAL_PYTHON'],*args])
if name=='sleep':sys.exit()
if name=='openssl':stage='tls-'+str(ordinal('tls'))
if name=='node':stage='http-'+str(ordinal('http')) if args[0]=='-' else 'digest' if args[:1]==['-e'] and 'repeat(64)' in args[1] else 'json'
if name=='docker':
 if args[:2] in (['container','inspect'],['network','inspect'],['volume','inspect']):
  kind,value=args[0],args[-1];messages={'container':'No such container: '+value,'network':'network '+value+' not found','volume':'get '+value+': no such volume'}
  print('Error response from daemon: '+messages[kind],file=sys.stderr);sys.exit(1)
 if args[0]=='info':stage='info'
 elif args[:2]==['network','create']:stage='network'
 elif args[:2]==['volume','create']:stage='volume'
 elif args[0]=='rm':stage='remove-'+str(ordinal('remove'))
 elif args[0]=='logs':stage='logs'
 elif args[0]=='exec':
  stage='receiver' if '--detach' in args else 'password' if any(x.startswith('\\password ') for x in args) else 'roles' if '-i' in args else 'probe'
 elif args[0]=='run':
  operation=next((x.split('=',1)[1] for x in args if x.startswith('PERSISTENCE_ADMINISTRATION_OPERATION=')),None)
  if operation:stage=operation
  elif '--user' in args:stage='certificate-install'
  elif any(x.startswith('postgres:') for x in args):stage='database'
  elif '--detach' in args:stage='server-'+str(ordinal('server'))
  elif any('LEGACY_PASSWORD=' in x for x in args):stage='legacy'
  elif any(x.endswith('persistence-migration.main.js') for x in args):stage='migration'
  elif any(x.endswith('persistence-restore-verifier.main.js') for x in args):stage='restore-read'
  elif any(x.endswith('persistence-verifier.main.js') for x in args):stage='read'
  else:stage='support'
with open(os.environ['FIXTURE_CALLS'],'a') as stream:stream.write(stage+'\n')
if stage==os.environ['FAIL_STAGE']:
 print('credential-canary-value',file=sys.stderr);sys.exit(31 if name=='openssl' else 59 if name=='node' else 41)
if name=='node':
 if stage=='digest':print('f'*64,end='')
 elif stage=='json':sys.stdin.read()
if name=='docker' and 'SHOW server_version_num' in args:print('180003')
if name=='docker' and args[0]=='run':
 codes={'bootstrap-identities':'PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED','observe-migration-state':'PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED','confirm-runtime-iam-access':'PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED','migration':'PERSISTENCE_MIGRATION_APPLIED','grant-runtime-application-access':'PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED','read':'KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED','restore-read':'KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED','revoke-runtime':'PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED','restore-runtime':'PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED'}
 codes['prove-effective-privilege']='PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN'
 if stage=='observe-migration-state' and ordinal('observation')>1:codes[stage]='PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED'
 if any('core_rejected_administrator' in x for x in args):print('{"code":"PERSISTENCE_ADMINISTRATION_ACCESS_DENIED"}');sys.exit(1)
 if 'PERSISTENCE_RESTORE_DIAGNOSTIC_MODE=connection' in args:
  if any('synthetic-rejected-admin-canary-3' in x for x in args):print('{}');sys.exit(1)
  print('{}')
 elif stage in codes:print(json.dumps({'code':codes[stage]},separators=(',',':')))
'''
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);calls=root/'calls';counts=root/'counts'
            for name in ['git','docker','openssl','node','python3','sleep']:
                binary=root/name;binary.write_text('#!'+sys.executable+'\n'+fake);binary.chmod(0o755)
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'REAL_PYTHON':sys.executable,'FIXTURE_ROOT':str(ROOT),'FIXTURE_CALLS':str(calls),'FIXTURE_COUNTS':str(counts)}
            common=[('tls-1',31,'CA_CREATION_FAILED'),('tls-2',31,'CERTIFICATE_REQUEST_FAILED'),('tls-3',31,'CERTIFICATE_SIGNING_FAILED'),('network',41,'NETWORK_CREATION_FAILED'),('volume',41,'VOLUME_CREATION_FAILED'),('certificate-install',41,'CERTIFICATE_INSTALL_FAILED'),('database',41,'CONTAINER_START_FAILED'),('roles',41,'ROLE_SETUP_FAILED'),('password',41,'CREDENTIAL_SETUP_FAILED'),('server-1',41,'CONTAINER_START_FAILED'),('http-1',59,'HTTP_OBSERVATION_FAILED'),('remove-1',41,'SERVER_REMOVAL_FAILED'),('http-2',59,'HTTP_OBSERVATION_FAILED')]
            for owner,prefix,arguments,extra in [
                ('smoke-test-core-server-persistence-image','PERSISTENCE_QUALIFICATION',[],[('digest',59,'DIGEST_PREPARATION_FAILED'),('legacy',1,'LEGACY_CONNECTION_FAILED'),('receiver',41,'METRIC_RECEIVER_START_FAILED'),('server-2',41,'CONTAINER_START_FAILED'),('remove-2',41,'SERVER_REMOVAL_FAILED'),('server-3',41,'CONTAINER_START_FAILED'),('http-3',59,'HTTP_OBSERVATION_FAILED')]),
                ('qualify-retained-persistence-rollback-image','RETAINED_QUALIFICATION',['--retained-image','fixture:retained','--support-image','fixture:support'],[('bootstrap-identities',1,'BOOTSTRAP_RESULT_FAILED'),('confirm-runtime-iam-access',1,'IAM_CONFIRMATION_RESULT_FAILED'),('migration',1,'MIGRATION_RESULT_FAILED'),('grant-runtime-application-access',1,'APPLICATION_GRANT_RESULT_FAILED'),('read',1,'READ_RESULT_FAILED'),('restore-read',1,'RESTORE_READ_RESULT_FAILED'),('revoke-runtime',1,'REVOCATION_RESULT_FAILED'),('restore-runtime',1,'IAM_RESTORATION_RESULT_FAILED'),('server-2',41,'CONTAINER_START_FAILED'),('http-3',59,'HTTP_OBSERVATION_FAILED')]),
            ]:
                for stage,status,code in [('',0,None),*common,*extra]:
                    calls.write_text('');counts.unlink(missing_ok=True)
                    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy/lifecycle/40-package'/owner/'script.sh'),*arguments],cwd=ROOT,env={**env,'FAIL_STAGE':stage},capture_output=True,text=True,timeout=15)
                    self.assertEqual(result.returncode,status,(owner,stage,result.stdout,result.stderr));self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
                    if code:self.assertIn('DIAGNOSTIC_CODE='+prefix+'_'+code,result.stderr);self.assertIn('LIFECYCLE_STAGE=package',result.stderr)
                    seen=calls.read_text().splitlines()
                    if stage:self.assertIn(stage,seen);self.assertEqual(seen[-1],stage)
                    else:self.assertIn('compatibility qualification passed.' if prefix=='RETAINED_QUALIFICATION' else 'package smoke test passed.',result.stdout)

    def test_build_and_shell_smoke_children_are_bounded_and_fail_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir();calls=root/'calls'
            for relative in ['scripts/04.deploy/shared/safe-command-diagnostics.sh','scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh','scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py','infra/04.deploy/03.product/image/Dockerfile.dockerignore']:
                local=root/relative;local.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,local)
            commands={
                'git':'#!/bin/sh\nif [ "$2" = HEAD ]; then printf "%040d\\n" 0; else printf "%s\\n" "$FIXTURE_ROOT"; fi\n',
                'bash':'#!/bin/sh\nprintf "%s\\n" "$1" >> "$FIXTURE_CALLS"\nif [ "$1" = "$FAIL_COMMAND" ]; then printf "credential-canary-value\\n" >&2; exit 23; fi\n',
                'python3':'#!/bin/sh\nprintf "%s\\n" "$1" >> "$FIXTURE_CALLS"\n',
                'node':'#!/bin/sh\nprintf "%s\\n" "$1" >> "$FIXTURE_CALLS"\nif [ "$1" = "$FAIL_COMMAND" ]; then printf "credential-canary-value\\n" >&2; exit 43; fi\n',
                'docker':'''#!/bin/sh
printf "docker:%s\\n" "$1" >> "$FIXTURE_CALLS"
if [ "$1" = build ]; then printf "credential-canary-value\\n" >&2; exit "$BUILD_EXIT"; fi
'''}
            for name,text in commands.items():
                path=binary/name;path.write_text(text);path.chmod(0o755)
            env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'FIXTURE_ROOT':str(root),'FIXTURE_CALLS':str(calls)}
            for owner,prefix,rejected in [
                ('lifecycle/40-package/build-core-server-image','CORE_IMAGE',[('scripts/04.deploy/validate-container-boundaries/script.sh',23,'CONTAINER_BOUNDARY_FAILED'),('scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',23,'PROGRAM_CONTRACT_FAILED'),('scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh',23,'DEPENDENCY_BOUNDARY_FAILED'),('scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh',23,'COMPILATION_FAILED'),('scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs',43,'RUNTIME_PREPARATION_FAILED')]),
                ('lifecycle/40-package/build-core-server-persistence-image','PERSISTENCE_IMAGE',[('scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh',23,'PROGRAM_CONTRACT_FAILED')]),
                ('legacy/kanbien-staging/build-platform-shell-image','SHELL_IMAGE',[('scripts/04.deploy/validate-container-boundaries/script.sh',23,'CONTAINER_BOUNDARY_FAILED')]),
            ]:
                for failed,status,code in [*rejected,('',47,'BUILD_FAILED'),('',0,None)]:
                    calls.write_text('')
                    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy'/owner/'script.sh')],cwd=root,env={**env,'FAIL_COMMAND':failed,'BUILD_EXIT':str(status if not failed else 0)},capture_output=True,text=True)
                    self.assertEqual(result.returncode,status,result.stdout+result.stderr);self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
                    seen=calls.read_text().splitlines()
                    if code:self.assertIn('DIAGNOSTIC_CODE='+prefix+'_'+code,result.stderr);self.assertIn('LIFECYCLE_STAGE=package',result.stderr)
                    if failed:self.assertEqual(seen.count(failed),1);self.assertNotIn('docker:build',seen);self.assertEqual(seen[-1],failed)
                    else:self.assertEqual(seen.count('docker:build'),1)
            # Actual smoke wrapper: the builder is a controlled failed child;
            # the existing cleanup remains separate and must preserve status23.
            cleanup=root/'scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py'
            cleanup.write_text('')  # python3 substitute records but does not execute it.
            calls.write_text('')
            result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy/legacy/kanbien-staging/smoke-test-platform-shell-image/script.sh')],cwd=root,env={**env,'FAIL_COMMAND':'scripts/04.deploy/legacy/kanbien-staging/build-platform-shell-image/script.sh','BUILD_EXIT':'0'},capture_output=True,text=True)
            self.assertEqual(result.returncode,23,result.stdout+result.stderr);self.assertIn('DIAGNOSTIC_CODE=SHELL_QUALIFICATION_BUILD_FAILED',result.stderr);self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
            self.assertEqual(calls.read_text().splitlines().count('scripts/04.deploy/legacy/kanbien-staging/build-platform-shell-image/script.sh'),1)

    def test_capture_native_faults_and_arguments_are_bounded(self):
        capture=ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sbom=root/'credential-canary-value.json';receipt=root/'receipt.json'
            keys=['QUALIFICATION_OUTCOME','ACCESS_OUTCOME','PUBLICATION_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
            env={**os.environ,**{key:'success' for key in keys},'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','IMAGE_DIGEST':'sha256:'+'b'*64}
            argv=['python3','-B',str(capture),'--target','catalog-target','--environment-class','private-fixture','--provider-region-alias','provider-local-fixture','--candidate','catalog-candidate','--package-contract','catalog-image','--program','catalog-worker','--scan-check','vulnerability_scan','--sbom',str(sbom),'--output',str(receipt)]
            for payload,code in [(b'credential-canary-value','custody-evidence-invalid'),(b'\xffcredential-canary-value','custody-evidence-invalid'),(b'{}','custody-sbom-invalid')]:
                sbom.write_bytes(payload)
                result=subprocess.run(argv,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout),{'verdict':'failed','code':code});self.assertFalse(receipt.exists());self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
            sbom.write_text('{"spdxVersion":"SPDX-2.3"}')
            for modified,environment,code in [(argv,{**env,'ACCESS_OUTCOME':'skipped'},'custody-prerequisite-not-successful'),([*argv[:argv.index('vulnerability_scan')],'credential-canary-value',*argv[argv.index('vulnerability_scan')+1:]],env,'custody-scan-kind-invalid'),([*argv[:-1],str(root/'missing'/'credential-canary-value')],env,'custody-evidence-invalid')]:
                result=subprocess.run(modified,env=environment,capture_output=True,text=True)
                self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['code'],code);self.assertFalse(receipt.exists());self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
            result=subprocess.run([*argv,'--credential-canary-value'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stderr),{'verdict':'failed','code':'custody-evidence-invalid'});self.assertNotIn('credential-canary-value',result.stdout+result.stderr)

    def test_receipt_and_workflow_unicode_reads_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);receipt=root/'credential-canary-value.json';receipt.write_bytes(b'\xffcredential-canary-value')
            validator=ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py'
            argv=['python3','-B',str(validator),'--receipt',str(receipt),'--expected-target','catalog-target','--expected-candidate','catalog-candidate','--expected-package-contract','catalog-image','--expected-program','catalog-worker','--json']
            result=subprocess.run(argv,capture_output=True,text=True)
            self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['findings'],[{'code':'receipt-unreadable'}]);self.assertNotIn('credential-canary-value',result.stdout+result.stderr)
            result=subprocess.run(['python3','-B',str(validator),'--receipt'],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stderr)['findings'],[{'code':'arguments-invalid'}])
            for kind,filename,code in [('core-server','publish-kanbien-core-platform-core-server.yml','workflow-missing'),('core-server-persistence','publish-kanbien-core-platform-core-server-persistence.yml','workflow-missing'),('core-server-persistence-observability-collector','publish-kanbien-core-platform-observability-collector.yml','collector-custody-artifact-unreadable')]:
                local=root/'.github/workflows'/filename;local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(b'\xffcredential-canary-value')
                guard=ROOT/'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform'/(kind+'-package-custody')/'verify-workflow.py'
                argv=['python3','-B',str(guard),'--json']
                if kind.endswith('collector'):argv+=['--workflow',str(local)]
                result=subprocess.run(argv,cwd=root,capture_output=True,text=True)
                self.assertEqual(result.returncode,1,result.stderr);self.assertIn(code,{item['code'] for item in json.loads(result.stdout)['findings']});self.assertNotIn('Traceback',result.stderr);self.assertNotIn('credential-canary-value',result.stdout+result.stderr)

    def test_tls_and_password_setup_preserve_status_without_native_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);events=root/'calls'
            docker=root/'docker';docker.write_text('''#!/usr/bin/env python3
import json,os,sys
args=sys.argv[1:]
with open(os.environ['FIXTURE_CALLS'],'a') as stream:stream.write(json.dumps(args)+'\\n')
if args[:2] in (['container','inspect'],['network','inspect'],['volume','inspect']):
 kind,name=args[0],args[-1];messages={'container':'No such container: '+name,'network':'network '+name+' not found','volume':'get '+name+': no such volume'}
 print('Error response from daemon: '+messages[kind],file=sys.stderr);sys.exit(1)
if 'SHOW server_version_num' in args:print('180003');sys.exit(0)
if args[0]=='exec' and any(value.startswith('\\\\password ') for value in args):print('credential-canary-value',file=sys.stderr);sys.exit(39)
sys.exit(0)
''');docker.chmod(0o755)
            openssl=root/'openssl';openssl.write_text('#!/bin/sh\nprintf "credential-canary-value\\n" >&2\nexit "$OPENSSL_EXIT"\n');openssl.chmod(0o755)
            git=root/'git';git.write_text('#!/bin/sh\nprintf "%s\\n" "$FIXTURE_ROOT"\n');git.chmod(0o755)
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'FIXTURE_ROOT':str(ROOT),'FIXTURE_CALLS':str(events)}
            for owner,prefix,arguments in [('smoke-test-core-server-persistence-image','PERSISTENCE_QUALIFICATION',[]),('qualify-retained-persistence-rollback-image','RETAINED_QUALIFICATION',['--retained-image','fixture:retained','--support-image','fixture:support'])]:
                script=ROOT/'scripts/04.deploy/lifecycle/40-package'/owner/'script.sh'
                for status,expected,code in [('31',31,'CA_CREATION_FAILED'),('0',39,'CREDENTIAL_SETUP_FAILED')]:
                    events.write_text('')
                    result=subprocess.run(['/bin/bash',str(script),*arguments],cwd=ROOT,env={**env,'OPENSSL_EXIT':status},capture_output=True,text=True,timeout=15)
                    self.assertEqual(result.returncode,expected,result.stdout+result.stderr);self.assertIn('DIAGNOSTIC_CODE='+prefix+'_'+code,result.stderr);self.assertNotIn('credential-canary-value',result.stdout+result.stderr);self.assertEqual(json.loads(result.stdout.splitlines()[-1])['verdict'],'passed')
                    calls=[json.loads(line) for line in events.read_text().splitlines()]
                    if status=='31':self.assertFalse(any(item[:2]==['network','create'] for item in calls))
                    else:self.assertEqual(sum(item[0]=='exec' and any(value.startswith('\\password ') for value in item) for item in calls),1)

    def test_exact_artifact_config_reuse_and_invalidation_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker'
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_IMAGE_ID"\n');binary.chmod(0o755)
            config=root/'config.yml';config.write_text('enabled: true\n');receipt=root/'receipt.json'
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'TEST_IMAGE_ID':'sha256:'+'a'*64}
            def run(action,expected=0,**extra):
                result=subprocess.run(['python3','-B',str(HELPER),action,'--image','fixture:tag','--receipt',str(receipt),'--input',str(config)],env={**env,**extra},capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr);return result
            run('record');run('verify');historical=receipt.read_bytes()
            run('verify',1,TEST_IMAGE_ID='sha256:'+'b'*64)
            config.write_text('enabled: false\n');run('verify',1)
            config.write_text('enabled: true\n');run('verify')
            run('record',1)
            self.assertEqual(receipt.read_bytes(),historical)

    def test_publication_guards_reject_control_and_identity_substitution(self):
        for kind, filename, job_name, qualify_name in [
            ('core-server','publish-kanbien-core-platform-core-server.yml','publish-core-server','Qualify the declared core-server candidate'),
            ('core-server-persistence','publish-kanbien-core-platform-core-server-persistence.yml','qualify-and-publish','Qualify declarations and actual candidate payload'),
            ('core-server-persistence-observability-collector','publish-kanbien-core-platform-observability-collector.yml','build-and-qualify','Qualify exact collector startup with non-secret configuration'),
        ]:
            with self.subTest(route=kind), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/'.github/workflows').mkdir(parents=True)
                # Validators are the actual CLI; only workflow input is disposable.
                guard=ROOT/'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform'/(kind+'-package-custody')/'verify-workflow.py'
                original=(ROOT/'.github/workflows'/filename).read_text();workflow=yaml.safe_load(original)
                local=root/'.github/workflows'/filename
                shutil.copytree(ROOT/'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image',root/'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image')
                shutil.copytree(ROOT/'scripts/04.deploy/lifecycle/40-package/build-candidate-image',root/'scripts/04.deploy/lifecycle/40-package/build-candidate-image')
                def run(text, expected):
                    local.write_text(text)
                    args=['python3','-B',str(guard),'--json']
                    if kind.endswith('collector'):args+=['--workflow',str(local)]
                    result=subprocess.run(args,cwd=root,capture_output=True,text=True)
                    self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
                    return json.loads(result.stdout)
                if kind.endswith('collector'):
                    relative='scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh'
                    nested=root/relative;nested.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,nested)
                run(original,0)
                if kind=='core-server-persistence':
                    for change in ['omitted','conditional','suppressed','substituted','reordered','unprepared']:
                        broken=copy.deepcopy(workflow);steps=broken['jobs'][job_name]['steps'];item=next(x for x in steps if x.get('name')=='Enforce approved source')
                        if change=='omitted':steps.remove(item)
                        elif change=='conditional':item['if']='false'
                        elif change=='suppressed':item['continue-on-error']=True
                        elif change=='substituted':item['run']='true'
                        elif change=='reordered':steps.remove(item);steps.append(item)
                        else:steps.remove(item);steps.insert(1,item)
                        report=run(yaml.safe_dump(broken,sort_keys=False),1)
                        self.assertIn({'code':'workflow-qualification-route-invalid'},report['findings'],change)
                    broken=copy.deepcopy(workflow);broken['jobs'][job_name]['environment']='unprotected'
                    report=run(yaml.safe_dump(broken,sort_keys=False),1)
                    self.assertIn({'code':'workflow-qualification-route-invalid'},report['findings'])
                    for stage in ['Prove fixed delivery read access','Retain pre-publication identity','Retain safe failed-operation evidence']:
                        for change in ['omitted','suppressed','substituted','reordered']:
                            broken=copy.deepcopy(workflow);steps=broken['jobs'][job_name]['steps'];item=next(x for x in steps if x.get('name')==stage)
                            if change=='omitted':steps.remove(item)
                            elif change=='suppressed':item['continue-on-error']=True
                            elif change=='reordered':steps.remove(item);steps.insert(0,item)
                            elif 'run' in item:item['run']=item['run'].replace('--operation reserve','--operation reconcile')
                            else:item['with']['overwrite']=True
                            run(yaml.safe_dump(broken,sort_keys=False),1)
                if kind.endswith('collector'):
                    nested_original=nested.read_text()
                    proof=next(line for line in nested_original.splitlines() if line.startswith('exec python3'))
                    for mutated in [nested_original.replace(proof,proof+' || true'),nested_original.replace(proof,'if false; then '+proof+'; fi'),nested_original.replace(proof,''),nested_original.replace('trap - EXIT\n\n'+proof,proof+'\ntrap - EXIT'),nested_original.replace('set -euo pipefail','set +e')]:
                        nested.write_text(mutated);run(original,1)
                    nested.write_text(nested_original)

                    for replacement in ['--output observability-collector.trivy.json || true', '--output observability-collector.trivy.json; true', '--output other.json']:
                        report=run(original.replace('--output observability-collector.trivy.json',replacement),1)
                        self.assertIn('collector-qualification-route-invalid',{item['code'] for item in report['findings']})
                    for replacement in ['id: unobserved_scan','id: vulnerability_scan\n        if: false',"id: vulnerability_scan\n        env: {TRIVY_SKIP_FILES: '*'}"]:
                        run(original.replace('id: vulnerability_scan',replacement),1)
                    for stage in ['Verify collector archive provenance','Export exact qualified collector archive','Verify archive is the scanned qualified payload','Install pinned portable scanner','Retrieve exact qualified collector archive','Retain vulnerability scan artifact']:
                        for mutation in ['omitted','conditional','substituted']:
                            broken=copy.deepcopy(workflow)
                            owner=next(job for job in broken['jobs'].values() if any(item.get('name')==stage for item in job.get('steps',[])))
                            item=next(item for item in owner['steps'] if item.get('name')==stage)
                            if mutation=='omitted':owner['steps'].remove(item)
                            elif mutation=='conditional':item['if']='false'
                            elif 'run' in item:item['run']+=' || true'
                            else:item['with']['name']='unrelated-artifact'
                            run(yaml.safe_dump(broken,sort_keys=False),1)
                # Each later proof is an executable prerequisite, not a name
                # whose presence can survive a conditional/suppressed body.
                later_job='complete-custody' if kind.endswith('collector') else job_name
                for stage in ['Generate SBOM','Attest collector provenance' if kind.endswith('collector') else 'Attest image provenance','Attest collector SBOM' if kind.endswith('collector') else 'Attest image SBOM','Write and validate safe collector custody receipt' if kind.endswith('collector') else 'Write and validate safe package-custody receipt','Upload safe collector custody evidence' if kind.endswith('collector') else 'Upload safe package-custody evidence']:
                    for change in ['omitted','conditional','suppressed','substituted','reordered','environment-substituted']:
                        broken=copy.deepcopy(workflow);later=broken['jobs'][later_job]['steps'];item=next(x for x in later if x.get('name')==stage)
                        if change=='omitted':later.remove(item)
                        elif change=='conditional':item['if']='false'
                        elif change=='suppressed':item['continue-on-error']=True
                        elif change=='environment-substituted':item['env']={'BASH_ENV':'injected-shell-environment'}
                        elif change=='substituted':
                            if 'uses' in item:item['uses']='actions/checkout@v4'
                            else:item['run']+='\ntrue'
                        else:later.remove(item);later.insert(0,item)
                        run(yaml.safe_dump(broken,sort_keys=False),1)
                if not kind.endswith('collector'):
                    for change in ['omitted','conditional','suppressed','reordered','shell-suppressed','digest-substitution']:
                        broken=copy.deepcopy(workflow);later=broken['jobs'][job_name]['steps'];item=next(x for x in later if x.get('name')=='Require clean ECR scan')
                        if change=='omitted':later.remove(item)
                        elif change=='conditional':item['if']='false'
                        elif change=='suppressed':item['continue-on-error']=True
                        elif change=='reordered':later.remove(item);later.insert(0,item)
                        elif change=='shell-suppressed':item['run']+=' || true'
                        else:item['run']=item['run'].replace('steps.image.outputs.digest','steps.unrelated.outputs.digest')
                        run(yaml.safe_dump(broken,sort_keys=False),1)
                for mutation in ['omitted','conditional','failure-suppressed','reordered','substituted','publication-tag-substitution','publication-failstop-disabled','publication-identity-suppressed']:
                    broken=copy.deepcopy(workflow);steps=broken['jobs'][job_name]['steps'];qualify=next(x for x in steps if x.get('name')==qualify_name)
                    if mutation=='omitted':steps.remove(qualify)
                    elif mutation=='conditional':qualify['if']='false'
                    elif mutation=='failure-suppressed':qualify['continue-on-error']=True
                    elif mutation=='reordered':steps.remove(qualify);steps.append(qualify)
                    elif mutation=='substituted':qualify['run']=qualify['run'].replace('bash ','echo ',1)
                    else:
                        pubjob=broken['jobs']['complete-custody'] if kind.endswith('collector') else broken['jobs'][job_name]
                        publish=next(x for x in pubjob['steps'] if x.get('name','').startswith(('Publish immutable','Publish exact')))
                        if kind=='core-server-persistence':
                            if mutation=='publication-failstop-disabled':publish['run']+=' || true'
                            elif mutation=='publication-identity-suppressed':publish['run']=publish['run'].replace('--operation publish','--operation reconcile')
                            else:publish['run']=publish['run'].replace('/publication.py','/unrelated.py')
                        elif mutation=='publication-failstop-disabled':publish['run']=publish['run'].replace('docker pull ', 'set +e\ndocker pull ')
                        elif mutation=='publication-identity-suppressed':publish['run']=publish['run'].replace('= "$qualified_image"','= "$qualified_image" || true')
                        else:publish['run']=publish['run'].replace('docker tag "$qualified_image"','docker tag unrelated:tag')
                    report=run(yaml.safe_dump(broken,sort_keys=False),1)
                    self.assertTrue(any('qualification-route-invalid' in x['code'] for x in report['findings']),report)

    def test_shell_workflow_and_durable_custody_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir()
            git=binary/'git';git.write_text('#!/bin/sh\nprintf "%s\\n" "$FIXTURE_ROOT"\n');git.chmod(0o755)
            paths=['.github/workflows/deploy-platform-shell-staging.yml','infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml','infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml','scripts/04.deploy/legacy/kanbien-staging/build-platform-shell-image/script.sh','scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/qualify-image.sh','scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py']
            for relative in paths:
                destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,destination)
            workflow_path=root/paths[0];original=workflow_path.read_text();workflow=yaml.safe_load(original)
            def run(value,expected):
                workflow_path.write_text(value)
                result=subprocess.run(['bash',str(ROOT/'scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/script.sh')],cwd=root,env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'FIXTURE_ROOT':str(root)},capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            run(original,0)
            qualifier=root/'scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/qualify-image.sh';qualifier_original=qualifier.read_text()
            smoke=next(line for line in qualifier_original.splitlines() if line.startswith('bash scripts/'))
            for mutated in [qualifier_original.replace(smoke,smoke+' || true'),qualifier_original.replace(smoke,'if false; then '+smoke+'; fi'),qualifier_original.replace(smoke,''),qualifier_original.replace(smoke+'\n','')+'\n'+smoke,qualifier_original.replace('set -euo pipefail','set +e')]:
                qualifier.write_text(mutated);run(original,1)
            qualifier.write_text(qualifier_original)
            for mutation in ['omitted','conditional','suppressed','reordered','substituted','custody-omitted','custody-outcome-forged','upload-overwrite','scan-omitted','scan-suppressed','scan-substituted','sbom-conditional','attestation-conditional','published-identity-suppressed']:
                broken=copy.deepcopy(workflow);steps=broken['jobs']['build-image']['steps'];qualify=next(item for item in steps if item.get('name')=='Qualify exact platform shell image')
                if mutation=='omitted':steps.remove(qualify)
                elif mutation=='conditional':qualify['if']='false'
                elif mutation=='suppressed':qualify['continue-on-error']=True
                elif mutation=='reordered':steps.remove(qualify);steps.append(qualify)
                elif mutation=='substituted':qualify['run']='echo bypass'
                elif mutation=='custody-omitted':steps.remove(next(item for item in steps if item.get('name')=='Capture durable package custody receipt'))
                elif mutation=='custody-outcome-forged':next(item for item in steps if item.get('name')=='Capture durable package custody receipt')['env']['QUALIFICATION_OUTCOME']='success'
                elif mutation=='upload-overwrite':next(item for item in steps if item.get('name')=='Retain immutable package custody evidence')['with']['overwrite']=True
                elif mutation=='scan-omitted':steps.remove(next(item for item in steps if item.get('name')=='Read ECR scan finding counts'))
                elif mutation=='scan-suppressed':next(item for item in steps if item.get('name')=='Read ECR scan finding counts')['run']+=' || true'
                elif mutation=='scan-substituted':next(item for item in steps if item.get('name')=='Read ECR scan finding counts')['run']='echo passed'
                elif mutation=='sbom-conditional':next(item for item in steps if item.get('name')=='Generate image SBOM')['if']='false'
                elif mutation=='attestation-conditional':next(item for item in steps if item.get('name')=='Attest image provenance')['if']='false'
                else:next(item for item in steps if item.get('name')=='Verify published target-platform image')['run']+='\nset +e'
                run(yaml.safe_dump(broken,sort_keys=False),1)
            emitter=ROOT/'scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/emit-custody.py'
            sbom=root/'sbom.json';sbom.write_text('{"spdxVersion":"SPDX-2.3"}')
            receipt=root/'custody.json';keys=['SOURCE_CHECKS_OUTCOME','QUALIFICATION_OUTCOME','CREDENTIALS_OUTCOME','REGISTRY_LOGIN_OUTCOME','PUBLISHED_IMAGE_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
            environment={**os.environ,**{key:'success' for key in keys},'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'456','PUBLISHED_DIGEST':'sha256:'+'b'*64,'SBOM_PATH':str(sbom)}
            for key in keys:
                failed=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env={**environment,key:'skipped'},capture_output=True,text=True)
                self.assertEqual(failed.returncode,1,failed.stdout+failed.stderr);self.assertFalse(receipt.exists())
            accepted=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env=environment,capture_output=True,text=True);self.assertEqual(accepted.returncode,0,accepted.stdout+accepted.stderr)
            checked=subprocess.run(['python3','-B',str(ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py'),'--receipt',str(receipt),'--expected-target','kanbien-staging','--expected-candidate','platform-shell','--expected-package-contract','kanbien-staging-platform-shell','--expected-program','platform-shell','--json'],capture_output=True,text=True)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr);proof=json.loads(receipt.read_text());self.assertEqual(proof['receipt_reference'],'github-actions-run:456');self.assertEqual(proof['source_revision'],'a'*40)
            original_receipt=receipt.read_bytes();duplicate=subprocess.run(['python3','-B',str(emitter),'--output',str(receipt)],env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original_receipt)

    def test_common_capture_requires_real_outcomes_and_immutable_valid_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sbom=root/'sbom.json';sbom.write_text('{"spdxVersion":"SPDX-2.3"}');receipt=root/'receipt.json'
            keys=['QUALIFICATION_OUTCOME','ACCESS_OUTCOME','PUBLICATION_OUTCOME','SCAN_OUTCOME','SBOM_OUTCOME','PROVENANCE_OUTCOME','SBOM_ATTESTATION_OUTCOME']
            environment={**os.environ,**{key:'success' for key in keys},'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','IMAGE_DIGEST':'sha256:'+'b'*64}
            argv=['python3','-B',str(ROOT/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py'),'--target','catalog-target','--environment-class','private-fixture','--provider-region-alias','provider-local-fixture','--candidate','catalog-candidate','--package-contract','catalog-image','--program','catalog-worker','--scan-check','vulnerability_scan','--sbom',str(sbom),'--output',str(receipt)]
            for key in keys:
                result=subprocess.run(argv,env={**environment,key:'skipped'},capture_output=True,text=True);self.assertEqual(result.returncode,1,result.stdout);self.assertFalse(receipt.exists())
            result=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr);original=receipt.read_bytes()
            duplicate=subprocess.run(argv,env=environment,capture_output=True,text=True);self.assertEqual(duplicate.returncode,1);self.assertEqual(receipt.read_bytes(),original)

    def test_shell_actual_qualification_resume_and_failure_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'bin';binary.mkdir();docker=binary/'docker'
            docker.write_text('#!/bin/sh\nif [ "$1" = image ]; then printf "sha256:'+'a'*64+'\\n"; fi\n');docker.chmod(0o755)
            smoke=root/'scripts/04.deploy/legacy/kanbien-staging/smoke-test-platform-shell-image/script.sh';smoke.parent.mkdir(parents=True);smoke.write_text('#!/bin/sh\ntouch "$SMOKE_MARKER"\nexit "$SMOKE_RESULT"\n')
            capture=root/'scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py';capture.parent.mkdir(parents=True);shutil.copy2(HELPER,capture)
            for relative in ['infra/04.deploy/03.product/image/Dockerfile','infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml','scripts/04.deploy/legacy/kanbien-staging/smoke-test-platform-shell-image/relational-package-test.py','infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml']:
                destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text('synthetic input')
            adapter='scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py'
            (root/adapter).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/adapter,root/adapter)
            (root/'infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml').write_text('Resources: {Worker: {Type: "AWS::ECS::TaskDefinition", Properties: {ContainerDefinitions: [{Name: worker, Command: [node, worker.js]}]}}}')
            for existing in ['true','false']:
                for status in [23,0]:
                    output=root/(existing+'-'+str(status));output.mkdir();marker=output/'smoke-called';github=output/'github-output'
                    environment={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'EXISTING_IMAGE':existing,'EXISTING_DIGEST':'sha256:'+'b'*64,'ECR_URI':'fixture.example/repository','CANDIDATE_IMAGE':'fixture:tag','RUNNER_TEMP':str(output),'GITHUB_OUTPUT':str(github),'SMOKE_MARKER':str(marker),'SMOKE_RESULT':str(status)}
                    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deployment-workflow/qualify-image.sh')],cwd=root,env=environment,capture_output=True,text=True)
                    self.assertEqual(result.returncode,status,result.stdout+result.stderr);self.assertTrue(marker.exists())
                    if status:self.assertFalse((output/'qualified-image.json').exists());self.assertFalse(github.exists())
                    else:self.assertEqual(json.loads((output/'qualified-image.json').read_text())['image_id'],'sha256:'+'a'*64);self.assertIn('image_id=sha256:',github.read_text())

    def test_configuration_projection_reuses_permissions_and_invalidates_runtime_cli(self):
        adapter='scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker';binary.write_text('#!/bin/sh\nprintf "sha256:'+'a'*64+'\\n"\n');binary.chmod(0o755)
            ordinary=root/'input';ordinary.write_text('package proof');receipt=root/'receipt.json';config=root/'template.yml'
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']}
            source=(ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml').read_text()
            def run(action,expected=0,selector='core-server-persistence'):
                result=subprocess.run(['python3','-B',str(HELPER),action,'--image','fixture:tag','--receipt',str(receipt),'--input',str(ordinary),'--configuration-input',adapter,str(config),selector],cwd=ROOT,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
            config.write_text(source);run('record');run('verify');historical=receipt.read_bytes()
            self.assertIn('rds-db:connect',source)
            config.write_text(source.replace('rds-db:connect','rds-db:changed-permission'));run('verify')
            self.assertIn('Value: kanbienpersistence',source)
            config.write_text(source.replace('Value: kanbienpersistence','Value: different-database'));run('verify',1)
            config.write_text(source);run('verify');self.assertEqual(receipt.read_bytes(),historical)
            missing=json.loads(historical);missing.pop('configuration_inputs');receipt.write_text(json.dumps(missing));run('verify',1)
            receipt.unlink()
            fixture={'Mappings':{'Settings':{'Local':{'Endpoint':'http://first.invalid'}},'Unrelated':{'Local':{'Value':'initial'}}},'Resources':{'Worker':{'Type':'AWS::ECS::TaskDefinition','Properties':{'ContainerDefinitions':[{'Name':'worker','Command':['node','catalog.js'],'Environment':[{'Name':'CATALOG_ENDPOINT','Value':{'Fn::FindInMap':['Settings','Local','Endpoint']}}]}]}}}}
            original=copy.deepcopy(fixture)
            config.write_text(yaml.safe_dump(fixture));run('record',selector='worker');run('verify',selector='worker')
            fixture['Mappings']['Unrelated']['Local']['Value']='changed';config.write_text(yaml.safe_dump(fixture));run('verify',selector='worker')
            fixture['Mappings']['Settings']['Local']['Endpoint']='http://changed.invalid';config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            fixture=copy.deepcopy(original);fixture['Resources']['Worker']['Properties']['ContainerDefinitions'][0]['Command']=['node','unrelated.js'];config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            fixture=copy.deepcopy(original);fixture['Resources']['Worker']['Properties']['ContainerDefinitions'][0]['Environment'][0]['Value']={'Fn::Unsupported':['hidden-input']};config.write_text(yaml.safe_dump(fixture));run('verify',1,selector='worker')
            config.write_text(yaml.safe_dump(original));run('verify',selector='worker')

    def test_missing_engine_is_unavailable_not_passed_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=root/'docker';binary.write_text('#!/bin/sh\nexit 1\n');binary.chmod(0o755)
            for owner in ['lifecycle/40-package/build-core-server-image','lifecycle/40-package/smoke-test-core-server-image','legacy/kanbien-staging/smoke-test-platform-shell-image']:
                result=subprocess.run(['bash',str(ROOT/'scripts/04.deploy'/owner/'script.sh'),'--allow-skip-without-engine'],cwd=ROOT,env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']},capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,77,result.stdout+result.stderr)
                self.assertIn('SKIP:',result.stdout)
                self.assertNotIn('image smoke test passed',result.stdout.lower())

if __name__=='__main__':unittest.main(verbosity=2)

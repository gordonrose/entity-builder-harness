#!/usr/bin/env python3
"""Exercise exact, bounded finite-job execution without a Docker daemon."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-job-engine-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify finite command identity, closed completion observations, deadlines and owned cleanup fail safely.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import container_engine as engine
import finite_job_contracts as contracts
from test_container_engine import FakeDocker, BASE, BASE_ID, CID, COMMIT, IMAGE

FILES = [{'path': 'jobs/task.cjs', 'digest': 'sha256:' + 'f' * 64, 'bytes': 12}]


def profile():
    return {'schema': 'finite-job-profile/v1', 'id': 'fixture-success',
            'artifact': {'image_id': IMAGE, 'payload_digest': contracts.digest(FILES)},
            'execution': {'entrypoint': [engine.NODE], 'command': list(engine.JOB_COMMAND), 'working_dir': '/app'},
            'limits': {'timeout_seconds': 2, 'output_bytes': 4096},
            'completion': {'protocol': 'finite-job-terminal/v1', 'required_checks': ['fixture-calculation']}}


class JobDocker(FakeDocker):
    def __init__(self):
        super().__init__()
        self.image['Config']['Cmd'] = list(engine.JOB_COMMAND)
        self.inventory = deepcopy(FILES)
        self.job_output = None
        self.job_failure = None
        self.job_returncode = 0
        self.job_stderr = b''
        self.job_exit_code = 0
        self.job_oom = False
        self.job_running = False
        self.job_state_hook = None
        self.jobs = 0

    def __call__(self, argv, **kwargs):
        args = argv[3:]
        is_job = self.container and self.container['Config']['Cmd'] != ['-e', engine.INVENTORY_PROBE]
        if args[:2] == ['start', '--attach'] and is_job:
            self.calls.append(argv)
            self.snapshots.append(kwargs)
            self.jobs += 1
            self.container['State'].update(Running=self.job_running, ExitCode=self.job_exit_code, OOMKilled=self.job_oom)
            if self.job_state_hook:
                self.job_state_hook(self.container)
            if self.job_failure:
                raise self.job_failure
            env = dict(row.split('=', 1) for row in self.container['Config']['Env'])
            terminal = {'schema': 'finite-job-terminal/v1', 'run_id': env['RELEASE_CONTROL_RUN_ID'],
                        'profile_digest': env['RELEASE_CONTROL_PROFILE_DIGEST'], 'outcome': 'completed',
                        'checks': [{'id': 'fixture-calculation', 'verdict': 'passed'}]}
            raw = json.dumps(terminal).encode() if self.job_output is None else (
                self.job_output(terminal) if callable(self.job_output) else self.job_output)
            return subprocess.CompletedProcess(argv, self.job_returncode, raw, self.job_stderr)
        result = super().__call__(argv, **kwargs)
        if args[0] == 'create' and self.container:
            self.deleted = False
            config = self.container['Config']
            env = dict(row.split('=', 1) for row in self.image['Config']['Env'])
            for index, item in enumerate(args):
                if item == '--env':
                    key, value = args[index + 1].split('=', 1)
                    env[key] = value
            config['Env'] = [key + '=' + value for key, value in env.items()]
            if '--entrypoint' not in args:
                config['Cmd'] = args[args.index(IMAGE) + 1:]
        return result


class FiniteJobEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='finite-job-engine-test-')
        self.root = Path(self.temp.name)
        self.fake = JobDocker()
        self.engine = engine.Engine(self.root, runner=self.fake)
        self.profile = profile()
        self.files = deepcopy(FILES)

    def tearDown(self):
        self.temp.cleanup()

    def run_job(self):
        return self.engine.run_job(self.profile, self.files)

    def negative(self, code, outcome='failed', cleanup=True):
        receipt = self.run_job()
        self.assertEqual(receipt['outcome'], outcome)
        self.assertEqual(receipt['failure_code'], code)
        self.assertEqual(receipt['cleanup_verified'], cleanup)
        self.assertEqual(receipt['checks'], [])
        self.assertIsNone(receipt['terminal_digest'])
        self.assertFalse(receipt['authorized'])
        self.assertEqual(receipt['semantic_verdict'], 'unverified')
        self.assertNotIn('fixture-private-value', json.dumps(receipt))
        return receipt

    def test_success_requires_inventory_terminal_exit_and_cleanup(self):
        result = self.run_job()
        self.assertEqual(result['outcome'], 'completed')
        self.assertIsNone(result['failure_code'])
        self.assertEqual(result['exit_code'], 0)
        self.assertFalse(result['oom_killed'])
        self.assertTrue(result['cleanup_verified'])
        self.assertEqual(result['checks'], [{'id': 'fixture-calculation', 'verdict': 'passed'}])
        self.assertEqual(result['semantic_verdict'], 'unverified')
        self.assertEqual(result['qualification_verdict'], 'blocked')
        self.assertEqual(self.fake.jobs, 1)
        self.assertEqual(self.engine._owned, {})
        self.assertEqual(len([row for row in self.fake.calls if row[3] == 'rm']), 2)

    def test_job_uses_exact_command_and_fixed_restrictions(self):
        self.profile['execution']['command'][-1] = 'other-safe-mode'
        result = self.run_job()
        args = [call[3:] for call in self.fake.calls if call[3] == 'create'][-1]
        self.assertEqual(args[args.index(IMAGE) + 1:], self.profile['execution']['command'])
        self.assertEqual(args[args.index('--network') + 1], 'none')
        self.assertEqual(args[args.index('--user') + 1], '65532:65532')
        self.assertEqual(args[args.index('--memory') + 1], '512m')
        self.assertIn('--read-only', args)
        self.assertEqual(args[args.index('--log-driver') + 1], 'none')
        self.assertNotIn('--entrypoint', args)
        self.assertEqual(result['outcome'], 'completed')

    def test_only_nonce_and_profile_environment_are_added(self):
        with patch.dict(os.environ, {'AWS_SECRET_ACCESS_KEY': 'fixture-private-value', 'NODE_OPTIONS': '--inspect'}):
            result = self.run_job()
        args = [call[3:] for call in self.fake.calls if call[3] == 'create'][-1]
        values = [args[index + 1] for index, value in enumerate(args) if value == '--env']
        self.assertEqual(sorted(values), sorted(['RELEASE_CONTROL_RUN_ID=' + result['run_id'],
                                                'RELEASE_CONTROL_PROFILE_DIGEST=' + result['profile_digest']]))
        self.assertNotIn('fixture-private-value', json.dumps(self.fake.snapshots, default=str))

    def test_fresh_nonce_prevents_previous_terminal_replay(self):
        first = self.run_job()
        self.fake.job_output = json.dumps({'schema': 'finite-job-terminal/v1', 'run_id': first['run_id'],
            'profile_digest': first['profile_digest'], 'outcome': 'completed', 'checks': first['checks']}).encode()
        second = self.negative('terminal-invalid')
        self.assertNotEqual(first['run_id'], second['run_id'])

    def test_invalid_profile_is_rejected_before_docker(self):
        self.profile['execution']['command'] = ['-e', 'process.exit(0)']
        with self.assertRaises(contracts.ReleaseFailure):
            self.run_job()
        self.assertEqual(self.fake.calls, [])

    def test_fixture_image_cannot_be_accepted_as_production_server(self):
        with self.assertRaises(engine.EngineFailure):
            self.engine.inspect_image(IMAGE)
        self.assertEqual(self.engine.inspect_job_image(IMAGE)['command'], engine.JOB_COMMAND)

    def test_unreviewed_image_default_cannot_be_accepted_for_job(self):
        self.fake.image['Config']['Cmd'] = ['jobs/unreviewed-default.js']
        self.negative('image-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_product_image_can_run_a_declared_packaged_finite_command(self):
        self.fake.image['Config']['Cmd'] = list(engine.SERVER_COMMAND)
        self.assertEqual(self.engine.inspect_job_image(IMAGE)['command'], engine.SERVER_COMMAND)
        self.files[0]['path'] = '.cache/product/finite-task.js'
        self.fake.inventory = deepcopy(self.files)
        self.profile['artifact']['payload_digest'] = contracts.digest(self.files)
        self.profile['execution']['command'] = ['.cache/product/finite-task.js']
        receipt = self.run_job()
        self.assertEqual(receipt['outcome'], 'completed')
        self.assertEqual(receipt['profile']['execution']['command'], ['.cache/product/finite-task.js'])
        self.assertEqual(receipt['semantic_verdict'], 'unverified')
        self.assertEqual(self.fake.jobs, 1)

    def test_mutated_image_identity_fails_before_create(self):
        self.fake.image['Id'] = BASE_ID
        self.negative('image-mismatch')
        self.assertFalse(any(call[3] == 'create' for call in self.fake.calls))

    def test_unreviewed_image_environment_is_redacted(self):
        self.fake.image['Config']['Env'].append('AWS_SECRET_ACCESS_KEY=fixture-private-value')
        self.negative('image-mismatch')

    def test_payload_digest_mismatch_fails_before_inventory_container(self):
        self.profile['artifact']['payload_digest'] = BASE_ID
        self.negative('payload-mismatch')
        self.assertFalse(any(call[3] == 'create' for call in self.fake.calls))

    def test_inventory_content_mismatch_fails_before_job(self):
        self.fake.inventory[0]['digest'] = BASE_ID
        self.negative('payload-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_unexpected_file_in_image_fails_before_job(self):
        self.fake.inventory.append({'path': 'unexpected.js', 'digest': BASE_ID, 'bytes': 1})
        self.negative('payload-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_missing_inventory_file_fails_before_job(self):
        self.fake.inventory = []
        self.negative('payload-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_invalid_expected_inventory_fails_without_execution(self):
        self.files[0]['bytes'] = True
        self.negative('payload-mismatch')
        self.assertFalse(any(call[3] == 'create' for call in self.fake.calls))

    def test_unsorted_expected_inventory_rejected(self):
        self.files.append({'path': 'a.js', 'digest': BASE_ID, 'bytes': 1})
        self.profile['artifact']['payload_digest'] = contracts.digest(self.files)
        self.negative('payload-mismatch')

    def test_typescript_payload_fallback_rejected(self):
        self.files.append({'path': 'source/main.ts', 'digest': BASE_ID, 'bytes': 1})
        self.profile['artifact']['payload_digest'] = contracts.digest(self.files)
        self.fake.inventory = deepcopy(self.files)
        self.negative('payload-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_command_must_exist_in_verified_inventory(self):
        self.profile['execution']['command'][0] = 'jobs/missing.js'
        self.negative('command-mismatch')
        self.assertEqual(self.fake.jobs, 0)

    def test_exit_zero_without_terminal_does_not_pass(self):
        self.fake.job_output = b''
        self.negative('terminal-invalid')

    def test_malformed_terminal_is_redacted(self):
        self.fake.job_output = b'fixture-private-value'
        self.negative('terminal-invalid')

    def test_wrong_profile_terminal_rejected(self):
        self.fake.job_output = lambda doc: json.dumps({**doc, 'profile_digest': BASE_ID}).encode()
        self.negative('terminal-invalid')

    def test_duplicate_terminal_key_rejected(self):
        self.fake.job_output = lambda doc: (json.dumps(doc)[:-1] + ',"outcome":"completed"}').encode()
        self.negative('terminal-invalid')

    def test_extra_terminal_field_rejected(self):
        self.fake.job_output = lambda doc: json.dumps({**doc, 'secret': 'fixture-private-value'}).encode()
        self.negative('terminal-invalid')

    def test_terminal_with_missing_required_check_rejected(self):
        self.fake.job_output = lambda doc: json.dumps({**doc, 'checks': []}).encode()
        self.negative('terminal-invalid')

    def test_trailing_stdout_is_not_accepted(self):
        self.fake.job_output = lambda doc: json.dumps(doc).encode() + b'fixture-private-value'
        self.negative('terminal-invalid')

    def test_nonzero_exit_rejected_even_with_valid_terminal(self):
        self.fake.job_exit_code = 7
        self.fake.job_returncode = 7
        self.assertEqual(self.negative('exit-nonzero')['exit_code'], 7)

    def test_oom_killed_rejected_even_with_exit_zero(self):
        self.fake.job_oom = True
        self.assertTrue(self.negative('oom-killed')['oom_killed'])

    def test_attach_transport_failure_cannot_reuse_terminal(self):
        self.fake.job_returncode = 1
        self.negative('start-failed')

    def test_timeout_returns_safe_receipt_and_cleans_container(self):
        self.fake.job_failure = subprocess.TimeoutExpired(['fixture-private-value'], 2)
        result = self.negative('deadline-exceeded', 'timed-out')
        self.assertIsNone(result['exit_code'])
        self.assertTrue(self.fake.deleted)

    def test_keyboard_interrupt_returns_safe_receipt_and_cleans_container(self):
        self.fake.job_failure = KeyboardInterrupt()
        self.negative('interrupted', 'interrupted')
        self.assertTrue(self.fake.deleted)

    def test_output_limit_returns_safe_receipt_and_cleans_container(self):
        self.fake.job_output = b'fixture-private-value' * 4096
        self.negative('output-limit')
        self.assertTrue(self.fake.deleted)

    def test_stderr_output_limit_is_enforced_and_redacted(self):
        self.fake.job_stderr = b'fixture-private-value' * 4096
        self.negative('output-limit')
        self.assertTrue(self.fake.deleted)

    def test_keyboard_interrupt_kills_and_reaps_transport_process_group(self):
        process = Mock(pid=12345)
        process.wait.side_effect = [KeyboardInterrupt(), 0]
        with patch.object(engine.subprocess, 'Popen', return_value=process), patch.object(engine.os, 'killpg') as killed:
            with self.assertRaises(KeyboardInterrupt):
                engine._bounded_runner(['/usr/bin/docker', 'fixture'], cwd=self.root,
                                       env={'PATH': '/usr/bin:/bin'}, timeout=2, max_output=1024)
        killed.assert_called_once_with(12345, engine.signal.SIGKILL)
        self.assertEqual(process.wait.call_count, 2)

    def test_engine_disconnection_stays_unknown_and_cleans_container(self):
        self.fake.job_failure = OSError('fixture-private-value')
        self.negative('engine-unavailable', 'unknown')
        self.assertTrue(self.fake.deleted)

    def test_still_running_job_cannot_report_completed(self):
        self.fake.job_running = True
        self.negative('observation-unavailable', 'unknown')

    def test_unreadable_exit_status_cannot_report_completed(self):
        self.fake.job_exit_code = '0'
        self.negative('observation-unavailable', 'unknown')

    def test_network_change_after_execution_is_rejected(self):
        self.fake.job_state_hook = lambda row: row['HostConfig'].update(NetworkMode='bridge')
        self.negative('isolation-mismatch')

    def test_environment_change_after_execution_is_rejected(self):
        self.fake.job_state_hook = lambda row: row['Config']['Env'].append('SECRET=fixture-private-value')
        self.negative('isolation-mismatch')

    def test_container_command_change_is_rejected(self):
        self.fake.job_state_hook = lambda row: row['Config'].update(Cmd=['jobs/other.js'])
        self.negative('isolation-mismatch')

    def test_foreign_container_is_never_removed(self):
        self.fake.job_state_hook = lambda row: row['Config']['Labels'].update({engine.OWNER_LABEL: 'foreign'})
        self.negative('cleanup-failed', 'unknown', cleanup=False)
        self.assertEqual(len([row for row in self.fake.calls if row[3] == 'rm']), 1)

    def test_cleanup_failure_overrides_a_valid_terminal(self):
        def hook(args):
            if args[0] == 'rm' and self.fake.jobs:
                return subprocess.CompletedProcess(args, 1, b'', b'fixture-private-value')
        self.fake.hook = hook
        self.negative('cleanup-failed', 'unknown', cleanup=False)

    def test_cleanup_requires_confirmed_absence(self):
        def hook(args):
            if args[:2] == ['container', 'ls'] and self.fake.jobs:
                return subprocess.CompletedProcess(args, 0, CID.encode(), b'')
        self.fake.hook = hook
        self.negative('cleanup-failed', 'unknown', cleanup=False)

    def test_attach_deadline_and_output_bounds_are_profile_limits(self):
        self.profile['limits'] = {'timeout_seconds': 7, 'output_bytes': 2048}
        self.run_job()
        for call, snapshot in zip(self.fake.calls, self.fake.snapshots):
            if call[3:5] == ['start', '--attach']:
                last = snapshot
        self.assertEqual(last['timeout'], 7)
        self.assertEqual(last['max_output'], 2048)

    def test_job_build_uses_shared_manifest_binding_without_production_stage(self):
        context = self.root / 'context'
        context.mkdir()
        dockerfile = context / 'Dockerfile'
        dockerfile.write_text('fixture')
        self.assertEqual(self.engine.build_job_fixture(context, dockerfile, BASE, COMMIT), IMAGE)
        args = next(row[3:] for row in self.fake.calls if row[3] == 'build')
        self.assertNotIn('PAYLOAD_STAGE=verified', args)
        self.assertIn('RUNTIME_NODE_IMAGE=' + BASE, args)
        self.assertIn('--metadata-file', args)
        self.assertIn('--pull=false', args)
        self.assertNotIn('--tag', args)

    def test_job_build_rejects_unrelated_metadata_identity(self):
        context = self.root / 'context'
        context.mkdir()
        dockerfile = context / 'Dockerfile'
        dockerfile.write_text('fixture')
        self.fake.build_iid = 'sha256:' + '0' * 64
        with self.assertRaises(engine.EngineFailure) as caught:
            self.engine.build_job_fixture(context, dockerfile, BASE, COMMIT)
        self.assertEqual(caught.exception.code, 'local-container-build-identity-mismatch')


if __name__ == '__main__':
    unittest.main()

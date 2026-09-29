"""Verify finite fixture orchestration and closed public refusal boundaries."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.finite-job-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject stale finite-job evidence and unsafe public requests without granting product qualification or release authority.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
from functools import lru_cache
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import container_engine
import finite_job_conformance as conformance
import finite_job_contracts as contracts
import release_compiler as release
import result_consumption
from local_build_sandbox import canonical, digest

ROOT = DIRECTORY.parents[2]
WRAPPER = ROOT / 'scripts/04.deploy/smoke-test-platform-shell-image/script.sh'
SENTINEL = 'PRIVATE_FINITE_JOB_SENTINEL'
IMAGE_ID = 'sha256:' + 'a' * 64
REVISION = 'sha256:' + 'b' * 64
HEAD = 'c' * 40
RECIPE = 'sha256:' + 'd' * 64
FILES = [{'path': 'jobs/task.cjs', 'digest': digest(b'fixture'), 'bytes': 7}]
PROFILES = [{'id': 'product-migration', 'status': 'pending'}]
INVENTORY = digest(canonical(PROFILES))
LOCK = {
    'runtime_image': 'gcr.io/distroless/nodejs22-debian12@sha256:' + 'e' * 64,
    'runtime_config_digest': 'sha256:' + 'f' * 64,
}
ENGINE = {'client': '29.5.2', 'server': '29.5.2'}


def execution(profile, run_id, outcome, code):
    # Memoize only synthetic fixture creation; real conformance validators run
    # on every test invocation and every independently resealed mutation.
    return deepcopy(_execution(json.dumps(profile, sort_keys=True), run_id, outcome, code))


@lru_cache(maxsize=64)
def _execution(serialized_profile, run_id, outcome, code):
    profile = json.loads(serialized_profile)
    checks = [{'id': value, 'verdict': 'passed'} for value in profile['completion']['required_checks']]
    complete = outcome == 'completed'
    return contracts.make_result(profile, run_id, {
        'outcome': outcome, 'failure_code': code,
        'exit_code': 0 if complete or code == 'terminal-invalid' else (7 if code == 'exit-nonzero' else None),
        'oom_killed': False, 'terminal_digest': contracts.terminal_digest(profile, run_id, checks) if complete else None,
        'checks': checks if complete else [], 'cleanup_verified': code != 'cleanup-failed', 'elapsed_ms': 20,
    })


def seal(value):
    value['result_digest'] = digest(canonical({key: item for key, item in value.items() if key != 'result_digest'}))
    return value


def valid_result():
    cases = []
    for index, (case, outcome, code) in enumerate(conformance.CASES, 1):
        profile = conformance.profile(case, IMAGE_ID, FILES)
        cases.append({'case': case, 'expected_outcome': outcome, 'expected_failure_code': code,
                      'conformance_verdict': 'passed',
                      'execution': execution(profile, format(index, '032x'), outcome, code)})
    return seal({
        'schema': 'finite-job-conformance-result/v1', 'scope': 'inert-fixture-conformance',
        'verdict': 'passed', **conformance.BLOCKED,
        'started_at': '2026-09-29T20:00:00Z', 'completed_at': '2026-09-29T20:00:01Z',
        'repository_head': HEAD, 'runner_digest': REVISION,
        'artifact': {'image_id': IMAGE_ID, 'payload_digest': digest(canonical(FILES)),
                     'runtime_image': LOCK['runtime_image'], 'runtime_config_digest': LOCK['runtime_config_digest'],
                     'recipe_digest': RECIPE},
        'payload_files': deepcopy(FILES), 'engine': deepcopy(ENGINE),
        'product_profile_inventory_digest': INVENTORY, 'product_profile_updates': [], 'cases': cases,
    })


class ResultBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = valid_result()

    def setUp(self):
        self.result = deepcopy(self.template)

    def validate(self, result=None, **changes):
        expected = dict(image_id=IMAGE_ID, files=FILES, revision=REVISION,
                        inventory_digest=INVENTORY, lock=LOCK, recipe_digest=RECIPE, repository_head=HEAD)
        expected.update(changes)
        return conformance.validate_result(self.result if result is None else result, **expected)

    def reject(self, *, reseal=True):
        if reseal:
            seal(self.result)
        with self.assertRaises(release.ReleaseFailure):
            self.validate()

    def test_complete_fixture_receipt_validates_without_product_updates(self):
        self.assertEqual(self.validate(), self.result)
        self.assertEqual(self.result['product_profile_updates'], [])
        self.assertEqual(len(self.result['cases']), len(conformance.CASES))

    def test_missing_negative_case_rejected(self):
        self.result['cases'].pop()
        self.reject()

    def test_duplicate_case_rejected_even_with_expected_total(self):
        self.result['cases'][-1] = deepcopy(self.result['cases'][0])
        self.reject()

    def test_reordered_cases_rejected(self):
        self.result['cases'][0], self.result['cases'][1] = self.result['cases'][1], self.result['cases'][0]
        self.reject()

    def test_extra_case_rejected(self):
        self.result['cases'].append(deepcopy(self.result['cases'][0]))
        self.reject()

    def test_negative_case_cannot_be_replaced_by_valid_completed_execution(self):
        row = self.result['cases'][2]
        row['execution'] = execution(row['execution']['profile'], row['execution']['run_id'], 'completed', None)
        self.reject()

    def test_negative_case_expected_outcome_cannot_be_rewritten_to_pass(self):
        row = self.result['cases'][2]
        row.update(expected_outcome='completed', expected_failure_code=None)
        row['execution'] = execution(row['execution']['profile'], row['execution']['run_id'], 'completed', None)
        self.reject()

    def test_missing_terminal_cannot_be_misreported_as_different_failure(self):
        row = self.result['cases'][3]
        row['execution'] = execution(row['execution']['profile'], row['execution']['run_id'], 'failed', 'exit-nonzero')
        self.reject()

    def test_run_identifier_cannot_be_reused_across_profiles(self):
        row = self.result['cases'][1]
        row['execution'] = execution(row['execution']['profile'], self.result['cases'][0]['execution']['run_id'], 'completed', None)
        self.reject()

    def test_failure_receipt_with_unverified_cleanup_cannot_pass_conformance(self):
        row = self.result['cases'][2]
        row['execution'] = execution(row['execution']['profile'], row['execution']['run_id'], 'unknown', 'cleanup-failed')
        self.reject()

    def test_product_profile_promotion_rejected(self):
        self.result['product_profile_updates'] = [{'id': 'postgres-migration', 'status': 'qualified'}]
        self.reject()

    def test_product_inventory_digest_cannot_be_substituted(self):
        self.result['product_profile_inventory_digest'] = RECIPE
        self.reject()

    def test_wrong_image_binding_rejected(self):
        self.result['artifact']['image_id'] = RECIPE
        self.reject()

    def test_wrong_payload_digest_rejected(self):
        self.result['artifact']['payload_digest'] = RECIPE
        self.reject()

    def test_wrong_base_image_rejected(self):
        self.result['artifact']['runtime_image'] = 'gcr.io/distroless/nodejs22-debian12@' + IMAGE_ID
        self.reject()

    def test_wrong_base_configuration_rejected(self):
        self.result['artifact']['runtime_config_digest'] = RECIPE
        self.reject()

    def test_wrong_recipe_rejected(self):
        self.result['artifact']['recipe_digest'] = IMAGE_ID
        self.reject()

    def test_changed_payload_files_rejected(self):
        self.result['payload_files'][0]['bytes'] += 1
        self.reject()

    def test_changed_runner_rejected(self):
        self.result['runner_digest'] = RECIPE
        self.reject()

    def test_nested_execution_rebound_to_another_image_rejected(self):
        row = self.result['cases'][0]
        profile = deepcopy(row['execution']['profile'])
        profile['artifact']['image_id'] = RECIPE
        row['execution'] = execution(profile, row['execution']['run_id'], 'completed', None)
        self.reject()

    def test_nested_arbitrary_command_cannot_replace_the_fixture(self):
        row = self.result['cases'][0]
        profile = deepcopy(row['execution']['profile'])
        profile['execution']['command'] = ['jobs/unreviewed.cjs']
        row['execution'] = execution(profile, row['execution']['run_id'], 'completed', None)
        self.reject()

    def test_result_digest_detects_unsealed_change(self):
        self.result['completed_at'] = '2026-09-29T20:00:02Z'
        self.reject(reseal=False)

    def test_unknown_top_level_output_rejected(self):
        self.result['raw_stdout'] = SENTINEL
        self.reject()

    def test_unknown_nested_case_output_rejected(self):
        self.result['cases'][0]['stderr'] = SENTINEL
        self.reject()

    def test_every_authority_field_remains_blocked(self):
        for field, value in conformance.BLOCKED.items():
            with self.subTest(field=field):
                self.result = deepcopy(self.template)
                self.result[field] = True if value is False else 'passed'
                self.reject()

    def test_numeric_false_does_not_substitute_for_boolean_authority(self):
        self.result['authorized'] = 0
        self.reject()

    def test_unknown_top_level_scope_rejected(self):
        self.result['scope'] = 'product-task-qualification'
        self.reject()

    def test_unpassed_case_cannot_be_summarized_as_passed(self):
        self.result['cases'][0]['conformance_verdict'] = 'pending'
        self.reject()

    def test_repository_head_must_be_safe_commit_metadata(self):
        self.result['repository_head'] = SENTINEL
        self.reject()

    def test_different_valid_commit_cannot_replace_fresh_expected_head(self):
        self.result['repository_head'] = 'd' * 40
        self.reject()

    def test_timestamps_must_be_safe_and_ordered(self):
        for updates in [{'started_at': SENTINEL}, {'completed_at': '2026-09-29T19:00:00Z'}]:
            with self.subTest(updates=updates):
                self.result = deepcopy(self.template)
                self.result.update(updates)
                self.reject()

    def test_engine_metadata_cannot_contain_raw_diagnostics(self):
        self.result['engine']['stderr'] = SENTINEL
        self.reject()


class PublicCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='finite-cli-')
        self.addCleanup(temporary.cleanup)
        self.scratch = Path(temporary.name)
        self.arguments = ['--source-root', str(ROOT), '--scratch-root', str(self.scratch)]

    def invoke(self, arguments=None, *, error=None):
        stdout, stderr = StringIO(), StringIO()
        result = {'schema': 'test-routing-only/v1', 'verdict': 'passed'}
        with patch.object(conformance, 'run', return_value=result, side_effect=error) as run, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            status = conformance.main(self.arguments if arguments is None else arguments)
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)
        self.assertNotIn(SENTINEL, stdout.getvalue())
        return status, json.loads(stdout.getvalue()), run

    def reject(self, arguments):
        status, result, run = self.invoke(arguments)
        self.assertEqual(status, 1)
        self.assertEqual(result['schema'], 'finite-job-conformance-error/v1')
        self.assertEqual(result['verdict'], 'failed')
        self.assertEqual(set(result), {'schema', 'verdict', 'findings'} | set(conformance.BLOCKED))
        for field, expected in conformance.BLOCKED.items():
            self.assertEqual(result[field], expected)
        run.assert_not_called()

    def test_valid_flags_route_to_fixture_conformance_only(self):
        status, result, run = self.invoke()
        self.assertEqual(status, 0)
        self.assertEqual(result['schema'], 'test-routing-only/v1')
        run.assert_called_once_with(str(ROOT), str(self.scratch))

    def test_nonempty_paths_with_spaces_are_preserved(self):
        arguments = ['--source-root', '/source with spaces', '--scratch-root', '/scratch with spaces']
        status, _, run = self.invoke(arguments)
        self.assertEqual(status, 0)
        run.assert_called_once_with('/source with spaces', '/scratch with spaces')

    def test_empty_source_value_rejected_before_execution(self):
        self.reject(['--source-root', ''] + self.arguments[2:])

    def test_whitespace_source_value_rejected_before_execution(self):
        self.reject(['--source-root', '  '] + self.arguments[2:])

    def test_empty_scratch_value_rejected_before_execution(self):
        self.reject(self.arguments[:2] + ['--scratch-root', ''])

    def test_whitespace_scratch_value_rejected_before_execution(self):
        self.reject(self.arguments[:2] + ['--scratch-root', '  '])

    def test_missing_all_arguments_rejected(self):
        self.reject([])

    def test_missing_source_rejected(self):
        self.reject(self.arguments[2:])

    def test_missing_scratch_rejected(self):
        self.reject(self.arguments[:2])

    def test_missing_flag_value_rejected(self):
        self.reject(self.arguments[:-1])

    def test_duplicate_source_flags_rejected(self):
        self.reject(self.arguments + ['--source-root', SENTINEL])

    def test_duplicate_equals_flags_rejected(self):
        self.reject(self.arguments + ['--scratch-root=' + SENTINEL])

    def test_abbreviated_option_rejected(self):
        self.reject(['--source', SENTINEL] + self.arguments[2:])

    def test_unknown_sensitive_option_is_redacted(self):
        self.reject(self.arguments + ['--credential=' + SENTINEL])

    def test_unknown_positional_is_redacted(self):
        self.reject(self.arguments + [SENTINEL])

    def test_arbitrary_command_is_unavailable(self):
        self.reject(self.arguments + ['--command', SENTINEL])

    def test_arbitrary_image_is_unavailable(self):
        self.reject(self.arguments + ['--image', SENTINEL])

    def test_saved_receipt_cannot_be_admitted(self):
        self.reject(self.arguments + ['--result', SENTINEL])

    def test_saved_profile_cannot_be_executed(self):
        self.reject(self.arguments + ['--profile', SENTINEL])

    def test_legacy_skip_mode_cannot_mix(self):
        self.reject(self.arguments + ['--allow-skip-without-engine'])

    def test_product_qualification_mode_cannot_mix(self):
        self.reject(self.arguments + ['--qualify-local'])

    def test_unexpected_exception_is_redacted(self):
        status, result, run = self.invoke(error=RuntimeError(SENTINEL + '\ntraceback'))
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'finite-job-conformance-failed'}])
        run.assert_called_once()

    def test_untrusted_engine_failure_code_is_redacted(self):
        status, result, _ = self.invoke(error=container_engine.EngineFailure(SENTINEL))
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'finite-job-conformance-failed'}])

    def test_fixed_source_change_failure_is_preserved(self):
        status, result, _ = self.invoke(error=release.ReleaseFailure('finite-job-conformance-source-changed'))
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'finite-job-conformance-source-changed'}])


class ExistingWrapperTests(unittest.TestCase):
    def refuse(self, arguments):
        with tempfile.TemporaryDirectory(prefix='finite-wrapper-') as temporary:
            outside = Path(temporary)
            process = subprocess.run(['/bin/bash', str(WRAPPER), *arguments], cwd=outside,
                                     env={'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
                                          'DOCKER_CONFIG': str(outside / 'uncreated-config')},
                                     capture_output=True, timeout=20, check=False)
            self.assertEqual(process.returncode, 1)
            self.assertEqual(process.stderr, b'')
            self.assertNotIn(SENTINEL.encode(), process.stdout)
            self.assertEqual(len(process.stdout.splitlines()), 1)
            result = json.loads(process.stdout)
            self.assertEqual(result['schema'], 'finite-job-conformance-error/v1')
            for field, expected in conformance.BLOCKED.items():
                self.assertEqual(result[field], expected)
            self.assertFalse((outside / 'uncreated-config').exists())

    def test_actual_wrapper_rejects_missing_arguments_before_legacy_setup(self):
        self.refuse(['--verify-finite-jobs'])

    def test_actual_wrapper_rejects_arbitrary_command_and_image(self):
        self.refuse(['--verify-finite-jobs', '--command', SENTINEL, '--image', SENTINEL])

    def test_actual_wrapper_rejects_sensitive_argument_without_echo(self):
        self.refuse(['--verify-finite-jobs', '--credential=' + SENTINEL])

    def test_actual_wrapper_rejects_duplicate_flags(self):
        self.refuse(['--verify-finite-jobs', '--source-root', SENTINEL, '--source-root=' + SENTINEL])

    def test_actual_wrapper_rejects_mixed_legacy_mode(self):
        self.refuse(['--verify-finite-jobs', '--allow-skip-without-engine'])

    def test_finite_mode_after_legacy_skip_cannot_reach_legacy_setup(self):
        self.refuse(['--allow-skip-without-engine', '--verify-finite-jobs'])

    def test_finite_mode_after_sensitive_legacy_value_is_redacted(self):
        self.refuse(['--tag', SENTINEL, '--verify-finite-jobs'])

    def test_finite_mode_cannot_mix_with_product_mode(self):
        self.refuse(['--qualify-local', '--verify-finite-jobs'])

    def test_finite_equals_variant_is_rejected_without_echo(self):
        self.refuse(['--verify-finite-jobs=' + SENTINEL])


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='finite-orchestration-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'source'
        self.root.mkdir()
        self.scratch = Path(temporary.name) / 'scratch'
        self.scratch.mkdir()
        self.source = {conformance.FIXTURES + 'Dockerfile': b'FROM scratch\n',
                       conformance.FIXTURES + 'jobs/task.cjs': b'fixture'}
        self.calls = 0
        self.executor = MagicMock()
        self.executor.version.return_value = deepcopy(ENGINE)
        self.executor.build_job_fixture.return_value = IMAGE_ID
        self.executor.run_job.side_effect = self.observe
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.snapshots = self.stack.enter_context(patch.object(conformance, 'snapshot', return_value=(self.source, REVISION)))
        self.stack.enter_context(patch.object(conformance.local_container, 'checked_scratch', return_value=self.scratch))
        self.lock = self.stack.enter_context(patch.object(conformance.local_container, 'load_lock', return_value=deepcopy(LOCK)))
        self.head = self.stack.enter_context(patch.object(conformance.local_container, 'repository_head', return_value=HEAD))
        self.profiles = self.stack.enter_context(patch.object(conformance.container_profiles, 'discover', return_value=deepcopy(PROFILES)))
        self.base = self.stack.enter_context(patch.object(conformance.local_container, 'check_base'))
        self.engine = self.stack.enter_context(patch.object(conformance.container_engine, 'Engine', return_value=self.executor))

    def observe(self, profile, files):
        self.calls += 1
        case = profile['execution']['command'][1]
        expected = next((outcome, code) for name, outcome, code in conformance.CASES if name == case)
        self.assertEqual(files, FILES)
        return execution(profile, format(self.calls, '032x'), *expected)

    def run_fixture(self):
        return conformance.run(self.root, self.scratch)

    def test_fresh_fixture_build_runs_all_cases_and_does_not_promote_product_profiles(self):
        result = self.run_fixture()
        self.assertEqual(result['verdict'], 'passed')
        self.assertEqual([row['case'] for row in result['cases']], [row[0] for row in conformance.CASES])
        self.assertEqual(result['product_profile_updates'], [])
        self.executor.build_job_fixture.assert_called_once()
        self.executor.run_server.assert_not_called()
        self.executor.build.assert_not_called()
        self.base.assert_called_once()
        self.assertFalse(any(self.scratch.iterdir()), 'Owned fixture context must be removed')

    def reject_source_change(self):
        # Source revalidation happens after execution regardless of case count.
        # One genuine contract-bound execution isolates this boundary cheaply;
        # the positive orchestration test above exercises the complete matrix.
        with patch.object(conformance, 'CASES', conformance.CASES[:1]), \
                self.assertRaisesRegex(release.ReleaseFailure, 'source-changed'):
            self.run_fixture()

    def test_source_change_during_run_rejected(self):
        self.snapshots.side_effect = [(self.source, REVISION), (self.source, RECIPE)]
        self.reject_source_change()

    def test_product_inventory_change_during_run_rejected(self):
        self.profiles.side_effect = [deepcopy(PROFILES), []]
        self.reject_source_change()

    def test_repository_head_change_during_run_rejected(self):
        self.head.side_effect = [HEAD, 'd' * 40]
        self.reject_source_change()

    def test_base_lock_change_during_run_rejected(self):
        self.lock.side_effect = [deepcopy(LOCK), {**LOCK, 'runtime_config_digest': IMAGE_ID}]
        self.reject_source_change()

    def test_context_change_during_execution_rejected(self):
        observe = self.observe
        def changed(profile, files):
            result = observe(profile, files)
            next(self.scratch.glob('finite-job-conformance-*/context/jobs/task.cjs')).write_bytes(b'changed')
            return result
        self.executor.run_job.side_effect = changed
        self.reject_source_change()

    def test_unexpected_success_of_negative_fixture_fails_entire_run(self):
        def all_complete(profile, files):
            self.calls += 1
            return execution(profile, format(self.calls, '032x'), 'completed', None)
        self.executor.run_job.side_effect = all_complete
        with self.assertRaisesRegex(release.ReleaseFailure, 'case-execution-invalid'):
            self.run_fixture()
        self.assertEqual(self.calls, 3)

    def test_failed_cleanup_cannot_be_accepted_as_expected_negative_behavior(self):
        self.executor.run_job.side_effect = lambda profile, files: execution(profile, '1' * 32, 'unknown', 'cleanup-failed')
        with self.assertRaisesRegex(release.ReleaseFailure, 'case-execution-invalid'):
            self.run_fixture()
        self.assertEqual(self.executor.run_job.call_count, 1)

    def test_unavailable_engine_prevents_build_and_execution(self):
        self.executor.version.side_effect = container_engine.EngineFailure('engine-unavailable')
        with self.assertRaises(container_engine.EngineFailure):
            self.run_fixture()
        self.executor.build_job_fixture.assert_not_called()
        self.executor.run_job.assert_not_called()

    def test_base_mismatch_prevents_build_and_execution(self):
        self.base.side_effect = container_engine.EngineFailure('local-container-base-binding-invalid')
        with self.assertRaises(container_engine.EngineFailure):
            self.run_fixture()
        self.executor.build_job_fixture.assert_not_called()
        self.executor.run_job.assert_not_called()


class SnapshotBindingTests(unittest.TestCase):
    HELPERS = ('scripts/04.deploy/operational-realization-gate/finite_job_conformance.py',
               'scripts/04.deploy/operational-realization-gate/finite_job_contracts.py')
    SCHEMAS = ('infra/04.deploy/contracts/release-control/v1/finite-job-profile.schema.yml',
               'infra/04.deploy/contracts/release-control/v1/finite-job-result.schema.yml')

    def snapshot(self, changed=None):
        executing = {
            (conformance.DIRECTORY, 'finite_job_conformance.py'): self.HELPERS[0],
            (Path(contracts.__file__).resolve().parent, 'finite_job_contracts.py'): self.HELPERS[1],
            (contracts.build_contracts.SCHEMA_DIR, 'finite-job-profile.schema.yml'): self.SCHEMAS[0],
            (contracts.build_contracts.SCHEMA_DIR, 'finite-job-result.schema.yml'): self.SCHEMAS[1],
        }
        def read(root, path):
            if root != ROOT:
                self.assertIn((root, path), executing)
                path = executing[(root, path)]
            # This helper models a reviewed schema change in both the source
            # tree and the implementation being executed; neither is stale.
            return (path + (' changed' if path == changed else '')).encode('utf-8')
        with patch.object(conformance.local_container, 'read', side_effect=read), \
                patch.object(conformance.local_container, 'implementation_digest', return_value=REVISION):
            return conformance.snapshot(ROOT)

    def alternate_root(self):
        temporary = tempfile.TemporaryDirectory(prefix='finite-source-identity-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'source'
        root.mkdir()
        for relative in (*self.HELPERS, *self.SCHEMAS, conformance.FIXTURES + 'Dockerfile',
                         conformance.FIXTURES + 'jobs/task.cjs'):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        return root

    def reject_mismatched_source(self, relative):
        root = self.alternate_root()
        target = root / relative
        target.write_bytes(target.read_bytes() + b'\nchanged source bytes\n')
        scratch = root.parent / 'scratch'
        scratch.mkdir()
        with patch.object(conformance.local_container, 'checked_scratch', return_value=scratch), \
                patch.object(conformance.local_container, 'load_lock') as lock, \
                patch.object(conformance.container_engine, 'Engine') as engine, \
                self.assertRaisesRegex(release.ReleaseFailure, 'finite-job-conformance-source-changed'):
            conformance.run(root, scratch)
        lock.assert_not_called()
        engine.assert_not_called()
        self.assertFalse(any(scratch.iterdir()))

    def test_both_finite_schemas_are_in_the_source_snapshot(self):
        files, revision = self.snapshot()
        for path in self.SCHEMAS:
            with self.subTest(path=path):
                self.assertIn(path, files)
                self.assertEqual(files[path], path.encode('utf-8'))
        self.assertEqual((files, revision), self.snapshot())

    def test_profile_schema_change_changes_runner_binding(self):
        _, original = self.snapshot()
        files, changed = self.snapshot(self.SCHEMAS[0])
        self.assertNotEqual(original, changed)
        self.assertEqual(files[self.SCHEMAS[0]], (self.SCHEMAS[0] + ' changed').encode('utf-8'))

    def test_result_schema_change_changes_runner_binding(self):
        _, original = self.snapshot()
        files, changed = self.snapshot(self.SCHEMAS[1])
        self.assertNotEqual(original, changed)
        self.assertEqual(files[self.SCHEMAS[1]], (self.SCHEMAS[1] + ' changed').encode('utf-8'))

    def test_different_conformance_source_is_rejected_before_any_engine_build(self):
        self.reject_mismatched_source(self.HELPERS[0])

    def test_different_contract_source_is_rejected_before_any_engine_build(self):
        self.reject_mismatched_source(self.HELPERS[1])

    def test_different_profile_schema_is_rejected_before_any_engine_build(self):
        self.reject_mismatched_source(self.SCHEMAS[0])

    def test_different_result_schema_is_rejected_before_any_engine_build(self):
        self.reject_mismatched_source(self.SCHEMAS[1])

    def test_identical_alternate_root_copy_has_the_same_snapshot(self):
        root = self.alternate_root()
        with patch.object(conformance.local_container, 'implementation_digest', return_value=REVISION):
            original = conformance.snapshot(ROOT)
            copied = conformance.snapshot(root)
        self.assertEqual(copied, original)



class ConsumerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = valid_result()

    def test_conformance_is_rejected_for_every_common_consumer_purpose(self):
        for purpose in sorted(result_consumption.PURPOSES):
            with self.subTest(purpose=purpose):
                result = result_consumption.consume_result(self.receipt, purpose, self.receipt)
                self.assertEqual(result['verdict'], 'rejected')
                self.assertIs(result['authorized'], False)
                self.assertEqual(result['release_eligibility'], 'blocked')
                self.assertEqual(result['operation_authorization'], 'blocked')

    def test_finite_execution_is_rejected_for_every_common_consumer_purpose(self):
        receipt = self.receipt['cases'][0]['execution']
        for purpose in sorted(result_consumption.PURPOSES):
            with self.subTest(purpose=purpose):
                result = result_consumption.consume_result(receipt, purpose, receipt)
                self.assertEqual(result['verdict'], 'rejected')
                self.assertIs(result['authorized'], False)
                self.assertEqual(result['release_eligibility'], 'blocked')
                self.assertEqual(result['operation_authorization'], 'blocked')


if __name__ == '__main__':
    unittest.main()

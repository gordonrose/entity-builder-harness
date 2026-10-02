"""Check public qualification routing, safe failures and unavailable authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.local-container-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject ambiguous public qualification requests and prevent local container evidence from granting authority.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import container_engine
import local_container
import local_container_contracts as contracts
import locked_toolchain
import release_compiler as release
import result_consumption

ROOT = DIRECTORY.parents[2]
SENTINEL = 'SENSITIVE_CLI_SENTINEL'
DIGEST = 'sha256:' + 'a' * 64
IMAGE = 'gcr.io/distroless/nodejs22-debian12@' + DIGEST
LOCK = {
    'schema': 'local-container-lock/v1', 'platform': 'linux/amd64',
    'runtime_image': IMAGE, 'runtime_config_digest': DIGEST,
    'recipe_path': 'infra/04.deploy/03.product/image/Dockerfile', 'recipe_digest': DIGEST,
}
BASE = {'image_id': DIGEST, 'repo_digests': [IMAGE], 'os': 'linux', 'architecture': 'amd64'}


class PublicCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='local-container-cli-')
        self.addCleanup(temporary.cleanup)
        self.scratch = Path(temporary.name)
        self.arguments = ['--source-root', str(ROOT), '--scratch-root', str(self.scratch),
                          '--package-cache', str(self.scratch / 'verified-cache')]

    def invoke(self, arguments=None, *, error=None):
        stdout, stderr = StringIO(), StringIO()
        result = {'schema': 'test-routing-only/v1', 'verdict': 'passed'}
        with patch.object(local_container, 'checked_scratch', return_value=self.scratch), \
                patch.object(local_container, 'run', return_value=result, side_effect=error) as run, \
                patch.object(local_container.container_engine, 'Engine') as engine, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            status = local_container.main(self.arguments if arguments is None else arguments)
        self.assertEqual(stderr.getvalue(), '')
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 1, 'Public result must be one complete JSON document')
        self.assertNotIn(SENTINEL, stdout.getvalue())
        return status, json.loads(lines[0]), run, engine

    def reject(self, arguments):
        status, result, run, engine = self.invoke(arguments)
        self.assertEqual(status, 1)
        self.assertEqual(result['schema'], 'local-container-error/v1')
        self.assertEqual(result['verdict'], 'failed')
        self.assertIs(result['authorized'], False)
        self.assertEqual(result['release_eligibility'], 'blocked')
        self.assertEqual(result['operation_authorization'], 'blocked')
        self.assertNotIn('image', result)
        self.assertNotIn('runtime', result)
        run.assert_not_called()
        engine.assert_not_called()

    def test_package_cache_routes_only_to_local_execution(self):
        status, result, run, engine = self.invoke()
        self.assertEqual(status, 0)
        self.assertEqual(result['schema'], 'test-routing-only/v1')
        run.assert_called_once_with(ROOT, str(self.scratch / 'verified-cache'), self.scratch)
        engine.assert_not_called()

    def test_missing_all_arguments_rejected_before_execution(self):
        self.reject([])

    def test_missing_cache_or_acquisition_mode_rejected(self):
        self.reject(self.arguments[:-2])

    def test_acquisition_and_execution_modes_cannot_mix(self):
        self.reject(self.arguments + ['--acquire-base'])

    def test_missing_source_rejected(self):
        self.reject(self.arguments[2:])

    def test_missing_scratch_rejected(self):
        self.reject(self.arguments[:2] + self.arguments[4:])

    def test_missing_flag_value_rejected(self):
        self.reject(self.arguments[:-1])

    def test_empty_cache_rejected(self):
        self.reject(self.arguments[:-1] + [''])

    def test_duplicate_flags_rejected(self):
        self.reject(self.arguments + ['--source-root', SENTINEL])

    def test_duplicate_equals_flags_rejected(self):
        self.reject(self.arguments + ['--source-root=' + SENTINEL])

    def test_duplicate_boolean_flag_rejected(self):
        self.reject(self.arguments[:-2] + ['--acquire-base', '--acquire-base'])

    def test_abbreviated_option_rejected(self):
        self.reject(['--source', str(ROOT)] + self.arguments[2:])

    def test_unsafe_unknown_option_is_not_echoed(self):
        self.reject(self.arguments + ['--credential=' + SENTINEL])

    def test_unknown_positional_value_is_not_echoed(self):
        self.reject(self.arguments + [SENTINEL])

    def test_legacy_skip_flag_is_not_qualification_success(self):
        self.reject(self.arguments + ['--allow-skip-without-engine'])

    def test_legacy_image_override_cannot_change_qualification_recipe(self):
        self.reject(self.arguments + ['--runtime-image', SENTINEL])

    def test_source_path_failure_is_redacted(self):
        self.reject(['--source-root', str(self.scratch / SENTINEL)] + self.arguments[2:])

    def test_unexpected_exception_has_no_partial_success_or_raw_diagnostic(self):
        status, result, run, engine = self.invoke(error=RuntimeError(SENTINEL + '\ntraceback detail'))
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'local-container-verification-failed'}])
        self.assertEqual(set(result), {'schema', 'verdict', 'authorized', 'release_eligibility',
                                     'operation_authorization', 'findings'})
        run.assert_called_once()
        engine.assert_not_called()

    def test_expected_closed_failure_preserves_fixed_reason(self):
        status, result, _, _ = self.invoke(error=container_engine.EngineFailure('local-container-source-changed'))
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'local-container-source-changed'}])

    def test_locked_toolchain_failures_preserve_fixed_reason_without_authority(self):
        for reason in ('command-failed', 'execution-failed', 'cache-lock-mismatch'):
            code = 'locked-toolchain-' + reason
            with self.subTest(reason=reason):
                status, result, run, engine = self.invoke(error=locked_toolchain.ToolchainFailure(code))
                self.assertEqual(status, 1)
                self.assertEqual(result['findings'], [{'code': code}])
                self.assertIs(result['authorized'], False)
                self.assertEqual(result['release_eligibility'], 'blocked')
                self.assertEqual(result['operation_authorization'], 'blocked')
                run.assert_called_once()
                engine.assert_not_called()

    def test_publication_failure_preserves_fixed_reason_and_redacts_unsafe_text(self):
        fixed = release.ReleaseFailure('qualified-publication-image-binding-invalid')
        status, result, _, _ = self.invoke(error=fixed)
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'qualified-publication-image-binding-invalid'}])
        self.assertIs(result['authorized'], False)
        for unsafe in ('qualified-publication-' + SENTINEL,
                       'qualified-publication-image-binding-invalid\n' + SENTINEL):
            with self.subTest(unsafe=unsafe):
                _, result, _, _ = self.invoke(error=release.ReleaseFailure(unsafe))
                self.assertEqual(result['findings'], [{'code': 'local-container-verification-failed'}])

    def test_locked_toolchain_unsafe_and_malformed_failures_are_redacted(self):
        malformed = locked_toolchain.ToolchainFailure(SENTINEL)
        malformed.code = {'raw': SENTINEL}
        errors = [locked_toolchain.ToolchainFailure('locked-toolchain-' + SENTINEL),
                  locked_toolchain.ToolchainFailure('locked-toolchain-command-failed\n' + SENTINEL),
                  locked_toolchain.ToolchainFailure('locked-toolchain-command-failed /' + SENTINEL),
                  malformed]
        for index, error in enumerate(errors):
            with self.subTest(case=index):
                status, result, _, _ = self.invoke(error=error)
                self.assertEqual(status, 1)
                self.assertEqual(result['findings'], [{'code': 'local-container-verification-failed'}])

    def test_malformed_error_code_is_redacted(self):
        error = RuntimeError(SENTINEL)
        error.code = {'raw': SENTINEL}
        status, result, _, _ = self.invoke(error=error)
        self.assertEqual(status, 1)
        self.assertEqual(result['findings'], [{'code': 'local-container-verification-failed'}])

    def test_acquire_mode_is_separate_and_reports_no_runtime_success(self):
        stdout, stderr = StringIO(), StringIO()
        with patch.object(local_container, 'checked_scratch', return_value=self.scratch), \
                patch.object(local_container, 'load_lock', return_value=deepcopy(LOCK)), \
                patch.object(local_container, 'run') as run, \
                patch.object(local_container.container_engine, 'Engine') as engine, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            engine.return_value.acquire.return_value = deepcopy(BASE)
            status = local_container.main(self.arguments[:-2] + ['--acquire-base'])
        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), '')
        result = json.loads(stdout.getvalue())
        self.assertEqual(result, {'schema': 'local-container-acquisition/v1', 'verdict': 'verified',
                                 'authorized': False, 'runtime_image': IMAGE, 'image_id': DIGEST})
        run.assert_not_called()
        engine.return_value.acquire.assert_called_once_with(IMAGE)
        engine.return_value.run_server.assert_not_called()
        engine.return_value.build.assert_not_called()

    def test_acquired_wrong_base_cannot_be_reported_verified(self):
        stdout, stderr = StringIO(), StringIO()
        with patch.object(local_container, 'checked_scratch', return_value=self.scratch), \
                patch.object(local_container, 'load_lock', return_value=deepcopy(LOCK)), \
                patch.object(local_container.container_engine, 'Engine') as engine, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            engine.return_value.acquire.return_value = {**BASE, 'image_id': 'sha256:' + 'b' * 64}
            status = local_container.main(self.arguments[:-2] + ['--acquire-base'])
        self.assertEqual(status, 1)
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(json.loads(stdout.getvalue())['findings'], [{'code': 'local-container-base-binding-invalid'}])


class ExistingWrapperTests(unittest.TestCase):
    """Invoke the actual wrappers only with requests rejected before any engine call."""

    def exercise(self, tail, *, qualify_first=True):
        with tempfile.TemporaryDirectory(prefix='qualification-wrapper-') as temporary:
            outside = Path(temporary)
            for wrapper in local_container.WRAPPERS:
                with self.subTest(wrapper=wrapper):
                    # Running outside a Git checkout proves qualification routing
                    # occurs before legacy git discovery or Docker setup.
                    arguments = (['--qualify-local'] if qualify_first else []) + tail
                    result = subprocess.run(['/bin/bash', str(ROOT / wrapper), *arguments],
                                            cwd=outside, env={'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
                                                             'DOCKER_CONFIG': str(outside / 'uncreated-config')},
                                            capture_output=True, timeout=20, check=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stderr, b'')
                    self.assertNotIn(SENTINEL.encode(), result.stdout)
                    document = json.loads(result.stdout)
                    self.assertEqual(document['schema'], 'local-container-error/v1')
                    self.assertEqual(document['verdict'], 'failed')
                    self.assertIs(document['authorized'], False)
                    self.assertFalse((outside / 'uncreated-config').exists())

    def test_both_existing_wrappers_reject_missing_qualification_arguments(self):
        self.exercise([])

    def test_both_existing_wrappers_reject_mixed_legacy_flags(self):
        self.exercise(['--allow-skip-without-engine', '--runtime-image', SENTINEL])

    def test_both_existing_wrappers_reject_unsafe_unknown_arguments(self):
        self.exercise(['--credential=' + SENTINEL])

    def test_both_existing_wrappers_reject_duplicate_flags(self):
        self.exercise(['--source-root', SENTINEL, '--source-root=' + SENTINEL])

    def test_qualification_after_skip_cannot_enter_legacy_skip_route(self):
        self.exercise(['--allow-skip-without-engine', '--qualify-local'], qualify_first=False)

    def test_qualification_after_unsafe_unknown_flag_is_redacted(self):
        self.exercise(['--credential=' + SENTINEL, '--qualify-local'], qualify_first=False)

    def test_qualification_after_legacy_option_value_is_rejected_without_mutation(self):
        self.exercise(['--tag', SENTINEL, '--qualify-local'], qualify_first=False)

    def test_qualification_equals_variant_is_rejected_without_echo(self):
        self.exercise(['--qualify-local=' + SENTINEL], qualify_first=False)


class AuthorityAndBoundsTests(unittest.TestCase):
    def setUp(self):
        self.local_result = {'schema': 'local-container-result/v1', 'scope': 'selected-local-container',
                             'verdict': 'passed', 'authorized': False,
                             'release_eligibility': 'blocked', 'operation_authorization': 'blocked'}
        path = release.SCHEMA_DIR / 'local-container-result.schema.yml'
        self.schema = release.load_document(path)

    def test_local_container_result_is_not_a_source_analysis_producer(self):
        decision = result_consumption.consume_result(self.local_result, 'source-analysis', self.local_result)
        self.assertEqual(decision['verdict'], 'rejected')
        self.assertEqual(decision['findings'], [{'code': 'source-result-producer-unsupported'}])

    def test_local_container_cannot_grant_release_eligibility(self):
        decision = result_consumption.consume_result(self.local_result, 'release-eligibility', self.local_result)
        self.assertEqual(decision['verdict'], 'rejected')
        self.assertIs(decision['authorized'], False)
        self.assertEqual(decision['release_eligibility'], 'blocked')
        self.assertEqual(decision['findings'], [{'code': 'source-result-authority-unavailable'}])

    def test_local_container_cannot_grant_operation_authorization(self):
        decision = result_consumption.consume_result(self.local_result, 'operation-authorization', self.local_result)
        self.assertEqual(decision['verdict'], 'rejected')
        self.assertIs(decision['authorized'], False)
        self.assertEqual(decision['operation_authorization'], 'blocked')
        self.assertEqual(decision['findings'], [{'code': 'source-result-authority-unavailable'}])

    def test_local_container_cannot_invent_a_deployment_purpose(self):
        decision = result_consumption.consume_result(self.local_result, 'deploy-now', self.local_result)
        self.assertEqual(decision['verdict'], 'rejected')
        self.assertIs(decision['authorized'], False)

    def test_lock_requires_immutable_reviewed_registry_image(self):
        contracts.validate_lock(deepcopy(LOCK))
        for reference in ['gcr.io/distroless/nodejs22-debian12:latest',
                          'private.invalid/image@' + DIGEST, 'SENSITIVE_CLI_SENTINEL']:
            with self.subTest(reference=reference), self.assertRaises(release.ReleaseFailure):
                contracts.validate_lock({**LOCK, 'runtime_image': reference})

    def test_lock_rejects_other_architecture_or_recipe(self):
        for change in [{'platform': 'linux/arm64'}, {'recipe_path': '../Dockerfile'},
                       {'recipe_path': 'other/Dockerfile'}, {'credentials': SENTINEL}]:
            with self.subTest(change=change), self.assertRaises(release.ReleaseFailure):
                contracts.validate_lock({**LOCK, **change})

    def test_actual_runtime_settings_fit_closed_result_schema(self):
        validator = Draft202012Validator(self.schema['properties']['runtime']['properties']['settings'])
        self.assertTrue(validator.is_valid(deepcopy(container_engine.SETTINGS)))
        for change in [{'network': 'host'}, {'host_mounts': ['/home/owner']}, {'published_ports': [3000]},
                       {'read_only': False}, {'user': 'root'}, {'no_new_privileges': False},
                       {'credentials': SENTINEL}]:
            with self.subTest(change=change):
                self.assertFalse(validator.is_valid({**container_engine.SETTINGS, **change}))

    def test_skipped_or_missing_health_checks_cannot_fit_success_schema(self):
        validator = Draft202012Validator(self.schema['properties']['runtime']['properties']['checks'])
        checks = [{'path': '/livez', 'status': 200, 'body_status': 'live'},
                  {'path': '/readyz', 'status': 200, 'body_status': 'ready'}]
        self.assertTrue(validator.is_valid(checks))
        self.assertFalse(validator.is_valid([]))
        self.assertFalse(validator.is_valid(checks[:1]))
        self.assertFalse(validator.is_valid([{'status': 'skipped'}]))

    def test_result_schema_enforces_resource_bounds_and_closed_objects(self):
        pending = [self.schema]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                self.assertFalse(any(key in value for key in ('$ref', '$dynamicRef', '$recursiveRef')))
                if value.get('type') == 'object':
                    self.assertIs(value.get('additionalProperties'), False)
                    self.assertEqual(set(value.get('properties', {})), set(value.get('required', [])))
                if value.get('type') == 'array':
                    self.assertIsInstance(value.get('maxItems'), int)
                    self.assertLessEqual(value['maxItems'], 50000)
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)

    def test_impossible_success_authority_flags_are_schema_invalid(self):
        for key in ['release_eligibility', 'operation_authorization', 'qualification_verdict', 'source_closure']:
            with self.subTest(field=key):
                validator = Draft202012Validator(self.schema['properties'][key])
                self.assertTrue(validator.is_valid('blocked'))
                self.assertFalse(validator.is_valid('passed'))
        self.assertFalse(Draft202012Validator(self.schema['properties']['authorized']).is_valid(True))


if __name__ == '__main__':
    unittest.main()

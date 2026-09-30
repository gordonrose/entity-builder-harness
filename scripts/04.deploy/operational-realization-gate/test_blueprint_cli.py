#!/usr/bin/env python3
"""Exercise the selected blueprint public boundary without provider execution."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-blueprint-cli-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify source blueprint CLI strictness and safe failure output against real selected source fixtures.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import blueprint_cli as cli

ROOT = Path(__file__).resolve().parents[3]
BLUEPRINT = ROOT / 'infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml'
REVISION = 'a' * 40
IMAGE = 'sha256:' + 'b' * 64
SENTINEL = 'PRIVATE_SENTINEL_MUST_NOT_ESCAPE'


class BlueprintCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = cli.load_compiler()
        cls.document = cls.compiler.release.load_document(BLUEPRINT)
        cls.result = cls.compiler.compile_blueprint(ROOT, cls.document, REVISION, IMAGE, 'staging-cli-review')

    def argv(self):
        return ['--blueprint', str(BLUEPRINT), '--source-root', str(ROOT),
                '--source-revision', REVISION, '--image-digest', IMAGE,
                '--release-id', 'staging-cli-review', '--json']

    def invoke(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(argv)
        self.assertEqual('', stderr.getvalue())
        self.assertNotIn(SENTINEL, stdout.getvalue())
        self.assertNotIn('Traceback', stdout.getvalue())
        return status, json.loads(stdout.getvalue())

    def assert_failure(self, argv, code=None):
        status, result = self.invoke(argv)
        self.assertEqual(1, status)
        self.assertEqual(cli.ERROR_SCHEMA, result['schema'])
        self.assertEqual({'schema', 'scope', 'verdict', 'authorized', 'release_eligibility',
                          'operation_authorization', 'qualification_verdict', 'findings'}, set(result))
        self.assertIs(result['authorized'], False)
        self.assertEqual('failed', result['verdict'])
        for name in ('release_eligibility', 'operation_authorization', 'qualification_verdict'):
            self.assertEqual('blocked', result[name])
        if code is not None:
            self.assertEqual([{'code': code}], result['findings'])

    def test_real_selected_source_compiles_and_stays_unauthorized(self):
        status, result = self.invoke(self.argv())
        self.assertEqual(0, status)
        self.assertEqual(self.result, result)
        self.assertEqual(13, len(result['operation_projection']))
        self.assertEqual(9, len({row['execution_group_digest'] for row in result['operation_projection']}))
        self.assertEqual(17, len(result['compiled_release']['acceptance_matrix']))
        self.assertIs(result['authorized'], False)
        self.assertEqual('blocked', result['operation_authorization'])

    def test_json_flag_does_not_change_output(self):
        self.assertEqual(self.invoke(self.argv()), self.invoke(self.argv()[:-1]))

    def test_duplicate_abbreviated_missing_and_mixed_modes_reject_before_loading(self):
        variants = [self.argv() + ['--release-id', SENTINEL],
                    self.argv() + ['--release-id=' + SENTINEL],
                    self.argv() + ['--json'],
                    self.argv()[2:],
                    [item.replace('--source-revision', '--source-rev') for item in self.argv()],
                    self.argv() + ['--release', SENTINEL],
                    self.argv() + ['--finite-recovery-conformance'],
                    self.argv() + ['--through', SENTINEL],
                    self.argv() + [SENTINEL], self.argv() + ['--help']]
        with patch.object(cli, 'load_compiler') as load:
            for argv in variants:
                with self.subTest(argv=argv):
                    self.assert_failure(argv, 'arguments-invalid')
            load.assert_not_called()

    def test_unreadable_blueprint_redacts_path(self):
        argv = self.argv()
        argv[1] = '/missing/' + SENTINEL
        self.assert_failure(argv, 'blueprint-unreadable')

    def test_duplicate_key_and_yaml_alias_reject_without_compilation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'input.yml'
            for raw in ('schema: one\nschema: two\n', 'schema: &anchor one\nid: *anchor\n'):
                path.write_text(raw + 'private: ' + SENTINEL + '\n')
                argv = self.argv(); argv[1] = str(path)
                with patch.object(self.compiler, 'compile_blueprint') as compile_blueprint:
                    self.assert_failure(argv)
                    compile_blueprint.assert_not_called()

    def test_oversized_blueprint_is_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'input.yml'
            path.write_text('x' * (self.compiler.release.MAX_BYTES + 1))
            argv = self.argv(); argv[1] = str(path)
            self.assert_failure(argv, 'document-limit-exceeded')

    def test_input_schema_rejects_extra_nested_field_wrong_target_and_unsafe_path(self):
        changes = [lambda value: value.update(secret=SENTINEL),
                   lambda value: value['operations'][0].update(raw=SENTINEL),
                   lambda value: value.update(target_id='other/staging'),
                   lambda value: value.update(realization_contract='../' + SENTINEL),
                   lambda value: value['operations'][0].update(source_profile='name/' + SENTINEL)]
        for change in changes:
            value = deepcopy(self.document); change(value)
            with self.subTest(change=change):
                with self.assertRaises(self.compiler.release.ReleaseFailure):
                    self.compiler.validate_blueprint(value)

    def test_missing_schema_is_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(self.compiler.release, 'SCHEMA_DIR', Path(temporary)):
                self.assert_failure(self.argv(), 'blueprint-schema-unreadable')

    def test_corrupt_schema_is_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / self.compiler.SCHEMA_FILE
            path.write_text('private: [' + SENTINEL)
            with patch.object(self.compiler.release, 'SCHEMA_DIR', Path(temporary)):
                self.assert_failure(self.argv(), 'blueprint-schema-unreadable')

    def test_compiler_import_failure_is_safe(self):
        with patch.object(cli, 'load_compiler', side_effect=cli.CliFailure('blueprint-dependency-unavailable')):
            self.assert_failure(self.argv(), 'blueprint-dependency-unavailable')

    def test_unexpected_failure_and_unrecognized_error_code_are_redacted(self):
        errors = [RuntimeError(SENTINEL), self.compiler.release.ReleaseFailure(SENTINEL),
                  self.compiler.release.ReleaseFailure([SENTINEL])]
        for error in errors:
            with patch.object(self.compiler, 'compile_blueprint', side_effect=error):
                self.assert_failure(self.argv(), 'blueprint-compilation-failed')

    def test_result_authority_extra_fields_and_self_digest_tamper_reject(self):
        def add_nested(value):
            value['operation_projection'][0]['raw'] = SENTINEL
        changes = [lambda value: value.update(authorized=True),
                   lambda value: value.update(raw=SENTINEL), add_nested,
                   lambda value: value['operation_projection'][0].update(execution_group_digest=SENTINEL),
                   lambda value: value.update(result_digest='sha256:' + 'f' * 64)]
        for index, change in enumerate(changes):
            value = deepcopy(self.result); change(value)
            if index < len(changes) - 1:
                value['result_digest'] = self.compiler.release.digest_document({key: row for key, row in value.items() if key != 'result_digest'})
            with patch.object(self.compiler, 'compile_blueprint', return_value=value):
                self.assert_failure(self.argv(), 'blueprint-result-invalid')

    def test_invalid_declared_identity_fields_fail_without_echo(self):
        for flag in ('--source-revision', '--image-digest', '--release-id'):
            argv = self.argv(); argv[argv.index(flag) + 1] = SENTINEL
            self.assert_failure(argv, 'blueprint-release-binding-invalid')


if __name__ == '__main__':
    unittest.main()

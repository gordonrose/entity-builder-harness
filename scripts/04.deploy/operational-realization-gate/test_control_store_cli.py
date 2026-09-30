"""Public local-store boundary: closed output, bad input, drift and authority refusal."""
import builtins
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import build_contracts
import control_store_cli as cli
import control_store_conformance as runner
import operation_journal as contracts
import result_consumption


class ControlStoreCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(__file__).resolve().parents[3]
        command = ['bash', 'scripts/04.deploy/operational-realization-gate/script.sh',
                   '--control-store-conformance', '--scratch-root', cls.temp.name]
        cls.execution = subprocess.run(command, cwd=cls.root, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, timeout=60)
        cls.result = json.loads(cls.execution.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def call(self, argv=None):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = cli.main(argv if argv is not None else [
                '--control-store-conformance', '--scratch-root', self.temp.name])
        self.assertEqual('', errors.getvalue())
        result = json.loads(output.getvalue())
        self.assertNotIn('PRIVATE-CANARY', output.getvalue())
        return status, result

    def rejected(self, argv=None, code=None):
        status, result = self.call(argv)
        self.assertEqual(1, status)
        build_contracts.validate_schema('control-store-error', result)
        self.assertIs(result['authorized'], False)
        if code:
            self.assertEqual([{'code': code}], result['findings'])
        return result

    def test_existing_wrapper_runs_real_conformance(self):
        self.assertEqual(0, self.execution.returncode)
        self.assertEqual(b'', self.execution.stderr)
        contracts.validate('control-store-conformance', self.result)
        self.assertEqual(10, len(self.result['cases']))
        self.assertEqual(3, sum(row['processes_killed'] for row in self.result['cases']))
        self.assertEqual(7, sum(row['subprocesses'] for row in self.result['cases']))
        self.assertNotIn(self.temp.name.encode(), self.execution.stdout)

    def test_missing_scratch_root(self):
        self.rejected(['--control-store-conformance'], 'input-invalid')

    def test_duplicate_mode(self):
        self.rejected(['--control-store-conformance', '--control-store-conformance',
                       '--scratch-root', self.temp.name], 'input-invalid')

    def test_duplicate_root_equals_form(self):
        self.rejected(['--control-store-conformance', '--scratch-root='+self.temp.name,
                       '--scratch-root=PRIVATE-CANARY'], 'input-invalid')

    def test_abbreviated_mode_is_refused(self):
        self.rejected(['--control-store-conf', '--scratch-root', self.temp.name], 'input-invalid')

    def test_arbitrary_command_is_refused_before_execution(self):
        with mock.patch.object(runner, 'conformance') as execute:
            self.rejected(['--control-store-conformance', '--scratch-root', self.temp.name,
                           '--command', 'PRIVATE-CANARY'], 'input-invalid')
            execute.assert_not_called()

    def test_other_modes_cannot_mix(self):
        self.rejected(['--control-store-conformance', '--scratch-root', self.temp.name,
                       '--release', 'PRIVATE-CANARY'], 'input-invalid')

    def test_missing_directory_redacted(self):
        self.rejected(['--control-store-conformance', '--scratch-root',
                       str(Path(self.temp.name)/'PRIVATE-CANARY')], 'scratch-root-invalid')

    def test_existing_database_cannot_be_given_as_scratch(self):
        with tempfile.NamedTemporaryFile(dir=self.temp.name) as existing:
            before = os.fstat(existing.fileno()).st_size
            self.rejected(['--control-store-conformance', '--scratch-root', existing.name],
                          'scratch-root-invalid')
            self.assertEqual(before, os.fstat(existing.fileno()).st_size)

    def test_missing_dependency_has_fixed_envelope(self):
        original = builtins.__import__
        def altered(name, *args, **kwargs):
            if name == 'control_store_conformance':
                raise ImportError('PRIVATE-CANARY')
            return original(name, *args, **kwargs)
        with mock.patch('builtins.__import__', side_effect=altered):
            self.rejected(code='dependency-unavailable')

    def test_missing_schema_safe_without_schema_backed_error_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(contracts, 'SCHEMA_DIR', Path(directory)):
                status, result = self.call()
        self.assertEqual(1, status)
        build_contracts.validate_schema('control-store-error', result)
        self.assertEqual([{'code': 'source-invalid'}], result['findings'])

    def test_unknown_exception_is_redacted(self):
        with mock.patch.object(runner, 'conformance', side_effect=RuntimeError('PRIVATE-CANARY')):
            self.rejected(code='conformance-failed')

    def test_unreviewed_control_error_is_redacted(self):
        with mock.patch.object(runner, 'conformance', side_effect=contracts.ControlFailure('PRIVATE-CANARY')):
            self.rejected(code='conformance-failed')

    def test_exception_subclass_cannot_choose_safe_looking_error(self):
        class Derived(contracts.ControlFailure):
            pass
        with mock.patch.object(runner, 'conformance', side_effect=Derived('scratch-root-invalid')):
            self.rejected(code='conformance-failed')

    def test_unsafe_extra_result_field_is_redacted(self):
        changed = copy.deepcopy(self.result)
        changed['password'] = 'PRIVATE-CANARY'
        with mock.patch.object(runner, 'conformance', return_value=changed):
            self.rejected(code='conformance-failed')

    def test_digest_mutation_is_rejected(self):
        changed = copy.deepcopy(self.result)
        changed['result_digest'] = 'sha256:'+'0'*64
        with mock.patch.object(runner, 'conformance', return_value=changed):
            self.rejected(code='conformance-failed')

    def test_fresh_self_hash_cannot_hide_stale_bindings(self):
        changed = copy.deepcopy(self.result)
        changed['runner_digest'] = 'sha256:'+'0'*64
        changed['result_digest'] = contracts.digest({key: value for key, value in changed.items()
                                                     if key != 'result_digest'})
        with mock.patch.object(runner, 'conformance', return_value=changed):
            self.rejected(code='conformance-failed')

    def test_authority_cannot_be_promoted(self):
        for key, value in [('authorized', True), ('release_eligibility', 'passed'),
                           ('operation_authorization', 'passed'), ('qualification_verdict', 'passed')]:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.result); changed[key] = value
                with mock.patch.object(runner, 'conformance', return_value=changed):
                    self.rejected(code='conformance-failed')

    def test_consumer_rejects_conformance_for_all_purposes(self):
        for purpose in ('source-analysis', 'release-eligibility', 'operation-authorization'):
            with self.subTest(purpose=purpose):
                result = result_consumption.consume_result(self.result, purpose)
                self.assertEqual('rejected', result['verdict'])
                self.assertFalse(result['authorized'])

    def test_public_bootstrap_import_failure_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory)/'script.py'
            script.write_bytes(Path(__file__).with_name('script.py').read_bytes())
            outcome = subprocess.run([sys.executable, '-B', str(script), '--control-store-conformance',
                                      '--scratch-root', 'PRIVATE-CANARY'], cwd=directory,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
                                     env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'})
        self.assertEqual(1, outcome.returncode)
        self.assertEqual(b'', outcome.stderr)
        self.assertNotIn(b'PRIVATE-CANARY', outcome.stdout)
        result = json.loads(outcome.stdout)
        build_contracts.validate_schema('control-store-error', result)
        self.assertEqual([{'code': 'dependency-unavailable'}], result['findings'])


if __name__ == '__main__':
    unittest.main()

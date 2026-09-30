"""Existing public recovery dispatch is bounded and cannot confer source or release authority."""
import builtins
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import build_contracts
import finite_recovery_conformance as runner
import finite_recovery_contracts as contracts
import result_consumption
import result_consumption_cli
import release_compiler
import script as gate
from test_finite_recovery_conformance import fixture

MODE = '--finite-recovery-conformance'
ARGS = [MODE, '--source-root', 'unused', '--scratch-root', 'unused', '--image-id', 'unused']


class FiniteRecoveryCliTests(unittest.TestCase):
    def call(self, arguments):
        output, errors = StringIO(), StringIO()
        with patch.object(sys, 'argv', ['script.py', *arguments]), redirect_stdout(output), redirect_stderr(errors):
            status = gate.main()
        self.assertEqual('', errors.getvalue())
        self.assertNotIn('PRIVATE-CANARY', output.getvalue())
        return status, json.loads(output.getvalue())

    def rejected(self, arguments):
        status, result = self.call(arguments)
        self.assertEqual(1, status)
        build_contracts.validate_schema('finite-recovery-error', result)
        self.assertEqual(False, result['authorized'])
        return result

    def test_valid_dispatch_returns_revalidated_source_only_receipt(self):
        value = fixture()
        value['runner_digest'] = runner._bindings()
        value['result_digest'] = contracts.digest({key: item for key, item in value.items() if key != 'result_digest'})
        with patch.object(runner, 'run', return_value=value) as execute:
            status, result = self.call(ARGS)
        execute.assert_called_once_with('unused', 'unused', 'unused')
        self.assertEqual(0, status)
        self.assertEqual(value, result)
        build_contracts.validate_schema('finite-recovery-conformance', result)

    def test_shell_wrapper_invalid_request_is_closed(self):
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(['bash', 'scripts/04.deploy/operational-realization-gate/script.sh',
                                 MODE, '--command', 'PRIVATE-CANARY'], cwd=root,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        self.assertEqual(1, result.returncode)
        self.assertEqual(b'', result.stderr)
        self.assertNotIn(b'PRIVATE-CANARY', result.stdout)
        build_contracts.validate_schema('finite-recovery-error', json.loads(result.stdout))

    def test_missing_required_arguments_refused_before_runner(self):
        with patch.object(runner, 'run') as execute:
            for arguments in ([MODE], ARGS[:-2], ARGS[:3], [MODE, '--image-id', 'PRIVATE-CANARY']):
                with self.subTest(arguments=arguments):
                    self.rejected(arguments)
            execute.assert_not_called()

    def test_duplicate_or_value_selector_refused_before_runner(self):
        with patch.object(runner, 'run') as execute:
            for arguments in ([*ARGS, MODE], [MODE + '=true', *ARGS[1:]], [*ARGS, MODE + '=true']):
                with self.subTest(arguments=arguments):
                    self.rejected(arguments)
            execute.assert_not_called()

    def test_duplicate_input_equals_forms_refused_before_runner(self):
        with patch.object(runner, 'run') as execute:
            for flag in ('--source-root', '--scratch-root', '--image-id'):
                with self.subTest(flag=flag):
                    self.rejected([*ARGS, flag + '=PRIVATE-CANARY'])
            execute.assert_not_called()

    def test_other_modes_and_consumer_options_refused_before_runner(self):
        with patch.object(runner, 'run') as execute:
            for flags in (['--control-store-conformance'], ['--estate-callers'], ['--release', 'PRIVATE-CANARY'],
                          ['--consume-result', 'PRIVATE-CANARY', '--purpose', 'source-analysis'], ['--builds']):
                with self.subTest(flags=flags):
                    self.rejected([*ARGS, *flags])
            execute.assert_not_called()

    def test_unknown_command_and_abbreviated_input_refused_before_runner(self):
        with patch.object(runner, 'run') as execute:
            self.rejected([*ARGS, '--command', 'PRIVATE-CANARY'])
            self.rejected([MODE, '--source', 'PRIVATE-CANARY', *ARGS[3:]])
            execute.assert_not_called()

    def test_import_failure_uses_schema_independent_error(self):
        original = builtins.__import__
        def altered(name, *args, **kwargs):
            if name == 'finite_recovery_conformance':
                raise ImportError('PRIVATE-CANARY')
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=altered):
            self.rejected(ARGS)

    def test_unknown_entrypoint_exception_is_redacted(self):
        with patch.object(runner, 'main', side_effect=RuntimeError('PRIVATE-CANARY')):
            self.rejected(ARGS)

    def test_aggregate_conformance_is_refused_for_every_consumer_purpose(self):
        value = fixture()
        for purpose in ('source-analysis', 'release-eligibility', 'operation-authorization'):
            with self.subTest(purpose=purpose):
                decision = result_consumption.consume_result(value, purpose, expected_result=deepcopy(value))
                self.assertEqual('rejected', decision['verdict'])
                self.assertFalse(decision['authorized'])

    def test_per_attempt_results_are_refused_for_every_consumer_purpose(self):
        for row in fixture()['cases']:
            for purpose in ('source-analysis', 'release-eligibility', 'operation-authorization'):
                with self.subTest(case=row['case'], purpose=purpose):
                    value = row['result']
                    decision = result_consumption.consume_result(value, purpose, expected_result=deepcopy(value))
                    self.assertEqual('rejected', decision['verdict'])
                    self.assertFalse(decision['authorized'])

    def test_consumer_never_dispatches_recovery_as_recomputation(self):
        with patch.object(runner, 'run') as execute:
            with self.assertRaises(release_compiler.ReleaseFailure):
                result_consumption_cli.recompute(ARGS)
            execute.assert_not_called()

    def test_error_schema_refuses_extra_fields_and_authority(self):
        value = self.rejected([MODE])
        for key, change in [('password', 'PRIVATE-CANARY'), ('authorized', True),
                            ('operation_authorization', 'passed')]:
            with self.subTest(key=key), self.assertRaises(release_compiler.ReleaseFailure):
                build_contracts.validate_schema('finite-recovery-error', {**value, key: change})


if __name__ == '__main__':
    unittest.main()

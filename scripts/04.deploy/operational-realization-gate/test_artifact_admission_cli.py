"""Public command refusal and authority-boundary tests."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import TestCase, main, mock

import artifact_admission_cli as cli
import artifact_admission as admission
import artifact_verifier as verifier
from test_artifact_admission import fixtures, IMAGE_CONFIG


class CliTests(TestCase):
    def call(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(argv)
        return status, json.loads(output.getvalue())

    def test_missing_inputs_is_safe_rejection(self):
        status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)
        self.assertEqual([{'code': 'input-invalid'}], result['findings'])

    def test_duplicate_flag(self):
        status, result = self.call(['--artifact-admission', '--artifact-admission', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)
        self.assertFalse(result['authorized'])

    def test_arbitrary_executable_override_unavailable(self):
        status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing', '--verifier', 'SECRET-MARKER'])
        self.assertEqual(1, status)
        self.assertNotIn('SECRET-MARKER', json.dumps(result))

    def test_custom_trust_root_override_unavailable(self):
        status, _ = self.call(['--artifact-admission', '--verifier-cache', '/missing', '--custom-trusted-root', '/other'])
        self.assertEqual(1, status)

    def test_preverified_result_override_unavailable(self):
        status, _ = self.call(['--artifact-admission', '--verifier-cache', '/missing', '--verified-result', '/other'])
        self.assertEqual(1, status)

    def test_fixture_conformance_cannot_use_custom_policy(self):
        status, _ = self.call(['--artifact-verifier-conformance', '--verifier-cache', '/missing', '--policy', '/other'])
        self.assertEqual(1, status)

    def test_acquisition_cannot_use_extra_source_inputs(self):
        status, _ = self.call(['--artifact-verifier-acquire', '--verifier-cache', '/missing', '--artifact', '/other'])
        self.assertEqual(1, status)

    def test_modes_mutually_exclusive(self):
        status, _ = self.call(['--artifact-admission', '--artifact-verifier-conformance', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)

    def test_policy_incomplete_does_not_acquire_or_invoke_verifier(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            policy, artifact, _ = fixtures(); policy['scan']['scanner_version'] = None
            for name, data in [('policy.json', json.dumps(policy).encode()), ('artifact.json', artifact),
                               ('config.json', IMAGE_CONFIG), ('bundle.json', b'{}')]:
                (temp/name).write_bytes(data)
            argv = ['--artifact-admission', '--verifier-cache', '/missing', '--policy', str(temp/'policy.json'),
                    '--artifact', str(temp/'artifact.json'), '--image-config', str(temp/'config.json')]
            for name in ('provenance', 'sbom', 'scan'):
                argv += ['--'+name+'-bundle', str(temp/'bundle.json')]
            with mock.patch.object(verifier, 'verify_bundle') as crypto, mock.patch.object(verifier, 'acquire') as acquire:
                status, result = self.call(argv)
                crypto.assert_not_called(); acquire.assert_not_called()
            self.assertEqual(1, status)
            self.assertEqual([{'code': 'policy-incomplete'}], result['findings'])

    def test_existing_gate_dispatches_safely(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('script.py')), '--artifact-admission',
                   '--verifier-cache', '/missing', '--unexpected', 'SECRET-MARKER']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        self.assertEqual(1, result.returncode)
        self.assertEqual(b'', result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual('artifact-supply-chain', parsed['scope'])
        self.assertNotIn(b'SECRET-MARKER', result.stdout)

    def test_missing_schema_still_emits_safe_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(admission.build_contracts, 'SCHEMA_DIR', Path(temp)):
                status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)
        self.assertEqual([{'code': 'schema-invalid'}], result['findings'])
        self.assertFalse(result['authorized'])

    def test_corrupt_schema_still_emits_safe_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for name in admission.SCHEMAS:
                (temp/(name+'.schema.yml')).write_text('invalid: [SECRET-MARKER')
            with mock.patch.object(admission.build_contracts, 'SCHEMA_DIR', temp):
                status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)
        self.assertNotIn('SECRET-MARKER', json.dumps(result))
        self.assertEqual([{'code': 'schema-invalid'}], result['findings'])

    def test_unreadable_runner_still_emits_safe_rejection(self):
        with mock.patch.object(verifier, 'read_bytes', side_effect=verifier.AdmissionFailure('artifact-unreadable')):
            status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing'])
        self.assertEqual(1, status)
        self.assertEqual([{'code': 'schema-invalid'}], result['findings'])

    def test_bootstrap_failure_uses_distinct_closed_error_contract(self):
        import jsonschema
        import release_compiler
        with mock.patch.object(admission, 'initial', side_effect=OSError('SECRET-MARKER')):
            status, result = self.call(['--artifact-admission', '--verifier-cache', '/missing'])
        schema = release_compiler.load_document(admission.build_contracts.SCHEMA_DIR / 'artifact-admission-error.schema.yml')
        jsonschema.Draft202012Validator(schema).validate(result)
        self.assertEqual(1, status)
        self.assertEqual('artifact-admission-error/v1', result['schema'])
        self.assertNotIn('SECRET-MARKER', json.dumps(result))

    def test_unsafe_json_inputs_not_echoed(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp); path = temp/'input.json'; path.write_text('{"password":"SECRET-MARKER","password":1}')
            args = ['--artifact-admission', '--verifier-cache', '/missing', '--policy', str(path),
                    '--artifact', str(path), '--image-config', str(path)]
            for name in ('provenance', 'sbom', 'scan'): args += ['--'+name+'-bundle', str(path)]
            status, result = self.call(args)
            self.assertEqual(1, status)
            self.assertNotIn('SECRET-MARKER', json.dumps(result))


if __name__ == '__main__':
    main()

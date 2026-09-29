"""Boundary tests for maintained offline signature verification; real fixtures run separately."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import signal
import subprocess
import tempfile
from unittest import TestCase, main, mock

import artifact_verifier as verifier
from artifact_verifier_conformance import fixture_expected


def verified_output(expected=None):
    expected = expected or fixture_expected()
    identity = 'https://github.com/' + expected['repository'] + '/' + expected['workflow'] + '@' + expected['ref']
    certificate = {'subjectAlternativeName': identity, 'issuer': verifier.ISSUER,
                   'sourceRepositoryURI': 'https://github.com/' + expected['repository'],
                   'sourceRepositoryDigest': expected['commit'], 'sourceRepositoryRef': expected['ref'],
                   'buildSignerURI': identity, 'buildSignerDigest': expected['commit'],
                   'buildConfigURI': identity, 'buildConfigDigest': expected['commit'],
                   'runnerEnvironment': 'github-hosted'}
    return [{'verificationResult': {'signature': {'certificate': certificate},
             'verifiedTimestamps': [{'timestamp': '2024-04-22T17:33:26Z'}],
             'statement': {'_type': 'https://in-toto.io/Statement/v1',
                           'subject': [{'name': expected['subject_name'], 'digest': {'sha256': expected['subject_digest'][7:]}}],
                           'predicateType': expected['predicate'], 'predicate': {}}}}]


class VerifierTests(TestCase):
    def setUp(self):
        self.expected = fixture_expected()
        self.output = verified_output()

    def parse(self):
        return verifier.parse_verified(json.dumps(self.output).encode(), self.expected)

    def test_single_fresh_verifier_statement(self):
        self.assertEqual(verifier.PROVENANCE, self.parse()['predicateType'])

    def test_multiple_verified_statements_ambiguous(self):
        self.output *= 2
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_empty_verified_output(self):
        self.output = []
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_no_trusted_timestamp(self):
        self.output[0]['verificationResult']['verifiedTimestamps'] = []
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_wrong_oidc_issuer(self):
        self.output[0]['verificationResult']['signature']['certificate']['issuer'] = 'https://attacker.invalid'
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_reusable_signer_wrong_digest(self):
        self.output[0]['verificationResult']['signature']['certificate']['buildSignerDigest'] = '0' * 40
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_self_hosted_runner(self):
        self.output[0]['verificationResult']['signature']['certificate']['runnerEnvironment'] = 'self-hosted'
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_source_identity_mismatch(self):
        self.output[0]['verificationResult']['signature']['certificate']['sourceRepositoryURI'] += '-other'
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_duplicate_subject_rejected(self):
        self.output[0]['verificationResult']['statement']['subject'] *= 2
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_config_digest_not_expected_subject(self):
        self.output[0]['verificationResult']['statement']['subject'][0]['digest']['sha256'] = '0' * 64
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_wrong_predicate(self):
        self.output[0]['verificationResult']['statement']['predicateType'] = verifier.SBOM
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_missing_verification_result(self):
        self.output = [{'verified': True}]
        with self.assertRaises(verifier.AdmissionFailure): self.parse()

    def test_duplicate_json_keys(self):
        with self.assertRaises(verifier.AdmissionFailure): verifier.json_bytes(b'{"a":1,"a":2}')

    def test_nonfinite_json(self):
        with self.assertRaises(verifier.AdmissionFailure): verifier.json_bytes(b'{"a":NaN}')

    def test_nested_json_limit(self):
        with self.assertRaises(verifier.AdmissionFailure): verifier.json_bytes(b'[' * 500 + b']' * 500)

    def test_unreadable_file(self):
        with self.assertRaises(verifier.AdmissionFailure): verifier.read_bytes('/not-found-artifact-test')

    def test_file_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp); (path/'file').write_bytes(b'x'); (path/'link').symlink_to(path/'file')
            with self.assertRaises(verifier.AdmissionFailure): verifier.read_bytes(path/'link')

    def test_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp); (path/'dir').mkdir(); (path/'dir/file').write_bytes(b'x'); (path/'link').symlink_to(path/'dir')
            with self.assertRaises(verifier.AdmissionFailure): verifier.read_bytes(path/'link/file')

    def test_fifo_rejected_without_blocking(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fifo'; os.mkfifo(path)
            with self.assertRaises(verifier.AdmissionFailure): verifier.read_bytes(path)

    def test_file_size_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'data'; path.write_bytes(b'123')
            with self.assertRaises(verifier.AdmissionFailure): verifier.read_bytes(path, 2)

    def test_pinned_root_modified(self):
        original = verifier.read_bytes
        def read(path, maximum=verifier.MAX_INPUT):
            value = original(path, maximum)
            return value + b' ' if Path(path).name == 'trusted-root.jsonl' else value
        with mock.patch.object(verifier, 'read_bytes', side_effect=read):
            with self.assertRaisesRegex(verifier.AdmissionFailure, 'verifier-integrity'): verifier.load_lock()

    def test_unknown_cache_binary_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'gh').write_bytes(b'#!/bin/sh\nexit 0\n')
            with self.assertRaisesRegex(verifier.AdmissionFailure, 'verifier-integrity'): verifier.checked_binary(temp)

    def test_no_unsigned_saved_result_parameter(self):
        import inspect
        parameters = inspect.signature(verifier.verify_bundle).parameters
        self.assertEqual({'cache', 'artifact', 'bundle', 'expected'}, set(parameters))

    def test_subprocess_arguments_are_fixed_and_network_isolated(self):
        artifact = verifier.read_bytes(verifier.FIXTURES/'upstream-artifact.whl')
        bundle = verifier.read_bytes(verifier.FIXTURES/'upstream-provenance.bundle.jsonl')
        lock, root = verifier.load_lock()
        with mock.patch.object(verifier, 'checked_binary', return_value=(lock, root, b'fake-tool-for-unit-test')):
            with mock.patch.object(verifier, '_run', return_value=json.dumps(self.output).encode()) as runner:
                verifier.verify_bundle('/test', artifact, bundle, self.expected)
        argv = runner.call_args.args[0]
        self.assertIn('--unshare-net', argv)
        self.assertIn('--clearenv', argv)
        self.assertIn('--deny-self-hosted-runners', argv)
        self.assertIn('--source-digest', argv)
        self.assertIn('--signer-digest', argv)
        self.assertNotIn('--bundle-from-oci', argv)
        self.assertNotIn('--cert-identity-regex', argv)
        self.assertFalse(any('TOKEN' in value for value in argv))

    def test_bundle_collection_rejected(self):
        artifact = verifier.read_bytes(verifier.FIXTURES/'upstream-artifact.whl')
        with self.assertRaises(verifier.AdmissionFailure): verifier.verify_bundle('/test', artifact, b'[]', self.expected)

    def test_mismatched_artifact_fails_before_tool_access(self):
        with mock.patch.object(verifier, 'checked_binary') as tool:
            with self.assertRaises(verifier.AdmissionFailure): verifier.verify_bundle('/test', b'wrong', b'{}', self.expected)
            tool.assert_not_called()

    def test_timeout_kills_owned_process_group(self):
        child = mock.Mock(pid=1234)
        child.wait.side_effect = [subprocess.TimeoutExpired('gh', 30), 0]
        child.poll.return_value = 0
        with mock.patch.object(verifier.subprocess, 'Popen', return_value=child):
            with mock.patch.object(verifier.os, 'killpg') as kill:
                with self.assertRaisesRegex(verifier.AdmissionFailure, 'verifier-timeout'): verifier._run(['test'])
        kill.assert_called_once_with(1234, signal.SIGKILL)

    def test_nonzero_exit_is_safe_failure(self):
        child = mock.Mock(returncode=1); child.poll.return_value = 1
        with mock.patch.object(verifier.subprocess, 'Popen', return_value=child):
            with self.assertRaisesRegex(verifier.AdmissionFailure, 'verifier-failed'): verifier._run(['test'])

    def test_source_ref_argument_injection_rejected(self):
        with self.assertRaises(verifier.AdmissionFailure):
            verifier.expected_identity('actions/attest-demo', '--help', '.github/workflows/build-python.yml',
                                       'a'*40, 'subject', 'sha256:'+'b'*64, verifier.PROVENANCE)


if __name__ == '__main__':
    main()

"""Reject stale, ambiguous and unsafe finite-job evidence without a daemon."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.finite-job-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Exercise exact-command terminal bindings and negative authority, cleanup, timeout and schema boundaries.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_contracts
import finite_job_contracts as contracts
import release_compiler as release

IMAGE = 'sha256:' + 'a' * 64
PAYLOAD = 'sha256:' + 'b' * 64
OTHER = 'sha256:' + 'c' * 64
RUN = 'd' * 32


def profile():
    return {'schema': 'finite-job-profile/v1', 'id': 'fixture-success',
            'artifact': {'image_id': IMAGE, 'payload_digest': PAYLOAD},
            'execution': {'entrypoint': ['/nodejs/bin/node'],
                          'command': ['jobs/fixture.mjs', 'success'], 'working_dir': '/app'},
            'limits': {'timeout_seconds': 3, 'output_bytes': 4096},
            'completion': {'protocol': 'finite-job-terminal/v1', 'required_checks': ['fixture-completed']}}


def terminal(value=None):
    value = profile() if value is None else value
    return {'schema': 'finite-job-terminal/v1', 'run_id': RUN,
            'profile_digest': contracts.profile_digest(value), 'outcome': 'completed',
            'checks': [{'id': name, 'verdict': 'passed'} for name in value['completion']['required_checks']]}


def receipt():
    value = profile()
    checks = terminal(value)['checks']
    return contracts.make_result(value, RUN, {
        'outcome': 'completed', 'failure_code': None, 'exit_code': 0, 'oom_killed': False,
        'terminal_digest': contracts.terminal_digest(value, RUN, checks), 'checks': checks,
        'cleanup_verified': True, 'elapsed_ms': 75})


def reseal(value):
    value['result_digest'] = contracts.digest({key: row for key, row in value.items() if key != 'result_digest'})
    return value


class ProfileTests(unittest.TestCase):
    def test_valid_profile_has_stable_schema_bound_digest(self):
        value = profile()
        self.assertEqual(contracts.validate_profile(value), value)
        self.assertEqual(contracts.profile_digest(value), contracts.profile_digest(deepcopy(value)))

    def test_changed_schema_invalidates_previous_profile_binding(self):
        before = contracts.profile_digest(profile())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in contracts.SCHEMAS:
                path = build_contracts.SCHEMA_DIR / (name + '.schema.yml')
                schema = json.loads(path.read_text())
                if name == 'finite-job-result': schema['description'] = 'Changed contract revision fixture.'
                (root / path.name).write_text(json.dumps(schema))
            with patch.object(build_contracts, 'SCHEMA_DIR', root):
                self.assertNotEqual(before, contracts.profile_digest(profile()))

    def test_result_schema_must_remain_closed(self):
        value = receipt()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in contracts.SCHEMAS:
                path = build_contracts.SCHEMA_DIR / (name + '.schema.yml')
                schema = json.loads(path.read_text())
                if name == 'finite-job-result': schema['additionalProperties'] = True
                (root / path.name).write_text(json.dumps(schema))
            with patch.object(build_contracts, 'SCHEMA_DIR', root), self.assertRaises(release.ReleaseFailure):
                contracts.validate_result(value, profile(), RUN)

    def test_missing_profile_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(build_contracts, 'SCHEMA_DIR', Path(temporary)):
            with self.assertRaises(release.ReleaseFailure): contracts.validate_profile(profile())

    def test_result_binds_expected_profile_without_mutation(self):
        value = receipt()
        original = deepcopy(value)
        self.assertEqual(contracts.validate_result(value, profile(), RUN), original)
        self.assertEqual(value, original)


PROFILE_CHANGES = {
    'unknown_environment': lambda v: v.update(environment={'TOKEN': 'fixture'}),
    'unsafe_nested_field': lambda v: v['execution'].update(host_mount='/host'),
    'unsupported_version': lambda v: v.update(schema='finite-job-profile/v2'),
    'mutable_image': lambda v: v['artifact'].update(image_id='image:latest'),
    'unbound_payload': lambda v: v['artifact'].pop('payload_digest'),
    'absolute_command': lambda v: v['execution'].update(command=['/host/command.js']),
    'option_command': lambda v: v['execution'].update(command=['--fixture.js']),
    'newline_command': lambda v: v['execution'].update(command=['fixture.js\n']),
    'newline_argument': lambda v: v['execution'].update(command=['fixture.js', 'mode\n']),
    'newline_identifier': lambda v: v.update(id='fixture\n'),
    'newline_check': lambda v: v['completion'].update(required_checks=['fixture\n']),
    'parent_command': lambda v: v['execution'].update(command=['jobs/../command.js']),
    'dot_command': lambda v: v['execution'].update(command=['./command.js']),
    'empty_segment_command': lambda v: v['execution'].update(command=['jobs//command.js']),
    'source_typescript_command': lambda v: v['execution'].update(command=['jobs/fixture.ts']),
    'shell_entrypoint': lambda v: v['execution'].update(entrypoint=['/bin/sh']),
    'different_working_directory': lambda v: v['execution'].update(working_dir='/tmp'),
    'arbitrary_command_argument': lambda v: v['execution'].update(command=['job.js', '--secret=value']),
    'argument_path': lambda v: v['execution'].update(command=['job.js', '/host/value']),
    'zero_deadline': lambda v: v['limits'].update(timeout_seconds=0),
    'unbounded_deadline': lambda v: v['limits'].update(timeout_seconds=121),
    'boolean_deadline': lambda v: v['limits'].update(timeout_seconds=True),
    'small_output_limit': lambda v: v['limits'].update(output_bytes=127),
    'large_output_limit': lambda v: v['limits'].update(output_bytes=65537),
    'empty_completion_rules': lambda v: v['completion'].update(required_checks=[]),
    'duplicate_completion_rules': lambda v: v['completion'].update(required_checks=['same', 'same']),
    'unbounded_completion_rules': lambda v: v['completion'].update(required_checks=['check-' + str(i) for i in range(17)]),
    'unsafe_check_identifier': lambda v: v['completion'].update(required_checks=['secret=fixture']),
    'unsupported_terminal_protocol': lambda v: v['completion'].update(protocol='stdout-exit-zero'),
}


def profile_case(change):
    def test(self):
        value = profile(); change(value)
        with self.assertRaises(release.ReleaseFailure): contracts.validate_profile(value)
    return test


for case_name, change in PROFILE_CHANGES.items():
    setattr(ProfileTests, 'test_reject_' + case_name, profile_case(change))


class TerminalTests(unittest.TestCase):
    def reject(self, value):
        with self.assertRaises(release.ReleaseFailure):
            contracts.evaluate_terminal(value, profile(), RUN)

    def test_exact_terminal_returns_only_reviewed_checks(self):
        value = terminal()
        self.assertEqual(contracts.evaluate_terminal(json.dumps(value).encode(), profile(), RUN), value['checks'])

    def test_whitespace_does_not_change_terminal_identity(self):
        value = terminal(); raw = (' \n' + json.dumps(value, indent=2) + '\n').encode()
        checks = contracts.evaluate_terminal(raw, profile(), RUN)
        self.assertEqual(contracts.terminal_digest(profile(), RUN, checks), contracts.digest(value))

    def test_multiple_required_checks_are_ordered_and_complete(self):
        value = profile(); value['completion']['required_checks'] = ['one', 'two']
        message = terminal(value)
        self.assertEqual(contracts.evaluate_terminal(json.dumps(message).encode(), value, RUN), message['checks'])
        message['checks'].reverse()
        with self.assertRaises(release.ReleaseFailure):
            contracts.evaluate_terminal(json.dumps(message).encode(), value, RUN)

    def test_empty_output_rejects(self): self.reject(b'')
    def test_nonbyte_output_rejects(self): self.reject(json.dumps(terminal()))
    def test_invalid_utf8_rejects(self): self.reject(b'\xff')
    def test_raw_logs_reject(self): self.reject(b'job finished successfully')
    def test_multiple_envelopes_reject(self): self.reject(json.dumps(terminal()).encode() * 2)
    def test_nan_rejects(self): self.reject(b'{"outcome":NaN}')
    def test_top_level_array_rejects(self): self.reject(json.dumps([terminal()]).encode())
    def test_duplicate_top_level_key_rejects(self): self.reject(json.dumps(terminal()).replace('"schema":', '"schema":"finite-job-terminal/v1","schema":', 1).encode())
    def test_duplicate_nested_key_rejects(self): self.reject(json.dumps(terminal()).replace('"verdict":', '"verdict":"passed","verdict":', 1).encode())
    def test_over_limit_rejects_without_text_exposure(self):
        with self.assertRaises(release.ReleaseFailure) as caught:
            contracts.evaluate_terminal(b'private-fixture' * 400, profile(), RUN)
        self.assertEqual(str(caught.exception), 'finite-job-output-limit')
    def test_deep_document_rejects(self): self.reject(b'[' * 1000 + b'0' + b']' * 1000)
    def test_missing_run_rejects(self):
        value = terminal(); value.pop('run_id'); self.reject(json.dumps(value).encode())
    def test_stale_run_rejects(self):
        value = terminal(); value['run_id'] = 'e' * 32; self.reject(json.dumps(value).encode())
    def test_stale_profile_rejects(self):
        value = terminal(); value['profile_digest'] = OTHER; self.reject(json.dumps(value).encode())
    def test_extra_secret_field_rejects(self):
        value = terminal(); value['secret'] = 'fixture'; self.reject(json.dumps(value).encode())
    def test_missing_check_rejects(self):
        value = terminal(); value['checks'] = []; self.reject(json.dumps(value).encode())
    def test_duplicate_check_rejects(self):
        value = terminal(); value['checks'] *= 2; self.reject(json.dumps(value).encode())
    def test_wrong_check_rejects(self):
        value = terminal(); value['checks'][0]['id'] = 'other'; self.reject(json.dumps(value).encode())
    def test_failed_check_rejects(self):
        value = terminal(); value['checks'][0]['verdict'] = 'failed'; self.reject(json.dumps(value).encode())
    def test_pretended_protocol_completion_rejects(self):
        value = terminal(); value['outcome'] = 'failed'; self.reject(json.dumps(value).encode())
    def test_invalid_requested_run_rejects(self):
        with self.assertRaises(release.ReleaseFailure): contracts.evaluate_terminal(json.dumps(terminal()).encode(), profile(), 'not-fresh')


class ResultTests(unittest.TestCase):
    def test_completed_result_still_cannot_claim_semantics_or_authority(self):
        value = receipt()
        self.assertEqual(value['outcome'], 'completed')
        self.assertEqual(value['semantic_verdict'], 'unverified')
        self.assertEqual(value['operation_authorization'], 'blocked')
        self.assertFalse(value['authorized'])

    def test_elapsed_includes_preparation_and_cleanup_outside_execution_deadline(self):
        value = receipt(); value['elapsed_ms'] = 9000; reseal(value)
        self.assertEqual(contracts.validate_result(value, profile(), RUN)['elapsed_ms'], 9000)

    def test_changed_expected_image_rejects_resealed_result(self):
        value = receipt(); expected = profile(); expected['artifact']['image_id'] = OTHER
        with self.assertRaises(release.ReleaseFailure): contracts.validate_result(value, expected, RUN)

    def test_changed_expected_run_rejects_resealed_result(self):
        with self.assertRaises(release.ReleaseFailure): contracts.validate_result(receipt(), profile(), 'e' * 32)

    def test_observation_unknown_field_cannot_be_projected_away(self):
        observation = {key: value for key, value in receipt().items() if key in contracts.OBSERVATION_FIELDS}
        observation['raw_stdout'] = 'private fixture'
        with self.assertRaises(release.ReleaseFailure): contracts.make_result(profile(), RUN, observation)

    def test_missing_observation_field_rejects(self):
        observation = {key: value for key, value in receipt().items() if key in contracts.OBSERVATION_FIELDS}
        observation.pop('cleanup_verified')
        with self.assertRaises(release.ReleaseFailure): contracts.make_result(profile(), RUN, observation)

    def test_digest_mutation_rejects(self):
        value = receipt(); value['elapsed_ms'] = 76
        with self.assertRaises(release.ReleaseFailure): contracts.validate_result(value, profile(), RUN)

    def test_valid_failures_preserve_failed_outcome_and_no_semantic_claim(self):
        for code in sorted(contracts.FAILURE_CODES):
            outcome = ('timed-out' if code == 'deadline-exceeded' else 'interrupted' if code == 'interrupted'
                       else 'unknown' if code in {'engine-unavailable', 'observation-unavailable', 'cleanup-failed'} else 'failed')
            value = contracts.make_result(profile(), RUN, {
                'outcome': outcome, 'failure_code': code, 'exit_code': 17 if code == 'exit-nonzero' else None,
                'oom_killed': True if code == 'oom-killed' else None, 'terminal_digest': None, 'checks': [],
                'cleanup_verified': code != 'cleanup-failed', 'elapsed_ms': 75})
            self.assertNotEqual(value['outcome'], 'completed')
            self.assertEqual(value['semantic_verdict'], 'unverified')


RESULT_CHANGES = {
    'unknown_public_field': lambda v: v.update(raw_stdout='private-fixture'),
    'unknown_settings': lambda v: v['settings'].update(secret='fixture'),
    'authorized': lambda v: v.update(authorized=True),
    'eligible': lambda v: v.update(release_eligibility='eligible'),
    'operation_authorized': lambda v: v.update(operation_authorization='authorized'),
    'qualification_pass': lambda v: v.update(qualification_verdict='passed'),
    'source_closed': lambda v: v.update(source_closure='complete'),
    'semantic_pass': lambda v: v.update(semantic_verdict='passed'),
    'network_expansion': lambda v: v['settings'].update(network='bridge'),
    'host_mount': lambda v: v['settings'].update(host_mounts=['/host']),
    'root_user': lambda v: v['settings'].update(user='0:0'),
    'arbitrary_environment_key': lambda v: v['settings']['environment_keys'].append('AWS_SECRET_ACCESS_KEY'),
    'wrong_profile_hash': lambda v: v.update(profile_digest=OTHER),
    'wrong_schema_hash': lambda v: v['schema_digests'].update({'finite-job-result/v1': OTHER}),
    'wrong_terminal_hash': lambda v: v.update(terminal_digest=OTHER),
    'completed_without_terminal': lambda v: v.update(terminal_digest=None),
    'completed_without_check': lambda v: v.update(checks=[]),
    'completed_without_cleanup': lambda v: v.update(cleanup_verified=False),
    'completed_nonzero_exit': lambda v: v.update(exit_code=17),
    'completed_unknown_exit': lambda v: v.update(exit_code=None),
    'completed_oom': lambda v: v.update(oom_killed=True),
    'completed_unknown_oom': lambda v: v.update(oom_killed=None),
    'completed_failure_code': lambda v: v.update(failure_code='exit-nonzero'),
    'negative_elapsed': lambda v: v.update(elapsed_ms=-1),
    'boolean_exit': lambda v: v.update(exit_code=False),
    'boolean_elapsed': lambda v: v.update(elapsed_ms=True),
    'failed_retains_checks': lambda v: v.update(outcome='failed', failure_code='terminal-invalid'),
    'failed_without_failure_code': lambda v: v.update(outcome='failed', terminal_digest=None, checks=[]),
    'timeout_misclassified': lambda v: v.update(outcome='failed', failure_code='deadline-exceeded', terminal_digest=None, checks=[]),
    'interruption_misclassified': lambda v: v.update(outcome='failed', failure_code='interrupted', terminal_digest=None, checks=[]),
    'unknown_misclassified': lambda v: v.update(outcome='failed', failure_code='engine-unavailable', terminal_digest=None, checks=[]),
    'cleanup_failure_claims_cleanup': lambda v: v.update(outcome='unknown', failure_code='cleanup-failed', terminal_digest=None, checks=[]),
    'failure_missing_cleanup_reason': lambda v: v.update(outcome='failed', failure_code='terminal-invalid', terminal_digest=None, checks=[], cleanup_verified=False),
    'failed_exit_zero_as_nonzero': lambda v: v.update(outcome='failed', failure_code='exit-nonzero', terminal_digest=None, checks=[]),
    'failed_oom_false': lambda v: v.update(outcome='failed', failure_code='oom-killed', terminal_digest=None, checks=[]),
    'private_failure_code': lambda v: v.update(outcome='failed', failure_code='secret-fixture', terminal_digest=None, checks=[]),
}


def result_case(change):
    def test(self):
        value = receipt(); change(value); reseal(value)
        with self.assertRaises(release.ReleaseFailure): contracts.validate_result(value, profile(), RUN)
    return test


for case_name, change in RESULT_CHANGES.items():
    setattr(ResultTests, 'test_reject_' + case_name, result_case(change))


if __name__ == '__main__':
    unittest.main()

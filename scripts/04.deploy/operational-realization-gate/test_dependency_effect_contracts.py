"""Positive bindings and adversarial local dependency evidence mutations."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.dependency-effect-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Reject unsafe, stale and authority-bearing local dependency evidence.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependency_effect_contracts as c

D = 'sha256:' + 'a' * 64
ROOT = Path(__file__).resolve().parent


def profile():
    return {'schema': 'dependency-effect-profile/v1', 'scope': 'local-packaged-postgresql-effects',
            'repository_head': 'a' * 40, 'source_digest': D, 'build_result_digest': D, 'runner_digest': D,
            'lock_digest': D, 'expectations_digest': D, 'artifact': {'image_id': D, 'payload_digest': D},
            'dependency': {'image': 'docker.io/library/postgres@' + D, 'image_id': D, 'engine_version': '17.11',
                           'network': 'owned-internal', 'published_ports': [], 'tls': 'verify-full-local-ca'},
            'commands': deepcopy(c.COMMANDS), 'schema_digests': c.schema_digests()}


def result():
    cases = [{'case': name, 'task': task, 'outcome': outcome, 'exit_code': 0 if outcome == 'succeeded' else 1,
              'attempt_id': f'{index:032x}', 'terminal_digest': D, 'before_digest': D, 'after_digest': D,
              'assertions': [{'id': a, 'verdict': 'passed'} for a in checks], 'elapsed_ms': 100}
             for index, (name, task, outcome, checks) in enumerate(c.CASES)]
    return c.make_result(profile(), 'f' * 32, cases, D, {'client': '29.5.2', 'server': '29.5.2'})


def terminal(outcome='succeeded', task='bootstrap', **fields):
    return json.dumps({'level': 'info' if outcome == 'succeeded' else 'error',
                       'message': 'kanbien-platform.relational-smoke.' + task + '_completed',
                       'fields': {'outcome': outcome, **fields}}).encode()


class Contracts(unittest.TestCase):
    def test_complete_local_receipt(self):
        value = result()
        self.assertEqual(c.validate_result(value, profile(), 'f' * 32), value)
        self.assertEqual(value['pending_tasks'], ['relay', 'worker', 'restore-verify'])

    def test_lock_is_pinned(self):
        value = json.loads((ROOT / 'dependency-image.lock.json').read_text())
        self.assertEqual(c.validate_lock(value), value)
        value['image'] = 'postgres:17.11-bookworm'
        with self.assertRaises(c.release.ReleaseFailure): c.validate_lock(value)

    def test_expectations_closed(self):
        value = json.loads((ROOT / 'fixtures/dependency-effects/expectations.json').read_text())
        self.assertEqual(c.validate_expectations(value), value)
        value['password'] = 'private'
        with self.assertRaises(c.release.ReleaseFailure): c.validate_expectations(value)

    def test_terminal_success(self):
        self.assertRegex(c.terminal(terminal(), 'bootstrap', 'succeeded'), r'^sha256:')

    def test_terminal_expected_failure_category(self):
        raw = terminal('failed', failure_category='bootstrap-database-authentication-failure')
        self.assertRegex(c.terminal(raw, 'bootstrap', 'failed', failure_category='bootstrap-database-authentication-failure'), '^sha256:')
        with self.assertRaises(c.release.ReleaseFailure):
            c.terminal(raw, 'bootstrap', 'failed', failure_category='bootstrap-database-tls-failure')

    def test_terminal_duplicate(self):
        raw = terminal().replace(b'"outcome": "succeeded"', b'"outcome":"failed","outcome":"succeeded"')
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(raw, 'bootstrap', 'succeeded')

    def test_terminal_multiline(self):
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(terminal() + b'\n' + terminal(), 'bootstrap', 'succeeded')

    def test_terminal_extra_secret(self):
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(terminal(password='do-not-print'), 'bootstrap', 'succeeded')

    def test_terminal_unknown_category(self):
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(terminal('failed', failure_category='raw-secret-error'), 'bootstrap', 'failed')

    def test_terminal_wrong_task(self):
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(terminal(task='migration'), 'bootstrap', 'succeeded')

    def test_terminal_oversize(self):
        with self.assertRaises(c.release.ReleaseFailure): c.terminal(b' ' * 4097, 'bootstrap', 'succeeded')

    def test_attempt_replay(self):
        value = result(); value['cases'][1]['attempt_id'] = value['cases'][0]['attempt_id']
        self.refuse(value)

    def test_case_order(self):
        value = result(); value['cases'][0], value['cases'][1] = value['cases'][1], value['cases'][0]
        self.refuse(value)

    def test_missing_case(self):
        value = result(); value['cases'].pop()
        self.refuse(value)

    def test_duplicate_case(self):
        value = result(); value['cases'][1] = value['cases'][0]
        self.refuse(value)

    def test_changed_effect(self):
        value = result(); value['cases'][4]['after_digest'] = 'sha256:' + 'b' * 64
        self.refuse(value)

    def test_wrong_exit(self):
        value = result(); value['cases'][0]['exit_code'] = 0
        self.refuse(value)

    def test_wrong_assertion(self):
        value = result(); value['assertions'][0]['id'] = 'raw-output'
        self.refuse(value)

    def test_stale_attempt(self):
        with self.assertRaises(c.release.ReleaseFailure): c.validate_result(result(), profile(), 'e' * 32)

    def test_stale_profile(self):
        expected = profile(); expected['source_digest'] = 'sha256:' + 'b' * 64
        with self.assertRaises(c.release.ReleaseFailure): c.validate_result(result(), expected, 'f' * 32)

    def test_stale_schemas(self):
        expected = profile(); expected['schema_digests']['dependency-effect-profile/v1'] = D
        with self.assertRaises(c.release.ReleaseFailure): c.validate_profile(expected)

    def refuse(self, value):
        value['result_digest'] = c.digest({k:v for k,v in value.items() if k != 'result_digest'})
        with self.assertRaises(c.release.ReleaseFailure): c.validate_result(value, profile(), 'f' * 32)


def mutation(name, path, bad):
    def check(self):
        value = result(); node = value
        for key in path[:-1]: node = node[key]
        node[path[-1]] = bad
        self.refuse(value)
    setattr(Contracts, 'test_refuse_' + name, check)

for name, path, value in [
    ('authority', ['authorized'], True), ('integer_authority', ['authorized'], 0),
    ('release', ['release_eligibility'], 'eligible'), ('operation', ['operation_authorization'], 'allowed'),
    ('qualification', ['qualification_verdict'], 'passed'), ('closure', ['source_closure'], 'complete'),
    ('cleanup', ['cleanup_verified'], False), ('extra', ['raw_stdout'], 'private'),
    ('unbounded_port', ['profile','dependency','published_ports'], [5432]),
    ('host_network', ['profile','dependency','network'], 'host'),
    ('tls_disabled', ['profile','dependency','tls'], 'disabled'),
    ('arbitrary_command', ['profile','commands','bootstrap'], ['/tmp/task.js']),
    ('pending_erased', ['pending_tasks'], []), ('wrong_version', ['profile','dependency','engine_version'], '18.6'),
]: mutation(name, path, value)

if __name__ == '__main__': unittest.main()

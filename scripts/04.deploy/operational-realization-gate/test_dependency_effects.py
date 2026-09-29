"""Independent state assertions and safe CLI boundaries for packaged command proof."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.dependency-effects
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Verify independent effects reject missing grants, corrupt history, altered tables and unsafe CLI inputs.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependency_effects as e
import dependency_effect_contracts as c

EXPECTED = json.loads((Path(__file__).resolve().parent / 'fixtures/dependency-effects/expectations.json').read_text())
EMPTY = {'roles': [], 'memberships': [], 'schema_owner': None, 'tables': [], 'runtime_schema_create': None,
         'runtime_database_create': None, 'migration_schema_create': None, 'history': [], 'columns': [], 'constraints': []}


def bootstrapped():
    return {'roles': [{'name': 'psmokemigrate', 'login': True, 'elevated': False},
                      {'name': 'psmokeruntime', 'login': True, 'elevated': False}],
            'memberships': [], 'schema_owner': 'psmokemigrate', 'tables': [], 'runtime_schema_create': False,
            'runtime_database_create': False, 'migration_schema_create': True, 'history': [], 'columns': [], 'constraints': []}


def migrated():
    return {**bootstrapped(), 'tables': [{'name': name, 'owner': 'psmokemigrate', 'runtime_dml': True} for name in EXPECTED['tables']],
            'history': [{'id': key, 'checksum': value, 'tool_version': 'stage6-staging', 'applied_at': '2026-09-29T12:00:00Z'}
                        for key,value in sorted(EXPECTED['migration_checksums'].items())],
            'columns': deepcopy(EXPECTED['columns']), 'constraints': deepcopy(EXPECTED['constraints'])}


class Effects(unittest.TestCase):
    def test_empty_baseline(self): self.assertTrue(e.empty_state(EMPTY))
    def test_bootstrap_effect(self): e.check_case('bootstrap', EMPTY, bootstrapped(), EXPECTED)
    def test_migration_effect(self): e.check_case('migration', bootstrapped(), migrated(), EXPECTED)
    def test_repeat_preserves_applied_time(self): e.check_case('migration-repeat', migrated(), migrated(), EXPECTED)
    def test_negative_auth_no_effect(self): e.check_case('bootstrap-bad-password', EMPTY, EMPTY, EXPECTED)
    def test_negative_tls_no_effect(self): e.check_case('bootstrap-untrusted-ca', EMPTY, EMPTY, EXPECTED)
    def test_denied_migration_no_tables(self): e.check_case('migration-denied', bootstrapped(), bootstrapped(), EXPECTED)
    def test_checksum_mismatch(self):
        state = migrated(); state['history'][1]['checksum'] = '0' * 64
        e.check_case('migration-checksum-mismatch', state, state, EXPECTED)
    def test_negative_does_not_erase_effect(self):
        with self.assertRaises(c.release.ReleaseFailure): e.check_case('bootstrap-bad-password', EMPTY, bootstrapped(), EXPECTED)
    def test_repeat_changed_time(self):
        value = migrated(); value['history'][0]['applied_at'] = '2026-09-29T13:00:00Z'
        with self.assertRaises(c.release.ReleaseFailure): e.check_case('migration-repeat', migrated(), value, EXPECTED)
    def test_unknown_case(self):
        with self.assertRaises(c.release.ReleaseFailure): e.check_case('unknown', EMPTY, EMPTY, EXPECTED)
    def test_missing_argument_safe_json(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): status=e.main([])
        self.assertEqual(status,1); self.assertFalse(json.loads(output.getvalue())['authorized'])
    def test_duplicate_argument_safe(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): status=e.main(['--source-root','/tmp','--source-root','/private-value'])
        self.assertEqual(status,1); self.assertNotIn('private-value',output.getvalue())
    def test_exception_redacted(self):
        output=io.StringIO()
        with patch.object(e.local_container,'checked_scratch',side_effect=RuntimeError('secret-do-not-print')), contextlib.redirect_stdout(output):
            status=e.main(['--source-root','/tmp','--scratch-root','/tmp','--package-cache','/tmp'])
        self.assertEqual(status,1); self.assertNotIn('secret-do-not-print',output.getvalue())
    def assert_cli_failure(self, error, expected):
        output=io.StringIO()
        with patch.object(e.local_container, 'checked_scratch', side_effect=error), contextlib.redirect_stdout(output):
            status=e.main(['--source-root','/tmp','--scratch-root','/tmp','--package-cache','/tmp'])
        self.assertEqual(status, 1)
        result=json.loads(output.getvalue())
        self.assertEqual(result['findings'], [{'code': expected}])
        self.assertFalse(result['authorized'])
        self.assertEqual({key: result[key] for key in c.BLOCKED}, c.BLOCKED)
    def test_upstream_build_timeout_preserved(self):
        self.assert_cli_failure(e.LocalBuildFailure('local-build-timeout'), 'local-build-timeout')
    def test_upstream_payload_failure_preserved(self):
        self.assert_cli_failure(e.LocalBuildFailure('container-payload-copy-changed'), 'container-payload-copy-changed')
    def test_upstream_toolchain_failure_preserved(self):
        self.assert_cli_failure(e.ToolchainFailure('locked-toolchain-node-hash-mismatch'), 'locked-toolchain-node-hash-mismatch')
    def test_upstream_toolchain_cache_binding_preserved(self):
        self.assert_cli_failure(e.ToolchainFailure('locked-toolchain-cache-binding-mismatch'), 'locked-toolchain-cache-binding-mismatch')
    def test_upstream_build_output_membership_preserved(self):
        self.assert_cli_failure(e.LocalBuildFailure('local-build-output-membership-invalid'), 'local-build-output-membership-invalid')
    def test_engine_code_preserved(self):
        self.assert_cli_failure(e.EngineFailure('local-container-command-timeout'), 'local-container-command-timeout')
    def test_contract_code_preserved(self):
        self.assert_cli_failure(e.release.ReleaseFailure('dependency-effect-source-changed'), 'dependency-effect-source-changed')
    def test_unknown_exception_code_lookalike_redacted(self):
        self.assert_cli_failure(RuntimeError('local-build-timeout'), 'dependency-effect-verification-failed')
    def test_unknown_exception_attribute_redacted(self):
        error=RuntimeError('secret-do-not-print'); error.code='local-container-command-timeout'
        self.assert_cli_failure(error, 'dependency-effect-verification-failed')
    def test_known_exception_secret_message_redacted(self):
        self.assert_cli_failure(e.LocalBuildFailure('local-build-timeout password=private-value'), 'dependency-effect-verification-failed')
    def test_known_build_type_private_code_redacted(self):
        self.assert_cli_failure(e.LocalBuildFailure('local-build-private-canary'), 'dependency-effect-verification-failed')
    def test_known_toolchain_type_private_code_redacted(self):
        self.assert_cli_failure(e.ToolchainFailure('locked-toolchain-private-canary'), 'dependency-effect-verification-failed')
    def test_known_exception_wrong_prefix_redacted(self):
        self.assert_cli_failure(e.ToolchainFailure('local-build-timeout'), 'dependency-effect-verification-failed')
    def test_known_exception_newline_redacted(self):
        self.assert_cli_failure(e.LocalBuildFailure('local-build-timeout\nprivate-value'), 'dependency-effect-verification-failed')
    def test_known_exception_oversized_code_redacted(self):
        self.assert_cli_failure(e.ToolchainFailure('locked-toolchain-'+('private-'*100)+'value'), 'dependency-effect-verification-failed')
    def test_known_exception_subclass_redacted(self):
        class Unreviewed(e.LocalBuildFailure): pass
        self.assert_cli_failure(Unreviewed('local-build-timeout'), 'dependency-effect-verification-failed')
    def test_actual_executing_source_snapshot(self):
        root=Path(__file__).resolve().parents[3]
        files, digest=e.snapshot(root)
        self.assertIn(e.LOCK,files); self.assertRegex(digest,r'^sha256:')
    def test_alternate_source_changed_helper(self):
        root=Path(__file__).resolve().parents[3]; original=e.local_container.read
        def changed(where,name):
            raw=original(where,name)
            return raw+b'\n' if where==root and name.endswith('/dependency_effect_contracts.py') else raw
        with patch.object(e.local_container,'read',side_effect=changed):
            with self.assertRaises(c.release.ReleaseFailure): e.snapshot(root)


def mutation(name, change):
    def test(self):
        state=migrated();change(state)
        self.assertFalse(e.migration_state(state,EXPECTED))
    setattr(Effects,'test_mismatch_'+name,test)

for name, change in [
    ('inherited_role',lambda s:s['memberships'].append({'role':'pg_read_all_data','member':'psmokeruntime'})),
    ('role_elevated',lambda s:s['roles'][1].update(elevated=True)),
    ('schema_owner',lambda s:s.update(schema_owner='postgres')),
    ('runtime_ddl',lambda s:s.update(runtime_schema_create=True)),
    ('runtime_database_ddl',lambda s:s.update(runtime_database_create=True)),
    ('missing_table',lambda s:s['tables'].pop()),
    ('extra_table',lambda s:s['tables'].append({'name':'unexpected','owner':'psmokemigrate','runtime_dml':True})),
    ('wrong_owner',lambda s:s['tables'][0].update(owner='postgres')),
    ('missing_grant',lambda s:s['tables'][0].update(runtime_dml=False)),
    ('missing_history',lambda s:s['history'].pop()),
    ('wrong_checksum',lambda s:s['history'][0].update(checksum='0'*64)),
    ('wrong_tool',lambda s:s['history'][0].update(tool_version='unknown')),
    ('column_type',lambda s:s['columns'][0].update(type='integer')),
    ('missing_column',lambda s:s['columns'].pop()),
    ('nullable',lambda s:s['columns'][0].update(nullable=True)),
    ('missing_constraint',lambda s:s['constraints'].pop()),
    ('weakened_constraint',lambda s:s['constraints'][0].update(definition='CHECK (true)')),
]:mutation(name,change)

if __name__=='__main__':unittest.main()

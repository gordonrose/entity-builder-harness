#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.mechanics
#   version: 2
#   status: active
#   created_on: "2026-10-29"
#   updated_on: "2026-11-05"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: test
#   purpose: Prove runner mechanics using disposable fixture repositories.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh
from __future__ import annotations
from test_support import *


class SelectionTests(FixtureSupport):
    def test_registered_preflight_without_cache_falls_back_to_execution(self):
        subprocess.run(['git', '-C', str(self.root), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'fixture baseline'], check=True)
        with tempfile.TemporaryDirectory() as directory:
            preflight = Path(directory) / 'preflight'
            subprocess.run(['git', '-C', str(self.root), 'worktree', 'add', '--detach', '--quiet', str(preflight)], check=True)
            try:
                self.assertIsNone(local_cache.LocalCache.registered_source(self.root, preflight))
                report = self.run_plan(checks=['local'], execute=True, reuse_from_worktree=preflight)
                self.assertFalse(report['findings'], report['findings'])
                self.assertEqual(report['execution_summary']['executed_check_ids'], ['local'])
                self.assertEqual(report['execution_summary']['reused_check_ids'], [])
                cache_path = Path(subprocess.run(['git', '-C', str(preflight), 'rev-parse', '--absolute-git-dir'], check=True, capture_output=True, text=True).stdout.strip()) / 'agentic-local-checks'
                cache_path.mkdir(mode=0o755)
                cache_path.chmod(0o755)
                unsafe = self.run_plan(checks=['local'], execute=True, reuse_from_worktree=preflight)
                self.assertIn({'code': 'reuse-worktree-unavailable', 'detail': 'local-cache-permissions-invalid'}, unsafe['findings'])
                self.assertEqual(unsafe['execution_summary']['executed_check_ids'], [])
            finally:
                subprocess.run(['git', '-C', str(self.root), 'worktree', 'remove', '--force', str(preflight)], check=True)

    def test_artifact_migration_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('harness-artifact-migration-regression', 'artifact-migration')

    def test_dynamodb_owned_leaf_failure_reuse_and_source_runtime_contract_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('dynamodb-persistence-runtime', 'dynamodb')

    def test_sqs_owned_leaf_failure_reuse_and_source_runtime_contract_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('sqs-queue-runtime', 'sqs')

    def test_aws_alignment_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('aws-runtime-alignment-regression', 'aws-alignment')

    def test_provider_condition_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('provider-condition-evidence-regression', 'provider-condition')

    def test_core_target_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('core-target-declaration-regression', 'core-target')

    def test_delivery_access_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('delivery-access-contract-regression', 'delivery-access')

    def test_bootstrap_controls_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('bootstrap-target-controls-regression', 'bootstrap-controls')

    def test_foundation_budget_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('foundation-budget-regression', 'foundation-budget')

    def test_harness_validator_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('harness-agent-validator-regression', 'harness-validator')

    def test_harness_index_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('harness-index-regression', 'harness-index')

    def test_chat_export_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-export-regression', 'chat-export')

    def test_chat_commit_metrics_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-commit-metrics-regression', 'chat-commit-metrics')

    def test_imported_diagnostic_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-refresh-readiness-regression', 'chat-refresh-readiness')

    def test_imported_audit_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-conflict-audit-regression', 'chat-conflict-audit')

    def test_imported_cleanup_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-cleanup-regression', 'chat-cleanup')

    def test_imported_prerequisites_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-prerequisites-regression', 'chat-prerequisites')

    def test_imported_recovery_leaf_failure_reuse_and_invalidation(self):
        self.assert_owned_adapter_leaf_receipts('chat-recovery-regression', 'chat-recovery')

    def test_chat_leaf_closed_dispatch_preserves_child_status_without_forwarded_commands(self):
        wrapper = self.root / 'scripts/repo/check-selection/smoke-test.sh'
        shutil.copyfile(ROOT / 'scripts/repo/check-selection/smoke-test.sh', wrapper)
        units = {
            'chat-startup': 'scripts/00.chat/startup/start-chat-session/smoke-test.sh',
            'chat-log-writers': 'scripts/00.chat/session-log/update-chat-log/smoke-test.sh',
            'chat-log-maintenance': 'scripts/00.chat/session-log/checkpoint-chat-session-log/smoke-test.sh',
            'chat-summary': 'scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh',
            'chat-upstream-portability': 'scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh',
            'harness-governed-runner': 'scripts/01.harness/smoke-test-governed-script-runner.sh',
            'harness-command-drift': 'scripts/01.harness/smoke-test-governed-script-command-drift.sh',
            'harness-process-drift': 'scripts/01.harness/smoke-test-deterministic-process-drift.sh',
            'chat-bootstrap-audit': 'scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/smoke-test.sh',
            'chat-migration-audit': 'scripts/00.chat/migration/audit-chat-layer-migration/smoke-test.sh',
            'chat-upstream-ensure': 'scripts/00.chat/upstream/ensure-llm-workbench-repo/smoke-test.sh',
            'chat-upstream-contract': 'scripts/00.chat/upstream/check-llm-workbench-contract/smoke-test.sh',
            'chat-upstream-bootstrap': 'scripts/00.chat/upstream/bootstrap-llm-workbench-repo/smoke-test.sh',
            'chat-integration-preparation': 'scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/smoke-test.sh',
            'chat-cleanup': 'scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh',
            'chat-prerequisites': 'scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh',
            'chat-conflict-audit': 'scripts/00.chat/main-refresh/verify-conflict-audit/smoke-test.sh',
            'chat-recovery': 'scripts/00.chat/recovery/import-active-paths-to-chat-worktree/smoke-test.sh',
            'chat-session-reader': 'scripts/00.chat/session-log/read-current-chat-log/smoke-test.sh',
            'chat-session-resolution': 'scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh',
            'chat-worktree-paths': 'scripts/00.chat/worktree/paths/smoke-test.sh',
            'chat-command-dispatch': 'scripts/00.chat/command/dispatcher/smoke-test.sh',
            'chat-refresh-readiness': 'scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh',
            'chat-conflict-classification': 'scripts/00.chat/main-refresh/classify-conflict/smoke-test.sh',
            'chat-log-deletion': 'scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh',
            'chat-export': 'scripts/00.chat/export/smoke-test.sh',
            'chat-commit-metrics': 'scripts/00.chat/session-log/record-chat-commit/smoke-test.sh',
        }
        for unit, relative in units.items():
            child = self.root / relative
            child.parent.mkdir(parents=True, exist_ok=True)
            child.write_text('printf "%s\\n" "' + unit + '" >> dispatch-counts\nif [ -f fail-child ]; then exit 17; fi\n')
        def invoke(*arguments):
            return subprocess.run(['bash', str(wrapper), *arguments], cwd=self.root, capture_output=True, text=True)
        for unit in units:
            self.assertEqual(invoke('--unit', unit).returncode, 0)
        counts = self.root / 'dispatch-counts'
        self.assertEqual(counts.read_text().splitlines(), list(units))
        for arguments in [('--unit', 'unknown'), ('--unit', 'chat-export; touch escaped'), ('--unit', 'chat-export', 'extra')]:
            self.assertEqual(invoke(*arguments).returncode, 2)
        self.assertFalse((self.root / 'escaped').exists())
        self.assertEqual(counts.read_text().splitlines(), list(units))
        (self.root / 'fail-child').touch()
        for unit in units:
            self.assertEqual(invoke('--unit', unit).returncode, 17)
        self.assertEqual(counts.read_text().splitlines(), [*units, *units])

    def assert_owned_adapter_leaf_receipts(self, identity, fixture):
        # Real command membership is asserted by RepositoryContractTests; here a
        # disposable command proves the existing runner's leaf receipt behavior.
        real = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks'][identity]
        self.check_script(fixture, real['effects'], 'echo run >> adapter-counts\nif [ -f fail-adapter ]; then exit 9; fi\n')
        check = copy.deepcopy(real)
        check.update(argv=['bash', f'scripts/{fixture}.sh'], inputs=['src', f'scripts/{fixture}.sh'],
            runtime={'tools': ['bash'], 'environment': ['ADAPTER_FIXTURE_RUNTIME']}, owner=f'fixture.{fixture}')
        self.catalog['checks'][identity] = check
        self.save()
        failed_marker = self.root / 'fail-adapter'
        failed_marker.touch()
        failed = self.run_plan(checks=[identity], execute=True)
        self.assertEqual(next(item for item in failed['checks'] if item['check_id'] == identity)['status'], 'failed')
        failed_marker.unlink()
        first = self.run_plan(checks=[identity], execute=True)
        self.assertEqual(first['execution_summary']['executed_check_ids'], [identity])
        again = self.run_plan(checks=[identity], execute=True)
        self.assertEqual(again['execution_summary']['reused_check_ids'], [identity])
        (self.root / 'src/main.ts').write_text('changed adapter source\n')
        changed = self.run_plan(checks=[identity], execute=True)
        self.assertEqual(changed['execution_summary']['executed_check_ids'], [identity])
        with patch.dict(os.environ, {'ADAPTER_FIXTURE_RUNTIME': 'changed'}):
            runtime = self.run_plan(checks=[identity], execute=True)
            self.assertEqual(runtime['execution_summary']['executed_check_ids'], [identity])
        check['argv'].append('--changed-verification-contract')
        self.save()
        contract = self.run_plan(checks=[identity], execute=True)
        self.assertEqual(contract['execution_summary']['executed_check_ids'], [identity])

    def test_focused_prerequisites_order_explicit_and_unrelated_context(self):
        self.focused_fixture()
        report = self.run_plan(checks=['local'], task_paths=['src/main.ts'], execute=True)
        self.assertFalse(report['findings'], report['findings'])
        self.assertEqual((self.root / 'counts').read_text(), 'focus\nlocal\n')
        again = self.run_plan(checks=['local'], task_paths=['src/main.ts'], execute=True)
        self.assertEqual(set(again['execution_summary']['reused_check_ids']), {'focus', 'local'})
        unrelated = self.run_plan(checks=['local'], task_paths=['docs/guide.md'], execute=True)
        self.assertIn('verification-task-context-mismatch', self.codes(unrelated))
        self.run_plan(checks=['local'], task_paths=['docs/guide.md'], record_preparation=True)
        unrelated = self.run_plan(checks=['local'], execute=True)
        self.assertEqual([item['check_id'] for item in unrelated['checks']], ['local'])
        selection.LocalCache(self.root).save_preparation({'checks': []})
        missing = self.run_plan(checks=['local'], execute=True)
        self.assertIn('verification-task-context-required', self.codes(missing))


    def test_failed_or_mutated_focused_proof_blocks_broad_command(self):
        for body in ['echo focus >> counts\nexit 7\n', 'echo changed >> scripts/focus.sh\n']:
            self.focused_fixture(body)
            report = self.run_plan(checks=['local'], task_paths=['src/main.ts'], execute=True)
            self.assertIn('verification-prerequisite-not-passed', self.codes(report))
            self.assertEqual(next(item for item in report['checks'] if item['check_id'] == 'local')['status'], 'blocked')
            self.assertNotIn('local', (self.root / 'counts').read_text() if (self.root / 'counts').exists() else '')


    def test_dependency_contracts_reject_cycles_unknown_refs_and_external_children(self):
        base = {'stage': 'local', 'effects': ['writes-files']}
        for child, expected in [({'stage': 'package', 'effects': ['network']}, 'verification-dependency-boundary-invalid'), ({**base, 'members': ['root']}, 'verification-dependency-cycle')]:
            graph, findings = selection.verification_dependencies({'root': {**base, 'members': ['child']}, 'child': child}, ['root'], ['src'])
            self.assertIn(expected, {item['code'] for item in findings})
        _, findings = selection.verification_dependencies({'root': {**base, 'members': ['missing']}}, ['root'], ['src'])
        self.assertIn('verification-dependency-unknown', {item['code'] for item in findings})


    def test_focused_member_peers_do_not_gain_artificial_cycles(self):
        leaf = {'stage': 'local', 'effects': ['writes-files']}
        graph, findings = selection.verification_dependencies({'root': {**leaf, 'members': ['first', 'second', 'work'], 'focused_prerequisites': [{'inputs': ['src'], 'checks': ['first', 'second']}]}, **{name: leaf for name in ['first', 'second', 'work']}}, ['root'], ['src'])
        self.assertFalse(findings)
        self.assertEqual(graph['first'], set())
        self.assertEqual(graph['second'], set())
        self.assertEqual(graph['work'], {'first', 'second'})


    def test_all_inputs_and_workload_specific_startup_conditions(self):
        self.focused_fixture()
        report = self.run_plan(all_inputs=True)
        self.assertFalse({'verification-task-context-invalid', 'verification-task-context-required'} & self.codes(report), report['findings'])

    def test_explicit_broad_context_cannot_be_forged_and_stale_prep_blocks(self):
        self.prepare_selector_cli()
        self.focused_fixture()
        for flags, environment in [(['--task-paths', 'docs/unrelated.md'], self.cli_environment), ([], {**self.cli_environment, 'REPO_CHECK_TASK_PATHS': '["docs/unrelated.md"]'}), ([], {**self.cli_environment, 'REPO_CHECK_TASK_PATHS': '"src/main.ts"'})]:
            result = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--checks', 'local', '--execute-local', *flags], cwd=self.root, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertTrue({'verification-task-context-mismatch', 'verification-task-context-invalid'} & self.codes(json.loads(result.stdout)))
        self.assertFalse((self.root / 'counts').exists())
        (self.root / 'src/main.ts').write_text('changed prepared source\n')
        self.assertIn('verification-task-context-stale', self.codes(self.run_plan(checks=['local'], execute=True)))
        self.assertFalse((self.root / 'counts').exists())


    def test_aggregate_input_runtime_and_contract_changes_invalidate_parent(self):
        self.focused_fixture()
        self.catalog['checks']['focus']['runtime']['environment'] = ['FIXTURE_RUNTIME']
        self.save()
        with patch.dict(os.environ, {'FIXTURE_RUNTIME': 'one'}): first = self.run_plan(execute=True)
        self.assertFalse(first['findings'], first['findings'])
        with patch.dict(os.environ, {'FIXTURE_RUNTIME': 'two'}): runtime = self.run_plan(execute=True)
        self.assertFalse(runtime['findings'], runtime['findings'])
        self.assertIn('local', runtime['execution_summary']['executed_check_ids'])
        with (self.root / 'scripts/focus.sh').open('a') as stream: stream.write('# changed member input\n')
        with patch.dict(os.environ, {'FIXTURE_RUNTIME': 'two'}): source = self.run_plan(execute=True)
        self.assertIn('local', source['execution_summary']['executed_check_ids'])
        self.catalog['checks']['focus']['description'] = 'Changed member contract'
        self.save()
        with patch.dict(os.environ, {'FIXTURE_RUNTIME': 'two'}): contract = self.run_plan(execute=True)
        self.assertIn('local', contract['execution_summary']['executed_check_ids'])
        self.assertTrue(all(report['verdict'] == 'passed' for report in [source, contract]))


    def test_standalone_leaf_receipt_reuses_under_conditional_aggregate_gates(self):
        self.focused_fixture()
        self.catalog['checks']['local'].pop('focused_prerequisites')
        aggregate = copy.deepcopy(self.catalog['checks']['local'])
        aggregate.update(argv=['bash', 'scripts/aggregate.sh'], inputs=['scripts/aggregate.sh'], members=['local'], aggregate_branch='whole',
                         focused_prerequisites=[{'inputs': ['src'], 'checks': ['focus']}])
        self.catalog['checks']['aggregate'] = aggregate
        self.catalog['repository_inputs'] = [{'inputs': ['src'], 'checks': ['aggregate']}]
        selector = ROOT / 'scripts/repo/check-selection/script.py'
        bridge = self.root / 'scripts/repo/check-selection/script.sh'
        bridge.parent.mkdir(parents=True, exist_ok=True)
        bridge.write_text('exec python3 -B "' + str(selector) + '" --root "$PWD" --catalog "' + str(self.catalog_path) + '" "$@"\n')
        self.check_script('aggregate', ['read-only', 'writes-files'], 'set -euo pipefail\nROOT="$(git rev-parse --show-toplevel)"\ncd "$ROOT"\nexec bash scripts/repo/check-selection/script.sh --aggregate-members aggregate --execute-local --json\n')
        self.save()
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'fixture baseline'], check=True)
        focused = self.run_plan(checks=['local'], execute=True)
        self.assertFalse(focused['findings'], focused['findings'])
        leaf = focused['checks'][0]
        combined = self.run_plan(execute=True)
        self.assertFalse(combined['findings'], combined['findings'])
        member = next(item for item in combined['checks'] if item['check_id'] == 'local')
        root = next(item for item in combined['checks'] if item['check_id'] == 'aggregate')
        self.assertEqual(member['dependency_ids'], ['focus'], 'Caller gate must still order and qualify the member.')
        self.assertEqual(member['proof_dependency_ids'], [], 'Caller-only gate is not a consumed command input.')
        self.assertEqual(member['preparation_key'], leaf['preparation_key'])
        self.assertEqual(member['evidence_key'], leaf['evidence_key'])
        self.assertEqual(member['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual(root['nested_execution_summary']['reused_check_ids'], ['focus', 'local'])
        self.assertEqual((self.root / 'counts').read_text().splitlines().count('local'), 1)
        with (self.root / 'scripts/focus.sh').open('a') as stream: stream.write('# changed aggregate-owned focus proof\n')
        changed = self.run_plan(execute=True)
        self.assertFalse(changed['findings'], changed['findings'])
        changed_root = next(item for item in changed['checks'] if item['check_id'] == 'aggregate')
        self.assertNotEqual(changed_root['evidence_key'], root['evidence_key'])
        self.assertEqual(changed_root['evidence_source'], 'local-runner')
        self.assertEqual(next(item for item in changed['checks'] if item['check_id'] == 'local')['evidence_source'], 'trusted-worktree-cache')
        for body in ['exit 7\n', 'echo changed >> scripts/focus.sh\n']:
            self.check_script('focus', ['read-only', 'writes-files'], body)
            blocked = self.run_plan(execute=True)
            self.assertIn('verification-prerequisite-not-passed', self.codes(blocked))
            self.assertEqual(next(item for item in blocked['checks'] if item['check_id'] == 'aggregate')['status'], 'blocked')
            self.assertEqual(next(item for item in blocked['checks'] if item['check_id'] == 'local')['status'], 'blocked')
            self.assertEqual((self.root / 'counts').read_text().splitlines().count('local'), 1)


    def test_review_scoped_receipts_bind_actual_relevant_semantics(self):
        (self.root / 'package.json').write_text('{"workspaces":[]}')
        destination = self.root / 'scripts/repo/diagnostic-coverage/script.py'
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/repo/diagnostic-coverage/script.py', destination)
        for path in ['ordinary.ts', 'unrelated.ts', 'proof.test.ts']: (self.root / path).write_text('// fixture\n')
        def entry(source, check): return {'owner': source, 'status': 'support', 'reason': 'Reviewed proof plumbing.', 'sources': [{'path': source, 'sha256': 'a' * 64}], 'tests': ['proof.test.ts'], 'checks': [check]}
        document = {'schema': 'repo/diagnostic-adoption/v1', 'reviews': [entry('ordinary.ts', 'local'), entry('unrelated.ts', 'other')]}
        ledger = destination.parent / 'reviews.v1.json'
        ledger.write_text(json.dumps(document))
        self.catalog['checks']['diagnostic-adoption'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['other'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['local']['inputs'].append('scripts/repo/diagnostic-coverage')
        self.save()
        first = self.run_plan(checks=['local'], execute=True)
        self.assertFalse(first['findings'], first['findings'])
        document['reviews'][1]['reason'] = 'Unrelated review changed.'
        ledger.write_text(json.dumps(document))
        other = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(other['execution_summary']['reused_check_ids'], ['local'])
        document['reviews'][0]['reason'] = 'Relevant review changed.'
        ledger.write_text(json.dumps(document))
        own = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(own['execution_summary']['executed_check_ids'], ['local'])
        document['reviews'][0].pop('reason')
        ledger.write_text(json.dumps(document))
        invalid = self.run_plan(checks=['local'], execute=True)
        self.assertIn('diagnostic-adoption-selection-invalid', self.codes(invalid))


    def test_capability_review_receipts_preserve_independence_and_shared_delivery(self):
        (self.root / 'package.json').write_text('{"workspaces":[]}')
        destination = self.root / 'scripts/repo/diagnostic-coverage/script.py'
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/repo/diagnostic-coverage/script.py', destination)
        for path in ['config.ts', 'server.ts', 'delivery.ts', 'config.test.ts', 'server.test.ts', 'delivery.test.ts']:
            (self.root / path).write_text('// fixture\n')
        def entry(owner, source, proof, checks, definitions=()):
            return {'owner': owner, 'status': 'partial', 'reason': 'Reviewed capability boundary.',
                    'remaining_debt': ['Unselected provider failures remain unclassified.'],
                    'sources': [{'path': source, 'sha256': 'a' * 64}],
                    'tests': [proof], 'checks': checks, 'definitions': list(definitions)}
        document = {'schema': 'repo/diagnostic-adoption/v1', 'reviews': [
            entry('config', 'config.ts', 'config.test.ts', ['local']),
            entry('server', 'server.ts', 'server.test.ts', ['server'], ['config.ts']),
            entry('shared-delivery', 'delivery.ts', 'delivery.test.ts', ['local', 'server']),
        ]}
        ledger = destination.parent / 'reviews.v1.json'
        ledger.write_text(json.dumps(document))
        self.catalog['checks']['diagnostic-adoption'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['server'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['server'].update(argv=['bash', 'scripts/server.sh'], inputs=['scripts/server.sh'])
        self.check_script('server', ['read-only', 'writes-files'], 'echo server >> counts\n')
        self.save()
        first = self.run_plan(checks=['local', 'server'], execute=True)
        self.assertFalse(first['findings'], first['findings'])
        for mutation in ['reason', 'source']:
            if mutation == 'reason': document['reviews'][1]['reason'] = 'Server-only review clarification.'
            else:
                (self.root / 'server.ts').write_text('// server changed\n')
                document['reviews'][1]['sources'][0]['sha256'] = 'b' * 64
            ledger.write_text(json.dumps(document))
            report = self.run_plan(checks=['local', 'server'], execute=True)
            self.assertFalse(report['findings'], report['findings'])
            self.assertEqual(report['execution_summary']['reused_check_ids'], ['local'], mutation)
            self.assertEqual(report['execution_summary']['executed_check_ids'], ['server'], mutation)
        # One real shared proof must invalidate every consuming capability.
        (self.root / 'delivery.test.ts').write_text('// shared delivery proof changed\n')
        report = self.run_plan(checks=['local', 'server'], execute=True)
        self.assertFalse(report['findings'], report['findings'])
        self.assertEqual(report['execution_summary']['executed_check_ids'], ['local', 'server'])
        for path in ['delivery.ts', 'delivery.test.ts', 'config.ts']:
            selected = self.run_plan(paths=[path])
            self.assertFalse(selected['findings'], selected['findings'])
            self.assertTrue({'local', 'server'} <= {item['check_id'] for item in selected['checks']}, path)
        # A downstream definition reference invalidates the downstream proof too.
        (self.root / 'config.ts').write_text('// config definition changed\n')
        report = self.run_plan(checks=['local', 'server'], execute=True)
        self.assertEqual(report['execution_summary']['executed_check_ids'], ['local', 'server'])


    def test_aggregate_executes_wrapper_reuses_members_and_propagates_failure(self):
        self.focused_fixture()
        self.catalog['checks']['local'].pop('focused_prerequisites')
        self.catalog['checks']['local']['members'] = ['focus']
        self.catalog['checks']['local']['aggregate_branch'] = 'whole'
        selector = ROOT / 'scripts/repo/check-selection/script.py'
        bridge = self.root / 'scripts/repo/check-selection/script.sh'
        bridge.parent.mkdir(parents=True, exist_ok=True)
        bridge.write_text('exec python3 -B "' + str(selector) + '" --root "$PWD" --catalog "' + str(self.catalog_path) + '" "$@"\n')
        self.check_script('local', ['read-only', 'writes-files'], 'set -euo pipefail\nROOT="$(git rev-parse --show-toplevel)"\ncd "$ROOT"\nexec bash scripts/repo/check-selection/script.sh --aggregate-members local --execute-local --json\n')
        self.save()
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'fixture baseline'], check=True)
        report = self.run_plan(execute=True)
        aggregate = next(item for item in report['checks'] if item['check_id'] == 'local')
        self.assertFalse(report['findings'], {**aggregate, 'findings': report['findings']})
        self.assertEqual(aggregate['evidence_source'], 'local-runner', 'Aggregate command must actually run; never synthesize success.')
        self.assertEqual(aggregate['nested_execution_summary']['reused_check_ids'], ['focus'])
        self.assertEqual((self.root / 'counts').read_text(), 'focus\n')
        cache = selection.LocalCache(self.root)
        self.assertNotIn('active_execution', cache.read_preparation())
        expired = subprocess.run(['python3', '-B', str(selector), '--root', str(self.root), '--catalog', str(self.catalog_path), '--aggregate-members', 'local', '--execute-local'], env={**os.environ, 'REPO_CHECK_PARENT_BINDING': 'expired-reference'}, capture_output=True, text=True)
        self.assertEqual(expired.returncode, 1)
        self.assertIn('verification-parent-context-invalid', self.codes(json.loads(expired.stdout)))
        # Direct members still consume the owner's context rules, not recursion.
        cache.save_preparation({'checks': []})
        direct = subprocess.run(['python3', '-B', str(selector), '--root', str(self.root), '--catalog', str(self.catalog_path), '--aggregate-members', 'local', '--execute-local'], capture_output=True, text=True)
        self.assertIn('verification-task-context-required', self.codes(json.loads(direct.stdout)))
        prepared = self.run_plan(checks=['local'], task_paths=['src/main.ts'], record_preparation=True)
        self.assertFalse(prepared['findings'], prepared['findings'])
        direct = subprocess.run(['python3', '-B', str(selector), '--root', str(self.root), '--catalog', str(self.catalog_path), '--aggregate-members', 'local', '--execute-local'], capture_output=True, text=True)
        self.assertEqual(direct.returncode, 0, direct.stdout)
        # Exercise the actual command-exception cleanup path before receipt save.
        self.catalog['checks']['local']['description'] = 'Force a fresh wrapper attempt.'
        self.save()
        real_run = subprocess.run
        def command_failure(argv, *args, **kwargs):
            if argv == self.catalog['checks']['local']['argv']: raise OSError('synthetic runner failure')
            return real_run(argv, *args, **kwargs)
        with patch.object(selection.subprocess, 'run', side_effect=command_failure):
            with self.assertRaises(OSError): self.run_plan(execute=True)
        self.assertNotIn('active_execution', cache.read_preparation())
        self.check_script('focus', ['read-only', 'writes-files'], 'exit 7\n')
        failure = self.run_plan(execute=True)
        self.assertIn('verification-prerequisite-not-passed', self.codes(failure))
        self.assertEqual(next(item for item in failure['checks'] if item['check_id'] == 'local')['status'], 'blocked')


    def test_execution_context_preserves_preparation_and_expires_dead_runner(self):
        cache = selection.LocalCache(self.root)
        durable = {'checks': [], 'changed_inputs': [{'path': 'src/main.ts'}], 'lifecycle_inputs': {'owned': {'sha256': 'a' * 64, 'mode': 420}}}
        cache.save_preparation(durable)
        first = {'token': 'first'}
        previous = cache.begin_execution(first)
        self.assertIsNone(previous)
        second = {'token': 'second'}
        previous = cache.begin_execution(second, 'first')
        cache.end_execution('second', previous)
        self.assertEqual(cache.read_preparation()['active_execution']['token'], 'first')
        cache.end_execution('first', None)
        self.assertEqual(cache.read_preparation()['lifecycle_inputs'], durable['lifecycle_inputs'])
        self.assertNotIn('active_execution', cache.read_preparation())
        stale = {'token': 'dead', 'runner': {'pid': os.getpid(), 'start_ticks': -1}}
        cache.save_preparation({**cache.read_preparation(), 'active_execution': stale})
        self.assertFalse(cache.execution_live(stale))
        replacement = {'token': 'replacement'}
        self.assertIsNone(cache.begin_execution(replacement))
        cache.end_execution('replacement', None)
        for error in [FileNotFoundError('missing process support'), None]:
            with patch.object(local_cache.Path, 'read_text', side_effect=error, return_value='malformed process identity'):
                self.assertFalse(cache.execution_live({'runner': {'pid': os.getpid(), 'start_ticks': 1}}))
                with self.assertRaises((OSError, ValueError)): cache.begin_execution({'token': 'unsupported'})
            self.assertNotIn('active_execution', cache.read_preparation())


    def test_leaf_command_context_is_clean_under_unrelated_outer_runner_values(self):
        cases = [
            'SelectionTests.test_aggregate_executes_wrapper_reuses_members_and_propagates_failure',
            'SelectionTests.test_standalone_leaf_receipt_reuses_under_conditional_aggregate_gates',
            'SelectionTests.test_explicit_broad_context_cannot_be_forged_and_stale_prep_blocks',
        ]
        body = "python3 -B - <<'PY'\nimport importlib.util, json, os, unittest\nfrom pathlib import Path\n"
        body += "assert 'REPO_CHECK_TASK_PATHS' not in os.environ, 'leaf inherited outer task paths'\n"
        body += "assert 'REPO_CHECK_PARENT_BINDING' not in os.environ, 'leaf inherited outer parent binding'\n"
        body += 'source = ' + repr(str(ROOT / 'scripts/repo/check-selection/smoke-test.py')) + '\n'
        body += 'spec = importlib.util.spec_from_file_location("leaf_context_suite", source)\n'
        body += 'module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n'
        body += 'cases = ' + repr(cases) + '\n'
        body += '''class ObservedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.observed_ids = getattr(self, 'observed_ids', []) + [test.id().split('.', 1)[1]]
        super().startTest(test)
suite = unittest.defaultTestLoader.loadTestsFromNames(cases, module)
result = unittest.TextTestRunner(verbosity=2, resultclass=ObservedResult).run(suite)
Path('leaf-test-result.json').write_text(json.dumps({'tests_run': result.testsRun, 'successful': result.wasSuccessful(), 'test_ids': result.observed_ids, 'failures': len(result.failures), 'errors': len(result.errors)}))
raise SystemExit(0 if result.wasSuccessful() else 1)
PY
'''
        self.check_script('local', ['read-only', 'writes-files'], body)
        self.save()
        with patch.dict(os.environ, {'REPO_CHECK_TASK_PATHS': '["outer/unrelated-workflow.yml"]', 'REPO_CHECK_PARENT_BINDING': 'unrelated-outer-reference'}):
            report = self.run_plan(checks=['local'], execute=True)
        leaf = next(item for item in report['checks'] if item['check_id'] == 'local')
        self.assertFalse(report['findings'], {'findings': report['findings'], 'stderr': leaf.get('stderr_tail')})
        self.assertEqual(leaf['evidence_source'], 'local-runner')
        self.assertEqual(leaf['stderr_tail'], 'not-retained')
        self.assertEqual(json.loads((self.root / 'leaf-test-result.json').read_text()), {
            'tests_run': 3, 'successful': True, 'test_ids': cases, 'failures': 0, 'errors': 0,
        })


    def test_child_output_is_not_retained_in_report_cache_or_failure(self):
        canary = 'controlled-child-private-output'
        body = 'echo attempt >> output-counts\nprintf "' + canary + '"\nprintf "' + canary + '" >&2\n'
        self.check_script('local', ['read-only', 'writes-files'], body)
        self.save()
        passed = self.run_plan(checks=['local'], execute=True)
        item = passed['checks'][0]
        self.assertEqual((item['status'], item['exit_code'], item['stdout_tail'], item['stderr_tail']), ('passed', 0, 'not-retained', 'not-retained'))
        cache = selection.LocalCache(self.root)
        retained = cache.read(item['evidence_key'])
        self.assertEqual((retained['stdout_tail'], retained['stderr_tail']), ('not-retained', 'not-retained'))
        self.assertNotIn(canary, json.dumps(passed) + json.dumps(retained) + Path(passed['local_report_path']).read_text())
        reused = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(reused['execution_summary']['reused_check_ids'], ['local'])
        self.check_script('local', ['read-only', 'writes-files'], body + 'exit 17\n')
        for _ in range(2):
            failed = self.run_plan(checks=['local'], execute=True)
            item = failed['checks'][0]
            self.assertEqual((item['status'], item['exit_code']), ('failed', 17))
            self.assertEqual((item['stdout_tail'], item['stderr_tail']), ('not-retained', 'not-retained'))
            self.assertNotIn(canary, json.dumps(failed) + Path(failed['local_report_path']).read_text())
            self.assertFalse(cache.read(item['evidence_key']))
        self.assertEqual((self.root / 'output-counts').read_text().splitlines(), ['attempt'] * 3)


    def test_nested_summary_rejects_unknown_fields_values_and_unbounded_observations(self):
        valid = {
            'selected_check_ids': ['focus', 'local'], 'reused_check_ids': ['focus'],
            'executed_check_ids': ['local'], 'deferred_check_ids': [],
            'elapsed_seconds': 2.0, 'execution_seconds': 1.0,
            'timings': {key: 0.0 for key in ('planning_seconds', 'fingerprinting_seconds', 'runtime_identity_seconds', 'receipt_validation_seconds', 'command_execution_seconds', 'other_seconds')},
            'invalidated_checks': [{'check_id': 'local', 'reasons': ['verified-inputs-changed']}],
        }
        projected = selection.safe_nested_execution_summary(valid, {'focus', 'local'})
        self.assertEqual(projected, valid)
        self.assertIsNot(projected, valid)
        self.assertIsNot(projected['timings'], valid['timings'])
        self.assertIsNot(projected['invalidated_checks'][0]['reasons'], valid['invalidated_checks'][0]['reasons'])
        for reason in ('no-prior-successful-local-evidence', 'verified-inputs-changed', 'runtime-identity-changed', 'dependency-proof-changed', 'verification-contract-changed', 'evidence-key-changed'):
            changed = copy.deepcopy(valid); changed['invalidated_checks'][0]['reasons'] = [reason]
            self.assertEqual(selection.safe_nested_execution_summary(changed, {'focus', 'local'}), changed)
        mutations = [
            lambda value: value.update(private='controlled-nested-canary'),
            lambda value: value.update(selected_check_ids=['controlled-nested-canary']),
            lambda value: value.update(selected_check_ids=['focus', 'focus']),
            lambda value: value.update(selected_check_ids=['focus']),
            lambda value: value.update(executed_check_ids=['focus']),
            lambda value: value.update(deferred_check_ids=['local']),
            lambda value: value.update(reused_check_ids='controlled-nested-canary'),
            lambda value: value.update(elapsed_seconds='controlled-nested-canary'),
            lambda value: value.update(execution_seconds=True),
            lambda value: value.update(elapsed_seconds=-1),
            lambda value: value.update(elapsed_seconds=float('nan')),
            lambda value: value.update(elapsed_seconds=float('inf')),
            lambda value: value.update(elapsed_seconds=10 ** 1000),
            lambda value: value['timings'].update(private='controlled-nested-canary'),
            lambda value: value['timings'].update(planning_seconds='controlled-nested-canary'),
            lambda value: value['invalidated_checks'][0].update(check_id='controlled-nested-canary'),
            lambda value: value['invalidated_checks'][0].update(reasons=['controlled-nested-canary']),
            lambda value: value['invalidated_checks'][0].update(reasons=['verified-inputs-changed'] * 2),
            lambda value: value['invalidated_checks'][0].update(private='controlled-nested-canary'),
            lambda value: value['invalidated_checks'].append(copy.deepcopy(value['invalidated_checks'][0])),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(valid); mutate(changed)
            with self.subTest(value=changed):
                self.assertEqual(selection.safe_nested_execution_summary(changed, {'focus', 'local'}), {'unavailable': True})


    def test_main_does_not_publish_arbitrary_native_subclass_names(self):
        import contextlib, io, sys
        private = type('ControlledPrivateNativeClass', (ValueError,), {})
        for error, expected in ((ValueError('controlled-native-canary'), 'ValueError'), (private('controlled-native-canary'), 'unknown-runtime-error')):
            output = io.StringIO()
            with patch.object(selection, 'plan', side_effect=error), patch.object(sys, 'argv', ['selector', '--paths', 'src']), contextlib.redirect_stdout(output):
                self.assertEqual(selection.main(), 1)
            self.assertEqual(json.loads(output.getvalue()), {'schema': 'repo/check-selection-report/v1', 'verdict': 'gap', 'findings': [{'code': 'selection-input-or-runtime-invalid', 'error_type': expected}]})
            self.assertNotIn('controlled-native-canary', output.getvalue())
            self.assertNotIn('ControlledPrivateNativeClass', output.getvalue())


    def test_nested_summary_delivery_does_not_change_real_child_status_or_cache(self):
        self.focused_fixture()
        self.catalog['checks']['local'].pop('focused_prerequisites')
        self.catalog['checks']['local'].update(members=['focus'], aggregate_branch='whole')
        self.check_script('local', ['read-only', 'writes-files'], 'set -euo pipefail\nROOT="$(git rev-parse --show-toplevel)"\ncd "$ROOT"\nexec bash scripts/repo/check-selection/script.sh --aggregate-members local --execute-local --json\n')
        self.save()
        valid = {
            'selected_check_ids': ['focus'], 'reused_check_ids': ['focus'], 'executed_check_ids': [], 'deferred_check_ids': [],
            'elapsed_seconds': 1.0, 'execution_seconds': 0.0,
            'timings': {key: 0.0 for key in ('planning_seconds', 'fingerprinting_seconds', 'runtime_identity_seconds', 'receipt_validation_seconds', 'command_execution_seconds', 'other_seconds')},
            'invalidated_checks': [],
        }
        malformed = {**valid, 'private': 'controlled-nested-canary'}
        real_run = subprocess.run
        for position, (summary, status) in enumerate(((valid, 0), (malformed, 0), (malformed, 19))):
            self.catalog['checks']['local']['description'] = 'Fresh summary boundary ' + str(position)
            self.save()
            calls = []
            def command(argv, *args, **kwargs):
                if argv == self.catalog['checks']['local']['argv']:
                    calls.append(argv)
                    return subprocess.CompletedProcess(argv, status, json.dumps({'execution_summary': summary, 'private': 'controlled-nested-canary'}), 'controlled-nested-canary')
                return real_run(argv, *args, **kwargs)
            with patch.object(selection.subprocess, 'run', side_effect=command):
                report = self.run_plan(execute=True)
            item = next(item for item in report['checks'] if item['check_id'] == 'local')
            self.assertEqual(len(calls), 1)
            self.assertEqual(item['nested_execution_summary'], valid if position == 0 else {'unavailable': True})
            self.assertEqual((item['status'], item['exit_code']), ('passed' if status == 0 else 'failed', status))
            self.assertEqual((item['stdout_tail'], item['stderr_tail']), ('not-retained', 'not-retained'))
            self.assertNotIn('controlled-nested-canary', json.dumps(report) + Path(report['local_report_path']).read_text())
            retained = selection.LocalCache(self.root).read(item['evidence_key'])
            if status:
                self.assertFalse(retained)
            else:
                self.assertNotIn('controlled-nested-canary', json.dumps(retained))
                reused = self.run_plan(execute=True)
                self.assertIn('local', reused['execution_summary']['reused_check_ids'])


    def test_owned_runtime_failure_context_keeps_legacy_messages_without_private_values(self):
        canary = 'controlled-private-package'
        with self.assertRaisesRegex(ValueError, '^node-installation-dependency-missing:' + canary + '$') as missing:
            local_cache.node_installation_identity(self.root, [canary])
        self.assertEqual(local_cache.local_check_diagnostic(missing.exception), {'detail': 'node-installation-dependency-missing'})
        package = self.root / 'node_modules' / canary
        package.mkdir(parents=True)
        (package / 'package.json').write_text('{controlled-private-malformed-json')
        with self.assertRaisesRegex(ValueError, '^node-installation-manifest-invalid:' + canary + '$') as malformed:
            local_cache.node_installation_identity(self.root, [canary])
        self.assertEqual(local_cache.local_check_diagnostic(malformed.exception), {'detail': 'node-installation-manifest-invalid'})
        (package / 'package.json').write_text(json.dumps({'name': canary, 'dependencies': []}))
        with self.assertRaisesRegex(ValueError, '^node-installation-dependencies-invalid:' + canary + '$') as dependencies:
            local_cache.node_installation_identity(self.root, [canary])
        self.assertEqual(local_cache.local_check_diagnostic(dependencies.exception), {'detail': 'node-installation-dependencies-invalid'})
        for error in (ValueError('local-cache-owner-invalid ' + canary), local_cache.LocalCheckError(canary), type('PrivateNativeCanary', (local_cache.LocalCheckError,), {})('local-cache-owner-invalid')):
            self.assertEqual(local_cache.local_check_diagnostic(error), {'detail': 'unclassified-runtime-failure'})
        with patch.object(local_cache.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(ValueError, '^check-runtime-tool-missing:bash$') as absent:
                local_cache.runtime_identity(self.root, {'tools': ['bash'], 'environment': []})
        self.assertEqual(local_cache.local_check_diagnostic(absent.exception), {'detail': 'check-runtime-tool-missing', 'tool': 'bash'})
        with patch.object(local_cache.subprocess, 'run', return_value=subprocess.CompletedProcess(['bash'], 7, canary, canary)) as calls:
            with self.assertRaisesRegex(ValueError, '^check-runtime-tool-unavailable:bash$') as unavailable:
                local_cache.runtime_identity(self.root, {'tools': ['bash'], 'environment': []})
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(local_cache.local_check_diagnostic(unavailable.exception), {'detail': 'check-runtime-tool-unavailable', 'tool': 'bash'})
        self.assertEqual(local_cache.local_check_diagnostic(local_cache.LocalCheckError('check-runtime-tool-missing', canary, tool=canary)), {'detail': 'check-runtime-tool-missing'})


    def test_runner_preserves_owned_cache_and_runtime_concerns_without_native_text(self):
        canary = 'controlled-native-detail-canary'
        for error, expected in ((local_cache.LocalCheckError('node-installation-manifest-invalid', canary), 'node-installation-manifest-invalid'), (ValueError('input-symlink:' + canary), 'unclassified-runtime-failure')):
            with patch.object(selection, 'runtime_identity', side_effect=error):
                report = self.run_plan(checks=['local'], execute=True)
            finding = next(item for item in report['findings'] if item['code'] == 'check-runtime-identity-unavailable')
            self.assertEqual(finding['detail'], expected)
            self.assertNotIn(canary, json.dumps(report))
        with patch.object(selection, 'LocalCache', side_effect=OSError(canary)):
            report = self.run_plan(checks=['local'], execute=True)
        self.assertIn({'code': 'local-cache-unavailable', 'detail': 'unclassified-runtime-failure'}, report['findings'])
        self.assertNotIn(canary, json.dumps(report))
        with patch.object(selection.LocalCache, 'registered_source', side_effect=local_cache.LocalCheckError('reuse-worktree-not-registered', canary)):
            report = self.run_plan(checks=['local'], reuse_from_worktree=self.root)
        self.assertIn({'code': 'reuse-worktree-unavailable', 'detail': 'reuse-worktree-not-registered'}, report['findings'])
        self.assertNotIn(canary, json.dumps(report))


    def test_package_new_tests_and_transitive_source_invalidate_not_deploy_fixture(self):
        for relative in ['packages/upstream/src/input.ts', 'packages/owned/tests/first.test.ts', 'scripts/04.deploy/fixture.mjs']:
            path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('// initial\n')
        (self.root / 'packages/upstream/package.json').write_text('{"name":"@fixture/upstream"}')
        (self.root / 'packages/owned/package.json').write_text('{"name":"@fixture/owned","dependencies":{"@fixture/upstream":"0.0.0"}}')
        self.catalog['checks']['local']['inputs'] = ['packages/owned']
        self.save()
        self.assertFalse(self.run_plan(checks=['local'], execute=True)['findings'])
        (self.root / 'scripts/04.deploy/fixture.mjs').write_text('// unrelated correction\n')
        self.assertEqual(self.run_plan(checks=['local'], execute=True)['execution_summary']['reused_check_ids'], ['local'])
        (self.root / 'packages/owned/tests/new.test.ts').write_text('// discovered new test\n')
        self.assertEqual(self.run_plan(checks=['local'], execute=True)['execution_summary']['executed_check_ids'], ['local'])
        (self.root / 'packages/upstream/src/input.ts').write_text('// relevant dependency changed\n')
        self.assertEqual(self.run_plan(checks=['local'], execute=True)['execution_summary']['executed_check_ids'], ['local'])


    def test_measurement_and_safe_progress_do_not_echo_command_output(self):
        import contextlib, io
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream): report = self.run_plan(checks=['local'], execute=True)
        events = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual([event['event'] for event in events], ['check-start', 'check-complete'])
        self.assertEqual(events[-1]['completed'], events[-1]['total'])
        self.assertTrue(all(set(event) <= {'event', 'check_id', 'status', 'result', 'completed', 'total'} for event in events))
        timings = report['execution_summary']['timings']
        self.assertTrue(all(value >= 0 for value in timings.values()))
        self.assertAlmostEqual(sum(timings.values()), report['execution_summary']['elapsed_seconds'], delta=0.02)


    def test_explicit_checks_seed_the_same_impact_receipt(self):
        focused = self.run_plan(checks=['local'], execute=True)
        self.assertFalse(focused['findings'], focused['findings'])
        self.assertEqual(focused['selection_mode'], 'explicit-checks')
        self.assertEqual(focused['scopes'], [])
        self.assertEqual(focused['execution_summary']['executed_check_ids'], ['local'])
        impact = self.run_plan(execute=True)
        self.assertIn('local', impact['execution_summary']['reused_check_ids'])
        again = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(again['execution_summary']['reused_check_ids'], ['local'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_explicit_checks_reject_invalid_selection_before_execution(self):
        for requested, code in [([], 'explicit-check-selection-invalid'),
                                (['local', 'local'], 'explicit-check-selection-invalid'),
                                (['local', 'unknown'], 'required-check-missing'),
                                (['scope-inventory'], 'repository-check-placeholder-invalid')]:
            with self.subTest(requested=requested):
                report = self.run_plan(checks=requested, execute=True)
                self.assertIn(code, self.codes(report))
                self.assertEqual(report['execution_summary']['executed_check_ids'], [])
        self.assertFalse((self.root / 'counts').exists())


    def test_explicit_checks_keep_stage_and_effect_boundaries(self):
        report = self.run_plan(checks=['package', 'live', 'acceptance'], execute=True)
        self.assertFalse(report['findings'], report['findings'])
        self.assertEqual(set(report['execution_summary']['deferred_check_ids']), {'package', 'live', 'acceptance'})
        report = self.run_plan(checks=['package', 'live', 'acceptance'], execute=True, stage='acceptance')
        self.assertIn('required-proof-owned-by-stage-controller', self.codes(report))
        self.assertEqual(report['execution_summary']['executed_check_ids'], [])
        self.assertFalse((self.root / 'operations').exists())
        self.catalog['checks']['local']['effects'] = ['aws-mutation']
        self.save()
        self.assertIn('check-effects-mismatch', self.codes(self.run_plan(checks=['local'], execute=True)))


    def test_explicit_failed_check_never_seeds_success(self):
        self.check_script('local', ['read-only', 'writes-files'], 'exit 7\n')
        for _ in range(2):
            report = self.run_plan(checks=['local'], execute=True)
            self.assertIn('required-check-failed', self.codes(report))
            self.assertEqual(report['execution_summary']['executed_check_ids'], ['local'])
            self.assertEqual(report['execution_summary']['reused_check_ids'], [])


    def test_explicit_checks_revalidate_inputs_runtime_and_contract(self):
        self.assertFalse(self.run_plan(checks=['local'], execute=True)['findings'])
        (self.root / 'src/main.ts').write_text('changed\n')
        source = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(source['execution_summary']['executed_check_ids'], ['local'])
        with patch.dict(os.environ, {'LANG': 'verification-unit-test'}):
            runtime = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(runtime['execution_summary']['executed_check_ids'], ['local'])
        self.catalog['checks']['local']['description'] = 'Changed proof contract'
        self.save()
        contract = self.run_plan(checks=['local'], execute=True)
        self.assertEqual(contract['execution_summary']['executed_check_ids'], ['local'])
        self.assertFalse(contract['findings'])


    def test_explicit_unit_contract_change_preserves_unaffected_sibling(self):
        self.check_script('sibling', ['read-only', 'writes-files'], 'echo sibling >> counts\n')
        self.catalog['checks']['sibling'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['sibling']['argv'] = ['bash', 'scripts/sibling.sh']
        self.save()
        self.assertFalse(self.run_plan(checks=['local', 'sibling'], execute=True)['findings'])
        self.catalog['checks']['local']['description'] = 'Changed unit contract'
        self.save()
        report = self.run_plan(checks=['local', 'sibling'], execute=True)
        self.assertEqual(report['execution_summary']['executed_check_ids'], ['local'])
        self.assertEqual(report['execution_summary']['reused_check_ids'], ['sibling'])


    def test_aggregate_receipt_binds_consumed_child_catalog(self):
        self.check_script('aggregate', ['read-only', 'writes-files'], 'echo aggregate >> counts\n')
        self.catalog['checks']['aggregate'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['aggregate'].update(argv=['bash', 'scripts/aggregate.sh'],
                                                 inputs=['scripts/repo/check-selection/checks.yml'])
        self.save()
        self.assertFalse(self.run_plan(checks=['aggregate', 'local'], execute=True)['findings'])
        self.catalog['checks']['local']['description'] = 'Changed child contract'
        self.save()
        report = self.run_plan(checks=['aggregate', 'local'], execute=True)
        self.assertEqual(set(report['execution_summary']['executed_check_ids']), {'aggregate', 'local'})
        self.assertFalse(report['findings'])


    def test_explicit_cli_is_mutually_exclusive_with_impact_modes(self):
        self.prepare_selector_cli()
        for mode in [['--paths', 'src/main.ts'], ['--staged'], ['--all'], ['--ci']]:
            result = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--checks', 'local', *mode],
                                    cwd=self.root, env=self.cli_environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


    def test_explicit_adoption_still_fingerprints_discovered_sources(self):
        (self.root / 'package.json').write_text('{"workspaces":[]}')
        relative = 'scripts/repo/diagnostic-coverage/script.py'
        target = self.root / relative
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / relative, target)
        (target.parent / 'reviews.v1.json').write_text('{"schema":"repo/diagnostic-adoption/v1","reviews":[]}')
        source = self.root / 'platform/new-service/src/call.ts'
        source.parent.mkdir(parents=True)
        source.write_text('export const value = 1;\n')
        self.catalog['checks']['diagnostic-adoption'] = copy.deepcopy(self.catalog['checks']['local'])
        self.save()
        report = self.run_plan(checks=['diagnostic-adoption'])
        self.assertFalse(report['findings'])
        self.assertIn('platform/new-service/src/call.ts', report['checks'][0]['references'])


    def test_ordinary_diagnostic_review_selects_registered_proof(self):
        (self.root / 'package.json').write_text('{"workspaces":[]}')
        relative = 'scripts/repo/diagnostic-coverage/script.py'
        destination = self.root / relative
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / relative, destination)
        (destination.parent / 'reviews.v1.json').write_text(json.dumps({'schema': 'repo/diagnostic-adoption/v1', 'reviews': [{
            'owner': 'fixture', 'status': 'support', 'reason': 'Fixture proof plumbing.',
            'sources': [{'path': 'ordinary-service.ts', 'sha256': 'a' * 64}], 'tests': ['proof.test.ts'], 'checks': ['local']}]}))
        (self.root / 'ordinary-service.ts').write_text('export const call = () => undefined;\n')
        (self.root / 'proof.test.ts').write_text('// synthetic proof\n')
        self.catalog['checks']['diagnostic-adoption'] = copy.deepcopy(self.catalog['checks']['local'])
        self.save()
        report = self.run_plan(paths=['ordinary-service.ts'])
        self.assertNotIn('changed-input-uncovered', self.codes(report))
        self.assertNotIn('diagnostic-adoption-selection-invalid', self.codes(report))
        self.assertIn('local', report['execution_summary']['selected_check_ids'])
        (destination.parent / 'reviews.v1.json').unlink()
        self.assertIn('diagnostic-adoption-selection-invalid', self.codes(self.run_plan(paths=['ordinary-service.ts'])))


    def test_protected_ci_invocation_defaults_to_required_integration(self):
        self.catalog['checks']['local']['boundary'] = 'integration'
        self.save()
        self.prepare_selector_cli()
        result = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--ci', '--execute-local', '--json'], cwd=self.root, env={**self.cli_environment, 'BASE_SHA': '', 'HEAD_SHA': ''}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['boundary'], 'integration')
        self.assertIn('local', report['execution_summary']['executed_check_ids'])
        self.assertFalse((self.root / 'operations').exists())


    def test_ci_catalog_only_change_selects_consumers_against_pr_base(self):
        self.prepare_selector_cli()
        def git(*argv):
            result = subprocess.run(['git', *argv], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Baseline')
        base = git('rev-parse', 'HEAD')
        self.catalog['checks']['local']['boundary'] = 'integration'
        self.save()
        git('add', str(self.catalog_path.relative_to(self.root)))
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Catalog contract only')
        head = git('rev-parse', 'HEAD')
        result = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--ci', '--execute-local', '--json'],
            cwd=self.root, env={**os.environ, 'BASE_SHA': base, 'HEAD_SHA': head}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual([item['path'] for item in report['changed_inputs']], ['scripts/repo/check-selection/checks.yml'])
        self.assertIn('local', report['execution_summary']['executed_check_ids'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertFalse((self.root / 'operations').exists())


    def test_ci_repository_only_contract_change_selects_only_changed_identity(self):
        # No scope can accidentally select the mapped command through a broad
        # fixture command directory; this is the independent repository route.
        shutil.rmtree(self.target.parent)
        (self.root / 'trigger.md').write_text('Unchanged selection input.\n')
        for name in ('mapped', 'sibling', 'catalog-check'):
            self.check_script(name, ['read-only', 'writes-files'], 'echo ' + name + ' >> ' + name + '-counts\n')
            self.catalog['checks'][name] = copy.deepcopy(self.catalog['checks']['local'])
            self.catalog['checks'][name]['argv'] = ['bash', 'scripts/' + name + '.sh']
            self.catalog['checks'][name]['inputs'] = ['trigger.md']
        self.catalog['repository_inputs'] = [
            {'inputs': ['trigger.md'], 'checks': ['mapped', 'sibling']},
            {'inputs': ['scripts/repo/check-selection/checks.yml'], 'checks': ['catalog-check']},
        ]
        write(self.catalog_path, self.catalog)
        self.prepare_selector_cli()
        def git(*argv):
            result = subprocess.run(['git', *argv], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Mapped baseline')
        base = git('rev-parse', 'HEAD')
        self.catalog['checks']['mapped']['boundary'] = 'integration'
        write(self.catalog_path, self.catalog)
        git('add', str(self.catalog_path.relative_to(self.root)))
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Mapped contract only')
        head = git('rev-parse', 'HEAD')
        def run(boundary):
            result = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--ci', '--boundary', boundary, '--execute-local', '--json'],
                cwd=self.root, env={**os.environ, 'BASE_SHA': base, 'HEAD_SHA': head}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        commit = run('commit')
        self.assertIn('mapped', commit['execution_summary']['deferred_check_ids'])
        self.assertNotIn('sibling', commit['execution_summary']['selected_check_ids'])
        self.assertFalse((self.root / 'mapped-counts').exists())
        integrated = run('integration')
        self.assertIn('mapped', integrated['execution_summary']['executed_check_ids'])
        self.assertNotIn('sibling', integrated['execution_summary']['selected_check_ids'])
        self.assertEqual((self.root / 'mapped-counts').read_text(), 'mapped\n')
        self.assertEqual(run('integration')['execution_summary']['executed_check_ids'], [])
        del self.catalog['checks']['mapped']
        write(self.catalog_path, self.catalog)
        git('add', str(self.catalog_path.relative_to(self.root)))
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Invalid removed obligation')
        rejected = subprocess.run(['bash', 'scripts/repo/check-selection/script.sh', '--ci', '--execute-local', '--json'],
            cwd=self.root, env={**os.environ, 'BASE_SHA': base, 'HEAD_SHA': git('rev-parse', 'HEAD')}, capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('required-check-missing', self.codes(json.loads(rejected.stdout)))
        self.assertEqual((self.root / 'mapped-counts').read_text(), 'mapped\n')


    def test_cli_unrelated_catalog_changes_reuse_full_selected_alias_definitions(self):
        self.catalog['checks']['alias'] = copy.deepcopy(self.catalog['checks']['local'])
        self.requirement['local_proofs'].append('alias')
        self.catalog['checks']['unrelated'] = copy.deepcopy(self.catalog['checks']['local'])
        self.save()
        # The catalog's metadata can put it back into upstream references; the
        # command directory also contains it. Neither is an explicit consumer.
        header = '# agentic-artifact:\n#   id: fixture.catalog\n#   used_by:\n#   - path: scripts/local.sh\n'
        self.catalog_path.write_text(header + self.catalog_path.read_text())
        self.prepare_selector_cli()
        first = self.local_command_result(self.run_selector_cli())
        self.assertEqual(set(first['catalog_entries']), {'local', 'alias'})
        self.assertFalse(first['catalog_input'])
        self.assertNotIn(self.catalog_path.relative_to(self.root).as_posix(), first['references'])
        for field, value in [('description', 'unrelated policy description'), ('effects', ['writes-files', 'read-only'])]:
            self.catalog['checks']['unrelated'][field] = value
            self.save(); self.catalog_path.write_text(header + self.catalog_path.read_text())
            reused = self.local_command_result(self.run_selector_cli())
            self.assertEqual(reused['evidence_key'], first['evidence_key'])
            self.assertEqual(reused['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.catalog['checks']['alias']['description'] = 'changed selected alias obligation'
        self.save(); self.catalog_path.write_text(header + self.catalog_path.read_text())
        changed = self.local_command_result(self.run_selector_cli())
        self.assertEqual(changed['evidence_source'], 'local-runner')
        self.assertNotEqual(changed['evidence_key'], first['evidence_key'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_cli_selected_catalog_fields_invalidate_or_block(self):
        self.prepare_selector_cli()
        first = self.local_command_result(self.run_selector_cli())
        for field, value in [('description', 'selected proof description'), ('argv', ['bash', 'scripts/local.sh', '--selected-option']), ('effects', ['writes-files', 'read-only']), ('runtime', {'tools': ['bash', 'python3'], 'environment': ['LANG', 'PYTHONPATH', 'SELECTOR_TEST_CONFIGURATION']})]:
            with self.subTest(field=field):
                self.catalog['checks']['local'][field] = value; self.save()
                result = self.local_command_result(self.run_selector_cli())
                self.assertEqual(result['evidence_source'], 'local-runner')
                self.assertNotEqual(result['evidence_key'], first['evidence_key'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 5)
        self.catalog['checks']['local']['applicability']['scope'] = 'another-scope'; self.save()
        report = self.run_selector_cli(expected=1)
        self.assertIn('requirement-check-subject-mismatch', self.codes(report))
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 5)


    def test_cli_explicit_catalog_consumers_keep_whole_file_identity(self):
        self.check_script('local', ['read-only', 'writes-files'], 'case "${1:-}" in --catalog=*) source="${1#--catalog=}";; --catalog) source="$2";; *) source="scripts/repo/check-selection/checks.yml";; esac\ncat "$source" >/dev/null\necho local >> counts\n')
        self.catalog['checks']['unrelated'] = copy.deepcopy(self.catalog['checks']['local'])
        self.save(); self.prepare_selector_cli()
        catalog_ref = self.catalog_path.relative_to(self.root).as_posix()
        original = copy.deepcopy(self.catalog['checks']['local'])
        modes = ('file-input', 'directory-input', 'runtime-config', 'argv', 'argv-assignment', 'argv-dot', 'argv-absolute', 'argv-assignment-dot', 'argv-assignment-absolute')
        for mode in modes:
            with self.subTest(mode=mode):
                check = copy.deepcopy(original)
                if mode == 'file-input': check['inputs'] = [catalog_ref]
                elif mode == 'directory-input': check['inputs'] = ['scripts/repo/check-selection']
                elif mode == 'runtime-config': check['runtime']['config_inputs'] = [catalog_ref]
                else:
                    spelling = str(self.catalog_path) if mode.endswith('absolute') else './' + catalog_ref if mode.endswith('dot') else catalog_ref
                    check['argv'] += ['--catalog=' + spelling] if 'assignment' in mode else ['--catalog', spelling]
                self.catalog['checks']['local'] = check; self.save()
                before = self.local_command_result(self.run_selector_cli())
                self.assertTrue(before['catalog_input'])
                self.assertIn(catalog_ref, before['references'])
                self.catalog['checks']['unrelated']['description'] = mode
                self.save()
                after = self.local_command_result(self.run_selector_cli())
                self.assertNotEqual(after['evidence_key'], before['evidence_key'])
                self.assertEqual(after['evidence_source'], 'local-runner')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * (2 * len(modes)))


    def test_cli_catalog_replanning_selects_new_repository_check(self):
        self.check_script('other', ['read-only', 'writes-files'], 'echo other >> other-counts\n')
        self.catalog['checks']['other'] = {**copy.deepcopy(self.catalog['checks']['local']), 'argv': ['bash', 'scripts/other.sh']}
        self.save(); self.prepare_selector_cli()
        self.run_selector_cli()
        self.catalog['repository_inputs'] = [{'inputs': ['src/main.ts'], 'checks': ['other']}]
        self.save()
        report = self.run_selector_cli()
        self.assertEqual(self.local_command_result(report)['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual(next(item for item in report['checks'] if item['check_id'] == 'other')['evidence_source'], 'local-runner')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertEqual((self.root / 'other-counts').read_text(), 'other\n')
        self.catalog['schema'] = 'unsupported/catalog'; self.save()
        self.assertIn('check-catalog-invalid', self.codes(self.run_selector_cli(expected=1)))
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_cli_catalog_mutation_blocks_invocation_but_preserves_unaffected_receipt(self):
        mutator = self.root / 'checks/mutator/script.sh'
        mutator.parent.mkdir(parents=True)
        mutator.write_text('#!/bin/bash\n# agentic-artifact:\n#   id: fixture.mutator\n#   effects: [read-only, writes-files]\nif [ ! -e catalog-edited ]; then\n  printf "\\n# changed during command\\n" >> scripts/repo/check-selection/checks.yml\n  touch catalog-edited\nfi\n')
        self.catalog['checks']['a-mutator'] = {**copy.deepcopy(self.catalog['checks']['local']), 'argv': ['bash', 'checks/mutator/script.sh']}
        self.save(); self.prepare_selector_cli()
        original = self.local_command_result(self.run_selector_cli())
        self.catalog['repository_inputs'] = [{'inputs': ['src/main.ts'], 'checks': ['a-mutator']}]
        self.save()
        report = self.run_selector_cli(expected=1)
        self.assertIn('check-catalog-changed-during-execution', self.codes(report))
        self.assertIn('check-catalog-changed-before-execution', self.codes(report))
        self.assertEqual(self.local_command_result(report)['status'], 'uncertain')
        mutator_result = next(item for item in report['checks'] if item['check_id'] == 'a-mutator')
        self.assertFalse((self.root / '.git/agentic-local-checks' / (mutator_result['evidence_key'] + '.json')).exists())
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        resumed = self.local_command_result(self.run_selector_cli())
        self.assertEqual(resumed['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual(resumed['evidence_key'], original['evidence_key'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_cli_unstaged_catalog_authority_blocks_even_unaffected_cached_proof(self):
        self.catalog['checks']['unrelated'] = copy.deepcopy(self.catalog['checks']['local'])
        self.save(); self.prepare_selector_cli()
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        self.run_selector_cli(staged=True)
        self.catalog['checks']['unrelated']['description'] = 'unstaged selection authority'
        self.save()
        report = self.run_selector_cli(expected=1, staged=True)
        self.assertIn({'code': 'selected-input-not-staged', 'path': self.catalog_path.relative_to(self.root).as_posix()}, report['findings'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        subprocess.run(['git', '-C', str(self.root), 'add', str(self.catalog_path)], check=True)
        report = self.run_selector_cli(staged=True)
        self.assertEqual(self.local_command_result(report)['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_target_without_scope_index_blocks_before_checks(self):
        (self.target / 'scope-index.yml').unlink()
        report = self.run_plan(execute=True)
        self.assertIn('scope-inventory-missing', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())
        self.assertFalse((self.root / 'operations').exists())


    def test_second_unindexed_target_cannot_hide_behind_valid_target(self):
        unindexed = self.root / 'infra/04.deploy/03.product/targets/another/20-scopes/worker/00-declaration'
        unindexed.mkdir(parents=True)
        (unindexed / 'declaration-contract.yml').write_text('schema: deploy/target-scope-contract/v1\n')
        report = self.run_plan(execute=True)
        self.assertIn('scope-inventory-missing', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())


    def test_synthetic_scope_reuses_existing_generic_validators_and_accepts_valid_na(self):
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual([scope['scope'] for scope in report['scopes']], ['synthetic-worker'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertEqual({item['check_id'] for item in report['checks'] if item['status'] == 'passed'}, {'local', 'scope-inventory', 'runnable-program'})
        self.assertEqual(self.contract['persistence_diagnostics']['status'], 'not-applicable')


    def test_openssl_runtime_identity_is_bounded_and_versioned(self):
        identity = local_cache.runtime_identity(self.root, {'tools': ['openssl'], 'environment': [], 'node_packages': []})
        self.assertIn('openssl', identity['tools'])
        self.assertTrue(identity['tools']['openssl']['version'])
        self.assertEqual(len(identity['tools']['openssl']['digest']), 64)


    def test_duplicate_commands_run_once(self):
        self.catalog['checks']['alias'] = copy.deepcopy(self.catalog['checks']['local'])
        self.requirement['local_proofs'].append('alias'); self.save()
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual(len(report['checks']), 6)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_dormant_impact_roots_do_not_expand_normal_dependency_proofs(self):
        dormant = self.root / 'dormant'; dormant.mkdir()
        (dormant / 'source.md').write_text('''<!-- agentic-artifact:
schema: agentic-artifact/v3
id: fixture.dormant-source
used_by:
- id: fixture.main
  path: src/main.ts
-->\n''')
        paths = [path.relative_to(self.root).as_posix() for path in self.root.rglob('*') if path.is_file()]
        active = selection.consumer_graph(self.root, paths)
        isolated = selection.consumer_graph(self.root, paths, ['dormant'])
        self.assertIn('src/main.ts', active.get('dormant/source.md', set()))
        self.assertNotIn('dormant/source.md', isolated)
        self.catalog['dormant_impact_roots'] = ['dormant']; self.save()
        self.assertEqual(self.run_plan()['verdict'], 'planned')


    def test_dormant_prose_does_not_activate_checks_but_code_and_definitions_do(self):
        docs = self.root / '.agentic/dormant'
        docs.mkdir(parents=True)
        guide = docs / 'guide.md'
        guide.write_text('Maintenance instructions.\n')
        self.check_script('dormant', ['read-only', 'writes-files'], 'echo dormant >> counts\n')
        self.catalog['dormant_impact_roots'] = ['.agentic/dormant', 'scripts/dormant.sh']
        # Roots are directories; put the actual command inside its owning root.
        scripts = self.root / 'scripts/dormant'
        scripts.mkdir()
        (self.root / 'scripts/dormant.sh').rename(scripts / 'check.sh')
        self.catalog['dormant_impact_roots'][1] = 'scripts/dormant'
        self.catalog['checks']['dormant'] = {
            **copy.deepcopy(self.catalog['checks']['local']),
            'argv': ['bash', 'scripts/dormant/check.sh'],
            'inputs': ['scripts/dormant'],
        }
        self.catalog['repository_inputs'] = [{
            'inputs': ['src', '.agentic/dormant', 'scripts/dormant'],
            'checks': ['dormant'],
        }]
        self.save()
        def selected(report):
            return {item['check_id'] for item in report['checks']}
        prose = self.run_plan(paths=['src/main.ts', '.agentic/dormant/guide.md'])
        self.assertFalse(prose['findings'], prose['findings'])
        self.assertNotIn('dormant', selected(prose))
        for kind in ('schema', 'contract', 'configuration', 'deployment-contract', 'script', 'gate'):
            guide.write_text('<!-- agentic-artifact:\nschema: agentic-artifact/v3\nkind: ' + kind + '\n-->\n')
            with self.subTest(kind=kind):
                self.assertIn('dormant', selected(self.run_plan(paths=['.agentic/dormant/guide.md'])))
        guide.write_text('Maintenance instructions.\n')
        self.assertIn('dormant', selected(self.run_plan(paths=['scripts/dormant/check.sh'])))
        self.assertIn('dormant', selected(self.run_plan(checks=['dormant'])))
        self.assertIn('dormant', selected(self.run_plan(all_inputs=True)))
        guide.unlink()
        self.assertIn('dormant', selected(self.run_plan(paths=['.agentic/dormant/guide.md'])))


    def test_duplicate_command_cannot_claim_conflicting_evidence_classes(self):
        self.catalog['checks']['alias'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['alias']['evidence_class'] = 'local-runtime'
        self.requirement['local_proofs'].append('alias'); self.save()
        self.assertIn('duplicate-check-contract-conflict', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())


    def test_failure_blocks_and_is_not_success_evidence(self):
        self.check_script('local', ['read-only', 'writes-files'], 'exit 7\n')
        report = self.run_plan(execute=True)
        self.assertIn('required-check-failed', self.codes(report))
        self.assertEqual(report['checks'][0]['status'], 'failed')


    def test_independent_local_checks_continue_after_a_failure(self):
        self.check_script('other', ['read-only', 'writes-files'], 'echo other >> counts\n')
        self.catalog['checks']['other'] = {**copy.deepcopy(self.catalog['checks']['local']), 'argv': ['bash', 'scripts/other.sh']}
        self.requirement['local_proofs'].append('other'); self.save()
        self.check_script('local', ['read-only', 'writes-files'], 'exit 7\n')
        report = self.run_plan(execute=True)
        self.assertIn('required-check-failed', self.codes(report))
        self.assertEqual((self.root / 'counts').read_text(), 'other\n')


    def test_missing_check_and_missing_source_fail_before_execution(self):
        (self.root / 'scripts/local.sh').unlink()
        report = self.run_plan(execute=True)
        self.assertIn('required-check-command-missing', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())
        (self.root / 'src/main.ts').unlink()
        self.assertIn('requirement-implementation-missing', self.codes(self.run_plan()))


    def test_unsupported_requirement_is_gap(self):
        self.requirement['local_proofs'].append('unimplemented-queue-delivery'); self.save()
        self.assertIn('requirement-check-unsupported', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())


    def test_na_requires_reason_and_cannot_hide_required_proof(self):
        self.requirement['not_applicable']['local_proofs'] = 'Skip required local work.'; self.save()
        self.assertIn('requirement-applicability-conflict', self.codes(self.run_plan()))
        self.auxiliary['not_applicable'].pop('target_proofs'); self.save()
        self.assertIn('requirement-proof-missing', self.codes(self.run_plan()))


    def test_prefix_boundaries_and_deleted_renamed_paths_are_reported(self):
        self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=['src-extra/file.ts'])))
        report = self.run_plan(staged=True)
        self.assertIn({'path': 'src/old.ts', 'state': 'deleted'}, report['changed_inputs'])
        self.assertIn({'path': 'src/main.ts', 'state': 'present'}, report['changed_inputs'])
        self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=['removed-package/index.ts'])))


    def test_session_stream_logs_are_evidence_without_exempting_source_or_scripts(self):
        paths = ['commitLogs/session/check.stderr', 'commitLogs/session/check.stdout']
        report = self.run_plan(paths=paths)
        self.assertEqual(report['verdict'], 'planned')
        self.assertEqual({item['path'] for item in report['non_applicable']}, set(paths))
        for path in ('src-extra/check.stderr', 'commitLogs/session/check.sh'):
            with self.subTest(path=path):
                self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=[path])))


    def test_skill_instruction_entry_is_prose_without_exempting_skill_executables(self):
        path = '.agents/skills/write-readme/SKILL.md'
        report = self.run_plan(paths=[path])
        self.assertEqual(report['verdict'], 'planned', report['findings'])
        self.assertEqual([item['path'] for item in report['non_applicable']], [path])
        for other in ('.agents/skills/write-readme/script.py', '.agents/skills/write-readme/SKILL.sh',
                      '.agents/skills/write-readme/scripts/SKILL.md', '.agents/other/SKILL.md'):
            with self.subTest(path=other):
                self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=[other])))
        artifact = self.root / path
        artifact.parent.mkdir(parents=True)
        artifact.write_text('<!-- agentic-artifact:\nid: fixture.contract\nkind: schema\n-->\n# Contract\n')
        self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=[path])))


    def test_effect_changes_and_wrong_stage_never_execute(self):
        self.catalog['checks']['local']['effects'] = ['network']; self.save()
        self.assertIn('check-effects-mismatch', self.codes(self.run_plan(execute=True)))
        self.catalog['checks']['local']['effects'] = ['aws-mutation']
        self.check_script('local', ['aws-mutation'], 'echo forbidden >> operations\n'); self.save()
        self.assertIn('local-check-effects-forbidden', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'operations').exists())
        self.catalog['checks']['local']['stage'] = 'deploy'; self.catalog['checks']['local']['evidence_class'] = 'live'; self.save()
        self.assertIn('requirement-proof-stage-invalid', self.codes(self.run_plan(execute=True)))


    def test_package_and_live_checks_stay_deferred_then_block_their_stage(self):
        self.requirement.update(package_proofs=['package'], target_proofs=['live'])
        self.requirement['not_applicable'].pop('package_proofs', None); self.requirement['not_applicable'].pop('target_proofs', None); self.save()
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual([item['status'] for item in report['checks']], ['passed', 'passed', 'passed', 'deferred', 'deferred', 'deferred'])
        for stage in ('package', 'deploy', 'acceptance'):
            report = self.run_plan(stage=stage, execute=True)
            self.assertIn('required-proof-owned-by-stage-controller', self.codes(report))
            self.assertFalse((self.root / 'operations').exists())


    def test_fresh_local_evidence_reused_but_stale_evidence_rejected(self):
        report = self.run_plan(execute=True)
        evidence = self.root / 'evidence.json'; evidence.write_text(json.dumps(report))
        reused = self.run_plan(execute=True, evidence=evidence)
        self.assertEqual(reused['verdict'], 'passed', reused)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        (self.root / 'src/main.ts').write_text('changed\n')
        stale = self.run_plan(stage='deploy', evidence=evidence)
        self.assertIn('required-proof-missing-or-stale', self.codes(stale))


    def test_metadata_and_workspace_consumers_are_discovered(self):
        (self.root / 'upstream').mkdir(); (self.root / 'upstream/package.json').write_text(json.dumps({'name': 'upstream'}))
        (self.root / 'src/package.json').write_text(json.dumps({'name': 'consumer', 'dependencies': {'upstream': '*'}}))
        (self.root / 'upstream/index.ts').write_text('export {};\n')
        report = self.run_plan(paths=['upstream/index.ts'])
        self.assertEqual(report['verdict'], 'planned', report)
        self.assertIn('src', report['affected_consumers'])
        self.assertEqual(len(report['scopes']), 1)


    def test_repository_input_rule_covers_inputs_before_gap_classification(self):
        self.catalog['repository_inputs'] = [{'inputs': ['consumer.ts'], 'checks': ['local']}]; self.save()
        # Remove the consumer from scope requirements to exercise only the repo rule.
        self.requirement['required_by'] = ['src/main.ts']; self.save()
        report = self.run_plan(paths=['consumer.ts'], execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_forged_external_report_cannot_qualify_stage(self):
        self.requirement['package_proofs'] = ['package']; self.requirement['not_applicable'].pop('package_proofs', None); self.save()
        report = self.run_plan(execute=True)
        for item in report['checks']: item['status'] = 'passed'
        evidence = self.root / 'evidence.json'; evidence.write_text(json.dumps(report))
        result = self.run_plan(stage='package', evidence=evidence)
        self.assertIn('required-proof-owned-by-stage-controller', self.codes(result))
        self.assertFalse((self.root / 'operations').exists())


    def test_command_content_argv_catalog_and_dependency_changes_invalidate_evidence(self):
        report = self.run_plan(execute=True)
        evidence = self.root / 'evidence.json'; evidence.write_text(json.dumps(report))
        for change in ('content', 'argv', 'catalog', 'dependency'):
            with self.subTest(change=change):
                if change == 'content': self.check_script('local', ['read-only', 'writes-files'], 'echo changed >> counts\n')
                elif change == 'argv': self.catalog['checks']['local']['argv'].append('--fixture-argument')
                elif change == 'catalog': self.catalog['checks']['local']['description'] = 'updated catalog proof description'
                else:
                    (self.root / 'additional-input').write_text('changed dependency')
                    self.catalog['checks']['local']['inputs'] = ['additional-input']
                self.save()
                self.assertIn('required-proof-missing-or-stale', self.codes(self.run_plan(stage='deploy', evidence=evidence)))
                current = self.run_plan(execute=True); evidence.write_text(json.dumps(current))


    def test_mandatory_scope_checks_cannot_be_removed_to_hide_broken_health(self):
        self.contract['health_recovery']['declaration_schema'] = 'unsupported-health-contract'
        self.requirement['local_proofs'].remove('scope-inventory'); self.save()
        report = self.run_plan(execute=True)
        self.assertIn('mandatory-scope-check-missing', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())
        self.requirement['local_proofs'].append('scope-inventory'); self.save()
        self.assertIn('required-check-failed', self.codes(self.run_plan(execute=True)))


    def test_transitive_package_source_changes_invalidate_cached_proof(self):
        (self.root / 'upstream').mkdir(); (self.root / 'upstream/package.json').write_text(json.dumps({'name': 'upstream'}))
        (self.root / 'src/package.json').write_text(json.dumps({'name': 'consumer', 'dependencies': {'upstream': '*'}}))
        source = self.root / 'upstream/index.ts'; source.write_text('initial\n')
        report = self.run_plan(paths=['upstream/index.ts'], execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        evidence = self.root / 'evidence.json'; evidence.write_text(json.dumps(report))
        source.write_text('changed\n')
        repeated = self.run_plan(paths=['upstream/index.ts'], execute=True, evidence=evidence)
        self.assertEqual(repeated['verdict'], 'passed', repeated)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_nested_input_symlink_cannot_reuse_evidence(self):
        report = self.run_plan(execute=True)
        evidence = self.root / 'evidence.json'; evidence.write_text(json.dumps(report))
        (self.root / 'src/link.ts').symlink_to(self.root / 'consumer.ts')
        result = self.run_plan(execute=True, evidence=evidence)
        self.assertIn('check-input-symlink-unsupported', self.codes(result))
        (self.root / 'consumer.ts').write_text('different target\n')
        self.assertIn('check-input-symlink-unsupported', self.codes(self.run_plan(execute=True, evidence=evidence)))
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_deployable_scope_cannot_erase_all_later_proof_with_na(self):
        for field in ('package_proofs', 'target_proofs', 'run_proofs'):
            self.requirement[field] = []
            self.requirement['not_applicable'][field] = 'Unjustified waiver.'
        self.save()
        report = self.run_plan(stage='acceptance', execute=True)
        self.assertIn('scope-stage-proof-missing', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())


    def test_scope_program_image_and_binding_identities_must_connect(self):
        self.contract['program']['id'] = 'unknown-program'; self.save()
        self.assertIn('scope-runnable-program-identity-mismatch', self.codes(self.run_plan()))
        self.contract['program']['id'] = 'generic-server'; self.save()
        image_path = self.root / 'image.yml'; image = yaml.safe_load(image_path.read_text())
        for field, wrong, code in (
            ('program_id', 'wrong-program', 'scope-image-program-identity-mismatch'),
            ('compiled_entrypoint', 'artifacts/wrong.js', 'scope-image-entrypoint-mismatch'),
            ('id', 'wrong-image', 'scope-image-contract-identity-mismatch'),
            ('command', ['artifacts/other.js'], 'scope-image-command-mismatch')):
            with self.subTest(field=field):
                invalid = copy.deepcopy(image); invalid[field] = wrong; write(image_path, invalid)
                self.assertIn(code, self.codes(self.run_plan()))
        write(image_path, image)
        program = yaml.safe_load((self.root / 'program.yml').read_text())
        program['runnable_programs'][0]['configuration_boundary'] = 'missing-config.ts'; write(self.root / 'program.yml', program)
        self.assertIn('scope-program-implementation-missing', self.codes(self.run_plan()))


    def test_malformed_proof_and_catalog_shapes_return_gaps(self):
        self.requirement['local_proofs'] = None; self.save()
        self.assertIn('requirement-proof-list-invalid', self.codes(self.run_plan()))
        self.requirement['local_proofs'] = ['local', 'scope-inventory', 'runnable-program']
        self.catalog['checks']['local']['inputs'] = 7; self.save()
        self.assertIn('check-input-contract-missing', self.codes(self.run_plan()))


    def test_malformed_program_shapes_return_structured_gaps(self):
        for malformed in (None, [], 'unsupported-program', {'contract': []}):
            with self.subTest(program=malformed):
                self.contract['program'] = malformed; self.save()
                report = self.run_plan(execute=True)
                self.assertEqual(report['verdict'], 'gap')
                self.assertIn('scope-program-reference-missing', self.codes(report))
                self.assertFalse((self.root / 'counts').exists())


    def test_catalog_owner_matches_command_artifact_identity(self):
        self.catalog['checks']['local']['owner'] = 'wrong-artifact-owner'; self.save()
        report = self.run_plan(execute=True)
        self.assertIn('check-owner-mismatch', self.codes(report))
        self.assertFalse((self.root / 'counts').exists())
        self.catalog['checks']['local']['owner'] = 'fixture.local'; self.save()
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')


    def test_wrong_subject_and_missing_program_integration_proof_are_gaps(self):
        for identity in ('local', 'package', 'live', 'acceptance'):
            with self.subTest(identity=identity):
                original = copy.deepcopy(self.catalog['checks'][identity]['applicability'])
                self.catalog['checks'][identity]['applicability']['program_id'] = 'different-program'; self.save()
                self.assertIn('requirement-check-subject-mismatch', self.codes(self.run_plan(execute=True)))
                self.catalog['checks'][identity]['applicability'] = original
        self.requirement['local_proofs'].remove('local')
        self.auxiliary['local_proofs'] = ['scope-inventory']; self.save()
        self.assertIn('scope-program-local-proof-missing', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())


    def test_generic_capability_requires_schema_and_consumed_context(self):
        self.catalog['checks']['package']['applicability'] = {'kind': 'generic', 'contract_schema': 'deploy/target-scope-contract/v1', 'context_parameters': ['scope_contract']}; self.save()
        self.assertIn('requirement-check-generic-contract-invalid', self.codes(self.run_plan()))
        check = self.catalog['checks']['package']; check['argv'].append('{scope_contract}'); self.save()
        self.assertIn('requirement-check-generic-capability-missing', self.codes(self.run_plan()))
        check['owner'] = 'fixture.package'; check['capability'] = 'scripts/package.capability.yml'
        write(self.root / check['capability'], {'schema': 'repo/check-capability/v1', 'owner': check['owner'], 'command': check['argv'][1], 'argv': check['argv'], 'contract_schema': 'deploy/target-scope-contract/v1', 'context_parameters': ['scope_contract']}); self.save()
        self.assertEqual(self.run_plan()['verdict'], 'planned')
        check['argv'].append('--unsupported-argument'); self.save()
        self.assertIn('requirement-check-generic-capability-mismatch', self.codes(self.run_plan()))


    def test_authoritative_schema_selects_transitive_consumers_and_invalidates_cache(self):
        schema = self.root / '.agentic/schemas/fixture.yml'; schema.parent.mkdir(parents=True)
        schema.write_text('# agentic-artifact:\n#   id: fixture.schema\n#   used_by: [{path: scripts/bridge.py}]\nschema: fixture/v1\n')
        bridge = self.root / 'scripts/bridge.py'
        bridge.write_text('# agentic-artifact:\n#   id: fixture.bridge\n#   used_by: [{path: scripts/local.sh}]\n')
        self.catalog['checks']['local']['inputs'].append('.agentic/schemas/fixture.yml')
        self.check_script('local', ['read-only', 'writes-files'], 'cat .agentic/schemas/fixture.yml >/dev/null\necho local >> counts\n')
        self.catalog['repository_inputs'] = [{'inputs': ['scripts/local.sh'], 'checks': ['local']}]; self.save()
        first = self.run_plan(paths=['.agentic/schemas/fixture.yml'], execute=True)
        self.assertEqual(first['verdict'], 'passed', first)
        self.assertTrue(first['checks'])
        self.assertFalse(first['non_applicable'])
        self.run_plan(paths=['.agentic/schemas/fixture.yml'], execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        schema.write_text(schema.read_text() + 'changed: true\n')
        self.run_plan(paths=['.agentic/schemas/fixture.yml'], execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_unmapped_authoritative_schema_is_gap_while_prose_is_proportionate(self):
        path = self.root / '.agentic/schemas/unowned.yml'; path.parent.mkdir(parents=True); path.write_text('schema: unknown/v1\n')
        self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=['.agentic/schemas/unowned.yml'])))
        report = self.run_plan(paths=['.agentic/standards/prose.md'])
        self.assertEqual(report['verdict'], 'planned', report)
        self.assertFalse(report['checks'])


    def test_cache_reuses_across_unrelated_revision_but_environment_invalidates(self):
        self.run_plan(execute=True)
        self.revision = 'b' * 40
        result = self.run_plan(execute=True)
        local = next(item for item in result['checks'] if item['check_id'] == 'local')
        self.assertEqual(local['evidence_source'], 'trusted-worktree-cache')
        self.assertEqual(local['executed_revision'], 'a' * 40)
        self.assertEqual(local['source_revision'], 'b' * 40)
        self.assertEqual(result['execution_summary']['reused_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
        with patch.dict(os.environ, {'LANG': 'C.fixture'}): self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_preparation_reuses_unchanged_proof_and_rejects_changed_inputs(self):
        prepared = self.run_plan(record_preparation=True)
        self.assertEqual(prepared['preparation_status'], 'recorded')
        verified = self.run_plan(execute=True)
        self.assertEqual(verified['execution_summary']['executed_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
        commit = self.run_plan(execute=True, staged=True, require_preparation=True)
        self.assertEqual(commit['preparation_status'], 'matched')
        self.assertEqual(commit['execution_summary']['reused_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        (self.root / 'src/main.ts').write_text('changed implementation\n')
        stale = self.run_plan(execute=True, staged=True, require_preparation=True)
        self.assertIn('verification-preparation-inputs-changed', self.codes(stale))


    def test_scope_explanation_preserves_unconsumed_runtime_and_contract_proof(self):
        self.run_plan(execute=True)
        self.requirement['purpose'] = 'An unrelated scope explanation changed.'
        self.save()
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report['findings'])
        self.assertEqual(report['execution_summary']['executed_check_ids'], ['scope-inventory'])
        self.assertEqual(report['execution_summary']['reused_check_ids'], ['local', 'runnable-program'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_mapping_triggers_do_not_enter_explicit_proof_inputs(self):
        (self.root / 'trigger.md').write_text('Selection only.\n')
        self.catalog['repository_inputs'] = [{'inputs': ['trigger.md'], 'checks': ['local']}]
        self.save()
        first = self.run_plan(paths=['trigger.md'], execute=True)
        self.assertEqual(first['verdict'], 'passed', first['findings'])
        (self.root / 'trigger.md').write_text('Another selection explanation.\n')
        second = self.run_plan(paths=['trigger.md'], execute=True)
        self.assertEqual(second['execution_summary']['executed_check_ids'], [])
        self.assertEqual(second['execution_summary']['reused_check_ids'], ['local'])
        (self.root / 'src/main.ts').write_text('A consumed source changed.\n')
        changed = self.run_plan(paths=['trigger.md'], execute=True)
        self.assertEqual(changed['execution_summary']['executed_check_ids'], ['local'])


    def test_commit_is_bounded_and_integration_reuses_final_proof_without_images(self):
        self.catalog['checks']['local']['boundary'] = 'integration'
        self.save()
        self.run_plan(record_preparation=True)
        commit = self.run_plan(execute=True, boundary='commit', staged=True, require_preparation=True)
        self.assertEqual(commit['verdict'], 'passed', commit['findings'])
        self.assertNotIn('local', commit['execution_summary']['executed_check_ids'])
        self.assertFalse((self.root / 'counts').exists())
        verified = self.run_plan(execute=True)
        self.assertEqual(verified['execution_summary']['executed_check_ids'], ['local'])
        commit = self.run_plan(execute=True, boundary='commit', staged=True, require_preparation=True)
        integrated = self.run_plan(execute=True)
        for report in (commit, integrated):
            self.assertEqual(report['verdict'], 'passed', report['findings'])
            self.assertEqual(report['execution_summary']['executed_check_ids'], [])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertFalse((self.root / 'operations').exists(), 'No image or provider operation may run locally.')


    def test_missing_explicit_inputs_and_invalid_scheduling_fail_closed(self):
        self.catalog['checks']['local'].pop('inputs')
        self.save()
        self.assertIn('check-input-contract-missing', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())
        self.catalog['checks']['local']['inputs'] = ['src']
        self.catalog['checks']['local']['boundary'] = 'anything'
        self.save()
        self.assertIn('check-boundary-invalid', self.codes(self.run_plan(execute=True)))


    def test_deferred_integration_runtime_is_not_qualified_at_commit(self):
        self.catalog['checks']['local']['boundary'] = 'integration'
        self.catalog['checks']['local']['runtime']['environment'].append('EXPENSIVE_FIXTURE')
        self.save()
        actual = selection.runtime_identity
        def bounded(root, declaration, **kwargs):
            if 'EXPENSIVE_FIXTURE' in declaration.get('environment', []):
                raise ValueError('fixture integration runtime unavailable')
            return actual(root, declaration, **kwargs)
        with patch.object(selection, 'runtime_identity', side_effect=bounded):
            self.assertEqual(self.run_plan(boundary='commit', record_preparation=True)['verdict'], 'planned')
            commit = self.run_plan(boundary='commit', staged=True, execute=True, require_preparation=True)
            self.assertEqual(commit['verdict'], 'passed', commit['findings'])
            self.assertIn('check-runtime-identity-unavailable', self.codes(self.run_plan(execute=True)))


    def test_later_command_cannot_revoke_an_earlier_pass_unnoticed(self):
        self.check_script('other', ['read-only', 'writes-files'], 'echo changed >> src/main.ts\n')
        self.catalog['checks']['z-mutator'] = {**copy.deepcopy(self.catalog['checks']['local']), 'argv': ['bash', 'scripts/other.sh'], 'inputs': ['consumer.ts']}
        self.requirement['local_proofs'].append('z-mutator')
        self.save()
        report = self.run_plan(execute=True)
        self.assertIn('check-input-changed-before-completion', self.codes(report))
        self.assertEqual(next(item for item in report['checks'] if item['check_id'] == 'local')['status'], 'uncertain')


    def test_registered_worktree_transfer_revalidates_inputs_and_rejects_other_repos(self):
        source_root, source_catalog = self.root, self.catalog_path
        subprocess.run(['git', '-C', str(source_root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(source_root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture source'], check=True)
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'integration'
            subprocess.run(['git', '-C', str(source_root), 'worktree', 'add', '--detach', '--quiet', str(destination)], check=True)
            try:
                self.root, self.catalog_path = destination, destination / source_catalog.relative_to(source_root)
                reused = self.run_plan(execute=True, reuse_from_worktree=source_root)
                self.assertEqual(reused['verdict'], 'passed', reused['findings'])
                self.assertEqual(reused['execution_summary']['executed_check_ids'], [])
                self.assertEqual(reused['execution_summary']['reused_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
                self.assertFalse((destination / 'counts').exists())
                (destination / 'src/main.ts').write_text('Resolved incoming changes.\n')
                changed = self.run_plan(execute=True, reuse_from_worktree=source_root)
                self.assertIn('local', changed['execution_summary']['executed_check_ids'])
                with patch.dict(os.environ, {'LANG': 'C.transfer-fixture'}):
                    runtime_changed = self.run_plan(execute=True, reuse_from_worktree=source_root)
                self.assertIn('local', runtime_changed['execution_summary']['executed_check_ids'])
                unregistered = source_root / 'not-a-worktree'
                unregistered.mkdir()
                rejected = self.run_plan(execute=True, reuse_from_worktree=unregistered)
                self.assertIn('reuse-worktree-unavailable', self.codes(rejected))
                foreign = Path(directory) / 'foreign'
                subprocess.run(['git', 'init', '--quiet', str(foreign)], check=True)
                rejected = self.run_plan(execute=True, reuse_from_worktree=foreign)
                self.assertIn('reuse-worktree-unavailable', self.codes(rejected))
                self.assertEqual(rejected['execution_summary']['executed_check_ids'], [])
            finally:
                self.root, self.catalog_path = source_root, source_catalog


    def test_receipt_with_changed_identity_fields_is_not_authority(self):
        report = self.run_plan(execute=True)
        item = next(item for item in report['checks'] if item['check_id'] == 'local')
        path = self.root / '.git/agentic-local-checks' / (item['evidence_key'] + '.json')
        value = json.loads(path.read_text())
        value['input_digest'] = 'forged-digest'
        path.write_text(json.dumps(value))
        rerun = self.run_plan(execute=True)
        self.assertIn('local', rerun['execution_summary']['executed_check_ids'])


    def test_actual_refresh_retains_verified_preflight_receipts(self):
        for relative in (
            'scripts/repo/check-selection/script.sh', 'scripts/repo/check-selection/script.py',
            'scripts/repo/check-selection/local_cache.py',
            'scripts/04.deploy/inventory-deploy-control/delivery_inventory.py',
            'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py',
            'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py',
            'scripts/01.harness/artifact-metadata/header_discovery.py',
            'scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh',
        ):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        (self.root / '.gitignore').write_text('counts\n')
        (self.root / 'package.json').write_text(json.dumps({'scripts': {'fixture:coverage': 'python3 scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'}}))
        def command(directory, *argv):
            result = subprocess.run(argv, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-4000:] + result.stderr[-4000:])
            return result.stdout
        command(self.root, 'git', 'add', '.')
        command(self.root, 'git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture baseline')
        if command(self.root, 'git', 'branch', '--show-current').strip() != 'main':
            command(self.root, 'git', 'branch', 'main')
        command(self.root, 'git', 'checkout', '-qb', 'chat/fixture')
        branch = 'agentic/preflight/chat-fixture/20261026000000'
        with tempfile.TemporaryDirectory() as temporary:
            preflight = Path(temporary) / 'preflight'
            command(self.root, 'git', 'worktree', 'add', '--quiet', '-b', branch, str(preflight))
            (preflight / 'src/main.ts').write_text('Resolved combined code.\n')
            command(preflight, 'git', 'add', 'src/main.ts')
            command(preflight, 'git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture refresh')
            verified = json.loads(command(preflight, 'bash', 'scripts/repo/check-selection/script.sh', '--paths', 'src/main.ts', '--execute-local', '--json'))
            self.assertEqual(verified['execution_summary']['executed_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
            output = command(self.root, 'bash', 'scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh', branch)
            applied = json.loads(next(line for line in output.splitlines() if line.startswith('{')))
            self.assertEqual(applied['execution_summary']['executed_check_ids'], [])
            self.assertEqual(applied['execution_summary']['reused_check_ids'], ['local', 'runnable-program', 'scope-inventory'])
            self.assertFalse(preflight.exists())
            self.assertFalse((self.root / 'counts').exists(), 'Refresh must not repeat the behavioral command.')
            self.assertFalse((self.root / 'operations').exists(), 'Refresh must not build images or invoke providers.')
            retained = json.loads(command(self.root, 'bash', 'scripts/repo/check-selection/script.sh', '--paths', 'src/main.ts', '--execute-local', '--json'))
            self.assertEqual(retained['execution_summary']['executed_check_ids'], [])


    def test_imported_report_cannot_qualify_local_check(self):
        planned = self.run_plan()
        for item in planned['checks']: item.update(status='passed', exit_code=0)
        evidence = self.root / 'imported.json'; evidence.write_text(json.dumps(planned))
        result = self.run_plan(execute=True, evidence=evidence)
        self.assertEqual(result['evidence_import_status'], 'rejected-untrusted-report')
        self.assertEqual(next(item for item in result['checks'] if item['check_id'] == 'local')['evidence_source'], 'local-runner')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')


    def test_pure_plan_probes_runtime_once_without_execution_revalidation(self):
        # A plan describes pending checks; it must not invent execution-race
        # findings by re-probing a toolchain when no command will be run.
        with patch.object(selection, 'runtime_identity', side_effect=lambda *_, **__: {'probe': probe.call_count}) as probe:
            report = self.run_plan()
        self.assertEqual(report['verdict'], 'planned', report)
        self.assertEqual(probe.call_count, 1)
        self.assertTrue(all(item['status'] == 'pending' for item in report['checks'] if item['stage'] == 'local'))
        self.assertFalse((self.root / 'counts').exists())
        self.assertFalse((self.root / '.git/agentic-local-checks').exists())


    def test_execution_still_revalidates_runtime_before_and_after_commands(self):
        with patch.object(selection, 'runtime_identity', side_effect=lambda *_, **__: {'probe': before.call_count}) as before:
            blocked = self.run_plan(execute=True)
        self.assertIn('check-input-changed-before-execution', self.codes(blocked))
        self.assertFalse((self.root / 'counts').exists())
        with patch.object(selection, 'runtime_identity', side_effect=lambda *_, **__: {'version': 'stable' if after.call_count <= 3 else 'changed'}) as after:
            uncertain = self.run_plan(execute=True)
        self.assertIn('check-input-changed-during-execution', self.codes(uncertain))
        local = next(item for item in uncertain['checks'] if item['check_id'] == 'local')
        self.assertEqual(local['status'], 'uncertain')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertFalse((self.root / '.git/agentic-local-checks' / (local['evidence_key'] + '.json')).exists())


    def test_receipt_only_checks_share_window_but_final_sweep_is_fresh(self):
        with patch.object(selection, 'runtime_identity', return_value={'version': 'stable'}):
            self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')
        with patch.object(selection, 'runtime_identity', return_value={'version': 'stable'}) as probes:
            reused = self.run_plan(execute=True)
        self.assertEqual(reused['verdict'], 'passed', reused['findings'])
        self.assertEqual(reused['execution_summary']['executed_check_ids'], [])
        self.assertEqual(probes.call_count, 3, 'planning, receipt-only window and independent final sweep')
        last_key = next(item['evidence_key'] for item in reused['checks'] if item['check_id'] == 'scope-inventory')
        original_read = selection.LocalCache.read
        version = 'stable'
        def read(cache, key):
            nonlocal version
            proof = original_read(cache, key)
            if key == last_key: version = 'changed'
            return proof
        with patch.object(selection, 'runtime_identity', side_effect=lambda *_, **__: {'version': version}), patch.object(selection.LocalCache, 'read', read):
            changed = self.run_plan(execute=True)
        self.assertEqual(changed['execution_summary']['executed_check_ids'], [])
        self.assertIn('check-input-changed-before-completion', self.codes(changed))


    def test_new_command_revalidates_prerequisites_after_receipt_reads(self):
        self.focused_fixture()
        self.assertEqual(self.run_plan(checks=['focus'], execute=True)['verdict'], 'passed')
        planned = self.run_plan(checks=['local'])
        key = next(item['evidence_key'] for item in planned['checks'] if item['check_id'] == 'local')
        original_read = selection.LocalCache.read
        def read(cache, current):
            proof = original_read(cache, current)
            if current == key: os.environ['LANG'] = 'fixture-runtime-changed-after-receipt'
            return proof
        with patch.dict(os.environ), patch.object(selection.LocalCache, 'read', read):
            changed = self.run_plan(checks=['local'], execute=True)
        self.assertIn('verification-prerequisite-not-passed', self.codes(changed))
        self.assertEqual(next(item for item in changed['checks'] if item['check_id'] == 'local')['status'], 'blocked')
        self.assertEqual((self.root / 'counts').read_text(), 'focus\n')


    def test_new_command_revalidates_own_inputs_after_receipt_reads(self):
        planned = self.run_plan()
        key = next(item['evidence_key'] for item in planned['checks'] if item['check_id'] == 'local')
        original_read = selection.LocalCache.read
        def read(cache, current):
            proof = original_read(cache, current)
            if current == key: (self.root / 'src/main.ts').write_text('changed after receipt lookup\n')
            return proof
        with patch.object(selection.LocalCache, 'read', read):
            changed = self.run_plan(execute=True)
        self.assertIn('check-input-changed-before-execution', self.codes(changed))
        self.assertEqual(next(item for item in changed['checks'] if item['check_id'] == 'local')['status'], 'uncertain')
        self.assertFalse((self.root / 'counts').exists())


    def test_closure_reuse_is_limited_to_one_immutable_plan_graph(self):
        self.catalog['repository_inputs'] = [
            {'inputs': ['src'], 'checks': ['local']},
            {'inputs': ['src/main.ts'], 'checks': ['local']},
        ]
        self.save()
        original = selection.closure
        calls = []
        def measured(inputs, graph):
            calls.append(frozenset(inputs))
            return original(inputs, graph)
        with patch.object(selection, 'closure', side_effect=measured):
            first = self.run_plan(paths=['src/main.ts'])
            self.assertEqual(len(calls), len(set(calls)))
            first_calls = len(calls)
            # A second invocation must read a changed graph, even for the same
            # changed path and check catalog. No process-global closure cache.
            graph = {'src': {'new-consumer'}}
            with patch.object(selection, 'consumer_graph', return_value=graph):
                second = self.run_plan(paths=['src/main.ts'])
        self.assertGreater(len(calls), first_calls)
        self.assertNotIn('new-consumer', first['affected_consumers'])
        self.assertIn('new-consumer', second['affected_consumers'])


    def test_mutation_during_check_is_uncertain_and_not_cached(self):
        self.check_script('local', ['read-only', 'writes-files'], 'echo changed >> src/main.ts\necho local >> counts\n')
        for _ in range(2):
            result = self.run_plan(execute=True)
            self.assertIn('check-input-changed-during-execution', self.codes(result))
            self.assertEqual(next(item for item in result['checks'] if item['check_id'] == 'local')['status'], 'uncertain')
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_cache_symlink_and_unsafe_permissions_fail_closed(self):
        private = self.root / '.git/agentic-local-checks'
        outside = self.root / 'outside'; outside.mkdir()
        private.symlink_to(outside, target_is_directory=True)
        report = self.run_plan(execute=True)
        self.assertIn({'code': 'local-cache-unavailable', 'detail': 'local-cache-symlink-forbidden'}, report['findings'])
        private.unlink(); private.mkdir(mode=0o755)
        report = self.run_plan(execute=True)
        self.assertIn({'code': 'local-cache-unavailable', 'detail': 'local-cache-permissions-invalid'}, report['findings'])
        self.assertFalse((self.root / 'counts').exists())


    def test_real_repository_hook_reuses_local_evidence_without_report_argument(self):
        # Actual source-owned hook, selector, and cache run in an isolated Git
        # worktree. The unrelated revision is simulated without creating commits.
        for relative in ('scripts/repo/commit-gates/script.sh', 'scripts/repo/check-selection/script.sh', 'scripts/repo/check-selection/script.py', 'scripts/repo/check-selection/local_cache.py', 'scripts/04.deploy/inventory-deploy-control/delivery_inventory.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py', 'scripts/01.harness/artifact-metadata/header_discovery.py'):
            target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / relative, target)
        (self.root / 'package.json').write_text(json.dumps({'scripts': {'fixture:coverage': 'python3 scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'}}))
        gate = self.root / 'scripts/01.harness/artifact-metadata/generate-index/script.sh'; gate.parent.mkdir(parents=True); gate.write_text('#!/bin/bash\nexit 0\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        # Stage only the source subject: definition setup is fixture baseline.
        shim = self.root / 'bin'; shim.mkdir()
        git = shutil.which('git'); revision = self.root / 'revision'; revision.write_text('a' * 40)
        (shim / 'git').write_text('#!/bin/bash\ncase "$*" in *"rev-parse HEAD"*) cat "' + str(revision) + '";; *"diff --cached --name-only --no-renames -z"*) printf "src/main.ts\\0";; *) exec "' + str(git) + '" "$@";; esac\n')
        (shim / 'git').chmod(0o755)
        environment = {**os.environ, 'PATH': str(shim) + ':' + os.environ['PATH']}
        def prepare():
            result = subprocess.run(
                ['bash', 'scripts/repo/check-selection/script.sh', '--staged', '--record-preparation', '--json'],
                cwd=self.root,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        def invoke():
            result = subprocess.run(['bash', 'scripts/repo/commit-gates/script.sh'], cwd=self.root, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{')))
        # Commit gates require a recorded pre-verification selection. The
        # source revision is deliberately not part of the reusable local-proof
        # identity, so an unrelated revision change may still reuse it.
        prepare()
        first = invoke(); revision.write_text('b' * 40); second = invoke()
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertTrue(Path(second['local_report_path']).is_file())
        self.assertTrue(all(item['evidence_source'] == 'trusted-worktree-cache' for item in second['checks'] if item['stage'] == 'local'))
        (self.root / 'unrelated-not-staged.txt').write_text('unrelated local work\n'); invoke()
        (self.root / 'src/main.ts').write_text('changed\n')
        blocked = subprocess.run(['bash', 'scripts/repo/commit-gates/script.sh'], cwd=self.root, env=environment, capture_output=True, text=True)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn('selected-input-not-staged', blocked.stdout)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'src/main.ts'], check=True)
        unfinished = subprocess.run(['bash', 'scripts/repo/commit-gates/script.sh'], cwd=self.root, env=environment, capture_output=True, text=True)
        self.assertNotEqual(unfinished.returncode, 0)
        self.assertIn('verification-preparation-inputs-changed', unfinished.stdout)
        prepare()
        invoke()
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_failed_incomplete_or_nonzero_cache_receipts_are_never_reused(self):
        first = self.run_plan(execute=True)
        item = next(item for item in first['checks'] if item['check_id'] == 'local')
        cached = self.root / '.git/agentic-local-checks' / (item['evidence_key'] + '.json')
        for update in ({'status': 'failed'}, {'status': 'pending'}, {'exit_code': 9}):
            value = json.loads(cached.read_text()); value.update(update); cached.write_text(json.dumps(value))
            result = self.run_plan(execute=True)
            self.assertEqual(next(item for item in result['checks'] if item['check_id'] == 'local')['evidence_source'], 'local-runner')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 4)


    def test_executable_mode_and_toolchain_identity_invalidate_cache(self):
        self.run_plan(execute=True)
        (self.root / 'scripts/local.sh').chmod(0o644)
        result = self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')
        original = selection.runtime_identity
        def changed_runtime(root, declaration, **kwargs): return {**original(root, declaration, **kwargs), 'fixture_tool_version': 'changed'}
        with patch.object(selection, 'runtime_identity', side_effect=changed_runtime): self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\nlocal\n')


    def test_markdown_authoritative_schema_is_not_exempt_as_prose(self):
        path = self.root / '.agentic/schemas/contract.md'; path.parent.mkdir(parents=True)
        path.write_text('<!-- agentic-artifact:\nid: fixture.contract\nkind: schema\n-->\n# Contract\n')
        self.assertIn('changed-input-uncovered', self.codes(self.run_plan(paths=['.agentic/schemas/contract.md'])))


    def test_catalogued_acceptance_route_cannot_be_removed_from_scope(self):
        self.catalog['checks']['acceptance']['acceptance_route'] = 'route.yml'; self.save()
        result = self.run_plan(execute=True)
        self.assertIn('acceptance-check-route-mismatch', self.codes(result))
        self.assertFalse((self.root / 'counts').exists())


    def test_declared_optional_runtime_configuration_invalidates_when_created(self):
        self.catalog['checks']['local']['runtime']['config_inputs'] = ['local-toolchain.conf']; self.save()
        self.run_plan(execute=True)
        (self.root / 'local-toolchain.conf').write_text('compiler-option=changed\n')
        result = self.run_plan(paths=['local-toolchain.conf'], execute=True)
        self.assertEqual(result['verdict'], 'passed', result)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')


    def test_selector_control_changes_cannot_hide_behind_removed_mapping(self):
        self.catalog['repository_inputs'] = []; self.save()
        shutil.rmtree(self.target)  # No arbitrary fixture scripts directory can claim the control input.
        result = self.run_plan(paths=['scripts/repo/check-selection/script.py'])
        self.assertIn('changed-input-uncovered', self.codes(result))


    def test_mandatory_generic_checks_cannot_be_replaced_by_fixed_program_proof(self):
        self.catalog['checks']['scope-inventory'] = copy.deepcopy(self.catalog['checks']['local']); self.save()
        self.assertIn('mandatory-scope-check-capability-invalid', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())


    def test_node_installation_bytes_modes_rename_and_removal_invalidate(self):
        package = self.node_package('pg'); self.node_check(['pg'])
        lock = self.root / 'package-lock.json'; lock.write_text('{"lockfileVersion":3}\n')
        self.check_script('local', ['read-only', 'writes-files'], 'test -f node_modules/pg/index.js || exit 9\necho local >> counts\n')
        first = self.run_plan(execute=True); self.assertEqual(first['verdict'], 'passed', first)
        reused = self.run_plan(execute=True)
        self.assertEqual(next(item for item in reused['checks'] if item['check_id'] == 'local')['evidence_source'], 'trusted-worktree-cache')
        (package / 'index.js').write_text('module.exports = {changed:true};\n'); self.run_plan(execute=True)
        (package / 'index.js').chmod(0o755); self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 3)
        (package / 'index.js').rename(package / 'renamed.js')
        missing = self.run_plan(execute=True)
        self.assertIn('required-check-failed', self.codes(missing))
        self.assertEqual(next(item for item in missing['checks'] if item['check_id'] == 'local')['exit_code'], 9)
        shutil.rmtree(package)
        self.assertIn('check-runtime-identity-unavailable', self.codes(self.run_plan(execute=True)))
        self.assertEqual(lock.read_text(), '{"lockfileVersion":3}\n')


    def test_node_transitive_types_and_optional_installation_are_inputs(self):
        self.node_package('pg', dependencies={'pg-protocol': '*'}, optional={'pg-native': '*'})
        protocol = self.node_package('pg-protocol')
        self.node_package('@types/node', dependencies={'undici-types': '*'})
        types = self.node_package('undici-types')
        self.node_check(['pg', '@types/node'])
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')
        (types / 'index.js').write_text('changed declaration bytes\n'); self.run_plan(execute=True)
        (protocol / 'index.js').write_text('changed transitive protocol\n'); self.run_plan(execute=True)
        self.node_package('pg-native'); self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 4)
        shutil.rmtree(protocol)
        self.assertIn('check-runtime-identity-unavailable', self.codes(self.run_plan(execute=True)))


    def test_node_workspace_links_track_target_and_reject_escape(self):
        first = self.node_package('fixture-workspace', path=self.root / 'packages/first')
        second = self.node_package('fixture-workspace', path=self.root / 'packages/second')
        link = self.root / 'node_modules/fixture-workspace'; link.parent.mkdir(); link.symlink_to(first, target_is_directory=True)
        self.node_check(['fixture-workspace'])
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')
        (first / 'index.js').write_text('changed workspace content\n'); self.run_plan(execute=True)
        link.unlink(); link.symlink_to(second, target_is_directory=True); self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 3)
        with tempfile.TemporaryDirectory() as outside:
            escaped = self.node_package('fixture-workspace', path=Path(outside))
            link.unlink(); link.symlink_to(escaped, target_is_directory=True)
            self.assertIn('check-runtime-identity-unavailable', self.codes(self.run_plan(execute=True)))
        self.assertEqual((self.root / 'counts').read_text(), 'local\n' * 3)


    def test_python_package_identity_includes_paths_modes_and_bytes(self):
        package = self.root / 'fixture-yaml'; package.mkdir(); source = package / 'one.py'; source.write_text('same bytes\n')
        first = local_cache.tool_package_identity(package)
        source.rename(package / 'two.py'); source = package / 'two.py'
        renamed = local_cache.tool_package_identity(package); self.assertNotEqual(first, renamed)
        source.chmod(0o755); changed_mode = local_cache.tool_package_identity(package); self.assertNotEqual(renamed, changed_mode)
        source.write_text('new bytes!\n'); self.assertNotEqual(changed_mode, local_cache.tool_package_identity(package))


    def test_runtime_window_shares_components_not_declaration_identity(self):
        common = self.node_package('common')
        self.node_package('first', dependencies={'common': '*'})
        self.node_package('second', dependencies={'common': '*'})
        declarations = [
            {'tools': ['bash', 'node'], 'node_packages': ['first'], 'environment': []},
            {'tools': ['bash', 'node'], 'node_packages': ['second'], 'environment': ['FIXTURE_VALUE']},
        ]
        expected = [local_cache.runtime_identity(self.root, declaration) for declaration in declarations]
        reads = []
        read_bytes = Path.read_bytes
        def observed(path):
            reads.append(path)
            return read_bytes(path)
        window = local_cache.RuntimeIdentityWindow(self.root)
        with patch.object(Path, 'read_bytes', observed), patch.object(local_cache.subprocess, 'run', wraps=subprocess.run) as probes:
            actual = [local_cache.runtime_identity(self.root, declaration, window=window) for declaration in declarations]
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual[0]['node_installation'], actual[1]['node_installation'])
        self.assertEqual(reads.count(common / 'index.js'), 1)
        self.assertEqual(probes.call_count, 2, 'shared bash and node are probed only once')
        actual[0]['tools']['bash']['version'] = 'caller mutation'
        self.assertEqual(local_cache.runtime_identity(self.root, declarations[0], window=window), expected[0])
        self.assertGreater(window.node_tree_bytes, 0)
        window.clear()
        self.assertEqual(window.node_tree_bytes, 0)
        self.assertFalse(window.node_trees)
        self.assertFalse(window.tools)
        self.assertEqual(local_cache.runtime_identity(self.root, declarations[0], window=window), expected[0])


    def test_runtime_window_reset_rechecks_same_timestamp_content_and_links(self):
        package = self.node_package('fixture-workspace', path=self.root / 'packages/first')
        other = self.node_package('fixture-workspace', path=self.root / 'packages/second')
        link = self.root / 'node_modules/fixture-workspace'
        link.parent.mkdir(); link.symlink_to(package, target_is_directory=True)
        source = package / 'index.js'
        window = local_cache.RuntimeIdentityWindow(self.root)
        def identify():
            return local_cache.node_installation_identity(self.root, ['fixture-workspace'], window=window)
        initial = identify()
        info = source.stat()
        content = source.read_bytes()
        source.write_bytes(b'x' * len(content))
        os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns))
        self.assertEqual(source.stat().st_size, info.st_size)
        self.assertEqual(source.stat().st_mtime_ns, info.st_mtime_ns)
        window.clear()
        changed = identify()
        self.assertNotEqual(initial, changed)
        source.chmod(0o755); window.clear()
        self.assertNotEqual(changed, identify())
        link.unlink(); link.symlink_to(other, target_is_directory=True); window.clear()
        self.assertEqual(identify(), local_cache.node_installation_identity(self.root, ['fixture-workspace']))
        with self.assertRaisesRegex(ValueError, 'window-root-mismatch'):
            local_cache.node_installation_identity(package, [], window=window)


    def test_runtime_window_keys_tool_probe_environment_and_python_component(self):
        window = local_cache.RuntimeIdentityWindow(self.root)
        declaration = {'tools': ['python3'], 'environment': ['FIXTURE_VALUE']}
        expected = local_cache.runtime_identity(self.root, declaration)
        with patch.object(local_cache.subprocess, 'run', wraps=subprocess.run) as probes, patch.object(local_cache, 'tool_package_identity', wraps=local_cache.tool_package_identity) as package:
            self.assertEqual(local_cache.runtime_identity(self.root, declaration, window=window), expected)
            self.assertEqual(local_cache.runtime_identity(self.root, declaration, window=window), expected)
            self.assertEqual(package.call_count, 1)
            self.assertEqual(probes.call_count, 2)
            with patch.dict(os.environ, {'FIXTURE_VALUE': 'different probe context'}):
                changed = local_cache.runtime_identity(self.root, declaration, window=window)
            self.assertNotEqual(changed['environment'], expected['environment'])
            self.assertEqual(probes.call_count, 4)
            window.clear()
            local_cache.runtime_identity(self.root, declaration, window=window)
            self.assertEqual(package.call_count, 3)


    def test_runtime_window_content_budget_falls_back_without_changing_identity(self):
        self.node_package('fixture-package')
        expected = local_cache.node_installation_identity(self.root, ['fixture-package'])
        window = local_cache.RuntimeIdentityWindow(self.root)
        window.node_tree_bytes = 128 * 1024 * 1024
        self.assertEqual(local_cache.node_installation_identity(self.root, ['fixture-package'], window=window), expected)
        self.assertFalse(window.node_trees)


    def test_runtime_window_reset_rechecks_tool_bytes_modes_and_link_target(self):
        directory = self.root / 'fixture-tools'; directory.mkdir()
        first = directory / 'first'
        first.write_text('#!/bin/sh\nprintf "stable-version\\n"\n# a\n'); first.chmod(0o755)
        second = directory / 'second'
        second.write_bytes(first.read_bytes()); second.chmod(0o755)
        executable = directory / 'bash'; executable.symlink_to(first)
        window = local_cache.RuntimeIdentityWindow(self.root)
        declaration = {'tools': ['bash'], 'environment': ['PATH']}
        with patch.dict(os.environ, {'PATH': str(directory)}):
            def identify():
                return local_cache.runtime_identity(self.root, declaration, window=window)
            original = identify()
            info = first.stat()
            first.write_bytes(first.read_bytes().replace(b'# a', b'# b'))
            os.utime(first, ns=(info.st_atime_ns, info.st_mtime_ns))
            self.assertEqual(first.stat().st_size, info.st_size)
            self.assertEqual(first.stat().st_mtime_ns, info.st_mtime_ns)
            window.clear(); content = identify()
            self.assertEqual(original['tools']['bash']['version'], content['tools']['bash']['version'])
            self.assertNotEqual(original, content)
            first.chmod(0o700); window.clear(); mode = identify()
            self.assertNotEqual(content, mode)
            executable.unlink(); executable.symlink_to(second); window.clear()
            self.assertNotEqual(mode, identify())


    def test_node_checks_require_explicit_installation_declaration(self):
        self.catalog['checks']['local']['runtime']['tools'].append('node'); self.save()
        self.assertIn('check-runtime-node-installation-invalid', self.codes(self.run_plan(execute=True)))
        self.catalog['checks']['local']['runtime']['node_packages'] = []; self.save()
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')


    def test_shell_strings_and_outside_paths_are_refused(self):
        self.catalog['checks']['local']['argv'] = ['bash', 'scripts/local.sh; echo unsafe']; self.save()
        self.assertIn('check-argv-invalid', self.codes(self.run_plan(execute=True)))
        self.assertIn('changed-path-invalid', self.codes(self.run_plan(paths=['../outside'])))



    def test_split_component_receipt_is_independent_and_aggregate_reuses_it(self):
        # Exercise the real default aggregate dispatch with cheap fixture children.
        # Actual repository membership and input ownership are proved separately.
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        aggregate_id = 'check-selection-regression'
        members = catalog[aggregate_id]['members']
        wrapper = self.root / 'scripts/repo/check-selection/smoke-test.sh'
        shutil.copyfile(ROOT / 'scripts/repo/check-selection/smoke-test.sh', wrapper)
        # Keep the exact default branch; replace only component work with bounded
        # counters. This fixture cannot recursively launch the actual test suite.
        text = wrapper.read_text()
        text = text[:text.index('case "$2" in')] + 'printf "%s\\n" "$2" >> counts\n'
        wrapper.write_text(text)
        selector = ROOT / 'scripts/repo/check-selection/script.py'
        bridge = self.root / 'scripts/repo/check-selection/script.sh'
        bridge.write_text('exec python3 -B "' + str(selector) + '" --root "$PWD" --catalog "' + str(self.catalog_path) + '" "$@"\n')
        base = copy.deepcopy(self.catalog['checks']['local'])
        for identity in [*members, aggregate_id]:
            self.catalog['checks'][identity] = copy.deepcopy(base)
            self.catalog['checks'][identity].update(argv=catalog[identity]['argv'], inputs=['scripts/repo/check-selection/smoke-test.sh'], owner='repo.test.check-selection.wrapper', scope_inputs=False)
        self.catalog['checks'][aggregate_id].update(members=members, aggregate_branch='default')
        self.catalog['repository_inputs'] = [{'inputs': ['src'], 'checks': [aggregate_id]}]
        self.save()
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'fixture baseline'], check=True)
        unit = 'check-selection-mechanics'
        first = self.run_plan(checks=[unit], execute=True)
        self.assertFalse(first['findings'], first['findings'])
        (self.root / 'unrelated-runtime.ts').write_text('unrelated body change\n')
        unchanged = self.run_plan(checks=[unit], execute=True)
        self.assertEqual(unchanged['execution_summary']['reused_check_ids'], [unit])
        prepared = self.run_plan(paths=['src/main.ts'], record_preparation=True)
        self.assertFalse(prepared['findings'], prepared['findings'])
        combined = self.run_plan(checks=[aggregate_id], task_paths=['src/main.ts'], execute=True)
        self.assertFalse(combined['findings'], combined['findings'])
        self.assertEqual(combined['execution_summary']['reused_check_ids'], [unit])
        item = next(item for item in combined['checks'] if item['check_id'] == aggregate_id)
        self.assertEqual(set(item['nested_execution_summary']['reused_check_ids']), set(members))
        self.assertEqual(item['nested_execution_summary']['executed_check_ids'], [])
        self.assertEqual(len((self.root / 'counts').read_text().splitlines()), len(members))
        self.catalog['checks'][unit]['description'] = 'Changed relevant child contract'
        self.save()
        stale = self.run_plan(checks=[aggregate_id], task_paths=['src/main.ts'], execute=True)
        self.assertIn('verification-task-context-stale', self.codes(stale))
        self.assertFalse(self.run_plan(paths=['src/main.ts'], record_preparation=True)['findings'])
        changed = self.run_plan(checks=[aggregate_id], task_paths=['src/main.ts'], execute=True)
        self.assertFalse(changed['findings'], changed['findings'])
        self.assertEqual(set(changed['execution_summary']['executed_check_ids']), {unit, aggregate_id})
        self.assertEqual(len((self.root / 'counts').read_text().splitlines()), len(members) + 1)
        # A failed real child dispatch cannot produce a passing aggregate receipt.
        wrapper.write_text(wrapper.read_text().replace('printf "%s\\n" "$2" >> counts', 'if [ "$2" = "mechanics" ]; then exit 7; fi\nprintf "%s\\n" "$2" >> counts'))
        self.assertFalse(self.run_plan(paths=['src/main.ts'], record_preparation=True)['findings'])
        failed = self.run_plan(checks=[aggregate_id], task_paths=['src/main.ts'], execute=True)
        self.assertIn('required-check-failed', self.codes(failed))
        self.assertIn('verification-prerequisite-not-passed', self.codes(failed))
        self.assertNotEqual(next(item for item in failed['checks'] if item['check_id'] == aggregate_id)['status'], 'passed')

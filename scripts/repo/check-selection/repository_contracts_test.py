#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.repository-contracts
#   version: 7
#   status: active
#   created_on: "2026-10-29"
#   updated_on: "2026-11-09"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: test
#   purpose: Prove actual repository verification ownership and executable catalog contracts.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh
from __future__ import annotations
from test_support import *


class RepositoryContractTests(unittest.TestCase):
    def codes(self, report): return {item["code"] for item in report["findings"]}

    def test_feature_catalog_inputs_invalidate_actual_fingerprints(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for identity in ('diagnostic-catalog-readers', 'diagnostic-runtime-contracts'):
            with self.subTest(check=identity), tempfile.TemporaryDirectory(prefix='feature-catalog-inputs-') as directory:
                root = Path(directory)
                source = root / 'apps/entity-smoke/features/test-entity/contract/diagnostics.ts'
                export = root / 'apps/entity-smoke/contracts/diagnostics.v1.json'
                source.parent.mkdir(parents=True); source.write_text('fixture source v1\n')
                export.parent.mkdir(parents=True); export.write_text('{"fixture":1}\n')
                inputs = set(checks[identity]['inputs'])
                before = selection.fingerprint(root, inputs)
                source.write_text('fixture source v2\n')
                changed_source = selection.fingerprint(root, inputs)
                self.assertNotEqual(before, changed_source, 'consumed feature source must invalidate catalog proof')
                export.write_text('{"fixture":2}\n')
                changed_export = selection.fingerprint(root, inputs)
                self.assertNotEqual(changed_source, changed_export, 'feature export must invalidate catalog proof')
                (root / 'unrelated.txt').write_text('unrelated fixture input\n')
                self.assertEqual(changed_export, selection.fingerprint(root, inputs))
                omitted = inputs - {'apps/entity-smoke'}
                missing_before = selection.fingerprint(root, omitted)
                source.write_text('fixture source v3\n')
                self.assertEqual(missing_before, selection.fingerprint(root, omitted), 'counterexample reproduces omitted-root cache identity')
                self.assertIn('@kanbien/app-entity-smoke', checks[identity]['runtime']['node_packages'])

    def test_feedback_pilot_binds_real_owners_without_reclassifying_existing_gates(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        for identity, check in checks.items():
            self.assertEqual(selection.execution_policy.validate_feedback(identity, check), [], identity)
        feature = checks['entity-smoke-runtime']
        self.assertEqual(feature['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'entity-smoke'])
        self.assertEqual(feature['boundary'], 'integration')
        self.assertEqual(feature['effects'], ['writes-files'])
        self.assertTrue(feature['feedback']['development'])
        self.assertIn('apps/entity-smoke', feature['inputs'])
        self.assertIn('packages/core', feature['inputs'])
        self.assertIn('platform/contracts', feature['inputs'])
        self.assertIn('packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture.ts', feature['inputs'])
        scripts = json.loads((ROOT / 'package.json').read_text())['scripts']
        self.assertEqual(scripts['app:entity-smoke:check'], 'npm run app:entity-smoke:typecheck && npm run app:entity-smoke:test')
        self.assertIn('tsc -p apps/entity-smoke/tsconfig.check.json', scripts['app:entity-smoke:typecheck'])
        self.assertIn('node apps/entity-smoke/tests/run-runtime-tests.mjs', scripts['app:entity-smoke:test'])
        self.assertTrue(checks['dynamodb-persistence-runtime']['feedback']['development'])
        self.assertTrue(checks['postgresql-connection-diagnostics']['feedback']['development'])
        for identity in ('platform-server-runtime', 'kanbien-platform-runtime', 'platform-shell-payload',
                         'check-selection-mechanics', 'check-selection-repository-contracts'):
            self.assertFalse(checks[identity]['feedback']['development'], identity)
            self.assertEqual(checks[identity]['boundary'], 'integration', identity)
        self.assertTrue(checks['diagnostic-runtime-contracts']['focused_prerequisites'])
        self.assertIn('platform-server-runtime', checks['diagnostic-runtime-contracts']['members'])
        self.assertIn('kanbien-platform-runtime', checks['diagnostic-runtime-contracts']['members'])
        self.assertNotIn('feedback', checks['core-runtime'])

    def test_migrated_runner_units_bind_shared_fixture_changes(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        fixture = 'packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture.ts'
        identities = ('core-runtime', 'platform-contracts-runtime', 'platform-config-runtime',
                      'platform-health-runtime', 'platform-observability-runtime',
                      'platform-persistence-runtime', 'platform-runtime-runtime',
                      'platform-security-runtime', 'platform-testing-runtime',
                      'platform-workers-runtime', 'platform-server-runtime',
                      'platform-smoke-runtime', 'kanbien-platform-runtime',
                      'cloudwatch-observability-runtime', 'ecs-fargate-runtime',
                      'dynamodb-persistence-runtime', 'sqs-queue-runtime',
                      'security-cognito-diagnostics', 'security-shared-rate-limit-diagnostics',
                      'postgresql-connection-diagnostics')

        def assert_binding(candidate):
            for identity in identities:
                self.assertTrue(any(selection.below(fixture, item)
                                    for item in candidate['checks'][identity]['inputs']), identity)

        assert_binding(catalog)
        stale = copy.deepcopy(catalog)
        stale['checks']['platform-config-runtime']['inputs'].remove(fixture)
        with self.assertRaises(AssertionError):
            assert_binding(stale)

    def test_imported_diagnostic_fixtures_have_focused_registered_owners(self):
        import re
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        expected = {
            "chat-startup-regression": ("scripts/00.chat/startup/start-chat-session/smoke-test.sh", True),
            "chat-log-writers-regression": ("scripts/00.chat/session-log/update-chat-log/smoke-test.sh", False),
            "chat-log-maintenance-regression": ("scripts/00.chat/session-log/checkpoint-chat-session-log/smoke-test.sh", False),
            "chat-summary-regression": ("scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh", True),
            "chat-upstream-portability-regression": ("scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh", True),
            "harness-governed-runner-regression": ("scripts/01.harness/smoke-test-governed-script-runner.sh", False),
            "harness-command-drift-regression": ("scripts/01.harness/smoke-test-governed-script-command-drift.sh", False),
            "harness-process-drift-regression": ("scripts/01.harness/smoke-test-deterministic-process-drift.sh", False),
            "chat-bootstrap-audit-regression": ("scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/smoke-test.sh", False),
            "chat-migration-audit-regression": ("scripts/00.chat/migration/audit-chat-layer-migration/smoke-test.sh", False),
            "chat-upstream-ensure-regression": ("scripts/00.chat/upstream/ensure-llm-workbench-repo/smoke-test.sh", False),
            "chat-upstream-contract-regression": ("scripts/00.chat/upstream/check-llm-workbench-contract/smoke-test.sh", False),
            "chat-upstream-bootstrap-regression": ("scripts/00.chat/upstream/bootstrap-llm-workbench-repo/smoke-test.sh", True),
            "chat-integration-preparation-regression": ("scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/smoke-test.sh", False),
            "chat-cleanup-regression": ("scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh", False),
            "chat-prerequisites-regression": ("scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh", False),
            "chat-conflict-audit-regression": ("scripts/00.chat/main-refresh/verify-conflict-audit/smoke-test.sh", False),
            "chat-recovery-regression": ("scripts/00.chat/recovery/import-active-paths-to-chat-worktree/smoke-test.sh", False),
            "chat-session-reader-regression": ("scripts/00.chat/session-log/read-current-chat-log/smoke-test.sh", False),
            "chat-session-resolution-regression": ("scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh", True),
            "chat-worktree-paths-regression": ("scripts/00.chat/worktree/paths/smoke-test.sh", True),
            "chat-command-dispatch-regression": ("scripts/00.chat/command/dispatcher/smoke-test.sh", True),
            "chat-refresh-readiness-regression": ("scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh", True),
            "chat-conflict-classification-regression": ("scripts/00.chat/main-refresh/classify-conflict/smoke-test.sh", False),
            "chat-log-deletion-regression": ("scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh", False),
        }
        for identity, (fixture, uses_node) in expected.items():
            with self.subTest(identity=identity):
                check = catalog['checks'][identity]
                unit = identity.removesuffix('-regression')
                self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', unit])
                self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
                wrapper = (ROOT / 'scripts/repo/check-selection/smoke-test.sh').read_text()
                self.assertEqual(wrapper.count(unit + ') exec bash ' + fixture + ' ;;'), 1)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['boundary'], 'integration')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertEqual('node' in check['runtime']['tools'], uses_node)
                inputs = check['inputs']
                self.assertEqual(len(inputs), len(set(inputs)))
                # Real copied source files, not merely the fixture itself, must invalidate proof.
                copied = re.findall(r'\$SOURCE_ROOT/(scripts/[^"\s$]+)"', (ROOT / fixture).read_text())
                for source in [fixture, 'scripts/repo/check-selection/smoke-test.sh', *copied]:
                    self.assertTrue(any(selection.below(source, ref) for ref in inputs), source)
                rules = [rule for rule in catalog['repository_inputs'] if identity in rule['checks']]
                self.assertEqual(len(rules), 1)
                self.assertEqual(set(rules[0]['inputs']), set(inputs))
                self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in inputs))
                self.assertNotIn(identity, catalog['checks']['check-selection-regression']['members'])
        readiness = catalog['checks']['chat-refresh-readiness-regression']['inputs']
        merge = catalog['checks']['chat-local-merge-regression']['inputs']
        for source in ('scripts/00.chat/local-merge/list-active-chat-branches',
                       'scripts/00.chat/local-merge/report-chat-branch-overlaps',
                       'scripts/00.chat/reporting/report-chat-workspaces'):
            self.assertIn(source, merge)
        merge_rule = next(rule for rule in catalog['repository_inputs']
                          if rule['checks'] == ['chat-local-merge-regression'])
        self.assertEqual(set(merge_rule['inputs']), set(merge))
        for rule in catalog['repository_inputs']:
            for source in rule['inputs']:
                self.assertNotIn(' - scripts/', source, 'indented YAML list item became part of a path')
        for capability in ('classify-refresh-readiness', 'check-chat-is-current-with-main', 'show-main-update-status', 'rehearse-refresh-from-main'):
            self.assertIn('scripts/00.chat/main-refresh/' + capability, readiness)

    def test_configuration_requirements_have_one_harness_standard_owner(self):
        canonical = '.agentic/03.product/standards/config-runtime-settings.md'
        legacy = 'docs/03.product/rules/platform/concerns/config-runtime-settings.yml'
        manifest = yaml.safe_load((ROOT / '.agentic/01.harness/manifest.yml').read_text())
        pointer = yaml.safe_load((ROOT / legacy).read_text())
        workflow = (ROOT / '.agentic/03.product/workflows/platform-runtime-implementation.md').read_text()
        metadata = selection.metadata(ROOT / canonical)
        placement = (ROOT / '.agentic/01.harness/standards/document-artifact-placement.md').read_text()
        self.assertNotIn('| Structured ruleset | `docs/', placement)
        self.assertNotIn('| Rule pack | `docs/', placement)
        self.assertIn('`.agentic/<owner-layer>/standards/`', placement)

        def assert_owner(candidate):
            self.assertIn(canonical, candidate['current_known_artifacts']['standards'])
            self.assertNotIn(legacy, json.dumps(candidate['current_known_artifacts']))
            self.assertEqual(metadata['kind'], 'standard')
            self.assertEqual(metadata['id'], 'product.standard.config-runtime-settings')
            self.assertEqual(metadata['status'], 'active')
            self.assertIn('../standards/config-runtime-settings.md', workflow)
            self.assertEqual(pointer['canonical_document'], canonical)
            self.assertEqual(pointer['canonical_id'], metadata['id'])
            self.assertEqual(pointer['compatibility'], 'human-readable-pointer')
            self.assertEqual(pointer['status'], 'deprecated')
            self.assertNotIn('rules', pointer, 'the pointer must not retain a second requirements body')

        assert_owner(manifest)
        stale = copy.deepcopy(manifest)
        stale['current_known_artifacts']['standards'].remove(canonical)
        stale['current_known_artifacts']['concern_rulesets'].append(legacy)
        with self.assertRaises(AssertionError):
            assert_owner(stale)

    def test_configuration_standard_retains_diagnostic_selection_and_rejects_stale_binding(self):
        canonical = '.agentic/03.product/standards/config-runtime-settings.md'
        legacy = 'docs/03.product/rules/platform/concerns/config-runtime-settings.yml'
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        expected = {'diagnostic-adoption', 'diagnostic-runtime-contracts'}

        def assert_binding(candidate):
            rules = candidate['repository_inputs']
            self.assertTrue(any(canonical in rule['inputs'] and expected <= set(rule['checks'])
                                for rule in rules), 'canonical requirements must retain their diagnostic owners')
            self.assertFalse(any(legacy in rule['inputs'] for rule in rules),
                             'current selection must not treat the pointer as the requirements owner')
            selected = {identity for rule in rules
                        if any(selection.below(canonical, item) for item in rule['inputs'])
                        for identity in rule['checks']}
            self.assertTrue(expected <= selected)

        assert_binding(catalog)
        stale = copy.deepcopy(catalog)
        for rule in stale['repository_inputs']:
            rule['inputs'] = [legacy if item == canonical else item for item in rule['inputs']]
        with self.assertRaises(AssertionError):
            assert_binding(stale)

    def test_module_structure_is_a_shared_commit_gate_with_bounded_regression(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        for identity, command, owner, boundary in [
            ('module-index-structure', 'script.sh', 'repo.module-structure.command', 'commit'),
            ('module-index-structure-regression', 'smoke-test.sh', 'repo.module-structure.regression', 'integration'),
        ]:
            check = checks[identity]
            self.assertEqual(check['argv'], ['bash', 'scripts/repo/module-structure/' + command])
            self.assertEqual(check['owner'], owner)
            self.assertEqual(check['boundary'], boundary)
            self.assertEqual(check['effects'], ['read-only'])
            self.assertEqual(check['stage'], 'local')
            self.assertFalse(selection.validate_check(ROOT, identity, check))
            self.assertIn('typescript', check['runtime']['node_packages'])
            for root in ['packages', 'platform', 'apps', 'products', 'infra']:
                self.assertIn(root, check['inputs'], 'dependency discovery inputs must invalidate both checks')
        rules = catalog['repository_inputs']
        for ref in ['packages/core/src/config/index.ts', 'packages/future/src/index.ts',
                    'platform/future/src/index.ts', 'apps/future/src/index.ts',
                    'products/future/src/index.ts', 'infra/04.deploy/future.ts', 'scripts/repo/module-structure/legacy.v1.json',
                    '.agentic/03.product/standards/public-module-structure.md']:
            selected = {identity for rule in rules if any(selection.below(ref, item) for item in rule['inputs'])
                        for identity in rule['checks']}
            self.assertIn('module-index-structure', selected, ref)
        baseline = json.loads((ROOT / 'scripts/repo/module-structure/legacy.v1.json').read_text())
        self.assertNotIn('packages/core/src/config/index.ts', [row['path'] for row in baseline['legacy']])
        self.assertIn('module-structure/check.mjs', (ROOT / 'packages/core/tests/test-infrastructure/static-validation/core-boundaries.test.mjs').read_text())
        self.assertIn('scripts/repo/module-structure/check.mjs', checks['core-runtime']['inputs'])
        self.assertTrue(any('scripts/repo/module-structure/check.mjs' in rule['inputs']
                            and 'core-runtime' in rule['checks'] for rule in rules))

    def test_configuration_access_uses_the_existing_gate_and_policy_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        policy = '.agentic/03.product/standards/config-runtime-settings.md'
        for identity in ['module-index-structure', 'module-index-structure-regression']:
            self.assertIn(policy, catalog['checks'][identity]['inputs'])
            self.assertTrue(any(policy in rule['inputs'] and identity in rule['checks']
                                for rule in catalog['repository_inputs']))
        implementation = (ROOT / 'scripts/repo/module-structure/check.mjs').read_text()
        self.assertIn('const access = inspectConfigurationAccess(sources)', implementation)
        self.assertIn('...access.findings', implementation)
        self.assertNotIn('configuration-access-registry', json.dumps(catalog))

    def test_artifact_migration_owns_complete_existing_command_and_exact_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        check = catalog['checks']['harness-artifact-migration-regression']
        self.assertEqual(check['argv'], ['bash', 'scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual(check['owner'], 'harness.script.smoke-test-artifact-path-migration')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['boundary'], 'integration')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['inputs'], [
            'scripts/01.harness/check-artifact-path-migration.sh',
            'scripts/01.harness/plan-artifact-path-migration.sh',
            'scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual(check['runtime'], {'tools': ['bash', 'git'], 'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'TMPDIR']})
        self.assertFalse(selection.validate_check(ROOT, 'harness-artifact-migration-regression', check))
        self.assertNotIn('harness-artifact-migration-regression', catalog['checks']['check-selection-regression']['members'])
        driver = (ROOT / check['argv'][1]).read_text()
        for child in ('plan-artifact-path-migration.sh', 'check-artifact-path-migration.sh'):
            self.assertIn('bash "$SOURCE_ROOT/scripts/01.harness/' + child + '"', driver)
        reviews = json.loads((ROOT / 'scripts/repo/diagnostic-coverage/reviews.v1.json').read_text())['reviews']
        review = next(row for row in reviews if row['owner'] == 'harness-artifact-migration-diagnostics')
        self.assertEqual(review['checks'], ['harness-artifact-migration-regression'])
        self.assertEqual(review['tests'], ['scripts/01.harness/smoke-test-artifact-path-migration.sh'])
        self.assertEqual([source['path'] for source in review['sources']], check['inputs'][:2])

    def test_chat_export_and_metrics_own_exact_standalone_commands_inputs_and_runtime(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        checks = catalog['checks']
        common_environment = ['PATH', 'LANG', 'LC_ALL', 'NODE_OPTIONS', 'NODE_PATH', 'TMPDIR']
        metrics_environment = ['CHAT_COST_PROFILE', 'CHAT_COST_PRICING_FILE', 'CHAT_TRANSCRIPT_PROVIDER',
            'CHAT_TRANSCRIPT_PATH', 'CHAT_TRANSCRIPT_BYTES', 'CHAT_TRANSCRIPT_SOURCE', 'CHAT_TRANSCRIPT_METRICS_MODE',
            'TRANSCRIPT_PROVIDER', 'TRANSCRIPT_PATH', 'TRANSCRIPT_BYTES', 'TRANSCRIPT_SOURCE',
            'CODEX_SESSION_LOG_PATH', 'LLM_WORKBENCH_TRANSCRIPT_PROVIDER', 'ESTIMATED_CHAT_TOKENS',
            'ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS']
        expected = {
            'chat-export-regression': ('chat-export', 'scripts/00.chat/export/smoke-test.sh', {
                'scripts/repo/check-selection/smoke-test.sh', 'scripts/00.chat/export/smoke-test.sh',
                'scripts/00.chat/export/create-worktree-bundle/script.js',
                'scripts/00.chat/export/worktree/script.sh', 'scripts/00.chat/export/worktree-diff/script.sh',
                'bin/llm-workbench.js', 'bin/llm-workbench-ownership.js', 'package.json'}, common_environment),
            'chat-commit-metrics-regression': ('chat-commit-metrics', 'scripts/00.chat/session-log/record-chat-commit/smoke-test.sh', {
                'scripts/repo/check-selection/smoke-test.sh',
                'scripts/00.chat/session-log/record-chat-commit/smoke-test.sh',
                'scripts/00.chat/session-log/record-chat-commit/script.sh',
                'scripts/00.chat/session-log/paths/lib.sh',
                'scripts/00.chat/transcript/discover-codex-session-log/script.sh',
                'scripts/00.chat/metrics/estimate-chat-cost/script.js',
                'scripts/00.chat/metrics/data/chat-pricing.json'}, common_environment + metrics_environment),
        }
        wrapper = (ROOT / 'scripts/repo/check-selection/smoke-test.sh').read_text()
        self.assertEqual(selection.LOCAL_EFFECTS, {'read-only', 'writes-files'})
        for identity, (unit, child, inputs, environment) in expected.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', unit])
                self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['boundary'], 'integration')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(len(check['inputs']), len(inputs))
                self.assertEqual(check['runtime'], {'tools': ['bash', 'node', 'git'], 'node_packages': [],
                    'environment': environment, 'config_inputs': ['.node-version', '.nvmrc']})
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertNotIn(identity, checks['check-selection-regression']['members'])
                self.assertEqual(wrapper.count(unit + ') exec bash ' + child + ' ;;'), 1)
                rules = [rule for rule in catalog['repository_inputs'] if identity in rule['checks']]
                self.assertEqual(len(rules), 1)
                self.assertEqual(set(rules[0]['inputs']), inputs)
                self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in inputs))

    def test_alignment_suites_have_separate_actual_local_commands_and_input_closures(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        alignment = 'scripts/04.deploy/lifecycle/00-target-alignment/'
        expected = {
            'aws-runtime-alignment-regression': (
                'provider-adapters/aws/runtime-alignment', 'deploy.test.aws.runtime-alignment',
                {alignment + 'provider-adapters/aws/runtime-alignment',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py'}),
            'provider-condition-evidence-regression': (
                'validate-provider-condition-evidence', 'deploy.test.validate-provider-condition-evidence',
                {alignment + 'validate-provider-condition-evidence'}),
            'core-target-declaration-regression': (
                'core-platform-target-declaration', 'deploy.test.core-platform-target-declaration',
                {alignment.rstrip('/'), 'scripts/04.deploy/lifecycle/60-run',
                 'scripts/04.deploy/lifecycle/40-package/package-custody-receipt',
                 'scripts/04.deploy/shared/deployment-operation-diagnostics.py',
                 'scripts/repo/diagnostic-coverage/runtime_contract.py',
                 'platform/persistence/contracts/diagnostics.v1.json',
                 'infra/04.deploy/03.product/targets/kanbien-core-platform',
                 'infra/04.deploy/03.product/image/core-server/image-contract.yml',
                 'infra/04.deploy/03.product/image/core-server-persistence-observability-collector',
                 '.github/workflows/publish-kanbien-core-platform-core-server.yml',
                 '.github/workflows/publish-kanbien-core-platform-core-server-persistence.yml',
                 '.github/workflows/publish-kanbien-core-platform-observability-collector.yml'}),
        }
        for identity, (directory, owner, inputs) in expected.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', alignment + directory + '/smoke-test.sh'])
                self.assertEqual(check['owner'], owner)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(check['runtime'], checks['target-alignment-regression']['runtime'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                self.assertNotIn(identity, checks['target-alignment-regression'].get('members', []))
        # Ordinary runtime implementation edits do not own these fixture suites.
        for identity in expected:
            self.assertFalse(any(selection.below('platform/server/src/index.ts', path)
                                 for path in checks[identity]['inputs']))

    def test_deployment_diagnostic_fixture_binds_actual_controller_and_catalog_dependencies(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['deployment-operation-diagnostics-regression']
        run = 'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/'
        required = {
            run + name for name in ('run-administration/script.py', 'run-migration/script.py',
                'proof-receipts.py', 'rehearse-runtime-credential-lifecycle/script.py',
                'rehearse-observability-readiness/script.py', 'rehearse-server-replacement/script.py')
        } | {
            'packages/core/contracts', 'apps/platform-smoke/contracts',
            'infra/04.deploy/03.product/entrypoints/contracts',
            'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py'
        } | {'platform/' + name + '/contracts' for name in (
            'config', 'contracts', 'health', 'observability', 'persistence', 'runtime', 'security', 'server', 'workers')}
        self.assertLessEqual(required, set(check['inputs']))
        self.assertNotIn('platform', check['inputs'])
        self.assertFalse(selection.validate_check(ROOT, 'deployment-operation-diagnostics-regression', check))
        self.assertIn('infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml',
                      checks['shell-release-evidence-regression']['inputs'])

    def test_disposable_postgresql_proof_binds_actual_composition_dependencies(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['postgresql-disposable-diagnostics']
        self.assertEqual(check['stage'], 'package')
        self.assertEqual(check['argv'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh'])
        self.assertEqual(set(check['inputs']), {
            'platform/adapters/aws/persistence/postgresql', 'platform/persistence', 'packages/core',
            'platform/contracts', 'platform/security', 'platform/observability', 'apps/platform-smoke',
            'platform/config', 'platform/health', 'platform/runtime', 'platform/server', 'platform/workers',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts',
            'infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts',
            'package.json', 'package-lock.json',
            'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh'})
        self.assertEqual(check['effects'], ['network', 'writes-files'])
        self.assertEqual(check['owner'], 'deploy.test.postgresql-disposable-connection-diagnostics')
        self.assertFalse(selection.validate_check(ROOT, 'postgresql-disposable-diagnostics', check))
        local = checks['postgresql-connection-diagnostics']
        self.assertEqual(local['argv'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh'])
        self.assertEqual(set(local['inputs']), {
            'platform/adapters/aws/persistence/postgresql', 'platform/persistence', 'packages/core',
            'platform/contracts', 'platform/security', 'platform/observability',
            'package.json', 'package-lock.json',
            'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh'})
        self.assertEqual(local['stage'], 'local')
        self.assertFalse(selection.validate_check(ROOT, 'postgresql-connection-diagnostics', local))

    def test_harness_index_owns_actual_complete_command_and_input_closure(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        identity = 'harness-index-regression'
        check = checks[identity]
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/check-selection/smoke-test.sh', '--unit', 'harness-index'])
        self.assertEqual(check['owner'], 'repo.test.check-selection.wrapper')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/repo/check-selection/smoke-test.sh',
            'scripts/01.harness/artifact-metadata/generate-index',
            'scripts/01.harness/artifact-metadata/header_discovery.py',
            'scripts/01.harness/artifact-metadata/backfill-v2-headers',
            'scripts/01.harness/artifact-metadata/check-headers/script.sh',
            'scripts/01.harness/check-artifact-metadata-headers.sh',
            '.agentic/01.harness/artifact-metadata/examples/markdown.v2.md',
            '.agentic/01.harness/artifact-metadata/examples/yaml.v2.yml',
            'docs/02.rag-rulebook/rules/README.md',
            'docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml',
            'docs/03.product/rules/core/layers/packages-core.yml'})
        self.assertEqual(check['runtime'], {
            'tools': ['bash', 'python3', 'git'], 'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'PYTHONPATH', 'PYTHONHOME',
                            'PYTHONHASHSEED', 'PYTHONDONTWRITEBYTECODE', 'RAG_REPO_ROOT', 'RAG_SOURCE_COMMIT_SHA'],
            'config_inputs': ['.python-version', 'pyproject.toml', 'requirements.txt']})
        self.assertFalse(selection.validate_check(ROOT, identity, check))
        self.assertNotIn(identity, checks['check-selection-regression']['members'])
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('harness-index) exec bash scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh ;;'), 1)
        driver = (ROOT / 'scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh').read_text()
        self.assertEqual(driver.count('python3 -B "$repo_root/scripts/01.harness/artifact-metadata/backfill-v2-headers/diagnostic-test.py"'), 1)
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in check['inputs']))

    def test_harness_validator_owns_actual_complete_command_and_input_closure(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        identity = 'harness-agent-validator-regression'
        check = checks[identity]
        self.assertEqual(check['argv'], ['bash', 'scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh'])
        self.assertEqual(check['owner'], 'harness.test.agents.validate-harness-agents.diagnostics')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/01.harness/agents/validate-harness-agents',
            'scripts/01.harness/metrics/compare-task-token-consumption',
            '.agentic/01.harness/agents',
            *('.agentic/01.harness/templates/' + name for name in [
                'agent-review-report.md', 'agent-scorecard.yml', 'agent-scorecard.schema.yml',
                'agent-scorecard.example.yml', 'examples/cfo-token-efficiency-scorecard.yml']),
            *('.agentic/01.harness/workflows/' + name for name in [
                'run-agent-review.md', 'run-review-board.md', 'implement-backend-architecture-guideline.md']),
            '.agentic/01.harness/standards/agent-contracts.md',
            '.agentic/01.harness/manifest.yml', '.agentic/01.harness/README.md'})
        self.assertEqual(check['runtime'], {
            'tools': ['bash', 'node', 'git'],
            'node_packages': [],
            'environment': ['PATH', 'LANG', 'LC_ALL', 'NODE_OPTIONS', 'NODE_PATH'],
            'config_inputs': ['.node-version', '.nvmrc']})
        self.assertFalse(selection.validate_check(ROOT, identity, check))
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('exec node '), 1)
        self.assertIn('/diagnostic-test.js', wrapper)
        driver = (ROOT / 'scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js').read_text()
        self.assertIn("const wrapper = path.join(__dirname, 'script.sh');", driver)
        self.assertIn("spawnSync('bash', [wrapper, ...args]", driver)
        self.assertIn("run('existing complete internal fixtures')", driver)
        self.assertIn("run('restored complete internal fixtures')", driver)
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref) for ref in check['inputs']))

    def test_target_controls_and_budget_own_actual_complete_local_commands(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        base = 'scripts/04.deploy/lifecycle/'
        cases = {
            'bootstrap-target-controls-regression': (
                base + '50-deploy/targets/kanbien-core-platform/bootstrap-runtime',
                'deploy.test.kanbien-core-platform.target-controls',
                ['release-contract/smoke-test.sh', 'deployment-cli-regression.py',
                 'rehearse-accepted-workload-replacement/smoke-test.sh',
                 'rehearse-private-verifier-fault/smoke-test.sh',
                 'verify-delivery-role-access/smoke-test.py'],
                {base + '50-deploy/targets/kanbien-core-platform/bootstrap-runtime',
                 base + '60-run/targets/kanbien-core-platform/bootstrap-runtime',
                 base + '00-target-alignment',
                 *(base + '60-run/' + name for name in ['validate-active-workload-health-recovery',
                    'validate-health-failure-and-recovery-declaration', 'validate-persistence-diagnostic-mapping',
                    'validate-acceptance-route', 'promote-accepted-scope', 'release-succession']),
                 base + '40-package/package-custody-receipt',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py',
                 'scripts/04.deploy/shared/deployment-operation-diagnostics.py',
                 'scripts/repo/diagnostic-coverage/runtime_contract.py',
                 'platform/persistence/contracts/diagnostics.v1.json',
                 '.agentic/04.deploy/60-run/schemas', 'infra/04.deploy/03.product/image',
                 'infra/04.deploy/03.product/entrypoints', 'infra/04.deploy/03.product/targets/kanbien-core-platform'}),
            'foundation-budget-regression': (
                base + '50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget',
                'deploy.test.kanbien-core-platform.provision-target-budget',
                ['recovery-test.py', 'RecoveryCli.test_budget_lost_response_resumes_exact_operation'],
                {base + '50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget',
                 'scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/response.py',
                 'scripts/04.deploy/shared/provider-adapters/aws/cognito-provisioning.py',
                 'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml'}),
        }
        for identity, (directory, owner, fixtures, inputs) in cases.items():
            with self.subTest(identity=identity):
                check = checks[identity]
                self.assertEqual(check['argv'], ['bash', directory + '/smoke-test.sh'])
                self.assertEqual(check['owner'], owner)
                self.assertEqual(check['stage'], 'local')
                self.assertEqual(check['evidence_class'], 'local-runtime')
                self.assertEqual(check['effects'], ['read-only', 'writes-files'])
                self.assertFalse(check['scope_inputs'])
                self.assertEqual(set(check['inputs']), inputs)
                self.assertEqual(check['runtime'], checks['target-alignment-regression']['runtime'])
                self.assertFalse(selection.validate_check(ROOT, identity, check))
                wrapper = (ROOT / check['argv'][1]).read_text()
                for fixture in fixtures:
                    self.assertEqual(wrapper.count(fixture), 1, (identity, fixture))
        self.assertFalse(any(selection.below('platform/server/src/index.ts', ref)
                             for identity in cases for ref in checks[identity]['inputs']))

    def test_delivery_access_suite_and_package_fixture_dependencies_are_real_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['delivery-access-contract-regression']
        base = 'scripts/04.deploy/lifecycle/40-package/'
        self.assertEqual(check['argv'], ['bash', base + 'validate-delivery-access-contract/smoke-test.sh'])
        self.assertEqual(check['owner'], 'deploy.test.validate-delivery-access-contract')
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertEqual(check['effects'], ['read-only', 'writes-files'])
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(set(check['inputs']), {
            'scripts/04.deploy/shared/safe-command-diagnostics.sh',
            base + 'validate-delivery-access-contract', base + 'provider-adapters/aws/iam-policy-coverage',
            base + 'targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access',
            base + 'targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access'})
        self.assertFalse(selection.validate_check(ROOT, 'delivery-access-contract-regression', check))
        package = checks['package-custody-regression']
        wrapper = (ROOT / package['argv'][1]).read_text()
        for fixture in ['qualification-test.py', 'disposable-cleanup-test.py', 'ecr-scan-test.py']:
            self.assertIn(fixture, wrapper)
        # These are actually read/executed by existing fixtures, not a broad
        # platform dependency guessed from the directory's name.
        for path in [base + 'build-core-server-image/script.sh',
                     base + 'qualify-retained-persistence-rollback-image/script.sh',
                     'scripts/04.deploy/shared/safe-command-diagnostics.sh',
                     'scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py',
                     'scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py',
                     'scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh',
                     'platform/server/src/index.ts', 'packages/core/src/index.ts']:
            self.assertTrue(any(selection.below(path, ref) for ref in package['inputs']), path)
        self.assertTrue({'python3', 'node', 'typescript'} <= set(package['runtime']['tools']))
        self.assertIn('typescript', package['runtime']['node_packages'])
        # The payload fixture reads the actual Dockerfile COPY closure, so its
        # source identity must invalidate proof when an imported file is omitted.
        self.assertIn('infra/04.deploy/03.product/image/core-server-persistence/Dockerfile',
                      checks['persistence-payload-regression']['inputs'])

    def test_dynamodb_persistence_owns_complete_adapter_command_and_actual_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['dynamodb-persistence-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'dynamodb-persistence'])
        wrapper = (ROOT / 'scripts/repo/diagnostic-coverage/verify.sh').read_text()
        self.assertIn('  dynamodb-persistence) exec npm --ignore-scripts run platform:adapter:aws:persistence:dynamodb:check ;;', wrapper.splitlines())
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(set(check['inputs']), {'scripts/repo/diagnostic-coverage/verify.sh', 'packages/core', 'platform/persistence',
            'platform/adapters/aws/persistence/dynamodb', 'package.json', 'package-lock.json'})
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:persistence:dynamodb:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:persistence:dynamodb:' + name
            for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'dynamodb-persistence-runtime', check))

    def test_ecs_runtime_uses_existing_complete_adapter_command_and_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['ecs-fargate-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'ecs-fargate'])
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        expected = {'packages/core', 'platform/contracts', 'platform/config', 'platform/health',
                    'platform/observability', 'platform/runtime', 'platform/security', 'platform/server',
                    'platform/testing', 'platform/adapters/aws/runtime/ecs-fargate', 'package.json', 'package-lock.json',
                    'scripts/repo/diagnostic-coverage/verify.sh'}
        self.assertEqual(set(check['inputs']), expected)
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:runtime:ecs-fargate:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:runtime:ecs-fargate:' + name
                         for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'ecs-fargate-runtime', check))

    def test_sqs_queue_owns_complete_adapter_command_and_actual_inputs(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        check = checks['sqs-queue-runtime']
        self.assertEqual(check['argv'], ['bash', 'scripts/repo/diagnostic-coverage/verify.sh', '--unit', 'sqs-queue'])
        wrapper = (ROOT / 'scripts/repo/diagnostic-coverage/verify.sh').read_text()
        self.assertIn('  sqs-queue) exec npm --ignore-scripts run platform:adapter:aws:queue:sqs:check ;;', wrapper.splitlines())
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['evidence_class'], 'local-runtime')
        self.assertFalse(check['scope_inputs'])
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(set(check['inputs']), {'scripts/repo/diagnostic-coverage/verify.sh', 'packages/core',
            'platform/adapters/aws/queue/sqs', 'package.json', 'package-lock.json'})
        script = json.loads((ROOT / 'package.json').read_text())['scripts']['platform:adapter:aws:queue:sqs:check']
        self.assertEqual(script.split(' && '), ['npm run platform:adapter:aws:queue:sqs:' + name
            for name in ['typecheck', 'build', 'test', 'boundary']])
        self.assertFalse(selection.validate_check(ROOT, 'sqs-queue-runtime', check))

    def test_package_units_preserve_original_command_membership_and_audited_inputs(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        members = catalog['diagnostic-base-runtime']['members']
        expected = {'catalog', 'core', 'contracts', 'config', 'security', 'observability', 'health', 'persistence', 'runtime', 'testing', 'workers', 'smoke-app'}
        self.assertEqual({catalog[identity]['argv'][-1] for identity in members}, expected)
        self.assertEqual(len(members), len(expected))
        for identity in members:
            if identity == 'diagnostic-catalog-readers': continue
            check = catalog[identity]
            self.assertNotIn('scripts/04.deploy', check['inputs'])
            self.assertNotIn('platform', check['inputs'])
            self.assertTrue(any((ROOT / path / 'tests').is_dir() for path in check['inputs']))
            self.assertIn('typescript', check['runtime']['node_packages'])


    def test_real_aggregate_contracts_cover_child_inputs_and_runtime(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for aggregate, children in {
            'diagnostic-runtime-contracts': ['diagnostic-base-runtime', 'platform-server-runtime', 'kanbien-platform-runtime'],
            'shell-package-source': ['platform-server-runtime', 'kanbien-platform-runtime', 'platform-shell-payload'],
        }.items():
            parent = checks[aggregate]
            self.assertEqual(parent['members'], children)
            for child in children:
                leaf = checks[child]
                self.assertFalse(selection.validate_check(ROOT, child, leaf))
                for field in ['tools', 'node_packages', 'environment']:
                    self.assertTrue(set(leaf['runtime'][field]) <= set(parent['runtime'][field]), (aggregate, child, field))
                for reference in leaf['runtime']['config_inputs']:
                    self.assertTrue(reference in parent['runtime']['config_inputs'] or reference in parent['inputs'])


    def test_bootstrap_payload_regression_is_a_local_owned_check(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        check = catalog['checks']['bootstrap-payload-regression']
        self.assertEqual(check['stage'], 'local')
        self.assertEqual(check['boundary'], 'integration')
        self.assertEqual(check['effects'], ['writes-files'])
        self.assertEqual(check['applicability']['program_id'], 'kanbien-core-server')
        self.assertEqual(check['argv'], ['bash', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh'])
        self.assertIn('scripts/04.deploy/lifecycle/40-package/build-core-server-image', check['inputs'])
        for path in [
            'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs',
            'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/runtime-contract.mjs',
            'scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs',
        ]:
            self.assertIn(path, check['inputs'])
        wrapper = (ROOT / check['argv'][1]).read_text()
        self.assertEqual(wrapper.count('python3 -B scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py'), 1)
        self.assertIn('platform', check['inputs'])
        self.assertIn('packages/core', check['inputs'])


    def test_every_registered_check_has_a_valid_execution_contract(self):
        catalog = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())
        errors = [error for key, check in catalog['checks'].items()
                  for error in selection.validate_check(ROOT, key, check)]
        self.assertEqual(errors, [])


    def test_existing_persistence_scope_has_coverage(self):
        catalog = selection.coverage.document(ROOT / 'scripts/repo/check-selection/checks.yml')
        report = selection.coverage.inspect(ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml', ROOT, catalog)
        self.assertEqual(report['verdict'], 'covered', report)
        self.assertIn('persistence-composition', report['required_checks'])


    def test_actual_diagnostic_paths_select_focused_checks(self):
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        for paths, expected in [
            (['platform/adapters/aws/persistence/dynamodb/src/transactions.ts'], {'dynamodb-persistence-runtime', 'platform-shell-payload'}),
            (['platform/adapters/aws/queue/sqs/src/worker.ts'], {'sqs-queue-runtime', 'platform-shell-payload'}),
            (['platform/adapters/aws/persistence/postgresql/src/errors.ts', 'platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-diagnostics-runtime.test.ts'], {'postgresql-connection-diagnostics', 'postgresql-disposable-diagnostics', 'persistence-composition'}),
            (['scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py', '.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml'], {'restore-connection-diagnostics', 'deployment-operation-diagnostics-regression'}),
        ]:
            args = argparse.Namespace(root=ROOT, catalog=catalog, paths=paths, staged=False, all=False, stage='local', execute_local=False, evidence=None, json=True)
            report = selection.plan(args)
            self.assertEqual(report['verdict'], 'planned', report.get('findings'))
            selected = {check['check_id'] for check in report['checks']}
            self.assertTrue(expected <= selected, (paths, selected))
            if 'postgresql-disposable-diagnostics' in expected:
                engine = next(check for check in report['checks'] if check['check_id'] == 'postgresql-disposable-diagnostics')
                self.assertEqual(engine['stage'], 'package'); self.assertEqual(engine['evidence_class'], 'ci')
                image = next(check for check in report['checks'] if check['check_id'] == 'persistence-container')
                self.assertEqual(image['evidence_class'], 'container-qualification')
                self.assertNotEqual(engine['argv'], image['argv'])
            if paths[0].startswith('scripts/04.deploy'):
                self.assertNotIn('postgresql-connection-diagnostics', selected, 'report-only changes reuse unaffected adapter evidence')


    def test_selection_does_not_probe_unrelated_acceptance_commands(self):
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        calls = []
        original = selection.coverage.inspect

        def inspect(contract, root, catalog, *, probe_commands=True):
            calls.append(probe_commands)
            return original(contract, root, catalog, probe_commands=probe_commands)

        args = argparse.Namespace(root=ROOT, catalog=catalog,
            paths=['scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py'],
            staged=False, all=False, stage='local', execute_local=False,
            evidence=None, json=True)
        with patch.object(selection.coverage, 'inspect', side_effect=inspect):
            selection.plan(args)
        self.assertTrue(calls)
        self.assertEqual(set(calls), {False})


    def test_local_runner_and_commit_hook_declare_write_effects(self):
        for path in ('scripts/repo/check-selection/script.sh', 'scripts/repo/commit-gates/script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'):
            self.assertIn('writes-files', selection.metadata(ROOT / path)['effects'])
        result = subprocess.run(['bash', 'scripts/01.harness/run-governed-script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approval-sensitive script requires --approved-action', result.stderr)


    def test_real_persistence_cannot_borrow_bootstrap_proofs_or_omit_composition(self):
        path = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml'
        original = selection.coverage.document
        contract = copy.deepcopy(original(path))
        requirement = contract['change_impact']['requirements'][0]
        requirement.update(local_proofs=['scope-inventory', 'runnable-program'], package_proofs=['bootstrap-container'], target_proofs=['bootstrap-target-alignment'], run_proofs=['bootstrap-acceptance'])
        with patch.object(selection.coverage, 'document', side_effect=lambda candidate: contract if candidate == path else original(candidate)):
            report = selection.coverage.inspect(path, ROOT, original(ROOT / 'scripts/repo/check-selection/checks.yml'))
        self.assertIn('requirement-check-subject-mismatch', self.codes(report))
        self.assertIn('scope-program-local-proof-missing', self.codes(report))


    def test_workload_specific_startup_conditions(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        for context, expected in [(['platform/observability/src/configuration.ts'], {'persistence-composition', 'platform-shell-payload'}), (['infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts'], {'platform-shell-payload'}), (['services/new-independent/src/main.ts'], set())]:
            graph, findings = selection.verification_dependencies(checks, ['diagnostic-base-runtime'], context)
            self.assertFalse(findings)
            self.assertEqual(graph['diagnostic-base-runtime'] & {'persistence-composition', 'platform-shell-payload'}, expected)



    def test_component_assignment_preserves_original_methods_without_duplicates(self):
        import ast
        import mechanics_test
        import repository_contracts_test
        folder = ROOT / 'scripts/repo/check-selection'
        def names(module):
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            def flatten(items):
                for item in items:
                    if isinstance(item, unittest.TestSuite): yield from flatten(item)
                    else: yield item
            tests = list(flatten(suite))
            ids = [case.id() for case in tests]
            self.assertEqual(len(ids), len(set(ids)))
            return {case._testMethodName for case in tests}
        mechanics = names(mechanics_test)
        repository = names(repository_contracts_test)
        self.assertFalse(mechanics & repository)
        discovered = []
        for path in folder.glob('*.py'):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                    self.assertIn(path.name, {'mechanics_test.py', 'repository_contracts_test.py'}, (path, node.name))
                    discovered.append(node.name)
        self.assertEqual(len(discovered), len(set(discovered)), "Physical test definitions must not shadow each other.")
        self.assertEqual(set(discovered), mechanics | repository, 'New executable tests must belong to a loaded collection.')

    def test_runner_aggregate_retains_exact_components_and_owner_obligations(self):
        checks = yaml.safe_load((ROOT / 'scripts/repo/check-selection/checks.yml').read_text())['checks']
        expected = {'check-selection-mechanics', 'check-selection-repository-contracts', 'harness-lifecycle-metadata-regression', 'harness-header-regression', 'chat-session-preparation-regression', 'chat-local-merge-regression', 'chat-main-refresh-regression'}
        parent = checks['check-selection-regression']
        self.assertEqual(set(parent['members']), expected)
        self.assertEqual(len(parent['members']), len(expected))
        self.assertEqual(parent['inputs'], ['scripts/repo/check-selection'])
        self.assertEqual(checks['check-selection-mechanics']['runtime']['node_packages'], [])
        for excluded in ['platform', 'packages/core', 'docs', '.agentic', 'scripts/04.deploy']:
            self.assertNotIn(excluded, checks['check-selection-mechanics']['inputs'])
        for member in expected:
            child = checks[member]
            self.assertFalse(selection.validate_check(ROOT, member, child))
            for field in ['tools', 'environment', 'node_packages']:
                self.assertTrue(set(child['runtime'].get(field, [])) <= set(parent['runtime'].get(field, [])), (member, field))

    def test_actual_runtime_and_runner_changes_select_independent_proof(self):
        # These are real repository paths, catalog, metadata and review rules.
        # No test command executes. Runtime probing is already separately proved;
        # a bounded identity avoids re-hashing installed SDKs in each pure plan.
        catalog = ROOT / 'scripts/repo/check-selection/checks.yml'
        owners = {'harness-lifecycle-metadata-regression', 'harness-header-regression', 'chat-session-preparation-regression', 'chat-local-merge-regression', 'chat-main-refresh-regression'}
        cases = [
            ('apps/entity-smoke/features/test-entity/domain/services/update-test-entity.ts', {'entity-smoke-runtime', 'kanbien-platform-runtime'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/persistence/dynamodb/src/index.ts', {'dynamodb-persistence-runtime', 'platform-shell-payload'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/persistence/postgresql/src/index.ts', {'postgresql-connection-diagnostics', 'postgresql-disposable-diagnostics'}, {'check-selection-mechanics'}),
            ('platform/adapters/aws/runtime/ecs-fargate/src/index.ts', {'ecs-fargate-runtime', 'platform-shell-payload', 'check-selection-repository-contracts'}, {'check-selection-mechanics', 'chat-export-regression', 'chat-commit-metrics-regression', *owners}),
            ('platform/server/src/configuration/runtime.ts', {'platform-server-runtime', 'check-selection-repository-contracts'}, {'check-selection-mechanics', 'check-selection-regression', 'chat-export-regression', 'chat-commit-metrics-regression', *owners}),
            ('scripts/repo/check-selection/script.py', {'check-selection-mechanics', 'check-selection-repository-contracts', 'check-selection-regression', *owners}, set()),
            ('scripts/repo/check-selection/checks.yml', {'check-selection-mechanics', 'check-selection-repository-contracts', 'check-selection-regression', *owners}, set()),
            ('infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml', {'check-selection-mechanics', 'check-selection-repository-contracts'}, set()),
            ('scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh', {'chat-main-refresh-regression', 'check-selection-repository-contracts'}, {'check-selection-regression', 'check-selection-mechanics'}),
            ('bin/llm-workbench.js', {'chat-export-regression'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('bin/llm-workbench-ownership.js', {'chat-export-regression'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('scripts/00.chat/export/create-worktree-bundle/script.js', {'chat-export-regression', 'check-selection-repository-contracts'}, {'chat-commit-metrics-regression', 'check-selection-regression', 'check-selection-mechanics'}),
            ('scripts/00.chat/metrics/estimate-chat-cost/script.js', {'chat-commit-metrics-regression', 'check-selection-repository-contracts'}, {'chat-export-regression', 'check-selection-regression', 'check-selection-mechanics'}),
        ]
        # A valid future baseline contains this split catalog. Simulate only its
        # git-show bytes: selection logic, current wiring and dependencies remain
        # real. Current task impact against HEAD is intentionally broader.
        original_git = selection.git
        def git(root, *arguments):
            if arguments == ('show', 'HEAD:scripts/repo/check-selection/checks.yml'):
                return catalog.read_text()
            return original_git(root, *arguments)
        original_fingerprint = selection.fingerprint
        def planning_fingerprint(root, references, *, exclude=frozenset()):
            if references == {'scripts/repo/check-selection/checks.yml'}:
                return original_fingerprint(root, references, exclude=exclude)
            # This test proves selection, not source-byte freshness. Preserve the
            # real catalog race guard, but don't hash every selected SDK/runtime
            # payload five times. Execution/cache regressions remain unmocked.
            import hashlib
            return hashlib.sha256(json.dumps(sorted(set(references) - set(exclude))).encode()).hexdigest()
        with patch.object(selection, 'git', side_effect=git), patch.object(selection, 'runtime_identity', return_value={'pure_plan_fixture': 'no-execution'}), patch.object(selection, 'fingerprint', side_effect=planning_fingerprint):
            for path, required, forbidden in cases:
                with self.subTest(path=path):
                    args = argparse.Namespace(root=ROOT, catalog=catalog, paths=[path], staged=False, all=False, stage='local', execute_local=False, evidence=None, json=True)
                    report = selection.plan(args)
                    self.assertEqual(report['verdict'], 'planned', report['findings'])
                    selected = {item['check_id'] for item in report['checks']}
                    self.assertTrue(required <= selected, (required - selected, selected))
                    self.assertFalse(forbidden & selected, forbidden & selected)

    def test_foreign_imports_preserve_fixture_and_facade_without_launching_suites(self):
        import sys
        code = '''
import importlib.util, subprocess, sys
def forbidden(*args, **kwargs):
    raise AssertionError('Import must not launch a suite or child command')
subprocess.call = subprocess.run = subprocess.Popen = forbidden
spec = importlib.util.spec_from_file_location('foreign_fixture_surface', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if sys.argv[1] == 'facade':
    assert callable(module.SelectionTests)
    assert module.selection is module.SelectionTests.run_plan.__globals__['selection']
else:
    assert not any(name.startswith('test_') for name in vars(module.FixtureSupport))
    fixture = module.FixtureSupport()
    assert callable(fixture.setUp) and callable(fixture.run_plan)
    assert module.selection is fixture.run_plan.__globals__['selection']
print('Foreign ' + sys.argv[1] + ' import passed without executing suites.')
'''
        with tempfile.TemporaryDirectory(prefix='foreign-fixture-import-') as directory:
            for surface, filename in [('facade', 'smoke-test.py'), ('helper', 'test_support.py')]:
                with self.subTest(surface=surface):
                    # Separate processes prevent one surface's sys.path setup
                    # from concealing a broken standalone import of the other.
                    result = subprocess.run([sys.executable, '-I', '-B', '-c', code,
                        surface, str(ROOT / 'scripts/repo/check-selection' / filename)],
                        cwd=directory, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), 'Foreign ' + surface + ' import passed without executing suites.')

#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.regression
#   version: 8
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-11-04"
#   layer: 06.shared
#   domain: diagnostics
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Prove independent ordinary-code discovery, anti-drift adoption and TypeScript/Python record parity.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.diagnostics.verification
#     path: scripts/repo/diagnostic-coverage/verify.sh
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import os
import contextlib
import io
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]

def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

coverage = load("adoption", ROOT / "scripts/repo/diagnostic-coverage/script.py")
reader = load("runtime_contract", ROOT / "scripts/repo/diagnostic-coverage/runtime_contract.py")
deployment = load("deployment", ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py")

class DiscoveryTests(unittest.TestCase):
    def verification_fixture(self, relative, arguments, *, fail=0):
        with tempfile.TemporaryDirectory(prefix='verification-unit-') as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '--quiet', temporary], check=True)
            target = root / relative
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / relative, target)
            selector = root / 'scripts/repo/check-selection/script.sh'
            selector.parent.mkdir(parents=True, exist_ok=True)
            selector.write_text('printf "selector %s\\n" "$*" >> "$TRACE"\nexit "$TOOL_EXIT"\n')
            commands = root / 'fixture-bin'
            commands.mkdir()
            for name in ['npm', 'node', 'python3']:
                tool = commands / name
                tool.write_text('#!/bin/bash\nprintf "' + name + ' %s\\n" "$*" >> "$TRACE"\nexit "$TOOL_EXIT"\n')
                tool.chmod(0o755)
            compiler = root / 'node_modules/.bin/tsc'
            compiler.parent.mkdir(parents=True)
            compiler.write_text('#!/bin/bash\nprintf "tsc %s\\n" "$*" >> "$TRACE"\nexit "$TOOL_EXIT"\n')
            compiler.chmod(0o755)
            if relative == 'scripts/repo/check-selection/smoke-test.sh':
                for owner in [
                    'scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh',
                    'scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh',
                    'scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh',
                    'scripts/00.chat/session-log/prepare-chat-session-before-commit/smoke-test.sh',
                    'scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh',
                    'scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh',
                ]:
                    child = root / owner
                    child.parent.mkdir(parents=True, exist_ok=True)
                    child.write_text('printf "owner ' + owner + '\n" >> "$TRACE"\nexit "$TOOL_EXIT"\n')
            trace = root / 'trace'
            result = subprocess.run(['bash', str(target), *arguments], cwd=root, capture_output=True, text=True,
                                    env={**os.environ, 'PATH': str(commands) + ':' + os.environ['PATH'],
                                         'TRACE': str(trace), 'TOOL_EXIT': str(fail)})
            return result.returncode, trace.read_text().splitlines() if trace.exists() else []

    def test_aggregate_wrappers_request_complete_registered_units(self):
        for path, identity in [
            ('scripts/repo/diagnostic-coverage/verify.sh', 'diagnostic-runtime-contracts'),
            ('scripts/repo/check-selection/smoke-test.sh', 'check-selection-regression'),
            ('scripts/04.deploy/build-platform-shell-image/check-source.sh', 'shell-package-source'),
            ('scripts/04.deploy/verify-platform-shell-infrastructure/script.sh', 'shell-infrastructure'),
        ]:
            for failure in [0, 7]:
                code, calls = self.verification_fixture(path, [], fail=failure)
                self.assertEqual(code, failure)
                self.assertEqual(calls, ['selector --aggregate-members ' + identity + ' --execute-local --json'])

    def test_runner_component_dispatch_is_closed_and_preserves_child_failure(self):
        path = 'scripts/repo/check-selection/smoke-test.sh'
        for unit in ['mechanics', 'repository-contracts']:
            for failure in [0, 7]:
                self.assertEqual(self.verification_fixture(path, ['--unit', unit], fail=failure),
                    (failure, ['python3 -B scripts/repo/check-selection/smoke-test.py --suite ' + unit]))
        for arguments in [['--unit'], ['--unit', 'unknown'], ['--unit', 'mechanics', 'extra'], ['--unknown', 'mechanics']]:
            self.assertEqual(self.verification_fixture(path, arguments), (2, []))
        # Owner branches are exact literals, not arbitrary path forwarding. Their
        # bodies remain separately registered proof; don't run them just to test
        # orchestration. The metadata contract and isolation receive source review.
        owners = {
            'harness-lifecycle': 'scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh',
            'harness-header': 'scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh',
            'harness-index': 'scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh',
            'chat-session': 'scripts/00.chat/session-log/prepare-chat-session-before-commit/smoke-test.sh',
            'chat-local-merge': 'scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh',
            'chat-main-refresh': 'scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh',
        }
        for unit, owner in owners.items():
            for failure in [0, 7]:
                self.assertEqual(self.verification_fixture(path, ['--unit', unit], fail=failure), (failure, ['owner ' + owner]))

    def test_verification_units_retain_all_original_commands(self):
        path = 'scripts/repo/diagnostic-coverage/verify.sh'
        self.assertEqual(self.verification_fixture(path, ['--unit', 'base']), (0, ['selector --aggregate-members diagnostic-base-runtime --execute-local --json']))
        code, calls = self.verification_fixture(path, ['--unit', 'catalog'])
        self.assertEqual(code, 0)
        self.assertEqual(calls[:3], [
            'tsc -p scripts/repo/diagnostic-coverage/tsconfig.json',
            'node scripts/repo/diagnostic-coverage/export-catalogs.mjs --compiled-root .cache/diagnostic-catalog-export --check',
            'python3 -B scripts/repo/diagnostic-coverage/smoke-test.py'])
        self.assertEqual(len(calls), 3)
        for unit, command in [('server', 'platform:server:check'), ('product', 'product:kanbien-platform:check'), ('cloudwatch', 'platform:adapter:aws:observability:cloudwatch:check'), ('ecs-fargate', 'platform:adapter:aws:runtime:ecs-fargate:check'), ('dynamodb-persistence', 'platform:adapter:aws:persistence:dynamodb:check'), ('sqs-queue', 'platform:adapter:aws:queue:sqs:check')]:
            self.assertEqual(self.verification_fixture(path, ['--unit', unit]), (0, ['npm --ignore-scripts run ' + command]))
            self.assertEqual(self.verification_fixture(path, ['--unit', unit], fail=7), (7, ['npm --ignore-scripts run ' + command]))
        self.assertEqual(self.verification_fixture('scripts/04.deploy/build-platform-shell-image/check-source.sh', ['--payload-only']),
                         (0, ['npm --ignore-scripts run platform:server:image-runtime-check']))
        self.assertEqual(self.verification_fixture('scripts/04.deploy/build-platform-shell-image/check-source.sh', ['--payload-only'], fail=7),
                         (7, ['npm --ignore-scripts run platform:server:image-runtime-check']))
        code, calls = self.verification_fixture(path, ['--unit', 'base'], fail=7)
        self.assertEqual(code, 7)
        self.assertEqual(len(calls), 1)

    def test_verification_units_reject_invalid_arguments_without_work(self):
        for arguments in [['--unit'], ['--unit', 'unknown'], ['--unit', 'server', 'extra'], ['--unknown', 'server']]:
            self.assertEqual(self.verification_fixture('scripts/repo/diagnostic-coverage/verify.sh', arguments), (2, []))
        for arguments in [['--payload-only', 'extra'], ['--unknown']]:
            self.assertEqual(self.verification_fixture('scripts/04.deploy/build-platform-shell-image/check-source.sh', arguments), (2, []))

    def test_each_split_package_dispatch_preserves_command_and_failure(self):
        for unit, command in [('core', 'core'), ('smoke-app', 'app:platform-smoke')] + [(name, 'platform:' + name) for name in ['contracts', 'config', 'security', 'observability', 'health', 'persistence', 'runtime', 'testing', 'workers']]:
            for failure in [0, 7]:
                self.assertEqual(self.verification_fixture('scripts/repo/diagnostic-coverage/verify.sh', ['--unit', unit], fail=failure), (failure, ['npm run ' + command + ':check']))
        code, calls = self.verification_fixture('scripts/repo/diagnostic-coverage/verify.sh', ['--unit', 'catalog'])
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 3)

    def test_split_package_dispatch_retains_npm_lifecycle_hooks(self):
        with tempfile.TemporaryDirectory(prefix='diagnostic-lifecycle-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '--quiet', directory], check=True)
            target = root / 'scripts/repo/diagnostic-coverage/verify.sh'
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'scripts/repo/diagnostic-coverage/verify.sh', target)
            (root / 'package.json').write_text(json.dumps({'scripts': {'precore:check': 'echo pre >> trace', 'core:check': 'echo check >> trace', 'postcore:check': 'echo post >> trace'}}))
            result = subprocess.run(['bash', str(target), '--unit', 'core'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / 'trace').read_text().splitlines(), ['pre', 'check', 'post'])

    def test_deployment_ci_prepares_before_unchanged_checks_and_builder_preflight(self):
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/deploy-platform-shell-staging.yml').read_text())
        steps = workflow['jobs']['build-image']['steps']
        source = next(step for step in steps if step.get('name') == 'Run platform shell checks')
        lines = source['run'].strip().splitlines()
        self.assertIn('--record-preparation', lines[0])
        self.assertIn('--checks shell-package-source shell-infrastructure shell-publication', lines[0])
        self.assertEqual(lines[1], 'bash scripts/repo/check-selection/script.sh --checks platform-shell-payload --execute-local --json')
        original = ['npm run platform:server:check', 'npm run platform:server:image-runtime-check', 'npm run product:kanbien-platform:check', 'npm run platform:shell:infrastructure:check', 'npm run platform:shell:deployment-workflow:check', 'bash scripts/04.deploy/validate-container-boundaries/script.sh']
        self.assertEqual(lines[2:], original)
        self.assertIn('bash scripts/04.deploy/build-platform-shell-image/check-source.sh', (ROOT / 'scripts/04.deploy/build-platform-shell-image/script.sh').read_text().splitlines())
        with tempfile.TemporaryDirectory(prefix='ci-source-order-') as directory:
            root = Path(directory)
            for relative in ['scripts/repo/check-selection/script.sh', 'scripts/04.deploy/validate-container-boundaries/script.sh']:
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('printf "bash %s\\n" "$*" >> "$TRACE"\nif [ "${FAIL_FOCUSED:-0}" = 1 ] && [[ "$*" == *"--checks platform-shell-payload "* ]]; then exit 7; fi\n')
            commands = root / 'bin'; commands.mkdir()
            npm = commands / 'npm'; npm.write_text('#!/bin/bash\nprintf "npm %s\\n" "$*" >> "$TRACE"\n'); npm.chmod(0o755)
            for fail in ['0', '1']:
                trace = root / ('trace-' + fail)
                result = subprocess.run(['bash', '-e', '-c', source['run']], cwd=root, env={**os.environ, 'PATH': str(commands) + ':' + os.environ['PATH'], 'TRACE': str(trace), 'FAIL_FOCUSED': fail}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 7 if fail == '1' else 0)
                calls = trace.read_text().splitlines()
                self.assertEqual(len(calls), 2 if fail == '1' else 8)
                self.assertFalse(any(call.startswith('npm ') for call in calls) if fail == '1' else False)

    def test_review_inputs_preserve_overlapping_source_and_proof_ownership(self):
        with tempfile.TemporaryDirectory(prefix="diagnostic-review-inputs-") as temporary:
            root = Path(temporary)
            review_path = root / coverage.REVIEWS
            review_path.parent.mkdir(parents=True)
            review_path.write_text(json.dumps({"schema": "repo/diagnostic-adoption/v1", "reviews": [{
                "owner": "fixture", "status": "support", "reason": "Fixture proof plumbing.",
                "sources": [{"path": "source.ts", "sha256": "a" * 64}, {"path": "proof.mjs", "sha256": "b" * 64}],
                "tests": ["proof.mjs", "test.ts", coverage.REVIEWS],
                "checks": ["fixture-check"],
            }]}))
            self.assertEqual(coverage.review_rules(root), [{
                "inputs": ["source.ts", "proof.mjs", "test.ts", coverage.REVIEWS],
                "checks": ["fixture-check"],
            }])

    def test_review_ledger_semantics_preserve_removed_and_transferred_obligations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / coverage.REVIEWS
            path.parent.mkdir(parents=True)
            def review(owner, source, check): return {'owner': owner, 'status': 'support', 'reason': 'Fixture proof plumbing.', 'sources': [{'path': source, 'sha256': 'a' * 64}], 'tests': ['deleted-proof.test.ts'], 'checks': [check]}
            old = {'schema': 'repo/diagnostic-adoption/v1', 'reviews': [review('old', 'deleted.ts', 'old-check'), review('stable', 'stable.ts', 'stable-check')]}
            current = {'schema': old['schema'], 'reviews': [review('new', 'renamed.ts', 'new-check'), old['reviews'][1]]}
            path.write_text(json.dumps(current))
            def baseline(_root, *args):
                if args[0] == 'rev-parse': return b'a' * 40
                if args[0] == 'ls-tree': return b'present'
                return json.dumps(old).encode()
            with patch.object(coverage, 'git', side_effect=baseline):
                rules = coverage.review_rules(root, ledger_changed=True, comparison_base='fixture-base')
            self.assertEqual(rules[-1], {'inputs': [coverage.REVIEWS], 'checks': ['new-check', 'old-check']})
            self.assertNotIn(coverage.REVIEWS, rules[1]['inputs'])
            with patch.object(coverage, 'git', side_effect=lambda _root, *args: b'' if args[0] == 'ls-tree' else b'a' * 40):
                self.assertEqual(coverage.review_rules(root, ledger_changed=True)[-1]['checks'], ['new-check', 'stable-check'])
            with patch.object(coverage, 'git', return_value=b'malformed'):
                with self.assertRaises(ValueError): coverage.review_rules(root, ledger_changed=True)

            # A split retains the broad former owner's obligations during the
            # transition, even when a redundant edge has no current owner.
            old = {'schema': old['schema'], 'reviews': [review('combined', 'config.ts', 'former-check')]}
            old['reviews'][0]['sources'].append({'path': 'server.ts', 'sha256': 'b' * 64})
            current = {'schema': old['schema'], 'reviews': [review('config', 'config.ts', 'config-check'), review('server', 'server.ts', 'server-check')]}
            path.write_text(json.dumps(current))
            with patch.object(coverage, 'git', side_effect=baseline):
                self.assertEqual(coverage.review_rules(root, ledger_changed=True)[-1], {
                    'inputs': [coverage.REVIEWS], 'checks': ['config-check', 'former-check', 'server-check']})

    def test_independent_platform_capability_reviews_keep_ownership_and_shared_proof(self):
        reviews = coverage.review_document(json.loads((ROOT / coverage.REVIEWS).read_text()))
        # Guard these existing independent responsibilities, not arbitrary future
        # integrated capabilities or immutable hashes of evolving implementations.
        expected = {
            'config': ['diagnostics.ts', 'index.ts'],
            'observability': ['diagnostic-log.ts', 'diagnostics.ts', 'index.ts', 'logging.ts', 'readiness-observation.ts'],
            'persistence': ['diagnostics.ts', 'errors.ts', 'index.ts', 'observability/integration.ts'],
            'server': ['diagnostics.ts', 'index.ts', 'main.ts'],
            'workers': ['diagnostics.ts', 'errors.ts', 'index.ts', 'worker.ts'],
        }
        by_source = {source['path']: review for review in reviews for source in review['sources']}
        owners = {}
        for capability, paths in expected.items():
            entries = [by_source[f'platform/{capability}/src/{path}'] for path in paths]
            self.assertTrue(all(entry == entries[0] for entry in entries), capability)
            owners[capability] = entries[0]
            self.assertEqual(entries[0]['status'], 'partial', capability)
            self.assertTrue(entries[0]['remaining_debt'], capability)
            self.assertIn('diagnostic-catalog-readers', entries[0]['checks'])
        self.assertEqual(len({entry['owner'] for entry in owners.values()}), 5,
                         'Independent platform source owners must not become one shared review binding.')
        self.assertEqual(set(owners['config']['checks']), {'platform-config-runtime', 'diagnostic-catalog-readers'})
        for capability in ['persistence', 'server', 'workers']:
            self.assertEqual(set(owners[capability]['checks']), {f'platform-{capability}-runtime', 'diagnostic-catalog-readers'})
        self.assertEqual(set(owners['observability']['checks']), {
            'platform-observability-runtime', 'platform-persistence-runtime', 'platform-server-runtime',
            'platform-workers-runtime', 'platform-health-runtime', 'diagnostic-catalog-readers'})
        self.assertIn('platform/health/tests/platform-health-runtime.test.ts', owners['observability']['tests'])
        for capability in ['server', 'workers']:
            self.assertIn('platform/config/src/diagnostics.ts', owners[capability]['definitions'])
        self.assertIn('platform/security/src/diagnostics.ts', owners['server']['definitions'])
        for capability in ['persistence', 'security']:
            self.assertIn(f'platform/{capability}/src/diagnostics.ts', owners['observability']['definitions'])
        # Configuration predicates and security mechanisms retain their own
        # proof owners; their debt/status must not be absorbed by this split.
        self.assertTrue(any('platform/observability/tests/configuration-runtime.test.ts' in entry['tests']
                            and 'platform/observability/src/configuration.ts' in entry.get('definitions', [])
                            and 'platform-observability-runtime' in entry['checks'] for entry in reviews))
        self.assertTrue(any('platform/security/src/diagnostics.ts' in [source['path'] for source in entry['sources']]
                            and 'platform-security-runtime' in entry['checks'] for entry in reviews))

    def test_security_adapter_selection_rejects_unsupported_arguments(self):
        for arguments in [["--security-adapter"], ["--security-adapter", "unregistered"], ["--security-adapter", "cognito", "extra"]]:
            result = subprocess.run(["bash", str(ROOT / "scripts/repo/diagnostic-coverage/verify.sh"), *arguments], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)

    def test_ordinary_service_and_changed_legacy_cannot_escape(self):
        with tempfile.TemporaryDirectory(prefix="diagnostic-discovery-") as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet", temporary], check=True)
            (root / "package.json").write_text(json.dumps({"workspaces": ["services/*"]}))
            source = root / "platform/old/src/call.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const legacy = true;\n")
            legacy_cli = root / "bin/existing.js"
            legacy_cli.parent.mkdir()
            legacy_cli.write_text("module.exports = true;\n")
            subprocess.run(["git", "-C", temporary, "add", "."], check=True)
            subprocess.run(["git", "-C", temporary, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture baseline"], check=True)
            baseline = coverage.git(root, "rev-parse", "HEAD").decode().strip()
            previous = coverage.BASELINE
            coverage.BASELINE = baseline
            try:
                review_path = root / coverage.REVIEWS
                review_path.parent.mkdir(parents=True)
                (root / "scripts/repo/check-selection").mkdir()
                (root / "scripts/repo/check-selection/checks.yml").write_text("checks: {fixture: {stage: local}}\n")
                document = {"schema": "repo/diagnostic-adoption/v1", "baseline": baseline, "reviews": []}
                review_path.write_text(json.dumps(document))
                report = coverage.validate(root)
                self.assertIn(source.relative_to(root).as_posix(), report["legacy_debt"])
                self.assertIn("bin/existing.js", report["legacy_debt"])
                cli = root / "bin/new.js"
                cli.write_text("module.exports = false;\n")
                self.assertIn("bin/new.js", coverage.discover(root))
                self.assertIn("bin/new.js", {item["path"] for item in coverage.validate(root)["findings"]})
                legacy_cli.write_text("module.exports = false;\n")
                self.assertIn("bin/existing.js", {item["path"] for item in coverage.validate(root)["findings"]})
                service = root / "services/new/client.ts"
                service.parent.mkdir(parents=True)
                service.write_text("export const call = () => false;\n")
                (service.parent / "package.json").write_text('{"name":"new-service"}')
                self.assertIn("services/new/client.ts", coverage.discover(root))
                self.assertIn("services/new/client.ts", {item["path"] for item in coverage.validate(root)["findings"]})
                source.write_text("export const legacy = false;\n")
                self.assertIn("platform/old/src/call.ts", {item["path"] for item in coverage.validate(root)["findings"]})
                proof = root / "proof.test.ts"
                proof.write_text("// Fixture proof reference.\n")
                document["reviews"] = [{"owner": "fixture", "status": "partial", "reason": "Review the changed operation without hiding legacy debt.", "remaining_debt": ["Precise remote outcome mapping remains unadopted."], "tests": ["proof.test.ts"], "checks": ["fixture"], "sources": [{"path": item.relative_to(root).as_posix(), "sha256": hashlib.sha256(item.read_bytes()).hexdigest()} for item in [source, service, cli, legacy_cli]]}]
                review_path.write_text(json.dumps(document))
                self.assertEqual(coverage.validate(root)["verdict"], "passed")
                service.write_text("export const call = () => true;\n")
                self.assertIn("diagnostic-review-stale", {item["code"] for item in coverage.validate(root)["findings"]})
                self.assertEqual(coverage.review_rules(root)[0]["checks"], ["fixture"])
            finally:
                coverage.BASELINE = previous

class ReaderTests(unittest.TestCase):
    def test_config_local_catalogue_preserves_aggregate_and_reader_boundaries(self):
        local = ROOT / 'packages/core/src/config/contract/reporting/diagnostics.v1.json'
        module = json.loads(local.read_text())
        aggregate = json.loads(reader.CORE_CATALOG.read_text())
        self.assertEqual(module['schema'], aggregate['schema'])
        self.assertEqual(module['delivery'], aggregate['delivery'])
        self.assertEqual(module['catalog']['owner'], 'core.config')
        self.assertEqual(module['catalog']['definitions'], [
            definition for definition in aggregate['catalog']['definitions']
            if definition['code'].startswith('core.config.')])
        self.assertEqual(len(module['catalog']['definitions']), 5)
        samples = [
            ('core.config.primitive-invalid', {'field': 'value', 'reader': 'number', 'reason': 'wrong-type'}),
            ('core.config.source-threw', {'reader': 'schema', 'phase': 'source-read', 'reason': 'invocation-threw', 'index': 1}),
            ('core.config.declaration-invalid', {'field': 'bounds', 'reason': 'reversed'}),
            ('core.config.relationship-declaration-invalid', {'field': 'participants', 'reason': 'self-reference'}),
            ('core.config.choice-declaration-invalid', {'reason': 'duplicate', 'index': 1}),
        ]
        for code, detail in samples:
            record = {'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail}
            self.assertEqual(reader.validate_record(record, local), record)
            self.assertEqual(reader.validate_record(record, reader.CORE_CATALOG), record)
            for mutation in [
                {**record, 'definitionVersion': 2},
                {**record, 'detail': {**detail, 'private': 'synthetic-private-canary'}},
                {**record, 'detail': {**detail, 'reason': 'synthetic-private-canary'}},
            ]:
                for catalog in [local, reader.CORE_CATALOG]:
                    with self.assertRaises(reader.DiagnosticContractError):
                        reader.validate_record(mutation, catalog)
        unrelated = {'schema': 'core/diagnostic-record/v1', 'code': 'core.shared.source-threw',
                     'definitionVersion': 1, 'detail': {}}
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_record(unrelated, local)
        # Config selection does not grant a native operation reader new meanings.
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_operation_record({'schema': 'core/diagnostic-record/v1',
                'code': samples[0][0], 'definitionVersion': 1, 'detail': samples[0][1]}, 'readiness')

    def test_maintenance_instruction_reader_preserves_closed_task_records(self):
        local = ROOT / 'platform/persistence/src/maintenance/contract/reporting/diagnostics.v1.json'
        selected = json.loads(local.read_text())['catalog']['definitions']
        self.assertEqual({entry['code'] for entry in selected}, {
            'persistence.migration-instructions-invalid', 'persistence.verification-instructions-invalid'})
        cases = [('persistence.migration-instructions-invalid', 'migration.operation', reason)
                 for reason in ['wrong-type', 'blank', 'surrounding-whitespace', 'unsupported-value']]
        cases += [('persistence.verification-instructions-invalid', 'verification.mode', 'unsupported-value')]
        cases += [('persistence.verification-instructions-invalid', setting, reason)
                  for setting in ['verification.expected-record-id', 'verification.expected-fingerprint']
                  for reason in ['missing', 'wrong-type', 'blank', 'surrounding-whitespace', 'invalid-format']]
        self.assertEqual(len(cases), 15)
        for code, setting, reason in cases:
            record = {'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1,
                      'detail': {'issues': [{'setting': setting, 'reason': reason}]}}
            self.assertEqual(reader.validate_record(record, local), record)
            self.assertEqual(reader.validate_record(record, reader.PERSISTENCE_CATALOG), record)
            self.assertEqual(reader.validate_configuration_record(record), record)
            self.assertEqual(deployment.validate_runtime_diagnostic(record), record)
            for bad in [{**record, 'definitionVersion': 2},
                        {**record, 'detail': {'issues': [{'setting': 'physical-private-source', 'reason': reason}]}},
                        {**record, 'detail': {'issues': [{'setting': setting, 'reason': 'private-unrecognised-reason'}]}},
                        {**record, 'detail': {**record['detail'], 'value': 'synthetic-private-canary'}}]:
                with self.assertRaises(reader.DiagnosticContractError):
                    reader.validate_configuration_record(bad)
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_operation_record(record, 'migration')

    def test_sqs_configuration_explicit_catalogue_reader_and_family_restrictions(self):
        local = ROOT / 'platform/adapters/aws/queue/sqs/src/configuration/contract/reporting/diagnostics.v1.json'
        definitions = json.loads(local.read_text())['catalog']['definitions']
        self.assertEqual([item['code'] for item in definitions], [
            'aws-sqs.sender-configuration-invalid', 'aws-sqs.worker-configuration-invalid',
            'aws-sqs.sender-configuration-source-failed', 'aws-sqs.worker-configuration-source-failed'])
        records = []
        for role, settings in [('sender', ['queue.address', 'queue.region']),
                               ('worker', ['queue.address', 'queue.region', 'queue.receive-wait', 'queue.visibility-timeout'])]:
            for setting in settings:
                reasons = ['missing', 'wrong-type', 'blank', 'surrounding-whitespace']
                if setting in ['queue.receive-wait', 'queue.visibility-timeout']:
                    reasons += ['invalid-integer', 'out-of-range']
                records += [{'schema': 'core/diagnostic-record/v1', 'code': f'aws-sqs.{role}-configuration-invalid',
                             'definitionVersion': 1, 'detail': {'issues': [{'setting': setting, 'reason': reason}]}}
                            for reason in reasons]
                records.append({'schema': 'core/diagnostic-record/v1', 'code': f'aws-sqs.{role}-configuration-source-failed',
                                'definitionVersion': 1, 'detail': {'phase': 'configuration-source-read', 'source': setting,
                                'reason': 'unclassified-read-failure', 'effect': 'not-assessed'}})
        for record in records:
            self.assertEqual(reader.validate_record(record, local), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
        malformed = []
        for record in records:
            malformed.extend([{**record, 'definitionVersion': 2},
                              {**record, 'detail': {**record['detail'], 'value': 'PRIVATE_SQS_VALUE'}},
                              {**record, 'detail': {**record['detail'], 'reason': 'read-denied'}}])
        malformed += [{**records[0], 'detail': {'issues': [{'setting': 'PHYSICAL_PRIVATE_NAME', 'reason': 'missing'}]}},
                      {**records[0], 'detail': {'issues': [{'setting': 'queue.receive-wait', 'reason': 'missing'}]}}]
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(record, local)
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const x=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(x.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(x.records.map(record=>{const d=defs.find(d=>d.code===record.code&&d.version===record.definitionVersion);return !!d&&parseDiagnosticRecord(d,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], cwd=ROOT, input=json.dumps({'catalog': str(local), 'records': records + malformed}),
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_jwt_configuration_catalogue_readers(self):
        local = ROOT / 'platform/security/src/jwt-configuration/contract/reporting/diagnostics.v1.json'
        document = json.loads(local.read_text())
        self.assertEqual([item['code'] for item in document['catalog']['definitions']], ['security.jwt-configuration-invalid'])
        record = {'schema': 'core/diagnostic-record/v1', 'code': 'security.jwt-configuration-invalid', 'definitionVersion': 1,
                  'detail': {'phase': 'verifier-construction', 'effect': 'verifier-not-created',
                             'issues': [{'setting': 'clock-tolerance', 'reason': 'not-finite'}], 'truncated': False}}
        self.assertEqual(reader.validate_record(record, local), record)
        self.assertEqual(reader.validate_record(record, reader.SECURITY_CATALOG), record)
        self.assertEqual(reader.validate_selected_record(record), record)
        with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'migration')
        with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
        bad = [{**record, 'definitionVersion': 2}, {**record, 'detail': {**record['detail'], 'value': 'PRIVATE_JWT_CANARY'}},
               {**record, 'detail': {**record['detail'], 'issues': [{'setting': 'PRIVATE_JWT_CANARY', 'reason': 'missing'}]}},
               {**record, 'detail': {**record['detail'], 'issues': [{'setting': 'issuer', 'reason': 'PRIVATE_JWT_CANARY'}]}}]
        for value in bad:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(value, local)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const core=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {jwtConfigurationDiagnostic}=require(path.join(root,'platform/security/src/jwt-configuration/index.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(record=>core.parseDiagnosticRecord(jwtConfigurationDiagnostic,record).ok)));"
        output = subprocess.run(['node', '-e', javascript], cwd=ROOT, input=json.dumps([record, *bad]), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(output.stdout), [True] + [False] * len(bad))

    def test_worker_retry_and_lease_configuration_readers(self):
        cases = [
            ('platform/workers/src/configuration/contract/reporting/diagnostics.v1.json', reader.WORKER_CATALOG,
             'platform-worker.retry-configuration-invalid', {'operation': 'configure-worker', 'phase': 'configuration',
             'issues': [{'setting': 'max-attempts', 'reason': 'not-positive'}], 'effect': 'worker-not-created'}),
            ('platform/workers/src/configuration/contract/reporting/diagnostics.v1.json', reader.WORKER_CATALOG,
             'platform-worker.retry-delay-invalid', {'operation': 'job-delivery', 'phase': 'backoff',
             'setting': 'retry-delay', 'reason': 'negative', 'effect': 'retry-not-submitted'}),
            ('platform/persistence/src/leasing/contract/reporting/diagnostics.v1.json', reader.PERSISTENCE_CATALOG,
             'persistence.relay-configuration-invalid', {'operation': 'configure-relay', 'phase': 'configuration',
             'setting': 'lease-duration', 'reason': 'missing', 'effect': 'relay-not-created'}),
        ]
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const x=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(x.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(x.records.map(record=>{const d=defs.find(d=>d.code===record.code&&d.version===record.definitionVersion);return !!d&&parseDiagnosticRecord(d,record).ok})));"
        for relative, aggregate, code, detail in cases:
            local = ROOT / relative
            record = {'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail}
            self.assertEqual(reader.validate_record(record, local), record)
            self.assertEqual(reader.validate_record(record, aggregate), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'migration')
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            malformed = [{**record, 'definitionVersion': 2},
                         {**record, 'detail': {**detail, 'value': 'PRIVATE_RETRY_CANARY'}},
                         {**record, 'detail': {**detail, 'effect': 'work-succeeded'}}]
            if 'issues' in detail:
                malformed.append({**record, 'detail': {**detail, 'issues': [{'setting': 'max-attempts', 'reason': 'PRIVATE_RETRY_CANARY'}]}})
            else:
                malformed.append({**record, 'detail': {**detail, 'reason': 'PRIVATE_RETRY_CANARY'}})
            for value in malformed:
                with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(value, local)
            result = subprocess.run(['node', '-e', javascript], cwd=ROOT,
                                    input=json.dumps({'catalog': str(local), 'records': [record, *malformed]}),
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), [True] + [False] * len(malformed))

    def test_config_export_generation_assets_staleness_and_conflicts(self):
        # Use the compilation already owned by this registered catalogue unit.
        # All regeneration/mutation happens in a disposable tree, never ROOT.
        compiled = ROOT / '.cache/diagnostic-catalog-export'
        git_directory = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory(prefix='config-catalogue-export-') as temporary:
            root = Path(temporary)
            for relative in ['scripts/repo/diagnostic-coverage/export-catalogs.mjs',
                             'scripts/repo/diagnostic-coverage/compatibility.mjs', 'packages/core/package.json', 'platform/persistence/package.json', 'platform/security/package.json', 'platform/workers/package.json',
                             'platform/adapters/aws/queue/sqs/package.json']:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            output = root / 'compiled'
            shutil.copytree(compiled, output)
            env = {**os.environ, 'GIT_DIR': git_directory, 'NODE_PATH': str(ROOT / 'node_modules')}
            command = ['node', str(root / 'scripts/repo/diagnostic-coverage/export-catalogs.mjs'), '--compiled-root', str(output)]
            def run(*arguments):
                result = subprocess.run([*command, *arguments], cwd=root, env=env, capture_output=True, text=True)
                self.assertIn(result.returncode, [0, 1], result.stderr)
                self.assertTrue(result.stdout, result.stderr)
                return result.returncode, json.loads(result.stdout)
            self.assertEqual(run()[0], 0)
            aggregate = root / 'packages/core/contracts/diagnostics.v1.json'
            self.assertEqual(aggregate.read_bytes(), reader.CORE_CATALOG.read_bytes())
            local = root / 'packages/core/src/config/contract/reporting/diagnostics.v1.json'
            expected = local.read_bytes()
            self.assertEqual(run()[0], 0)
            self.assertEqual(local.read_bytes(), expected, 'generation is deterministic')
            self.assertEqual(run('--check')[0], 0)
            public_access = """
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { readFileSync } = require('node:fs');
const from = createRequire(process.argv[1]);
const config = from('@kanbien/core/config');
const json = from('@kanbien/core/config/diagnostics.v1.json');
assert.equal(config.coreConfigDiagnosticCatalog.owner, 'core.config');
assert.deepEqual(json.catalog, config.coreConfigDiagnosticCatalog);
assert.equal(readFileSync(from.resolve('@kanbien/core/config/diagnostics.v1.json'), 'utf8'), readFileSync(process.argv[2], 'utf8'));
assert.throws(() => from('@kanbien/core/config/contract/reporting/diagnostics'), {code: 'ERR_PACKAGE_PATH_NOT_EXPORTED'});
const persistence = from('@kanbien/platform-persistence');
const maintenance = from('@kanbien/platform-persistence/maintenance/diagnostics.v1.json');
assert.deepEqual(maintenance.catalog, persistence.persistenceMaintenanceDiagnosticCatalog);
assert.equal(maintenance.catalog.definitions.length, 2);
assert.throws(() => from('@kanbien/platform-persistence/src/maintenance/contract/reporting/diagnostics'), {code: 'ERR_PACKAGE_PATH_NOT_EXPORTED'});
const sqs = from('@kanbien/platform-adapter-aws-queue-sqs');
const sqsJson = from('@kanbien/platform-adapter-aws-queue-sqs/configuration/diagnostics.v1.json');
assert.deepEqual(sqsJson.catalog, sqs.sqsConfigurationDiagnosticCatalog);
assert.equal(sqsJson.catalog.definitions.length, 4);
assert.throws(() => from('@kanbien/platform-adapter-aws-queue-sqs/src/configuration/contract/reporting/diagnostics'), {code: 'ERR_PACKAGE_PATH_NOT_EXPORTED'});
const contracts = from('@kanbien/platform-contracts');
assert.equal(contracts.validatePlatformDiagnosticCatalog(sqsJson.catalog).ok, true);
const binding = contracts.bindPlatformDiagnosticContext({capability: 'queue', operation: 'startup', stage: 'configuration'}, sqs.sqsConfigurationDiagnosticCatalog.definitions);
const failure = sqs.validateSqsSenderConfiguration({get() { return undefined; }});
assert.equal(failure.ok, false);
const selected = binding.select(failure.error.diagnosticRecord);
assert.deepEqual(selected.context, {capability: 'queue', operation: 'startup', stage: 'configuration'});
const delivered = [];
const reporter = from('@kanbien/platform-observability').createPlatformDiagnosticReporter({catalogs: [sqs.sqsConfigurationDiagnosticCatalog],
  clock: {now() { return new Date('2026-11-04T00:00:00Z'); }}, logger: {write(record) {delivered.push(record);}}});
assert.equal(reporter.report(selected.record, selected.context).status, 'written');
assert.deepEqual(delivered[0].fields.diagnostic, failure.error.diagnosticRecord);
assert.equal(delivered[0].fields.capability, 'queue');
const security = from('@kanbien/platform-security');
const jwtJson = from('@kanbien/platform-security/jwt-configuration/diagnostics.v1.json');
assert.deepEqual(jwtJson.catalog, security.jwtConfigurationDiagnosticCatalog);
assert.equal(jwtJson.catalog.definitions.length, 1);
assert.throws(() => from('@kanbien/platform-security/src/jwt-configuration/contract/reporting/diagnostics'), {code: 'ERR_PACKAGE_PATH_NOT_EXPORTED'});
const configuration = security.validateJwtVerifierConfiguration({issuer: 'issuer', jwksUri: 'https://example.invalid/keys', clockSkewSeconds: NaN});
assert.equal(configuration.ok, false);
const constructionFailure = security.jwtConfigurationError(configuration.error.diagnosticRecord);
assert.deepEqual(security.securityDiagnosticRecordsFrom(constructionFailure), [configuration.error.diagnosticRecord]);
const jwtBinding = contracts.bindPlatformDiagnosticContext({capability: 'security', operation: 'verifier-construction', stage: 'configuration'}, security.jwtConfigurationDiagnosticCatalog.definitions);
const jwtSelected = jwtBinding.select(configuration.error.diagnosticRecord);
const jwtLogs = [];
const jwtReporter = from('@kanbien/platform-observability').createPlatformDiagnosticReporter({catalogs: [security.jwtConfigurationDiagnosticCatalog],
  clock: {now() { return new Date('2026-11-04T00:00:00Z'); }}, logger: {write(record) {jwtLogs.push(record);}}});
assert.equal(jwtReporter.report(jwtSelected.record, jwtSelected.context).status, 'written');
assert.deepEqual(jwtLogs[0].fields.diagnostic, configuration.error.diagnosticRecord);
from('@kanbien/platform-observability').reportPlatformDiagnostic({report() {throw Error('PRIVATE_SINK_CANARY');}}, jwtSelected.record, jwtSelected.context);
assert.equal(security.isJwtConfigurationError(constructionFailure), true);
const workers = from('@kanbien/platform-workers');
for (const [name, publicPath, privatePath, catalog, count] of [
  ['workers', '@kanbien/platform-workers/configuration/diagnostics.v1.json', '@kanbien/platform-workers/src/configuration/contract/reporting/diagnostics', workers.workerRetryConfigurationDiagnosticCatalog, 2],
  ['leasing', '@kanbien/platform-persistence/leasing/diagnostics.v1.json', '@kanbien/platform-persistence/src/leasing/contract/reporting/diagnostics', persistence.persistenceLeasingDiagnosticCatalog, 1],
]) {
  assert.deepEqual(from(publicPath).catalog, catalog);
  assert.equal(catalog.definitions.length, count);
  assert.equal(contracts.validatePlatformDiagnosticCatalog(catalog).ok, true);
  assert.throws(() => from(privatePath), {code: 'ERR_PACKAGE_PATH_NOT_EXPORTED'});
}
const leaseError = persistence.persistenceRelayConfigurationError('not-positive');
assert.deepEqual(persistence.selectPlatformPersistenceDiagnosticEvidence({}, leaseError).diagnosticRecord, leaseError.diagnosticRecord);
const retryFailure = workers.validateWorkerRetryConfiguration({maxAttempts: 0});
assert.equal(retryFailure.ok, false);
const retryLogs = [];
const retryReporter = from('@kanbien/platform-observability').createPlatformDiagnosticReporter({catalogs: [workers.workerRetryConfigurationDiagnosticCatalog],
  clock: {now() {return new Date('2026-11-04T00:00:00Z');}}, logger: {write(record) {retryLogs.push(record);}}});
assert.equal(retryReporter.report(retryFailure.error.diagnosticRecord, {capability: 'platform-worker', operation: 'configure', stage: 'configuration'}).status, 'written');
assert.deepEqual(retryLogs[0].fields.diagnostic, retryFailure.error.diagnosticRecord);
"""
            access = subprocess.run(['node', '-e', public_access, str(output / 'consumer.cjs'), str(local)],
                                    cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(access.returncode, 0, access.stderr)
            # Missing, omitted and extra definitions must all fail freshness.
            for definitions in [[], json.loads(expected)['catalog']['definitions'][:-1],
                                json.loads(expected)['catalog']['definitions'] * 2]:
                changed = json.loads(expected)
                changed['catalog']['definitions'] = definitions
                local.write_text(json.dumps(changed))
                self.assertEqual(run('--check'), (1, {'schema': 'repo/diagnostic-export-report/v1',
                    'verdict': 'failed', 'code': 'diagnostic-contract-export-stale'}))
            local.unlink()
            self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            self.assertEqual(run()[0], 0)
            maintenance_local = root / 'platform/persistence/src/maintenance/contract/reporting/diagnostics.v1.json'
            maintenance_expected = maintenance_local.read_bytes()
            for definitions in [[], json.loads(maintenance_expected)['catalog']['definitions'][:-1],
                                json.loads(maintenance_expected)['catalog']['definitions'] * 2]:
                changed = json.loads(maintenance_expected)
                changed['catalog']['definitions'] = definitions
                maintenance_local.write_text(json.dumps(changed))
                self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            maintenance_local.unlink()
            self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            self.assertEqual(run()[0], 0)
            self.assertEqual(maintenance_local.read_bytes(), maintenance_expected)
            sqs_local = root / 'platform/adapters/aws/queue/sqs/src/configuration/contract/reporting/diagnostics.v1.json'
            sqs_expected = sqs_local.read_bytes()
            for definitions in [[], json.loads(sqs_expected)['catalog']['definitions'][:-1],
                                json.loads(sqs_expected)['catalog']['definitions'] * 2]:
                changed = json.loads(sqs_expected)
                changed['catalog']['definitions'] = definitions
                sqs_local.write_text(json.dumps(changed))
                self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            sqs_local.unlink()
            self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            self.assertEqual(run()[0], 0)
            self.assertEqual(sqs_local.read_bytes(), sqs_expected)
            jwt_local = root / 'platform/security/src/jwt-configuration/contract/reporting/diagnostics.v1.json'
            jwt_expected = jwt_local.read_bytes()
            for definitions in [[], json.loads(jwt_expected)['catalog']['definitions'] * 2]:
                changed = json.loads(jwt_expected)
                changed['catalog']['definitions'] = definitions
                jwt_local.write_text(json.dumps(changed))
                self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            jwt_local.unlink()
            self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
            self.assertEqual(run()[0], 0)
            self.assertEqual(jwt_local.read_bytes(), jwt_expected)
            for relative in ['platform/persistence/src/leasing/contract/reporting/diagnostics.v1.json',
                             'platform/workers/src/configuration/contract/reporting/diagnostics.v1.json']:
                local_catalogue = root / relative
                original_catalogue = local_catalogue.read_bytes()
                for definitions in [[], json.loads(original_catalogue)['catalog']['definitions'] * 2]:
                    changed = json.loads(original_catalogue)
                    changed['catalog']['definitions'] = definitions
                    local_catalogue.write_text(json.dumps(changed))
                    self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
                local_catalogue.unlink()
                self.assertEqual(run('--check')[1]['code'], 'diagnostic-contract-export-stale')
                self.assertEqual(run()[0], 0)
                self.assertEqual(local_catalogue.read_bytes(), original_catalogue)
            # Conflicting same-code/version definitions block writes before any
            # otherwise stale output is regenerated.
            module = output / 'packages/core/src/config/contract/reporting/diagnostics.js'
            module.write_text(module.read_text() + '''
exports.coreConfigDiagnosticCatalog = {owner: 'core.config', definitions: [
  exports.coreConfigDiagnosticDefinitions[0],
  {...exports.coreConfigDiagnosticDefinitions[0], detail: {type: 'boolean'}}
]};
''')
            local.write_text('stale fixture sentinel\n')
            self.assertEqual(run()[1]['code'], 'diagnostic-definition-version-conflict')
            self.assertEqual(local.read_text(), 'stale fixture sentinel\n')
            self.assertEqual(aggregate.read_bytes(), reader.CORE_CATALOG.read_bytes())

    def test_configuration_selection_and_loading_declaration_are_closed_additive_records(self):
        selection = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.persistence-implementation-invalid",
                     "definitionVersion": 1, "detail": {"phase": "implementation-selection", "reason": "unsupported", "effect": "not-started"}}
        self.assertEqual(reader.validate_configuration_record(selection), selection)
        unsafe = copy.deepcopy(selection)
        unsafe["detail"]["reason"] = "synthetic-private-selection"
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_configuration_record(unsafe)
        loading = {"schema": "core/diagnostic-record/v1", "code": "platform-config.loading-declaration-invalid",
                   "definitionVersion": 1, "detail": {"field": "bindings", "reason": "identity-count-mismatch", "effect": "not-started"}}
        catalog = ROOT / "platform/config/contracts/diagnostics.v1.json"
        self.assertEqual(reader.validate_record(loading, catalog), loading)
        unsafe = copy.deepcopy(loading)
        unsafe["detail"]["source"] = "synthetic-private-source"
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_record(unsafe, catalog)

    def test_task_and_postgresql_observations_have_explicit_literal_reader_parity(self):
        cases = [
            (reader.PERSISTENCE_TASK_OPERATION_CATALOG, 'administration',
             'kanbien-core-server.operations.administration-predicate-rejected',
             {'task': 'administration', 'operation': 'role-identifier', 'field': 'identifier',
              'condition': 'pattern', 'effect': 'predicate-rejected'}),
            (reader.PERSISTENCE_TASK_OPERATION_CATALOG, 'administration',
             'kanbien-core-server.operations.administration-boundary-failed',
             {'task': 'administration', 'operation': 'administration', 'phase': 'pool-connect',
              'condition': 'threw', 'effect': 'unknown'}),
            (reader.PERSISTENCE_TASK_OPERATION_CATALOG, 'verification',
             'kanbien-core-server.operations.verification-predicate-rejected',
             {'task': 'verification', 'operation': 'verification', 'field': 'base-url',
              'condition': 'missing', 'effect': 'predicate-rejected'}),
            (reader.PERSISTENCE_TASK_OPERATION_CATALOG, 'verification',
             'kanbien-core-server.operations.verification-boundary-failed',
             {'task': 'verification', 'operation': 'verification', 'phase': 'fetch',
              'condition': 'rejected', 'effect': 'unknown'}),
            (reader.PLATFORM_POSTGRESQL_OPERATION_CATALOG, None,
             'kanbien-platform.postgresql.composition-boundary-failed',
             {'operation': 'compose', 'phase': 'schema-predicate',
              'condition': 'predicate-rejected', 'effect': 'not-started'}),
        ]
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(input.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(input.records.map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        for catalog, task, code, detail in cases:
            record = {'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail}
            self.assertEqual(reader.validate_record(record, catalog), record)
            if task is None:
                self.assertEqual(reader.validate_selected_record(record), record)
                with self.assertRaises(reader.DiagnosticContractError):
                    reader.validate_persistence_task_observation(record, 'administration')
            else:
                self.assertEqual(reader.validate_persistence_task_observation(record, task), record)
                with self.assertRaises(reader.DiagnosticContractError):
                    reader.validate_persistence_task_observation(record, 'verification' if task == 'administration' else 'administration')
                with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'administration')
            malformed = [
                {**record, 'definitionVersion': 999}, {**record, 'detail': {}},
                {**record, 'detail': {**detail, 'value': 'private-task-postgresql-parity-canary'}},
                {**record, 'detail': {**detail, 'effect': 'succeeded'}},
                {**record, 'detail': {**detail, 'condition': 'provider-definitely-rejected'}},
            ]
            for rejected in malformed:
                with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(rejected, catalog)
            checked = subprocess.run(['node', '-e', javascript], input=json.dumps({
                'catalog': str(catalog.relative_to(ROOT)), 'records': [record, *malformed]}),
                capture_output=True, text=True, check=True, cwd=ROOT)
            self.assertEqual(json.loads(checked.stdout), [True, *([False] * len(malformed))])

    def test_identity_boundaries_have_literal_selected_parity_without_reader_widening(self):
        cases = [
            (reader.CORE_CATALOG, 'core.authn.boundary-failed',
             {'operation': 'principal', 'phase': 'claims-enumeration', 'field': 'claims', 'reason': 'threw', 'effect': 'value-not-produced'}),
            (reader.CORE_CATALOG, 'core.tenancy.boundary-failed',
             {'operation': 'tenant-context', 'phase': 'input-projection', 'field': 'isolation-key', 'reason': 'threw', 'effect': 'value-not-produced'}),
            (reader.SECURITY_CATALOG, 'security.authentication.principal-boundary-failed',
             {'operation': 'principal-from-authentication', 'phase': 'input-projection', 'field': 'subject', 'reason': 'threw', 'effect': 'value-not-produced'}),
        ]
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(input.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(input.records.map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        for catalog, code, detail in cases:
            record = {'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail}
            self.assertEqual(reader.validate_record(record, catalog), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'readiness')
            malformed = [
                {**record, 'definitionVersion': 999}, {**record, 'detail': {}},
                {**record, 'detail': {**detail, 'value': 'private-identity-parity-canary'}},
                {**record, 'detail': {**detail, 'field': 'private-identity-parity-canary'}},
                {**record, 'detail': {**detail, 'effect': 'authenticated'}},
                {**record, 'detail': {**detail, 'reason': 'credential-invalid'}},
            ]
            for rejected in malformed:
                with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(rejected)
            checked = subprocess.run(['node', '-e', javascript], input=json.dumps({'catalog': str(catalog.relative_to(ROOT)), 'records': [record, *malformed]}), capture_output=True, text=True, check=True, cwd=ROOT)
            self.assertEqual(json.loads(checked.stdout), [True, *([False] * len(malformed))])

    def test_translation_localization_predicates_and_selection_have_closed_parity(self):
        cases = [
            ('core.i18n.validation-rejected', {'operation': 'interpolate', 'field': 'parameter', 'reason': 'missing-own-property', 'ordinal': 3, 'effect': 'predicate-rejected'}),
            ('core.i18n.selection-observed', {'operation': 'translate', 'phase': 'source-selection', 'selection': 'fallback-catalog', 'reason': 'candidate-present', 'ordinal': 1, 'catalogMisses': 1, 'templateMisses': 0, 'effect': 'source-selected'}),
            ('core.i18n.boundary-failed', {'operation': 'interpolate', 'phase': 'parameter-coercion', 'field': 'parameter', 'ordinal': 2, 'reason': 'threw', 'effect': 'value-not-produced'}),
            ('core.localization.validation-rejected', {'operation': 'number', 'field': 'minimum-fraction-digits', 'reason': 'not-integer', 'effect': 'predicate-rejected'}),
            ('core.localization.unsupported-observed', {'operation': 'format', 'phase': 'implementation-selection', 'reason': 'unsupported-implementation', 'effect': 'format-not-performed'}),
            ('core.localization.boundary-failed', {'operation': 'format', 'phase': 'reason-projection', 'field': 'default-message', 'reason': 'threw', 'effect': 'value-not-produced'}),
            ('core.localization.validation-rejected', {'operation': 'time-zone-id', 'field': 'time-zone', 'reason': 'parent-sequence-rejected', 'effect': 'predicate-rejected'}),
            ('core.i18n.selection-observed', {'operation': 'translate', 'phase': 'source-selection', 'selection': 'default-message', 'reason': 'no-candidate-match', 'catalogMisses': 2, 'templateMisses': 1, 'effect': 'source-selected'}),
        ]
        records = [{'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail} for code, detail in cases]
        malformed = []
        for record in records:
            self.assertEqual(reader.validate_record(record, reader.CORE_CATALOG), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'readiness')
            malformed.extend([
                {**record, 'definitionVersion': 999},
                {**record, 'detail': {**record['detail'], 'value': 'private-translation-canary'}},
                {**record, 'detail': {}},
                {**record, 'detail': {**record['detail'], 'effect': 'rendered-successfully'}},
            ])
        malformed.extend([
            {**records[0], 'detail': {**records[0]['detail'], 'ordinal': -1}},
            {**records[1], 'detail': {**records[1]['detail'], 'catalogMisses': 9007199254740992}},
            {**records[1], 'detail': {**records[1]['detail'], 'templateMisses': True}},
            {**records[2], 'detail': {**records[2]['detail'], 'field': 'private-param-name'}},
            {**records[3], 'detail': {**records[3]['detail'], 'reason': 'intl-limit-exceeded'}},
            {**records[4], 'detail': {**records[4]['detail'], 'locale': 'private-locale'}},
        ])
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(input.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(input.records.map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps({'catalog': str(reader.CORE_CATALOG.relative_to(ROOT)), 'records': records + malformed}), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_audit_event_and_file_boundaries_have_closed_parity(self):
        cases = [
            ('core.audit.validation-rejected', {'operation': 'target', 'field': 'target-id', 'reason': 'empty', 'effect': 'rejected'}),
            ('core.audit.boundary-failed', {'operation': 'record', 'phase': 'record-copy', 'field': 'metadata', 'reason': 'threw', 'effect': 'append-not-reached'}),
            ('core.events.validation-rejected', {'operation': 'event-version', 'field': 'version', 'reason': 'not-positive', 'effect': 'rejected'}),
            ('core.events.boundary-failed', {'operation': 'publish', 'phase': 'handler-completion', 'reason': 'rejected', 'effect': 'publish-not-appended', 'handlerEffect': 'unknown', 'eventOrdinal': 1, 'handlerOrdinal': 0}),
            ('core.files.validation-rejected', {'operation': 'storage-key', 'field': 'storage-key', 'reason': 'parent-segment', 'ordinal': 1, 'effect': 'rejected'}),
            ('core.files.operation-rejected', {'operation': 'get', 'field': 'tenant-id', 'reason': 'tenant-mismatch', 'effect': 'rejected-before-write'}),
            ('core.files.boundary-failed', {'operation': 'put', 'phase': 'history-copy', 'field': 'body', 'reason': 'threw', 'effect': 'map-written-history-not-appended'}),
            ('core.files.validation-rejected', {'operation': 'storage-key', 'field': 'storage-key', 'reason': 'predicate-rejected', 'effect': 'rejected'}),
        ]
        records = [{'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail} for code, detail in cases]
        malformed = []
        for record in records:
            self.assertEqual(reader.validate_record(record, reader.CORE_CATALOG), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'readiness')
            malformed.extend([
                {**record, 'detail': {**record['detail'], 'payload': 'private-audit-event-file-canary'}},
                {**record, 'detail': {**record['detail'], 'effect': 'durably-committed'}},
                {**record, 'definitionVersion': 999},
                {**record, 'detail': {}},
            ])
        malformed.extend([
            {**records[3], 'detail': {**records[3]['detail'], 'eventOrdinal': -1}},
            {**records[3], 'detail': {**records[3]['detail'], 'handlerOrdinal': 9007199254740992}},
            {**records[3], 'detail': {**records[3]['detail'], 'handlerEffect': 'rolled-back'}},
            {**records[4], 'detail': {**records[4]['detail'], 'field': 'private-filename-canary'}},
            {**records[4], 'detail': {**records[4]['detail'], 'ordinal': -1}},
            {**records[5], 'detail': {**records[5]['detail'], 'reason': 'scan-policy-enforced'}},
        ])
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const defs=JSON.parse(fs.readFileSync(input.catalog,'utf8')).catalog.definitions;process.stdout.write(JSON.stringify(input.records.map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps({'catalog': str(reader.CORE_CATALOG.relative_to(ROOT)), 'records': records + malformed}), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_monitoring_logging_and_observation_boundaries_have_closed_parity(self):
        cases = [
            (reader.CORE_CATALOG, 'core.monitoring.validation-rejected', 1,
             {'operation': 'signal-definition', 'field': 'signal-intent', 'reason': 'closed-value-rejected', 'ordinal': 1, 'effect': 'rejected'}),
            (reader.CORE_CATALOG, 'core.monitoring.boundary-failed', 1,
             {'operation': 'trace-start', 'phase': 'append', 'reason': 'threw', 'effect': 'sequence-advanced-append-unknown'}),
            (reader.CORE_CATALOG, 'core.monitoring.boundary-failed', 1,
             {'operation': 'trace-end', 'phase': 'attribute-copy', 'field': 'attributes', 'reason': 'threw', 'effect': 'end-marked-record-not-replaced'}),
            (reader.CORE_CATALOG, 'core.logging.boundary-failed', 1,
             {'operation': 'write', 'phase': 'inner-invocation', 'field': 'logger', 'reason': 'rejected', 'effect': 'inner-outcome-unknown'}),
            (reader.CONTRACT_CATALOG, 'platform-contracts.registration-rejected', 1,
             {'registration': 'route', 'field': 'name', 'condition': 'invalid-format', 'phase': 'validation', 'effect': 'rejected'}),
            (reader.CONTRACT_CATALOG, 'platform-contracts.registration-rejected', 2,
             {'registration': 'observability-profile', 'field': 'errorClasses', 'condition': 'member-invalid', 'index': 63, 'phase': 'validation', 'effect': 'rejected'}),
            (reader.OBSERVABILITY_CATALOG, 'observability.boundary-failed', 1,
             {'operation': 'request-observation', 'phase': 'elapsed-computation', 'field': 'timestamp', 'reason': 'threw', 'effect': 'observation-incomplete'}),
            (reader.OBSERVABILITY_CATALOG, 'observability.diagnostic-reporting-suppressed', 1,
             {'reason': 'attempt-limit', 'limit': 128, 'attempted': 127, 'effect': 'further-observations-not-attempted'}),
        ]
        records = [{'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': version, 'detail': detail}
                   for _, code, version, detail in cases]
        malformed = []
        for (catalog, _, _, _), record in zip(cases, records):
            self.assertEqual(reader.validate_record(record, catalog), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'readiness')
            for mutation in ({**record, 'detail': {**record['detail'], 'raw': 'private-observation-canary'}},
                             {**record, 'definitionVersion': 999}, {**record, 'detail': {}}):
                malformed.append(mutation)
        declaration = records[5]
        malformed.extend([
            {**declaration, 'definitionVersion': 1},
            {**declaration, 'detail': {**declaration['detail'], 'index': 64}},
            {**declaration, 'detail': {**declaration['detail'], 'field': 'name'}},
            {**declaration, 'detail': {**declaration['detail'], 'registration': 'route'}},
            {**records[-1], 'detail': {**records[-1]['detail'], 'limit': 129}},
            {**records[-1], 'detail': {**records[-1]['detail'], 'attempted': 128}},
            {**records[2], 'detail': {**records[2]['detail'], 'effect': 'committed'}},
            {**records[6], 'detail': {**records[6]['detail'], 'phase': 'private-observation-canary'}},
        ])
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        catalogs = [str(path.relative_to(ROOT)) for path in dict.fromkeys(case[0] for case in cases)]
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const defs=input.catalogs.flatMap(file=>JSON.parse(fs.readFileSync(file,'utf8')).catalog.definitions);process.stdout.write(JSON.stringify(input.records.map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps({'catalogs': catalogs, 'records': records + malformed}), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_queue_relay_worker_and_target_delivery_have_closed_selected_parity(self):
        records = [
            {'schema': 'core/diagnostic-record/v1', 'code': 'core.queue.validation-rejected', 'definitionVersion': 1,
             'detail': {'operation': 'send', 'field': 'delay', 'reason': 'above-maximum', 'effect': 'rejected'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'core.queue.boundary-failed', 'definitionVersion': 1,
             'detail': {'operation': 'acknowledge', 'boundary': 'invocation', 'reason': 'rejected', 'effect': 'unknown'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'core.queue.boundary-failed', 'definitionVersion': 1,
             'detail': {'operation': 'receive', 'boundary': 'invocation', 'reason': 'rejected', 'effect': 'unknown',
                        'native': {'codeAvailability': 'recognized', 'condition': 'request-throttled'}}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'core.queue.receive-reduced', 'definitionVersion': 1,
             'detail': {'operation': 'receive', 'issues': [{'field': 'receive-count', 'reason': 'not-positive', 'reduction': 'count-one'}], 'truncated': False, 'effect': 'reduction-observed'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'persistence.relay-boundary-observed', 'definitionVersion': 1,
             'detail': {'operation': 'run-once', 'boundary': 'publish-marker', 'reason': 'returned-failure', 'effect': 'send-success-marker-outcome-unknown'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'platform-worker.delivery-rejected', 'definitionVersion': 1,
             'detail': {'operation': 'job-delivery', 'field': 'claimed-lease', 'condition': 'absent', 'effect': 'handler-not-invoked'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'platform-worker.coordination-observed', 'definitionVersion': 1,
             'detail': {'condition': 'already-terminal', 'effect': 'handler-not-invoked'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'platform-worker.boundary-failed', 'definitionVersion': 2,
             'detail': {'operation': 'job-delivery', 'phase': 'complete', 'reason': 'thrown', 'effect': 'handler-succeeded'}},
            {'schema': 'core/diagnostic-record/v1', 'code': 'kanbien-platform.delivery.boundary-observed', 'definitionVersion': 1,
             'detail': {'workload': 'relational-worker', 'boundary': 'claim-result', 'condition': 'unexpected-disposition', 'disposition': 'lease-active', 'effect': 'work-outcome-unknown'}},
        ]
        for record in records:
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, 'read_processing')
        malformed = []
        for record in records:
            private = copy.deepcopy(record); private['detail']['body'] = 'private-payload-receipt-canary'; malformed.append(private)
            guessed = copy.deepcopy(record); guessed['detail']['effect'] = 'committed'; malformed.append(guessed)
            version = copy.deepcopy(record); version['definitionVersion'] += 10; malformed.append(version)
        oversized = copy.deepcopy(records[3]); oversized['detail']['issues'] *= 17; malformed.append(oversized)
        private_native = copy.deepcopy(records[2]); private_native['detail']['native']['message'] = 'private-sdk-message'; malformed.append(private_native)
        guessed_native = copy.deepcopy(records[2]); guessed_native['detail']['native']['condition'] = 'permission-denied'; malformed.append(guessed_native)
        private_disposition = copy.deepcopy(records[-1]); private_disposition['detail']['disposition'] = 'private-native-response'; malformed.append(private_disposition)
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const defs=[...require(path.join(root,'packages/core/src/diagnostic-catalog.js')).coreDiagnosticCatalog.definitions,...require(path.join(root,'platform/persistence/src/diagnostics.js')).platformPersistenceDiagnosticCatalog.definitions,...require(path.join(root,'platform/workers/src/diagnostics.js')).platformWorkerDiagnosticCatalog.definitions,...require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.js')).kanbienPlatformDeliveryDiagnosticCatalog.definitions];process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(record=>{const def=defs.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(records + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))
        self.assertEqual(len({item['code'] for item in reader.persistence_operation_definitions()}), 9)

    def test_command_attribute_and_state_observations_have_strict_cross_language_parity(self):
        records = [
            {"schema": "core/diagnostic-record/v1", "code": "persistence.command-condition-observed", "definitionVersion": 1,
             "detail": {"operation": "create_outbox", "boundary": "invocation", "role": "primary", "condition": "condition-rejected", "codeStatus": "recognized", "effect": "unknown"}},
            {"schema": "core/diagnostic-record/v1", "code": "persistence.unclassified-failure", "definitionVersion": 4,
             "detail": {"operation": "write_atomic", "boundary": "invocation", "role": "primary", "condition": "transaction-canceled",
                 "codeStatus": "recognized", "effect": "unknown", "cancellation": {"availability": "available", "truncated": False,
                     "reasons": [{"ordinal": 0, "codeStatus": "recognized", "condition": "condition-rejected"}]}}},
            {"schema": "core/diagnostic-record/v1", "code": "persistence.stored-attribute-observed", "definitionVersion": 1,
             "detail": {"operation": "read_processing", "reduction": "thrown", "effect": "not-assessed", "truncated": False,
                 "issues": [{"field": "leaseOwner", "condition": "string-component-absent", "rowOrdinal": 0, "count": 2}]}},
            {"schema": "core/diagnostic-record/v1", "code": "persistence.reconciliation-observed", "definitionVersion": 2,
             "detail": {"operation": "complete_processing", "primaryOutcome": "condition-rejected", "observed": "valid-current-state", "effect": "read-result-observed"}},
        ]
        for record in records:
            self.assertEqual(reader.validate_selected_record(record), record)
            self.assertEqual(reader.validate_operation_record(record, record['detail']['operation']), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
        malformed = []
        for record in records:
            extra = copy.deepcopy(record); extra['detail']['nativeMessage'] = 'sensitive-canary'; malformed.append(extra)
            guessed = copy.deepcopy(record); guessed['detail']['effect'] = 'committed'; malformed.append(guessed)
        oversized = copy.deepcopy(records[1]); oversized['detail']['cancellation']['reasons'] *= 65; malformed.append(oversized)
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformPersistenceDiagnosticCatalog:catalog}=require(path.join(root,'platform/persistence/src/diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(record=>{const definition=catalog.definitions.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!definition&&parseDiagnosticRecord(definition,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(records + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))
        self.assertEqual(len({item['code'] for item in reader.persistence_operation_definitions()}), 9,
            'New command/attribute records do not silently join the native recovery-mapping family')

    def test_acceptance_request_catalog_parity_does_not_widen_configuration_or_operation_readers(self):
        records = [{"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.acceptance.request-invalid", "definitionVersion": 1,
            "detail": {"operation": operation, "source": source, "field": field, "reason": reason, "effect": "persistence-not-invoked"}}
            for operation, source, field, reason in [("create", "body", "record_id", "missing"),
                ("read", "query", "record_id", "array"), ("delete", "query", "record_id", "invalid-format")]]
        for record in records:
            self.assertEqual(reader.validate_selected_record(record), record)
            self.assertEqual(reader.validate_record(record, reader.ACCEPTANCE_CATALOG), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, record['detail']['operation'])
        malformed = []
        for field, value in [('reason', 'native-private-message'), ('field', 'submitted-private-field'),
                             ('effect', 'committed'), ('operation', 'connect')]:
            changed = copy.deepcopy(records[0]); changed['detail'][field] = value; malformed.append(changed)
        extra = copy.deepcopy(records[0]); extra['detail']['value'] = 'sensitive-canary'; malformed.append(extra)
        wrong_version = copy.deepcopy(records[0]); wrong_version['definitionVersion'] = 2; malformed.append(wrong_version)
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {kanbienCoreAcceptanceDiagnosticCatalog:catalog}=require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(record=>{const definition=catalog.definitions.find(item=>item.code===record.code&&item.version===record.definitionVersion);return !!definition&&parseDiagnosticRecord(definition,record).ok})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(records + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_runtime_transport_process_catalogs_have_literal_cross_language_parity(self):
        samples = [
            ('runtime', 'platform-runtime.state-rejected', {'operation': 'start', 'state': 'ready', 'effect': 'state-unchanged'}),
            ('runtime', 'platform-runtime.boundary-failed', {'operation': 'request-context', 'phase': 'clock-read', 'subject': 'context', 'boundary': 'invocation', 'effect': 'context-not-returned'}),
            ('runtime', 'platform-runtime.boundary-failed', {'operation': 'shutdown', 'phase': 'resource.close', 'subject': 'resource', 'boundary': 'event-clock', 'effect': 'step-completed-event-unrecorded', 'ordinal': 2}),
            ('server', 'platform-server.transport-request-rejected', {'reason': 'handler-deadline-observed', 'phase': 'handler', 'effect': 'handler-still-pending'}),
            ('server', 'platform-server.transport-boundary-failed', {'phase': 'response-serialization', 'reason': 'threw', 'effect': 'request-not-returned'}),
            ('server', 'platform-server.transport-state-observed', {'phase': 'shutdown', 'reason': 'drain-deadline-observed', 'effect': 'shutdown-still-pending'}),
            ('server', 'platform-server.client-address-trust-invalid', {'phase': 'configuration', 'setting': 'http.client-address-trust', 'reason': 'unsupported', 'effect': 'rejected'}),
            ('server', 'platform-server.client-address-fallback-selected', {'phase': 'client-address-selection', 'reason': 'forwarded-header-missing', 'source': 'socket-peer', 'effect': 'fallback-selected'}),
            ('server', 'platform-server.configuration-omitted', {'phase': 'configuration', 'setting': 'release.source-commit', 'reason': 'format-rejected', 'effect': 'omitted'}),
            ('server', 'platform-server.process-boundary-failed', {'phase': 'startup-log', 'reason': 'boundary-threw', 'effect': 'process-not-returned'}),
            ('server', 'platform-server.request-predicate-rejected', {'phase': 'tenant-resolution', 'field': 'isolationKey', 'condition': 'string-required', 'effect': 'handler-not-invoked'}),
            ('server', 'platform-server.request-boundary-failed', {'phase': 'route-parameter-decoding', 'reason': 'boundary-threw', 'effect': 'handler-not-invoked', 'index': 1}),
            ('workers', 'platform-worker.boundary-failed', {'operation': 'shutdown', 'phase': 'queue-close', 'boundary': 'selection-or-invocation', 'effect': 'lifecycle-shutdown-not-invoked'}),
        ]
        javascript = """const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');
const {createDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));
const catalogs={runtime:'platformRuntimeDiagnosticCatalog',server:'platformServerDiagnosticCatalog',workers:'platformWorkerDiagnosticCatalog'};
process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([owner,code,detail])=>{
 const catalog=require(path.join(root,'platform',owner,'src/diagnostics.js'))[catalogs[owner]];
 const record=createDiagnosticRecord(catalog.definitions.find(d=>d.code===code&&d.version===1),detail);
 if(!record.ok)throw Error('literal-fixture-invalid');return record.value;
})));"""
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(samples), cwd=ROOT, capture_output=True, text=True, check=True)
        records = json.loads(result.stdout)
        self.assertEqual(records, [{'schema': 'core/diagnostic-record/v1', 'code': code, 'definitionVersion': 1, 'detail': detail}
                                   for _, code, detail in samples])
        cases = []
        expected = []
        for (owner, _, _), record in zip(samples, records):
            catalog = ROOT / 'platform' / owner / 'contracts/diagnostics.v1.json'
            self.assertEqual(reader.validate_record(record, catalog), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            cases.append([owner, record]); expected.append(True)
            for changed in [dict(record, definitionVersion=999), dict(record, detail={**record['detail'], 'raw': 'synthetic-private-canary'}),
                            dict(record, detail={**record['detail'], 'effect': 'guessed-effect'}),
                            dict(record, detail={key: value for key, value in record['detail'].items() if key != 'effect'})]:
                with self.assertRaises(reader.DiagnosticContractError):
                    reader.validate_record(changed, catalog)
                cases.append([owner, changed]); expected.append(False)
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_operation_record(record, 'readiness')
        javascript = """const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');
const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));
const names={runtime:'platformRuntimeDiagnosticCatalog',server:'platformServerDiagnosticCatalog',workers:'platformWorkerDiagnosticCatalog'};
process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([owner,record])=>{
 const defs=require(path.join(root,'platform',owner,'src/diagnostics.js'))[names[owner]].definitions;
 const def=defs.find(d=>d.code===record.code&&d.version===record.definitionVersion);return !!def&&parseDiagnosticRecord(def,record).ok;
})));"""
        parsed = subprocess.run(['node', '-e', javascript], input=json.dumps(cases), cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(parsed.stdout), expected)

    def test_persistence_operation_family_excludes_configuration_without_widening_mapping(self):
        expected = {
            "persistence.transport-unavailable", "persistence.trust-validation-failed",
            "persistence.credential-rejected", "persistence.runtime-permission-denied",
            "persistence.capacity-exhausted", "persistence.schema-incompatible",
            "persistence.operation-timed-out", "persistence.outcome-uncertain",
            "persistence.unclassified-failure",
        }
        selected = reader.persistence_operation_definitions()
        self.assertEqual({definition["code"] for definition in selected}, expected)
        self.assertIn("persistence.configuration-invalid", {definition["code"] for definition in reader.persistence_definitions()})
        self.assertTrue(any(definition["code"] == "persistence.trust-validation-failed" and definition["classification"]["failureKind"] == "configuration" for definition in selected))
        record = {"schema": "core/diagnostic-record/v1", "code": "persistence.configuration-invalid", "definitionVersion": 1,
                  "detail": {"field": "outbox-index", "reason": "too-long"}}
        self.assertEqual(reader.validate_selected_record(record), record)
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_operation_record(record, "readiness")
        for field in ("phase", "classification", "codeStatus"):
            self.assertEqual(reader.persistence_vocabulary(field), set(selected[0]["detail"]["properties"][field]["values"]))

    def test_committed_versions_cannot_be_changed_or_removed(self):
        javascript = "import {catalogCompatible} from './scripts/repo/diagnostic-coverage/compatibility.mjs'; const definition={code:'fixture.invalid',version:1,classification:{severity:'warning'},detail:{type:'boolean'}};const old={schema:'core/diagnostic-catalog-export/v1',catalog:{owner:'fixture',definitions:[definition]}};const make=definitions=>({...old,catalog:{owner:'fixture',definitions}});process.stdout.write(JSON.stringify([catalogCompatible(old,old),catalogCompatible(old,make([{...definition,detail:{type:'number'}}])),catalogCompatible(old,make([])),catalogCompatible(old,make([{...definition,version:2}])),catalogCompatible(old,make([definition,{...definition,version:2}]))]));"
        result = subprocess.run(["node", "--input-type=module", "-e", javascript], capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True, False, False, False, True])
    def test_reason_growth_requires_explicit_selection_and_a_new_version(self):
        javascript = """
import {catalogCompatible} from './scripts/repo/diagnostic-coverage/compatibility.mjs';
const names = {missing: 'missing', future: 'fixture-future-reason'};
const definition = {code: 'fixture.reasons', version: 1, classification: {severity: 'warning'},
  detail: {type: 'enum', values: [names.missing]}};
const previous = {schema: 'core/diagnostic-catalog-export/v1', catalog: {owner: 'fixture', definitions: [definition]}};
const make = definitions => ({...previous, catalog: {...previous.catalog, definitions}});
const widened = {...definition, detail: {type: 'enum', values: Object.values(names)}};
const next = {...widened, version: 2};
process.stdout.write(JSON.stringify([
  catalogCompatible(previous, make([definition])),
  catalogCompatible(previous, make([widened])),
  catalogCompatible(previous, make([definition, next])),
  catalogCompatible(previous, make([next])),
]));
"""
        result = subprocess.run(['node', '--input-type=module', '-e', javascript],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), [True, False, True, False])

    def test_migration_and_administration_collect_only_validated_detail(self):
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        migration = load("diagnostic_migration", folder / "run-migration/script.py")
        administration = load("diagnostic_administration", folder / "run-administration/script.py")
        diagnostic = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.configuration-invalid", "definitionVersion": 1,
                      "detail": {"issues": [{"setting": "database.port", "reason": "out-of-range"}]}}
        task = {"taskArn": "fixture/task-1"}
        value = {"verdict": "rejected", "code": "PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", "diagnostic": diagnostic}
        with patch.object(migration, "aws", return_value=(True, {"events": [{"message": json.dumps(value)}]}, "ok")):
            retained, state = migration.migration_log_rejection(task)
        self.assertEqual(state, "ok")
        self.assertEqual(retained["diagnostic"], diagnostic)
        bad = copy.deepcopy(value)
        bad["diagnostic"]["detail"]["issues"][0]["value"] = "synthetic-sensitive-canary"
        with patch.object(migration, "aws", return_value=(True, {"events": [{"message": json.dumps(bad)}]}, "ok")):
            self.assertIsNone(migration.migration_log_rejection(task)[0])
        value["code"] = "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID"
        output = io.StringIO()
        with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [{"message": json.dumps(value)}]}, "ok")), contextlib.redirect_stdout(output):
            self.assertEqual(administration.accept(task, 10, "bootstrap-identities"), 1)
        self.assertEqual(json.loads(output.getvalue())["facts"]["diagnostic"], diagnostic)

    def test_http_configuration_observations_match_closed_server_catalog(self):
        catalog = ROOT / 'platform/server/contracts/diagnostics.v1.json'
        samples = [
            ('platform-server.listener-configuration-selected', {'phase': 'configuration', 'setting': 'http.host', 'source': 'default', 'reason': 'missing', 'effect': 'default-selected'}),
            ('platform-server.port-configuration-fallback', {'phase': 'configuration', 'setting': 'http.port', 'source': 'default', 'reason': 'not-numeric', 'effect': 'default-selected'}),
            ('platform-server.health-exposure-selected', {'phase': 'configuration', 'setting': 'http.health.readiness-exposure', 'source': 'authentication-default', 'exposure': 'authenticated', 'reason': 'missing', 'effect': 'default-selected'}),
            ('platform-server.health-exposure-fallback', {'phase': 'configuration', 'setting': 'http.health.liveness-exposure', 'source': 'default', 'exposure': 'public', 'reason': 'unsupported', 'effect': 'default-selected'}),
        ]
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {createDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformServerDiagnosticCatalog:catalog}=require(path.join(root,'platform/server/src/diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([code,detail])=>{const result=createDiagnosticRecord(catalog.definitions.find(def=>def.code===code),detail);if(!result.ok)throw Error('fixture-invalid');return result.value;})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(samples), cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertNotIn('synthetic-private-canary', result.stdout)
        records = json.loads(result.stdout)
        self.assertEqual(len(records), 4)
        cases, expected = [], []
        for record in records:
            self.assertEqual(reader.validate_record(record, catalog), record)
            cases.append(record)
            expected.append(True)
            for mutation in [dict(record, definitionVersion=999), dict(record, detail={**record['detail'], 'value': 'synthetic-private-canary'}), dict(record, detail={**record['detail'], 'reason': 'synthetic-private-canary'})]:
                with self.assertRaises(reader.DiagnosticContractError):
                    reader.validate_record(mutation, catalog)
                cases.append(mutation)
                expected.append(False)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformServerDiagnosticCatalog:catalog}=require(path.join(root,'platform/server/src/diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(record=>{const definition=catalog.definitions.find(def=>def.code===record.code&&def.version===record.definitionVersion);return definition?parseDiagnosticRecord(definition,record).ok:false;})));"
        result = subprocess.run(['node', '-e', javascript], input=json.dumps(cases), cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), expected)
        # Existing operation-specific readers must not accept startup selection as a failed task.
        with self.assertRaises(reader.DiagnosticContractError):
            reader.validate_configuration_record(records[0])

    def test_iam_diagnostics_survive_existing_task_readers(self):
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        migration = load("iam_diagnostic_migration", folder / "run-migration/script.py")
        administration = load("iam_diagnostic_administration", folder / "run-administration/script.py")
        diagnostic = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.iam-configuration-invalid", "definitionVersion": 1,
                      "detail": {"issues": [{"setting": "authentication.username", "reason": "missing"}, {"setting": "authentication.region", "reason": "invalid-format"}]}}
        task = {"taskArn": "fixture/task-1"}
        value = {"verdict": "rejected", "code": "PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", "diagnostic": diagnostic}
        with patch.object(migration, "aws", return_value=(True, {"events": [{"message": json.dumps(value)}]}, "ok")):
            retained, state = migration.migration_log_rejection(task)
        self.assertEqual(state, "ok")
        self.assertEqual(retained["diagnostic"], diagnostic)
        restored = {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "rejected", "code": "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID", "diagnostic": diagnostic}
        self.assertEqual(deployment.validate_verifier_result(restored)["diagnostic"], diagnostic)
        for operation, code, detail, expected in [
            ("prove-effective-privilege", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", diagnostic, True),
            ("prove-effective-privilege", "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", diagnostic, True),
            ("bootstrap-identities", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", diagnostic, False),
            ("prove-effective-privilege", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", {**diagnostic, "code": "kanbien-core-server.configuration-invalid", "detail": {"issues": [{"setting": "database.port", "reason": "missing"}]}}, False),
            ("prove-effective-privilege", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", {**diagnostic, "detail": {"issues": [{"setting": "authentication.region", "reason": "missing", "value": "synthetic-sensitive-canary"}]}}, False),
        ]:
            with self.subTest(operation=operation, code=code, expected=expected):
                output = io.StringIO()
                envelope = {"verdict": "rejected", "code": code, "diagnostic": detail}
                with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [{"message": json.dumps(envelope)}]}, "ok")), contextlib.redirect_stdout(output):
                    self.assertEqual(administration.accept(task, 10, operation), 1)
                report = json.loads(output.getvalue())
                if expected:
                    self.assertEqual(report["facts"]["diagnostic"], diagnostic)
                    self.assertEqual(report["facts"]["safe_result_code"], code)
                else:
                    self.assertNotIn("diagnostic", report.get("facts", {}))
                self.assertNotIn("synthetic-sensitive-canary", output.getvalue())

    def test_administrator_credentials_survive_reader_without_disclosure(self):
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        administration = load("credential_diagnostic_administration", folder / "run-administration/script.py")
        task = {"taskArn": "fixture/task-1"}
        diagnostic = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.administrator-credentials-invalid", "definitionVersion": 1,
                      "detail": {"issues": [{"setting": "administrator.username", "reason": "missing"}, {"setting": "administrator.password", "reason": "forbidden-character"}]}}
        self.assertEqual(reader.validate_record(diagnostic), diagnostic)
        for operation in ["bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"]:
            with self.subTest(operation=operation):
                output = io.StringIO()
                envelope = {"verdict": "rejected", "code": "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "diagnostic": diagnostic}
                with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [{"message": json.dumps(envelope)}]}, "ok")), contextlib.redirect_stdout(output):
                    self.assertEqual(administration.accept(task, 10, operation), 1)
                self.assertEqual(json.loads(output.getvalue())["facts"]["diagnostic"], diagnostic)
        cases = [diagnostic, {**diagnostic, "detail": {"issues": [{"setting": "administrator.credentials", "reason": "invalid-json"}]}}]
        for extra in ["value", "password", "rawJson", "length", "parserMessage"]:
            bad = copy.deepcopy(diagnostic)
            bad["detail"]["issues"][1][extra] = "synthetic-sensitive-canary"
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_record(bad)
            cases.append(bad)
        javascript = "const fs=require('node:fs'),path=require('node:path'); const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {persistenceAdministratorCredentialDiagnostic}=require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>parseDiagnosticRecord(persistenceAdministratorCredentialDiagnostic,value).ok)));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(cases), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True, True] + [False] * 5)

    def test_administration_relationship_records_survive_strict_readers(self):
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        administration = load("relationship_diagnostic_administration", folder / "run-administration/script.py")
        prefix = "kanbien-core-server.administration-configuration-invalid."
        field = {"setting": "migration.username", "reason": "missing"}
        relationship = {"relationship": "administrator-runtime-separation", "rule": "must-differ"}
        records = [{"schema": "core/diagnostic-record/v1", "code": prefix + suffix, "definitionVersion": 1, "detail": detail}
                   for suffix, detail in [("fields", {"issues": [field]}),
                                          ("relationships", {"relationshipIssues": [relationship]}),
                                          ("fields-and-relationships", {"issues": [field], "relationshipIssues": [relationship]})]]
        task = {"taskArn": "fixture/task-1"}
        operations = ["bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"]
        for record in records:
            self.assertEqual(reader.validate_record(record), record)
            for operation in operations:
                output = io.StringIO()
                envelope = {"verdict": "rejected", "code": "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "diagnostic": record}
                with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [{"message": json.dumps(envelope)}]}, "ok")), contextlib.redirect_stdout(output):
                    self.assertEqual(administration.accept(task, 10, operation), 1)
                self.assertEqual(json.loads(output.getvalue())["facts"]["diagnostic"], record)
        malformed = []
        for record in records:
            malformed.extend([{**record, "detail": {}},
                              {**record, "detail": {key: [] for key in record["detail"]}},
                              {**record, "detail": {**record["detail"], "value": "synthetic-sensitive-canary"}},
                              {**record, "definitionVersion": 2}])
        for suffix, detail in [("fields", {"relationshipIssues": [relationship]}),
                              ("relationships", {"issues": [field]}),
                              ("fields-and-relationships", {"issues": [field]}),
                              ("fields-and-relationships", {"relationshipIssues": [relationship]}),
                              ("relationships", {"relationshipIssues": [{**relationship, "relationship": "synthetic-sensitive-canary"}]}),
                              ("relationships", {"relationshipIssues": [{**relationship, "rule": "must-match"}]}),
                              ("relationships", {"relationshipIssues": [{**relationship, "left": "synthetic-sensitive-canary"}]}),
                              ("fields", {"issues": [{**field, "value": "synthetic-sensitive-canary"}]}),
                              ("relationships", {"relationshipIssues": [relationship] * 33})]:
            malformed.append({**records[0], "code": prefix + suffix, "detail": detail})
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_record(record)
            output = io.StringIO()
            envelope = {"verdict": "rejected", "code": "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "diagnostic": record}
            with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [{"message": json.dumps(envelope)}]}, "ok")), contextlib.redirect_stdout(output):
                self.assertEqual(administration.accept(task, 10, "bootstrap-identities"), 1)
            self.assertNotIn("diagnostic", json.loads(output.getvalue()).get("facts", {}))
            self.assertNotIn("synthetic-sensitive-canary", output.getvalue())
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {persistenceConfigurationDiagnosticCatalog:catalog}=require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>{const definition=catalog.definitions.find(item=>item.code===value.code);return !!definition&&parseDiagnosticRecord(definition,value).ok})));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(records + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_observability_catalog_parity_and_strict_selection(self):
        failure = {"schema": "core/diagnostic-record/v1", "code": "observability.configuration-invalid", "definitionVersion": 1,
                   "detail": {"phase": "configuration-validation", "effect": "not-started", "issues": [
                       {"setting": "series.allowed-labels", "reason": "duplicate", "index": 1, "attributeIndex": 2, "relatedIndex": 0}], "truncated": False}}
        construction = {**failure, "code": "observability.runtime-construction-failed", "detail": {
            "phase": "runtime-construction", "reason": "unclassified-construction-failure", "effect": "not-assessed"}}
        bounded = copy.deepcopy(failure)
        bounded["detail"]["issues"] *= 32
        bounded["detail"]["truncated"] = True
        valid = [failure, construction, bounded]
        malformed = []
        for key, value in [("phase", "runtime-construction"), ("effect", "unknown"), ("issues", []),
                           ("issues", failure["detail"]["issues"] * 33), ("truncated", "false")]:
            malformed.append({**failure, "detail": {**failure["detail"], key: value}})
        for key, value in [("setting", "synthetic-sensitive-canary"), ("reason", "guessed"), ("index", -1),
                           ("attributeIndex", 1.5), ("relatedIndex", 9007199254740992), ("value", "synthetic-sensitive-canary")]:
            malformed.append({**failure, "detail": {**failure["detail"], "issues": [{**failure["detail"]["issues"][0], key: value}]}})
        malformed += [{**failure, "definitionVersion": 2}, {**failure, "definitionVersion": True},
                      {**failure, "detail": {key: value for key, value in failure["detail"].items() if key != "truncated"}},
                      {**construction, "detail": {**construction["detail"], "effect": "not-started"}}]
        for record in valid:
            self.assertEqual(reader.validate_record(record, reader.OBSERVABILITY_CATALOG), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(record, reader.OBSERVABILITY_CATALOG)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformObservabilityDiagnosticCatalog:catalog}=require(path.join(root,'platform/observability/src/configuration.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>{const definition=catalog.definitions.find(item=>item.code===value.code);return !!definition&&parseDiagnosticRecord(definition,value).ok})));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(valid + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(valid) + [False] * len(malformed))

    def test_health_readiness_catalog_parity_and_strict_meanings(self):
        records = []
        for code, detail in [
            ("observability.readiness-configuration-invalid", {"field": "timeout", "reason": "not-integer", "phase": "configuration", "effect": "probe-not-invoked"}),
            ("observability.readiness-probe-not-ready", {"phase": "result", "effect": "returned-not-ready"}),
            ("observability.readiness-probe-threw", {"phase": "invocation", "effect": "unknown"}),
            ("observability.readiness-probe-rejected", {"phase": "completion", "effect": "unknown"}),
            ("observability.readiness-probe-deadline-observed", {"phase": "deadline", "effect": "unknown"}),
            ("health.check-not-ready", {"index": 0, "status": "degraded", "phase": "result", "effect": "returned-not-ready"}),
            ("health.check-not-ready", {"index": 1, "status": "unhealthy", "phase": "result", "effect": "returned-not-ready"}),
            ("health.check-threw", {"index": 0, "phase": "invocation", "effect": "unknown"}),
            ("health.check-rejected", {"index": 0, "phase": "completion", "effect": "unknown"}),
            ("health.check-projection-failed", {"index": 0, "phase": "projection", "effect": "output-unhealthy"}),
            ("health.lifecycle-not-ready", {"phase": "aggregation", "effect": "output-not-ready"}),
        ]:
            records.append({"schema": "core/diagnostic-record/v1", "code": code, "definitionVersion": 1, "detail": detail})
        malformed = []
        for record in records:
            catalog = reader.HEALTH_CATALOG if record["code"].startswith("health.") else reader.OBSERVABILITY_CATALOG
            self.assertEqual(reader.validate_record(record, catalog), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_record(record)
            for field, value in [("phase", "guessed"), ("effect", "cancelled"), ("raw", "synthetic-sensitive-canary")]:
                malformed.append({**record, "detail": {**record["detail"], field: value}})
            malformed += [{**record, "schema": "unknown"}, {**record, "definitionVersion": 2}]
        malformed += [{**records[0], "detail": {**records[0]["detail"], "reason": "guessed"}},
                      {**records[5], "detail": {**records[5]["detail"], "status": "healthy"}},
                      {**records[7], "detail": {**records[7]["detail"], "index": -1}},
                      {**records[8], "detail": {**records[8]["detail"], "phase": "invocation"}},
                      {**records[4], "detail": {**records[4]["detail"], "effect": "transport-unavailable"}}]
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformObservabilityDiagnosticCatalog:observability}=require(path.join(root,'platform/observability/src/configuration.js'));const {platformHealthDiagnosticCatalog:health}=require(path.join(root,'platform/health/src/diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>{const catalog=value.code.startsWith('health.')?health:observability;const definition=catalog.definitions.find(item=>item.code===value.code&&item.version===value.definitionVersion);return !!definition&&parseDiagnosticRecord(definition,value).ok})));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(records + malformed), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_configuration_registration_vertical_catalog_parity(self):
        cases = [
            (reader.CORE_CATALOG, "core.config.primitive-invalid", 1, {"field": "value", "reader": "string", "reason": "missing"}),
            (reader.CORE_CATALOG, "core.config.source-threw", 1, {"reader": "string", "phase": "source-read", "reason": "invocation-threw"}),
            (reader.CORE_CATALOG, "core.shared.json-invalid", 1, {"reason": "non-finite-number", "depth": 1, "path": [], "pathTruncated": True, "locationUnavailable": True}),
            (reader.CONFIG_CATALOG, "platform-config.schema-rejected", 1, {"schemaIndex": 0, "reason": "missing"}),
            (reader.CONFIG_CATALOG, "platform-config.schema-rejected", 2, {"schemaIndex": 65536, "reason": "missing"}),
            (reader.CONFIG_CATALOG, "platform-config.schema-boundary-threw", 1, {"schemaIndex": 0, "phase": "parse", "reason": "boundary-threw", "effect": "result-not-returned"}),
            (reader.CONTRACT_CATALOG, "platform-contracts.registration-rejected", 1, {"registration": "route", "field": "name", "condition": "duplicate-name", "phase": "registration", "effect": "rejected"}),
            (reader.CONTRACT_CATALOG, "platform-contracts.operational-event-rejected", 1, {"operation": "readiness-event", "field": "target", "condition": "invalid-format", "phase": "validation", "effect": "predicate-rejected"}),
            (reader.CONTRACT_CATALOG, "platform-contracts.operational-boundary-failed", 1, {"operation": "fixed-feature-flags", "phase": "snapshot", "field": "flags", "reason": "threw", "effect": "reader-not-produced"}),
            (reader.PLATFORM_TARGET_CATALOG, "kanbien-platform.configuration-invalid", 1, {"issues": [{"setting": "worker.queue-provider", "reason": "unsupported"}]}),
            (reader.PLATFORM_TARGET_CATALOG, "kanbien-platform.lease-owner-source-failed", 1, {"phase": "response-status", "reason": "invocation-failed", "effect": "not-assessed"}),
            (reader.SECURITY_CATALOG, "security.configuration-predicate-invalid", 1, {"field": "limit", "reason": "not-integer", "phase": "configuration", "effect": "rejected"}),
            (reader.SECURITY_CATALOG, "security.rate-limit-clock-failed", 1, {"phase": "clock-evaluation", "reason": "evaluation-threw", "effect": "decision-not-returned"}),
            (reader.SERVER_CATALOG, "platform-server.transport-configuration-invalid", 1, {"field": "requestTimeoutMs", "reason": "not-positive", "phase": "configuration", "effect": "rejected"}),
            (reader.WORKER_CATALOG, "platform-worker.configuration-invalid", 1, {"issues": [{"setting": "durable-lease-duration", "reason": "not-positive"}]}),
            (reader.PERSISTENCE_CATALOG, "persistence.configuration-invalid", 1, {"field": "outbox-index", "reason": "too-long"}),
            (reader.SMOKE_CATALOG, "platform-smoke.configuration-invalid", 1, {"field": "app-name", "reason": "missing"}),
            (reader.SMOKE_CATALOG, "platform-smoke.accepted-payload-not-observed", 1, {"field": "payload.outboxEntryId", "phase": "diagnostic-projection", "reason": "accessor-not-read", "effect": "not-assessed"}),
        ]
        records = [{"schema": "core/diagnostic-record/v1", "code": code, "definitionVersion": version, "detail": detail} for _, code, version, detail in cases]
        malformed = []
        for (catalog, _, _, _), record in zip(cases, records):
            self.assertEqual(reader.validate_record(record, catalog), record)
            self.assertEqual(reader.validate_selected_record(record), record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_configuration_record(record)
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(record, "readiness")
            malformed.extend([{**record, "detail": {**record["detail"], "raw": "synthetic-sensitive-canary"}}, {**record, "definitionVersion": 999}, {**record, "detail": {}}])
        wide = next(record for record in records if record["code"] == "platform-config.schema-rejected" and record["definitionVersion"] == 2)
        target = next(record for record in records if record["code"] == "kanbien-platform.configuration-invalid")
        malformed += [{**wide, "definitionVersion": 1}, {**target, "detail": {"issues": [{"setting": "synthetic-sensitive-canary", "reason": "missing"}]}}]
        for record in malformed:
            with self.assertRaises(reader.DiagnosticContractError): reader.validate_selected_record(record)
        catalogs = [str(path.relative_to(ROOT)) for path in dict.fromkeys(case[0] for case in cases)]
        javascript = "const fs=require('node:fs'),path=require('node:path');const {parseDiagnosticRecord}=require(path.resolve('.cache/diagnostic-catalog-export/packages/core/src/diagnostics/index.js'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const definitions=input.catalogs.flatMap(file=>JSON.parse(fs.readFileSync(file,'utf8')).catalog.definitions);process.stdout.write(JSON.stringify(input.records.map(value=>{const definition=definitions.find(item=>item.code===value.code&&item.version===value.definitionVersion);return !!definition&&parseDiagnosticRecord(definition,value).ok})));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps({"catalogs": catalogs, "records": records + malformed}), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(records) + [False] * len(malformed))

    def test_security_catalog_parity_and_rejection_boundaries(self):
        definitions = json.loads(reader.SECURITY_CATALOG.read_text())["catalog"]["definitions"]
        valid = []
        for definition in definitions:
            properties = definition["detail"]["properties"]
            if definition['code'] == 'security.jwt-configuration-invalid':
                valid.append({'schema': 'core/diagnostic-record/v1', 'code': definition['code'], 'definitionVersion': definition['version'],
                              'detail': {'phase': 'verifier-construction', 'effect': 'verifier-not-created',
                                         'issues': [{'setting': 'clock-tolerance', 'reason': 'not-finite'}], 'truncated': False}})
                continue
            for reason in properties["reason"]["values"]:
                detail = {"phase": properties["phase"]["values"][0], "reason": reason, "effect": properties["effect"]["values"][0]}
                if "blockNumber" in properties:
                    detail["blockNumber"] = 2
                optional = definition["detail"].get("optional", [])
                for name, schema in properties.items():
                    if name in detail or name in optional:
                        continue
                    detail[name] = schema["values"][0] if schema["type"] == "enum" else schema["minimum"]
                valid.append({"schema": "core/diagnostic-record/v1", "code": definition["code"], "definitionVersion": definition["version"], "detail": detail})
        for record in valid:
            self.assertEqual(reader.validate_record(record, reader.SECURITY_CATALOG), record)
        first = valid[0]
        invalid = [
            {**first, "definitionVersion": True}, {**first, "definitionVersion": 2},
            {**first, "code": "security.synthetic-sensitive-canary"},
            {**first, "detail": {**first["detail"], "reason": "expired"}},
            {**first, "detail": {**first["detail"], "phase": "peer-trust-verification"}},
            {**first, "detail": {**first["detail"], "effect": "not-started"}},
        ]
        for record in valid:
            definition = next(item for item in definitions if item["code"] == record["code"])
            for name in record["detail"]:
                if name in {"phase", "reason", "effect", "blockNumber"} or name in definition["detail"].get("optional", []):
                    continue
                incomplete = copy.deepcopy(record)
                del incomplete["detail"][name]
                invalid.append(incomplete)
            invalid.append({**record, "detail": {**record["detail"], "token": "synthetic-sensitive-canary"}})
        for extra in ["certificate", "subject", "issuer", "path", "endpoint", "nativeError"]:
            invalid.append({**first, "detail": {**first["detail"], extra: "synthetic-sensitive-canary"}})
        for record in invalid:
            with self.assertRaises(reader.DiagnosticContractError):
                reader.validate_record(record, reader.SECURITY_CATALOG)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {platformSecurityDiagnosticCatalog}=require(path.join(root,'platform/security/src/diagnostics.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>{const definition=platformSecurityDiagnosticCatalog.definitions.find(item=>item.code===value.code);return definition!==undefined&&parseDiagnosticRecord(definition,value).ok;})));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(valid + invalid), capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout), [True] * len(valid) + [False] * len(invalid))

    def test_real_typescript_parser_and_python_agree(self):
        record = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.configuration-invalid", "definitionVersion": 1,
                  "detail": {"issues": [{"setting": "database.port", "reason": "missing"}]}}
        cases = [record, {**record, "definitionVersion": 1.0}]
        for key, value in [("definitionVersion", True), ("definitionVersion", 2), ("code", "synthetic-canary"), ("extra", "synthetic-canary")]:
            cases.append({**record, key: value})
        for issue in [{"setting": "database.port", "reason": "unknown"}, {"setting": "raw-password", "reason": "missing"}, {"setting": "database.port", "reason": "missing", "value": "synthetic-canary"}]:
            cases.append({**record, "detail": {"issues": [issue]}})
        cases.extend([{**record, "detail": {"issues": []}}, {**record, "detail": {"issues": record["detail"]["issues"] * 33}}, {**record, "detail": {"__proto__": {}}}])
        expected = []
        for candidate in cases:
            try:
                reader.validate_record(candidate)
                expected.append(True)
            except reader.DiagnosticContractError:
                expected.append(False)
        javascript = "const fs=require('node:fs'),path=require('node:path'); const root=path.resolve('.cache/diagnostic-catalog-export'); const {parseDiagnosticRecord}=require(path.join(root,'packages/core/src/diagnostics/index.js')); const {persistenceConfigurationDiagnostic}=require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js')); process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(value=>parseDiagnosticRecord(persistenceConfigurationDiagnostic,value).ok)));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(cases), capture_output=True, text=True, check=True, cwd=ROOT, env={**os.environ, "NODE_PATH": str(ROOT / "node_modules")})
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(expected, [True, True] + [False] * (len(cases) - 2))

    def test_certificate_and_related_tls_readers_are_bound_and_bounded(self):
        source = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.certificate-source-invalid", "definitionVersion": 1,
                  "detail": {"source": "database.tls.authority-source", "reason": "missing", "phase": "configuration-source-validation", "effect": "not-started"}}
        content = {"schema": "core/diagnostic-record/v1", "code": "security.certificate-block-invalid", "definitionVersion": 1,
                   "detail": {"reason": "malformed-certificate-block", "blockNumber": 2, "phase": "certificate-content-parsing", "effect": "not-assessed"}}
        security = {"schema": "core/diagnostic-record/v1", "code": "security.peer-identity-verification-failed", "definitionVersion": 1,
                    "detail": {"phase": "peer-identity-verification", "reason": "hostname-mismatch", "effect": "not-assessed"}}
        primary = {"schema": "core/diagnostic-record/v1", "code": "persistence.trust-validation-failed", "definitionVersion": 2,
                   "detail": {"phase": "tls_probe", "classification": "tls_trust_invalid", "codeStatus": "recognized", "operation": "restore_verification", "effect": "not-assessed"}}
        configuration = {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "rejected", "code": "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID", "diagnostic": source}
        execution = {"classification": "tls_trust_invalid", "phase": "tls_probe", "code_status": "recognized", "elapsed_ms": 1}
        envelope = {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "diagnostic-failed", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID", "execution": execution, "diagnostic": primary, "related_diagnostics": [security]}
        deployment.validate_verifier_result(configuration)
        deployment.validate_verifier_result({**configuration, "diagnostic": content})
        self.assertEqual(deployment.validate_verifier_result(envelope), envelope)
        limit = json.loads(reader.TARGET_CATALOG.read_text())["delivery"]["maxRelatedRecords"]
        for bad in [
            {**configuration, "diagnostic": security}, {**configuration, "diagnostic": primary},
            {**envelope, "diagnostic": content}, {**envelope, "diagnostic": source},
            {**envelope, "diagnostic": {**primary, "detail": {**primary["detail"], "operation": "migration"}}},
            {**envelope, "related_diagnostics": [security] * (limit + 1)},
            {**envelope, "related_diagnostics": [content]},
            {**envelope, "related_diagnostics": [{**security, "detail": {**security["detail"], "certificate": "synthetic-secret-canary"}}]},
            {key: value for key, value in envelope.items() if key != "diagnostic"},
            {**envelope, "execution": {**execution, "phase": "pool_connect"}},
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(deployment.DiagnosticFailure): deployment.validate_verifier_result(bad)
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        migration = load("tls_migration", folder / "run-migration/script.py")
        administration = load("tls_administration", folder / "run-administration/script.py")
        for operation in ["migration", "administration"]:
            record = {**primary, "detail": {**primary["detail"], "operation": operation, "effect": "unknown", "phase": "pool_query"}}
            value = {"verdict": "rejected", "code": "PERSISTENCE_MIGRATION_NOT_CONFIRMED" if operation == "migration" else "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "diagnostic": record, "related_diagnostics": [security]}
            if operation == "migration": value["stage"] = "migration"
            for valid in [True, False]:
                test_value = copy.deepcopy(value)
                if not valid: test_value["diagnostic"]["detail"]["operation"] = "readiness"
                logs = (True, {"events": [{"message": json.dumps(test_value)}]}, "ok")
                if operation == "migration":
                    with patch.object(migration, "aws", return_value=logs):
                        result, _ = migration.migration_log_rejection({"taskArn": "fixture/task-1"})
                else:
                    output = io.StringIO()
                    with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=logs), contextlib.redirect_stdout(output):
                        administration.accept({"taskArn": "fixture/task-1"}, 10, "observe-migration-state")
                    result = json.loads(output.getvalue()).get("facts")
                if valid:
                    self.assertEqual(result["related_diagnostics"], [security])
                elif operation == "administration":
                    # The intentionally synthetic task identity is unavailable
                    # to the new bounded collector. Preserve that independent
                    # fact, without accepting the wrong-operation TLS record.
                    self.assertEqual(result, {"task_log_observation": "unavailable"})
                else:
                    self.assertIsNone(result)
    def test_persistence_source_companions_match_typescript_without_widening_tls_policy(self):
        record = lambda code, detail, version=1: {"schema": "core/diagnostic-record/v1", "code": code, "definitionVersion": version, "detail": detail}
        local = record("persistence.local-rejected", {"operation": "migration", "field": "checksum", "condition": "checksum-mismatch", "phase": "after-statements", "effect": "unknown", "ordinal": 0})
        sources = [record("core.persistence.in-memory-boundary-failed", {"operation": "initialize", "phase": "get-id", "reason": "boundary-threw", "effect": "write-not-reached", "ordinal": ordinal}) for ordinal in range(9)]
        native = record("persistence.credential-rejected", {"phase": "pool_query", "classification": "authentication_rejected", "codeStatus": "recognized", "operation": "migration", "effect": "unknown"}, 2)
        tls = record("persistence.trust-validation-failed", {**native["detail"], "classification": "tls_trust_invalid"}, 2)
        peer = record("security.peer-identity-verification-failed", {"phase": "peer-identity-verification", "reason": "hostname-mismatch", "effect": "not-assessed"})
        content = record("security.certificate-block-invalid", {"phase": "certificate-content-parsing", "reason": "malformed-certificate-block", "blockNumber": 1, "effect": "not-assessed"})
        configuration = record("kanbien-core-server.configuration-invalid", {"issues": [{"setting": "database.host", "reason": "missing"}]})
        cases = [
            [local, sources[1:]], [sources[0], [local]], [native, sources[1:]], [tls, [peer, sources[1]]],
            [native, [peer]], [local, [content]], [tls, [content]], [configuration, [sources[0]]],
            [local, sources], [local, [{**sources[0], "definitionVersion": 999}]],
            [local, [{**sources[0], "detail": {**sources[0]["detail"], "raw": "synthetic-secret-canary"}}]],
            [local, [{**sources[0], "code": "unknown.synthetic-canary"}]], [local, None],
        ]
        expected = []
        for primary, related in cases:
            try:
                self.assertEqual(deployment.validate_related_diagnostics(related, primary), related)
                expected.append(True)
            except deployment.DiagnosticFailure:
                expected.append(False)
        self.assertEqual(expected, [True] * 4 + [False] * 9)
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {persistenceTaskDiagnosticFields:fields}=require(path.join(root,'infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js'));process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([primary,related])=>fields(primary,related).related_diagnostics!==undefined)));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(cases), capture_output=True, text=True, check=True, cwd=ROOT, env={**os.environ, "NODE_PATH": str(ROOT / "node_modules")})
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(reader.validate_operation_record(local, "migration"), local)
        with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(local, "administration")
        with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(sources[0], "migration")
        self.assertEqual(reader.validate_operation_record(sources[0], "migration", allow_core_source=True), sources[0], "Only the task envelope explicitly selects source-helper evidence")
        with self.assertRaises(reader.DiagnosticContractError): reader.validate_operation_record(sources[0], "synthetic-unknown-operation", allow_core_source=True)
        restore = {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED",
                   "execution": {"classification": "authentication_rejected", "phase": "pool_query", "code_status": "recognized", "elapsed_ms": 1},
                   "diagnostic": sources[0], "related_diagnostics": sources[1:]}
        self.assertEqual(deployment.validate_verifier_result(restore), restore)
        boundary = {"schema": "core/diagnostic-record/v1", "code": "persistence.boundary-observed", "definitionVersion": 1,
                    "detail": {"operation": "restore_verification", "phase": "invocation", "boundary": "body", "condition": "threw", "effect": "not-assessed"}}
        self.assertEqual(deployment.validate_verifier_result({**restore, "diagnostic": boundary}), {**restore, "diagnostic": boundary},
                         "Body boundary phase is not a newly invented native execution phase")
        for bad in [{**restore, "verdict": "accepted"}, {**restore, "execution": {**restore["execution"], "phase": "synthetic-secret-canary"}},
                    {**restore, "code": "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID"}, {**restore, "diagnostic": content}]:
            with self.assertRaises(deployment.DiagnosticFailure): deployment.validate_verifier_result(bad)
        folder = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
        migration = load("b04_source_migration", folder / "run-migration/script.py")
        administration = load("b04_source_administration", folder / "run-administration/script.py")
        for operation in ["migration", "administration"]:
            for source in [sources[0], {**local, "detail": {**local["detail"], "operation": operation}}]:
                value = {"verdict": "rejected", "code": "PERSISTENCE_MIGRATION_NOT_CONFIRMED" if operation == "migration" else "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED",
                         "diagnostic": source, "related_diagnostics": sources[1:]}
                if operation == "migration": value["stage"] = "migration"
                logs = (True, {"events": [{"message": json.dumps(value)}]}, "ok")
                if operation == "migration":
                    with patch.object(migration, "aws", return_value=logs):
                        result, _ = migration.migration_log_rejection({"taskArn": "fixture/task-1"})
                else:
                    output = io.StringIO()
                    with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=logs), contextlib.redirect_stdout(output):
                        administration.accept({"taskArn": "fixture/task-1"}, 10, "observe-migration-state")
                    result = json.loads(output.getvalue()).get("facts")
                self.assertEqual(result["diagnostic"], source)
                self.assertEqual(result["related_diagnostics"], sources[1:])

    def test_b04_additive_records_have_strict_cross_language_parity(self):
        record = lambda code, detail, version=1: {"schema": "core/diagnostic-record/v1", "code": code, "definitionVersion": version, "detail": detail}
        records = [
            record("core.persistence.validation-rejected", {"operation": "page-request", "field": "limit", "reason": "not-integer", "effect": "rejected"}),
            record("core.persistence.in-memory-boundary-failed", {"operation": "save", "phase": "clone-after-write", "reason": "boundary-threw", "effect": "write-completed"}),
            record("persistence.local-rejected", {"operation": "validate-identifier", "field": "schema", "condition": "pattern", "phase": "preflight", "effect": "not-started"}),
            record("persistence.boundary-observed", {"operation": "connection-pool", "phase": "event", "boundary": "idle-pool", "condition": "rejected", "effect": "not-assessed"}),
            record("persistence.stored-record-observed", {"operation": "read_outbox", "reduction": "null", "effect": "not-assessed", "issues": [{"field": "row", "condition": "absent", "ordinal": 0, "count": 1}], "truncated": False}),
            record("persistence.credential-rejected", {"phase": "unknown", "classification": "authentication_rejected", "codeStatus": "recognized", "operation": "create", "boundary": "primary", "effect": "unknown"}, 3),
            record("persistence.reconciliation-observed", {"operation": "create", "primaryOutcome": "call-threw", "observed": "matching", "effect": "read-result-observed"}),
        ]
        cases = records + [
            {**record, "definitionVersion": 999} for record in records
        ] + [{**record, "detail": {**record["detail"], "value": "synthetic-secret-canary"}} for record in records] + [
            {**records[5], "detail": {**records[5]["detail"], "effect": "not-started"}},
            {**records[5], "definitionVersion": 2},
            {**records[6], "detail": {**records[6]["detail"], "effect": "created"}},
            {**records[4], "detail": {**records[4]["detail"], "issues": records[4]["detail"]["issues"] * 17}},
        ]
        expected = []
        for candidate in cases:
            try:
                self.assertEqual(reader.validate_selected_record(candidate), candidate)
                expected.append(True)
            except reader.DiagnosticContractError:
                expected.append(False)
        self.assertEqual(expected, [True] * len(records) + [False] * (len(cases) - len(records)))
        javascript = "const fs=require('node:fs'),path=require('node:path');const root=path.resolve('.cache/diagnostic-catalog-export');const {selectDiagnosticEvidence}=require(path.join(root,'packages/core/src/diagnostics/index.js'));const {coreDiagnosticCatalog}=require(path.join(root,'packages/core/src/diagnostic-catalog.js'));const {platformPersistenceDiagnosticCatalog}=require(path.join(root,'platform/persistence/src/diagnostics.js'));const defs=[...coreDiagnosticCatalog.definitions,...platformPersistenceDiagnosticCatalog.definitions];process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(diagnosticRecord=>selectDiagnosticEvidence(defs,{diagnosticRecord}).diagnosticRecord!==undefined)));"
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(cases), capture_output=True, text=True, check=True, cwd=ROOT, env={**os.environ, "NODE_PATH": str(ROOT / "node_modules")})
        self.assertEqual(json.loads(result.stdout), expected)

    def test_historical_envelope_and_new_detail_are_both_readable(self):
        deployment.validate_verifier_result({"verdict": "rejected", "code": "SAFE_REJECTED"})
        record = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.configuration-invalid", "definitionVersion": 1,
                  "detail": {"issues": [{"setting": "database.host", "reason": "blank"}]}}
        value = {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "rejected", "code": "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID", "diagnostic": record}
        self.assertEqual(deployment.validate_verifier_result(value)["diagnostic"], record)
        bad = copy.deepcopy(value)
        bad["diagnostic"]["detail"]["issues"][0]["value"] = "synthetic-sensitive-canary"
        with self.assertRaises(deployment.DiagnosticFailure): deployment.validate_verifier_result(bad)
        with self.assertRaises(deployment.DiagnosticFailure): deployment.validate_verifier_result({**value, "verdict": "accepted"})

if __name__ == "__main__":
    unittest.main(verbosity=2)

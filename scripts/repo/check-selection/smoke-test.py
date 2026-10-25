#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection
#   version: 2
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Prove reusable impact discovery, fail-closed selection, stage isolation and evidence invalidation with local fixtures.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.test.check-selection.wrapper
#     path: scripts/repo/check-selection/smoke-test.sh
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('selection', ROOT / 'scripts/repo/check-selection/script.py')
assert spec and spec.loader
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)
import local_cache
SOURCE_SCOPE = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime'


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        self.target = self.root / 'infra/04.deploy/03.product/targets/synthetic/20-scopes'
        self.scope = self.target / 'synthetic-worker'
        shutil.copytree(SOURCE_SCOPE, self.scope)
        self.contract_path = self.scope / '00-declaration/declaration-contract.yml'
        self.contract = yaml.safe_load(self.contract_path.read_text())
        self.contract.update(target='synthetic', scope='synthetic-worker')
        self.contract.pop('acceptance', None)
        self.contract['dependencies']['required'] = ['synthetic-catalog']
        server = self.contract['health_recovery']['workloads'][0]
        server['readiness']['depends_on'] = ['synthetic-catalog']
        server['dependency_failures'] = [{'dependency': 'synthetic-catalog', 'unavailable': {'result': 'not-ready', 'diagnostic_code': 'CATALOG_UNAVAILABLE'}}]
        server['health_signal_mapping']['provider_replacement_signal'] = 'liveness'
        server['health_signal_mapping'].pop('dependency_free_replacement_basis', None)
        self.contract['program'] = {'id': 'generic-server', 'contract': 'program.yml', 'image_contract': 'image.yml', 'local_proof': 'scripts/local.sh'}
        self.contract['workload']['runtime_template'] = '30-provider-realization/fixture.yml'
        self.contract['change_impact'] = {'schema': 'deploy/change-impact/v1', 'inputs': ['src', 'program.yml'], 'requirements': [{
            'id': 'synthetic-runtime', 'purpose': 'A second dependency-bearing scope proves reuse.', 'owner': 'synthetic-owner',
            'required_by': ['consumer.ts'], 'declarations': ['src/main.ts'], 'expectation': 'Declared implementation and local proof exist.',
            'local_proofs': ['local', 'scope-inventory', 'runnable-program'], 'package_proofs': [], 'target_proofs': [], 'run_proofs': [],
            'not_applicable': {'package_proofs': 'Fixture has no packaged deployment.', 'target_proofs': 'Fixture has no provider.', 'run_proofs': 'Fixture never runs on a target.'}}]}
        self.requirement = self.contract['change_impact']['requirements'][0]
        self.auxiliary = copy.deepcopy(self.requirement)
        self.auxiliary['id'] = 'local-observation-only'
        self.auxiliary['local_proofs'] = ['local']
        self.contract['change_impact']['requirements'].append(self.auxiliary)
        self.requirement.update(package_proofs=['package'], target_proofs=['live'], run_proofs=['acceptance'], not_applicable={})
        binding_path = self.scope / '10-workload-binding/workload-binding.yml'
        binding = yaml.safe_load(binding_path.read_text())
        binding.update(target='synthetic', scope='synthetic-worker', program_id='generic-server', program_contract='program.yml', image_contract='image.yml')
        binding['proposed_provider_binding']['template'] = '30-provider-realization/fixture.yml'
        binding['workloads'][0]['health_signal_mapping'] = copy.deepcopy(server['health_signal_mapping'])
        for workload in binding['workloads']: workload['execution']['source_reference'] = 'src/main.ts'
        write(binding_path, binding)
        write(self.target / 'scope-index.yml', {'schema': 'deploy/scope-lifecycle-inventory/v1', 'target': 'synthetic', 'scopes': [{'id': 'synthetic-worker', 'lifecycle': 'active', 'declaration': 'synthetic-worker/00-declaration/declaration-contract.yml', 'workload_binding': 'synthetic-worker/10-workload-binding/workload-binding.yml', 'workload_ownership': [item['id'] for item in binding['workloads']]}], 'legacy_exceptions': []})
        for path in ('src/main.ts', 'consumer.ts', 'program.yml', 'image.yml', 'infra/04.deploy/03.product/targets/synthetic/30-provider-realization/fixture.yml'):
            file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_text('fixture\n')
        self.check_script('local', ['read-only', 'writes-files'], 'echo local >> counts\n')
        self.check_script('package', ['network'], 'echo forbidden >> operations\n')
        self.check_script('live', ['aws-mutation'], 'echo forbidden >> operations\n')
        self.check_script('acceptance', ['aws-mutation'], 'echo forbidden >> operations\n')
        self.check_script('inventory', ['read-only'], 'fixture_target="$PWD/$1"\ncd "' + str(ROOT) + '"\nexec python3 scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.py --target-root "$fixture_target" --json\n')
        self.check_script('program', ['read-only'], 'exec python3 "' + str(ROOT / 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py') + '" --contract "$1" --json\n')
        shutil.copyfile(ROOT / 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/fixtures/valid-contract.yml', self.root / 'program.yml')
        program_index = yaml.safe_load((self.root / 'program.yml').read_text())
        program_index['runnable_programs'][0].update(source_entrypoint='src/main.ts', configuration_boundary='src', dependency_failure_boundary='src', local_proof='scripts/local.sh')
        write(self.root / 'program.yml', program_index)
        write(self.root / 'image.yml', {'schema': 'deploy/core-server-image-contract/v1', 'id': 'generic-server-image', 'program_id': 'generic-server', 'runnable_program_contract': 'program.yml', 'compiled_entrypoint': 'artifacts/generic-server.main.js', 'command': ['artifacts/generic-server.main.js'], 'payload': {'allowed_program': 'generic-server'}})
        self.catalog = {'schema': 'repo/check-catalog/v1', 'checks': {
            'scope-inventory': {'argv': ['bash', 'scripts/inventory.sh', '{target_root}'], 'stage': 'local', 'effects': ['read-only'], 'evidence_class': 'static'},
            'runnable-program': {'argv': ['bash', 'scripts/program.sh', '{program_contract}'], 'stage': 'local', 'effects': ['read-only'], 'evidence_class': 'static'},
            'local': {'argv': ['bash', 'scripts/local.sh'], 'stage': 'local', 'effects': ['read-only', 'writes-files'], 'evidence_class': 'static'},
            'package': {'argv': ['bash', 'scripts/package.sh'], 'stage': 'package', 'effects': ['network'], 'evidence_class': 'container-qualification'},
            'acceptance': {'argv': ['bash', 'scripts/acceptance.sh'], 'stage': 'acceptance', 'effects': ['aws-mutation'], 'evidence_class': 'live'},
            'live': {'argv': ['bash', 'scripts/live.sh'], 'stage': 'deploy', 'effects': ['aws-mutation'], 'evidence_class': 'live'}}}
        for identity, check in self.catalog['checks'].items():
            if identity in {'scope-inventory', 'runnable-program'}:
                parameter = 'target_root' if identity == 'scope-inventory' else 'program_contract'
                check['applicability'] = {'kind': 'generic', 'contract_schema': 'deploy/target-scope-contract/v1' if identity == 'scope-inventory' else 'deploy/runnable-program-contract/v1', 'context_parameters': [parameter]}
                check['owner'] = 'fixture.inventory' if identity == 'scope-inventory' else 'fixture.program'
                check['capability'] = 'scripts/' + identity + '.capability.yml'
                write(self.root / check['capability'], {'schema': 'repo/check-capability/v1', 'owner': check['owner'], 'command': check['argv'][1], 'argv': check['argv'], 'contract_schema': check['applicability']['contract_schema'], 'context_parameters': [parameter]})
            else:
                check['applicability'] = {'kind': 'bound', 'program_id': 'generic-server', 'image_id': 'generic-server-image', 'target': 'synthetic', 'scope': 'synthetic-worker'}
            if check['stage'] == 'local': check['runtime'] = {'tools': ['bash', 'python3'], 'environment': ['LANG', 'PYTHONPATH']}
        self.catalog_path = self.root / 'scripts/repo/check-selection/checks.yml'
        self.save()

    def check_script(self, name: str, effects: list[str], body: str) -> None:
        path = self.root / ('scripts/' + name + '.sh'); path.parent.mkdir(exist_ok=True)
        path.write_text('#!/bin/bash\n# agentic-artifact:\n#   schema: agentic-artifact/v3\n#   id: fixture.' + name + '\n#   effects: ' + json.dumps(effects) + '\n' + body)
        path.chmod(0o755)

    def save(self) -> None:
        write(self.contract_path, self.contract); write(self.catalog_path, self.catalog)

    def run_plan(self, *, paths=None, stage='local', execute=False, evidence=None, staged=False):
        args = argparse.Namespace(root=self.root, catalog=self.catalog_path, paths=paths or ['src/main.ts'], staged=staged, all=False, stage=stage, execute_local=execute, evidence=evidence, json=True)
        files = [path.relative_to(self.root).as_posix() for path in self.root.rglob('*') if path.is_file() and '.git' not in path.relative_to(self.root).parts]
        def git(_root, *arguments):
            if arguments[0] == 'diff': return 'src/old.ts\0src/main.ts\0' if '--cached' in arguments else ''
            if arguments[0] == 'ls-files': return ''
            return getattr(self, 'revision', 'a' * 40)
        with patch.object(selection, 'repository_paths', return_value=files), patch.object(selection, 'git', side_effect=git): return selection.plan(args)

    def codes(self, report): return {item['code'] for item in report['findings']}

    def test_synthetic_scope_reuses_existing_generic_validators_and_accepts_valid_na(self):
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual([scope['scope'] for scope in report['scopes']], ['synthetic-worker'])
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')
        self.assertEqual({item['check_id'] for item in report['checks'] if item['status'] == 'passed'}, {'local', 'scope-inventory', 'runnable-program'})
        self.assertEqual(self.contract['persistence_diagnostics']['status'], 'not-applicable')

    def test_existing_persistence_scope_has_coverage(self):
        catalog = selection.coverage.document(ROOT / 'scripts/repo/check-selection/checks.yml')
        report = selection.coverage.inspect(ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml', ROOT, catalog)
        self.assertEqual(report['verdict'], 'covered', report)
        self.assertIn('persistence-composition', report['required_checks'])

    def test_duplicate_commands_run_once(self):
        self.catalog['checks']['alias'] = copy.deepcopy(self.catalog['checks']['local'])
        self.requirement['local_proofs'].append('alias'); self.save()
        report = self.run_plan(execute=True)
        self.assertEqual(report['verdict'], 'passed', report)
        self.assertEqual(len(report['checks']), 6)
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')

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

    def test_local_runner_and_commit_hook_declare_write_effects(self):
        for path in ('scripts/repo/check-selection/script.sh', 'scripts/repo/commit-gates/script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'):
            self.assertIn('writes-files', selection.metadata(ROOT / path)['effects'])
        result = subprocess.run(['bash', 'scripts/01.harness/run-governed-script.sh', 'scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh'], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approval-sensitive script requires --approved-action', result.stderr)

    def test_mandatory_scope_checks_cannot_be_removed_to_hide_broken_health(self):
        self.contract['health_recovery'] = {}
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
        self.assertIn('check-input-missing', self.codes(self.run_plan()))

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
        with patch.dict(os.environ, {'LANG': 'C.fixture'}): self.run_plan(execute=True)
        self.assertEqual((self.root / 'counts').read_text(), 'local\nlocal\n')

    def test_imported_report_cannot_qualify_local_check(self):
        planned = self.run_plan()
        for item in planned['checks']: item.update(status='passed', exit_code=0)
        evidence = self.root / 'imported.json'; evidence.write_text(json.dumps(planned))
        result = self.run_plan(execute=True, evidence=evidence)
        self.assertEqual(result['evidence_import_status'], 'rejected-untrusted-report')
        self.assertEqual(next(item for item in result['checks'] if item['check_id'] == 'local')['evidence_source'], 'local-runner')
        self.assertEqual((self.root / 'counts').read_text(), 'local\n')

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
        self.assertIn('local-cache-unavailable', self.codes(self.run_plan(execute=True)))
        private.unlink(); private.mkdir(mode=0o755)
        self.assertIn('local-cache-unavailable', self.codes(self.run_plan(execute=True)))
        self.assertFalse((self.root / 'counts').exists())

    def test_real_repository_hook_reuses_local_evidence_without_report_argument(self):
        # Actual source-owned hook, selector, and cache run in an isolated Git
        # worktree. The unrelated revision is simulated without creating commits.
        for relative in ('scripts/repo/commit-gates/script.sh', 'scripts/repo/check-selection/script.sh', 'scripts/repo/check-selection/script.py', 'scripts/repo/check-selection/local_cache.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py', 'scripts/01.harness/artifact-metadata/header_discovery.py'):
            target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / relative, target)
        gate = self.root / 'scripts/01.harness/artifact-metadata/generate-index/script.sh'; gate.parent.mkdir(parents=True); gate.write_text('#!/bin/bash\nexit 0\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        # Stage only the source subject: definition setup is fixture baseline.
        shim = self.root / 'bin'; shim.mkdir()
        git = shutil.which('git'); revision = self.root / 'revision'; revision.write_text('a' * 40)
        (shim / 'git').write_text('#!/bin/bash\ncase "$*" in *"rev-parse HEAD"*) cat "' + str(revision) + '";; *"diff --cached --name-only --no-renames -z"*) printf "src/main.ts\\0";; *) exec "' + str(git) + '" "$@";; esac\n')
        (shim / 'git').chmod(0o755)
        environment = {**os.environ, 'PATH': str(shim) + ':' + os.environ['PATH']}
        def invoke():
            result = subprocess.run(['bash', 'scripts/repo/commit-gates/script.sh'], cwd=self.root, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{')))
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
        def changed_runtime(root, declaration): return {**original(root, declaration), 'fixture_tool_version': 'changed'}
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

    def node_package(self, name, *, dependencies=None, optional=None, path=None):
        package = path or self.root / 'node_modules' / name
        package.mkdir(parents=True, exist_ok=True)
        (package / 'package.json').write_text(json.dumps({'name': name, 'version': '1.0.0', 'dependencies': dependencies or {}, 'optionalDependencies': optional or {}}))
        (package / 'index.js').write_text('module.exports = {};\n')
        return package

    def node_check(self, packages):
        self.catalog['checks']['local']['runtime'].update(tools=['bash', 'python3', 'node'], node_packages=packages)
        self.save()

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

    def test_node_checks_require_explicit_installation_declaration(self):
        self.catalog['checks']['local']['runtime']['tools'].append('node'); self.save()
        self.assertIn('check-runtime-node-installation-invalid', self.codes(self.run_plan(execute=True)))
        self.catalog['checks']['local']['runtime']['node_packages'] = []; self.save()
        self.assertEqual(self.run_plan(execute=True)['verdict'], 'passed')

    def test_shell_strings_and_outside_paths_are_refused(self):
        self.catalog['checks']['local']['argv'] = ['bash', 'scripts/local.sh; echo unsafe']; self.save()
        self.assertIn('check-argv-invalid', self.codes(self.run_plan(execute=True)))
        self.assertIn('changed-path-invalid', self.codes(self.run_plan(paths=['../outside'])))


if __name__ == '__main__':
    unittest.main(verbosity=2)

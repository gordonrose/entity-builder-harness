#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection
#   version: 1
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
SOURCE_SCOPE = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime'


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.target = self.root / 'infra/04.deploy/03.product/targets/synthetic/20-scopes'
        self.scope = self.target / 'synthetic-worker'
        shutil.copytree(SOURCE_SCOPE, self.scope)
        self.contract_path = self.scope / '00-declaration/declaration-contract.yml'
        self.contract = yaml.safe_load(self.contract_path.read_text())
        self.contract.update(target='synthetic', scope='synthetic-worker')
        self.contract['program'] = {'id': 'generic-server', 'contract': 'program.yml', 'image_contract': 'image.yml', 'local_proof': 'scripts/local.sh'}
        self.contract['workload']['runtime_template'] = '30-provider-realization/fixture.yml'
        self.contract['change_impact'] = {'schema': 'deploy/change-impact/v1', 'inputs': ['src', 'program.yml'], 'requirements': [{
            'id': 'synthetic-runtime', 'purpose': 'A second dependency-free scope proves reuse.', 'owner': 'synthetic-owner',
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
        files = [path.relative_to(self.root).as_posix() for path in self.root.rglob('*') if path.is_file()]
        def git(_root, *arguments): return 'src/old.ts\0src/main.ts\0' if arguments[0] == 'diff' else 'a' * 40
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
        self.catalog['checks']['other'] = {'argv': ['bash', 'scripts/other.sh'], 'stage': 'local', 'effects': ['read-only', 'writes-files'], 'evidence_class': 'static'}
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

    def test_shell_strings_and_outside_paths_are_refused(self):
        self.catalog['checks']['local']['argv'] = ['bash', 'scripts/local.sh; echo unsafe']; self.save()
        self.assertIn('check-argv-invalid', self.codes(self.run_plan(execute=True)))
        self.assertIn('changed-path-invalid', self.codes(self.run_plan(paths=['../outside'])))


if __name__ == '__main__':
    unittest.main(verbosity=2)

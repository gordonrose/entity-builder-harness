#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.delivery-inventory
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.declaration-coverage
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Exercise independent route discovery and pre-build blocking through real command interfaces and disposable targets.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.inventory-deploy-control.smoke-test
#     path: scripts/04.deploy/inventory-deploy-control/smoke-test.sh
from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import unittest
import copy
import yaml

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('selector_fixture', ROOT / 'scripts/repo/check-selection/smoke-test.py')
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)

class DeliveryInventoryCLI(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.SelectionTests('test_synthetic_scope_reuses_existing_generic_validators_and_accepts_valid_na')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.bin = self.root / 'bin'; self.bin.mkdir()
        git = shutil.which('git')
        (self.bin / 'git').write_text('#!/bin/bash\ncase "$*" in *"rev-parse HEAD"*) printf "%040d\\n" 1;; *) exec "' + git + '" "$@";; esac\n')
        (self.bin / 'git').chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'], 'PYTHONDONTWRITEBYTECODE': '1'}

    def invoke(self):
        result = subprocess.run(['python3', str(ROOT / 'scripts/04.deploy/inventory-deploy-control/script.py'), '--root', str(self.root), '--delivery', '--check', '--json'], cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_valid_second_target_has_bound_report(self):
        code, report = self.invoke()
        self.assertEqual(code, 0, report['findings'])
        self.assertEqual(report['source_revision'], '0' * 39 + '1')
        self.assertEqual(report['routes'][0]['target'], 'synthetic')
        self.assertTrue(report['inputs']); self.assertTrue(report['routes'][0]['chain'])

    def test_catalogued_dormant_root_does_not_block_active_delivery_inventory(self):
        dormant = self.root / 'dormant-rag'
        dormant.mkdir()
        (dormant / 'unregistered-deploy.sh').write_text('#!/bin/bash\naws cloudformation deploy --stack-name dormant\n')
        self.fixture.catalog['dormant_impact_roots'] = ['dormant-rag']
        self.fixture.save()
        code, report = self.invoke()
        self.assertEqual(code, 0, report['findings'])
        self.assertNotIn('dormant-rag/unregistered-deploy.sh', {item['path'] for item in report['inputs']})

    def test_dormant_package_command_requires_exact_governed_action_under_dormant_root(self):
        dormant = self.root / 'dormant-rag'; dormant.mkdir()
        action = dormant / 'script.sh'; action.write_text('#!/bin/bash\nprintf dormant\n')
        package = self.root / 'package.json'
        package.write_text(json.dumps({'scripts': {'rag:fixture': 'bash scripts/01.harness/run-governed-script.sh --approved-action dormant-rag/script.sh'}}))
        wrapper = self.root / 'scripts/01.harness/run-governed-script.sh'; wrapper.parent.mkdir(parents=True, exist_ok=True); wrapper.write_text('#!/bin/bash\n')
        self.fixture.catalog['dormant_impact_roots'] = ['dormant-rag']
        self.fixture.catalog['dormant_package_commands'] = ['package.json#scripts.rag:fixture']
        self.fixture.save()
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        entry = next(item for item in report['entrypoints'] if item['path'] == 'package.json#scripts.rag:fixture')
        self.assertEqual(entry['classification'], 'dormant')
        package.write_text(json.dumps({'scripts': {'rag:fixture': 'bash scripts/01.harness/run-governed-script.sh --approved-action scripts/automation/active.sh'}}))
        code, report = self.invoke(); self.assertEqual(code, 1)
        self.assertIn(('delivery-dormant-package-command-invalid', 'package.json#scripts.rag:fixture'), {(item['code'], item['path']) for item in report['findings']})

    def test_effective_image_context_inputs_are_bound_without_becoming_images(self):
        ignore = self.root / 'Dockerfile.dockerignore'
        ignore.write_text('**\n!src/**\n')
        code, before = self.invoke(); self.assertEqual(code, 0, before['findings'])
        self.assertIn('Dockerfile.dockerignore', {item['path'] for item in before['inputs']})
        self.assertNotIn('Dockerfile.dockerignore', {item['path'] for item in before['entrypoints']})
        ignore.write_text('**\n!src/**\n!config/**\n')
        code, after = self.invoke(); self.assertEqual(code, 0, after['findings'])
        self.assertNotEqual(before['input_digest'], after['input_digest'])

    def test_scope_without_any_index_is_detected(self):
        (self.fixture.target / 'scope-index.yml').unlink()
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('scope-inventory-missing', {f['code'] for f in report['findings']})

    def test_new_workflow_image_and_alternative_command_are_not_implicitly_registered(self):
        for path, content in {
            '.github/workflows/unregistered.yml': 'jobs:\n  publish:\n    steps:\n      - run: docker push example\n',
            'infra/04.deploy/second/image/Dockerfile': 'FROM scratch\n',
            'scripts/04.deploy/alternative-deploy/script.py': 'if __name__ == "__main__":\n    print("mutation")\n',
        }.items():
            file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(content)
        code, report = self.invoke()
        self.assertEqual(code, 1)
        gaps = {f['path'] for f in report['findings'] if f['code'] == 'delivery-entrypoint-unregistered'}
        self.assertEqual(len(gaps), 3, gaps)

    def test_governance_reference_does_not_substitute_for_a_requirement_chain(self):
        command = self.root / 'scripts/04.deploy/orphan/script.sh'
        command.parent.mkdir(parents=True)
        command.write_text('#!/bin/bash\naws cloudformation deploy --stack-name orphan\n')
        owner = self.root / '.agentic/workflow.md'; owner.parent.mkdir(exist_ok=True)
        owner.write_text('Call scripts/04.deploy/orphan/script.sh only when approved.\n')
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn(('delivery-consumer-unbound', 'scripts/04.deploy/orphan/script.sh'), {(f['code'], f['path']) for f in report['findings']})

    def test_test_like_filename_does_not_exempt_a_provider_command(self):
        command = self.root / 'scripts/04.deploy/orphan/publish-test.sh'
        command.parent.mkdir(parents=True)
        command.write_text('#!/bin/bash\naws cloudformation deploy --stack-name orphan\n')
        owner = self.root / '.agentic/workflow.md'; owner.parent.mkdir(exist_ok=True)
        owner.write_text('Use scripts/04.deploy/orphan/publish-test.sh when approved.\n')
        for declared in ('', '#   effects: [network]\n', '#   effects: [aws-mutation]\n'):
            command.write_text('#!/bin/bash\n' + declared + 'aws cloudformation deploy --stack-name orphan\n')
            code, report = self.invoke()
            self.assertEqual(code, 1)
            self.assertIn('delivery-consumer-unbound', {f['code'] for f in report['findings']})

    def invoke_selector(self, path):
        result = subprocess.run(['python3', str(ROOT / 'scripts/repo/check-selection/script.py'), '--root', str(self.root), '--paths', path, '--json'], cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def automation(self, name='publish-test.sh', declared='[network, aws-mutation]'):
        relative = 'scripts/automation/' + name
        target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#!/bin/bash\n#   effects: ' + declared + '\nprintf "disposable fixture only\\n"\n')
        return relative

    def test_consequential_effects_override_filename_in_both_actual_clis(self):
        for name in ('publish.sh', 'publish-test.sh', 'publish-regression.sh'):
            with self.subTest(name=name):
                path = self.automation(name)
                code, report = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn(('delivery-entrypoint-unregistered', path), {(f['code'], f.get('path')) for f in report['findings']})
                # Focused selection consumes declared routes only. The independent
                # census, above, remains the mandatory global discovery gate.
                code, report = self.invoke_selector(path)
                self.assertEqual(code, 0, report['findings'])
                (self.root / path).unlink()

    def test_supported_javascript_effect_headers_override_fixture_names(self):
        for extension in ('mjs', 'js', 'cjs'):
            for header in ('//   effects: [network, aws-mutation]\n', '//   effects:\n//   - network\n//   - aws-mutation\n'):
                with self.subTest(extension=extension, header=header):
                    path = 'scripts/automation/publish-test.' + extension
                    target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('// agentic-artifact:\n' + header + 'console.log("fixture only");\n')
                    code, report = self.invoke()
                    self.assertEqual(code, 1)
                    self.assertIn(('delivery-entrypoint-unregistered', path), {(f['code'], f.get('path')) for f in report['findings']})
                    code, report = self.invoke_selector(path)
                    self.assertEqual(code, 0, report['findings'])
                    target.unlink()

    def test_bash_wrapper_and_npm_alias_require_each_consequential_implementation(self):
        path = self.automation()
        package = self.root / 'package.json'
        # A legitimate impact mapping must not mask missing delivery registration.
        self.fixture.catalog['repository_inputs'] = [{'inputs': ['package.json'], 'checks': ['local']}]
        self.fixture.save()
        for commands in ({'publish:fixture': 'bash ' + path},
                         {'invoke': 'bash ' + path, 'publish:fixture': 'npm run invoke'},
                         {'invoke': 'bash ' + path, 'publish:fixture': 'npm run-script invoke'},
                         {'publish:fixture': 'env MODE=fixture bash ./' + path},
                         {'publish:fixture': 'bash -c "bash ' + path + '"'}):
            with self.subTest(commands=commands):
                package.write_text(json.dumps({'scripts': commands}))
                code, report = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn(('delivery-command-unbound', 'package.json#scripts.publish:fixture'), {(f['code'], f.get('path')) for f in report['findings']})
                code, report = self.invoke_selector('package.json')
                self.assertEqual(code, 0, report['findings'])
        self.fixture.requirement['required_by'].append(path); self.fixture.save()
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        wrapped = next(x for x in report['entrypoints'] if x['path'] == 'package.json#scripts.publish:fixture')
        self.assertTrue(wrapped['routes']); self.assertIn(path, wrapped['implementation'])
        code, report = self.invoke_selector('package.json'); self.assertEqual(code, 0, report['findings'])
        package.write_text(json.dumps({'scripts': {'publish:fixture': 'bash ' + path + ' && aws cloudformation deploy --stack-name orphan'}}))
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn(('delivery-command-relationship-unsupported', 'package.json#scripts.publish:fixture'), {(f['code'], f.get('path')) for f in report['findings']})
        code, report = self.invoke_selector('package.json')
        self.assertEqual(code, 0, report['findings'])
        second = self.automation('second-test.sh')
        package.write_text(json.dumps({'scripts': {'publish:fixture': 'bash ' + path + ' && bash ' + second}}))
        code, report = self.invoke(); self.assertEqual(code, 1)
        self.assertIn(('delivery-command-unbound', 'package.json#scripts.publish:fixture'), {(f['code'], f.get('path')) for f in report['findings']})

    def test_governed_wrapper_resolves_action_with_and_without_interpreter(self):
        path = self.automation()
        self.fixture.requirement['required_by'].append(path); self.fixture.save()
        wrapper = 'scripts/01.harness/run-governed-script.sh'
        target = self.root / wrapper; target.parent.mkdir(parents=True)
        target.write_text('#!/bin/bash\n#   effects: [read-only]\n')
        for prefix in ('bash ', './'):
            (self.root / 'package.json').write_text(json.dumps({'scripts': {'publish:fixture': prefix + wrapper + ' --approved-action ' + path}}))
            code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
            entry = next(x for x in report['entrypoints'] if x['kind'] == 'package-command')
            self.assertIn(path, entry['implementation']); self.assertTrue(entry['routes'])

    def test_unknown_and_cyclic_delivery_aliases_are_not_success(self):
        package = self.root / 'package.json'
        for commands in ({'publish:fixture': 'npm run absent'},
                         {'publish:fixture': 'npm run loop', 'loop': 'npm run publish:fixture'},
                         {'publish:fixture': 'bash -c "$PUBLICATION_COMMAND"'},
                         {'publish:fixture': 'unknown-wrapper scripts/missing.sh'}):
            with self.subTest(commands=commands):
                package.write_text(json.dumps({'scripts': commands}))
                code, report = self.invoke(); self.assertEqual(code, 1)
                self.assertIn('delivery-command-relationship-unsupported', {f['code'] for f in report['findings']})

    def test_genuine_nonoperational_test_does_not_acquire_mutation_effects(self):
        path = self.automation(declared='[read-only, writes-files]')
        (self.root / path).write_text((self.root / path).read_text() + '# aws cloudformation deploy is inert fixture data\n')
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        self.assertNotIn(path, {x['path'] for x in report['entrypoints']})
        package = self.root / 'package.json'; package.write_text(json.dumps({'scripts': {'publish:fixture:check': 'bash ' + path}}))
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        entry = next(x for x in report['entrypoints'] if x['kind'] == 'package-command')
        self.assertFalse(entry['requires_delivery_chain'])

    def test_runtime_input_existing_file_cannot_hide_missing_delivery(self):
        binding_path = self.fixture.scope / '10-workload-binding/workload-binding.yml'
        binding = yaml.safe_load(binding_path.read_text())
        for item in binding['runtime_requirements']:
            item['runtime_inputs'] = {'CATALOG_ENDPOINT': {'source': 'src/main.ts'}}
        fixture.write(binding_path, binding)
        template_path = self.root / 'infra/04.deploy/03.product/targets/synthetic/30-provider-realization/fixture.yml'
        template = yaml.safe_load(template_path.read_text())
        for resource in template['Resources'].values(): resource['Properties']['ContainerDefinitions'][0]['Environment'] = []
        fixture.write(template_path, template)
        code, report = self.invoke()
        self.assertEqual(code, 1)
        codes = {f['code'] for f in report['findings']}
        self.assertIn('runtime-input-producer-unbound', codes)
        self.assertIn('runtime-required-configuration-missing', codes)

    def test_repeated_command_arguments_are_valid_when_delivered_exactly(self):
        binding_path = self.fixture.scope / '10-workload-binding/workload-binding.yml'
        binding = yaml.safe_load(binding_path.read_text())
        command = ['artifacts/generic-server.main.js', '--include', 'one', '--include', 'two']
        for item in binding['runtime_requirements']: item['command'] = command
        fixture.write(binding_path, binding)
        template_path = self.root / 'infra/04.deploy/03.product/targets/synthetic/30-provider-realization/fixture.yml'
        template = yaml.safe_load(template_path.read_text())
        for resource in template['Resources'].values(): resource['Properties']['ContainerDefinitions'][0]['Command'] = command
        fixture.write(template_path, template)
        code, report = self.invoke()
        self.assertEqual(code, 0, report['findings'])

    def test_named_service_and_its_nonstandard_executable_require_a_chain(self):
        service = self.root / 'packages/orphan/server.js'
        service.parent.mkdir(parents=True)
        service.write_text("import http from 'node:http'; http.createServer().listen(8080);\n")
        package = self.root / 'package.json'
        package.write_text(json.dumps({'scripts': {'serve:orphan': 'node packages/orphan/server.js'}}))
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn(('delivery-command-unbound', 'package.json#scripts.serve:orphan'), {(f['code'], f['path']) for f in report['findings']})
        self.assertIn('packages/orphan/server.js', {item['path'] for item in report['entrypoints'] if item['kind'] == 'runnable-program'})

    def test_root_images_and_direct_package_publication_are_discovered(self):
        for path in ('Dockerfile', 'Containerfile.alternate'):
            (self.root / path).write_text('FROM scratch\n')
        package = self.root / 'package.json'
        package.write_text(json.dumps({'scripts': {'publish:outside': 'docker build -f Dockerfile .'}}))
        code, report = self.invoke()
        self.assertEqual(code, 1)
        gaps = {(f['code'], f['path']) for f in report['findings']}
        self.assertIn(('delivery-entrypoint-unregistered', 'Dockerfile'), gaps)
        self.assertIn(('delivery-entrypoint-unregistered', 'Containerfile.alternate'), gaps)
        self.assertIn(('delivery-command-unbound', 'package.json#scripts.publish:outside'), gaps)

    def test_malformed_existing_declaration_is_not_silently_ignored(self):
        self.fixture.contract_path.write_text('schema: [unterminated\n')
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('delivery-declaration-invalid', {f['code'] for f in report['findings']})

    def test_default_cli_has_the_same_failure_semantics(self):
        (self.fixture.target / 'scope-index.yml').unlink()
        result = subprocess.run(['python3', str(ROOT / 'scripts/04.deploy/inventory-deploy-control/script.py'), '--root', str(self.root), '--check', '--json'], cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('scope-inventory-missing', {f['code'] for f in json.loads(result.stdout)['findings']})

    def old_declaration(self):
        profile = 'infra/04.deploy/old/target-profile.yml'
        self.old_path = self.root / 'infra/04.deploy/old/declaration-contract.yml'
        self.old_path.parent.mkdir(parents=True)
        fixture.write(self.root / profile, {'schema': 'deploy/platform-shell-target-profile/v1', 'id': 'old-target'})
        req = {'id': 'old-runtime', 'purpose': 'An existing declaration format retains executable proof.', 'owner': 'fixture', 'expectation': 'Configured worker succeeds.', 'required_by': ['consumer.ts'], 'declarations': [{'path': 'src/main.ts', 'expectation': 'Real executable source exists.'}], 'not_applicable': {}}
        for field, identity in [('local_proofs','local'), ('package_proofs','package'), ('target_proofs','live'), ('run_proofs','acceptance')]:
            proof = 'old-' + identity
            req[field] = [proof]
            self.fixture.catalog['checks'][proof] = copy.deepcopy(self.fixture.catalog['checks'][identity])
            self.fixture.catalog['checks'][proof]['applicability'] = {'kind': 'profile', 'target_profile': profile}
        self.old = {'schema': 'deploy/declaration-contract/v1', 'id': 'older-supported-route', 'target': {'profile': profile}, 'scope': {'covers': ['worker'], 'excludes': []}, 'requirements': [req]}
        self.fixture.save(); fixture.write(self.old_path, self.old)

    def test_existing_format_rejects_empty_chain_and_wrong_stage_or_target(self):
        self.old_declaration()
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        for mutation, expected in [('empty','requirement-chain-missing'), ('stage','requirement-proof-stage-invalid'), ('subject','requirement-check-subject-mismatch')]:
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(self.old)
                if mutation == 'empty': value['requirements'] = []
                if mutation == 'stage': value['requirements'][0]['target_proofs'] = ['old-local']
                if mutation == 'subject': value['requirements'][0]['target_proofs'] = ['live']
                fixture.write(self.old_path, value)
                code, report = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn(expected, {f['code'] for f in report['findings']})

    def test_existing_format_is_selected_by_actual_generic_cli(self):
        self.old_declaration()
        result = subprocess.run(['python3', str(ROOT / 'scripts/repo/check-selection/script.py'), '--root', str(self.root), '--paths', self.old_path.relative_to(self.root).as_posix(), '--json'], cwd=self.root, env=self.env, capture_output=True, text=True)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, report.get('findings'))
        self.assertIn('older-supported-route', {item['scope'] for item in report['scopes']})
        self.assertTrue({'old-local','old-package','old-live','old-acceptance'} <= {item['check_id'] for item in report['checks']})

    def test_ci_qualification_cannot_be_omitted_reordered_suppressed_or_substituted(self):
        path = '.github/workflows/delivery-coverage.yml'
        target = self.root / path; target.parent.mkdir(parents=True)
        source = yaml.safe_load((ROOT / path).read_text())
        self.fixture.catalog['repository_inputs'] = [{'inputs': [path], 'checks': ['local']}]
        self.fixture.save()
        fixture.write(target, source)
        code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        for mutation in ('omitted','conditional','suppressed','reordered','substituted','wrong-diff','missing-workflow'):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(source); steps = value['jobs']['source-and-local-proof']['steps']
                guard = next(item for item in steps if item.get('name') == 'Reconcile independent delivery census')
                if mutation == 'omitted': steps.remove(guard)
                if mutation == 'conditional': guard['if'] = '${{ false }}'
                if mutation == 'suppressed': guard['run'] += ' || true'
                if mutation == 'reordered': steps.remove(guard); steps.append(guard)
                if mutation == 'substituted': guard['run'] = 'echo qualified'
                if mutation == 'wrong-diff': steps[-1]['env']['BASE_SHA'] = 'accepted-old-revision'
                fixture.write(target, value)
                if mutation == 'missing-workflow': target.unlink()
                code, report = self.invoke()
                self.assertEqual(code, 1)
                self.assertTrue({'delivery-ci-enforcement-invalid','delivery-ci-workflow-missing'} & {f['code'] for f in report['findings']}, report)

    def test_ci_trigger_restrictions_cannot_disable_automatic_delivery_checks(self):
        path = '.github/workflows/delivery-coverage.yml'
        target = self.root / path; target.parent.mkdir(parents=True)
        source = yaml.safe_load((ROOT / path).read_text())
        event_key = 'on' if 'on' in source else True
        self.fixture.catalog['repository_inputs'] = [{'inputs': [path], 'checks': ['local']}]
        self.fixture.save()
        for trigger in (None, {}):
            source[event_key]['pull_request'] = trigger; fixture.write(target, source)
            code, report = self.invoke(); self.assertEqual(code, 0, report['findings'])
        for trigger in ({'paths': ['unrelated/**']}, {'paths': ['**', '!scripts/**']},
                        {'paths-ignore': ['infra/**', 'scripts/**']}, {'branches': ['unrelated']},
                        {'branches': ['**', '!main']}, {'branches-ignore': ['main']},
                        {'types': ['closed']}, {'paths': ['**']}, [], 'main'):
            with self.subTest(trigger=trigger):
                source[event_key]['pull_request'] = trigger; fixture.write(target, source)
                for code, report in (self.invoke(), self.invoke_selector(path)):
                    self.assertEqual(code, 1)
                    self.assertIn(('delivery-ci-enforcement-invalid', 'ci-pull-request-restrictions-unsupported'), {(f['code'], f.get('reference')) for f in report['findings']})

    def test_actual_builder_blocks_before_compilation_or_docker(self):
        for path in ('scripts/04.deploy/inventory-deploy-control/script.py', 'scripts/04.deploy/inventory-deploy-control/delivery_inventory.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / path, target)
        (self.root / 'package.json').write_text(json.dumps({'scripts': {'inventory': 'python3 scripts/04.deploy/inventory-deploy-control/script.py', 'coverage': 'python3 scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'}}))
        (self.fixture.target / 'scope-index.yml').unlink()
        marker = self.root / 'consequential-work'
        for command in ('docker', 'npm', 'tsc'):
            shim = self.bin / command; shim.write_text('#!/bin/bash\ntouch "' + str(marker) + '"\nexit 97\n'); shim.chmod(0o755)
        result = subprocess.run(['bash', str(ROOT / 'scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh')], cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('scope-inventory-missing', result.stdout + result.stderr)
        self.assertFalse(marker.exists())

if __name__ == '__main__': unittest.main(verbosity=2)

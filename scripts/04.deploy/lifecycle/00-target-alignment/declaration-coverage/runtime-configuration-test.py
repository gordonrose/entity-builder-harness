#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runtime-configuration
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise real declaration CLI failure for missing runtime configuration, commands, identities and secret injection.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.compiler.declaration-coverage
#     path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[5]
COMMAND = ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'

def copy_repository(root):
    subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
    shutil.copyfile(ROOT / 'package.json', root / 'package.json')
    # Real producers and adapters; mutations cannot touch accepted evidence.
    for path in ['.github', 'infra', 'scripts', '.agentic', 'packages', 'platform', 'products']:
        shutil.copytree(ROOT / path, root / path, ignore=shutil.ignore_patterns('__pycache__', 'node_modules', '.cache'))


class RuntimeConfigurationTests(unittest.TestCase):
    def test_command_alias_requires_its_own_runtime_input_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_repository(root)
            scope = root / 'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence'
            contract = scope / '00-declaration/declaration-contract.yml'
            route_path = scope / '00-declaration/acceptance-route-contract.yml'
            binding_path = scope / '10-workload-binding/workload-binding.yml'
            route = yaml.safe_load(route_path.read_text())
            binding = yaml.safe_load(binding_path.read_text())
            alias = 'zz-extra-producer'
            route['commands'][alias] = copy.deepcopy(route['commands']['isolated-restore'])
            workload = next(item for item in binding['runtime_requirements'] if item['workload'] == 'persistence-restoration-verifier-task')
            # An alias delivering the same observed input remains valid.
            workload['runtime_inputs']['PERSISTENCE_POSTGRES_HOST']['command'] = alias
            for conflicting in [False, True]:
                with self.subTest(conflicting=conflicting):
                    if conflicting:
                        route['commands'][alias]['runtime_input_contract']['names'] = ['NEVER_DELIVERED']
                        workload['runtime_inputs']['PERSISTENCE_POSTGRES_HOST']['command'] = 'isolated-restore'
                        workload['required_names'].append('NEVER_DELIVERED')
                        workload['runtime_inputs']['NEVER_DELIVERED'] = {
                            **workload['runtime_inputs']['PERSISTENCE_POSTGRES_HOST'], 'command': alias,
                        }
                    self.assertEqual(route['commands'][alias]['argv'], route['commands']['isolated-restore']['argv'])
                    route_path.write_text(yaml.safe_dump(route, sort_keys=False))
                    binding_path.write_text(yaml.safe_dump(binding, sort_keys=False))
                    result = subprocess.run(['python3', '-B', str(COMMAND), '--root', str(root), '--scope-contract', str(contract), '--json'], capture_output=True, text=True)
                    report = json.loads(result.stdout)
                    if conflicting:
                        self.assertNotEqual(result.returncode, 0, report)
                        self.assertEqual(report['findings'], [{'code': 'acceptance-route-runtime-input-command-mismatch', 'reference': alias}])
                    else:
                        self.assertEqual(result.returncode, 0, report)
                        self.assertEqual(report['findings'], [])


    def test_actual_cli_and_selected_workload_alternatives(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            copy_repository(root)
            scope=root/'infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence'
            contract=scope/'00-declaration/declaration-contract.yml'
            template=root/'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
            original=template.read_text()
            def run(expected=None):
                result=subprocess.run(['python3','-B',str(COMMAND),'--root',str(root),'--scope-contract',str(contract),'--json'],capture_output=True,text=True)
                report=json.loads(result.stdout)
                codes={item['code'] for item in report['findings']}
                if expected:self.assertNotEqual(result.returncode,0);self.assertIn(expected,codes)
                else:self.assertEqual(result.returncode,0,report)
            run()
            for changed, expected in [
                (original.replace('Name: PERSISTENCE_POSTGRES_HOST','Name: UNDECLARED_HOST'), 'runtime-required-configuration-missing'),
                (original.replace('Name: PLATFORM_OBSERVABILITY_METRICS_ENDPOINT','Name: UNDECLARED_ENDPOINT'), 'runtime-required-configuration-missing'),
                (original.replace('Name: PERSISTENCE_ADMINISTRATOR_CREDENTIALS','Name: UNDECLARED_SECRET'), 'runtime-secret-injection-missing'),
                (original.replace('Command: [artifacts/kanbien-core-server-persistence-migration.main.js]','Command: [artifacts/unrelated.main.js]'), 'runtime-workload-command-mismatch'),
                (original.replace('TaskRoleArn: !GetAtt MigrationTaskRole.Arn','TaskRoleArn: !Ref AWS::NoValue'), 'runtime-workload-identity-missing'),
                (original.replace("Action: rds-db:connect", "Action: rds-db:unrelated"), 'runtime-workload-permission-missing'),
            ]:
                self.assertNotEqual(changed, original, "negative mutation must change its intended boundary")
                template.write_text(changed);run(expected)
            template.write_text(original);run()
            binding_path = scope / '10-workload-binding/workload-binding.yml'
            binding = yaml.safe_load(binding_path.read_text())
            for mutation in ('omitted-command', 'invalid-command', 'invalid-secrets', 'invalid-identity', 'invalid-capability'):
                with self.subTest(mutation=mutation):
                    value = copy.deepcopy(binding)
                    item = next(item for item in value['runtime_requirements'] if item['workload'] == 'persistence-migration-task')
                    if mutation == 'omitted-command': item.pop('command')
                    if mutation == 'invalid-command': item['command'] = 'artifacts/unrelated.main.js'
                    if mutation == 'invalid-secrets': item['secret_names'] = 'secret-name'
                    if mutation == 'invalid-identity': item['identity_required'] = 'false'
                    if mutation == 'invalid-capability': item['optional_capabilities'] = [None]
                    binding_path.write_text(yaml.safe_dump(value, sort_keys=False))
                    template.write_text(original.replace('Command: [artifacts/kanbien-core-server-persistence-migration.main.js]', 'Command: [artifacts/unrelated.main.js]'))
                    run('runtime-workload-command-required' if mutation in {'omitted-command','invalid-command'} else 'runtime-requirement-invalid')
            binding_path.write_text(yaml.safe_dump(binding, sort_keys=False)); template.write_text(original); run()
            route_path = scope / '00-declaration/acceptance-route-contract.yml'
            route_source = route_path.read_text()
            route = yaml.safe_load(route_source)
            argv = route['commands']['isolated-restore']['argv']
            argv[argv.index('--operation') + 1] = 'cleanup'
            route_path.write_text(yaml.safe_dump(route, sort_keys=False))
            run('acceptance-route-runtime-input-command-mismatch')
            route_path.write_text(route_source); run()

if __name__=='__main__':unittest.main(verbosity=2)

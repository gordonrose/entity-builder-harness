#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.support
#   version: 1
#   status: active
#   created_on: "2026-10-29"
#   updated_on: "2026-11-04"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Share disposable fixture utilities without inheritable test methods.
#   portability: {class: source-only, targets: []}
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


class FixtureSupport(unittest.TestCase):
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
        # A second workload carries a different dependency and only its own
        # required environment. It uses the same provider normalizer/checks.
        self.contract['configuration']['required_names'] = ['CATALOG_ENDPOINT']
        binding['runtime_requirements'] = [
            {'workload': item['id'], 'declaration_workload': 'core-server' if item['id'] == 'core-server-service' else 'private-release-verifier', 'required_names': ['CATALOG_ENDPOINT'],
             'command': ['artifacts/generic-server.main.js'], 'secret_names': [],
             'identity_required': False} for item in binding['workloads']]
        adapter_ref = binding['proposed_provider_binding']['configuration_adapter']
        (self.root / adapter_ref).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / adapter_ref, self.root / adapter_ref)
        runtime_helper = 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py'
        (self.root / runtime_helper).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / runtime_helper, self.root / runtime_helper)
        write(binding_path, binding)
        write(self.target / 'scope-index.yml', {'schema': 'deploy/scope-lifecycle-inventory/v1', 'target': 'synthetic', 'scopes': [{'id': 'synthetic-worker', 'lifecycle': 'active', 'declaration': 'synthetic-worker/00-declaration/declaration-contract.yml', 'workload_binding': 'synthetic-worker/10-workload-binding/workload-binding.yml', 'workload_ownership': [item['id'] for item in binding['workloads']]}], 'legacy_exceptions': []})
        for path in ('src/main.ts', 'consumer.ts', 'program.yml', 'image.yml', 'infra/04.deploy/03.product/targets/synthetic/30-provider-realization/fixture.yml'):
            file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_text('fixture\n')
        resources = {}
        for item in binding['workloads']:
            resources[item['provider_reference']] = {'Type': 'AWS::ECS::TaskDefinition', 'Properties': {
                'ContainerDefinitions': [{'Name': 'catalog-worker', 'Command': ['artifacts/generic-server.main.js'],
                    'Environment': [{'Name': 'CATALOG_ENDPOINT', 'Value': 'http://catalog.invalid'}]}]}}
        write(self.root / 'infra/04.deploy/03.product/targets/synthetic/30-provider-realization/fixture.yml', {'Resources': resources})
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
        self.catalog['checks']['local'].update(scope_inputs=False, inputs=['src', 'program.yml', 'image.yml'])
        self.catalog['checks']['runnable-program'].update(scope_inputs=False, inputs=['program.yml'])
        self.catalog_path = self.root / 'scripts/repo/check-selection/checks.yml'
        self.save()


    def check_script(self, name: str, effects: list[str], body: str) -> None:
        path = self.root / ('scripts/' + name + '.sh'); path.parent.mkdir(exist_ok=True)
        path.write_text('#!/bin/bash\n# agentic-artifact:\n#   schema: agentic-artifact/v3\n#   id: fixture.' + name + '\n#   effects: ' + json.dumps(effects) + '\n' + body)
        path.chmod(0o755)


    def save(self) -> None:
        write(self.contract_path, self.contract); write(self.catalog_path, self.catalog)


    def run_plan(self, *, paths=None, checks=None, task_paths=None, all_inputs=False, stage='local', boundary='integration', execute=False, evidence=None, staged=False, record_preparation=False, require_preparation=False, reuse_from_worktree=None):
        args = argparse.Namespace(root=self.root, catalog=self.catalog_path, paths=paths or ['src/main.ts'], staged=staged, all=False, stage=stage, execute_local=execute, record_preparation=record_preparation, require_preparation=require_preparation, evidence=evidence, json=True)
        args.checks = checks
        args.task_paths = task_paths
        if all_inputs: args.all, args.paths = True, []
        if checks is not None: args.paths = []
        args.boundary = boundary
        args.reuse_from_worktree = reuse_from_worktree
        files = [path.relative_to(self.root).as_posix() for path in self.root.rglob('*') if path.is_file() and '.git' not in path.relative_to(self.root).parts]
        def git(_root, *arguments):
            if arguments[0] == 'diff': return 'src/old.ts\0src/main.ts\0' if '--cached' in arguments else ''
            if arguments[0] == 'ls-files': return ''
            return getattr(self, 'revision', 'a' * 40)
        with patch.object(selection, 'repository_paths', return_value=files), patch.object(selection, 'git', side_effect=git): return selection.plan(args)


    def codes(self, report): return {item['code'] for item in report['findings']}


    def focused_fixture(self, body='echo focus >> counts\n'):
        self.check_script('focus', ['read-only', 'writes-files'], body)
        self.catalog['checks']['focus'] = copy.deepcopy(self.catalog['checks']['local'])
        self.catalog['checks']['focus'].pop('focused_prerequisites', None)
        self.catalog['checks']['focus']['argv'] = ['bash', 'scripts/focus.sh']
        self.catalog['checks']['focus']['inputs'] = ['scripts/focus.sh']
        self.catalog['checks']['focus']['scope_inputs'] = False
        self.catalog['checks']['local']['focused_prerequisites'] = [{'inputs': ['src'], 'checks': ['focus']}]
        self.save()
        prepared = self.run_plan(paths=['src/main.ts'], record_preparation=True)
        self.assertFalse(prepared['findings'], prepared['findings'])


    def prepare_selector_cli(self):
        # Real selector/cache/inventory processes in a disposable Git root; only
        # HEAD and the staged path list are fixture identities, with no commits.
        for relative in ('scripts/repo/check-selection/script.sh', 'scripts/repo/check-selection/script.py', 'scripts/repo/check-selection/local_cache.py', 'scripts/04.deploy/inventory-deploy-control/delivery_inventory.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py', 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py', 'scripts/01.harness/artifact-metadata/header_discovery.py'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        shim = self.root / '.selector-test-bin'
        shim.mkdir()
        (shim / 'git').write_text('#!/bin/bash\ncase "$*" in *"rev-parse HEAD"*) printf "' + 'a' * 40 + '\\n";; *"diff --cached --name-only --no-renames -z"*) printf "src/main.ts\\0";; *) exec "' + shutil.which('git') + '" "$@";; esac\n')
        (shim / 'git').chmod(0o755)
        self.cli_environment = {**os.environ, 'PATH': str(shim) + ':' + os.environ['PATH']}


    def run_selector_cli(self, *, expected=0, staged=False):
        argv = ['bash', 'scripts/repo/check-selection/script.sh', '--execute-local', '--json']
        argv += ['--staged'] if staged else ['--paths', 'src/main.ts']
        result = subprocess.run(argv, cwd=self.root, env=self.cli_environment, capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)


    def local_command_result(self, report):
        return next(item for item in report['checks'] if item['argv'][1] == 'scripts/local.sh')


    def node_package(self, name, *, dependencies=None, optional=None, path=None):
        package = path or self.root / 'node_modules' / name
        package.mkdir(parents=True, exist_ok=True)
        (package / 'package.json').write_text(json.dumps({'name': name, 'version': '1.0.0', 'dependencies': dependencies or {}, 'optionalDependencies': optional or {}}))
        (package / 'index.js').write_text('module.exports = {};\n')
        return package


    def node_check(self, packages):
        self.catalog['checks']['local']['runtime'].update(tools=['bash', 'python3', 'node'], node_packages=packages)
        self.save()

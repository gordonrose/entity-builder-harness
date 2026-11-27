#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runtime-configuration
#   version: 5
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-27"
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
import contextlib
from dataclasses import FrozenInstanceError, replace
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[5]
COMMAND = ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py'

def copy_repository(root):
    subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
    shutil.copyfile(ROOT / 'package.json', root / 'package.json')
    # Real producers and adapters; mutations cannot touch accepted evidence.
    for path in ['.github', 'infra', 'scripts', '.agentic', 'packages', 'platform', 'products']:
        shutil.copytree(ROOT / path, root / path, ignore=shutil.ignore_patterns('__pycache__', 'node_modules', '.cache'))



class PostgreSqlVersionTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'scripts/04.deploy/shared/postgresql-version.py'
        spec = importlib.util.spec_from_file_location('postgresql_version_test', path)
        self.pg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.pg)

    def test_exact_qualification_is_separate_from_compatibility(self):
        for major, minor in [(18, 3), (18, 4), (17, 11)]:
            version = f'{major}.{minor}'
            policy = self.pg.configuration({'postgresql': {'compatible_major': major, 'qualification_image': f'postgres:{version}-bookworm'}})
            self.assertEqual(policy['qualification_version'], version)
            self.assertEqual(policy['server_version_num'], str(major * 10000 + minor))
            self.assertEqual(policy['data_directory'], f'/var/lib/postgresql/{major}/docker' if major >= 18 else '/var/lib/postgresql/data')
        for observed in ['18.0', '18.3', '18.4', '18.12', '18.4-rds.20261116']:
            self.assertEqual(self.pg.compatible(observed, 18), observed)
        for observed in ['16.9', '17.11', '19.0']:
            with self.assertRaisesRegex(self.pg.VersionFailure, 'major-incompatible'):
                self.pg.compatible(observed, 18)

    def test_malformed_observations_and_declarations_fail_safely(self):
        for observed in [None, True, 18.3, {}, '', '18', '180.3', '18.03', '018.3', '18.3x', '18.3.1', '18.3\\n', '18.3-rds.bad', 'private-version-canary']:
            with self.assertRaisesRegex(self.pg.VersionFailure, '^postgresql-version-observation-invalid$'):
                self.pg.compatible(observed, 18)
        for major in [True, '18', 9, 100, None]:
            with self.assertRaisesRegex(self.pg.VersionFailure, 'major-invalid'):
                self.pg.compatible('18.3', major)
        for value in [None, {}, {'postgresql': []}, {'postgresql': {'compatible_major': 18}}]:
            with self.assertRaisesRegex(self.pg.VersionFailure, 'declaration-invalid'):
                self.pg.configuration(value)
        for image in ['postgres:18-bookworm', 'private.invalid/postgres:18.3-bookworm', 'postgres:18.3-alpine', 'postgres:18.3-bookworm;bad']:
            with self.assertRaisesRegex(self.pg.VersionFailure, 'qualification-image-invalid'):
                self.pg.configuration({'postgresql': {'compatible_major': 18, 'qualification_image': image}})
        with self.assertRaisesRegex(self.pg.VersionFailure, 'major-incompatible'):
            self.pg.configuration({'postgresql': {'compatible_major': 18, 'qualification_image': 'postgres:17.11-bookworm'}})

    def test_duplicate_contract_keys_are_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'contract.yml'
            path.write_text('postgresql: {}\npostgresql: {compatible_major: 18, qualification_image: "postgres:18.3-bookworm"}\n')
            with self.assertRaisesRegex(self.pg.VersionFailure, '^postgresql-version-source-invalid$'):
                self.pg.read(path)

    def test_cli_does_not_disclose_arguments_or_source(self):
        command = ['python3', '-B', str(ROOT / 'scripts/04.deploy/shared/postgresql-version.py')]
        result = subprocess.run([*command, '--private-version-canary'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)['code'], 'postgresql-version-arguments-invalid')
        self.assertNotIn('private-version-canary', result.stdout + result.stderr)
        result = subprocess.run([*command, '--contract', '/missing/private-version-canary'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['code'], 'postgresql-version-source-invalid')
        self.assertNotIn('private-version-canary', result.stdout + result.stderr)

class PreparationInputTests(unittest.TestCase):
    target = 'kanbien-core-platform'
    base = 'infra/04.deploy/03.product/targets/' + target
    owner_path = 'scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py'
    session_path = 'scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/session-binding/implementation.py'
    profile_path = base + '/00-target/target-profile.yml'
    prerequisite_path = base + '/30-provider-realization/aws/cloudformation/private-network.yml'
    callers = {
        'core-server-persistence': 'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py',
        'entity-smoke': 'scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py',
    }

    @staticmethod
    def imported(path):
        spec = importlib.util.spec_from_file_location('preparation_fixture_' + path.parent.name, path)
        result = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(result)
        return result

    def setUp(self):
        self.owner = self.imported(ROOT / self.owner_path)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        paths = {self.owner_path, self.session_path, self.prerequisite_path, *self.callers.values(),
                 'scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py',
                 *('scripts/04.deploy/shared/provider-adapters/aws/' + name for name in ('cloudformation-template.py', 'cli.py', 'response.py', 'ecr-scan.py', 'foundation-checks.py', 'change_sets.py'))}
        for scope in self.callers:
            paths.update(self.owner.load(ROOT, self.target, scope)['references'])
        for name in paths:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def edit(self, name, change):
        path = self.root / name
        value = self.owner.CF.template(path.read_text())
        change(value)
        path.write_text(yaml.safe_dump(value, sort_keys=False))

    def resolve(self, scope='entity-smoke'):
        return self.owner.load(self.root, self.target, scope)

    def session_document(self, scope='entity-smoke', identity='a' * 32):
        return {'schema': 'deploy/environment-session-intent/v1', 'target': self.target, 'scope': scope,
                'session_id': identity, 'starts_at': 1000, 'expires_at': 8200,
                'environment_lifecycle': {'mode': 'temporary', 'data_retention': 'discard', 'max_duration_seconds': 7200}}

    def session_plan(self, document=None, scope='entity-smoke', now=1000, maximum=7200):
        return self.owner.load_session_plan(self.root, self.target, scope,
                                          self.session_document(scope) if document is None else document, now, maximum)

    def test_session_source_plan_uses_shared_projection_and_preserves_package_target(self):
        for scope in self.callers:
            ordinary = self.resolve(scope)
            before = {name: (self.root / name).read_bytes() for name in ordinary['references']}
            with patch.object(self.owner.CF, 'project_parameters', wraps=self.owner.CF.project_parameters) as project:
                first = self.session_plan(scope=scope)
            second = self.session_plan(self.session_document(scope, 'b' * 32), scope)
            self.assertEqual(first['execution_status'], 'not-admitted')
            self.assertEqual(first['source_configuration'], ordinary)
            self.assertEqual(first['source_configuration']['target'], self.target)
            self.assertEqual(first['binding'].intent.lifecycle.mode, 'temporary')
            self.assertEqual(first['binding'].intent.lifecycle.data_retention, 'discard')
            self.assertIn(self.session_path, first['references'])
            self.assertEqual(first['resource_name_prefix'], 's-' + 'a' * 19)
            self.assertEqual(first['binding'].source_inputs, second['binding'].source_inputs)
            self.assertTrue(set(dict(first['stack_names']).values()).isdisjoint(dict(second['stack_names']).values()))
            self.assertEqual(first['binding'].scopes, ('core-server-persistence', 'entity-smoke') if scope == 'entity-smoke' else ('core-server-persistence',))
            stacks = dict(first['stack_names'])
            expected_pairings = ((stacks['foundation'], ordinary['foundation_template']),
                                 (stacks['private-network'], self.prerequisite_path),
                                 *((stacks[name], self.resolve(name)['template']) for name in first['binding'].scopes))
            self.assertEqual(first['stack_templates'], expected_pairings)
            self.assertEqual(tuple(stack for stack, _ in first['stack_templates']), tuple(stacks.values()))
            self.assertEqual({reference for _, reference in first['stack_templates']}, set(dict(first['projected_templates'])))
            self.assertEqual(tuple(reference for _, reference in first['stack_templates']),
                             tuple(reference for _, reference in second['stack_templates']))
            for _, reference in first['stack_templates']:
                self.assertIn(reference, dict(first['binding'].source_inputs))
            with self.assertRaises(TypeError): first['stack_templates'][0] = ('different', 'different')
            with self.assertRaises(TypeError): first['stack_templates'][0][1] = 'different'
            expected_calls = len(first['projected_templates']) + len(first['activation_templates'])
            self.assertEqual(sum(len(call.args) == 3 and call.args[2]['ResourceNamePrefix'] == first['resource_name_prefix'] for call in project.call_args_list), expected_calls)
            for reference, rendered in first['projected_templates']:
                projected = json.loads(rendered)
                # Declaration defaults and shared publication retain source custody.
                original = self.owner.CF.template((self.root / reference).read_text())
                self.assertEqual(projected['Parameters']['ResourceNamePrefix'], original['Parameters']['ResourceNamePrefix'])
                self.assertIn(first['resource_name_prefix'], rendered)
                self.assertIn(reference, dict(first['binding'].source_inputs))
            self.assertEqual(before, {name: (self.root / name).read_bytes() for name in before})
            self.assertEqual(self.resolve(scope), ordinary)

    def test_session_dependency_order_and_activation_are_captured_for_both_plans(self):
        for scope in self.callers:
            with self.subTest(scope=scope):
                plan = self.session_plan(scope=scope)
                stacks = dict(plan['stack_names'])
                expected = ((stacks['foundation'], (stacks['private-network'],)), (stacks['private-network'], ()),
                            (stacks['core-server-persistence'], (stacks['foundation'],)))
                if scope == 'entity-smoke':
                    expected += ((stacks['entity-smoke'], (stacks['foundation'], stacks['core-server-persistence'])),)
                self.assertEqual(plan['stack_dependencies'], expected)
                self.assertEqual(plan['stack_order'], (stacks['private-network'], stacks['foundation'], *(stack for stack, _ in expected[2:])))
                for stack, dependencies in plan['stack_dependencies']:
                    self.assertTrue(all(plan['stack_order'].index(dependency) < plan['stack_order'].index(stack) for dependency in dependencies))
                for key in ('stack_dependencies', 'stack_order', 'activation_templates', 'activation_parameters'):
                    self.assertIsInstance(plan[key], tuple)
                    with self.assertRaises(TypeError): plan[key][0] = 'changed'
                with self.assertRaises(TypeError): plan['stack_dependencies'][0][1][0] = 'changed'
                with self.assertRaises(TypeError): plan['activation_parameters'][0][1][0][1] = 'changed'

                creation = dict(plan['projected_templates'])
                active = dict(plan['activation_templates'])
                active_parameters = dict(plan['activation_parameters'])
                self.assertEqual(set(active), set(creation) - {plan['source_configuration']['foundation_template'], self.prerequisite_path})
                self.assertEqual(set(active_parameters), set(active))
                for reference, rendered in active.items():
                    original = self.owner.CF.template((self.root / reference).read_text())
                    expected_template = json.loads(creation[reference])
                    expected_parameters = dict(dict(plan['creation_parameters'])[reference])
                    for parameter, row in original['Metadata']['CreationControls'].items():
                        if row['kind'] != 'desired-count': continue
                        expected_parameters[parameter] = str(row['active'])
                        for resource in row['resources']:
                            self.assertEqual(expected_template['Resources'][resource]['Properties']['DesiredCount'], 0)
                            expected_template['Resources'][resource]['Properties']['DesiredCount'] = row['active']
                    self.assertEqual(json.loads(rendered), expected_template)
                    self.assertEqual(dict(active_parameters[reference]), expected_parameters)
                    self.assertEqual(json.loads(rendered)['Parameters'], original['Parameters'])
                    self.assertIn(reference, dict(plan['binding'].source_inputs))
                entity = self.owner.CF.template((self.root / self.base / '30-provider-realization/aws/cloudformation/entity-smoke.yml').read_text())
                self.assertEqual(entity['Parameters']['ServerDesiredCount'], {'Type': 'Number', 'Default': 0, 'AllowedValues': [0, 1]})
                self.assertEqual(entity['Resources']['FeatureService']['Properties']['DesiredCount'], {'Ref': 'ServerDesiredCount'})
                self.assertEqual(self.resolve('entity-smoke')['creation_parameters'], {'ServerDesiredCount': '0'})

    def test_session_dependency_order_follows_edges_not_scope_or_stack_names(self):
        replacements = {'entity-smoke': 'aaa-frontend', 'core-server-persistence': 'zzz-database'}
        for name, replacement in replacements.items():
            reference = self.base + '/20-scopes/' + name + '/10-workload-binding/workload-binding.yml'
            def change(binding):
                binding['scope'] = replacement
                binding['proposed_provider_binding']['stack'] = self.target + '-' + replacement
                for dependency in binding['proposed_provider_binding']['dependencies'].values():
                    dependency['scope'] = replacements[dependency['scope']]
                if name == 'entity-smoke':
                    binding['proposed_provider_binding']['dependencies']['same-database'] = dict(binding['proposed_provider_binding']['dependencies']['database'])
            self.edit(reference, change)
            folder = self.root / self.base / '20-scopes' / name
            folder.rename(folder.with_name(replacement))
        self.edit(self.base + '/40-package-custody/github-actions/pipeline-index.yml',
                  lambda document: [row.update(used_by_scopes=[replacements.get(name, name) for name in row['used_by_scopes']]) for row in document['pipelines']])
        plan = self.session_plan(scope='aaa-frontend')
        stacks = dict(plan['stack_names'])
        self.assertEqual(tuple(stacks), ('foundation', 'private-network', 'aaa-frontend', 'zzz-database'))
        self.assertEqual(plan['stack_order'], (stacks['private-network'], stacks['foundation'], stacks['zzz-database'], stacks['aaa-frontend']))
        self.assertEqual(dict(plan['stack_dependencies']), {
            stacks['foundation']: (stacks['private-network'],), stacks['private-network']: (), stacks['zzz-database']: (stacks['foundation'],),
            stacks['aaa-frontend']: (stacks['foundation'], stacks['zzz-database'])})
        self.assertEqual(plan['binding'].scopes, ('aaa-frontend', 'zzz-database'))
        reference = self.base + '/20-scopes/aaa-frontend/10-workload-binding/workload-binding.yml'
        self.edit(reference, lambda value: value['proposed_provider_binding']['dependencies']['database'].update(scope='missing'))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-source-unavailable$'):
            self.session_plan(scope='aaa-frontend')

    def test_foundation_prerequisites_capture_exact_outputs_without_execution_inputs(self):
        for scope in self.callers:
            ordinary = self.resolve(scope)
            plan = self.session_plan(scope=scope)
            stacks = dict(plan['stack_names'])
            self.assertEqual(plan['prerequisite_components'], ('private-network',))
            self.assertEqual(plan['stack_parameter_sources'], tuple(sorted(
                (stacks['foundation'], name, stacks['private-network'], name)
                for name in ('VpcId', 'VpcCidr', 'PrivateSubnetIds'))))
            for key in ('prerequisite_components', 'stack_parameter_sources'):
                self.assertIsInstance(plan[key], tuple)
                with self.assertRaises(TypeError): plan[key][0] = 'changed'
            with self.assertRaises(TypeError): plan['stack_parameter_sources'][0][1] = 'changed'
            for key in ('projected_templates', 'creation_parameters', 'discard_templates', 'discard_parameters'):
                self.assertIn(self.prerequisite_path, dict(plan[key]))
            for key in ('activation_templates', 'activation_parameters'):
                self.assertNotIn(self.prerequisite_path, dict(plan[key]))
            network = json.loads(dict(plan['projected_templates'])[self.prerequisite_path])
            original = self.owner.CF.template((self.root / self.prerequisite_path).read_text())
            self.assertEqual(network['Parameters'], original['Parameters'])
            self.assertTrue(all('Default' not in row for row in network['Parameters'].values()))
            self.assertEqual(set(network['Parameters']) - {'ResourceNamePrefix'},
                             {'VpcCidr', 'PrivateSubnetOneCidr', 'PrivateSubnetTwoCidr', 'AvailabilityZoneOne', 'AvailabilityZoneTwo'})
            self.assertEqual(dict(dict(plan['creation_parameters'])[self.prerequisite_path]), {'ResourceNamePrefix': plan['resource_name_prefix']})
            self.assertEqual(dict(plan['projected_templates'])[self.prerequisite_path], dict(plan['discard_templates'])[self.prerequisite_path])
            self.assertIn(self.prerequisite_path, plan['references'])
            self.assertIn(self.prerequisite_path, dict(plan['binding'].source_inputs))
            self.assertNotIn(self.prerequisite_path, ordinary['references'])
            self.assertEqual(plan['source_configuration'], ordinary)
            self.assertEqual(self.resolve(scope), ordinary)

    def test_foundation_prerequisites_follow_renamed_components_outputs_and_multiple_suppliers(self):
        before = self.session_plan()
        renamed_path = self.prerequisite_path.replace('private-network.yml', 'independent-component.yml')
        second_path = self.prerequisite_path.replace('private-network.yml', 'another-component.yml')
        (self.root / self.prerequisite_path).rename(self.root / renamed_path)
        self.edit(renamed_path, lambda d: d.update(Outputs={name + 'Result': row for name, row in d['Outputs'].items()}))
        shutil.copyfile(self.root / renamed_path, self.root / second_path)
        def declaration(profile):
            original = profile['provider']['foundation']['instance_prerequisites'].pop('private-network')
            original.update(stack=self.target + '-independent', template=renamed_path.removeprefix(self.base + '/'),
                            foundation_parameters={'VpcId': 'VpcIdResult', 'PrivateSubnetIds': 'PrivateSubnetIdsResult'})
            profile['provider']['foundation']['instance_prerequisites'].update({
                'zzz-supplier': original,
                'aaa-supplier': {'stack': self.target + '-another', 'template': second_path.removeprefix(self.base + '/'),
                                 'foundation_parameters': {'VpcCidr': 'VpcCidrResult'}}})
        self.edit(self.profile_path, declaration)
        plan = self.session_plan()
        stacks = dict(plan['stack_names'])
        self.assertEqual(plan['prerequisite_components'], ('aaa-supplier', 'zzz-supplier'))
        self.assertEqual(tuple(stacks), ('foundation', 'aaa-supplier', 'zzz-supplier', *plan['binding'].scopes))
        self.assertEqual(plan['stack_order'], (stacks['aaa-supplier'], stacks['zzz-supplier'], stacks['foundation'],
                                             stacks['core-server-persistence'], stacks['entity-smoke']))
        self.assertEqual(dict(plan['stack_dependencies'])[stacks['foundation']], (stacks['aaa-supplier'], stacks['zzz-supplier']))
        self.assertEqual(plan['stack_parameter_sources'], tuple(sorted((stacks['foundation'], parameter, stacks[component], output)
                         for parameter, component, output in (('VpcCidr', 'aaa-supplier', 'VpcCidrResult'),
                                                              ('VpcId', 'zzz-supplier', 'VpcIdResult'),
                                                              ('PrivateSubnetIds', 'zzz-supplier', 'PrivateSubnetIdsResult')))))
        self.assertEqual(plan['binding'].scopes, before['binding'].scopes)
        self.assertNotEqual(plan['binding'].source_inputs_sha256, before['binding'].source_inputs_sha256)
        inputs = dict(plan['binding'].source_inputs)
        self.assertNotIn(self.prerequisite_path, inputs)
        for reference in (self.profile_path, renamed_path, second_path):
            self.assertEqual(inputs[reference], hashlib.sha256((self.root / reference).read_bytes()).hexdigest())
        self.assertEqual({key: value for key, value in inputs.items() if key not in {self.profile_path, renamed_path, second_path}},
                         {key: value for key, value in before['binding'].source_inputs if key not in {self.profile_path, self.prerequisite_path}})

    def test_absent_foundation_prerequisites_preserve_legacy_shape_and_persistent_selection(self):
        ordinary = {scope: self.resolve(scope) for scope in self.callers}
        self.edit(self.profile_path, lambda d: d['provider']['foundation'].pop('instance_prerequisites'))
        for scope in self.callers:
            plan = self.session_plan(scope=scope)
            stacks = dict(plan['stack_names'])
            self.assertEqual(plan['prerequisite_components'], ())
            self.assertEqual(plan['stack_parameter_sources'], ())
            self.assertEqual(tuple(stacks), ('foundation', *plan['binding'].scopes))
            self.assertEqual(dict(plan['stack_dependencies'])[stacks['foundation']], ())
            self.assertEqual(plan['stack_order'], tuple(stacks.values()))
            self.assertNotIn(self.prerequisite_path, plan['references'])
            self.assertNotIn(self.prerequisite_path, dict(plan['binding'].source_inputs))
            self.assertEqual({reference for _, reference in plan['stack_templates']}, set(dict(plan['projected_templates'])))
            self.assertEqual(plan['source_configuration'], ordinary[scope])
        absent = self.session_plan()
        self.edit(self.profile_path, lambda d: d['provider']['foundation'].update(instance_prerequisites={}))
        empty = self.session_plan()
        self.assertEqual({key: value for key, value in absent.items() if key != 'binding'},
                         {key: value for key, value in empty.items() if key != 'binding'})
        self.edit(self.profile_path, lambda d: d['provider']['foundation'].update(instance_prerequisites='private-canary'))
        (self.root / self.prerequisite_path).unlink()
        for scope in self.callers:
            self.assertEqual(self.resolve(scope), ordinary[scope])

    def test_foundation_prerequisite_declaration_rejections_are_closed_and_finite(self):
        path = self.root / self.profile_path
        original = path.read_bytes()
        cases = [(lambda f, value=value: f.update(instance_prerequisites=value), 'session-prerequisite-invalid')
                 for value in (None, [], 'private-canary')]
        rows = [(lambda r: r.update(extra='private-canary'), 'session-prerequisite-invalid'),
                (lambda r: r.pop('stack'), 'session-prerequisite-invalid'),
                (lambda r: r.pop('template'), 'session-prerequisite-invalid'),
                (lambda r: r.pop('foundation_parameters'), 'session-prerequisite-invalid'),
                (lambda r: r.update(stack='private-canary/'), 'session-prerequisite-invalid'),
                (lambda r: r.update(stack='unrelated-stack'), 'session-stack-source-unsupported'),
                (lambda r: r.update(stack=self.target + '-foundation'), 'session-stack-identity-ambiguous'),
                (lambda r: r.update(stack=self.target + '-entity-smoke'), 'session-stack-identity-ambiguous'),
                (lambda r: r.update(template='missing-private-canary.yml'), 'source-unavailable')]
        rows += [(lambda r, value=value: r.update(template=value), 'path-invalid')
                 for value in (None, 1, '/private-canary.yml', '../private-canary.yml', './private-canary.yml',
                               'nested/../private-canary.yml', 'nested//private-canary.yml', 'nested/private-canary.yml/', 'private\\canary.yml')]
        rows += [(lambda r, value=value: r.update(foundation_parameters=value), 'session-prerequisite-binding-invalid')
                 for value in (None, [], {}, 'private-canary', {'MissingParameter': 'VpcId'}, {'VpcId': 'MissingOutput'},
                               {'ResourceNamePrefix': 'VpcId'}, {'EnableDeliveryRole': 'VpcId'}, {'VpcId': None}, {'VpcId': []})]
        rows += [(lambda r: r.update(template='30-provider-realization/aws/cloudformation/foundation.yml', foundation_parameters={'VpcId': 'VpcId'}),
                  'session-template-identity-ambiguous')]
        cases += [(lambda f, change=change: change(f['instance_prerequisites']['private-network']), reason) for change, reason in rows]
        cases += [(lambda f, name=name: f['instance_prerequisites'].update({name: f['instance_prerequisites'].pop('private-network')}), reason)
                  for name, reason in (('foundation', 'session-prerequisite-identity-ambiguous'), ('entity-smoke', 'session-prerequisite-identity-ambiguous'),
                                       ('core-server-persistence', 'session-prerequisite-identity-ambiguous'), ('private-canary/', 'session-prerequisite-invalid'))]
        cases += [(lambda f: f['instance_prerequisites'].update({'other': copy.deepcopy(f['instance_prerequisites']['private-network'])}),
                   'session-prerequisite-destination-ambiguous'),
                  (lambda f: f['instance_prerequisites'].update({'private-network': None}), 'session-prerequisite-invalid')]
        for index, (change, reason) in enumerate(cases):
            try:
                self.edit(self.profile_path, lambda d: change(d['provider']['foundation']))
                with self.subTest(case=index, reason=reason), patch('subprocess.run', side_effect=AssertionError('child-started')), \
                        patch('subprocess.Popen', side_effect=AssertionError('child-started')):
                    with self.assertRaises(self.owner.InputFailure) as failure: self.session_plan()
                    self.assertEqual(failure.exception.code, 'preparation-inputs-' + reason)
                    self.assertNotIn('private-canary', str(failure.exception))
            finally: path.write_bytes(original)

    def test_foundation_prerequisites_reject_duplicate_template_identities_without_duplicate_destinations(self):
        path = self.root / self.profile_path
        original = path.read_bytes()
        def duplicate_components(profile):
            rows = profile['provider']['foundation']['instance_prerequisites']
            rows['private-network']['foundation_parameters'] = {'VpcId': 'VpcId'}
            rows['other-supplier'] = {**rows['private-network'], 'stack': self.target + '-other-supplier',
                                      'foundation_parameters': {'VpcCidr': 'VpcCidr'}}
        def alias_foundation(profile):
            foundation = profile['provider']['foundation']
            foundation['instance_prerequisites']['private-network'].update(
                template=foundation['template'], foundation_parameters={'VpcId': 'VpcId'})
            foundation['template'] = foundation['template'].replace('/cloudformation/', '/cloudformation/./')
        for change in (duplicate_components, alias_foundation):
            try:
                self.edit(self.profile_path, change)
                with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-template-identity-ambiguous$'):
                    self.session_plan()
            finally: path.write_bytes(original)

    def test_foundation_prerequisites_reject_missing_outputs_and_reserved_count_destinations(self):
        path = self.root / self.prerequisite_path
        original = path.read_bytes()
        for change in (lambda d: d['Outputs'].pop('VpcId'), lambda d: d['Outputs']['VpcId'].pop('Value'),
                       lambda d: d['Outputs']['VpcId'].update(Value=None)):
            try:
                self.edit(self.prerequisite_path, change)
                with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-prerequisite-binding-invalid$'):
                    self.session_plan()
            finally: path.write_bytes(original)
        def conditional(document):
            document['Parameters']['IncludeSecret'] = {'Type': 'String', 'Default': 'true', 'AllowedValues': ['true', 'false']}
            document['Conditions'] = {'IncludeSecretCondition': {'Fn::Equals': [{'Ref': 'IncludeSecret'}, 'true']}}
            document['Resources']['OptionalSecret'] = {'Type': 'AWS::SecretsManager::Secret', 'Condition': 'IncludeSecretCondition'}
            document['Outputs']['VpcId']['Condition'] = 'IncludeSecretCondition'
            document['Metadata']['CreationControls']['IncludeSecret'] = {
                'kind': 'optional-resources', 'temporary': 'false', 'resources': ['OptionalSecret'],
                'condition': 'IncludeSecretCondition', 'outputs': ['VpcId']}
        self.edit(self.prerequisite_path, conditional)
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-prerequisite-binding-invalid$'):
            self.session_plan()
        path.write_bytes(original)
        def count(document):
            document['Parameters']['InstanceCount'] = {'Type': 'Number', 'Default': 1, 'AllowedValues': [0, 1]}
            document['Resources']['CountedService'] = {'Type': 'AWS::ECS::Service', 'Properties': {'DesiredCount': {'Ref': 'InstanceCount'}}}
            document['Metadata']['CreationControls']['InstanceCount'] = {
                'kind': 'desired-count', 'temporary': 0, 'active': 1, 'resources': ['CountedService']}
        self.edit(self.base + '/30-provider-realization/aws/cloudformation/foundation.yml', count)
        self.edit(self.profile_path, lambda d: d['provider']['foundation']['instance_prerequisites']['private-network']['foundation_parameters'].update(InstanceCount='VpcId'))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-prerequisite-binding-invalid$'):
            self.session_plan()

    def test_foundation_prerequisite_source_paths_and_freshness_fail_closed(self):
        path = self.root / self.prerequisite_path
        original = Path.read_bytes
        captured = []
        def read(selected):
            raw = original(selected)
            if selected == path and not captured:
                captured.append(True)
                path.write_bytes(raw + b'\n# changed after capture\n')
            return raw
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-source-changed$'):
                self.session_plan()
        moved = path.with_name('unselected-component.yml')
        path.rename(moved)
        path.symlink_to(moved)
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-path-invalid$'):
            self.session_plan()

    def test_session_binding_is_immutable_and_hashes_the_parsed_source_bytes(self):
        document = self.session_document()
        calls = {}
        original = Path.read_bytes
        def read(path):
            if path.is_relative_to(self.root): calls[path.relative_to(self.root).as_posix()] = calls.get(path.relative_to(self.root).as_posix(), 0) + 1
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            result = self.session_plan(document)
        binding = result['binding']
        self.assertEqual({calls[path] for path, _ in binding.source_inputs}, {2})  # One capture, one final freshness observation.
        for path, digest in binding.source_inputs:
            self.assertEqual(digest, hashlib.sha256((self.root / path).read_bytes()).hexdigest())
        self.assertEqual(binding.source_inputs_sha256, hashlib.sha256(json.dumps(binding.source_inputs, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest())
        document['environment_lifecycle']['mode'] = 'persistent'
        document['session_id'] = 'b' * 32
        self.assertEqual(binding.intent.session_id, 'a' * 32)
        self.assertEqual(binding.intent.lifecycle.mode, 'temporary')
        for obj, key, value in ((binding, 'scopes', ()), (binding.intent, 'expires_at', 9000), (binding.intent.lifecycle, 'mode', 'persistent')):
            with self.assertRaises(FrozenInstanceError): setattr(obj, key, value)
        with self.assertRaises(TypeError): binding.source_inputs[0][0] = 'changed'
        with self.assertRaises(TypeError): binding.scopes[0] = 'changed'

    def test_session_creation_controls_are_quiet_and_preserve_database_protection(self):
        plan = self.session_plan()
        controls = dict(plan['creation_parameters'])
        for reference, rendered in plan['projected_templates']:
            temporary = json.loads(rendered)
            original = self.owner.CF.template((self.root / reference).read_text())
            production = self.owner.target_template(original, self.target) if 'Default' in original['Parameters']['ResourceNamePrefix'] else None
            selected = dict(controls[reference])
            if reference.endswith('/foundation.yml'):
                self.assertEqual(selected['EnableDeliveryRole'], 'false')
                self.assertNotIn('DeliveryRole', temporary['Resources'])
                self.assertIn('DeliveryRole', production['Resources'])
                self.assertFalse(any(row['Type'] in ('AWS::ECR::Repository', 'AWS::IAM::OIDCProvider') for row in temporary['Resources'].values()))
            if reference.endswith('/core-server-persistence.yml'):
                self.assertEqual({key: value for key, value in selected.items() if key != 'ResourceNamePrefix'},
                                 {'ServerDesiredCount': '0', 'ObservabilityCollectorDesiredCount': '0', 'IncludeLegacyPasswordSecrets': 'false'})
                for name in ('CoreServerPersistenceService', 'ObservabilityCollectorService'):
                    self.assertEqual(temporary['Resources'][name]['Properties']['DesiredCount'], 0)
                    self.assertIs(type(temporary['Resources'][name]['Properties']['DesiredCount']), int)
                    self.assertEqual(production['Resources'][name]['Properties']['DesiredCount'], 1)
                for name in ('RuntimeCredentialsSecret', 'OrdinaryMigrationCredentialsSecret'):
                    self.assertNotIn(name, temporary['Resources'])
                    self.assertNotIn(name + 'Arn', temporary['Outputs'])
                    self.assertIn(name, production['Resources'])
                database = temporary['Resources']['PersistenceDatabase']
                self.assertIs(database['Properties']['DeletionProtection'], True)
                self.assertEqual(database['DeletionPolicy'], 'Snapshot')
                self.assertEqual(database['UpdateReplacePolicy'], 'Snapshot')
                administrator = temporary['Outputs']['AdministratorCredentialsSecretArn']['Value']['Ref']
                self.assertIn(administrator, temporary['Resources'])
                self.assertEqual(temporary['Resources'][administrator]['Type'], 'AWS::SecretsManager::Secret')
        self.assertEqual(self.resolve('core-server-persistence')['creation_parameters'],
                         {'ServerDesiredCount': '1', 'ObservabilityCollectorDesiredCount': '1', 'IncludeLegacyPasswordSecrets': 'true'})

    def test_instance_control_drift_rejects_in_both_actual_preparation_routes(self):
        cases = [('foundation', lambda d: d['Parameters']['EnableDeliveryRole'].update(Default='false')),
                 ('foundation', lambda d: d['Resources']['DeliveryRole'].pop('Condition')),
                 ('foundation', lambda d: d['Resources']['Cluster'].update(Condition='CreateDeliveryRole')),
                 ('foundation', lambda d: d['Conditions'].update(CreateDeliveryRole={'Fn::Equals': ['true', 'true']})),
                 ('core-server-persistence', lambda d: d['Parameters']['ServerDesiredCount'].update(Default=-1)),
                 ('core-server-persistence', lambda d: d['Parameters']['ObservabilityCollectorDesiredCount'].update(AllowedValues=[0, 1, -1])),
                 ('core-server-persistence', lambda d: d['Parameters']['ServerDesiredCount'].update(Default=True)),
                 ('core-server-persistence', lambda d: d['Resources']['CoreServerPersistenceService']['Properties'].update(DesiredCount=1)),
                 ('core-server-persistence', lambda d: d['Resources']['RuntimeCredentialsSecret'].pop('Condition')),
                 ('core-server-persistence', lambda d: d['Resources']['PersistenceDatabase'].update(Condition='CreateLegacyPasswordSecrets')),
                 ('core-server-persistence', lambda d: d['Outputs']['OrdinaryMigrationCredentialsSecretArn'].pop('Condition'))]
        for name, change in cases:
            path = self.root / self.base / '30-provider-realization/aws/cloudformation' / (name + '.yml')
            original = path.read_bytes()
            try:
                self.edit(str(path.relative_to(self.root)), change)
                for call in (self.resolve, self.session_plan):
                    with self.subTest(name=name), self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-instance-controls-invalid$'):
                        call()
            finally: path.write_bytes(original)

    def test_discard_projection_changes_only_declared_paths_and_preserves_both_other_phases(self):
        for scope in self.callers:
            ordinary = self.resolve(scope)
            before = {name: (self.root / name).read_bytes() for name in ordinary['references']}
            plan = self.session_plan(scope=scope)
            creation = dict(plan['projected_templates'])
            discard = dict(plan['discard_templates'])
            self.assertEqual(set(discard), {reference for _, reference in plan['stack_templates']})
            self.assertEqual(plan['discard_parameters'], plan['creation_parameters'])
            for key in ('discard_templates', 'discard_parameters'):
                self.assertIsInstance(plan[key], tuple)
                with self.assertRaises(TypeError): plan[key][0] = 'changed'
            with self.assertRaises(TypeError): plan['discard_parameters'][0][1][0][1] = 'changed'
            changed = []
            for reference, rendered in discard.items():
                original = self.owner.CF.template((self.root / reference).read_text())
                expected = json.loads(creation[reference])
                for name, row in original['Metadata'].get('DiscardControls', {}).items():
                    changed.append((reference, name))
                    self.assertEqual(set(row['attributes']), {'DeletionPolicy', 'UpdateReplacePolicy'})
                    self.assertEqual(set(row['properties']), {'DeletionProtection', 'DeleteAutomatedBackups'})
                    expected['Resources'][name].update(DeletionPolicy='Delete', UpdateReplacePolicy='Delete')
                    expected['Resources'][name]['Properties'].update(DeletionProtection=False, DeleteAutomatedBackups=True)
                    for unchanged in (json.loads(creation[reference]), json.loads(dict(plan['activation_templates'])[reference]),
                                      self.owner.target_template(original, self.target)):
                        resource = unchanged['Resources'][name]
                        self.assertEqual((resource['DeletionPolicy'], resource['UpdateReplacePolicy']), ('Snapshot', 'Snapshot'))
                        self.assertIs(resource['Properties']['DeletionProtection'], True)
                        self.assertNotIn('DeleteAutomatedBackups', resource['Properties'])
                    self.assertEqual(expected['Resources'][name]['Properties']['BackupRetentionPeriod'], 7)
                self.assertEqual(json.loads(rendered), expected)
                self.assertEqual(rendered, json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False))
                self.assertLessEqual(len(rendered.encode()), 51200)
                self.assertLessEqual(len((ROOT / reference).read_bytes()), 51200)
            self.assertEqual(len(changed), 1)
            self.assertEqual(before, {name: (self.root / name).read_bytes() for name in before})
            self.assertEqual(self.resolve(scope), ordinary)

    def test_discard_binding_follows_renamed_database_and_updates_source_fingerprint(self):
        previous = self.session_plan()
        reference = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        path = self.root / reference
        document = self.owner.CF.template(path.read_text())
        # Rename the logical resource, not the public output contract names.
        def rename(value):
            if isinstance(value, dict): return {('FreshDatabase' if key == 'PersistenceDatabase' else key): rename(item) for key, item in value.items()}
            if isinstance(value, list): return [rename(item) for item in value]
            if not isinstance(value, str): return value
            if value == 'PersistenceDatabase': return 'FreshDatabase'
            if value.startswith('PersistenceDatabase.'): return value.replace('PersistenceDatabase.', 'FreshDatabase.', 1)
            return value.replace('${PersistenceDatabase.', '${FreshDatabase.')
        document = rename(document)
        document['Resources']['FreshDatabase']['DeletionPolicy'] = 'Retain'
        document['Metadata']['DiscardControls']['FreshDatabase']['attributes']['DeletionPolicy']['expected'] = 'Retain'
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        current = self.session_plan()
        self.assertNotEqual(current['binding'].source_inputs_sha256, previous['binding'].source_inputs_sha256)
        inputs = dict(current['binding'].source_inputs)
        self.assertEqual(inputs[reference], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual({key: value for key, value in inputs.items() if key != reference},
                         {key: value for key, value in previous['binding'].source_inputs if key != reference})
        for key in ('projected_templates', 'activation_templates'):
            resource = json.loads(dict(current[key])[reference])['Resources']['FreshDatabase']
            self.assertEqual(resource['DeletionPolicy'], 'Retain')
            self.assertIs(resource['Properties']['DeletionProtection'], True)
        resources = json.loads(dict(current['discard_templates'])[reference])['Resources']
        self.assertNotIn('PersistenceDatabase', resources)
        self.assertEqual(resources['FreshDatabase']['DeletionPolicy'], 'Delete')
        self.assertIs(resources['FreshDatabase']['Properties']['DeletionProtection'], False)

    def test_discard_metadata_rejections_are_finite_at_actual_session_reader(self):
        reference = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        path = self.root / reference; original = path.read_bytes()
        changes = [lambda d: d['Metadata'].update(DiscardControls=None),
                   lambda d: d['Metadata'].update(DiscardControls=[]),
                   lambda d: d['Metadata'].update(DiscardControls='private-canary'),
                   lambda d: d['Metadata']['DiscardControls'].update(Missing=d['Metadata']['DiscardControls'].pop('PersistenceDatabase')),
                   lambda d: d['Metadata']['DiscardControls'].update(PersistenceDatabase=None)]
        rows = [lambda r: r.update(extra='private-canary'), lambda r: r.update(type='AWS::SecretsManager::Secret'),
                lambda r: r.pop('type'), lambda r: r.update(attributes=[]), lambda r: r.update(properties=None),
                lambda r: r['attributes'].pop('DeletionPolicy'),
                lambda r: r['properties'].update(Engine={'expected': 'postgres', 'discard': 'private-canary'}),
                lambda r: r['properties']['DeleteAutomatedBackups'].update(expected_absent=False),
                lambda r: r['properties']['DeleteAutomatedBackups'].update(expected_absent=1),
                lambda r: r['properties']['DeleteAutomatedBackups'].update(expected=False),
                lambda r: r['properties']['DeletionProtection'].update(expected=1),
                lambda r: r['properties']['DeletionProtection'].update(expected={'Ref': 'private-canary'}),
                lambda r: r['attributes']['DeletionPolicy'].update(expected='private-canary'),
                lambda r: r['attributes']['DeletionPolicy'].update(discard='Retain'),
                lambda r: r['attributes']['DeletionPolicy'].update(discard={'Fn::If': ['private-canary', 'Delete', 'Retain']}),
                lambda r: r['properties']['DeletionProtection'].update(discard=0),
                lambda r: r['properties']['DeletionProtection'].update(discard=True),
                lambda r: r['properties']['DeleteAutomatedBackups'].update(discard=1),
                lambda r: r['properties']['DeleteAutomatedBackups'].update(discard=False),
                lambda r: r['properties']['DeletionProtection'].pop('expected')]
        changes += [lambda d, change=change: change(d['Metadata']['DiscardControls']['PersistenceDatabase']) for change in rows]
        changes += [lambda d: d['Resources']['PersistenceDatabase'].update(DeletionPolicy='Retain'),
                    lambda d: d['Resources']['PersistenceDatabase']['Properties'].update(DeletionProtection=1),
                    lambda d: d['Resources']['PersistenceDatabase']['Properties'].update(DeleteAutomatedBackups=False)]
        for change in changes:
            try:
                self.edit(reference, change)
                with self.subTest(change=changes.index(change)), patch('subprocess.run', side_effect=AssertionError('child-started')), \
                        patch('subprocess.Popen', side_effect=AssertionError('child-started')):
                    with self.assertRaises(self.owner.InputFailure) as failure: self.session_plan()
                self.assertEqual(failure.exception.code, 'preparation-inputs-discard-controls-invalid')
                self.assertNotIn('private-canary', str(failure.exception))
            finally: path.write_bytes(original)

    def test_discard_inventory_rejects_unlisted_implicit_and_conditional_retention(self):
        foundation = self.base + '/30-provider-realization/aws/cloudformation/foundation.yml'
        persistence = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        cases = [(foundation, lambda d, key=key, value=value: d['Resources']['LogGroup'].update({key: value}), 'discard-retention-unresolved')
                 for key in ('DeletionPolicy', 'UpdateReplacePolicy')
                 for value in ('Retain', 'RetainExceptOnCreate', 'Snapshot', None, 1, {'Fn::If': ['private-canary', 'Delete', 'Retain']})]
        cases += [(persistence, lambda d: d['Metadata'].pop('DiscardControls'), 'discard-retention-unresolved'),
                  (persistence, lambda d: d['Metadata'].update(DiscardControls={}), 'discard-retention-unresolved'),
                  (foundation, lambda d: d['Resources'].update(Unowned={'Type': 'AWS::S3::Bucket'}), 'discard-resource-type-unsupported'),
                  (foundation, lambda d: d['Resources']['LogGroup'].update(Type='private-canary'), 'foundation-resource-unsupported'),
                  (foundation, lambda d: d['Resources'].update(ConditionalHistory={'Type': 'AWS::Logs::LogGroup', 'Condition': 'NotSelected', 'DeletionPolicy': 'Retain'}), 'discard-retention-unresolved'),
                  (foundation, lambda d: d['Resources'].update(ImplicitSnapshot={'Type': 'AWS::RDS::DBInstance', 'Properties': {'DeletionProtection': False, 'DeleteAutomatedBackups': True}}), 'discard-retention-unresolved'),
                  (foundation, lambda d: d['Resources'].update(ProtectedDatabase={'Type': 'AWS::RDS::DBInstance', 'DeletionPolicy': 'Delete', 'Properties': {'DeletionProtection': True, 'DeleteAutomatedBackups': True}}), 'discard-retention-unresolved'),
                  (foundation, lambda d: d['Resources']['LogGroup']['Properties'].update(DeletionProtection=True), 'discard-retention-unresolved')]
        for reference, change, reason in cases:
            path = self.root / reference; original = path.read_bytes()
            try:
                self.edit(reference, change)
                with self.subTest(reason=reason), self.assertRaises(self.owner.InputFailure) as failure: self.session_plan()
                self.assertEqual(failure.exception.code, 'preparation-inputs-' + reason)
                self.assertNotIn('private-canary', str(failure.exception))
            finally: path.write_bytes(original)

    def test_discard_checked_absence_can_explicitly_remove_an_implicit_snapshot_default(self):
        reference = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        def absent_policy(document):
            document['Resources']['PersistenceDatabase'].pop('DeletionPolicy')
            document['Metadata']['DiscardControls']['PersistenceDatabase']['attributes']['DeletionPolicy'] = {'expected_absent': True, 'discard': 'Delete'}
        self.edit(reference, absent_policy)
        plan = self.session_plan()
        self.assertNotIn('DeletionPolicy', json.loads(dict(plan['projected_templates'])[reference])['Resources']['PersistenceDatabase'])
        self.assertEqual(json.loads(dict(plan['discard_templates'])[reference])['Resources']['PersistenceDatabase']['DeletionPolicy'], 'Delete')

    def test_discard_duplicate_declarations_reject_at_the_shared_parser(self):
        path = self.root / self.base / '30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        original = path.read_text()
        cases = [original.replace('  DiscardControls:\n', '  DiscardControls: {}\n  DiscardControls:\n', 1),
                 original.replace('        DeletionProtection: {expected: true, discard: false}',
                                  '        DeletionProtection: {expected: true, discard: true}\n        DeletionProtection: {expected: true, discard: false}', 1)]
        for source in cases:
            try:
                self.assertNotEqual(source, original)
                path.write_text(source)
                with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-document-invalid$'): self.session_plan()
            finally: path.write_text(original)

    def test_creation_control_bindings_follow_renamed_resources_and_bounded_declarations(self):
        replacements = {'DeliveryRole': 'PublicationRole', 'CreateDeliveryRole': 'PublicationSelected',
                        'CoreServerPersistenceService': 'WriterService', 'ObservabilityCollectorService': 'TelemetryService',
                        'ServerDesiredCount': 'WriterCount', 'ObservabilityCollectorDesiredCount': 'TelemetryCount',
                        'RuntimeCredentialsSecret': 'UnusedWriterSecret', 'OrdinaryMigrationCredentialsSecret': 'UnusedMigrationSecret',
                        'RuntimeCredentialsSecretArn': 'UnusedWriterSecretArn', 'OrdinaryMigrationCredentialsSecretArn': 'UnusedMigrationSecretArn',
                        'FeatureService': 'ApplicationService'}
        def rename(value):
            if isinstance(value, dict): return {replacements.get(key, key): rename(item) for key, item in value.items()}
            if isinstance(value, list): return [rename(item) for item in value]
            return replacements.get(value, value) if isinstance(value, str) else value
        for name in ('foundation', 'core-server-persistence', 'entity-smoke'):
            path = self.root / self.base / '30-provider-realization/aws/cloudformation' / (name + '.yml')
            source = rename(self.owner.CF.template(path.read_text()))
            if name == 'core-server-persistence':
                source['Parameters']['WriterCount'].update(Default=2, AllowedValues=[0, 1, 2])
                source['Metadata']['CreationControls']['WriterCount']['active'] = 2
            if name == 'entity-smoke':
                source['Parameters']['WriterCount']['AllowedValues'] = [0, 3]
                source['Metadata']['CreationControls']['WriterCount']['active'] = 3
            path.write_text(yaml.safe_dump(source, sort_keys=False))
        self.assertEqual(self.resolve('core-server-persistence')['creation_parameters']['WriterCount'], '2')
        plan = self.session_plan()
        for reference, rendered in plan['projected_templates']:
            resources = json.loads(rendered)['Resources']
            if reference.endswith('/foundation.yml'): self.assertNotIn('PublicationRole', resources)
            if reference.endswith('/core-server-persistence.yml'):
                self.assertEqual(resources['WriterService']['Properties']['DesiredCount'], 0)
                self.assertEqual(resources['TelemetryService']['Properties']['DesiredCount'], 0)
                self.assertNotIn('UnusedWriterSecret', resources)
                self.assertNotIn('UnusedMigrationSecret', resources)
        for reference, rendered in plan['activation_templates']:
            resources = json.loads(rendered)['Resources']
            if reference.endswith('/core-server-persistence.yml'):
                self.assertEqual(resources['WriterService']['Properties']['DesiredCount'], 2)
                self.assertEqual(resources['TelemetryService']['Properties']['DesiredCount'], 1)
                self.assertNotIn('UnusedWriterSecret', resources)
                self.assertNotIn('UnusedMigrationSecret', resources)
            if reference.endswith('/entity-smoke.yml'):
                self.assertEqual(resources['ApplicationService']['Properties']['DesiredCount'], 3)
                self.assertEqual(self.resolve('entity-smoke')['creation_parameters'], {'WriterCount': '0'})

    def test_active_count_predicates_reject_at_actual_preparation_callers(self):
        changes = [lambda row: row.pop('active')]
        changes += [lambda row, value=value: row.update(active=value) for value in (None, False, True, 0, -1, 2, 1.0, 'private-canary', [], {})]
        for name in ('core-server-persistence', 'entity-smoke'):
            reference = self.base + '/30-provider-realization/aws/cloudformation/' + name + '.yml'
            path = self.root / reference; original = path.read_bytes()
            for change in changes:
                try:
                    self.edit(reference, lambda document: change(document['Metadata']['CreationControls']['ServerDesiredCount']))
                    for call in (self.resolve, self.session_plan):
                        with self.subTest(template=name), self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-instance-controls-invalid$'):
                            call()
                finally: path.write_bytes(original)
        reference = self.base + '/30-provider-realization/aws/cloudformation/entity-smoke.yml'
        self.edit(reference, lambda document: document['Metadata']['CreationControls'].clear())
        for call in (self.resolve, self.session_plan):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-instance-controls-invalid$'): call()

    def test_every_service_requires_an_explicit_bound_count_control(self):
        reference = self.base + '/30-provider-realization/aws/cloudformation/entity-smoke.yml'
        path = self.root / reference; original = path.read_bytes()
        for properties in ({}, {'DesiredCount': 0}, {'DesiredCount': 1}, {'DesiredCount': {'Ref': 'UnboundCount'}},
                           {'DesiredCount': {'Ref': 'ServerDesiredCount'}}, {'DesiredCount': {'Fn::If': ['Other', 0, 1]}}):
            try:
                self.edit(reference, lambda document: document['Resources'].update(UnboundService={'Type': 'AWS::ECS::Service', 'Properties': properties}))
                for call in (self.resolve, self.session_plan):
                    with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-instance-controls-invalid$'): call()
            finally: path.write_bytes(original)

    def test_creation_control_metadata_rejects_malformed_and_unbound_inputs(self):
        reference = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        path = self.root / reference; original = path.read_bytes()
        changes = [lambda d: d.pop('Metadata'), lambda d: d['Metadata'].pop('CreationControls'),
                   lambda d: d['Metadata'].update(CreationControls=[]),
                   lambda d: d['Metadata']['CreationControls'].pop('ServerDesiredCount'),
                   lambda d: d['Metadata']['CreationControls'].pop('IncludeLegacyPasswordSecrets'),
                   lambda d: d['Metadata']['CreationControls']['ServerDesiredCount'].update(temporary=True),
                   lambda d: d['Metadata']['CreationControls']['ServerDesiredCount'].update(resources=['Missing']),
                   lambda d: d['Metadata']['CreationControls']['ServerDesiredCount'].update(kind='unsupported'),
                   lambda d: d['Metadata']['CreationControls']['ServerDesiredCount'].update(extra='private-canary'),
                   lambda d: d['Metadata']['CreationControls']['ServerDesiredCount'].update(resources=['PersistenceDatabase']),
                   lambda d: d['Metadata']['CreationControls']['IncludeLegacyPasswordSecrets'].update(outputs=[]),
                   lambda d: d['Metadata']['CreationControls']['IncludeLegacyPasswordSecrets'].update(condition='Missing'),
                   lambda d: d['Metadata']['CreationControls']['IncludeLegacyPasswordSecrets'].update(resources=[]),
                   lambda d: d['Resources']['RuntimeCredentialsSecret'].update(Type='AWS::RDS::DBInstance'),
                   lambda d: d['Parameters']['ServerDesiredCount'].pop('AllowedValues'),
                   lambda d: d['Parameters']['ServerDesiredCount'].update(AllowedValues=[0, True]),
                   lambda d: d['Parameters']['ServerDesiredCount'].update(AllowedValues=[0, 2])]
        for change in changes:
            try:
                self.edit(reference, change)
                for call in (self.resolve, self.session_plan):
                    with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-instance-controls-invalid$'): call()
            finally: path.write_bytes(original)

    def test_session_predicates_reach_the_actual_consumer_without_values_or_children(self):
        cases = []
        def changed(key, value, reason):
            item = self.session_document(); item[key] = value; cases.append((item, 1000, 7200, reason))
        for value in (None, [], 'private-canary'):
            cases.append((value, 1000, 7200, 'document-type-invalid'))
        for key in self.session_document():
            item = self.session_document(); del item[key]; cases.append((item, 1000, 7200, 'document-fields-invalid'))
        for key in ('prefix', 'source_inputs_sha256', 'stack', 'account'):
            changed(key, 'private-canary', 'document-fields-invalid')
        changed('schema', 'private-canary', 'schema-unsupported')
        for key in ('target', 'scope'):
            for value in (None, [], '', 'private-canary/'):
                changed(key, value, key + '-invalid')
            changed(key, 'different', key + '-mismatch')
        for value in (None, True, '', 'A' * 32, 'a' * 31, 'a' * 33, 'private-canary'):
            changed('session_id', value, 'identity-invalid')
        for key in ('starts_at', 'expires_at'):
            for value in (None, True, 1.0, '1000', -1):
                changed(key, value, key.replace('_', '-') + '-invalid')
        changed('expires_at', 1000, 'expiry-order-invalid')
        changed('starts_at', 1001, 'start-in-future')
        cases.append((self.session_document(), 8200, 7200, 'expired'))
        for value in (None, True, 1000.0, -1): cases.append((self.session_document(), value, 7200, 'clock-invalid'))
        for value in (None, True, 7200.0, 0, -1): cases.append((self.session_document(), 1000, value, 'approved-duration-invalid'))
        cases.append((self.session_document(), 1000, 7199, 'approved-duration-exceeded'))
        changed('environment_lifecycle', {'mode': 'temporary', 'data_retention': 'discard', 'max_duration_seconds': 7199}, 'policy-duration-exceeded')
        changed('environment_lifecycle', {'mode': 'persistent', 'data_retention': 'preserve'}, 'temporary-policy-required')
        changed('environment_lifecycle', {'mode': 'temporary', 'data_retention': 'preserve', 'max_duration_seconds': 7200}, 'environment-lifecycle-temporary-data-retention-conflict')
        for document, now, maximum, reason in cases:
            with self.subTest(reason=reason, document=document), patch.object(self.owner, '_load', side_effect=AssertionError('source resolution must not run')), \
                    patch('subprocess.run', side_effect=AssertionError('child must not run')):
                with self.assertRaises(self.owner.InputFailure) as failure:
                    self.owner.load_session_plan(self.root, self.target, 'entity-smoke', document, now, maximum)
                self.assertEqual(str(failure.exception), 'preparation-inputs-environment-session-' + reason)
                self.assertNotIn('private-canary', str(failure.exception))

    def test_session_helper_failure_preserves_persistent_path_and_reports_source_failure(self):
        ordinary = self.resolve()
        original = self.owner.module
        for failure in (FileNotFoundError, SyntaxError, ImportError, RuntimeError):
            def module(name, path):
                if name == 'preparation_environment_session': raise failure('private-canary')
                return original(name, path)
            with self.subTest(failure=failure), patch.object(self.owner, 'module', side_effect=module), \
                    patch('subprocess.run', side_effect=AssertionError('child must not run')):
                self.assertEqual(self.resolve(), ordinary)
                with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-source-unavailable$'):
                    self.session_plan()

    def test_session_captured_inputs_change_detection_and_new_fingerprint(self):
        first = self.session_plan()
        profile = self.base + '/00-target/target-profile.yml'
        original = self.owner.CF.project_parameters
        changed = []
        def project(*args, **kwargs):
            result = original(*args, **kwargs)
            if not changed:
                self.edit(profile, lambda value: value['provider'].update(profile='changed-profile'))
                changed.append(True)
            return result
        with patch.object(self.owner.CF, 'project_parameters', side_effect=project):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-source-changed$'):
                self.session_plan()
        second = self.session_plan()
        self.assertNotEqual(first['binding'].source_inputs_sha256, second['binding'].source_inputs_sha256)
        self.assertEqual(second['source_configuration']['profile'], 'changed-profile')

    def test_session_planning_does_not_weaken_source_policy_or_stack_selection(self):
        profile = self.base + '/00-target/target-profile.yml'
        self.edit(profile, lambda value: value.update(environment_lifecycle=self.session_document()['environment_lifecycle']))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-environment-lifecycle-session-binding-unsupported$'):
            self.session_plan()
        self.edit(profile, lambda value: value.pop('environment_lifecycle'))
        binding = self.base + '/20-scopes/entity-smoke/10-workload-binding/workload-binding.yml'
        self.edit(binding, lambda value: value['proposed_provider_binding'].update(stack='unrelated-stack'))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-stack-source-unsupported$'):
            self.session_plan()
        self.edit(binding, lambda value: value['proposed_provider_binding'].update(stack=self.target + '-foundation'))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-stack-identity-ambiguous$'):
            self.session_plan()

    def test_session_planning_rejects_the_actual_production_prefix(self):
        replacement = 's-' + 'a' * 19
        scope = 'another-feature'
        self.rename_source_target(replacement, scope)
        document = self.session_document(scope)
        document['target'] = replacement
        self.assertEqual(self.owner.load(self.root, replacement, scope)['target'], replacement)
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-production-identity-conflict$'):
            self.owner.load_session_plan(self.root, replacement, scope, document, 1000, 7200)

    def test_session_planning_rejects_a_declared_dependency_cycle(self):
        dependency = self.owner.CF.template((self.root / self.base / '20-scopes/entity-smoke/10-workload-binding/workload-binding.yml').read_text())['proposed_provider_binding']['dependencies']
        self.edit(self.base + '/20-scopes/core-server-persistence/10-workload-binding/workload-binding.yml',
                  lambda value: value['proposed_provider_binding'].update(dependencies=dependency))
        with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-dependency-cycle$'):
            self.session_plan()

    def test_session_projection_and_source_failures_are_finite(self):
        original_project = self.owner.CF.project_parameters
        def project(*args, **kwargs):
            if len(args) == 3: raise ValueError('private-canary')
            return original_project(*args, **kwargs)
        with patch.object(self.owner.CF, 'project_parameters', side_effect=project):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-session-template-projection-invalid$'):
                self.session_plan()
        original_read = Path.read_bytes
        def read(path):
            if path == self.root / self.base / '00-target/target-profile.yml': raise OSError('private-canary')
            return original_read(path)
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-source-unavailable$'):
                self.session_plan()

    def test_session_preparation_uses_both_shared_checked_results(self):
        session = self.imported(ROOT / self.session_path)
        original_module = self.owner.module
        original_read, original_bind = session.read, session.bind_sources
        checked_bindings = []
        def module(name, path):
            return session if name == 'preparation_environment_session' else original_module(name, path)
        def read(*args, **kwargs):
            return replace(original_read(*args, **kwargs), session_id='b' * 32)
        def bind(*args):
            result = original_bind(*args)
            checked_bindings.append(result)
            return result
        with patch.object(self.owner, 'module', side_effect=module), \
                patch.object(session, 'read', side_effect=read) as checked_read, \
                patch.object(session, 'bind_sources', side_effect=bind) as checked_bind:
            result = self.session_plan()
            checked_read.assert_called_once()
            checked_bind.assert_called_once()
            self.assertEqual(result['resource_name_prefix'], 's-' + 'b' * 19)
            self.assertIs(result['binding'], checked_bindings[0])
            self.assertIs(checked_bind.call_args.args[0], result['binding'].intent)
        with patch.object(self.owner, 'module', side_effect=module), \
                patch.object(session, 'read', side_effect=session.SessionFailure('identity-invalid')), \
                patch.object(self.owner, '_load', side_effect=AssertionError('unchecked input must not reach source work')):
            with self.assertRaisesRegex(self.owner.InputFailure, '^preparation-inputs-environment-session-identity-invalid$'):
                self.session_plan()

    def assert_core_profile_failure(self, code):
        core = self.imported(ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py')
        with patch('sys.argv', ['target', '--target-root', str(self.root / self.base)]), \
                patch.object(core, 'check_foundation', side_effect=AssertionError('later validation must not run')), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(), 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report['findings'], [{'code': code}])
        self.assertEqual(report['verdict'], 'failed')
        self.assertNotIn('private-canary', output.getvalue())

    def run_with_import_failure(self, command, owner, fault, arguments):
        driver = '''import importlib.machinery, runpy, subprocess, sys
fault, selected, command, *arguments = sys.argv[1:]
sys.argv = [command, *arguments]
original = importlib.machinery.SourceFileLoader.exec_module
failures = {'missing': FileNotFoundError, 'syntax': SyntaxError, 'import': ImportError, 'unexpected': RuntimeError}
def load(loader, module):
    if loader.name == selected: raise failures[fault]('private-import-canary')
    return original(loader, module)
children = []
def no_child(*args, **kwargs):
    children.append(True)
    raise AssertionError('child-work-started')
importlib.machinery.SourceFileLoader.exec_module = load
subprocess.run = subprocess.Popen = no_child
try: runpy.run_path(command, run_name='__main__')
finally: assert not children, 'child-work-started'
'''
        return subprocess.run([sys.executable, '-B', '-c', driver, fault, owner, str(ROOT / command), *arguments],
                              capture_output=True, text=True, timeout=10)

    def test_added_import_failures_reach_real_cli_reports(self):
        core = 'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py'
        core_report = {'schema': 'deploy/target-declaration-report/v1', 'target': self.target,
                       'scope': 'repository-declaration', 'verdict': 'failed',
                       'findings': [{'code': 'declaration-observation-unavailable'}]}
        cases = [(core, owner, [], core_report) for owner in ('target_environment_lifecycle', 'target_profile_document')]
        cases.extend([
            (self.callers['core-server-persistence'], 'preparation_environment_lifecycle', ['--receipt', '/unused/private-import-canary'],
             {'schema': 'deploy/persistence-candidate-preparation-report/v1', 'target': self.target,
              'scope': 'core-server-persistence', 'verdict': 'blocked', 'findings': [{'code': 'preparation-inputs-source-unavailable'}]}),
            (self.callers['entity-smoke'], 'preparation_environment_lifecycle', ['--receipt', '/unused/private-import-canary'],
             {'schema': 'deploy/entity-smoke-target-alignment/v1', 'verdict': 'blocked', 'code': 'ENTITY_SMOKE_ALIGNMENT_NOT_CONFIRMED',
              'condition': 'preparation-inputs-source-unavailable', 'effect': 'not-started', 'provider_mutation': False}),
        ])
        for command, owner, arguments, expected in cases:
            for fault in ('missing', 'syntax', 'import', 'unexpected'):
                with self.subTest(owner=owner, command=command, fault=fault):
                    result = self.run_with_import_failure(command, owner, fault, arguments)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stderr, '')
                    self.assertEqual(json.loads(result.stdout), expected)
                    self.assertNotIn('private-import-canary', result.stdout + result.stderr)

    def test_added_import_failures_preserve_argument_only_paths(self):
        core = 'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py'
        valid = {'schema': 'deploy/command-arguments-report/v1', 'verdict': 'valid', 'findings': []}
        for owner in ('target_environment_lifecycle', 'target_profile_document'):
            for arguments in (['--validate-arguments'], ['--help']):
                result = self.run_with_import_failure(core, owner, 'unexpected', arguments)
                self.assertEqual((result.returncode, result.stderr), (0, ''))
                if arguments == ['--help']:
                    self.assertEqual(result.stdout, 'Usage: script.py [--target-root <path>] [--json]\n')
                else:
                    self.assertEqual(json.loads(result.stdout), valid)
        result = self.run_with_import_failure(self.callers['entity-smoke'], 'preparation_environment_lifecycle', 'unexpected',
                                              ['--receipt', '/unused/private-import-canary', '--validate-arguments'])
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(json.loads(result.stdout), valid)
        result = self.run_with_import_failure(self.callers['core-server-persistence'], 'preparation_environment_lifecycle', 'unexpected', [])
        self.assertEqual((result.returncode, result.stderr), (1, ''))
        self.assertEqual(json.loads(result.stdout)['findings'], [{'code': 'persistence-candidate-preparation-arguments-invalid'}])

    def test_environment_lifecycle_defaults_and_explicit_choices_are_checked(self):
        owner = self.owner.LIFECYCLE
        persistent = {'mode': 'persistent', 'data_retention': 'preserve'}
        absent = owner.read({})
        self.assertEqual(vars(absent), {'mode': 'persistent', 'data_retention': 'preserve', 'max_duration_seconds': None, 'explicit': False})
        declared = owner.read({'environment_lifecycle': persistent})
        self.assertEqual(vars(declared), {**vars(absent), 'explicit': True})
        self.assertIs(owner.require_persistent(declared), declared)
        with self.assertRaises(FrozenInstanceError):
            declared.mode = 'temporary'
        for duration in (1, 7200, 86401):
            selected = owner.read({'environment_lifecycle': {'mode': 'temporary', 'data_retention': 'discard', 'max_duration_seconds': duration}})
            self.assertEqual(vars(selected), {'mode': 'temporary', 'data_retention': 'discard', 'max_duration_seconds': duration, 'explicit': True})
            with self.assertRaisesRegex(owner.PolicyFailure, '^environment-lifecycle-session-binding-unsupported$'):
                owner.require_persistent(selected)
        for scope in self.callers:
            result = self.resolve(scope)
            self.assertEqual(result['environment_lifecycle'], vars(absent))
            self.assertIn(self.owner.LIFECYCLE_REFERENCE, result['references'])
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d.update(environment_lifecycle=persistent))
        core = self.imported(ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py')
        core.check_profile(core.profile_mapping(self.root / self.base / '00-target/target-profile.yml'))
        for scope, path in self.callers.items():
            caller = self.imported(self.root / path)
            self.assertIsNone(caller.INPUT_ERROR)
            self.assertEqual(caller.INPUTS['environment_lifecycle'], vars(declared))

    def test_environment_lifecycle_rejections_reach_actual_callers(self):
        owner = self.owner.LIFECYCLE
        persistent = {'mode': 'persistent', 'data_retention': 'preserve'}
        temporary = {'mode': 'temporary', 'data_retention': 'discard', 'max_duration_seconds': 7200}
        cases = [
            (None, 'policy-null'),
            ('private-canary', 'policy-type-invalid'),
            ([], 'policy-type-invalid'),
            ({}, 'policy-empty'),
            ({**persistent, 'private-canary': True}, 'policy-field-unsupported'),
            ({'data_retention': 'preserve'}, 'mode-missing'),
            ({'mode': 'persistent'}, 'data-retention-missing'),
            ({**persistent, 'data_retention': 'discard'}, 'persistent-data-retention-conflict'),
            ({**persistent, 'max_duration_seconds': None}, 'persistent-expiry-prohibited'),
            ({**persistent, 'max_duration_seconds': 7200}, 'persistent-expiry-prohibited'),
            ({**temporary, 'data_retention': 'preserve'}, 'temporary-data-retention-conflict'),
            ({'mode': 'temporary', 'data_retention': 'discard'}, 'max-duration-seconds-missing'),
            ({**temporary, 'max_duration_seconds': None}, 'max-duration-seconds-null'),
        ]
        for field in ('mode', 'data_retention'):
            for value, reason in ((None, 'null'), ([], 'type-invalid'), (True, 'type-invalid'), ('', 'empty'), ('private-canary', 'unsupported'), (' ', 'unsupported')):
                cases.append(({**persistent, field: value}, field.replace('_', '-') + '-' + reason))
        for value in (True, False, 1.0, '7200', [], 'private-canary'):
            cases.append(({**temporary, 'max_duration_seconds': value}, 'max-duration-seconds-type-invalid'))
        for value in (0, -1):
            cases.append(({**temporary, 'max_duration_seconds': value}, 'max-duration-seconds-not-positive'))
        for policy, reason in cases:
            with self.subTest(reason=reason, policy_type=type(policy).__name__):
                code = 'environment-lifecycle-' + reason
                with self.assertRaises(owner.PolicyFailure) as failure:
                    owner.read({'environment_lifecycle': policy})
                self.assertEqual(str(failure.exception), code)
                self.edit(self.base + '/00-target/target-profile.yml', lambda d: d.update(environment_lifecycle=policy))
                with self.assertRaises(self.owner.InputFailure) as failure:
                    self.resolve()
                self.assertEqual(failure.exception.code, 'preparation-inputs-' + code)
                self.assert_core_profile_failure(code)
                self.assert_preparation_failure('preparation-inputs-' + code)
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d.update(environment_lifecycle=temporary))
        self.assert_core_profile_failure('environment-lifecycle-session-binding-unsupported')
        self.assert_preparation_failure('preparation-inputs-environment-lifecycle-session-binding-unsupported')
        for profile in (None, [], 'private-canary'):
            with self.assertRaisesRegex(owner.PolicyFailure, '^environment-lifecycle-profile-type-invalid$'):
                owner.read(profile)

    def test_lifecycle_shared_checked_result_is_used_by_both_owners(self):
        core = self.imported(ROOT / 'scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py')
        profile = self.owner.read_document(self.root, self.base + '/00-target/target-profile.yml')
        for module, operation, failure_type in (
                (self.owner, self.resolve, self.owner.InputFailure),
                (core, lambda: core.check_profile(profile), core.DeclarationFailure)):
            selected = module.LIFECYCLE.LifecyclePolicy('temporary', 'discard', 7200, True)
            with patch.object(module.LIFECYCLE, 'read', return_value=selected) as shared:
                with self.assertRaises(failure_type) as failure:
                    operation()
                self.assertIn('environment-lifecycle-session-binding-unsupported', str(failure.exception))
                shared.assert_called_once_with(profile)
            with patch.object(module.LIFECYCLE, 'require_persistent', side_effect=module.LIFECYCLE.PolicyFailure('session-binding-unsupported')) as shared:
                with self.assertRaises(failure_type):
                    operation()
                shared.assert_called_once()
                self.assertEqual(vars(shared.call_args.args[0]), {'mode': 'persistent', 'data_retention': 'preserve', 'max_duration_seconds': None, 'explicit': False})
        checked = self.owner.LIFECYCLE.LifecyclePolicy('persistent', 'preserve', None, True)
        with patch.object(self.owner.LIFECYCLE, 'read', return_value=checked):
            self.assertEqual(self.resolve()['environment_lifecycle'], vars(checked))

    def test_ambiguous_profile_cannot_hide_a_temporary_policy(self):
        path = self.root / self.base / '00-target/target-profile.yml'
        original = path.read_text()
        duplicates = [
            'environment_lifecycle: {mode: temporary, data_retention: discard, max_duration_seconds: 7200}\nenvironment_lifecycle: {mode: persistent, data_retention: preserve}\n',
            'environment_lifecycle: {mode: temporary, mode: persistent, data_retention: preserve}\n',
        ]
        for duplicate in duplicates:
            path.write_text(original + '\n' + duplicate)
            self.assert_core_profile_failure('target-profile-document-invalid')
            self.assert_preparation_failure('preparation-inputs-document-invalid')
        for raw in ('[]', '[', 'environment_lifecycle: private-canary\nenvironment_lifecycle: {}'):
            path.write_text(raw)
            self.assert_core_profile_failure('target-profile-document-invalid')
        path.unlink()
        self.assert_core_profile_failure('target-profile-unreadable')


    def test_declared_postgresql_major_reaches_both_preparation_routes(self):
        image = 'infra/04.deploy/03.product/image/entity-smoke/image-contract.yml'
        database = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        self.assertEqual(self.resolve()['dependencies']['database']['engine_major'], 18)
        self.edit(image, lambda d: d['postgresql'].update(compatible_major=19, qualification_image='postgres:19.1-bookworm'))
        with self.assertRaisesRegex(self.owner.InputFailure, 'dependency-engine-major-incompatible'):
            self.resolve()
        self.edit(database, lambda d: d['Resources']['PersistenceDatabase']['Properties'].update(EngineVersion='19'))
        self.assertEqual(self.resolve()['dependencies']['database']['engine_major'], 19)
        with self.assertRaisesRegex(self.owner.InputFailure, 'engine-major-incompatible'):
            self.resolve('core-server-persistence')
        self.edit(database, lambda d: d['Resources']['PersistenceDatabase']['Properties'].pop('EngineVersion'))
        with self.assertRaisesRegex(self.owner.InputFailure, 'dependency-engine-version-unsupported'):
            self.resolve()
        self.edit(image, lambda d: d.pop('postgresql'))
        with self.assertRaisesRegex(self.owner.InputFailure, 'postgresql-version-declaration-invalid'):
            self.resolve()

    def test_real_callers_consume_selected_values_and_optional_profile(self):
        for scope in self.callers:
            actual = self.imported(ROOT / self.callers[scope])
            self.assertIsNone(actual.INPUT_ERROR)
            self.assertEqual(actual.INPUTS, self.owner.load(ROOT, self.target, scope))
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d['provider'].update(account_id='123456789012', region='eu-west-2'))
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d['provider'].pop('profile'))
        self.edit(self.base + '/30-provider-realization/aws/cloudformation/foundation.yml',
                  lambda d: (d['Resources']['Cluster']['Properties'].update(ClusterName='different-cluster'),
                             d['Resources']['LogGroup']['Properties'].update(LogGroupName='/different/logs'),
                             d['Resources']['Namespace']['Properties'].update(Name='different.internal')))
        self.edit(self.base + '/40-package-custody/github-actions/pipeline-index.yml',
                  lambda d: [p.update(provider_region_alias='aws-eu-west-2', package_destination='another/product') for p in d['pipelines']])
        for scope, path in self.callers.items():
            caller = self.imported(self.root / path)
            self.assertIsNone(caller.INPUT_ERROR)
            self.assertEqual(caller.INPUTS['foundation_expected'], {'cluster_arn':'arn:aws:ecs:eu-west-2:123456789012:cluster/different-cluster','log_group':'/different/logs','namespace':'different.internal'})
            self.assertEqual((caller.ACCOUNT, caller.REGION, caller.PROFILE, caller.REPOSITORY), ('123456789012', 'eu-west-2', None, 'another/product'))
            if scope == 'entity-smoke':
                with patch.object(caller.CLI, 'invoke_json', return_value={}) as invoke:
                    caller.aws('sts', 'get-caller-identity')
            else:
                with patch.object(caller.aws_response(), 'inventory_covered', return_value=True), patch.object(caller.aws_cli(), 'invoke_json', return_value={}) as invoke:
                    self.assertTrue(caller.aws('sts', 'get-caller-identity')[0])
                parameters = caller.candidate_parameters({}, {}, {'image_digest': 'digest', 'source_revision': 'source'})
                self.assertEqual(parameters['ImageRepositoryUri'], '123456789012.dkr.ecr.eu-west-2.amazonaws.com/another/product')
            argv = invoke.call_args.args[0]
            self.assertNotIn('--profile', argv)
            self.assertEqual(argv[argv.index('--region') + 1], 'eu-west-2')
        # Recovery's supported imported identifier also follows its existing template owner.
        self.edit(self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml',
                  lambda d: d['Resources']['PersistenceDatabase']['Properties'].update(DBInstanceIdentifier='different-database'))
        feature = self.imported(self.root / self.callers['entity-smoke'])
        self.assertEqual(feature.DATABASE, 'different-database')

    def test_foundation_selection_follows_output_references_not_resource_names(self):
        expected = self.resolve()['foundation_expected']
        def rename(document):
            resources = document['Resources']
            for old, new in [('Cluster','OtherCluster'),('LogGroup','OtherLog'),('Namespace','OtherNamespace'),('BootstrapServiceDiscovery','OtherService')]:
                resources[new] = resources.pop(old)
            document['Outputs']['ClusterArn']['Value'] = {'Fn::GetAtt':['OtherCluster','Arn']}
            document['Outputs']['LogGroupName']['Value'] = {'Ref':'OtherLog'}
            document['Outputs']['ServiceDiscoveryArn']['Value'] = {'Fn::GetAtt':['OtherService','Arn']}
            resources['OtherService']['Properties']['DnsConfig']['NamespaceId'] = {'Ref':'OtherNamespace'}
        self.edit(self.base + '/30-provider-realization/aws/cloudformation/foundation.yml', rename)
        self.assertEqual(self.resolve()['foundation_expected'], expected)

    def test_resource_prefix_defaults_preserve_checked_literal_inputs(self):
        templates = [self.root / self.base / '30-provider-realization/aws/cloudformation' / name
                     for name in ('foundation.yml', 'core-server-persistence.yml', 'entity-smoke.yml')]
        originals = [path.read_bytes() for path in templates]
        with patch.object(self.owner.CF, 'project_parameters', wraps=self.owner.CF.project_parameters) as shared:
            result = self.resolve()
            self.assertTrue(shared.called)
            for call in shared.call_args_list:
                self.assertEqual(call.args[1][0], 'ResourceNamePrefix')
                self.assertEqual(set(call.kwargs), {'condition_names'})
        self.assertEqual(result['foundation_expected'], {'cluster_arn': 'arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform',
                         'log_group': '/aws/ecs/kanbien-core-platform', 'namespace': 'kanbien-core-platform.internal'})
        database = result['dependencies']['database']
        self.assertEqual((database['identifier'], database['administrator_secret_name']),
                         ('kanbien-core-platform-persistence', 'kanbien-core-platform-persistence-migration'))
        self.assertEqual((result['budget']['BudgetName'], result['budget']['CostFilters']),
                         ('kanbien-core-platform-monthly', {'TagKeyValue': ['user:Target$kanbien-core-platform']}))
        self.assertIn(self.owner.CF_REFERENCE, result['references'])
        self.assertEqual([path.read_bytes() for path in templates], originals)
        project = self.owner.CF.project_parameters
        def checked(document, names, **kwargs):
            selected = project(document, names, **kwargs)
            if 'Cluster' in selected.get('Resources', {}):
                selected['Resources']['Cluster']['Properties']['ClusterName'] = 'checked-cluster'
            return selected
        with patch.object(self.owner.CF, 'project_parameters', side_effect=checked):
            self.assertTrue(self.resolve()['foundation_expected']['cluster_arn'].endswith('/checked-cluster'))

    def test_resource_prefix_rejections_reach_fixed_callers(self):
        for template in ('foundation', 'core-server-persistence', 'entity-smoke'):
            source = self.base + '/30-provider-realization/aws/cloudformation/' + template + '.yml'
            path = self.root / source
            original = path.read_bytes()
            scopes = ['entity-smoke'] if template == 'entity-smoke' else list(self.callers)
            for mutation, reason in (
                    (lambda d: d['Parameters']['ResourceNamePrefix'].update(Default='private-canary'), 'target-mismatch'),
                    (lambda d: d['Parameters'].pop('ResourceNamePrefix'), 'document-invalid'),
                    (lambda d: d['Parameters']['ResourceNamePrefix'].pop('Default'), 'document-invalid'),
                    (lambda d: d['Parameters'].update(ResourceNamePrefix=None), 'document-invalid'),
                    (lambda d: d['Parameters']['ResourceNamePrefix'].update(NoEcho=True), 'document-invalid'),
                    (lambda d: d['Parameters']['ResourceNamePrefix'].update(Default=True), 'document-invalid')):
                with self.subTest(template=template, reason=reason):
                    self.edit(source, mutation)
                    self.assert_preparation_failure('preparation-inputs-' + reason, scopes)
                    path.write_bytes(original)
            path.write_bytes(original + b'\nParameters: {ResourceNamePrefix: {Type: String, Default: private-canary}}\n')
            self.assert_preparation_failure('preparation-inputs-document-invalid', scopes)
            path.write_bytes(original)

    def test_endpoint_policy_declarations_reach_actual_caller(self):
        source = self.base + '/30-provider-realization/aws/cloudformation/foundation.yml'
        def change(document):
            resources = document['Resources']
            resources['RenamedApiEndpoint'] = resources.pop('EcrApiEndpoint')
            for entry in resources.values():
                if entry.get('Type') == 'AWS::EC2::VPCEndpoint':
                    for row in entry['Properties']['PolicyDocument']['Statement']:
                        if isinstance(row['Resource'], list): row['Resource'].extend(['arn:aws:ecr:eu-west-1:337159794548:repository/new/one', 'arn:aws:ecr:eu-west-1:337159794548:repository/new/two'])
        self.edit(source, change)
        caller = self.imported(self.root / self.callers['entity-smoke'])
        self.assertIsNone(caller.INPUT_ERROR)
        policies = caller.INPUTS['foundation_endpoint_policies']
        self.assertEqual(policies, self.resolve()['foundation_endpoint_policies'])
        for policy in policies.values():
            row = next(row for row in policy['Statement'] if isinstance(row['Action'], list))
            self.assertEqual(len(row['Resource']), 4)
            self.assertEqual(row['Resource'][-1], 'arn:aws:ecr:eu-west-1:337159794548:repository/new/two')
        before = (self.root / source).read_bytes()
        for mutation, reason in [
            (lambda d: d['Resources']['RenamedApiEndpoint']['Properties']['PolicyDocument']['Statement'][1].update(Resource={'Ref':'Unknown'}), 'endpoint-policy-reference-unsupported'),
            (lambda d: d['Resources']['RenamedApiEndpoint']['Properties']['PolicyDocument']['Statement'][1].update(Resource={'Fn::Sub':'${Unknown}'}), 'endpoint-policy-source-unsupported'),
            (lambda d: d['Resources'].update(Duplicate=copy.deepcopy(d['Resources']['RenamedApiEndpoint'])), 'endpoint-policy-selection-ambiguous'),
        ]:
            try:
                self.edit(source, mutation)
                rejected = self.imported(self.root / self.callers['entity-smoke'])
                self.assertEqual(rejected.INPUT_ERROR, 'preparation-inputs-' + reason)
                with self.assertRaises(rejected.AlignmentFailure): rejected.inspect(lambda *a, **kw: self.fail('provider invoked'), {}, 'unused')
            finally: (self.root / source).write_bytes(before)

    def test_budget_declarations_reach_all_callers_without_package_inputs_for_provisioning(self):
        source = self.base + '/10-foundation/budget-control.yml'
        template = self.base + '/30-provider-realization/aws/cloudformation/foundation.yml'
        self.edit(source, lambda d: d['expected_provider_configuration'].update(budget_name='another-monthly', amount=250, unit='EUR', target_filter='user:Target$another'))
        self.edit(template, lambda d: d['Resources']['Budget']['Properties']['Budget'].update(BudgetName='another-monthly', BudgetLimit={'Amount':'250.00','Unit':'EUR'}, CostFilters={'TagKeyValue':['user:Target$another']}))
        expected = self.resolve()['budget']
        for scope, path in self.callers.items():
            caller = self.imported(self.root / path)
            self.assertIsNone(caller.INPUT_ERROR)
            self.assertEqual(caller.INPUTS['budget'], expected)
            if scope == 'core-server-persistence':
                with patch.object(caller, 'aws', return_value=(True, {'Budget':expected}, 'ok')) as provider, patch.object(caller.FOUNDATION_CHECKS, 'budget', wraps=caller.FOUNDATION_CHECKS.budget) as shared:
                    self.assertEqual(caller.live_budget(), (True, 'ok'))
                    self.assertEqual(provider.call_args.args[-1], 'another-monthly')
                    shared.assert_called_once_with(expected, expected)
                with patch.object(caller, 'aws', return_value=(False, None, 'aws-access-denied')):
                    self.assertEqual(caller.live_budget(), (False, 'aws-access-denied'))
        provision = 'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py'
        destination = self.root / provision; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / provision, destination)
        # This consumer does not need an application image or program declaration.
        shutil.rmtree(self.root / 'infra/04.deploy/03.product/image')
        caller = self.imported(destination)
        self.assertIsNone(caller.INPUT_ERROR)
        with patch.object(caller, 'aws', return_value=(True, {'Budget':expected}, 'ok')) as provider, patch.object(caller.INPUT_OWNER.CHECKS, 'budget', wraps=caller.INPUT_OWNER.CHECKS.budget) as shared:
            result, code = caller.verify()
            self.assertIsNone(code); self.assertEqual((result['amount'],result['unit']), ('250','EUR'))
            self.assertEqual(provider.call_args.args[-1], 'another-monthly')
            shared.assert_called_once_with(expected, expected)
        self.edit(source, lambda d: d['expected_provider_configuration'].update(amount=251))
        caller = self.imported(destination)
        self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-budget-template-mismatch')
        with patch.object(caller, 'aws', side_effect=AssertionError('provider must not run')):
            self.assertEqual(caller.verify(), (None, caller.INPUT_ERROR))
            with patch('sys.argv',['budget','--mode','create']), contextlib.redirect_stdout(io.StringIO()): self.assertEqual(caller.main(), 1)
        for mutation, reason in (
                (lambda d: d['Parameters']['ResourceNamePrefix'].update(Default='private-canary'), 'target-mismatch'),
                (lambda d: d['Parameters'].pop('ResourceNamePrefix'), 'document-invalid')):
            self.edit(template, mutation)
            caller = self.imported(destination)
            self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-' + reason)
            with patch.object(caller, 'aws', side_effect=AssertionError('provider must not run')):
                self.assertEqual(caller.verify(), (None, caller.INPUT_ERROR))

    def test_budget_source_errors_reject_before_provider_work(self):
        source = self.base + '/10-foundation/budget-control.yml'
        original = (self.root / source).read_bytes()
        for change, reason in [
            (lambda d: d.update(target='other'), 'budget-target-mismatch'),
            (lambda d: d.pop('expected_provider_configuration'), 'budget-declaration-invalid'),
            (lambda d: d['expected_provider_configuration'].update(amount=True), 'budget-declaration-invalid'),
            (lambda d: d['expected_provider_configuration'].update(amount='sNaN'), 'budget-declaration-invalid'),
            (lambda d: d['expected_provider_configuration'].update(budget_name='other'), 'budget-selection-not-confirmed'),
            (lambda d: d['expected_provider_configuration'].update(amount=101), 'budget-template-mismatch'),
        ]:
            self.edit(source, change)
            for scope, path in self.callers.items():
                caller = self.imported(self.root / path)
                self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-' + reason)
                if scope == 'entity-smoke':
                    with self.assertRaises(caller.AlignmentFailure): caller.inspect(lambda *a, **kw:self.fail('provider invoked'), {}, 'unused')
                else:
                    with patch.object(caller,'aws',side_effect=AssertionError('provider invoked')): self.assertEqual(caller.live_budget(), (False, caller.INPUT_ERROR))
            (self.root / source).write_bytes(original)

        template = self.base + '/30-provider-realization/aws/cloudformation/foundation.yml'
        original = (self.root / template).read_bytes()
        for mutation, reason in [
            (lambda d: d['Resources'].update(DuplicateBudget=copy.deepcopy(d['Resources']['Budget'])), 'budget-selection-not-confirmed'),
            (lambda d: d['Resources']['Budget']['Properties']['Budget']['BudgetLimit'].update(Amount=101), 'budget-template-mismatch'),
            (lambda d: d['Resources']['Budget']['Properties']['Budget']['CostFilters'].update(Service=['other']), 'budget-template-mismatch'),
        ]:
            self.edit(template, mutation)
            with self.assertRaises(self.owner.InputFailure) as failure: self.resolve()
            self.assertEqual(failure.exception.code, 'preparation-inputs-' + reason)
            (self.root / template).write_bytes(original)
        self.edit(template, lambda d: d['Resources'].update(RenamedBudget=d['Resources'].pop('Budget')))
        self.assertEqual(self.resolve()['budget']['BudgetLimit']['Amount'], 100)

    def test_database_settings_follow_supplier_declarations(self):
        source = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        def change(document):
            document['Resources']['PersistenceDatabase']['Properties']['DBName'] = 'another_database'
            secret = document['Resources'].pop('MigrationCredentialsSecret')
            secret['Properties']['Name'] = 'another/admin.secret+name'
            document['Resources']['RenamedAdministratorSecret'] = secret
            for output in ('AdministratorCredentialsSecretArn', 'MigrationCredentialsSecretArn'):
                document['Outputs'][output]['Value'] = {'Ref':'RenamedAdministratorSecret'}
            document['Resources']['SecretsManagerEndpoint']['Properties']['PolicyDocument']['Statement'][0]['Resource'] = [{'Ref':'RenamedAdministratorSecret'}]
        self.edit(source, change)
        caller = self.imported(self.root / self.callers['entity-smoke'])
        self.assertIsNone(caller.INPUT_ERROR)
        expected = caller.DATABASE_BINDING
        self.assertEqual((expected['database_name'], expected['engine'], expected['administrator_secret_name']),
                         ('another_database', 'postgres', 'another/admin.secret+name'))
        database = {'DBInstanceIdentifier':caller.DATABASE, 'DBInstanceStatus':'available', 'Engine':'postgres', 'EngineVersion':'18.3',
                    'StorageEncrypted':True, 'PubliclyAccessible':False, 'IAMDatabaseAuthenticationEnabled':True,
                    'DbiResourceId':'db-ABC123', 'DBName':'another_database',
                    'VpcSecurityGroups':[{'Status':'active', 'VpcSecurityGroupId':'sg-fixture'}],
                    'DBSubnetGroup':{'SubnetGroupStatus':'Complete', 'DBSubnetGroupName':'fixture'},
                    'DBParameterGroups':[{'ParameterApplyStatus':'in-sync'}], 'Endpoint':{'Address':'fixture.internal', 'Port':5432}}
        secret = 'arn:aws:secretsmanager:' + caller.REGION + ':' + caller.ACCOUNT + ':secret:another/admin.secret+name-aBc123'
        self.assertEqual(caller.database_facts(database, secret)['DatabaseName'], 'another_database')
        for field, value, code in [('DBName','kanbienpersistence','alignment-dependency-name-not-confirmed'),
                                   ('Engine','mysql','alignment-engine-not-confirmed')]:
            with self.assertRaises(caller.AlignmentFailure) as failure: caller.database_facts({**database, field:value}, secret)
            self.assertEqual(failure.exception.code, code)
        with self.assertRaises(caller.AlignmentFailure) as failure:
            caller.database_facts(database, secret.replace('admin.secret+name', 'adminXsecrettname'))
        self.assertEqual(failure.exception.code, 'alignment-administrative-reference-not-confirmed')

    def test_invalid_database_declarations_stop_before_provider_work(self):
        source = self.base + '/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
        original = (self.root / source).read_bytes()
        for field, reason in [('DBName','name'), ('Engine','engine')]:
            for value in (None, '', [], {'Ref':'Unknown'}, 'private-canary!'):
                with self.subTest(field=field, value=value):
                    self.edit(source, lambda d: d['Resources']['PersistenceDatabase']['Properties'].update({field:value}))
                    caller = self.imported(self.root / self.callers['entity-smoke'])
                    self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-dependency-' + reason + '-unsupported')
                    with self.assertRaises(caller.AlignmentFailure) as failure:
                        caller.inspect(lambda *a, **kw: self.fail('provider invoked'), {}, 'unused')
                    self.assertEqual(failure.exception.code, caller.INPUT_ERROR)
                    (self.root / source).write_bytes(original)
        cases = [
            (lambda d: d['Outputs'].pop('AdministratorCredentialsSecretArn'), 'administrator-output'),
            (lambda d: d['Outputs']['AdministratorCredentialsSecretArn'].update(Value={'Ref':'Missing'}), 'administrator-secret'),
            (lambda d: d['Resources']['MigrationCredentialsSecret'].update(Type='Other'), 'administrator-secret'),
        ]
        cases.extend((lambda d, value=value: d['Resources']['MigrationCredentialsSecret']['Properties'].update(Name=value), 'administrator-name')
                     for value in (None, '', [], {'Ref':'Unknown'}, 'private-canary!'))
        for mutation, reason in cases:
            with self.subTest(reason=reason):
                self.edit(source, mutation)
                caller = self.imported(self.root / self.callers['entity-smoke'])
                self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-dependency-' + reason + '-unsupported')
                with self.assertRaises(caller.AlignmentFailure) as failure:
                    caller.inspect(lambda *a, **kw: self.fail('provider invoked'), {}, 'unused')
                self.assertNotIn('private-canary', str(failure.exception))
                (self.root / source).write_bytes(original)

    def test_invalid_input_reaches_both_callers_before_provider_work(self):
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d['provider'].update(account_id='private-canary-never-report'))
        self.assert_preparation_failure('preparation-inputs-account-invalid')

    def assert_preparation_failure(self, code, scopes=None):
        scopes = list(self.callers) if scopes is None else scopes
        for scope in scopes:
            relative = self.base + '/20-scopes/' + scope + '/00-declaration/declaration-contract.yml'
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            report = self.owner.PATHS.inspect(destination, self.root, {'schema': 'repo/check-catalog/v1', 'checks': {}}, probe_commands=False)
            self.assertIn({'code': code}, report['findings'])
            self.assertNotIn('private-canary', json.dumps(report))
        for scope in scopes:
            path = self.callers[scope]
            caller = self.imported(self.root / path)
            self.assertEqual(caller.INPUT_ERROR, code)
            with patch.object(subprocess, 'run', side_effect=AssertionError('provider must not run')):
                if scope == 'entity-smoke':
                    with self.assertRaises(caller.AlignmentFailure) as failure:
                        caller.read_receipt(self.root / 'unused')
                    self.assertEqual(str(failure.exception), code)
                    with self.assertRaises(caller.AlignmentFailure):
                        caller.inspect(lambda *a, **kw: self.fail('provider invoked'), {}, 'unused')
                else:
                    with patch('sys.argv', ['prepare', '--receipt', str(self.root / 'unused')]), contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(caller.main(), 1)
                    self.assertEqual(json.loads(output.getvalue())['findings'], [{'code': code}])
                    self.assertNotIn('private-canary', output.getvalue())
                    self.assertEqual(caller.aws('sts', 'get-caller-identity'), (False, None, code))

    def rename_source_target(self, replacement, scope):
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d.update(id=replacement))
        self.edit(self.base + '/10-foundation/budget-control.yml', lambda d: d.update(target=replacement))
        self.edit(self.base + '/10-foundation/budget-control.yml',
                  lambda d: d['expected_provider_configuration'].update(budget_name=replacement + '-monthly', target_filter='user:Target$' + replacement))
        for template in ('foundation', 'core-server-persistence', 'entity-smoke'):
            self.edit(self.base + '/30-provider-realization/aws/cloudformation/' + template + '.yml',
                      lambda d: d['Parameters']['ResourceNamePrefix'].update(Default=replacement))
        for selected in self.callers:
            self.edit(self.base + '/20-scopes/' + selected + '/10-workload-binding/workload-binding.yml',
                      lambda d: d.update(target=replacement, scope=scope if d['scope'] == 'entity-smoke' else d['scope']))
        self.edit(self.base + '/40-package-custody/github-actions/pipeline-index.yml',
                  lambda d: d['pipelines'][0].update(used_by_scopes=[scope]))
        (self.root / self.base / '20-scopes/entity-smoke').rename(self.root / self.base / '20-scopes' / scope)
        (self.root / self.base).rename(self.root / 'infra/04.deploy/03.product/targets' / replacement)

    def test_differently_named_target_and_scope_need_no_resolver_changes(self):
        replacement, scope = 'another-target', 'another-feature'
        self.rename_source_target(replacement, scope)
        result = self.owner.load(self.root, replacement, scope)
        self.assertEqual((result['target'], result['scope']), (replacement, scope))
        self.assertEqual(result['dependencies']['database']['identifier'], replacement + '-persistence')

    def test_missing_ambiguous_mismatched_and_unsupported_selections(self):
        pipeline = self.base + '/40-package-custody/github-actions/pipeline-index.yml'
        binding = self.base + '/20-scopes/entity-smoke/10-workload-binding/workload-binding.yml'
        program = 'infra/04.deploy/03.product/entrypoints/runnable-program-index.yml'
        profile = self.base + '/00-target/target-profile.yml'
        foundation = self.base + '/30-provider-realization/aws/cloudformation/foundation.yml'
        cases = [
            (foundation, lambda d: d['Outputs']['ClusterArn'].update(Value='private-canary'), 'foundation-output-unsupported'),
            (foundation, lambda d: d['Resources']['Cluster'].update(Type='Other'), 'foundation-resource-unsupported'),
            (foundation, lambda d: d['Resources']['Cluster']['Properties'].update(ClusterName={'Ref':'Other'}), 'foundation-cluster-unsupported'),
            (foundation, lambda d: d['Resources']['LogGroup']['Properties'].update(LogGroupName=None), 'foundation-log-group-unsupported'),
            (foundation, lambda d: d['Resources']['BootstrapServiceDiscovery']['Properties']['DnsConfig'].update(NamespaceId='private-canary'), 'foundation-namespace-unsupported'),
            (foundation, lambda d: d['Resources']['Namespace'].update(Type='AWS::ServiceDiscovery::PublicDnsNamespace'), 'foundation-namespace-unsupported'),
            (foundation, lambda d: d['Resources']['Namespace']['Properties'].update(Name=None), 'foundation-namespace-unsupported'),
            (pipeline, lambda d: d['pipelines'].append(copy.deepcopy(d['pipelines'][0])), 'pipeline-ambiguous'),
            (pipeline, lambda d: d['pipelines'].pop(0), 'pipeline-missing'),
            (pipeline, lambda d: d['pipelines'][0].update(used_by_scopes=[]), 'pipeline-scope-mismatch'),
            (pipeline, lambda d: d['pipelines'][0].update(provider_region_alias='aws-other'), 'pipeline-region-mismatch'),
            (binding, lambda d: d.update(scope='other'), 'binding-mismatch'),
            (binding, lambda d: d.update(image_contract='../private-canary'), 'path-invalid'),
            (binding, lambda d: d['proposed_provider_binding'].pop('publication_pipeline'), 'pipeline-selection-invalid'),
            (binding, lambda d: d['proposed_provider_binding']['dependencies']['database'].update(output='MissingOutput'), 'dependency-output-unsupported'),
            (program, lambda d: d['package_candidates'].append(copy.deepcopy(d['package_candidates'][-1])), 'candidate-ambiguous'),
            (profile, lambda d: d['provider'].update(profile=''), 'profile-invalid'),
            (profile, lambda d: d['provider'].update(region=None), 'region-invalid'),
            (profile, lambda d: d['provider'].update(family='other'), 'provider-unsupported'),
        ]
        for name, change, reason in cases:
            path = self.root / name
            before = path.read_bytes()
            with self.subTest(reason=reason):
                try:
                    self.edit(name, change)
                    with self.assertRaises(self.owner.InputFailure) as failure: self.resolve()
                    self.assertEqual(str(failure.exception), 'preparation-inputs-' + reason)
                finally: path.write_bytes(before)
        path = self.root / profile
        before = path.read_bytes()
        for raw in ['[', 'provider: null\nprovider: private-canary', '[]']:
            path.write_text(raw)
            with self.assertRaises(self.owner.InputFailure) as failure: self.resolve()
            self.assertEqual(str(failure.exception), 'preparation-inputs-document-invalid')
        path.unlink()
        with self.assertRaises(self.owner.InputFailure) as failure: self.resolve()
        self.assertEqual(str(failure.exception), 'preparation-inputs-source-unavailable')
        path.symlink_to(ROOT / profile)
        with self.assertRaises(self.owner.InputFailure) as failure: self.resolve()
        self.assertEqual(str(failure.exception), 'preparation-inputs-path-invalid')
        path.unlink()
        path.write_bytes(before)


class DeclaredTemplateTests(unittest.TestCase):
    # Captured before parameterization from explicit source 2220763a974580eb37d3c14f7e38075a4a9e47c7.
    # Compact sorted JSON preserves scalar types; these are not recomputed from
    # a moving checkout or from a second copy of the production templates.
    BASELINES = {
        'foundation': ('6e9bb7134d1aba5ca89e84c3184ec5856dbf761b63e1871947e2b5ba5b9ce612', '23aaa09d5e8f34a36be2fb2527f079178f69be7e20e73353d8cbd48a14802b16'),
        'core-server-persistence': ('d288a5e58533a1b68ea6e2e1665bad737d3b7857d2f266b557a3f404cfbeb2af', '6afa75446006003d92d925dd5fbe1e109c28e4155b99eda1aab7ab461d4b4c56'),
        'entity-smoke': ('db60be6bbf8b5bccb7bb9dd93c4bd405655830093fdc4201802063f2f0b7b736', '0ab4d047f7aa8527787a22847992e38d9e3cddd904b1ba4ae6ff2af34de6ddac'),
    }

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('declared_ecs', COMMAND.parent.parent / 'provider-adapters/aws/ecs-runtime-configuration.py')
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)
        spec = importlib.util.spec_from_file_location('declared_runtime', COMMAND.with_name('runtime_configuration.py'))
        cls.runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runtime)
        spec = importlib.util.spec_from_file_location('declared_cf', ROOT / 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py')
        cls.cf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cf)

    def source(self, name):
        path = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation' / (name + '.yml')
        return self.cf.template(path.read_text())

    def digest(self, value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()

    def assert_default_preserved(self, name, source):
        controls = {'foundation': {'EnableDeliveryRole': {'Type': 'String', 'Default': 'true', 'AllowedValues': ['true', 'false']}},
                    'core-server-persistence': {'ServerDesiredCount': {'Type': 'Number', 'Default': 1, 'AllowedValues': [0, 1]},
                        'ObservabilityCollectorDesiredCount': {'Type': 'Number', 'Default': 1, 'AllowedValues': [0, 1]},
                        'IncludeLegacyPasswordSecrets': {'Type': 'String', 'Default': 'true', 'AllowedValues': ['true', 'false']}},
                    'entity-smoke': {}}[name]
        guards = {'foundation': ['CreateDeliveryRole'], 'core-server-persistence': ['CreateLegacyPasswordSecrets'], 'entity-smoke': []}[name]
        for key, expected in controls.items():
            self.assertEqual(self.digest(source['Parameters'][key]), self.digest(expected))
        projected = self.cf.project_parameters(source, ['ResourceNamePrefix', *controls], condition_names=guards)
        self.assertEqual(self.digest({key: projected.get(key, {}) for key in ('Resources', 'Outputs', 'Conditions')}), self.BASELINES[name][0])
        # The two accepting identity patterns are intentionally widened and
        # checked separately below; every other old parameter stays identical.
        accepting = set() if name == 'foundation' else {'ClusterArn', 'LogGroupName'}
        for key in accepting:
            declaration = projected['Parameters'][key]
            self.assertEqual(set(declaration), {'Type', 'AllowedPattern'})
            self.assertEqual(declaration['Type'], 'String')
        unchanged = {key: value for key, value in projected['Parameters'].items()
                     if key != 'ResourceNamePrefix' and key not in accepting and key not in controls}
        self.assertEqual(self.digest(unchanged), self.BASELINES[name][1])

    def assert_instance_identity(self, source, prefix):
        projected = self.cf.project_string_parameters(source, ['ResourceNamePrefix'], {'ResourceNamePrefix': prefix})
        identities = {}
        fields = {'AWS::ECS::Cluster': 'ClusterName', 'AWS::Logs::LogGroup': 'LogGroupName',
                  'AWS::ServiceDiscovery::PrivateDnsNamespace': 'Name', 'AWS::IAM::Role': 'RoleName',
                  'AWS::SecretsManager::Secret': 'Name', 'AWS::RDS::DBInstance': 'DBInstanceIdentifier',
                  'AWS::ECS::TaskDefinition': 'Family', 'AWS::ECS::Service': 'ServiceName',
                  'AWS::CloudWatch::Alarm': 'AlarmName', 'AWS::SNS::Topic': 'TopicName'}
        for name, resource in projected['Resources'].items():
            properties = resource['Properties']; field = fields.get(resource['Type'])
            if field and field in properties:
                value = properties[field]
                self.assertIsInstance(value, str)
                self.assertIn(prefix, value)
                if resource['Type'] == 'AWS::IAM::Role': self.assertLessEqual(len(value), 64)
                identities[(name, field)] = value
            if resource['Type'] == 'AWS::Budgets::Budget':
                self.assertEqual(properties['Budget']['BudgetName'], prefix + '-monthly')
                self.assertEqual(properties['Budget']['CostFilters'], {'TagKeyValue': ['user:Target$' + prefix]})
                identities[(name, 'BudgetName')] = properties['Budget']['BudgetName']
            for tag in properties.get('Tags', []):
                if tag['Key'] == 'Target': self.assertEqual(tag['Value'], prefix)
        def visit(value):
            if isinstance(value, dict):
                if value.get('Name') in ('PLATFORM_OBSERVABILITY_TARGET', 'PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT', 'target'):
                    self.assertEqual(value['Value'], prefix)
                for item in value.values(): visit(item)
            elif isinstance(value, list):
                for item in value: visit(item)
            elif isinstance(value, str) and value.startswith('http://') and '.internal' in value:
                self.assertIn('.' + prefix + '.internal:', value)
        visit(projected['Resources'])
        self.assertTrue(identities)
        return identities

    def test_named_instances_preserve_all_default_resources_and_parameters(self):
        for name in self.BASELINES:
            with self.subTest(name=name): self.assert_default_preserved(name, self.source(name))

    def test_two_prefixes_isolate_names_private_urls_tags_and_metrics(self):
        for name in self.BASELINES:
            source = self.source(name)
            with self.subTest(name=name):
                first = self.assert_instance_identity(source, 'session-one')
                second = self.assert_instance_identity(source, 'session-two')
                self.assertEqual(set(first), set(second))
                self.assertTrue(set(first.values()).isdisjoint(second.values()))
                self.assert_instance_identity(source, 'a' * 21)

    def test_prefix_constraints_and_accepting_cluster_log_patterns(self):
        import re
        declaration = {'Type': 'String', 'Default': 'kanbien-core-platform', 'MinLength': 1,
                       'MaxLength': 21, 'AllowedPattern': '^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$'}
        for name in self.BASELINES:
            source = self.source(name)
            self.assertEqual(source['Parameters']['ResourceNamePrefix'], declaration)
            for prefix in ('a', 'a' * 21, 'session-one'):
                self.assert_instance_identity(source, prefix)
            for prefix in ('', 'a' * 22, 'Upper', '-leading', 'trailing-', 'two--hyphens', 'with.dot', '${AWS::Region}'):
                with self.subTest(name=name, prefix=prefix), self.assertRaises(ValueError):
                    self.cf.project_string_parameters(source, ['ResourceNamePrefix'], {'ResourceNamePrefix': prefix})
            if name == 'foundation': continue
            for parameter, base in [('ClusterArn', 'arn:aws:ecs:eu-west-1:337159794548:cluster/'), ('LogGroupName', '/aws/ecs/')]:
                pattern = source['Parameters'][parameter]['AllowedPattern']
                region = 'eu-west-1' if name == 'entity-smoke' else '[a-z0-9-]+'
                head = '^/aws/ecs/' if parameter == 'LogGroupName' else '^arn:aws:ecs:' + region + ':[0-9]{12}:cluster/'
                self.assertEqual(pattern, head + '(?=[a-z0-9-]{1,21}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
                for prefix in ('a', 'a' * 21, 'session-one'):
                    self.assertIsNotNone(re.fullmatch(pattern, base + prefix))
                for prefix in ('', 'a' * 22, 'Upper', 'two--hyphens', 'trailing-', 'with.dot'):
                    self.assertIsNone(re.fullmatch(pattern, base + prefix))

    def test_default_and_isolation_assertions_detect_semantic_counterexamples(self):
        changes = [
            ('foundation', lambda d: d['Resources'].pop('Cluster')),
            ('foundation', lambda d: d['Resources'].update(Extra={'Type': 'AWS::ECS::Cluster'})),
            ('foundation', lambda d: d['Outputs']['VpcId'].update(Value='vpc-other')),
            ('foundation', lambda d: d['Resources']['EcrApiEndpoint']['Properties'].update(PrivateDnsEnabled=1)),
            ('core-server-persistence', lambda d: d['Resources']['PersistenceDatabase'].update(DeletionPolicy='Delete')),
            ('core-server-persistence', lambda d: d['Resources']['CoreServerPersistenceService']['Properties'].update(DesiredCount=0)),
            ('entity-smoke', lambda d: d['Parameters']['ServerDesiredCount'].update(Default=1)),
            ('foundation', lambda d: d['Parameters'].update(ClusterArn={'Type': 'String'})),
            ('foundation', lambda d: d['Parameters'].update(LogGroupName={'Type': 'String'})),
            ('core-server-persistence', lambda d: d['Parameters']['ClusterArn'].update(Type='Number')),
            ('core-server-persistence', lambda d: d['Parameters']['ClusterArn'].update(Default='another-cluster')),
            ('entity-smoke', lambda d: d['Parameters']['LogGroupName'].update(NoEcho=True)),
        ]
        for name, mutate in changes:
            source = self.source(name); mutate(source)
            with self.subTest(name=name), self.assertRaises(AssertionError): self.assert_default_preserved(name, source)
        for mutate in (
            lambda d: d['Resources']['Cluster']['Properties'].update(ClusterName='kanbien-core-platform'),
            lambda d: d['Resources']['Cluster']['Properties'].update(Tags=[{'Key': 'Target', 'Value': 'kanbien-core-platform'}]),
        ):
            source = self.source('foundation'); mutate(source)
            with self.assertRaises(AssertionError): self.assert_instance_identity(source, 'session-one')

    def test_real_bindings_share_adapter_and_keep_database_routes_distinct(self):
        target = ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform'
        for scope in ('core-server-persistence', 'entity-smoke'):
            with self.subTest(scope=scope):
                directory = target / '20-scopes' / scope
                binding = yaml.safe_load((directory / '10-workload-binding/workload-binding.yml').read_text())
                contract = yaml.safe_load((directory / '00-declaration/declaration-contract.yml').read_text())
                image = yaml.safe_load((ROOT / binding['image_contract']).read_text())
                selected = binding['proposed_provider_binding']
                self.assertEqual(selected['configuration_adapter'], str(Path(self.adapter.__file__).relative_to(ROOT)))
                template = target / selected['template']
                facts = self.adapter.normalize(template, binding)
                self.assertEqual(set(facts), {item['id'] for item in binding['workloads']})
                self.assertEqual(self.runtime.inspect(contract, binding, image, template, ROOT), [])
                if scope == 'entity-smoke':
                    self.assertEqual(facts['entity-smoke-restore-reader-task'][0]['environment']['PERSISTENCE_POSTGRES_HOST'], {'Fn::GetAtt': 'RestoredDatabase.Endpoint.Address'})
                    self.assertEqual(facts['entity-smoke-database-proof-task'][0]['environment']['PERSISTENCE_POSTGRES_HOST'], {'Ref': 'DatabaseEndpoint'})
                    self.assertFalse(any(name.startswith('PERSISTENCE_') for name in facts['entity-smoke-verifier-task'][0]['environment']))

    def test_different_workload_names_and_explicit_sibling_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in [('main.yml', 'source'), ('reader.yml', 'restored')]:
                (root / name).write_text(yaml.safe_dump({'Resources': {'Task': {'Type': 'AWS::ECS::TaskDefinition', 'Properties': {'ContainerDefinitions': [{'Name': 'different-container', 'Environment': [{'Name': 'DATABASE', 'Value': value}], 'Command': ['different-program.js']}]}}}}))
            binding = {'target': 'different-target', 'scope': 'different-scope', 'workloads': [
                {'id': 'writer', 'provider_reference': 'Task'},
                {'id': 'reader', 'provider_reference': 'Task', 'provider_template': 'reader.yml'}]}
            facts = self.adapter.normalize(root / 'main.yml', binding)
            self.assertEqual(facts['writer'][0]['environment'], {'DATABASE': 'source'})
            self.assertEqual(facts['reader'][0]['environment'], {'DATABASE': 'restored'})
            projection = self.adapter.package_projection(root / 'main.yml', '*')
            self.assertEqual(projection['containers']['Task']['ContainerDefinitions'][0]['Environment'], [{'Name': 'DATABASE', 'Value': 'source'}])
            for invalid in ('', None, False, [], {}, '../reader.yml', '/tmp/private-canary', 'nested/reader.yml', 'missing.yml', 'a\\b', '.'):
                with self.subTest(invalid=invalid):
                    changed = copy.deepcopy(binding)
                    changed['workloads'][1]['provider_template'] = invalid
                    with self.assertRaisesRegex(ValueError, '^workload-template-invalid$'):
                        self.adapter.normalize(root / 'main.yml', changed)
                    changed['runtime_requirements'] = [{'workload': 'reader'}]
                    changed['proposed_provider_binding'] = {'configuration_adapter': str(Path(self.adapter.__file__).relative_to(ROOT))}
                    self.assertEqual(self.runtime.inspect({}, changed, {}, root / 'main.yml', ROOT), [{'code': 'runtime-provider-configuration-invalid'}])
            duplicate = copy.deepcopy(binding)
            duplicate['workloads'][1]['id'] = 'writer'
            with self.assertRaisesRegex(ValueError, '^workload-binding-invalid$'):
                self.adapter.normalize(root / 'main.yml', duplicate)
            for workloads in ([], None, {}, [None], [{'id': ''}], [{'id': 'writer', 'provider_reference': 'absent-private-canary'}]):
                with self.subTest(workloads=workloads):
                    changed = {'workloads': workloads, 'runtime_requirements': [{'workload': 'writer'}], 'proposed_provider_binding': {'configuration_adapter': str(Path(self.adapter.__file__).relative_to(ROOT))}}
                    self.assertEqual(self.runtime.inspect({}, changed, {}, root / 'main.yml', ROOT), [{'code': 'runtime-provider-configuration-invalid'}])
            (root / 'linked.yml').symlink_to(root / 'reader.yml')
            binding['workloads'][1]['provider_template'] = 'linked.yml'
            with self.assertRaisesRegex(ValueError, '^workload-template-invalid$'):
                self.adapter.normalize(root / 'main.yml', binding)
            with self.assertRaisesRegex(ValueError, '^workload-template-invalid$'):
                self.adapter.normalize(root / 'linked.yml', {'workloads': [binding['workloads'][0]]})
            (root / 'linked-directory').symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, '^workload-template-invalid$'):
                self.adapter.normalize(root / 'linked-directory/main.yml', {'workloads': [binding['workloads'][0]]})


class RuntimeConfigurationTests(unittest.TestCase):
    def test_b10_rejected_reference_projection(self):
        spec=importlib.util.spec_from_file_location('b10_coverage', COMMAND)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        canary='https://private.invalid/reference-canary'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); contract=root/'contract.yml'
            contract.write_text(yaml.safe_dump({'schema':'deploy/declaration-contract/v1','id':canary,'target':{'profile':canary},'requirements':[{'id':'requirement','required_by':[canary],'declarations':[{'path':{'private':canary},'expectation':'exists'}]}]}))
            report=module.inspect_declaration(contract,root,{})
            self.assertEqual(report['scope'],'invalid-scope'); self.assertEqual(report['target'],'invalid-target')
            self.assertNotIn(canary,json.dumps(report)); self.assertIn('invalid-reference',json.dumps(report))
            contract.write_text(yaml.safe_dump({'schema':'deploy/target-scope-contract/v1','target':canary,'scope':canary,'change_impact':{'schema':'deploy/change-impact/v1','inputs':[canary],'requirements':[{'id':'requirement','required_by':[canary],'declarations':[canary],'local_proofs':[],'package_proofs':[],'target_proofs':[],'run_proofs':[]}]}}))
            report=module.inspect(contract,root,{})
            self.assertNotIn(canary,json.dumps(report)); self.assertEqual(report['inputs'],[]); self.assertEqual(report['consumers'],[])
            # A lexically valid but out-of-root symlink was rejected by within;
            # it must not reappear through consumers, inputs or target fields.
            with tempfile.TemporaryDirectory() as external:
                rejected='linked-private'; (root/rejected).symlink_to(Path(external),target_is_directory=True)
                legacy={'schema':'deploy/declaration-contract/v1','id':'Scope_With.Dots','target':{'profile':rejected},'requirements':[{'id':'requirement','required_by':[rejected,'missing/local-file.py'],'declarations':[{'path':rejected,'expectation':'exists'}]}]}
                contract.write_text(yaml.safe_dump(legacy)); report=module.inspect_declaration(contract,root,{})
                self.assertNotIn(rejected,json.dumps(report)); self.assertEqual(report['scope'],'Scope_With.Dots')
                self.assertIn('missing/local-file.py',report['consumers']); self.assertIn({'code':'requirement-implementation-missing','reference':'missing/local-file.py'},report['findings'])
                current={'schema':'deploy/target-scope-contract/v1','target':'Target_With.Dots','scope':'Scope_With.Dots','change_impact':{'schema':'deploy/change-impact/v1','inputs':[rejected,'missing/local-file.py'],'requirements':[{'id':'requirement','required_by':[rejected,'missing/local-file.py'],'declarations':[rejected],'local_proofs':[],'package_proofs':[],'target_proofs':[],'run_proofs':[]}]}}
                contract.write_text(yaml.safe_dump(current)); report=module.inspect(contract,root,{})
                self.assertNotIn(rejected,json.dumps(report)); self.assertEqual(report['scope'],'Scope_With.Dots'); self.assertEqual(report['target'],'Target_With.Dots')
                self.assertEqual(report['inputs'],['missing/local-file.py']); self.assertEqual(report['consumers'],['missing/local-file.py'])

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

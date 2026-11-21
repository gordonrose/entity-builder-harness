#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runtime-configuration
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-16"
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
import io
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
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
        paths = {self.owner_path, *self.callers.values(),
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
        for scope in self.callers:
            relative = self.base + '/20-scopes/' + scope + '/00-declaration/declaration-contract.yml'
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            report = self.owner.PATHS.inspect(destination, self.root, {'schema': 'repo/check-catalog/v1', 'checks': {}}, probe_commands=False)
            self.assertIn({'code': 'preparation-inputs-account-invalid'}, report['findings'])
            self.assertNotIn('private-canary', json.dumps(report))
        for scope, path in self.callers.items():
            caller = self.imported(self.root / path)
            self.assertEqual(caller.INPUT_ERROR, 'preparation-inputs-account-invalid')
            with patch.object(subprocess, 'run', side_effect=AssertionError('provider must not run')):
                if scope == 'entity-smoke':
                    with self.assertRaises(caller.AlignmentFailure) as failure:
                        caller.read_receipt(self.root / 'unused')
                    self.assertEqual(str(failure.exception), 'preparation-inputs-account-invalid')
                    with self.assertRaises(caller.AlignmentFailure):
                        caller.inspect(lambda *a, **kw: self.fail('provider invoked'), {}, 'unused')
                else:
                    with patch('sys.argv', ['prepare', '--receipt', str(self.root / 'unused')]), contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(caller.main(), 1)
                    self.assertEqual(json.loads(output.getvalue())['findings'], [{'code': 'preparation-inputs-account-invalid'}])
                    self.assertNotIn('private-canary', output.getvalue())
                    self.assertEqual(caller.aws('sts', 'get-caller-identity'), (False, None, 'preparation-inputs-account-invalid'))

    def test_differently_named_target_and_scope_need_no_resolver_changes(self):
        replacement = 'another-target'
        scope = 'another-feature'
        self.edit(self.base + '/00-target/target-profile.yml', lambda d: d.update(id=replacement))
        self.edit(self.base + '/10-foundation/budget-control.yml', lambda d: d.update(target=replacement))
        for selected in self.callers:
            self.edit(self.base + '/20-scopes/' + selected + '/10-workload-binding/workload-binding.yml',
                      lambda d: d.update(target=replacement, scope=scope if d['scope'] == 'entity-smoke' else d['scope']))
        self.edit(self.base + '/40-package-custody/github-actions/pipeline-index.yml',
                  lambda d: d['pipelines'][0].update(used_by_scopes=[scope]))
        (self.root / self.base / '20-scopes/entity-smoke').rename(self.root / self.base / '20-scopes' / scope)
        (self.root / self.base).rename(self.root / 'infra/04.deploy/03.product/targets' / replacement)
        result = self.owner.load(self.root, replacement, scope)
        self.assertEqual((result['target'], result['scope']), (replacement, scope))
        self.assertEqual(result['dependencies']['database']['identifier'], 'kanbien-core-platform-persistence')

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
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('declared_ecs', COMMAND.parent.parent / 'provider-adapters/aws/ecs-runtime-configuration.py')
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)
        spec = importlib.util.spec_from_file_location('declared_runtime', COMMAND.with_name('runtime_configuration.py'))
        cls.runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runtime)

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

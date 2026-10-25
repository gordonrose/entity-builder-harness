#!/usr/bin/env python3
"""Run real persistence proof controllers against explicitly simulated observations."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.fixture.persistence-acceptance-controller-captures
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: fixture
#   purpose: Exercise actual controller parsers and retained receipt writes with controlled provider responses in an isolated temporary rehearsal root.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only, writes-files]
from __future__ import annotations
import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import yaml

SOURCE = Path(__file__).resolve().parents[8]
RUN = Path('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence')
SCOPE = Path('infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence')
TASK_PREFIX = 'arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/'
DEFINITION_PREFIX = 'arn:aws:ecs:eu-west-1:337159794548:task-definition/'
REPOSITORY = '337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server'


def load(path: Path):
    spec = importlib.util.spec_from_file_location('fixture_' + path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def timestamp(value: datetime) -> str:
    return value.isoformat().replace('+00:00', 'Z')


def invoke(controller, argv: list[str]) -> dict:
    output = io.StringIO()
    with patch.object(sys, 'argv', ['controller-fixture', *argv]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        status = controller.main()
    reports = [json.loads(line) for line in output.getvalue().splitlines() if line.startswith('{')]
    if status != 0 or not reports or reports[-1].get('verdict') not in {'accepted', 'replaced'}:
        raise AssertionError({'controller': controller.__file__, 'exit_code': status, 'reports': reports})
    return reports[-1]


def capture_proofs(root: Path) -> dict:
    """Return simulated proofs created by production controllers, never live evidence."""
    root = root.resolve()
    if root == SOURCE.resolve() or not root.is_relative_to(Path(tempfile.gettempdir()).resolve()) or root.is_symlink():
        raise ValueError('controller-fixtures-require-isolated-temporary-root')
    root.mkdir(parents=True, exist_ok=True)
    destination = root / SCOPE / '30-release-evidence/proof-receipts'
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('controller-fixtures-require-empty-receipt-destination')
    receipt_module = load(SOURCE / RUN / 'proof-receipts.py')
    receipt_module.ROOT = root
    receipt_module.RECEIPTS = destination
    receipt_module.EVIDENCE_CLASS = 'simulated'
    route = yaml.safe_load((SOURCE / SCOPE / '00-declaration/acceptance-route-contract.yml').read_text())
    candidate, rollback = 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64
    begin = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=2)
    snapshot = 'kanbien-core-platform-persistence-recovery-' + begin.strftime('%Y%m%d') + '-r1'
    captures: dict[str, str] = {}
    observations: list[tuple[str, ...]] = []
    original_arn = successor_arn = None

    def task(number: int, family: str, start: datetime, container: str) -> dict:
        return {'taskArn': TASK_PREFIX + f'{number:032x}', 'taskDefinitionArn': DEFINITION_PREFIX + family + ':7',
                'lastStatus': 'STOPPED', 'startedAt': timestamp(start), 'stoppedAt': timestamp(start + timedelta(seconds=2)),
                'containers': [{'name': container, 'exitCode': 0}], 'stoppedReason': 'Essential container in task exited'}

    def task_capture(name: str, proof: dict, number: int, start: datetime) -> str:
        kind, mode = proof['proof_type'], proof['operation']
        controller_name = 'run-migration' if kind == 'migration' else 'verify-candidate'
        container = 'persistence-migration' if kind == 'migration' else 'private-persistence-verifier'
        controller = load(SOURCE / RUN / controller_name / 'script.py')
        deadline = controller.deadline()
        if type(deadline) is not int or deadline <= 0: raise AssertionError('owner completion deadline unavailable')
        observed = task(number, proof['family'], start, container)
        environment = {'PERSISTENCE_MIGRATION_OPERATION': mode} if kind == 'migration' else {'PERSISTENCE_VERIFIER_MODE': mode, 'PERSISTENCE_ACCEPTANCE_RECORD_ID': controller.RECORD_ID, 'PERSISTENCE_ACCEPTANCE_FACT': controller.FACT}
        observed['overrides'] = {'containerOverrides': [{'name': container, 'environment': [{'name': key, 'value': value} for key, value in environment.items()]}], 'inferenceAcceleratorOverrides': []}
        digest = candidate if proof['image_role'] == 'candidate' else rollback
        definition = {'family': proof['family'], 'taskDefinitionArn': observed['taskDefinitionArn'], 'containerDefinitions': [{'name': container, 'image': REPOSITORY + '@' + digest, 'environment': [], 'secrets': []}]}
        def aws(*parts):
            observations.append(parts)
            if parts[1] == 'describe-tasks':
                assert parts[-1] == observed['taskArn']
                return True, {'tasks': [observed]}, 'ok'
            if parts[1] == 'describe-task-definition':
                return True, {'taskDefinition': definition}, 'ok'
            if parts[1] == 'get-log-events':
                return True, {'events': [{'message': json.dumps({'verdict': 'accepted', 'code': proof['result_code']})}]}, 'ok'
            raise AssertionError('unexpected provider action: ' + str(parts))
        output_key = 'CoreServerPersistenceMigrationTaskDefinitionArn' if kind == 'migration' else 'CoreServerPersistenceVerifierTaskDefinitionArn'
        outputs = {output_key: DEFINITION_PREFIX + proof['family'] + ':99', 'PersistenceMigrationSecurityGroupId': 'sg-fixture', 'PrivateSubnetIds': 'subnet-fixture', 'VerifierSecurityGroupId': 'sg-fixture'}
        flag = '--migration-operation' if kind == 'migration' else '--mode'
        with patch.object(controller, 'ROOT', root), patch.object(controller, 'proof_receipts', return_value=receipt_module), patch.object(controller, 'deadline', return_value=deadline), patch.object(controller, 'outputs', return_value=(outputs, 'ok')), patch.object(controller, 'qualified_digest', return_value=digest), patch.object(controller, 'aws', side_effect=aws):
            report = invoke(controller, [flag, mode, '--capture-completed-task', observed['taskArn'], '--qualified-receipt', str(root / ('qualified-' + proof['image_role'] + '.json')), '--json'])
        return str(root / report['facts']['proof_receipt'])

    record_proof = task_capture('retained-record', {'proof_type': 'verifier', 'operation': 'create', 'image_role': 'candidate', 'family': 'kanbien-core-platform-persistence-verifier', 'result_code': 'KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED'}, 1, begin - timedelta(minutes=1))
    for number, (name, proof) in enumerate(route['proofs'].items(), start=10):
        start = begin + timedelta(minutes=number - 10)
        if proof['proof_type'] in {'migration', 'verifier'}:
            captures[name] = task_capture(name, proof, number, start)
            continue
        if proof['proof_type'] == 'administration':
            controller = load(SOURCE / RUN / 'run-administration' / 'script.py')
            observed = task(number, proof['family'], start, 'persistence-administration')
            digest = candidate if proof['image_role'] == 'candidate' else rollback
            definition = {
                'taskDefinitionArn': observed['taskDefinitionArn'],
                'containerDefinitions': [
                    {
                        'name': 'persistence-administration',
                        'image': REPOSITORY + '@' + digest,
                    }
                ],
            }
            outputs = {
                'CoreServerPersistenceAdministrationTaskDefinitionArn': observed['taskDefinitionArn'],
                'PersistenceAdministrationSecurityGroupId': 'sg-fixture',
            }
            foundation = {'PrivateSubnetIds': 'subnet-fixture'}

            def aws(*parts):
                observations.append(parts)
                if parts[1] == 'describe-tasks':
                    assert parts[-1] == observed['taskArn']
                    return True, {'tasks': [observed]}, 'ok'
                if parts[1] == 'describe-task-definition':
                    return True, {'taskDefinition': definition}, 'ok'
                if parts[1] == 'get-log-events':
                    message = '{"verdict":"accepted","code":"' + proof['result_code'] + '"}'
                    return True, {'events': [{'message': message}]}, 'ok'
                raise AssertionError('unexpected provider action: ' + str(parts))

            def stack_outputs(name):
                if name == controller.STACK:
                    return outputs, 'ok'
                if name == controller.FOUNDATION:
                    return foundation, 'ok'
                raise AssertionError('unexpected stack output request: ' + name)

            with patch.object(controller, 'ROOT', root), \
                 patch.object(controller, 'RECEIPTS', receipt_module), \
                 patch.object(controller.MIGRATION, 'aws', side_effect=aws), \
                 patch.object(controller.MIGRATION, 'outputs', side_effect=stack_outputs):
                report = invoke(controller, [
                    '--operation', proof['operation'],
                    '--reconcile-task', observed['taskArn'],
                    '--json',
                ])
            captures[name] = str(root / report['facts']['proof_receipt'])
            continue
        if proof['proof_type'] == 'server-replacement':
            controller = load(SOURCE / RUN / 'rehearse-server-replacement/script.py')
            original = task(number, proof['family'], start, 'core-server-persistence')
            original.update(group='service:' + controller.SERVICE, stoppedReason='governed core-server-persistence replacement rehearsal')
            original['containers'][0]['exitCode'] = 137
            successor = task(1000 + number, proof['family'], start + timedelta(seconds=3), 'core-server-persistence')
            successor.update(group='service:' + controller.SERVICE, lastStatus='RUNNING')
            original_arn, successor_arn = original['taskArn'], successor['taskArn']
            definition = {'containerDefinitions': [{'image': REPOSITORY + '@' + candidate}]}
            def aws(*parts):
                observations.append(parts)
                if parts[1] == 'describe-tasks':
                    assert parts[-1] in {original_arn, successor_arn}
                    return True, {'tasks': [original if parts[-1] == original_arn else successor]}, 'ok'
                if parts[1] == 'describe-task-definition': return True, {'taskDefinition': definition}, 'ok'
                raise AssertionError('unexpected provider action: ' + str(parts))
            prepare = SimpleNamespace(aws=aws, REGION='eu-west-1', ACCOUNT='337159794548', validate_receipt=lambda _: {'image_digest': candidate, 'source_revision': 'a' * 40}, live_budget=lambda: (True, 'ok'))
            create = SimpleNamespace(package_gates=lambda _: True)
            with patch.object(controller, 'ROOT', root), patch.object(controller, 'proof_receipts', return_value=receipt_module), patch.object(controller, 'module', side_effect=[prepare, create]):
                report = invoke(controller, ['--receipt', str(root / 'qualified-candidate.json'), '--capture-completed-original-task', original_arn, '--capture-completed-successor-task', successor_arn, '--json'])
            captures[name] = str(root / report['facts']['proof_receipt'])
            continue
        if proof['proof_type'] != 'restore': raise AssertionError('unsupported fixture proof: ' + name)
        controller = load(SOURCE / RUN / 'rehearse-isolated-database-restore/script.py')
        restored_id = controller.restore_id(snapshot)
        source = {'DBInstanceIdentifier': controller.DATABASE, 'DBInstanceStatus': 'available', 'PubliclyAccessible': False, 'StorageEncrypted': True, 'IAMDatabaseAuthenticationEnabled': True, 'DBSubnetGroup': {'DBSubnetGroupName': 'fixture-private'}}
        restored = {**source, 'DBInstanceIdentifier': restored_id, 'DbiResourceId': 'db-FIXTURE-RESTORE', 'Engine': 'postgres', 'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-restored'}], 'Endpoint': {'Address': 'restored.fixture.invalid'}}
        observed = task(number, proof['family'], start, 'persistence-restoration-verifier')
        observed['startedBy'] = controller.restore_run_identity(restored)
        identity = controller.restore_identity_resource(restored)
        environment = {'PERSISTENCE_POSTGRES_HOST': 'restored.fixture.invalid', 'PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE': identity, 'PERSISTENCE_ACCEPTANCE_RECORD_ID': controller.RECORD_ID, 'PERSISTENCE_ACCEPTANCE_FACT_DIGEST': controller.FACT_DIGEST}
        observed['overrides'] = {'containerOverrides': [{'name': 'persistence-restoration-verifier', 'environment': [{'name': key, 'value': value} for key, value in environment.items()]}], 'inferenceAcceleratorOverrides': []}
        definition = {'containerDefinitions': [{'name': 'persistence-restoration-verifier', 'image': REPOSITORY + '@' + candidate, 'command': ['artifacts/kanbien-core-server-persistence-restore-verifier.main.js'], 'environment': [{'name': 'PERSISTENCE_POSTGRES_PORT', 'value': '5432'}, {'name': 'PERSISTENCE_POSTGRES_DATABASE', 'value': 'kanbienpersistence'}, {'name': 'PERSISTENCE_POSTGRES_SCHEMA', 'value': 'platform'}, {'name': 'PERSISTENCE_POSTGRES_IAM_REGION', 'value': 'eu-west-1'}, {'name': 'PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE', 'value': 'restoration-identity-supplied-at-governed-task-run'}, {'name': 'PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME', 'value': 'core_runtime'}], 'secrets': []}]}
        outputs = {'CoreServerPersistenceRestorationVerifierTaskDefinitionArn': observed['taskDefinitionArn'], 'PersistenceRestorationVerifierSecurityGroupId': 'sg-verifier', 'PersistenceRestoredDatabaseSecurityGroupId': 'sg-restored', 'PersistenceRestorationVerifierTaskRoleName': 'fixture-restoration-role', 'PrivateSubnetIds': 'subnet-fixture'}
        def aws(*parts):
            observations.append(parts)
            if parts[1] == 'describe-db-instances': return True, {'DBInstances': [source if parts[-1] == controller.DATABASE else restored]}, 'ok'
            if parts[1] == 'describe-services': return True, {'services': [{'desiredCount': 1, 'runningCount': 1}]}, 'ok'
            if parts[1] == 'describe-stacks': return True, {'Stacks': [{'Outputs': [{'OutputKey': key, 'OutputValue': value} for key, value in outputs.items()]}]}, 'ok'
            if parts[1] == 'describe-task-definition': return True, {'taskDefinition': definition}, 'ok'
            if parts[1] == 'list-tasks':
                assert '--started-by' not in parts
                return True, {'taskArns': [observed['taskArn']]}, 'ok'
            if parts[1] == 'describe-tasks': return True, {'tasks': [observed]}, 'ok'
            if parts[1] == 'get-log-events': return True, {'events': [{'message': json.dumps({'verdict': 'accepted', 'code': proof['result_code']})}]}, 'ok'
            if parts[1] == 'get-role-policy': return True, {'PolicyDocument': {'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Action': 'rds-db:connect', 'Resource': identity}]}}, 'ok'
            raise AssertionError('unexpected provider action: ' + str(parts))
        prepare = SimpleNamespace(aws=aws, live_budget=lambda: (True, 'ok'))
        with patch.object(controller, 'ROOT', root), patch.object(controller, 'EVIDENCE_CLASS', 'simulated'), patch.object(controller, 'proof_receipts', return_value=receipt_module), patch.object(controller, 'load', return_value=prepare):
            report = invoke(controller, ['--operation', 'verify', '--snapshot-id', snapshot, '--observe-only', '--json'])
        captures[name] = str(root / report['facts']['proof_receipt'])
    for path in [record_proof, *captures.values()]:
        value = receipt_module.validate(json.loads(Path(path).read_text()))
        assert value['provenance']['evidence_class'] == 'simulated'
    assert set(captures) == set(route['proofs'])
    return {'proof_receipts': captures, 'record_proof_receipt': record_proof, 'original_task': original_arn, 'successor_task': successor_arn,
            'candidate_digest': candidate, 'rollback_digest': rollback, 'recovery_snapshot': snapshot,
            'snapshot_created_at': timestamp(begin + timedelta(minutes=13)), 'observations': observations}

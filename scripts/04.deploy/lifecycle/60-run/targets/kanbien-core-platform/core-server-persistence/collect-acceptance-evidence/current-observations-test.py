#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-current-acceptance-observations
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject stale readiness, runtime overrides, wrong image/source and unsuitable recovery snapshots in fresh acceptance observations.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.persistence-acceptance-receipts
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/smoke-test.py
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('current_acceptance', Path(__file__).with_name('script.py'))
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
now = datetime.now(timezone.utc)
def stamp(delta): return (now + timedelta(seconds=delta)).isoformat().replace('+00:00', 'Z')
candidate = {'image_digest': 'sha256:' + 'a' * 64, 'source_revision': 'c' * 40}
child = 'sha256:' + 'b' * 64
image = f'{collector.ACCOUNT}.dkr.ecr.{collector.REGION}.amazonaws.com/kanbien-core-platform/core-server@{candidate["image_digest"]}'
arn = f'arn:aws:ecs:{collector.REGION}:{collector.ACCOUNT}:task/{collector.CLUSTER}/' + 'd' * 32
health_arn = arn[:-32] + 'e' * 32
server_definition = f'arn:aws:ecs:{collector.REGION}:{collector.ACCOUNT}:task-definition/kanbien-core-platform-core-server-persistence:10'
health_definition = server_definition.replace('core-server-persistence:10', 'persistence-verifier:11')
service = {'serviceName': collector.SERVICE, 'status': 'ACTIVE', 'desiredCount': 1, 'runningCount': 1, 'pendingCount': 0, 'taskDefinition': server_definition, 'deployments': [{'status': 'PRIMARY', 'rolloutState': 'COMPLETED'}]}
server = {'taskArn': arn, 'taskDefinitionArn': server_definition, 'group': f'service:{collector.SERVICE}', 'lastStatus': 'RUNNING', 'healthStatus': 'HEALTHY', 'overrides': {'containerOverrides': [{'name': 'core-server-persistence'}], 'inferenceAcceleratorOverrides': []}, 'containers': [{'name': 'core-server-persistence', 'image': image, 'imageDigest': child}]}
server_spec = {'taskDefinitionArn': server_definition, 'family': 'kanbien-core-platform-core-server-persistence', 'containerDefinitions': [{'name': 'core-server-persistence', 'image': image, 'environment': [{'name': 'PLATFORM_SOURCE_COMMIT_SHA', 'value': candidate['source_revision']}]}]}
verifier = collector.controller('scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py')
health = {'taskArn': health_arn, 'taskDefinitionArn': health_definition, 'lastStatus': 'STOPPED', 'startedAt': stamp(-60), 'stoppedAt': stamp(-50), 'overrides': {'containerOverrides': [{'name': 'private-persistence-verifier', 'environment': [{'name': name, 'value': value} for name, value in {'PERSISTENCE_VERIFIER_MODE': 'health-ready', 'PERSISTENCE_ACCEPTANCE_RECORD_ID': verifier.RECORD_ID, 'PERSISTENCE_ACCEPTANCE_FACT': verifier.FACT}.items()]}], 'inferenceAcceleratorOverrides': []}, 'containers': [{'name': 'private-persistence-verifier', 'image': image, 'imageDigest': child, 'exitCode': 0}]}
health_spec = {'taskDefinitionArn': health_definition, 'family': 'kanbien-core-platform-persistence-verifier', 'containerDefinitions': [{'name': 'private-persistence-verifier', 'image': image}]}
snapshot_id = 'kanbien-core-platform-persistence-recovery-20261025-r2'
source = {'DBInstanceIdentifier': collector.DATABASE, 'DbiResourceId': 'db-synthetic-incarnation', 'InstanceCreateTime': stamp(-86400), 'DBInstanceStatus': 'available', 'Engine': 'postgres', 'PubliclyAccessible': False, 'StorageEncrypted': True, 'DeletionProtection': True}
snapshot = {'DBSnapshotIdentifier': snapshot_id, 'DBInstanceIdentifier': collector.DATABASE, 'DbiResourceId': source['DbiResourceId'], 'SnapshotCreateTime': stamp(-600), 'OriginalSnapshotCreateTime': stamp(-600), 'Status': 'available', 'Encrypted': True}
record_proof = {'task': {'started_at': stamp(-1200), 'stopped_at': stamp(-1190)}, 'integrity': {'payload_sha256': 'sha256:' + 'f' * 64}}
state = {}
def reset():
    state.update(service=copy.deepcopy(service), server=copy.deepcopy(server), server_spec=copy.deepcopy(server_spec), health=copy.deepcopy(health), health_spec=copy.deepcopy(health_spec), source=copy.deepcopy(source), snapshot=copy.deepcopy(snapshot))
    collector.TASKS = {}
    collector.task_definition.cache_clear()
def observe(*parts):
    action = parts[1]
    if action == 'batch-get-image': return {'images': [{'imageManifest': json.dumps({'manifests': [{'digest': child, 'mediaType': 'application/vnd.oci.image.manifest.v1+json', 'platform': {'architecture': 'amd64', 'os': 'linux'}}]})}]}
    if action == 'describe-services': return {'services': [state['service']]}
    if action == 'list-tasks': return {'taskArns': [arn]}
    if action == 'describe-tasks': return {'tasks': [state['server'] if parts[-1] == arn else state['health']]}
    if action == 'describe-task-definition': return {'taskDefinition': state['server_spec'] if parts[-1] == server_definition else state['health_spec']}
    if action == 'get-log-events': return {'events': [{'message': json.dumps({'verdict': 'accepted', 'code': 'KANBIEN_CORE_PERSISTENCE_HEALTHY'})}]}
    if action == 'describe-db-instances': return {'DBInstances': [state['source']]}
    if action == 'describe-db-snapshots': return {'DBSnapshots': [state['snapshot']]}
    raise AssertionError(f'unexpected observation or mutation: {parts}')
def rejects(call):
    try: call()
    except collector.EvidenceFailure: return
    raise AssertionError('invalid current observation accepted')
with patch.object(collector, 'aws', side_effect=observe):
    reset()
    assert collector.qualified_runnable_digest(candidate) == child
    assert collector.current_service(server_definition, candidate, child)['running_task'] == arn
    assert collector.current_health(health_arn, health_definition, candidate, child)['task_arn'] == health_arn
    for change in ('wrong-image', 'wrong-source', 'command-override', 'role-override', 'resource-override', 'pending', 'wrong-service', 'wrong-group'):
        reset()
        if change == 'wrong-image': state['server']['containers'][0]['imageDigest'] = 'sha256:' + '9' * 64
        elif change == 'wrong-source': state['server_spec']['containerDefinitions'][0]['environment'][0]['value'] = '9' * 40
        elif change == 'command-override': state['server']['overrides']['containerOverrides'][0]['command'] = ['anything']
        elif change == 'role-override': state['server']['overrides']['taskRoleArn'] = 'unrelated-role'
        elif change == 'resource-override': state['server']['overrides']['cpu'] = '1024'
        elif change == 'pending': state['service']['pendingCount'] = 1
        elif change == 'wrong-service': state['service']['serviceName'] = 'unrelated'
        else: state['server']['group'] = 'service:unrelated'
        rejects(lambda: collector.current_service(server_definition, candidate, child))
    for change in ('stale', 'future', 'wrong-mode', 'command-override', 'wrong-digest', 'wrong-definition', 'malformed-time'):
        reset()
        if change == 'stale': state['health'].update(startedAt=stamp(-1200), stoppedAt=stamp(-1190))
        elif change == 'future': state['health'].update(startedAt=stamp(3600), stoppedAt=stamp(3610))
        elif change == 'wrong-mode': state['health']['overrides']['containerOverrides'][0]['environment'][0]['value'] = 'health-unready'
        elif change == 'command-override': state['health']['overrides']['containerOverrides'][0]['command'] = ['anything']
        elif change == 'wrong-digest': state['health']['containers'][0]['imageDigest'] = 'sha256:' + '9' * 64
        elif change == 'wrong-definition': state['health']['taskDefinitionArn'] += '2'
        else: state['health']['startedAt'] = []
        rejects(lambda: collector.current_health(health_arn, health_definition, candidate, child))
    reset()
    with patch.object(collector.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'DBInstanceNotFound')) as cleanup:
        proof = collector.database_posture(snapshot_id, record_proof)
        assert proof['record_proof_digest'] == record_proof['integrity']['payload_sha256'] and proof['restore_cleanup'] == 'confirmed-absent'
        assert cleanup.call_count == 1 and cleanup.call_args.kwargs['timeout'] == 30
        for change in ('early-snapshot', 'other-source', 'new-incarnation', 'wrong-snapshot'):
            reset(); cleanup.reset_mock()
            if change == 'early-snapshot': state['snapshot'].update(SnapshotCreateTime=stamp(-1800), OriginalSnapshotCreateTime=stamp(-1800))
            elif change == 'other-source': state['snapshot']['DbiResourceId'] = 'db-other'
            elif change == 'new-incarnation': state['source']['InstanceCreateTime'] = stamp(-1000)
            else: state['snapshot']['DBSnapshotIdentifier'] += '-wrong'
            rejects(lambda: collector.database_posture(snapshot_id, record_proof))
            assert cleanup.call_count == 0
    reset()
    with patch.object(collector.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')):
        rejects(lambda: collector.database_posture(snapshot_id, record_proof))
print('Fresh acceptance observations passed: exact qualified image/source/overrides, bounded health freshness, retained record/snapshot/source ordering and fresh cleanup; 20 negative observations rejected without provider access.')

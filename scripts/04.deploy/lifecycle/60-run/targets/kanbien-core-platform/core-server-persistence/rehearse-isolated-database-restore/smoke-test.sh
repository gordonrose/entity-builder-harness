#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.isolated-persistence-restore
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the isolated restore verifier accepts the exact ECS task-definition shape only.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-isolated-persistence-restore
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
RESTORE_SCRIPT="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py"

python3 -B - "$RESTORE_SCRIPT" <<'PY'
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

spec = importlib.util.spec_from_file_location("isolated_restore", sys.argv[1])
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

class AwsFixture:
    def __init__(self, container):
        self.container = container

    def aws(self, *_args):
        return True, {"taskDefinition": {"containerDefinitions": [self.container]}}, "ok"

valid = {
    "name": "persistence-restoration-verifier",
    "command": ["artifacts/kanbien-core-server-persistence-restore-verifier.main.js"],
    "environment": [
        {"name": "PERSISTENCE_POSTGRES_PORT", "value": "5432"},
        {"name": "PERSISTENCE_POSTGRES_DATABASE", "value": "kanbienpersistence"},
        {"name": "PERSISTENCE_POSTGRES_SCHEMA", "value": "platform"},
        {"name": "PERSISTENCE_POSTGRES_IAM_REGION", "value": "eu-west-1"},
        {"name": "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE", "value": "restoration-identity-supplied-at-governed-task-run"},
        {"name": "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME", "value": "core_runtime"},
    ],
    "secrets": [],
}
assert module.task_def_valid(AwsFixture(valid), "synthetic:1")

# This is the former parser bug: the valid AWS response uses lower-case names.
upper_case_only = {**valid, "environment": [{"Name": "PERSISTENCE_POSTGRES_DATABASE", "Value": "kanbienpersistence"}]}
assert not module.task_def_valid(AwsFixture(upper_case_only), "synthetic:1")

# The guard remains fail-closed for a definition that could carry a static host.
unsafe = {**valid, "environment": valid["environment"] + [{"name": "PERSISTENCE_POSTGRES_HOST", "value": "db.example.invalid"}]}
assert not module.task_def_valid(AwsFixture(unsafe), "synthetic:1")
assert module.restore_identity_resource({"DbiResourceId": "db-RESTORE-A"}).endswith("db-RESTORE-A/core_runtime")
assert module.restore_identity_resource({}) is None

class TaskListFixture:
    def __init__(self):
        self.calls = []

    def aws(self, *_args):
        self.calls.append(_args)
        if _args[1] == "describe-tasks":
            return True, {"tasks": [{"taskArn": "task-1", "startedBy": "synthetic-start"}]}, "ok"
        assert "--started-by" not in _args, "startedBy cannot be combined with status filters"
        return True, {"taskArns": ["task-1"]}, "ok"

tasks = TaskListFixture()
assert module.verifier_tasks(tasks, "synthetic-start", "synthetic-definition") == (["task-1"], "ok")
assert [call[-1] for call in tasks.calls if call[1] == "list-tasks"] == ["RUNNING", "STOPPED"]

first_restore = {"DbiResourceId": "db-RESTORE-A"}
second_restore = {"DbiResourceId": "db-RESTORE-B"}
assert module.restore_run_identity(first_restore) != module.restore_run_identity(second_restore)
assert module.restore_run_identity(first_restore).startswith("kanbien-restore-")
assert module.restore_run_identity({}) is None

# The restored copy must expose PostgreSQL logs, but the controller only ever
# returns a closed category.  Raw provider/server messages (including a
# synthetic credential canary) cannot enter its report or stdout.
assert module.restored_postgresql_log_group("kanbien-core-platform-persistence-restore-20261025-r2") == "/aws/rds/instance/kanbien-core-platform-persistence-restore-20261025-r2/postgresql"
assert module.restored_postgresql_log_group("unrelated-instance") is None
canary = "password=synthetic-not-for-output"
assert module.classify_restored_postgresql_log_events([{"message": f'FATAL: password authentication failed for user "runtime" {canary}'}]) == "persistence-restore-server-log-authentication-rejected"
assert module.classify_restored_postgresql_log_events([{"message": "FATAL: no pg_hba.conf entry"}]) == "persistence-restore-server-log-client-authentication-policy-rejected"
assert module.classify_restored_postgresql_log_events([{"message": 'FATAL: role "runtime" does not exist'}]) == "persistence-restore-server-log-role-state-invalid"
assert module.classify_restored_postgresql_log_events([{"message": "Failed to authorize the connection request because the caller is not authorized to perform `rds-db:connect` " + canary}]) == "persistence-restore-server-log-iam-authorization-rejected"
assert module.classify_restored_postgresql_log_events([{"message": "Failed to authenticate the connection request because the provided token is malformed " + canary}]) == "persistence-restore-server-log-iam-authentication-rejected"
assert module.classify_restored_postgresql_log_events([{"message": "unexpected provider detail " + canary}]) == "persistence-restore-server-log-no-classified-event"
assert module.classify_restored_postgresql_log_events({}) == "persistence-restore-server-log-observation-invalid"

class RdsLogFixture:
    def __init__(self, response): self.response = response; self.calls = []
    def aws(self, *args):
        self.calls.append(args)
        return self.response

window_task = {"startedAt": "2026-10-26T02:00:00Z", "stoppedAt": "2026-10-26T02:00:11Z"}
fixture = RdsLogFixture((True, {"events": [{"message": "PAM authentication failed " + canary}]}, "ok"))
classification, collection = module.collect_restored_postgresql_log_classification(fixture, "kanbien-core-platform-persistence-restore-20261025-r2", window_task)
assert (classification, collection) == ("persistence-restore-server-log-authentication-rejected", "collected")
assert fixture.calls[0][:2] == ("logs", "filter-log-events") and canary not in json.dumps({"classification": classification, "collection": collection})
missing_export = RdsLogFixture((False, None, "aws-resource-missing"))
assert module.collect_restored_postgresql_log_classification(missing_export, "kanbien-core-platform-persistence-restore-20261025-r2", window_task) == ("persistence-restore-server-log-export-unavailable", "unavailable")
assert module.collect_restored_postgresql_log_classification(fixture, "kanbien-core-platform-persistence-restore-20261025-r2", {"startedAt": "not-a-time", "stoppedAt": "2026-10-26T02:00:11Z"}) == ("persistence-restore-server-log-time-invalid", "failed")
original_diagnostics = module.OPERATION_DIAGNOSTICS
with TemporaryDirectory() as temporary:
    module.OPERATION_DIAGNOSTICS = Path(temporary)
    assert module.retain_verifier_rejection(fixture, "kanbien-restore-diagnostic-test", "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE", "kanbien-core-platform-persistence-restore-20261025-r2", window_task) == (True, "ok")
    retained = json.loads((Path(temporary) / "kanbien-restore-diagnostic-test-rejected.json").read_text())
    assert retained["classification"] == {"code": "persistence-restore-server-log-authentication-rejected"}
    assert retained["collection"] == {"status": "collected"}
    assert retained["next_action"] == {"decision": "correct-and-create-new-operation"}
    assert canary not in json.dumps(retained)
    assert module.retain_verifier_rejection(missing_export, "kanbien-restore-diagnostic-missing-export", "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE", "kanbien-core-platform-persistence-restore-20261025-r2", window_task) == (True, "ok")
    unavailable = json.loads((Path(temporary) / "kanbien-restore-diagnostic-missing-export-rejected.json").read_text())
    assert unavailable["collection"] == {"status": "unavailable"}
    assert unavailable["next_action"] == {"decision": "inspect-retained-evidence"}
    assert module.retain_verifier_rejection(fixture, "kanbien-restore-diagnostic-follow-up", "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE", "kanbien-core-platform-persistence-restore-20261025-r2", window_task, "rejected-reobservation") == (True, "ok")
    assert (Path(temporary) / "kanbien-restore-diagnostic-follow-up-rejected-reobservation.json").is_file()
module.OPERATION_DIAGNOSTICS = original_diagnostics

# RDS IAM authentication can lag the IAM policy read that binds the temporary
# restored instance.  A first verifier launch waits for an aged, exact
# CloudTrail policy observation, then launches at most one bound task.
restored = {"DBInstanceStatus": "available", "Engine": "postgres", "DbiResourceId": "db-RESTORE-A", "PubliclyAccessible": False, "StorageEncrypted": True, "IAMDatabaseAuthenticationEnabled": True, "EnabledCloudwatchLogsExports": ["postgresql", "iam-db-auth-error"], "VpcSecurityGroups": [{"VpcSecurityGroupId": "sg-restored"}], "DBSubnetGroup": {"DBSubnetGroupName": "subnet-group"}, "Endpoint": {"Address": "restore.example.invalid"}}
controls = {"CoreServerPersistenceRestorationVerifierTaskDefinitionArn": "definition-safe", "PersistenceRestoredDatabaseSecurityGroupId": "sg-restored", "PersistenceRestorationVerifierTaskRoleName": "restore-role", "PrivateSubnetIds": "subnet-safe", "PersistenceRestorationVerifierSecurityGroupId": "sg-verifier"}
source_for_posture = {"DBSubnetGroup": {"DBSubnetGroupName": "subnet-group"}}
assert module.correct(restored, source_for_posture, "sg-restored")
assert not module.correct({**restored, "EnabledCloudwatchLogsExports": ["postgresql"]}, source_for_posture, "sg-restored")
class LaunchFixture:
    def __init__(self): self.calls = []
    def aws(self, *args):
        self.calls.append(args)
        if args[1] == "run-task": return True, {}, "ok"
        raise AssertionError(args)

launch = LaunchFixture()
originals = module.source, module.controls, module.db, module.correct, module.task_def_valid, module.temporary_restore_identity_policy, module.temporary_restore_identity_policy_stable, module.verifier_tasks
module.source = lambda _m: ({}, "ok")
module.controls = lambda _m: (controls, "ok")
module.db = lambda _m, _id: (restored, "ok")
module.correct = lambda *_: True
module.task_def_valid = lambda *_: True
identity = module.restore_identity_resource(restored)
module.temporary_restore_identity_policy = lambda *_args: ("ok", identity)
module.temporary_restore_identity_policy_stable = lambda *_args: True
module.verifier_tasks = lambda *_args: ([], "ok")
output = io.StringIO()
with contextlib.redirect_stdout(output):
    assert module.verify(launch, "kanbien-core-platform-persistence-recovery-20261025-r2", "kanbien-core-platform-persistence-restore-20261025-r2") == 1
module.source, module.controls, module.db, module.correct, module.task_def_valid, module.temporary_restore_identity_policy, module.temporary_restore_identity_policy_stable, module.verifier_tasks = originals
assert any(call[1] == "run-task" for call in launch.calls)
assert json.loads(output.getvalue())["findings"] == [{"code": "persistence-restoration-verifier-submitted-awaiting-provider-observation"}]

# A new isolated restore must request both ordinary PostgreSQL and dedicated
# IAM-authentication error exports.  The controller retains only closed
# classifications; this extra provider signal is for in-memory diagnosis.
class RestoreLaunchFixture:
    def __init__(self): self.calls = []
    def aws(self, *args): self.calls.append(args); return True, {}, "ok"

originals = module.source, module.snapshot, module.controls, module.read_record_proof, module.recovery_point_binding, module.db
module.source = lambda _m: ({"DBInstanceClass": "db.t4g.micro", "DBSubnetGroup": {"DBSubnetGroupName": "subnet-safe"}}, "ok")
module.snapshot = lambda _m, _id: ({"Status": "available", "Encrypted": True, "DBInstanceIdentifier": module.DATABASE}, "ok")
module.controls = lambda _m: (controls, "ok")
module.read_record_proof = lambda _path: ({}, "ok")
module.recovery_point_binding = lambda *_args: (({"Target": "kanbien-core-platform"}, {"snapshot": "safe"}), "ok")
module.db = lambda _m, _id: (None, "aws-resource-missing")
restore_launch = RestoreLaunchFixture()
with contextlib.redirect_stdout(io.StringIO()):
    assert module.restore(restore_launch, "kanbien-core-platform-persistence-recovery-20261025-r2", "kanbien-core-platform-persistence-restore-20261025-r2", record_proof_path=Path("safe")) == 1
module.source, module.snapshot, module.controls, module.read_record_proof, module.recovery_point_binding, module.db = originals
restore_call = next(call for call in restore_launch.calls if call[1] == "restore-db-instance-from-db-snapshot")
export_index = restore_call.index("--enable-cloudwatch-logs-exports")
assert restore_call[export_index + 1:export_index + 3] == module.RESTORE_SERVER_LOG_EXPORTS

# The non-blocking stabilization check has to identify the exact temporary
# policy mutation, and must fail closed for fresh, unrelated, or malformed
# CloudTrail observations. The raw event is parsed only in memory and never
# becomes controller output or retained evidence.
policy_event = json.dumps({"requestParameters": {"roleName": "restore-role", "policyName": "kanbien-core-platform-restoration-verifier-current-instance"}})
class CloudTrailFixture:
    def __init__(self, events): self.events = events
    def aws_in_region(self, region, *args):
        assert region == "us-east-1"
        assert args[:2] == ("cloudtrail", "lookup-events")
        return True, {"Events": self.events}, "ok"

old_event = {"EventTime": "2020-01-01T00:00:00Z", "CloudTrailEvent": policy_event}
assert module.temporary_restore_identity_policy_stable(CloudTrailFixture([old_event]), controls)
fresh_event = {"EventTime": module.datetime.now(module.timezone.utc).isoformat(), "CloudTrailEvent": policy_event}
assert not module.temporary_restore_identity_policy_stable(CloudTrailFixture([fresh_event]), controls)
wrong_target = {"EventTime": "2020-01-01T00:00:00Z", "CloudTrailEvent": json.dumps({"requestParameters": {"roleName": "other-role", "policyName": "kanbien-core-platform-restoration-verifier-current-instance"}})}
assert not module.temporary_restore_identity_policy_stable(CloudTrailFixture([wrong_target]), controls)
assert not module.temporary_restore_identity_policy_stable(CloudTrailFixture([{"EventTime": "2020-01-01T00:00:00Z", "CloudTrailEvent": "[]"}]), controls)
assert not module.temporary_restore_identity_policy_stable(CloudTrailFixture([{"EventTime": "not-a-time", "CloudTrailEvent": policy_event}]), controls)

# A failed verifier may contribute only an explicit allowlisted result code.
# Raw provider output and lookalike payloads are not diagnostic evidence.
class LogFixture:
    def __init__(self, messages): self.messages = messages
    def aws(self, *_args): return True, {"events": [{"message": message} for message in self.messages]}, "ok"

assert module.terminal_result(LogFixture([json.dumps({"verdict": "accepted", "code": "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED"})]), "task-accepted") == ("accepted", "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED"})]), "task-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID"})]), "task-tls-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_UNAVAILABLE"})]), "task-token-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_UNAVAILABLE")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE"})]), "task-query-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_TRANSPORT_UNAVAILABLE"})]), "task-transport-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_TRANSPORT_UNAVAILABLE")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_NEGOTIATION_UNAVAILABLE"})]), "task-tls-negotiation-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_NEGOTIATION_UNAVAILABLE")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE"})]), "task-handshake-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "password=synthetic"})]), "task-unsafe") == ("unavailable", None)
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED", "provider_message": "synthetic"})]), "task-extra") == ("unavailable", None)

# A normal RDS restore reports ``creating`` before it has an endpoint.  The
# controller must preserve that as an in-flight operation instead of claiming
# an invalid restored posture.
original_source, original_controls, original_db = module.source, module.controls, module.db
module.source = lambda _m: ({"DBInstanceIdentifier": module.DATABASE}, "ok")
module.controls = lambda _m: ({"PersistenceRestoredDatabaseSecurityGroupId": "sg-fixture"}, "ok")
module.db = lambda _m, _identifier: ({"DBInstanceStatus": "creating"}, "ok")
output = io.StringIO()
with contextlib.redirect_stdout(output):
    assert module.verify(object(), "kanbien-core-platform-persistence-recovery-20261025-r2", "kanbien-core-platform-persistence-restore-20261025-r2", True) == 1
module.db = lambda _m, _identifier: ({"DBInstanceStatus": "configuring-log-exports"}, "ok")
log_export_output = io.StringIO()
with contextlib.redirect_stdout(log_export_output):
    assert module.verify(object(), "kanbien-core-platform-persistence-recovery-20261025-r2", "kanbien-core-platform-persistence-restore-20261025-r2", True) == 1
module.source, module.controls, module.db = original_source, original_controls, original_db
assert json.loads(output.getvalue())["findings"] == [{"code": "persistence-restore-still-provisioning"}]
assert json.loads(log_export_output.getvalue())["findings"] == [{"code": "persistence-restore-still-provisioning"}]
print("isolated persistence restore verifier task-definition checks passed")
PY

#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.isolated-persistence-restore
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
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

# RDS IAM authentication can lag the IAM policy read that binds the temporary
# restored instance.  A first verifier launch therefore waits once, rechecks
# that exact policy, and launches at most one bound task; it is not a retry of
# an already submitted verifier.
restored = {"DBInstanceStatus": "available", "DbiResourceId": "db-RESTORE-A", "PubliclyAccessible": False, "StorageEncrypted": True, "IAMDatabaseAuthenticationEnabled": True, "VpcSecurityGroups": [{"VpcSecurityGroupId": "sg-restored"}], "Endpoint": {"Address": "restore.example.invalid"}}
controls = {"CoreServerPersistenceRestorationVerifierTaskDefinitionArn": "definition-safe", "PersistenceRestoredDatabaseSecurityGroupId": "sg-restored", "PersistenceRestorationVerifierTaskRoleName": "restore-role", "PrivateSubnetIds": "subnet-safe", "PersistenceRestorationVerifierSecurityGroupId": "sg-verifier"}
class LaunchFixture:
    def __init__(self): self.calls = []
    def aws(self, *args):
        self.calls.append(args)
        if args[1] == "run-task": return True, {}, "ok"
        raise AssertionError(args)

launch = LaunchFixture()
originals = module.source, module.controls, module.db, module.correct, module.task_def_valid, module.temporary_restore_identity_policy, module.verifier_tasks, module.time.sleep
module.source = lambda _m: ({}, "ok")
module.controls = lambda _m: (controls, "ok")
module.db = lambda _m, _id: (restored, "ok")
module.correct = lambda *_: True
module.task_def_valid = lambda *_: True
identity = module.restore_identity_resource(restored)
module.temporary_restore_identity_policy = lambda *_args: ("ok", identity)
module.verifier_tasks = lambda *_args: ([], "ok")
waits = []
module.time.sleep = lambda seconds: waits.append(seconds)
output = io.StringIO()
with contextlib.redirect_stdout(output):
    assert module.verify(launch, "kanbien-core-platform-persistence-recovery-20261025-r2", "kanbien-core-platform-persistence-restore-20261025-r2") == 1
module.source, module.controls, module.db, module.correct, module.task_def_valid, module.temporary_restore_identity_policy, module.verifier_tasks, module.time.sleep = originals
assert waits == [module.RESTORATION_IDENTITY_STABILIZATION_SECONDS]
assert any(call[1] == "run-task" for call in launch.calls)
assert json.loads(output.getvalue())["findings"] == [{"code": "persistence-restoration-verifier-submitted-awaiting-provider-observation"}]

# A failed verifier may contribute only an explicit allowlisted result code.
# Raw provider output and lookalike payloads are not diagnostic evidence.
class LogFixture:
    def __init__(self, messages): self.messages = messages
    def aws(self, *_args): return True, {"events": [{"message": message} for message in self.messages]}, "ok"

assert module.terminal_result(LogFixture([json.dumps({"verdict": "accepted", "code": "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED"})]), "task-accepted") == ("accepted", "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED"})]), "task-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED")
assert module.terminal_result(LogFixture([json.dumps({"verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID"})]), "task-tls-rejected") == ("rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID")
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
module.source, module.controls, module.db = original_source, original_controls, original_db
assert json.loads(output.getvalue())["findings"] == [{"code": "persistence-restore-still-provisioning"}]
print("isolated persistence restore verifier task-definition checks passed")
PY

#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.isolated-persistence-restore
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-24"
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
import importlib.util
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
        {"name": "PERSISTENCE_POSTGRES_DATABASE", "value": "kanbienpersistence"},
        {"name": "PERSISTENCE_POSTGRES_SCHEMA", "value": "platform"},
    ],
    "secrets": [{"name": "PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS", "valueFrom": "synthetic"}],
}
assert module.task_def_valid(AwsFixture(valid), "synthetic:1")

# This is the former parser bug: the valid AWS response uses lower-case names.
upper_case_only = {**valid, "environment": [{"Name": "PERSISTENCE_POSTGRES_DATABASE", "Value": "kanbienpersistence"}]}
assert not module.task_def_valid(AwsFixture(upper_case_only), "synthetic:1")

# The guard remains fail-closed for a definition that could carry a static host.
unsafe = {**valid, "environment": valid["environment"] + [{"name": "PERSISTENCE_POSTGRES_HOST", "value": "db.example.invalid"}]}
assert not module.task_def_valid(AwsFixture(unsafe), "synthetic:1")

class TaskListFixture:
    def __init__(self):
        self.calls = []

    def aws(self, *_args):
        self.calls.append(_args)
        return True, {"taskArns": ["task-1"]}, "ok"

tasks = TaskListFixture()
assert module.verifier_tasks(tasks, "synthetic-start") == (["task-1"], "ok")
assert [call[-1] for call in tasks.calls] == ["RUNNING", "STOPPED"]

first_restore = {"DbiResourceId": "db-RESTORE-A"}
second_restore = {"DbiResourceId": "db-RESTORE-B"}
assert module.restore_run_identity(first_restore) != module.restore_run_identity(second_restore)
assert module.restore_run_identity(first_restore).startswith("kanbien-restore-")
assert module.restore_run_identity({}) is None
print("isolated persistence restore verifier task-definition checks passed")
PY

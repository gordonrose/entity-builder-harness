#!/usr/bin/env python3
"""Run one fixed migration task and fail closed on an uncertain outcome."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, CLUSTER = "kanbien-dev", "eu-west-1", "kanbien-core-platform"
ACCOUNT = "337159794548"
STACK, FOUNDATION = "kanbien-core-platform-core-server-persistence", "kanbien-core-platform-foundation"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"


def aws(*parts: str):
    result = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        lowered = result.stderr.lower()
        if "accessdenied" in lowered or "not authorized" in lowered:
            return False, None, "aws-access-denied"
        return False, None, "aws-command-failed"
    try:
        return True, json.loads(result.stdout or "{}"), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    value: dict[str, object] = {"schema": "deploy/persistence-migration-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "accepted" else 1


def deadline() -> int | None:
    path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    workloads = contract.get("health_recovery", {}).get("workloads", []) if isinstance(contract, dict) else []
    migration = next((item for item in workloads if isinstance(item, dict) and item.get("id") == "persistence-migration"), None)
    value = migration.get("completion", {}).get("deadline_seconds") if isinstance(migration, dict) else None
    return value if isinstance(value, int) and value > 0 else None


def outputs(stack_name: str) -> tuple[dict[str, str] | None, str]:
    ok, data, code = aws("cloudformation", "describe-stacks", "--stack-name", stack_name)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return None, code if not ok else "persistence-stack-outputs-unavailable"
    value = {item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", []) if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)}
    return value, "ok"


def timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def duration(task: dict[str, object]) -> int | None:
    start, stop = timestamp(task.get("startedAt")), timestamp(task.get("stoppedAt"))
    if start is None or stop is None or stop < start:
        return None
    return int((stop - start).total_seconds())


def task_exit(task: dict[str, object]) -> bool:
    containers = task.get("containers")
    return isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) and type(containers[0].get("exitCode")) is int and containers[0].get("exitCode") == 0


def current_reconciliation_task(task: dict[str, object], requested_arn: str, task_definition: str) -> str:
    """Reject a replay unless the supplied task is this deployment's terminal task."""
    expected_prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
    if not requested_arn.startswith(expected_prefix):
        return "persistence-migration-reconciliation-task-identity-invalid"
    if task.get("taskArn") != requested_arn or task.get("taskDefinitionArn") != task_definition:
        return "persistence-migration-reconciliation-task-not-current"
    if task.get("lastStatus") != "STOPPED":
        return "persistence-migration-reconciliation-task-not-terminal"
    return "ok"


SUCCESS = {
    "apply": "PERSISTENCE_MIGRATION_APPLIED",
    "rotate": "PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED",
    "revoke": "PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED",
}


def migration_log_accepted(task: dict[str, object], operation: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "persistence-migration-evidence-unavailable"
    stream = f"persistence-migration/persistence-migration/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return False, code
    messages = [event.get("message") for event in events.get("events", []) if isinstance(event, dict)] if isinstance(events, dict) else []
    expected = SUCCESS[operation]
    if any(isinstance(message, str) and '"verdict":"accepted"' in message and f'"code":"{expected}"' in message for message in messages):
        return True, "ok"
    return False, "persistence-migration-not-confirmed"


def accepted_completion(task: dict[str, object], seconds: int, operation: str) -> int:
    observed_duration = duration(task)
    if observed_duration is None:
        return report("blocked", "persistence-migration-duration-unavailable")
    if observed_duration > seconds:
        return report("blocked", "persistence-migration-completion-deadline-exceeded")
    if not task_exit(task):
        return report("blocked", "persistence-migration-unsuccessful-completion")
    accepted, code = migration_log_accepted(task, operation)
    if not accepted:
        return report("blocked", code)
    arn = task.get("taskArn")
    return report("accepted", "persistence-migration-applied", facts={"operation": operation, "migration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration})


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reconcile-task")
    parser.add_argument("--runtime-credential-operation", default="apply")
    args, unknown = parser.parse_known_args()
    if unknown or (args.reconcile_task is not None and not isinstance(args.reconcile_task, str)) or args.runtime_credential_operation not in SUCCESS:
        return report("blocked", "persistence-migration-arguments-invalid")
    seconds = deadline()
    if seconds is None:
        return report("blocked", "persistence-migration-deadline-invalid")
    scope_outputs, code = outputs(STACK)
    if scope_outputs is None:
        return report("blocked", code)
    foundation, code = outputs(FOUNDATION)
    if foundation is None:
        return report("blocked", code)
    task_definition, security_group = scope_outputs.get("CoreServerPersistenceMigrationTaskDefinitionArn"), scope_outputs.get("PersistenceMigrationSecurityGroupId")
    subnets = foundation.get("PrivateSubnetIds")
    if not all(isinstance(value, str) and value for value in (task_definition, security_group, subnets)):
        return report("blocked", "persistence-migration-network-or-task-definition-unavailable")
    if args.reconcile_task is not None:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("blocked", "persistence-migration-controller-observation-uncertain")
        task = listed[0]
        code = current_reconciliation_task(task, args.reconcile_task, task_definition)
        if code != "ok":
            return report("blocked", code)
        return accepted_completion(task, seconds, args.runtime_credential_operation)
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{security_group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "persistence-migration", "environment": [{"name": "PERSISTENCE_RUNTIME_CREDENTIAL_OPERATION", "value": args.runtime_credential_operation}]}]})
    ok, started, code = aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", task_definition, "--launch-type", "FARGATE", "--count", "1", "--network-configuration", network, "--overrides", overrides)
    tasks = started.get("tasks", []) if ok and isinstance(started, dict) else []
    if not ok or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        return report("blocked", code if not ok else "persistence-migration-not-started")
    arn = tasks[0]["taskArn"]
    started_at = time.monotonic()
    current: dict[str, object] | None = None
    while time.monotonic() - started_at <= seconds:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("blocked", "persistence-migration-controller-observation-uncertain")
        current = listed[0]
        if current.get("lastStatus") == "STOPPED":
            break
        time.sleep(5)
    if current is None or current.get("lastStatus") != "STOPPED":
        return report("blocked", "persistence-migration-controller-deadline-remote-task-still-running")
    return accepted_completion(current, seconds, args.runtime_credential_operation)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run one bounded administrative persistence task with durable proof."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[8]
CLUSTER = "kanbien-core-platform"
STACK = "kanbien-core-platform-core-server-persistence"
FOUNDATION = "kanbien-core-platform-foundation"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
ACCOUNT, REGION = "337159794548", "eu-west-1"
SUCCESS = {
    "bootstrap-identities": "PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED",
    "grant-runtime-application-access": "PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED",
    "rotate-runtime": "PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED",
    "revoke-runtime": "PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED",
    "prove-effective-privilege": "PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN",
}


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value


MIGRATION = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.py", "persistence_migration")
RECEIPTS = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py", "persistence_proof_receipts")


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    value: dict[str, object] = {"schema": "deploy/persistence-administration-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "accepted" else 1


def deadline() -> int | None:
    path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    workloads = document.get("health_recovery", {}).get("workloads", []) if isinstance(document, dict) else []
    administration = next((item for item in workloads if isinstance(item, dict) and item.get("id") == "persistence-administration"), None)
    value = administration.get("completion", {}).get("deadline_seconds") if isinstance(administration, dict) else None
    return value if isinstance(value, int) and value > 0 else None


def current_task(task: dict[str, object], requested: str, definition: str) -> str:
    prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
    if not requested.startswith(prefix):
        return "persistence-administration-reconciliation-task-identity-invalid"
    if task.get("taskArn") != requested or task.get("taskDefinitionArn") != definition:
        return "persistence-administration-reconciliation-task-not-current"
    return "ok" if task.get("lastStatus") == "STOPPED" else "persistence-administration-reconciliation-task-not-terminal"


def accepted_log(task: dict[str, object], operation: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "persistence-administration-evidence-unavailable"
    stream = f"persistence-administration/persistence-administration/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = MIGRATION.aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    messages = [item.get("message") for item in events.get("events", []) if isinstance(item, dict)] if ok and isinstance(events, dict) else []
    expected = SUCCESS[operation]
    return (True, "ok") if any(isinstance(message, str) and '"verdict":"accepted"' in message and f'"code":"{expected}"' in message for message in messages) else (False, code if not ok else "persistence-administration-not-confirmed")


def accept(task: dict[str, object], seconds: int, operation: str) -> int:
    observed = MIGRATION.duration(task)
    if observed is None:
        return report("blocked", "persistence-administration-duration-unavailable")
    if observed > seconds:
        return report("blocked", "persistence-administration-completion-deadline-exceeded")
    if not MIGRATION.task_exit(task):
        return report("blocked", "persistence-administration-unsuccessful-completion")
    ok, code = accepted_log(task, operation)
    if not ok:
        return report("blocked", code)
    digest = MIGRATION.image_digest(task.get("taskDefinitionArn"))
    arn = task.get("taskArn")
    if not isinstance(digest, str) or not isinstance(arn, str):
        return report("blocked", "persistence-administration-receipt-identity-unavailable")
    try:
        receipt = RECEIPTS.make(proof_type="administration", operation=operation, task=task, image_digest=digest, result_code=SUCCESS[operation], context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed}, controller="run-administration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        path = RECEIPTS.persist(receipt)
    except Exception:
        return report("blocked", "persistence-administration-receipt-persistence-failed")
    return report("accepted", "persistence-administration-applied", facts={"operation": operation, "administration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed, "proof_receipt": str(path.relative_to(ROOT))})


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--operation", choices=sorted(SUCCESS))
    parser.add_argument("--reconcile-task")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.operation is None or (args.reconcile_task is not None and not isinstance(args.reconcile_task, str)):
        return report("blocked", "persistence-administration-arguments-invalid")
    seconds = deadline()
    if seconds is None:
        return report("blocked", "persistence-administration-deadline-invalid")
    outputs, code = MIGRATION.outputs(STACK)
    foundation, foundation_code = MIGRATION.outputs(FOUNDATION)
    definition = outputs.get("CoreServerPersistenceAdministrationTaskDefinitionArn") if isinstance(outputs, dict) else None
    security_group = outputs.get("PersistenceAdministrationSecurityGroupId") if isinstance(outputs, dict) else None
    subnets = foundation.get("PrivateSubnetIds") if isinstance(foundation, dict) else None
    if not all(isinstance(value, str) and value for value in (definition, security_group, subnets)):
        return report("blocked", code if outputs is None else foundation_code if foundation is None else "persistence-administration-network-or-task-definition-unavailable")
    if args.reconcile_task:
        ok, described, code = MIGRATION.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_task)
        tasks = described.get("tasks", []) if ok and isinstance(described, dict) else []
        task = tasks[0] if len(tasks) == 1 and isinstance(tasks[0], dict) else None
        if not isinstance(task, dict):
            return report("blocked", code if not ok else "persistence-administration-controller-observation-uncertain")
        reconciliation = current_task(task, args.reconcile_task, definition)
        return accept(task, seconds, args.operation) if reconciliation == "ok" else report("blocked", reconciliation)
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{security_group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "persistence-administration", "environment": [{"name": "PERSISTENCE_ADMINISTRATION_OPERATION", "value": args.operation}]}]})
    ok, started, code = MIGRATION.aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", definition, "--launch-type", "FARGATE", "--count", "1", "--network-configuration", network, "--overrides", overrides)
    tasks = started.get("tasks", []) if ok and isinstance(started, dict) else []
    task = tasks[0] if len(tasks) == 1 and isinstance(tasks[0], dict) else None
    if not isinstance(task, dict) or not isinstance(task.get("taskArn"), str):
        return report("blocked", code if not ok else "persistence-administration-not-started")
    begun, current = time.monotonic(), task
    while time.monotonic() - begun <= seconds:
        ok, described, code = MIGRATION.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", task["taskArn"])
        tasks = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(tasks) != 1 or not isinstance(tasks[0], dict):
            return report("blocked", "persistence-administration-controller-observation-uncertain")
        current = tasks[0]
        if current.get("lastStatus") == "STOPPED":
            return accept(current, seconds, args.operation)
        time.sleep(5)
    return report("blocked", "persistence-administration-controller-deadline-remote-task-still-running")


if __name__ == "__main__":
    raise SystemExit(main())


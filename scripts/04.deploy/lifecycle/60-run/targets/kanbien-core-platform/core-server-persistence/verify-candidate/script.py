#!/usr/bin/env python3
"""Run a fixed private, server-mediated persistence verification task."""
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
STACK, FOUNDATION = "kanbien-core-platform-core-server-persistence", "kanbien-core-platform-foundation"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
RECORD_ID, FACT = "core-persistence-acceptance-v1", "kanbien-core-persistence-acceptance-v1"
SUCCESS = {"create": "KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED", "read": "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "cleanup": "KANBIEN_CORE_PERSISTENCE_RECORD_CLEANED_UP"}


def aws(*parts: str):
    result = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        lowered = result.stderr.lower()
        return False, None, "aws-access-denied" if "accessdenied" in lowered or "not authorized" in lowered else "aws-command-failed"
    try:
        return True, json.loads(result.stdout or "{}"), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    value: dict[str, object] = {"schema": "deploy/private-persistence-verification-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "accepted" else 1


def outputs(stack_name: str) -> tuple[dict[str, str] | None, str]:
    ok, data, code = aws("cloudformation", "describe-stacks", "--stack-name", stack_name)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return None, code if not ok else "persistence-stack-outputs-unavailable"
    return ({item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", []) if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)}, "ok")


def deadline() -> int | None:
    path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    workloads = contract.get("health_recovery", {}).get("workloads", []) if isinstance(contract, dict) else []
    verifier = next((item for item in workloads if isinstance(item, dict) and item.get("id") == "private-release-verifier"), None)
    value = verifier.get("completion", {}).get("deadline_seconds") if isinstance(verifier, dict) else None
    return value if isinstance(value, int) and value > 0 else None


def parsed(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
    except ValueError:
        return None


def duration(task: dict[str, object]) -> int | None:
    start, stop = parsed(task.get("startedAt")), parsed(task.get("stoppedAt"))
    return int((stop - start).total_seconds()) if start is not None and stop is not None and stop >= start else None


def exited_zero(task: dict[str, object]) -> bool:
    containers = task.get("containers")
    return isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) and type(containers[0].get("exitCode")) is int and containers[0].get("exitCode") == 0


def log_accepted(task: dict[str, object], expected: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "private-persistence-verifier-evidence-unavailable"
    stream = f"persistence-verifier/private-persistence-verifier/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return False, code
    messages = [event.get("message") for event in events.get("events", []) if isinstance(event, dict)] if isinstance(events, dict) else []
    return (True, "ok") if any(isinstance(message, str) and '"verdict":"accepted"' in message and f'"code":"{expected}"' in message for message in messages) else (False, "private-persistence-verifier-evidence-mismatch")


def no_direct_database_credential(task_definition: str) -> bool:
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", task_definition)
    containers = definition.get("taskDefinition", {}).get("containerDefinitions", []) if ok and isinstance(definition, dict) else []
    if len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    names = {item.get("Name") for item in container.get("environment", []) if isinstance(item, dict)}
    return not container.get("secrets") and not any(isinstance(name, str) and name.startswith("PERSISTENCE_POSTGRES") for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.mode not in SUCCESS:
        return report("blocked", "private-persistence-verification-arguments-invalid")
    seconds = deadline()
    if seconds is None:
        return report("blocked", "private-persistence-verifier-deadline-invalid")
    scope, code = outputs(STACK)
    if scope is None:
        return report("blocked", code)
    foundation, code = outputs(FOUNDATION)
    if foundation is None:
        return report("blocked", code)
    task_definition = scope.get("CoreServerPersistenceVerifierTaskDefinitionArn")
    subnets, group = foundation.get("PrivateSubnetIds"), foundation.get("VerifierSecurityGroupId")
    if not all(isinstance(value, str) and value for value in (task_definition, subnets, group)):
        return report("blocked", "private-persistence-verifier-network-or-task-definition-unavailable")
    if not no_direct_database_credential(task_definition):
        return report("blocked", "private-persistence-verifier-isolation-not-proven")
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "private-persistence-verifier", "environment": [
        {"name": "PERSISTENCE_VERIFIER_MODE", "value": args.mode},
        {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": RECORD_ID},
        {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": FACT},
    ]}]})
    ok, started, code = aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", task_definition, "--launch-type", "FARGATE", "--count", "1", "--network-configuration", network, "--overrides", overrides)
    tasks = started.get("tasks", []) if ok and isinstance(started, dict) else []
    if not ok or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        return report("blocked", code if not ok else "private-persistence-verifier-not-started")
    arn = tasks[0]["taskArn"]
    current: dict[str, object] | None = None
    started_at = time.monotonic()
    while time.monotonic() - started_at <= seconds:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("blocked", "private-persistence-verifier-controller-observation-uncertain")
        current = listed[0]
        if current.get("lastStatus") == "STOPPED":
            break
        time.sleep(5)
    if current is None or current.get("lastStatus") != "STOPPED":
        return report("blocked", "private-persistence-verifier-controller-deadline-remote-task-still-running")
    observed_duration = duration(current)
    if observed_duration is None:
        return report("blocked", "private-persistence-verifier-duration-unavailable")
    if observed_duration > seconds:
        return report("blocked", "private-persistence-verifier-completion-deadline-exceeded")
    if not exited_zero(current):
        return report("blocked", "private-persistence-verifier-unsuccessful-completion")
    accepted, code = log_accepted(current, SUCCESS[args.mode])
    if not accepted:
        return report("blocked", code)
    return report("accepted", "private-persistence-verifier-accepted", facts={"mode": args.mode, "verifier_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration})


if __name__ == "__main__":
    raise SystemExit(main())

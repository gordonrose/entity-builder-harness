#!/usr/bin/env python3
"""Run a fixed private, server-mediated persistence verification task."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, CLUSTER = "kanbien-dev", "eu-west-1", "kanbien-core-platform"
ACCOUNT = "337159794548"
STACK, FOUNDATION = "kanbien-core-platform-core-server-persistence", "kanbien-core-platform-foundation"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
RECORD_ID, FACT = "core-persistence-acceptance-v1", "kanbien-core-persistence-acceptance-v1"
SUCCESS = {
    "create": "KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED",
    "read": "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED",
    "cleanup": "KANBIEN_CORE_PERSISTENCE_RECORD_CLEANED_UP",
    "health-ready": "KANBIEN_CORE_PERSISTENCE_HEALTHY",
    "health-unready": "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY",
}
AWS_CONNECT_TIMEOUT_SECONDS = 5
AWS_READ_TIMEOUT_SECONDS = 20
AWS_PROCESS_TIMEOUT_SECONDS = 30


def aws(*parts: str):
    try:
        result = subprocess.run(
            ["aws", *parts, "--cli-connect-timeout", str(AWS_CONNECT_TIMEOUT_SECONDS), "--cli-read-timeout", str(AWS_READ_TIMEOUT_SECONDS), "--profile", PROFILE, "--region", REGION, "--output", "json"],
            capture_output=True, text=True, timeout=AWS_PROCESS_TIMEOUT_SECONDS, env={**os.environ, "AWS_PAGER": ""},
        )
    except subprocess.TimeoutExpired:
        return False, None, "aws-command-timeout"
    if result.returncode:
        lowered = result.stderr.lower()
        return False, None, "aws-access-denied" if "accessdenied" in lowered or "not authorized" in lowered else "aws-command-failed"
    try:
        return True, json.loads(result.stdout or "{}"), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None, stream=None) -> int:
    value: dict[str, object] = {"schema": "deploy/private-persistence-verification-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True), file=stream or sys.stdout)
    return 0 if verdict == "accepted" else 1


def proof_receipts():
    path = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"
    spec = importlib.util.spec_from_file_location("persistence_proof_receipts", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


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


def current_reconciliation_task(task: dict[str, object], requested_arn: str, task_definition: str) -> str:
    """Permit evidence recovery only for this deployment's terminal verifier task."""
    expected_prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
    if not requested_arn.startswith(expected_prefix):
        return "private-persistence-verifier-reconciliation-task-identity-invalid"
    if task.get("taskArn") != requested_arn or task.get("taskDefinitionArn") != task_definition:
        return "private-persistence-verifier-reconciliation-task-not-current"
    if task.get("lastStatus") != "STOPPED":
        return "private-persistence-verifier-reconciliation-task-not-terminal"
    return "ok"


def log_accepted(task: dict[str, object], expected: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "private-persistence-verifier-evidence-unavailable"
    stream = f"persistence-verifier/private-persistence-verifier/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return False, code
    messages = [event.get("message") for event in events.get("events", []) if isinstance(event, dict)] if isinstance(events, dict) else []
    return (True, "ok") if any(accepted_message(message, expected) for message in messages) else (False, "private-persistence-verifier-evidence-mismatch")


def no_direct_database_credential(task_definition: str) -> bool:
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", task_definition)
    containers = definition.get("taskDefinition", {}).get("containerDefinitions", []) if ok and isinstance(definition, dict) else []
    if len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    # ECS describes environment fields as lower-case ``name``.  A
    # credential-bearing verifier definition must never pass this check just
    # because the controller read the provider response with the wrong case.
    names = {item.get("name") for item in container.get("environment", []) if isinstance(item, dict)}
    return not container.get("secrets") and not any(isinstance(name, str) and name.startswith("PERSISTENCE_POSTGRES") for name in names)


def accepted_message(message: object, expected: str) -> bool:
    try:
        value = json.loads(message) if isinstance(message, str) else None
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(value, dict) and value.get("verdict") == "accepted" and value.get("code") == expected


def reconciliation_operation(operation: str, definition: str) -> tuple[str | None, str]:
    arns = []
    family = definition.rsplit("/", 1)[-1].split(":", 1)[0]
    for state in ("RUNNING", "STOPPED"):
        # AWS forbids combining startedBy with another ListTasks filter.
        ok, listed, code = aws("ecs", "list-tasks", "--cluster", CLUSTER, "--family", family, "--desired-status", state)
        values = listed.get("taskArns") if ok and isinstance(listed, dict) else None
        if not isinstance(values, list) or listed.get("nextToken") or not all(isinstance(value, str) for value in values):
            return None, "private-persistence-verifier-observation-uncertain"
        arns.extend(values)
    arns = list(dict.fromkeys(arns))
    matching = []
    for offset in range(0, len(arns), 100):
        batch = arns[offset:offset + 100]
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", *batch)
        tasks = described.get("tasks") if ok and isinstance(described, dict) else None
        if not isinstance(tasks, list) or described.get("failures") or len(tasks) != len(batch) or {task.get("taskArn") for task in tasks if isinstance(task, dict)} != set(batch):
            return None, "private-persistence-verifier-observation-uncertain"
        matching.extend(task["taskArn"] for task in tasks if task.get("startedBy") == operation)
    return (matching[0], "ok") if len(matching) == 1 else (None, "private-persistence-verifier-task-identity-unresolved")


def task_operation_bound(task: dict, mode: str) -> bool:
    overrides = task.get("overrides")
    containers = overrides.get("containerOverrides") if isinstance(overrides, dict) and set(overrides) == {"containerOverrides"} else None
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    expected = {"PERSISTENCE_VERIFIER_MODE": mode, "PERSISTENCE_ACCEPTANCE_RECORD_ID": RECORD_ID, "PERSISTENCE_ACCEPTANCE_FACT": FACT}
    environment = container.get("environment")
    if container.get("name") != "private-persistence-verifier" or set(container) - {"name", "environment"} or not isinstance(environment, list) or len(environment) != len(expected):
        return False
    return all(isinstance(item, dict) and set(item) == {"name", "value"} for item in environment) and {item["name"]: item["value"] for item in environment} == expected


def image_digest(task_definition: object) -> str | None:
    if not isinstance(task_definition, str):
        return None
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", task_definition)
    containers = definition.get("taskDefinition", {}).get("containerDefinitions", []) if ok and isinstance(definition, dict) else []
    image = containers[0].get("image") if isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) else None
    return image.rsplit("@", 1)[1] if isinstance(image, str) and image.count("@") == 1 and image.rsplit("@", 1)[1].startswith("sha256:") else None


def qualified_digest(path: Path) -> str | None:
    source = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("historic_capture_prepare", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    value = module.validate_receipt(path)
    return value.get("image_digest") if isinstance(value, dict) and isinstance(value.get("image_digest"), str) else None


def historical_task_identity(task: dict[str, object], expected_digest: str) -> bool:
    arn, definition_arn = task.get("taskArn"), task.get("taskDefinitionArn")
    if not isinstance(arn, str) or not arn.startswith(f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/") or not isinstance(definition_arn, str):
        return False
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", definition_arn)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    return isinstance(value, dict) and value.get("family") == "kanbien-core-platform-persistence-verifier" and image_digest(definition_arn) == expected_digest and no_direct_database_credential(definition_arn)


def accepted_completion(task: dict[str, object], seconds: int, mode: str) -> int:
    facts = {"verifier_task": task.get("taskArn"), "operation_id": task.get("startedBy")}
    observed_duration = duration(task)
    if observed_duration is None:
        return report("uncertain", "private-persistence-verifier-duration-unavailable", facts=facts)
    if observed_duration > seconds:
        return report("failed", "private-persistence-verifier-completion-deadline-exceeded", facts=facts)
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int:
        return report("uncertain", "persistence-task-exit-evidence-unavailable", facts=facts)
    if not exited_zero(task):
        return report("failed", "private-persistence-verifier-unsuccessful-completion", facts=facts)
    accepted, code = log_accepted(task, SUCCESS[mode])
    if not accepted:
        return report("uncertain" if code.startswith("aws-") else "pending", code, facts=facts)
    arn = task.get("taskArn")
    digest = image_digest(task.get("taskDefinitionArn"))
    if not isinstance(arn, str) or digest is None:
        return report("blocked", "private-persistence-verifier-receipt-identity-unavailable")
    try:
        receipt = proof_receipts().make(
            proof_type="verifier", operation=mode, task=task, image_digest=digest,
            result_code=SUCCESS[mode], context={"record_id": RECORD_ID, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration},
            controller="verify-candidate", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        path = proof_receipts().persist(receipt)
    except Exception:
        return report("blocked", "private-persistence-verifier-receipt-persistence-failed")
    return report("accepted", "private-persistence-verifier-accepted", facts={"mode": mode, "verifier_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, "proof_receipt": str(path.relative_to(ROOT))})


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode")
    parser.add_argument("--reconcile-task")
    parser.add_argument("--reconcile-operation")
    parser.add_argument("--capture-completed-task")
    parser.add_argument("--qualified-receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.mode not in SUCCESS or (args.reconcile_task is not None and args.capture_completed_task is not None) or (args.capture_completed_task is not None and args.qualified_receipt is None) or (args.capture_completed_task is None and args.qualified_receipt is not None):
        return report("blocked", "private-persistence-verification-arguments-invalid")
    if args.reconcile_operation is not None and (args.reconcile_task is not None or args.capture_completed_task is not None or re.fullmatch(r"kp-[a-f0-9]{32}", args.reconcile_operation) is None):
        return report("blocked", "private-persistence-verifier-reconciliation-operation-invalid")
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
    if args.reconcile_operation is not None:
        args.reconcile_task, code = reconciliation_operation(args.reconcile_operation, task_definition)
        if args.reconcile_task is None:
            return report("uncertain", code, facts={"operation_id": args.reconcile_operation})
    if args.reconcile_task is not None:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("uncertain", "private-persistence-verifier-controller-observation-uncertain", facts={"verifier_task": args.reconcile_task, "operation_id": args.reconcile_operation})
        task = listed[0]
        if args.reconcile_operation is not None and task.get("startedBy") != args.reconcile_operation:
            return report("blocked", "private-persistence-verifier-reconciliation-operation-mismatch")
        if not task_operation_bound(task, args.mode):
            return report("blocked", "private-persistence-verifier-reconciliation-operation-binding-invalid")
        code = current_reconciliation_task(task, args.reconcile_task, task_definition)
        if code != "ok":
            verdict = "pending" if code.endswith("-not-terminal") and task.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"} else "blocked"
            return report(verdict, code, facts={"verifier_task": args.reconcile_task, "operation_id": args.reconcile_operation})
        return accepted_completion(task, seconds, args.mode)
    if args.capture_completed_task is not None:
        expected_digest = qualified_digest(args.qualified_receipt)
        if expected_digest is None:
            return report("blocked", "private-persistence-verifier-historic-receipt-invalid")
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.capture_completed_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        task = listed[0] if len(listed) == 1 and isinstance(listed[0], dict) else None
        if not isinstance(task, dict) or task.get("taskArn") != args.capture_completed_task or not historical_task_identity(task, expected_digest) or not task_operation_bound(task, args.mode):
            return report("blocked", code if not ok else "private-persistence-verifier-historic-task-identity-invalid")
        return accepted_completion(task, seconds, args.mode)
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "private-persistence-verifier", "environment": [
        {"name": "PERSISTENCE_VERIFIER_MODE", "value": args.mode},
        {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": RECORD_ID},
        {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": FACT},
    ]}]})
    operation_id = "kp-" + uuid.uuid4().hex
    # Flush identity before submission so a lost response has a read-only recovery path.
    report("pending", "private-persistence-verifier-submission-prepared", facts={"operation_id": operation_id}, stream=sys.stderr)
    sys.stderr.flush()
    ok, started, code = aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", task_definition, "--launch-type", "FARGATE", "--count", "1", "--started-by", operation_id, "--client-token", operation_id, "--network-configuration", network, "--overrides", overrides)
    tasks = started.get("tasks", []) if ok and isinstance(started, dict) else []
    if not ok or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        return report("uncertain" if not ok else "failed", code if not ok else "private-persistence-verifier-not-started", facts={"operation_id": operation_id})
    arn = tasks[0]["taskArn"]
    current: dict[str, object] | None = None
    started_at = time.monotonic()
    while time.monotonic() - started_at <= seconds:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("uncertain", "private-persistence-verifier-controller-observation-uncertain", facts={"verifier_task": arn, "operation_id": operation_id})
        current = listed[0]
        if current.get("taskArn") != arn or current.get("taskDefinitionArn") != task_definition or current.get("startedBy") != operation_id or not task_operation_bound(current, args.mode):
            return report("uncertain", "private-persistence-verifier-controller-task-identity-mismatch", facts={"verifier_task": arn, "operation_id": operation_id})
        if current.get("lastStatus") == "STOPPED":
            break
        time.sleep(5)
    if current is None or current.get("lastStatus") != "STOPPED":
        return report("pending", "private-persistence-verifier-controller-deadline-remote-task-still-running", facts={"verifier_task": arn, "operation_id": operation_id})
    return accepted_completion(current, seconds, args.mode)


if __name__ == "__main__":
    raise SystemExit(main())

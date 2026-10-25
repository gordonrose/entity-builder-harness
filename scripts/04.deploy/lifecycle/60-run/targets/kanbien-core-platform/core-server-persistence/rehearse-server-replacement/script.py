#!/usr/bin/env python3
"""Replace exactly one healthy persistence server task and record the boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement.impl
#   version: 2
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Replace one exact healthy persistence server task and bind the succeeding private read proof to its recovery boundary.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh
#   effects: [aws-mutation]
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
CLUSTER = "kanbien-core-platform"
SERVICE = "kanbien-core-platform-core-server-persistence"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    body: dict[str, object] = {
        "schema": "deploy/persistence-server-replacement-report/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "verdict": verdict,
        "findings": [{"code": code} for code in codes],
    }
    if facts:
        body["facts"] = facts
    print(json.dumps(body, sort_keys=True))
    return 0 if verdict == "replaced" else 1


def healthy_service(service: object) -> bool:
    if not isinstance(service, dict):
        return False
    deployments = service.get("deployments")
    return (
        service.get("status") == "ACTIVE"
        and service.get("desiredCount") == 1
        and service.get("runningCount") == 1
        and isinstance(service.get("taskDefinition"), str)
        and isinstance(deployments, list)
        and any(isinstance(item, dict) and item.get("status") == "PRIMARY" and item.get("rolloutState") == "COMPLETED" for item in deployments)
    )


def current_task(prepare: object) -> tuple[dict | None, str, str | None]:
    ok, described, code = prepare.aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    services = described.get("services") if ok and isinstance(described, dict) else None
    if isinstance(services, list) and len(services) == 1 and isinstance(services[0], dict) and any(isinstance(item, dict) and item.get("rolloutState") == "FAILED" for item in services[0].get("deployments", [])):
        return None, "persistence-replacement-rollout-failed", None
    if not isinstance(services, list) or len(services) != 1 or not healthy_service(services[0]):
        return None, code if not ok else "persistence-replacement-service-not-healthy", None
    definition = services[0]["taskDefinition"]
    ok, listed, code = prepare.aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE, "--desired-status", "RUNNING")
    arns = listed.get("taskArns") if ok and isinstance(listed, dict) else None
    if not isinstance(arns, list) or len(arns) != 1 or not isinstance(arns[0], str):
        return None, code if not ok else "persistence-replacement-running-task-count-invalid", None
    ok, described, code = prepare.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arns[0])
    tasks = described.get("tasks") if ok and isinstance(described, dict) else None
    task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 else None
    if not isinstance(task, dict) or task.get("lastStatus") != "RUNNING" or task.get("taskDefinitionArn") != definition:
        return None, code if not ok else "persistence-replacement-current-task-invalid", None
    return task, "ok", definition


def replacement_task(prepare: object, original_arn: str, definition: str, deadline: float) -> tuple[dict | None, str]:
    while time.monotonic() < deadline:
        task, code, observed_definition = current_task(prepare)
        if task is not None and observed_definition != definition:
            return None, "persistence-replacement-task-definition-changed"
        if task is not None and observed_definition == definition and task.get("taskArn") != original_arn:
            return task, "ok"
        if code not in {"ok", "persistence-replacement-running-task-count-invalid", "persistence-replacement-current-task-invalid", "persistence-replacement-service-not-healthy"}:
            return None, code
        time.sleep(5)
    return None, "persistence-replacement-not-healthy"


def reconciled_original(prepare: object, arn: str) -> tuple[dict | None, str]:
    if not arn.startswith(f"arn:aws:ecs:{prepare.REGION}:{prepare.ACCOUNT}:task/{CLUSTER}/"):
        return None, "persistence-replacement-reconciliation-task-identity-invalid"
    ok, described, code = prepare.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
    tasks = described.get("tasks") if ok and isinstance(described, dict) else None
    task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 else None
    if isinstance(task, dict) and task.get("taskArn") == arn and task.get("lastStatus") in {"RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}:
        return None, "persistence-replacement-original-stop-pending" if task.get("desiredStatus") == "STOPPED" else "persistence-replacement-original-stop-uncertain"
    if not isinstance(task, dict) or task.get("taskArn") != arn or task.get("lastStatus") != "STOPPED" or task.get("stoppedReason") != "governed core-server-persistence replacement rehearsal":
        return None, code if not ok else "persistence-replacement-reconciliation-original-invalid"
    return task, "ok"


def receipt_matches_task(prepare, receipt: dict, task: dict, definition: str) -> tuple[bool, str]:
    """Bind both intended image/source and actual running digest before replacement."""
    expected_image = f"{prepare.ACCOUNT}.dkr.ecr.{prepare.REGION}.amazonaws.com/{prepare.REPOSITORY}@{receipt['image_digest']}"
    ok, described, code = prepare.aws("ecs", "describe-task-definition", "--task-definition", definition)
    value = described.get("taskDefinition") if ok and isinstance(described, dict) else None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
    if not ok: return False, code
    if not isinstance(value, dict) or value.get("taskDefinitionArn") != definition or not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False, "persistence-replacement-receipt-definition-unproven"
    container = containers[0]
    environment = container.get("environment", [])
    sources = [item.get("value") for item in environment if isinstance(item, dict) and item.get("name") == "PLATFORM_SOURCE_COMMIT_SHA"] if isinstance(environment, list) else []
    if container.get("name") != "core-server-persistence" or container.get("image") != expected_image or sources != [receipt["source_revision"]]:
        return False, "persistence-replacement-receipt-definition-mismatch"
    running = task.get("containers")
    if task.get("taskDefinitionArn") != definition or not isinstance(running, list) or len(running) != 1 or not isinstance(running[0], dict) or running[0].get("name") != "core-server-persistence" or running[0].get("image") != expected_image:
        return False, "persistence-replacement-receipt-runtime-mismatch"
    overrides = task.get("overrides", {})
    if not isinstance(overrides, dict) or overrides.get("taskRoleArn") or overrides.get("executionRoleArn"):
        return False, "persistence-replacement-runtime-override-unproven"
    container_overrides = overrides.get("containerOverrides", [])
    if not isinstance(container_overrides, list): return False, "persistence-replacement-runtime-override-unproven"
    for item in container_overrides:
        if not isinstance(item, dict) or item.get("command") or item.get("environment") or item.get("environmentFiles"):
            return False, "persistence-replacement-runtime-override-unproven"
    runnable, code = prepare.candidate_runnable_manifest(receipt)
    if runnable is None: return False, code
    if running[0].get("imageDigest") not in {receipt["image_digest"], runnable}:
        return False, "persistence-replacement-receipt-runtime-digest-mismatch"
    return True, "ok"


def outcome(code: str) -> str:
    if code == "persistence-replacement-rollout-failed": return "failed"
    if code in {"persistence-replacement-original-stop-pending", "persistence-replacement-not-healthy", "persistence-replacement-service-not-healthy", "persistence-replacement-running-task-count-invalid", "persistence-replacement-current-task-invalid"}: return "pending"
    if code.startswith("aws-") or code.endswith("uncertain"): return "uncertain"
    return "blocked"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--reconcile-original-task")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", "persistence-replacement-arguments-invalid")
    prepare = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]:
        return report("blocked", "persistence-replacement-preconditions-not-proven")
    original, code, definition = current_task(prepare)
    current_code = code
    if original is not None and definition is not None:
        bound, code = receipt_matches_task(prepare, receipt, original, definition)
        if not bound:
            return report(outcome(code), code)
    if args.reconcile_original_task:
        stopped, code = reconciled_original(prepare, args.reconcile_original_task)
        if stopped is None:
            return report(outcome(code), code, facts={"original_task": args.reconcile_original_task})
        if definition is None or original is None:
            return report(outcome(current_code), current_code, facts={"original_task": args.reconcile_original_task})
        if original.get("taskArn") == args.reconcile_original_task or stopped.get("taskDefinitionArn") != definition:
            return report("blocked", "persistence-replacement-reconciliation-replacement-invalid")
        stopped_at = stopped.get("stoppedAt")
        if not isinstance(stopped_at, str):
            return report("blocked", "persistence-replacement-reconciliation-original-invalid")
        return report("replaced", "persistence-server-replaced-read-proof-required", facts={"candidate_image_digest": receipt["image_digest"], "source_revision": receipt["source_revision"], "runtime_task_definition": definition, "original_task": args.reconcile_original_task, "replacement_task": original["taskArn"], "recovery_boundary": stopped_at})
    if original is None or definition is None:
        return report(outcome(code), code)
    original_arn = original.get("taskArn")
    if not isinstance(original_arn, str):
        return report("blocked", "persistence-replacement-current-task-invalid")
    boundary = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print(json.dumps({"verdict": "pending", "facts": {"original_task": original_arn, "recovery_boundary": boundary}}), file=sys.stderr, flush=True)
    ok, _, code = prepare.aws("ecs", "stop-task", "--cluster", CLUSTER, "--task", original_arn, "--reason", "governed core-server-persistence replacement rehearsal")
    if not ok:
        return report("uncertain", code, facts={"original_task": original_arn, "recovery_boundary": boundary})
    replacement, code = replacement_task(prepare, original_arn, definition, time.monotonic() + 600)
    if replacement is None or not isinstance(replacement.get("taskArn"), str):
        return report(outcome(code), code, facts={"original_task": original_arn, "recovery_boundary": boundary})
    bound, code = receipt_matches_task(prepare, receipt, replacement, definition)
    if not bound:
        return report(outcome(code), code, facts={"original_task": original_arn, "replacement_task": replacement["taskArn"], "recovery_boundary": boundary})
    return report("replaced", "persistence-server-replaced-read-proof-required", facts={
        "candidate_image_digest": receipt["image_digest"],
        "source_revision": receipt["source_revision"],
        "runtime_task_definition": definition,
        "original_task": original_arn,
        "replacement_task": replacement["taskArn"],
        "recovery_boundary": boundary,
    })


if __name__ == "__main__":
    raise SystemExit(main())

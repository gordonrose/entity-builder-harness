#!/usr/bin/env python3
"""Replace exactly one healthy persistence server task and record the boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement.impl
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
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
        if task is not None and observed_definition == definition and task.get("taskArn") != original_arn:
            return task, "ok"
        if code not in {"persistence-replacement-running-task-count-invalid", "persistence-replacement-current-task-invalid", "persistence-replacement-service-not-healthy"}:
            return None, code
        time.sleep(5)
    return None, "persistence-replacement-not-healthy"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
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
    if original is None or definition is None:
        return report("blocked", code)
    original_arn = original.get("taskArn")
    if not isinstance(original_arn, str):
        return report("blocked", "persistence-replacement-current-task-invalid")
    boundary = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ok, _, code = prepare.aws("ecs", "stop-task", "--cluster", CLUSTER, "--task", original_arn, "--reason", "governed core-server-persistence replacement rehearsal")
    if not ok:
        return report("blocked", code)
    replacement, code = replacement_task(prepare, original_arn, definition, time.monotonic() + 600)
    if replacement is None or not isinstance(replacement.get("taskArn"), str):
        return report("blocked", code, facts={"original_task": original_arn, "recovery_boundary": boundary})
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

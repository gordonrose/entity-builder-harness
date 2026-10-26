#!/usr/bin/env python3
"""Replace exactly one healthy persistence server task and record the boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement.impl
#   version: 5
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Replace one exact healthy persistence server task and bind the succeeding private read proof to its recovery boundary.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh
#   effects: [aws-mutation, writes-files]
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


def proof_receipts():
    path = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"
    spec = importlib.util.spec_from_file_location("persistence_proof_receipts", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def retained_reconciliation_receipt(
    receipts: object,
    *,
    stopped: dict,
    successor: dict,
    definition: str,
    image_digest: str,
) -> Path | None:
    """Reuse only the exact receipt written before an interrupted response.

    The replacement boundary is selected before the stop mutation. A later
    reconciliation cannot recreate that timestamp, so rebuilding a receipt
    would conflict with the durable first observation. This deliberately
    trusts no filename alone: integrity, every task identity, the immutable
    image, and the successor relationship must all agree with fresh provider
    observations made by the caller.
    """
    original_arn = stopped.get("taskArn")
    successor_arn = successor.get("taskArn")
    successor_started = successor.get("startedAt")
    if not isinstance(original_arn, str) or not isinstance(successor_arn, str) or not isinstance(successor_started, str):
        return None
    destination = receipts.RECEIPTS / f"server-replacement-controlled-replacement-{original_arn.rsplit('/', 1)[-1]}.json"
    if not destination.is_file():
        return None
    try:
        existing = receipts.validate(json.loads(destination.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("persistence-replacement-reconciliation-receipt-invalid")
    task = existing["task"]
    context = existing["context"]
    if (
        existing["proof_type"] != "server-replacement"
        or existing["operation"] != "controlled-replacement"
        or existing["provenance"].get("controller") != "rehearse-server-replacement"
        or task.get("arn") != original_arn
        or task.get("definition") != definition
        or task.get("image_digest") != image_digest
        or task.get("terminal_status") != "STOPPED"
        or task.get("result_code") != "PERSISTENCE_SERVER_REPLACED"
        or task.get("stopped_reason") != "governed core-server-persistence replacement rehearsal"
        or context.get("original_stopped_reason") != "governed core-server-persistence replacement rehearsal"
        or context.get("successor_task_arn") != successor_arn
        or context.get("successor_started_at") != successor_started
        or context.get("runtime_task_definition") != definition
    ):
        raise ValueError("persistence-replacement-reconciliation-receipt-mismatch")
    return destination


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


def historical_service_task(prepare: object, task: object, digest: str) -> bool:
    """Accept a retained service task only when its own immutable image matches.

    A later rollback/return legitimately creates a different task-definition
    revision.  Historical proof must therefore be bound to that task's own
    definition and digest, never substituted with the current service task.
    """
    if not isinstance(task, dict) or task.get("group") != f"service:{SERVICE}":
        return False
    definition = task.get("taskDefinitionArn")
    if not isinstance(definition, str):
        return False
    ok, described, _ = prepare.aws("ecs", "describe-task-definition", "--task-definition", definition)
    containers = described.get("taskDefinition", {}).get("containerDefinitions", []) if ok and isinstance(described, dict) else []
    image = containers[0].get("image") if isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) else None
    return isinstance(image, str) and image.endswith("@" + digest)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--reconcile-original-task")
    parser.add_argument("--reconcile-successor-task")
    parser.add_argument("--capture-completed-original-task")
    parser.add_argument("--capture-completed-successor-task")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    capture_requested = args.capture_completed_original_task is not None or args.capture_completed_successor_task is not None
    if unknown or args.receipt is None or (capture_requested and (not isinstance(args.capture_completed_original_task, str) or not isinstance(args.capture_completed_successor_task, str))) or (capture_requested and args.reconcile_original_task is not None):
        return report("blocked", "persistence-replacement-arguments-invalid")
    if args.validate_arguments: print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[],"proof_contract":{"proof_type":"server-replacement","operation":"controlled-replacement","result_code":"PERSISTENCE_SERVER_REPLACED","family":"kanbien-core-platform-core-server-persistence","deadline_workload":None}})); return 0
    prepare = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]:
        return report("blocked", "persistence-replacement-preconditions-not-proven")
    if capture_requested:
        stopped, code = reconciled_original(prepare, args.capture_completed_original_task)
        ok, described, successor_code = prepare.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.capture_completed_successor_task)
        tasks = described.get("tasks") if ok and isinstance(described, dict) else None
        successor = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
        if stopped is None or not isinstance(successor, dict) or successor.get("taskArn") != args.capture_completed_successor_task or not historical_service_task(prepare, stopped, receipt["image_digest"]) or not historical_service_task(prepare, successor, receipt["image_digest"]):
            return report("blocked", code if stopped is None else successor_code if not ok else "persistence-replacement-historic-task-identity-invalid")
        stopped_at, successor_started = stopped.get("stoppedAt"), successor.get("startedAt")
        if not isinstance(stopped_at, str) or not isinstance(successor_started, str) or successor.get("taskArn") == stopped.get("taskArn"):
            return report("blocked", "persistence-replacement-historic-task-relationship-invalid")
        try:
            receipt_body = proof_receipts().make(proof_type="server-replacement", operation="controlled-replacement", task=stopped, image_digest=receipt["image_digest"], result_code="PERSISTENCE_SERVER_REPLACED", context={"original_stopped_reason": "governed core-server-persistence replacement rehearsal", "successor_task_arn": args.capture_completed_successor_task, "successor_started_at": successor_started, "runtime_task_definition": stopped["taskDefinitionArn"], "recovery_boundary": stopped_at}, controller="rehearse-server-replacement", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
            proof_path = proof_receipts().persist(receipt_body)
        except Exception:
            return report("blocked", "persistence-replacement-receipt-persistence-failed")
        return report("replaced", "persistence-server-replaced-read-proof-required", facts={"candidate_image_digest": receipt["image_digest"], "source_revision": receipt["source_revision"], "runtime_task_definition": stopped["taskDefinitionArn"], "original_task": args.capture_completed_original_task, "replacement_task": args.capture_completed_successor_task, "recovery_boundary": stopped_at, "proof_receipt": str(proof_path.relative_to(ROOT))})
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
        if not isinstance(args.reconcile_successor_task, str):
            return report("blocked", "persistence-replacement-reconciliation-successor-required")
        ok, described, code = prepare.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_successor_task)
        tasks = described.get("tasks") if ok and isinstance(described, dict) else None
        successor = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
        if not isinstance(successor, dict) or successor.get("taskArn") != args.reconcile_successor_task or successor.get("group") != f"service:{SERVICE}":
            return report("blocked", code if not ok else "persistence-replacement-reconciliation-successor-invalid")
        if successor.get("taskArn") == args.reconcile_original_task or stopped.get("taskDefinitionArn") != definition or successor.get("taskDefinitionArn") != definition:
            return report("blocked", "persistence-replacement-reconciliation-replacement-invalid")
        stopped_at = stopped.get("stoppedAt")
        if not isinstance(stopped_at, str) or not isinstance(successor.get("startedAt"), str):
            return report("blocked", "persistence-replacement-reconciliation-original-invalid")
        try:
            retained = retained_reconciliation_receipt(
                proof_receipts(),
                stopped=stopped,
                successor=successor,
                definition=definition,
                image_digest=receipt["image_digest"],
            )
            if retained is not None:
                return report("replaced", "persistence-server-replaced-read-proof-required", facts={"candidate_image_digest": receipt["image_digest"], "source_revision": receipt["source_revision"], "runtime_task_definition": definition, "original_task": args.reconcile_original_task, "replacement_task": args.reconcile_successor_task, "recovery_boundary": json.loads(retained.read_text(encoding="utf-8"))["context"]["recovery_boundary"], "proof_receipt": str(retained.relative_to(ROOT))})
            receipt_body = proof_receipts().make(proof_type="server-replacement", operation="controlled-replacement", task=stopped, image_digest=receipt["image_digest"], result_code="PERSISTENCE_SERVER_REPLACED", context={"original_stopped_reason": "governed core-server-persistence replacement rehearsal", "successor_task_arn": args.reconcile_successor_task, "successor_started_at": successor["startedAt"], "runtime_task_definition": definition, "recovery_boundary": stopped_at}, controller="rehearse-server-replacement", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
            proof_path = proof_receipts().persist(receipt_body)
        except ValueError as error:
            return report("blocked", str(error))
        except Exception:
            return report("blocked", "persistence-replacement-receipt-persistence-failed")
        return report("replaced", "persistence-server-replaced-read-proof-required", facts={"candidate_image_digest": receipt["image_digest"], "source_revision": receipt["source_revision"], "runtime_task_definition": definition, "original_task": args.reconcile_original_task, "replacement_task": args.reconcile_successor_task, "recovery_boundary": stopped_at, "proof_receipt": str(proof_path.relative_to(ROOT))})
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
    stopped, code = reconciled_original(prepare, original_arn)
    if stopped is None:
        return report(outcome(code), code, facts={"original_task": original_arn, "replacement_task": replacement["taskArn"], "recovery_boundary": boundary})
    try:
        receipt_body = proof_receipts().make(
            proof_type="server-replacement", operation="controlled-replacement", task=stopped,
            image_digest=receipt["image_digest"], result_code="PERSISTENCE_SERVER_REPLACED",
            context={"original_stopped_reason": "governed core-server-persistence replacement rehearsal", "successor_task_arn": replacement["taskArn"], "successor_started_at": replacement["startedAt"], "runtime_task_definition": definition, "recovery_boundary": boundary},
            controller="rehearse-server-replacement", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        proof_path = proof_receipts().persist(receipt_body)
    except Exception:
        return report("blocked", "persistence-replacement-receipt-persistence-failed", facts={"original_task": original_arn, "replacement_task": replacement["taskArn"], "recovery_boundary": boundary})
    return report("replaced", "persistence-server-replaced-read-proof-required", facts={
        "candidate_image_digest": receipt["image_digest"],
        "source_revision": receipt["source_revision"],
        "runtime_task_definition": definition,
        "original_task": original_arn,
        "replacement_task": replacement["taskArn"],
        "recovery_boundary": boundary,
        "proof_receipt": str(proof_path.relative_to(ROOT)),
    })


if __name__ == "__main__":
    raise SystemExit(main())

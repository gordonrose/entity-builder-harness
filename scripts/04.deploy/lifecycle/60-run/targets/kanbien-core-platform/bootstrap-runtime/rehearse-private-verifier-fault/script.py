#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault.implementation
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Run one fixed private-verifier rejection or controller-timeout rehearsal without changing the accepted service or accepting arbitrary commands.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.sh
"""Bounded fault fixtures for the existing private verifier controller."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION = "kanbien-dev", "eu-west-1"
CLUSTER, SERVICE = "kanbien-core-platform", "kanbien-core-platform-bootstrap-runtime"
RUNTIME_STACK, FOUNDATION_STACK = "kanbien-core-platform-bootstrap-runtime", "kanbien-core-platform-foundation"
FAULT_CASES = {"expected-source-mismatch", "controller-deadline"}
MISMATCH_SOURCE_REVISION = "0000000000000000000000000000000000000000"
TIMEOUT_SLEEP_MILLISECONDS = 121_000
CLEANUP_WAIT_SECONDS = 120


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module-load-failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPLACEMENT = load_module(
    "accepted_workload_replacement",
    ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.py",
)
VERIFIER = load_module(
    "runtime_verifier",
    ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/verify.py",
)


def report(verdict: str, *codes: str, facts: dict | None = None) -> int:
    body = {"schema": "deploy/private-verifier-fault-rehearsal-report/v1", "target": "kanbien-core-platform", "scope": "bootstrap-runtime", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        body["facts"] = facts
    print(json.dumps(body, sort_keys=True))
    return 0 if verdict in {"prepared", "rejected-as-expected", "controller-deadline-confirmed"} else 1


def aws(*args: str):
    result = subprocess.run(["aws", *args, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if result.returncode:
        text = result.stderr.lower()
        return False, None, "aws-access-denied" if "accessdenied" in text or "not authorized" in text else "aws-command-failed"
    try:
        return True, json.loads(result.stdout), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def outputs(stack_name: str) -> tuple[dict[str, str] | None, str]:
    ok, described, code = aws("cloudformation", "describe-stacks", "--stack-name", stack_name)
    stacks = described.get("Stacks", []) if ok else []
    if not ok or len(stacks) != 1:
        return None, code if not ok else "stack-not-returned"
    return {item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", []) if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)}, "ok"


def fault_override(case: str) -> dict:
    container = {"name": "private-release-verifier"}
    if case == "expected-source-mismatch":
        container["environment"] = [{"name": "KANBIEN_EXPECTED_SOURCE_REVISION", "value": MISMATCH_SOURCE_REVISION}]
    else:
        container["command"] = ["-e", f"setTimeout(() => process.exit(0), {TIMEOUT_SLEEP_MILLISECONDS})"]
    return {"containerOverrides": [container]}


def task_log_contains(task: dict, code: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "private-verifier-evidence-unavailable"
    task_id = arn.rsplit("/", 1)[-1]
    ok, events, aws_code = aws("logs", "get-log-events", "--log-group-name", "/aws/ecs/kanbien-core-platform", "--log-stream-name", f"release-verifier/private-release-verifier/{task_id}", "--start-from-head")
    if not ok:
        return False, aws_code
    messages = [event.get("message") for event in events.get("events", []) if isinstance(event, dict)]
    return any(isinstance(message, str) and f'"code":"{code}"' in message for message in messages), "ok"


def task_exit_code(task: dict) -> int | None:
    containers = task.get("containers", []) if isinstance(task, dict) else []
    value = containers[0].get("exitCode") if containers and isinstance(containers[0], dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def wait_for_cleanup_stop(task_arn: str) -> tuple[dict | None, str]:
    deadline = time.monotonic() + CLEANUP_WAIT_SECONDS
    while time.monotonic() < deadline:
        state, task = VERIFIER.inspect_verifier_task(task_arn)
        if state != "ok" or not isinstance(task, dict):
            return None, "private-verifier-cleanup-state-uncertain"
        if task.get("lastStatus") == "STOPPED":
            return task, "ok"
        time.sleep(5)
    return None, "private-verifier-cleanup-not-stopped"


def service_unchanged(release: dict, original_task_arn: str) -> bool:
    task, code = REPLACEMENT.current_workload(release)
    return code == "ok" and isinstance(task, dict) and task.get("taskArn") == original_task_arn


def run_fault(case: str, verifier_definition: str, subnets: str, security_group: str) -> tuple[dict | None, str]:
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{security_group}],assignPublicIp=DISABLED}}"
    ok, result, code = aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", verifier_definition, "--launch-type", "FARGATE", "--count", "1", "--started-by", f"kanbien-core-platform-{case}", "--network-configuration", network, "--overrides", json.dumps(fault_override(case), separators=(",", ":")))
    tasks = result.get("tasks", []) if ok else []
    if not ok or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        return None, code if not ok else "private-verifier-fault-task-not-started"
    if tasks[0].get("taskDefinitionArn") != verifier_definition:
        return None, "private-verifier-fault-task-definition-mismatch"
    return tasks[0], "ok"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--case")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.case not in FAULT_CASES:
        return report("blocked", "private-verifier-fault-arguments-invalid")
    release = REPLACEMENT.accepted_release()
    if release is None:
        return report("blocked", "accepted-release-record-invalid")
    with tempfile.TemporaryDirectory() as directory:
        receipt_path = Path(directory) / "accepted-receipt.json"
        REPLACEMENT.receipt(release, receipt_path)
        accepted_task, code = REPLACEMENT.preflight(release, receipt_path)
        if accepted_task is None:
            return report("blocked", code)
        runtime_outputs, runtime_code = outputs(RUNTIME_STACK)
        foundation_outputs, foundation_code = outputs(FOUNDATION_STACK)
        verifier = runtime_outputs.get("ReleaseVerifierTaskDefinitionArn") if runtime_outputs else None
        subnets = foundation_outputs.get("PrivateSubnetIds") if foundation_outputs else None
        security_group = foundation_outputs.get("VerifierSecurityGroupId") if foundation_outputs else None
        if runtime_code != "ok" or foundation_code != "ok" or not all(isinstance(value, str) and value for value in (verifier, subnets, security_group)):
            return report("blocked", "private-verifier-fault-foundation-unavailable")
        deadline = VERIFIER.verifier_completion_deadline()
        if deadline is None:
            return report("blocked", "private-verifier-deadline-contract-invalid")
        facts = {"case": args.case, "accepted_source_revision": release["source_revision"], "accepted_image_digest": release["image_digest"], "accepted_runtime_task_definition": release["runtime_task_definition"], "verifier_task_definition": verifier, "completion_deadline_seconds": deadline, "accepted_server_task_suffix": REPLACEMENT.task_suffix(accepted_task)}
        if not args.execute:
            return report("prepared", "private-verifier-fault-ready", facts=facts)
        fixture, code = run_fault(args.case, verifier, subnets, security_group)
        if fixture is None:
            return report("blocked", code, facts=facts)
        fixture_arn = fixture["taskArn"]
        facts["fixture_task_suffix"] = REPLACEMENT.task_suffix(fixture)
        state, terminal = VERIFIER.wait_for_verifier_stop(fixture_arn, deadline, VERIFIER.inspect_verifier_task)
        if args.case == "expected-source-mismatch":
            if state != "stopped" or terminal is None:
                return report("blocked", "private-verifier-rejection-state-invalid", facts=facts)
            within, timing_code = VERIFIER.completed_within_deadline(terminal, deadline)
            rejected, log_code = task_log_contains(terminal, "KANBIEN_CORE_RELEASE_VERIFICATION_FAILED")
            exit_code = task_exit_code(terminal)
            if not within or exit_code is None or exit_code == 0 or not rejected or not service_unchanged(release, accepted_task["taskArn"]):
                return report("blocked", timing_code if not within else log_code if not rejected else "private-verifier-rejection-not-contained", facts=facts)
            facts["completion_duration_seconds"] = VERIFIER.verifier_duration_seconds(terminal)
            return report("rejected-as-expected", "private-verifier-source-mismatch-rejected", facts=facts)
        if state != "still-running" or terminal is None:
            return report("blocked", "private-verifier-controller-timeout-not-observed", facts=facts)
        if terminal.get("taskDefinitionArn") != verifier or not service_unchanged(release, accepted_task["taskArn"]):
            return report("blocked", "private-verifier-timeout-not-contained", facts=facts)
        ok, _, stop_code = aws("ecs", "stop-task", "--cluster", CLUSTER, "--task", fixture_arn, "--reason", "governed controller-deadline fixture cleanup")
        if not ok:
            return report("blocked", stop_code, facts=facts)
        cleaned, cleanup_code = wait_for_cleanup_stop(fixture_arn)
        if cleaned is None or not service_unchanged(release, accepted_task["taskArn"]):
            return report("blocked", cleanup_code if cleaned is None else "private-verifier-timeout-cleanup-not-contained", facts=facts)
        facts["cleanup_task_status"] = cleaned.get("lastStatus")
        return report("controller-deadline-confirmed", "private-verifier-controller-deadline-remote-task-still-running", "private-verifier-timeout-fixture-cleaned", facts=facts)


if __name__ == "__main__":
    raise SystemExit(main())

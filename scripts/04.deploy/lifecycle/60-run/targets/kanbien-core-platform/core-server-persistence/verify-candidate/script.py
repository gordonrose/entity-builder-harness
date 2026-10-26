#!/usr/bin/env python3
"""Run a fixed private, server-mediated persistence verification task."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import tempfile
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
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
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
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    # ECS describes environment fields as lower-case ``name``.  A
    # credential-bearing verifier definition must never pass this check just
    # because the controller read the provider response with the wrong case.
    environment = container.get("environment", [])
    secrets = container.get("secrets", [])
    if not isinstance(environment, list) or not isinstance(secrets, list) or secrets or not all(isinstance(item, dict) and isinstance(item.get("name"), str) for item in environment): return False
    return not any(item["name"].startswith("PERSISTENCE_POSTGRES") for item in environment)


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
        if not isinstance(tasks, list) or described.get("failures") or len(tasks) != len(batch) or not all(isinstance(task, dict) and isinstance(task.get("taskArn"), str) for task in tasks) or {task["taskArn"] for task in tasks} != set(batch):
            return None, "private-persistence-verifier-observation-uncertain"
        matching.extend(task["taskArn"] for task in tasks if task.get("startedBy") == operation)
    return (matching[0], "ok") if len(matching) == 1 else (None, "private-persistence-verifier-task-identity-unresolved")


def task_evidence():
    path = Path(__file__).resolve().parents[1] / "ecs-task-evidence.py"
    spec = importlib.util.spec_from_file_location("persistence_ecs_task_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def task_operation_bound(task: dict, mode: str) -> bool:
    return task_evidence().task_overrides_match(task, "private-persistence-verifier", {"PERSISTENCE_VERIFIER_MODE": mode, "PERSISTENCE_ACCEPTANCE_RECORD_ID": RECORD_ID, "PERSISTENCE_ACCEPTANCE_FACT": FACT})

def image_digest(task_definition: object) -> str | None:
    if not isinstance(task_definition, str):
        return None
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", task_definition)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
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


def accepted_completion(task: dict[str, object], seconds: int, mode: str, on_receipt=None) -> int:
    facts = {"verifier_task": task.get("taskArn"), "operation_id": task.get("startedBy")}
    observed_duration = duration(task)
    if observed_duration is None:
        return report("uncertain", "private-persistence-verifier-duration-unavailable", facts=facts)
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int:
        return report("uncertain", "persistence-task-exit-evidence-unavailable", facts=facts)
    failure = "private-persistence-verifier-completion-deadline-exceeded" if observed_duration > seconds else "private-persistence-verifier-unsuccessful-completion" if not exited_zero(task) else None
    if failure is not None:
        if on_receipt is not None:
            try:
                digest = image_digest(task.get("taskDefinitionArn"))
                if digest is None: raise ValueError()
                receipt = proof_receipts().make(proof_type="verifier", operation=mode, task=task, image_digest=digest, result_code=failure, context={"record_id": RECORD_ID, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration}, controller="verify-candidate", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
                on_receipt(proof_receipts().persist(receipt))
            except Exception:
                return report("failed", failure, "private-persistence-verifier-receipt-persistence-failed", facts=facts)
        return report("failed", failure, facts=facts)
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
        if on_receipt is not None: on_receipt(path)
    except Exception:
        return report("blocked", "private-persistence-verifier-receipt-persistence-failed")
    return report("accepted", "private-persistence-verifier-accepted", facts={"mode": mode, "verifier_task": arn, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, "proof_receipt": str(path.relative_to(ROOT)), "operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"})



class OperationError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def operation_paths(mode: str) -> tuple[Path, Path]:
    # The same bounded worktree metadata boundary used by the candidate and
    # delivery controllers; terminal evidence remains owned by proof-receipts.
    git_directory = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
    directory = Path(git_directory) / "private-persistence-verifier"
    if not Path(git_directory).is_absolute() or not Path(git_directory).is_dir():
        raise OperationError("private-persistence-verifier-operation-store-unavailable")
    try:
        directory.mkdir(mode=0o700)
        parent = os.open(directory.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(parent)
        finally: os.close(parent)
    except FileExistsError:
        pass
    if directory.is_symlink() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
        raise OperationError("private-persistence-verifier-operation-store-unsafe")
    return directory / (mode + ".json"), directory / (mode + ".lock")


def save_operation(path: Path, value: dict) -> None:
    body = {key: item for key, item in value.items() if key != "integrity"}
    value = {**body, "integrity": hashlib.sha256(canonical(body)).hexdigest()}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)


def load_operation(path: Path, mode: str) -> dict:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor) as handle:
            info = os.fstat(handle.fileno())
            if info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 65536:
                raise ValueError()
            value = json.load(handle)
        fields = {"schema", "mode", "operation_id", "predecessor", "request", "task_arn", "proof_receipt", "proof_sha256", "integrity"}
        if not isinstance(value, dict) or set(value) != fields or value["schema"] != "deploy/private-persistence-verifier-operation/v1" or value["mode"] != mode:
            raise ValueError()
        if re.fullmatch(r"kp-[a-f0-9]{32}", value["operation_id"]) is None or (value["predecessor"] is not None and re.fullmatch(r"kp-[a-f0-9]{32}", value["predecessor"]) is None):
            raise ValueError()
        if not isinstance(value["request"], dict) or set(value["request"]) != {"task_definition", "network", "overrides", "deadline_seconds"}:
            raise ValueError()
        request = value["request"]
        definition_prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/kanbien-core-platform-persistence-verifier:"
        expected_overrides = {"containerOverrides": [{"name": "private-persistence-verifier", "environment": [
            {"name": "PERSISTENCE_VERIFIER_MODE", "value": mode},
            {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": RECORD_ID},
            {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": FACT},
        ]}]}
        if not isinstance(request["task_definition"], str) or re.fullmatch(re.escape(definition_prefix) + r"[1-9][0-9]*", request["task_definition"]) is None or not isinstance(request["network"], str) or not request["network"] or request["overrides"] != expected_overrides or type(request["deadline_seconds"]) is not int or request["deadline_seconds"] <= 0:
            raise ValueError()
        if value["task_arn"] is not None and (not isinstance(value["task_arn"], str) or re.fullmatch(re.escape(f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/") + r"[a-f0-9]{32}", value["task_arn"]) is None):
            raise ValueError()
        if (value["proof_receipt"] is None) != (value["proof_sha256"] is None):
            raise ValueError()
        if value["proof_receipt"] is not None and (not isinstance(value["proof_receipt"], str) or not isinstance(value["proof_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", value["proof_sha256"]) is None):
            raise ValueError()
        body = {key: item for key, item in value.items() if key != "integrity"}
        if value["integrity"] != hashlib.sha256(canonical(body)).hexdigest(): raise ValueError()
        return value
    except (OSError, ValueError, TypeError):
        raise OperationError("private-persistence-verifier-operation-metadata-invalid") from None


@contextlib.contextmanager
def locked_operation(mode: str):
    path, lock_path = operation_paths(mode)
    if path.exists() and not lock_path.exists():
        raise OperationError("private-persistence-verifier-operation-metadata-missing")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise OperationError("private-persistence-verifier-operation-busy") from None
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1:
            raise OperationError("private-persistence-verifier-operation-store-unsafe")
        marker = os.read(descriptor, 128)
        if marker not in {b"", b"private-persistence-verifier-operation/v1\n"}:
            raise OperationError("private-persistence-verifier-operation-metadata-invalid")
        if marker and not path.exists():
            raise OperationError("private-persistence-verifier-operation-metadata-missing")
        value = load_operation(path, mode) if path.exists() else None
        if value is not None and not marker:
            os.write(descriptor, b"private-persistence-verifier-operation/v1\n"); os.fsync(descriptor)
        yield path, descriptor, value
    finally:
        os.close(descriptor)


def retained_completion(value: dict) -> dict | None:
    if value["proof_receipt"] is None: return None
    try:
        path = (ROOT / value["proof_receipt"]).resolve()
        if not path.is_relative_to(ROOT) or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != value["proof_sha256"]:
            raise ValueError()
        proof = proof_receipts().validate(json.loads(path.read_text()))
        task = proof["task"]
        if proof["proof_type"] != "verifier" or proof["operation"] != value["mode"] or task["arn"] != value["task_arn"] or task["definition"] != value["request"]["task_definition"]:
            raise ValueError()
        allowed = {"private-persistence-verifier-completion-deadline-exceeded", SUCCESS[value["mode"]] if task["exit_code"] == 0 else "private-persistence-verifier-unsuccessful-completion"}
        if task["result_code"] not in allowed: raise ValueError()
        return proof
    except (OSError, ValueError, KeyError, TypeError):
        raise OperationError("private-persistence-verifier-terminal-proof-unavailable") from None


def observe_reserved(value: dict, path: Path, seconds: int, mode: str, *, wait: bool = False) -> int:
    proof = retained_completion(value)
    if proof is not None:
        accepted = proof["task"]["exit_code"] == 0 and proof["task"]["result_code"] == SUCCESS[mode]
        return report("accepted" if accepted else "failed", proof["task"]["result_code"], facts={"operation_id": value["operation_id"], "mode": mode, "proof_receipt": value["proof_receipt"], "evidence_reuse": "historical-completion", "completed_at": proof["task"]["stopped_at"], "verifier_task": proof["task"]["arn"]})
    arn = value["task_arn"]
    if arn is None:
        arn, code = reconciliation_operation(value["operation_id"], value["request"]["task_definition"])
        if arn is None: return report("uncertain", code, facts={"operation_id": value["operation_id"]})
    started = time.monotonic()
    while True:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        tasks = described.get("tasks") if ok and isinstance(described, dict) else None
        if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict) or described.get("failures"):
            return report("uncertain", code if not ok else "private-persistence-verifier-controller-observation-uncertain", facts={"operation_id": value["operation_id"], "verifier_task": arn})
        task = tasks[0]
        if task.get("taskArn") != arn or task.get("taskDefinitionArn") != value["request"]["task_definition"] or task.get("startedBy") != value["operation_id"] or not task_operation_bound(task, mode):
            return report("uncertain", "private-persistence-verifier-controller-task-identity-mismatch", facts={"operation_id": value["operation_id"]})
        value["task_arn"] = arn; save_operation(path, value)
        if task.get("lastStatus") == "STOPPED":
            return accepted_completion(task, seconds, mode, on_receipt=lambda receipt: remember_completion(value, path, receipt))
        pending = task.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}
        remaining = seconds - (time.monotonic() - started)
        if not wait or not pending or remaining <= 0:
            return report("pending" if pending else "uncertain", "private-persistence-verifier-reconciliation-task-not-terminal", facts={"operation_id": value["operation_id"], "verifier_task": arn})
        time.sleep(min(5, remaining))


def remember_completion(value: dict, path: Path, receipt: Path) -> None:
    value["proof_receipt"] = receipt.relative_to(ROOT).as_posix()
    value["proof_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    save_operation(path, value)


def execute_reserved(args, seconds: int, task_definition: str, network: str, overrides: str) -> int:
    request = {"task_definition": task_definition, "network": network, "overrides": json.loads(overrides), "deadline_seconds": seconds}
    expected = None if args.expected_operation == "none" else args.expected_operation
    with locked_operation(args.mode) as (path, descriptor, value):
        if value is not None:
            if args.new_operation and value["operation_id"] == expected:
                if retained_completion(value) is None:
                    return report("blocked", "private-persistence-verifier-prior-operation-not-complete", facts={"operation_id": value["operation_id"]})
                predecessor = value["operation_id"]
                value = None
            else:
                if args.new_operation and value["predecessor"] != expected:
                    return report("blocked", "private-persistence-verifier-operation-predecessor-mismatch", facts={"operation_id": value["operation_id"]})
                if value["request"] != request:
                    return report("blocked", "private-persistence-verifier-operation-request-changed", facts={"operation_id": value["operation_id"]})
                return observe_reserved(value, path, seconds, args.mode)
        else:
            if args.new_operation and expected is not None:
                return report("blocked", "private-persistence-verifier-operation-predecessor-missing")
            predecessor = None
        value = {"schema": "deploy/private-persistence-verifier-operation/v1", "mode": args.mode, "operation_id": "kp-" + uuid.uuid4().hex, "predecessor": predecessor, "request": request, "task_arn": None, "proof_receipt": None, "proof_sha256": None}
        save_operation(path, value)
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, b"private-persistence-verifier-operation/v1\n"); os.fsync(descriptor)
        # Both reservation and permanent initialization sentinel are durable
        # before submission. Existing reservations never enter this branch.
        operation_id = value["operation_id"]
        report("pending", "private-persistence-verifier-submission-prepared", facts={"operation_id": operation_id}, stream=sys.stderr)
        sys.stderr.flush()
        ok, started, code = aws("ecs", "run-task", "--cluster", CLUSTER, "--task-definition", task_definition, "--launch-type", "FARGATE", "--count", "1", "--started-by", operation_id, "--client-token", operation_id, "--network-configuration", network, "--overrides", overrides)
        tasks = started.get("tasks", []) if ok and isinstance(started, dict) else []
        if not ok or not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str) or started.get("failures"):
            return report("failed" if ok and isinstance(started, dict) and isinstance(started.get("failures"), list) and started["failures"] else "uncertain", code if not ok else "private-persistence-verifier-not-started", facts={"operation_id": operation_id})
        arn = tasks[0]["taskArn"]
        if re.fullmatch(re.escape(f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/") + r"[a-f0-9]{32}", arn) is None:
            return report("uncertain", "private-persistence-verifier-controller-task-identity-mismatch", facts={"operation_id": operation_id})
        value["task_arn"] = arn
        save_operation(path, value)
        return observe_reserved(value, path, seconds, args.mode, wait=True)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode")
    parser.add_argument("--reconcile-task")
    parser.add_argument("--reconcile-operation")
    parser.add_argument("--new-operation", action="store_true")
    parser.add_argument("--expected-operation")
    parser.add_argument("--capture-completed-task")
    parser.add_argument("--qualified-receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.mode not in SUCCESS or (args.reconcile_task is not None and args.capture_completed_task is not None) or (args.capture_completed_task is not None and args.qualified_receipt is None) or (args.capture_completed_task is None and args.qualified_receipt is not None):
        return report("blocked", "private-persistence-verification-arguments-invalid")
    if args.reconcile_operation is not None and (args.reconcile_task is not None or args.capture_completed_task is not None or re.fullmatch(r"kp-[a-f0-9]{32}", args.reconcile_operation) is None):
        return report("blocked", "private-persistence-verifier-reconciliation-operation-invalid")
    if args.new_operation != (args.expected_operation is not None) or (args.expected_operation is not None and args.expected_operation != "none" and re.fullmatch(r"kp-[a-f0-9]{32}", args.expected_operation) is None) or (args.new_operation and any((args.reconcile_task, args.reconcile_operation, args.capture_completed_task))):
        return report("blocked", "private-persistence-verifier-new-operation-arguments-invalid")
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": [], "proof_contract": {"proof_type":"verifier","operation":args.mode,"result_code":SUCCESS[args.mode],"family":"kanbien-core-platform-persistence-verifier","deadline_workload":"private-release-verifier"}}))
        return 0
    if args.reconcile_operation is not None or args.reconcile_task is not None:
        try:
            with locked_operation(args.mode) as (path, descriptor, reserved):
                if reserved is not None and (reserved["operation_id"] == args.reconcile_operation or args.reconcile_task is not None and reserved["task_arn"] in {None, args.reconcile_task}):
                    # This read-only recovery concerns the original reservation,
                    # even when today's selected definition or deadline changed.
                    # A later new operation still runs all current prerequisites.
                    if retained_completion(reserved) is None and not no_direct_database_credential(reserved["request"]["task_definition"]):
                        return report("blocked", "private-persistence-verifier-isolation-not-proven")
                    if args.reconcile_task is not None:
                        if re.fullmatch(re.escape(f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/") + r"[a-f0-9]{32}", args.reconcile_task) is None:
                            return report("blocked", "private-persistence-verifier-reconciliation-task-identity-invalid")
                        reserved["task_arn"] = args.reconcile_task
                    return observe_reserved(reserved, path, reserved["request"]["deadline_seconds"], args.mode)
        except OperationError as error:
            return report("pending" if str(error).endswith("-busy") else "blocked", str(error))
        except (OSError, subprocess.SubprocessError):
            return report("blocked", "private-persistence-verifier-operation-store-unavailable")
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
    if args.reconcile_operation is not None:
        args.reconcile_task, code = reconciliation_operation(args.reconcile_operation, task_definition)
        if args.reconcile_task is None:
            return report("uncertain", code, facts={"operation_id": args.reconcile_operation})
    if args.reconcile_task is not None:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or not isinstance(listed, list) or len(listed) != 1 or not isinstance(listed[0], dict):
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
        task = listed[0] if isinstance(listed, list) and len(listed) == 1 and isinstance(listed[0], dict) else None
        if not isinstance(task, dict) or task.get("taskArn") != args.capture_completed_task or not historical_task_identity(task, expected_digest) or not task_operation_bound(task, args.mode):
            return report("blocked", code if not ok else "private-persistence-verifier-historic-task-identity-invalid")
        return accepted_completion(task, seconds, args.mode)
    try:
        return execute_reserved(args, seconds, task_definition, network, overrides)
    except OperationError as error:
        return report("pending" if str(error).endswith("-busy") else "blocked", str(error))
    except (OSError, subprocess.SubprocessError):
        return report("blocked", "private-persistence-verifier-operation-store-unavailable")


if __name__ == "__main__":
    raise SystemExit(main())

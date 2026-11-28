#!/usr/bin/env python3
"""Run a fixed private, server-mediated persistence verification task."""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
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
_AWS_CLI = None
_MIGRATION_HELPERS = None


def migration_helpers():
    global _MIGRATION_HELPERS
    if _MIGRATION_HELPERS is None:
        path = Path(__file__).resolve().parents[1] / "run-migration/script.py"
        spec = importlib.util.spec_from_file_location("verifier_migration_helpers", path)
        _MIGRATION_HELPERS = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MIGRATION_HELPERS)
    return _MIGRATION_HELPERS


def runtime_context(runtime):
    if runtime is None:
        return {"cluster_arn": CLUSTER, "family": "kanbien-core-platform-persistence-verifier",
                "container_name": "private-persistence-verifier", "log_group": LOG_GROUP,
                "log_stream_prefix": "persistence-verifier"}
    return migration_helpers().runtime_context(runtime, "private-persistence-verifier")


def task_prefix(context):
    return migration_helpers().runtime_task_prefix(context)


def aws_cli():
    global _AWS_CLI
    if _AWS_CLI is None:
        spec = importlib.util.spec_from_file_location("aws_cli", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cli.py")
        _AWS_CLI = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_AWS_CLI)
    return _AWS_CLI


def aws(*parts: str):
    cli = aws_cli()
    try:
        value = cli.invoke_json(
            ["aws", *parts, "--cli-connect-timeout", str(AWS_CONNECT_TIMEOUT_SECONDS), "--cli-read-timeout", str(AWS_READ_TIMEOUT_SECONDS), "--profile", PROFILE, "--region", REGION, "--output", "json"],
            timeout=AWS_PROCESS_TIMEOUT_SECONDS, empty_body="empty-string", object_only=False, environment={**os.environ, "AWS_PAGER": ""},
        )
        return True, value, "ok"
    except cli.CliFailure as failure:
        return False, None, failure.code

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


def failed_task_log(arn: object, *, runtime=None, provider=None) -> dict[str, object]:
    """One approved read of a positively identified failed verifier stream."""
    context = runtime_context(runtime)
    if context is None or runtime is not None and not callable(provider): return {"task_log_observation": "unavailable"}
    if not isinstance(arn, str) or re.fullmatch(re.escape(task_prefix(context)) + r"[0-9a-f]{32}", arn) is None:
        return {"task_log_observation": "unavailable"}
    stream = context["log_stream_prefix"] + "/" + context["container_name"] + "/" + arn.rsplit("/", 1)[-1]
    try:
        ok, value, _ = (aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", stream, "--start-from-head", "--limit", "100")
    except Exception:
        return {"task_log_observation": "failed"}
    if not ok:
        return {"task_log_observation": "failed"}
    try:
        path = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/binding.py"
        specification = importlib.util.spec_from_file_location("verifier_task_diagnostics", path)
        module = importlib.util.module_from_spec(specification)
        assert specification and specification.loader
        specification.loader.exec_module(module)
        failure, observation = module.collect_persistence_task_failure(value, "verification")
        return {"task_log_observation": observation, **({"task_failure": failure} if failure is not None else {})}
    except Exception:
        return {"task_log_observation": "failed"}


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


def log_accepted(task: dict[str, object], expected: str, *, runtime=None, provider=None) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "private-persistence-verifier-evidence-unavailable"
    context = runtime_context(runtime)
    if context is None or runtime is not None and (not callable(provider) or not migration_helpers().runtime_task_matches(task, context)):
        return False, "private-persistence-verifier-evidence-unavailable"
    stream = f"{context['log_stream_prefix']}/{context['container_name']}/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = (aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return False, code
    messages = [event.get("message") for event in events.get("events", []) if isinstance(event, dict)] if isinstance(events, dict) else []
    return (True, "ok") if any(accepted_message(message, expected) for message in messages) else (False, "private-persistence-verifier-evidence-mismatch")


def no_direct_database_credential(task_definition: str, *, runtime=None, provider=None) -> bool:
    context = runtime_context(runtime)
    if context is None or runtime is not None and not callable(provider): return False
    ok, definition, _ = (aws if provider is None else provider)("ecs", "describe-task-definition", "--task-definition", task_definition)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    if runtime is not None and (value.get("taskDefinitionArn") != task_definition or container.get("name") != context["container_name"]): return False
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


def task_execution():
    path = Path(__file__).resolve().parents[6] / "shared/provider-adapters/aws/tasks.py"
    spec = importlib.util.spec_from_file_location("persistence_task_execution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reconciliation_operation(operation: str, definition: str, *, runtime=None, provider=None) -> tuple[str | None, str]:
    context = runtime_context(runtime)
    if context is None or runtime is not None and not callable(provider): return None, "private-persistence-verifier-observation-uncertain"
    tasks = task_execution()
    try:
        found = tasks.reconcile_task(tasks.cli_provider(aws if provider is None else provider), cluster=context["cluster_arn"], definition=definition, operation_id=operation, validate_task=lambda task: task)
        return found["taskArn"], "ok"
    except tasks.TaskFailure as failure:
        return None, "private-persistence-verifier-task-identity-unresolved" if failure.code == "reconciliation-unresolved" else "private-persistence-verifier-observation-uncertain"


def task_evidence():
    path = Path(__file__).resolve().parents[1] / "ecs-task-evidence.py"
    spec = importlib.util.spec_from_file_location("persistence_ecs_task_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def task_operation_bound(task: dict, mode: str, *, runtime=None) -> bool:
    context = runtime_context(runtime)
    return context is not None and task_evidence().task_overrides_match(task, context["container_name"], {"PERSISTENCE_VERIFIER_MODE": mode, "PERSISTENCE_ACCEPTANCE_RECORD_ID": RECORD_ID, "PERSISTENCE_ACCEPTANCE_FACT": FACT})

def image_digest(task_definition: object, *, runtime=None, provider=None) -> str | None:
    if not isinstance(task_definition, str):
        return None
    context = runtime_context(runtime)
    if context is None or runtime is not None and not callable(provider): return None
    ok, definition, _ = (aws if provider is None else provider)("ecs", "describe-task-definition", "--task-definition", task_definition)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    if runtime is not None and (not isinstance(value, dict) or value.get("taskDefinitionArn") != task_definition): return None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
    if runtime is not None and (not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or containers[0].get("name") != context["container_name"]): return None
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


def accepted_completion(task: dict[str, object], seconds: int, mode: str, on_receipt=None, *, runtime=None, provider=None, receipt_storage=None) -> int:
    context = runtime_context(runtime)
    if context is None: return report("blocked", "private-persistence-verifier-operation-runtime-invalid")
    if runtime is not None and (not callable(provider) or receipt_storage is None or not callable(on_receipt)):
        return report("blocked", "private-persistence-verifier-operation-storage-invalid")
    if runtime is not None and (not migration_helpers().runtime_task_matches(task, context) or not task_operation_bound(task, mode, runtime=runtime)):
        return report("uncertain", "private-persistence-verifier-controller-task-identity-mismatch")
    prefix = task_prefix(context)
    selected = {"runtime": runtime, "provider": provider} if runtime is not None or provider is not None else {}
    facts = {}
    for key, item, pattern in (("verifier_task", task.get("taskArn"), re.escape(prefix) + r"[0-9a-f]{32}"),
                               ("operation_id", task.get("startedBy"), r"kp-[0-9a-f]{32}")):
        if isinstance(item, str) and re.fullmatch(pattern, item):
            facts[key] = item
    if task.get("lastStatus") != "STOPPED":
        return report("uncertain", "private-persistence-verifier-reconciliation-task-not-terminal", facts=facts)
    observed_duration = duration(task)
    if observed_duration is None:
        return report("uncertain", "private-persistence-verifier-duration-unavailable", facts=facts)
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int:
        return report("uncertain", "persistence-task-exit-evidence-unavailable", facts=facts)
    failure = "private-persistence-verifier-completion-deadline-exceeded" if observed_duration > seconds else "private-persistence-verifier-unsuccessful-completion" if not exited_zero(task) else None
    if failure is not None:
        if not exited_zero(task):
            facts.update(failed_task_log(task.get("taskArn"), **selected))
        if on_receipt is not None:
            try:
                digest = image_digest(task.get("taskDefinitionArn"), **selected)
                if digest is None: raise ValueError()
                receipt = proof_receipts().make(proof_type="verifier", operation=mode, task=task, image_digest=digest, result_code=failure, context={"record_id": RECORD_ID, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration}, controller="verify-candidate", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix)
                reference = migration_helpers().retain_completion(proof_receipts(), receipt, root=ROOT, storage=receipt_storage,
                    task_arn_prefix=prefix, on_receipt=on_receipt)
                # Publish a usable failure reference only after both immutable
                # receipt and the original operation journal retain it. A mere
                # failed verdict (including persistence failure) is not proof.
                facts.update(mode=mode, proof_receipt=reference["path"],
                             proof_sha256=reference["sha256"],
                             evidence_reuse="fresh-terminal-observation")
            except Exception:
                return report("uncertain" if receipt_storage is not None else "failed", failure, "private-persistence-verifier-receipt-persistence-failed", facts=facts)
        return report("failed", failure, facts=facts)
    accepted, code = log_accepted(task, SUCCESS[mode], **selected)
    if not accepted:
        return report("uncertain" if code.startswith("aws-") else "pending", code, facts=facts)
    arn = task.get("taskArn")
    digest = image_digest(task.get("taskDefinitionArn"), **selected)
    if not isinstance(arn, str) or digest is None:
        return report("blocked", "private-persistence-verifier-receipt-identity-unavailable")
    try:
        receipt = proof_receipts().make(
            proof_type="verifier", operation=mode, task=task, image_digest=digest,
            result_code=SUCCESS[mode], context={"record_id": RECORD_ID, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration},
            controller="verify-candidate", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix,
        )
        reference = migration_helpers().retain_completion(proof_receipts(), receipt, root=ROOT, storage=receipt_storage,
            task_arn_prefix=prefix, on_receipt=on_receipt)
    except Exception:
        return report("uncertain" if receipt_storage is not None else "blocked", "private-persistence-verifier-receipt-persistence-failed")
    return report("accepted", "private-persistence-verifier-accepted", facts={"mode": mode, "verifier_task": arn, "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, "proof_receipt": reference["path"], "operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"})



class OperationError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def task_journal():
    path = Path(__file__).resolve().parents[6] / "shared/provider-adapters/aws/task_journal.py"
    spec = importlib.util.spec_from_file_location("persistence_task_journal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operation_paths(mode: str) -> tuple[Path, Path]:
    git_directory = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
    journal = task_journal()
    try: directory = journal.directory(git_directory, "private-persistence-verifier")
    except journal.JournalFailure as error: raise OperationError("private-persistence-verifier-" + str(error)) from None
    return directory / (mode + ".json"), directory / (mode + ".lock")


def save_operation(path: Path, value: dict) -> None:
    task_journal().save(path, value)


def load_operation(path: Path, mode: str) -> dict:
    try:
        return validate_operation(task_journal().read(path), mode)
    except (OSError, ValueError, TypeError):
        raise OperationError("private-persistence-verifier-operation-metadata-invalid") from None


def validate_request(request, mode):
    required = {"task_definition", "network", "overrides", "deadline_seconds"}
    if mode not in SUCCESS or not isinstance(request, dict) or set(request) not in (required, required | {"runtime"}): raise ValueError()
    if "runtime" in request and request["runtime"] is None: raise ValueError()
    context = runtime_context(request.get("runtime"))
    if context is None: raise ValueError()
    definition_prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{context['family']}:"
    expected_overrides = {"containerOverrides": [{"name": context["container_name"], "environment": [
        {"name": "PERSISTENCE_VERIFIER_MODE", "value": mode},
        {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": RECORD_ID},
        {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": FACT},
    ]}]}
    if not isinstance(request["task_definition"], str) or re.fullmatch(re.escape(definition_prefix) + r"[1-9][0-9]*", request["task_definition"]) is None or not isinstance(request["network"], str) or not request["network"] or request["overrides"] != expected_overrides or type(request["deadline_seconds"]) is not int or request["deadline_seconds"] <= 0: raise ValueError()
    return context


def validate_operation(value: dict, mode: str) -> dict:
    try:
        fields = {"schema", "mode", "operation_id", "predecessor", "request", "task_arn", "proof_receipt", "proof_sha256", "integrity"}
        if mode not in SUCCESS or not isinstance(value, dict) or set(value) != fields or value["schema"] != "deploy/private-persistence-verifier-operation/v1" or value["mode"] != mode:
            raise ValueError()
        if re.fullmatch(r"kp-[a-f0-9]{32}", value["operation_id"]) is None or (value["predecessor"] is not None and re.fullmatch(r"kp-[a-f0-9]{32}", value["predecessor"]) is None):
            raise ValueError()
        request = value["request"]
        context = validate_request(request, mode)
        if value["task_arn"] is not None and (not isinstance(value["task_arn"], str) or re.fullmatch(re.escape(task_prefix(context)) + r"[a-f0-9]{32}", value["task_arn"]) is None):
            raise ValueError()
        if (value["proof_receipt"] is None) != (value["proof_sha256"] is None):
            raise ValueError()
        if value["proof_receipt"] is not None and (not isinstance(value["proof_receipt"], str) or not isinstance(value["proof_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", value["proof_sha256"]) is None):
            raise ValueError()
        body = {key: item for key, item in value.items() if key != "integrity"}
        if value["integrity"] != hashlib.sha256(canonical(body)).hexdigest(): raise ValueError()
        return value
    except (OSError, ValueError, TypeError, KeyError):
        raise OperationError("private-persistence-verifier-operation-metadata-invalid") from None


@contextlib.contextmanager
def locked_operation(mode: str):
    path, lock_path = operation_paths(mode)
    journal = task_journal()
    try:
        with journal.locked(path, lock_path, b"private-persistence-verifier-operation/v1\n", lambda item: load_operation(item, mode)) as locked:
            yield locked
    except journal.JournalFailure as error: raise OperationError("private-persistence-verifier-" + str(error)) from None


def retained_completion(value: dict, *, storage=None) -> dict | None:
    if value["proof_receipt"] is None: return None
    try:
        context = runtime_context(value["request"].get("runtime"))
        proof = proof_receipts().read({"path": value["proof_receipt"], "sha256": value["proof_sha256"]},
            root=ROOT, storage=storage, task_arn_prefix=task_prefix(context))
        task = proof["task"]
        if proof["proof_type"] != "verifier" or proof["operation"] != value["mode"] or task["arn"] != value["task_arn"] or task["definition"] != value["request"]["task_definition"]:
            raise ValueError()
        allowed = {"private-persistence-verifier-completion-deadline-exceeded", SUCCESS[value["mode"]] if task["exit_code"] == 0 else "private-persistence-verifier-unsuccessful-completion"}
        if task["result_code"] not in allowed: raise ValueError()
        if storage is not None and (proof["context"].get("record_id") != RECORD_ID or proof["context"].get("completion_deadline_seconds") != value["request"]["deadline_seconds"]): raise ValueError()
        return proof
    except Exception:
        raise OperationError("private-persistence-verifier-terminal-proof-unavailable") from None


def observe_reserved(value: dict, path: Path, seconds: int, mode: str, *, wait: bool = False, provider=None, storage=None, step_id=None) -> int:
    runtime = value["request"].get("runtime")
    context = runtime_context(runtime)
    if context is None: raise OperationError("private-persistence-verifier-operation-runtime-invalid")
    if runtime is not None and (storage is None or not callable(provider)):
        raise OperationError("private-persistence-verifier-operation-storage-invalid")
    selected = {"runtime": runtime, "provider": provider} if runtime is not None or provider is not None else {}
    proof = retained_completion(value, storage=storage)
    if proof is not None:
        accepted = proof["task"]["exit_code"] == 0 and proof["task"]["result_code"] == SUCCESS[mode]
        facts = {"operation_id": value["operation_id"], "mode": mode, "proof_receipt": value["proof_receipt"], "proof_sha256": value["proof_sha256"], "evidence_reuse": "historical-completion", "completed_at": proof["task"]["stopped_at"], "verifier_task": proof["task"]["arn"]}
        if proof["task"]["exit_code"] != 0:
            facts.update(failed_task_log(proof["task"]["arn"], **selected))
        return report("accepted" if accepted else "failed", proof["task"]["result_code"], facts=facts)
    arn = value["task_arn"]
    if runtime is not None and not no_direct_database_credential(value["request"]["task_definition"], **selected):
        return report("uncertain", "private-persistence-verifier-isolation-not-proven", facts={"operation_id": value["operation_id"]})
    if arn is None:
        arn, code = reconciliation_operation(value["operation_id"], value["request"]["task_definition"], **selected)
        if arn is None: return report("uncertain", code, facts={"operation_id": value["operation_id"]})
    execution = task_execution()
    def exact(task):
        if task.get("taskArn") != arn or not isinstance(arn, str) or re.fullmatch(re.escape(task_prefix(context)) + r"[a-f0-9]{32}", arn) is None or task.get("taskDefinitionArn") != value["request"]["task_definition"] or task.get("startedBy") != value["operation_id"] or not task_operation_bound(task, mode, runtime=runtime):
            raise execution.TaskFailure("observation-identity-mismatch")
        return task
    def read(_previous):
        task = execution.describe_task(execution.cli_provider(aws if provider is None else provider), cluster=context["cluster_arn"], arn=arn, validate_task=exact)
        if storage is None:
            value["task_arn"] = arn; save_operation(path, value)
        elif value["task_arn"] is None:
            attach_operation(value, storage, step_id, "retain_task", arn)
        return task
    try:
        task, terminal = execution.observe_until_terminal(read, seconds=seconds, interval=5, wait=wait,
            pending_states={"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"},
            monotonic=time.monotonic, sleep=time.sleep)
    except execution.TaskFailure as error:
        if error.code == "observation-identity-mismatch":
            return report("uncertain", "private-persistence-verifier-controller-task-identity-mismatch", facts={"operation_id": value["operation_id"]})
        return report("uncertain", error.provider_code or "private-persistence-verifier-controller-observation-uncertain", facts={"operation_id": value["operation_id"], "verifier_task": arn})
    if terminal:
        retention = {"runtime": runtime, "provider": provider, "receipt_storage": storage} if storage is not None else {}
        return accepted_completion(task, seconds, mode, on_receipt=lambda receipt: remember_completion(value, path, receipt, storage=storage, step_id=step_id), **retention)
    pending = task.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}
    return report("pending" if pending else "uncertain", "private-persistence-verifier-reconciliation-task-not-terminal", facts={"operation_id": value["operation_id"], "verifier_task": arn})


def attach_operation(value, storage, step_id, method, argument):
    journal = task_journal()
    try:
        journal.attach_retained(storage, step_id, value, method=method, argument=argument,
            validate_record=lambda item: validate_operation(item, value["mode"]))
    except journal.JournalFailure as failure:
        raise OperationError("private-persistence-verifier-" + str(failure)) from None


def remember_completion(value: dict, path: Path, receipt, *, storage=None, step_id=None) -> None:
    if storage is not None: return attach_operation(value, storage, step_id, "retain_proof", receipt)
    value["proof_receipt"] = receipt.relative_to(ROOT).as_posix()
    value["proof_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    save_operation(path, value)


def execute_reserved(args, seconds: int, task_definition: str, network: str, overrides: str, *, runtime=None, provider=None, storage=None, step_id=None) -> int:
    retained = runtime is not None or storage is not None or step_id is not None
    value, remote_possible = None, False
    journal, tasks = task_journal(), task_execution()
    try:
        try:
            request = {"task_definition": task_definition, "network": network, "overrides": json.loads(overrides), "deadline_seconds": seconds}
            if runtime is not None: request["runtime"] = copy.deepcopy(runtime)
            context = validate_request(request, args.mode)
        except (ValueError, TypeError):
            raise OperationError("private-persistence-verifier-operation-request-invalid") from None
        if retained and (runtime is None or not callable(provider) or not isinstance(step_id, str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", step_id) is None
                or not all(callable(getattr(storage, name, None)) for name in ("read", "compare_and_reserve", "retain_task", "retain_proof", "before_submit", "read_receipt", "retain_receipt"))):
            raise OperationError("private-persistence-verifier-operation-storage-invalid")
        expected = None if args.expected_operation == "none" else args.expected_operation
        selected = {"runtime": runtime, "provider": provider} if runtime is not None or provider is not None else {}
        observation = {"provider": provider, "storage": storage, "step_id": step_id} if retained or provider is not None else {}
        manager = contextlib.nullcontext((None, None, None)) if retained else locked_operation(args.mode)
        with manager as (path, descriptor, value):
            if retained:
                value, fresh = journal.reserve_retained(storage, step_id, schema="deploy/private-persistence-verifier-operation/v1", mode=args.mode,
                    request=request, new_operation=args.new_operation, expected=expected,
                    completed=lambda previous: retained_completion(previous, storage=storage), validate_record=lambda item: validate_operation(item, args.mode))
            else:
                value, fresh = journal.reserve(path, descriptor, value, schema="deploy/private-persistence-verifier-operation/v1",
                    marker=b"private-persistence-verifier-operation/v1\n", mode=args.mode, request=request,
                    new_operation=args.new_operation, expected=expected, completed=retained_completion)
            if not fresh:
                remote_possible = True
                return observe_reserved(value, path, seconds, args.mode, **observation)
            operation_id = value["operation_id"]
            report("pending", "private-persistence-verifier-submission-prepared", facts={"operation_id": operation_id}, stream=sys.stderr)
            sys.stderr.flush()
            if retained and not no_direct_database_credential(task_definition, **selected):
                raise OperationError("private-persistence-verifier-isolation-not-proven")
            def before_submit():
                nonlocal remote_possible
                if retained:
                    try: admitted = storage.before_submit(step_id, copy.deepcopy(value))
                    except Exception: raise OperationError("private-persistence-verifier-operation-admission-not-confirmed") from None
                    if admitted is not True: raise OperationError("private-persistence-verifier-operation-admission-not-confirmed")
                remote_possible = True
            def submitted(task):
                arn = task.get("taskArn")
                if not isinstance(arn, str) or re.fullmatch(re.escape(task_prefix(context)) + r"[a-f0-9]{32}", arn) is None:
                    raise tasks.TaskFailure("observation-identity-mismatch")
                if retained and (task.get("taskDefinitionArn") != task_definition or task.get("startedBy") != operation_id or not task_operation_bound(task, args.mode, runtime=runtime)):
                    raise tasks.TaskFailure("observation-identity-mismatch")
                return task
            task = tasks.submit_task(tasks.cli_provider(aws if provider is None else provider), cluster=context["cluster_arn"], definition=task_definition, operation_id=operation_id,
                network=network, overrides=request["overrides"], validate_task=submitted, before_submit=before_submit)
            if retained: attach_operation(value, storage, step_id, "retain_task", task["taskArn"])
            else:
                value["task_arn"] = task["taskArn"]
                save_operation(path, value)
            return observe_reserved(value, path, seconds, args.mode, wait=True, **observation)
    except journal.JournalFailure as error:
        return report("uncertain" if retained and remote_possible else "blocked", "private-persistence-verifier-" + str(error), facts={"operation_id": value["operation_id"]} if value is not None else None)
    except tasks.TaskFailure as error:
        code = "private-persistence-verifier-controller-task-identity-mismatch" if error.code == "observation-identity-mismatch" else error.provider_code or "private-persistence-verifier-not-started"
        return report("failed" if error.rejected else "uncertain", code, facts={"operation_id": value["operation_id"]} if value is not None else None)
    except OperationError as error:
        if not retained: raise
        return report("uncertain" if remote_possible else "blocked", str(error), facts={"operation_id": value["operation_id"]} if value is not None else None)
    except (OSError, subprocess.SubprocessError):
        if not retained: raise
        return report("uncertain" if remote_possible else "blocked", "private-persistence-verifier-operation-store-unavailable", facts={"operation_id": value["operation_id"]} if value is not None else None)


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

#!/usr/bin/env python3
"""Run one fixed migration task and fail closed on an uncertain outcome."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, CLUSTER = "kanbien-dev", "eu-west-1", "kanbien-core-platform"
ACCOUNT = "337159794548"
STACK, FOUNDATION = "kanbien-core-platform-core-server-persistence", "kanbien-core-platform-foundation"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
AWS_CONNECT_TIMEOUT_SECONDS = 5
AWS_READ_TIMEOUT_SECONDS = 20
AWS_PROCESS_TIMEOUT_SECONDS = 30
_AWS_CLI = None


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
    value: dict[str, object] = {"schema": "deploy/persistence-migration-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
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
}
REJECTION_CODES = {
    "PERSISTENCE_MIGRATION_CONFIGURATION_INVALID",
    "PERSISTENCE_MIGRATION_NOT_CONFIRMED",
}
FAILURE_CLASSES = {
    "access_denied", "conflict", "constraint", "resource_not_found",
    "timeout", "transaction_rolled_back", "transport", "validation", "unknown",
}


def runtime_context(runtime, workload):
    """Shared syntax selection only; the controller supplies checked ownership."""
    if runtime is None:
        return {"container_name": workload, "log_group": LOG_GROUP, "log_stream_prefix": workload,
                "cluster_arn": CLUSTER}
    tasks = task_execution()
    try: return tasks.runtime_binding(runtime, account=ACCOUNT, region=REGION)
    except tasks.TaskFailure: return None


def runtime_task_prefix(context):
    return f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{context['cluster_arn'].rsplit('/', 1)[-1]}/"


def runtime_task_matches(task, context):
    containers = task.get("containers")
    return (isinstance(task.get("taskArn"), str)
        and re.fullmatch(re.escape(runtime_task_prefix(context)) + r"[a-f0-9]{32}", task["taskArn"]) is not None
        and isinstance(containers, list) and len(containers) == 1
        and isinstance(containers[0], dict) and containers[0].get("name") == context["container_name"])


def retain_completion(receipts, receipt, *, root, storage, task_arn_prefix, on_receipt):
    reference = receipts.retain(receipt, root=root, storage=storage, task_arn_prefix=task_arn_prefix)
    if on_receipt is not None:
        on_receipt(root / reference["path"] if storage is None else reference)
    return reference


def migration_log_accepted(task: dict[str, object], operation: str, *, runtime=None, provider=None) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "persistence-migration-evidence-unavailable"
    context = runtime_context(runtime, "persistence-migration")
    if context is None or runtime is not None and not callable(provider): return False, "persistence-migration-evidence-unavailable"
    if runtime is not None and not runtime_task_matches(task, context): return False, "persistence-migration-evidence-unavailable"
    stream = f"{context['log_stream_prefix']}/{context['container_name']}/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = (aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return False, code
    messages = events.get("events") if isinstance(events, dict) else None
    if not isinstance(messages, list): return False, "aws-response-invalid"
    messages = [event.get("message") for event in messages if isinstance(event, dict)]
    expected = SUCCESS[operation]
    if any(accepted_message(message, expected) for message in messages):
        return True, "ok"
    return False, "persistence-migration-not-confirmed"


def accepted_message(message: object, expected: str) -> bool:
    try:
        value = json.loads(message) if isinstance(message, str) else None
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(value, dict) and value.get("verdict") == "accepted" and value.get("code") == expected


def migration_log_rejection(task: dict[str, object], *, runtime=None, provider=None) -> tuple[dict[str, object] | None, str]:
    """Extract only a closed safe rejection record from an unsuccessful task.

    Task logs are untrusted provider evidence.  This deliberately parses their
    JSON in memory and returns only the entrypoint's finite code/class values;
    arbitrary message text, nested fields, credentials, and provider details
    never become controller output or a repository artifact.
    """
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return None, "persistence-migration-evidence-unavailable"
    context = runtime_context(runtime, "persistence-migration")
    if context is None or runtime is not None and not callable(provider): return None, "persistence-migration-evidence-unavailable"
    if runtime is not None and not runtime_task_matches(task, context): return None, "persistence-migration-evidence-unavailable"
    stream = f"{context['log_stream_prefix']}/{context['container_name']}/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = (aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", stream, "--start-from-head")
    if not ok:
        return None, code
    messages = events.get("events") if isinstance(events, dict) else None
    if not isinstance(messages, list):
        return None, "aws-response-invalid"
    for event in messages:
        message = event.get("message") if isinstance(event, dict) else None
        try:
            value = json.loads(message) if isinstance(message, str) else None
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(value, dict) or set(value) - {"verdict", "code", "stage", "provider_failure_class", "diagnostic", "related_diagnostics"}:
            continue
        code_value, stage, failure_class = value.get("code"), value.get("stage"), value.get("provider_failure_class")
        if (
            value.get("verdict") != "rejected"
            or not isinstance(code_value, str)
            or code_value not in REJECTION_CODES
            or stage not in {None, "migration"}
            or (failure_class is not None and (not isinstance(failure_class, str) or failure_class not in FAILURE_CLASSES))
        ):
            continue
        result: dict[str, object] = {"safe_result_code": code_value}
        if "diagnostic" in value:
            if code_value not in {"PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", "PERSISTENCE_MIGRATION_NOT_CONFIRMED"}:
                continue
            try:
                path = ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py"
                spec = importlib.util.spec_from_file_location("migration_safe_diagnostics", path)
                contract = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(contract)
                result["diagnostic"] = contract.validate_runtime_diagnostic(value["diagnostic"], "migration" if code_value == "PERSISTENCE_MIGRATION_NOT_CONFIRMED" else None, allow_core_source=True)
                if code_value == "PERSISTENCE_MIGRATION_NOT_CONFIRMED" and not (result["diagnostic"]["code"].startswith("core.") or (result["diagnostic"]["code"].startswith("persistence.") and result["diagnostic"]["detail"].get("operation") == "migration")):
                    continue
                if "related_diagnostics" in value:
                    if code_value != "PERSISTENCE_MIGRATION_NOT_CONFIRMED":
                        continue
                    result["related_diagnostics"] = contract.validate_related_diagnostics(value["related_diagnostics"], result["diagnostic"])
            except Exception:
                continue
        elif "related_diagnostics" in value:
            continue
        if isinstance(failure_class, str):
            result["safe_provider_failure_class"] = failure_class
        return result, "ok"
    return None, "persistence-migration-rejection-not-confirmed"


def task_execution():
    path = Path(__file__).resolve().parents[6] / "shared/provider-adapters/aws/tasks.py"
    spec = importlib.util.spec_from_file_location("persistence_task_execution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reconciliation_operation(operation: str, definition: str) -> tuple[str | None, str]:
    tasks = task_execution()
    try:
        found = tasks.reconcile_task(tasks.cli_provider(aws), cluster=CLUSTER, definition=definition, operation_id=operation, validate_task=lambda task: task)
        return found["taskArn"], "ok"
    except tasks.TaskFailure as failure:
        return None, "persistence-migration-task-identity-unresolved" if failure.code == "reconciliation-unresolved" else "persistence-migration-observation-uncertain"


def task_operations():
    path = Path(__file__).resolve().parents[1] / "task-operations.py"
    spec = importlib.util.spec_from_file_location("persistence_task_operations", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task_evidence():
    path = Path(__file__).resolve().parents[1] / "ecs-task-evidence.py"
    spec = importlib.util.spec_from_file_location("persistence_ecs_task_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def task_operation_bound(task: dict, mode: str) -> bool:
    return task_evidence().task_overrides_match(task, "persistence-migration", {"PERSISTENCE_MIGRATION_OPERATION": mode})

def image_digest(task_definition: object, *, runtime=None, provider=None) -> str | None:
    if not isinstance(task_definition, str):
        return None
    context = runtime_context(runtime, "persistence-migration")
    if context is None or runtime is not None and not callable(provider): return None
    ok, definition, _ = (aws if provider is None else provider)("ecs", "describe-task-definition", "--task-definition", task_definition)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    if runtime is not None and (not isinstance(value, dict) or value.get("taskDefinitionArn") != task_definition): return None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
    if runtime is not None and (not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or containers[0].get("name") != context["container_name"]): return None
    image = containers[0].get("image") if isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) else None
    return image.rsplit("@", 1)[1] if isinstance(image, str) and image.count("@") == 1 and image.rsplit("@", 1)[1].startswith("sha256:") else None


def historical_task_identity(task: dict[str, object], expected_digest: str) -> bool:
    arn, definition_arn = task.get("taskArn"), task.get("taskDefinitionArn")
    if not isinstance(arn, str) or not arn.startswith(f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/") or not isinstance(definition_arn, str):
        return False
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", definition_arn)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    return isinstance(value, dict) and value.get("family") == "kanbien-core-platform-persistence-migration" and image_digest(definition_arn) == expected_digest


def qualified_digest(path: Path) -> str | None:
    source = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("historic_capture_prepare", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    value = module.validate_receipt(path)
    return value.get("image_digest") if isinstance(value, dict) and isinstance(value.get("image_digest"), str) else None


def accepted_completion(task: dict[str, object], seconds: int, operation: str, on_receipt=None, *, runtime=None, provider=None, receipt_storage=None) -> int:
    context = runtime_context(runtime, "persistence-migration")
    if context is None: return report("blocked", "persistence-migration-operation-runtime-invalid")
    prefix = runtime_task_prefix(context)
    if runtime is not None and (receipt_storage is None or not callable(provider) or not callable(on_receipt)):
        return report("blocked", "persistence-migration-operation-storage-invalid")
    if runtime is not None and not runtime_task_matches(task, context):
        return report("uncertain", "persistence-migration-controller-task-identity-mismatch")
    selected = {"runtime": runtime, "provider": provider} if runtime is not None or provider is not None else {}
    facts = {"migration_task": task.get("taskArn"), "operation_id": task.get("startedBy")}
    observed_duration = duration(task)
    if observed_duration is None:
        return report("uncertain", "persistence-migration-duration-unavailable", facts=facts)
    if on_receipt is not None and (observed_duration > seconds or not task_exit(task)):
        try:
            digest = image_digest(task.get("taskDefinitionArn"), **selected)
            if digest is None: raise ValueError()
            failure = "persistence-migration-completion-deadline-exceeded" if observed_duration > seconds else "persistence-migration-unsuccessful-completion"
            receipt = proof_receipts().make(proof_type="migration", operation=operation, task=task, image_digest=digest, result_code=failure,
                context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration}, controller="run-migration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix)
            retain_completion(proof_receipts(), receipt, root=ROOT, storage=receipt_storage, task_arn_prefix=prefix, on_receipt=on_receipt)
        except Exception: return report("uncertain", "persistence-migration-receipt-persistence-failed", facts=facts)
    if observed_duration > seconds:
        return report("failed", "persistence-migration-completion-deadline-exceeded", facts=facts)
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int:
        return report("uncertain", "persistence-task-exit-evidence-unavailable", facts=facts)
    if not task_exit(task):
        rejection, code = migration_log_rejection(task, **selected)
        if rejection is not None:
            return report("failed", "persistence-migration-unsuccessful-completion", "persistence-migration-safe-rejection-observed", facts={**facts, **rejection})
        return report("failed", "persistence-migration-unsuccessful-completion", code, facts=facts)
    accepted, code = migration_log_accepted(task, operation, **selected)
    if not accepted:
        return report("uncertain" if code.startswith("aws-") else "pending", code, facts=facts)
    arn = task.get("taskArn")
    digest = image_digest(task.get("taskDefinitionArn"), **selected)
    if not isinstance(arn, str) or digest is None:
        return report("blocked", "persistence-migration-receipt-identity-unavailable")
    try:
        receipt = proof_receipts().make(
            proof_type="migration", operation=operation, task=task, image_digest=digest,
            result_code=SUCCESS[operation], context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration},
            controller="run-migration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix,
        )
        reference = retain_completion(proof_receipts(), receipt, root=ROOT, storage=receipt_storage, task_arn_prefix=prefix, on_receipt=on_receipt)
    except Exception:
        return report("uncertain" if on_receipt is not None else "blocked", "persistence-migration-receipt-persistence-failed",
            facts=facts if on_receipt is not None else None)
    return report("accepted", "persistence-migration-applied", facts={"operation": operation, "migration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, "proof_receipt": reference["path"], **({"operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"} if on_receipt is not None else {})})


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--reconcile-task")
    parser.add_argument("--reconcile-operation")
    parser.add_argument("--capture-completed-task")
    parser.add_argument("--qualified-receipt", type=Path)
    parser.add_argument("--migration-operation", default="apply")
    parser.add_argument("--new-operation", action="store_true")
    parser.add_argument("--expected-operation")
    parser.add_argument("--migration-state-receipt", type=Path)
    args, unknown = parser.parse_known_args()
    if unknown or (args.reconcile_task is not None and not isinstance(args.reconcile_task, str)) or (args.capture_completed_task is not None and not isinstance(args.capture_completed_task, str)) or (args.reconcile_task is not None and args.capture_completed_task is not None) or (args.capture_completed_task is not None and args.qualified_receipt is None) or (args.capture_completed_task is None and args.qualified_receipt is not None) or args.migration_operation not in SUCCESS:
        return report("blocked", "persistence-migration-arguments-invalid")
    if args.reconcile_operation is not None and (args.reconcile_task is not None or args.capture_completed_task is not None or re.fullmatch(r"kp-[a-f0-9]{32}", args.reconcile_operation) is None):
        return report("blocked", "persistence-migration-reconciliation-operation-invalid")
    if args.new_operation != (args.expected_operation is not None) or (args.expected_operation is not None and args.expected_operation != "none" and re.fullmatch(r"kp-[a-f0-9]{32}", args.expected_operation) is None) or (args.new_operation and any((args.reconcile_task, args.reconcile_operation, args.capture_completed_task))):
        return report("blocked", "persistence-migration-new-operation-arguments-invalid")
    if args.migration_state_receipt is not None and not args.new_operation:
        return report("blocked", "persistence-migration-new-operation-arguments-invalid")
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": [], "proof_contract": {"proof_type":"migration","operation":args.migration_operation,"result_code":SUCCESS[args.migration_operation],"family":"kanbien-core-platform-persistence-migration","deadline_workload":"persistence-migration"}}))
        return 0
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
    if args.reconcile_operation is not None:
        args.reconcile_task, code = reconciliation_operation(args.reconcile_operation, task_definition)
        if args.reconcile_task is None:
            return report("uncertain", code, facts={"operation_id": args.reconcile_operation})
    if args.reconcile_task is not None:
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.reconcile_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        if not ok or not isinstance(listed, list) or len(listed) != 1 or not isinstance(listed[0], dict):
            return report("uncertain", "persistence-migration-controller-observation-uncertain", facts={"migration_task": args.reconcile_task, "operation_id": args.reconcile_operation})
        task = listed[0]
        if args.reconcile_operation is not None and task.get("startedBy") != args.reconcile_operation:
            return report("blocked", "persistence-migration-reconciliation-operation-mismatch")
        if not task_operation_bound(task, args.migration_operation):
            return report("blocked", "persistence-migration-reconciliation-operation-binding-invalid")
        code = current_reconciliation_task(task, args.reconcile_task, task_definition)
        if code != "ok":
            verdict = "pending" if code.endswith("-not-terminal") and task.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"} else "blocked"
            return report(verdict, code, facts={"migration_task": args.reconcile_task, "operation_id": args.reconcile_operation})
        return accepted_completion(task, seconds, args.migration_operation)
    if args.capture_completed_task is not None:
        expected_digest = qualified_digest(args.qualified_receipt)
        if expected_digest is None:
            return report("blocked", "persistence-migration-historic-receipt-invalid")
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.capture_completed_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        task = listed[0] if isinstance(listed, list) and len(listed) == 1 and isinstance(listed[0], dict) else None
        if not isinstance(task, dict) or task.get("taskArn") != args.capture_completed_task or not historical_task_identity(task, expected_digest) or not task_operation_bound(task, args.migration_operation):
            return report("blocked", code if not ok else "persistence-migration-historic-task-identity-invalid")
        return accepted_completion(task, seconds, args.migration_operation)
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{security_group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "persistence-migration", "environment": [{"name": "PERSISTENCE_MIGRATION_OPERATION", "value": args.migration_operation}]}]})
    operations = task_operations()
    admission, observer = None, None
    if args.migration_state_receipt is not None:
        try:
            path = args.migration_state_receipt.absolute()
            if any(part.is_symlink() for part in (path, *path.parents)) or not path.resolve().is_relative_to(proof_receipts().RECEIPTS.resolve()): raise ValueError()
            raw = path.read_bytes()
            if len(raw) > 1048576: raise ValueError()
            observer = proof_receipts().validate(json.loads(raw))
            admission = {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
        except Exception:
            return report("blocked", "persistence-migration-replay-observation-invalid")
    def authorize_successor(previous, proof):
        if proof["task"]["exit_code"] == 0 and proof["task"]["result_code"] == SUCCESS[args.migration_operation]: return
        try:
            if observer is None or observer["proof_type"] != "administration" or observer["operation"] != "observe-migration-state": raise ValueError()
            task, context, provenance = observer["task"], observer["context"], observer["provenance"]
            if task["exit_code"] != 0 or task["result_code"] != "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED" or task["definition"] != scope_outputs.get("CoreServerPersistenceAdministrationTaskDefinitionArn") or task["image_digest"] != image_digest(task_definition): raise ValueError()
            if provenance.get("evidence_class", "live") != proof_receipts().EVIDENCE_CLASS or provenance["controller"] != "run-administration" or context["completion_duration_seconds"] > context["completion_deadline_seconds"]: raise ValueError()
            after, prior = timestamp(task["started_at"]), timestamp(proof["task"]["stopped_at"])
            if after is None or prior is None or after < prior: raise ValueError()
        except Exception:
            raise operations.OperationFailure("replay-observation-required") from None
    binding = operations.BoundOperation(root=ROOT, proof_type="migration", family="kanbien-core-platform-persistence-migration",
        container="persistence-migration", selector="PERSISTENCE_MIGRATION_OPERATION", results=SUCCESS,
        aws=aws, report=report, accept=accepted_completion, receipts=proof_receipts())
    return binding.run(mode=args.migration_operation, definition=task_definition, network=network, overrides=overrides,
        seconds=seconds, new_operation=args.new_operation, expected_operation=args.expected_operation,
        admission=admission, authorize_successor=authorize_successor)


if __name__ == "__main__":
    raise SystemExit(main())

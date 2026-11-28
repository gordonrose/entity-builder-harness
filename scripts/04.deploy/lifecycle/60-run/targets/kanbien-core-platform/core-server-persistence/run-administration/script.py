#!/usr/bin/env python3
"""Run one bounded administrative persistence task with durable proof."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
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
    "confirm-runtime-iam-access": "PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED",
    "revoke-runtime": "PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED",
    "restore-runtime": "PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED",
    "prove-effective-privilege": "PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN",
    "observe-migration-state": (
        "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED",
        "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED",
    ),
}
PROOF_RESULT = {
    **{operation: result for operation, result in SUCCESS.items() if isinstance(result, str)},
    # The acceptance route is deliberately the applied-manifest branch. The
    # controller may also record replay permission for an empty history, but
    # that result is not evidence that a migration was applied.
    "observe-migration-state": "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED",
}
PROOF_CONTRACT = {
    operation: {
        "proof_type": "administration",
        "operation": operation,
        "result_code": PROOF_RESULT[operation],
        "family": "kanbien-core-platform-persistence-administration",
        "deadline_workload": "persistence-administration",
    }
    for operation in SUCCESS
}
OPERATIONS = (
    "bootstrap-identities",
    "grant-runtime-application-access",
    "confirm-runtime-iam-access",
    "revoke-runtime",
    "restore-runtime",
    "prove-effective-privilege",
    "observe-migration-state",
)
# These operations observe an already-present state.  Retrying after a host
# interruption must reuse a terminal receipt for the exact current task
# definition/image rather than submit an equivalent task.  State-changing
# identity operations intentionally require an explicit task reconciliation or
# a new governed invocation; an old revoke/restore receipt cannot establish a
# new transition.
RESUMABLE_OPERATIONS = frozenset({
    "confirm-runtime-iam-access",
    "prove-effective-privilege",
    "observe-migration-state",
})


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value


MIGRATION = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.py", "persistence_migration")
RECEIPTS = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py", "persistence_proof_receipts")


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None, stream=None) -> int:
    value: dict[str, object] = {"schema": "deploy/persistence-administration-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True), file=stream or sys.stdout)
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


class AdministrationArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        report("blocked", "persistence-administration-arguments-invalid")
        self.exit(2)


def current_task(task: dict[str, object], requested: str, definition: str) -> str:
    prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
    if not requested.startswith(prefix):
        return "persistence-administration-reconciliation-task-identity-invalid"
    if task.get("taskArn") != requested or task.get("taskDefinitionArn") != definition:
        return "persistence-administration-reconciliation-task-not-current"
    return "ok" if task.get("lastStatus") == "STOPPED" else "persistence-administration-reconciliation-task-not-terminal"


def accepted_log(task: dict[str, object], operation: str, *, runtime=None, provider=None) -> tuple[str | None, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return None, "persistence-administration-evidence-unavailable"
    context = MIGRATION.runtime_context(runtime, "persistence-administration")
    if context is None or runtime is not None and not callable(provider): return None, "persistence-administration-evidence-unavailable"
    if runtime is not None and not MIGRATION.runtime_task_matches(task, context): return None, "persistence-administration-evidence-unavailable"
    stream = f"{context['log_stream_prefix']}/{context['container_name']}/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = (MIGRATION.aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", stream, "--start-from-head")
    messages = [item.get("message") for item in events.get("events", []) if isinstance(item, dict)] if ok and isinstance(events, dict) else []
    expected = SUCCESS[operation]
    allowed = {expected} if isinstance(expected, str) else set(expected)
    for message in messages:
        try:
            record = json.loads(message) if isinstance(message, str) else None
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(record, dict) and set(record) == {"verdict", "code"} and record.get("verdict") == "accepted" and isinstance(record.get("code"), str) and record.get("code") in allowed:
            return record["code"], "ok"
    return None, code if not ok else "persistence-administration-not-confirmed"


def accept(task: dict[str, object], seconds: int, operation: str, on_receipt=None, *, runtime=None, provider=None, receipt_storage=None) -> int:
    context = MIGRATION.runtime_context(runtime, "persistence-administration")
    if context is None: return report("blocked", "persistence-administration-operation-runtime-invalid")
    prefix = MIGRATION.runtime_task_prefix(context)
    if runtime is not None and (receipt_storage is None or not callable(provider) or not callable(on_receipt)):
        return report("blocked", "persistence-administration-operation-storage-invalid")
    if runtime is not None and not MIGRATION.runtime_task_matches(task, context):
        return report("uncertain", "persistence-administration-controller-task-identity-mismatch")
    selected = {"runtime": runtime, "provider": provider} if runtime is not None or provider is not None else {}
    terminal = {}
    def unsuccessful(code, *, facts=None):
        return report("failed" if terminal else "blocked", code, facts={**(facts or {}), **terminal})
    observed = MIGRATION.duration(task)
    if observed is None:
        return report("blocked", "persistence-administration-duration-unavailable")
    if on_receipt is not None and (observed > seconds or not MIGRATION.task_exit(task)):
        try:
            digest = MIGRATION.image_digest(task.get("taskDefinitionArn"), **selected)
            if digest is None: raise ValueError()
            failure = "persistence-administration-completion-deadline-exceeded" if observed > seconds else "persistence-administration-unsuccessful-completion"
            receipt = RECEIPTS.make(proof_type="administration", operation=operation, task=task, image_digest=digest, result_code=failure,
                context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed}, controller="run-administration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix)
            reference = MIGRATION.retain_completion(RECEIPTS, receipt, root=ROOT, storage=receipt_storage, task_arn_prefix=prefix, on_receipt=on_receipt)
            terminal = {"operation_id": task.get("startedBy"), "operation": operation,
                        "proof_receipt": reference["path"], "proof_sha256": reference["sha256"]}
        except Exception: return report("uncertain", "persistence-administration-receipt-persistence-failed", facts={"operation_id": task.get("startedBy")})
    if observed > seconds:
        return unsuccessful("persistence-administration-completion-deadline-exceeded")
    if not MIGRATION.task_exit(task):
        # Use the task's actual log stream and a closed reader; never replay it.
        arn = task.get("taskArn")
        known_facts = {}
        if isinstance(arn, str) and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{32}", arn):
            known_facts["administration_task"] = arn.rsplit("/", 1)[-1]
        if isinstance(arn, str) and arn.rsplit("/", 1)[-1]:
            ok, events, _ = (MIGRATION.aws if provider is None else provider)("logs", "get-log-events", "--log-group-name", context["log_group"], "--log-stream-name", f"{context['log_stream_prefix']}/{context['container_name']}/{arn.rsplit('/', 1)[-1]}", "--start-from-head")
            contract = None
            task_evidence = None
            try:
                task_evidence = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/binding.py", "administration_task_evidence")
                failure, observation = task_evidence.collect_persistence_task_failure(events, "administration") if ok and "administration_task" in known_facts else (None, "failed" if not ok else "unavailable")
                known_facts["task_log_observation"] = observation
                if failure is not None:
                    return unsuccessful("persistence-administration-unsuccessful-completion", facts={**known_facts, "safe_result_code": failure["code"], "task_failure": failure})
            except Exception:
                known_facts["task_log_observation"] = "failed"
            for event in events.get("events", []) if ok and isinstance(events, dict) else []:
                try:
                    value = json.loads(event.get("message"))
                    if not {"verdict", "code", "diagnostic"} <= set(value) or set(value) - {"verdict", "code", "diagnostic", "related_diagnostics"} or value["verdict"] != "rejected":
                        continue
                    iam_preflight = operation == "prove-effective-privilege" and value["code"] == "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED"
                    if contract is None:
                        contract = module(ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py", "administration_safe_diagnostics")
                    native_record = value["diagnostic"]
                    operational_family = isinstance(native_record, dict) and isinstance(native_record.get("code"), str) and native_record["code"].startswith(("persistence.", "core."))
                    diagnostic = contract.validate_runtime_diagnostic(native_record, "administration" if operational_family else None, allow_core_source=True)
                    operational = diagnostic["code"].startswith("core.") or (diagnostic["code"].startswith("persistence.") and diagnostic["detail"].get("operation") == "administration")
                    if value["code"] == "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID" and operational:
                        continue
                    if value["code"] != "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID" and not iam_preflight and not operational:
                        continue
                    if iam_preflight and diagnostic["code"] != "kanbien-core-server.iam-configuration-invalid" and not operational:
                        continue
                    safe_code = value["code"] if value["code"] in {"PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "PERSISTENCE_ADMINISTRATION_ACCESS_DENIED", "PERSISTENCE_ADMINISTRATION_CREDENTIAL_REJECTED"} else "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED"
                    facts = {**known_facts, "safe_result_code": safe_code, "diagnostic": diagnostic}
                    if "related_diagnostics" in value:
                        if not operational:
                            continue
                        facts["related_diagnostics"] = contract.validate_related_diagnostics(value["related_diagnostics"], diagnostic)
                    return unsuccessful("persistence-administration-unsuccessful-completion", facts=facts)
                except Exception:
                    continue
        return unsuccessful("persistence-administration-unsuccessful-completion", facts=known_facts)
    result_code, code = accepted_log(task, operation, **selected)
    if result_code is None:
        return report("blocked", code)
    digest = MIGRATION.image_digest(task.get("taskDefinitionArn"), **selected)
    arn = task.get("taskArn")
    if not isinstance(digest, str) or not isinstance(arn, str):
        return report("blocked", "persistence-administration-receipt-identity-unavailable")
    try:
        receipt = RECEIPTS.make(proof_type="administration", operation=operation, task=task, image_digest=digest, result_code=result_code, context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed}, controller="run-administration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), task_arn_prefix=prefix)
        reference = MIGRATION.retain_completion(RECEIPTS, receipt, root=ROOT, storage=receipt_storage, task_arn_prefix=prefix, on_receipt=on_receipt)
    except Exception:
        return report("uncertain" if on_receipt is not None else "blocked", "persistence-administration-receipt-persistence-failed",
            facts={"operation_id": task.get("startedBy")} if on_receipt is not None else None)
    return report("accepted", "persistence-administration-applied", facts={"operation": operation, "safe_result_code": result_code, "administration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed, "proof_receipt": reference["path"], **({"operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"} if on_receipt is not None else {})})


def retained_observation(operation: str, definition: str) -> tuple[Path | None, dict[str, object] | None]:
    """Find one valid exact-image observation receipt for an interrupted retry."""
    if operation not in RESUMABLE_OPERATIONS:
        return None, None
    digest = MIGRATION.image_digest(definition)
    if not isinstance(digest, str):
        return None, None
    try:
        candidates = sorted(RECEIPTS.RECEIPTS.glob(f"administration-{operation}-*.json"), key=lambda path: path.name, reverse=True)
    except OSError:
        return None, None
    for path in candidates:
        try:
            observed = RECEIPTS.validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, RECEIPTS.ReceiptError):
            continue
        task = observed.get("task")
        if not isinstance(task, dict):
            continue
        if task.get("definition") != definition or task.get("image_digest") != digest or task.get("result_code") != PROOF_RESULT[operation]:
            continue
        return path, observed
    return None, None


def reused_observation(path: Path, receipt: dict[str, object], operation: str) -> int:
    task = receipt.get("task")
    context = receipt.get("context")
    if not isinstance(task, dict) or not isinstance(context, dict):
        return report("blocked", "persistence-administration-retained-receipt-invalid")
    try:
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
        task_id = str(task["arn"]).rsplit("/", 1)[-1]
        deadline_seconds = context["completion_deadline_seconds"]
        duration_seconds = context["completion_duration_seconds"]
    except (KeyError, ValueError):
        return report("blocked", "persistence-administration-retained-receipt-invalid")
    return report("accepted", "persistence-administration-reconciled-retained-receipt", facts={"operation": operation, "safe_result_code": task["result_code"], "administration_task": task_id, "completion_deadline_seconds": deadline_seconds, "completion_duration_seconds": duration_seconds, "proof_receipt": relative})


def main() -> int:
    parser = AdministrationArgumentParser(add_help=False)
    # Keep this literal tuple beside the controller contract.  The declaration
    # coverage gate intentionally reads the controller's permitted operations
    # without executing it, so a computed dictionary view is insufficient.
    parser.add_argument("--operation", choices=OPERATIONS)
    parser.add_argument("--reconcile-task")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--new-operation", action="store_true")
    parser.add_argument("--expected-operation")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.operation is None or (args.reconcile_task is not None and not isinstance(args.reconcile_task, str)) or (args.reconcile_task is not None and args.fresh):
        return report("blocked", "persistence-administration-arguments-invalid")
    new_operation = args.new_operation or args.fresh
    if new_operation != (args.expected_operation is not None) or (args.expected_operation is not None and args.expected_operation != "none" and re.fullmatch(r"kp-[a-f0-9]{32}", args.expected_operation) is None) or (new_operation and args.reconcile_task is not None):
        return report("blocked", "persistence-administration-new-operation-arguments-invalid")
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": [], "proof_contract": PROOF_CONTRACT[args.operation]}, sort_keys=True))
        return 0
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
    def historical():
        retained_path, retained = retained_observation(args.operation, definition)
        if retained_path is not None and retained is not None: return reused_observation(retained_path, retained, args.operation)
        return None
    operations = MIGRATION.task_operations()
    binding = operations.BoundOperation(root=ROOT, proof_type="administration", family="kanbien-core-platform-persistence-administration",
        container="persistence-administration", selector="PERSISTENCE_ADMINISTRATION_OPERATION", results=SUCCESS,
        aws=MIGRATION.aws, report=report, accept=accept, receipts=RECEIPTS)
    return binding.run(mode=args.operation, definition=definition, network=network, overrides=overrides, seconds=seconds,
        new_operation=new_operation, expected_operation=args.expected_operation, historical=historical)


if __name__ == "__main__":
    raise SystemExit(main())


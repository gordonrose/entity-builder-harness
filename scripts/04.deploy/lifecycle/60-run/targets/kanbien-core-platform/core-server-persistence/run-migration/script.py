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


def migration_log_accepted(task: dict[str, object], operation: str) -> tuple[bool, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return False, "persistence-migration-evidence-unavailable"
    stream = f"persistence-migration/persistence-migration/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
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


def migration_log_rejection(task: dict[str, object]) -> tuple[dict[str, object] | None, str]:
    """Extract only a closed safe rejection record from an unsuccessful task.

    Task logs are untrusted provider evidence.  This deliberately parses their
    JSON in memory and returns only the entrypoint's finite code/class values;
    arbitrary message text, nested fields, credentials, and provider details
    never become controller output or a repository artifact.
    """
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return None, "persistence-migration-evidence-unavailable"
    stream = f"persistence-migration/persistence-migration/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
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


def migration_environment(mode: str, profile: str = "baseline") -> dict[str, str]:
    if mode != "apply" or profile not in {"baseline", "scheduling"}:
        raise ValueError("persistence-migration-profile-invalid")
    return {"PERSISTENCE_MIGRATION_OPERATION": mode, **({"PERSISTENCE_MIGRATION_PROFILE": "scheduling"} if profile == "scheduling" else {})}


def task_operation_bound(task: dict, mode: str, profile: str = "baseline") -> bool:
    return task_evidence().task_overrides_match(task, "persistence-migration", migration_environment(mode, profile))

def image_digest(task_definition: object) -> str | None:
    if not isinstance(task_definition, str):
        return None
    ok, definition, _ = aws("ecs", "describe-task-definition", "--task-definition", task_definition)
    value = definition.get("taskDefinition") if ok and isinstance(definition, dict) else None
    containers = value.get("containerDefinitions") if isinstance(value, dict) else None
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


def scheduling_database_binding(qualified, scope_outputs, definitions):
    """One checked maintenance/template/database identity for all scoped proofs."""
    receipts = proof_receipts()
    ok, described, _ = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = described.get("Stacks") if ok and isinstance(described, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or stacks[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}: raise ValueError()
    parameters = {row["ParameterKey"]: row["ParameterValue"] for row in stacks[0].get("Parameters", [])}
    if parameters.get("SourceRevision") != qualified["source_revision"] or parameters.get("SupportImageDigest") != qualified["image_digest"]: raise ValueError()
    ok, described, _ = aws("cloudformation", "get-template", "--stack-name", STACK)
    source = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
    cloudformation = receipts.owner("core_scheduling_template", "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
    body = described.get("TemplateBody") if ok and isinstance(described, dict) else None
    if isinstance(body, str): body = cloudformation.template(body)
    if body != cloudformation.template(source.read_text()): raise ValueError()
    ok, described, _ = aws("rds", "describe-db-instances", "--db-instance-identifier", scope_outputs.get("PersistenceDatabaseIdentifier", ""))
    databases = described.get("DBInstances") if ok and isinstance(described, dict) else None
    if not isinstance(databases, list) or len(databases) != 1: raise ValueError()
    database = databases[0]
    if database.get("DBInstanceIdentifier") != scope_outputs.get("PersistenceDatabaseIdentifier") or database.get("DBInstanceStatus") != "available" or database.get("DBName") != "kanbienpersistence" or database.get("Endpoint", {}).get("Address") != scope_outputs.get("PersistenceDatabaseEndpoint") or database.get("IAMDatabaseAuthenticationEnabled") is not True: raise ValueError()
    resource = database.get("DbiResourceId")
    if not isinstance(resource, str) or re.fullmatch(r"db-[A-Za-z0-9]+", resource) is None: raise ValueError()
    for definition, role in definitions:
        ok, described, _ = aws("ecs", "describe-task-definition", "--task-definition", definition)
        actual = described.get("taskDefinition") if ok and isinstance(described, dict) else None
        if not isinstance(actual, dict) or actual.get("taskDefinitionArn") != definition: raise ValueError()
        containers = actual.get("containerDefinitions")
        if not isinstance(containers, list) or len(containers) != 1: raise ValueError()
        container = containers[0]
        if container.get("image") != parameters.get("ImageRepositoryUri", "") + "@" + qualified["image_digest"]: raise ValueError()
        entries = container.get("environment", [])
        environment = {row["name"]: row["value"] for row in entries}
        if len(environment) != len(entries): raise ValueError()
        expected = {"PERSISTENCE_POSTGRES_HOST": database["Endpoint"]["Address"], "PERSISTENCE_POSTGRES_DATABASE": database["DBName"],
            "PERSISTENCE_POSTGRES_SCHEMA": "platform", "PERSISTENCE_POSTGRES_IAM_REGION": REGION,
            "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": f"arn:aws:rds-db:{REGION}:{ACCOUNT}:dbuser:{resource}/{role}"}
        if any(environment.get(key) != value for key, value in expected.items()): raise ValueError()
    return receipts.validate_scheduling_binding({"source_revision": qualified["source_revision"], "image_digest": qualified["image_digest"],
        "dependency_incarnation_sha256": receipts.digest({"resource_id": resource, "database": database["DBName"], "schema": "platform"})})


def observe_scheduling_administration(observer, scope_outputs, operation, *, now=None, deadline_seconds=None):
    """Reconcile one original finite result against its actual current task.

    This is read-only provider evidence, not a submission or activation grant.
    Both prefix admission and initial scheduler readiness use this same owner.
    """
    receipts = proof_receipts()
    observer = receipts.validate(observer)
    task, context, provenance = observer["task"], observer["context"], observer["provenance"]
    prefix = operation == receipts.SCHEDULING_STATE.PREFIX_OPERATION
    if not prefix and operation not in receipts.SCHEDULING_STATE.RESULTS: raise ValueError()
    result_code = receipts.SCHEDULING_STATE.PREFIX_RESULT if prefix else receipts.SCHEDULING_STATE.RESULTS[operation]
    field = "migration_prefix" if prefix else "database_state"
    if (observer["proof_type"] != "administration" or observer["operation"] != operation
            or task["exit_code"] != 0 or task["result_code"] != result_code
            or task["terminal_status"] != "STOPPED"
            or task["definition"] != scope_outputs.get("CoreServerPersistenceAdministrationTaskDefinitionArn")
            or provenance.get("evidence_class") != "live" or provenance["controller"] != "run-administration"
            or provenance["collection_method"] != "ecs-terminal-task+task-definition+safe-log"): raise ValueError()
    start, stopped = timestamp(task["started_at"]), timestamp(task["stopped_at"])
    current = datetime.now(timezone.utc) if now is None else now
    policy = receipts.owner("core_scheduling_freshness", "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
    collected = timestamp(provenance["collected_at"])
    if (start is None or stopped is None or collected is None or not start <= stopped <= collected <= current
            or policy.observation_expired(task["stopped_at"], current.isoformat(), timestamp)
            or context["completion_duration_seconds"] > context["completion_deadline_seconds"]
            or deadline_seconds is not None and context["completion_deadline_seconds"] != deadline_seconds): raise ValueError()
    ok, described, _ = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", task["arn"])
    tasks = described.get("tasks") if ok and isinstance(described, dict) else None
    if not isinstance(tasks, list) or len(tasks) != 1 or described.get("failures"): raise ValueError()
    actual_task = tasks[0]
    if (actual_task.get("taskArn") != task["arn"] or actual_task.get("taskDefinitionArn") != task["definition"]
            or actual_task.get("lastStatus") != "STOPPED" or not task_exit(actual_task)
            or timestamp(actual_task.get("startedAt")) != start or timestamp(actual_task.get("stoppedAt")) != stopped
            or duration(actual_task) != context["completion_duration_seconds"]
            or not task_evidence().task_overrides_match(actual_task, "persistence-administration", {"PERSISTENCE_ADMINISTRATION_OPERATION": operation})): raise ValueError()
    stream = "persistence-administration/persistence-administration/" + task["arn"].rsplit("/", 1)[1]
    ok, described, _ = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    events = described.get("events") if ok and isinstance(described, dict) else None
    if not isinstance(events, list): raise ValueError()
    expected = {"verdict": "accepted", "code": result_code, field: context[field]}
    observed = []
    for event in events:
        try: observed.append(json.loads(event.get("message")))
        except (ValueError, TypeError, AttributeError): continue
    if observed.count(expected) != 1: raise ValueError()
    return context[field]


def scheduling_admission(observer, qualified_path, scope_outputs, task_definition, previous, previous_proof):
    """A fresh partial prefix authorizes one reserved continuation, not replay."""
    receipts = proof_receipts()
    try:
        if previous is not None and previous_proof is None: raise ValueError()
        if previous_proof is not None and (previous_proof["task"]["exit_code"] != 0
                or previous_proof["task"]["result_code"] != SUCCESS["apply"]):
            return "persistence-migration-scheduling-successor-prefix-required"
        prefix = observe_scheduling_administration(observer, scope_outputs, receipts.SCHEDULING_STATE.PREFIX_OPERATION)
        task, context = observer["task"], observer["context"]
        start = timestamp(task["started_at"])
        if previous_proof is not None and start < timestamp(previous_proof["task"]["stopped_at"]): raise ValueError()
        qualified = receipts.qualified_maintenance(qualified_path)
        if task["image_digest"] != qualified["image_digest"]: raise ValueError()
        binding = scheduling_database_binding(qualified, scope_outputs, ((task_definition, "core_schema_migration"), (task["definition"], "core_runtime")))
        if context.get("scheduling_binding") != binding: raise ValueError()
        return "complete" if prefix["state"] == "complete" else "partial"
    except Exception:
        return "persistence-migration-scheduling-admission-invalid"


def accepted_completion(task: dict[str, object], seconds: int, operation: str, on_receipt=None, migration_profile: str = "baseline", scheduling_context=None) -> int:
    migration_environment(operation, migration_profile)
    if migration_profile == "scheduling" and not task_operation_bound(task, operation, migration_profile):
        return report("blocked", "persistence-migration-reconciliation-operation-binding-invalid")
    facts = {"migration_task": task.get("taskArn"), "operation_id": task.get("startedBy")}
    observed_duration = duration(task)
    profile_context = {"migration_profile": "scheduling"} if migration_profile == "scheduling" else {}
    if migration_profile == "scheduling" and scheduling_context is not None:
        profile_context.update(scheduling_context)
    if observed_duration is None:
        return report("uncertain", "persistence-migration-duration-unavailable", facts=facts)
    if on_receipt is not None and (observed_duration > seconds or not task_exit(task)):
        try:
            digest = image_digest(task.get("taskDefinitionArn"))
            if digest is None: raise ValueError()
            failure = "persistence-migration-completion-deadline-exceeded" if observed_duration > seconds else "persistence-migration-unsuccessful-completion"
            receipt = proof_receipts().make(proof_type="migration", operation=operation, task=task, image_digest=digest, result_code=failure,
                context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, **profile_context}, controller="run-migration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
            on_receipt(proof_receipts().persist(receipt))
        except Exception: return report("uncertain", "persistence-migration-receipt-persistence-failed", facts=facts)
    if observed_duration > seconds:
        return report("failed", "persistence-migration-completion-deadline-exceeded", facts=facts)
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int:
        return report("uncertain", "persistence-task-exit-evidence-unavailable", facts=facts)
    if not task_exit(task):
        rejection, code = migration_log_rejection(task)
        if rejection is not None:
            return report("failed", "persistence-migration-unsuccessful-completion", "persistence-migration-safe-rejection-observed", facts={**facts, **rejection})
        return report("failed", "persistence-migration-unsuccessful-completion", code, facts=facts)
    accepted, code = migration_log_accepted(task, operation)
    if not accepted:
        return report("uncertain" if code.startswith("aws-") else "pending", code, facts=facts)
    arn = task.get("taskArn")
    digest = image_digest(task.get("taskDefinitionArn"))
    if not isinstance(arn, str) or digest is None:
        return report("blocked", "persistence-migration-receipt-identity-unavailable")
    try:
        receipt = proof_receipts().make(
            proof_type="migration", operation=operation, task=task, image_digest=digest,
            result_code=SUCCESS[operation], context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, **profile_context},
            controller="run-migration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        path = proof_receipts().persist(receipt)
        if on_receipt is not None: on_receipt(path)
    except Exception:
        return report("uncertain" if on_receipt is not None else "blocked", "persistence-migration-receipt-persistence-failed",
            facts=facts if on_receipt is not None else None)
    return report("accepted", "persistence-migration-applied", facts={"operation": operation, "migration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed_duration, "proof_receipt": str(path.relative_to(ROOT)), **({"operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"} if on_receipt is not None else {})})


def operation_binding(accept_callback):
    return task_operations().BoundOperation(root=ROOT, proof_type="migration", family="kanbien-core-platform-persistence-migration",
        container="persistence-migration", selector="PERSISTENCE_MIGRATION_OPERATION", results=SUCCESS,
        aws=aws, report=report, accept=accept_callback, receipts=proof_receipts())


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--reconcile-task")
    parser.add_argument("--reconcile-operation")
    parser.add_argument("--capture-completed-task")
    parser.add_argument("--qualified-receipt", type=Path)
    parser.add_argument("--migration-operation", default="apply")
    parser.add_argument("--migration-profile", default="baseline")
    parser.add_argument("--new-operation", action="store_true")
    parser.add_argument("--expected-operation")
    parser.add_argument("--migration-state-receipt", type=Path)
    args, unknown = parser.parse_known_args()
    if args.migration_profile not in {"baseline", "scheduling"}:
        return report("blocked", "persistence-migration-profile-invalid")
    if unknown or (args.reconcile_task is not None and not isinstance(args.reconcile_task, str)) or (args.capture_completed_task is not None and not isinstance(args.capture_completed_task, str)) or (args.reconcile_task is not None and args.capture_completed_task is not None) or (args.capture_completed_task is not None and args.qualified_receipt is None) or (args.capture_completed_task is None and args.qualified_receipt is not None and args.migration_profile != "scheduling") or args.migration_operation not in SUCCESS:
        return report("blocked", "persistence-migration-arguments-invalid")
    if args.reconcile_operation is not None and (args.reconcile_task is not None or args.capture_completed_task is not None or re.fullmatch(r"kp-[a-f0-9]{32}", args.reconcile_operation) is None):
        return report("blocked", "persistence-migration-reconciliation-operation-invalid")
    if args.new_operation != (args.expected_operation is not None) or (args.expected_operation is not None and args.expected_operation != "none" and re.fullmatch(r"kp-[a-f0-9]{32}", args.expected_operation) is None) or (args.new_operation and any((args.reconcile_task, args.reconcile_operation, args.capture_completed_task))):
        return report("blocked", "persistence-migration-new-operation-arguments-invalid")
    if args.migration_state_receipt is not None and not args.new_operation and args.migration_profile != "scheduling":
        return report("blocked", "persistence-migration-new-operation-arguments-invalid")
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": [], "proof_contract": {"proof_type":"migration","operation":args.migration_operation,"result_code":SUCCESS[args.migration_operation],"family":"kanbien-core-platform-persistence-migration","deadline_workload":"persistence-migration"}}))
        return 0
    if args.migration_profile == "scheduling" and (args.qualified_receipt is None or args.migration_state_receipt is None):
        return report("blocked", "persistence-migration-scheduling-prefix-observation-required")
    if args.migration_profile == "scheduling" and any((args.reconcile_task, args.reconcile_operation, args.capture_completed_task)):
        return report("blocked", "persistence-migration-scheduling-reserved-reconciliation-required")
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
        if not task_operation_bound(task, args.migration_operation, args.migration_profile):
            return report("blocked", "persistence-migration-reconciliation-operation-binding-invalid")
        code = current_reconciliation_task(task, args.reconcile_task, task_definition)
        if code != "ok":
            verdict = "pending" if code.endswith("-not-terminal") and task.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"} else "blocked"
            return report(verdict, code, facts={"migration_task": args.reconcile_task, "operation_id": args.reconcile_operation})
        return accepted_completion(task, seconds, args.migration_operation, migration_profile=args.migration_profile)
    if args.capture_completed_task is not None:
        expected_digest = qualified_digest(args.qualified_receipt)
        if expected_digest is None:
            return report("blocked", "persistence-migration-historic-receipt-invalid")
        ok, described, code = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", args.capture_completed_task)
        listed = described.get("tasks", []) if ok and isinstance(described, dict) else []
        task = listed[0] if isinstance(listed, list) and len(listed) == 1 and isinstance(listed[0], dict) else None
        if not isinstance(task, dict) or task.get("taskArn") != args.capture_completed_task or not historical_task_identity(task, expected_digest) or not task_operation_bound(task, args.migration_operation, args.migration_profile):
            return report("blocked", code if not ok else "persistence-migration-historic-task-identity-invalid")
        return accepted_completion(task, seconds, args.migration_operation, migration_profile=args.migration_profile)
    network = f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{security_group}],assignPublicIp=DISABLED}}"
    overrides = json.dumps({"containerOverrides": [{"name": "persistence-migration", "environment": [{"name": key, "value": value} for key, value in migration_environment(args.migration_operation, args.migration_profile).items()]}]})
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
            if args.migration_profile == "scheduling": proof_receipts().validate_scheduling_binding(observer["context"].get("scheduling_binding"))
        except Exception:
            return report("blocked", "persistence-migration-replay-observation-invalid")
    def authorize_successor(previous, proof):
        if args.migration_profile == "scheduling": return
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
    def authorize_submission(previous, proof):
        result = scheduling_admission(observer, args.qualified_receipt, scope_outputs, task_definition, previous, proof)
        if result == "complete":
            return report("accepted", "persistence-migration-scheduling-already-complete", facts={"evidence_reuse": "fresh-prefix-observation", "migration_submitted": False, "proof_receipt": admission["path"]})
        if result != "partial": raise operations.OperationFailure(result.removeprefix("persistence-migration-"))
    binding = operation_binding(lambda task, seconds, operation, on_receipt=None: accepted_completion(task, seconds, operation, on_receipt, args.migration_profile,
            {"scheduling_binding": observer["context"]["scheduling_binding"], "prefix_receipt_sha256": "sha256:" + admission["sha256"]}
            if args.migration_profile == "scheduling" else None))
    return binding.run(mode=args.migration_operation, definition=task_definition, network=network, overrides=overrides,
        seconds=seconds, new_operation=args.new_operation, expected_operation=args.expected_operation,
        admission=admission, authorize_successor=authorize_successor,
        authorize_submission=authorize_submission if args.migration_profile == "scheduling" else None)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Collect one persistence acceptance record from independently observed AWS facts."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-24"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Record persistence-scope acceptance only after AWS independently confirms every required rehearsal task, final workload, recovery-point cleanup, budget, and qualified immutable package identity.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
#   effects: [network, writes-files]
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from functools import lru_cache

import yaml


ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, ACCOUNT = "kanbien-dev", "eu-west-1", "337159794548"
TARGET, SCOPE, CLUSTER = "kanbien-core-platform", "core-server-persistence", "kanbien-core-platform"
STACK = "kanbien-core-platform-core-server-persistence"
SERVICE = "kanbien-core-platform-core-server-persistence"
DATABASE = "kanbien-core-platform-persistence"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
RECORD = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/accepted-release.yml"
TASK_ARN = re.compile(rf"^arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/[0-9a-f]{{32}}$")
SNAPSHOT = re.compile(r"^kanbien-core-platform-persistence-recovery-[0-9]{8}(?:-[a-z0-9]{1,8})?$")
TASKS: dict[str, dict[str, Any]] = {}


class EvidenceFailure(Exception):
    pass


def report(verdict: str, *codes: str) -> int:
    print(json.dumps({"schema": "deploy/persistence-acceptance-collection-report/v1", "target": TARGET, "scope": SCOPE, "verdict": verdict, "findings": [{"code": code} for code in dict.fromkeys(codes)]}, sort_keys=True))
    return 0 if verdict in {"ready", "recorded"} else 1


def aws(*parts: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True, timeout=30, env={**os.environ, "AWS_PAGER": ""}, check=False)
    except subprocess.TimeoutExpired as error:
        raise EvidenceFailure("acceptance-evidence-aws-observation-timeout") from error
    if completed.returncode:
        detail = completed.stderr.lower()
        code = "acceptance-evidence-aws-access-denied" if "accessdenied" in detail or "not authorized" in detail else "acceptance-evidence-aws-observation-failed"
        raise EvidenceFailure(code)
    try:
        parsed = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise EvidenceFailure("acceptance-evidence-aws-response-invalid") from error
    if not isinstance(parsed, dict):
        raise EvidenceFailure("acceptance-evidence-aws-response-invalid")
    return parsed


def receipt(path: Path) -> dict[str, str]:
    command = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceFailure("acceptance-evidence-package-receipt-unreadable") from error
    if not isinstance(candidate, dict):
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as snapshot:
        json.dump(candidate, snapshot)
        snapshot.flush()
        completed = subprocess.run(["bash", str(command), "--receipt", snapshot.name, "--expected-target", TARGET, "--expected-candidate", "kanbien-core-server-persistence-candidate", "--expected-package-contract", "kanbien-core-server-persistence-image", "--expected-program", "kanbien-core-server-persistence", "--json"], capture_output=True, text=True, check=False)
    required = ("source_revision", "image_digest", "receipt_reference")
    if completed.returncode or not all(isinstance(candidate.get(key), str) and candidate[key] for key in required):
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    digest = candidate["image_digest"]
    if re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is None:
        raise EvidenceFailure("acceptance-evidence-package-receipt-invalid")
    return {key: candidate[key] for key in required}


def parsed_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid") from error
    if parsed.tzinfo is None:
        raise EvidenceFailure("acceptance-evidence-task-timestamp-invalid")
    return parsed.astimezone(timezone.utc)


def contract_deadlines() -> dict[str, int]:
    path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise EvidenceFailure("acceptance-evidence-scope-contract-unreadable") from error
    workloads = document.get("health_recovery", {}).get("workloads") if isinstance(document, dict) else None
    if not isinstance(workloads, list):
        raise EvidenceFailure("acceptance-evidence-scope-contract-invalid")
    deadlines: dict[str, int] = {}
    for workload in workloads:
        if not isinstance(workload, dict) or not isinstance(workload.get("id"), str):
            continue
        completion = workload.get("completion")
        value = completion.get("deadline_seconds") if isinstance(completion, dict) else None
        if workload["id"] in {"private-release-verifier", "persistence-migration", "persistence-restoration-verifier"} and type(value) is int and value > 0:
            deadlines[workload["id"]] = value
    if set(deadlines) != {"private-release-verifier", "persistence-migration", "persistence-restoration-verifier"}:
        raise EvidenceFailure("acceptance-evidence-scope-contract-invalid")
    return deadlines


@lru_cache(maxsize=8)
def task_definition(arn: str) -> dict[str, Any]:
    response = aws("ecs", "describe-task-definition", "--task-definition", arn)
    definition = response.get("taskDefinition")
    if not isinstance(definition, dict):
        raise EvidenceFailure("acceptance-evidence-task-definition-unavailable")
    return definition


def preload_tasks(arns: list[str]) -> None:
    """Observe the immutable proof set together, not through serial task reads."""
    unique = list(dict.fromkeys(arns))
    if not unique or any(TASK_ARN.fullmatch(arn) is None for arn in unique):
        raise EvidenceFailure("acceptance-evidence-task-identity-invalid")
    response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", *unique)
    tasks = response.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != len(unique):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    observed = {item.get("taskArn"): item for item in tasks if isinstance(item, dict) and isinstance(item.get("taskArn"), str)}
    if set(observed) != set(unique):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    TASKS.update(observed)


def observed_task(arn: str) -> dict[str, Any]:
    task = TASKS.get(arn)
    if task is None:
        response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arn)
        tasks = response.get("tasks")
        task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
        if isinstance(task, dict):
            TASKS[arn] = task
    if not isinstance(task, dict):
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    return task


def definition_identity(arn: object, expected_family: str, expected_digest: str) -> None:
    if not isinstance(arn, str):
        raise EvidenceFailure("acceptance-evidence-task-definition-unavailable")
    definition = task_definition(arn)
    containers = definition.get("containerDefinitions")
    if definition.get("family") != expected_family or not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        raise EvidenceFailure("acceptance-evidence-task-definition-mismatch")
    image = containers[0].get("image")
    if not isinstance(image, str) or not image.endswith("@" + expected_digest):
        raise EvidenceFailure("acceptance-evidence-task-image-mismatch")


def expected_stream(kind: str, task_id: str) -> str:
    prefixes = {"verifier": "persistence-verifier/private-persistence-verifier", "migration": "persistence-migration/persistence-migration", "restore": "persistence-restoration-verifier/persistence-restoration-verifier"}
    return f"{prefixes[kind]}/{task_id}"


def log_has_code(kind: str, arn: str, code: str) -> None:
    task_id = arn.rsplit("/", 1)[-1]
    response = aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", expected_stream(kind, task_id), "--start-from-head")
    events = response.get("events")
    if not isinstance(events, list) or not any(isinstance(event, dict) and isinstance(event.get("message"), str) and '"verdict":"accepted"' in event["message"] and f'"code":"{code}"' in event["message"] for event in events):
        raise EvidenceFailure("acceptance-evidence-safe-result-code-missing")


def task_fact(name: str, arn: str, kind: str, family: str, digest: str, code: str, deadline: int) -> dict[str, Any]:
    if TASK_ARN.fullmatch(arn) is None:
        raise EvidenceFailure("acceptance-evidence-task-identity-invalid")
    task = observed_task(arn)
    if task is None or task.get("taskArn") != arn or task.get("lastStatus") != "STOPPED":
        raise EvidenceFailure("acceptance-evidence-task-not-terminal")
    containers = task.get("containers")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or type(containers[0].get("exitCode")) is not int or containers[0]["exitCode"] != 0:
        raise EvidenceFailure("acceptance-evidence-task-unsuccessful")
    started, stopped = parsed_time(task.get("startedAt")), parsed_time(task.get("stoppedAt"))
    duration = int((stopped - started).total_seconds())
    if duration < 0 or duration > deadline:
        raise EvidenceFailure("acceptance-evidence-task-deadline-exceeded")
    definition_identity(task.get("taskDefinitionArn"), family, digest)
    log_has_code(kind, arn, code)
    return {"name": name, "task_arn": arn, "task_definition": task["taskDefinitionArn"], "image_digest": digest, "started_at": started.isoformat().replace("+00:00", "Z"), "stopped_at": stopped.isoformat().replace("+00:00", "Z"), "duration_seconds": duration, "result_code": code}


def server_task(arn: str, digest: str) -> dict[str, Any]:
    if TASK_ARN.fullmatch(arn) is None:
        raise EvidenceFailure("acceptance-evidence-server-task-identity-invalid")
    task = observed_task(arn)
    if task is None or task.get("taskArn") != arn or task.get("group") != f"service:{SERVICE}":
        raise EvidenceFailure("acceptance-evidence-server-task-invalid")
    definition_identity(task.get("taskDefinitionArn"), "kanbien-core-platform-core-server-persistence", digest)
    started = parsed_time(task.get("startedAt"))
    stopped = parsed_time(task.get("stoppedAt")) if task.get("lastStatus") == "STOPPED" else None
    return {"task_arn": arn, "task_definition": task["taskDefinitionArn"], "started_at": started, "stopped_at": stopped, "stopped_reason": task.get("stoppedReason")}


def parse_proofs(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if value.count("=") != 1:
            raise EvidenceFailure("acceptance-evidence-proof-argument-invalid")
        name, arn = value.split("=", 1)
        if not name or not arn or name in result:
            raise EvidenceFailure("acceptance-evidence-proof-argument-invalid")
        result[name] = arn
    return result


def receipt_module():
    path = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"
    specification = importlib.util.spec_from_file_location("persistence_proof_receipts", path)
    module = importlib.util.module_from_spec(specification)
    assert specification and specification.loader
    specification.loader.exec_module(module)
    return module


def parse_proof_receipts(values: list[str], required: dict[str, tuple[str, str, str, str, str]], deadlines: dict[str, int], receipt_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Validate retained controller receipts without re-querying aged ECS tasks."""
    result: dict[str, dict[str, Any]] = {}
    receipt_paths: dict[str, Path] = {}
    root = receipt_root.resolve() if receipt_root is not None else ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts"
    module = receipt_module()
    for value in values:
        if value.count("=") != 1:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-argument-invalid")
        name, raw_path = value.split("=", 1)
        path = Path(raw_path).resolve()
        if not name or name in result or root not in path.parents:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-argument-invalid")
        try:
            item = module.validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-invalid") from error
        result[name] = item
        receipt_paths[name] = path
    if set(result) != set(required):
        raise EvidenceFailure("acceptance-evidence-proof-receipt-set-invalid")
    observed: dict[str, dict[str, Any]] = {}
    controllers = {"migration": "run-migration", "verifier": "verify-candidate", "restore": "rehearse-isolated-database-restore", "server-replacement": "rehearse-server-replacement"}
    operations = {"migration-apply": "apply", "effective-privilege": "prove-effective-privilege", "server-replacement": "controlled-replacement", "server-replacement-read": "read", "credential-rotation": "rotate", "credential-revocation": "revoke", "credential-revocation-unready": "health-unready", "credential-recovery": "rotate", "credential-recovery-health": "health-ready", "credential-recovery-read": "read", "rollback-b-health": "health-ready", "rollback-b-read": "read", "rollback-final-health": "health-ready", "rollback-final-read": "read", "isolated-restore": "isolated-restore"}
    for name, (kind, family, expected_digest, code, workload) in required.items():
        item = result[name]
        task = item["task"]
        if kind not in controllers or name not in operations:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-mapping-invalid")
        if item["proof_type"] != kind or item["operation"] != operations[name] or task["result_code"] != code or task["image_digest"] != expected_digest or item["provenance"]["controller"] != controllers[kind] or item["provenance"]["collection_method"] != "ecs-terminal-task+task-definition+safe-log":
            raise EvidenceFailure("acceptance-evidence-proof-receipt-mismatch")
        replacement = kind == "server-replacement"
        if TASK_ARN.fullmatch(task["arn"]) is None or not isinstance(task["definition"], str) or f":task-definition/{family}:" not in task["definition"] or task["terminal_status"] != "STOPPED" or (not replacement and task["exit_code"] != 0) or (replacement and task.get("stopped_reason") != "governed core-server-persistence replacement rehearsal"):
            raise EvidenceFailure("acceptance-evidence-proof-receipt-terminal-invalid")
        started, stopped = parsed_time(task["started_at"]), parsed_time(task["stopped_at"])
        if parsed_time(item["provenance"]["collected_at"]) < stopped:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-provenance-invalid")
        duration = int((stopped - started).total_seconds())
        if duration < 0 or (workload is not None and duration > deadlines[workload]):
            raise EvidenceFailure("acceptance-evidence-proof-receipt-deadline-exceeded")
        context = item["context"]
        if "completion_duration_seconds" in context and context["completion_duration_seconds"] != duration:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-duration-mismatch")
        if workload is not None and context.get("completion_deadline_seconds") != deadlines[workload]:
            raise EvidenceFailure("acceptance-evidence-proof-receipt-deadline-mismatch")
        if replacement:
            try:
                successor_started = parsed_time(context["successor_started_at"])
                boundary = parsed_time(context["recovery_boundary"])
            except (KeyError, EvidenceFailure) as error:
                raise EvidenceFailure("acceptance-evidence-server-replacement-receipt-invalid") from error
            if context.get("original_stopped_reason") != "governed core-server-persistence replacement rehearsal" or context.get("runtime_task_definition") != task["definition"] or context.get("successor_task_arn") == task["arn"] or successor_started <= started or boundary < started or boundary > stopped:
                raise EvidenceFailure("acceptance-evidence-server-replacement-receipt-invalid")
        try:
            receipt_path = str(receipt_paths[name].relative_to(ROOT))
        except ValueError:  # test-only injected root; production receipts are repo-relative.
            receipt_path = str(receipt_paths[name])
        observed[name] = {"name": name, "task_arn": task["arn"], "task_definition": task["definition"], "image_digest": task["image_digest"], "started_at": task["started_at"], "stopped_at": task["stopped_at"], "duration_seconds": duration, "result_code": task["result_code"], "receipt": receipt_path}
    return observed


def stack_outputs() -> dict[str, str]:
    response = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = response.get("Stacks")
    stack = stacks[0] if isinstance(stacks, list) and len(stacks) == 1 and isinstance(stacks[0], dict) else None
    if stack is None or stack.get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        raise EvidenceFailure("acceptance-evidence-runtime-stack-not-stable")
    outputs = stack.get("Outputs")
    result = {item.get("OutputKey"): item.get("OutputValue") for item in outputs if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)} if isinstance(outputs, list) else {}
    required = {"CoreServerPersistenceTaskDefinitionArn", "CoreServerPersistenceVerifierTaskDefinitionArn", "CoreServerPersistenceMigrationTaskDefinitionArn", "CoreServerPersistenceRestorationVerifierTaskDefinitionArn"}
    if not required <= set(result):
        raise EvidenceFailure("acceptance-evidence-runtime-stack-outputs-invalid")
    return result


def current_service(expected_server_definition: str, digest: str) -> dict[str, str]:
    response = aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    services = response.get("services")
    service = services[0] if isinstance(services, list) and len(services) == 1 and isinstance(services[0], dict) else None
    deployments = service.get("deployments") if isinstance(service, dict) else None
    if not isinstance(service, dict) or service.get("status") != "ACTIVE" or service.get("desiredCount") != 1 or service.get("runningCount") != 1 or service.get("taskDefinition") != expected_server_definition or not isinstance(deployments, list) or not any(isinstance(item, dict) and item.get("status") == "PRIMARY" and item.get("rolloutState") == "COMPLETED" for item in deployments):
        raise EvidenceFailure("acceptance-evidence-current-service-unhealthy")
    definition_identity(expected_server_definition, "kanbien-core-platform-core-server-persistence", digest)
    response = aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE, "--desired-status", "RUNNING")
    arns = response.get("taskArns")
    if not isinstance(arns, list) or len(arns) != 1 or not isinstance(arns[0], str):
        raise EvidenceFailure("acceptance-evidence-current-service-task-invalid")
    task_response = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", arns[0])
    tasks = task_response.get("tasks")
    task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
    if task is None or task.get("lastStatus") != "RUNNING" or task.get("taskDefinitionArn") != expected_server_definition:
        raise EvidenceFailure("acceptance-evidence-current-service-task-invalid")
    return {"service": SERVICE, "task_definition": expected_server_definition, "running_task": arns[0]}


def database_posture(snapshot_id: str) -> dict[str, str]:
    database = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE).get("DBInstances")
    instance = database[0] if isinstance(database, list) and len(database) == 1 and isinstance(database[0], dict) else None
    if not isinstance(instance, dict) or instance.get("DBInstanceStatus") != "available" or instance.get("Engine") != "postgres" or instance.get("PubliclyAccessible") is not False or instance.get("StorageEncrypted") is not True or instance.get("DeletionProtection") is not True:
        raise EvidenceFailure("acceptance-evidence-source-database-posture-invalid")
    snapshots = aws("rds", "describe-db-snapshots", "--db-snapshot-identifier", snapshot_id).get("DBSnapshots")
    snapshot = snapshots[0] if isinstance(snapshots, list) and len(snapshots) == 1 and isinstance(snapshots[0], dict) else None
    if not isinstance(snapshot, dict) or snapshot.get("Status") != "available" or snapshot.get("Encrypted") is not True or snapshot.get("DBInstanceIdentifier") != DATABASE:
        raise EvidenceFailure("acceptance-evidence-recovery-point-invalid")
    restored_identifier = snapshot_id.replace("-recovery-", "-restore-", 1)
    check = subprocess.run(["aws", "rds", "describe-db-instances", "--db-instance-identifier", restored_identifier, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True, env={**os.environ, "AWS_PAGER": ""}, check=False)
    if check.returncode == 0:
        raise EvidenceFailure("acceptance-evidence-restored-database-not-cleaned-up")
    if "DBInstanceNotFound" not in check.stderr:
        raise EvidenceFailure("acceptance-evidence-restored-database-observation-failed")
    return {"database": DATABASE, "snapshot": snapshot_id, "restored_database": restored_identifier, "restore_cleanup": "confirmed-absent"}


def live_budget() -> None:
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    try:
        specification = importlib.util.spec_from_file_location("persistence_acceptance_prepare", path)
        if specification is None or specification.loader is None:
            raise OSError("provider preparation module unavailable")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        result = module.live_budget()
    except (OSError, AttributeError, TypeError, ValueError) as error:
        raise EvidenceFailure("acceptance-evidence-budget-observation-failed") from error
    if not isinstance(result, tuple) or not result or result[0] is not True:
        raise EvidenceFailure("acceptance-evidence-target-budget-invalid")


def write_record(record: dict[str, Any]) -> None:
    metadata = {"schema": "agentic-artifact/v3", "id": "infra.04-deploy.03-product.targets.kanbien-core-platform.scope.core-server-persistence.accepted-release", "version": 1, "status": "active", "created_on": "2026-10-24", "updated_on": "2026-10-24", "layer": "04.deploy", "domain": "deployment.core-server-persistence", "disciplines": ["security", "sre"], "kind": "accepted-release-record", "purpose": "Record the qualified persistence release and AWS-observed proof set accepted for core-server-persistence.", "portability": {"class": "internal", "targets": []}, "used_by": [{"id": "deploy.command.core-platform-target-declaration", "path": "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh"}]}
    rendered = "# agentic-artifact:\n" + "".join("#   " + line + "\n" for line in yaml.safe_dump(metadata, sort_keys=False).splitlines()) + yaml.safe_dump(record, sort_keys=False)
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECORD.parent, prefix=f".{RECORD.name}.", suffix=".tmp", delete=False) as output:
        temporary = Path(output.name)
        output.write(rendered)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, RECORD)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--rollback-receipt", type=Path, required=True); parser.add_argument("--proof", action="append", default=[]); parser.add_argument("--proof-receipt", action="append", default=[]); parser.add_argument("--server-replacement-original"); parser.add_argument("--server-replacement-successor"); parser.add_argument("--recovery-snapshot"); parser.add_argument("--write", action="store_true"); parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or not isinstance(args.server_replacement_original, str) or not isinstance(args.server_replacement_successor, str) or not isinstance(args.recovery_snapshot, str) or SNAPSHOT.fullmatch(args.recovery_snapshot) is None:
        return report("blocked", "acceptance-evidence-arguments-invalid")
    try:
        candidate, rollback = receipt(args.receipt), receipt(args.rollback_receipt)
        if candidate["image_digest"] == rollback["image_digest"]:
            raise EvidenceFailure("acceptance-evidence-rollback-identity-invalid")
        required = {
            "migration-apply": ("migration", "kanbien-core-platform-persistence-migration", candidate["image_digest"], "PERSISTENCE_MIGRATION_APPLIED", "persistence-migration"), "effective-privilege": ("migration", "kanbien-core-platform-persistence-migration", candidate["image_digest"], "PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN", "persistence-migration"), "server-replacement": ("server-replacement", "kanbien-core-platform-core-server-persistence", candidate["image_digest"], "PERSISTENCE_SERVER_REPLACED", None), "server-replacement-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"), "credential-rotation": ("migration", "kanbien-core-platform-persistence-migration", candidate["image_digest"], "PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED", "persistence-migration"), "credential-revocation": ("migration", "kanbien-core-platform-persistence-migration", candidate["image_digest"], "PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED", "persistence-migration"), "credential-revocation-unready": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", "private-release-verifier"), "credential-recovery": ("migration", "kanbien-core-platform-persistence-migration", candidate["image_digest"], "PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED", "persistence-migration"), "credential-recovery-health": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"), "credential-recovery-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"), "rollback-b-health": ("verifier", "kanbien-core-platform-persistence-verifier", rollback["image_digest"], "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"), "rollback-b-read": ("verifier", "kanbien-core-platform-persistence-verifier", rollback["image_digest"], "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"), "rollback-final-health": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"), "rollback-final-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"), "isolated-restore": ("restore", "kanbien-core-platform-persistence-restoration-verifier", candidate["image_digest"], "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED", "persistence-restoration-verifier")}
        deadlines = contract_deadlines()
        if args.proof and args.proof_receipt:
            raise EvidenceFailure("acceptance-evidence-proof-source-ambiguous")
        if args.proof_receipt:
            observed = parse_proof_receipts(args.proof_receipt, required, deadlines)
        else:
            proofs = parse_proofs(args.proof)
            if set(proofs) != set(required):
                raise EvidenceFailure("acceptance-evidence-proof-set-invalid")
            # Every proof and the retired original must be terminal.  The
            # successor is deliberately live, so observe it separately below.
            preload_tasks([*proofs.values(), args.server_replacement_original])
            observed = {name: task_fact(name, proofs[name], kind, family, digest, code, deadlines[workload]) for name, (kind, family, digest, code, workload) in required.items()}
        if args.proof_receipt:
            replacement = observed["server-replacement"]
            original = {"task_arn": replacement["task_arn"], "task_definition": replacement["task_definition"], "started_at": parsed_time(replacement["started_at"]), "stopped_at": parsed_time(replacement["stopped_at"]), "stopped_reason": "governed core-server-persistence replacement rehearsal"}
            # The receipt parser has already authenticated the bounded
            # relationship; do not re-query the aged predecessor/successor.
            source_path = next(value.split("=", 1)[1] for value in args.proof_receipt if value.startswith("server-replacement="))
            receipt_value = receipt_module().validate(json.loads(Path(source_path).read_text(encoding="utf-8")))
            successor = {"task_arn": receipt_value["context"]["successor_task_arn"], "task_definition": receipt_value["context"]["runtime_task_definition"], "started_at": parsed_time(receipt_value["context"]["successor_started_at"]), "stopped_at": None, "stopped_reason": None}
        else:
            original, successor = server_task(args.server_replacement_original, candidate["image_digest"]), server_task(args.server_replacement_successor, candidate["image_digest"])
        # ECS may start a healthy replacement slightly before it stops the
        # retiring task.  Require the governed retirement and an independent
        # read after the replacement begins; ordering task starts after stops
        # would reject that normal, availability-preserving service behaviour.
        if original["stopped_at"] is None or original["stopped_reason"] != "governed core-server-persistence replacement rehearsal" or successor["started_at"] <= original["started_at"] or parsed_time(observed["server-replacement-read"]["started_at"]) < successor["started_at"]:
            raise EvidenceFailure("acceptance-evidence-server-replacement-sequence-invalid")
        order = (("credential-revocation", "credential-revocation-unready"), ("credential-revocation-unready", "credential-recovery"), ("credential-recovery", "credential-recovery-health"), ("credential-recovery-health", "credential-recovery-read"), ("rollback-b-health", "rollback-b-read"), ("rollback-b-read", "rollback-final-health"), ("rollback-final-health", "rollback-final-read"))
        for prior, later in order:
            if parsed_time(observed[later]["started_at"]) < parsed_time(observed[prior]["stopped_at"]):
                raise EvidenceFailure("acceptance-evidence-rehearsal-sequence-invalid")
        outputs = stack_outputs(); current = current_service(outputs["CoreServerPersistenceTaskDefinitionArn"], candidate["image_digest"]); database = database_posture(args.recovery_snapshot); live_budget()
        stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        serialise = lambda item: {key: value.isoformat().replace("+00:00", "Z") if isinstance(value, datetime) else value for key, value in item.items()}
        record = {"schema": "deploy/persistence-accepted-release/v1", "target": TARGET, "scope": SCOPE, "status": "accepted", "release": {"source_revision": candidate["source_revision"], "image_digest": candidate["image_digest"], "image_repository": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server", "package_custody_reference": candidate["receipt_reference"], "runtime_stack": STACK, "service": SERVICE, "runtime_task_definition": outputs["CoreServerPersistenceTaskDefinitionArn"], "verifier_task_definition": outputs["CoreServerPersistenceVerifierTaskDefinitionArn"], "migration_task_definition": outputs["CoreServerPersistenceMigrationTaskDefinitionArn"], "restoration_verifier_task_definition": outputs["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]}, "acceptance": {"accepted_at": stamp, "collector": "collect-acceptance-evidence", "retained_for_restoration": True, "rollback_release": {"source_revision": rollback["source_revision"], "image_digest": rollback["image_digest"], "package_custody_reference": rollback["receipt_reference"]}}, "provider_observation": {"current_service": current, "database": database, "proofs": observed, "server_replacement": {"original_task": serialise(original), "replacement_task": serialise(successor)}}}
        if args.write:
            if RECORD.exists():
                raise EvidenceFailure("acceptance-evidence-record-already-exists")
            write_record(record)
        return report("recorded" if args.write else "ready")
    except EvidenceFailure as error:
        return report("blocked", str(error))


if __name__ == "__main__":
    raise SystemExit(main())

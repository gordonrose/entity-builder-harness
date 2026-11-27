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
    "grant-scheduling-access": "PERSISTENCE_SCHEDULING_ACCESS_GRANTED",
    "observe-scheduling-state": "PERSISTENCE_SCHEDULING_STATE_CONFIRMED",
    "observe-scheduling-prefix": "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED",
    "prove-scheduling-access": "PERSISTENCE_SCHEDULING_PRIVILEGE_PROVEN",
    "seed-scheduling-proof": "PERSISTENCE_SCHEDULING_PROOF_SEEDED",
    "observe-scheduling-proof": "PERSISTENCE_SCHEDULING_PROOF_OBSERVED",
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
    "grant-scheduling-access",
    "observe-scheduling-state",
    "observe-scheduling-prefix",
    "prove-scheduling-access",
    "seed-scheduling-proof",
    "observe-scheduling-proof",
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


def accepted_log(task: dict[str, object], operation: str) -> tuple[dict[str, object] | None, str]:
    arn = task.get("taskArn")
    if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]:
        return None, "persistence-administration-evidence-unavailable"
    stream = f"persistence-administration/persistence-administration/{arn.rsplit('/', 1)[-1]}"
    ok, events, code = MIGRATION.aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", stream, "--start-from-head")
    messages = [item.get("message") for item in events.get("events", []) if isinstance(item, dict)] if ok and isinstance(events, dict) else []
    expected = SUCCESS[operation]
    allowed = {expected} if isinstance(expected, str) else set(expected)
    synthetic_results = []
    for message in messages:
        try:
            record = json.loads(message) if isinstance(message, str) else None
        except (json.JSONDecodeError, TypeError):
            continue
        fields = {"verdict", "code"} | ({"database_state"} if operation in RECEIPTS.SCHEDULING_STATE.RESULTS else set())
        if operation == RECEIPTS.SCHEDULING_STATE.PREFIX_OPERATION: fields.add("migration_prefix")
        if operation in RECEIPTS.SCHEDULING_PROOF.PROOF_OPERATIONS:
            fields.add("scheduling_seed" if operation == "seed-scheduling-proof" else "scheduling_observation")
        if isinstance(record, dict) and set(record) == fields and record.get("verdict") == "accepted" and isinstance(record.get("code"), str) and record.get("code") in allowed:
            if "database_state" in fields:
                try: RECEIPTS.SCHEDULING_STATE.validate(record["database_state"])
                except ValueError: return None, "persistence-administration-not-confirmed"
            if "migration_prefix" in fields:
                try: RECEIPTS.SCHEDULING_STATE.validate_prefix(record["migration_prefix"], minimum_applied_migrations=2, manifest_migration_count=7)
                except ValueError: return None, "persistence-administration-not-confirmed"
            if operation in RECEIPTS.SCHEDULING_PROOF.PROOF_OPERATIONS:
                try:
                    rows = task["overrides"]["containerOverrides"]
                    if len(rows) != 1 or rows[0]["name"] != "persistence-administration": raise ValueError()
                    environment = {row["name"]: row["value"] for row in rows[0]["environment"]}
                    if len(environment) != len(rows[0]["environment"]): raise ValueError()
                    expected = {"PERSISTENCE_ADMINISTRATION_OPERATION", "PERSISTENCE_SCHEDULING_PROOF_ID"}
                    if operation == "seed-scheduling-proof": expected.add("PERSISTENCE_SCHEDULING_PROOF_DUE_AT")
                    if set(environment) != expected or environment["PERSISTENCE_ADMINISTRATION_OPERATION"] != operation: raise ValueError()
                    if operation == "seed-scheduling-proof":
                        seed = RECEIPTS.SCHEDULING_PROOF.proof_seed(record["scheduling_seed"])
                        if (seed["schedule_id"], seed["due_at"]) != (environment["PERSISTENCE_SCHEDULING_PROOF_ID"], environment["PERSISTENCE_SCHEDULING_PROOF_DUE_AT"]): raise ValueError()
                    else:
                        RECEIPTS.SCHEDULING_PROOF.proof_snapshot(record["scheduling_observation"], scope="core-server-persistence",
                            selection={"kind": "schedule", "id": environment["PERSISTENCE_SCHEDULING_PROOF_ID"]}, start=task["startedAt"], stop=task["stoppedAt"])
                except (ValueError, KeyError, TypeError): return None, "persistence-administration-not-confirmed"
            if operation in RECEIPTS.SCHEDULING_PROOF.PROOF_OPERATIONS: synthetic_results.append(record)
            else: return record, "ok"
    if len(synthetic_results) == 1: return synthetic_results[0], "ok"
    return None, code if not ok else "persistence-administration-not-confirmed"


def accept(task: dict[str, object], seconds: int, operation: str, on_receipt=None, scheduling_binding=None) -> int:
    terminal = {}
    def unsuccessful(code, *, facts=None):
        return report("failed" if terminal else "blocked", code, facts={**(facts or {}), **terminal})
    observed = MIGRATION.duration(task)
    if observed is None:
        return report("blocked", "persistence-administration-duration-unavailable")
    if on_receipt is not None and (observed > seconds or not MIGRATION.task_exit(task)):
        try:
            digest = MIGRATION.image_digest(task.get("taskDefinitionArn"))
            if digest is None: raise ValueError()
            failure = "persistence-administration-completion-deadline-exceeded" if observed > seconds else "persistence-administration-unsuccessful-completion"
            receipt = RECEIPTS.make(proof_type="administration", operation=operation, task=task, image_digest=digest, result_code=failure,
                context={"completion_deadline_seconds": seconds, "completion_duration_seconds": observed}, controller="run-administration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
            path = RECEIPTS.persist(receipt)
            on_receipt(path)
            terminal = {"operation_id": task.get("startedBy"), "operation": operation,
                        "proof_receipt": path.relative_to(ROOT).as_posix(), "proof_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        except Exception: return report("uncertain", "persistence-administration-receipt-persistence-failed", facts={"operation_id": task.get("startedBy")})
    if observed > seconds:
        return unsuccessful("persistence-administration-completion-deadline-exceeded")
    if not MIGRATION.task_exit(task):
        # Use the task's actual log stream and a closed reader; never replay it.
        arn = task.get("taskArn")
        known_facts = {}
        if isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[0-9a-f]{32}", arn):
            known_facts["administration_task"] = arn.rsplit("/", 1)[-1]
        if isinstance(arn, str) and arn.rsplit("/", 1)[-1]:
            ok, events, _ = MIGRATION.aws("logs", "get-log-events", "--log-group-name", LOG_GROUP, "--log-stream-name", f"persistence-administration/persistence-administration/{arn.rsplit('/', 1)[-1]}", "--start-from-head")
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
    result, code = accepted_log(task, operation)
    if result is None:
        return report("blocked", code)
    result_code = result["code"]
    digest = MIGRATION.image_digest(task.get("taskDefinitionArn"))
    arn = task.get("taskArn")
    if not isinstance(digest, str) or not isinstance(arn, str):
        return report("blocked", "persistence-administration-receipt-identity-unavailable")
    try:
        context = {"completion_deadline_seconds": seconds, "completion_duration_seconds": observed}
        if "database_state" in result: context["database_state"] = result["database_state"]
        if "migration_prefix" in result: context["migration_prefix"] = result["migration_prefix"]
        for field in ("scheduling_seed", "scheduling_observation"):
            if field in result: context[field] = result[field]
        if scheduling_binding is not None: context["scheduling_binding"] = RECEIPTS.validate_scheduling_binding(scheduling_binding())
        receipt = RECEIPTS.make(proof_type="administration", operation=operation, task=task, image_digest=digest, result_code=result_code, context=context, controller="run-administration", collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        path = RECEIPTS.persist(receipt)
        if on_receipt is not None: on_receipt(path)
    except Exception:
        return report("uncertain" if on_receipt is not None else "blocked", "persistence-administration-receipt-persistence-failed",
            facts={"operation_id": task.get("startedBy")} if on_receipt is not None else None)
    return report("accepted", "persistence-administration-applied", facts={"operation": operation, "safe_result_code": result_code, "administration_task": arn.rsplit("/", 1)[-1], "completion_deadline_seconds": seconds, "completion_duration_seconds": observed, "proof_receipt": str(path.relative_to(ROOT)), **({"operation_id": task.get("startedBy"), "evidence_reuse": "fresh-terminal-observation"} if on_receipt is not None else {})})


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


def operation_binding(accept_callback):
    return MIGRATION.task_operations().BoundOperation(root=ROOT, proof_type="administration", family="kanbien-core-platform-persistence-administration",
        container="persistence-administration", selector="PERSISTENCE_ADMINISTRATION_OPERATION", results=SUCCESS,
        aws=MIGRATION.aws, report=report, accept=accept_callback, receipts=RECEIPTS)


def scheduling_reservation_census(task_definition_arns):
    """All four native maintenance task owners, including unknown originals."""
    operations = MIGRATION.task_operations()
    verifier = RECEIPTS.owner("core_cost_verifier", "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py")
    restore = RECEIPTS.owner("core_cost_restore", "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py")
    restore.ROOT = ROOT
    values = [*operation_binding(None).reservation_census(task_definition_arns),
        *MIGRATION.operation_binding(None).reservation_census(task_definition_arns),
        *operations.reservation_census(ROOT, "private-persistence-verifier", verifier.SUCCESS, verifier.load_operation, task_definition_arns),
        *restore.scheduling_reservation_census(task_definition_arns)]
    if len({value["operation_id"] for value in values}) != len(values):
        raise operations.OperationFailure("reservation-census-identity-conflict")
    return sorted(values, key=lambda value: value["operation_id"])


def _validate_scheduling_packet(packet, *, expected_binding, required_after, state=False, preparation=False):
    """Pure native journal/receipt validation for a self-contained proof bundle."""
    try:
        if not isinstance(packet, dict) or set(packet) != {"journal", "receipt"}: raise ValueError()
        proof = RECEIPTS.validate(packet["receipt"])
        operation, task, context = proof["operation"], proof["task"], proof["context"]
        allowed = RECEIPTS.SCHEDULING_STATE.RESULTS if preparation else {"observe-scheduling-state"} if state else RECEIPTS.SCHEDULING_PROOF.PROOF_OPERATIONS
        if operation not in allowed or state and preparation: raise ValueError()
        controller = operation_binding(None)
        journal = controller.load(None, operation, document=packet["journal"])
        if controller.completion(journal, receipt=proof) != proof: raise ValueError()
        binding = RECEIPTS.validate_scheduling_binding(expected_binding)
        if (journal["request"].get("scheduling_binding") != binding or context.get("scheduling_binding") != binding
                or journal["request"]["admission"] is not None or task["exit_code"] != 0
                or task["result_code"] != SUCCESS[operation]
                or proof["provenance"].get("evidence_class") != RECEIPTS.EVIDENCE_CLASS
                or proof["provenance"]["controller"] != "run-administration"
                or proof["provenance"]["collection_method"] != "ecs-terminal-task+task-definition+safe-log"
                or Path(journal["proof_receipt"]).is_absolute() or ".." in Path(journal["proof_receipt"]).parts): raise ValueError()
        start, stop, boundary, collected = (MIGRATION.timestamp(item) for item in (task["started_at"], task["stopped_at"], required_after, proof["provenance"]["collected_at"]))
        if any(item is None for item in (start, stop, boundary, collected)) or not boundary <= start <= stop <= collected or context["completion_duration_seconds"] > context["completion_deadline_seconds"]: raise ValueError()
        field = "database_state" if state or preparation else "scheduling_seed" if operation == "seed-scheduling-proof" else "scheduling_observation"
        environment = {row["name"]: row["value"] for row in journal["request"]["overrides"]["containerOverrides"][0]["environment"]}
        selection = None if state or preparation else {"kind": "schedule", "id": environment["PERSISTENCE_SCHEDULING_PROOF_ID"]}
        if operation == "seed-scheduling-proof": selection["due_at"] = environment["PERSISTENCE_SCHEDULING_PROOF_DUE_AT"]
        return {"operation": operation, "result": {field: context[field]}, "selection": selection, "binding": binding,
            "task": {key: task[key] for key in ("arn", "definition", "started_at", "stopped_at")},
            "receipt_sha256": "sha256:" + journal["proof_sha256"], "packet": packet}
    except Exception:
        raise RECEIPTS.ReceiptError("persistence-scheduling-proof-packet-invalid") from None


def _observe_scheduling_receipt(path, *, qualified_path, required_after, source_revision, image_digest, state=False, preparation=False):
    """Read original task/logs and retain its native current-or-history journal.

    No task is submitted, no journal is created, and an older observation is
    not rebound to the current mutable journal after a subsequent observation.
    """
    try:
        original = Path(path).absolute()
        if any(item.is_symlink() for item in (original, *original.parents)) or not original.resolve().is_relative_to(RECEIPTS.RECEIPTS.resolve()) or original.stat().st_size > 1048576: raise ValueError()
        proof = RECEIPTS.validate(json.loads(original.read_bytes()))
        qualified = RECEIPTS.qualified_maintenance(qualified_path)
        if (qualified["source_revision"], qualified["image_digest"]) != (source_revision, image_digest): raise ValueError()
        outputs, _ = MIGRATION.outputs(STACK)
        definition = outputs.get("CoreServerPersistenceAdministrationTaskDefinitionArn") if isinstance(outputs, dict) else None
        binding = MIGRATION.scheduling_database_binding(qualified, outputs, ((definition, "core_runtime"),))
        task = proof["task"]
        if task["definition"] != definition: raise ValueError()
        ok, described, _ = MIGRATION.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", task["arn"])
        rows = described.get("tasks") if ok and isinstance(described, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or described.get("failures"): raise ValueError()
        actual = rows[0]
        operation_id = actual.get("startedBy")
        if not isinstance(operation_id, str) or re.fullmatch(r"kp-[a-f0-9]{32}", operation_id) is None: raise ValueError()
        operations = MIGRATION.task_operations()
        git = operations.subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
        directory = Path(git) / "persistence-administration"
        controller = operation_binding(None)
        current = directory / (proof["operation"] + ".json")
        journal = controller.load(current, proof["operation"])
        if journal["operation_id"] != operation_id:
            journal = controller.load(directory / "history" / (operation_id + ".json"), proof["operation"])
        if journal["proof_receipt"] != original.relative_to(ROOT).as_posix(): raise ValueError()
        packet = {"journal": journal, "receipt": proof}
        checked = _validate_scheduling_packet(packet, expected_binding=binding, required_after=required_after, state=state, preparation=preparation)
        controller.exact(actual, journal)
        if (actual.get("lastStatus") != "STOPPED" or not MIGRATION.task_exit(actual)
                or MIGRATION.timestamp(actual.get("startedAt")) != MIGRATION.timestamp(task["started_at"])
                or MIGRATION.timestamp(actual.get("stoppedAt")) != MIGRATION.timestamp(task["stopped_at"])
                or MIGRATION.duration(actual) != proof["context"]["completion_duration_seconds"]): raise ValueError()
        result, _ = accepted_log(actual, proof["operation"])
        if result != {"verdict": "accepted", "code": task["result_code"], **checked["result"]}: raise ValueError()
        return checked
    except Exception:
        raise RECEIPTS.ReceiptError("persistence-scheduling-proof-not-confirmed") from None


def validate_scheduling_proof_packet(packet, *, expected_binding, required_after):
    return _validate_scheduling_packet(packet, expected_binding=expected_binding, required_after=required_after)


def observe_scheduling_proof_receipt(path, *, qualified_path, required_after, source_revision, image_digest):
    return _observe_scheduling_receipt(path, qualified_path=qualified_path, required_after=required_after,
        source_revision=source_revision, image_digest=image_digest)


def _reobserve_scheduling_packet(packet, *, qualified_path, expected_binding, required_after, preparation=False):
    """Authenticate supplied original custody without accepting a caller task path."""
    try:
        checked = _validate_scheduling_packet(packet, expected_binding=expected_binding, required_after=required_after, preparation=preparation)
        qualified = Path(qualified_path)
        if qualified.is_absolute() or not qualified.parts or any(part in {".", ".."} for part in qualified.parts): raise ValueError()
        observed = _observe_scheduling_receipt(ROOT / packet["journal"]["proof_receipt"], qualified_path=ROOT / qualified,
            required_after=required_after, source_revision=expected_binding["source_revision"], image_digest=expected_binding["image_digest"], preparation=preparation)
        if observed != checked: raise ValueError()
        return observed
    except Exception:
        raise RECEIPTS.ReceiptError("persistence-scheduling-proof-not-confirmed") from None


def reobserve_scheduling_proof_packet(packet, *, qualified_path, expected_binding, required_after):
    return _reobserve_scheduling_packet(packet, qualified_path=qualified_path, expected_binding=expected_binding, required_after=required_after)


def validate_scheduling_preparation_packet(packet, *, expected_binding, required_after):
    return _validate_scheduling_packet(packet, expected_binding=expected_binding, required_after=required_after, preparation=True)


def observe_scheduling_preparation_receipt(path, *, qualified_path, required_after, source_revision, image_digest):
    return _observe_scheduling_receipt(path, qualified_path=qualified_path, required_after=required_after,
        source_revision=source_revision, image_digest=image_digest, preparation=True)


def reobserve_scheduling_preparation_packet(packet, *, qualified_path, expected_binding, required_after):
    return _reobserve_scheduling_packet(packet, qualified_path=qualified_path, expected_binding=expected_binding,
        required_after=required_after, preparation=True)


def observe_scheduling_state_receipt(path, *, qualified_path, required_after, source_revision, image_digest):
    """Current native inventory observation; no zero-work or grant replay claim."""
    checked = _observe_scheduling_receipt(path, qualified_path=qualified_path, required_after=required_after,
        source_revision=source_revision, image_digest=image_digest, state=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    policy = RECEIPTS.owner("core_inventory_freshness", "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
    if policy.observation_expired(checked["task"]["stopped_at"], now, MIGRATION.timestamp):
        raise RECEIPTS.ReceiptError("persistence-scheduling-state-observation-expired")
    return {"schema": "kanbien/scheduling-database-observation/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence",
        **{key: checked[key] for key in ("binding", "task", "receipt_sha256", "packet")},
        "database_state": checked["result"]["database_state"], "required_after": required_after,
        "checked_at": now}


def scheduling_database_readiness(qualified_path, receipt_paths, *, required_after, source_revision, image_digest):
    """Fresh original state/grant/privilege evidence for initial empty activation.

    The caller supplies its retained phase boundary, not a user-selected time.
    This reader performs observations only; it never launches or retries tasks.
    """
    try:
        if type(receipt_paths) is not dict or set(receipt_paths) != {"state", "grant", "prove"}: raise ValueError()
        qualified = RECEIPTS.qualified_maintenance(qualified_path)
        if (qualified["source_revision"], qualified["image_digest"]) != (source_revision, image_digest): raise ValueError()
        outputs, _ = MIGRATION.outputs(STACK)
        if not isinstance(outputs, dict): raise ValueError()
        definition = outputs.get("CoreServerPersistenceAdministrationTaskDefinitionArn")
        binding = MIGRATION.scheduling_database_binding(qualified, outputs, ((definition, "core_runtime"),))
        seconds, now = deadline(), datetime.now(timezone.utc)
        if seconds is None: raise ValueError()
        observations = {}
        for name, operation in (("state", "observe-scheduling-state"), ("grant", "grant-scheduling-access"), ("prove", "prove-scheduling-access")):
            path = Path(receipt_paths[name]).absolute()
            if any(part.is_symlink() for part in (path, *path.parents)) or not path.resolve().is_relative_to(RECEIPTS.RECEIPTS.resolve()): raise ValueError()
            raw = path.read_bytes()
            if len(raw) > 1048576: raise ValueError()
            original = RECEIPTS.validate(json.loads(raw))
            if original["context"].get("scheduling_binding") != binding or original["task"]["image_digest"] != image_digest: raise ValueError()
            state = MIGRATION.observe_scheduling_administration(original, outputs, operation, now=now, deadline_seconds=seconds)
            task = original["task"]
            observations[name] = {"receipt_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(), "task_arn": task["arn"],
                "started_at": task["started_at"], "stopped_at": task["stopped_at"], "database_state": state}
        policy = RECEIPTS.owner("core_readiness_freshness", "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
        return RECEIPTS.SCHEDULING_STATE.initial_readiness(binding, observations, target="kanbien-core-platform", scope="core-server-persistence",
            required_after=required_after, checked_at=now.isoformat().replace("+00:00", "Z"), timestamp=MIGRATION.timestamp,
            observation_expired=policy.observation_expired)
    except Exception as error:
        if isinstance(error, ValueError) and str(error) == "scheduling-database-readiness-unrelated-work":
            raise RECEIPTS.ReceiptError("persistence-scheduling-readiness-unrelated-work") from None
        raise RECEIPTS.ReceiptError("persistence-scheduling-readiness-not-confirmed") from None


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
    parser.add_argument("--qualified-receipt", type=Path)
    parser.add_argument("--scheduling-proof-id")
    parser.add_argument("--scheduling-proof-due-at")
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
    synthetic = args.operation in RECEIPTS.SCHEDULING_PROOF.PROOF_OPERATIONS
    try:
        if synthetic:
            RECEIPTS.SCHEDULING_PROOF.proof_identifier(args.scheduling_proof_id)
            if args.operation == "seed-scheduling-proof": RECEIPTS.SCHEDULING_PROOF.proof_time(args.scheduling_proof_due_at)
            elif args.scheduling_proof_due_at is not None: raise ValueError()
        elif args.scheduling_proof_id is not None or args.scheduling_proof_due_at is not None: raise ValueError()
    except ValueError: return report("blocked", "persistence-administration-scheduling-proof-selection-invalid")
    scheduling = synthetic or args.operation in RECEIPTS.SCHEDULING_STATE.RESULTS or args.operation == RECEIPTS.SCHEDULING_STATE.PREFIX_OPERATION
    if scheduling != (args.qualified_receipt is not None) or scheduling and args.reconcile_task is not None:
        return report("blocked", "persistence-administration-scheduling-custody-required")
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
    environment = [{"name": "PERSISTENCE_ADMINISTRATION_OPERATION", "value": args.operation}]
    if synthetic:
        environment.append({"name": "PERSISTENCE_SCHEDULING_PROOF_ID", "value": args.scheduling_proof_id})
        if args.operation == "seed-scheduling-proof": environment.append({"name": "PERSISTENCE_SCHEDULING_PROOF_DUE_AT", "value": args.scheduling_proof_due_at})
    overrides = json.dumps({"containerOverrides": [{"name": "persistence-administration", "environment": environment}]})
    def historical():
        retained_path, retained = retained_observation(args.operation, definition)
        if retained_path is not None and retained is not None: return reused_observation(retained_path, retained, args.operation)
        return None
    operations = MIGRATION.task_operations()
    captured = {}
    def scheduling_identity():
        if not captured:
            qualified = RECEIPTS.qualified_maintenance(args.qualified_receipt)
            captured.update(MIGRATION.scheduling_database_binding(qualified, outputs, ((definition, "core_runtime"),)))
        return dict(captured)
    def authorize_submission(_previous, _proof):
        try: scheduling_identity()
        except Exception: raise operations.OperationFailure("scheduling-binding-not-confirmed") from None
    binding = operation_binding(lambda task, seconds, operation, on_receipt=None, scheduling_binding=None:
        accept(task, seconds, operation, on_receipt, (lambda: scheduling_binding) if scheduling_binding is not None else None))
    return binding.run(mode=args.operation, definition=definition, network=network, overrides=overrides, seconds=seconds,
        new_operation=new_operation, expected_operation=args.expected_operation, historical=historical,
        authorize_submission=authorize_submission if scheduling else None,
        submission_binding=scheduling_identity if scheduling else None)


if __name__ == "__main__":
    raise SystemExit(main())


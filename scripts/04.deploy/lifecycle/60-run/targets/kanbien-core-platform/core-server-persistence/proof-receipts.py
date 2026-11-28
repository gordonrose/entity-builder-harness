#!/usr/bin/env python3
"""Small, allowlisted durable receipts for completed persistence proof tasks.

The receipt is deliberately a task-proof artifact, not a general execution
journal.  It is written only after a controller has observed terminal ECS
state, the exact task definition/image and the safe application result.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.persistence-proof-receipts
#   version: 5
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Build and validate bounded, non-secret durable receipts for completed persistence proof tasks.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [writes-files]
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
from typing import Any

TARGET = "kanbien-core-platform"
SCOPE = "core-server-persistence"
ROOT = Path(__file__).resolve().parents[7]
RECEIPTS = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts"
SCHEMA = "deploy/persistence-proof-receipt/v1"
ALLOWED_PROOFS = {"administration", "migration", "verifier", "restore", "server-replacement"}
EVIDENCE_CLASS = "live"
OPERATIONS = {"administration": {"bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"}, "migration": {"apply"}, "verifier": {"create", "read", "health-ready", "health-unready", "cleanup"}, "restore": {"isolated-restore"}, "server-replacement": {"controlled-replacement"}}
_STATE_SPEC = importlib.util.spec_from_file_location("scheduling_database_state", ROOT / "scripts/04.deploy/shared/scheduling-database-state.py")
SCHEDULING_STATE = importlib.util.module_from_spec(_STATE_SPEC)
_STATE_SPEC.loader.exec_module(SCHEDULING_STATE)
_PROOF_SPEC = importlib.util.spec_from_file_location("scheduling_runtime_proof", ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py")
SCHEDULING_PROOF = importlib.util.module_from_spec(_PROOF_SPEC)
_PROOF_SPEC.loader.exec_module(SCHEDULING_PROOF)
OPERATIONS["administration"].update(SCHEDULING_STATE.RESULTS)
OPERATIONS["administration"].add(SCHEDULING_STATE.PREFIX_OPERATION)
OPERATIONS["administration"].update(SCHEDULING_PROOF.PROOF_OPERATIONS)
TASK_ARN_PREFIX = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/"


class ReceiptError(ValueError):
    pass


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def owner(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def qualified_maintenance(path, *, get=None):
    """Authenticate current maintenance custody, not a caller's success flag.

    The existing publisher owns workflow identity and qualification inputs;
    the common artifact reader authenticates its immutable first-run output.
    This read is used only when admitting a new scheduling operation.
    """
    try:
        path = Path(path).absolute()
        if any(item.is_symlink() for item in (path, *path.parents)) or path.stat().st_size > 1048576: raise ValueError()
        receipt = json.loads(path.read_bytes())
        package = "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/"
        validator = owner("core_maintenance_custody", package + "validate.py")
        program = "kanbien-core-server-persistence"
        validator.validate(receipt, SimpleNamespace(expected_target=TARGET, expected_candidate=program + "-candidate",
            expected_package_contract=program + "-image", expected_program=program))
        publisher = owner("core_maintenance_publisher", "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/publication.py").PUBLISHER.binding
        artifact = owner("core_maintenance_artifact", package + "github-artifact.py")
        revision = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        if revision != receipt["source_revision"]: raise ValueError()
        if not owner("core_maintenance_source", package + "qualification.py").runtime_sources_clean(ROOT): raise ValueError()
        run = receipt["receipt_reference"].split(":", 1)[1]
        documents = artifact.documents(repository=publisher.source_repository, workflow=publisher.workflow,
            source_revision=revision, run_id=run, artifact_name="kanbien-core-platform-persistence-package-custody-" + run,
            members=("package-custody-receipt.json", "qualified-image.json"), get=get)
        if documents["package-custody-receipt.json"] != receipt: raise ValueError()
        qualification = documents["qualified-image.json"]
        inputs = qualification.get("inputs")
        if qualification.get("schema") != "deploy/local-image-qualification/v1" or not isinstance(inputs, dict) or not inputs: raise ValueError()
        if not isinstance(qualification.get("image_id"), str) or re.fullmatch(r"sha256:[a-f0-9]{64}", qualification["image_id"]) is None: raise ValueError()
        for relative, checksum in inputs.items():
            if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts or not (ROOT / relative).resolve().is_relative_to(ROOT.resolve()): raise ValueError()
            if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != checksum: raise ValueError()
        configurations = []
        for adapter, source, selector in publisher.configuration:
            projection = owner("core_maintenance_configuration", adapter).package_projection(ROOT / source, selector)
            configurations.append({"adapter": adapter, "source": source, "selector": selector,
                "adapter_sha256": hashlib.sha256((ROOT / adapter).read_bytes()).hexdigest(),
                "projection_sha256": hashlib.sha256(canonical(projection)).hexdigest()})
        if not configurations or qualification.get("configuration_inputs") != configurations: raise ValueError()
        return receipt
    except Exception:
        raise ReceiptError("persistence-scheduling-maintenance-custody-invalid") from None


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReceiptError(f"persistence-proof-receipt-{field}-invalid")
    return value


def _timestamp(value: object, field: str) -> str:
    """Keep a receipt's explicit timestamp fields structurally safe."""
    result = _string(value, field)
    if "T" not in result or not (result.endswith("Z") or "+" in result):
        raise ReceiptError(f"persistence-proof-receipt-{field}-invalid")
    return result


def validate_scheduling_binding(value):
    """Finite original maintenance/database identity; no host or credentials."""
    if (not isinstance(value, dict) or set(value) != {"source_revision", "image_digest", "dependency_incarnation_sha256"}
            or not isinstance(value["source_revision"], str) or re.fullmatch(r"[a-f0-9]{40}", value["source_revision"]) is None
            or any(not isinstance(value[key], str) or re.fullmatch(r"sha256:[a-f0-9]{64}", value[key]) is None
                   for key in ("image_digest", "dependency_incarnation_sha256"))):
        raise ReceiptError("persistence-proof-receipt-scheduling-binding-invalid")
    return value


def _context(proof_type: str, value: object, operation: str, result_code: str) -> dict[str, Any]:
    """Allowlist non-secret facts needed to understand a completed proof."""
    if not isinstance(value, dict):
        raise ReceiptError("persistence-proof-receipt-context-invalid")
    if proof_type in {"administration", "migration"}:
        allowed = {"completion_deadline_seconds", "completion_duration_seconds"}
        timing = set(allowed)
        scheduling_success = proof_type == "administration" and SCHEDULING_STATE.RESULTS.get(operation) == result_code
        prefix_success = proof_type == "administration" and operation == SCHEDULING_STATE.PREFIX_OPERATION and result_code == SCHEDULING_STATE.PREFIX_RESULT
        proof_success = proof_type == "administration" and SCHEDULING_PROOF.PROOF_OPERATIONS.get(operation) == result_code
        if scheduling_success: allowed.add("database_state")
        if prefix_success: allowed.add("migration_prefix")
        if proof_success: allowed.update({"scheduling_seed" if operation == "seed-scheduling-proof" else "scheduling_observation", "scheduling_binding"})
        if "scheduling_binding" in value:
            if not (scheduling_success or prefix_success or proof_success or proof_type == "migration" and value.get("migration_profile") == "scheduling"):
                raise ReceiptError("persistence-proof-receipt-context-invalid")
            validate_scheduling_binding(value["scheduling_binding"])
            allowed.add("scheduling_binding")
        if "prefix_receipt_sha256" in value:
            if (proof_type != "migration" or value.get("migration_profile") != "scheduling" or "scheduling_binding" not in value
                    or not isinstance(value["prefix_receipt_sha256"], str) or re.fullmatch(r"sha256:[a-f0-9]{64}", value["prefix_receipt_sha256"]) is None):
                raise ReceiptError("persistence-proof-receipt-context-invalid")
            allowed.add("prefix_receipt_sha256")
        if "migration_profile" in value:
            if proof_type != "migration" or operation != "apply" or value["migration_profile"] != "scheduling":
                raise ReceiptError("persistence-proof-receipt-context-invalid")
            allowed.add("migration_profile")
        if set(value) != allowed or any(type(value[key]) is not int or value[key] < 0 for key in timing):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
        if scheduling_success:
            try: SCHEDULING_STATE.validate(value["database_state"])
            except ValueError: raise ReceiptError("persistence-proof-receipt-context-invalid") from None
        if prefix_success:
            try: SCHEDULING_STATE.validate_prefix(value["migration_prefix"], minimum_applied_migrations=2, manifest_migration_count=7)
            except ValueError: raise ReceiptError("persistence-proof-receipt-context-invalid") from None
        if proof_success:
            try:
                if operation == "seed-scheduling-proof": SCHEDULING_PROOF.proof_seed(value["scheduling_seed"])
                else: SCHEDULING_PROOF.proof_snapshot(value["scheduling_observation"], scope=SCOPE)
            except ValueError: raise ReceiptError("persistence-proof-receipt-context-invalid") from None
    elif proof_type == "verifier":
        allowed = {"record_id", "completion_deadline_seconds", "completion_duration_seconds"}
        if set(value) != allowed or not isinstance(value["record_id"], str) or not value["record_id"] or any(type(value[key]) is not int or value[key] < 0 for key in ("completion_deadline_seconds", "completion_duration_seconds")):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
    elif proof_type == "restore":
        allowed = {"snapshot", "restored_database", "completion_deadline_seconds", "completion_duration_seconds"}
        if set(value) != allowed or not isinstance(value["snapshot"], str) or not value["snapshot"] or not isinstance(value["restored_database"], str) or not value["restored_database"] or any(type(value[key]) is not int or value[key] < 0 for key in ("completion_deadline_seconds", "completion_duration_seconds")):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
    else:
        allowed = {"original_stopped_reason", "successor_task_arn", "successor_started_at", "runtime_task_definition", "recovery_boundary"}
        if set(value) != allowed or not all(isinstance(value[key], str) and value[key] for key in allowed):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
        if not value["successor_task_arn"].startswith(TASK_ARN_PREFIX):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
        _timestamp(value["successor_started_at"], "context-successor-started-at")
        _timestamp(value["recovery_boundary"], "context-recovery-boundary")
    return value


def validate(receipt: object) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ReceiptError("persistence-proof-receipt-invalid")
    allowed = {"schema", "target", "scope", "proof_type", "operation", "task", "context", "provenance", "integrity"}
    if set(receipt) != allowed or receipt.get("schema") != SCHEMA or receipt.get("target") != TARGET or receipt.get("scope") != SCOPE:
        raise ReceiptError("persistence-proof-receipt-identity-invalid")
    proof_type = receipt.get("proof_type")
    if not isinstance(proof_type, str) or proof_type not in ALLOWED_PROOFS:
        raise ReceiptError("persistence-proof-receipt-proof-type-invalid")
    if not isinstance(receipt.get("operation"), str) or receipt["operation"] not in OPERATIONS[proof_type]:
        raise ReceiptError("persistence-proof-receipt-operation-invalid")
    task = receipt.get("task")
    base_task_fields = {"arn", "definition", "image_digest", "started_at", "stopped_at", "terminal_status", "exit_code", "result_code"}
    if not isinstance(task, dict) or (set(task) != base_task_fields and set(task) != base_task_fields | {"stopped_reason"}):
        raise ReceiptError("persistence-proof-receipt-task-invalid")
    for field in ("arn", "definition", "image_digest", "terminal_status", "result_code"):
        _string(task.get(field), f"task-{field}")
    if re.fullmatch(re.escape(TASK_ARN_PREFIX) + r"[0-9a-f]{32}", task["arn"]) is None:
        raise ReceiptError("persistence-proof-receipt-task-arn-invalid")
    _timestamp(task.get("started_at"), "task-started-at")
    _timestamp(task.get("stopped_at"), "task-stopped-at")
    if task["terminal_status"] != "STOPPED" or type(task.get("exit_code")) is not int:
        raise ReceiptError("persistence-proof-receipt-terminal-invalid")
    if "stopped_reason" in task and not isinstance(task["stopped_reason"], str):
        raise ReceiptError("persistence-proof-receipt-terminal-invalid")
    _context(proof_type, receipt.get("context"), receipt["operation"], task["result_code"])
    if "scheduling_binding" in receipt["context"] and receipt["context"]["scheduling_binding"]["image_digest"] != task["image_digest"]:
        raise ReceiptError("persistence-proof-receipt-scheduling-binding-invalid")
    provenance = receipt.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) not in ({"controller", "collection_method", "collected_at"}, {"controller", "collection_method", "collected_at", "evidence_class"}):
        raise ReceiptError("persistence-proof-receipt-provenance-invalid")
    if not isinstance(provenance.get("evidence_class", "live"), str) or provenance.get("evidence_class", "live") not in {"live", "simulated"}:
        raise ReceiptError("persistence-proof-receipt-evidence-class-invalid")
    for field in ("controller", "collection_method", "collected_at"):
        _string(provenance.get(field), f"provenance-{field}")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or set(integrity) != {"algorithm", "payload_sha256"} or integrity.get("algorithm") != "sha256" or not isinstance(integrity.get("payload_sha256"), str):
        raise ReceiptError("persistence-proof-receipt-integrity-invalid")
    payload = {key: value for key, value in receipt.items() if key != "integrity"}
    if integrity["payload_sha256"] != digest(payload):
        raise ReceiptError("persistence-proof-receipt-integrity-mismatch")
    return receipt


def make(*, proof_type: str, operation: str, task: dict[str, object], image_digest: str, result_code: str, context: dict[str, object], controller: str, collected_at: str) -> dict[str, Any]:
    if not isinstance(proof_type, str) or proof_type not in ALLOWED_PROOFS:
        raise ReceiptError("persistence-proof-receipt-proof-type-invalid")
    containers = task.get("containers")
    container = containers[0] if isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) else None
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target": TARGET,
        "scope": SCOPE,
        "proof_type": proof_type,
        "operation": operation,
        "task": {
            "arn": task.get("taskArn"),
            "definition": task.get("taskDefinitionArn"),
            "image_digest": image_digest,
            "started_at": task.get("startedAt"),
            "stopped_at": task.get("stoppedAt"),
            "terminal_status": task.get("lastStatus"),
            "exit_code": container.get("exitCode") if container else None,
            "result_code": result_code,
        },
        "context": context,
        "provenance": {"controller": controller, "collection_method": "ecs-terminal-task+task-definition+safe-log", "collected_at": collected_at, "evidence_class": EVIDENCE_CLASS},
    }
    if proof_type == "server-replacement":
        if task.get("stoppedReason") != "governed core-server-persistence replacement rehearsal":
            raise ReceiptError("persistence-proof-receipt-terminal-invalid")
        if not isinstance(context, dict) or context.get("original_stopped_reason") != "governed core-server-persistence replacement rehearsal":
            raise ReceiptError("persistence-proof-receipt-context-invalid")
        body["task"]["stopped_reason"] = "governed core-server-persistence replacement rehearsal"
    body["integrity"] = {"algorithm": "sha256", "payload_sha256": digest(body)}
    return validate(body)


def document_bytes(receipt):
    return (json.dumps(validate(receipt), sort_keys=True, indent=2) + "\n").encode()


def persist(receipt: dict[str, Any]) -> Path:
    validated = validate(receipt)
    task_id = validated["task"]["arn"].rsplit("/", 1)[-1]
    destination = RECEIPTS / f"{validated['proof_type']}-{validated['operation']}-{task_id}.json"
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    rendered = document_bytes(validated).decode()
    if destination.exists():
        try:
            existing = validate(json.loads(destination.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ReceiptError) as error:
            raise ReceiptError("persistence-proof-receipt-existing-invalid") from error
        # Re-observing the same completed proof must preserve the first receipt.
        # Collection time is provenance, not a new execution or proof identity.
        def substantive(value):
            task = value["task"]
            if value["proof_type"] != "server-replacement":
                task = {key: item for key, item in task.items() if key != "stopped_reason"}
            return {**{key: item for key, item in value.items() if key not in {"integrity", "provenance"}}, "task": task,
                    "provenance": {**{key: item for key, item in value["provenance"].items() if key != "collected_at"}, "evidence_class": value["provenance"].get("evidence_class", "live")}}
        if substantive(existing) != substantive(validated):
            raise ReceiptError("persistence-proof-receipt-conflict")
        return destination
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECEIPTS, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return destination

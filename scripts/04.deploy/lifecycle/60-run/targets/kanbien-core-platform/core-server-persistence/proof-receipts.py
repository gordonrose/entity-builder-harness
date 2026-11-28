#!/usr/bin/env python3
"""Small, allowlisted durable receipts for completed persistence proof tasks.

The receipt is deliberately a task-proof artifact, not a general execution
journal.  It is written only after a controller has observed terminal ECS
state, the exact task definition/image and the safe application result.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.persistence-proof-receipts
#   version: 4
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-27"
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
#   - id: deploy.test.kanbien-core-platform.persistence-proof-receipts
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts-smoke-test.py
#   effects: [network, writes-files]
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
from typing import Any

TARGET = "kanbien-core-platform"
SCOPE = "core-server-persistence"
ROOT = Path(__file__).resolve().parents[7]
RECEIPTS = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts"
SCHEMA = "deploy/persistence-proof-receipt/v1"
ALLOWED_PROOFS = {"administration", "migration", "verifier", "restore", "server-replacement"}
EVIDENCE_CLASS = "live"
OPERATIONS = {"administration": {"bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"}, "migration": {"apply"}, "verifier": {"create", "read", "health-ready", "health-unready", "cleanup"}, "restore": {"isolated-restore"}, "server-replacement": {"controlled-replacement"}}
TASK_ARN_PREFIX = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/"
MAX_RECEIPT_BYTES = 1048576


class ReceiptError(ValueError):
    pass


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


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


def _checked_task_prefix(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task/[A-Za-z0-9_-]+/", value) is None:
        raise ReceiptError("persistence-proof-receipt-task-prefix-invalid")
    return value


def _context(proof_type: str, value: object, *, task_arn_prefix: str = TASK_ARN_PREFIX) -> dict[str, Any]:
    """Allowlist non-secret facts needed to understand a completed proof."""
    task_arn_prefix = _checked_task_prefix(task_arn_prefix)
    if not isinstance(value, dict):
        raise ReceiptError("persistence-proof-receipt-context-invalid")
    if proof_type in {"administration", "migration"}:
        allowed = {"completion_deadline_seconds", "completion_duration_seconds"}
        if set(value) != allowed or any(type(value[key]) is not int or value[key] < 0 for key in allowed):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
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
        if not value["successor_task_arn"].startswith(task_arn_prefix):
            raise ReceiptError("persistence-proof-receipt-context-invalid")
        _timestamp(value["successor_started_at"], "context-successor-started-at")
        _timestamp(value["recovery_boundary"], "context-recovery-boundary")
    return value


def validate(receipt: object, *, task_arn_prefix: str = TASK_ARN_PREFIX) -> dict[str, Any]:
    task_arn_prefix = _checked_task_prefix(task_arn_prefix)
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
    if re.fullmatch(re.escape(task_arn_prefix) + r"[0-9a-f]{32}", task["arn"]) is None:
        raise ReceiptError("persistence-proof-receipt-task-arn-invalid")
    _timestamp(task.get("started_at"), "task-started-at")
    _timestamp(task.get("stopped_at"), "task-stopped-at")
    if task["terminal_status"] != "STOPPED" or type(task.get("exit_code")) is not int:
        raise ReceiptError("persistence-proof-receipt-terminal-invalid")
    if "stopped_reason" in task and not isinstance(task["stopped_reason"], str):
        raise ReceiptError("persistence-proof-receipt-terminal-invalid")
    _context(proof_type, receipt.get("context"), task_arn_prefix=task_arn_prefix)
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


def make(*, proof_type: str, operation: str, task: dict[str, object], image_digest: str, result_code: str, context: dict[str, object], controller: str, collected_at: str, task_arn_prefix: str = TASK_ARN_PREFIX) -> dict[str, Any]:
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
    return validate(body, task_arn_prefix=task_arn_prefix)


def substantive(value):
    """Collection time is provenance, not a new execution or proof identity."""
    task = value["task"]
    if value["proof_type"] != "server-replacement":
        task = {key: item for key, item in task.items() if key != "stopped_reason"}
    return {**{key: item for key, item in value.items() if key not in {"integrity", "provenance"}}, "task": task,
            "provenance": {**{key: item for key, item in value["provenance"].items() if key != "collected_at"}, "evidence_class": value["provenance"].get("evidence_class", "live")}}


def _label(value):
    return f"{value['proof_type']}-{value['operation']}-{value['task']['arn'].rsplit('/', 1)[-1]}.json"


def _render(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def persist(receipt: dict[str, Any]) -> Path:
    validated = validate(receipt)
    destination = RECEIPTS / _label(validated)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    rendered = _render(validated).decode("utf-8")
    if destination.exists():
        try:
            existing = validate(json.loads(destination.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ReceiptError) as error:
            raise ReceiptError("persistence-proof-receipt-existing-invalid") from error
        # Re-observing the same completed proof must preserve the first receipt.
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


def _bounded(raw):
    if type(raw) is not bytes or not raw or len(raw) > MAX_RECEIPT_BYTES:
        raise ReceiptError("persistence-proof-receipt-storage-invalid")
    return raw


def _decode(raw, *, task_arn_prefix):
    _bounded(raw)
    try: value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError):
        raise ReceiptError("persistence-proof-receipt-storage-invalid") from None
    return validate(value, task_arn_prefix=task_arn_prefix)


def _storage(storage):
    if not all(callable(getattr(storage, name, None)) for name in ("read_receipt", "retain_receipt")):
        raise ReceiptError("persistence-proof-receipt-storage-invalid")
    return storage


def _reference(reference, *, retained):
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ReceiptError("persistence-proof-receipt-reference-invalid")
    path, digest_value = reference["path"], reference["sha256"]
    if not isinstance(path, str) or not path or "\\" in path or Path(path).is_absolute() or Path(path).as_posix() != path or ".." in Path(path).parts or not isinstance(digest_value, str) or re.fullmatch(r"[a-f0-9]{64}", digest_value) is None:
        raise ReceiptError("persistence-proof-receipt-reference-invalid")
    label = Path(path).name
    matched = re.fullmatch(r"([a-z-]+)-([a-f0-9]{32})\.json", label)
    if matched is None or matched[1] not in {kind + "-" + operation for kind, operations in OPERATIONS.items() for operation in operations} or (retained and path != label):
        raise ReceiptError("persistence-proof-receipt-reference-invalid")
    return path


def retain(receipt, *, root, storage=None, task_arn_prefix=TASK_ARN_PREFIX):
    """Return journal reference facts, not task admission or storage authority.

    The retained adapter owns session binding and exact child-version/readback
    proof. It returns the positively retained first bytes, including on reuse.
    """
    validated = validate(receipt, task_arn_prefix=task_arn_prefix)
    proposed = _bounded(_render(validated))
    label = _label(validated)
    if storage is None:
        root = Path(root)
        if not root.is_absolute() or not RECEIPTS.resolve().is_relative_to(root.resolve()):
            raise ReceiptError("persistence-proof-receipt-reference-invalid")
        try:
            path = persist(validated)
            with path.open("rb") as stream: raw = stream.read(MAX_RECEIPT_BYTES + 1)
        except OSError: raise ReceiptError("persistence-proof-receipt-storage-unavailable") from None
        reference_path = path.relative_to(root).as_posix()
    else:
        adapter = _storage(storage)
        try: raw = adapter.retain_receipt(label, proposed)
        except Exception: raise ReceiptError("persistence-proof-receipt-retention-not-confirmed") from None
        reference_path = label
    observed = _decode(raw, task_arn_prefix=task_arn_prefix)
    if _label(observed) != label or substantive(observed) != substantive(validated):
        raise ReceiptError("persistence-proof-receipt-conflict")
    return {"path": reference_path, "sha256": hashlib.sha256(raw).hexdigest()}


def read(reference, *, root, storage=None, task_arn_prefix=TASK_ARN_PREFIX):
    """Read exact referenced bytes and apply the existing receipt validator."""
    task_arn_prefix = _checked_task_prefix(task_arn_prefix)
    label = _reference(reference, retained=storage is not None)
    if storage is None:
        root = Path(root)
        path = root / label
        if not root.is_absolute() or not path.resolve().is_relative_to(root.resolve()) or any(item.is_symlink() for item in (path, *path.parents)):
            raise ReceiptError("persistence-proof-receipt-reference-invalid")
        try:
            with path.open("rb") as stream: raw = stream.read(MAX_RECEIPT_BYTES + 1)
        except OSError: raise ReceiptError("persistence-proof-receipt-storage-unavailable") from None
    else:
        adapter = _storage(storage)
        try: raw = adapter.read_receipt(label)
        except Exception: raise ReceiptError("persistence-proof-receipt-storage-unavailable") from None
    _bounded(raw)
    if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ReceiptError("persistence-proof-receipt-reference-mismatch")
    observed = _decode(raw, task_arn_prefix=task_arn_prefix)
    if _label(observed) != Path(label).name:
        raise ReceiptError("persistence-proof-receipt-reference-mismatch")
    return observed

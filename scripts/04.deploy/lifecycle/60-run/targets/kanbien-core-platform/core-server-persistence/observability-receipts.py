#!/usr/bin/env python3
"""Validate and retain the three bounded observability-MVP proof receipts.

This target-specific module deliberately records only the first readiness path:
failure observed, alarm delivery acknowledged, and recovery observed.  It is
not an alert journal, mail archive, or general execution history.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.observability-receipts
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate and retain bounded non-secret evidence for the first PostgreSQL readiness alert path.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
#   effects: [writes-files]
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

TARGET = "kanbien-core-platform"
SCOPE = "core-server-persistence"
ROOT = Path(__file__).resolve().parents[7]
EVIDENCE_ROOT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
RECEIPTS = EVIDENCE_ROOT / "observability-receipts"
SCHEMA = "deploy/persistence-observability-receipt/v1"
TYPES = {"readiness-failure-observed", "readiness-alarm-notified", "readiness-recovery-observed"}
ALARM = "kanbien-core-platform-core-server-postgresql-readiness-not-ready-or-silent"
METRIC = "kanbien.core_server.postgresql_readiness"
DIMENSIONS = {
    "target": TARGET,
    "scope": SCOPE,
    "workload": "core-server",
    "dependency": "postgresql",
}
TASK_ARN = re.compile(r"^arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[0-9a-f]{32}$")
TASK_DEFINITION = re.compile(r"^arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:[1-9][0-9]*$")
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReceiptError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReceiptError(code)
    return value


def timestamp(value: object, code: str) -> str:
    result = string(value, code)
    if "T" not in result or not (result.endswith("Z") or "+" in result):
        raise ReceiptError(code)
    return result


def source(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "task_arn", "task_definition", "image_digest", "result_code"}:
        raise ReceiptError("observability-receipt-source-invalid")
    path = string(value.get("path"), "observability-receipt-source-invalid")
    if Path(path).is_absolute() or not path.startswith("infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/"):
        raise ReceiptError("observability-receipt-source-invalid")
    if SHA.fullmatch(string(value.get("sha256"), "observability-receipt-source-invalid")) is None or TASK_ARN.fullmatch(string(value.get("task_arn"), "observability-receipt-source-invalid")) is None or TASK_DEFINITION.fullmatch(string(value.get("task_definition"), "observability-receipt-source-invalid")) is None or SHA.fullmatch(string(value.get("image_digest"), "observability-receipt-source-invalid")) is None:
        raise ReceiptError("observability-receipt-source-invalid")
    if value.get("result_code") not in {"KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", "KANBIEN_CORE_PERSISTENCE_HEALTHY"}:
        raise ReceiptError("observability-receipt-source-invalid")
    return value


def observation(receipt_type: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReceiptError("observability-receipt-observation-invalid")
    if receipt_type == "readiness-alarm-notified":
        required = {"alarm_name", "alarm_state", "alarm_state_updated_at", "subscription_confirmed_at", "operator_delivery_confirmed_at"}
        if set(value) != required or value.get("alarm_name") != ALARM or value.get("alarm_state") != "ALARM":
            raise ReceiptError("observability-receipt-notification-invalid")
        for field in required - {"alarm_name", "alarm_state"}:
            timestamp(value.get(field), "observability-receipt-notification-invalid")
        return value
    required = {"alarm_name", "alarm_state", "alarm_state_updated_at", "metric_name", "dimensions", "metric_value", "metric_observed_at"}
    state = "ALARM" if receipt_type == "readiness-failure-observed" else "OK"
    expected_value = 0 if receipt_type == "readiness-failure-observed" else 1
    if set(value) != required or value.get("alarm_name") != ALARM or value.get("alarm_state") != state or value.get("metric_name") != METRIC or value.get("dimensions") != DIMENSIONS or type(value.get("metric_value")) is not int or value.get("metric_value") != expected_value:
        raise ReceiptError("observability-receipt-observation-invalid")
    timestamp(value.get("alarm_state_updated_at"), "observability-receipt-observation-invalid")
    timestamp(value.get("metric_observed_at"), "observability-receipt-observation-invalid")
    return value


def validate(receipt: object) -> dict[str, Any]:
    if not isinstance(receipt, dict) or set(receipt) != {"schema", "target", "scope", "receipt_type", "source_proof", "observation", "provenance", "integrity"}:
        raise ReceiptError("observability-receipt-invalid")
    if receipt.get("schema") != SCHEMA or receipt.get("target") != TARGET or receipt.get("scope") != SCOPE or receipt.get("receipt_type") not in TYPES:
        raise ReceiptError("observability-receipt-identity-invalid")
    source(receipt.get("source_proof"))
    observation(receipt["receipt_type"], receipt.get("observation"))
    provenance = receipt.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"controller", "collection_method", "collected_at", "evidence_class"} or provenance.get("controller") != "rehearse-observability-readiness" or provenance.get("collection_method") != "cloudwatch-alarm+metric+confirmed-subscription" or provenance.get("evidence_class") not in {"live", "simulated"}:
        raise ReceiptError("observability-receipt-provenance-invalid")
    timestamp(provenance.get("collected_at"), "observability-receipt-provenance-invalid")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or set(integrity) != {"algorithm", "payload_sha256"} or integrity.get("algorithm") != "sha256" or SHA.fullmatch(str(integrity.get("payload_sha256"))) is None:
        raise ReceiptError("observability-receipt-integrity-invalid")
    if integrity["payload_sha256"] != digest({key: value for key, value in receipt.items() if key != "integrity"}):
        raise ReceiptError("observability-receipt-integrity-mismatch")
    return receipt


def make(*, receipt_type: str, source_proof: dict[str, str], observation_value: dict[str, Any], collected_at: str, evidence_class: str = "live") -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target": TARGET,
        "scope": SCOPE,
        "receipt_type": receipt_type,
        "source_proof": source_proof,
        "observation": observation_value,
        "provenance": {
            "controller": "rehearse-observability-readiness",
            "collection_method": "cloudwatch-alarm+metric+confirmed-subscription",
            "collected_at": collected_at,
            "evidence_class": evidence_class,
        },
    }
    body["integrity"] = {"algorithm": "sha256", "payload_sha256": digest(body)}
    return validate(body)


def persist(receipt: dict[str, Any]) -> Path:
    value = validate(receipt)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    suffix = value["integrity"]["payload_sha256"][7:19]
    destination = RECEIPTS / f"{value['receipt_type']}-{suffix}.json"
    rendered = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if destination.exists():
        try:
            existing = validate(json.loads(destination.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ReceiptError) as error:
            raise ReceiptError("observability-receipt-existing-invalid") from error
        if existing != value:
            raise ReceiptError("observability-receipt-conflict")
        return destination
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECEIPTS, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return destination

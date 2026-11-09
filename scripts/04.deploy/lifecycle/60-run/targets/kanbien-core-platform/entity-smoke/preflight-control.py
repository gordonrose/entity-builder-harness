#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.preflight-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Admit only bounded observation-task requests and require an actual fresh immutable matching preflight receipt before later operation admission.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Provider-owned applicability predicate, never an authority or gate producer.

The public route still owes the first five normal gates and concrete approval
before supplying a RunTask capability. This module cannot mark any gate passed.
"""
from datetime import timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

SPEC = importlib.util.spec_from_file_location("entity_smoke_preflight_evidence", Path(__file__).with_name("task-evidence.py"))
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)
CONTROL = EVIDENCE.CONTROL
STORAGE_SPEC = importlib.util.spec_from_file_location("entity_smoke_preflight_storage", Path(__file__).with_name("resource-control.py"))
STORAGE = importlib.util.module_from_spec(STORAGE_SPEC)
STORAGE_SPEC.loader.exec_module(STORAGE)


class PreflightFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise PreflightFailure(code)


def validate_launch(request):
    CONTROL.validate_request(request)
    workload = request["workload"]
    operation = request["environment"][CONTROL.OPERATIONS[workload][0]]
    require(request["deadline_seconds"] <= 90, "preflight-deadline-exceeds-bound")
    require(operation == ("ready" if workload == "verifier" else "preflight"), "preflight-operation-not-read-only")
    # Even benign-looking arbitrary overrides are outside this narrow exception.
    expected = {CONTROL.OPERATIONS[workload][0]}
    if workload in {"verifier", "database-proof", "restore-reader"}: expected.add("ENTITY_SMOKE_PROOF_LABEL")
    if workload == "verifier": expected.add("ENTITY_SMOKE_EXPECTED_SOURCE")
    require(set(request["environment"]) == expected, "preflight-overrides-not-closed")
    return request


def require_receipt(request, reservation, receipt, *, expected_preflight_label, current_time, required_after):
    """Admission of a later operation, not a fresh remote observation.

    A preflight can have its own explicitly selected attempt label. It cannot
    stand in for the business record label, and an unknown launch cannot be
    replayed merely by supplying another label. The owning plan binds both.
    """
    CONTROL.validate_request(request)
    require(isinstance(reservation, dict) and isinstance(reservation.get("request"), dict), "preflight-reservation-invalid")
    probe = validate_launch(reservation["request"])
    retained = EVIDENCE.validate_retained(receipt, reservation)
    require(probe["proof_label"] == expected_preflight_label, "preflight-label-not-selected")
    immutable = set(request) - {"environment", "deadline_seconds", "proof_label"}
    require(all(probe[key] == request[key] for key in immutable), "preflight-operation-binding-mismatch")
    observed, current, prerequisite = (EVIDENCE.timestamp(value) for value in (retained["task"]["stopped_at"], current_time, required_after))
    created = EVIDENCE.timestamp(retained["task"]["created_at"])
    collected = EVIDENCE.timestamp(retained["collected_at"])
    require(prerequisite <= created and prerequisite <= current, "preflight-predates-required-state")
    require(-timedelta(seconds=60) <= current - observed <= timedelta(seconds=900)
            and collected <= current + timedelta(seconds=60), "preflight-observation-not-fresh")
    return retained


def admission_path(root, reservation):
    # validate_retained/AttemptStore has already checked the reservation, but
    # do not let an unchecked operation ID select a path even at this seam.
    require(isinstance(reservation, dict) and isinstance(reservation.get("operation_id"), str)
            and re.fullmatch(r"es-[a-f0-9]{32}", reservation["operation_id"]) is not None, "preflight-reservation-invalid")
    path = Path(root) / "admissions" / (reservation["operation_id"] + ".json")
    CONTROL.no_symlinks(path)
    return path


def validate_admission(value, reservation):
    require(isinstance(value, dict) and set(value) == {"schema", "reservation_sha256", "preflight", "required_after", "admitted_at"}
            and value["schema"] == "deploy/entity-smoke-task-admission/v1"
            and value["reservation_sha256"] == hashlib.sha256(CONTROL.canonical(reservation)).hexdigest(), "preflight-admission-binding-mismatch")
    packet = value["preflight"]
    require(isinstance(packet, dict) and set(packet) == {"reservation", "receipt", "label"}, "preflight-admission-invalid")
    admitted, reserved = EVIDENCE.timestamp(value["admitted_at"]), EVIDENCE.timestamp(reservation["reserved_at"])
    require(abs(admitted - reserved) <= timedelta(seconds=60), "preflight-admission-time-not-bound")
    checked = require_receipt(reservation["request"], packet["reservation"], packet["receipt"], expected_preflight_label=packet["label"], current_time=value["admitted_at"], required_after=value["required_after"])
    return max(value["required_after"], checked["task"]["stopped_at"], key=EVIDENCE.timestamp)


def read_admission(root, reservation):
    path = admission_path(root, reservation)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream: raw = stream.read(1048577)
        require(len(raw) <= 1048576, "preflight-admission-invalid")
        value = json.loads(raw)
    except FileNotFoundError: raise PreflightFailure("preflight-admission-not-retained") from None
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError): raise PreflightFailure("preflight-admission-unavailable") from None
    return validate_admission(value, reservation)


def retain_admission(root, reservation, packet, required_after, admitted_at):
    value = {"schema": "deploy/entity-smoke-task-admission/v1", "reservation_sha256": hashlib.sha256(CONTROL.canonical(reservation)).hexdigest(),
             "preflight": packet, "required_after": required_after, "admitted_at": admitted_at}
    effective_after = validate_admission(value, reservation)
    path = admission_path(root, reservation)
    try: written = STORAGE.write_exclusive(path, value)
    except STORAGE.ResourceFailure as failure: raise PreflightFailure(failure.code) from None
    # A new callback must not replace or reinterpret a previous admission.
    require(written, "preflight-admission-already-retained")
    return effective_after

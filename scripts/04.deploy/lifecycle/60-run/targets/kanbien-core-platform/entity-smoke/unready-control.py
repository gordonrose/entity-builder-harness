#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.unready-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind a bounded expected-unready observation to actual retained revocation evidence without admitting business work or granting provider capability.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Negative recovery admission, never healthy access or a gate producer."""
from datetime import timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("entity_smoke_unready_preflight", Path(__file__).with_name("preflight-control.py"))
P = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(P)
C, E = P.CONTROL, P.EVIDENCE


class UnreadyFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise UnreadyFailure(code)


def validate_launch(request, revocation):
    try:
        C.validate_request(request)
        require(request["workload"] == "verifier" and request["environment"].get("ENTITY_SMOKE_VERIFICATION_OPERATION") == "unready", "unready-operation-not-selected")
        require(request["deadline_seconds"] <= 90, "unready-deadline-exceeds-bound")
        require(set(request["environment"]) == {"ENTITY_SMOKE_VERIFICATION_OPERATION", "ENTITY_SMOKE_PROOF_LABEL", "ENTITY_SMOKE_EXPECTED_SOURCE"}, "unready-overrides-not-closed")
        require(isinstance(revocation, dict) and set(revocation) == {"reservation", "receipt", "label"}
                and isinstance(revocation["reservation"], dict) and isinstance(revocation["reservation"].get("request"), dict), "unready-revocation-required")
        revoked = C.validate_request(revocation["reservation"]["request"])
        require(revoked["workload"] == "administration" and revoked["environment"] == {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "revoke-runtime"}, "unready-revocation-operation-mismatch")
        require(revocation["label"] == request["proof_label"] == revoked["proof_label"], "unready-revocation-label-mismatch")
        fields = ("source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")
        require(all(request[key] == revoked[key] for key in fields), "unready-revocation-binding-mismatch")
        receipt = E.validate_retained(revocation["receipt"], revocation["reservation"])
        return receipt["task"]["stopped_at"]
    except (C.TaskFailure, E.EvidenceFailure) as failure: raise UnreadyFailure(failure.code) from None


def path_for(root, reservation):
    try: return P.admission_path(Path(root) / "unready", reservation)
    except (P.PreflightFailure, C.TaskFailure) as failure: raise UnreadyFailure(failure.code) from None


def validate_admission(value, reservation):
    require(isinstance(value, dict) and set(value) == {"schema", "reservation_sha256", "revocation", "admitted_at"}
            and value["schema"] == "deploy/entity-smoke-unready-admission/v1"
            and value["reservation_sha256"] == hashlib.sha256(C.canonical(reservation)).hexdigest(), "unready-admission-binding-mismatch")
    after = validate_launch(reservation["request"], value["revocation"])
    try:
        admitted, reserved, revoked = (E.timestamp(item) for item in (value["admitted_at"], reservation["reserved_at"], after))
        require(abs(admitted - reserved) <= timedelta(seconds=60), "unready-admission-time-not-bound")
        require(revoked <= admitted, "unready-admission-predates-revocation")
        # This is the time of original admission, not a restamped resumed check.
        require(admitted - revoked <= timedelta(seconds=900), "unready-revocation-not-fresh")
        return after
    except E.EvidenceFailure as failure: raise UnreadyFailure(failure.code) from None


def retain_admission(root, reservation, revocation, admitted_at):
    value = {"schema": "deploy/entity-smoke-unready-admission/v1", "reservation_sha256": hashlib.sha256(C.canonical(reservation)).hexdigest(),
             "revocation": revocation, "admitted_at": admitted_at}
    after = validate_admission(value, reservation)
    try: written = P.STORAGE.write_exclusive(path_for(root, reservation), value)
    except P.STORAGE.ResourceFailure as failure: raise UnreadyFailure(failure.code) from None
    require(written, "unready-admission-already-retained")
    return after


def read_admission(root, reservation, revocation=None):
    path = path_for(root, reservation)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream: raw = stream.read(1048577)
        require(len(raw) <= 1048576, "unready-admission-invalid")
        value = json.loads(raw)
    except FileNotFoundError: raise UnreadyFailure("unready-admission-not-retained") from None
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError): raise UnreadyFailure("unready-admission-unavailable") from None
    after = validate_admission(value, reservation)
    require(revocation is None or value["revocation"] == revocation, "unready-admission-revocation-changed")
    return after

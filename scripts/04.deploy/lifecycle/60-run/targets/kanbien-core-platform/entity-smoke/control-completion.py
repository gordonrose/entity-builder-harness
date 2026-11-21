#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.control-completion
#   version: 1
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-21"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Close actual completed control receipts and validate historical custody separately from the current successor without requiring expired ECS predecessor records.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/script.py
import hashlib
import json
import re
from types import SimpleNamespace

NAMES = {"server-replacement": "replacement", "credential-replacement": "credential-replacement", "initial-stop": "failure", "initial-restart": "initial-restart"}
# Exact already-completed receipt predating companion retention. Never fabricate
# a companion or attribute this old observation to the repaired controller.
LEGACY = {("server-replacement", "sha256:fefc8e5561299b9e5cb63e41f820fae3a250f1bf3452bbf01f24eb72580b83e6"):
          "sha256:8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"}
# Completed under a preceding checked controller. NAMES retain their producer
# companions; snapshot/restore readers retain their own original seven gates.
REPAIRS = {
    ("restore-cleanup", "sha256:3c82ef1c8e22aa04bfc4c9824224fc2113c166cbc387a17640f158217d72e443"):
        "sha256:2f07f14b598ee22cfd9b1ab8980ef990f06ed43d1301bda848bf75934daa9f4c",
    ("snapshot", "sha256:fe3c3e880906ce0a3aacb44105a27af2297a1e2ff1b08d84d69b8d67365d57b9"):
        "sha256:26de3e49221e6c9f653d7743218f7022c58d00ace899a71635758e07ff05d23e",
    ("restore-deployment", "sha256:dd92ab0e3ecb16d9ea5db41070ccc96ff12e75fddb6fc36e8dedd1951a3a2be1"):
        "sha256:26de3e49221e6c9f653d7743218f7022c58d00ace899a71635758e07ff05d23e",
    ("credential-replacement", "sha256:f414b14961fd75cdac1194d83cff8f7f5572f33e16f3940f72d124b5cf0dda61"):
        "sha256:73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76",
    ("initial-stop", "sha256:00b9f317659a999ff0d3eaa27dc109319d1ba34ba30a0a8f3613e4612b4f2e7f"):
        "sha256:8528955470b87a617667f2c1a502e356b7e831e5a65101358a83b323493d3b2e",
    ("initial-restart", "sha256:f3e0823c12b19c1ab9ebcc19f4021c5fc9adceaaba6d2f58f6a037a4cc172726"):
        "sha256:8528955470b87a617667f2c1a502e356b7e831e5a65101358a83b323493d3b2e",
}


def document(value):
    return "sha256:" + hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()


def controller(name, receipt_digest, current):
    return (LEGACY | REPAIRS).get((name, receipt_digest), current)


def checked_controller(C, name, receipt_digest, plan, current, *, allow_history=False):
    historical = controller(name, receipt_digest, current)
    if not allow_history or historical != current or plan.get("controller_sha256") == current: return historical
    return C.retained_controller({"plan": plan, "binding": plan["binding"]}, current)


def companion(path):
    return path.with_name(path.stem + ".completion.json")


def checked(C, path, name, graph, current):
    C.require(name in NAMES, "control-completion-selection-invalid")
    value = C.read_json(path)
    C.require(isinstance(value, dict), "control-completion-receipt-invalid")
    digest = document(value)
    C.require(C.digest_file(path) == digest, "control-completion-receipt-not-canonical")
    packet = value.get("root", {}).get("request", {}).get("packet") if name == "initial-stop" else value.get("packet")
    C.require(isinstance(packet, dict) and isinstance(packet.get("plan"), dict), "control-completion-plan-required")
    plan = packet["plan"]
    C.require(packet.get("plan_sha256") == C.DEPLOY.fingerprint(plan)
              and plan.get("controller_sha256") == checked_controller(C, name, digest, plan, current, allow_history="releases" in path.parts)
              and plan.get("graph_sha256") == C.DEPLOY.fingerprint(graph), "control-completion-source-or-plan-mismatch")
    cache = path.parent.parent if name == "initial-stop" else path.parent
    prefix = str((cache / (NAMES[name] + "-realization")).relative_to(C.ROOT)) + "/controlled-execution-"
    reference = value.get("realization_evidence")
    C.require(isinstance(reference, str) and reference.startswith(prefix)
              and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):]), "control-completion-gate-reference-invalid")
    gate_path = C.ROOT / reference
    C.require(C.digest_file(gate_path) == value.get("realization_evidence_sha256"), "control-completion-gate-changed")
    gate = C.read_json(gate_path)
    C.GATE.validate_contract(graph)
    completion = C.module("entity_smoke_closed_control_gate", C.DIRECTORY / "task-completion.py")
    completion.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), graph, gate,
                             packet["plan_sha256"], {graph["artifacts"][0]["id"]: plan["controller_sha256"]})
    closed = {"schema": "deploy/entity-smoke-control-completion/v1", "name": name, "receipt_sha256": digest,
              "plan_sha256": packet["plan_sha256"], "realization_evidence_sha256": value["realization_evidence_sha256"]}
    return value, closed


def retain(C, path, name, graph, current):
    value, closed = checked(C, path, name, graph, current)
    target = companion(path)
    if not C.RESOURCE.write_exclusive(target, closed):
        C.require(C.read_json(target) == closed, "control-completion-conflict")
    return value


def read(C, path, name, graph, current):
    value, closed = checked(C, path, name, graph, current)
    if (name, closed["receipt_sha256"]) not in LEGACY:
        target = companion(path)
        C.RESOURCE.CONTROL.no_symlinks(target)
        C.require(target.is_file(), "control-completion-required")
        C.require(C.read_json(target) == closed, "control-completion-changed")
    return value


def successor(C, provider, receipt):
    """Use only after read() validates the original completed receipt/gates."""
    request, result = receipt["packet"]["request"], receipt["result"]
    reservation, facts = result["reservation"], result["facts"]
    C.require(result.get("status") == "completed" and reservation.get("request") == request
              and isinstance(facts, dict) and set(facts) == {"original_task", "successor_task", "predecessor_stopped_at", "successor_started_at"}
              and facts["original_task"] == request["original_task"] and facts["successor_task"] != facts["original_task"], "control-completion-replacement-facts-invalid")
    timestamp = C.RESOURCE.timestamp
    C.require(timestamp(facts["predecessor_stopped_at"]) >= timestamp(reservation["reserved_at"]), "control-completion-predecessor-time-invalid")
    actual = C.RESOURCE.task(provider, facts["successor_task"], request["definition"], request["binding"]["image_digest"])
    service = C.RESOURCE.service(provider, request["definition"], 1)
    C.require(actual.get("lastStatus") == "RUNNING" and actual.get("healthStatus") == "HEALTHY"
              and service.get("runningCount") == 1 and service.get("pendingCount") == 0
              and C.RESOURCE.running_service_tasks(provider) == [facts["successor_task"]]
              and timestamp(actual.get("startedAt")) == timestamp(facts["successor_started_at"])
              and timestamp(actual.get("startedAt")) >= timestamp(actual.get("createdAt")) >= timestamp(reservation["reserved_at"]),
              "control-completion-current-successor-not-confirmed")
    return result

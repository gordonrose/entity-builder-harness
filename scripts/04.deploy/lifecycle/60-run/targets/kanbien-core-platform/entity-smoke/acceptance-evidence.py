#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.acceptance-evidence
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Preserve checked task, admission and historical gate evidence for the isolated feature without turning captured proof into current health or release promotion.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from datetime import timedelta
import hashlib
import importlib.util
from pathlib import Path
import re


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


T = module("entity_smoke_acceptance_evidence_task", Path(__file__).with_name("task-route.py"))
C = T.C
SCHEMA = "deploy/entity-smoke-retained-task-proof/v1"
# Explicit selections, not all operations that might later be added to a runner.
TASKS = {
    "bootstrap": ("baseline", "administration", ("bootstrap",)),
    "migration": ("baseline", "migration", ("apply",)),
    "grant-runtime": ("baseline", "administration", ("grant-runtime",)),
    "baseline-permissions": ("baseline", "database-proof", ("permissions",)),
    "original-record": ("baseline", "verifier", ("create", "observe-create")),
    "lifecycle": ("baseline", "verifier", ("lifecycle",)),
    "collision": ("baseline", "database-proof", ("collision",)),
    "baseline-read": ("baseline", "verifier", ("read",)),
    "replacement-read": ("server-replacement", "verifier", ("read",)),
    "initial-read": ("initial-recovery", "verifier", ("read",)),
    "migration-state": ("initial-recovery", "administration", ("observe-migration-state",)),
    "permission-state": ("credential-recovery", "administration", ("observe-permissions",)),
    "credential-revoke": ("credential-recovery", "administration", ("revoke-runtime",)),
    "credential-unready": ("credential-recovery", "verifier", ("unready",)),
    "credential-restore": ("credential-recovery", "administration", ("restore-runtime",)),
    "credential-read": ("credential-recovery", "verifier", ("read",)),
    "credential-permissions": ("credential-recovery", "database-proof", ("permissions",)),
    "restore-read": ("isolated-restore", "restore-reader", ("restore-read",)),
    "final-read": ("acceptance", "verifier", ("read",)),
}


class EvidenceFailure(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value: raise EvidenceFailure(code, item)


def digest(value):
    return "sha256:" + hashlib.sha256(T.RUNNER.CONTROL.canonical(value)).hexdigest()


def document_digest(value):
    return "sha256:" + hashlib.sha256(T.RUNNER.CONTROL.canonical(value) + b"\n").hexdigest()


def preflight_label(binding, stage, workload, operation):
    suffix = "" if stage == "baseline" else ":" + stage
    return "entity-smoke-" + hashlib.sha256((binding["proof_label"] + ":" + workload + ":" + operation + ":preflight" + suffix).encode()).hexdigest()[:24]


def validate_gate(graph, gate, plan_sha256, artifacts, counts, *, item, family="task"):
    """Reuse the original completion owner; additionally close archived fields."""
    C.GATE.validate_contract(graph)
    require(isinstance(gate, dict) and isinstance(gate.get("facts"), dict)
            and set(gate["facts"]) == {"schema", "contract_id", "gate_evidence", "component_evidence", "artifact_bindings"},
            "acceptance-" + family + "-gate-fields-invalid", item)
    for key, fields in (("gate_evidence", {"gate", "check_id", "timestamp", "verdict", "input_sha256"}),
                        ("component_evidence", {"component_id", "component_kind", "check_id", "timestamp", "verdict", "input_sha256"}),
                        ("artifact_bindings", {"component_id", "immutable_reference", "check_id", "timestamp", "verdict"})):
        rows = gate["facts"].get(key)
        require(isinstance(rows, list) and all(isinstance(row, dict) and set(row) == fields for row in rows),
                "acceptance-" + family + "-gate-fields-invalid", item)
    T.COMPLETION.validate_gate(T.dependencies(), graph, gate, plan_sha256, artifacts)
    summary = gate["change_summary"]
    require(isinstance(summary, dict) and set(summary) == {"schema", "contract_id", "check_id", "timestamp", "input_sha256", "operation_counts"}
            and summary["schema"] == C.GATE.CHANGE_SCHEMA and summary["contract_id"] == graph["id"]
            and summary["check_id"] in graph["gates"][4]["evidence"]
            and summary["input_sha256"] == C.GATE.evidence_bindings(graph, gate["facts"])["gates"]["change-set"]
            and isinstance(summary["operation_counts"], dict) and set(summary["operation_counts"]) == set(counts)
            and all(type(value) is int for value in summary["operation_counts"].values())
            and summary["operation_counts"] == counts, "acceptance-" + family + "-change-summary-invalid", item)
    C.GATE.safe_timestamp(summary["timestamp"], "acceptance-" + family + "-change-summary-time-invalid")
    return gate


def validate_task(value, collection_binding, *, expected_binding=None):
    """Pure historical validation; no provider access or today's source hash."""
    fields = {"schema", "name", "stage", "phase", "requested_operation", "controller_sha256", "collection_binding", "graph", "packet", "completion", "gate", "admission"}
    require(isinstance(value, dict) and set(value) == fields and value["schema"] == SCHEMA, "acceptance-task-envelope-invalid")
    name = value["name"]
    require(isinstance(name, str) and name in TASKS, "acceptance-task-selection-invalid")
    stage, workload, allowed_operations = TASKS[name]
    operation, phase = value["requested_operation"], value["phase"]
    require(value["stage"] == stage and isinstance(operation, str) and operation in allowed_operations and isinstance(phase, str) and phase in {"preflight", "operation"}
            and not (name == "credential-unready" and phase != "operation"), "acceptance-task-selection-invalid", name)
    C.RESOURCE.validate_binding(collection_binding)
    require(value["collection_binding"] == collection_binding and isinstance(value["controller_sha256"], str)
            and re.fullmatch(r"sha256:[a-f0-9]{64}", value["controller_sha256"]), "acceptance-task-source-invalid", name)
    packet = value["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan_sha256", "binding", "reservation", "receipt"}
            and packet["schema"] == "deploy/entity-smoke-task-step/v1", "acceptance-task-packet-invalid", name)
    parent = {key: item for key, item in collection_binding.items() if key != "record_digest"}
    expected_binding = parent if expected_binding is None else expected_binding
    C.RESOURCE.validate_binding(expected_binding, record_required=False)
    require(packet["binding"] == expected_binding, "acceptance-task-binding-mismatch", name)
    # The clone reader alone has a distinct incarnation and permission contract.
    require(all(expected_binding[key] == parent[key] for key in parent if name != "restore-read" or key not in {"permission_contract_sha256", "dependency_incarnation_sha256"})
            and (name == "restore-read" or expected_binding == parent), "acceptance-task-parent-mismatch", name)
    reservation, receipt = packet["reservation"], packet["receipt"]
    checked = T.RUNNER.EVIDENCE.validate_retained(receipt, reservation)
    require(checked == receipt, "acceptance-task-receipt-mismatch", name)
    request = reservation["request"]
    require(request["workload"] == workload and all(request[key] == expected_binding[key] for key in parent if key != "proof_label"), "acceptance-task-request-binding-mismatch", name)
    actual_operation = ("ready" if workload == "verifier" else "preflight") if phase == "preflight" else operation
    label = preflight_label(parent, stage, workload, operation) if phase == "preflight" else parent["proof_label"]
    require(request["environment"][T.RUNNER.CONTROL.OPERATIONS[workload][0]] == actual_operation
            and request["proof_label"] == label, "acceptance-task-request-selection-mismatch", name)
    if workload in {"verifier", "database-proof", "restore-reader"}:
        require(request["environment"].get("ENTITY_SMOKE_PROOF_LABEL") == label, "acceptance-task-label-mismatch", name)
    original = name in {"original-record", "collision", "baseline-read", "replacement-read", "initial-read", "credential-read", "restore-read", "final-read"}
    if phase == "operation" and original:
        require(receipt["result"].get("record_digest") == collection_binding["record_digest"], "acceptance-original-record-mismatch", name)
    if phase == "operation" and name == "migration-state":
        require(receipt["result"].get("code") == "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED", "acceptance-migration-state-not-applied", name)
    graph, gate, completion = value["graph"], value["gate"], value["completion"]
    C.GATE.validate_contract(graph)
    require(graph.get("id") == T.GRAPH.contract(workload, C.GATE, negative=name == "credential-unready")["id"], "acceptance-task-graph-selection-mismatch", name)
    require(isinstance(completion, dict) and set(completion) == {"schema", "step_sha256", "plan_sha256", "realization_evidence", "realization_evidence_sha256"}
            and completion["schema"] == "deploy/entity-smoke-task-completion/v1" and completion["plan_sha256"] == packet["plan_sha256"]
            and completion["step_sha256"] == document_digest(packet) and completion["realization_evidence_sha256"] == document_digest(gate), "acceptance-task-completion-mismatch", name)
    require(isinstance(completion["realization_evidence"], str) and re.fullmatch(
        r"\.cache/entity-smoke-live/" + re.escape(parent["proof_label"]) + r"/task-realization/controlled-execution-[a-f0-9]{32}\.json",
        completion["realization_evidence"]), "acceptance-task-gate-reference-invalid", name)
    expected = {row["id"]: value["controller_sha256"] if row["id"] == T.GRAPH.CONTROLLER_SOURCE else parent["image_digest"] for row in graph["artifacts"]}
    validate_gate(graph, gate, packet["plan_sha256"], expected,
                  {"create": 1, "update": 0, "delete": 0, "replace": 0, "broaden-permission": 0}, item=name)
    admission = value["admission"]
    if phase == "preflight": require(admission is None, "acceptance-preflight-admission-unexpected", name)
    elif name == "credential-unready": T.RUNNER.UNREADY.validate_admission(admission, reservation)
    else:
        T.RUNNER.PREFLIGHT.validate_admission(admission, reservation)
        require(admission["preflight"]["label"] == preflight_label(parent, stage, workload, operation), "acceptance-preflight-stage-mismatch", name)
    return value


def fresh_final(value, cleanup_at, current_time):
    require(value.get("name") == "final-read" and value.get("phase") == "operation", "acceptance-final-read-required")
    receipt = value["packet"]["receipt"]
    timestamp = T.RUNNER.EVIDENCE.timestamp
    created, stopped, collected, current = (timestamp(receipt["task"]["created_at"]), timestamp(receipt["task"]["stopped_at"]), timestamp(receipt["collected_at"]), timestamp(current_time))
    require(created >= timestamp(cleanup_at) and stopped >= created and collected >= stopped, "acceptance-final-read-predates-cleanup")
    require(-timedelta(seconds=60) <= current - collected <= timedelta(seconds=900), "acceptance-final-read-not-fresh")
    return receipt


def capture_task(route, context, args, provider, name, collection_binding, *, historical=True):
    require(name in TASKS and (args.proof_stage, args.workload) == TASKS[name][:2]
            and args.operation in TASKS[name][2], "acceptance-task-selection-invalid", name)
    packet = route.STEPS.observe_packet(route.dependencies(), context, args, provider, historical=historical)
    require(packet is not None, "acceptance-task-completion-required", name)
    step = route.STEPS.path(context, args)
    completion = route.C.read_json(route.COMPLETION.path(step))
    gate = route.C.read_json(route.C.ROOT / completion["realization_evidence"])
    admission = None
    if args.phase == "operation":
        selected = route.RUNNER.UNREADY.path_for(context["cache"] / "task-receipts", packet["reservation"]) if name == "credential-unready" else route.RUNNER.PREFLIGHT.admission_path(context["cache"] / "task-receipts", packet["reservation"])
        admission = route.C.read_json(selected)
    value = {"schema": SCHEMA, "name": name, "stage": args.proof_stage, "phase": args.phase, "requested_operation": args.operation,
             "controller_sha256": context["artifact"], "collection_binding": collection_binding,
             "graph": route.GRAPH.contract(args.workload, route.C.GATE, negative=name == "credential-unready"),
             "packet": packet, "completion": completion, "gate": gate, "admission": admission}
    return validate_task(value, collection_binding, expected_binding=context["binding"])


def immutable_json(path, value):
    """Content-addressed owned evidence only; no overwrite or promotion."""
    C.RESOURCE.CONTROL.no_symlinks(path)
    if not C.RESOURCE.write_exclusive(path, value):
        expected = T.RUNNER.CONTROL.canonical(value) + b"\n"
        try:
            with path.open("rb") as stream: previous = stream.read(len(expected) + 1)
        except OSError: raise EvidenceFailure("acceptance-retained-proof-unavailable") from None
        require(previous == expected, "acceptance-retained-proof-conflict")
    return {"path": path, "sha256": document_digest(value)}

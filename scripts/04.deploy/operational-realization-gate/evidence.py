#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.operational-realization-evidence
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reuse ordered input-bound realization evidence mechanics while callers own observations, authority and exclusive storage.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/orchestration/commands/script.py
#   - id: deploy.library.environment-sessions.setup
#     path: scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/setup.py
"""Evidence assembly is not proof production or provider authorization."""
import importlib.util
from pathlib import Path
import re
import uuid

_SPEC = importlib.util.spec_from_file_location("realization_evidence_compiler", Path(__file__).with_name("script.py"))
GATE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GATE)


class EvidenceFailure(Exception):
    def __init__(self, reason):
        self.code = "realization-evidence-" + reason
        super().__init__(self.code)


class GateBook:
    def __init__(self, contract, artifact_bindings, cache, *, writer, clock, component_check_id, failure=EvidenceFailure):
        self.contract = contract
        self.identity = GATE.validate_contract(self.contract)
        self.component_check_id = component_check_id
        self.known = GATE.ids(self.contract)[1]
        self.cache, self.components, self.gates = cache, {}, []
        self.plan_digest = None
        self.writer, self.clock, self.failure = writer, clock, failure
        self.require(callable(writer) and callable(clock), "context-invalid")
        self.require(set(artifact_bindings) == {item["id"] for item in self.contract["artifacts"]}, "artifact-binding-incomplete")
        self.facts = {"schema": GATE.FACTS_SCHEMA, "contract_id": self.identity, "gate_evidence": [], "component_evidence": [],
            "artifact_bindings": [{"component_id": name, "immutable_reference": selected,
                "check_id": self.contract["gates"][1]["evidence"][0], "timestamp": self.clock(), "verdict": "passed"}
                for name, selected in sorted(artifact_bindings.items())]}

    def require(self, condition, reason):
        if not condition:
            raise self.failure(reason)

    def component(self, identifier):
        self.require(identifier in self.known and identifier not in self.components, "component-observation-invalid")
        self.components[identifier] = self.clock()

    def gate(self, identifier):
        self.require(identifier == GATE.GATE_ORDER[len(self.gates)], "gate-order-invalid")
        self.gates.append(identifier)
        self.facts["gate_evidence"].append({"gate": identifier, "check_id": self.contract["gates"][len(self.gates) - 1]["evidence"][0], "timestamp": self.clock(), "verdict": "passed", "input_sha256": GATE.evidence_bindings(self.contract, self.facts)["gates"][identifier]})

    def bind_plan(self, selected):
        self.require(isinstance(selected, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", selected) is not None and self.plan_digest in (None, selected), "evidence-plan-mismatch")
        self.plan_digest = selected

    def validate(self, through, change_count=None, activate=False, *, operation_class=None, operation_counts=None):
        self.require(set(self.components) == set(self.known), "component-proof-incomplete")
        self.require(self.plan_digest is not None, "evidence-plan-missing")
        bindings = GATE.evidence_bindings(self.contract, self.facts)
        self.facts["component_evidence"] = [{"component_id": name, "component_kind": self.known[name], "check_id": self.component_check_id, "timestamp": self.components[name], "verdict": "passed", "input_sha256": bindings["components"][name]} for name in sorted(self.components)]
        GATE.validate_facts(self.facts, self.contract, self.identity, self.known, through)
        summary = None
        if change_count is not None:
            selected_operation = ("update" if activate else "create") if operation_class is None else operation_class
            self.require(selected_operation in {"create", "update", "delete"}, "change-operation-invalid")
            counts = {name: change_count if name == selected_operation else 0 for name in ("create", "update", "delete", "replace", "broaden-permission")}
            if operation_counts is not None:
                self.require(isinstance(operation_counts, dict) and set(operation_counts) == set(counts)
                        and all(type(value) is int and value >= 0 for value in operation_counts.values())
                        and sum(operation_counts.values()) == change_count, "change-counts-invalid")
                counts = operation_counts
            summary = {"schema": GATE.CHANGE_SCHEMA, "contract_id": self.identity, "check_id": self.contract["gates"][4]["evidence"][0], "timestamp": self.clock(),
                       "input_sha256": bindings["gates"]["change-set"], "operation_counts": counts}
            GATE.validate_change_summary(summary, self.contract, self.identity, self.facts)
        path = self.cache / (through + "-" + uuid.uuid4().hex + ".json")
        self.require(self.writer(path, {"plan_sha256": self.plan_digest, "facts": self.facts, "change_summary": summary}), "gate-evidence-retention-failed")
        return path

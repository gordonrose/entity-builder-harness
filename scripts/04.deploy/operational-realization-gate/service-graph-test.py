#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.realization-service-graph
#   version: 2
#   status: active
#   created_on: "2026-11-08"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove v2 synchronous service graphs, direct-storage absence, legacy admission and transitive evidence binding through the actual compiler CLI.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

BASE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("service_graph_owner", BASE / "script.py")
OWNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OWNER)
CONTRACT = yaml.safe_load((BASE / "fixtures/private-service-contract.v2.yml").read_text())
LEGACY = yaml.safe_load((BASE / "fixtures/valid-contract.yml").read_text())
CANARY = "synthetic-private-service-canary"
CASES = 0


def run(root, contract, code=None, facts=None, summary=None):
    global CASES
    path = root / "contract.yml"
    path.write_text(yaml.safe_dump(contract))
    argv = [sys.executable, "-B", str(BASE / "script.py"), "--contract", str(path), "--json"]
    if facts is None:
        argv.append("--validate-contract")
    else:
        (root / "facts.yml").write_text(yaml.safe_dump(facts))
        (root / "summary.yml").write_text(yaml.safe_dump(summary))
        argv.extend(["--facts", str(root / "facts.yml"), "--change-summary", str(root / "summary.yml"), "--through", "execution-preflight"])
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    assert result.returncode == (1 if code else 0), (result.returncode, result.stdout, result.stderr)
    report = json.loads(result.stdout)
    assert report["verdict"] == ("failed" if code else "passed")
    assert report["findings"] == ([{"code": code}] if code else []), report
    assert result.stderr == "", result.stderr
    assert CANARY not in result.stdout
    assert set(report) == {"schema", "contract_id", "scope", "verdict", "findings"}
    CASES += 1


def observations(contract):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _, known = OWNER.ids(contract)
    bindings = OWNER.evidence_bindings(contract, {})
    facts = {"schema": OWNER.FACTS_SCHEMA, "contract_id": contract["id"],
             "gate_evidence": [{"gate": gate, "check_id": contract["gates"][i]["evidence"][0], "timestamp": stamp,
                                "verdict": "passed", "input_sha256": bindings["gates"][gate]}
                               for i, gate in enumerate(OWNER.GATE_ORDER[:6])],
             "component_evidence": [{"component_id": name, "component_kind": kind, "check_id": "component-check",
                                     "timestamp": stamp, "verdict": "passed", "input_sha256": bindings["components"][name]}
                                    for name, kind in known.items()]}
    summary = {"schema": OWNER.CHANGE_SCHEMA, "contract_id": contract["id"], "check_id": "change-shape-check", "timestamp": stamp,
               "operation_counts": {"create": 1, "update": 0, "delete": 0, "replace": 0, "broaden-permission": 0},
               "input_sha256": bindings["gates"]["change-set"]}
    return facts, summary


def without_edge(contract, source, destination):
    contract["edges"] = [edge for edge in contract["edges"] if (edge["from"], edge["to"]) != (source, destination)]


def main():
    if not __debug__:
        raise SystemExit("REALIZATION_SERVICE_GRAPH_ASSERTIONS_DISABLED")
    original = copy.deepcopy(CONTRACT)
    repository = BASE.parents[2]
    schema = yaml.safe_load((repository / ".agentic/04.deploy/schemas/operational-realization-contract.v2.schema.yml").read_text())
    assert schema["contract_schema"] == OWNER.SERVICE_CONTRACT_SCHEMA == CONTRACT["schema"]
    assert set(schema["required_top_level"]) == set(CONTRACT)
    assert schema["field_guide"] and (repository / schema["companion_guide"]).is_file()
    assert (repository / schema["base_schema"]).is_file()
    with tempfile.TemporaryDirectory(prefix="realization-service-graph-") as directory:
        root = Path(directory)
        run(root, CONTRACT)
        run(root, LEGACY)
        upgraded = copy.deepcopy(LEGACY); upgraded["schema"] = OWNER.SERVICE_CONTRACT_SCHEMA
        run(root, upgraded)
        refresh = copy.deepcopy(CONTRACT)
        refresh["change_shape"] = {
            "reviewed_change_summary_required": True,
            "allowed_operation_classes": ["update", "replace"],
            "forbidden_operation_classes": ["create", "delete", "broaden-permission"],
            "immutable_definition_refresh": {key: True for key in (
                "owned_task_definitions_only", "stopped_workload_required", "unchanged_permissions_and_storage",
                "qualified_image_required", "original_preparation_retained")}}
        assert set(refresh["change_shape"]["immutable_definition_refresh"]) == set(schema["bounded_definition_refresh"]["required_true_fields"])
        run(root, refresh)
        for field in refresh["change_shape"]["immutable_definition_refresh"]:
            for invalid in (None, False, 1, CANARY):
                changed = copy.deepcopy(refresh); changed["change_shape"]["immutable_definition_refresh"][field] = invalid
                run(root, changed, "change-shape-invalid")
        for invalid in (None, False, [], {}, CANARY):
            changed = copy.deepcopy(refresh); changed["change_shape"]["immutable_definition_refresh"] = invalid
            run(root, changed, "change-shape-invalid")
        changed = copy.deepcopy(refresh); changed["change_shape"].pop("immutable_definition_refresh")
        run(root, changed, "change-shape-invalid")
        changed = copy.deepcopy(LEGACY); changed["change_shape"] = copy.deepcopy(refresh["change_shape"])
        run(root, changed, "change-shape-invalid")
        changed = copy.deepcopy(refresh); changed["change_shape"]["immutable_definition_refresh"]["extra"] = True
        run(root, changed, "change-shape-invalid")
        changed = copy.deepcopy(refresh); changed["change_shape"]["disposable_restore_cleanup"] = {}
        run(root, changed, "change-shape-invalid")
        for operation in ("create", "delete", "broaden-permission"):
            changed = copy.deepcopy(refresh)
            changed["change_shape"]["allowed_operation_classes"].append(operation)
            changed["change_shape"]["forbidden_operation_classes"].remove(operation)
            run(root, changed, "change-shape-invalid")
        refresh_facts, refresh_summary = observations(refresh)
        refresh_summary["operation_counts"].update(create=0, update=1, replace=5)
        run(root, refresh, facts=refresh_facts, summary=refresh_summary)
        cleanup = copy.deepcopy(CONTRACT)
        cleanup["change_shape"] = {
            "reviewed_change_summary_required": True,
            "allowed_operation_classes": ["delete"],
            "forbidden_operation_classes": ["create", "update", "replace", "broaden-permission"],
            "disposable_restore_cleanup": {key: True for key in (
                "original_readback_required", "positive_ownership_required",
                "explicit_execution_approval_required", "preserve_source_and_shared_resources")}}
        assert set(cleanup["change_shape"]["disposable_restore_cleanup"]) == set(schema["bounded_cleanup"]["required_true_fields"])
        run(root, cleanup)
        absent = copy.deepcopy(cleanup); absent["change_shape"].pop("disposable_restore_cleanup")
        run(root, absent, "change-shape-invalid")
        legacy_cleanup = copy.deepcopy(upgraded)
        legacy_cleanup["schema"] = OWNER.CONTRACT_SCHEMA
        legacy_cleanup["change_shape"] = copy.deepcopy(cleanup["change_shape"])
        run(root, legacy_cleanup, "change-shape-invalid")
        for invalid in (None, False, True, [], CANARY, {}):
            changed = copy.deepcopy(cleanup); changed["change_shape"]["disposable_restore_cleanup"] = invalid
            run(root, changed, "change-shape-invalid")
        for field in cleanup["change_shape"]["disposable_restore_cleanup"]:
            for invalid in (None, False, 1, CANARY):
                changed = copy.deepcopy(cleanup); changed["change_shape"]["disposable_restore_cleanup"][field] = invalid
                run(root, changed, "change-shape-invalid")
            changed = copy.deepcopy(cleanup); changed["change_shape"]["disposable_restore_cleanup"].pop(field)
            run(root, changed, "change-shape-invalid")
        changed = copy.deepcopy(cleanup); changed["change_shape"]["disposable_restore_cleanup"]["extra"] = True
        run(root, changed, "change-shape-invalid")
        for operation in ("create", "update", "replace", "broaden-permission"):
            changed = copy.deepcopy(cleanup)
            changed["change_shape"]["allowed_operation_classes"].append(operation)
            changed["change_shape"]["forbidden_operation_classes"].remove(operation)
            run(root, changed, "change-shape-invalid")
        cleanup_facts, cleanup_summary = observations(cleanup)
        cleanup_summary["operation_counts"]["create"] = 0
        cleanup_summary["operation_counts"]["delete"] = 8
        run(root, cleanup, facts=cleanup_facts, summary=cleanup_summary)
        for operation in ("create", "update", "replace", "broaden-permission"):
            changed_summary = copy.deepcopy(cleanup_summary); changed_summary["operation_counts"][operation] = 1
            run(root, cleanup, "normalized-change-summary-forbidden-operation", cleanup_facts, changed_summary)
        missing_gate = copy.deepcopy(cleanup_facts); missing_gate["gate_evidence"].pop(0)
        run(root, cleanup, "normalized-facts-evidence-sequence-invalid", missing_gate, cleanup_summary)
        old = copy.deepcopy(CONTRACT); old["schema"] = OWNER.CONTRACT_SCHEMA
        run(root, old, "connection-destination-type-invalid")
        old = copy.deepcopy(LEGACY); old["execution_units"][0]["state_stores"] = []
        run(root, old, "execution-unit-state_stores-missing")
        old = copy.deepcopy(LEGACY); old["connections"] = []
        run(root, old, "connections-missing")
        old = copy.deepcopy(LEGACY); old["state_stores"] = []
        run(root, old, "state_stores-missing")
        for field in ("connections", "state_stores"):
            for invalid in (None, CANARY, {}):
                changed = copy.deepcopy(CONTRACT); changed["execution_units"][0][field] = invalid
                run(root, changed, "execution-unit-" + field + "-missing")
            changed = copy.deepcopy(CONTRACT); changed["execution_units"][0].pop(field)
            run(root, changed, "execution-unit-" + field + "-missing")
            changed = copy.deepcopy(CONTRACT); changed.pop(field)
            run(root, changed, field + "-missing")
            for invalid in (None, CANARY, {}):
                changed = copy.deepcopy(CONTRACT); changed[field] = invalid
                run(root, changed, field + "-missing")
        for destination, code in (("missing-server", "connection-references-undeclared-node"), ("verifier-identity", "connection-destination-type-invalid")):
            changed = copy.deepcopy(CONTRACT); changed["connections"][0]["destination"] = destination
            run(root, changed, code)
        changed = copy.deepcopy(CONTRACT); changed["connections"][0]["source"] = "verifier-identity"
        run(root, changed, "connection-source-type-invalid")
        changed = copy.deepcopy(CONTRACT); changed["connections"][0]["source"] = "feature-server"
        run(root, changed, "execution-unit-connection-source-mismatch")
        changed = copy.deepcopy(CONTRACT); changed["execution_units"][0]["connections"] = []
        run(root, changed, "connection-source-unit-binding-missing")
        channel = copy.deepcopy(upgraded)
        channel["connections"][0]["destination"] = "delivery-channel"
        channel["execution_units"][0]["state_stores"] = []
        without_edge(channel, "delivery-worker", "delivery-store")
        without_edge(channel, "delivery-connection", "delivery-store")
        channel["edges"].append({"from": "delivery-connection", "to": "delivery-channel", "purpose": "reaches-channel"})
        run(root, channel)
        for source, destination, code in (("private-verifier", "private-call", "undeclared-dependency-edge"), ("private-call", "feature-server", "connection-destination-edge-missing")):
            changed = copy.deepcopy(CONTRACT); without_edge(changed, source, destination)
            run(root, changed, code)
        changed = copy.deepcopy(CONTRACT)
        changed["execution_units"][0]["state_stores"] = ["feature-store"]
        changed["edges"].append({"from": "private-verifier", "to": "feature-store", "purpose": "invented-direct-store"})
        run(root, changed, "execution-unit-store-connection-missing")
        changed["execution_units"][0]["state_stores"] = []
        run(root, changed, "execution-unit-store-edge-unbound")
        changed = copy.deepcopy(CONTRACT); changed["execution_units"][1]["state_stores"] = []
        without_edge(changed, "feature-server", "feature-store")
        run(root, changed, "execution-unit-store-connection-unbound")

        stateless = copy.deepcopy(CONTRACT)
        removed = {item["id"] for item in stateless["connections"] + stateless["state_stores"]}
        stateless["connections"], stateless["state_stores"] = [], []
        for unit in stateless["execution_units"]: unit["connections"], unit["state_stores"] = [], []
        stateless["edges"] = [edge for edge in stateless["edges"] if edge["from"] not in removed and edge["to"] not in removed]
        run(root, stateless)
        for schema in ("operational-realization-contract/v3", None, [], CANARY):
            changed = copy.deepcopy(CONTRACT); changed["schema"] = schema
            run(root, changed, "contract-schema-or-boundary-invalid")
        changed = copy.deepcopy(CONTRACT); changed["connections"][0]["transport_security"] = CANARY
        run(root, changed, "connection-security-invalid")
        changed = copy.deepcopy(CONTRACT); changed["gates"][5]["may_mutate_live_target"] = True
        run(root, changed, "gate-mutation-boundary-invalid")
        changed = copy.deepcopy(CONTRACT); changed["gates"].pop()
        run(root, changed, "gate-sequence-invalid")
        changed = copy.deepcopy(CONTRACT); changed["lifecycle"]["retry"]["mode"] = "automatic"
        run(root, changed, "unsafe-retry-policy")
        changed = copy.deepcopy(CONTRACT); changed["configuration_inputs"][0]["token_value"] = CANARY
        run(root, changed, "unsafe-value-field-declared")

        facts, summary = observations(CONTRACT)
        run(root, CONTRACT, facts=facts, summary=summary)
        missing = copy.deepcopy(facts); missing["component_evidence"] = [item for item in missing["component_evidence"] if item["component_id"] != "feature-store"]
        run(root, CONTRACT, "component-evidence-incomplete", missing, summary)
        stale = copy.deepcopy(facts); stale["gate_evidence"][3]["timestamp"] = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        run(root, CONTRACT, "normalized-facts-current-evidence-stale", stale, summary)
        baseline = OWNER.evidence_bindings(CONTRACT, {})
        caller_identity = copy.deepcopy(CONTRACT["identities"][0])
        for mutation in ("configuration", "permissions", "connection", "image", "store"):
            changed = copy.deepcopy(CONTRACT)
            if mutation == "configuration": changed["configuration_inputs"][1]["required_fields"].append("second-setting")
            elif mutation == "permissions": changed["identities"][1]["permissions"].append("new-state-operation")
            elif mutation == "connection": changed["connections"][1]["transport_security"] = "not-applicable"
            elif mutation == "image": changed["artifacts"][1]["immutable_reference"] = "sha256:" + "c" * 64
            else: changed["state_stores"][0]["semantics"].append("reviewed-concurrency-policy")
            bindings = OWNER.evidence_bindings(changed, {})
            assert bindings["components"]["private-verifier"] != baseline["components"]["private-verifier"]
            assert bindings["components"]["verifier-identity"] == baseline["components"]["verifier-identity"]
            assert bindings["components"]["verifier-artifact"] == baseline["components"]["verifier-artifact"]
            assert changed["identities"][0] == caller_identity
            revised_facts, revised_summary = observations(changed)
            for item in revised_facts["component_evidence"]:
                if item["component_id"] == "private-verifier": item["input_sha256"] = baseline["components"]["private-verifier"]
            run(root, changed, "component-evidence-input-mismatch", revised_facts, revised_summary)
            if mutation == "permissions":
                # Reuse the actual unchanged artifact gate record, not merely
                # its hash. Current permission/source observations remain new.
                old_gate = copy.deepcopy(facts["gate_evidence"][1])
                revised_facts, revised_summary = observations(changed)
                assert revised_facts["gate_evidence"][1]["input_sha256"] == old_gate["input_sha256"]
                revised_facts["gate_evidence"][1] = old_gate
                run(root, changed, facts=revised_facts, summary=revised_summary)
                assert revised_facts["gate_evidence"][1] == facts["gate_evidence"][1]
        assert CONTRACT == original
        assert CONTRACT["execution_units"][0]["state_stores"] == []
        assert CONTRACT["identities"][0]["permissions"] == ["call-private-feature"]
    print(json.dumps({"verdict": "passed", "scope": "realization-service-graph", "evidence_class": "simulated", "cli_cases": CASES, "provider_calls": 0}))


if __name__ == "__main__":
    main()

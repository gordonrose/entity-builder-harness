#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.entity-smoke.task-graph
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Derive a versioned selected-operation graph containing the actual controller and every reachable workload dependency without claiming unrelated workloads live-proven.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import copy
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[7]
RUNTIME = ROOT / "infra/04.deploy/03.product/image/entity-smoke/realization-contract.v2.yml"
CONTROLLER = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/infrastructure-realization-contract.v2.yml"
ROOT_UNITS = {"administration": "feature-administration", "migration": "feature-migration", "database-proof": "feature-database-proof", "verifier": "feature-verifier", "restore-reader": "feature-restore-reader"}
CONTROLLER_SOURCE = "task-controller-source"
RENAMES = {"infrastructure-controller-source": CONTROLLER_SOURCE, "infrastructure-controller": "task-controller", "infrastructure-operator": "task-operator", "infrastructure-inputs": "task-inputs", "infrastructure-safe-reports": "task-safe-reports", "infrastructure-reconciliation": "task-reconciliation"}


def contract(workload, compiler, *, negative=False):
    if not isinstance(workload, str) or workload not in ROOT_UNITS: raise compiler.ContractFailure("task-graph-workload-invalid")
    if type(negative) is not bool or negative and workload != "verifier": raise compiler.ContractFailure("task-graph-negative-selection-invalid")
    runtime, controller = (yaml.safe_load(path.read_text()) for path in (RUNTIME, CONTROLLER))
    compiler.validate_contract(runtime); compiler.validate_contract(controller)
    def rename(value):
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return RENAMES.get(value, value) if isinstance(value, str) else value
    result = rename(controller)
    result["id"] = "entity-smoke-task-operation-" + workload
    result["version"] = 1
    if result["schema"] != runtime["schema"] or result["lifecycle"] != runtime["lifecycle"] or result["change_shape"] != runtime["change_shape"]:
        raise compiler.ContractFailure("task-graph-source-contracts-disagree")
    result["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py"
    if workload == "restore-reader": result["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restore-reader-route.py"
    result["artifacts"][0]["assertions"] = ["committed-controller-source-closure", "qualified-application-source-match", "actual-task-binding-and-control-fixtures"]
    result["identities"][0]["permissions"] = ["inspect-selected-target", "launch-only-reviewed-private-task", "pass-only-selected-workload-roles"]
    result["configuration_inputs"][0]["required_fields"].extend(["selected-workload", "selected-operation", "selected-preflight-label"])
    state = next(item for item in result["state_stores"] if item["id"] == "resource-control-state")
    state["semantics"] = ["matching-deployed-source-and-parameters", "matching-immutable-task-role-and-network", "reserved-operation-identity", "explicit-terminal-state"]
    nodes, pending = set(), [ROOT_UNITS[workload]]
    while pending:
        name = pending.pop()
        if name in nodes: continue
        nodes.add(name)
        pending.extend(edge["to"] for edge in runtime["edges"] if edge["from"] == name)
    for section in compiler.COMPONENTS:
        result[section].extend(copy.deepcopy(item) for item in runtime[section] if item["id"] in nodes)
    result["edges"].extend(copy.deepcopy(edge) for edge in runtime["edges"] if edge["from"] in nodes and edge["to"] in nodes)
    result["edges"].append({"from": "task-controller", "to": ROOT_UNITS[workload], "purpose": "dispatches-and-observes-reviewed-unit"})
    result["assumptions"].extend(copy.deepcopy(runtime["assumptions"]))
    result["assumptions"].append({"id": "preflight-is-not-business-proof", "statement": "provider-owned-observation-launch-allowance-does-not-mark-execution-preflight-or-business-completion-passed", "required_proof": "declared", "actual_proof": "declared"})
    for gate in result["gates"]: gate["evidence"] = ["entity-smoke-task-" + gate["id"]]
    if negative:
        result["id"] = "entity-smoke-credential-unready-observation"
        next(item for item in result["identities"] if item["id"] == "feature-runtime-identity")["permissions"] = ["runtime-authentication-intentionally-revoked", "no-feature-operation-admission"]
        next(item for item in result["state_stores"] if item["id"] == "feature-record-store")["semantics"] = ["same-qualified-dependency-incarnation", "no-record-access-proof-from-negative-observation"]
        next(item for item in result["artifacts"] if item["id"] == "feature-verifier-artifact")["assertions"].append("live-but-not-ready-after-source-owned-revocation")
        result["assumptions"].append({"id": "negative-is-not-healthy-access", "statement": "execution-preflight-in-this-distinct-contract-means-completed-bounded-expected-denial-only-never-ordinary-ready-admission", "required_proof": "declared", "actual_proof": "declared"})
        for gate in result["gates"]: gate["evidence"] = ["entity-smoke-credential-unready-" + gate["id"]]
    compiler.validate_contract(result)
    return result


def replacement(compiler, source, stage="baseline"):
    if stage not in {"baseline", "credential-recovery"}: raise compiler.ContractFailure("replacement-graph-stage-invalid")
    name = "replacement" if stage == "baseline" else "credential-replacement"
    def rename(value):
        if isinstance(value, str): return value.replace("infrastructure", name)
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return value
    value = rename(yaml.safe_load(source.read_text()))
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/replacement-route.py"
    value["identities"][0]["permissions"] = ["inspect-selected-target", "stop-only-exact-original-server"]
    value["state_stores"][0]["semantics"] = ["original-labelled-record-read", "owned-source-and-creation-lineage", "distinct-qualified-healthy-successor"]
    value["recovery_plans"][0].update(entry_condition="original-reserved-stop-not-terminal", cleanup="no-data-or-resource-deletion", rollback="observe-original-stop-never-stop-successor")
    value["change_shape"]["allowed_operation_classes"] = ["update"]
    value["change_shape"]["forbidden_operation_classes"] = ["create", "delete", "replace", "broaden-permission"]
    value["assumptions"] = [{"id": "replacement-is-not-readback", "statement": "replacement-completion-requires-a-separate-original-record-read-before-acceptance", "required_proof": "declared", "actual_proof": "declared"}]
    if stage == "credential-recovery":
        value["state_stores"][0]["semantics"].append("owned-access-restoration-after-expected-denial")
    compiler.validate_contract(value)
    return value

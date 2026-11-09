#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-completion
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind immutable collected task steps to actual retained seventh-gate completion without restamping historical facts or authorizing replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.task-plan.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py


def path(step): return step.with_name(step.stem + ".completion.json")


def read(route, context, args, step):
    C, require = route.C, route.STEPS.require
    target = path(step)
    route.RUNNER.CONTROL.no_symlinks(target)
    require(target.is_file(), "task-step-completion-required")
    value = C.read_json(target)
    require(isinstance(value, dict) and set(value) == {"schema", "step_sha256", "plan_sha256", "realization_evidence", "realization_evidence_sha256"}
            and value["schema"] == "deploy/entity-smoke-task-completion/v1" and value["step_sha256"] == C.digest_file(step), "task-step-completion-binding-mismatch")
    packet = C.read_json(step)
    require(value["plan_sha256"] == packet["plan_sha256"], "task-step-completion-plan-mismatch")
    reference = value["realization_evidence"]
    prefix = str((context["cache"] / "task-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and route.re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):]), "task-step-completion-gate-path-invalid")
    evidence = C.ROOT / reference
    route.RUNNER.CONTROL.no_symlinks(evidence)
    require(C.digest_file(evidence) == value["realization_evidence_sha256"], "task-step-completion-gate-changed")
    retained = C.read_json(evidence)
    declaration = route.GRAPH.contract(args.workload, C.GATE, negative=route.CREDENTIAL.negative(args))
    expected = {row["id"]: C.source_digest() if row["id"] == route.GRAPH.CONTROLLER_SOURCE else context["binding"]["image_digest"] for row in declaration["artifacts"]}
    validate_gate(route, declaration, retained, value["plan_sha256"], expected)
    return value


def validate_gate(route, declaration, retained, plan_sha256, expected):
    """Validate captured seventh-gate custody without restamping it as fresh.

    Current task completion supplies current source bindings; historical receipt
    readers supply the immutable bindings captured with their selected graph.
    """
    C, require = route.C, route.STEPS.require
    require(isinstance(retained, dict) and set(retained) == {"plan_sha256", "facts", "change_summary"}
            and retained["plan_sha256"] == plan_sha256, "task-step-completion-gate-plan-mismatch")
    facts = retained["facts"]
    identity, known = C.GATE.ids(declaration)
    require(isinstance(facts, dict) and facts.get("schema") == C.GATE.FACTS_SCHEMA and facts.get("contract_id") == declaration["id"], "task-step-completion-contract-mismatch")
    gates, components, artifacts = (facts.get(name) for name in ("gate_evidence", "component_evidence", "artifact_bindings"))
    require(isinstance(gates, list) and all(isinstance(row, dict) for row in gates)
            and [row.get("gate") for row in gates] == list(C.GATE.GATE_ORDER[:7]), "task-step-completion-gates-incomplete")
    require(isinstance(components, list) and len(components) == len(known) and all(isinstance(row, dict) for row in components)
            and {row.get("component_id") for row in components} == set(known), "task-step-completion-components-incomplete")
    require(isinstance(artifacts, list) and len(artifacts) == len(expected) and all(isinstance(row, dict) for row in artifacts)
            and {row.get("component_id"): row.get("immutable_reference") for row in artifacts} == expected, "task-step-completion-artifacts-mismatch")
    bindings = C.GATE.evidence_bindings(declaration, facts)
    require(all(row.get("verdict") == "passed" and row.get("check_id") in declaration["gates"][index]["evidence"]
                and row.get("input_sha256") == bindings["gates"][row["gate"]] for index, row in enumerate(gates))
            and all(row.get("verdict") == "passed" and row.get("component_kind") == known[row["component_id"]]
                    and row.get("input_sha256") == bindings["components"][row["component_id"]] for row in components)
            and all(row.get("verdict") == "passed" for row in artifacts), "task-step-completion-facts-mismatch")
    # These immutable bytes were validated by the actual gate producer. This
    # linkage is historical custody, not a new current-state/freshness pass.
    for row in gates + components + artifacts: C.GATE.safe_timestamp(row.get("timestamp"), "task-step-completion-timestamp-invalid")
    return retained


def retain(route, context, args, step, evidence):
    C = route.C
    value = {"schema": "deploy/entity-smoke-task-completion/v1", "step_sha256": C.digest_file(step),
             "plan_sha256": C.read_json(step)["plan_sha256"], "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence)}
    route.STEPS.require(C.read_json(evidence).get("plan_sha256") == value["plan_sha256"], "task-step-completion-original-plan-required")
    C.RESOURCE.write_exclusive(path(step), value)
    return read(route, context, args, step)

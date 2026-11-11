#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.source-transition
#   version: 1
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Replace only the stopped feature's image after administrator recovery while retaining exact original preparation evidence without replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

LABEL = "entity-smoke-8f76ed3480e85d60fb60f547"
OLD_SOURCE = "8f76ed3480e85d60fb60f547f996628c8554504d"
OLD_IMAGE = "sha256:282b3b2a4dab14df45cc7433c9d52ad30a8a4ea61ba1353d861c487b5251c0ac"
FAILED_PREFLIGHT = "es-cfa256731b854baeb1e1427fd94cb01f"
PINS = {
    "54e1f8035f6c1cf1404ce685193d0e5e141bee0856ee726afe239581f93c8cb3": ("9c66ffe83e80692c301e98c7bd89b158c4b675e58c1e011eee7ebb3f48778c30", "ae545968c53e005e223320e805967c95209b7a96d764257e3b537cb4adce9903"),
    "c048875837a67e77371278a31ee77600e53f7b8633c1dffcfd51445576f916f4": ("2e77bb18ed5b82574a04d69e4b4b5df522c5749edf4670c35bf104e78a2982f1", "ae545968c53e005e223320e805967c95209b7a96d764257e3b537cb4adce9903"),
    "d5ed43c61fa2179b4c46cc8326e83c6bcdf9f38a7a8e5b643ef16a1125f999db": ("626dd88cd876e4d8e969c713fa783eda4340c35042f89a2959e6a8e6ba27ba79", "20373db2f9f42a0a63f5948c14d587343161b4666f225f32818a937300a742c8"),
    "b7f6b2db5eaef57d82088aee602102a4283698bc60dc817a4df44ffe06c69da5": ("0390d89072d1a0a0493d662d9cf06d9931c0ddbeb1dc3a4928ed2bbed07e4311", "20373db2f9f42a0a63f5948c14d587343161b4666f225f32818a937300a742c8"),
}
TASK_DEFINITIONS = {name + "TaskDefinition" for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof")}
RECOVERY = {
    "administrator-recovery/validated/result.json": "9adfdc13e471d1c12839af34d6f5d0ac4d136d367c45ea3f68e34c910b07a727",
    "administrator-recovery/validated/temporary-access-removed.json": "78793d7a4addfc11a4b3045ad3feed4eb2bb009d2600533e1da7ebf591db83d6",
}
RECOVERY_PROGRAMS = {
    "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-observation.js": "98f4e513d81880502511f85ac6fae3b8c8b239fd6cbfbcb9d0e21a9947bb2cd0",
    "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-recovery.js": "f01ca9388da3f9a55aba35e310c97050f4b3a10dfe7a6a0999a4b76e81f7d1bf",
}


def document(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()


def controller(packet, completion, current):
    pinned = PINS.get(document(packet))
    return "sha256:" + pinned[1] if pinned and document(completion) == pinned[0] else current


def historical(packet, completion):
    return controller(packet, completion, None) is not None


def compatible(C, before, after):
    C.RESOURCE.validate_binding(before, record_required=False)
    C.RESOURCE.validate_binding(after, record_required=False)
    C.require(before["source_revision"] == OLD_SOURCE and before["image_digest"] == OLD_IMAGE
              and before["proof_label"] == after["proof_label"] == LABEL
              and before["source_revision"] != after["source_revision"] and before["image_digest"] != after["image_digest"]
              and all(before[key] == after[key] for key in before if key not in {"source_revision", "image_digest"}), "source-transition-binding-incompatible")


def validate(C, value, binding):
    C.require(isinstance(value, dict) and set(value) == {"schema", "plan", "plan_sha256", "resources", "terminal_token", "completed_at", "graph", "gate"}
              and value["schema"] == "deploy/entity-smoke-source-transition/v1", "source-transition-receipt-invalid")
    plan = value["plan"]
    C.require(isinstance(plan, dict) and value["plan_sha256"] == C.DEPLOY.fingerprint(plan)
              and plan.get("binding") == binding and plan.get("desired_count") == 0
              and plan.get("automatic_retry") is False, "source-transition-plan-mismatch")
    compatible(C, plan["previous_binding"], binding)
    before, after = plan["resources"], value["resources"]
    C.require(set(before) == set(after) == set(C.DEPLOY.RESOURCE_TYPES), "source-transition-resource-set-invalid")
    for name, row in before.items():
        C.require(row["type"] == after[name]["type"] == C.DEPLOY.RESOURCE_TYPES[name]
                  and (row == after[name] if name not in TASK_DEFINITIONS else row["physical_id"] != after[name]["physical_id"]), "source-transition-resource-identity-invalid")
    C.require(value["terminal_token"] == "es-source-execute-" + value["plan_sha256"][7:39], "source-transition-terminal-token-invalid")
    C.RESOURCE.timestamp(value["completed_at"])
    C.require(value["graph"] == graph(C), "source-transition-graph-mismatch")
    completion = C.module("entity_smoke_transition_gate_reader", C.DIRECTORY / "task-completion.py")
    completion.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), value["graph"], value["gate"], value["plan_sha256"], {"infrastructure-controller-source": plan["controller_sha256"]})
    summary = value["gate"].get("change_summary")
    C.require(isinstance(summary, dict) and summary.get("operation_counts") == {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}
              and summary.get("input_sha256") == C.GATE.evidence_bindings(value["graph"], value["gate"]["facts"])["gates"]["change-set"], "source-transition-change-counts-mismatch")
    return value


def read(C, cache, binding):
    path = cache / "source-transition/receipt.json"
    C.RESOURCE.CONTROL.no_symlinks(path)
    if not path.exists(): return None
    value = validate(C, C.read_json(path), binding)
    plan = value["plan"]
    C.require(C.digest_file(cache / "receipts/create.json") == plan["creation_sha256"], "source-transition-creation-changed")
    for name, digest in RECOVERY.items():
        C.require(C.digest_file(cache / name) == "sha256:" + digest, "source-transition-recovery-changed")
    return value


def original_receipt(C, context, packet, completion):
    if not historical(packet, completion): return False
    before = packet["binding"]
    if before != context["binding"]:
        transition = read(C, context["cache"], context["binding"])
        C.require(transition is not None and before == transition["plan"]["previous_binding"], "source-transition-historical-binding-invalid")
    return True


def legacy_context(route, context, args, packet, completion):
    if not original_receipt(route.C, context, packet, completion): return None
    C = route.C
    request = packet["reservation"]["request"]
    checked = {**context["checked"], **{key: request[key] for key in ("definition", "security_group", "subnets")}}
    report = {"plan": {"preflight_label": request["proof_label"]}}
    return {**context, "binding": packet["binding"], "checked": checked, "report": report}


def replacement_label(context, args, original):
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) != (LABEL, "administration", "grant-runtime", "baseline"):
        return original
    return "entity-smoke-" + hashlib.sha256((original + ":" + FAILED_PREFLIGHT + ":administrator-authentication-recovery-1").encode()).hexdigest()[:24]


def recovery_preflight(C, context, args, original):
    selected = replacement_label(context, args, original)
    if selected == original: return original
    C.require(read(C, context["cache"], context["binding"]) is not None, "source-transition-replacement-preflight-recovery-required")
    target = context["cache"] / "task-attempts" / (original + "-administration-preflight.json")
    previous = C.read_json(target)
    request = previous.get("request", {})
    C.require(previous.get("operation_id") == FAILED_PREFLIGHT and request.get("source_revision") == OLD_SOURCE
              and request.get("image_digest") == OLD_IMAGE and request.get("proof_label") == original
              and request.get("environment") == {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}
              and C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts").read("original-preflight", request) == previous,
              "source-transition-original-preflight-mismatch")
    return selected


def inventory(C, provider, binding, parameters):
    stack = C.DEPLOY.deployed_stack(provider, binding, parameters)
    response = provider("cloudformation", "list-stack-resources", StackName=stack["StackId"])
    rows = response.get("StackResourceSummaries")
    C.require(isinstance(rows, list) and len(rows) == len(C.DEPLOY.RESOURCE_TYPES) and not response.get("NextToken"), "source-transition-inventory-incomplete")
    resources = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows}
    C.require(set(resources) == set(C.DEPLOY.RESOURCE_TYPES), "source-transition-inventory-invalid")
    service = C.RESOURCE.service(provider, resources["ServerTaskDefinition"]["physical_id"], 0)
    C.require(service.get("runningCount") == service.get("pendingCount") == 0, "source-transition-service-not-stopped")
    return stack, resources


def retain(C, root, name, value):
    if not C.RESOURCE.write_exclusive(root / name, value):
        C.require(C.read_json(root / name) == value, "source-transition-retention-conflict")
    return value


def graph(C):
    value = C.yaml.safe_load(C.CONTRACT.read_text())
    value["id"] += "-source-transition"
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/source-transition.py"
    value["change_shape"].update(allowed_operation_classes=["update", "replace"], forbidden_operation_classes=["create", "delete", "broaden-permission"])
    value["change_shape"]["immutable_definition_refresh"] = {key: True for key in (
        "owned_task_definitions_only", "stopped_workload_required", "unchanged_permissions_and_storage", "qualified_image_required", "original_preparation_retained")}
    C.GATE.validate_contract(value)
    return value


def gates(C, root, plan, through):
    """The same infrastructure gate graph, with truthful replacement counts."""
    book = C.GateBook(plan["controller_sha256"], root / "realization", contract=graph(C))
    book.bind_plan(C.DEPLOY.fingerprint(plan))
    for identifier in book.known: book.component(identifier)
    for identifier in C.GATE.GATE_ORDER:
        book.gate(identifier)
        if identifier == through: break
    initial = book.validate(through)
    value = C.read_json(initial)
    if through in {"change-set", "execution-preflight", "controlled-execution"}:
        summary = {"schema": C.GATE.CHANGE_SCHEMA, "contract_id": book.identity, "check_id": book.contract["gates"][4]["evidence"][0], "timestamp": C.now(),
                   "input_sha256": C.GATE.evidence_bindings(book.contract, book.facts)["gates"]["change-set"],
                   "operation_counts": {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}}
        C.GATE.validate_change_summary(summary, book.contract, book.identity, book.facts)
        value["change_summary"] = summary
        selected = root / "realization" / (through + "-" + C.uuid.uuid4().hex + ".json")
        C.require(C.RESOURCE.write_exclusive(selected, value), "source-transition-gate-retention-failed")
        return selected
    return initial


def change(C, provider, plan, *, executed=False):
    digest = C.DEPLOY.fingerprint(plan)
    name = "entity-smoke-source-" + digest[7:31]
    response = provider("cloudformation", "describe-change-set", StackName=plan["stack_arn"], ChangeSetName=name)
    C.require(response.get("StackId") == plan["stack_arn"] and response.get("ChangeSetName") == name
              and response.get("Description") == "es-source-review-" + digest[7:39] and not response.get("NextToken"), "source-transition-change-identity-invalid")
    if response.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}: return None
    C.require(response.get("Status") == "CREATE_COMPLETE" and response.get("ExecutionStatus") in ({"EXECUTE_IN_PROGRESS", "EXECUTE_COMPLETE"} if executed else {"AVAILABLE"})
              and response.get("Capabilities") == ["CAPABILITY_IAM"] and not response.get("RoleARN") and not response.get("NotificationARNs")
              and not response.get("IncludeNestedStacks", False) and not response.get("ImportExistingResources", False), "source-transition-change-not-ready")
    C.DEPLOY.exact_parameters(response.get("Parameters"), plan["parameters"])
    changes = response.get("Changes")
    C.require(isinstance(changes, list) and len(changes) == 6, "source-transition-change-count-invalid")
    seen = set()
    for entry in changes:
        row = entry.get("ResourceChange", {})
        name = row.get("LogicalResourceId")
        C.require(name in TASK_DEFINITIONS | {"FeatureService"} and name not in seen and row.get("Action") == "Modify"
                  and row.get("ResourceType") == C.DEPLOY.RESOURCE_TYPES[name] and row.get("PhysicalResourceId") == plan["resources"][name]["physical_id"]
                  and row.get("Replacement") == ("True" if name in TASK_DEFINITIONS else "False")
                  and row.get("Scope") == ["Properties"], "source-transition-change-shape-invalid")
        details = row.get("Details")
        allowed = {"ContainerDefinitions"} if name in TASK_DEFINITIONS else {"TaskDefinition"}
        C.require(isinstance(details, list) and details and all(item.get("Target", {}).get("Attribute") == "Properties" and item["Target"].get("Name") in allowed for item in details), "source-transition-change-property-invalid")
        seen.add(name)
    C.require(seen == TASK_DEFINITIONS | {"FeatureService"}, "source-transition-change-set-invalid")
    body = provider("cloudformation", "get-template", StackName=plan["stack_arn"], ChangeSetName=response["ChangeSetId"], TemplateStage="Original").get("TemplateBody")
    C.require(C.DEPLOY.CF.templates_equal(body, C.DEPLOY.source()[1]), "source-transition-template-changed")
    return response["ChangeSetId"]


def run(C, args, provider):
    receipt = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(receipt)
    C.local_checks()
    operator = C.operator_preflight(provider)
    alignment, parameters, _ = C.ALIGN.inspect(provider, receipt, C.now())
    parameters["ServerDesiredCount"] = "0"
    binding = {**C.binding_for(receipt, alignment), "proof_label": LABEL}
    cache = C.ROOT / ".cache/entity-smoke-live" / LABEL
    root = cache / "source-transition"
    C.filesystem_preflight(root)
    created = C.read_json(cache / "receipts/create.json")
    old_binding = created["binding"]
    compatible(C, old_binding, binding)
    old_parameters = {**parameters, "SourceRevision": OLD_SOURCE, "ImageDigest": OLD_IMAGE}
    for name, digest in RECOVERY.items(): C.require(C.digest_file(cache / name) == "sha256:" + digest, "source-transition-recovery-required")
    for name, digest in RECOVERY_PROGRAMS.items(): C.require(C.digest_file(C.ROOT / name) == "sha256:" + digest, "source-transition-recovery-program-changed")
    # Runtime/schema/package inputs other than the two reviewed authority fixes
    # must be byte-identical. Controller/docs/tests changes are not app changes.
    changed = C.ALIGN.command(["git", "diff", "--name-only", OLD_SOURCE, receipt["source_revision"], "--", "apps", "packages", "platform", "infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/image", "package.json", "package-lock.json"]).splitlines()
    allowed = {"infra/04.deploy/03.product/entrypoints/entity-smoke/administration.ts", "infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.ts"}
    C.require(set(changed) == allowed, "source-transition-runtime-change-not-approved")
    fixed = {"administration.ts": "e00e20c8bfaf1e891e011942f440432ed13be15fc8a4bd6069e56a657c4cb388",
             "preflight.ts": "307d353bd6797f1c2fef06e620911d045b7f04bd42186b58bc362f9f06958f75"}
    for name, expected in fixed.items():
        body = C.ALIGN.command(["git", "show", receipt["source_revision"] + ":infra/04.deploy/03.product/entrypoints/entity-smoke/" + name])
        C.require(hashlib.sha256(body.encode()).hexdigest() == expected, "source-transition-reviewed-correction-changed")
    if (root / "plan.json").exists():
        plan = C.read_json(root / "plan.json")
        C.require(plan["binding"] == binding and plan["controller_sha256"] == C.source_digest() and plan["parameters"] == parameters, "source-transition-original-plan-mismatch")
    else:
        stack, resources = inventory(C, provider, old_binding, old_parameters)
        C.require(stack.get("StackStatus") == "CREATE_COMPLETE" and created["result"]["facts"]["resources"] == resources
                  and created["result"]["facts"]["stack_arn"] == stack["StackId"], "source-transition-original-creation-required")
        plan = {"schema": "deploy/entity-smoke-source-transition-plan/v1", "binding": binding, "previous_binding": old_binding,
                "stack_arn": stack["StackId"], "resources": resources, "parameters": parameters, "controller_sha256": C.source_digest(),
                "creation_sha256": C.digest_file(cache / "receipts/create.json"), "template_sha256": C.digest_file(C.DEPLOY.SOURCE),
                "package_custody_reference": receipt["receipt_reference"], "operator_sha256": operator, "desired_count": 0, "automatic_retry": False}
    digest = C.DEPLOY.fingerprint(plan)
    C.require(plan["operator_sha256"] == operator and plan["template_sha256"] == C.digest_file(C.DEPLOY.SOURCE), "source-transition-preflight-changed")
    if args.mode == "plan": return {"verdict": "planned", "plan_sha256": digest, "replace": sorted(TASK_DEFINITIONS), "modify": ["FeatureService"], "desired_count": 0, "database_writes": False}
    C.require(args.approved_plan == digest, "source-transition-approved-plan-mismatch")
    retain(C, root, "plan.json", plan)
    if args.mode == "review":
        stack, resources = inventory(C, provider, old_binding, old_parameters)
        C.require(stack["StackId"] == plan["stack_arn"] and stack.get("StackStatus") == "CREATE_COMPLETE" and resources == plan["resources"], "source-transition-before-state-changed")
        token = "es-source-review-" + digest[7:39]
        intent = {"plan_sha256": digest, "token": token, "operation": "create-change-set"}
        if C.RESOURCE.write_exclusive(root / "review-intent.json", intent):
            provider.effect = "unknown-reconcile-only"
            provider._invoke("cloudformation", "create-change-set", {"StackName": plan["stack_arn"], "ChangeSetName": "entity-smoke-source-" + digest[7:31], "ChangeSetType": "UPDATE",
                "Description": token, "ClientToken": token, "UsePreviousTemplate": True, "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())], "Capabilities": ["CAPABILITY_IAM"]})
        else: C.require(C.read_json(root / "review-intent.json") == intent, "source-transition-review-intent-mismatch")
        arn = change(C, provider, plan)
        if arn is None: return {"verdict": "pending", "next": "review", "plan_sha256": digest}
        retain(C, root, "review.json", {"plan_sha256": digest, "change_set_arn": arn})
        gates(C, root, plan, "change-set")
        return {"verdict": "reviewed", "plan_sha256": digest}
    review = C.read_json(root / "review.json")
    C.require(review.get("plan_sha256") == digest, "source-transition-review-mismatch")
    token = "es-source-execute-" + digest[7:39]
    intent = {"plan_sha256": digest, "token": token, "operation": "execute-change-set", "change_set_arn": review["change_set_arn"]}
    if not (root / "execute-intent.json").exists():
        C.require(args.mode == "execute", "source-transition-execution-intent-required")
        stack, resources = inventory(C, provider, old_binding, old_parameters)
        C.require(stack["StackId"] == plan["stack_arn"] and resources == plan["resources"] and stack.get("StackStatus") == "CREATE_COMPLETE"
                  and change(C, provider, plan) == review["change_set_arn"], "source-transition-execution-state-changed")
        C.ALIGN.source_preflight(receipt)
        C.require(C.source_digest() == plan["controller_sha256"] and C.operator_preflight(provider) == operator, "source-transition-source-or-operator-changed")
        validation = provider("cloudformation", "validate-template", TemplateBody=C.DEPLOY.source()[0])
        C.require({row.get("ParameterKey") for row in validation.get("Parameters", [])} == C.DEPLOY.PARAMETERS
                  and validation.get("Capabilities") == ["CAPABILITY_IAM"] and not validation.get("DeclaredTransforms"), "source-transition-template-preflight-failed")
        gates(C, root, plan, "execution-preflight")
        if C.RESOURCE.write_exclusive(root / "execute-intent.json", intent):
            provider.effect = "unknown-reconcile-only"
            provider._invoke("cloudformation", "execute-change-set", {"StackName": plan["stack_arn"], "ChangeSetName": review["change_set_arn"], "ClientRequestToken": token})
    C.require(C.read_json(root / "execute-intent.json") == intent, "source-transition-execution-intent-mismatch")
    stack = C.RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=plan["stack_arn"]), "Stacks")
    if stack.get("StackStatus") in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"}:
        return {"verdict": "pending", "next": "reconcile", "plan_sha256": digest}
    C.require(stack.get("StackStatus") == "UPDATE_COMPLETE", "source-transition-update-not-successful")
    stack, resources = inventory(C, provider, binding, parameters)
    binding_owner = C.module("entity_smoke_transition_task_binding", C.DIRECTORY / "task-binding.py")
    for workload in ("server", "migration", "administration", "verifier", "database-proof"):
        binding_owner.inspect(provider, workload, parameters, resources, C.DEPLOY.source()[1])
    events = provider("cloudformation", "describe-stack-events", StackName=plan["stack_arn"])
    C.require(any(row.get("PhysicalResourceId") == plan["stack_arn"] and row.get("ClientRequestToken") == token and row.get("ResourceStatus") == "UPDATE_COMPLETE" for row in events.get("StackEvents", [])), "source-transition-terminal-event-missing")
    if (root / "receipt.json").exists(): result = read(C, cache, binding)
    else:
        evidence = gates(C, root, plan, "controlled-execution")
        result = {"schema": "deploy/entity-smoke-source-transition/v1", "plan": plan, "plan_sha256": digest, "resources": resources, "terminal_token": token,
                  "completed_at": C.now(), "graph": graph(C), "gate": C.read_json(evidence)}
        validate(C, result, binding)
        retain(C, root, "completion.json", {"realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence), "plan_sha256": digest})
        retain(C, root, "receipt.json", result)
    return {"verdict": "completed", "plan_sha256": digest, "receipt": str((root / "receipt.json").relative_to(C.ROOT))}


def main():
    spec = importlib.util.spec_from_file_location("entity_smoke_source_transition_common", Path(__file__).with_name("script.py"))
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    provider = C.module("entity_smoke_transition_provider", C.DIRECTORY / "task-route.py").Provider()
    try:
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--receipt", type=Path, required=True)
        parser.add_argument("--mode", choices=("plan", "review", "execute", "reconcile"), required=True)
        parser.add_argument("--approved-plan")
        result = run(C, parser.parse_args(), provider)
        print(json.dumps({**result, "effect": provider.effect}, sort_keys=True)); return 0
    except Exception as failure:
        print(json.dumps({"verdict": "blocked", "condition": getattr(failure, "code", "source-transition-observation-not-confirmed"), "effect": provider.effect})); return 1


if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.image-delivery-repair
#   version: 1
#   status: draft
#   created_on: "2026-11-10"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Apply the approved two-endpoint policy repair with immutable intent, exact change review and no mutation replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.command.entity-smoke.task-plan.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py
import argparse
import importlib.util
import json
from pathlib import Path
import re

SPEC = importlib.util.spec_from_file_location("entity_smoke_image_repair_common", Path(__file__).with_name("script.py"))
C = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(C)
STACK = "kanbien-core-platform-foundation"
LABEL = "entity-smoke-8f76ed3480e85d60fb60f547"
ENDPOINTS = {"EcrApiEndpoint", "EcrDkrEndpoint"}
FAILURE_ID = "es-4a34dceff456486cb2a33666613d6949"
FAILURE_HASH = "sha256:da7e03014d1be5c02205da7b536cf9f1a109a4d3372a212229f299fb961dc69b"
require = C.require
fingerprint = C.DEPLOY.fingerprint


def cache(): return C.ROOT / ".cache/entity-smoke-live" / LABEL / "image-delivery-repair"


def retain(name, value):
    path = cache() / name
    if not C.RESOURCE.write_exclusive(path, value):
        require(C.read_json(path) == value, "image-repair-retention-conflict")
    return value


def current(provider):
    stack = C.RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=STACK), "Stacks")
    arn = stack.get("StackId")
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:cloudformation:eu-west-1:337159794548:stack/" + STACK + r"/[a-f0-9-]+", arn)
            and stack.get("StackName") == STACK and {row.get("Key"): row.get("Value") for row in stack.get("Tags", [])}.get("Target") == "kanbien-core-platform", "image-repair-foundation-identity-invalid")
    rows = provider("cloudformation", "list-stack-resources", StackName=arn)
    require(not rows.get("NextToken") and isinstance(rows.get("StackResourceSummaries"), list), "image-repair-resource-inventory-incomplete")
    resources = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows["StackResourceSummaries"]}
    require(len(resources) == len(rows["StackResourceSummaries"]) == 25 and all(resources.get(name, {}).get("type") == "AWS::EC2::VPCEndpoint" for name in ENDPOINTS), "image-repair-resource-inventory-invalid")
    body = provider("cloudformation", "get-template", StackName=arn, TemplateStage="Original").get("TemplateBody")
    template = C.DEPLOY.CF.template(body)
    configuration = {"parameters": sorted(stack.get("Parameters", []), key=lambda row: row["ParameterKey"]), "tags": sorted(stack.get("Tags", []), key=lambda row: row["Key"]),
                     "role": stack.get("RoleARN"), "notifications": stack.get("NotificationARNs", [])}
    return stack, resources, template, fingerprint(configuration)


def check_state(plan, observed, template):
    stack, resources, actual, configuration = observed
    require(stack["StackId"] == plan["stack_arn"], "image-repair-foundation-incarnation-changed")
    require(resources == plan["resources"], "image-repair-resource-identities-changed")
    require(configuration == plan["configuration_sha256"], "image-repair-configuration-changed")
    require(C.DEPLOY.CF.templates_equal(actual, template), "image-repair-foundation-template-changed")


def prepare(receipt, provider):
    C.ALIGN.source_preflight(receipt)
    C.local_checks()
    caller = provider("sts", "get-caller-identity")
    require(caller.get("Account") == C.ALIGN.ACCOUNT, "image-repair-account-mismatch")
    head = C.ALIGN.command(["git", "rev-parse", "HEAD"]).strip()
    before, after = C.ALIGN.foundation_sources(receipt["source_revision"], head)
    retained = cache() / "plan.json"
    if retained.exists():
        plan = C.read_json(retained)
        require(plan.get("source_revision") == receipt["source_revision"] and plan.get("image_digest") == receipt["image_digest"]
                and plan.get("controller_sha256") == C.source_digest() and plan.get("before_sha256") == fingerprint(before)
                and plan.get("after_sha256") == fingerprint(after), "image-repair-original-plan-mismatch")
        return plan, before, after
    observed = current(provider)
    stack, resources, actual, configuration = observed
    require(stack.get("StackStatus") == "UPDATE_COMPLETE", "image-repair-foundation-not-ready")
    require(C.DEPLOY.CF.templates_equal(actual, before), "image-repair-original-template-mismatch")
    plan = {"schema": "deploy/entity-smoke-image-delivery-plan/v1", "account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION,
            "stack_arn": stack["StackId"], "source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"],
            "controller_sha256": C.source_digest(), "configuration_sha256": configuration, "resources": resources,
            "before_sha256": fingerprint(before), "after_sha256": fingerprint(after),
            "parameter_keys": sorted(row["ParameterKey"] for row in stack["Parameters"]), "modify": sorted(ENDPOINTS), "replace": [], "delete": [], "automatic_retry": False}
    return plan, before, after


def change_name(plan): return "entity-smoke-image-delivery-" + fingerprint(plan)[7:31]


def change_shape(value, plan, token):
    require(value.get("StackId") == plan["stack_arn"] and value.get("StackName") == STACK
            and value.get("ChangeSetName") == change_name(plan) and value.get("Description") == token and not value.get("NextToken"), "image-repair-change-identity-invalid")
    if value.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}: return False
    require(value.get("Status") == "CREATE_COMPLETE" and value.get("ExecutionStatus") == "AVAILABLE", "image-repair-change-not-available")
    changes = value.get("Changes")
    require(isinstance(changes, list) and len(changes) == 2, "image-repair-change-count-invalid")
    seen = set()
    for row in changes:
        item = row.get("ResourceChange", {})
        name = item.get("LogicalResourceId")
        require(name in ENDPOINTS and name not in seen and item.get("ResourceType") == "AWS::EC2::VPCEndpoint"
                and item.get("Action") == "Modify" and item.get("Replacement") == "False" and item.get("Scope") == ["Properties"]
                and item.get("PhysicalResourceId") == plan["resources"][name]["physical_id"], "image-repair-change-shape-invalid")
        details = item.get("Details")
        require(isinstance(details, list) and details and all(detail.get("Target", {}).get("Attribute") == "Properties"
                and detail["Target"].get("Name") == "PolicyDocument" and detail["Target"].get("RequiresRecreation") == "Never" for detail in details), "image-repair-change-property-invalid")
        seen.add(name)
    require(seen == ENDPOINTS, "image-repair-change-shape-invalid")
    return True


def reviewed(provider, plan, after):
    token = "es-image-review-" + fingerprint(plan)[7:39]
    value = provider("cloudformation", "describe-change-set", StackName=plan["stack_arn"], ChangeSetName=change_name(plan))
    if not change_shape(value, plan, token): return None
    body = provider("cloudformation", "get-template", StackName=plan["stack_arn"], ChangeSetName=value["ChangeSetId"], TemplateStage="Original")
    require(C.DEPLOY.CF.templates_equal(body.get("TemplateBody"), after), "image-repair-change-template-invalid")
    require(value.get("Capabilities") == ["CAPABILITY_NAMED_IAM"] and not value.get("IncludeNestedStacks", False)
            and not value.get("ImportExistingResources", False) and value.get("OnStackFailure") is None, "image-repair-change-options-invalid")
    return {"schema": "deploy/entity-smoke-image-delivery-review/v1", "plan_sha256": fingerprint(plan), "change_set_arn": value["ChangeSetId"], "review_token": token}


def submit(provider, operation, parameters):
    # Called only after exact checks and exclusive durable reservation below.
    provider.effect = "unknown-reconcile-only"
    return provider._invoke("cloudformation", operation, parameters)


def run(args, provider):
    receipt = C.ALIGN.read_receipt(args.receipt.absolute())
    plan, before, after = prepare(receipt, provider)
    digest = fingerprint(plan)
    if args.mode == "plan": return {"verdict": "planned", "plan_sha256": digest, "plan": plan}
    require(args.approved_plan == digest, "image-repair-approved-plan-mismatch")
    retain("plan.json", plan)
    review_intent = {"schema": "deploy/entity-smoke-image-delivery-intent/v1", "plan_sha256": digest, "operation": "create-change-set", "token": "es-image-review-" + digest[7:39]}
    if args.mode == "review":
        observed = current(provider); check_state(plan, observed, before)
        require(observed[0].get("StackStatus") == "UPDATE_COMPLETE", "image-repair-foundation-not-ready")
        if C.RESOURCE.write_exclusive(cache() / "review-intent.json", review_intent):
            submit(provider, "create-change-set", {"StackName": plan["stack_arn"], "ChangeSetName": change_name(plan), "ChangeSetType": "UPDATE",
                   "Description": review_intent["token"], "ClientToken": review_intent["token"], "TemplateBody": json.dumps(after),
                   "Parameters": [{"ParameterKey": name, "UsePreviousValue": True} for name in plan["parameter_keys"]], "Capabilities": ["CAPABILITY_NAMED_IAM"]})
        else: require(C.read_json(cache() / "review-intent.json") == review_intent, "image-repair-review-intent-mismatch")
        result = reviewed(provider, plan, after)
        if result is None: return {"verdict": "pending", "plan_sha256": digest, "next": "review"}
        retain("review.json", result)
        return {"verdict": "reviewed", "plan_sha256": digest, "modify": sorted(ENDPOINTS), "replace": [], "delete": []}
    review = C.read_json(cache() / "review.json")
    require(review.get("plan_sha256") == digest, "image-repair-review-mismatch")
    token = "es-image-execute-" + digest[7:39]
    intent = {"schema": "deploy/entity-smoke-image-delivery-intent/v1", "plan_sha256": digest, "operation": "execute-change-set", "token": token, "review_sha256": fingerprint(review)}
    target = cache() / "execute-intent.json"
    if not target.exists():
        require(args.mode == "execute", "image-repair-execution-intent-required")
        observed = current(provider); check_state(plan, observed, before)
        require(observed[0].get("StackStatus") == "UPDATE_COMPLETE" and reviewed(provider, plan, after) == review, "image-repair-review-changed")
        C.ALIGN.source_preflight(receipt)
        require(C.source_digest() == plan["controller_sha256"], "image-repair-source-changed")
        if C.RESOURCE.write_exclusive(target, intent):
            submit(provider, "execute-change-set", {"StackName": plan["stack_arn"], "ChangeSetName": review["change_set_arn"], "ClientRequestToken": token})
    require(C.read_json(target) == intent, "image-repair-execution-intent-mismatch")
    observed = current(provider)
    require(observed[0]["StackId"] == plan["stack_arn"], "image-repair-foundation-incarnation-changed")
    if observed[0].get("StackStatus") in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"}:
        return {"verdict": "pending", "plan_sha256": digest, "next": "reconcile"}
    require(observed[0].get("StackStatus") == "UPDATE_COMPLETE", "image-repair-update-not-successful")
    check_state(plan, observed, after)
    events = provider("cloudformation", "describe-stack-events", StackName=plan["stack_arn"])
    require(any(row.get("PhysicalResourceId") == plan["stack_arn"] and row.get("ClientRequestToken") == token and row.get("ResourceStatus") == "UPDATE_COMPLETE" for row in events.get("StackEvents", [])), "image-repair-terminal-token-missing")
    ids = {name: plan["resources"][name]["physical_id"] for name in ENDPOINTS}
    endpoints = provider("ec2", "describe-vpc-endpoints", VpcEndpointIds=list(ids.values())).get("VpcEndpoints", [])
    require(len(endpoints) == 2 and {row.get("VpcEndpointId") for row in endpoints} == set(ids.values()), "image-repair-endpoint-readback-missing")
    for name, identifier in ids.items():
        endpoint = next(row for row in endpoints if row["VpcEndpointId"] == identifier)
        require(endpoint.get("State") == "available", "image-repair-endpoint-not-available")
        C.ALIGN.image_delivery_policy(endpoint, name == "EcrApiEndpoint")
    completed = {"schema": "deploy/entity-smoke-image-delivery-receipt/v1", "plan_sha256": digest, "execution_sha256": fingerprint(intent),
                 "source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"], "before_sha256": plan["before_sha256"], "after_sha256": plan["after_sha256"], "resources_sha256": fingerprint(plan["resources"]), "terminal_token_confirmed": True}
    retain("receipt.json", completed)
    provider.effect = "original-update-completion-observed"
    return {"verdict": "completed", "receipt": str((cache() / "receipt.json").relative_to(C.ROOT)), "plan_sha256": digest}


def recovery_label(context, args, original):
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) != (LABEL, "administration", "bootstrap", "baseline"):
        return original
    # Exact observed failed attempt: this cannot become a caller-controlled retry.
    observation_path = context["cache"] / "diagnostics" / ("startup-failed-" + FAILURE_ID + ".json")
    require(C.digest_file(observation_path) == FAILURE_HASH, "image-repair-original-failure-changed")
    observed = C.read_json(observation_path)
    reservation = observed["reservation"]
    expected = {**context["binding"], "workload": "administration", "definition": context["checked"]["definition"],
                "security_group": context["checked"]["security_group"], "subnets": context["checked"]["subnets"],
                "environment": {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}, "deadline_seconds": 90, "proof_label": original}
    require(reservation["operation_id"] == FAILURE_ID and reservation["request"] == expected
            and observed["application_started"] is False and observed["task"]["stop_code"] == "TaskFailedToStart", "image-repair-original-failure-mismatch")
    require(C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts").read("original-preflight", expected) == reservation, "image-repair-original-reservation-mismatch")
    plan, receipt = C.read_json(cache() / "plan.json"), C.read_json(cache() / "receipt.json")
    execution = C.read_json(cache() / "execute-intent.json")
    require(receipt.get("schema") == "deploy/entity-smoke-image-delivery-receipt/v1" and receipt.get("plan_sha256") == fingerprint(plan)
            and receipt.get("execution_sha256") == fingerprint(execution) and receipt.get("terminal_token_confirmed") is True
            and receipt.get("source_revision") == expected["source_revision"] and receipt.get("image_digest") == expected["image_digest"], "image-repair-successful-receipt-required")
    return "entity-smoke-" + C.hashlib.sha256((original + ":" + FAILURE_ID + ":image-delivery-recovery-1").encode()).hexdigest()[:24]


def main():
    provider = C.Provider()
    try:
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.error = lambda message: (_ for _ in ()).throw(C.InfrastructureFailure("image-repair-arguments-invalid"))
        parser.add_argument("--receipt", type=Path, required=True)
        parser.add_argument("--mode", choices=("plan", "review", "execute", "reconcile"), required=True)
        parser.add_argument("--approved-plan")
        args = parser.parse_args()
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-image-delivery-report/v1", **result, "effect": provider.effect}, sort_keys=True)); return 0
    except Exception as failure:
        known = (C.InfrastructureFailure, C.ALIGN.AlignmentFailure, C.RESOURCE.ResourceFailure, C.RESOURCE.CONTROL.TaskFailure)
        print(json.dumps({"schema": "deploy/entity-smoke-image-delivery-report/v1", "verdict": "blocked", "condition": failure.code if isinstance(failure, known) else "image-repair-observation-not-confirmed", "effect": provider.effect})); return 1


if __name__ == "__main__": raise SystemExit(main())

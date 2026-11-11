#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.image-delivery-repair
#   version: 1
#   status: draft
#   created_on: "2026-11-10"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise exact policy repair, preserved resources, immutable submissions and fixed recovery provenance using controlled responses.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.target-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_IMAGE_REPAIR_ASSERTIONS_DISABLED")
spec = importlib.util.spec_from_file_location("image_repair_fixture", Path(__file__).with_name("image-delivery-repair.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
C = M.C
SOURCE = "8f76ed3480e85d60fb60f547f996628c8554504d"
BEFORE = C.DEPLOY.CF.template((C.ROOT / C.ALIGN.FOUNDATION).read_text())
# Reconstruct the exact pinned pre-repair fixture without requiring Git
# history in hosted shallow checkouts. This hash was independently obtained
# from SOURCE's original template, not from the reconstruction under test.
for endpoint in ("EcrApiEndpoint", "EcrDkrEndpoint"):
    statements = BEFORE["Resources"][endpoint]["Properties"]["PolicyDocument"]["Statement"]
    matches = [row for row in statements if row.get("Resource") == [
        {"Ref": "ExistingRepositoryArn"},
        {"Fn::Sub": "arn:aws:ecr:${AWS::Region}:${AWS::AccountId}:repository/kanbien-core-platform/entity-smoke"}]]
    assert len(matches) == 1
    matches[0]["Resource"] = {"Ref": "ExistingRepositoryArn"}
assert C.DEPLOY.fingerprint(BEFORE) == "sha256:aef24b28801c4ada9c405ec908d7c7151d12bb5f854d3734883f8da02b0b8997"
AFTER = C.ALIGN.repaired_foundation(BEFORE)
assert C.DEPLOY.CF.templates_equal(AFTER, (C.ROOT / C.ALIGN.FOUNDATION).read_text())


def fails(callback, code):
    try: callback()
    except Exception as failure: assert getattr(failure, "code", None) == code, (code, type(failure).__name__, str(failure))
    else: raise AssertionError(code)


for mutate in (lambda value: value["Resources"]["EcrApiEndpoint"]["Properties"].update(PrivateDnsEnabled=False),
               lambda value: value["Resources"]["EcrDkrEndpoint"]["Properties"]["PolicyDocument"]["Statement"][0].update(Resource="*"),
               lambda value: value.update(Description="unrelated-change")):
    changed = copy.deepcopy(AFTER); mutate(changed)
    with patch.object(C.ALIGN, "command", side_effect=lambda args: json.dumps(BEFORE if args[2].startswith(SOURCE + ":") else changed)):
        fails(lambda: C.ALIGN.foundation_sources(SOURCE, "b" * 40), "alignment-foundation-repair-invalid")


class Provider:
    def __init__(self):
        self.effect, self.calls, self.template, self.event, self.lost = "not-started", [], copy.deepcopy(BEFORE), None, None
        self.stack = {"StackId": "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-foundation/12345678-abcd", "StackName": M.STACK,
                      "StackStatus": "UPDATE_COMPLETE", "Tags": [{"Key": "Target", "Value": "kanbien-core-platform"}],
                      "Parameters": [{"ParameterKey": key, "ParameterValue": "****" if key == "CostAlertEmail" else "fixture-value"} for key in BEFORE["Parameters"]]}
        self.resources = [{"LogicalResourceId": name, "ResourceType": "AWS::EC2::VPCEndpoint", "PhysicalResourceId": "vpce-" + str(index).zfill(17)} for index, name in enumerate(sorted(M.ENDPOINTS))]
        self.resources += [{"LogicalResourceId": "Preserved" + str(index), "ResourceType": "AWS::Logs::LogGroup", "PhysicalResourceId": "existing-" + str(index)} for index in range(23)]
    def __call__(self, service, operation, **parameters):
        if operation == "get-caller-identity": return {"Account": C.ALIGN.ACCOUNT}
        if operation == "describe-stacks": return {"Stacks": [copy.deepcopy(self.stack)]}
        if operation == "list-stack-resources": return {"StackResourceSummaries": copy.deepcopy(self.resources)}
        if operation == "get-template": return {"TemplateBody": AFTER if "ChangeSetName" in parameters else self.template}
        if operation == "describe-change-set": return copy.deepcopy(self.change)
        if operation == "describe-stack-events": return {"StackEvents": [] if self.event is None else [self.event]}
        if operation == "describe-vpc-endpoints":
            rows = []
            for item in self.resources[:2]:
                statements = [{"Effect": "Allow", "Principal": "*", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"], "Resource": ["arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/" + name for name in ("core-server", "entity-smoke")]}]
                if item["LogicalResourceId"] == "EcrApiEndpoint": statements.append({"Effect": "Allow", "Principal": "*", "Action": "ecr:GetAuthorizationToken", "Resource": "*"})
                rows.append({"VpcEndpointId": item["PhysicalResourceId"], "State": "available", "PolicyDocument": {"Version": "2012-10-17", "Statement": statements}})
            return {"VpcEndpoints": rows}
        raise AssertionError(operation)
    def _invoke(self, service, operation, parameters):
        self.calls.append((operation, copy.deepcopy(parameters)))
        assert parameters["StackName"] == self.stack["StackId"]
        if operation == "create-change-set":
            assert all(row == {"ParameterKey": row["ParameterKey"], "UsePreviousValue": True} for row in parameters["Parameters"])
            self.change = {"StackId": self.stack["StackId"], "StackName": M.STACK, "ChangeSetName": parameters["ChangeSetName"], "ChangeSetId": "arn:fixture:change", "Description": parameters["Description"], "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Capabilities": ["CAPABILITY_NAMED_IAM"], "Changes": []}
            for item in self.resources[:2]: self.change["Changes"].append({"ResourceChange": {**item, "Action": "Modify", "Replacement": "False", "Scope": ["Properties"], "Details": [{"Target": {"Attribute": "Properties", "Name": "PolicyDocument", "RequiresRecreation": "Never"}}]}})
        elif operation == "execute-change-set":
            self.template = copy.deepcopy(AFTER)
            self.event = {"PhysicalResourceId": self.stack["StackId"], "ClientRequestToken": parameters["ClientRequestToken"], "ResourceStatus": "UPDATE_COMPLETE"}
        else: raise AssertionError(operation)
        if self.lost == operation: self.lost = None; raise OSError("native-credential-canary")
        return {}


for lost in (None, "create-change-set", "execute-change-set"):
    with tempfile.TemporaryDirectory(prefix="entity-image-repair-") as temporary:
        root = Path(temporary)
        receipt = {"source_revision": SOURCE, "image_digest": "sha256:" + "a" * 64}
        with patch.object(C, "ROOT", root), patch.object(C.ALIGN, "read_receipt", return_value=receipt), patch.object(C.ALIGN, "source_preflight"), patch.object(C, "local_checks"), \
             patch.object(C.ALIGN, "command", return_value="b" * 40), patch.object(C.ALIGN, "foundation_sources", return_value=(BEFORE, AFTER)), patch.object(C, "source_digest", return_value="sha256:" + "c" * 64):
            provider = Provider(); provider.lost = lost
            args = SimpleNamespace(receipt=root / "custody.json", mode="plan", approved_plan=None)
            planned = M.run(args, provider); assert provider.calls == []
            args.mode, args.approved_plan = "review", "sha256:" + "0" * 64
            fails(lambda: M.run(args, provider), "image-repair-approved-plan-mismatch"); assert provider.calls == []
            args.approved_plan = planned["plan_sha256"]
            if lost == "create-change-set":
                try: M.run(args, provider)
                except OSError: pass
                else: raise AssertionError("lost review not exercised")
            assert M.run(args, provider)["verdict"] == "reviewed"
            for mutate, condition in ((lambda value: value["Changes"].pop(), "image-repair-change-count-invalid"),
                                      (lambda value: value["Changes"][0]["ResourceChange"].update(Replacement="True"), "image-repair-change-shape-invalid"),
                                      (lambda value: value["Changes"][0]["ResourceChange"]["Details"][0]["Target"].update(Name="SubnetIds"), "image-repair-change-property-invalid")):
                changed = copy.deepcopy(provider.change); mutate(changed)
                fails(lambda: M.change_shape(changed, planned["plan"], provider.change["Description"]), condition)
            args.mode = "execute"
            if lost == "execute-change-set":
                try: M.run(args, provider)
                except OSError: pass
                else: raise AssertionError("lost execution not exercised")
            assert M.run(args, provider)["verdict"] == "completed"
            args.mode = "reconcile"
            assert M.run(args, provider)["verdict"] == "completed"
            assert [name for name, _ in provider.calls] == ["create-change-set", "execute-change-set"]
            provider.resources[-1]["PhysicalResourceId"] = "replaced"
            fails(lambda: M.run(args, provider), "image-repair-resource-identities-changed")

with tempfile.TemporaryDirectory(prefix="entity-image-recovery-") as temporary:
    root = Path(temporary)
    args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="bootstrap", proof_stage="baseline", phase="preflight")
    original = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":administration:bootstrap:preflight").encode()).hexdigest()[:24]
    binding = {"proof_label": M.LABEL, "source_revision": SOURCE, "image_digest": "sha256:" + "a" * 64,
               **{name: "sha256:" + "b" * 64 for name in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}}
    checked = {"definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-administration:1", "security_group": "sg-" + "1" * 17, "subnets": ["subnet-" + "2" * 17]}
    context = {"cache": root / ".cache/entity-smoke-live" / M.LABEL, "binding": binding, "checked": checked}
    request = {**binding, **checked, "workload": "administration", "environment": {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}, "deadline_seconds": 90, "proof_label": original}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "request": request, "request_sha256": C.hashlib.sha256(C.RESOURCE.CONTROL.canonical(request)).hexdigest(), "operation_id": M.FAILURE_ID, "reserved_at": "2026-11-10T19:11:29+00:00"}
    observation = {"reservation": reservation, "application_started": False, "task": {"stop_code": "TaskFailedToStart"}}
    observation_path = context["cache"] / "diagnostics" / ("startup-failed-" + M.FAILURE_ID + ".json")
    C.RESOURCE.write_exclusive(observation_path, observation)
    store = C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    C.RESOURCE.write_exclusive(store.path_for("original", request), reservation)
    original_bytes = store.path_for("original", request).read_bytes()
    with patch.object(C, "ROOT", root), patch.object(M, "FAILURE_HASH", C.digest_file(observation_path)):
        plan, execution = {"fixture": "reviewed-plan"}, {"fixture": "executed-intent"}
        M.retain("plan.json", plan); M.retain("execute-intent.json", execution)
        fails(lambda: M.recovery_label(context, args, original), "infrastructure-input-unavailable")
        M.retain("receipt.json", {"schema": "deploy/entity-smoke-image-delivery-receipt/v1", "plan_sha256": M.fingerprint(plan), "execution_sha256": M.fingerprint(execution), "terminal_token_confirmed": True, "source_revision": SOURCE, "image_digest": binding["image_digest"]})
        recovery = M.recovery_label(context, args, original)
        acceptance_spec = importlib.util.spec_from_file_location("image_repair_acceptance_label_fixture", Path(__file__).with_name("acceptance-evidence.py"))
        acceptance = importlib.util.module_from_spec(acceptance_spec); acceptance_spec.loader.exec_module(acceptance)
        assert acceptance.preflight_label(binding, "baseline", "administration", "bootstrap") == recovery
        for stage, workload, operation in (("credential-recovery", "administration", "bootstrap"), ("baseline", "migration", "apply")):
            suffix = "" if stage == "baseline" else ":" + stage
            ordinary = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":" + workload + ":" + operation + ":preflight" + suffix).encode()).hexdigest()[:24]
            assert acceptance.preflight_label(binding, stage, workload, operation) == ordinary
        grant_original = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":administration:grant-runtime:preflight").encode()).hexdigest()[:24]
        grant_args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="grant-runtime", proof_stage="baseline")
        assert acceptance.preflight_label(binding, "baseline", "administration", "grant-runtime") == C.TRANSITION.replacement_label({}, grant_args, grant_original)
        assert recovery != original and M.recovery_label(context, SimpleNamespace(**{**vars(args), "phase": "operation"}), original) == recovery
        assert store.path_for("recovery", {**request, "proof_label": recovery}) != store.path_for("original", request)
        assert store.path_for("original", request).read_bytes() == original_bytes
        fails(lambda: M.recovery_label({**context, "checked": {**checked, "security_group": "sg-" + "3" * 17}}, args, original), "image-repair-original-failure-mismatch")
        with patch.object(M, "FAILURE_HASH", "sha256:" + "0" * 64):
            fails(lambda: M.recovery_label(context, args, original), "image-repair-original-failure-changed")

print(json.dumps({"schema": "deploy/entity-smoke-image-repair-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "checks": ["two-policy-source-delta", "whole-template-preservation", "exact-change-shape", "previous-parameters", "immutable-intent", "lost-review-no-replay", "lost-execute-no-replay", "terminal-token-and-policy-readback", "resource-replacement-rejected"]}))

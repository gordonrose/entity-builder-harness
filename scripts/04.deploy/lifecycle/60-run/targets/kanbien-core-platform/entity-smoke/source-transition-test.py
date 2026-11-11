#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.source-transition
#   version: 1
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject unreviewed image transitions, changed historical evidence and mutation replay using controlled provider fixtures, not live proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from contextlib import ExitStack
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_SOURCE_TRANSITION_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_source_transition_test", DIRECTORY / "source-transition.py")
C = module("entity_smoke_source_transition_common_test", DIRECTORY / "script.py")
before = {"source_revision": M.OLD_SOURCE, "image_digest": M.OLD_IMAGE, "proof_label": M.LABEL,
          "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64,
          "dependency_incarnation_sha256": "sha256:" + "e" * 64}
after = {**before, "source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64}
resources = {name: {"type": kind, "physical_id": "owned-" + name + ":1"} for name, kind in C.DEPLOY.RESOURCE_TYPES.items()}
successors = {name: {**row, "physical_id": row["physical_id"][:-1] + "2"} if name in M.TASK_DEFINITIONS else copy.deepcopy(row) for name, row in resources.items()}
plan = {"binding": after, "previous_binding": before, "resources": resources, "desired_count": 0, "automatic_retry": False, "controller_sha256": "sha256:" + "f" * 64,
        "stack_arn": "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-entity-smoke/11111111-1111-1111-1111-111111111111", "parameters": {"ServerDesiredCount": "0"}}
digest = C.DEPLOY.fingerprint(plan)
receipt = {"schema": "deploy/entity-smoke-source-transition/v1", "plan": plan, "plan_sha256": digest, "resources": successors,
           "terminal_token": "es-source-execute-" + digest[7:39], "completed_at": "2026-11-11T10:00:00Z"}
with tempfile.TemporaryDirectory(prefix="entity-smoke-transition-gate-") as gate_root:
    gate_path = M.gates(C, Path(gate_root), plan, "controlled-execution")
    receipt.update(graph=M.graph(C), gate=C.read_json(gate_path))


def fails(call, expected):
    try: call()
    except (C.InfrastructureFailure, C.RESOURCE.ResourceFailure) as failure:
        assert failure.code == expected, (failure.code, expected)
    else: raise AssertionError("expected source transition rejection")


assert M.validate(C, receipt, after) == receipt
for key in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "proof_label"):
    changed = {**after, key: ("entity-smoke-" + "1" * 24) if key == "proof_label" else "sha256:" + "1" * 64}
    fails(lambda: M.compatible(C, before, changed), "source-transition-binding-incompatible")
fails(lambda: M.compatible(C, before, before), "source-transition-binding-incompatible")
for name in resources:
    broken = copy.deepcopy(receipt)
    broken["resources"][name]["physical_id"] = resources[name]["physical_id"] if name in M.TASK_DEFINITIONS else "different-resource"
    fails(lambda: M.validate(C, broken, after), "source-transition-resource-identity-invalid")
for field, value in (("terminal_token", "other-token"), ("plan_sha256", "sha256:" + "0" * 64)):
    fails(lambda: M.validate(C, {**receipt, field: value}, after), "source-transition-terminal-token-invalid" if field == "terminal_token" else "source-transition-plan-mismatch")

class Provider:
    def __init__(self):
        self.value = {"StackId": plan["stack_arn"], "ChangeSetId": "owned-change", "ChangeSetName": "entity-smoke-source-" + digest[7:31],
                      "Description": "es-source-review-" + digest[7:39], "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Capabilities": ["CAPABILITY_IAM"],
                      "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in plan["parameters"].items()], "Changes": []}
        for name in sorted(M.TASK_DEFINITIONS | {"FeatureService"}):
            self.value["Changes"].append({"ResourceChange": {"LogicalResourceId": name, "PhysicalResourceId": resources[name]["physical_id"], "ResourceType": resources[name]["type"],
                "Action": "Modify", "Replacement": "True" if name in M.TASK_DEFINITIONS else "False", "Scope": ["Properties"],
                "Details": [{"Target": {"Attribute": "Properties", "Name": "ContainerDefinitions" if name in M.TASK_DEFINITIONS else "TaskDefinition"}}]}})
        self.calls = []
    def __call__(self, service, operation, **parameters):
        self.calls.append((service, operation, parameters))
        if operation == "describe-change-set": return copy.deepcopy(self.value)
        assert operation == "get-template"
        return {"TemplateBody": C.DEPLOY.source()[0]}

provider = Provider()
assert M.change(C, provider, plan) == "owned-change"
assert all(operation in {"describe-change-set", "get-template"} for _, operation, _ in provider.calls)
for field, value in (("Action", "Remove"), ("LogicalResourceId", "MigrationTaskRole"), ("PhysicalResourceId", "not-owned"), ("Replacement", "Conditional")):
    altered = Provider(); altered.value["Changes"][0]["ResourceChange"][field] = value
    fails(lambda: M.change(C, altered, plan), "source-transition-change-shape-invalid")
altered = Provider(); altered.value["Changes"][0]["ResourceChange"]["Details"][0]["Target"]["Name"] = "TaskRoleArn"
fails(lambda: M.change(C, altered, plan), "source-transition-change-property-invalid")
altered = Provider(); altered.value["Parameters"][0]["ParameterValue"] = "1"
fails(lambda: M.change(C, altered, plan), "deployment-provider-parameters-mismatch")
altered = Provider(); altered.value["Status"] = "CREATE_IN_PROGRESS"
assert M.change(C, altered, plan) is None

# Only exact pinned preparation bytes may be historical; no arbitrary receipt
# is trusted merely for carrying a former source or a valid-looking gate.
assert M.controller({}, {}, "current") == "current"
packet, completion = {"binding": before, "reservation": {"request": {"definition": "old-definition", "security_group": "old-group", "subnets": ["old-subnet"], "proof_label": "old-preflight"}}}, {"gate": "controlled-original"}
pin = M.document(packet); old_pins = M.PINS
M.PINS = {pin: (M.document(completion), "f" * 64)}
assert M.historical(packet, completion)
assert not M.historical({**packet, "unreviewed": True}, completion)
assert not M.historical(packet, {**completion, "gate": "restamped"})
route = SimpleNamespace(C=C)
context = {"binding": before, "checked": {}, "cache": Path("/not-used")}
legacy = M.legacy_context(route, context, None, packet, completion)
assert legacy["checked"]["definition"] == "old-definition" and legacy["binding"] == before
assert M.legacy_context(route, context, None, packet, {"gate": "wrong"}) is None
M.PINS = old_pins
args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="grant-runtime", proof_stage="baseline")
label = M.replacement_label({}, args, "original")
assert label != "original" and M.replacement_label({}, args, "original") == label
assert M.replacement_label({}, SimpleNamespace(**{**vars(args), "operation": "bootstrap"}), "original") == "original"

# Run the complete public coordinator with retained single-submission intent.
# Source/identity/alignment are controlled prerequisites; real file retention,
# change review and generic gate validation remain exercised.
class ExecutionProvider(Provider):
    def __init__(self):
        super().__init__()
        self.effect = "not-started"
        self.stack_status, self.updated, self.token = "CREATE_COMPLETE", False, None
        self.submissions = []
        self.lose_review, self.lose_execution = True, True
    def _invoke(self, service, operation, parameters):
        self.submissions.append(operation)
        if operation == "create-change-set":
            self.value.update(ChangeSetName=parameters["ChangeSetName"], Description=parameters["Description"], Parameters=parameters["Parameters"])
            if self.lose_review: raise OSError("sensitive-response-canary")
        elif operation == "execute-change-set":
            self.updated = True; self.stack_status = "UPDATE_COMPLETE"; self.token = parameters["ClientRequestToken"]
            if self.lose_execution: raise OSError("sensitive-response-canary")
        else: raise AssertionError(operation)
        return {}
    def __call__(self, service, operation, **parameters):
        if operation == "validate-template": return {"Parameters": [{"ParameterKey": name} for name in C.DEPLOY.PARAMETERS], "Capabilities": ["CAPABILITY_IAM"]}
        if operation == "describe-stacks": return {"Stacks": [{"StackId": plan["stack_arn"], "StackStatus": self.stack_status}]}
        if operation == "describe-stack-events": return {"StackEvents": [{"PhysicalResourceId": plan["stack_arn"], "ClientRequestToken": self.token, "ResourceStatus": self.stack_status}]}
        return super().__call__(service, operation, **parameters)

with tempfile.TemporaryDirectory(prefix="entity-smoke-source-transition-") as temporary, ExitStack() as patches:
    root = Path(temporary)
    cache = root / ".cache/entity-smoke-live" / M.LABEL
    created = {"binding": before, "result": {"facts": {"resources": resources, "stack_arn": plan["stack_arn"]}}}
    C.RESOURCE.write_exclusive(cache / "receipts/create.json", created)
    custody = {"source_revision": after["source_revision"], "image_digest": after["image_digest"], "receipt_reference": "fixture:qualified-image"}
    source_files = {name: (C.ROOT / "infra/04.deploy/03.product/entrypoints/entity-smoke" / name).read_text() for name in ("administration.ts", "preflight.ts")}
    actual_digest = C.digest_file
    actual_module, readbacks = C.module, []
    def selected_module(name, path):
        if path.name == "task-binding.py":
            return SimpleNamespace(inspect=lambda provider, workload, parameters, selected, source: readbacks.append((workload, copy.deepcopy(selected))))
        return actual_module(name, path)
    def digest_file(path):
        relative = str(path.relative_to(cache)) if path.is_relative_to(cache) else None
        program = str(path.relative_to(root)) if path.is_relative_to(root) else None
        if program in M.RECOVERY_PROGRAMS: return "sha256:" + M.RECOVERY_PROGRAMS[program]
        return "sha256:" + M.RECOVERY[relative] if relative in M.RECOVERY else actual_digest(path)
    def command(arguments):
        if arguments[:2] == ["git", "diff"]: return "\n".join("infra/04.deploy/03.product/entrypoints/entity-smoke/" + name for name in source_files)
        assert arguments[:2] == ["git", "show"]
        return source_files[arguments[2].rsplit("/", 1)[1]]
    def inventory(common, provider, binding, parameters):
        assert binding == (after if provider.updated else before)
        return {"StackId": plan["stack_arn"], "StackStatus": provider.stack_status}, copy.deepcopy(successors if provider.updated else resources)
    for owner, name, value in ((C, "ROOT", root), (C, "local_checks", lambda: None), (C, "source_digest", lambda: "sha256:" + "f" * 64),
            (C, "operator_preflight", lambda provider: "sha256:" + "1" * 64), (C, "binding_for", lambda receipt, alignment: {key: value for key, value in after.items() if key != "proof_label"}),
            (C, "digest_file", digest_file), (C, "module", selected_module), (C.ALIGN, "read_receipt", lambda path: custody), (C.ALIGN, "source_preflight", lambda receipt: None),
            (C.ALIGN, "inspect", lambda *args: ({}, {"ServerDesiredCount": "0"}, None)), (C.ALIGN, "command", command), (M, "inventory", inventory)):
        patches.enter_context(patch.object(owner, name, value))
    provider = ExecutionProvider()
    args = SimpleNamespace(receipt=root / "custody.json", mode="plan", approved_plan=None)
    planned = M.run(C, args, provider)
    assert not provider.submissions and planned["verdict"] == "planned"
    args.mode = "review"; args.approved_plan = "sha256:" + "0" * 64
    fails(lambda: M.run(C, args, provider), "source-transition-approved-plan-mismatch")
    args.approved_plan = planned["plan_sha256"]
    try: M.run(C, args, provider)
    except OSError: pass
    else: raise AssertionError("expected lost review response")
    assert M.run(C, args, provider)["verdict"] == "reviewed" and provider.submissions == ["create-change-set"]
    args.mode = "execute"
    try: M.run(C, args, provider)
    except OSError: pass
    else: raise AssertionError("expected lost execution response")
    args.mode = "reconcile"
    assert M.run(C, args, provider)["verdict"] == "completed"
    assert M.run(C, args, provider)["verdict"] == "completed"
    assert provider.submissions == ["create-change-set", "execute-change-set"]
    assert len(readbacks) == 10 and {workload for workload, _ in readbacks} == {"server", "migration", "administration", "verifier", "database-proof"}
    assert all(selected == successors for _, selected in readbacks)
    assert M.read(C, cache, after)["resources"] == successors
print("ENTITY_SMOKE_SOURCE_TRANSITION_CONTROLS_PASSED")

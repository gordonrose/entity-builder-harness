#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.foundation-access-update
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.foundation-access
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove exact permission scope, original-intent recovery and readback using controlled providers and the real reservation owner.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.capability.foundation-access-update
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/foundation-access-update/script.py
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("foundation_access", Path(__file__).with_name("script.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def rejected(call, code):
    try:
        call()
    except (M.Failure, M.CHANGES.ChangeSetFailure, M.RESERVATIONS.ReservationFailure) as failure:
        assert failure.code == code, (failure.code, code)
    else:
        raise AssertionError("expected " + code)


def fixture():
    selected = M.binding()
    after = M.CF.template((M.ROOT / selected["template"]).read_text())
    before = copy.deepcopy(after)
    M.statement(M.policy(before, selected), {"Ref": selected["resource_parameter"]})["Action"].remove(selected["action"])
    source = {"revision": "a" * 40, "predecessor": "b" * 40, "identities": {"fixture": "c" * 64},
              "before_sha256": M.digest(before), "after_sha256": M.digest(after)}
    return selected, before, after, source


class Provider:
    def __init__(self, selected, before, after):
        self.selected, self.before, self.after = selected, before, after
        self.parameters = {key: "fixture" for key in before["Parameters"]}
        self.parameters.update(ExistingRepositoryArn="arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/core-server",
                               CostAlertEmail="****", EnableTargetBudget="true")
        self.stack_id = "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-foundation/fixture"
        self.resources = [{"LogicalResourceId": "DeliveryRole", "PhysicalResourceId": "github-kanbien-core-platform-delivery", "ResourceType": "AWS::IAM::Role"},
                          {"LogicalResourceId": "SharedEndpoint", "PhysicalResourceId": "vpce-fixture", "ResourceType": "AWS::EC2::VPCEndpoint"}]
        self.role = {"RoleName": "github-kanbien-core-platform-delivery", "RoleId": "AROA-FIXTURE",
            "Arn": "arn:aws:iam::337159794548:role/github-kanbien-core-platform-delivery", "Path": "/",
            "AssumeRolePolicyDocument": {"Version": "2012-10-17", "Statement": []}, "MaxSessionDuration": 3600,
            "Tags": [{"Key": "Target", "Value": "kanbien-core-platform"}]}
        self.change, self.events, self.executed, self.calls = None, [], False, []
        self.status, self.loss, self.pending = "UPDATE_COMPLETE", None, False

    def __call__(self, service, operation, **arguments):
        self.calls.append((service, operation, copy.deepcopy(arguments)))
        if operation == "describe-stacks":
            return {"Stacks": [{"StackId": self.stack_id, "StackName": self.selected["stack"], "StackStatus": self.status,
                "Tags": [{"Key": "Target", "Value": self.selected["target"]}],
                "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in self.parameters.items()]}]}
        if operation == "list-stack-resources":
            return {"StackResourceSummaries": copy.deepcopy(self.resources)}
        if operation == "get-template":
            return {"TemplateBody": copy.deepcopy(self.after if self.executed or "ChangeSetName" in arguments else self.before)}
        if operation == "get-role":
            return {"Role": copy.deepcopy(self.role)}
        if operation == "list-role-policies":
            return {"PolicyNames": [self.selected["policy_name"]]}
        if operation == "list-attached-role-policies":
            return {"AttachedPolicies": []}
        if operation == "get-role-policy":
            return {"RoleName": self.role["RoleName"], "PolicyName": self.selected["policy_name"],
                    "PolicyDocument": M.resolved_policy(self.after if self.executed else self.before, self.selected, self.parameters)}
        if operation == "describe-change-set":
            if self.change is None:
                raise M.Failure("aws-resource-missing")
            return copy.deepcopy(self.change)
        if operation == "create-change-set":
            assert arguments["Parameters"] == [{"ParameterKey": key, "UsePreviousValue": True} for key in sorted(self.parameters)]
            assert "****" not in json.dumps(arguments)
            assert set(arguments) == {"StackName", "ChangeSetName", "ChangeSetType", "TemplateBody", "Parameters", "Capabilities", "ClientToken", "Description"}
            assert arguments["ClientToken"] == arguments["Description"]
            self.change = {"StackId": self.stack_id, "ChangeSetName": arguments["ChangeSetName"], "Description": arguments["Description"],
                "ChangeSetType": "UPDATE", "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Capabilities": arguments["Capabilities"],
                "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in self.parameters.items()],
                "Changes": [{"ResourceChange": {"Action": "Modify", "LogicalResourceId": "DeliveryRole", "ResourceType": "AWS::IAM::Role",
                    "PhysicalResourceId": self.role["RoleName"],
                    "Replacement": "False", "Scope": ["Properties"], "Details": [{"Target": {"Attribute": "Properties", "Name": "Policies", "RequiresRecreation": "Never"}}]}}]}
            if self.loss == "prepare":
                raise TimeoutError("private-canary")
            return {}
        if operation == "execute-change-set":
            assert set(arguments) == {"StackName", "ChangeSetName", "ClientRequestToken"}
            self.executed = True
            self.change["ExecutionStatus"] = "EXECUTE_COMPLETE"
            self.events = [{"PhysicalResourceId": self.stack_id, "ClientRequestToken": arguments["ClientRequestToken"], "ResourceStatus": "UPDATE_COMPLETE"}]
            if self.loss == "execute":
                raise TimeoutError("private-canary")
            return {}
        if operation == "describe-stack-events":
            return {"StackEvents": copy.deepcopy(self.events)}
        raise AssertionError((service, operation))

    def writes(self):
        return [item for item in self.calls if item[1] in {"create-change-set", "execute-change-set"}]


def setup(directory):
    selected, before, after, source = fixture()
    provider = Provider(selected, before, after)
    intent = M.make_intent(provider, selected, source, before, after)
    store = M.Store(Path(directory))
    return provider, store, selected, intent, before, after


def run(values, action, approved=True):
    provider, store, selected, intent, before, after = values
    return M.control(provider, store, selected, intent, before, after, action, M.digest(intent) if approved else None)


def test_source_and_declaration():
    selected, before, after, source = fixture()
    assert M.source_delta(before, after, selected) == (before, after)
    access = M.CF.template((M.ROOT / M.ACCESS).read_text())
    assert M.DECLARATION.check_access_maintenance(access)["action"] == selected["action"]
    for key, value in (("action", "ecr:*"), ("resource_parameter", "AnotherRepository"), ("logical_resource", "TaskExecutionRole")):
        wrong = copy.deepcopy(access)
        wrong["maintenance"]["delivery-repository-observation"][key] = value
        try:
            M.DECLARATION.check_access_maintenance(wrong)
        except M.DECLARATION.DeclarationFailure as failure:
            assert failure.codes == ("technical-access-maintenance-invalid",)
        else:
            raise AssertionError("unowned declaration accepted")
    for mutate in (
        lambda doc: doc["Resources"]["DeliveryRole"]["Properties"].update(RoleName="another-role"),
        lambda doc: doc["Parameters"]["EnableTargetBudget"].update(Default="true"),
        lambda doc: M.statement(M.policy(doc, selected), {"Ref": "ExistingRepositoryArn"})["Action"].append("ecr:DeleteRepository"),
        lambda doc: doc["Resources"].pop("Budget"),
    ):
        wrong = copy.deepcopy(after); mutate(wrong)
        rejected(lambda: M.source_delta(before, wrong, selected), "foundation-source-change-outside-scope")
    wrong = copy.deepcopy(after)
    M.statement(M.policy(wrong, selected), {"Ref": "ExistingRepositoryArn"})["Resource"] = "*"
    rejected(lambda: M.source_delta(before, wrong, selected), "repository-statement-invalid")
    rejected(lambda: M.source_delta(after, after, selected), "permission-addition-invalid")
    with patch.object(M, "git", side_effect=lambda *args, **kwargs: "a" * 40 if args[:2] == ("rev-parse", "HEAD") else " M private-canary"):
        rejected(lambda: M.sources(selected, "b" * 40), "source-not-clean-committed")


def test_connected_and_uncertain():
    for loss in (None, "prepare", "execute"):
        with tempfile.TemporaryDirectory() as directory:
            values = setup(directory)
            provider, store, selected, intent, before, after = values
            rejected(lambda: run(values, "prepare", False), "approved-plan-mismatch")
            assert not provider.writes()
            provider.loss = loss
            if loss == "prepare":
                rejected(lambda: run(values, "prepare"), "create-change-set-submission-uncertain")
            else:
                assert run(values, "prepare")["verdict"] == "reviewed"
            assert run(values, "prepare")["verdict"] == "reviewed"
            assert len(provider.writes()) == 1
            if loss == "execute":
                rejected(lambda: run(values, "execute"), "execute-change-set-submission-uncertain")
            else:
                assert run(values, "execute")["verdict"] == "completed"
            original = (Path(directory) / "execute.json").read_bytes()
            # Reconstructed process uses the original token; the live predecessor
            # no longer exists, so this also detects wrong gate ordering.
            new_values = (provider, M.Store(Path(directory)), selected, intent, before, after)
            assert run(new_values, "execute")["verdict"] == "completed"
            assert run(new_values, "observe")["verdict"] == "completed"
            assert len(provider.writes()) == 2
            assert (Path(directory) / "execute.json").read_bytes() == original
            altered = copy.deepcopy(intent); altered["source"]["revision"] = "d" * 40
            rejected(lambda: M.control(provider, store, selected, altered, before, after, "execute", M.digest(altered)), "reservation-reservation-mismatch")
            assert len(provider.writes()) == 2


def test_review_and_readback():
    changes = (
        (lambda change: change.update(StackId="another-stack"), "change-set-lineage-mismatch"),
        (lambda change: change.update(Description="another-token"), "change-set-lineage-mismatch"),
        (lambda change: change["Parameters"].append(copy.deepcopy(change["Parameters"][0])), "change-set-parameters-mismatch"),
        (lambda change: change["Parameters"][0].update(ParameterValue="changed"), "change-set-parameters-mismatch"),
        (lambda change: change.update(Capabilities=["CAPABILITY_IAM"]), "change-set-capabilities-mismatch"),
        (lambda change: change["Changes"].append(copy.deepcopy(change["Changes"][0])), "change-set-scope-invalid"),
        (lambda change: change["Changes"][0]["ResourceChange"].update(Replacement="Conditional"), "change-set-scope-invalid"),
        (lambda change: change["Changes"][0]["ResourceChange"].pop("Replacement"), "change-set-scope-invalid"),
        (lambda change: change["Changes"][0]["ResourceChange"].update(Action="Remove"), "change-set-scope-invalid"),
        (lambda change: change["Changes"][0]["ResourceChange"].update(PhysicalResourceId="foreign-role"), "change-set-scope-invalid"),
        (lambda change: change["Changes"][0]["ResourceChange"]["Details"][0]["Target"].update(Name="AssumeRolePolicyDocument"), "change-set-property-invalid"),
    )
    for mutate, code in changes:
        with tempfile.TemporaryDirectory() as directory:
            values = setup(directory); run(values, "prepare")
            mutate(values[0].change)
            rejected(lambda: run(values, "execute"), code)
            assert len(values[0].writes()) == 1
    for mutate, code in (
        (lambda provider: provider.events[0].update(ClientRequestToken="foreign"), "execution-lineage-not-observed"),
        (lambda provider: provider.events[0].update(ResourceStatus="UPDATE_IN_PROGRESS"), "execution-completion-not-observed"),
        (lambda provider: provider.role.update(RoleId="replacement"), "foundation-role-changed"),
        (lambda provider: provider.resources[1].update(PhysicalResourceId="replacement"), "foundation-resources-changed"),
        (lambda provider: provider.parameters.update(VpcId="changed"), "foundation-parameters-changed"),
    ):
        with tempfile.TemporaryDirectory() as directory:
            values = setup(directory); run(values, "prepare"); run(values, "execute")
            mutate(values[0])
            rejected(lambda: run(values, "observe"), code)
            assert len(values[0].writes()) == 2


def test_original_intent_and_provider():
    for mutate, code in (
        (lambda response: response["Stacks"][0].update(StackId="foreign-stack"), "stack-identity-mismatch"),
        (lambda response: response["Stacks"][0].update(Tags=[]), "stack-target-tag-mismatch"),
        (lambda response: response["Stacks"][0].update(StackStatus="UPDATE_IN_PROGRESS"), "foundation-stack-not-stable"),
        (lambda response: response["Stacks"][0]["Parameters"].append(copy.deepcopy(response["Stacks"][0]["Parameters"][0])), "foundation-parameters-invalid"),
    ):
        selected, before, after, source = fixture()
        provider = Provider(selected, before, after)
        def wrong(service, operation, **arguments):
            response = provider(service, operation, **arguments)
            if operation == "describe-stacks":
                mutate(response)
            return response
        rejected(lambda: M.make_intent(wrong, selected, source, before, after), code)
        assert not provider.writes()
    with tempfile.TemporaryDirectory() as directory:
        values = setup(directory)
        provider, store, selected, intent, before, after = values
        store.reserve("execute", {"intent_sha256": M.digest(intent)})
        rejected(lambda: run(values, "observe"), "execution-reservation-orphaned")
        assert not provider.writes()
    with tempfile.TemporaryDirectory() as directory:
        values = setup(directory); run(values, "prepare"); run(values, "execute")
        values[0].status = "UPDATE_ROLLBACK_COMPLETE"
        assert run(values, "observe")["verdict"] == "failed"
        values[0].status = "UPDATE_ROLLBACK_IN_PROGRESS"
        assert run(values, "observe")["verdict"] == "pending"
        assert len(values[0].writes()) == 2
    with tempfile.TemporaryDirectory() as directory:
        values = setup(directory)
        values[0].change = {"Status": "CREATE_COMPLETE"}
        rejected(lambda: run(values, "prepare"), "unowned-change-set")
        assert not values[0].writes()
    with tempfile.TemporaryDirectory() as directory:
        values = setup(directory)
        selected, source = values[2], values[3]["source"]
        assert M.validate_intent(values[3], selected, source) == values[3]
        wrong = copy.deepcopy(values[3]); wrong["source"]["revision"] = "f" * 40
        rejected(lambda: M.validate_intent(wrong, selected, source), "retained-intent-mismatch")
        wrong = copy.deepcopy(values[3]); wrong["change_set"] = "alternate-attempt"
        rejected(lambda: M.validate_intent(wrong, selected, source), "retained-operation-mismatch")
    selected, *_ = fixture()
    with patch.object(M.RESPONSE, "inventory_covered", return_value=True), patch.object(M.CLI, "invoke_json", return_value={"Account": "999999999999"}) as invoke:
        rejected(lambda: M.Provider(selected)("cloudformation", "describe-stacks", StackName=selected["stack"]), "provider-account-mismatch")
        assert invoke.call_count == 1
        assert invoke.call_args.kwargs["environment"]["AWS_MAX_ATTEMPTS"] == "1"
    with patch.object(M.RESPONSE, "inventory_covered", return_value=False), patch.object(M.CLI, "invoke_json") as invoke:
        rejected(lambda: M.Provider(selected)("sts", "get-caller-identity"), "delivery-inventory-not-covered")
        invoke.assert_not_called()
    pages = iter([{"StackEvents": [{"event": 1}], "NextToken": "next"}, {"StackEvents": [{"event": 2}]}])
    assert M.rows(lambda *args, **kwargs: next(pages), "cloudformation", "describe-stack-events", "StackEvents") == [{"event": 1}, {"event": 2}]
    rejected(lambda: M.rows(lambda *args, **kwargs: {"StackEvents": [], "NextToken": "same"}, "cloudformation", "describe-stack-events", "StackEvents"), "provider-pagination-invalid")


def test_safe_boundary():
    failure = M.Failure("foundation-role-changed", "unknown")
    result = M.failure_report(failure)
    assert result["code"] == "foundation-role-changed"
    assert result["diagnostic"]["original_failure"]["code"] == "foundation-role-changed"
    with patch.object(M.DIAGNOSTICS, "build_report", side_effect=RuntimeError("private-canary")):
        result = M.failure_report(failure)
        assert result == {"verdict": "unknown", "code": "foundation-role-changed", "diagnostic_collection": "unavailable"}
        assert "private-canary" not in json.dumps(result)
    output = io.StringIO()
    with contextlib.redirect_stdout(output), patch.object(M, "Provider") as provider:
        assert M.main(["--operation", "delete", "--predecessor", "private-canary"]) == 1
        provider.assert_not_called()
    assert "private-canary" not in output.getvalue()
    assert json.loads(output.getvalue())["code"] == "arguments-invalid"


def test_main_handoff():
    selected, before, after, source = fixture()
    provider = Provider(selected, before, after)
    with tempfile.TemporaryDirectory() as directory:
        def invoke(operation, approved=None):
            output = io.StringIO()
            arguments = ["--operation", operation, "--predecessor", source["predecessor"], "--json"]
            if approved:
                arguments.extend(["--approved-plan-sha256", approved])
            with contextlib.redirect_stdout(output):
                code = M.main(arguments)
            return code, json.loads(output.getvalue())
        with patch.object(M, "sources", return_value=(source, before, after)), patch.object(M, "git", return_value=directory), patch.object(M, "Provider", return_value=provider):
            code, plan = invoke("plan")
            assert code == 0 and plan["verdict"] == "planned" and not provider.writes()
            intent_path = Path(directory) / "foundation-access-update/intent.json"
            original = intent_path.read_bytes()
            assert "****" not in original.decode() and "kanbien-core-platform/core-server" not in original.decode()
            assert invoke("plan") == (code, plan) and intent_path.read_bytes() == original
            assert invoke("prepare")[1]["code"] == "approved-plan-mismatch" and not provider.writes()
            assert invoke("prepare", plan["plan_sha256"])[1]["verdict"] == "reviewed"
            assert invoke("review")[1]["verdict"] == "reviewed"
            assert invoke("execute", plan["plan_sha256"])[1]["verdict"] == "completed"
            assert invoke("observe")[1]["verdict"] == "completed" and len(provider.writes()) == 2
            assert intent_path.read_bytes() == original


if __name__ == "__main__":
    started = time.monotonic()
    for test in (test_source_and_declaration, test_connected_and_uncertain, test_review_and_readback, test_original_intent_and_provider, test_safe_boundary, test_main_handoff):
        test()
    print(json.dumps({"verdict": "passed", "groups": 6, "elapsed_seconds": round(time.monotonic() - started, 3), "provider": "controlled-only"}, sort_keys=True))

#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.foundation-access-update
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.foundation-access
#   disciplines: [security, sre]
#   kind: script
#   purpose: Preserve original intent while admitting only the declared nonreplacing repository observation permission update.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: aws.workflow.kanbien-core-platform.update-delivery-observation-access
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/10-foundation/update-delivery-observation-access.md
"""One declared permission adoption; never an arbitrary IAM or retry interface."""
from datetime import datetime
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[6]
sys.dont_write_bytecode = True


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


BASE = "scripts/04.deploy/shared/provider-adapters/aws/"
CF = module("foundation_access_cf", BASE + "cloudformation-template.py")
CLI = module("foundation_access_cli", BASE + "cli.py")
RESPONSE = module("foundation_access_response", BASE + "response.py")
CHANGES = module("foundation_access_changes", BASE + "change_sets.py")
RESERVATIONS = module("foundation_access_reservations", BASE + "resource_reservation.py")
DECLARATION = module("foundation_access_declaration", "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py")
DIAGNOSTICS = module("foundation_access_diagnostics", "scripts/04.deploy/shared/deployment-operation-diagnostics.py")
TARGET_ROOT = "infra/04.deploy/03.product/targets/kanbien-core-platform/"
ACCESS = TARGET_ROOT + "10-foundation/technical-access.yml"
PROFILE = TARGET_ROOT + "00-target/target-profile.yml"
RULE = ".agentic/aws/standards/operational-realization-applicability.md"
STABLE = {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}


class Failure(Exception):
    def __init__(self, code, outcome="rejected"):
        self.code, self.outcome = code, outcome
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise Failure(code)


def digest(value):
    return hashlib.sha256(RESERVATIONS.canonical(value)).hexdigest()


def read(path):
    try:
        value = Path(path).read_bytes()
        require(len(value) <= 262144, "input-too-large")
        return json.loads(value)
    except (OSError, ValueError, UnicodeError, RecursionError):
        raise Failure("input-unavailable") from None


def binding():
    try:
        access = CF.template((ROOT / ACCESS).read_text())
        selected = DECLARATION.check_access_maintenance(access)
        profile = CF.template((ROOT / PROFILE).read_text())
        provider = profile["provider"]
        require(profile["id"] == access["target"] == "kanbien-core-platform" and provider["family"] == "aws", "target-binding-invalid")
        require(provider["account_id"] == "337159794548" and provider["region"] == "eu-west-1" and provider["profile"] == "kanbien-dev", "provider-binding-invalid")
        foundation = provider["foundation"]
        require(foundation == {"stack": "kanbien-core-platform-foundation", "template": "30-provider-realization/aws/cloudformation/foundation.yml"}, "foundation-binding-invalid")
        return {**selected, "target": access["target"], "provider": provider,
                "stack": foundation["stack"], "template": TARGET_ROOT + foundation["template"]}
    except DECLARATION.DeclarationFailure:
        raise Failure("technical-access-maintenance-invalid") from None


def policy(document, selected):
    role = document["Resources"][selected["logical_resource"]]
    require(role["Type"] == "AWS::IAM::Role", "role-source-invalid")
    policies = role["Properties"]["Policies"]
    require(isinstance(policies, list), "policy-source-invalid")
    matches = [item for item in policies if isinstance(item, dict) and item.get("PolicyName") == selected["policy_name"]]
    require(len(matches) == 1, "policy-source-ambiguous")
    result = matches[0]["PolicyDocument"]
    require(isinstance(result, dict) and isinstance(result.get("Statement"), list), "policy-source-invalid")
    return result


def statement(document, resource):
    matches = [item for item in document["Statement"] if isinstance(item, dict) and item.get("Resource") == resource]
    require(len(matches) == 1 and matches[0].get("Effect") == "Allow" and set(matches[0]) == {"Effect", "Action", "Resource"}, "repository-statement-invalid")
    result = matches[0]
    actions = result.get("Action")
    require(isinstance(actions, list) and all(isinstance(item, str) for item in actions) and len(set(actions)) == len(actions), "repository-actions-invalid")
    return result


def source_delta(before, after, selected):
    before, after = CF.template(before), CF.template(after)
    changed = copy.deepcopy(after)
    original = statement(policy(before, selected), {"Ref": selected["resource_parameter"]})
    successor = statement(policy(changed, selected), {"Ref": selected["resource_parameter"]})
    action = selected["action"]
    require(action not in original["Action"] and successor["Action"].count(action) == 1, "permission-addition-invalid")
    successor["Action"].remove(action)
    require(CF.templates_equal(before, changed), "foundation-source-change-outside-scope")
    return before, after


def git(*args, binary=False):
    try:
        result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True, timeout=15)
        return result.stdout if binary else result.stdout.decode().strip()
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise Failure("source-observation-unavailable") from None


def sources(selected, predecessor):
    require(isinstance(predecessor, str) and re.fullmatch(r"[a-f0-9]{40}", predecessor), "predecessor-invalid")
    revision = git("rev-parse", "HEAD")
    require(re.fullmatch(r"[a-f0-9]{40}", revision) and not git("status", "--porcelain"), "source-not-clean-committed")
    git("merge-base", "--is-ancestor", predecessor, revision)
    before, after = source_delta(git("show", predecessor + ":" + selected["template"]),
                                git("show", revision + ":" + selected["template"]), selected)
    paths = [selected["template"], ACCESS, PROFILE, selected["controller"], selected["workflow"], RULE,
             "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py",
             "scripts/04.deploy/shared/deployment-operation-diagnostics.py",
             *[BASE + name for name in ("cloudformation-template.py", "cli.py", "response.py", "resource_reservation.py", "change_sets.py")]]
    identities = {path: hashlib.sha256(git("show", revision + ":" + path, binary=True)).hexdigest() for path in paths}
    return {"revision": revision, "predecessor": predecessor, "identities": identities,
            "before_sha256": digest(before), "after_sha256": digest(after)}, before, after


class Provider:
    def __init__(self, selected):
        self.selected, self.checked = selected, False

    def __call__(self, service, operation, **arguments):
        allowed = {("sts", "get-caller-identity"), ("cloudformation", "describe-stacks"),
                   ("cloudformation", "list-stack-resources"), ("cloudformation", "get-template"),
                   ("cloudformation", "describe-change-set"), ("cloudformation", "describe-stack-events"),
                   ("cloudformation", "create-change-set"), ("cloudformation", "execute-change-set"),
                   ("iam", "get-role"), ("iam", "get-role-policy"), ("iam", "list-role-policies"),
                   ("iam", "list-attached-role-policies")}
        require((service, operation) in allowed, "provider-operation-unowned")
        if not self.checked:
            require(RESPONSE.inventory_covered(ROOT), "delivery-inventory-not-covered")
            if (service, operation) != ("sts", "get-caller-identity"):
                identity = self("sts", "get-caller-identity")
                require(identity.get("Account") == self.selected["provider"]["account_id"], "provider-account-mismatch")
                self.checked = True
        provider = self.selected["provider"]
        argv = ["aws", service, operation, "--region", provider["region"], "--profile", provider["profile"],
                "--output", "json", "--no-paginate", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"]
        if arguments:
            argv.extend(["--cli-input-json", json.dumps(arguments, separators=(",", ":"))])
        try:
            return CLI.invoke_json(argv, timeout=30, empty_body="whitespace", object_only=True,
                environment={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
        except CLI.CliFailure as failure:
            raise Failure(failure.code, "unknown") from None


def rows(provider, service, operation, field, **arguments):
    result, token, seen = [], None, set()
    for _ in range(20):
        value = provider(service, operation, **arguments, **({"NextToken": token} if token else {}))
        require(isinstance(value.get(field), list), "provider-collection-invalid")
        result.extend(value[field])
        token = value.get("NextToken")
        require(not value.get("IsTruncated"), "provider-collection-incomplete")
        if token is None:
            return result
        require(isinstance(token, str) and token and token not in seen, "provider-pagination-invalid")
        seen.add(token)
    raise Failure("provider-collection-incomplete")


def stack(provider, selected, stack_id=None):
    value = provider("cloudformation", "describe-stacks", StackName=stack_id or selected["stack"])
    values = value.get("Stacks")
    require(isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict), "stack-observation-invalid")
    value = values[0]
    prefix = f"arn:aws:cloudformation:{selected['provider']['region']}:{selected['provider']['account_id']}:stack/{selected['stack']}/"
    require(value.get("StackName") == selected["stack"] and isinstance(value.get("StackId"), str)
            and value["StackId"].startswith(prefix) and (stack_id is None or value["StackId"] == stack_id), "stack-identity-mismatch")
    tags = value.get("Tags")
    require(isinstance(tags, list) and sum(item == {"Key": "Target", "Value": selected["target"]} for item in tags) == 1, "stack-target-tag-mismatch")
    return value


def inventory(provider, stack_id):
    values = rows(provider, "cloudformation", "list-stack-resources", "StackResourceSummaries", StackName=stack_id)
    result = {}
    for item in values:
        require(isinstance(item, dict) and all(isinstance(item.get(key), str) and item[key] for key in ("LogicalResourceId", "PhysicalResourceId", "ResourceType")), "resource-inventory-invalid")
        require(item["LogicalResourceId"] not in result, "resource-inventory-ambiguous")
        result[item["LogicalResourceId"]] = {key: item[key] for key in ("PhysicalResourceId", "ResourceType")}
    require(bool(result), "resource-inventory-empty")
    return result


def role_state(provider, selected, resources):
    identity = resources[selected["logical_resource"]]
    require(identity["ResourceType"] == "AWS::IAM::Role", "role-resource-mismatch")
    name = identity["PhysicalResourceId"]
    observed = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(observed, dict) and observed.get("RoleName") == name
            and isinstance(observed.get("RoleId"), str) and observed["RoleId"]
            and observed.get("Arn") == f"arn:aws:iam::{selected['provider']['account_id']}:role/{name}", "role-identity-mismatch")
    keys = ("RoleId", "Arn", "RoleName", "Path", "AssumeRolePolicyDocument", "MaxSessionDuration", "PermissionsBoundary", "Tags")
    state = {key: observed[key] for key in keys if key in observed}
    names = rows(provider, "iam", "list-role-policies", "PolicyNames", RoleName=name)
    require(all(isinstance(item, str) for item in names) and len(names) == len(set(names)) and selected["policy_name"] in names, "role-policies-invalid")
    state["policies"] = {}
    for policy_name in sorted(names):
        value = provider("iam", "get-role-policy", RoleName=name, PolicyName=policy_name)
        require(value.get("RoleName") == name and value.get("PolicyName") == policy_name and isinstance(value.get("PolicyDocument"), dict), "role-policy-observation-invalid")
        state["policies"][policy_name] = value["PolicyDocument"]
    attached = rows(provider, "iam", "list-attached-role-policies", "AttachedPolicies", RoleName=name)
    require(all(isinstance(item, dict) and set(item) == {"PolicyName", "PolicyArn"} for item in attached), "role-attached-policies-invalid")
    state["attached"] = sorted(attached, key=lambda item: item["PolicyArn"])
    if "Tags" in state:
        state["Tags"] = sorted(state["Tags"], key=lambda item: item["Key"])
    return state


def resolved_policy(document, selected, parameters):
    value = copy.deepcopy(policy(document, selected))
    statement(value, {"Ref": selected["resource_parameter"]})["Resource"] = parameters[selected["resource_parameter"]]
    return value


def observe_state(provider, selected, document, stack_id=None):
    observed = stack(provider, selected, stack_id)
    require(observed.get("StackStatus") in STABLE, "foundation-stack-not-stable")
    parameters = CHANGES.parameter_values(observed.get("Parameters"))
    require(isinstance(parameters, dict) and set(parameters) == set(document["Parameters"]), "foundation-parameters-invalid")
    require(re.fullmatch(r"arn:aws:ecr:eu-west-1:337159794548:repository/[a-z0-9/-]+", parameters[selected["resource_parameter"]]), "repository-parameter-invalid")
    actual = provider("cloudformation", "get-template", StackName=observed["StackId"], TemplateStage="Original").get("TemplateBody")
    require(CF.templates_equal(actual, document), "deployed-template-mismatch")
    resources = inventory(provider, observed["StackId"])
    require(resources.get(selected["logical_resource"], {}).get("PhysicalResourceId") == document["Resources"][selected["logical_resource"]]["Properties"]["RoleName"], "role-source-identity-mismatch")
    role = role_state(provider, selected, resources)
    require(CF.templates_equal(role["policies"][selected["policy_name"]], resolved_policy(document, selected, parameters)), "deployed-policy-mismatch")
    return observed, parameters, resources, role


def make_intent(provider, selected, source, before, after):
    observed, parameters, resources, role = observe_state(provider, selected, before)
    successor = copy.deepcopy(role)
    successor["policies"][selected["policy_name"]] = resolved_policy(after, selected, parameters)
    return {"schema": "deploy/foundation-access-intent/v1", "target": selected["target"],
            "binding_sha256": digest(selected), "source": source, "stack_id": observed["StackId"],
            "change_set": "delivery-repository-observation",
            "parameters_sha256": digest(parameters), "resources_sha256": digest(resources),
            "role_before_sha256": digest(role), "role_after_sha256": digest(successor)}


def validate_intent(intent, selected, source):
    keys = {"schema", "target", "binding_sha256", "source", "stack_id", "change_set", "parameters_sha256", "resources_sha256", "role_before_sha256", "role_after_sha256"}
    require(isinstance(intent, dict) and set(intent) == keys and intent["schema"] == "deploy/foundation-access-intent/v1"
            and intent["target"] == selected["target"] and intent["binding_sha256"] == digest(selected) and intent["source"] == source,
            "retained-intent-mismatch")
    require(all(isinstance(intent[key], str) and re.fullmatch(r"[a-f0-9]{64}", intent[key]) for key in keys if key.endswith("sha256")), "retained-intent-invalid")
    require(intent["change_set"] == "delivery-repository-observation", "retained-operation-mismatch")
    return intent


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/foundation-access-reservation/v1"
    operation_prefix = "foundation-access-"
    failure = staticmethod(lambda code: Failure("reservation-" + code))

    def path_for(self, phase, request):
        require(phase in {"prepare", "execute"} and isinstance(request, dict) and set(request) == {"intent_sha256"}
                and isinstance(request["intent_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", request["intent_sha256"]), "reservation-request-invalid")
        # A different source/label cannot evade an uncertain predecessor.
        return self.root / (phase + ".json")

    def validate_time(self, value):
        require(isinstance(value, str) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None, "reservation-time-invalid")


def unchanged(provider, selected, intent, document, *, successor=False):
    observed, parameters, resources, role = observe_state(provider, selected, document, intent["stack_id"])
    require(digest(parameters) == intent["parameters_sha256"], "foundation-parameters-changed")
    require(digest(resources) == intent["resources_sha256"], "foundation-resources-changed")
    require(digest(role) == intent["role_after_sha256" if successor else "role_before_sha256"], "foundation-role-changed")
    return observed, parameters


def review(provider, selected, intent, prepared, after):
    value = provider("cloudformation", "describe-change-set", StackName=intent["stack_id"], ChangeSetName=intent["change_set"])
    require(value.get("StackId") == intent["stack_id"] and value.get("ChangeSetName") == intent["change_set"]
            and value.get("Description") == prepared["operation_id"] and value.get("ChangeSetType") == "UPDATE", "change-set-lineage-mismatch")
    if value.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}:
        return {"verdict": "pending", "code": "change-set-pending"}
    require(value.get("Status") == "CREATE_COMPLETE" and value.get("ExecutionStatus") == "AVAILABLE", "change-set-not-reviewable")
    parameters = CHANGES.parameter_values(value.get("Parameters"))
    require(parameters is not None and digest(parameters) == intent["parameters_sha256"], "change-set-parameters-mismatch")
    require(value.get("Capabilities") == ["CAPABILITY_NAMED_IAM"], "change-set-capabilities-mismatch")
    actual = provider("cloudformation", "get-template", StackName=intent["stack_id"], ChangeSetName=intent["change_set"], TemplateStage="Original").get("TemplateBody")
    require(CF.templates_equal(actual, after), "change-set-template-mismatch")
    changes = value.get("Changes")
    require(isinstance(changes, list) and len(changes) == 1 and isinstance(changes[0], dict), "change-set-scope-invalid")
    row = changes[0].get("ResourceChange")
    require(isinstance(row, dict) and row.get("Action") == "Modify" and row.get("LogicalResourceId") == selected["logical_resource"]
            and row.get("ResourceType") == "AWS::IAM::Role" and row.get("Replacement") == "False"
            and row.get("PhysicalResourceId") == after["Resources"][selected["logical_resource"]]["Properties"]["RoleName"]
            and row.get("Scope") == ["Properties"], "change-set-scope-invalid")
    details = row.get("Details")
    require(isinstance(details, list) and details and all(isinstance(item, dict) and isinstance(item.get("Target"), dict)
        and item["Target"].get("Attribute") == "Properties" and item["Target"].get("Name") == "Policies"
        and item["Target"].get("RequiresRecreation") == "Never" for item in details), "change-set-property-invalid")
    return {"verdict": "reviewed", "code": "permission-only-change-reviewed"}


def observe_execution(provider, selected, intent, executed, after):
    observed = stack(provider, selected, intent["stack_id"])
    events = rows(provider, "cloudformation", "describe-stack-events", "StackEvents", StackName=intent["stack_id"])
    selected_events = CHANGES.execution_events({"StackEvents": events}, executed["operation_id"], intent["stack_id"])
    require(bool(selected_events), "execution-lineage-not-observed")
    status = observed.get("StackStatus")
    if status in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"}:
        return {"verdict": "pending", "code": "foundation-update-pending"}
    if status in {"UPDATE_FAILED", "UPDATE_ROLLBACK_FAILED", "UPDATE_ROLLBACK_COMPLETE"}:
        return {"verdict": "failed", "code": "foundation-update-failed"}
    require(status == "UPDATE_COMPLETE" and any(item.get("ResourceStatus") == "UPDATE_COMPLETE" for item in selected_events), "execution-completion-not-observed")
    unchanged(provider, selected, intent, after, successor=True)
    return {"verdict": "completed", "code": "foundation-access-update-verified"}


def control(provider, store, selected, intent, before, after, action, approved):
    request = {"intent_sha256": digest(intent)}
    prepared = store.read("prepare", request)
    executed = CHANGES.retained_execution(store, preparation_phase="prepare", preparation_request=request,
        execution_phase="execute", execution_request=request, missing_preparation=lambda: Failure("execution-reservation-orphaned"))
    if executed is not None:
        return observe_execution(provider, selected, intent, executed, after)
    if action in {"observe", "review"}:
        require(prepared is not None, "operation-not-reserved")
        return review(provider, selected, intent, prepared, after)
    require(approved == digest(intent), "approved-plan-mismatch")
    if action == "prepare":
        if prepared is not None:
            return review(provider, selected, intent, prepared, after)
        _, parameters = unchanged(provider, selected, intent, before)
        def absent(_reservation):
            try:
                provider("cloudformation", "describe-change-set", StackName=intent["stack_id"], ChangeSetName=intent["change_set"])
            except Failure as failure:
                if failure.code == "aws-resource-missing":
                    return
                raise
            raise Failure("unowned-change-set")
        return CHANGES.prepare(provider, store, phase="prepare", request=request,
            arguments={"StackName": intent["stack_id"], "ChangeSetName": intent["change_set"], "ChangeSetType": "UPDATE",
                       "TemplateBody": json.dumps(after), "Parameters": CHANGES.update_parameter_inputs(parameters, {}),
                       "Capabilities": ["CAPABILITY_NAMED_IAM"]}, precondition=absent,
            observe=lambda reservation: review(provider, selected, intent, reservation, after))
    require(action == "execute" and prepared is not None, "preparation-required")
    require(review(provider, selected, intent, prepared, after)["verdict"] == "reviewed", "change-set-not-ready")
    def fresh(_reservation):
        unchanged(provider, selected, intent, before)
        require(review(provider, selected, intent, prepared, after)["verdict"] == "reviewed", "change-set-not-ready")
    return CHANGES.execute(provider, store, phase="execute", request=request,
        arguments={"StackName": intent["stack_id"], "ChangeSetName": intent["change_set"]}, precondition=fresh,
        observe=lambda reservation: observe_execution(provider, selected, intent, reservation, after))


def failure_report(failure):
    code = failure.code
    outcome = getattr(failure, "outcome", "unknown")
    # Builder failure never hides the original finite condition or prompts replay.
    result = {"verdict": outcome, "code": code}
    try:
        result["diagnostic"] = DIAGNOSTICS.build_report(target="kanbien-core-platform", scope="foundation",
            operation_id="delivery-repository-observation", stage="deploy", original_code=code,
            exit_status=1, outcome=outcome, classification=code, evidence_reference="provider-operation:delivery-repository-observation",
            next_decision="observe-current-operation" if outcome == "unknown" else "stop-and-escalate")
    except Exception:
        result["diagnostic_collection"] = "unavailable"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: (_ for _ in ()).throw(Failure("arguments-invalid"))
    parser.add_argument("--operation", choices=["plan", "prepare", "review", "execute", "observe"], required=True)
    parser.add_argument("--predecessor", required=True)
    parser.add_argument("--approved-plan-sha256")
    parser.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
        selected = binding()
        source, before, after = sources(selected, args.predecessor)
        private = Path(git("rev-parse", "--absolute-git-dir")) / "foundation-access-update"
        RESERVATIONS.no_symlinks(private)
        store, intent_path = Store(private), private / "intent.json"
        if intent_path.exists():
            RESERVATIONS.no_symlinks(intent_path)
            intent = validate_intent(read(intent_path), selected, source)
        else:
            require(args.operation == "plan", "retained-plan-required")
            intent = make_intent(Provider(selected), selected, source, before, after)
            require(RESERVATIONS.write_exclusive(intent_path, intent), "plan-retention-race")
        if args.operation == "plan":
            result = {"verdict": "planned", "code": "permission-update-plan-retained", "plan_sha256": digest(intent)}
        else:
            result = control(Provider(selected), store, selected, intent, before, after, args.operation, args.approved_plan_sha256)
            result["plan_sha256"] = digest(intent)
    except (Failure, CHANGES.ChangeSetFailure, RESERVATIONS.ReservationFailure) as failure:
        result = failure_report(failure)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        result = failure_report(Failure("foundation-input-or-observation-invalid", "unknown"))
    print(json.dumps({"schema": "deploy/foundation-access-update-report/v1", **result}, sort_keys=True))
    return 0 if result["verdict"] in {"planned", "reviewed", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

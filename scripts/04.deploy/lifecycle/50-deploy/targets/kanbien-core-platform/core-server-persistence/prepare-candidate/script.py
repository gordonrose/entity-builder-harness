#!/usr/bin/env python3
"""Inspect only the fixed persistence candidate target before change-set creation."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
INPUT_PATH = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py"
_input_spec = importlib.util.spec_from_file_location("persistence_preparation_inputs", INPUT_PATH)
INPUT_OWNER = importlib.util.module_from_spec(_input_spec)
_input_spec.loader.exec_module(INPUT_OWNER)
_image_spec = importlib.util.spec_from_file_location("persistence_image_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py")
IMAGE_CHECKS = importlib.util.module_from_spec(_image_spec)
_image_spec.loader.exec_module(IMAGE_CHECKS)
_foundation_spec = importlib.util.spec_from_file_location("persistence_foundation_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py")
FOUNDATION_CHECKS = importlib.util.module_from_spec(_foundation_spec)
_foundation_spec.loader.exec_module(FOUNDATION_CHECKS)
try:
    INPUTS = INPUT_OWNER.load(ROOT, "kanbien-core-platform", "core-server-persistence")
    INPUT_ERROR = None
except INPUT_OWNER.InputFailure as failure:
    INPUTS, INPUT_ERROR = {}, failure.code
PROFILE, REGION, ACCOUNT = (INPUTS.get(key) for key in ("profile", "region", "account"))
FOUNDATION, STACK, REPOSITORY = (INPUTS.get(key) for key in ("foundation_stack", "stack", "repository"))
EXPECTED = {key: INPUTS.get(key) for key in ("candidate", "package", "program")}
REQUIRED_FOUNDATION = {
    "VpcId", "PrivateSubnetIds", "ClusterArn", "VerifierSecurityGroupId", "LogGroupName", "RepositoryUri", "ServiceDiscoveryArn",
}
INTERFACE_SERVICES = {
    f"com.amazonaws.{REGION}.ecr.dkr",
    f"com.amazonaws.{REGION}.ecr.api",
    f"com.amazonaws.{REGION}.logs",
}
AWS_CONNECT_TIMEOUT_SECONDS = 5
AWS_READ_TIMEOUT_SECONDS = 20
AWS_PROCESS_TIMEOUT_SECONDS = 30


_AWS_RESPONSE=None
_AWS_CLI=None
_UPDATE_OPERATIONS=None


def update_operations():
    """Load the shared provider binding once for every baseline UPDATE caller."""
    global _UPDATE_OPERATIONS
    if _UPDATE_OPERATIONS is None:
        path = Path(__file__).resolve().parent.parent / "change-set-operations.py"
        spec = importlib.util.spec_from_file_location("persistence_update_operations", path)
        _UPDATE_OPERATIONS = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_UPDATE_OPERATIONS)
    return _UPDATE_OPERATIONS


def apply_update(**arguments):
    """Keep all baseline UPDATE callers on the same provider sequence."""
    return update_operations().apply_update(aws, root=ROOT, stack=STACK, **arguments)


def update_settings(settings):
    return {"target": {key: INPUTS.get(key) for key in ("account", "region", "profile", "repository_uri")}, "operation": settings}


def update_request(**arguments):
    arguments["settings"] = update_settings(arguments["settings"])
    return update_operations().update_request(stack=STACK, **arguments)


def begin_update(**arguments):
    arguments["settings"] = update_settings(arguments["settings"])
    return update_operations().begin_update(ROOT, stack=STACK, **arguments)


def labelled_update_name(name, label):
    return update_operations().labelled_name(name, label)

def aws_response():
    global _AWS_RESPONSE
    if _AWS_RESPONSE is None:
        spec=importlib.util.spec_from_file_location("aws_response",ROOT/"scripts/04.deploy/shared/provider-adapters/aws/response.py")
        _AWS_RESPONSE=importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(_AWS_RESPONSE)
    return _AWS_RESPONSE


def aws_cli():
    global _AWS_CLI
    if _AWS_CLI is None:
        spec = importlib.util.spec_from_file_location("aws_cli", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cli.py")
        _AWS_CLI = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_AWS_CLI)
    return _AWS_CLI


def aws_in_region(region: str, *parts: str) -> tuple[bool, Any, str]:
    if INPUT_ERROR: return False, None, INPUT_ERROR
    if not aws_response().inventory_covered(ROOT): return False, None, "delivery-inventory-not-covered"
    cli = aws_cli()
    try:
        value = cli.invoke_json(
            ["aws", *parts, "--cli-connect-timeout", str(AWS_CONNECT_TIMEOUT_SECONDS),
             "--cli-read-timeout", str(AWS_READ_TIMEOUT_SECONDS), *(["--profile", PROFILE] if PROFILE else []), "--region", region, "--output", "json"],
            timeout=AWS_PROCESS_TIMEOUT_SECONDS, environment={**os.environ, "AWS_PAGER": ""}, empty_body="whitespace", object_only=False,
        )
        return True, value, "ok"
    except cli.CliFailure as failure:
        # Lost responses still require observation; this boundary never retries.
        return False, None, failure.code

def aws(*parts: str) -> tuple[bool, Any, str]:
    return aws_in_region(REGION, *parts)


def report(verdict: str, codes: list[str], facts: dict[str, Any] | None = None) -> int:
    value: dict[str, Any] = {
        "schema": "deploy/persistence-candidate-preparation-report/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "verdict": verdict,
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "prepared" else 1


def validate_receipt(path: Path) -> dict[str, Any] | None:
    """Reuse custody validation and retain its checked provenance for rollback."""
    if INPUT_ERROR: return None
    try:
        spec = importlib.util.spec_from_file_location("persistence_custody_validation", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py")
        if spec is None or spec.loader is None: return None
        owner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(owner)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        expected = argparse.Namespace(expected_target="kanbien-core-platform", expected_candidate=EXPECTED["candidate"], expected_package_contract=EXPECTED["package"], expected_program=EXPECTED["program"])
        try: owner.validate(receipt, expected)
        except owner.Failure: return None
        return {**json.loads(owner.report("passed", receipt=receipt)), "receipt_reference": receipt["receipt_reference"]}
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, ImportError, AttributeError, SyntaxError):
        return None


def declaration_covered() -> bool:
    """Offline coverage is compulsory before provider observation or mutation."""
    checker = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py"
    contract = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    try:
        checked = subprocess.run([sys.executable, "-B", str(checker), "--scope-contract", str(contract), "--root", str(ROOT), "--json"], capture_output=True, text=True, timeout=30)
        value = json.loads(checked.stdout)
    except (OSError, UnicodeError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return False
    return checked.returncode == 0 and isinstance(value, dict) and value.get("verdict") == "covered" and value.get("findings") == []


def foundation_observation(service, operation, **parameters):
    ok, value, code = aws(service, operation, "--cli-input-json", json.dumps(parameters))
    if not ok: raise FOUNDATION_CHECKS.FoundationFailure(code)
    return value


def foundation_outputs() -> tuple[dict[str, str] | None, str]:
    if INPUT_ERROR: return None, INPUT_ERROR
    try:
        document = foundation_observation("cloudformation", "describe-stacks", StackName=FOUNDATION)
        outputs = FOUNDATION_CHECKS.foundation(document, REQUIRED_FOUNDATION, INPUTS["foundation_expected"])
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        return None, failure.code
    if outputs["RepositoryUri"] != INPUTS["repository_uri"]:
        return None, "preparation-inputs-repository-mismatch"
    return outputs, "ok"


def infrastructure_parameters(outputs: dict[str, str]) -> tuple[dict[str, str] | None, str]:
    if INPUT_ERROR: return None, INPUT_ERROR
    try:
        network = FOUNDATION_CHECKS.private_network(foundation_observation, outputs, INPUTS["foundation_expected"]["namespace"], REGION)
        _, endpoint_group = FOUNDATION_CHECKS.private_endpoints(foundation_observation, outputs["VpcId"], INTERFACE_SERVICES)
        prefix_id = FOUNDATION_CHECKS.s3_prefix_list(foundation_observation, REGION)
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        return None, failure.code
    return {
        **network,
        "EndpointSecurityGroupId": endpoint_group, "VerifierSecurityGroupId": outputs["VerifierSecurityGroupId"],
        "S3ArtifactPrefixListId": prefix_id,
    }, "ok"


def change_name_matches(value: object, expected: str) -> bool:
    return value == expected or (isinstance(value, str) and value.startswith("arn:aws:cloudformation:") and value.split(":changeSet/", 1)[-1].split("/", 1)[0] == expected)


def observe_update(name: str, expected_parameters: dict, review, *, reservation=None) -> tuple[str, str]:
    """Observe one named UPDATE; never create, execute, wait on, or replace it."""
    def completed(stack, code):
        # Historical explicit reconciliation keeps its original contract.
        # A new reservation is intent, not proof that submission occurred.
        if reservation is not None:
            if reservation.get("phase") != "update-execute":
                return "uncertain", "persistence-update-execution-lineage-not-confirmed"
            ok, events, observed = aws("cloudformation", "describe-stack-events", "--stack-name", STACK)
            if not ok: return "uncertain", observed
            owned = update_operations().CHANGE_SETS.execution_events(events, reservation["operation_id"], stack.get("StackId"))
            if not any(event.get("ResourceStatus") == "UPDATE_COMPLETE" for event in owned):
                return "uncertain", "persistence-update-execution-lineage-not-confirmed"
        return "complete", code
    ok, change, code = aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok and code == "aws-resource-missing":
        # CloudFormation removes an executed change set.  When a controller
        # loses its response after execution, retain the no-retry boundary but
        # still recognize the exact candidate parameter identity on the stack.
        # A missing change set alone never proves execution or completion.
        stack_ok, observed, stack_code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
        stacks = observed.get("Stacks") if stack_ok and isinstance(observed, dict) else None
        if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
            return "uncertain", "persistence-update-stack-observation-uncertain" if stack_ok else stack_code
        stack = stacks[0]
        params = update_operations().CHANGE_SETS.parameter_values(stack.get("Parameters"))
        if params is None: return "uncertain", "persistence-update-stack-parameters-unobservable"
        if any(params.get(key) != value for key, value in expected_parameters.items()):
            return "uncertain", "persistence-update-missing-change-set-identity-unproven"
        status = stack.get("StackStatus")
        try: pending = status in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"}
        except TypeError: return "uncertain", "persistence-update-stack-status-unobservable"
        if pending:
            return "pending", "persistence-update-executed-stack-pending"
        if status == "UPDATE_COMPLETE":
            return completed(stack, "persistence-update-operation-complete")
        # Do not attach an absent named change set to an unrelated failed or
        # rollback stack operation.  A known executed change set follows the
        # explicit terminal path below; this branch remains conservative.
        return "uncertain", "persistence-update-missing-change-set-status-unproven"
    if not ok or not isinstance(change, dict):
        return "uncertain", code if not ok else "persistence-update-observation-invalid"
    if not change_name_matches(change.get("ChangeSetName"), name):
        return "blocked", "persistence-update-change-set-identity-invalid"
    try: pending = change.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}
    except TypeError: return "uncertain", "persistence-update-review-status-unobservable"
    if pending:
        return "pending", "persistence-update-review-pending"
    # A controller may resume after an acknowledged update completed and its
    # executed change set has disappeared.  CloudFormation then permits a new
    # change set with the same name, but reports it as FAILED because the
    # desired parameters are already applied.  This is not an update failure:
    # accept it only for CloudFormation's exact no-change shape and only after
    # independently proving the healthy stack still has every expected value.
    no_change = (
        change.get("Status") == "FAILED"
        and change.get("ExecutionStatus") == "UNAVAILABLE"
        and change.get("Changes") == []
        and isinstance(change.get("StatusReason"), str)
        and "didn't contain changes" in change["StatusReason"]
    )
    if no_change:
        stack_ok, observed, stack_code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
        stacks = observed.get("Stacks") if stack_ok and isinstance(observed, dict) else None
        if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
            return "uncertain", "persistence-update-stack-observation-uncertain" if stack_ok else stack_code
        stack = stacks[0]
        params = update_operations().CHANGE_SETS.parameter_values(stack.get("Parameters"))
        if params is None: return "uncertain", "persistence-update-stack-parameters-unobservable"
        if stack.get("StackStatus") == "UPDATE_COMPLETE" and all(params.get(key) == value for key, value in expected_parameters.items()):
            return completed(stack, "persistence-update-noop-candidate-already-applied")
        return "failed", "persistence-update-change-set-failed"
    try: failed = change.get("Status") in {"FAILED", "DELETE_COMPLETE", "DELETE_FAILED"}
    except TypeError: return "uncertain", "persistence-update-review-status-unobservable"
    if failed:
        return "failed", "persistence-update-change-set-failed"
    try: reviewed = review(change)
    except (AttributeError, TypeError, KeyError, IndexError, ValueError): return "uncertain", "persistence-update-review-unobservable"
    if not reviewed:
        return "blocked", "persistence-update-change-set-review-invalid"
    execution = change.get("ExecutionStatus")
    try: pending = execution in {"AVAILABLE", "EXECUTE_IN_PROGRESS"}
    except TypeError: return "uncertain", "persistence-update-execution-status-unobservable"
    if pending:
        return "pending", "persistence-update-execution-pending"
    if execution != "EXECUTE_COMPLETE":
        return "uncertain", "persistence-update-execution-state-unknown"
    ok, observed, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = observed.get("Stacks") if ok and isinstance(observed, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return "uncertain", "persistence-update-stack-observation-uncertain"
    stack = stacks[0]
    status = stack.get("StackStatus")
    try: pending = status in {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"}
    except TypeError: return "uncertain", "persistence-update-stack-status-unobservable"
    if pending:
        return "pending", "persistence-update-stack-pending"
    if status in {"UPDATE_FAILED", "UPDATE_ROLLBACK_FAILED", "UPDATE_ROLLBACK_COMPLETE", "DELETE_COMPLETE"}:
        return "failed", "persistence-update-stack-failed"
    params = update_operations().CHANGE_SETS.parameter_values(stack.get("Parameters"))
    if params is None: return "uncertain", "persistence-update-stack-parameters-unobservable"
    if status != "UPDATE_COMPLETE" or any(params.get(key) != value for key, value in expected_parameters.items()):
        return "uncertain", "persistence-update-completion-identity-unproven"
    return completed(stack, "persistence-update-operation-complete")


def candidate_parameters(outputs: dict, infrastructure: dict, receipt: dict) -> dict[str, str]:
    """One provider-owned mapping is shared by CREATE and its execution review."""
    # All executable programs in the template are part of one qualified image
    # release.  Keep these bindings together so either CREATE or UPDATE cannot
    # accidentally retain an obsolete support-program image while moving the
    # server or restoration verifier to the candidate digest.
    return {**infrastructure, "ImageRepositoryArn": f"arn:aws:ecr:{REGION}:{ACCOUNT}:repository/{REPOSITORY}", "ImageRepositoryUri": INPUTS["repository_uri"], "ImageDigest": receipt["image_digest"], "SupportImageDigest": receipt["image_digest"], "RestoreVerifierImageDigest": receipt["image_digest"], "SourceRevision": receipt["source_revision"]}


def update_parameters_match(actual: object, desired: object, current: object) -> bool:
    """Existing controller interface; the shared change-set owner defines policy."""
    return update_operations().CHANGE_SETS.update_parameters_match(actual, desired, current)


def candidate_runnable_manifest(receipt: dict[str, Any]) -> tuple[str | None, str]:
    """Retained interface for replacement/observability callers; no local predicates."""
    try: return IMAGE_CHECKS.runnable_digest(image_observation, REPOSITORY, receipt.get("image_digest")), "ok"
    except IMAGE_CHECKS.ScanFailure as failure: return None, str(failure)


def image_observation(service, operation, **parameters):
    ok, value, code = aws(service, operation, "--cli-input-json", json.dumps(parameters))
    if not ok: raise IMAGE_CHECKS.ScanFailure(code)
    return value


def candidate_image(receipt: dict[str, Any]) -> tuple[bool, str]:
    try: IMAGE_CHECKS.check_image(image_observation, REPOSITORY, receipt.get("image_digest"))
    except IMAGE_CHECKS.ScanFailure as failure: return False, str(failure)
    return True, "ok"


def live_budget() -> tuple[bool, str]:
    if INPUT_ERROR: return False, INPUT_ERROR
    expected = INPUTS["budget"]
    ok, observed, code = aws("budgets", "describe-budget", "--account-id", ACCOUNT, "--budget-name", expected["BudgetName"])
    if not ok: return False, code
    try: FOUNDATION_CHECKS.budget(observed.get("Budget") if isinstance(observed, dict) else None, expected)
    except FOUNDATION_CHECKS.FoundationFailure as failure: return False, failure.code
    return True, "ok"


def succession_control():
    spec=importlib.util.spec_from_file_location("release_succession",ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
    owner=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(owner)
    return owner


def retained_release(receipt: dict[str, Any]) -> bool:
    """A retained historical image cannot evade rollback checks via 'update'."""
    import yaml
    root=ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
    paths=[root/"accepted-release.yml",*sorted((root/succession_control().HISTORY_DIRECTORY).glob("*.yml"))]
    for path in paths:
        if not path.exists():continue
        try:record=yaml.safe_load(path.read_text())
        except (OSError,UnicodeError,yaml.YAMLError):return True
        if not isinstance(record,dict):return True
        acceptance=record.get("acceptance")
        identities=[record.get("release"),acceptance.get("rollback_release") if isinstance(acceptance,dict) else None]
        if any(isinstance(value,dict) and value.get("image_digest")==receipt.get("image_digest") for value in identities):return True
    return False


def rollback_compatibility(receipt: dict[str, Any], identifier: str | None) -> bool:
    """Use the existing immutable succession owner before changing a boundary."""
    if not isinstance(identifier,str) or not identifier.startswith("rollback-compatibility-"):
        return False
    root=ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
    owner=succession_control()
    try:
        _, reference=owner.compatibility_record(root,identifier)
        identity=reference["identity"]
        if reference["target"]!="kanbien-core-platform" or reference["scope"]!="core-server-persistence":return False
        if identity["image_digest"]!=receipt["image_digest"] or identity["source_revision"]!=receipt["source_revision"]:return False
        expected={"core-server-service","private-release-verifier-task"}
        workloads=set(identity["workloads"])
        if not expected <= workloads <= expected|{"persistence-restoration-verifier-task"}:return False
        contracts={"configuration_contract":"infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml","permission_contract":"infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"}
        if any(identity[key]["path"]!=path for key,path in contracts.items()):return False
        qualified=identity.get("qualified_predecessor")
        if qualified is not None:
            return qualified=={"source_revision":receipt["source_revision"],"image_digest":receipt["image_digest"],"package_custody_reference":receipt["receipt_reference"]}
        # Reading compatibility must retain the same historical ownership that
        # was required when recording it; a detached archive is not a rollback.
        try:
            history,_=owner.history_record_for_id(root,identity["historical_release_id"])
            historical=history["release"]
        except owner.SuccessionFailure:
            historical=owner.retained_rollback_identity(root)
            if historical["release_id"]!=identity["historical_release_id"]:return False
        return historical["image_digest"]==receipt["image_digest"] and historical["source_revision"]==receipt["source_revision"]
    except (owner.SuccessionFailure,OSError,KeyError,TypeError,ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", ["persistence-candidate-preparation-arguments-invalid"])
    if INPUT_ERROR: return report("blocked", [INPUT_ERROR])
    receipt = validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", ["package-custody-receipt-invalid"])
    if not declaration_covered():
        return report("blocked", ["persistence-declaration-coverage-gap"])
    codes: list[str] = []
    outputs, code = foundation_outputs()
    if outputs is None:
        codes.append(code)
        return report("blocked", codes)
    params, code = infrastructure_parameters(outputs)
    if params is None:
        codes.append(code)
    image_ok, code = candidate_image(receipt)
    if not image_ok:
        codes.append(code)
    budget_ok, code = live_budget()
    if not budget_ok:
        codes.append(code)
    template = ROOT / INPUTS["template"]
    ok, _, code = aws("cloudformation", "validate-template", "--template-body", f"file://{template}")
    if not ok:
        codes.append(code)
    if codes:
        return report("blocked", codes)
    return report("prepared", [], {
        "candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"],
        "foundation": "available", "private_startup_connectivity": "available", "target_budget": "verified-live",
    })


if __name__ == "__main__":
    raise SystemExit(main())

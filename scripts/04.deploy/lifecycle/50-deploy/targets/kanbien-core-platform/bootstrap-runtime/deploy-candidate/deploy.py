#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.execute-runtime-change-set
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Execute only the exact reviewed update or restoration change set derived from a qualified immutable receipt.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.deploy-runtime-change-set.wrapper
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, STACK = "kanbien-dev", "eu-west-1", "kanbien-core-platform-bootstrap-runtime"
ALLOWED_TYPES = {"AWS::ECS::TaskDefinition", "AWS::ECS::Service"}
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml"
_TEMPLATES = None


def template_adapter():
    global _TEMPLATES
    if _TEMPLATES is None:
        spec = importlib.util.spec_from_file_location("aws_cloudformation_template", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
        _TEMPLATES = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(_TEMPLATES)
    return _TEMPLATES

def decoded_aws_response(raw: str):
    """Mutation commands may succeed without a response body."""
    return {} if not raw.strip() else json.loads(raw)
_AWS_RESPONSE=None

def aws_response():
    global _AWS_RESPONSE
    if _AWS_RESPONSE is None:
        spec=importlib.util.spec_from_file_location("aws_response",ROOT/"scripts/04.deploy/shared/provider-adapters/aws/response.py")
        _AWS_RESPONSE=importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(_AWS_RESPONSE)
    return _AWS_RESPONSE


def aws(*parts: str):
    if not aws_response().inventory_covered(ROOT):return False,None,"delivery-inventory-not-covered"
    try:
        r = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, None, "aws-command-timeout"
    if r.returncode:
        return False, None, aws_response().classify_error(parts[0], parts[1], r.stderr)
    try: return True, decoded_aws_response(r.stdout), "ok"
    except json.JSONDecodeError: return False, None, "aws-response-invalid"
def report(verdict: str, *codes: str):
    print(json.dumps({"schema":"deploy/runtime-deployment-report/v1", "target":"kanbien-core-platform", "stack":STACK, "verdict":verdict, "findings":[{"code":c} for c in codes]}, sort_keys=True))
def initial_change_set_is_reviewable(change, runtime_stack_status: str | None) -> bool:
    """An initial CloudFormation change set has no stack or an empty review stack."""
    reported_type = change.get("ChangeSetType")
    return (
        runtime_stack_status in (None, "REVIEW_IN_PROGRESS")
        and change.get("Status") == "CREATE_COMPLETE"
        and reported_type in (None, "CREATE")
    )
def update_change_set_is_reviewable(change, runtime_stack_status: str | None) -> bool:
    """AWS may omit ChangeSetType for an existing-stack UPDATE response."""
    return (
        runtime_stack_status in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
        and change.get("Status") == "CREATE_COMPLETE"
        and change.get("ChangeSetType") in (None, "UPDATE")
    )
def candidate(path: Path):
    validator=ROOT/"scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    r=subprocess.run(["bash",str(validator),"--receipt",str(path),"--expected-target","kanbien-core-platform","--expected-candidate","kanbien-core-server-candidate","--expected-package-contract","kanbien-core-server-image","--expected-program","kanbien-core-server","--json"],capture_output=True,text=True)
    return json.loads(r.stdout) if not r.returncode else None
def prerequisites(receipt, operation):
    """Direct Python and shell entrypoints share every mutation prerequisite."""
    base=ROOT/"scripts/04.deploy/lifecycle"
    checks=[
        (base/"50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.sh", [], "release-contract-not-proven"),
        (base/"50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh", ["--receipt",str(receipt),"--operation",operation], "runtime-update-alignment-not-proven"),
        (base/"00-target-alignment/targets/kanbien-core-platform/validate-cost-condition/script.sh", [], "cost-condition-not-proven"),
    ]
    for path,arguments,code in checks:
        try:r=subprocess.run(["bash",str(path),*arguments,"--json"],capture_output=True,text=True,timeout=120)
        except (OSError,subprocess.TimeoutExpired):return code
        if r.returncode:return code
    return None

def matching_parameters(value, receipt):
    entries=value.get("Parameters") if isinstance(value,dict) else None
    if not isinstance(entries,list) or any(not isinstance(item,dict) for item in entries):return False
    params={item.get("ParameterKey"):item.get("ParameterValue") for item in entries}
    return len(params)==len(entries) and params.get("ImageDigest")==receipt["image_digest"] and params.get("SourceRevision")==receipt["source_revision"]

def parameter_values(value, previous=None):
    entries=value.get("Parameters") if isinstance(value,dict) else None
    if not isinstance(entries,list):return None
    result={}
    for item in entries:
        if not isinstance(item,dict):return None
        key=item.get("ParameterKey");supplied=item.get("ParameterValue")
        if not isinstance(key,str) or not key or key in result:return None
        flag=item.get("UsePreviousValue",False)
        if not isinstance(flag,bool):return None
        if flag:
            if previous is None or key not in previous:return None
            if supplied is not None and supplied!=previous[key]:return None
            supplied=previous[key]
        if not isinstance(supplied,str) or not supplied or supplied=="****":return None
        result[key]=supplied
    return result


def reviewed_parameters_match(change, stack, receipt, source):
    current=parameter_values(stack)
    actual=parameter_values(change,current)
    declared=source.get("Parameters")
    if current is None or actual is None or not isinstance(declared,dict):return False
    return (set(actual)==set(current)==set(declared)
        and actual.get("ImageDigest")==receipt["image_digest"]
        and actual.get("SourceRevision")==receipt["source_revision"]
        and all(actual[key]==value for key,value in current.items() if key not in {"ImageDigest","SourceRevision"}))


def reviewed_templates_match(name, source):
    # Image-only update/restoration must preserve the deployed configuration as
    # well as match the source that passed the release-contract prerequisite.
    for label,selection in [("runtime-template",[]),("change-set-template",["--change-set-name",name])]:
        ok,observed,code=aws("cloudformation","get-template","--stack-name",STACK,*selection,"--template-stage","Original")
        if not ok:return label+"-unavailable",code
        try:
            if not isinstance(observed,dict):raise ValueError("invalid template response")
            if not template_adapter().templates_equal(observed.get("TemplateBody"),source):return label+"-mismatch",None
        except ValueError:return label+"-invalid",None
    return None,None


def reviewed_resources_match(change):
    allowed={"BootstrapRuntimeTaskDefinition":"AWS::ECS::TaskDefinition","ReleaseVerifierTaskDefinition":"AWS::ECS::TaskDefinition","BootstrapRuntimeService":"AWS::ECS::Service"}
    changes=change.get("Changes")
    if not isinstance(changes,list) or not changes or change.get("NextToken"):return False
    seen=set()
    for item in changes:
        resource=item.get("ResourceChange") if isinstance(item,dict) else None
        if not isinstance(resource,dict):return False
        logical=resource.get("LogicalResourceId")
        if logical not in allowed or logical in seen or resource.get("ResourceType")!=allowed[logical] or resource.get("Action")!="Modify":return False
        if logical=="BootstrapRuntimeService" and resource.get("Replacement")!="False":return False
        seen.add(logical)
    return True

def reconcile(name, receipt):
    """Only observe the existing named operation; an absent review is uncertain."""
    ok,change,code=aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
    if not ok or not isinstance(change,dict):report("uncertain",code if not ok else "runtime-change-set-observation-invalid");return 1
    actual=change.get("ChangeSetName")
    if actual!=name and not (isinstance(actual,str) and actual.split(":changeSet/",1)[-1].split("/",1)[0]==name):report("blocked","runtime-change-set-identity-invalid");return 1
    if change.get("Status") in {"CREATE_PENDING","CREATE_IN_PROGRESS"}:report("pending","runtime-change-set-review-pending");return 1
    if change.get("Status") in {"FAILED","DELETE_FAILED","DELETE_COMPLETE"}:report("failed","runtime-change-set-failed");return 1
    if not matching_parameters(change,receipt):report("blocked","change-set-candidate-mismatch");return 1
    if change.get("ExecutionStatus") in {"AVAILABLE","EXECUTE_IN_PROGRESS"}:report("pending","runtime-change-set-execution-pending");return 1
    if change.get("ExecutionStatus")!="EXECUTE_COMPLETE":report("uncertain","runtime-change-set-execution-unknown");return 1
    ok,data,code=aws("cloudformation","describe-stacks","--stack-name",STACK)
    stacks=data.get("Stacks") if ok and isinstance(data,dict) else None
    if not isinstance(stacks,list) or len(stacks)!=1 or not isinstance(stacks[0],dict):report("uncertain",code if not ok else "runtime-stack-observation-invalid");return 1
    stack=stacks[0];status=stack.get("StackStatus")
    if status in {"UPDATE_IN_PROGRESS","UPDATE_COMPLETE_CLEANUP_IN_PROGRESS","UPDATE_ROLLBACK_IN_PROGRESS","UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"}:report("pending","runtime-stack-update-pending");return 1
    if status in {"UPDATE_FAILED","UPDATE_ROLLBACK_FAILED","UPDATE_ROLLBACK_COMPLETE","DELETE_COMPLETE"}:report("failed","runtime-stack-update-failed");return 1
    if status!="UPDATE_COMPLETE" or not matching_parameters(stack,receipt):report("uncertain","runtime-stack-completion-identity-unproven");return 1
    report("deployed-awaiting-private-verification","runtime-change-set-executed");return 0

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--operation", choices=("update", "restore"))
    parser.add_argument("--approved-change-set")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or args.operation is None or args.approved_change_set is None:
        report("blocked", "runtime-deployment-arguments-invalid"); return 1
    c = candidate(args.receipt)
    if not c:
        report("blocked", "package-custody-receipt-invalid"); return 1
    expected = f"kanbien-core-platform-{args.operation}-{c['image_digest'][7:19]}"
    if args.approved_change_set != expected:
        report("blocked", "approved-change-set-does-not-match-qualified-digest"); return 1
    if args.reconcile:return reconcile(expected,c)
    try:
        source_bytes=TEMPLATE.read_bytes()
        source=template_adapter().template(source_bytes.decode("utf-8"))
    except (OSError,UnicodeError,ValueError):report("blocked","runtime-template-source-invalid");return 1
    precondition=prerequisites(args.receipt,args.operation)
    if precondition:report("blocked",precondition);return 1
    ok, change, code = aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        report("blocked", code); return 1
    stack_ok, stack, stack_code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks=stack.get("Stacks") if stack_ok and isinstance(stack,dict) else None
    runtime_stack_status = stacks[0].get("StackStatus") if isinstance(stacks,list) and len(stacks)==1 and isinstance(stacks[0],dict) else None
    if not stack_ok:
        report("blocked", stack_code); return 1
    if not isinstance(change,dict):report("uncertain","runtime-change-set-observation-invalid");return 1
    if change.get("ExecutionStatus") != "AVAILABLE":return reconcile(expected,c)
    if not update_change_set_is_reviewable(change, runtime_stack_status):
        report("blocked", "change-set-not-reviewable"); return 1
    if not reviewed_parameters_match(change,stacks[0],c,source):
        report("blocked", "change-set-candidate-mismatch"); return 1
    actual_name=change.get("ChangeSetName")
    if actual_name!=expected and not (isinstance(actual_name,str) and actual_name.startswith("arn:aws:cloudformation:") and actual_name.split(":changeSet/",1)[-1].split("/",1)[0]==expected):report("blocked","runtime-change-set-identity-invalid");return 1
    if not reviewed_resources_match(change):
        report("blocked", "change-set-resource-boundary-violated"); return 1
    template_code,provider_code=reviewed_templates_match(expected,source)
    if template_code:report("blocked",template_code,*([provider_code] if provider_code else []));return 1
    try:unchanged=TEMPLATE.read_bytes()==source_bytes
    except OSError:unchanged=False
    if not unchanged:report("blocked","runtime-template-source-changed");return 1
    ok, _, code = aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        report("uncertain", code); return 1
    return reconcile(expected,c)

if __name__ == "__main__": sys.exit(main())

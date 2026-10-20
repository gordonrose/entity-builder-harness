#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.execute-runtime-change-set
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Execute only the exact reviewed initial-runtime change set derived from a qualified immutable receipt.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.deploy-runtime-change-set.wrapper
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION, STACK = "kanbien-dev", "eu-west-1", "kanbien-core-platform-bootstrap-runtime"
ALLOWED_TYPES = {"AWS::ECS::TaskDefinition", "AWS::ECS::Service"}
def decoded_aws_response(raw: str):
    """Mutation commands may succeed without a response body."""
    return {} if not raw.strip() else json.loads(raw)
def aws(*parts: str):
    r = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if r.returncode:
        text=r.stderr.lower()
        if "accessdenied" in text or "not authorized" in text: return False, None, "aws-access-denied"
        if "does not exist" in text: return False, None, "aws-resource-missing"
        return False, None, "aws-command-failed"
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
    return (
        runtime_stack_status in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
        and change.get("Status") == "CREATE_COMPLETE"
        and change.get("ChangeSetType") == "UPDATE"
    )
def candidate(path: Path):
    validator=ROOT/"scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    r=subprocess.run(["bash",str(validator),"--receipt",str(path),"--expected-target","kanbien-core-platform","--expected-candidate","kanbien-core-server-candidate","--expected-package-contract","kanbien-core-server-image","--expected-program","kanbien-core-server","--json"],capture_output=True,text=True)
    return json.loads(r.stdout) if not r.returncode else None
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--operation", choices=("update", "restore"))
    parser.add_argument("--approved-change-set")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or args.operation is None or args.approved_change_set is None:
        report("blocked", "runtime-deployment-arguments-invalid"); return 1
    c = candidate(args.receipt)
    if not c:
        report("blocked", "package-custody-receipt-invalid"); return 1
    expected = f"kanbien-core-platform-{args.operation}-{c['image_digest'][7:19]}"
    if args.approved_change_set != expected:
        report("blocked", "approved-change-set-does-not-match-qualified-digest"); return 1
    ok, change, code = aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        report("blocked", code); return 1
    stack_ok, stack, stack_code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    runtime_stack_status = stack.get("Stacks", [{}])[0].get("StackStatus") if stack_ok else None
    if not stack_ok:
        report("blocked", stack_code); return 1
    if not update_change_set_is_reviewable(change, runtime_stack_status):
        report("blocked", "change-set-not-reviewable"); return 1
    parameters = {x.get("ParameterKey"): x.get("ParameterValue") for x in change.get("Parameters", []) if isinstance(x, dict)}
    if parameters.get("ImageDigest") != c["image_digest"] or parameters.get("SourceRevision") != c["source_revision"]:
        report("blocked", "change-set-candidate-mismatch"); return 1
    types = {x.get("ResourceChange", {}).get("ResourceType") for x in change.get("Changes", []) if isinstance(x, dict)}
    if not types or not types <= ALLOWED_TYPES:
        report("blocked", "change-set-resource-boundary-violated"); return 1
    ok, _, code = aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok:
        report("blocked", code); return 1
    result = subprocess.run(["aws", "cloudformation", "wait", "stack-update-complete", "--stack-name", STACK, "--profile", PROFILE, "--region", REGION], capture_output=True, text=True)
    if result.returncode:
        report("blocked", "runtime-stack-not-update-complete"); return 1
    report("deployed-awaiting-private-verification", f"runtime-{args.operation}-change-set-executed"); return 0
if __name__ == "__main__": sys.exit(main())

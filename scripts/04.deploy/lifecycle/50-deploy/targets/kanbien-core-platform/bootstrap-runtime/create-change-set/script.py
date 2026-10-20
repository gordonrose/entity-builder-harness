#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.create-runtime-change-set
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Create one fixed, reviewable CloudFormation change set for the qualified first core runtime release.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.create-runtime-change-set.wrapper
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.sh
#   - id: deploy.command.kanbien-core-platform.create-change-set.readme
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/README.md
#   effects: [aws-mutation]
"""Fixed target change-set creation; no target or stack selector is accepted."""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION = "kanbien-dev", "eu-west-1"
FOUNDATION, RUNTIME = "kanbien-core-platform-foundation", "kanbien-core-platform-bootstrap-runtime"
REPOSITORY = "kanbien-core-platform/core-server"
REQUIRED = {"VpcId", "PrivateSubnetIds", "RepositoryUri", "ClusterArn", "LogGroupName", "TaskExecutionRoleArn", "ServiceSecurityGroupId", "VerifierSecurityGroupId", "ServiceDiscoveryArn"}
ALLOWED_TYPES = {"AWS::ECS::TaskDefinition", "AWS::ECS::Service"}

def aws(*parts: str) -> tuple[bool, object, str]:
    completed = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
    if completed.returncode:
        lowered = completed.stderr.lower()
        if "accessdenied" in lowered or "not authorized" in lowered: return False, None, "aws-access-denied"
        if "does not exist" in lowered: return False, None, "aws-resource-missing"
        if "must match pattern" in lowered or "parameter validation failed" in lowered: return False, None, "aws-parameter-invalid"
        return False, None, "aws-command-failed"
    try: return True, json.loads(completed.stdout), "ok"
    except json.JSONDecodeError: return False, None, "aws-response-invalid"

def fail(code: str) -> int:
    print(json.dumps({"schema":"deploy/runtime-change-set-report/v1", "target":"kanbien-core-platform", "verdict":"blocked", "findings":[{"code":code}]})); return 1

def receipt(path: Path) -> tuple[str, str] | None:
    validator = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    result = subprocess.run(["bash", str(validator), "--receipt", str(path), "--expected-target", "kanbien-core-platform", "--expected-candidate", "kanbien-core-server-candidate", "--expected-package-contract", "kanbien-core-server-image", "--expected-program", "kanbien-core-server", "--json"], capture_output=True, text=True)
    if result.returncode: return None
    data = json.loads(result.stdout); return data["image_digest"], data["source_revision"]

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown: return fail("runtime-change-set-arguments-invalid")
    candidate = receipt(args.receipt)
    if candidate is None: return fail("package-custody-receipt-invalid")
    digest, revision = candidate
    ok, foundation, code = aws("cloudformation", "describe-stacks", "--stack-name", FOUNDATION)
    if not ok: return fail(code)
    stacks = foundation.get("Stacks", []) if isinstance(foundation, dict) else []
    outputs = {item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", [])} if stacks else {}
    if not REQUIRED <= set(outputs) or any(not isinstance(outputs[key], str) or not outputs[key] for key in REQUIRED): return fail("foundation-runtime-parameters-unavailable")
    change_set = f"kanbien-core-platform-a-{digest[7:19]}"
    parameters = [
        {"ParameterKey":"ClusterArn", "ParameterValue":outputs["ClusterArn"]}, {"ParameterKey":"PrivateSubnetIds", "ParameterValue":outputs["PrivateSubnetIds"]},
        {"ParameterKey":"ServiceSecurityGroupId", "ParameterValue":outputs["ServiceSecurityGroupId"]}, {"ParameterKey":"VerifierSecurityGroupId", "ParameterValue":outputs["VerifierSecurityGroupId"]},
        {"ParameterKey":"ServiceDiscoveryArn", "ParameterValue":outputs["ServiceDiscoveryArn"]}, {"ParameterKey":"TaskExecutionRoleArn", "ParameterValue":outputs["TaskExecutionRoleArn"]},
        {"ParameterKey":"LogGroupName", "ParameterValue":outputs["LogGroupName"]}, {"ParameterKey":"ImageRepositoryUri", "ParameterValue":outputs["RepositoryUri"]},
        {"ParameterKey":"ImageDigest", "ParameterValue":digest}, {"ParameterKey":"SourceRevision", "ParameterValue":revision},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as file:
        json.dump(parameters, file); file.flush()
        ok, _, code = aws("cloudformation", "create-change-set", "--stack-name", RUNTIME, "--change-set-name", change_set, "--change-set-type", "CREATE", "--template-body", f"file://{ROOT / 'infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml'}", "--parameters", f"file://{file.name}", "--capabilities", "CAPABILITY_NAMED_IAM", "--tags", "Key=Target,Value=kanbien-core-platform")
    if not ok: return fail(code)
    print(json.dumps({"schema":"deploy/runtime-change-set-report/v1", "target":"kanbien-core-platform", "stack":"kanbien-core-platform-bootstrap-runtime", "change_set":change_set, "image_digest":digest, "source_revision":revision, "verdict":"created-awaiting-review", "findings":[]} , sort_keys=True)); return 0
if __name__ == "__main__": sys.exit(main())

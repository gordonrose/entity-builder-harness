#!/usr/bin/env python3
"""Create exactly one reviewable CREATE change set for the persistence candidate."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"


def controls():
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("persistence_prepare", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value = {"schema": "deploy/persistence-change-set-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "stack": STACK, "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "created-awaiting-review" else 1


def package_gates(receipt: Path) -> bool:
    checks = [
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/script.sh"), "--json"],
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access/script.sh"), "--json"],
        ["python3", str(ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py"), "--json"],
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh"), "--target-root", str(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes"), "--json"],
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh"), "--scope-contract", str(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"), "--json"],
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh"), "--scope-contract", str(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"), "--workload-binding", str(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/10-workload-binding/workload-binding.yml"), "--json"],
    ]
    return all(subprocess.run(command, capture_output=True, text=True).returncode == 0 for command in checks)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", "persistence-change-set-arguments-invalid")
    module = controls()
    receipt = module.validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", "package-custody-receipt-invalid")
    if not package_gates(args.receipt):
        return report("blocked", "persistence-declaration-or-package-gate-not-proven")
    outputs, code = module.foundation_outputs()
    if outputs is None:
        return report("blocked", code)
    infrastructure, code = module.infrastructure_parameters(outputs)
    if infrastructure is None:
        return report("blocked", code)
    if not module.candidate_image(receipt)[0]:
        return report("blocked", "persistence-candidate-image-unavailable")
    if not module.live_budget()[0]:
        return report("blocked", "target-budget-live-configuration-invalid")
    ok, stack, code = module.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    if ok:
        status = stack.get("Stacks", [{}])[0].get("StackStatus") if isinstance(stack, dict) else None
        return report("blocked", "persistence-candidate-stack-already-exists" if status else "persistence-candidate-stack-state-unknown")
    if code != "aws-resource-missing":
        return report("blocked", code)
    digest, revision = receipt["image_digest"], receipt["source_revision"]
    name = f"kanbien-core-platform-persistence-create-{digest[7:19]}"
    parameters = [
        {"ParameterKey": "VpcId", "ParameterValue": infrastructure["VpcId"]},
        {"ParameterKey": "VpcCidr", "ParameterValue": infrastructure["VpcCidr"]},
        {"ParameterKey": "PrivateSubnetIds", "ParameterValue": infrastructure["PrivateSubnetIds"]},
        {"ParameterKey": "ClusterArn", "ParameterValue": infrastructure["ClusterArn"]},
        {"ParameterKey": "NamespaceId", "ParameterValue": infrastructure["NamespaceId"]},
        {"ParameterKey": "EndpointSecurityGroupId", "ParameterValue": infrastructure["EndpointSecurityGroupId"]},
        {"ParameterKey": "S3ArtifactPrefixListId", "ParameterValue": infrastructure["S3ArtifactPrefixListId"]},
        {"ParameterKey": "VerifierSecurityGroupId", "ParameterValue": infrastructure["VerifierSecurityGroupId"]},
        {"ParameterKey": "LogGroupName", "ParameterValue": infrastructure["LogGroupName"]},
        {"ParameterKey": "ImageRepositoryArn", "ParameterValue": f"arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/core-server"},
        {"ParameterKey": "ImageRepositoryUri", "ParameterValue": outputs["RepositoryUri"]},
        {"ParameterKey": "ImageDigest", "ParameterValue": digest},
        {"ParameterKey": "SupportImageDigest", "ParameterValue": digest},
        # The qualified persistence image contains the isolated restore
        # verifier entrypoint as well as the server. Keep both task
        # definitions bound to the same immutable candidate on a clean
        # CREATE, rather than relying on an undeclared template default.
        {"ParameterKey": "RestoreVerifierImageDigest", "ParameterValue": digest},
        {"ParameterKey": "SourceRevision", "ParameterValue": revision},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as parameter_file:
        json.dump(parameters, parameter_file)
        parameter_file.flush()
        ok, _, code = module.aws(
            "cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name,
            "--change-set-type", "CREATE", "--template-body", f"file://{TEMPLATE}",
            "--parameters", f"file://{parameter_file.name}", "--capabilities", "CAPABILITY_NAMED_IAM",
            "--tags", "Key=Target,Value=kanbien-core-platform",
        )
    if not ok:
        return report("blocked", code)
    return report("created-awaiting-review", facts={"change_set": name, "candidate_image_digest": digest, "candidate_source_revision": revision})


if __name__ == "__main__":
    raise SystemExit(main())

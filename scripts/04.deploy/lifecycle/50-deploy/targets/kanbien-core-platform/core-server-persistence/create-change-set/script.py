#!/usr/bin/env python3
"""Create exactly one reviewable CREATE change set for the persistence candidate."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
DIAGNOSTICS = ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py"
DIAGNOSTIC_DIRECTORY = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/operation-diagnostics"


def controls():
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("persistence_prepare", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def diagnostic_controls():
    spec = importlib.util.spec_from_file_location("deployment_operation_diagnostics", DIAGNOSTICS)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def diagnostic_path_is_governed(path: Path) -> bool:
    try:
        path.resolve().relative_to(DIAGNOSTIC_DIRECTORY.resolve())
    except ValueError:
        return False
    return path.suffix == ".json"


def diagnostics_ready(path: Path) -> bool:
    """Preflight local report tooling before a protected provider mutation."""
    try:
        diagnostic_controls()
    except Exception:
        return False
    return path.resolve().parent == DIAGNOSTIC_DIRECTORY.resolve() and path.parent.is_dir() and os.access(path.parent, os.W_OK)


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value = {"schema": "deploy/persistence-change-set-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "stack": STACK, "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "created-awaiting-review" else 1


def retain_diagnostic(module, *, name: str, receipt: dict, path: Path, original_code: str, outcome: str, fallback_code: str) -> str | None:
    """Retain a safe result for this named operation without changing its result.

    This calls only the existing controller's read-only adapter after a failure.
    If that observation or the receipt write fails, the caller retains its
    original verdict and adds a distinct collection failure finding.
    """
    try:
        diagnostics = diagnostic_controls()
        classification, facts, diagnosed_outcome, collection = diagnostics.collect_cloudformation_failure(
            module.aws, stack_name=STACK, change_set_name=name,
        )
        facts = {**facts, "change_set_id": name, "artifact_identity": receipt["image_digest"]}
        report_value = diagnostics.build_report(
            target="kanbien-core-platform", scope="core-server-persistence", operation_id=name,
            stage="deploy", original_code=original_code, exit_status=1,
            outcome=outcome if outcome in {"rejected", "failed", "pending", "unknown"} else diagnosed_outcome,
            classification=classification if collection != "failed" else diagnostics.classify_aws_error(fallback_code),
            evidence_reference=f"receipt-path:operation-diagnostics/{name}.json",
            next_decision="observe-current-operation" if outcome == "unknown" else "inspect-retained-evidence",
            collection_status=collection, facts=facts,
        )
        diagnostics.write_report(path, report_value)
    except Exception:
        return "persistence-change-set-diagnostic-collection-failed"
    return None


def package_gates(receipt: Path, *, coverage_checked: bool = False) -> bool:
    if not coverage_checked and not controls().declaration_covered():
        return False
    checks = [
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/script.sh"), "--json"],
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access/script.sh"), "--json"],
        ["python3", str(ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py"), "--json"],
        # This aggregate validates health, secret dependencies and persistence diagnostics for every indexed scope.
        ["bash", str(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh"), "--target-root", str(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes"), "--json"],
    ]
    return all(subprocess.run(command, capture_output=True, text=True).returncode == 0 for command in checks)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--diagnostic-report", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", "persistence-change-set-arguments-invalid")
    module = controls()
    receipt = module.validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", "package-custody-receipt-invalid")
    name = f"kanbien-core-platform-persistence-create-{receipt['image_digest'][7:19]}"
    diagnostic_path = args.diagnostic_report or DIAGNOSTIC_DIRECTORY / f"{name}.json"
    if not module.declaration_covered():
        return report("blocked", "persistence-declaration-coverage-gap")
    # A declaration gap is a local, pre-provider rejection. Require retained
    # diagnostics before reconciliation or a provider mutation, not before the
    # existing structural guard can state its precise failure.
    if not diagnostic_path_is_governed(diagnostic_path) or not diagnostics_ready(diagnostic_path):
        return report("blocked", "persistence-change-set-diagnostic-route-unavailable")
    if args.reconcile:
        return reconcile(module, name, receipt, diagnostic_path)
    if not package_gates(args.receipt, coverage_checked=True):
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
    parameters = [{"ParameterKey": key, "ParameterValue": value} for key, value in module.candidate_parameters(outputs, infrastructure, receipt).items()]
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
        finding = retain_diagnostic(module, name=name, receipt=receipt, path=diagnostic_path,
                                    original_code="persistence-change-set-submission-uncertain",
                                    outcome="unknown", fallback_code=code)
        return report("uncertain", code, *(finding,) if finding else (), facts={"change_set": name})
    return reconcile(module, name, receipt, diagnostic_path)


def reconcile(module, name: str, receipt: dict, diagnostic_path: Path | None = None) -> int:
    facts = {"change_set": name, "candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"]}
    ok, change, code = module.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    diagnostic_path = diagnostic_path or DIAGNOSTIC_DIRECTORY / f"{name}.json"
    if not ok or not isinstance(change, dict):
        finding = retain_diagnostic(module, name=name, receipt=receipt, path=diagnostic_path,
                                    original_code="persistence-change-set-observation-uncertain",
                                    outcome="unknown", fallback_code=code)
        return report("uncertain", "persistence-change-set-observation-uncertain", *(finding,) if finding else (), facts=facts)
    if not module.change_name_matches(change.get("ChangeSetName"), name):
        return report("blocked", "persistence-change-set-identity-invalid", facts=facts)
    if change.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}:
        return report("pending", "persistence-change-set-creation-pending", facts=facts)
    if change.get("Status") in {"FAILED", "DELETE_FAILED", "DELETE_COMPLETE"}:
        finding = retain_diagnostic(module, name=name, receipt=receipt, path=diagnostic_path,
                                    original_code="persistence-change-set-creation-failed",
                                    outcome="rejected", fallback_code="aws-command-failed")
        return report("failed", "persistence-change-set-creation-failed", *(finding,) if finding else (), facts=facts)
    parameters = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    expected = {"ImageDigest": receipt["image_digest"], "RestoreVerifierImageDigest": receipt["image_digest"], "SourceRevision": receipt["source_revision"]}
    if change.get("Status") != "CREATE_COMPLETE" or change.get("ExecutionStatus") != "AVAILABLE" or any(parameters.get(key) != value for key, value in expected.items()):
        return report("uncertain", "persistence-change-set-review-identity-unproven", facts=facts)
    return report("created-awaiting-review", "persistence-change-set-ready-for-review", facts=facts)


if __name__ == "__main__":
    raise SystemExit(main())

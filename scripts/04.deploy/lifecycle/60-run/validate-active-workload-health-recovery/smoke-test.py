#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-active-workload-health-recovery
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise active-scope inventory coverage and retiring legacy-exception boundaries without a provider call.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.validate-active-workload-health-recovery.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/smoke-test.sh
"""Focused fixtures for active workload health/recovery inventory validation."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
CHECK = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh"
SCOPES = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes"


def run(target_root: Path) -> tuple[int, dict[str, Any]]:
    result = subprocess.run([str(CHECK), "--target-root", str(target_root), "--json"], check=False, capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)


def expect_failure(target_root: Path, code: str) -> None:
    status, report = run(target_root)
    if status == 0 or code not in {item["code"] for item in report["findings"]}:
        raise AssertionError(f"expected {code}, received {report}")


def index(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    yaml.safe_dump(value, path.open("w", encoding="utf-8"), sort_keys=False)


def legacy_exception(workload: str) -> dict[str, str]:
    return {
        "status": "retiring-reference-only",
        "legacy_workload": workload,
        "reason": "pre-framework-reference-remains-read-only-during-retirement",
        "owner": "platform-runtime",
        "replacement_path": "kanbien-core-platform/20-scopes/bootstrap-runtime",
        "review_condition": "before-new-workload-acceptance",
        "retirement_condition": "remove-after-replacement-is-accepted",
    }


def main() -> int:
    status, report = run(SCOPES)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"accepted target inventory failed: {report}")

    with tempfile.TemporaryDirectory() as directory:
        target_root = Path(directory) / "20-scopes"
        shutil.copytree(SCOPES, target_root)
        index_path = target_root / "scope-index.yml"

        valid = index(index_path)
        valid["legacy_exceptions"] = [legacy_exception("kanbien/staging/public-server")]
        write(index_path, valid)
        status, report = run(target_root)
        if status != 0 or report["verdict"] != "passed":
            raise AssertionError(f"valid legacy exception failed: {report}")

        invalid = copy.deepcopy(valid)
        invalid["legacy_exceptions"][0]["legacy_workload"] = "20-scopes/bootstrap-runtime"
        write(index_path, invalid)
        expect_failure(target_root, "legacy-exception-cannot-cover-active-scope")

        incomplete = copy.deepcopy(valid)
        incomplete["active_scopes"] = []
        write(index_path, incomplete)
        expect_failure(target_root, "active-scope-inventory-missing")

        binding_only = copy.deepcopy(valid)
        binding_only["active_scopes"].append({
            "id": "binding-only",
            "declaration": "binding-only/00-declaration/declaration-contract.yml",
            "workload_binding": "binding-only/10-workload-binding/workload-binding.yml",
        })
        binding_path = target_root / "binding-only" / "10-workload-binding"
        binding_path.mkdir(parents=True)
        shutil.copyfile(target_root / "bootstrap-runtime" / "10-workload-binding" / "workload-binding.yml", binding_path / "workload-binding.yml")
        write(index_path, binding_only)
        expect_failure(target_root, "active-scope-declaration-missing")

        redirected = copy.deepcopy(valid)
        redirected["active_scopes"].append({
            "id": "another-scope",
            "declaration": "bootstrap-runtime/00-declaration/declaration-contract.yml",
            "workload_binding": "bootstrap-runtime/10-workload-binding/workload-binding.yml",
        })
        write(index_path, redirected)
        expect_failure(target_root, "active-scope-path-noncanonical")

        misidentified = copy.deepcopy(valid)
        shutil.copytree(target_root / "bootstrap-runtime", target_root / "misidentified-scope")
        misidentified["active_scopes"].append({
            "id": "misidentified-scope",
            "declaration": "misidentified-scope/00-declaration/declaration-contract.yml",
            "workload_binding": "misidentified-scope/10-workload-binding/workload-binding.yml",
        })
        write(index_path, misidentified)
        expect_failure(target_root, "active-scope-identity-mismatch")

        missing_secret_declaration = copy.deepcopy(valid)
        contract_path = target_root / "bootstrap-runtime" / "00-declaration" / "declaration-contract.yml"
        contract = index(contract_path)
        contract["configuration"].pop("secret_dependencies")
        write(contract_path, contract)
        write(index_path, missing_secret_declaration)
        expect_failure(target_root, "active-scope-secret-dependency-invalid")

    print("Active workload health/recovery inventory tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

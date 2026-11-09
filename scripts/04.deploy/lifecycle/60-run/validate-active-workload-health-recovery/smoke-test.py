#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-active-workload-health-recovery
#   version: 5
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise scope lifecycle, active workload ownership, and retiring legacy-exception boundaries without a provider call.
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


def expect_success(target_root: Path) -> None:
    status, report = run(target_root)
    if status != 0 or report["verdict"] != "passed":
        raise AssertionError(f"expected pass, received {report}")


def index(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    yaml.safe_dump(value, path.open("w", encoding="utf-8"), sort_keys=False)


def copied_scope(target_root: Path, scope_id: str) -> None:
    source = target_root / "bootstrap-runtime"
    destination = target_root / scope_id
    shutil.copytree(source, destination)
    contract_path = destination / "00-declaration" / "declaration-contract.yml"
    contract = index(contract_path)
    contract.pop("acceptance", None)  # This fixture exercises health/ownership, not release acceptance.
    contract["scope"] = scope_id
    contract["id"] = f"kanbien-core-platform-{scope_id}"
    write(contract_path, contract)
    binding_path = destination / "10-workload-binding" / "workload-binding.yml"
    binding = index(binding_path)
    binding["scope"] = scope_id
    binding["id"] = f"kanbien-core-platform-{scope_id}-workload"
    write(binding_path, binding)


def scope_entry(scope_id: str, lifecycle: str, **extra: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": scope_id,
        "lifecycle": lifecycle,
        "declaration": f"{scope_id}/00-declaration/declaration-contract.yml",
        "workload_binding": f"{scope_id}/10-workload-binding/workload-binding.yml",
        "workload_ownership": ["core-server-service", "private-release-verifier-task"],
    }
    entry.update(extra)
    return entry


def selected_scope(value: dict[str, Any], scope_id: str) -> dict[str, Any]:
    matches = [item for item in value["scopes"] if item["id"] == scope_id]
    assert len(matches) == 1
    return matches[0]


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
        expect_failure(target_root, "legacy-exception-cannot-cover-new-framework-scope")

        incomplete = copy.deepcopy(valid)
        incomplete["scopes"] = []
        write(index_path, incomplete)
        expect_failure(target_root, "scope-lifecycle-inventory-missing")

        binding_only = copy.deepcopy(valid)
        binding_only["scopes"].append(scope_entry("binding-only", "active"))
        binding_path = target_root / "binding-only" / "10-workload-binding"
        binding_path.mkdir(parents=True)
        shutil.copyfile(target_root / "bootstrap-runtime" / "10-workload-binding" / "workload-binding.yml", binding_path / "workload-binding.yml")
        write(index_path, binding_only)
        expect_failure(target_root, "scope-lifecycle-declaration-missing")

        redirected = copy.deepcopy(valid)
        redirected["scopes"].append({
            **scope_entry("another-scope", "active"),
            "declaration": "bootstrap-runtime/00-declaration/declaration-contract.yml",
            "workload_binding": "bootstrap-runtime/10-workload-binding/workload-binding.yml",
        })
        write(index_path, redirected)
        expect_failure(target_root, "scope-lifecycle-path-noncanonical")

        misidentified = copy.deepcopy(valid)
        shutil.copytree(target_root / "bootstrap-runtime", target_root / "misidentified-scope")
        misidentified["scopes"].append(scope_entry("misidentified-scope", "active"))
        write(index_path, misidentified)
        expect_failure(target_root, "scope-lifecycle-identity-mismatch")

        missing_secret_declaration = copy.deepcopy(valid)
        contract_path = target_root / "bootstrap-runtime" / "00-declaration" / "declaration-contract.yml"
        contract = index(contract_path)
        contract["configuration"].pop("secret_dependencies")
        write(contract_path, contract)
        write(index_path, missing_secret_declaration)
        expect_failure(target_root, "scope-lifecycle-secret-dependency-invalid")

    with tempfile.TemporaryDirectory() as directory:
        target_root = Path(directory) / "20-scopes"
        shutil.copytree(SCOPES, target_root)
        index_path = target_root / "scope-index.yml"
        valid = index(index_path)
        # Isolate the generic successor fixture from the target's now-active
        # persistence scope.  Recreate a minimal active predecessor so this
        # fixture remains a true candidate-to-active transition test.
        shutil.rmtree(target_root / "core-server-persistence")
        unrelated = {item["id"]: copy.deepcopy(item) for item in valid["scopes"]
                     if item["id"] not in {"bootstrap-runtime", "core-server-persistence"}}
        valid["scopes"] = [scope_entry("bootstrap-runtime", "active"), *unrelated.values()]
        copied_scope(target_root, "core-server-persistence")

        def assert_unrelated_preserved(value: dict[str, Any]) -> None:
            for scope_id, original in unrelated.items():
                assert selected_scope(value, scope_id) == original
                assert (target_root / scope_id).is_dir()

        candidate = copy.deepcopy(valid)
        candidate["scopes"].append(scope_entry("core-server-persistence", "candidate", predecessor="bootstrap-runtime"))
        write(index_path, candidate)
        expect_success(target_root)
        assert_unrelated_preserved(index(index_path))

        candidate_missing_predecessor = copy.deepcopy(candidate)
        selected_scope(candidate_missing_predecessor, "core-server-persistence").pop("predecessor")
        write(index_path, candidate_missing_predecessor)
        expect_failure(target_root, "scope-lifecycle-candidate-predecessor-invalid")

        duplicate_active = copy.deepcopy(candidate)
        selected_scope(duplicate_active, "core-server-persistence").pop("predecessor")
        selected_scope(duplicate_active, "core-server-persistence")["lifecycle"] = "active"
        write(index_path, duplicate_active)
        expect_failure(target_root, "active-workload-ownership-duplicate")

        succession = copy.deepcopy(candidate)
        selected_scope(succession, "bootstrap-runtime")["lifecycle"] = "accepted-historical"
        selected_scope(succession, "bootstrap-runtime")["successor"] = "core-server-persistence"
        selected_scope(succession, "core-server-persistence")["lifecycle"] = "active"
        write(index_path, succession)
        expect_success(target_root)
        assert_unrelated_preserved(index(index_path))

        invalid_succession = copy.deepcopy(succession)
        selected_scope(invalid_succession, "core-server-persistence").pop("predecessor")
        write(index_path, invalid_succession)
        expect_failure(target_root, "scope-lifecycle-transition-invalid")

    independent_candidates()
    print("Active workload health/recovery inventory tests passed.")
    return 0


def independent_candidates() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target_root = Path(directory) / "20-scopes"
        shutil.copytree(SCOPES, target_root)
        copied_scope(target_root, "independent-feature")
        binding_path = target_root / "independent-feature/10-workload-binding/workload-binding.yml"
        binding = index(binding_path)
        identities = {item["id"]: "feature-" + item["id"] for item in binding["workloads"]}
        for item in binding["workloads"]:
            item["id"] = identities[item["id"]]
        for item in binding["runtime_requirements"]:
            item["workload"] = identities[item["workload"]]
        write(binding_path, binding)
        contract_path = target_root / "independent-feature/00-declaration/declaration-contract.yml"
        contract = index(contract_path)
        for item in contract["health_recovery"]["workloads"]:
            item["binding"] = identities[item["binding"]]
        write(contract_path, contract)
        index_path = target_root / "scope-index.yml"
        independent = index(index_path)
        entry = scope_entry("independent-feature", "candidate")
        entry["workload_ownership"] = list(identities.values())
        independent["scopes"].append(entry)
        write(index_path, independent)
        expect_success(target_root)
        initial_bytes = index_path.read_bytes()

        linked = copy.deepcopy(independent)
        linked["scopes"][-1]["successor"] = "core-server-persistence"
        write(index_path, linked)
        expect_failure(target_root, "scope-lifecycle-transition-invalid")

        collided = copy.deepcopy(independent)
        collided["scopes"][-1]["workload_ownership"] = ["core-server-service", "private-release-verifier-task"]
        original_binding = copy.deepcopy(binding)
        for item in binding["workloads"]:
            item["id"] = item["id"].removeprefix("feature-")
        for item in binding["runtime_requirements"]:
            item["workload"] = item["workload"].removeprefix("feature-")
        collided_contract = copy.deepcopy(contract)
        for item in collided_contract["health_recovery"]["workloads"]:
            item["binding"] = item["binding"].removeprefix("feature-")
        write(contract_path, collided_contract)
        write(binding_path, binding)
        write(index_path, collided)
        expect_failure(target_root, "scope-lifecycle-candidate-predecessor-invalid")

        write(binding_path, original_binding)
        write(index_path, independent)
        assert index_path.read_bytes() == initial_bytes
        contract["configuration"].pop("secret_dependencies")
        write(contract_path, contract)
        expect_failure(target_root, "scope-lifecycle-secret-dependency-invalid")

if __name__ == "__main__":
    raise SystemExit(main())

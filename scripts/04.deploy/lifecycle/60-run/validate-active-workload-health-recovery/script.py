#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-active-workload-health-recovery.implementation
#   version: 2
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Enforce health/recovery validation for every active indexed scope and reject unowned legacy exceptions.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.validate-active-workload-health-recovery
#     path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py"
SCOPE_ID = re.compile(r"^[a-z][a-z0-9-]*$")


def load(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def canonical_scope_paths(target_root: Path, scope_id: str) -> tuple[Path, Path]:
    scope_root = target_root / scope_id
    return (
        scope_root / "00-declaration" / "declaration-contract.yml",
        scope_root / "10-workload-binding" / "workload-binding.yml",
    )


def discovered_scope_ids(target_root: Path) -> set[str]:
    if not target_root.is_dir():
        return set()
    return {
        directory.name
        for directory in target_root.iterdir()
        if directory.is_dir()
        and (
            (directory / "00-declaration").exists()
            or (directory / "10-workload-binding").exists()
        )
    }


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    codes: list[str] = []
    index = load(args.target_root / "scope-index.yml") if not unknown else None
    if not isinstance(index, dict) or index.get("schema") != "deploy/scope-health-inventory/v1":
        codes.append("scope-health-inventory-invalid")
    else:
        target = index.get("target")
        active = index.get("active_scopes")
        active_ids: list[str] = []
        if not text(target):
            codes.append("scope-health-inventory-target-invalid")
        if not isinstance(active, list) or not active:
            codes.append("active-scope-inventory-missing")
        else:
            for item in active:
                if not isinstance(item, dict) or not all(text(item.get(key)) for key in ("id", "declaration", "workload_binding")):
                    codes.append("active-scope-entry-invalid")
                    continue
                scope_id = item["id"]
                if SCOPE_ID.fullmatch(scope_id) is None:
                    codes.append("active-scope-entry-invalid")
                    continue
                active_ids.append(scope_id)
                expected_contract, expected_binding = canonical_scope_paths(args.target_root, scope_id)
                if item["declaration"] != expected_contract.relative_to(args.target_root).as_posix() or item["workload_binding"] != expected_binding.relative_to(args.target_root).as_posix():
                    codes.append("active-scope-path-noncanonical")
                    continue
                contract, binding = expected_contract, expected_binding
                if not contract.is_file():
                    codes.append("active-scope-declaration-missing")
                    continue
                if not binding.is_file():
                    codes.append("active-scope-binding-missing")
                    continue
                contract_document = load(contract)
                binding_document = load(binding)
                if contract_document is None or binding_document is None:
                    codes.append("active-scope-document-unreadable")
                    continue
                if contract_document.get("target") != target or binding_document.get("target") != target:
                    codes.append("active-scope-target-mismatch")
                if contract_document.get("scope") != scope_id or binding_document.get("scope") != scope_id:
                    codes.append("active-scope-identity-mismatch")
                result = subprocess.run(
                    [sys.executable, str(VALIDATOR), "--scope-contract", str(contract), "--workload-binding", str(binding), "--json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode:
                    codes.append("active-scope-health-recovery-invalid")
            if len(active_ids) != len(set(active_ids)):
                codes.append("active-scope-entry-invalid")
            discovered = discovered_scope_ids(args.target_root)
            if discovered != set(active_ids):
                codes.append("active-scope-inventory-incomplete")

        exceptions = index.get("legacy_exceptions", [])
        if not isinstance(exceptions, list):
            codes.append("legacy-exceptions-invalid")
        for item in exceptions if isinstance(exceptions, list) else []:
            required = ("legacy_workload", "reason", "owner", "replacement_path", "review_condition", "retirement_condition")
            if not isinstance(item, dict) or item.get("status") != "retiring-reference-only" or any(not text(item.get(key)) for key in required):
                codes.append("legacy-exception-invalid")
            elif "20-scopes" in item["legacy_workload"] or item["legacy_workload"] in active_ids:
                codes.append("legacy-exception-cannot-cover-active-scope")

    report = {
        "schema": "deploy/active-workload-health-recovery-report/v1",
        "target": index.get("target") if isinstance(index, dict) else None,
        "verdict": "passed" if not codes else "failed",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    raise SystemExit(main())

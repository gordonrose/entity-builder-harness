#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-active-workload-health-recovery.implementation
#   version: 5
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Enforce lifecycle-aware health/recovery validation, exclusive active workload ownership, and explicit legacy exceptions.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.validate-active-workload-health-recovery
#     path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh
from __future__ import annotations

import argparse
import importlib.util
import tempfile
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py"
SECRET_VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh"
PERSISTENCE_DIAGNOSTIC_VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh"
SCOPE_ID = re.compile(r"^[a-z][a-z0-9-]*$")
LIFECYCLE_STATES = frozenset({"active", "candidate", "accepted-historical"})


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


def text_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value or not all(text(item) for item in value):
        return None
    values = [item for item in value if isinstance(item, str)]
    return values if len(values) == len(set(values)) else None


def binding_workload_ids(binding: dict[str, Any]) -> list[str] | None:
    workloads = binding.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        return None
    ids: list[str] = []
    for workload in workloads:
        if not isinstance(workload, dict) or not text(workload.get("id")):
            return None
        ids.append(workload["id"])
    return ids if len(ids) == len(set(ids)) else None


def acceptance_codes(contract: dict, contract_path: Path, rehearsal_root: Path | None = None) -> list[str]:
    """Existing health-only contracts remain supported; advertised acceptance is mandatory."""
    if 'acceptance' not in contract: return []
    root = Path(__file__).resolve().parents[5]
    path = root / 'scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py'
    try:
        if not path.is_file(): return ['scope-lifecycle-acceptance-route-helper-unavailable']
        spec = importlib.util.spec_from_file_location('lifecycle_acceptance_route', path)
        if spec is None or spec.loader is None: return ['scope-lifecycle-acceptance-route-helper-unavailable']
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        route, _ = module.load_route(contract_path, rehearsal_root or root)
    except (OSError, ImportError, SyntaxError, AttributeError, TypeError, ValueError):
        return ['scope-lifecycle-acceptance-route-helper-unavailable']
    if not isinstance(route, dict) or route.get('target') != contract.get('target') or route.get('scope') != contract.get('scope'): return ['scope-lifecycle-acceptance-route-invalid']
    record = route.get('accepted_record')
    commands = route.get('commands')
    if not isinstance(record, dict) or not isinstance(commands, dict) or not isinstance(record.get('validator'), str): return ['scope-lifecycle-acceptance-route-invalid']
    command = commands.get(record['validator'])
    if not isinstance(command, dict): return ['scope-lifecycle-acceptance-route-invalid']
    record_path = module.reference(contract_path.parent.parent, record.get('path'))
    if record_path is None: return ['scope-lifecycle-accepted-release-invalid']
    accepted = module.document(record_path)
    if any(accepted.get(key) != value for key, value in [('target', contract.get('target')), ('scope', contract.get('scope')), ('schema', record.get('schema'))]): return ['scope-lifecycle-accepted-release-identity-invalid']
    argv = module.resolve(command.get('argv'), {'accepted_record': str(record_path), 'scope_contract': str(contract_path)})
    if argv is None or argv[0] != 'bash': return ['scope-lifecycle-acceptance-validator-invalid']
    script = module.reference(root, argv[1])
    metadata = module.command_metadata(script) if script else {}
    if metadata.get('id') != command.get('owner') or metadata.get('effects') != ['read-only'] or command.get('effects') != ['read-only']: return ['scope-lifecycle-acceptance-validator-invalid']
    # Relative retained receipt references resolve in the owning repository. For
    # copied target fixtures the scope-local accepted record remains the input.
    args = ['bash', str(script), *argv[2:]]
    if rehearsal_root is not None: args += ['--rehearsal-root', str(rehearsal_root)]
    elif contract_path.is_relative_to(root): args += ['--root', str(root)]
    try:
        checked = subprocess.run(args, capture_output=True, text=True, check=False, timeout=30)
        report = json.loads(checked.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError): return ['scope-lifecycle-accepted-release-invalid']
    return [] if checked.returncode == 0 and isinstance(report, dict) and report.get('verdict') == 'validated' else ['scope-lifecycle-accepted-release-invalid']


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target-root", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--rehearsal-root", type=Path)
    parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    if not unknown and args.target_root is not None and args.validate_arguments: print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[]})); return 0
    if args.target_root is None:
        print(json.dumps({"schema":"deploy/scope-lifecycle-inventory-report/v1","verdict":"failed","findings":[{"code":"scope-lifecycle-arguments-invalid"}]})); return 1
    report = inspect(args.target_root, args.rehearsal_root, {} if unknown else None)
    print(json.dumps(report, sort_keys=True))
    return int(report["verdict"] != "passed")


def inspect(target_root: Path, rehearsal_root: Path | None = None, index_override: dict | None = None) -> dict:
    codes: list[str] = []
    if rehearsal_root is not None and (not rehearsal_root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or not target_root.resolve().is_relative_to(rehearsal_root.resolve())):
        return {"schema":"deploy/scope-lifecycle-inventory-report/v1","verdict":"failed","findings":[{"code":"scope-lifecycle-simulation-root-invalid"}]}
    index = index_override if index_override is not None else load(target_root / "scope-index.yml")
    if not isinstance(index, dict) or index.get("schema") != "deploy/scope-lifecycle-inventory/v1":
        codes.append("scope-lifecycle-inventory-invalid")
    else:
        target = index.get("target")
        scopes = index.get("scopes")
        indexed: dict[str, dict[str, Any]] = {}
        ownership: dict[str, list[str]] = {}
        if not text(target):
            codes.append("scope-lifecycle-inventory-target-invalid")
        if not isinstance(scopes, list) or not scopes:
            codes.append("scope-lifecycle-inventory-missing")
        else:
            for item in scopes:
                if not isinstance(item, dict) or not all(text(item.get(key)) for key in ("id", "lifecycle", "declaration", "workload_binding")):
                    codes.append("scope-lifecycle-entry-invalid")
                    continue
                scope_id = item["id"]
                lifecycle = item["lifecycle"]
                if SCOPE_ID.fullmatch(scope_id) is None or lifecycle not in LIFECYCLE_STATES or scope_id in indexed:
                    codes.append("scope-lifecycle-entry-invalid")
                    continue
                indexed[scope_id] = item
                expected_contract, expected_binding = canonical_scope_paths(target_root, scope_id)
                if item["declaration"] != expected_contract.relative_to(target_root).as_posix() or item["workload_binding"] != expected_binding.relative_to(target_root).as_posix():
                    codes.append("scope-lifecycle-path-noncanonical")
                    continue
                contract, binding = expected_contract, expected_binding
                if not contract.is_file():
                    codes.append("scope-lifecycle-declaration-missing")
                    continue
                if not binding.is_file():
                    codes.append("scope-lifecycle-binding-missing")
                    continue
                contract_document = load(contract)
                binding_document = load(binding)
                if contract_document is None or binding_document is None:
                    codes.append("scope-lifecycle-document-unreadable")
                    continue
                if contract_document.get("target") != target or binding_document.get("target") != target:
                    codes.append("scope-lifecycle-target-mismatch")
                if contract_document.get("scope") != scope_id or binding_document.get("scope") != scope_id:
                    codes.append("scope-lifecycle-identity-mismatch")
                if lifecycle in {"active", "accepted-historical"}:
                    codes.extend(acceptance_codes(contract_document, contract, rehearsal_root))
                declared_ownership = text_list(item.get("workload_ownership"))
                bound_workloads = binding_workload_ids(binding_document)
                if declared_ownership is None or bound_workloads is None or set(declared_ownership) != set(bound_workloads):
                    codes.append("scope-lifecycle-workload-ownership-mismatch")
                else:
                    ownership[scope_id] = declared_ownership
                result = subprocess.run(
                    [sys.executable, str(VALIDATOR), "--scope-contract", str(contract), "--workload-binding", str(binding), "--json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode:
                    codes.append("active-scope-health-recovery-invalid")
                secret_result = subprocess.run(
                    [str(SECRET_VALIDATOR), "--scope-contract", str(contract), "--json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if secret_result.returncode:
                    codes.append("scope-lifecycle-secret-dependency-invalid")
                diagnostic_result = subprocess.run(
                    [str(PERSISTENCE_DIAGNOSTIC_VALIDATOR), "--scope-contract", str(contract), "--workload-binding", str(binding), "--json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if diagnostic_result.returncode:
                    codes.append("scope-lifecycle-persistence-diagnostics-invalid")

            active_owners: dict[str, str] = {}
            for scope_id, item in indexed.items():
                lifecycle = item.get("lifecycle")
                predecessor = item.get("predecessor")
                successor = item.get("successor")
                if lifecycle == "candidate":
                    if not text(predecessor) or predecessor not in indexed or indexed[predecessor].get("lifecycle") != "active":
                        codes.append("scope-lifecycle-candidate-predecessor-invalid")
                    elif not set(ownership.get(scope_id, [])).intersection(ownership.get(predecessor, [])):
                        codes.append("scope-lifecycle-candidate-ownership-invalid")
                    if successor is not None:
                        codes.append("scope-lifecycle-transition-invalid")
                elif lifecycle == "accepted-historical":
                    if not text(successor) or successor not in indexed or indexed[successor].get("lifecycle") != "active":
                        codes.append("scope-lifecycle-historical-successor-invalid")
                    elif indexed[successor].get("predecessor") != scope_id:
                        codes.append("scope-lifecycle-transition-invalid")
                    elif not set(ownership.get(scope_id, [])).intersection(ownership.get(successor, [])):
                        codes.append("scope-lifecycle-historical-ownership-invalid")
                    if predecessor is not None:
                        codes.append("scope-lifecycle-transition-invalid")
                elif lifecycle == "active":
                    if predecessor is not None:
                        if not text(predecessor) or predecessor not in indexed or indexed[predecessor].get("lifecycle") != "accepted-historical" or indexed[predecessor].get("successor") != scope_id:
                            codes.append("scope-lifecycle-active-predecessor-invalid")
                    if successor is not None:
                        codes.append("scope-lifecycle-transition-invalid")
                    for workload_id in ownership.get(scope_id, []):
                        prior_owner = active_owners.get(workload_id)
                        if prior_owner is not None and prior_owner != scope_id:
                            codes.append("active-workload-ownership-duplicate")
                        else:
                            active_owners[workload_id] = scope_id

            discovered = discovered_scope_ids(target_root)
            if discovered != set(indexed):
                codes.append("scope-lifecycle-inventory-incomplete")

        exceptions = index.get("legacy_exceptions", [])
        if not isinstance(exceptions, list):
            codes.append("legacy-exceptions-invalid")
        for item in exceptions if isinstance(exceptions, list) else []:
            required = ("legacy_workload", "reason", "owner", "replacement_path", "review_condition", "retirement_condition")
            if not isinstance(item, dict) or item.get("status") != "retiring-reference-only" or any(not text(item.get(key)) for key in required):
                codes.append("legacy-exception-invalid")
            elif "20-scopes" in item["legacy_workload"] or item["legacy_workload"] in indexed:
                codes.append("legacy-exception-cannot-cover-new-framework-scope")

    report = {
        "schema": "deploy/scope-lifecycle-inventory-report/v1",
        "target": index.get("target") if isinstance(index, dict) else None,
        "verdict": "passed" if not codes else "failed",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    return report


if __name__ == "__main__":
    raise SystemExit(main())

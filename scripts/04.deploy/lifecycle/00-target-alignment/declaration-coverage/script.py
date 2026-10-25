#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.declaration-coverage
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.declaration-coverage
#   disciplines: [agentic, architecture, sre]
#   kind: script
#   purpose: Validate existing target scope requirement chains and referenced implementation and proof paths offline.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.declaration-coverage
#     path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[5]
MANDATORY_LOCAL_PROOFS = frozenset({"scope-inventory", "runnable-program"})
PROOF_STAGES = {"local_proofs": "local", "package_proofs": "package", "target_proofs": "deploy", "run_proofs": "acceptance"}


def document(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return value if isinstance(value, dict) else {}


def safe_path(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9._/-]+", value)) and not value.startswith(("/", "-")) and all(part not in {"..", "."} for part in PurePosixPath(value).parts) and "\\" not in value and not any(c in value for c in "\n\r\0*?[]")


def within(root: Path, value: str) -> Path | None:
    if not safe_path(value):
        return None
    path = root / value
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        return None
    return path


def strings(value: Any, *, empty: bool = False) -> bool:
    return isinstance(value, list) and (empty or bool(value)) and all(isinstance(item, str) and bool(item.strip()) for item in value) and len(value) == len(set(value))


def inspect(contract_path: Path, root: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    contract = document(contract_path)
    findings: list[dict[str, str]] = []
    references: set[str] = set()
    checks: set[str] = set()
    consumers: set[str] = set()
    def gap(code: str, reference: str = "") -> None:
        item = {"code": code}
        if reference: item["reference"] = reference
        if item not in findings: findings.append(item)
    def reference(value: Any, code: str) -> None:
        path = within(root, value) if isinstance(value, str) else None
        if path is None: gap(code)
        elif not path.exists(): gap(code, value)
        elif isinstance(value, str): references.add(value.rstrip("/"))
    if contract.get("schema") != "deploy/target-scope-contract/v1": gap("scope-contract-unsupported")
    impact = contract.get("change_impact")
    if not isinstance(impact, dict) or impact.get("schema") != "deploy/change-impact/v1":
        gap("change-impact-declaration-missing")
        impact = {}
    inputs = impact.get("inputs")
    if not strings(inputs): gap("change-impact-inputs-invalid"); inputs = []
    for value in inputs: reference(value, "change-impact-input-missing")
    requirements = impact.get("requirements")
    if not isinstance(requirements, list) or not requirements: gap("requirement-chain-missing"); requirements = []
    if catalog.get("schema") != "repo/check-catalog/v1": gap("check-catalog-schema-unsupported")
    known = catalog.get("checks", {})
    if not isinstance(known, dict): known = {}; gap("check-catalog-invalid")
    ids: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict): gap("requirement-chain-invalid"); continue
        identity = requirement.get("id")
        if not isinstance(identity, str) or not identity or identity in ids: gap("requirement-identity-invalid"); continue
        ids.add(identity)
        for field in ("purpose", "owner", "expectation"):
            if not isinstance(requirement.get(field), str) or not requirement[field].strip(): gap("requirement-chain-incomplete", identity + ":" + field)
        for field in ("required_by", "declarations"):
            values = requirement.get(field)
            if not strings(values): gap("requirement-chain-incomplete", identity + ":" + field); continue
            for value in values:
                reference(value, "requirement-implementation-missing")
                if field == "required_by": consumers.add(value)
        non_applicable = requirement.get("not_applicable", {})
        if not isinstance(non_applicable, dict): gap("requirement-applicability-invalid", identity); non_applicable = {}
        if set(non_applicable) - set(PROOF_STAGES): gap("requirement-applicability-unsupported", identity)
        for field, stage in PROOF_STAGES.items():
            proofs = requirement.get(field)
            reason = non_applicable.get(field)
            if not strings(proofs, empty=True): gap("requirement-proof-list-invalid", identity + ":" + field); continue
            if not proofs:
                if field == "local_proofs" or not isinstance(reason, str) or not reason.strip(): gap("requirement-proof-missing", identity + ":" + field)
            elif reason is not None: gap("requirement-applicability-conflict", identity + ":" + field)
            for check_id in proofs:
                check = known.get(check_id)
                if not isinstance(check, dict): gap("requirement-check-unsupported", check_id); continue
                checks.add(check_id)
                if check.get("stage") != stage: gap("requirement-proof-stage-invalid", check_id)
                argv = check.get("argv")
                if not isinstance(argv, list) or len(argv) < 2: gap("requirement-check-invalid", check_id); continue
                reference(argv[1], "requirement-proof-command-missing")
    declared_local = {identity for requirement in requirements if isinstance(requirement, dict) for identity in (requirement.get("local_proofs") if isinstance(requirement.get("local_proofs"), list) else []) if isinstance(identity, str)}
    for identity in sorted(MANDATORY_LOCAL_PROOFS - declared_local):
        gap("mandatory-scope-check-missing", identity)
    for field in ("package_proofs", "target_proofs", "run_proofs"):
        if not any(isinstance(requirement, dict) and requirement.get(field) for requirement in requirements):
            gap("scope-stage-proof-missing", field)
    # These established references remain compulsory; a new impact block cannot
    # erase a missing implementation already named by the actual scope contract.
    program = contract.get("program", {})
    if isinstance(program, dict):
        for field in ("contract", "image_contract", "local_proof"):
            reference(program.get(field), "scope-program-reference-missing")
    else: gap("scope-program-reference-missing"); program = {}
    def referenced_document(value: Any) -> dict[str, Any]:
        path = within(root, value) if isinstance(value, str) else None
        return document(path) if path is not None else {}
    program_index = referenced_document(program.get("contract"))
    image = referenced_document(program.get("image_contract"))
    if program_index.get("schema") != "deploy/runnable-program-contract/v1": gap("scope-program-schema-unsupported")
    if image.get("schema") != "deploy/core-server-image-contract/v1": gap("scope-image-schema-unsupported")
    program_id = program.get("id")
    declared_programs = program_index.get("runnable_programs", [])
    matches = [item for item in declared_programs if isinstance(item, dict) and item.get("id") == program_id] if isinstance(declared_programs, list) else []
    selected_program = matches[0] if len(matches) == 1 and isinstance(program_id, str) and program_id else {}
    if not selected_program: gap("scope-runnable-program-identity-mismatch")
    for field in ("source_entrypoint", "configuration_boundary", "dependency_failure_boundary", "local_proof"):
        reference(selected_program.get(field), "scope-program-implementation-missing")
    if image.get("program_id") != program_id or image.get("runnable_program_contract") != program.get("contract") or not isinstance(image.get("id"), str):
        gap("scope-image-program-identity-mismatch")
    entrypoint = selected_program.get("entrypoint")
    if not isinstance(entrypoint, str) or image.get("compiled_entrypoint") != entrypoint:
        gap("scope-image-entrypoint-mismatch")
    declared_images = program_index.get("image_contracts", [])
    matched_images = [item for item in declared_images if isinstance(item, dict) and item.get("id") == image.get("id")] if isinstance(declared_images, list) else []
    selected_image = matched_images[0] if len(matched_images) == 1 else {}
    if selected_image.get("program") != program_id or selected_image.get("command_mode") != "exec":
        gap("scope-image-contract-identity-mismatch")
    declared_command, packaged_command = selected_image.get("command"), image.get("command")
    if not strings(declared_command) or not strings(packaged_command) or entrypoint not in packaged_command or len(packaged_command) > len(declared_command) or declared_command[-len(packaged_command):] != packaged_command:
        gap("scope-image-command-mismatch")
    payload = image.get("payload")
    if not isinstance(payload, dict) or payload.get("allowed_program") != program_id:
        gap("scope-image-payload-program-mismatch")
    binding_path = contract_path.parent.parent / "10-workload-binding/workload-binding.yml"
    binding = document(binding_path)
    if not binding: gap("scope-workload-binding-missing")
    if binding.get("program_id") != program_id or binding.get("program_contract") != program.get("contract") or binding.get("image_contract") != program.get("image_contract"):
        gap("scope-workload-program-binding-mismatch")
    for workload in binding.get("workloads", []) if isinstance(binding.get("workloads"), list) else []:
        execution = workload.get("execution", {}) if isinstance(workload, dict) else {}
        value = execution.get("source_reference") if isinstance(execution, dict) else None
        reference(value.split("#", 1)[0] if isinstance(value, str) else value, "scope-execution-source-missing")
    try:
        scope_ref = contract_path.resolve().relative_to(root.resolve()).as_posix()
        references.add(scope_ref)
        references.add(binding_path.resolve().relative_to(root.resolve()).as_posix())
    except ValueError: gap("scope-path-outside-repository")
    workload = contract.get("workload", {})
    template = workload.get("runtime_template") if isinstance(workload, dict) else None
    provider_binding = binding.get("proposed_provider_binding")
    if not isinstance(provider_binding, dict) or provider_binding.get("template") != template:
        gap("scope-provider-template-binding-mismatch")
    if isinstance(template, str) and safe_path(template):
        try:
            ref = (contract_path.parents[3] / template).resolve().relative_to(root.resolve()).as_posix()
            reference(ref, "scope-provider-declaration-missing")
        except ValueError: gap("scope-provider-declaration-missing")
    else: gap("scope-provider-declaration-missing")
    return {"schema": "deploy/declaration-coverage-report/v1", "scope": contract.get("scope"), "target": contract.get("target"), "verdict": "gap" if findings else "covered", "findings": findings, "inputs": inputs, "references": sorted(references), "consumers": sorted(consumers), "required_checks": sorted(checks)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope-contract", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    catalog = document(args.catalog or args.root / "scripts/repo/check-selection/checks.yml")
    report = inspect(args.scope_contract, args.root, catalog)
    print(json.dumps(report, sort_keys=True))
    return 1 if report["findings"] else 0

if __name__ == "__main__":
    raise SystemExit(main())

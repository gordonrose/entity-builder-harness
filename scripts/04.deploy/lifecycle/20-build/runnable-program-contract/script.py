#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.runnable-program-contract
#   version: 3
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - agentic
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Validate runnable contracts and declared workspace build inputs using a bounded local reader without compilation or provider access.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.runnable-program-contract
#     path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


CONTRACT_SCHEMA = "deploy/runnable-program-contract/v1"
REPORT_SCHEMA = "deploy/runnable-program-report/v1"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ENTRYPOINT_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
FORBIDDEN_COMMAND_CHARACTERS = set("$;&|`\n\r")
SAFE_EVIDENCE_FIELDS = {
    "candidate_id",
    "checked_at",
    "health_verdict",
    "image_digest",
    "package_contract_id",
    "program_id",
    "receipt_reference",
    "release_identity",
    "source_revision",
    "verification_verdict",
}


class ContractFailure(Exception):
    def __init__(self, *codes: str) -> None:
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__(", ".join(self.codes))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "DIAGNOSTIC_CODE=RUNNABLE_PROGRAM_ARGUMENTS_INVALID\n")
    parser.add_argument("--contract")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py --contract <path> [--json]")
        raise SystemExit(0)
    if unknown or not args.contract:
        raise ContractFailure("arguments-invalid")
    return args


def is_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def is_entrypoint(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value
        and not value.startswith(("/", "../"))
        and "//" not in value
        and bool(ENTRYPOINT_RE.fullmatch(value))
    )


def report(contract_id: str | None, verdict: str, codes: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "scope": "contract",
        "verdict": verdict,
        "findings": [{"code": code} for code in codes],
    }
    if contract_id is not None:
        result["contract_id"] = contract_id
    return result


def load_contract(path: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        raise ContractFailure("contract-unreadable") from None
    if not isinstance(value, dict):
        raise ContractFailure("contract-shape-invalid")
    return value


def require_list(value: Any, code: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ContractFailure(code)
    return value


def validate_programs(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    programs: dict[str, dict[str, Any]] = {}
    for item in require_list(document.get("runnable_programs"), "program-record-missing"):
        if not isinstance(item, dict) or not is_id(item.get("id")) or not is_entrypoint(item.get("entrypoint")):
            raise ContractFailure("program-record-invalid")
        program_id = item["id"]
        if program_id in programs:
            raise ContractFailure("program-record-duplicate")
        if not isinstance(item.get("runtime_executable"), str) or item.get("runtime_executable") not in {"node", "python3", "ruby", "java"}:
            raise ContractFailure("program-runtime-unsupported")
        execution = item.get("execution_kind", "process")
        if execution not in ("process", "managed-handler"):
            raise ContractFailure("program-execution-kind-invalid")
        if execution == "managed-handler":
            if (item["runtime_executable"] != "node"
                    or not item["entrypoint"].endswith((".js", ".cjs", ".mjs"))
                    or any(part in (".", "..") for part in item["entrypoint"].split("/"))
                    or not isinstance(item.get("handler_export"), str)
                    or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item["handler_export"])):
                raise ContractFailure("program-handler-invalid")
        elif "handler_export" in item:
            raise ContractFailure("program-handler-invalid")
        approved = item.get("approved_dependencies")
        observed = item.get("observed_dependencies")
        if not isinstance(approved, list) or not isinstance(observed, list):
            raise ContractFailure("dependency-boundary-invalid")
        if not all(is_id(value) for value in approved + observed):
            raise ContractFailure("dependency-boundary-invalid")
        if not set(observed).issubset(set(approved)):
            raise ContractFailure("dependency-unapproved")
        programs[program_id] = item
    return programs


def is_safe_command(command: Any, entrypoint: str, runtime: str) -> bool:
    if not isinstance(command, list) or len(command) < 2 or not all(isinstance(token, str) and token for token in command):
        return False
    if command[0] != runtime or command[1] != entrypoint:
        return False
    return all(
        not any(character in token for character in FORBIDDEN_COMMAND_CHARACTERS)
        and not any(character.isspace() for character in token)
        for token in command
    )


def validate_images(document: dict[str, Any], programs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    images: dict[str, dict[str, Any]] = {}
    for item in require_list(document.get("image_contracts"), "image-contract-missing"):
        if not isinstance(item, dict) or not is_id(item.get("id")):
            raise ContractFailure("image-contract-invalid")
        image_id = item["id"]
        if image_id in images:
            raise ContractFailure("image-contract-duplicate")
        program_id = item.get("program")
        if not is_id(program_id) or program_id not in programs:
            raise ContractFailure("program-record-missing")
        program = programs[program_id]
        if program.get("execution_kind", "process") == "managed-handler":
            # A managed runtime selects exactly one exported function; it does
            # not execute an arbitrary shell command or silently change a process.
            handler = program["entrypoint"].rsplit(".", 1)[0] + "." + program["handler_export"]
            valid_command = item.get("command_mode") == "handler" and item.get("command") == [handler]
        else:
            valid_command = item.get("command_mode") == "exec" and is_safe_command(item.get("command"), program["entrypoint"], program["runtime_executable"])
        if not valid_command:
            raise ContractFailure("image-command-invalid")
        images[image_id] = item
    return images


def validate_candidates(document: dict[str, Any], images: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for item in require_list(document.get("package_candidates"), "package-candidate-missing"):
        if not isinstance(item, dict) or not is_id(item.get("id")):
            raise ContractFailure("package-candidate-invalid")
        candidate_id = item["id"]
        if candidate_id in candidates:
            raise ContractFailure("package-candidate-duplicate")
        if not isinstance(item.get("image_contract"), str) or item.get("image_contract") not in images:
            raise ContractFailure("image-contract-missing")
        if item.get("immutable_identity_rule") != "runtime-bound-sha256":
            raise ContractFailure("candidate-identity-rule-invalid")
        candidates[candidate_id] = item
    return candidates


def validate_evidence(document: dict[str, Any], candidates: dict[str, dict[str, Any]]) -> None:
    declared = document.get("candidate_verifications")
    verifications = declared if isinstance(declared, list) else [document.get("candidate_verification")]
    if not verifications or not all(isinstance(item, dict) for item in verifications):
        raise ContractFailure("candidate-verification-invalid")
    verified: set[str] = set()
    for verification in verifications:
        candidate = verification.get("candidate")
        if not isinstance(candidate, str) or candidate not in candidates or candidate in verified:
            raise ContractFailure("candidate-verification-invalid")
        verified.add(candidate)
        fields = verification.get("required_evidence_fields")
        if not isinstance(fields, list) or not fields or not all(isinstance(field, str) for field in fields):
            raise ContractFailure("evidence-fields-invalid")
        if len(fields) != len(set(fields)) or not set(fields).issubset(SAFE_EVIDENCE_FIELDS):
            raise ContractFailure("evidence-field-unsafe")
    if verified != set(candidates):
        raise ContractFailure("candidate-verification-invalid")


def validate(document: dict[str, Any]) -> str:
    if document.get("schema") != CONTRACT_SCHEMA or document.get("version") != 1:
        raise ContractFailure("contract-schema-invalid")
    contract_id = document.get("id")
    if not is_id(contract_id):
        raise ContractFailure("contract-id-invalid")
    programs = validate_programs(document)
    images = validate_images(document, programs)
    candidates = validate_candidates(document, images)
    validate_evidence(document, candidates)
    return contract_id


def validate_declared_builds(document: dict[str, Any], contract: str, *, root: Path | None = None, run=None) -> None:
    """Legacy records stay structural; declared builds use the canonical reader."""
    programs = document.get('runnable_programs', [])
    selected = [program for program in programs if isinstance(program, dict) and 'build' in program]
    if not selected and 'dependency_bindings' not in document:
        return
    if not selected or not isinstance(document.get('dependency_bindings'), dict):
        raise ContractFailure('program-build-declaration-invalid')
    repository = (root or Path.cwd()).resolve()
    try:
        relative = Path(contract).resolve().relative_to(repository).as_posix()
    except (OSError, ValueError):
        raise ContractFailure('program-build-contract-outside-repository') from None
    reader = Path(__file__).with_name('build-inputs.mjs')
    execute = run or subprocess.run
    for program in selected:
        try:
            result = execute(['node', str(reader), '--program', program['id'], '--contract', relative],
                             cwd=repository, capture_output=True, text=True, timeout=30, check=False)
            if len(result.stdout) > 2 * 1024 * 1024:
                raise ContractFailure('program-build-response-invalid')
            value = json.loads(result.stdout)
        except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
            raise ContractFailure('program-build-observation-unavailable') from None
        if result.returncode != 0:
            supported = {'program-build-binding-invalid', 'program-build-project-invalid',
                         'program-build-entrypoint-invalid', 'program-build-execution-invalid', 'program-build-handler-invalid',
                         'program-build-dependency-not-approved', 'program-build-external-dependency-not-approved',
                         'workspace-dependency-not-approved', 'workspace-dependency-unresolved',
                         'workspace-export-source-missing', 'workspace-export-target-unsupported',
                         'workspace-source-symlink'}
            code = value.get('error') if isinstance(value, dict) else None
            raise ContractFailure(code if code in supported else 'program-build-declaration-invalid')
        if not isinstance(value, dict) or value.get('programId') != program['id'] or not isinstance(value.get('inputs'), dict):
            raise ContractFailure('program-build-response-invalid')


def main() -> int:
    contract_id: str | None = None
    try:
        args = parse_args()
        document = load_contract(args.contract)
        candidate_id = document.get("id")
        if is_id(candidate_id):
            contract_id = candidate_id
        contract_id = validate(document)
        validate_declared_builds(document, args.contract)
        print(json.dumps(report(contract_id, "passed", ()), sort_keys=True))
        return 0
    except ContractFailure as failure:
        print(json.dumps(report(contract_id, "failed", failure.codes), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

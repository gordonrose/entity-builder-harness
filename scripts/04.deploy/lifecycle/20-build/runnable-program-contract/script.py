#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.runnable-program-contract
#   version: 1
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - agentic
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Compile a safe report from a runnable-program contract without reading source code or external state.
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
    except (OSError, yaml.YAMLError):
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


def is_safe_command(command: Any, entrypoint: str) -> bool:
    if not isinstance(command, list) or len(command) < 2 or not all(isinstance(token, str) and token for token in command):
        return False
    if command[0].startswith("-") or entrypoint not in command:
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
        if item.get("command_mode") != "exec" or not is_safe_command(item.get("command"), programs[program_id]["entrypoint"]):
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
        if item.get("image_contract") not in images:
            raise ContractFailure("image-contract-missing")
        if item.get("immutable_identity_rule") != "runtime-bound-sha256":
            raise ContractFailure("candidate-identity-rule-invalid")
        candidates[candidate_id] = item
    return candidates


def validate_evidence(document: dict[str, Any], candidates: dict[str, dict[str, Any]]) -> None:
    verification = document.get("candidate_verification")
    if not isinstance(verification, dict) or verification.get("candidate") not in candidates:
        raise ContractFailure("candidate-verification-invalid")
    fields = verification.get("required_evidence_fields")
    if not isinstance(fields, list) or not fields or not all(isinstance(field, str) for field in fields):
        raise ContractFailure("evidence-fields-invalid")
    if len(fields) != len(set(fields)) or not set(fields).issubset(SAFE_EVIDENCE_FIELDS):
        raise ContractFailure("evidence-field-unsafe")


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


def main() -> int:
    contract_id: str | None = None
    try:
        args = parse_args()
        document = load_contract(args.contract)
        candidate_id = document.get("id")
        if is_id(candidate_id):
            contract_id = candidate_id
        contract_id = validate(document)
        print(json.dumps(report(contract_id, "passed", ()), sort_keys=True))
        return 0
    except ContractFailure as failure:
        print(json.dumps(report(contract_id, "failed", failure.codes), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

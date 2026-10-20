#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.control.kanbien-core-platform.bootstrap-runtime
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Safely report the fixed core-platform target control state without contacting a provider.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only

"""Shared, local-only implementation for fixed core-platform control commands."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


TARGET = "kanbien-core-platform"
SCOPE = "bootstrap-runtime"
ROOT = Path(__file__).resolve().parents[7]
TARGET_ROOT = ROOT / "infra/04.deploy/03.product/targets" / TARGET
PROGRAM_CONTRACT = ROOT / "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"
IMAGE_CONTRACT = ROOT / "infra/04.deploy/03.product/image/core-server/image-contract.yml"
KNOWN_E0_FACTS = {
    "provider-account-profile",
    "provider-region",
    "runtime-family",
    "private-network-placement",
    "image-custody-destination",
    "private-verifier-placement",
    "logging-destination",
    "cost-guard",
    "delivery-identity",
    "workload-startup-identity",
    "rollback-custody",
}
CANDIDATE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


class ControlFailure(Exception):
    def __init__(self, *codes: str) -> None:
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__(", ".join(self.codes))


def load_mapping(path: Path, code: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raise ControlFailure(code) from None
    if not isinstance(value, dict):
        raise ControlFailure(code)
    return value


def static_assertions() -> tuple[str, ...]:
    codes: list[str] = []
    try:
        profile = load_mapping(TARGET_ROOT / "target-profile.yml", "target-profile-unreadable")
        if (
            profile.get("schema") != "deploy/target-profile/v1"
            or profile.get("id") != TARGET
            or profile.get("status") != "planned-not-live-selected"
            or profile.get("baseline") != "absent"
            or profile.get("live_alignment") != "not-checked"
        ):
            codes.append("target-profile-invalid")
        provider = profile.get("provider")
        if not isinstance(provider, dict) or provider.get("family") != "aws" or provider.get("selection_status") != "unresolved-e0-required":
            codes.append("provider-selection-invalid")
        mutation = profile.get("target_mutation")
        if not isinstance(mutation, dict) or mutation.get("status") != "blocked" or mutation.get("allowed_operation") != "create-only":
            codes.append("target-mutation-not-blocked")
        facts = profile.get("e0_required_facts")
        if not isinstance(facts, list):
            codes.append("e0-facts-invalid")
        else:
            actual_fact_ids = {
                item.get("id")
                for item in facts
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            if actual_fact_ids != KNOWN_E0_FACTS or any(
                not isinstance(item, dict) or item.get("status") != "unresolved-e0-required"
                for item in facts
            ):
                codes.append("e0-facts-invalid")
    except ControlFailure as failure:
        codes.extend(failure.codes)

    try:
        scope = load_mapping(
            TARGET_ROOT / "scopes" / SCOPE / "declaration-contract.yml",
            "scope-contract-unreadable",
        )
        program = scope.get("program")
        verification = scope.get("verification")
        if (
            scope.get("schema") != "deploy/target-scope-contract/v1"
            or scope.get("target") != TARGET
            or scope.get("id") != "kanbien-core-platform-bootstrap-runtime"
            or not isinstance(program, dict)
            or program.get("id") != "kanbien-core-server"
            or program.get("contract") != "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"
            or program.get("image_contract") != "infra/04.deploy/03.product/image/core-server/image-contract.yml"
            or not isinstance(verification, dict)
            or verification.get("route_exposure") != "private-verifier-only"
            or verification.get("status") != "unresolved-e0-required"
        ):
            codes.append("scope-contract-invalid")
    except ControlFailure as failure:
        codes.extend(failure.codes)

    try:
        program_contract = load_mapping(PROGRAM_CONTRACT, "runnable-program-contract-unreadable")
        programs = program_contract.get("runnable_programs")
        images = program_contract.get("image_contracts")
        candidates = program_contract.get("package_candidates")
        if (
            program_contract.get("schema") != "deploy/runnable-program-contract/v1"
            or not isinstance(programs, list)
            or not any(isinstance(item, dict) and item.get("id") == "kanbien-core-server" for item in programs)
            or not isinstance(images, list)
            or not any(
                isinstance(item, dict)
                and item.get("id") == "kanbien-core-server-image"
                and item.get("program") == "kanbien-core-server"
                and item.get("command_mode") == "exec"
                for item in images
            )
            or not isinstance(candidates, list)
            or not any(
                isinstance(item, dict)
                and item.get("id") == "kanbien-core-server-candidate"
                and item.get("immutable_identity_rule") == "runtime-bound-sha256"
                for item in candidates
            )
        ):
            codes.append("runnable-program-contract-invalid")
    except ControlFailure as failure:
        codes.extend(failure.codes)

    try:
        image = load_mapping(IMAGE_CONTRACT, "image-contract-unreadable")
        if (
            image.get("schema") != "deploy/core-server-image-contract/v1"
            or image.get("id") != "kanbien-core-server-image"
            or image.get("program_id") != "kanbien-core-server"
            or image.get("command") != ["node", "artifacts/kanbien-core-server.main.js"]
        ):
            codes.append("image-contract-invalid")
    except ControlFailure as failure:
        codes.extend(failure.codes)
    return tuple(dict.fromkeys(codes))


def parse_arguments(capability: str, arguments: list[str]) -> tuple[tuple[str, ...], dict[str, bool]]:
    required: dict[str, str] = {}
    if capability == "deploy-candidate":
        required = {
            "--candidate-id": "candidate-id-required",
            "--image-digest": "immutable-image-digest-required",
            "--approved-change-set": "approved-change-set-required",
        }
    elif capability == "verify-candidate":
        required = {
            "--candidate-id": "candidate-id-required",
            "--image-digest": "immutable-image-digest-required",
            "--receipt-reference": "receipt-reference-required",
        }

    supplied: dict[str, str] = {}
    codes: list[str] = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--json":
            index += 1
            continue
        if argument == "--target":
            codes.append("target-selector-not-allowed")
            index += 2
            continue
        if argument not in required or index + 1 >= len(arguments) or arguments[index + 1].startswith("--"):
            codes.append("arguments-invalid")
            index += 1
            continue
        if argument in supplied:
            codes.append("arguments-invalid")
        else:
            supplied[argument] = arguments[index + 1]
        index += 2

    for argument, code in required.items():
        if argument not in supplied:
            codes.append(code)
    if "--candidate-id" in supplied and not CANDIDATE_ID_RE.fullmatch(supplied["--candidate-id"]):
        codes.append("candidate-id-invalid")
    if "--image-digest" in supplied and not IMAGE_DIGEST_RE.fullmatch(supplied["--image-digest"]):
        codes.append("immutable-image-digest-invalid")
    for argument in ("--approved-change-set", "--receipt-reference"):
        if argument in supplied and not REFERENCE_RE.fullmatch(supplied[argument]):
            codes.append("approval-reference-invalid")
    return tuple(dict.fromkeys(codes)), {key.removeprefix("--").replace("-", "_"): key in supplied for key in required}


def report(capability: str, verdict: str, findings: list[dict[str, str]], evidence: dict[str, bool]) -> str:
    effect = "aws-mutation" if capability == "deploy-candidate" else "read-only"
    return json.dumps(
        {
            "schema": "deploy/target-control-report/v1",
            "capability": capability,
            "effect": effect,
            "external_access_attempted": False,
            "findings": findings,
            "input_evidence_present": evidence,
            "lifecycle_stage": "50-deploy" if capability != "verify-candidate" else "60-run",
            "scope": SCOPE,
            "target": TARGET,
            "verdict": verdict,
        },
        sort_keys=True,
    )


def run(capability: str, arguments: list[str]) -> int:
    argument_codes, evidence = parse_arguments(capability, arguments)
    assertion_codes = static_assertions()
    findings = [{"code": code} for code in argument_codes + assertion_codes]
    if argument_codes or assertion_codes:
        print(report(capability, "failed", findings, evidence))
        return 1
    findings.extend(
        {"code": "live-target-fact-unresolved", "fact_id": fact_id}
        for fact_id in sorted(KNOWN_E0_FACTS)
    )
    findings.append({"code": "blocked-live-target-not-selected"})
    print(report(capability, "blocked", findings, evidence))
    return 2


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2:]))

#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-target-alignment
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate safe normalized target-alignment evidence against a bounded declaration without provider access.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.validate-target-alignment.wrapper
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh
"""Provider-neutral, fail-closed target alignment validation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any
import yaml

BASELINE = {
    "right-destination", "right-application", "known-healthy-baseline",
    "allowed-deployment-route", "package-destination", "required-access",
    "required-settings", "change-safety", "freshness-and-drift",
}
TARGETS = {"kanbien-core-platform", "example-target"}
OUTCOMES = {"match", "mismatch", "missing", "unknown"}
# Values emitted by the existing bounded AWS producer, never caller text.
FINDINGS = {
    "delivery-inventory-not-covered", "unavailable", "not-found", "access-denied", "invalid-response",
    "arguments-invalid", "account-match", "immutable-digest-present", "foundation-ready",
    "foundation-runtime-output-missing", "accepted-release-invalid", "runtime-absent", "runtime-not-absent",
    "accepted-runtime-healthy", "restore-source-runtime-healthy", "accepted-runtime-not-healthy",
    "runtime-task-definition-missing", "runtime-configuration-declared", "roles-present",
    "fixed-create-route-ready", "fixed-update-route-ready", "fixed-restore-route-ready", "route-not-ready",
    "retained-accepted-release-and-no-automatic-retry", "accepted-release-not-retained", "fresh-read-only-inspection",
}

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "DIAGNOSTIC_CODE=TARGET_ALIGNMENT_ARGUMENTS_INVALID\n")

def selected(value, allowed):
    return value if isinstance(value, str) and value in allowed else None

def mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError("mapping-required")
    return value

def main() -> int:
    parser = Parser(add_help=False)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    codes: list[str] = ["arguments-invalid"] if unknown else []
    try:
        contract = mapping(args.contract)
        declared = contract.get("assertions")
        ids = [item.get("id") for item in declared if isinstance(item, dict)] if isinstance(declared, list) else []
        declared_ids = {value for value in ids if isinstance(value, str)}
        if contract.get("schema") != "deploy/target-alignment-contract/v1" or not all(isinstance(value, str) for value in ids) or declared_ids != BASELINE:
            codes.append("target-alignment-contract-invalid")
    except (OSError, yaml.YAMLError, ValueError):
        contract = {}; codes.append("target-alignment-contract-unreadable")
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        facts = evidence.get("assertions") if isinstance(evidence, dict) else None
        items = [item for item in facts if isinstance(item, dict)] if isinstance(facts, list) else []
        actual = {item.get("id"): item.get("outcome") for item in items if isinstance(item.get("id"), str)}
        if not isinstance(evidence, dict) or evidence.get("schema") != "deploy/target-alignment-evidence/v1" or any(not isinstance(item.get("id"), str) for item in items) or set(actual) != BASELINE:
            codes.append("target-alignment-evidence-invalid")
        elif any(actual[item] != "match" for item in BASELINE):
            codes.append("target-alignment-not-proven")
    except (OSError, UnicodeError, json.JSONDecodeError):
        evidence = {}; codes.append("target-alignment-evidence-unreadable")
    safe_assertions = []
    if isinstance(evidence, dict) and isinstance(evidence.get("assertions"), list):
        safe_assertions = [
            {"id": item.get("id"), "outcome": selected(item.get("outcome"), OUTCOMES), "finding_code": selected(item.get("finding_code"), FINDINGS)}
            for item in evidence["assertions"]
            if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id") in BASELINE
        ]
    report = {
        "schema": "deploy/target-alignment-report/v1",
        "target": selected(contract.get("target"), TARGETS),
        "verdict": "aligned" if not codes else "blocked",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
        "assertions": safe_assertions,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1

if __name__ == "__main__": sys.exit(main())

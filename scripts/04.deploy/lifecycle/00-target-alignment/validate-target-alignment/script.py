#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-target-alignment
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate safe normalized target-alignment evidence against a bounded declaration without provider access.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
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

def mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError("mapping-required")
    return value

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    codes: list[str] = []
    try:
        contract = mapping(args.contract)
        declared = contract.get("assertions")
        declared_ids = {item.get("id") for item in declared if isinstance(item, dict)} if isinstance(declared, list) else set()
        if contract.get("schema") != "deploy/target-alignment-contract/v1" or declared_ids != BASELINE:
            codes.append("target-alignment-contract-invalid")
    except (OSError, yaml.YAMLError, ValueError):
        contract = {}; codes.append("target-alignment-contract-unreadable")
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        facts = evidence.get("assertions") if isinstance(evidence, dict) else None
        actual = {item.get("id"): item.get("outcome") for item in facts if isinstance(item, dict)} if isinstance(facts, list) else {}
        if evidence.get("schema") != "deploy/target-alignment-evidence/v1" or set(actual) != BASELINE:
            codes.append("target-alignment-evidence-invalid")
        elif any(actual[item] != "match" for item in BASELINE):
            codes.append("target-alignment-not-proven")
    except (OSError, json.JSONDecodeError):
        evidence = {}; codes.append("target-alignment-evidence-unreadable")
    safe_assertions = []
    if isinstance(evidence, dict) and isinstance(evidence.get("assertions"), list):
        safe_assertions = [
            {"id": item.get("id"), "outcome": item.get("outcome"), "finding_code": item.get("finding_code")}
            for item in evidence["assertions"]
            if isinstance(item, dict) and item.get("id") in BASELINE
        ]
    report = {
        "schema": "deploy/target-alignment-report/v1",
        "target": contract.get("target") if isinstance(contract, dict) else None,
        "verdict": "aligned" if not codes else "blocked",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
        "assertions": safe_assertions,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1

if __name__ == "__main__": sys.exit(main())

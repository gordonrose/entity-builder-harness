#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-provider-condition-evidence
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate safe, provider-neutral evidence for a provider-controlled asynchronous condition.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


STATUSES = {"not-requested", "requested", "waiting-on-provider", "verified", "expired", "waived-by-approved-exception"}
REQUIRED = {"schema", "condition_id", "target", "status", "checked_at", "next_check_after", "evidence_reference"}
WAIVER_REQUIRED = {"authority_reference", "reason_code", "expires_at", "compensating_controls", "follow_up_owner"}


def timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def safe_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "@" not in value and "://" not in value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate safe provider-condition evidence.")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    codes: list[str] = []
    try:
        evidence = yaml.safe_load(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(evidence, dict):
            raise ValueError
    except (OSError, yaml.YAMLError, ValueError):
        evidence = {}
        codes.append("provider-condition-evidence-unreadable")
    if not REQUIRED.issubset(evidence) or evidence.get("schema") != "deploy/provider-condition-evidence/v1":
        codes.append("provider-condition-evidence-invalid")
    if evidence.get("status") not in STATUSES:
        codes.append("provider-condition-status-invalid")
    if not timestamp(evidence.get("checked_at")) or not timestamp(evidence.get("next_check_after")):
        codes.append("provider-condition-timestamp-invalid")
    for field in ("condition_id", "target", "evidence_reference"):
        if not safe_string(evidence.get(field)):
            codes.append("provider-condition-evidence-unsafe")
            break
    if evidence.get("status") == "waived-by-approved-exception":
        waiver = evidence.get("waiver")
        if not isinstance(waiver, dict) or not WAIVER_REQUIRED.issubset(waiver):
            codes.append("provider-condition-waiver-invalid")
        elif not all(safe_string(waiver[field]) for field in ("authority_reference", "reason_code", "follow_up_owner")) or not timestamp(waiver.get("expires_at")) or not isinstance(waiver.get("compensating_controls"), list) or not waiver["compensating_controls"]:
            codes.append("provider-condition-waiver-invalid")
    report = {
        "schema": "deploy/provider-condition-evidence-report/v1",
        "condition_id": evidence.get("condition_id") if isinstance(evidence.get("condition_id"), str) else None,
        "verdict": "passed" if not codes else "failed",
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not codes else 1


if __name__ == "__main__":
    sys.exit(main())

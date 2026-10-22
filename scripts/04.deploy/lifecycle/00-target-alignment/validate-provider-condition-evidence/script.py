#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-provider-condition-evidence
#   version: 3
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate safe, provider-neutral evidence for a provider-controlled asynchronous condition, including freshness, validity boundaries, and an explicit waiver's expiry.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   used_by:
#   - id: deploy.command.kanbien-core-platform.validate-cost-condition
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/validate-cost-condition/script.sh
#   effects:
#   - read-only

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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


def parsed_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def safe_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "@" not in value and "://" not in value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate safe provider-condition evidence.")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--required-status", action="append", default=[])
    parser.add_argument("--at")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    codes: list[str] = []
    now = datetime.now(timezone.utc)
    if args.at is not None:
        if not timestamp(args.at):
            codes.append("provider-condition-reference-time-invalid")
        else:
            now = parsed_timestamp(args.at)
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
    if args.required_status and evidence.get("status") not in set(args.required_status):
        codes.append("provider-condition-status-not-accepted")
    checked_at = evidence.get("checked_at")
    validity_boundary = evidence.get("next_check_after")
    if not timestamp(checked_at) or not timestamp(validity_boundary):
        codes.append("provider-condition-timestamp-invalid")
    else:
        checked = parsed_timestamp(checked_at)
        boundary = parsed_timestamp(validity_boundary)
        if checked > now:
            codes.append("provider-condition-observation-in-future")
        if boundary <= checked:
            codes.append("provider-condition-validity-window-invalid")
        elif evidence.get("status") == "verified" and now >= boundary:
            codes.append("provider-condition-evidence-stale")
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
        elif parsed_timestamp(waiver["expires_at"]) <= now:
            codes.append("provider-condition-waiver-expired")
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

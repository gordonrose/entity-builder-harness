#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.local-qualification.entity-smoke-proof
#   version: 2
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.qualification
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Capture only exact successful, locally run qualification identities for an entity-smoke artifact before package custody.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-entity-smoke
#     path: .github/workflows/publish-kanbien-core-platform-entity-smoke.yml
"""Turn an existing trusted selector result into bounded package-custody input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


TARGET = "kanbien-core-platform"
SCOPE = "entity-smoke"
REQUIRED_CHECKS = frozenset({"entity-smoke-infrastructure-route", "entity-smoke-composition-suite", "secret-dependency-declaration-regression"})
SHA = re.compile(r"^[a-f0-9]{40}$")
DIGEST = re.compile(r"^[a-f0-9]{64}$")


class QualificationFailure(Exception):
    pass


def require(value: bool) -> None:
    if not value: raise QualificationFailure()


def capture(report: object) -> dict:
    require(isinstance(report, dict) and report.get("schema") == "repo/check-selection-report/v1" and report.get("stage") == "local" and report.get("verdict") == "passed" and report.get("findings") == [])
    source, checks = report.get("source_revision"), report.get("checks")
    require(isinstance(source, str) and SHA.fullmatch(source) is not None and isinstance(checks, list))
    selected: dict[str, dict] = {}
    for item in checks:
        if not isinstance(item, dict) or item.get("check_id") not in REQUIRED_CHECKS: continue
        identity = item["check_id"]
        require(identity not in selected and item.get("status") == "passed" and item.get("stage") == "local" and item.get("source_revision") == source and item.get("evidence_source") == "local-runner")
        input_digest, evidence_key = item.get("input_digest"), item.get("evidence_key")
        require(isinstance(input_digest, str) and DIGEST.fullmatch(input_digest) is not None and isinstance(evidence_key, str) and DIGEST.fullmatch(evidence_key) is not None)
        selected[identity] = {"input_digest": input_digest, "evidence_key": evidence_key}
    require(set(selected) == REQUIRED_CHECKS)
    return {"schema": "deploy/local-qualification/v1", "target": TARGET, "scope": SCOPE, "source_revision": source, "checks": dict(sorted(selected.items()))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["capture"])
    parser.add_argument("--selector-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.selector_report.read_bytes()
        require(len(raw) <= 4 * 1024 * 1024 and not args.output.exists())
        value = capture(json.loads(raw))
        args.output.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError, TypeError, QualificationFailure):
        print(json.dumps({"schema": "deploy/local-qualification-report/v1", "verdict": "failed", "findings": [{"code": "local-qualification-evidence-invalid"}]}))
        return 1
    print(json.dumps({"schema": "deploy/local-qualification-report/v1", "verdict": "passed", "qualification": value}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.local-qualification.entity-smoke-proof
#   version: 3
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-25"
#   layer: 04.deploy
#   domain: deployment.qualification
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind current qualification identities to private successful local proof, including unchanged trusted reuse, before package custody.
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
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT / "scripts/repo/check-selection"))
from local_cache import LocalCache


TARGET = "kanbien-core-platform"
SCOPE = "entity-smoke"
REQUIRED_CHECKS = frozenset({"entity-smoke-infrastructure-route", "entity-smoke-composition-suite", "secret-dependency-declaration-regression"})
SHA = re.compile(r"^[a-f0-9]{40}$")
DIGEST = re.compile(r"^[a-f0-9]{64}$")


class QualificationFailure(Exception):
    pass


def require(value: bool) -> None:
    if not value: raise QualificationFailure()


def capture(report: object, current: object, cache: LocalCache) -> dict:
    require(isinstance(report, dict) and report.get("schema") == "repo/check-selection-report/v1" and report.get("stage") == "local" and report.get("verdict") == "passed" and report.get("findings") == [])
    source, checks = report.get("source_revision"), report.get("checks")
    require(isinstance(source, str) and SHA.fullmatch(source) is not None and isinstance(checks, list))
    require(isinstance(current, dict) and current.get("schema") == "repo/check-selection-report/v1" and current.get("stage") == "local" and current.get("verdict") in {"planned", "passed"} and current.get("findings") == [] and current.get("source_revision") == source and isinstance(current.get("checks"), list))
    expected_rows = [item for item in current["checks"] if isinstance(item, dict) and item.get("check_id") in REQUIRED_CHECKS]
    expected = {item["check_id"]: item for item in expected_rows}
    require(set(expected) == REQUIRED_CHECKS and len(expected_rows) == len(REQUIRED_CHECKS))
    selected: dict[str, dict] = {}
    for item in checks:
        if not isinstance(item, dict) or item.get("check_id") not in REQUIRED_CHECKS: continue
        identity = item["check_id"]
        require(identity not in selected and item.get("status") == "passed" and item.get("stage") == "local" and item.get("source_revision") == source and item.get("evidence_source") in {"local-runner", "trusted-worktree-cache"})
        input_digest, evidence_key = item.get("input_digest"), item.get("evidence_key")
        require(isinstance(input_digest, str) and DIGEST.fullmatch(input_digest) is not None and isinstance(evidence_key, str) and DIGEST.fullmatch(evidence_key) is not None)
        require(expected[identity].get("input_digest") == input_digest and expected[identity].get("evidence_key") == evidence_key)
        proof = cache.read(evidence_key)
        require(proof.get("check_id") == identity and proof.get("input_digest") == input_digest)
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
        planned = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/repo/check-selection/script.py"), "--checks", *sorted(REQUIRED_CHECKS), "--task-paths", "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml", "--json"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=120)
        value = capture(json.loads(raw), json.loads(planned.stdout), LocalCache(ROOT, create=False))
        args.output.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError, TypeError, subprocess.SubprocessError, QualificationFailure):
        print(json.dumps({"schema": "deploy/local-qualification-report/v1", "verdict": "failed", "findings": [{"code": "local-qualification-evidence-invalid"}]}))
        return 1
    print(json.dumps({"schema": "deploy/local-qualification-report/v1", "verdict": "passed", "qualification": value}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.report-recognition-candidates
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Report recognition-candidate review state and allowed next actions without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.workflow.review-recognition-candidates
#       path: .agentic/02.rag-rulebook/workflows/review-recognition-candidates.md
#     - id: rag-rulebook.standard.recognition-candidate-review
#       path: .agentic/02.rag-rulebook/standards/recognition-candidate-review.md
#     - id: rag-rulebook.script.report-recognition-candidates.readme
#       path: scripts/02.rag-rulebook/report-recognition-candidates/README.md
#     - id: rag-rulebook.script.report-recognition-candidates.smoke-test
#       path: scripts/02.rag-rulebook/report-recognition-candidates/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for recognition-candidate reporting.", file=sys.stderr)
    sys.exit(2)


DEFAULT_ROOT = ".agentic/02.rag-rulebook/recognition-candidates"
VALIDATOR = "scripts/02.rag-rulebook/validate-recognition-candidates/script.sh"
TERMINAL_STATUSES = {"accepted", "rejected", "merged"}


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def usage() -> str:
    return """Usage:
  report-recognition-candidates/script.sh --current [--json]
  report-recognition-candidates/script.sh --candidate <path> [--candidate <path> ...] [--json]

Validates recognition-candidate records, then reports review state and allowed
next actions without mutating curated recognition sources.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.candidate):
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def run_validator(args: argparse.Namespace) -> dict[str, Any]:
    command = ["bash", VALIDATOR]
    if args.current:
        command.append("--current")
    else:
        for candidate in args.candidate:
            command.extend(["--candidate", candidate])
    command.append("--json")

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout, file=sys.stderr, end="")
        if result.stderr.strip():
            print(result.stderr, file=sys.stderr, end="")
        print("ERROR: recognition candidates must validate before review reporting.", file=sys.stderr)
        sys.exit(result.returncode)
    return json.loads(result.stdout)


def load_yaml(path: str) -> dict[str, Any]:
    data = yaml.safe_load(repo_path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def stage_counts(coverage: dict[str, Any]) -> dict[str, int]:
    counts = {"present": 0, "missing": 0, "not-required": 0}
    stages = coverage.get("stages") if isinstance(coverage.get("stages"), dict) else {}
    for stage in stages.values():
        if not isinstance(stage, dict):
            continue
        status = stage.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def action(action_id: str, label: str, reason: str) -> dict[str, str]:
    return {"action_id": action_id, "label": label, "reason": reason}


def allowed_actions(data: dict[str, Any]) -> list[dict[str, str]]:
    status = str(data.get("status") or "")
    coverage = data.get("coverage") if isinstance(data.get("coverage"), dict) else {}
    coverage_required = coverage.get("required") is True
    coverage_status = coverage.get("status") or "not-required"

    actions: list[dict[str, str]] = []
    if status == "needs-review":
        actions.append(action("keep-pending", "Keep pending", "Use while review is not ready to make a terminal decision."))
        if coverage_required and coverage_status != "covered":
            actions.append(action("add-corpus-coverage", "Add corpus coverage", "Source material, structured rules, chunks, or selector proof are still missing."))
            actions.append(action("defer", "Defer", "Use when the term may be valid but needs more evidence or coverage."))
        else:
            actions.append(action("accept", "Accept", "Allowed when reviewer confirms stable meaning, curated-source update, and selector proof."))
            actions.append(action("defer", "Defer", "Use if the term is meaningful but should wait for more examples or deeper corpus coverage."))
        actions.append(action("reject", "Reject", "Use if the term is too broad, unsafe, redundant, or one-off."))
        actions.append(action("merge", "Merge", "Use if another candidate already captures the same meaning."))
    elif status == "deferred":
        actions.append(action("keep-deferred", "Keep deferred", "Use while waiting for more examples, narrower wording, or coverage."))
        actions.append(action("add-evidence", "Add evidence", "Add observed examples or coverage proof before revisiting the decision."))
        if not coverage_required or coverage_status == "covered":
            actions.append(action("accept", "Accept", "Allowed if the reviewer now has enough evidence and selector proof."))
        actions.append(action("reject", "Reject", "Use if review shows the term should not enter curated sources."))
        actions.append(action("merge", "Merge", "Use if another candidate now captures the same meaning."))
    elif status == "accepted":
        actions.append(action("audit", "Audit accepted record", "Accepted candidates should only change through a new governed review."))
    elif status == "rejected":
        actions.append(action("no-action", "No action", "Rejected candidates should stay closed unless new evidence creates a new candidate."))
    elif status == "merged":
        actions.append(action("inspect-target", "Inspect merge target", "Use the merged-into candidate as the durable review record."))
    else:
        actions.append(action("fix-record", "Fix record", "Candidate status is not recognized by the reporter."))

    return actions


def review_needs(data: dict[str, Any]) -> list[str]:
    needs: list[str] = []
    status = str(data.get("status") or "")
    coverage = data.get("coverage") if isinstance(data.get("coverage"), dict) else {}
    coverage_required = coverage.get("required") is True
    coverage_status = coverage.get("status") or "not-required"
    suggested = data.get("suggested") if isinstance(data.get("suggested"), dict) else {}

    if status == "needs-review":
        needs.append("review decision")
    if coverage_required and coverage_status != "covered":
        needs.append("complete staged corpus coverage")
    if status in {"needs-review", "deferred"} and suggested.get("source_id"):
        needs.append("deduplicate against curated sources")
    if status not in TERMINAL_STATUSES:
        needs.append("human reviewer before curated-source mutation")
    return needs


def build_report(validator_report: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    coverage_counts: dict[str, int] = {}

    for summary in validator_report.get("candidates", []):
        path = summary["path"]
        data = load_yaml(path)
        observed = data.get("observed") if isinstance(data.get("observed"), dict) else {}
        suggested = data.get("suggested") if isinstance(data.get("suggested"), dict) else {}
        review = data.get("review") if isinstance(data.get("review"), dict) else {}
        coverage = data.get("coverage") if isinstance(data.get("coverage"), dict) else {}
        coverage_status = coverage.get("status") or "not-required"
        coverage_counts[coverage_status] = coverage_counts.get(coverage_status, 0) + 1

        candidates.append(
            {
                "path": path,
                "candidate_id": data.get("candidate_id"),
                "term": observed.get("term"),
                "sentence": observed.get("sentence"),
                "status": data.get("status"),
                "review_decision": review.get("decision"),
                "lifecycle_directory": summary.get("lifecycle_directory"),
                "suggested_source_id": suggested.get("source_id"),
                "suggested_category": suggested.get("category"),
                "suggested_canonical_id": suggested.get("canonical_id"),
                "coverage_required": coverage.get("required") is True,
                "coverage_status": coverage_status,
                "coverage_stage_counts": stage_counts(coverage),
                "review_needs": review_needs(data),
                "allowed_next_actions": allowed_actions(data),
            }
        )

    return {
        "ok": validator_report.get("ok") is True,
        "schema": "rag-rulebook/recognition-candidate-review-report/v1",
        "root": str(ROOT),
        "counts": {
            "candidates": len(candidates),
            "statuses": validator_report.get("counts", {}).get("statuses", {}),
            "coverage_statuses": dict(sorted(coverage_counts.items())),
        },
        "candidates": candidates,
        "warnings": validator_report.get("warnings", []),
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Recognition candidate review report: {report['counts']['candidates']} candidate(s).")
    for candidate in report["candidates"]:
        print("")
        print(f"- {candidate['term']} [{candidate['status']} / {candidate['coverage_status']}]")
        print(f"  path: {candidate['path']}")
        print(f"  canonical: {candidate['suggested_canonical_id']} -> {candidate['suggested_source_id']}")
        print(f"  sentence: {candidate['sentence']}")
        if candidate["review_needs"]:
            print("  review needs:")
            for need in candidate["review_needs"]:
                print(f"    - {need}")
        print("  allowed next actions:")
        for next_action in candidate["allowed_next_actions"]:
            print(f"    - {next_action['action_id']}: {next_action['reason']}")

    for warning in report.get("warnings", []):
        print(f"WARNING: {warning}", file=sys.stderr)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    validator_report = run_validator(args)
    report = build_report(validator_report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

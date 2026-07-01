#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-source-to-rule-draft-packet
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate a read-only semantic draft packet for source-to-rule YAML proposal work.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.script.generate-source-to-rule-draft-packet.readme
#       path: scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/README.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPORT_SCHEMA = "rag-rulebook/source-to-rule-draft-packet/v1"
WORK_ORDER_SCRIPT = "scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh"
DEFAULT_MANIFEST = ".agentic/02.rag-rulebook/source-projections/v1.yml"
GENERATOR = "source-to-rule-draft-packet"
GENERATOR_VERSION = "v1"
DEFAULT_MAX_FILE_CHARS = 40000


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
  generate-source-to-rule-draft-packet/script.sh --current [--json]
  generate-source-to-rule-draft-packet/script.sh --current --projection-id <id> [--json]
  generate-source-to-rule-draft-packet/script.sh --current --manifest <path> [--max-file-chars <n>] [--json]

Generates a read-only semantic draft packet for source-to-rule proposal work.
The command does not write YAML rules, derivation reports, chunks, or
evaluations.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--projection-id")
    parser.add_argument("--max-file-chars", type=int, default=DEFAULT_MAX_FILE_CHARS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if not args.current:
        print("ERROR: --current is required.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.max_file_chars < 1000:
        print("ERROR: --max-file-chars must be at least 1000.", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def file_sha256(path: str) -> str | None:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return None
    digest = hashlib.sha256()
    with path_obj.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_bounded(path: str, max_chars: int) -> dict[str, Any]:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return {
            "path": path,
            "exists": False,
            "sha256": None,
            "content": "",
            "truncated": False,
            "char_count": 0,
        }
    text = path_obj.read_text(encoding="utf-8")
    truncated = len(text) > max_chars
    return {
        "path": path,
        "exists": True,
        "sha256": file_sha256(path),
        "content": text[:max_chars],
        "truncated": truncated,
        "char_count": len(text),
    }


def run_work_order(args: argparse.Namespace) -> dict[str, Any]:
    command = [
        "bash",
        WORK_ORDER_SCRIPT,
        "--current",
        "--manifest",
        args.manifest,
        "--json",
    ]
    if args.projection_id:
        command.extend(["--projection-id", args.projection_id])
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stderr.strip() or result.stdout.strip() or "ERROR: work-order command did not emit JSON", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0 or not report.get("ok"):
        for error in report.get("errors") or []:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    return report


def unique_paths(items: list[Any]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for item in items:
        path = item.get("path") if isinstance(item, dict) else None
        if isinstance(path, str) and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def packet_for_order(order: dict[str, Any], max_chars: int) -> dict[str, Any]:
    source_paths = unique_paths(order.get("source_material") or [])
    rule_paths = unique_paths(order.get("expected_rule_paths") or [])
    report_paths = unique_paths(order.get("derivation_reports") or [])
    corpus_gap_paths = unique_paths(order.get("corpus_gap_paths") or [])
    evaluation_paths = unique_paths(order.get("expected_selector_evaluations") or [])

    return {
        "projection_id": order.get("id"),
        "target": order.get("target"),
        "projection_mode": order.get("projection_mode"),
        "mechanically_current": order.get("mechanically_current"),
        "semantic_review": order.get("semantic_review"),
        "draft_objectives": [
            "Extract or update small source claims from approved source material.",
            "Propose the narrowest structured YAML rule changes needed.",
            "Propose derivation report updates for conflict, drift, ownership, validation, and review state.",
            "Name required generated artifacts and selector evaluations that must be rebuilt or rerun.",
            "Leave all proposed semantic changes review-gated.",
        ],
        "banned_actions": [
            "Do not write files from this packet.",
            "Do not approve derivation reports.",
            "Do not mark chunks, selector evaluations, runtime outputs, corpus packages, or deployment readiness current without checks.",
            "Do not hide conflicts or drift behind summary wording.",
            "Do not treat selected context as deploy execution approval.",
        ],
        "work_actions": order.get("work_actions") or [],
        "required_checks": order.get("required_checks") or [],
        "source_material": [read_bounded(path, max_chars) for path in source_paths],
        "current_rule_files": [read_bounded(path, max_chars) for path in rule_paths],
        "derivation_reports": [read_bounded(path, max_chars) for path in report_paths],
        "corpus_gaps": [read_bounded(path, max_chars) for path in corpus_gap_paths],
        "selector_evaluations": [read_bounded(path, max_chars) for path in evaluation_paths],
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    work_order = run_work_order(args)
    packets = [packet_for_order(order, args.max_file_chars) for order in work_order.get("work_orders") or []]
    truncated_files = [
        item["path"]
        for packet in packets
        for group in ["source_material", "current_rule_files", "derivation_reports", "corpus_gaps", "selector_evaluations"]
        for item in packet[group]
        if item.get("truncated")
    ]
    report = {
        "schema": REPORT_SCHEMA,
        "ok": True,
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "manifest_path": args.manifest,
        "max_file_chars": args.max_file_chars,
        "work_order": {
            "schema": work_order.get("schema"),
            "projection_sets": work_order.get("counts", {}).get("projection_sets"),
            "work_actions": work_order.get("counts", {}).get("work_actions"),
        },
        "counts": {
            "draft_packets": len(packets),
            "truncated_files": len(truncated_files),
        },
        "draft_packets": packets,
        "truncated_files": truncated_files,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Source-to-rule draft packet ready: {len(packets)} projection set(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

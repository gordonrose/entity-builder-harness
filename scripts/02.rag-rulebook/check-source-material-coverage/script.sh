#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-source-material-coverage
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Verify governed source material has a rule, gap, or derivation outcome and indexed/chunked rule proof.
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
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.check-source-material-coverage.readme
#       path: scripts/02.rag-rulebook/check-source-material-coverage/README.md
#     - id: rag-rulebook.script.check-source-material-coverage.smoke-test
#       path: scripts/02.rag-rulebook/check-source-material-coverage/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for source-material coverage checks.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/source-material-coverage-report/v1"
SOURCE_ROOTS = [
    "docs/02.rag-rulebook/source-material",
    "docs/04.deploy/source-material",
]
RULE_ROOTS = [
    "docs/02.rag-rulebook/rules",
    "docs/04.deploy/rules",
]
DERIVATION_REPORT_ROOT = ".agentic/02.rag-rulebook/derivation-reports"
CORPUS_GAP_ROOT = ".agentic/02.rag-rulebook/corpus-gaps"
INDEX_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"


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
  check-source-material-coverage/script.sh --current [--json]

Checks governed source material under docs/02.rag-rulebook/source-material and
docs/04.deploy/source-material. Each non-README Markdown source must have at
least one governed outcome: structured rule YAML, source-to-rule derivation
report, or corpus-gap evidence. Structured rule outcomes must be present in the
generated index and chunk set.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
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
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_under(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def is_source_material_path(value: str) -> bool:
    return (
        is_under(value, SOURCE_ROOTS)
        and value.endswith(".md")
        and Path(value).name != "README.md"
    )


def is_rule_path(value: str) -> bool:
    return is_under(value, RULE_ROOTS) and value.endswith((".yml", ".yaml"))


def list_files(roots: list[str], suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        root_path = repo_path(root)
        if not root_path.exists():
            continue
        if root_path.is_file():
            candidates = [root_path]
        else:
            candidates = sorted(path for path in root_path.rglob("*") if path.is_file())
        for path in candidates:
            if path.suffix.lower() in suffixes:
                files.append(path)
    return sorted(set(files))


def load_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"{rel(path)} failed to parse as YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel(path)} must contain a YAML object")
        return None
    return data


def collect_strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(collect_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(collect_strings(item))
    return found


def source_material_files() -> list[str]:
    return [
        rel(path)
        for path in list_files(SOURCE_ROOTS, {".md"})
        if path.name != "README.md"
    ]


def load_rule_source_refs(errors: list[str]) -> dict[str, list[str]]:
    by_source: dict[str, list[str]] = defaultdict(list)
    for path in list_files(RULE_ROOTS, {".yml", ".yaml"}):
        data = load_yaml(path, errors)
        if data is None:
            continue
        rule_path = rel(path)
        for value in collect_strings(data):
            if is_source_material_path(value):
                if not repo_path(value).exists():
                    errors.append(f"{rule_path} references missing source material: {value}")
                by_source[value].append(rule_path)
    return {key: sorted(set(values)) for key, values in by_source.items()}


def load_derivation_coverage(errors: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    reports_by_source: dict[str, list[str]] = defaultdict(list)
    rules_by_source: dict[str, list[str]] = defaultdict(list)
    for path in list_files([DERIVATION_REPORT_ROOT], {".yml", ".yaml"}):
        data = load_yaml(path, errors)
        if data is None:
            continue
        report_path = rel(path)
        source_change = data.get("source_change") if isinstance(data.get("source_change"), dict) else {}
        semantic_review = data.get("semantic_review") if isinstance(data.get("semantic_review"), dict) else {}
        target = data.get("target") if isinstance(data.get("target"), dict) else {}
        proposed = data.get("proposed_updates") if isinstance(data.get("proposed_updates"), dict) else {}

        sources: set[str] = set()
        for value in source_change.get("changed_paths") or []:
            if isinstance(value, str) and is_source_material_path(value):
                sources.add(value)
        for claim in semantic_review.get("source_claims") or []:
            if isinstance(claim, dict):
                evidence_path = claim.get("evidence_path")
                if isinstance(evidence_path, str) and is_source_material_path(evidence_path):
                    sources.add(evidence_path)

        rule_paths: set[str] = set()
        for field in ["affected_rule_paths", "expected_rule_paths"]:
            for value in target.get(field) or []:
                if isinstance(value, str) and is_rule_path(value) and repo_path(value).exists():
                    rule_paths.add(value)
        for value in proposed.get("rules") or []:
            if isinstance(value, str) and is_rule_path(value) and repo_path(value).exists():
                rule_paths.add(value)

        for source in sources:
            reports_by_source[source].append(report_path)
            rules_by_source[source].extend(sorted(rule_paths))

    return (
        {key: sorted(set(values)) for key, values in reports_by_source.items()},
        {key: sorted(set(values)) for key, values in rules_by_source.items()},
    )


def load_corpus_gap_coverage(errors: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    gaps_by_source: dict[str, list[str]] = defaultdict(list)
    rules_by_source: dict[str, list[str]] = defaultdict(list)
    for path in list_files([CORPUS_GAP_ROOT], {".yml", ".yaml"}):
        data = load_yaml(path, errors)
        if data is None:
            continue
        gap_path = rel(path)
        strings = collect_strings(data)
        sources = sorted({value for value in strings if is_source_material_path(value)})
        rule_paths = sorted({value for value in strings if is_rule_path(value) and repo_path(value).exists()})
        for source in sources:
            if not repo_path(source).exists():
                errors.append(f"{gap_path} references missing source material: {source}")
            gaps_by_source[source].append(gap_path)
            rules_by_source[source].extend(rule_paths)
    return (
        {key: sorted(set(values)) for key, values in gaps_by_source.items()},
        {key: sorted(set(values)) for key, values in rules_by_source.items()},
    )


def generate_index_and_chunks() -> tuple[dict[str, Any], dict[str, Any]]:
    index_result = subprocess.run(
        ["bash", INDEX_GENERATOR_SCRIPT],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    chunks_result = subprocess.run(
        ["bash", CHUNK_GENERATOR_SCRIPT, "--generate-current"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    index = json.loads(index_result.stdout)
    chunks = json.loads(chunks_result.stdout)
    if not isinstance(index, dict) or not isinstance(chunks, dict):
        raise ValueError("generated index and chunks must be JSON objects")
    return index, chunks


def indexed_rule_paths(index: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for artifact in index.get("artifacts") or []:
        if isinstance(artifact, dict):
            path = artifact.get("current_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    for candidate in index.get("chunk_candidates") or []:
        if isinstance(candidate, dict):
            path = candidate.get("source_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    return paths


def chunked_rule_paths(chunks: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for chunk in chunks.get("chunks") or []:
        if isinstance(chunk, dict):
            path = chunk.get("source_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    return paths


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    sources = source_material_files()
    rule_refs_by_source = load_rule_source_refs(errors)
    derivation_reports_by_source, derivation_rules_by_source = load_derivation_coverage(errors)
    corpus_gaps_by_source, corpus_gap_rules_by_source = load_corpus_gap_coverage(errors)
    index, chunks = generate_index_and_chunks()
    indexed_rules = indexed_rule_paths(index)
    chunked_rules = chunked_rule_paths(chunks)

    known_sources = set(sources)
    for source in sorted(set(rule_refs_by_source) | set(corpus_gaps_by_source) | set(derivation_reports_by_source)):
        if source not in known_sources and not repo_path(source).exists():
            errors.append(f"coverage record references missing source material: {source}")

    source_reports: list[dict[str, Any]] = []
    for source in sources:
        direct_rules = sorted(set(rule_refs_by_source.get(source, [])))
        derivation_reports = sorted(set(derivation_reports_by_source.get(source, [])))
        corpus_gaps = sorted(set(corpus_gaps_by_source.get(source, [])))
        claimed_rules = sorted(
            set(direct_rules)
            | set(derivation_rules_by_source.get(source, []))
            | set(corpus_gap_rules_by_source.get(source, []))
        )

        outcomes = {
            "structured_rules": direct_rules,
            "derivation_reports": derivation_reports,
            "corpus_gaps": corpus_gaps,
        }
        if not any(outcomes.values()):
            errors.append(
                f"{source} has no governed coverage outcome; add structured rule YAML, "
                "a source-to-rule derivation report, or a corpus gap record."
            )

        missing_index = [path for path in claimed_rules if path not in indexed_rules]
        missing_chunks = [path for path in claimed_rules if path not in chunked_rules]
        for path in missing_index:
            errors.append(f"{source} claims rule output not present in generated index: {path}")
        for path in missing_chunks:
            errors.append(f"{source} claims rule output not present in generated chunks: {path}")

        source_reports.append(
            {
                "path": source,
                "ok": bool(any(outcomes.values())) and not missing_index and not missing_chunks,
                "outcomes": outcomes,
                "claimed_rule_paths": claimed_rules,
                "indexed_rule_paths": sorted(path for path in claimed_rules if path in indexed_rules),
                "chunked_rule_paths": sorted(path for path in claimed_rules if path in chunked_rules),
                "missing_index_rule_paths": missing_index,
                "missing_chunk_rule_paths": missing_chunks,
            }
        )

    report = {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "source_roots": SOURCE_ROOTS,
        "rule_roots": RULE_ROOTS,
        "counts": {
            "sources": len(sources),
            "sources_with_structured_rules": sum(1 for item in source_reports if item["outcomes"]["structured_rules"]),
            "sources_with_derivation_reports": sum(1 for item in source_reports if item["outcomes"]["derivation_reports"]),
            "sources_with_corpus_gaps": sum(1 for item in source_reports if item["outcomes"]["corpus_gaps"]),
            "indexed_rule_paths": len(indexed_rules),
            "chunked_rule_paths": len(chunked_rules),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "sources": source_reports,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    else:
        print(f"Source material coverage valid: {len(sources)} source file(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

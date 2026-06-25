#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-rulebook-index
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: indexing
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate a rag-rulebook/rulebook-index/v1 JSON document without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.rulebook-index
#       path: .agentic/02.rag-rulebook/schemas/rulebook-index.schema.yml
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.script.generate-rulebook-index
#       path: scripts/02.rag-rulebook/generate-rulebook-index/script.sh
#     - id: rag-rulebook.script.validate-rulebook-index.readme
#       path: scripts/02.rag-rulebook/validate-rulebook-index/README.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


INDEX_SCHEMA = "rag-rulebook/rulebook-index/v1"
GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
REQUIRED_TOP_LEVEL = [
    "schema",
    "index_id",
    "generated_at",
    "source_roots",
    "corpus_packages",
    "artifacts",
    "rules",
    "rule_packs",
    "chunk_candidates",
    "graph_edges",
    "source_references",
    "path_mappings",
    "unresolved_references",
    "diagnostics",
    "provenance",
]


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
  validate-rulebook-index/script.sh --generate-current [--json]
  validate-rulebook-index/script.sh --index <path> [--json]

Validates a rag-rulebook/rulebook-index/v1 JSON document. The command is
read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--generate-current", action="store_true")
    parser.add_argument("--index")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    modes = [args.generate_current, args.index is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.index == "-":
        print("ERROR: --index - is not supported by this shell wrapper; use a saved JSON file.", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        return os.path.normpath(path_obj.as_posix())
    try:
        return path_obj.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path_obj.as_posix()


def resolve_ref_path(ref: str, owner_path: str) -> str:
    if ref.startswith(("docs/", ".agentic/", "scripts/", "AGENTS.md")):
        return normalize_path(ref)
    candidate = (repo_path(owner_path).parent / ref).resolve()
    return normalize_path(candidate)


def load_index(args: argparse.Namespace) -> dict[str, Any]:
    if args.generate_current:
        result = subprocess.run(
            ["bash", GENERATOR_SCRIPT],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        raw = result.stdout
    else:
        raw = Path(args.index).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("index JSON must be an object")
    return data


def list_field(data: dict[str, Any], field: str, errors: list[str]) -> list[dict[str, Any]]:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(f"{field} must be an array")
        return []
    items = [item for item in value if isinstance(item, dict)]
    if len(items) != len(value):
        errors.append(f"{field} must contain only objects")
    return items


def dict_field(data: dict[str, Any], field: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return {}
    return value


def string_value(item: dict[str, Any], field: str) -> str | None:
    value = item.get(field)
    return value if isinstance(value, str) and value else None


def report_duplicate(label: str, values: list[str], errors: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    for value in sorted(duplicates):
        errors.append(f"duplicate {label}: {value}")


def add_missing_required(data: dict[str, Any], errors: list[str]) -> None:
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing top-level field: {field}")


def path_should_exist(path: str) -> bool:
    if not path or "*" in path or path.startswith("corpus."):
        return False
    return path.startswith(("docs/", ".agentic/", "scripts/", "AGENTS.md"))


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    add_missing_required(data, errors)

    if data.get("schema") != INDEX_SCHEMA:
        errors.append(f"schema must be {INDEX_SCHEMA}")

    generated_at = data.get("generated_at")
    if isinstance(generated_at, str):
        try:
            dt.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("generated_at must be ISO-8601")
    else:
        errors.append("generated_at must be a string")

    source_roots = list_field(data, "source_roots", errors)
    corpus_packages = list_field(data, "corpus_packages", errors)
    artifacts = list_field(data, "artifacts", errors)
    rules = list_field(data, "rules", errors)
    rule_packs = list_field(data, "rule_packs", errors)
    chunk_candidates = list_field(data, "chunk_candidates", errors)
    graph_edges = list_field(data, "graph_edges", errors)
    source_references = list_field(data, "source_references", errors)
    path_mappings = list_field(data, "path_mappings", errors)
    unresolved_references = list_field(data, "unresolved_references", errors)
    diagnostics = dict_field(data, "diagnostics", errors)
    provenance = dict_field(data, "provenance", errors)

    source_root_ids = [value for item in source_roots if (value := string_value(item, "root_id"))]
    corpus_ids = [value for item in corpus_packages if (value := string_value(item, "corpus_id"))]
    artifact_refs = [value for item in artifacts if (value := string_value(item, "artifact_ref"))]
    rule_refs = [value for item in rules if (value := string_value(item, "rule_ref"))]
    rule_ids = [value for item in rules if (value := string_value(item, "rule_id"))]
    pack_refs = [value for item in rule_packs if (value := string_value(item, "pack_ref"))]
    pack_ids = [value for item in rule_packs if (value := string_value(item, "pack_id"))]
    chunk_ids = [value for item in chunk_candidates if (value := string_value(item, "chunk_id"))]
    edge_ids = [value for item in graph_edges if (value := string_value(item, "edge_id"))]
    source_ref_ids = [value for item in source_references if (value := string_value(item, "source_ref_id"))]

    for label, values in [
        ("source_roots[].root_id", source_root_ids),
        ("corpus_packages[].corpus_id", corpus_ids),
        ("artifacts[].artifact_ref", artifact_refs),
        ("rules[].rule_ref", rule_refs),
        ("rule_packs[].pack_ref", pack_refs),
        ("chunk_candidates[].chunk_id", chunk_ids),
        ("graph_edges[].edge_id", edge_ids),
        ("source_references[].source_ref_id", source_ref_ids),
        ("rules[].rule_id", rule_ids),
        ("rule_packs[].pack_id", pack_ids),
    ]:
        report_duplicate(label, values, errors)

    corpus_id_set = set(corpus_ids)
    artifact_ref_set = set(artifact_refs)
    rule_ref_set = set(rule_refs)
    pack_ref_set = set(pack_refs)
    chunk_id_set = set(chunk_ids)
    source_ref_id_set = set(source_ref_ids)
    proposed_paths = {
        value
        for item in path_mappings
        if isinstance(value := item.get("proposed_path"), str) and value
    }
    current_paths = {
        value
        for item in path_mappings
        if isinstance(value := item.get("current_path"), str) and value
    }
    all_refs = corpus_id_set | artifact_ref_set | rule_ref_set | pack_ref_set | chunk_id_set | source_ref_id_set

    artifact_by_ref = {
        item["artifact_ref"]: item
        for item in artifacts
        if isinstance(item.get("artifact_ref"), str)
    }
    artifact_by_path = {
        normalize_path(item["current_path"]): item["artifact_ref"]
        for item in artifacts
        if isinstance(item.get("current_path"), str) and isinstance(item.get("artifact_ref"), str)
    }
    edge_tuples = {
        (item.get("from_ref"), item.get("to_ref"), item.get("edge_type"))
        for item in graph_edges
    }
    unresolved_tuples = {
        (item.get("owner_ref"), item.get("ref"), item.get("ref_type"))
        for item in unresolved_references
    }

    for artifact in artifacts:
        artifact_ref = string_value(artifact, "artifact_ref")
        corpus_id = string_value(artifact, "corpus_id")
        current_path = string_value(artifact, "current_path")
        if not artifact_ref:
            errors.append("artifact missing artifact_ref")
            continue
        if not corpus_id or corpus_id not in corpus_id_set:
            errors.append(f"artifact has unknown corpus_id: {artifact_ref}")
        if current_path and path_should_exist(current_path) and not repo_path(current_path).is_file():
            errors.append(f"artifact current_path does not exist: {artifact_ref} -> {current_path}")
        for source_ref_id in artifact.get("source_ref_ids") or []:
            if source_ref_id not in source_ref_id_set:
                errors.append(f"artifact source_ref_id does not resolve: {artifact_ref} -> {source_ref_id}")
        if corpus_id and (artifact_ref, corpus_id, "belongs-to-corpus") not in edge_tuples:
            errors.append(f"artifact missing belongs-to-corpus edge: {artifact_ref} -> {corpus_id}")
        proposed_path = string_value(artifact, "proposed_path")
        if proposed_path and proposed_path not in proposed_paths:
            errors.append(f"artifact proposed_path lacks path mapping: {artifact_ref} -> {proposed_path}")

        for field, edge_type, ref_type in [
            ("related_ruleset_refs", "related-ruleset", "related-ruleset"),
            ("required_ruleset_refs", "required-ruleset", "required-ruleset"),
        ]:
            refs = artifact.get(field) or []
            if not isinstance(refs, list):
                errors.append(f"{artifact_ref} {field} must be an array")
                continue
            for ref in refs:
                if not isinstance(ref, str):
                    errors.append(f"{artifact_ref} {field} contains a non-string ref")
                    continue
                if current_path:
                    resolved = resolve_ref_path(ref, current_path)
                    target_ref = artifact_by_path.get(resolved)
                    if target_ref and (artifact_ref, target_ref, edge_type) not in edge_tuples:
                        errors.append(f"missing {edge_type} edge: {artifact_ref} -> {target_ref}")
                    if not target_ref and (artifact_ref, ref, ref_type) not in unresolved_tuples:
                        errors.append(f"missing unresolved reference entry: {artifact_ref} -> {ref}")

    for rule in rules:
        rule_ref = string_value(rule, "rule_ref")
        artifact_ref = string_value(rule, "artifact_ref")
        corpus_id = string_value(rule, "corpus_id")
        if not rule_ref:
            errors.append("rule missing rule_ref")
            continue
        if not artifact_ref or artifact_ref not in artifact_ref_set:
            errors.append(f"rule has unknown artifact_ref: {rule_ref}")
        if not corpus_id or corpus_id not in corpus_id_set:
            errors.append(f"rule has unknown corpus_id: {rule_ref}")
        if artifact_ref and (artifact_ref, rule_ref, "contains-rule") not in edge_tuples:
            errors.append(f"rule missing contains-rule edge: {artifact_ref} -> {rule_ref}")
        for chunk_id in rule.get("chunk_candidate_ids") or []:
            if chunk_id not in chunk_id_set:
                errors.append(f"rule chunk_candidate_id does not resolve: {rule_ref} -> {chunk_id}")

    for pack in rule_packs:
        pack_ref = string_value(pack, "pack_ref")
        artifact_ref = string_value(pack, "artifact_ref")
        corpus_id = string_value(pack, "corpus_id")
        if not pack_ref:
            errors.append("rule pack missing pack_ref")
            continue
        if not artifact_ref or artifact_ref not in artifact_ref_set:
            errors.append(f"rule pack has unknown artifact_ref: {pack_ref}")
        if not corpus_id or corpus_id not in corpus_id_set:
            errors.append(f"rule pack has unknown corpus_id: {pack_ref}")
        if artifact_ref and (artifact_ref, pack_ref, "contains-pack") not in edge_tuples:
            errors.append(f"rule pack missing contains-pack edge: {artifact_ref} -> {pack_ref}")
        owner_artifact = artifact_by_ref.get(artifact_ref or "")
        current_path = owner_artifact.get("current_path") if isinstance(owner_artifact, dict) else None
        for ref in pack.get("required_ruleset_refs") or []:
            if not isinstance(ref, str):
                errors.append(f"{pack_ref} required_ruleset_refs contains a non-string ref")
                continue
            if isinstance(current_path, str):
                resolved = resolve_ref_path(ref, current_path)
                target_ref = artifact_by_path.get(resolved)
                if target_ref and (pack_ref, target_ref, "required-ruleset") not in edge_tuples:
                    errors.append(f"missing pack required-ruleset edge: {pack_ref} -> {target_ref}")
                if not target_ref and (artifact_ref, ref, "required-ruleset") not in unresolved_tuples:
                    errors.append(f"missing unresolved pack required-ruleset entry: {pack_ref} -> {ref}")

    for chunk in chunk_candidates:
        chunk_id = string_value(chunk, "chunk_id")
        artifact_ref = string_value(chunk, "artifact_ref")
        corpus_id = string_value(chunk, "corpus_id")
        source_path = string_value(chunk, "source_path")
        if not chunk_id:
            errors.append("chunk candidate missing chunk_id")
            continue
        if not artifact_ref or artifact_ref not in artifact_ref_set:
            errors.append(f"chunk has unknown artifact_ref: {chunk_id}")
        if not corpus_id or corpus_id not in corpus_id_set:
            errors.append(f"chunk has unknown corpus_id: {chunk_id}")
        rule_ref = string_value(chunk, "rule_ref")
        pack_ref = string_value(chunk, "pack_ref")
        if rule_ref and rule_ref not in rule_ref_set:
            errors.append(f"chunk has unknown rule_ref: {chunk_id} -> {rule_ref}")
        if pack_ref and pack_ref not in pack_ref_set:
            errors.append(f"chunk has unknown pack_ref: {chunk_id} -> {pack_ref}")
        if source_path and path_should_exist(source_path) and not repo_path(source_path).is_file():
            errors.append(f"chunk source_path does not exist: {chunk_id} -> {source_path}")
        for source_ref_id in chunk.get("source_ref_ids") or []:
            if source_ref_id not in source_ref_id_set:
                errors.append(f"chunk source_ref_id does not resolve: {chunk_id} -> {source_ref_id}")

    for source_ref in source_references:
        source_ref_id = string_value(source_ref, "source_ref_id")
        corpus_id = string_value(source_ref, "corpus_id")
        artifact_ref = string_value(source_ref, "artifact_ref")
        source_path = string_value(source_ref, "source_path")
        if not source_ref_id:
            errors.append("source reference missing source_ref_id")
            continue
        if corpus_id and corpus_id not in corpus_id_set:
            errors.append(f"source reference has unknown corpus_id: {source_ref_id}")
        if artifact_ref and artifact_ref not in artifact_ref_set:
            errors.append(f"source reference has unknown artifact_ref: {source_ref_id}")
        if source_path and path_should_exist(source_path) and not repo_path(source_path).is_file():
            errors.append(f"source reference path does not exist: {source_ref_id} -> {source_path}")

    for mapping in path_mappings:
        current_path = string_value(mapping, "current_path")
        proposed_path = string_value(mapping, "proposed_path")
        proposed_corpus_id = string_value(mapping, "proposed_corpus_id")
        artifact_ref = string_value(mapping, "artifact_ref")
        if not current_path or not proposed_path or not proposed_corpus_id:
            errors.append(f"path mapping missing required path/corpus fields: {mapping}")
            continue
        if proposed_corpus_id not in corpus_id_set:
            errors.append(f"path mapping has unknown proposed_corpus_id: {current_path}")
        if artifact_ref and artifact_ref not in artifact_ref_set:
            errors.append(f"path mapping has unknown artifact_ref: {current_path} -> {artifact_ref}")
        if path_should_exist(current_path) and not repo_path(current_path).is_file():
            errors.append(f"path mapping current_path does not exist: {current_path}")

    for edge in graph_edges:
        edge_id = string_value(edge, "edge_id")
        from_ref = string_value(edge, "from_ref")
        to_ref = string_value(edge, "to_ref")
        edge_type = string_value(edge, "edge_type")
        if not edge_id or not from_ref or not to_ref or not edge_type:
            errors.append(f"graph edge missing required fields: {edge}")
            continue
        if from_ref not in all_refs:
            errors.append(f"graph edge from_ref does not resolve: {edge_id} -> {from_ref}")
        if edge_type in {"applies-to-path"}:
            if not to_ref:
                errors.append(f"graph edge applies-to-path missing path target: {edge_id}")
        elif edge_type in {"proposed-migration-target", "split-review-needed"}:
            if to_ref not in proposed_paths and to_ref not in current_paths:
                errors.append(f"graph edge migration target does not resolve to a path mapping: {edge_id} -> {to_ref}")
        elif to_ref not in all_refs:
            errors.append(f"graph edge to_ref does not resolve: {edge_id} -> {to_ref}")
        for source_ref_id in edge.get("source_ref_ids") or []:
            if source_ref_id not in source_ref_id_set:
                errors.append(f"graph edge source_ref_id does not resolve: {edge_id} -> {source_ref_id}")

    for unresolved in unresolved_references:
        owner_ref = string_value(unresolved, "owner_ref")
        severity = string_value(unresolved, "severity")
        if not owner_ref or owner_ref not in all_refs:
            errors.append(f"unresolved reference owner_ref does not resolve: {owner_ref}")
        if severity not in {"warning", "error", "blocking"}:
            errors.append(f"unresolved reference has invalid severity: {unresolved}")

    counts = diagnostics.get("counts") if isinstance(diagnostics.get("counts"), dict) else {}
    expected_counts = {
        "corpus_packages": len(corpus_packages),
        "artifacts": len(artifacts),
        "rules": len(rules),
        "rule_packs": len(rule_packs),
        "chunk_candidates": len(chunk_candidates),
        "graph_edges": len(graph_edges),
        "unresolved_references": len(unresolved_references),
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"diagnostics.counts.{key} expected {expected}, got {counts.get(key)}")

    diagnostic_errors = diagnostics.get("errors") if isinstance(diagnostics.get("errors"), list) else []
    if not isinstance(diagnostics.get("errors"), list):
        errors.append("diagnostics.errors must be an array")
    if not isinstance(diagnostics.get("warnings"), list):
        errors.append("diagnostics.warnings must be an array")

    blocking_unresolved = [
        item
        for item in unresolved_references
        if item.get("severity") == "blocking"
    ]
    expected_ok = not diagnostic_errors and not blocking_unresolved
    if diagnostics.get("ok") != expected_ok:
        errors.append(f"diagnostics.ok expected {expected_ok}, got {diagnostics.get('ok')}")

    if string_value(provenance, "generator") is None:
        errors.append("provenance.generator is required")
    if string_value(provenance, "generator_version") is None:
        errors.append("provenance.generator_version is required")
    if string_value(provenance, "git_commit") is None:
        errors.append("provenance.git_commit is required")
    provenance_inputs = provenance.get("inputs")
    if not isinstance(provenance_inputs, list):
        errors.append("provenance.inputs must be an array")
    else:
        for item in provenance_inputs:
            if not isinstance(item, dict):
                errors.append("provenance.inputs must contain only objects")
                continue
            path = string_value(item, "path")
            role = string_value(item, "role")
            if not path or not role:
                errors.append(f"provenance input missing path or role: {item}")
            elif role != "missing" and path_should_exist(path) and not repo_path(path).is_file():
                errors.append(f"provenance input path does not exist: {path}")

    report_ok = not errors
    return {
        "ok": report_ok,
        "schema": data.get("schema"),
        "index_id": data.get("index_id"),
        "counts": expected_counts,
        "errors": errors,
        "warnings": warnings,
    }


def print_human_report(report: dict[str, Any]) -> None:
    if report["ok"]:
        print("Rulebook index validation passed.")
    else:
        print("Rulebook index validation failed.")
    print(json.dumps(report["counts"], sort_keys=True))
    if report["warnings"]:
        print("WARNINGS")
        for warning in report["warnings"]:
            print(f"- {warning}")
    if report["errors"]:
        print("ERRORS")
        for error in report["errors"]:
            print(f"- {error}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        data = load_index(args)
        report = validate(data)
    except Exception as exc:
        report = {
            "ok": False,
            "schema": None,
            "index_id": None,
            "counts": {},
            "errors": [str(exc)],
            "warnings": [],
        }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

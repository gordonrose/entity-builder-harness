#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.compile-retrieval-policy
#   version: 2
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Compile governed retrieval policy, dimensions, recognition sources, corpus ownership, and graph metadata into a runtime JSON artifact.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#     - writes-files
#   used_by:
#     - id: rag-rulebook.schema.compiled-retrieval-policy
#       path: .agentic/02.rag-rulebook/schemas/compiled-retrieval-policy.schema.yml
#     - id: rag-rulebook.script.build-local-runtime
#       path: scripts/02.rag-rulebook/build-local-runtime/script.sh
#     - id: rag-rulebook.script.generate-retrieval-selector-fixture
#       path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for retrieval policy compilation.", file=sys.stderr)
    sys.exit(2)


SCHEMA = "rag-rulebook/compiled-retrieval-policy/v1"
POLICY_SCHEMA = "rag-rulebook/retrieval-policy-pack/v1"
DIMENSION_SCHEMA = "rag-rulebook/retrieval-policy-dimension/v1"
RECOGNITION_SCHEMA = "rag-rulebook/recognition-source/v1"
INDEX_SCHEMA = "rag-rulebook/rulebook-index/v1"
DEFAULT_POLICY = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml"
RECOGNITION_ROOT = ".agentic/02.rag-rulebook/recognition-sources"
POLICY_VALIDATOR = "scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
RECOGNITION_VALIDATOR = "scripts/02.rag-rulebook/validate-recognition-sources/script.sh"
INDEX_GENERATOR = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
COMPILER_ID = "rag-rulebook.compile-retrieval-policy"
COMPILER_VERSION = 1


def repo_root() -> Path:
    override = os.environ.get("RAG_REPO_ROOT")
    if override:
        return Path(override).resolve()
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
  compile-retrieval-policy/script.sh --current [--index <path>] [--output <path>] [--pretty]
  compile-retrieval-policy/script.sh --policy <path> [--index <path>] [--output <path>] [--pretty]

Compiles governed retrieval selector policy and recognition inputs into a
rag-rulebook/compiled-retrieval-policy/v1 JSON artifact. The command is
read-only unless --output is supplied.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--policy")
    parser.add_argument("--index")
    parser.add_argument("--output")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    modes = [args.current, args.policy is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one policy input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.current:
        args.policy = DEFAULT_POLICY
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(repo_path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain an object: {path}")
    return data


def load_json_text(raw: str, label: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def load_json_file(path: str | Path) -> dict[str, Any]:
    with repo_path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return data


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE)
    return load_json_text(result.stdout, "command output")


def run_text(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint_file(path: Path) -> dict[str, Any]:
    return {
        "algorithm": "sha256",
        "path": rel(path),
        "sha256": file_sha256(path),
    }


def content_hash(data: dict[str, Any]) -> str:
    payload = dict(data)
    payload["content_hash"] = None
    payload["compiled_policy_id"] = None
    payload["generated_at"] = None
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_policy(policy_path: str) -> dict[str, Any]:
    command = ["bash", POLICY_VALIDATOR, "--policy", policy_path, "--json"]
    report = run_json(command)
    if report.get("ok") is not True:
        raise ValueError("retrieval policy pack is invalid")
    return report


def validate_recognition_sources() -> dict[str, Any]:
    report = run_json(["bash", RECOGNITION_VALIDATOR, "--current", "--json"])
    if report.get("ok") is not True:
        raise ValueError("recognition sources are invalid")
    return report


def load_index(index_path: str | None) -> tuple[dict[str, Any], str | None]:
    if index_path:
        index = load_json_file(index_path)
        return index, rel(repo_path(index_path))
    raw = run_text(["bash", INDEX_GENERATOR])
    index = load_json_text(raw, "generated rulebook index")
    return index, None


def load_dimension(entry: dict[str, Any], policy_pack_id: str) -> dict[str, Any]:
    dimension_path = entry.get("path")
    if not isinstance(dimension_path, str):
        raise ValueError("dimension path must be a string")
    dimension = load_yaml(dimension_path)
    if dimension.get("schema") != DIMENSION_SCHEMA:
        raise ValueError(f"dimension has unsupported schema: {dimension_path}")
    if dimension.get("dimension_id") != entry.get("id"):
        raise ValueError(f"dimension ID mismatch for {dimension_path}")
    if dimension.get("applies_to_policy_pack") != policy_pack_id:
        raise ValueError(f"dimension does not apply to policy pack {policy_pack_id}: {dimension_path}")
    dimension["_path"] = dimension_path
    return dimension


def load_dimensions(policy: dict[str, Any]) -> list[dict[str, Any]]:
    policy_pack_id = str(policy.get("policy_pack_id") or "")
    dimensions = []
    for entry in policy.get("dimensions") or []:
        if not isinstance(entry, dict):
            continue
        dimensions.append(load_dimension(entry, policy_pack_id))
    if not dimensions:
        raise ValueError("policy pack has no dimensions")
    return dimensions


def dimension_by_id(dimensions: list[dict[str, Any]], dimension_id: str) -> dict[str, Any]:
    for dimension in dimensions:
        if dimension.get("dimension_id") == dimension_id:
            return dimension
    raise ValueError(f"missing required dimension: {dimension_id}")


def load_recognition_sources() -> list[dict[str, Any]]:
    root = repo_path(RECOGNITION_ROOT)
    sources: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        source = load_yaml(path)
        if source.get("schema") != RECOGNITION_SCHEMA:
            continue
        source["source_path"] = rel(path)
        sources.append(source)
    sources.sort(key=lambda item: (int(item.get("match_priority") or 9999), str(item.get("source_id"))))
    return sources


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def compile_intent_resolution(prompt_dimension: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    intent_resolution = dict_value(prompt_dimension.get("intent_resolution"))
    default_intent_id = str(intent_resolution.get("default_intent_id") or "").strip()
    precedence = list_of_strings(intent_resolution.get("precedence"))
    labels = dict_value(intent_resolution.get("labels"))
    if not default_intent_id:
        raise ValueError("prompt dimension intent_resolution.default_intent_id is required")
    if not precedence:
        raise ValueError("prompt dimension intent_resolution.precedence is required")
    known_intents = {default_intent_id}
    for source in sources:
        for term in list_of_dicts(source.get("terms")):
            if term.get("category") == "intent-form" and isinstance(term.get("canonical_id"), str):
                known_intents.add(str(term["canonical_id"]))
    unknown = [intent_id for intent_id in precedence if intent_id not in known_intents]
    if unknown:
        raise ValueError("intent precedence references unknown intent ids: " + ", ".join(unknown))
    return {
        "default_intent_id": default_intent_id,
        "precedence": precedence,
        "labels": {str(key): str(value) for key, value in labels.items()},
        "known_intent_ids": sorted(known_intents),
    }


def compile_evidence_bundles(evidence_dimension: dict[str, Any], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bundles = []
    known_question_categories = set()
    known_evidence_families = set()
    for source in sources:
        for term in list_of_dicts(source.get("terms")):
            canonical_id = term.get("canonical_id")
            if not isinstance(canonical_id, str):
                continue
            if term.get("category") == "question-category":
                known_question_categories.add(canonical_id)
            elif term.get("category") == "evidence-family":
                known_evidence_families.add(canonical_id)
    for raw_bundle in list_of_dicts(evidence_dimension.get("evidence_bundles")):
        question_category_id = str(raw_bundle.get("question_category_id") or "").strip()
        if not question_category_id:
            raise ValueError("evidence bundle missing question_category_id")
        if question_category_id not in known_question_categories:
            raise ValueError(f"evidence bundle references unknown question category: {question_category_id}")
        always_source_paths = list_of_strings(raw_bundle.get("always_source_paths"))
        family_source_paths = dict_value(raw_bundle.get("family_source_paths"))
        for source_path in always_source_paths:
            if not repo_path(source_path).is_file():
                raise ValueError(f"evidence bundle source path does not exist: {source_path}")
        compiled_family_paths: dict[str, str] = {}
        for family_id, source_path in sorted(family_source_paths.items()):
            if family_id not in known_evidence_families:
                raise ValueError(f"evidence bundle references unknown evidence family: {family_id}")
            if not isinstance(source_path, str) or not repo_path(source_path).is_file():
                raise ValueError(f"evidence family source path does not exist: {source_path}")
            compiled_family_paths[str(family_id)] = source_path
        bundles.append(
            {
                "question_category_id": question_category_id,
                "always_source_paths": always_source_paths,
                "family_source_paths": compiled_family_paths,
            }
        )
    return bundles


def compile_retrieval_strategy(strategy_dimension: dict[str, Any]) -> dict[str, Any]:
    strategy = dict_value(strategy_dimension.get("retrieval_strategy"))
    strategy_id = str(strategy.get("strategy_id") or "").strip()
    if not strategy_id:
        raise ValueError("retrieval-strategy dimension retrieval_strategy.strategy_id is required")
    stages = []
    seen_stage_ids: set[str] = set()
    for raw_stage in sorted(list_of_dicts(strategy.get("stages")), key=lambda item: int(item.get("rank") or 9999)):
        stage_id = str(raw_stage.get("stage_id") or "").strip()
        rank = raw_stage.get("rank")
        purpose = str(raw_stage.get("purpose") or "").strip()
        if not stage_id:
            raise ValueError("retrieval-strategy stage_id is required")
        if stage_id in seen_stage_ids:
            raise ValueError(f"duplicate retrieval-strategy stage_id: {stage_id}")
        if not isinstance(rank, int) or isinstance(rank, bool):
            raise ValueError(f"retrieval-strategy stage rank must be an integer: {stage_id}")
        if not purpose:
            raise ValueError(f"retrieval-strategy stage purpose is required: {stage_id}")
        stages.append(
            {
                "stage_id": stage_id,
                "rank": rank,
                "purpose": purpose,
                "primary_inputs": list_of_strings(raw_stage.get("primary_inputs")),
                "expected_outputs": list_of_strings(raw_stage.get("expected_outputs")),
            }
        )
        seen_stage_ids.add(stage_id)
    if not stages:
        raise ValueError("retrieval-strategy stages are required")
    expected_ranks = list(range(1, len(stages) + 1))
    actual_ranks = sorted(stage["rank"] for stage in stages)
    if actual_ranks != expected_ranks:
        raise ValueError("retrieval-strategy stage ranks must be contiguous starting at 1")
    return {
        "strategy_id": strategy_id,
        "stages": stages,
    }


def compile_chunk_selection(strategy_dimension: dict[str, Any]) -> dict[str, Any]:
    chunk_selection = dict_value(strategy_dimension.get("chunk_selection"))
    purpose_priority_by_intent = dict_value(chunk_selection.get("purpose_priority_by_intent"))
    authority_rules = dict_value(chunk_selection.get("authority_rules"))
    side_effect_restrictions = dict_value(chunk_selection.get("side_effect_restrictions"))
    if not purpose_priority_by_intent:
        raise ValueError("retrieval-strategy dimension chunk_selection.purpose_priority_by_intent is required")
    if not authority_rules:
        raise ValueError("retrieval-strategy dimension chunk_selection.authority_rules is required")
    if not side_effect_restrictions:
        raise ValueError("retrieval-strategy dimension chunk_selection.side_effect_restrictions is required")
    return {
        "purpose_priority_by_intent": {
            str(intent_id): list_of_strings(priority)
            for intent_id, priority in sorted(purpose_priority_by_intent.items())
        },
        "authority_rules": {
            str(authority): str(rule)
            for authority, rule in sorted(authority_rules.items())
        },
        "side_effect_restrictions": {
            "side_effect_classes": list_of_strings(side_effect_restrictions.get("side_effect_classes")),
            "authorization_authorities": list_of_strings(side_effect_restrictions.get("authorization_authorities")),
            "background_only_authorities": list_of_strings(side_effect_restrictions.get("background_only_authorities")),
        },
    }


def edge_type_counts(edges: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for edge in edges:
        edge_type = str(edge.get("edge_type") or "unknown")
        counts[edge_type] = counts.get(edge_type, 0) + 1
    return dict(sorted(counts.items()))


def compact_dimension(dimension: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": dimension.get("dimension_id"),
        "version": dimension.get("version"),
        "status": dimension.get("status"),
        "path": dimension.get("_path"),
        "source_hash": fingerprint_file(repo_path(str(dimension.get("_path"))))["sha256"],
    }


def build_compiled_policy(args: argparse.Namespace) -> dict[str, Any]:
    policy_report = validate_policy(args.policy)
    recognition_report = validate_recognition_sources()
    policy = load_yaml(args.policy)
    if policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("retrieval policy pack has unsupported schema")
    dimensions = load_dimensions(policy)
    sources = load_recognition_sources()
    index, index_path = load_index(args.index)
    if index.get("schema") != INDEX_SCHEMA:
        raise ValueError("rulebook index has unsupported schema")
    prompt_dimension = dimension_by_id(dimensions, "prompt")
    evidence_dimension = dimension_by_id(dimensions, "evidence-bundles")
    strategy_dimension = dimension_by_id(dimensions, "retrieval-strategy")
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    graph_edges = list_of_dicts(index.get("graph_edges"))
    compiled = {
        "schema": SCHEMA,
        "compiled_policy_id": "pending",
        "generated_at": generated_at,
        "compiler": {
            "id": COMPILER_ID,
            "version": COMPILER_VERSION,
            "path": "scripts/02.rag-rulebook/compile-retrieval-policy/script.sh",
        },
        "policy_pack": {
            "policy_pack_id": policy.get("policy_pack_id"),
            "version": policy.get("version"),
            "status": policy.get("status"),
            "path": args.policy,
            "validator_counts": policy_report.get("counts"),
        },
        "dimensions": [compact_dimension(dimension) for dimension in dimensions],
        "precedence": policy.get("precedence") or [],
        "thresholds": policy.get("thresholds") or {},
        "intent_resolution": compile_intent_resolution(prompt_dimension, sources),
        "evidence_bundles": compile_evidence_bundles(evidence_dimension, sources),
        "retrieval_strategy": compile_retrieval_strategy(strategy_dimension),
        "chunk_selection": compile_chunk_selection(strategy_dimension),
        "recognition_sources": {
            "counts": recognition_report.get("counts"),
            "sources": sources,
        },
        "corpus_ownership": {
            "corpus_packages": index.get("corpus_packages") or [],
            "path_mappings": index.get("path_mappings") or [],
        },
        "rule_graph": {
            "edge_count": len(graph_edges),
            "edge_type_counts": edge_type_counts(graph_edges),
        },
        "feature_flags": {
            "semantic_recall_enabled": bool((policy.get("thresholds") or {}).get("semantic_recall_enabled") is True),
        },
        "input_fingerprints": {
            "policy_pack": fingerprint_file(repo_path(args.policy)),
            "dimensions": [fingerprint_file(repo_path(str(dimension.get("_path")))) for dimension in dimensions],
            "recognition_sources": [fingerprint_file(repo_path(str(source.get("source_path")))) for source in sources],
            "index": fingerprint_file(repo_path(index_path)) if index_path else {"generated_from_current": True},
            "compiler": fingerprint_file(repo_path("scripts/02.rag-rulebook/compile-retrieval-policy/script.sh")),
        },
        "content_hash": None,
        "provenance": {
            "policy_report": policy_report,
            "recognition_report": recognition_report,
            "index_path": index_path,
            "schema_path": ".agentic/02.rag-rulebook/schemas/compiled-retrieval-policy.schema.yml",
        },
    }
    digest = content_hash(compiled)
    compiled["content_hash"] = digest
    compiled["compiled_policy_id"] = f"compiled.retrieval-policy.{policy.get('policy_pack_id')}.{digest[:16]}"
    return compiled


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        compiled = build_compiled_policy(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    indent = 2 if args.pretty else None
    raw = json.dumps(compiled, indent=indent, sort_keys=True) + "\n"
    if args.output:
        repo_path(args.output).parent.mkdir(parents=True, exist_ok=True)
        repo_path(args.output).write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

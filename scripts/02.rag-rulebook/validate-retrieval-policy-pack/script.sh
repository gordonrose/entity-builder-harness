#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-retrieval-policy-pack
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate a rag-rulebook/retrieval-policy-pack/v1 YAML policy pack without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.retrieval-policy-pack
#       path: .agentic/02.rag-rulebook/schemas/retrieval-policy-pack.schema.yml
#     - id: rag-rulebook.schema.retrieval-policy-dimension
#       path: .agentic/02.rag-rulebook/schemas/retrieval-policy-dimension.schema.yml
#     - id: rag-rulebook.policy.retrieval-selector.v1
#       path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.script.validate-retrieval-policy-pack.readme
#       path: scripts/02.rag-rulebook/validate-retrieval-policy-pack/README.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for retrieval policy-pack validation.", file=sys.stderr)
    sys.exit(2)


POLICY_SCHEMA = "rag-rulebook/retrieval-policy-pack/v1"
DIMENSION_SCHEMA = "rag-rulebook/retrieval-policy-dimension/v1"
CONTEXT_PACKET_SCHEMA = "rag-rulebook/context-packet/v1"
CHUNK_SET_SCHEMA = "rag-rulebook/chunk-set/v1"
INDEX_SCHEMA = "rag-rulebook/rulebook-index/v1"
DEFAULT_POLICY = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml"
DEFAULT_SCHEMA = ".agentic/02.rag-rulebook/schemas/retrieval-policy-pack.schema.yml"
DEFAULT_DIMENSION_SCHEMA = ".agentic/02.rag-rulebook/schemas/retrieval-policy-dimension.schema.yml"
REQUIRED_TOP_LEVEL = [
    "schema",
    "policy_pack_id",
    "version",
    "status",
    "applies_to",
    "change_reason",
    "dimensions",
    "precedence",
    "thresholds",
    "validation",
    "evolution",
]
ALLOWED_STATUS = {"draft", "active", "superseded", "retired"}
REQUIRED_DIMENSIONS = [
    "prompt",
    "request-context",
    "evidence-bundles",
    "session-metadata",
    "layer-mode-workflow",
    "focused-paths",
    "corpus-ownership",
    "rule-graph",
    "required-checks",
    "stop-conditions",
    "token-budget",
    "confidence-thresholds",
    "validation-handoff",
    "semantic-recall",
]
REQUIRED_DIMENSION_FIELDS = [
    "schema",
    "dimension_id",
    "version",
    "status",
    "applies_to_policy_pack",
    "purpose",
    "required_inputs",
    "expected_actions",
    "banned_actions",
    "output_obligations",
    "gap_or_stop_conditions",
    "ranking_effects",
    "validation_examples",
    "can_change_by",
]
PRECEDENCE_CONCEPTS = [
    "stop",
    "request",
    "evidence",
    "session",
    "path",
    "corpus",
    "required",
    "graph",
    "deterministic",
    "confidence",
    "validation",
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
  validate-retrieval-policy-pack/script.sh --current [--json]
  validate-retrieval-policy-pack/script.sh --policy <path> [--schema <path>] [--dimension-schema <path>] [--json]

Validates a rag-rulebook/retrieval-policy-pack/v1 YAML policy pack. The command
is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--policy")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--dimension-schema", default=DEFAULT_DIMENSION_SCHEMA)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    modes = [args.current, args.policy is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.current:
        args.policy = DEFAULT_POLICY
    return args


def repo_path(path: str) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def resolve_import_path(path: str, policy_path: str) -> Path:
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    if path_should_exist(path):
        return ROOT / path_obj
    policy_file = repo_path(policy_path)
    return policy_file.parent / path_obj


def load_yaml(path: str) -> dict[str, Any]:
    data = yaml.safe_load(repo_path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain an object: {path}")
    return data


def load_yaml_path(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain an object: {path}")
    return data


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def require_fields(owner: str, data: dict[str, Any], fields: list[str], errors: list[str]) -> None:
    for field in fields:
        if field not in data:
            errors.append(f"{owner} missing required field: {field}")


def report_duplicate(label: str, values: list[str], errors: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    for value in sorted(duplicates):
        errors.append(f"duplicate {label}: {value}")


def validate_probability(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{field} must be a number")
        return
    if value < 0 or value > 1:
        errors.append(f"{field} must be between 0 and 1")


def validate_positive_int(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        errors.append(f"{field} must be a positive integer")


def path_should_exist(path: str) -> bool:
    return path.startswith((".agentic/", "scripts/", "docs/", "AGENTS.md"))


def validate_schema_file(schema: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    if schema.get("policy_pack_schema") != POLICY_SCHEMA:
        errors.append(f"schema policy_pack_schema must be {POLICY_SCHEMA}")
    if schema.get("policy_dimension_schema") != DIMENSION_SCHEMA:
        errors.append(f"schema policy_dimension_schema must be {DIMENSION_SCHEMA}")
    required_fields = list_of_strings(schema.get("required_fields"))
    for field in REQUIRED_TOP_LEVEL:
        if field not in required_fields:
            errors.append(f"schema required_fields missing: {field}")
    schema_fields = schema.get("fields")
    if not isinstance(schema_fields, dict):
        errors.append("schema fields must be an object")
        return
    dimensions = schema_fields.get("dimensions")
    allowed_dimensions: list[str] = []
    if isinstance(dimensions, dict):
        item = dimensions.get("item")
        if isinstance(item, dict):
            fields = item.get("fields")
            if isinstance(fields, dict):
                id_field = fields.get("id")
                if isinstance(id_field, dict):
                    allowed_dimensions = list_of_strings(id_field.get("allowed_values"))
    for dimension_id in REQUIRED_DIMENSIONS:
        if dimension_id not in allowed_dimensions:
            errors.append(f"schema dimensions allowed_values missing: {dimension_id}")
    if isinstance(dimensions, dict):
        item = dimensions.get("item")
        if isinstance(item, dict):
            required = list_of_strings(item.get("required_fields"))
            for field in ["id", "path"]:
                if field not in required:
                    errors.append(f"schema dimensions item required_fields missing: {field}")
    if "field_guide" not in schema:
        warnings.append("schema has no field_guide entries")


def validate_dimension_schema_file(schema: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    if schema.get("policy_dimension_schema") != DIMENSION_SCHEMA:
        errors.append(f"dimension schema policy_dimension_schema must be {DIMENSION_SCHEMA}")
    required_fields = list_of_strings(schema.get("required_fields"))
    for field in REQUIRED_DIMENSION_FIELDS:
        if field not in required_fields:
            errors.append(f"dimension schema required_fields missing: {field}")
    schema_fields = schema.get("fields")
    if not isinstance(schema_fields, dict):
        errors.append("dimension schema fields must be an object")
        return
    dimension_id_field = schema_fields.get("dimension_id")
    allowed_dimensions: list[str] = []
    if isinstance(dimension_id_field, dict):
        allowed_dimensions = list_of_strings(dimension_id_field.get("allowed_values"))
    for dimension_id in REQUIRED_DIMENSIONS:
        if dimension_id not in allowed_dimensions:
            errors.append(f"dimension schema dimension_id allowed_values missing: {dimension_id}")
    if "field_guide" not in schema:
        warnings.append("dimension schema has no field_guide entries")


def validate_applies_to(applies_to: dict[str, Any], errors: list[str]) -> None:
    require_fields(
        "applies_to",
        applies_to,
        ["selector_version", "context_packet_schema", "chunk_set_schema", "corpus_ids"],
        errors,
    )
    if applies_to.get("context_packet_schema") != CONTEXT_PACKET_SCHEMA:
        errors.append(f"applies_to.context_packet_schema must be {CONTEXT_PACKET_SCHEMA}")
    if applies_to.get("chunk_set_schema") != CHUNK_SET_SCHEMA:
        errors.append(f"applies_to.chunk_set_schema must be {CHUNK_SET_SCHEMA}")
    if applies_to.get("index_schema") not in (None, INDEX_SCHEMA):
        errors.append(f"applies_to.index_schema must be {INDEX_SCHEMA}")
    corpus_ids = list_of_strings(applies_to.get("corpus_ids"))
    if not corpus_ids:
        errors.append("applies_to.corpus_ids must be a non-empty array of strings")
    report_duplicate("applies_to.corpus_ids", corpus_ids, errors)
    for corpus_id in corpus_ids:
        if not corpus_id.startswith("corpus."):
            errors.append(f"corpus_id must start with corpus.: {corpus_id}")
    for layer_mode in list_of_strings(applies_to.get("layer_modes")):
        if ":" not in layer_mode:
            errors.append(f"layer_modes entry must include layer:mode: {layer_mode}")
    for workflow in list_of_strings(applies_to.get("workflows")):
        if path_should_exist(workflow) and not repo_path(workflow).is_file():
            errors.append(f"applies_to workflow path does not exist: {workflow}")


def validate_dimension_contract(
    manifest_id: str,
    dimension_path: Path,
    dimension: dict[str, Any],
    policy_pack_id: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    owner = f"dimension[{manifest_id}]"
    require_fields(owner, dimension, REQUIRED_DIMENSION_FIELDS, errors)
    if dimension.get("schema") != DIMENSION_SCHEMA:
        errors.append(f"{owner} schema must be {DIMENSION_SCHEMA}: {dimension_path}")
    if dimension.get("dimension_id") != manifest_id:
        errors.append(f"{owner} dimension_id must match manifest id: {dimension_path}")
    validate_positive_int(dimension.get("version"), f"{owner}.version", errors)
    if dimension.get("status") not in ALLOWED_STATUS:
        errors.append(f"{owner} status is invalid: {dimension.get('status')}")
    if dimension.get("applies_to_policy_pack") != policy_pack_id:
        errors.append(f"{owner} applies_to_policy_pack must be {policy_pack_id}: {dimension_path}")
    if not isinstance(dimension.get("purpose"), str) or not dimension.get("purpose"):
        errors.append(f"{owner} purpose must be a non-empty string")
    for field in [
        "required_inputs",
        "expected_actions",
        "banned_actions",
        "output_obligations",
        "gap_or_stop_conditions",
        "ranking_effects",
        "can_change_by",
    ]:
        if not list_of_strings(dimension.get(field)):
            errors.append(f"{owner} {field} must be a non-empty string array")
    examples = list_of_dicts(dimension.get("validation_examples"))
    if not examples:
        errors.append(f"{owner} validation_examples must be a non-empty object array")
    for index, example in enumerate(examples, start=1):
        require_fields(f"{owner}.validation_examples[{index}]", example, ["name", "given", "expect"], errors)
        for field in ["name", "given", "expect"]:
            if not isinstance(example.get(field), str) or not example.get(field):
                errors.append(f"{owner}.validation_examples[{index}].{field} must be a non-empty string")
    if manifest_id == "prompt":
        recognition_sources = list_of_dicts(dimension.get("recognition_sources"))
        if not recognition_sources:
            errors.append("dimension prompt must include non-empty recognition_sources")
        generation_modes = {
            source.get("generation_mode")
            for source in recognition_sources
            if isinstance(source.get("generation_mode"), str)
        }
        if "generated" not in generation_modes:
            errors.append("dimension prompt recognition_sources must include a generated source")
        if "curated" not in generation_modes:
            errors.append("dimension prompt recognition_sources must include a curated source")
        for index, source in enumerate(recognition_sources, start=1):
            require_fields(
                f"{owner}.recognition_sources[{index}]",
                source,
                ["source_id", "source_kinds", "generation_mode", "expected_origin", "purpose"],
                errors,
            )
            if not list_of_strings(source.get("source_kinds")):
                errors.append(f"{owner}.recognition_sources[{index}].source_kinds must be a non-empty string array")
        for field in ["extraction_rules", "classification_outputs"]:
            if not list_of_strings(dimension.get(field)):
                errors.append(f"dimension prompt must include non-empty {field}")
        term_categories = dimension.get("term_categories")
        if not isinstance(term_categories, dict) or not term_categories:
            errors.append("dimension prompt must include non-empty term_categories")
        else:
            for category in ["artifact_terms", "routing_terms", "action_terms", "risk_terms", "broad_terms"]:
                if category not in term_categories:
                    errors.append(f"dimension prompt term_categories missing: {category}")
    if manifest_id == "semantic-recall":
        combined = "\n".join(list_of_strings(dimension.get("expected_actions")) + list_of_strings(dimension.get("banned_actions"))).lower()
        if "disabled" not in combined or "do not enable" not in combined:
            errors.append("dimension semantic-recall must explicitly keep semantic recall disabled in v1")
    if len(list_of_strings(dimension.get("banned_actions"))) < 2:
        warnings.append(f"{owner} should include more than one banned action")


def validate_dimensions(
    dimensions: list[dict[str, Any]],
    policy_path: str,
    policy_pack_id: str,
    errors: list[str],
    warnings: list[str],
) -> list[dict[str, Any]]:
    loaded_dimensions: list[dict[str, Any]] = []
    dimension_ids = [item.get("id") for item in dimensions if isinstance(item.get("id"), str)]
    report_duplicate("dimensions[].id", dimension_ids, errors)
    dimension_id_set = set(dimension_ids)
    for dimension_id in REQUIRED_DIMENSIONS:
        if dimension_id not in dimension_id_set:
            errors.append(f"missing required dimension: {dimension_id}")
    for dimension in dimensions:
        dimension_id = dimension.get("id")
        require_fields(f"dimension[{dimension_id or '?'}]", dimension, ["id", "path"], errors)
        if dimension_id not in REQUIRED_DIMENSIONS:
            warnings.append(f"unknown dimension id; ensure schema allows it before selector use: {dimension_id}")
        for inline_field in ["purpose", "instructions", "validation_requirements", "deterministic_rules"]:
            if inline_field in dimension:
                errors.append(f"dimension manifest entry must not inline {inline_field}: {dimension_id}")
        dimension_path_value = dimension.get("path")
        if not isinstance(dimension_path_value, str) or not dimension_path_value:
            errors.append(f"dimension path must be a non-empty string: {dimension_id}")
            continue
        dimension_path = resolve_import_path(dimension_path_value, policy_path)
        if not dimension_path.is_file():
            errors.append(f"dimension path does not exist: {dimension_path_value}")
            continue
        try:
            loaded_dimension = load_yaml_path(dimension_path)
        except Exception as exc:
            errors.append(f"failed to load dimension {dimension_id}: {exc}")
            continue
        validate_dimension_contract(
            str(dimension_id),
            dimension_path,
            loaded_dimension,
            policy_pack_id,
            errors,
            warnings,
        )
        loaded_dimensions.append(loaded_dimension)
    return loaded_dimensions


def validate_precedence(precedence: list[dict[str, Any]], errors: list[str]) -> None:
    ranks: list[int] = []
    texts: list[str] = []
    for item in precedence:
        require_fields("precedence[]", item, ["rank", "rule", "reason"], errors)
        rank = item.get("rank")
        if isinstance(rank, int) and not isinstance(rank, bool):
            ranks.append(rank)
        else:
            errors.append(f"precedence rank must be an integer: {rank}")
        rule = item.get("rule")
        reason = item.get("reason")
        if not isinstance(rule, str) or not rule:
            errors.append(f"precedence rule must be a non-empty string: rank {rank}")
        else:
            texts.append(rule.lower())
        if not isinstance(reason, str) or not reason:
            errors.append(f"precedence reason must be a non-empty string: rank {rank}")
    if ranks:
        expected = list(range(1, len(ranks) + 1))
        if sorted(ranks) != expected:
            errors.append(f"precedence ranks must be contiguous starting at 1: expected {expected}, got {sorted(ranks)}")
    report_duplicate("precedence[].rank", [str(rank) for rank in ranks], errors)
    joined = "\n".join(texts)
    for concept in PRECEDENCE_CONCEPTS:
        if concept not in joined:
            errors.append(f"precedence rules must cover concept: {concept}")
    if texts and "stop" not in texts[0]:
        errors.append("first precedence rule must be about stop conditions")


def validate_thresholds(thresholds: dict[str, Any], errors: list[str]) -> None:
    require_fields(
        "thresholds",
        thresholds,
        [
            "max_context_tokens",
            "max_selected_chunks",
            "min_intent_confidence",
            "min_routing_confidence",
            "min_retrieval_confidence",
            "semantic_recall_enabled",
        ],
        errors,
    )
    validate_positive_int(thresholds.get("max_context_tokens"), "thresholds.max_context_tokens", errors)
    validate_positive_int(thresholds.get("max_selected_chunks"), "thresholds.max_selected_chunks", errors)
    for field in ["min_intent_confidence", "min_routing_confidence", "min_retrieval_confidence"]:
        validate_probability(thresholds.get(field), f"thresholds.{field}", errors)
    if thresholds.get("semantic_recall_enabled") is not False:
        errors.append("thresholds.semantic_recall_enabled must be false for v1")


def validate_validation_section(validation: dict[str, Any], errors: list[str]) -> None:
    require_fields("validation", validation, ["required_checks", "smoke_fixtures"], errors)
    if not list_of_strings(validation.get("required_checks")):
        errors.append("validation.required_checks must be a non-empty string array")
    smoke_fixtures = list_of_strings(validation.get("smoke_fixtures"))
    if not smoke_fixtures:
        errors.append("validation.smoke_fixtures must be a non-empty string array")
    for path in smoke_fixtures:
        if path_should_exist(path) and not repo_path(path).is_file():
            errors.append(f"smoke fixture path does not exist: {path}")
    validator_scripts = list_of_strings(validation.get("validator_scripts"))
    if not validator_scripts:
        errors.append("validation.validator_scripts must be a non-empty string array")
    for path in validator_scripts:
        if path_should_exist(path) and not repo_path(path).is_file():
            errors.append(f"validator script path does not exist: {path}")


def validate_evolution(evolution: dict[str, Any], errors: list[str]) -> None:
    require_fields("evolution", evolution, ["compatible_change_types", "review_required_when"], errors)
    if not list_of_strings(evolution.get("compatible_change_types")):
        errors.append("evolution.compatible_change_types must be a non-empty string array")
    review_required_when = list_of_strings(evolution.get("review_required_when"))
    if not review_required_when:
        errors.append("evolution.review_required_when must be a non-empty string array")
    review_text = "\n".join(review_required_when).lower()
    for phrase in ["confidence", "context", "semantic", "precedence"]:
        if phrase not in review_text:
            errors.append(f"evolution.review_required_when must cover: {phrase}")
    if not isinstance(evolution.get("breaking_change_policy"), str) or not evolution.get("breaking_change_policy"):
        errors.append("evolution.breaking_change_policy must be a non-empty string")


def validate(
    policy: dict[str, Any],
    schema: dict[str, Any],
    dimension_schema: dict[str, Any],
    policy_path: str,
    schema_path: str,
    dimension_schema_path: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    validate_schema_file(schema, errors, warnings)
    validate_dimension_schema_file(dimension_schema, errors, warnings)

    for field in REQUIRED_TOP_LEVEL:
        if field not in policy:
            errors.append(f"missing top-level field: {field}")
    if policy.get("schema") != POLICY_SCHEMA:
        errors.append(f"schema must be {POLICY_SCHEMA}")
    if not isinstance(policy.get("policy_pack_id"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", policy.get("policy_pack_id", "")):
        errors.append("policy_pack_id must be a stable lowercase dot/dash ID")
    validate_positive_int(policy.get("version"), "version", errors)
    if policy.get("status") not in ALLOWED_STATUS:
        errors.append(f"status is invalid: {policy.get('status')}")
    if policy.get("status") == "superseded" and not isinstance(policy.get("supersedes"), str):
        warnings.append("superseded policy should identify supersedes")
    if not isinstance(policy.get("change_reason"), str) or not policy.get("change_reason"):
        errors.append("change_reason must be a non-empty string")

    applies_to = policy.get("applies_to")
    if not isinstance(applies_to, dict):
        errors.append("applies_to must be an object")
        applies_to = {}
    validate_applies_to(applies_to, errors)

    dimensions = list_of_dicts(policy.get("dimensions"))
    if not dimensions:
        errors.append("dimensions must be a non-empty array of objects")
    loaded_dimensions = validate_dimensions(
        dimensions,
        policy_path,
        str(policy.get("policy_pack_id") or ""),
        errors,
        warnings,
    )

    precedence = list_of_dicts(policy.get("precedence"))
    if not precedence:
        errors.append("precedence must be a non-empty array of objects")
    validate_precedence(precedence, errors)

    thresholds = policy.get("thresholds")
    if not isinstance(thresholds, dict):
        errors.append("thresholds must be an object")
        thresholds = {}
    validate_thresholds(thresholds, errors)

    validation_section = policy.get("validation")
    if not isinstance(validation_section, dict):
        errors.append("validation must be an object")
        validation_section = {}
    validate_validation_section(validation_section, errors)

    evolution = policy.get("evolution")
    if not isinstance(evolution, dict):
        errors.append("evolution must be an object")
        evolution = {}
    validate_evolution(evolution, errors)

    return {
        "ok": not errors,
        "schema": policy.get("schema"),
        "policy_pack_id": policy.get("policy_pack_id"),
        "policy_path": str(repo_path(policy_path)),
        "schema_path": str(repo_path(schema_path)),
        "dimension_schema_path": str(repo_path(dimension_schema_path)),
        "counts": {
            "dimensions": len(dimensions),
            "dimension_files": len(loaded_dimensions),
            "precedence": len(precedence),
            "smoke_fixtures": len(list_of_strings(validation_section.get("smoke_fixtures"))),
            "validator_scripts": len(list_of_strings(validation_section.get("validator_scripts"))),
        },
        "errors": errors,
        "warnings": warnings,
    }


def print_human_report(report: dict[str, Any]) -> None:
    if report["ok"]:
        print("Retrieval policy-pack validation passed.")
    else:
        print("Retrieval policy-pack validation failed.")
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
        policy = load_yaml(args.policy)
        schema = load_yaml(args.schema)
        dimension_schema = load_yaml(args.dimension_schema)
        report = validate(policy, schema, dimension_schema, args.policy, args.schema, args.dimension_schema)
    except Exception as exc:
        report = {
            "ok": False,
            "schema": None,
            "policy_pack_id": None,
            "policy_path": args.policy,
            "schema_path": args.schema,
            "dimension_schema_path": args.dimension_schema,
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

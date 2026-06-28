#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-context-packet
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: context-packets
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate a rag-rulebook/context-packet/v1 JSON packet against a generated chunk set.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.context-packet
#       path: .agentic/02.rag-rulebook/schemas/context-packet.schema.yml
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.script.generate-rulebook-chunks
#       path: scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh
#     - id: rag-rulebook.script.validate-context-packet.readme
#       path: scripts/02.rag-rulebook/validate-context-packet/README.md

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


PACKET_SCHEMA = "rag-rulebook/context-packet/v1"
CHUNK_SET_SCHEMA = "rag-rulebook/chunk-set/v1"
REQUIRED_TOP_LEVEL = [
    "schema",
    "packet_id",
    "generated_at",
    "request",
    "intent",
    "routing",
    "matched_corpora",
    "matched_rule_packs",
    "matched_rulesets",
    "selected_chunks",
    "required_checks",
    "forbidden_actions",
    "stop_conditions",
    "citations",
    "confidence",
    "gaps",
    "budgets",
    "provenance",
]
ALLOWED_INTENT_SOURCES = {"deterministic", "inferred", "user-supplied", "mixed"}
ALLOWED_ROUTING_STATUSES = {"ready", "needs-clarification", "blocked"}
ALLOWED_SELECTOR_TRACE_STAGE_STATUSES = {"applied", "skipped", "unknown"}
ALLOWED_RULESET_TYPES = {"layer", "concern", "standard", "workflow"}
ALLOWED_CHECK_TIMING = {"before-edit", "before-commit", "before-deploy", "after-change"}
ALLOWED_STOP_SEVERITY = {"warning", "blocking"}
ALLOWED_CITATION_SOURCE_TYPES = {"source", "rule", "rule-pack", "workflow", "standard", "schema", "plan"}
ALLOWED_GAP_TYPES = {
    "missing-corpus",
    "ambiguous-intent",
    "ambiguous-ownership",
    "missing-reference",
    "budget-overflow",
    "missing-validator",
    "unsupported-action",
}
ALLOWED_TRIM_POLICIES = {"deterministic-first", "cite-required-context-only", "fail-when-over-budget"}
ALLOWED_ACTION_SIDE_EFFECT_CLASSES = {"none", "write", "git", "deploy", "destructive"}
ALLOWED_ACTION_AUTHORIZATION_STATUSES = {
    "allowed",
    "blocked",
    "not-executable-intent",
    "not-requested",
    "requires-deploy-workflow-approval",
}


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
  validate-context-packet/script.sh --packet <path> --chunks <path> [--json]

Validates a rag-rulebook/context-packet/v1 JSON packet against a
rag-rulebook/chunk-set/v1 JSON file. The command is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--packet")
    parser.add_argument("--chunks")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if not args.packet or not args.chunks:
        print("ERROR: --packet and --chunks are required.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def load_json(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
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


def number_value(item: dict[str, Any], field: str) -> int | float | None:
    value = item.get(field)
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (int, float)) else None


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def report_duplicate(label: str, values: list[str], errors: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    for value in sorted(duplicates):
        errors.append(f"duplicate {label}: {value}")


def validate_iso8601(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be a string")
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be ISO-8601")


def validate_probability(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{field} must be a number")
        return
    if value < 0 or value > 1:
        errors.append(f"{field} must be between 0 and 1")


def path_should_exist(path: str) -> bool:
    if not path or "*" in path or path.startswith("corpus."):
        return False
    return path.startswith(("docs/", ".agentic/", "scripts/", "AGENTS.md"))


def require_fields(owner: str, item: dict[str, Any], fields: list[str], errors: list[str]) -> None:
    for field in fields:
        if field not in item:
            errors.append(f"{owner} missing required field: {field}")


def validate(packet: dict[str, Any], chunk_set: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in packet:
            errors.append(f"missing top-level field: {field}")

    if packet.get("schema") != PACKET_SCHEMA:
        errors.append(f"schema must be {PACKET_SCHEMA}")
    if chunk_set.get("schema") != CHUNK_SET_SCHEMA:
        errors.append(f"chunk set schema must be {CHUNK_SET_SCHEMA}")
    validate_iso8601(packet.get("generated_at"), "generated_at", errors)

    request = dict_field(packet, "request", errors)
    intent = dict_field(packet, "intent", errors)
    action_authorization = packet.get("action_authorization")
    if action_authorization is not None and not isinstance(action_authorization, dict):
        errors.append("action_authorization must be an object when present")
        action_authorization = None
    routing = dict_field(packet, "routing", errors)
    confidence = dict_field(packet, "confidence", errors)
    budgets = dict_field(packet, "budgets", errors)
    provenance = dict_field(packet, "provenance", errors)
    selector_trace = packet.get("selector_trace")
    if selector_trace is not None and not isinstance(selector_trace, dict):
        errors.append("selector_trace must be an object when present")
        selector_trace = None
    matched_corpora = list_field(packet, "matched_corpora", errors)
    matched_rule_packs = list_field(packet, "matched_rule_packs", errors)
    matched_rulesets = list_field(packet, "matched_rulesets", errors)
    selected_chunks = list_field(packet, "selected_chunks", errors)
    required_checks = list_field(packet, "required_checks", errors)
    forbidden_actions = list_field(packet, "forbidden_actions", errors)
    stop_conditions = list_field(packet, "stop_conditions", errors)
    citations = list_field(packet, "citations", errors)
    gaps = list_field(packet, "gaps", errors)

    chunk_set_chunks = list_field(chunk_set, "chunks", errors)
    chunk_set_citations = list_field(chunk_set, "citations", errors)
    chunk_set_diagnostics = dict_field(chunk_set, "diagnostics", errors)
    if chunk_set_diagnostics.get("ok") is not True:
        errors.append("chunk set diagnostics.ok must be true")

    require_fields("request", request, ["raw_text", "normalized_summary"], errors)
    require_fields("intent", intent, ["id", "label", "confidence", "source"], errors)
    require_fields("routing", routing, ["layer", "mode", "workflow", "status"], errors)
    require_fields("confidence", confidence, ["overall", "retrieval", "routing"], errors)
    require_fields("budgets", budgets, ["max_context_tokens", "selected_context_tokens", "trim_policy"], errors)
    require_fields("provenance", provenance, ["service_version", "corpus_index_versions", "retrieval_order"], errors)
    if selector_trace is not None:
        require_fields(
            "selector_trace",
            selector_trace,
            ["strategy_id", "stages", "recognition_match_counts", "candidate_counts", "required_evidence"],
            errors,
        )
        if not isinstance(selector_trace.get("strategy_id"), str) or not selector_trace.get("strategy_id"):
            errors.append("selector_trace.strategy_id must be a non-empty string")
        stages = selector_trace.get("stages")
        if not isinstance(stages, list) or not stages:
            errors.append("selector_trace.stages must be a non-empty array")
            stages = []
        stage_ids: list[str] = []
        for index, stage in enumerate(stages, start=1):
            if not isinstance(stage, dict):
                errors.append(f"selector_trace.stages[{index}] must be an object")
                continue
            require_fields(
                f"selector_trace.stages[{index}]",
                stage,
                ["stage_id", "rank", "status", "summary", "signals"],
                errors,
            )
            if isinstance(stage.get("stage_id"), str) and stage.get("stage_id"):
                stage_ids.append(stage["stage_id"])
            else:
                errors.append(f"selector_trace.stages[{index}].stage_id must be a non-empty string")
            if not isinstance(stage.get("rank"), int) or isinstance(stage.get("rank"), bool):
                errors.append(f"selector_trace.stages[{index}].rank must be an integer")
            if stage.get("status") not in ALLOWED_SELECTOR_TRACE_STAGE_STATUSES:
                errors.append(f"selector_trace.stages[{index}].status is invalid: {stage.get('status')}")
            if not isinstance(stage.get("summary"), str) or not stage.get("summary"):
                errors.append(f"selector_trace.stages[{index}].summary must be a non-empty string")
            if not isinstance(stage.get("signals"), dict):
                errors.append(f"selector_trace.stages[{index}].signals must be an object")
        report_duplicate("selector_trace.stages[].stage_id", stage_ids, errors)

    validate_probability(intent.get("confidence"), "intent.confidence", errors)
    if intent.get("source") not in ALLOWED_INTENT_SOURCES:
        errors.append(f"intent.source is invalid: {intent.get('source')}")
    if routing.get("status") not in ALLOWED_ROUTING_STATUSES:
        errors.append(f"routing.status is invalid: {routing.get('status')}")
    for field in ["overall", "retrieval", "routing"]:
        validate_probability(confidence.get(field), f"confidence.{field}", errors)
    if budgets.get("trim_policy") not in ALLOWED_TRIM_POLICIES:
        errors.append(f"budgets.trim_policy is invalid: {budgets.get('trim_policy')}")

    chunk_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunk_set_chunks
        if isinstance(chunk.get("chunk_id"), str)
    }
    chunk_set_citation_by_id = {
        citation["id"]: citation
        for citation in chunk_set_citations
        if isinstance(citation.get("id"), str)
    }
    packet_citation_by_id = {
        citation["id"]: citation
        for citation in citations
        if isinstance(citation.get("id"), str)
    }
    selected_chunk_ids = [value for item in selected_chunks if (value := string_value(item, "chunk_id"))]
    packet_citation_ids = [value for item in citations if (value := string_value(item, "id"))]
    check_ids = [value for item in required_checks if (value := string_value(item, "id"))]
    stop_ids = [value for item in stop_conditions if (value := string_value(item, "id"))]
    gap_ids = [value for item in gaps if (value := string_value(item, "id"))]
    report_duplicate("selected_chunks[].chunk_id", selected_chunk_ids, errors)
    report_duplicate("citations[].id", packet_citation_ids, errors)
    report_duplicate("required_checks[].id", check_ids, errors)
    report_duplicate("stop_conditions[].id", stop_ids, errors)
    report_duplicate("gaps[].id", gap_ids, errors)

    matched_corpus_ids = {item.get("corpus_id") for item in matched_corpora if isinstance(item.get("corpus_id"), str)}
    selected_corpus_ids = {item.get("corpus_id") for item in selected_chunks if isinstance(item.get("corpus_id"), str)}
    selected_artifact_ids = {item.get("artifact_id") for item in selected_chunks if isinstance(item.get("artifact_id"), str)}
    selected_pack_refs = {
        pack_ref
        for chunk in selected_chunks
        for pack_ref in list_of_strings(chunk.get("pack_refs"))
    }
    selected_rule_ids = {
        rule_id
        for chunk in selected_chunks
        for rule_id in list_of_strings(chunk.get("rule_ids"))
    }

    for corpus in matched_corpora:
        require_fields("matched_corpora[]", corpus, ["corpus_id", "owner_layer", "match_reason", "confidence"], errors)
        validate_probability(corpus.get("confidence"), f"matched_corpora[{corpus.get('corpus_id')}].confidence", errors)
    for corpus_id in selected_corpus_ids:
        if corpus_id not in matched_corpus_ids:
            errors.append(f"selected chunk corpus is not listed in matched_corpora: {corpus_id}")

    for citation in citations:
        citation_id = string_value(citation, "id")
        require_fields(f"citations[{citation_id or '?'}]", citation, ["id", "source_path", "source_type"], errors)
        if citation.get("source_type") not in ALLOWED_CITATION_SOURCE_TYPES:
            errors.append(f"citation source_type is invalid: {citation_id} -> {citation.get('source_type')}")
        if citation_id and citation_id not in chunk_set_citation_by_id:
            errors.append(f"packet citation does not resolve to chunk-set citation: {citation_id}")
        source_path = citation.get("source_path")
        if isinstance(source_path, str) and path_should_exist(source_path) and not repo_path(source_path).is_file():
            errors.append(f"citation source_path does not exist: {citation_id} -> {source_path}")

    for rank, chunk in enumerate(selected_chunks, start=1):
        chunk_id = string_value(chunk, "chunk_id")
        require_fields(
            f"selected_chunks[{chunk_id or '?'}]",
            chunk,
            ["chunk_id", "corpus_id", "artifact_id", "source_path", "content", "rank", "token_estimate", "selection_reason", "citation_ids"],
            errors,
        )
        if not chunk_id:
            continue
        source_chunk = chunk_by_id.get(chunk_id)
        if not source_chunk:
            errors.append(f"selected chunk does not resolve to chunk set: {chunk_id}")
            continue
        if chunk.get("corpus_id") != source_chunk.get("corpus_id"):
            errors.append(f"selected chunk corpus mismatch: {chunk_id}")
        if chunk.get("artifact_id") != source_chunk.get("artifact_id"):
            errors.append(f"selected chunk artifact mismatch: {chunk_id}")
        if chunk.get("source_path") != source_chunk.get("source_path"):
            errors.append(f"selected chunk source_path mismatch: {chunk_id}")
        if chunk.get("content") != source_chunk.get("content"):
            errors.append(f"selected chunk content mismatch: {chunk_id}")
        if chunk.get("rank") != rank:
            errors.append(f"selected chunk rank must be sequential: {chunk_id}")
        if not isinstance(chunk.get("token_estimate"), int) or chunk.get("token_estimate") < 1:
            errors.append(f"selected chunk token_estimate must be a positive integer: {chunk_id}")
        if not isinstance(chunk.get("content"), str) or not chunk.get("content").strip():
            errors.append(f"selected chunk content must not be empty: {chunk_id}")
        if chunk.get("retrieval_score") is not None:
            validate_probability(chunk.get("retrieval_score"), f"selected_chunks[{chunk_id}].retrieval_score", errors)
        citation_ids = list_of_strings(chunk.get("citation_ids"))
        if not citation_ids:
            errors.append(f"selected chunk must have at least one citation: {chunk_id}")
        for citation_id in citation_ids:
            if citation_id not in packet_citation_by_id:
                errors.append(f"selected chunk citation does not resolve in packet: {chunk_id} -> {citation_id}")
            if citation_id not in list_of_strings(source_chunk.get("citation_ids")):
                errors.append(f"selected chunk citation not present on source chunk: {chunk_id} -> {citation_id}")
        for rule_id in list_of_strings(chunk.get("rule_ids")):
            if rule_id not in list_of_strings(source_chunk.get("rule_ids")):
                errors.append(f"selected chunk rule_id not present on source chunk: {chunk_id} -> {rule_id}")

    for pack in matched_rule_packs:
        require_fields("matched_rule_packs[]", pack, ["id", "corpus_id", "selection_reason"], errors)
        pack_id = string_value(pack, "id")
        if pack_id and selected_pack_refs and pack_id not in selected_pack_refs:
            warnings.append(f"matched rule pack is not represented by selected chunks: {pack_id}")
        for citation_id in list_of_strings(pack.get("citation_ids")):
            if citation_id not in packet_citation_by_id:
                errors.append(f"matched rule pack citation does not resolve: {pack_id} -> {citation_id}")

    for ruleset in matched_rulesets:
        require_fields("matched_rulesets[]", ruleset, ["id", "corpus_id", "ruleset_type", "selection_reason"], errors)
        ruleset_id = string_value(ruleset, "id")
        if ruleset.get("ruleset_type") not in ALLOWED_RULESET_TYPES:
            errors.append(f"matched ruleset type is invalid: {ruleset_id} -> {ruleset.get('ruleset_type')}")
        if ruleset_id and ruleset_id not in selected_artifact_ids:
            warnings.append(f"matched ruleset is not represented by selected chunks: {ruleset_id}")
        for rule_id in list_of_strings(ruleset.get("rule_ids")):
            if rule_id not in selected_rule_ids:
                warnings.append(f"matched ruleset rule_id is not represented by selected chunks: {ruleset_id} -> {rule_id}")
        for citation_id in list_of_strings(ruleset.get("citation_ids")):
            if citation_id not in packet_citation_by_id:
                errors.append(f"matched ruleset citation does not resolve: {ruleset_id} -> {citation_id}")

    for check in required_checks:
        check_id = string_value(check, "id")
        require_fields(f"required_checks[{check_id or '?'}]", check, ["id", "description", "timing", "citation_ids"], errors)
        if check.get("timing") not in ALLOWED_CHECK_TIMING:
            errors.append(f"required check timing is invalid: {check_id} -> {check.get('timing')}")
        validate_citation_list(f"required check {check_id}", check, packet_citation_by_id, errors)

    for action in forbidden_actions:
        action_name = string_value(action, "action")
        require_fields(f"forbidden_actions[{action_name or '?'}]", action, ["action", "reason", "citation_ids"], errors)
        validate_citation_list(f"forbidden action {action_name}", action, packet_citation_by_id, errors)

    for stop in stop_conditions:
        stop_id = string_value(stop, "id")
        require_fields(f"stop_conditions[{stop_id or '?'}]", stop, ["id", "condition", "severity", "citation_ids"], errors)
        if stop.get("severity") not in ALLOWED_STOP_SEVERITY:
            errors.append(f"stop condition severity is invalid: {stop_id} -> {stop.get('severity')}")
        validate_citation_list(f"stop condition {stop_id}", stop, packet_citation_by_id, errors)

    blocking_gaps = []
    for gap in gaps:
        gap_id = string_value(gap, "id")
        require_fields(f"gaps[{gap_id or '?'}]", gap, ["id", "type", "description", "blocking"], errors)
        if gap.get("type") not in ALLOWED_GAP_TYPES:
            errors.append(f"gap type is invalid: {gap_id} -> {gap.get('type')}")
        if not isinstance(gap.get("blocking"), bool):
            errors.append(f"gap blocking must be boolean: {gap_id}")
        elif gap.get("blocking"):
            blocking_gaps.append(gap_id)
        for chunk_id in list_of_strings(gap.get("required_evidence_chunk_ids")):
            if chunk_id not in selected_chunk_ids:
                errors.append(f"gap required evidence chunk is not selected: {gap_id} -> {chunk_id}")
        for citation_id in list_of_strings(gap.get("citation_ids")):
            if citation_id not in packet_citation_by_id:
                errors.append(f"gap citation does not resolve: {gap_id} -> {citation_id}")

    if blocking_gaps and routing.get("status") == "ready":
        errors.append("routing.status cannot be ready when blocking gaps exist")
    if isinstance(action_authorization, dict):
        require_fields(
            "action_authorization",
            action_authorization,
            ["requested_action", "side_effect_class", "execution_allowed", "status", "resolved_intent_id", "blocking_gap_ids"],
            errors,
        )
        if action_authorization.get("side_effect_class") not in ALLOWED_ACTION_SIDE_EFFECT_CLASSES:
            errors.append(f"action_authorization.side_effect_class is invalid: {action_authorization.get('side_effect_class')}")
        if action_authorization.get("status") not in ALLOWED_ACTION_AUTHORIZATION_STATUSES:
            errors.append(f"action_authorization.status is invalid: {action_authorization.get('status')}")
        if not isinstance(action_authorization.get("execution_allowed"), bool):
            errors.append("action_authorization.execution_allowed must be boolean")
        if (
            action_authorization.get("side_effect_class") == "deploy"
            and action_authorization.get("execution_allowed") is True
        ):
            errors.append("action_authorization.execution_allowed cannot be true for deploy selector packets")
        if action_authorization.get("execution_allowed") is True and routing.get("status") == "blocked":
            errors.append("action_authorization.execution_allowed cannot be true when routing.status is blocked")
        if action_authorization.get("execution_allowed") is True and blocking_gaps:
            errors.append("action_authorization.execution_allowed cannot be true when blocking gaps exist")
        for gap_id in list_of_strings(action_authorization.get("blocking_gap_ids")):
            if gap_id not in gap_ids:
                errors.append(f"action_authorization blocking gap does not resolve: {gap_id}")
            elif gap_id not in blocking_gaps:
                errors.append(f"action_authorization blocking gap is not blocking: {gap_id}")
        if action_authorization.get("status") == "blocked" and not list_of_strings(action_authorization.get("blocking_gap_ids")):
            errors.append("action_authorization.status blocked requires blocking_gap_ids")

    max_context_tokens = budgets.get("max_context_tokens")
    selected_context_tokens = budgets.get("selected_context_tokens")
    if not isinstance(max_context_tokens, int) or max_context_tokens < 1:
        errors.append("budgets.max_context_tokens must be a positive integer")
    if not isinstance(selected_context_tokens, int) or selected_context_tokens < 0:
        errors.append("budgets.selected_context_tokens must be a non-negative integer")
    actual_selected_tokens = sum(
        chunk.get("token_estimate")
        for chunk in selected_chunks
        if isinstance(chunk.get("token_estimate"), int)
    )
    if selected_context_tokens != actual_selected_tokens:
        errors.append(f"budgets.selected_context_tokens expected {actual_selected_tokens}, got {selected_context_tokens}")
    if isinstance(max_context_tokens, int) and isinstance(selected_context_tokens, int):
        if selected_context_tokens > max_context_tokens:
            errors.append("selected context exceeds max_context_tokens")

    corpus_index_versions = provenance.get("corpus_index_versions")
    if not isinstance(corpus_index_versions, list) or not corpus_index_versions:
        errors.append("provenance.corpus_index_versions must be a non-empty array")
    else:
        version_corpora = {
            item.get("corpus_id")
            for item in corpus_index_versions
            if isinstance(item, dict) and isinstance(item.get("corpus_id"), str)
        }
        for corpus_id in selected_corpus_ids:
            if corpus_id not in version_corpora:
                errors.append(f"provenance missing corpus index version for selected corpus: {corpus_id}")
    if not isinstance(provenance.get("retrieval_order"), list) or not provenance.get("retrieval_order"):
        errors.append("provenance.retrieval_order must be a non-empty array")

    return {
        "ok": not errors,
        "schema": packet.get("schema"),
        "packet_id": packet.get("packet_id"),
        "chunk_set_id": chunk_set.get("chunk_set_id"),
        "counts": {
            "selected_chunks": len(selected_chunks),
            "citations": len(citations),
            "required_checks": len(required_checks),
            "forbidden_actions": len(forbidden_actions),
            "stop_conditions": len(stop_conditions),
            "gaps": len(gaps),
        },
        "errors": errors,
        "warnings": warnings,
    }


def validate_citation_list(owner: str, item: dict[str, Any], citations: dict[str, dict[str, Any]], errors: list[str]) -> None:
    citation_ids = list_of_strings(item.get("citation_ids"))
    if not citation_ids:
        errors.append(f"{owner} must have at least one citation")
    for citation_id in citation_ids:
        if citation_id not in citations:
            errors.append(f"{owner} citation does not resolve: {citation_id}")


def print_human_report(report: dict[str, Any]) -> None:
    if report["ok"]:
        print("Context packet validation passed.")
    else:
        print("Context packet validation failed.")
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
        packet = load_json(str(repo_path(args.packet)))
        chunk_set = load_json(str(repo_path(args.chunks)))
        report = validate(packet, chunk_set)
    except Exception as exc:
        report = {
            "ok": False,
            "schema": None,
            "packet_id": None,
            "chunk_set_id": None,
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

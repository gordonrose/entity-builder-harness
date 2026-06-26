#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-retrieval-selector-fixture
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate a deterministic retrieval-selector fixture packet from policy, recognition sources, session metadata, and chunks.
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
#     - id: rag-rulebook.policy.retrieval-selector.v1
#       path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
#     - id: rag-rulebook.script.generate-retrieval-selector-fixture.readme
#       path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/README.md
#     - id: rag-rulebook.script.generate-retrieval-selector-fixture.smoke-test
#       path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for retrieval-selector fixture generation.", file=sys.stderr)
    sys.exit(2)


PACKET_SCHEMA = "rag-rulebook/context-packet/v1"
CHUNK_SET_SCHEMA = "rag-rulebook/chunk-set/v1"
GENERATOR_VERSION = "retrieval-selector-fixture-v1"
POLICY_PACK_PATH = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml"
RECOGNITION_ROOT = ".agentic/02.rag-rulebook/recognition-sources"
CANDIDATE_ROOT = ".agentic/02.rag-rulebook/recognition-candidates"
CORPUS_GAP_ROOT = ".agentic/02.rag-rulebook/corpus-gaps"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
PACKET_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-context-packet/script.sh"
POLICY_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
RECOGNITION_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-recognition-sources/script.sh"
CANDIDATE_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-recognition-candidates/script.sh"
DEFAULT_REQUEST = "Build the first deterministic RAG rulebook retrieval selector fixture."
DEFAULT_SESSION_LAYER = "02.rag-rulebook"
DEFAULT_SESSION_MODE = "implementation"
DEFAULT_SESSION_WORKFLOW = ".agentic/02.rag-rulebook/workflows/default.md"
DEFAULT_FOCUSED_PATHS = [
    ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml",
    ".agentic/02.rag-rulebook/recognition-sources/generated/routing.yml",
    "scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh",
]
ALLOWED_CITATION_SOURCE_TYPES = {"source", "rule", "rule-pack", "workflow", "standard", "schema", "plan"}
SESSION_LAYER_TO_CORPUS = {
    "00.chat": "corpus.00.chat",
    "01.harness": "corpus.01.harness",
    "02.rag-rulebook": "corpus.02.rag-rulebook",
    "03.product": "corpus.03.product",
    "04.deploy": "corpus.04.deploy",
    "05.education": "corpus.05.education",
    "06.shared": "corpus.06.shared",
}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "can",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "with",
}
TOKEN_ALIASES = {
    "checks": "check",
    "chunks": "chunk",
    "corpora": "corpus",
    "packets": "packet",
    "policies": "policy",
    "recognised": "recognize",
    "recognises": "recognize",
    "recognition": "recognize",
    "rules": "rule",
    "validated": "validate",
    "validating": "validate",
    "validation": "validate",
    "validator": "validate",
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
  generate-retrieval-selector-fixture/script.sh --generate-current [--pretty]
  generate-retrieval-selector-fixture/script.sh --chunks <path> [--pretty]

Options:
  --request-text <text>       Prompt text used for recognition and ranking.
  --session-layer <layer>     Session layer. Default: 02.rag-rulebook.
  --session-mode <mode>       Session mode. Default: implementation.
  --session-workflow <path>   Session workflow path.
  --focused-path <path>       Focused path signal. Repeatable.
  --no-focused-paths          Use no focused path signals.
  --max-chunks <n>            Maximum selected chunks. Default: 6. Range: 3-12.

Emits a validated rag-rulebook/context-packet/v1 JSON fixture to stdout. The
command is read-only and performs deterministic fixture selection only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--generate-current", action="store_true")
    parser.add_argument("--chunks")
    parser.add_argument("--request-text", default=DEFAULT_REQUEST)
    parser.add_argument("--session-layer", default=DEFAULT_SESSION_LAYER)
    parser.add_argument("--session-mode", default=DEFAULT_SESSION_MODE)
    parser.add_argument("--session-workflow", default=DEFAULT_SESSION_WORKFLOW)
    parser.add_argument("--focused-path", action="append", dest="focused_paths")
    parser.add_argument("--no-focused-paths", action="store_true")
    parser.add_argument("--max-chunks", type=int, default=6)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    modes = [args.generate_current, args.chunks is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.max_chunks < 3 or args.max_chunks > 12:
        print("ERROR: --max-chunks must be between 3 and 12.", file=sys.stderr)
        sys.exit(2)
    if not args.request_text.strip():
        print("ERROR: --request-text must not be empty.", file=sys.stderr)
        sys.exit(2)
    if args.no_focused_paths and args.focused_paths:
        print("ERROR: --no-focused-paths cannot be combined with --focused-path.", file=sys.stderr)
        sys.exit(2)
    if args.no_focused_paths:
        args.focused_paths = []
    elif not args.focused_paths:
        args.focused_paths = list(DEFAULT_FOCUSED_PATHS)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(repo_path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain an object: {path}")
    return data


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise ValueError(f"command did not emit a JSON object: {' '.join(command)}")
    return data


def validate_policy_pack() -> dict[str, Any]:
    report = run_json(["bash", POLICY_VALIDATOR_SCRIPT, "--current", "--json"])
    if report.get("ok") is not True:
        raise ValueError("retrieval policy pack is invalid")
    return report


def validate_recognition_sources() -> dict[str, Any]:
    report = run_json(["bash", RECOGNITION_VALIDATOR_SCRIPT, "--current", "--json"])
    if report.get("ok") is not True:
        raise ValueError("recognition sources are invalid")
    return report


def validate_recognition_candidates() -> dict[str, Any]:
    if not repo_path(CANDIDATE_ROOT).exists():
        return {"ok": True, "counts": {"candidates": 0}}
    report = run_json(["bash", CANDIDATE_VALIDATOR_SCRIPT, "--current", "--json"])
    if report.get("ok") is not True:
        raise ValueError("recognition candidates are invalid")
    return report


def load_chunk_set(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    if args.generate_current:
        result = subprocess.run(
            ["bash", CHUNK_GENERATOR_SCRIPT, "--generate-current"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        raw = result.stdout
    else:
        raw = repo_path(args.chunks).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("chunk set JSON must be an object")
    if data.get("schema") != CHUNK_SET_SCHEMA:
        raise ValueError(f"chunk set schema must be {CHUNK_SET_SCHEMA}")
    diagnostics = data.get("diagnostics")
    if isinstance(diagnostics, dict) and diagnostics.get("ok") is not True:
        raise ValueError("chunk set diagnostics.ok must be true")
    if not isinstance(data.get("chunks"), list) or not data["chunks"]:
        raise ValueError("chunk set must include chunks")
    return data, raw


def load_recognition_sources() -> list[dict[str, Any]]:
    root = repo_path(RECOGNITION_ROOT)
    sources: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        data = load_yaml(path)
        if data.get("schema") != "rag-rulebook/recognition-source/v1":
            continue
        data["_path"] = str(path.relative_to(ROOT))
        sources.append(data)
    sources.sort(key=lambda source: (int(source.get("match_priority") or 9999), str(source.get("source_id"))))
    return sources


def load_recognition_candidates() -> list[dict[str, Any]]:
    root = repo_path(CANDIDATE_ROOT)
    if not root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        data = load_yaml(path)
        if data.get("schema") != "rag-rulebook/recognition-candidate/v1":
            continue
        data["_path"] = str(path.relative_to(ROOT))
        candidates.append(data)
    return candidates


def load_corpus_gaps() -> list[dict[str, Any]]:
    root = repo_path(CORPUS_GAP_ROOT)
    if not root.exists():
        return []
    gaps: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        data = load_yaml(path)
        if data.get("schema") != "rag-rulebook/corpus-gap/v1":
            continue
        data["_path"] = str(path.relative_to(ROOT))
        gaps.append(data)
    return gaps


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_id(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", ".", str(value or "unknown").lower()).strip(".")
    return cleaned or "unknown"


def normalize_token(token: str) -> str:
    token = TOKEN_ALIASES.get(token, token)
    if token.endswith("s") and len(token) > 4:
        token = token[:-1]
    return TOKEN_ALIASES.get(token, token)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for raw_token in re.findall(r"[a-z0-9]+", text.lower()):
        token = normalize_token(raw_token)
        if len(token) < 3 or token in STOP_WORDS or token in seen:
            continue
        tokens.append(token)
        seen.add(token)
    return tokens


def simple_exact_match(term: str, text: str) -> bool:
    term_lower = term.lower()
    text_lower = text.lower()
    if not term_lower:
        return False
    if "/" in term_lower or "." in term_lower or "-" in term_lower:
        return term_lower in text_lower
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term_lower)}(?![a-z0-9])", text_lower))


def coverage_stage_summary(coverage: dict[str, Any]) -> str:
    stages = coverage.get("stages")
    if not isinstance(stages, dict):
        return ""
    present = []
    missing = []
    for stage_name, stage in stages.items():
        if not isinstance(stage, dict):
            continue
        if stage.get("status") == "present":
            present.append(stage_name)
        elif stage.get("status") == "missing":
            missing.append(stage_name)
    parts = []
    if present:
        parts.append(f"present stages: {', '.join(sorted(present))}")
    if missing:
        parts.append(f"missing stages: {', '.join(sorted(missing))}")
    return "; ".join(parts)


def candidate_coverage_gaps(candidates: list[dict[str, Any]], request_text: str) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        status = candidate.get("status")
        if status not in {"needs-review", "deferred"}:
            continue
        observed = candidate.get("observed") if isinstance(candidate.get("observed"), dict) else {}
        term = str(observed.get("term") or "").strip()
        if not term or not simple_exact_match(term, request_text):
            continue
        coverage = candidate.get("coverage") if isinstance(candidate.get("coverage"), dict) else {}
        coverage_status = coverage.get("status")
        if coverage.get("required") is not True or coverage_status not in {"missing", "partial"}:
            continue
        gap_id = str(coverage.get("gap_id") or f"gap.selector-fixture.missing-corpus.{safe_id(term)}")
        if gap_id in seen:
            continue
        seen.add(gap_id)
        needed_corpus_ids = list_of_strings(coverage.get("needed_corpus_ids"))
        needed_topic = str(coverage.get("needed_topic") or term).strip().rstrip(".")
        description = (
            f"Prompt mentions {term}, but candidate {candidate.get('candidate_id')} says "
            f"coverage is {coverage_status} for {needed_topic}."
        )
        if needed_corpus_ids:
            description += f" Needed corpora: {', '.join(needed_corpus_ids)}."
        stage_summary = coverage_stage_summary(coverage)
        if stage_summary:
            description += f" Stage status: {stage_summary}."
        gaps.append(
            {
                "id": gap_id,
                "type": "missing-corpus",
                "description": description,
                "blocking": False,
                "suggested_resolution": coverage.get("suggested_resolution")
                or "Add governed corpus source material before treating this term as covered retrieval knowledge.",
            }
        )
    return gaps


def corpus_gap_matches_request(
    gap: dict[str, Any],
    candidates_by_id: dict[str, dict[str, Any]],
    request_text: str,
) -> bool:
    for term in list_of_strings(gap.get("match_terms")):
        if simple_exact_match(term, request_text):
            return True

    related_candidate = dict_value(gap.get("related_candidate"))
    candidate_id = related_candidate.get("candidate_id")
    candidate = candidates_by_id.get(str(candidate_id)) if candidate_id else None
    observed = dict_value(candidate.get("observed")) if candidate else {}
    candidate_term = str(observed.get("term") or "").strip()
    if candidate_term and simple_exact_match(candidate_term, request_text):
        return True

    observed_prompt = str(gap.get("observed_prompt") or "").strip()
    return bool(observed_prompt and observed_prompt.lower() == request_text.strip().lower())


def corpus_gap_blocking(gap: dict[str, Any], recognition_matches: list[dict[str, Any]]) -> bool:
    behavior = dict_value(gap.get("local_query_behavior"))
    blocking_by_intent = dict_value(behavior.get("blocking_by_intent"))
    intent_ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "intent-form" and isinstance(match.get("canonical_id"), str)
    }
    for intent_id in sorted(intent_ids):
        if isinstance(blocking_by_intent.get(intent_id), bool):
            return bool(blocking_by_intent[intent_id])
    return bool(behavior.get("blocking") is True)


def corpus_gap_records_gaps(
    corpus_gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    recognition_matches: list[dict[str, Any]],
    request_text: str,
) -> list[dict[str, Any]]:
    emitted: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidates_by_id = {
        str(candidate.get("candidate_id")): candidate
        for candidate in candidates
        if isinstance(candidate.get("candidate_id"), str)
    }
    for gap in corpus_gaps:
        gap_id = str(gap.get("gap_id") or "").strip()
        if not gap_id or gap_id in seen:
            continue
        if gap.get("status") not in {"open", "planned", "in-progress"}:
            continue
        behavior = dict_value(gap.get("local_query_behavior"))
        if behavior.get("should_emit_gap") is False:
            continue
        if not corpus_gap_matches_request(gap, candidates_by_id, request_text):
            continue
        seen.add(gap_id)
        target_corpus_id = str(gap.get("target_corpus_id") or "").strip()
        summary = str(gap.get("summary") or "A required corpus coverage gap is still open.").strip()
        description = summary
        if target_corpus_id:
            description += f" Target corpus: {target_corpus_id}."
        emitted.append(
            {
                "id": gap_id,
                "type": "missing-corpus",
                "description": description,
                "blocking": corpus_gap_blocking(gap, recognition_matches),
                "suggested_resolution": str(
                    gap.get("suggested_resolution")
                    or "Add governed source material, structured rules, chunks, and selector evaluation proof before treating this coverage as available."
                ),
            }
        )
    return emitted


def matched_candidate_evidence_paths(candidates: list[dict[str, Any]], request_text: str) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        status = candidate.get("status")
        if status not in {"needs-review", "deferred", "accepted"}:
            continue
        observed = candidate.get("observed") if isinstance(candidate.get("observed"), dict) else {}
        term = str(observed.get("term") or "").strip()
        if not term or not simple_exact_match(term, request_text):
            continue
        coverage = candidate.get("coverage") if isinstance(candidate.get("coverage"), dict) else {}
        stages = coverage.get("stages") if isinstance(coverage.get("stages"), dict) else {}
        for stage in stages.values():
            if not isinstance(stage, dict) or stage.get("status") != "present":
                continue
            for evidence_path in list_of_strings(stage.get("evidence_paths")):
                if evidence_path in seen or not repo_path(evidence_path).is_file():
                    continue
                seen.add(evidence_path)
                paths.append(evidence_path)
    return paths


def focused_path_match(term: str, paths: list[str]) -> bool:
    term_lower = term.lower()
    if not term_lower:
        return False
    for path in paths:
        path_lower = path.lower()
        if term_lower in path_lower or path_lower in term_lower:
            return True
    return False


def match_recognition_terms(
    sources: list[dict[str, Any]],
    request_text: str,
    session_text: str,
    focused_paths: list[str],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for source in sources:
        source_id = str(source.get("source_id"))
        for term in list_of_dicts(source.get("terms")):
            raw_term = str(term.get("term") or "").strip()
            if not raw_term:
                continue
            lookup_terms = [raw_term] + list_of_strings(term.get("aliases"))
            for lookup_term in lookup_terms:
                matched_inputs: list[str] = []
                if simple_exact_match(lookup_term, request_text):
                    matched_inputs.append("prompt")
                if simple_exact_match(lookup_term, session_text):
                    matched_inputs.append("session-metadata")
                if focused_path_match(lookup_term, focused_paths):
                    matched_inputs.append("focused-paths")
                for matched_input in matched_inputs:
                    key = (source_id, lookup_term.lower(), str(term.get("category")), matched_input)
                    if key in seen:
                        continue
                    seen.add(key)
                    matches.append(
                        {
                            "source_id": source_id,
                            "term": lookup_term,
                            "category": term.get("category"),
                            "canonical_id": term.get("canonical_id") or raw_term,
                            "match_type": term.get("match_type", "exact") if lookup_term == raw_term else "alias",
                            "matched_input": matched_input,
                            "evidence_path": term.get("evidence_path") or source.get("_path"),
                            "confidence_weight": term.get("confidence_weight", 1),
                        }
                    )
    return matches


def owner_layer(corpus_id: str) -> str:
    parts = corpus_id.split(".")
    if len(parts) >= 3 and parts[0] == "corpus":
        return ".".join(parts[1:3])
    return corpus_id


def ruleset_type(artifact_id: str) -> str:
    if ".concern." in artifact_id:
        return "concern"
    if ".workflow." in artifact_id:
        return "workflow"
    if ".standard." in artifact_id:
        return "standard"
    return "layer"


def normalize_source_type(source_type: Any) -> str:
    if isinstance(source_type, str) and source_type in ALLOWED_CITATION_SOURCE_TYPES:
        return source_type
    if isinstance(source_type, str) and "rule-pack" in source_type:
        return "rule-pack"
    if isinstance(source_type, str) and "rule" in source_type:
        return "rule"
    if isinstance(source_type, str) and "workflow" in source_type:
        return "workflow"
    if isinstance(source_type, str) and "standard" in source_type:
        return "standard"
    if isinstance(source_type, str) and "schema" in source_type:
        return "schema"
    if isinstance(source_type, str) and "plan" in source_type:
        return "plan"
    return "source"


def chunk_haystack(chunk: dict[str, Any]) -> str:
    parts = [
        chunk.get("chunk_id"),
        chunk.get("corpus_id"),
        chunk.get("artifact_id"),
        chunk.get("artifact_ref"),
        chunk.get("source_path"),
        chunk.get("content_kind"),
        chunk.get("content"),
        " ".join(list_of_strings(chunk.get("rule_ids"))),
        " ".join(list_of_strings(chunk.get("pack_refs"))),
    ]
    return "\n".join(str(part).lower() for part in parts if part)


def source_rank(chunk: dict[str, Any]) -> int:
    rank = chunk.get("rank")
    return rank if isinstance(rank, int) else 999999


def score_chunk(
    chunk: dict[str, Any],
    prompt_terms: list[str],
    recognition_matches: list[dict[str, Any]],
    focused_paths: list[str],
    session_corpus: str,
) -> float:
    haystack = chunk_haystack(chunk)
    score = 0.0
    for term in prompt_terms:
        score += haystack.count(term)

    chunk_corpus = str(chunk.get("corpus_id") or "")
    if chunk_corpus == session_corpus:
        score += 6

    source_path = str(chunk.get("source_path") or "")
    artifact_id = str(chunk.get("artifact_id") or "")
    for focused_path in focused_paths:
        focused_lower = focused_path.lower()
        if focused_lower and (focused_lower in source_path.lower() or source_path.lower() in focused_lower):
            score += 18

    for match in recognition_matches:
        category = match.get("category")
        canonical = str(match.get("canonical_id") or "")
        term = str(match.get("term") or "")
        matched_input = str(match.get("matched_input") or "")
        input_weight = 2 if matched_input == "prompt" else 1
        confidence_weight = match.get("confidence_weight")
        if not isinstance(confidence_weight, (int, float)):
            confidence_weight = 1
        weight = input_weight * float(confidence_weight)
        if category == "corpus-id" and canonical == chunk_corpus:
            score += 10 * weight
        elif category == "artifact-id" and canonical == artifact_id:
            score += 25 * weight
        elif category == "file-path" and (canonical in source_path or term in source_path):
            score += 25 * weight
        elif category in {"rule-id", "rule-pack-id"} and canonical.lower() in haystack:
            score += 16 * weight
        elif category in {"layer-name", "mode-name", "workflow-name"} and term.lower() in haystack:
            score += 3 * weight
        elif category == "action-verb" and term.lower() in haystack:
            score += 2 * weight
        elif category in {"risk-word", "stop-condition", "check-name"} and term.lower() in haystack:
            score += 4 * weight

    kind = chunk.get("content_kind")
    term_set = set(prompt_terms)
    if kind == "required-check" and term_set.intersection({"check", "validate", "governed", "gate"}):
        score += 6
    if kind == "rule" and term_set.intersection({"rule", "policy", "selector", "retrieval", "governed"}):
        score += 5
    if kind == "artifact-summary" and term_set.intersection({"artifact", "source", "rulebook", "rag"}):
        score += 4
    return score


def ranked_chunks(
    chunks: list[dict[str, Any]],
    prompt_terms: list[str],
    recognition_matches: list[dict[str, Any]],
    focused_paths: list[str],
    session_corpus: str,
) -> list[tuple[float, int, str, dict[str, Any]]]:
    ranked = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str):
            continue
        ranked.append(
            (
                score_chunk(chunk, prompt_terms, recognition_matches, focused_paths, session_corpus),
                source_rank(chunk),
                chunk_id,
                chunk,
            )
        )
    return sorted(ranked, key=lambda item: (-item[0], item[1], item[2]))


def select_chunks(ranked: list[tuple[float, int, str, dict[str, Any]]], max_chunks: int) -> list[tuple[float, dict[str, Any]]]:
    selected: dict[str, tuple[float, dict[str, Any]]] = {}

    def add(item: tuple[float, int, str, dict[str, Any]] | None) -> None:
        if item is None:
            return
        score, _rank, chunk_id, chunk = item
        selected.setdefault(chunk_id, (score, chunk))

    for kind in ["required-check", "rule", "artifact-summary"]:
        preferred = next((item for item in ranked if item[3].get("content_kind") == kind and item[0] > 0), None)
        fallback = next((item for item in ranked if item[3].get("content_kind") == kind), None)
        add(preferred or fallback)

    for item in ranked:
        if len(selected) >= max_chunks:
            break
        if item[0] <= 0 and len(selected) >= 3:
            continue
        add(item)

    if len(selected) < 3:
        for item in ranked:
            if len(selected) >= 3:
                break
            add(item)

    ordered = sorted(
        selected.values(),
        key=lambda item: (-item[0], source_rank(item[1]), item[1].get("chunk_id", "")),
    )
    return ordered[:max_chunks]


def citation_ids_for(chunks: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        for citation_id in list_of_strings(chunk.get("citation_ids")):
            if citation_id not in seen:
                ids.append(citation_id)
                seen.add(citation_id)
    return ids


def required_check_description(chunk: dict[str, Any]) -> str:
    content = str(chunk.get("content") or "")
    marker = "Required check:"
    if marker in content:
        return content.split(marker, 1)[1].strip()
    first_line = content.strip().splitlines()[0] if content.strip() else str(chunk.get("chunk_id"))
    return first_line


def category_summary(matches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in matches:
        category = str(match.get("category") or "unknown")
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def matched_corpus_ids(matches: list[dict[str, Any]], session_corpus: str) -> list[str]:
    corpus_ids = [session_corpus]
    for match in matches:
        if match.get("category") == "corpus-id":
            corpus_ids.append(str(match.get("canonical_id")))
    seen: set[str] = set()
    result: list[str] = []
    for corpus_id in corpus_ids:
        if corpus_id and corpus_id not in seen:
            result.append(corpus_id)
            seen.add(corpus_id)
    return result


def prototype_bridge_corpora(session_layer: str) -> list[str]:
    if session_layer == "02.rag-rulebook":
        return ["corpus.01.harness", "corpus.06.shared"]
    return []


def candidate_ranked_chunks(
    ranked: list[tuple[float, int, str, dict[str, Any]]],
    allowed_corpus_ids: list[str],
    allowed_source_paths: list[str],
) -> tuple[list[tuple[float, int, str, dict[str, Any]]], bool]:
    allowed = set(allowed_corpus_ids)
    source_paths = set(allowed_source_paths)
    filtered = [
        item
        for item in ranked
        if item[3].get("corpus_id") in allowed or item[3].get("source_path") in source_paths
    ]
    if len(filtered) >= 3:
        return filtered, True
    return ranked, False


def build_packet(
    args: argparse.Namespace,
    policy: dict[str, Any],
    policy_report: dict[str, Any],
    recognition_report: dict[str, Any],
    candidate_report: dict[str, Any],
    recognition_matches: list[dict[str, Any]],
    recognition_candidates: list[dict[str, Any]],
    corpus_gaps: list[dict[str, Any]],
    chunk_set: dict[str, Any],
) -> dict[str, Any]:
    chunks = list_of_dicts(chunk_set.get("chunks"))
    citations = list_of_dicts(chunk_set.get("citations"))
    prompt_terms = tokenize(args.request_text)
    session_corpus = SESSION_LAYER_TO_CORPUS.get(args.session_layer, f"corpus.{args.session_layer}")
    allowed_corpus_ids = matched_corpus_ids(recognition_matches, session_corpus) + prototype_bridge_corpora(args.session_layer)
    candidate_evidence_paths = matched_candidate_evidence_paths(recognition_candidates, args.request_text)
    ranking_paths = list(args.focused_paths) + candidate_evidence_paths
    ranked = ranked_chunks(chunks, prompt_terms, recognition_matches, ranking_paths, session_corpus)
    candidate_ranked, used_candidate_filter = candidate_ranked_chunks(
        ranked,
        allowed_corpus_ids,
        candidate_evidence_paths,
    )
    selected_pairs = select_chunks(candidate_ranked, args.max_chunks)
    selected_source_chunks = [chunk for _score, chunk in selected_pairs]
    if len(selected_source_chunks) < 3:
        raise ValueError("selector fixture requires at least three selected chunks")

    max_score = max((score for score, _chunk in selected_pairs), default=0)
    selected_chunks: list[dict[str, Any]] = []
    for rank, (score, source_chunk) in enumerate(selected_pairs, start=1):
        chunk = dict(source_chunk)
        chunk["rank"] = rank
        chunk["retrieval_score"] = round(score / max_score, 4) if max_score else 0
        chunk["selection_reason"] = (
            "Selected by deterministic retrieval-selector fixture using prompt terms, "
            "session metadata, focused paths, and recognition-source matches."
        )
        selected_chunks.append(chunk)

    chunk_citation_by_id = {
        citation.get("id"): citation
        for citation in citations
        if isinstance(citation.get("id"), str)
    }
    selected_citation_ids = citation_ids_for(selected_chunks)
    packet_citations = []
    for citation_id in selected_citation_ids:
        source = chunk_citation_by_id.get(citation_id)
        if not source:
            continue
        packet_citations.append(
            {
                "id": citation_id,
                "corpus_id": source.get("corpus_id"),
                "artifact_id": source.get("artifact_id"),
                "source_path": source.get("source_path"),
                "source_type": normalize_source_type(source.get("source_type")),
                "source_ref": citation_id,
            }
        )

    selected_corpus_ids = sorted({chunk["corpus_id"] for chunk in selected_chunks if isinstance(chunk.get("corpus_id"), str)})
    selected_artifact_ids = sorted({chunk["artifact_id"] for chunk in selected_chunks if isinstance(chunk.get("artifact_id"), str)})
    selected_pack_refs = sorted({pack_ref for chunk in selected_chunks for pack_ref in list_of_strings(chunk.get("pack_refs"))})
    selected_rule_ids = sorted({rule_id for chunk in selected_chunks for rule_id in list_of_strings(chunk.get("rule_ids"))})
    all_matched_corpora = sorted(set(selected_corpus_ids + allowed_corpus_ids))

    checks = []
    required_check_chunks = [chunk for chunk in selected_chunks if chunk.get("content_kind") == "required-check"]
    for index, chunk in enumerate(required_check_chunks[:3], start=1):
        checks.append(
            {
                "id": f"check.selector-fixture.{index}.{safe_id(chunk.get('chunk_id'))}",
                "description": required_check_description(chunk),
                "timing": "before-edit",
                "citation_ids": list_of_strings(chunk.get("citation_ids"))[:1] or selected_citation_ids[:1],
            }
        )
    if not checks:
        checks.append(
            {
                "id": "check.selector-fixture.validate-context-packet",
                "description": "Validate the selector fixture packet before using it as LLM context.",
                "timing": "before-edit",
                "command": "bash scripts/02.rag-rulebook/validate-context-packet/script.sh --packet <packet> --chunks <chunks>",
                "citation_ids": selected_citation_ids[:1],
            }
        )

    prompt_layer_matches = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "layer-name" and match.get("matched_input") == "prompt"
    }
    prompt_layer_conflicts = sorted(
        layer
        for layer in prompt_layer_matches
        if layer != args.session_layer and re.fullmatch(r"[0-9]{2}\.[a-z0-9-]+", layer)
    )
    gaps = []
    if prompt_layer_conflicts:
        gaps.append(
            {
                "id": "gap.selector-fixture.prompt-session-layer-conflict",
                "type": "ambiguous-intent",
                "description": "Prompt layer terms differ from complete session metadata; session metadata wins in this fixture.",
                "blocking": False,
            }
        )
    if not recognition_matches:
        gaps.append(
            {
                "id": "gap.selector-fixture.no-recognition-source-match",
                "type": "ambiguous-intent",
                "description": "No governed recognition-source terms matched the request or session metadata.",
                "blocking": False,
            }
        )
    prompt_or_path_matches = [
        match
        for match in recognition_matches
        if match.get("matched_input") in {"prompt", "focused-paths"}
    ]
    if not prompt_or_path_matches and prompt_terms:
        gaps.append(
            {
                "id": "gap.selector-fixture.low-confidence-prompt",
                "type": "ambiguous-intent",
                "description": "The prompt produced no governed prompt or focused-path recognition matches, so routing relies on session metadata only.",
                "blocking": False,
            }
        )
    if args.session_layer == "02.rag-rulebook" and session_corpus not in selected_corpus_ids:
        gaps.append(
            {
                "id": "gap.selector-fixture.prototype-corpus-bridge",
                "type": "missing-corpus",
                "description": "The current prototype chunks do not yet contain corpus.02.rag-rulebook, so the fixture bridges through harness/shared prototype corpus chunks until migration.",
                "blocking": False,
            }
        )
    gaps.extend(candidate_coverage_gaps(recognition_candidates, args.request_text))
    gaps.extend(corpus_gap_records_gaps(corpus_gaps, recognition_candidates, recognition_matches, args.request_text))

    selected_context_tokens = sum(
        chunk.get("token_estimate")
        for chunk in selected_chunks
        if isinstance(chunk.get("token_estimate"), int)
    )
    source_index_id = chunk_set.get("source_index_id") or chunk_set.get("provenance", {}).get("source_index_id")
    source_index_hash = chunk_set.get("provenance", {}).get("source_index_fingerprint")
    packet_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "request": args.request_text,
                "session_layer": args.session_layer,
                "session_mode": args.session_mode,
                "session_workflow": args.session_workflow,
                "focused_paths": args.focused_paths,
                "chunk_ids": [chunk.get("chunk_id") for chunk in selected_chunks],
                "recognition_matches": [
                    [match.get("source_id"), match.get("term"), match.get("matched_input")]
                    for match in recognition_matches[:40]
                ],
                "gaps": [gap.get("id") for gap in gaps],
                "source_index_id": source_index_id,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]

    recognition_confidence = min(1, 0.75 + (0.02 * min(len(recognition_matches), 10)))
    retrieval_confidence = 0.9 if max_score else 0.55
    if prompt_layer_conflicts:
        retrieval_confidence = min(retrieval_confidence, 0.82)
    if not prompt_or_path_matches and prompt_terms:
        recognition_confidence = min(recognition_confidence, 0.69)
        retrieval_confidence = min(retrieval_confidence, 0.69)
    routing_status = "blocked" if any(gap.get("blocking") is True for gap in gaps) else "ready"

    return {
        "schema": PACKET_SCHEMA,
        "packet_id": f"packet.selector-fixture.{packet_fingerprint}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "request": {
            "raw_text": args.request_text,
            "normalized_summary": "Generate a deterministic retrieval selector fixture from governed policy, recognition sources, session metadata, and chunks.",
            "focused_paths": args.focused_paths,
            "open_artifact_ids": selected_artifact_ids,
            "recognition_source_matches": recognition_matches[:80],
        },
        "intent": {
            "id": "intent.rag-rulebook.generate-retrieval-selector-fixture",
            "label": "Generate retrieval selector fixture",
            "mode": args.session_mode,
            "layer": args.session_layer,
            "workflow": args.session_workflow,
            "confidence": recognition_confidence,
            "source": "mixed",
            "evidence_ref_ids": selected_citation_ids,
        },
        "routing": {
            "layer": args.session_layer,
            "mode": args.session_mode,
            "workflow": args.session_workflow,
            "status": routing_status,
            "task_type": "generate_retrieval_selector_fixture",
            "target_paths": args.focused_paths,
            "classification_source": "session-metadata-plus-recognition-sources",
            "recognition_summary": category_summary(recognition_matches),
        },
        "matched_corpora": [
            {
                "corpus_id": corpus_id,
                "owner_layer": owner_layer(corpus_id),
                "match_reason": (
                    "Selected chunks belong to this corpus."
                    if corpus_id in selected_corpus_ids
                    else "Prototype bridge corpus used until final corpus migration."
                    if corpus_id in prototype_bridge_corpora(args.session_layer)
                    else "Session metadata or recognition-source terms matched this corpus."
                ),
                "confidence": 1 if corpus_id in selected_corpus_ids else recognition_confidence,
            }
            for corpus_id in all_matched_corpora
        ],
        "matched_rule_packs": [
            {
                "id": pack_ref,
                "corpus_id": next(
                    chunk["corpus_id"]
                    for chunk in selected_chunks
                    if pack_ref in list_of_strings(chunk.get("pack_refs"))
                ),
                "selection_reason": "Selected selector-fixture chunks reference this rule pack.",
                "citation_ids": citation_ids_for(
                    [chunk for chunk in selected_chunks if pack_ref in list_of_strings(chunk.get("pack_refs"))]
                ),
            }
            for pack_ref in selected_pack_refs
        ],
        "matched_rulesets": [
            {
                "id": artifact_id,
                "corpus_id": next(chunk["corpus_id"] for chunk in selected_chunks if chunk.get("artifact_id") == artifact_id),
                "ruleset_type": ruleset_type(artifact_id),
                "rule_ids": selected_rule_ids,
                "selection_reason": "Selected selector-fixture chunks reference this ruleset artifact.",
                "citation_ids": citation_ids_for(
                    [chunk for chunk in selected_chunks if chunk.get("artifact_id") == artifact_id]
                ),
            }
            for artifact_id in selected_artifact_ids
        ],
        "selected_chunks": selected_chunks,
        "required_checks": checks,
        "forbidden_actions": [
            {
                "action": "Treat selector fixture output as production semantic retrieval",
                "reason": "This fixture proves deterministic wiring only; it does not perform semantic recall or production ranking.",
                "citation_ids": selected_citation_ids[:1],
            }
        ],
        "stop_conditions": [
            {
                "id": "stop.selector-fixture.validation-failure",
                "condition": "The generated packet fails context-packet validation or references unresolved chunks or citations.",
                "severity": "blocking",
                "suggested_resolution": "Repair the selector fixture, chunk generator, or packet validator before using the packet.",
                "citation_ids": selected_citation_ids[:1],
            }
        ],
        "citations": packet_citations,
        "confidence": {
            "overall": min(recognition_confidence, retrieval_confidence),
            "retrieval": retrieval_confidence,
            "routing": recognition_confidence,
            "notes": [
                "Session metadata is preferred over prompt inference.",
                "Recognition-source matches are deterministic lookup signals.",
                "Semantic recall is not enabled for this fixture.",
            ],
        },
        "gaps": gaps,
        "budgets": {
            "max_context_tokens": int(policy.get("thresholds", {}).get("max_context_tokens") or selected_context_tokens + 1000),
            "selected_context_tokens": selected_context_tokens,
            "trim_policy": "deterministic-first",
        },
        "provenance": {
            "service_version": GENERATOR_VERSION,
            "policy_pack": {
                "policy_pack_id": policy.get("policy_pack_id"),
                "version": policy.get("version"),
                "validator_counts": policy_report.get("counts"),
            },
            "recognition_sources": {
                "validator_counts": recognition_report.get("counts"),
                "matched_terms": len(recognition_matches),
            },
            "recognition_candidates": {
                "validator_counts": candidate_report.get("counts"),
                "matched_coverage_gaps": len([gap for gap in gaps if gap.get("type") == "missing-corpus"]),
            },
            "corpus_gaps": {
                "loaded": len(corpus_gaps),
                "matched": len([gap for gap in gaps if str(gap.get("id") or "").startswith("gap.corpus.")]),
            },
            "corpus_index_versions": [
                {
                    "corpus_id": corpus_id,
                    "index_version": source_index_id,
                    "content_hash": source_index_hash,
                }
                for corpus_id in selected_corpus_ids
            ],
            "retrieval_order": [
                "validate retrieval policy pack",
                "validate recognition sources",
                "load generated chunks",
                "match prompt, session metadata, and focused paths against recognition sources",
                "restrict candidate chunks by session, recognition, and prototype bridge corpora when enough candidates exist",
                "score chunks with deterministic recognition, session, path, corpus, and token signals",
                "require required-check, rule, and artifact-summary coverage where available",
                "validate context packet against chunk set before output",
            ],
            "candidate_filter_used": used_candidate_filter,
            "candidate_corpus_ids": allowed_corpus_ids,
            "matched_candidate_evidence_paths": candidate_evidence_paths,
            "generator": "scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh",
            "chunk_set_id": chunk_set.get("chunk_set_id"),
        },
    }


def validate_packet(packet: dict[str, Any], chunk_set_raw: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as packet_handle:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as chunks_handle:
            json.dump(packet, packet_handle, sort_keys=True)
            packet_handle.flush()
            chunks_handle.write(chunk_set_raw)
            chunks_handle.flush()
            result = subprocess.run(
                [
                    "bash",
                    PACKET_VALIDATOR_SCRIPT,
                    "--packet",
                    packet_handle.name,
                    "--chunks",
                    chunks_handle.name,
                    "--json",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    report = json.loads(result.stdout)
    if not report.get("ok"):
        sys.stderr.write(result.stdout)
        raise SystemExit(1)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        policy_report = validate_policy_pack()
        recognition_report = validate_recognition_sources()
        candidate_report = validate_recognition_candidates()
        policy = load_yaml(POLICY_PACK_PATH)
        sources = load_recognition_sources()
        candidates = load_recognition_candidates()
        corpus_gaps = load_corpus_gaps()
        chunk_set, chunk_set_raw = load_chunk_set(args)
        session_text = "\n".join([args.session_layer, args.session_mode, args.session_workflow])
        recognition_matches = match_recognition_terms(
            sources,
            args.request_text,
            session_text,
            args.focused_paths,
        )
        packet = build_packet(
            args,
            policy,
            policy_report,
            recognition_report,
            candidate_report,
            recognition_matches,
            candidates,
            corpus_gaps,
            chunk_set,
        )
        validate_packet(packet, chunk_set_raw)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.pretty:
        print(json.dumps(packet, indent=2, sort_keys=True))
    else:
        print(json.dumps(packet, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

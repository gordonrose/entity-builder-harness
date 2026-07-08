#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-context-packet-fixture
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: context-packets
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate and validate a small deterministic context-packet fixture from rulebook chunks.
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
#     - id: rag-rulebook.script.validate-context-packet
#       path: scripts/02.rag-rulebook/validate-context-packet/script.sh
#     - id: rag-rulebook.script.generate-context-packet-fixture.readme
#       path: scripts/02.rag-rulebook/generate-context-packet-fixture/README.md

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


PACKET_SCHEMA = "rag-rulebook/context-packet/v1"
CHUNK_SET_SCHEMA = "rag-rulebook/chunk-set/v1"
GENERATOR_VERSION = "fixture-v1"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
PACKET_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-context-packet/script.sh"
DEFAULT_REQUEST = "Build a small governed context packet from generated rulebook chunks."
DEFAULT_TARGET_PATHS = [
    "scripts/02.rag-rulebook/**",
    ".agentic/02.rag-rulebook/**",
]
ALLOWED_CITATION_SOURCE_TYPES = {"source", "rule", "rule-pack", "workflow", "standard", "schema", "plan"}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
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
    "with",
}
TOKEN_ALIASES = {
    "checks": "check",
    "chunks": "chunk",
    "citations": "citation",
    "packets": "packet",
    "rules": "rule",
    "validating": "validate",
    "validated": "validate",
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
  generate-context-packet-fixture/script.sh --generate-current [--pretty]
  generate-context-packet-fixture/script.sh --chunks <path> [--pretty]

Options:
  --request-text <text>   Request text used for deterministic fixture ranking.
  --target-path <glob>    Target path to include in packet routing. Repeatable.
  --max-chunks <n>        Maximum selected chunks. Default: 5. Range: 3-12.

Emits a validated rag-rulebook/context-packet/v1 JSON fixture to stdout. The
command is read-only and does not provide semantic retrieval.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--generate-current", action="store_true")
    parser.add_argument("--chunks")
    parser.add_argument("--request-text", default=DEFAULT_REQUEST)
    parser.add_argument("--target-path", action="append", dest="target_paths")
    parser.add_argument("--max-chunks", type=int, default=5)
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
    if args.chunks == "-":
        print("ERROR: --chunks - is not supported by this shell wrapper; use a saved JSON file.", file=sys.stderr)
        sys.exit(2)
    if args.max_chunks < 3 or args.max_chunks > 12:
        print("ERROR: --max-chunks must be between 3 and 12.", file=sys.stderr)
        sys.exit(2)
    if not args.request_text.strip():
        print("ERROR: --request-text must not be empty.", file=sys.stderr)
        sys.exit(2)
    if not args.target_paths:
        args.target_paths = DEFAULT_TARGET_PATHS
    return args


def repo_path(path: str) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def safe_id(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", ".", str(value or "unknown").lower()).strip(".")
    return cleaned or "unknown"


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
    chunks = data.get("chunks")
    citations = data.get("citations")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunk set must include at least one chunk")
    if not isinstance(citations, list) or not citations:
        raise ValueError("chunk set must include at least one citation")
    return data, raw


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


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


def chunk_haystack(chunk: dict[str, Any]) -> str:
    parts = [
        chunk.get("chunk_id"),
        chunk.get("corpus_id"),
        chunk.get("artifact_id"),
        chunk.get("source_path"),
        chunk.get("content_kind"),
        chunk.get("content"),
        " ".join(list_of_strings(chunk.get("rule_ids"))),
        " ".join(list_of_strings(chunk.get("pack_refs"))),
    ]
    return "\n".join(str(part).lower() for part in parts if part)


def score_chunk(chunk: dict[str, Any], terms: list[str]) -> int:
    haystack = chunk_haystack(chunk)
    score = 0
    for term in terms:
        score += haystack.count(term)
    kind = chunk.get("content_kind")
    term_set = set(terms)
    if kind == "required-check" and term_set.intersection({"check", "validate", "governed"}):
        score += 4
    if kind == "rule" and term_set.intersection({"rule", "architecture", "governed", "harness"}):
        score += 3
    if kind == "artifact-summary" and term_set.intersection({"artifact", "corpus", "source", "rulebook"}):
        score += 2
    if chunk.get("corpus_id") == "corpus.01.harness" and term_set.intersection({"harness", "rulebook", "governed"}):
        score += 2
    return score


def source_rank(chunk: dict[str, Any]) -> int:
    rank = chunk.get("rank")
    return rank if isinstance(rank, int) else 999999


def ranked_chunks(chunks: list[dict[str, Any]], terms: list[str]) -> list[tuple[int, int, str, dict[str, Any]]]:
    ranked = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str):
            continue
        ranked.append((score_chunk(chunk, terms), source_rank(chunk), chunk_id, chunk))
    return sorted(ranked, key=lambda item: (-item[0], item[1], item[2]))


def select_chunks(chunks: list[dict[str, Any]], terms: list[str], max_chunks: int) -> list[tuple[int, dict[str, Any]]]:
    ranked = ranked_chunks(chunks, terms)
    selected: dict[str, tuple[int, dict[str, Any]]] = {}

    def add(item: tuple[int, int, str, dict[str, Any]] | None) -> None:
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


def required_check_description(chunk: dict[str, Any]) -> str:
    content = str(chunk.get("content") or "")
    marker = "Required check:"
    if marker in content:
        return content.split(marker, 1)[1].strip()
    first_line = content.strip().splitlines()[0] if content.strip() else str(chunk.get("chunk_id"))
    return first_line


def citation_ids_for(chunks: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        for citation_id in list_of_strings(chunk.get("citation_ids")):
            if citation_id not in seen:
                ids.append(citation_id)
                seen.add(citation_id)
    return ids


def build_packet(args: argparse.Namespace, chunk_set: dict[str, Any]) -> dict[str, Any]:
    chunks = list_of_dicts(chunk_set.get("chunks"))
    citations = list_of_dicts(chunk_set.get("citations"))
    terms = tokenize(args.request_text)
    selected_pairs = select_chunks(chunks, terms, args.max_chunks)
    selected_source_chunks = [chunk for _score, chunk in selected_pairs]
    if len(selected_source_chunks) < 3:
        raise ValueError("fixture selection requires at least three chunks")

    max_score = max((score for score, _chunk in selected_pairs), default=0)
    selected_chunks: list[dict[str, Any]] = []
    for rank, (score, source_chunk) in enumerate(selected_pairs, start=1):
        chunk = dict(source_chunk)
        chunk["rank"] = rank
        chunk["retrieval_score"] = round(score / max_score, 4) if max_score else 0
        chunk["selection_reason"] = (
            "Deterministic fixture selected this chunk from request terms: "
            + ", ".join(terms[:12])
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

    checks = []
    required_check_chunks = [chunk for chunk in selected_chunks if chunk.get("content_kind") == "required-check"]
    for index, chunk in enumerate(required_check_chunks[:3], start=1):
        checks.append(
            {
                "id": f"check.fixture.{index}.{safe_id(chunk.get('chunk_id'))}",
                "description": required_check_description(chunk),
                "timing": "before-edit",
                "citation_ids": list_of_strings(chunk.get("citation_ids"))[:1] or selected_citation_ids[:1],
            }
        )
    if not checks:
        checks.append(
            {
                "id": "check.fixture.validate-context-packet",
                "description": "Validate the generated context packet before using it as LLM context.",
                "timing": "before-edit",
                "command": "bash scripts/02.rag-rulebook/validate-context-packet/script.sh --packet <packet> --chunks <chunks>",
                "citation_ids": selected_citation_ids[:1],
            }
        )

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
                "chunk_ids": [chunk.get("chunk_id") for chunk in selected_chunks],
                "source_index_id": source_index_id,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "schema": PACKET_SCHEMA,
        "packet_id": f"packet.fixture.{packet_fingerprint}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "request": {
            "raw_text": args.request_text,
            "normalized_summary": "Generate a deterministic validated context-packet fixture from rulebook chunks.",
            "open_artifact_ids": selected_artifact_ids,
        },
        "intent": {
            "id": "intent.rag-rulebook.generate-context-packet-fixture",
            "label": "Generate context packet fixture",
            "mode": "implementation",
            "layer": "02.rag-rulebook",
            "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
            "confidence": 1,
            "source": "deterministic",
            "evidence_ref_ids": selected_citation_ids,
        },
        "routing": {
            "layer": "02.rag-rulebook",
            "mode": "implementation",
            "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
            "status": "ready",
            "task_type": "generate_context_packet_fixture",
            "target_paths": args.target_paths,
            "classification_source": "deterministic-fixture",
        },
        "matched_corpora": [
            {
                "corpus_id": corpus_id,
                "owner_layer": owner_layer(corpus_id),
                "match_reason": "Selected fixture chunks belong to this corpus.",
                "confidence": 1,
            }
            for corpus_id in selected_corpus_ids
        ],
        "matched_rule_packs": [
            {
                "id": pack_ref,
                "corpus_id": next(
                    chunk["corpus_id"]
                    for chunk in selected_chunks
                    if pack_ref in list_of_strings(chunk.get("pack_refs"))
                ),
                "selection_reason": "Selected fixture chunks reference this rule pack.",
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
                "selection_reason": "Selected fixture chunks reference this ruleset artifact.",
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
                "action": "Use unvalidated context-packet fixture output",
                "reason": "The fixture is only trustworthy after selected chunks and citations validate against the source chunk set.",
                "citation_ids": selected_citation_ids[:1],
            }
        ],
        "stop_conditions": [
            {
                "id": "stop.fixture.unresolved-reference",
                "condition": "A selected chunk, citation, check, forbidden action, stop condition, budget, or provenance field cannot be validated.",
                "severity": "blocking",
                "suggested_resolution": "Regenerate the fixture from a valid chunk set or repair the context-packet builder.",
                "citation_ids": selected_citation_ids[:1],
            }
        ],
        "citations": packet_citations,
        "confidence": {
            "overall": 1,
            "retrieval": 1 if max_score else 0.5,
            "routing": 1,
            "notes": [
                "Fixture selection is deterministic and validates before output.",
                "This is not a semantic retrieval result.",
            ],
        },
        "gaps": [],
        "budgets": {
            "max_context_tokens": selected_context_tokens + 1000,
            "selected_context_tokens": selected_context_tokens,
            "trim_policy": "deterministic-first",
        },
        "provenance": {
            "service_version": GENERATOR_VERSION,
            "corpus_index_versions": [
                {
                    "corpus_id": corpus_id,
                    "index_version": source_index_id,
                    "content_hash": source_index_hash,
                }
                for corpus_id in selected_corpus_ids
            ],
            "retrieval_order": [
                "tokenize request text",
                "score generated chunks deterministically",
                "require required-check, rule, and artifact-summary coverage where available",
                "validate packet against chunk set before output",
            ],
            "generator": "scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh",
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
        chunk_set, chunk_set_raw = load_chunk_set(args)
        packet = build_packet(args, chunk_set)
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

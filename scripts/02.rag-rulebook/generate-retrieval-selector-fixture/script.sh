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
#   purpose: Generate a deterministic retrieval-selector fixture packet from policy, recognition sources, prompt context, session continuity, and chunks.
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
import os
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
COMPILED_POLICY_SCHEMA = "rag-rulebook/compiled-retrieval-policy/v1"
POLICY_PACK_PATH = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml"
RECOGNITION_ROOT = ".agentic/02.rag-rulebook/recognition-sources"
CANDIDATE_ROOT = ".agentic/02.rag-rulebook/recognition-candidates"
CORPUS_GAP_ROOT = ".agentic/02.rag-rulebook/corpus-gaps"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
PACKET_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-context-packet/script.sh"
POLICY_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
RECOGNITION_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-recognition-sources/script.sh"
CANDIDATE_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-recognition-candidates/script.sh"
COMPILED_POLICY_SCRIPT = "scripts/02.rag-rulebook/compile-retrieval-policy/script.sh"
DEFAULT_REQUEST = "Build the first deterministic RAG rulebook retrieval selector fixture."
DEFAULT_SESSION_LAYER = "unknown"
DEFAULT_SESSION_MODE = "unknown"
DEFAULT_SESSION_WORKFLOW = "unknown"
MAX_SESSION_ID_CHARS = 160
MAX_SESSION_BRANCH_CHARS = 240
MAX_SESSION_WORKTREE_CHARS = 512
MAX_PACKET_ID_CHARS = 200
MAX_ROUTING_SUMMARY_CHARS = 500
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._:@/-]*$")
SAFE_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/@-]*$")
SAFE_PACKET_ID_RE = re.compile(r"^[A-Za-z0-9._:-]*$")
PATH_LIKE_SPAN_RE = re.compile(r"(?<![A-Za-z0-9._/@-])(?:[A-Za-z0-9._@-]+/)+[A-Za-z0-9._@-]+(?![A-Za-z0-9._/@-])")
EXAMPLE_INTRO_RE = re.compile(
    r"(?im)(?:^|\b)(?:e\.g\.|i\.e\.|for example|for instance|example|examples|such as)\s*:?"
)
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
DEFAULT_WORKFLOW_BY_LAYER = {
    "00.chat": ".agentic/00.chat/workflows/chat-start.md",
    "01.harness": ".agentic/01.harness/workflows/change-harness.md",
    "02.rag-rulebook": ".agentic/02.rag-rulebook/workflows/default.md",
    "03.product": ".agentic/product/workflows/default.md",
    "04.deploy": ".agentic/aws/workflows/plan-aws-change.md",
    "05.education": ".agentic/education/workflows/create-educational-resource.md",
    "06.shared": ".agentic/shared/workflows/change-shared-process.md",
}
DEPLOY_EXECUTION_WORKFLOW = ".agentic/aws/workflows/execute-approved-aws-change.md"
PROMPT_ROUTE_INPUTS = {"prompt"}
PROMPT_EXAMPLE_INPUT = "prompt-example"
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
    "artefact": "artifact",
    "artefacts": "artifact",
    "artifacts": "artifact",
    "checks": "check",
    "chunks": "chunk",
    "corpora": "corpus",
    "headers": "header",
    "harnes": "harness",
    "indexed": "index",
    "indexes": "index",
    "indexing": "index",
    "packets": "packet",
    "policies": "policy",
    "recognised": "recognize",
    "recognises": "recognize",
    "recognition": "recognize",
    "relevant": "right",
    "rules": "rule",
    "used": "use",
    "uses": "use",
    "using": "use",
    "validated": "validate",
    "validating": "validate",
    "validation": "validate",
    "validator": "validate",
}

QUESTION_FRAMES = (
    {
        "frame_id": "question-frame.indexed-for-rag",
        "summary": "Prompt asks how harness artifacts become indexed RAG material.",
        "required_terms": ["index", "rag"],
        "any_terms": ["harness", "artifact"],
        "retrieval_roles": [
            "artifact-index-builder",
            "recognition-source-generator",
            "rulebook-index-builder",
            "chunk-generator",
            "runtime-builder",
        ],
    },
    {
        "frame_id": "question-frame.rag-index-selection",
        "summary": "Prompt asks how RAG uses the index to select relevant content.",
        "required_terms": ["rag", "index", "use"],
        "any_terms": ["find", "right", "content", "select", "rank", "retrieve"],
        "retrieval_roles": [
            "runtime-query",
            "retrieval-selector",
            "retrieval-policy-compiler",
            "request-context-policy",
            "evidence-bundle-policy",
            "rulebook-index-builder",
        ],
    },
)

def repo_root() -> Path:
    override = os.environ.get("RAG_REPO_ROOT")
    if override:
        root = Path(override).resolve()
        assert_repo_root(root)
        return root
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    root = Path(result.stdout.strip())
    assert_repo_root(root)
    return root


def assert_repo_root(root: Path) -> None:
    markers = [
        "package.json",
        ".agentic/02.rag-rulebook/service",
        "scripts/02.rag-rulebook",
    ]
    for marker in markers:
        if not (root / marker).exists():
            raise SystemExit(f"ERROR: RAG repo root is missing required marker: {marker}")


ROOT = repo_root()


def usage() -> str:
    return """Usage:
  generate-retrieval-selector-fixture/script.sh --generate-current [--pretty]
  generate-retrieval-selector-fixture/script.sh --chunks <path> [--pretty]

Options:
  --request-text <text>       Prompt text used for recognition and ranking.
  --session-id <id>           Chat/session ID for provenance.
  --session-branch <branch>   Chat/session branch for provenance.
  --session-worktree <path>   Chat/session worktree for provenance.
  --session-layer <layer>     Legacy session routing hint. Default: unknown.
  --session-mode <mode>       Legacy session routing hint. Default: unknown.
  --session-workflow <path>   Legacy session routing hint. Default: unknown.
  --previous-packet-id <id>   Previous context packet used as continuity evidence.
  --previous-routing-summary <text>
                              Previous packet routing summary.
  --trust-session-routing     Treat supplied session layer/mode/workflow as
                              trusted routing hints. Use only after governed
                              session resolution verifies ownership.
  --max-chunks <n>            Maximum selected chunks. Default: 6. Range: 3-12.
  --compiled-policy <path>    Compiled retrieval policy JSON. If omitted, a
                              temporary current compiled policy is generated.

Emits a validated rag-rulebook/context-packet/v1 JSON fixture to stdout. The
command is read-only and performs deterministic fixture selection only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--generate-current", action="store_true")
    parser.add_argument("--chunks")
    parser.add_argument("--request-text", default=DEFAULT_REQUEST)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--session-branch", default="")
    parser.add_argument("--session-worktree", default="")
    parser.add_argument("--session-layer", default=DEFAULT_SESSION_LAYER)
    parser.add_argument("--session-mode", default=DEFAULT_SESSION_MODE)
    parser.add_argument("--session-workflow", default=DEFAULT_SESSION_WORKFLOW)
    parser.add_argument("--previous-packet-id", default="")
    parser.add_argument("--previous-routing-summary", default="")
    parser.add_argument("--trust-session-routing", action="store_true")
    parser.add_argument("--max-chunks", type=int, default=6)
    parser.add_argument("--compiled-policy")
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
    validate_session_context_args(args)
    return args


def has_control_chars(value: str) -> bool:
    return any(ord(char) < 32 or ord(char) == 127 for char in value)


def validate_optional_string(value: str, *, name: str, max_length: int, pattern: re.Pattern[str] | None = None) -> None:
    if not value:
        return
    if len(value) > max_length or has_control_chars(value):
        raise SystemExit(f"ERROR: {name} is too long or contains control characters.")
    if pattern is not None and not pattern.match(value):
        raise SystemExit(f"ERROR: {name} contains unsupported characters.")


def validate_session_context_args(args: argparse.Namespace) -> None:
    validate_optional_string(args.session_id, name="--session-id", max_length=MAX_SESSION_ID_CHARS, pattern=SAFE_ID_RE)
    validate_optional_string(args.session_branch, name="--session-branch", max_length=MAX_SESSION_BRANCH_CHARS, pattern=SAFE_BRANCH_RE)
    validate_optional_string(args.session_layer, name="--session-layer", max_length=80, pattern=SAFE_ID_RE)
    validate_optional_string(args.session_mode, name="--session-mode", max_length=80, pattern=SAFE_ID_RE)
    validate_optional_string(args.session_workflow, name="--session-workflow", max_length=300, pattern=SAFE_BRANCH_RE)
    validate_optional_string(args.previous_packet_id, name="--previous-packet-id", max_length=MAX_PACKET_ID_CHARS, pattern=SAFE_PACKET_ID_RE)
    validate_optional_string(args.previous_routing_summary, name="--previous-routing-summary", max_length=MAX_ROUTING_SUMMARY_CHARS)
    if args.session_worktree:
        validate_optional_string(args.session_worktree, name="--session-worktree", max_length=MAX_SESSION_WORKTREE_CHARS)
        path = Path(args.session_worktree)
        if not path.is_absolute() or ".." in path.parts:
            raise SystemExit("ERROR: --session-worktree must be an absolute path without parent traversal.")
    if args.trust_session_routing:
        missing = [
            option
            for option, value in [
                ("--session-id", args.session_id),
                ("--session-branch", args.session_branch),
                ("--session-worktree", args.session_worktree),
                ("--session-layer", args.session_layer if args.session_layer != "unknown" else ""),
                ("--session-mode", args.session_mode if args.session_mode != "unknown" else ""),
                ("--session-workflow", args.session_workflow if args.session_workflow != "unknown" else ""),
            ]
            if not value
        ]
        if missing:
            raise SystemExit(
                "ERROR: --trust-session-routing requires governed lifecycle proof fields: "
                + ", ".join(missing)
                + "."
            )


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


def load_compiled_policy(path: str | None) -> dict[str, Any]:
    if path:
        compiled = json.loads(repo_path(path).read_text(encoding="utf-8"))
        if not isinstance(compiled, dict):
            raise ValueError("compiled retrieval policy JSON must be an object")
    else:
        compiled = run_json(["bash", COMPILED_POLICY_SCRIPT, "--current"])
    if compiled.get("schema") != COMPILED_POLICY_SCHEMA:
        raise ValueError(f"compiled retrieval policy schema must be {COMPILED_POLICY_SCHEMA}")
    return compiled


def compiled_policy_pack(compiled_policy: dict[str, Any]) -> dict[str, Any]:
    policy_pack = compiled_policy.get("policy_pack")
    return policy_pack if isinstance(policy_pack, dict) else {}


def compiled_policy_report(compiled_policy: dict[str, Any]) -> dict[str, Any]:
    provenance = dict_value(compiled_policy.get("provenance"))
    report = provenance.get("policy_report")
    return report if isinstance(report, dict) else {"ok": True, "counts": {}}


def compiled_recognition_report(compiled_policy: dict[str, Any]) -> dict[str, Any]:
    provenance = dict_value(compiled_policy.get("provenance"))
    report = provenance.get("recognition_report")
    return report if isinstance(report, dict) else {"ok": True, "counts": {}}


def compiled_recognition_sources(compiled_policy: dict[str, Any]) -> list[dict[str, Any]]:
    recognition_sources = dict_value(compiled_policy.get("recognition_sources"))
    sources = list_of_dicts(recognition_sources.get("sources"))
    if not sources:
        raise ValueError("compiled retrieval policy has no recognition sources")
    return sources


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


def compiled_user_intents(compiled_policy: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(compiled_policy.get("user_intents"))


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


def exact_match_spans(term: str, text: str) -> list[tuple[int, int]]:
    term_lower = term.lower()
    text_lower = text.lower()
    if not term_lower:
        return []
    if "/" in term_lower or "." in term_lower or "-" in term_lower:
        spans: list[tuple[int, int]] = []
        start = 0
        while True:
            index = text_lower.find(term_lower, start)
            if index < 0:
                return spans
            spans.append((index, index + len(term_lower)))
            start = index + 1
    return [
        match.span()
        for match in re.finditer(rf"(?<![a-z0-9]){re.escape(term_lower)}(?![a-z0-9])", text_lower)
    ]


def term_matches_only_inside_path_spans(term: str, text: str) -> bool:
    match_spans = exact_match_spans(term, text)
    if not match_spans:
        return False
    path_spans = [match.span() for match in PATH_LIKE_SPAN_RE.finditer(text)]
    if not path_spans:
        return False
    return all(
        any(path_start <= match_start and match_end <= path_end for path_start, path_end in path_spans)
        for match_start, match_end in match_spans
    )


def line_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        start = cursor
        cursor += len(line)
        spans.append((start, cursor, line.rstrip("\r\n")))
    if text and not text.endswith(("\n", "\r")):
        return spans
    return spans


def line_index_for_offset(lines: list[tuple[int, int, str]], offset: int) -> int:
    for index, (start, end, _line) in enumerate(lines):
        if start <= offset < end:
            return index
    return max(0, len(lines) - 1)


def illustrative_example_spans(text: str) -> list[tuple[int, int]]:
    lines = line_spans(text)
    if not lines:
        return []
    spans: list[tuple[int, int]] = []
    for match in EXAMPLE_INTRO_RE.finditer(text):
        line_index = line_index_for_offset(lines, match.start())
        start = lines[line_index][0]
        end = lines[line_index][1]
        saw_content = bool(lines[line_index][2].strip())
        blank_after_content = 0
        for next_index in range(line_index + 1, len(lines)):
            _line_start, line_end, line_text = lines[next_index]
            stripped = line_text.strip()
            if not stripped:
                if saw_content:
                    blank_after_content += 1
                    if blank_after_content >= 2:
                        break
                end = line_end
                continue
            if saw_content and blank_after_content >= 1 and not line_text.startswith((" ", "\t", "#", "-", "`")):
                break
            saw_content = True
            blank_after_content = 0
            end = line_end
        spans.append((start, end))
    return spans


def spans_inside(inner_spans: list[tuple[int, int]], outer_spans: list[tuple[int, int]]) -> bool:
    if not inner_spans:
        return False
    return all(
        any(outer_start <= inner_start and inner_end <= outer_end for outer_start, outer_end in outer_spans)
        for inner_start, inner_end in inner_spans
    )


def remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return text
    parts: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        if start > cursor:
            parts.append(text[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(text):
        parts.append(text[cursor:])
    return "\n".join(part.strip("\n") for part in parts if part.strip("\n"))


def prompt_text_for_broad_terms(text: str) -> str:
    return remove_spans(text, illustrative_example_spans(text))


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
    match_text = prompt_text_for_broad_terms(request_text)
    for candidate in candidates:
        status = candidate.get("status")
        if status not in {"needs-review", "deferred"}:
            continue
        observed = candidate.get("observed") if isinstance(candidate.get("observed"), dict) else {}
        term = str(observed.get("term") or "").strip()
        if not term or not simple_exact_match(term, match_text):
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
    match_text = prompt_text_for_broad_terms(request_text)
    for term in list_of_strings(gap.get("match_terms")):
        if simple_exact_match(term, match_text):
            return True

    related_candidate = dict_value(gap.get("related_candidate"))
    candidate_id = related_candidate.get("candidate_id")
    candidate = candidates_by_id.get(str(candidate_id)) if candidate_id else None
    observed = dict_value(candidate.get("observed")) if candidate else {}
    candidate_term = str(observed.get("term") or "").strip()
    if candidate_term and simple_exact_match(candidate_term, match_text):
        return True

    observed_prompt = str(gap.get("observed_prompt") or "").strip()
    return bool(observed_prompt and observed_prompt.lower() == match_text.strip().lower())


def matched_intent_ids(recognition_matches: list[dict[str, Any]], *, prompt_only: bool = True) -> set[str]:
    ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "intent-form" and isinstance(match.get("canonical_id"), str)
        and (not prompt_only or match.get("matched_input") == "prompt")
    }
    if prompt_only and not ids:
        return matched_intent_ids(recognition_matches, prompt_only=False)
    return ids


def matched_user_intent_ids(recognition_matches: list[dict[str, Any]]) -> set[str]:
    return {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "user-intent"
        and isinstance(match.get("canonical_id"), str)
        and match.get("matched_input") == "prompt"
    }


def resolve_intent_id(recognition_matches: list[dict[str, Any]], compiled_policy: dict[str, Any]) -> str:
    intent_ids = matched_intent_ids(recognition_matches)
    intent_resolution = dict_value(compiled_policy.get("intent_resolution"))
    precedence = list_of_strings(intent_resolution.get("precedence"))
    default_intent_id = str(intent_resolution.get("default_intent_id") or "intent.context.retrieve")
    for intent_id in precedence:
        if intent_id in intent_ids:
            return intent_id
    return default_intent_id


def intent_label(compiled_policy: dict[str, Any], intent_id: str) -> str:
    labels = dict_value(dict_value(compiled_policy.get("intent_resolution")).get("labels"))
    label = labels.get(intent_id)
    return str(label) if isinstance(label, str) else intent_id


def prompt_route_matches(recognition_matches: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    return [
        match
        for match in recognition_matches
        if match.get("category") == category and match.get("matched_input") in PROMPT_ROUTE_INPUTS
    ]


def most_common(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        if not value or value == "mixed":
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return "unknown"
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def first_known(values: list[str]) -> str:
    for value in values:
        if value and value not in {"unknown", "mixed"}:
            return value
    return "unknown"


def layer_from_path(path: str) -> str:
    if path.startswith(".agentic/00.chat/") or path.startswith("docs/00.chat/"):
        return "00.chat"
    if path.startswith(".agentic/01.harness/") or path.startswith("docs/01.harness/"):
        return "01.harness"
    if path.startswith(".agentic/02.rag-rulebook/") or path.startswith("docs/02.rag-rulebook/"):
        return "02.rag-rulebook"
    if path.startswith("docs/harness/architecture/"):
        return "03.product"
    if path.startswith(".agentic/product/") or path.startswith("docs/03.product/") or "/03.product/" in path:
        return "03.product"
    if path.startswith(".agentic/aws/") or path.startswith("docs/04.deploy/") or "/04.deploy/" in path:
        return "04.deploy"
    if path.startswith(".agentic/education/") or path.startswith("docs/05.education/") or "/05.education/" in path:
        return "05.education"
    if path.startswith(".agentic/shared/") or path.startswith("docs/06.shared/") or "/06.shared/" in path:
        return "06.shared"
    return "unknown"


def mode_from_intent(intent_id: str) -> str:
    if intent_id == "intent.deploy.execution":
        return "execution"
    if intent_id in {"intent.git.commit", "intent.implementation.request"}:
        return "implementation"
    return "discovery"


def workflow_from_prompt_match(matches: list[dict[str, Any]], selected_layer: str) -> str:
    def compatible_path(match: dict[str, Any]) -> str:
        path = str(match.get("evidence_path") or match.get("canonical_id") or "")
        if not path.endswith(".md"):
            return ""
        if selected_layer == "unknown" or layer_from_path(path) == selected_layer:
            return path
        return ""

    prompt_paths = [
        compatible_path(match)
        for match in matches
        if match.get("matched_input") == "prompt"
    ]
    return first_known(prompt_paths)


def prompt_exact_path_layers(recognition_matches: list[dict[str, Any]]) -> list[str]:
    exact_path_categories = {
        "artifact-id",
        "file-path",
        "rule-id",
        "rule-pack-id",
        "source-material-id",
    }
    layers = []
    for match in recognition_matches:
        if match.get("matched_input") not in PROMPT_ROUTE_INPUTS:
            continue
        if match.get("category") not in exact_path_categories:
            continue
        layer = layer_from_path(str(match.get("evidence_path") or ""))
        if layer != "unknown":
            layers.append(layer)
    return layers


def resolve_prompt_route(recognition_matches: list[dict[str, Any]], resolved_intent_id: str, request_text: str) -> dict[str, str]:
    corpus_layers = [
        owner_layer(str(match.get("canonical_id")))
        for match in prompt_route_matches(recognition_matches, "corpus-id")
        if isinstance(match.get("canonical_id"), str)
    ]
    prompt_layer_values = [
        str(match.get("canonical_id"))
        for match in prompt_route_matches(recognition_matches, "layer-name")
        if isinstance(match.get("canonical_id"), str)
        and match.get("matched_input") == "prompt"
    ]
    exact_path_layers = prompt_exact_path_layers(recognition_matches)
    workflow_matches = prompt_route_matches(recognition_matches, "workflow-name")
    workflow_layers = []
    for match in workflow_matches:
        path_layer = layer_from_path(str(match.get("evidence_path") or ""))
        if path_layer != "unknown":
            workflow_layers.append(path_layer)
    deploy_intent_present = any(
        intent_id.startswith("intent.deploy.")
        for intent_id in matched_intent_ids(recognition_matches, prompt_only=False)
    )
    deploy_word_present = re.search(r"\bdeploy(?:ment)?\b", request_text, flags=re.IGNORECASE) is not None
    layer = "unknown"
    if (deploy_intent_present or deploy_word_present) and "04.deploy" in prompt_layer_values:
        layer = "04.deploy"
    if layer == "unknown":
        layer = first_known(corpus_layers) or "unknown"
    if layer == "unknown":
        layer = most_common(exact_path_layers)
    if layer == "unknown":
        layer = most_common(prompt_layer_values)
    if layer == "02.rag-rulebook" and re.search(r"\bdeploy(?:ment)?\b", request_text, flags=re.IGNORECASE):
        layer = "04.deploy"
    if layer == "unknown":
        layer = most_common(workflow_layers)

    mode_values = []
    for match in prompt_route_matches(recognition_matches, "mode-name"):
        canonical = str(match.get("canonical_id") or "")
        mode_values.append(canonical.split(":", 1)[1] if ":" in canonical else canonical)
    mode = most_common(mode_values)
    if mode == "unknown" and (layer != "unknown" or resolved_intent_id != "intent.context.retrieve"):
        mode = mode_from_intent(resolved_intent_id)
    if layer == "04.deploy" and mode == "discovery":
        mode = "planning"

    workflow = workflow_from_prompt_match(workflow_matches, layer)
    if workflow == "unknown" and layer == "04.deploy" and mode == "execution":
        workflow = DEPLOY_EXECUTION_WORKFLOW
    elif workflow == "unknown" and layer in DEFAULT_WORKFLOW_BY_LAYER:
        workflow = DEFAULT_WORKFLOW_BY_LAYER[layer]

    return {"layer": layer, "mode": mode, "workflow": workflow}


def corpus_gap_blocking(
    gap: dict[str, Any],
    recognition_matches: list[dict[str, Any]],
    compiled_policy: dict[str, Any],
) -> bool:
    behavior = dict_value(gap.get("local_query_behavior"))
    blocking_by_intent = dict_value(behavior.get("blocking_by_intent"))
    resolved_intent_id = resolve_intent_id(recognition_matches, compiled_policy)
    if isinstance(blocking_by_intent.get(resolved_intent_id), bool):
        return bool(blocking_by_intent[resolved_intent_id])
    return bool(behavior.get("blocking") is True)


def corpus_gap_records_gaps(
    corpus_gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    recognition_matches: list[dict[str, Any]],
    request_text: str,
    compiled_policy: dict[str, Any],
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
        blocking = corpus_gap_blocking(gap, recognition_matches, compiled_policy)
        detail_required_chunk_ids: list[str] = []
        if blocking:
            for detail in list_of_dicts(gap.get("execution_blocking_gaps")):
                for chunk_id in list_of_strings(detail.get("required_chunk_ids")):
                    if chunk_id not in detail_required_chunk_ids:
                        detail_required_chunk_ids.append(chunk_id)
        seen.add(gap_id)
        target_corpus_id = str(gap.get("target_corpus_id") or "").strip()
        summary = str(gap.get("summary") or "A required corpus coverage gap is still open.").strip()
        description = summary
        if target_corpus_id:
            description += f" Target corpus: {target_corpus_id}."
        main_record = {
            "id": gap_id,
            "type": "missing-corpus",
            "description": description,
            "blocking": blocking,
            "suggested_resolution": str(
                gap.get("suggested_resolution")
                or "Add governed source material, structured rules, chunks, and selector evaluation proof before treating this coverage as available."
            ),
        }
        if detail_required_chunk_ids:
            main_record["required_evidence_chunk_ids"] = detail_required_chunk_ids
        emitted.append(main_record)
        if not blocking:
            continue
        for detail in list_of_dicts(gap.get("execution_blocking_gaps")):
            detail_id = str(detail.get("id") or "").strip()
            if not detail_id or detail_id in seen:
                continue
            seen.add(detail_id)
            emitted.append(
                {
                    "id": detail_id,
                    "type": str(detail.get("type") or "missing-validator"),
                    "description": str(
                        detail.get("description")
                        or "Deploy execution is blocked because a required deploy-proof detail is missing."
                    ),
                    "blocking": True,
                    "required_evidence_chunk_ids": list_of_strings(detail.get("required_chunk_ids")),
                    "suggested_resolution": str(
                        detail.get("suggested_resolution")
                        or gap.get("suggested_resolution")
                        or "Add governed deploy proof before treating this request as executable."
                    ),
                }
            )
    return emitted


def matched_corpus_gap_required_chunk_ids(
    corpus_gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    recognition_matches: list[dict[str, Any]],
    request_text: str,
    compiled_policy: dict[str, Any],
) -> list[str]:
    chunk_ids: list[str] = []
    seen: set[str] = set()
    candidates_by_id = {
        str(candidate.get("candidate_id")): candidate
        for candidate in candidates
        if isinstance(candidate.get("candidate_id"), str)
    }
    for gap in corpus_gaps:
        if gap.get("status") not in {"open", "planned", "in-progress"}:
            continue
        if not corpus_gap_matches_request(gap, candidates_by_id, request_text):
            continue
        if not corpus_gap_blocking(gap, recognition_matches, compiled_policy):
            continue
        for detail in list_of_dicts(gap.get("execution_blocking_gaps")):
            for chunk_id in list_of_strings(detail.get("required_chunk_ids")):
                if chunk_id in seen:
                    continue
                seen.add(chunk_id)
                chunk_ids.append(chunk_id)
    return chunk_ids


def matched_candidate_evidence_paths(candidates: list[dict[str, Any]], request_text: str) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    match_text = prompt_text_for_broad_terms(request_text)
    for candidate in candidates:
        status = candidate.get("status")
        if status not in {"needs-review", "deferred", "accepted"}:
            continue
        observed = candidate.get("observed") if isinstance(candidate.get("observed"), dict) else {}
        term = str(observed.get("term") or "").strip()
        if not term or not simple_exact_match(term, match_text):
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


def compiled_evidence_bundles(compiled_policy: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    bundles_by_category: dict[str, list[dict[str, Any]]] = {}
    for bundle in list_of_dicts(compiled_policy.get("evidence_bundles")):
        category_id = bundle.get("question_category_id")
        if not isinstance(category_id, str):
            continue
        bundles_by_category.setdefault(category_id, [])
        bundles_by_category[category_id].append(bundle)
    return bundles_by_category


def evidence_bundle_applies(bundle: dict[str, Any], user_intent_ids: set[str]) -> bool:
    when = dict_value(bundle.get("when"))
    user_intent_id = when.get("user_intent_id")
    if isinstance(user_intent_id, str) and user_intent_id:
        return user_intent_id in user_intent_ids
    return True


def matched_evidence_bundle_source_paths(
    recognition_matches: list[dict[str, Any]],
    compiled_policy: dict[str, Any],
) -> list[str]:
    category_ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "question-category" and isinstance(match.get("canonical_id"), str)
    }
    family_ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "evidence-family" and isinstance(match.get("canonical_id"), str)
    }
    user_intent_ids = matched_user_intent_ids(recognition_matches)
    paths: list[str] = []
    seen: set[str] = set()
    evidence_bundles = compiled_evidence_bundles(compiled_policy)
    for category_id in sorted(category_ids):
        for bundle in evidence_bundles.get(category_id, []):
            if not evidence_bundle_applies(bundle, user_intent_ids):
                continue
            for source_path in list_of_strings(bundle.get("always_source_paths")):
                if source_path in seen or not repo_path(source_path).is_file():
                    continue
                seen.add(source_path)
                paths.append(source_path)
            family_source_paths = dict_value(bundle.get("family_source_paths"))
            for family_id in sorted(family_ids):
                source_path = family_source_paths.get(family_id)
                if not isinstance(source_path, str) or source_path in seen:
                    continue
                if not repo_path(source_path).is_file():
                    continue
                seen.add(source_path)
                paths.append(source_path)
    return paths


def question_frame_matches(prompt_terms: list[str]) -> list[dict[str, Any]]:
    term_set = set(prompt_terms)
    matches: list[dict[str, Any]] = []
    for frame in QUESTION_FRAMES:
        required_terms = list_of_strings(frame.get("required_terms"))
        any_terms = list_of_strings(frame.get("any_terms"))
        if not all(term in term_set for term in required_terms):
            continue
        if any_terms and not term_set.intersection(any_terms):
            continue
        matched_terms = sorted(term_set.intersection(required_terms + any_terms))
        matches.append(
            {
                "frame_id": frame.get("frame_id"),
                "summary": frame.get("summary"),
                "matched_terms": matched_terms,
                "retrieval_roles": list_of_strings(frame.get("retrieval_roles")),
            }
        )
    return matches


def matched_profile_evidence(
    chunks: list[dict[str, Any]],
    question_frames: list[dict[str, Any]],
) -> dict[str, list[str]]:
    role_order: list[str] = []
    for frame in question_frames:
        for role in list_of_strings(frame.get("retrieval_roles")):
            if role not in role_order:
                role_order.append(role)

    chunks_by_role: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        if chunk.get("content_kind") != "retrieval-profile":
            continue
        profile = dict_value(chunk.get("retrieval_profile"))
        for role in list_of_strings(profile.get("retrieval_roles")):
            chunks_by_role.setdefault(role, chunk)

    chunk_ids: list[str] = []
    source_paths: list[str] = []
    seen_chunks: set[str] = set()
    seen_paths: set[str] = set()
    for role in role_order:
        chunk = chunks_by_role.get(role)
        if not chunk:
            continue
        chunk_id = chunk.get("chunk_id")
        if isinstance(chunk_id, str) and chunk_id not in seen_chunks:
            seen_chunks.add(chunk_id)
            chunk_ids.append(chunk_id)
        source_path = chunk.get("source_path")
        if isinstance(source_path, str) and source_path not in seen_paths and repo_path(source_path).is_file():
            seen_paths.add(source_path)
            source_paths.append(source_path)

    return {
        "chunk_ids": chunk_ids,
        "source_paths": source_paths,
    }


def evidence_bundle_gaps(
    recognition_matches: list[dict[str, Any]],
    selected_chunks: list[dict[str, Any]],
    compiled_policy: dict[str, Any],
) -> list[dict[str, Any]]:
    category_ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "question-category" and isinstance(match.get("canonical_id"), str)
    }
    family_ids = {
        str(match.get("canonical_id"))
        for match in recognition_matches
        if match.get("category") == "evidence-family" and isinstance(match.get("canonical_id"), str)
    }
    user_intent_ids = matched_user_intent_ids(recognition_matches)
    selected_source_paths = {
        str(chunk.get("source_path"))
        for chunk in selected_chunks
        if isinstance(chunk.get("source_path"), str)
    }
    gaps: list[dict[str, Any]] = []
    evidence_bundles = compiled_evidence_bundles(compiled_policy)
    for category_id in sorted(category_ids):
        bundles = [
            bundle
            for bundle in evidence_bundles.get(category_id, [])
            if evidence_bundle_applies(bundle, user_intent_ids)
        ]
        if not bundles:
            gaps.append(
                {
                    "id": f"gap.selector-fixture.no-evidence-bundle.{safe_id(category_id)}",
                    "type": "missing-evidence",
                    "description": f"Question category {category_id} matched, but no evidence bundle is defined.",
                    "blocking": False,
                    "suggested_resolution": "Define an evidence bundle or downgrade the question-category recognition term.",
                }
            )
            continue
        for bundle in bundles:
            bundle_id = str(bundle.get("bundle_id") or category_id)
            expected_paths: list[str] = []
            for source_path in list_of_strings(bundle.get("always_source_paths")):
                expected_paths.append(source_path)
            family_source_paths = dict_value(bundle.get("family_source_paths"))
            for family_id in sorted(family_ids):
                source_path = family_source_paths.get(family_id)
                if isinstance(source_path, str):
                    expected_paths.append(source_path)
            expected_paths = sorted(set(path for path in expected_paths if repo_path(path).is_file()))
            if not expected_paths:
                gaps.append(
                    {
                        "id": f"gap.selector-fixture.no-evidence-family.{safe_id(bundle_id)}",
                        "type": "missing-evidence",
                        "description": f"Evidence bundle {bundle_id} resolved no expected evidence families.",
                        "blocking": False,
                        "suggested_resolution": "Add evidence-family terms or exact paths for this question category.",
                    }
                )
                continue
            missing_paths = [path for path in expected_paths if path not in selected_source_paths]
            if missing_paths:
                gaps.append(
                    {
                        "id": f"gap.selector-fixture.missing-evidence-bundle.{safe_id(bundle_id)}",
                        "type": "missing-evidence",
                        "description": (
                            f"Evidence bundle {bundle_id} expected evidence that was not selected: "
                            + ", ".join(missing_paths)
                        ),
                        "blocking": False,
                        "suggested_resolution": "Add the expected evidence paths to required source selection or tune ranking/trimming.",
                    }
                )
    return gaps


def match_recognition_terms(
    sources: list[dict[str, Any]],
    request_text: str,
    session_text: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    example_spans = illustrative_example_spans(request_text)
    for source in sources:
        source_id = str(source.get("source_id"))
        for term in list_of_dicts(source.get("terms")):
            raw_term = str(term.get("term") or "").strip()
            if not raw_term:
                continue
            category = str(term.get("category") or "")
            lookup_terms = [raw_term] + list_of_strings(term.get("aliases"))
            for lookup_term in lookup_terms:
                matched_inputs: list[str] = []
                request_match_spans = exact_match_spans(lookup_term, request_text)
                example_match = spans_inside(request_match_spans, example_spans)
                prompt_match = bool(request_match_spans) and not example_match
                if prompt_match:
                    if not (category == "layer-name" and term_matches_only_inside_path_spans(lookup_term, request_text)):
                        matched_inputs.append("prompt")
                if example_match:
                    matched_inputs.append(PROMPT_EXAMPLE_INPUT)
                if simple_exact_match(lookup_term, session_text):
                    if not (category == "layer-name" and term_matches_only_inside_path_spans(lookup_term, session_text)):
                        matched_inputs.append("session-metadata")
                for matched_input in matched_inputs:
                    key = (source_id, lookup_term.lower(), category, matched_input)
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


def match_user_intents(compiled_policy: dict[str, Any], request_text: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    match_text = prompt_text_for_broad_terms(request_text)
    for intent in compiled_user_intents(compiled_policy):
        intent_id = str(intent.get("intent_id") or "").strip()
        if not intent_id:
            continue
        for alias in list_of_strings(intent.get("aliases")):
            if not simple_exact_match(alias, match_text):
                continue
            key = (intent_id, alias.lower())
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                {
                    "source_id": "policy.user-intents",
                    "term": alias,
                    "category": "user-intent",
                    "canonical_id": intent_id,
                    "match_type": "alias",
                    "matched_input": "prompt",
                    "evidence_path": ".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/user-intents.yml",
                    "confidence_weight": intent.get("confidence_weight", 0.7),
                    "evidence_bias": list_of_strings(intent.get("evidence_bias")),
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
        chunk.get("rule_title"),
        chunk.get("rule_summary"),
        chunk.get("rule_must_text"),
        chunk.get("rule_must_not_text"),
        chunk.get("rule_agent_guidance"),
        chunk.get("content"),
        " ".join(list_of_strings(chunk.get("rule_ids"))),
        " ".join(list_of_strings(chunk.get("pack_refs"))),
    ]
    return "\n".join(str(part).lower() for part in parts if part)


RERANK_STOP_TERMS = STOP_WORDS | {
    "category",
    "concern",
    "evidence",
    "explain",
    "family",
    "implementation",
    "implemented",
    "layer",
    "platform",
    "policy",
    "question",
    "repo",
    "rule",
    "rules",
    "work",
    "works",
}


def rerank_terms(prompt_terms: list[str], recognition_matches: list[dict[str, Any]]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        for token in tokenize(raw.replace(".", " ").replace("-", " ")):
            if token in RERANK_STOP_TERMS or token in seen:
                continue
            seen.add(token)
            terms.append(token)

    for term in prompt_terms:
        add(term)
    for match in recognition_matches:
        if match.get("category") != "evidence-family":
            continue
        if match.get("matched_input") == PROMPT_EXAMPLE_INPUT:
            continue
        add(str(match.get("term") or ""))
    return terms


def count_term(text: str, term: str) -> int:
    if not text or not term:
        return 0
    if " " in term:
        return text.count(term)
    return len(re.findall(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text))


def field_score(text: Any, terms: list[str], weight: float) -> float:
    value = str(text or "").lower()
    return sum(count_term(value, term) * weight for term in terms)


def intra_source_score(chunk: dict[str, Any], prompt_terms: list[str], recognition_matches: list[dict[str, Any]]) -> float:
    if chunk.get("content_kind") != "rule":
        return 0.0
    terms = rerank_terms(prompt_terms, recognition_matches)
    if not terms:
        return 0.0
    score = 0.0
    score += field_score(" ".join(list_of_strings(chunk.get("rule_ids"))), terms, 100)
    score += field_score(chunk.get("rule_title"), terms, 80)
    score += field_score(chunk.get("rule_summary"), terms, 40)
    score += field_score(chunk.get("rule_must_text"), terms, 10)
    score += field_score(chunk.get("rule_must_not_text"), terms, 10)
    score += field_score(chunk.get("rule_agent_guidance"), terms, 6)
    score += field_score(chunk.get("content"), terms, 1)
    return score


def source_rank(chunk: dict[str, Any]) -> int:
    rank = chunk.get("rank")
    return rank if isinstance(rank, int) else 999999


def score_chunk(
    chunk: dict[str, Any],
    prompt_terms: list[str],
    recognition_matches: list[dict[str, Any]],
    session_corpus: str,
) -> float:
    haystack = chunk_haystack(chunk)
    score = 0.0
    scoring_terms = rerank_terms(prompt_terms, recognition_matches)
    for term in scoring_terms:
        score += haystack.count(term)

    chunk_corpus = str(chunk.get("corpus_id") or "")
    if chunk_corpus == session_corpus:
        score += 6

    source_path = str(chunk.get("source_path") or "")
    artifact_id = str(chunk.get("artifact_id") or "")

    for match in recognition_matches:
        category = match.get("category")
        canonical = str(match.get("canonical_id") or "")
        term = str(match.get("term") or "")
        matched_input = str(match.get("matched_input") or "")
        if matched_input == PROMPT_EXAMPLE_INPUT and category not in {
            "artifact-id",
            "file-path",
            "rule-id",
            "rule-pack-id",
            "source-material-id",
        }:
            continue
        input_weight = 2 if matched_input == "prompt" else 0.1 if matched_input == PROMPT_EXAMPLE_INPUT else 1
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
        elif category == "evidence-family" and term.lower() in haystack:
            score += 8 * weight
        elif category == "question-category" and term.lower() in haystack:
            score += 1 * weight
        elif category == "action-verb" and term.lower() in haystack:
            score += 2 * weight
        elif category in {"risk-word", "stop-condition", "check-name"} and term.lower() in haystack:
            score += 4 * weight

    kind = chunk.get("content_kind")
    term_set = set(scoring_terms)
    if kind == "required-check" and term_set.intersection({"check", "validate", "governed", "gate"}):
        score += 6
    if kind == "rule" and term_set.intersection({"rule", "policy", "selector", "retrieval", "governed"}):
        score += 5
    if kind == "artifact-summary" and term_set.intersection({"artifact", "source", "rulebook", "rag"}):
        score += 4
    if kind == "retrieval-profile" and term_set.intersection({"artifact", "content", "harness", "index", "rag", "retrieval"}):
        score += 8
    score += intra_source_score(chunk, prompt_terms, recognition_matches)
    return score


def ranked_chunks(
    chunks: list[dict[str, Any]],
    prompt_terms: list[str],
    recognition_matches: list[dict[str, Any]],
    session_corpus: str,
) -> list[tuple[float, int, str, dict[str, Any]]]:
    ranked = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str):
            continue
        ranked.append(
            (
                score_chunk(chunk, prompt_terms, recognition_matches, session_corpus),
                source_rank(chunk),
                chunk_id,
                chunk,
            )
        )
    return sorted(ranked, key=lambda item: (-item[0], item[1], item[2]))


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


def enrich_gap_evidence(gaps: list[dict[str, Any]], selected_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_chunk_by_id = {
        str(chunk.get("chunk_id")): chunk
        for chunk in selected_chunks
        if isinstance(chunk.get("chunk_id"), str)
    }
    enriched: list[dict[str, Any]] = []
    for gap in gaps:
        gap_copy = dict(gap)
        evidence_chunk_ids = [
            chunk_id
            for chunk_id in list_of_strings(gap_copy.get("required_evidence_chunk_ids"))
            if chunk_id in selected_chunk_by_id
        ]
        citation_ids: list[str] = []
        for chunk_id in evidence_chunk_ids:
            for citation_id in list_of_strings(selected_chunk_by_id[chunk_id].get("citation_ids")):
                if citation_id not in citation_ids:
                    citation_ids.append(citation_id)
        if evidence_chunk_ids:
            gap_copy["required_evidence_chunk_ids"] = evidence_chunk_ids
        if citation_ids:
            gap_copy["citation_ids"] = citation_ids
        enriched.append(gap_copy)
    return enriched


def category_summary(matches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in matches:
        category = str(match.get("category") or "unknown")
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def prompt_target_paths(matches: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for match in matches:
        if match.get("matched_input") != "prompt":
            continue
        if match.get("category") not in {"file-path", "artifact-id", "workflow-name"}:
            continue
        path = str(match.get("evidence_path") or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def source_id_summary(matches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in matches:
        source_id = str(match.get("source_id") or "unknown")
        counts[source_id] = counts.get(source_id, 0) + 1
    return dict(sorted(counts.items()))


def selector_trace_stage(
    stage: dict[str, Any],
    status: str,
    summary: str,
    signals: dict[str, Any],
) -> dict[str, Any]:
    return {
        "stage_id": stage.get("stage_id"),
        "rank": stage.get("rank"),
        "status": status,
        "summary": summary,
        "signals": signals,
    }


def selected_rule_ids_by_source(
    selected_chunks: list[dict[str, Any]],
    source_paths: list[str],
) -> dict[str, list[str]]:
    required_sources = set(source_paths)
    result: dict[str, list[str]] = {}
    for chunk in selected_chunks:
        source_path = str(chunk.get("source_path") or "")
        if source_path not in required_sources or chunk.get("content_kind") != "rule":
            continue
        rule_ids = list_of_strings(chunk.get("rule_ids"))
        if not rule_ids:
            continue
        result.setdefault(source_path, [])
        for rule_id in rule_ids:
            if rule_id not in result[source_path]:
                result[source_path].append(rule_id)
    return dict(sorted(result.items()))


def build_selector_trace(
    compiled_policy: dict[str, Any],
    recognition_matches: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    ranked: list[tuple[float, int, str, dict[str, Any]]],
    candidate_ranked: list[tuple[float, int, str, dict[str, Any]]],
    used_candidate_filter: bool,
    allowed_corpus_ids: list[str],
    candidate_evidence_paths: list[str],
    evidence_bundle_source_paths: list[str],
    question_frames: list[dict[str, Any]],
    profile_evidence_paths: list[str],
    profile_evidence_chunk_ids: list[str],
    graph_expansion_source_paths: list[str],
    required_chunk_ids: list[str],
    required_source_paths: list[str],
    selected_chunks: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    selected_context_tokens: int,
) -> dict[str, Any]:
    retrieval_strategy = dict_value(compiled_policy.get("retrieval_strategy"))
    strategy_id = str(retrieval_strategy.get("strategy_id") or "unknown")
    stages = list_of_dicts(retrieval_strategy.get("stages"))
    exact_categories = {"corpus-id", "artifact-id", "file-path", "rule-id", "rule-pack-id"}
    exact_matches = [match for match in recognition_matches if match.get("category") in exact_categories]
    generated_matches = [
        match
        for match in recognition_matches
        if str(match.get("source_id") or "").startswith("recognition.generated.")
    ]
    curated_matches = [
        match
        for match in recognition_matches
        if str(match.get("source_id") or "").startswith("recognition.curated.")
        or str(match.get("source_id") or "") == "policy.user-intents"
    ]
    missing_evidence_gap_ids = [
        str(gap.get("id"))
        for gap in gaps
        if gap.get("type") == "missing-evidence" and isinstance(gap.get("id"), str)
    ]
    stage_records: list[dict[str, Any]] = []
    for stage in stages:
        stage_id = str(stage.get("stage_id") or "")
        if stage_id == "exact-identifiers":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if exact_matches else "skipped",
                    "Matched exact corpus, artifact, path, rule, or rule-pack identifiers before broad concepts.",
                    {
                        "match_count": len(exact_matches),
                        "categories": category_summary(exact_matches),
                    },
                )
            )
        elif stage_id == "generated-concepts":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if generated_matches else "skipped",
                    "Applied generated artifact, routing, workflow, schema, and corpus concepts.",
                    {
                        "match_count": len(generated_matches),
                        "source_ids": source_id_summary(generated_matches),
                    },
                )
            )
        elif stage_id == "curated-concepts":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if curated_matches else "skipped",
                    "Applied reviewed intent, action, risk, alias, question-category, and evidence-family vocabulary.",
                    {
                        "match_count": len(curated_matches),
                        "source_ids": source_id_summary(curated_matches),
                        "categories": category_summary(curated_matches),
                    },
                )
            )
        elif stage_id == "graph-expansion":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if graph_expansion_source_paths else "skipped",
                    "Added bounded related rule source paths from artifact-summary signals.",
                    {
                        "source_paths": graph_expansion_source_paths,
                    },
                )
            )
        elif stage_id == "evidence-bundles":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if evidence_bundle_source_paths or profile_evidence_paths else "skipped",
                    "Promoted canonical evidence families and generated retrieval-profile sources before trimming.",
                    {
                        "candidate_evidence_paths": candidate_evidence_paths,
                        "bundle_source_paths": evidence_bundle_source_paths,
                        "question_frames": question_frames,
                        "profile_source_paths": profile_evidence_paths,
                        "profile_chunk_ids": profile_evidence_chunk_ids,
                        "missing_evidence_gap_ids": missing_evidence_gap_ids,
                    },
                )
            )
        elif stage_id == "intra-source-reranking":
            selected_by_source = selected_rule_ids_by_source(selected_chunks, required_source_paths)
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied" if selected_by_source else "skipped",
                    "Re-ranked rule chunks inside required source paths using prompt and evidence-family terms.",
                    {
                        "required_source_paths": sorted(set(required_source_paths)),
                        "selected_rule_ids_by_source": selected_by_source,
                    },
                )
            )
        elif stage_id == "final-ranking":
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "applied",
                    "Scored, filtered, trimmed, and validated chunks after required evidence was preserved.",
                    {
                        "used_candidate_filter": used_candidate_filter,
                        "selected_chunk_ids": [
                            str(chunk.get("chunk_id"))
                            for chunk in selected_chunks
                            if isinstance(chunk.get("chunk_id"), str)
                        ],
                    },
                )
            )
        else:
            stage_records.append(
                selector_trace_stage(
                    stage,
                    "unknown",
                    "No selector trace implementation exists for this compiled strategy stage.",
                    {},
                )
            )
    return {
        "strategy_id": strategy_id,
        "compiled_policy_id": compiled_policy.get("compiled_policy_id"),
        "recognition_match_counts": {
            "by_category": category_summary(recognition_matches),
            "by_source_id": source_id_summary(recognition_matches),
        },
        "candidate_counts": {
            "chunks_total": len(chunks),
            "ranked": len(ranked),
            "after_corpus_filter": len(candidate_ranked),
            "selected": len(selected_chunks),
        },
        "candidate_filter_used": used_candidate_filter,
        "candidate_corpus_ids": allowed_corpus_ids,
        "required_evidence": {
            "source_paths": sorted(set(required_source_paths)),
            "chunk_ids": required_chunk_ids,
            "question_frames": [
                str(frame.get("frame_id"))
                for frame in question_frames
                if isinstance(frame.get("frame_id"), str)
            ],
            "profile_chunk_ids": profile_evidence_chunk_ids,
        },
        "selected_context_tokens": selected_context_tokens,
        "stages": stage_records,
    }


def layer_match_can_seed_corpus(match: dict[str, Any]) -> bool:
    matched_input = str(match.get("matched_input") or "")
    if matched_input == "session-metadata":
        return True
    if matched_input != "prompt":
        return False
    canonical = str(match.get("canonical_id") or "")
    term = str(match.get("term") or "").strip().lower()
    if term == canonical.lower() and re.fullmatch(r"[0-9]{2}\.[a-z0-9-]+", canonical):
        return True
    return canonical == "04.deploy" and term == "aws"


def corpus_ids_by_evidence_path(chunks: list[dict[str, Any]]) -> dict[str, list[str]]:
    corpus_ids_by_path: dict[str, list[str]] = {}

    def add(path: str, corpus_id: str) -> None:
        if not path or not corpus_id:
            return
        corpus_ids_by_path.setdefault(path, [])
        if corpus_id not in corpus_ids_by_path[path]:
            corpus_ids_by_path[path].append(corpus_id)

    for chunk in chunks:
        corpus_id = str(chunk.get("corpus_id") or "")
        add(str(chunk.get("source_path") or ""), corpus_id)
        source_derivation = dict_value(chunk.get("source_derivation"))
        for source_material in list_of_dicts(source_derivation.get("source_material")):
            add(str(source_material.get("path") or ""), corpus_id)

    return corpus_ids_by_path


def matched_corpus_ids(matches: list[dict[str, Any]], session_corpus: str, chunks: list[dict[str, Any]]) -> list[str]:
    corpus_ids = [] if session_corpus in {"", "corpus.unknown"} else [session_corpus]
    exact_path_categories = {
        "artifact-id",
        "file-path",
        "rule-id",
        "rule-pack-id",
        "source-material-id",
    }
    corpus_ids_by_path = corpus_ids_by_evidence_path(chunks)
    for match in matches:
        if match.get("category") == "corpus-id":
            corpus_ids.append(str(match.get("canonical_id")))
        elif match.get("category") == "layer-name" and layer_match_can_seed_corpus(match):
            layer_corpus = SESSION_LAYER_TO_CORPUS.get(str(match.get("canonical_id") or ""))
            if layer_corpus:
                corpus_ids.append(layer_corpus)
        elif match.get("category") in exact_path_categories and match.get("matched_input") in PROMPT_ROUTE_INPUTS:
            evidence_path = str(match.get("evidence_path") or "")
            corpus_ids.extend(corpus_ids_by_path.get(evidence_path, []))
    seen: set[str] = set()
    result: list[str] = []
    for corpus_id in corpus_ids:
        if corpus_id and corpus_id not in seen:
            result.append(corpus_id)
            seen.add(corpus_id)
    return result


def matched_corpus_gap_target_ids(
    corpus_gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    request_text: str,
) -> list[str]:
    target_ids: list[str] = []
    candidates_by_id = {
        str(candidate.get("candidate_id")): candidate
        for candidate in candidates
        if isinstance(candidate.get("candidate_id"), str)
    }
    for gap in corpus_gaps:
        if gap.get("status") not in {"open", "planned", "in-progress"}:
            continue
        if not corpus_gap_matches_request(gap, candidates_by_id, request_text):
            continue
        target_corpus_id = str(gap.get("target_corpus_id") or "").strip()
        if target_corpus_id:
            target_ids.append(target_corpus_id)

    seen: set[str] = set()
    result: list[str] = []
    for target_id in target_ids:
        if target_id and target_id not in seen:
            result.append(target_id)
            seen.add(target_id)
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


def is_rule_source_path(path: str) -> bool:
    return path.startswith("docs/") and "/rules/" in path and path.endswith((".yml", ".yaml"))


def related_rule_source_paths(
    ranked: list[tuple[float, int, str, dict[str, Any]]],
    limit: int = 8,
) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    available_source_paths = {
        str(item[3].get("source_path"))
        for item in ranked
        if isinstance(item[3].get("source_path"), str)
    }
    for score, _rank, _chunk_id, chunk in ranked:
        if len(paths) >= limit:
            break
        if score <= 0 or chunk.get("content_kind") != "artifact-summary":
            continue
        in_related = False
        for line in str(chunk.get("content") or "").splitlines():
            stripped = line.strip()
            if stripped == "Related rulesets:":
                in_related = True
                continue
            if not in_related:
                continue
            if not stripped:
                continue
            if not stripped.startswith("- "):
                break
            related_path = stripped[2:].strip()
            if not is_rule_source_path(related_path):
                continue
            if related_path not in available_source_paths:
                continue
            if related_path in seen or not repo_path(related_path).is_file():
                continue
            seen.add(related_path)
            paths.append(related_path)
    return paths


def rule_evidence_paths(paths: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not is_rule_source_path(path):
            continue
        if path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def unique_source_paths(paths: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def select_chunks(
    ranked: list[tuple[float, int, str, dict[str, Any]]],
    max_chunks: int,
    required_chunk_ids: list[str] | None = None,
    required_source_paths: list[str] | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    selected: dict[str, tuple[float, dict[str, Any]]] = {}
    required_ids = set(required_chunk_ids or [])
    required_sources = set(required_source_paths or [])

    def add(item: tuple[float, int, str, dict[str, Any]] | None) -> None:
        if item is None:
            return
        score, _rank, chunk_id, chunk = item
        selected.setdefault(chunk_id, (score, chunk))

    by_chunk_id = {chunk_id: item for item in ranked for chunk_id in [item[2]]}

    for chunk_id in required_chunk_ids or []:
        add(by_chunk_id.get(chunk_id))

    for source_path in required_source_paths or []:
        excerpt = next(
            (
                item
                for item in ranked
                if item[3].get("source_path") == source_path
                and item[3].get("content_kind") == "source-excerpt"
                and item[0] > 0
            ),
            None,
        )
        preferred = next(
            (
                item
                for item in ranked
                if item[3].get("source_path") == source_path and item[0] > 0
            ),
            None,
        )
        fallback = next((item for item in ranked if item[3].get("source_path") == source_path), None)
        add(excerpt or preferred or fallback)

    for kind in ["required-check", "rule", "artifact-summary"]:
        preferred = next((item for item in ranked if item[3].get("content_kind") == kind and item[0] > 0), None)
        if kind == "required-check" and preferred is None:
            continue
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

    boosted: list[tuple[float, dict[str, Any]]] = []
    for score, chunk in selected.values():
        if chunk.get("chunk_id") in required_ids or chunk.get("source_path") in required_sources:
            score += 50
        boosted.append((score, chunk))

    ordered = sorted(
        boosted,
        key=lambda item: (-item[0], source_rank(item[1]), item[1].get("chunk_id", "")),
    )
    if len(ordered) <= max_chunks:
        return ordered

    required_by_id = [
        item
        for item in ordered
        if item[1].get("chunk_id") in required_ids
    ]
    required_by_source = [
        item
        for item in ordered
        if item[1].get("chunk_id") not in required_ids
        and item[1].get("source_path") in required_sources
    ]
    optional = [
        item
        for item in ordered
        if item[1].get("chunk_id") not in required_ids
        and item[1].get("source_path") not in required_sources
    ]
    limited = required_by_id[:max_chunks]
    covered_required_sources = {
        item[1].get("source_path")
        for item in limited
        if item[1].get("source_path") in required_sources
    }
    primary_required_by_source: list[tuple[float, dict[str, Any]]] = []
    extra_required_by_source: list[tuple[float, dict[str, Any]]] = []
    for item in required_by_source:
        source_path = item[1].get("source_path")
        if source_path not in covered_required_sources:
            primary_required_by_source.append(item)
            covered_required_sources.add(source_path)
            continue
        extra_required_by_source.append(item)
    if len(limited) < max_chunks:
        limited.extend(primary_required_by_source[: max_chunks - len(limited)])
    if len(limited) < max_chunks:
        limited.extend(extra_required_by_source[: max_chunks - len(limited)])
    if len(limited) < max_chunks:
        limited.extend(optional[: max_chunks - len(limited)])
    return sorted(
        limited,
        key=lambda item: (-item[0], source_rank(item[1]), item[1].get("chunk_id", "")),
    )


def build_packet(
    args: argparse.Namespace,
    policy: dict[str, Any],
    compiled_policy: dict[str, Any],
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
    prompt_terms = tokenize(prompt_text_for_broad_terms(args.request_text))
    user_intent_ids = sorted(matched_user_intent_ids(recognition_matches))
    resolved_intent_id = resolve_intent_id(recognition_matches, compiled_policy)
    prompt_route = resolve_prompt_route(recognition_matches, resolved_intent_id, args.request_text)
    use_trusted_session_route = args.trust_session_routing and prompt_route["layer"] == "unknown"
    routing_layer = args.session_layer if use_trusted_session_route else prompt_route["layer"]
    routing_mode = args.session_mode if use_trusted_session_route else prompt_route["mode"]
    routing_workflow = args.session_workflow if use_trusted_session_route else prompt_route["workflow"]
    session_corpus = (
        SESSION_LAYER_TO_CORPUS.get(args.session_layer, f"corpus.{args.session_layer}")
        if use_trusted_session_route
        else "corpus.unknown"
    )
    allowed_corpus_ids = (
        matched_corpus_ids(recognition_matches, session_corpus, chunks)
        + matched_corpus_gap_target_ids(corpus_gaps, recognition_candidates, args.request_text)
        + (prototype_bridge_corpora(args.session_layer) if use_trusted_session_route else [])
    )
    candidate_evidence_paths = matched_candidate_evidence_paths(recognition_candidates, args.request_text)
    evidence_bundle_source_paths = matched_evidence_bundle_source_paths(recognition_matches, compiled_policy)
    question_frames = question_frame_matches(prompt_terms)
    profile_evidence = matched_profile_evidence(chunks, question_frames)
    profile_evidence_source_paths = list_of_strings(profile_evidence.get("source_paths"))
    profile_evidence_chunk_ids = list_of_strings(profile_evidence.get("chunk_ids"))
    evidence_source_paths = candidate_evidence_paths + evidence_bundle_source_paths + profile_evidence_source_paths
    ranking_paths = evidence_source_paths
    ranked = ranked_chunks(chunks, prompt_terms, recognition_matches, session_corpus)
    candidate_ranked, used_candidate_filter = candidate_ranked_chunks(
        ranked,
        allowed_corpus_ids,
        ranking_paths,
    )
    gap_required_chunk_ids = matched_corpus_gap_required_chunk_ids(
        corpus_gaps,
        recognition_candidates,
        recognition_matches,
        args.request_text,
        compiled_policy,
    )
    required_chunk_ids = unique_source_paths(gap_required_chunk_ids + profile_evidence_chunk_ids)
    graph_expansion_source_paths = related_rule_source_paths(candidate_ranked)
    required_source_paths = list(candidate_evidence_paths)
    if gap_required_chunk_ids:
        required_source_paths += graph_expansion_source_paths
    required_source_paths += evidence_bundle_source_paths
    required_source_paths += profile_evidence_source_paths
    required_source_paths = unique_source_paths(required_source_paths)
    selected_pairs = select_chunks(
        candidate_ranked,
        args.max_chunks,
        required_chunk_ids=required_chunk_ids,
        required_source_paths=required_source_paths,
    )
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
            "Selected by deterministic retrieval-selector fixture using request context, "
            "recognition-source matches, and session safety context."
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
        if args.trust_session_routing
        and args.session_layer not in {"", "unknown"}
        and layer != args.session_layer
        and re.fullmatch(r"[0-9]{2}\.[a-z0-9-]+", layer)
    )
    side_effect_session_conflict = False
    side_effect_intents = {"intent.deploy.execution", "intent.git.commit", "intent.implementation.request"}
    if prompt_layer_conflicts:
        if resolved_intent_id == "intent.deploy.execution":
            side_effect_session_conflict = args.session_layer != "04.deploy"
        elif resolved_intent_id in {"intent.git.commit", "intent.implementation.request"}:
            side_effect_session_conflict = True
    gaps = []
    if prompt_layer_conflicts:
        gaps.append(
            {
                "id": "gap.selector-fixture.prompt-session-layer-conflict",
                "type": "ambiguous-intent",
                "description": (
                    "Prompt layer terms differ from complete session metadata; request context may retrieve evidence while session metadata remains provenance and safety context."
                    if not side_effect_session_conflict
                    else "Prompt requests a side-effecting action outside the current session layer; stop before acting."
                ),
                "blocking": side_effect_session_conflict,
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
    prompt_matches = [
        match
        for match in recognition_matches
        if match.get("matched_input") == "prompt"
    ]
    if not prompt_matches and prompt_terms and not question_frames:
        gaps.append(
            {
                "id": "gap.selector-fixture.low-confidence-prompt",
                "type": "ambiguous-intent",
                "description": "The prompt produced no governed prompt recognition matches, so current-prompt routing confidence is low.",
                "blocking": False,
            }
        )
    if resolved_intent_id in side_effect_intents and (not args.session_branch or not args.session_worktree):
        gaps.append(
            {
                "id": "gap.selector-fixture.missing-session-ownership-for-side-effect",
                "type": "ambiguous-ownership",
                "description": "The prompt requests a side-effecting action, but verified chat branch/worktree ownership is not available in the supplied lifecycle context.",
                "blocking": True,
                "suggested_resolution": "Resolve the active chat session and verify branch/worktree ownership before using this packet for side-effecting work.",
            }
        )
    if use_trusted_session_route and args.session_layer == "02.rag-rulebook" and session_corpus not in selected_corpus_ids:
        gaps.append(
            {
                "id": "gap.selector-fixture.prototype-corpus-bridge",
                "type": "missing-corpus",
                "description": "The current prototype chunks do not yet contain corpus.02.rag-rulebook, so the fixture bridges through harness/shared prototype corpus chunks until migration.",
                "blocking": False,
            }
        )
    gaps.extend(candidate_coverage_gaps(recognition_candidates, args.request_text))
    gaps.extend(corpus_gap_records_gaps(corpus_gaps, recognition_candidates, recognition_matches, args.request_text, compiled_policy))
    gaps.extend(evidence_bundle_gaps(recognition_matches, selected_chunks, compiled_policy))
    gaps = enrich_gap_evidence(gaps, selected_chunks)

    selected_context_tokens = sum(
        chunk.get("token_estimate")
        for chunk in selected_chunks
        if isinstance(chunk.get("token_estimate"), int)
    )
    selector_trace = build_selector_trace(
        compiled_policy,
        recognition_matches,
        chunks,
        ranked,
        candidate_ranked,
        used_candidate_filter,
        allowed_corpus_ids,
        candidate_evidence_paths,
        evidence_bundle_source_paths,
        question_frames,
        profile_evidence_source_paths,
        profile_evidence_chunk_ids,
        graph_expansion_source_paths,
        required_chunk_ids,
        required_source_paths,
        selected_chunks,
        gaps,
        selected_context_tokens,
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
                "trust_session_routing": args.trust_session_routing,
                "session_id": args.session_id,
                "session_branch": args.session_branch,
                "session_worktree": args.session_worktree,
                "previous_packet_id": args.previous_packet_id,
                "previous_routing_summary": args.previous_routing_summary,
                "chunk_ids": [chunk.get("chunk_id") for chunk in selected_chunks],
                "recognition_matches": [
                    [match.get("source_id"), match.get("term"), match.get("matched_input")]
                    for match in recognition_matches[:40]
                ],
                "question_frames": [
                    frame.get("frame_id")
                    for frame in question_frames
                ],
                "gaps": [gap.get("id") for gap in gaps],
                "source_index_id": source_index_id,
                "compiled_policy_id": compiled_policy.get("compiled_policy_id"),
                "strategy_id": selector_trace.get("strategy_id"),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]

    recognition_confidence = min(1, 0.75 + (0.02 * min(len(recognition_matches), 10)))
    retrieval_confidence = 0.9 if max_score else 0.55
    if prompt_layer_conflicts:
        retrieval_confidence = min(retrieval_confidence, 0.82)
    if any(gap.get("type") == "missing-evidence" for gap in gaps):
        retrieval_confidence = min(retrieval_confidence, 0.69)
    if not prompt_matches and prompt_terms and not question_frames:
        recognition_confidence = min(recognition_confidence, 0.69)
        retrieval_confidence = min(retrieval_confidence, 0.69)
    routing_status = "blocked" if any(gap.get("blocking") is True for gap in gaps) else "ready"
    blocking_gap_ids = [
        str(gap.get("id"))
        for gap in gaps
        if gap.get("blocking") is True and isinstance(gap.get("id"), str)
    ]
    requested_action = "context-retrieval"
    side_effect_class = "none"
    authorization_status = "not-requested"
    if resolved_intent_id == "intent.deploy.execution":
        requested_action = "deploy"
        side_effect_class = "deploy"
        authorization_status = "blocked" if blocking_gap_ids else "requires-deploy-workflow-approval"
    elif resolved_intent_id == "intent.git.commit":
        requested_action = "commit"
        side_effect_class = "git"
        authorization_status = "blocked" if blocking_gap_ids else "not-executable-intent"
    elif resolved_intent_id == "intent.implementation.request":
        requested_action = "edit"
        side_effect_class = "write"
        authorization_status = "blocked" if blocking_gap_ids else "not-executable-intent"
    elif any(intent_id == "intent.deploy.execution" for intent_id in matched_intent_ids(recognition_matches)):
        requested_action = "deployment-guidance"
        authorization_status = "not-executable-intent"
    action_authorization = {
        "requested_action": requested_action,
        "side_effect_class": side_effect_class,
        "execution_allowed": (
            authorization_status == "allowed"
            and not blocking_gap_ids
            and side_effect_class != "deploy"
        ),
        "status": authorization_status,
        "resolved_intent_id": resolved_intent_id,
        "blocking_gap_ids": blocking_gap_ids,
    }

    return {
        "schema": PACKET_SCHEMA,
        "packet_id": f"packet.selector-fixture.{packet_fingerprint}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "request": {
            "raw_text": args.request_text,
            "normalized_summary": "Generate a deterministic retrieval selector fixture from governed policy, request context, recognition sources, session safety metadata, and chunks.",
            "open_artifact_ids": selected_artifact_ids,
            "previous_packet_id": args.previous_packet_id,
            "user_intent_ids": user_intent_ids,
            "recognition_source_matches": recognition_matches[:80],
        },
        "intent": {
            "id": resolved_intent_id,
            "label": intent_label(compiled_policy, resolved_intent_id),
            "mode": routing_mode,
            "layer": routing_layer,
            "workflow": routing_workflow,
            "confidence": recognition_confidence,
            "source": "mixed",
            "evidence_ref_ids": selected_citation_ids,
        },
        "action_authorization": action_authorization,
        "selector_trace": selector_trace,
        "routing": {
            "layer": routing_layer,
            "mode": routing_mode,
            "workflow": routing_workflow,
            "status": routing_status,
            "task_type": "generate_retrieval_selector_fixture",
            "target_paths": prompt_target_paths(recognition_matches),
            "classification_source": "request-context-plus-recognition-sources",
            "scope": "prompt",
            "previous_packet_id": args.previous_packet_id,
            "continuity_reason": (
                args.previous_routing_summary
                or "No previous context packet supplied; current prompt is resolved from request context and available session continuity."
            ),
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
                    if args.trust_session_routing and corpus_id in prototype_bridge_corpora(args.session_layer)
                    else "Request context or recognition-source terms matched this corpus."
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
                "Request context is preferred over session continuity for retrieval target selection.",
                "Session metadata remains provenance and execution-safety context.",
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
            "compiled_policy": {
                "schema": compiled_policy.get("schema"),
                "compiled_policy_id": compiled_policy.get("compiled_policy_id"),
                "content_hash": compiled_policy.get("content_hash"),
            },
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
            "session_context": {
                "source": (
                    "governed-local-session-resolution"
                    if args.trust_session_routing
                    else "client-supplied-unverified"
                ),
                "verification_status": (
                    "routing-hints-trusted-by-governed-caller"
                    if args.trust_session_routing
                    else "unverified"
                ),
                "execution_safety_role": (
                    "routing-provenance-only; side-effect authorization must still verify ownership outside the packet"
                    if args.trust_session_routing
                    else "provenance-only; side-effect authorization must verify ownership outside the packet"
                ),
                "session_id": args.session_id,
                "branch": args.session_branch,
                "worktree": args.session_worktree,
                "legacy_routing_hint": {
                    "layer": args.session_layer,
                    "mode": args.session_mode,
                    "workflow": args.session_workflow,
                    "trusted": args.trust_session_routing,
                },
                "previous_packet_id": args.previous_packet_id,
                "previous_routing_summary": args.previous_routing_summary,
            },
            "retrieval_order": [
                "load compiled retrieval policy",
                "validate compiled policy provenance",
                "load generated chunks",
                "match prompt and session continuity metadata against recognition sources",
                "resolve intent forms with governed precedence before deciding blocking behavior",
                "restrict candidate chunks by prompt recognition and trusted local routing hints when enough candidates exist",
                "score chunks with deterministic recognition, path, corpus, trusted routing, and token signals",
                "preserve required evidence chunks for blocking gaps",
                "require required-check, rule, and artifact-summary coverage where available",
                "validate context packet against chunk set before output",
            ],
            "candidate_filter_used": used_candidate_filter,
            "candidate_corpus_ids": allowed_corpus_ids,
            "matched_candidate_evidence_paths": candidate_evidence_paths,
            "matched_question_frames": question_frames,
            "profile_evidence_source_paths": profile_evidence_source_paths,
            "profile_evidence_chunk_ids": profile_evidence_chunk_ids,
            "graph_expansion_source_paths": graph_expansion_source_paths,
            "required_gap_chunk_ids": gap_required_chunk_ids,
            "required_chunk_ids": required_chunk_ids,
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
        compiled_policy = load_compiled_policy(args.compiled_policy)
        policy_report = compiled_policy_report(compiled_policy)
        recognition_report = compiled_recognition_report(compiled_policy)
        candidate_report = validate_recognition_candidates()
        policy = compiled_policy_pack(compiled_policy)
        sources = compiled_recognition_sources(compiled_policy)
        candidates = load_recognition_candidates()
        corpus_gaps = load_corpus_gaps()
        chunk_set, chunk_set_raw = load_chunk_set(args)
        session_text = "\n".join([args.session_layer, args.session_mode, args.session_workflow]) if args.trust_session_routing else ""
        recognition_matches = match_recognition_terms(
            sources,
            args.request_text,
            session_text,
        )
        recognition_matches.extend(match_user_intents(compiled_policy, args.request_text))
        packet = build_packet(
            args,
            policy,
            compiled_policy,
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

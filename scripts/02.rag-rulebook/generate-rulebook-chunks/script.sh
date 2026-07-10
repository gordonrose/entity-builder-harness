#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-rulebook-chunks
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: chunking
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate deterministic retrieval chunks from a validated rulebook index without modifying files.
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
#     - id: rag-rulebook.script.validate-rulebook-index
#       path: scripts/02.rag-rulebook/validate-rulebook-index/script.sh
#     - id: rag-rulebook.script.generate-rulebook-chunks.readme
#       path: scripts/02.rag-rulebook/generate-rulebook-chunks/README.md

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
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for rulebook chunk generation.", file=sys.stderr)
    sys.exit(2)


CHUNK_SET_SCHEMA = "rag-rulebook/chunk-set/v1"
GENERATOR_VERSION = "prototype-v1"
INDEX_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
INDEX_VALIDATOR_SCRIPT = "scripts/02.rag-rulebook/validate-rulebook-index/script.sh"


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


def run_git(args: list[str]) -> str:
    if args == ["rev-parse", "HEAD"]:
        env_sha = os.environ.get("RAG_SOURCE_COMMIT_SHA", "").strip()
        if env_sha:
            return env_sha
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout.strip()


def usage() -> str:
    return """Usage:
  generate-rulebook-chunks/script.sh --generate-current [--pretty]
  generate-rulebook-chunks/script.sh --index <path> [--pretty]

Emits a rag-rulebook/chunk-set/v1 JSON document to stdout. The command
validates the index first and is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--generate-current", action="store_true")
    parser.add_argument("--index")
    parser.add_argument("--pretty", action="store_true")
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


def safe_id(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", ".", str(value or "unknown").lower()).strip(".")
    return cleaned or "unknown"


def load_yaml(path: str) -> dict[str, Any]:
    with repo_path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    return data


def load_index(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    if args.generate_current:
        result = subprocess.run(
            ["bash", INDEX_GENERATOR_SCRIPT],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        raw = result.stdout
    else:
        raw = Path(args.index).read_text(encoding="utf-8")
    validate_index(raw)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("index JSON must be an object")
    return data, raw


def validate_index(raw: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
        handle.write(raw)
        handle.flush()
        result = subprocess.run(
            ["bash", INDEX_VALIDATOR_SCRIPT, "--index", handle.name, "--json"],
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


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def get_section(yaml_data: dict[str, Any], section_path: str | None) -> Any:
    if not section_path:
        return None
    match = re.fullmatch(r"([a-zA-Z0-9_-]+)\[(\d+)\]", section_path)
    if not match:
        return None
    field_name, index_text = match.groups()
    value = yaml_data.get(field_name)
    if not isinstance(value, list):
        return None
    index = int(index_text)
    if index >= len(value):
        return None
    return value[index]


def render_list(label: str, values: list[str]) -> list[str]:
    if not values:
        return []
    lines = [f"{label}:"]
    lines.extend(f"- {value}" for value in values)
    return lines


def render_yaml_block(value: Any) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=False, width=88).strip()


def artifact_summary_content(candidate: dict[str, Any], artifact: dict[str, Any]) -> str:
    lines = [
        f"Artifact: {artifact.get('title') or artifact.get('artifact_ref')}",
        f"Artifact ref: {artifact.get('artifact_ref')}",
        f"Type: {artifact.get('artifact_type')}",
        f"Corpus: {artifact.get('corpus_id')}",
        f"Source path: {artifact.get('current_path')}",
        f"Migration status: {artifact.get('migration_status')}",
    ]
    proposed_path = artifact.get("proposed_path")
    if proposed_path:
        lines.append(f"Proposed path: {proposed_path}")
    source_derivation = artifact.get("source_derivation")
    if isinstance(source_derivation, dict):
        lines.append("Source derivation:")
        lines.append(f"- provenance_version: {source_derivation.get('provenance_version')}")
        lines.append(f"- generator: {source_derivation.get('generator')}")
        lines.append(f"- generator_version: {source_derivation.get('generator_version')}")
        lines.append(f"- derivation_report: {source_derivation.get('derivation_report')}")
        for item in list_of_dicts(source_derivation.get("source_material")):
            lines.append(f"- source_material: {item.get('path')}@{item.get('sha256')}")
    lines.extend(render_list("Applies to paths", list_of_strings(artifact.get("applies_to_paths"))))
    lines.extend(render_list("Required rulesets", list_of_strings(artifact.get("required_ruleset_refs"))))
    lines.extend(render_list("Related rulesets", list_of_strings(artifact.get("related_ruleset_refs"))))
    return "\n".join(lines)


def rule_content(rule: dict[str, Any], rule_body: Any) -> str:
    lines = [
        f"Rule: {rule.get('title') or rule.get('rule_id')}",
        f"Rule ID: {rule.get('rule_id')}",
        f"Rule ref: {rule.get('rule_ref')}",
        f"Artifact ref: {rule.get('artifact_ref')}",
        f"Corpus: {rule.get('corpus_id')}",
    ]
    if rule.get("severity"):
        lines.append(f"Severity: {rule.get('severity')}")
    if rule.get("summary"):
        lines.append(f"Summary: {rule.get('summary')}")
    if rule_body is not None:
        lines.append("")
        lines.append("Structured rule body:")
        lines.append(render_yaml_block(rule_body))
    return "\n".join(lines)


def rule_body_field(rule_body: Any, field_name: str) -> str:
    if not isinstance(rule_body, dict):
        return ""
    value = rule_body.get(field_name)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return ""


def rule_pack_step_content(pack: dict[str, Any], step_body: Any) -> str:
    step_id = step_body.get("id") if isinstance(step_body, dict) else None
    instruction = step_body.get("instruction") if isinstance(step_body, dict) else step_body
    lines = [
        f"Rule pack: {pack.get('pack_id')}",
        f"Pack ref: {pack.get('pack_ref')}",
        f"Task type: {pack.get('task_type')}",
        f"Agent step: {step_id or 'unknown'}",
        "Instruction:",
        str(instruction or "").strip(),
    ]
    return "\n".join(lines)


def required_check_content(pack: dict[str, Any], check_body: Any) -> str:
    lines = [
        f"Rule pack: {pack.get('pack_id')}",
        f"Pack ref: {pack.get('pack_ref')}",
        f"Task type: {pack.get('task_type')}",
        "Required check:",
        str(check_body or "").strip(),
    ]
    return "\n".join(lines)


def retrieval_profile_content(candidate: dict[str, Any], artifact: dict[str, Any], profile: dict[str, Any]) -> str:
    def list_lines(label: str, values: Any) -> list[str]:
        lines = [f"{label}:"]
        items = list_of_strings(values)
        if not items:
            lines.append("- none")
            return lines
        lines.extend(f"- {item}" for item in items)
        return lines

    lines = [
        f"Retrieval profile: {artifact.get('artifact_ref')}",
        f"Source path: {candidate.get('source_path') or artifact.get('current_path')}",
        f"Corpus: {candidate.get('corpus_id') or artifact.get('corpus_id')}",
        "",
    ]
    lines.extend(list_lines("Retrieval roles", profile.get("retrieval_roles")))
    lines.append("")
    lines.extend(list_lines("Answers questions about", profile.get("answers_questions_about")))
    lines.append("")
    lines.extend(list_lines("Produces", profile.get("produces")))
    lines.append("")
    lines.extend(list_lines("Consumes", profile.get("consumes")))
    lines.append("")
    lines.extend(list_lines("Validates", profile.get("validates")))
    return "\n".join(lines)


def merge_ranges(ranges: list[tuple[int, int]], max_line: int) -> list[tuple[int, int]]:
    normalized = sorted(
        (max(1, start), min(max_line, end))
        for start, end in ranges
        if max_line > 0 and start <= end
    )
    merged: list[tuple[int, int]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        merged[-1] = (previous_start, max(previous_end, end))
    return merged


def source_excerpt_ranges(path: str, lines: list[str]) -> list[tuple[int, int]]:
    max_line = len(lines)
    if max_line == 0:
        return []
    if path.endswith((".md", ".yml", ".yaml")):
        return [(1, min(max_line, 260))]

    patterns = [
        "Usage:",
        "--status)",
        "--batch)",
        "def parse_header",
        "def validate_v2",
        "def normalize_v2",
        "def normalize_v1_artifact",
        "def normalize_v1_script",
        "def v2_payload",
        "def render_comment_header",
        "def render_html_header",
        "def replace_header",
        "bash scripts/01.harness/artifact-metadata/check-headers",
        "bash scripts/01.harness/artifact-metadata/generate-index",
        "git add --",
    ]
    ranges: list[tuple[int, int]] = [(1, min(max_line, 120))]
    for line_number, line in enumerate(lines, start=1):
        if any(pattern in line for pattern in patterns):
            ranges.append((line_number - 25, line_number + 45))
    return merge_ranges(ranges, max_line)


def source_excerpt_content(path: str) -> str:
    source = repo_path(path)
    if not source.is_file():
        return f"Source excerpt unavailable: {path}"
    lines = source.read_text(encoding="utf-8").splitlines()
    output = [f"Source excerpt: {path}"]
    for start, end in source_excerpt_ranges(path, lines):
        output.append("")
        output.append(f"Lines {start}-{end}:")
        output.extend(lines[start - 1 : end])
    return "\n".join(output)


def estimate_tokens(content: str, fallback: int | None) -> int:
    estimated = max(1, round(len(content.split()) * 1.35))
    if fallback and fallback > 0:
        return max(estimated, fallback)
    return estimated


def build_chunk_set(index: dict[str, Any], raw_index: str) -> dict[str, Any]:
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    git_commit = run_git(["rev-parse", "HEAD"])
    artifacts = {
        artifact["artifact_ref"]: artifact
        for artifact in list_of_dicts(index.get("artifacts"))
        if isinstance(artifact.get("artifact_ref"), str)
    }
    rules = {
        rule["rule_ref"]: rule
        for rule in list_of_dicts(index.get("rules"))
        if isinstance(rule.get("rule_ref"), str)
    }
    packs = {
        pack["pack_ref"]: pack
        for pack in list_of_dicts(index.get("rule_packs"))
        if isinstance(pack.get("pack_ref"), str)
    }
    citations = []
    citation_ids = set()
    for source_ref in list_of_dicts(index.get("source_references")):
        source_ref_id = source_ref.get("source_ref_id")
        if not isinstance(source_ref_id, str):
            continue
        citation_ids.add(source_ref_id)
        citations.append(
            {
                "id": source_ref_id,
                "corpus_id": source_ref.get("corpus_id"),
                "artifact_id": source_ref.get("artifact_ref"),
                "source_path": source_ref.get("source_path"),
                "source_type": source_ref.get("source_type"),
                "section": source_ref.get("section"),
            }
        )

    yaml_cache: dict[str, dict[str, Any]] = {}

    def yaml_for(path: str | None) -> dict[str, Any]:
        if not path:
            return {}
        if path not in yaml_cache:
            if repo_path(path).is_file() and path.endswith((".yml", ".yaml")):
                yaml_cache[path] = load_yaml(path)
            else:
                yaml_cache[path] = {}
        return yaml_cache[path]

    chunks = []
    errors: list[str] = []
    warnings: list[str] = []
    for rank, candidate in enumerate(list_of_dicts(index.get("chunk_candidates")), start=1):
        chunk_id = candidate.get("chunk_id")
        artifact_ref = candidate.get("artifact_ref")
        content_kind = candidate.get("content_kind")
        source_path = candidate.get("source_path")
        source_ref_ids = list_of_strings(candidate.get("source_ref_ids"))
        artifact = artifacts.get(artifact_ref)
        rule_ref = candidate.get("rule_ref")
        pack_ref = candidate.get("pack_ref")
        rule = rules.get(rule_ref) if isinstance(rule_ref, str) else None
        pack = packs.get(pack_ref) if isinstance(pack_ref, str) else None
        yaml_data = yaml_for(source_path if isinstance(source_path, str) else None)
        section_body = get_section(yaml_data, candidate.get("section_path"))

        if not isinstance(chunk_id, str) or not isinstance(artifact_ref, str) or not artifact:
            errors.append(f"cannot render chunk candidate: {candidate}")
            continue

        if content_kind == "artifact-summary":
            content = artifact_summary_content(candidate, artifact)
        elif content_kind == "rule" and rule:
            content = rule_content(rule, section_body)
        elif content_kind == "rule-pack-step" and pack:
            content = rule_pack_step_content(pack, section_body)
        elif content_kind == "required-check" and pack:
            content = required_check_content(pack, section_body)
        elif content_kind == "source-excerpt" and isinstance(source_path, str):
            content = source_excerpt_content(source_path)
        elif content_kind == "retrieval-profile":
            profile = candidate.get("retrieval_profile") or artifact.get("retrieval_profile")
            content = retrieval_profile_content(candidate, artifact, profile if isinstance(profile, dict) else {})
        else:
            warnings.append(f"unsupported chunk content kind for {chunk_id}: {content_kind}")
            content = artifact_summary_content(candidate, artifact)

        if not source_ref_ids:
            warnings.append(f"chunk has no source_ref_ids: {chunk_id}")
        missing_citations = [source_ref_id for source_ref_id in source_ref_ids if source_ref_id not in citation_ids]
        if missing_citations:
            errors.append(f"chunk citation IDs do not resolve: {chunk_id} -> {', '.join(missing_citations)}")

        chunk = {
            "chunk_id": chunk_id,
            "corpus_id": candidate.get("corpus_id"),
            "artifact_id": artifact_ref,
            "artifact_ref": artifact_ref,
            "source_path": source_path,
            "content_kind": content_kind,
            "section_path": candidate.get("section_path"),
            "rule_ids": [rule.get("rule_id")] if rule else [],
            "rule_refs": [rule_ref] if isinstance(rule_ref, str) else [],
            "pack_refs": [pack_ref] if isinstance(pack_ref, str) else [],
            "content": content,
            "rank": rank,
            "token_estimate": estimate_tokens(content, candidate.get("token_estimate")),
            "selection_reason": "Generated from a structured rulebook index chunk candidate.",
            "citation_ids": source_ref_ids,
            "source_ref_ids": source_ref_ids,
            "retrieval_profile": candidate.get("retrieval_profile") or artifact.get("retrieval_profile") or {},
        }
        if content_kind == "rule" and rule:
            chunk["rule_title"] = str(rule.get("title") or "").strip()
            chunk["rule_summary"] = str(rule.get("summary") or "").strip()
            chunk["rule_must_text"] = rule_body_field(section_body, "must")
            chunk["rule_must_not_text"] = rule_body_field(section_body, "must_not")
            chunk["rule_agent_guidance"] = rule_body_field(section_body, "agent_guidance")
        source_derivation = candidate.get("source_derivation") or artifact.get("source_derivation")
        if isinstance(source_derivation, dict):
            chunk["source_derivation"] = source_derivation
        chunks.append(chunk)

    diagnostics = {
        "ok": not errors,
        "counts": {
            "chunks": len(chunks),
            "citations": len(citations),
            "source_index_chunk_candidates": len(list_of_dicts(index.get("chunk_candidates"))),
        },
        "warnings": warnings,
        "errors": errors,
    }
    index_fingerprint = hashlib.sha256(raw_index.encode("utf-8")).hexdigest()
    return {
        "schema": CHUNK_SET_SCHEMA,
        "chunk_set_id": f"chunks.{safe_id(index.get('index_id'))}.{index_fingerprint[:12]}",
        "generated_at": generated_at,
        "source_index_id": index.get("index_id"),
        "source_index_schema": index.get("schema"),
        "chunks": chunks,
        "citations": citations,
        "diagnostics": diagnostics,
        "provenance": {
            "generator": "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh",
            "generator_version": GENERATOR_VERSION,
            "git_commit": git_commit,
            "source_index_id": index.get("index_id"),
            "source_index_git_commit": (index.get("provenance") or {}).get("git_commit"),
            "source_index_fingerprint": index_fingerprint,
        },
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    index, raw_index = load_index(args)
    chunk_set = build_chunk_set(index, raw_index)
    json.dump(chunk_set, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if chunk_set["diagnostics"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

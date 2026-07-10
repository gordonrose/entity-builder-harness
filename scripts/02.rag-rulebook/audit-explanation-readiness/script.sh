#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.audit-explanation-readiness
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Audit governed Markdown source material and guides for human explanation readiness.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.plan.explanation-aware-chunking-and-retrieval
#       path: .agentic/02.rag-rulebook/plans/explanation-aware-chunking-and-retrieval.md
#     - id: rag-rulebook.script.audit-explanation-readiness.readme
#       path: scripts/02.rag-rulebook/audit-explanation-readiness/README.md
#     - id: rag-rulebook.script.audit-explanation-readiness.smoke-test
#       path: scripts/02.rag-rulebook/audit-explanation-readiness/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for explanation readiness audits.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/explanation-readiness-audit/v1"
INDEX_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
SOURCE_PROJECTION_MANIFEST = ".agentic/02.rag-rulebook/source-projections/v1.yml"
MARKDOWN_ROOTS = [
    "docs/harness/architecture/source-material",
    "docs/harness/architecture/guides/markdown",
    "docs/02.rag-rulebook/source-material",
    "docs/04.deploy/source-material",
    ".agentic/02.rag-rulebook/guides",
]
WEAK_HEADING_TITLES = {
    "background",
    "context",
    "notes",
    "overview",
    "purpose",
    "scope",
    "status",
    "summary",
    "tbd",
    "todo",
}
TEACHING_TERMS = {
    "allowed",
    "boundary",
    "boundaries",
    "capability",
    "contract",
    "contracts",
    "decision",
    "deployment",
    "disallowed",
    "example",
    "examples",
    "guide",
    "how",
    "mental",
    "model",
    "ownership",
    "policy",
    "provider",
    "rationale",
    "readiness",
    "runtime",
    "surface",
    "surfaces",
    "why",
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
  audit-explanation-readiness/script.sh --current [--json]

Audits governed Markdown source material and guides for human explanation
readiness. The command is read-only: it builds temporary current index/chunk
outputs, compares approved Markdown source roots against source-explanation
chunks, and reports whether each source is ready, weak, or not chunked.
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


def markdown_sources() -> list[str]:
    paths: list[Path] = []
    for root in MARKDOWN_ROOTS:
        root_path = repo_path(root)
        if not root_path.exists():
            continue
        paths.extend(
            path
            for path in root_path.rglob("*.md")
            if path.is_file() and path.name != "README.md"
        )
    return sorted({rel(path) for path in paths})


def parse_metadata_header(path: str) -> dict[str, Any]:
    text = repo_path(path).read_text(encoding="utf-8")
    markdown_match = re.match(r"\s*<!--\s*agentic-artifact:\s*\n(.*?)\n\s*-->", text, re.DOTALL)
    if not markdown_match:
        return {}
    data = yaml.safe_load(markdown_match.group(1)) or {}
    return data if isinstance(data, dict) else {}


def load_yaml(path: str) -> dict[str, Any]:
    candidate = repo_path(path)
    if not candidate.is_file():
        return {}
    data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def list_of_strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def run_current_index_and_chunks() -> tuple[dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="explanation-readiness-") as raw_tmp:
        tmp = Path(raw_tmp)
        index_path = tmp / "rulebook-index.json"
        with index_path.open("w", encoding="utf-8") as handle:
            subprocess.run(
                ["bash", INDEX_GENERATOR_SCRIPT, "--pretty"],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=handle,
            )
        with (tmp / "rulebook-chunks.json").open("w", encoding="utf-8") as handle:
            subprocess.run(
                ["bash", CHUNK_GENERATOR_SCRIPT, "--index", str(index_path), "--pretty"],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=handle,
            )
        index = json.loads(index_path.read_text(encoding="utf-8"))
        chunks = json.loads((tmp / "rulebook-chunks.json").read_text(encoding="utf-8"))
        return index, chunks


def source_projection_refs() -> dict[str, dict[str, Any]]:
    manifest = load_yaml(SOURCE_PROJECTION_MANIFEST)
    refs: dict[str, dict[str, Any]] = defaultdict(lambda: {"projection_ids": [], "selector_evaluations": []})
    for projection in list_of_dicts(manifest.get("projection_sets")):
        projection_id = projection.get("id")
        evaluations = list_of_strings(projection.get("expected_selector_evaluations"))
        for item in list_of_dicts(projection.get("source_material")):
            path = item.get("path")
            if not isinstance(path, str):
                continue
            if isinstance(projection_id, str):
                refs[path]["projection_ids"].append(projection_id)
            refs[path]["selector_evaluations"].extend(evaluations)
    return {path: dict(value) for path, value in refs.items()}


def weak_heading_issues(sections: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not sections:
        return ["no-chunkable-markdown-sections"]
    if len(sections) == 1:
        issues.append("single-section-outline")
    weak_titles = []
    for section in sections:
        title = str(section.get("heading_title") or "").strip()
        normalized = title.strip("`").lower()
        if normalized in WEAK_HEADING_TITLES:
            weak_titles.append(str(section.get("heading_path") or title))
    if weak_titles and len(weak_titles) == len(sections):
        issues.append("only-generic-heading-titles")
    issues.extend(f"weak-heading-title:{title}" for title in weak_titles[:8])
    return issues


def explanation_value(source: dict[str, Any]) -> str:
    score = 0
    sections = list_of_dicts(source.get("source_explanation_sections"))
    if source.get("chunked"):
        score += 2
    if len(sections) >= 2:
        score += 1
    if any(str(section.get("heading_title") or "").strip("`").lower() not in WEAK_HEADING_TITLES for section in sections):
        score += 1
    heading_text = " ".join(str(section.get("heading_path") or "") for section in sections).lower()
    if any(term in heading_text for term in TEACHING_TERMS):
        score += 1
    if int(source.get("source_explanation_token_estimate") or 0) >= 120:
        score += 1
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    if score >= 1:
        return "low"
    return "none"


def repair_source(path: str, source_kind: str, readiness_status: str) -> str:
    if readiness_status == "ready":
        return "none"
    if source_kind == "guide" or "/guides/" in path:
        return "guide"
    return "source-material"


def build_report() -> dict[str, Any]:
    errors: list[str] = []
    index, chunks = run_current_index_and_chunks()
    projections = source_projection_refs()

    artifacts_by_path = {
        artifact.get("current_path"): artifact
        for artifact in list_of_dicts(index.get("artifacts"))
        if isinstance(artifact.get("current_path"), str)
    }
    candidates_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in list_of_dicts(index.get("chunk_candidates")):
        if candidate.get("content_kind") == "source-explanation" and isinstance(candidate.get("source_path"), str):
            candidates_by_path[candidate["source_path"]].append(candidate)

    rendered_source_chunks_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    execution_rule_chunks_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in list_of_dicts(chunks.get("chunks")):
        source_path = chunk.get("source_path")
        if chunk.get("content_kind") == "source-explanation" and isinstance(source_path, str):
            rendered_source_chunks_by_path[source_path].append(chunk)
        derivation = chunk.get("source_derivation")
        if chunk.get("authority") == "execution-authority" and isinstance(derivation, dict):
            for source in list_of_dicts(derivation.get("source_material")):
                path = source.get("path")
                if isinstance(path, str):
                    execution_rule_chunks_by_path[path].append(chunk)

    sources: list[dict[str, Any]] = []
    for path in markdown_sources():
        metadata = parse_metadata_header(path)
        artifact = artifacts_by_path.get(path) or {}
        candidates = sorted(candidates_by_path.get(path, []), key=lambda item: (item.get("line_start") or 0, item.get("chunk_id") or ""))
        rendered_chunks = rendered_source_chunks_by_path.get(path, [])
        execution_chunks = execution_rule_chunks_by_path.get(path, [])
        source_kind = str(metadata.get("kind") or artifact.get("artifact_type") or "unknown")
        sections = [
            {
                "chunk_id": candidate.get("chunk_id"),
                "heading_title": candidate.get("heading_title"),
                "heading_path": candidate.get("heading_path"),
                "line_start": candidate.get("line_start"),
                "line_end": candidate.get("line_end"),
                "token_estimate": candidate.get("token_estimate"),
            }
            for candidate in candidates
        ]
        token_estimate = sum(
            int(candidate.get("token_estimate") or 0)
            for candidate in candidates
            if isinstance(candidate.get("token_estimate"), int)
        )
        issues = []
        if not metadata:
            issues.append("missing-agentic-artifact-metadata")
        if not artifact:
            issues.append("not-indexed")
        issues.extend(weak_heading_issues(sections))
        source = {
            "path": path,
            "metadata_id": metadata.get("id") or artifact.get("metadata_id"),
            "title": artifact.get("title") or metadata.get("purpose") or Path(path).stem,
            "source_kind": source_kind,
            "corpus_id": artifact.get("corpus_id"),
            "artifact_ref": artifact.get("artifact_ref"),
            "chunked": bool(rendered_chunks),
            "source_explanation_chunk_count": len(rendered_chunks),
            "source_explanation_section_count": len(sections),
            "source_explanation_token_estimate": token_estimate,
            "source_explanation_sections": sections,
            "weak_or_missing_heading_issues": issues,
            "execution_authority_status": (
                "has-execution-authority"
                if execution_chunks
                else "explanation-only-guide"
                if source_kind == "guide" or "/guides/" in path
                else "support-only"
            ),
            "execution_rule_ids": sorted(
                {
                    rule_id
                    for chunk in execution_chunks
                    for rule_id in list_of_strings(chunk.get("rule_ids"))
                }
            ),
            "projection_ids": sorted(set(list_of_strings(projections.get(path, {}).get("projection_ids")))),
            "selector_evaluations": sorted(set(list_of_strings(projections.get(path, {}).get("selector_evaluations")))),
        }
        value = explanation_value(source)
        source["explanation_value"] = value
        if not artifact:
            readiness_status = "gap:not-indexed"
        elif not rendered_chunks:
            readiness_status = "gap:not-chunked"
        elif value in {"none", "low"}:
            readiness_status = "gap:weak-explanation"
        else:
            readiness_status = "ready"
        source["readiness_status"] = readiness_status
        source["recommended_repair_source"] = repair_source(path, source_kind, readiness_status)
        sources.append(source)

    counts = {
        "sources": len(sources),
        "ready": sum(1 for source in sources if source["readiness_status"] == "ready"),
        "gaps": sum(1 for source in sources if source["readiness_status"] != "ready"),
        "chunked": sum(1 for source in sources if source["chunked"]),
        "with_execution_authority": sum(1 for source in sources if source["execution_authority_status"] == "has-execution-authority"),
        "source_explanation_chunks": sum(int(source["source_explanation_chunk_count"]) for source in sources),
    }
    return {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "counts": counts,
        "source_roots": MARKDOWN_ROOTS,
        "sources": sources,
        "gaps": [
            {
                "path": source["path"],
                "readiness_status": source["readiness_status"],
                "recommended_repair_source": source["recommended_repair_source"],
                "issues": source["weak_or_missing_heading_issues"],
            }
            for source in sources
            if source["readiness_status"] != "ready"
        ],
        "errors": errors,
    }


def print_human(report: dict[str, Any]) -> None:
    counts = report["counts"]
    print(
        "Explanation readiness audit: "
        f"{counts['ready']}/{counts['sources']} ready, "
        f"{counts['gaps']} gap(s), "
        f"{counts['source_explanation_chunks']} source-explanation chunk(s)."
    )
    for gap in report["gaps"]:
        print(f"- {gap['readiness_status']}: {gap['path']} -> repair: {gap['recommended_repair_source']}")
        for issue in gap["issues"][:4]:
            print(f"  issue: {issue}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

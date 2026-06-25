#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-recognition-sources
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate deterministic RAG/rulebook recognition-source YAML from artifact metadata indexes.
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
#     - id: rag-rulebook.recognition-source.generated.artifacts
#       path: .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
#     - id: rag-rulebook.script.generate-recognition-sources.readme
#       path: scripts/02.rag-rulebook/generate-recognition-sources/README.md
#     - id: rag-rulebook.script.generate-recognition-sources.smoke-test
#       path: scripts/02.rag-rulebook/generate-recognition-sources/smoke-test.sh
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for recognition-source generation.", file=sys.stderr)
    sys.exit(2)


DEFAULT_OUTPUT = ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml"
SOURCE_SCHEMA = "rag-rulebook/recognition-source/v1"
EXCLUDED_PREFIXES = (
    ".agentic/02.rag-rulebook/recognition-sources/",
)


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
  generate-recognition-sources/script.sh --print
  generate-recognition-sources/script.sh --output <path>
  generate-recognition-sources/script.sh --check [--output <path>]

Generates recognition.generated.artifacts from the existing artifact metadata
index. The generated source is deterministic and contains no timestamps.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--print", dest="print_output", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.print_output and (args.check or args.output is not None):
        print("ERROR: choose one mode: --print, --output, or --check.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if not args.print_output and not args.check and args.output is None:
        print("ERROR: choose one mode: --print, --output, or --check.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.check and args.output is None:
        args.output = DEFAULT_OUTPUT
    return args


def run_artifact_index() -> dict[str, Any]:
    result = subprocess.run(
        [
            "bash",
            "scripts/01.harness/artifact-metadata/generate-index/script.sh",
            "--all",
            "--strict",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def id_category(kind: str | None) -> str:
    if kind == "rule":
        return "rule-id"
    if kind in {"rule-pack", "ruleset", "layer-ruleset"}:
        return "rule-pack-id"
    return "artifact-id"


def add_term(
    terms: list[dict[str, Any]],
    seen_terms: set[str],
    *,
    term: str | None,
    category: str,
    canonical_id: str,
    evidence_path: str,
) -> None:
    if not term:
        return
    normalized = term.strip()
    if not normalized:
        return
    key = normalized.lower()
    if key in seen_terms:
        return
    seen_terms.add(key)
    terms.append(
        {
            "term": normalized,
            "category": category,
            "match_type": "exact",
            "canonical_id": canonical_id,
            "evidence_path": evidence_path,
            "confidence_weight": 1,
        }
    )


def build_source(index: dict[str, Any]) -> dict[str, Any]:
    artifacts = [
        artifact
        for artifact in index.get("artifacts", [])
        if isinstance(artifact, dict)
        and not artifact.get("legacy")
        and isinstance(artifact.get("id"), str)
        and isinstance(artifact.get("path"), str)
        and not any(str(artifact["path"]).startswith(prefix) for prefix in EXCLUDED_PREFIXES)
    ]
    artifacts.sort(key=lambda item: (str(item.get("layer") or ""), str(item.get("path") or "")))

    terms: list[dict[str, Any]] = []
    seen_terms: set[str] = set()
    for artifact in artifacts:
        artifact_id = str(artifact["id"])
        path = str(artifact["path"])
        kind = artifact.get("kind")

        add_term(
            terms,
            seen_terms,
            term=artifact_id,
            category=id_category(kind if isinstance(kind, str) else None),
            canonical_id=artifact_id,
            evidence_path=path,
        )
        add_term(
            terms,
            seen_terms,
            term=path,
            category="file-path",
            canonical_id=artifact_id,
            evidence_path=path,
        )
        if kind == "schema":
            add_term(
                terms,
                seen_terms,
                term=Path(path).name,
                category="schema-name",
                canonical_id=artifact_id,
                evidence_path=path,
            )

    return {
        "schema": SOURCE_SCHEMA,
        "source_id": "recognition.generated.artifacts",
        "version": 1,
        "status": "active",
        "source_kinds": [
            "artifact-id",
            "file-path",
            "schema-name",
            "rule-id",
            "rule-pack-id",
        ],
        "generation_mode": "generated",
        "owner_layer": "02.rag-rulebook",
        "purpose": "Recognize exact governed repo artifacts, paths, schemas, rule IDs, and rule-pack IDs from artifact metadata.",
        "match_priority": 10,
        "used_by_dimensions": [
            "prompt",
        ],
        "source_artifacts": [
            ".agentic/01.harness/artifact-metadata/schema.v2.yml",
            ".agentic/01.harness/artifact-metadata/taxonomy.yml",
            "scripts/01.harness/artifact-metadata/generate-index/script.sh",
        ],
        "generation_command": f"scripts/02.rag-rulebook/generate-recognition-sources/script.sh --output {DEFAULT_OUTPUT}",
        "generation_summary": {
            "artifact_index_schema": index.get("schema"),
            "indexed_artifacts": len(artifacts),
            "term_count": len(terms),
            "excluded_prefixes": list(EXCLUDED_PREFIXES),
        },
        "terms": terms,
        "validation_rules": [
            "Generated terms must retain evidence paths.",
            "Generated terms must be regenerated when artifact metadata headers, indexed paths, or the artifact metadata indexer change.",
            "Generated terms must not include duplicate canonical lookup terms.",
            "Generated recognition sources must stay deterministic and omit timestamps.",
        ],
        "refresh_policy": {
            "trigger": "Regenerate when artifact metadata headers, indexed paths, or artifact metadata index generation logic changes.",
            "owner": "02.rag-rulebook",
            "review_required_when": [
                "Changing source_kinds.",
                "Changing term category mapping.",
                "Changing excluded generated-output prefixes.",
            ],
        },
    }


def render_source(source: dict[str, Any]) -> str:
    header = """# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.recognition-source.generated.artifacts
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: recognition-source
#   purpose: Generated lookup source for exact artifact IDs, paths, schemas, rule IDs, and rule-pack IDs.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   used_by:
#     - id: rag-rulebook.script.generate-recognition-sources
#       path: scripts/02.rag-rulebook/generate-recognition-sources/script.sh
#     - id: rag-rulebook.script.validate-recognition-sources
#       path: scripts/02.rag-rulebook/validate-recognition-sources/script.sh
#     - id: rag-rulebook.policy.retrieval-selector.v1.dimension.prompt
#       path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml
"""
    return header + "\n" + yaml.safe_dump(source, sort_keys=False, allow_unicode=False)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    rendered = render_source(build_source(run_artifact_index()))

    if args.print_output:
        print(rendered, end="")
        return 0

    output_path = ROOT / args.output

    if args.check:
        if not output_path.exists():
            print(f"ERROR: generated recognition source is missing: {args.output}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile=args.output,
                tofile=f"{args.output} (regenerated)",
                lineterm="",
            )
            print("ERROR: generated recognition source is stale.", file=sys.stderr)
            for line in diff:
                print(line, file=sys.stderr)
            return 1
        print(f"Generated recognition source is current: {args.output}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Generated recognition source: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

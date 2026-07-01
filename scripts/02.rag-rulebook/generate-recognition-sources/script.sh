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
#   purpose: Generate deterministic RAG/rulebook recognition-source YAML from governed repo sources.
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
#     - id: rag-rulebook.recognition-source.generated.routing
#       path: .agentic/02.rag-rulebook/recognition-sources/generated/routing.yml
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
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for recognition-source generation.", file=sys.stderr)
    sys.exit(2)


SOURCE_SCHEMA = "rag-rulebook/recognition-source/v1"
SOURCE_ORDER = ("artifacts", "routing")
DEFAULT_OUTPUTS = {
    "artifacts": ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml",
    "routing": ".agentic/02.rag-rulebook/recognition-sources/generated/routing.yml",
}
ARTIFACT_EXCLUDED_PREFIXES = (
    ".agentic/02.rag-rulebook/recognition-sources/",
)
ROUTING_SOURCE_ARTIFACTS = [
    ".agentic/01.harness/artifact-metadata/taxonomy.yml",
    ".agentic/routing-policy.yaml",
    ".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml",
]


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
  generate-recognition-sources/script.sh --print [--source artifacts|routing]
  generate-recognition-sources/script.sh --output <path> [--source artifacts|routing]
  generate-recognition-sources/script.sh --write-all
  generate-recognition-sources/script.sh --check [--source artifacts|routing|all] [--output <path>]

Generates deterministic recognition sources from governed repo sources:
artifacts from the artifact metadata index, and routing from layer, mode,
corpus, and workflow policy files.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--print", dest="print_output", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-all", action="store_true")
    parser.add_argument("--source", choices=["artifacts", "routing", "all"])
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)

    if args.print_output:
        if args.output is not None or args.check or args.write_all:
            fail_mode()
        args.source = args.source or "artifacts"
        if args.source == "all":
            print("ERROR: --print requires --source artifacts or --source routing.", file=sys.stderr)
            sys.exit(2)
        return args

    if args.output is not None:
        if args.write_all:
            fail_mode()
        args.source = args.source or "artifacts"
        if args.source == "all":
            print("ERROR: --output requires --source artifacts or --source routing.", file=sys.stderr)
            sys.exit(2)
        return args

    if args.check:
        args.source = args.source or "all"
        return args

    if args.write_all:
        if args.source not in {None, "all"}:
            print("ERROR: --write-all cannot be combined with a single --source.", file=sys.stderr)
            sys.exit(2)
        args.source = "all"
        return args

    fail_mode()
    return args


def fail_mode() -> None:
    print("ERROR: choose one mode: --print, --output, --write-all, or --check.", file=sys.stderr)
    print(usage(), end="", file=sys.stderr)
    sys.exit(2)


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


def load_yaml(path: str) -> dict[str, Any]:
    data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML object: {path}")
    return data


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
    key = f"{category}:{normalized.lower()}"
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


def build_artifacts_source(index: dict[str, Any]) -> dict[str, Any]:
    artifacts = [
        artifact
        for artifact in index.get("artifacts", [])
        if isinstance(artifact, dict)
        and not artifact.get("legacy")
        and isinstance(artifact.get("id"), str)
        and isinstance(artifact.get("path"), str)
        and not any(str(artifact["path"]).startswith(prefix) for prefix in ARTIFACT_EXCLUDED_PREFIXES)
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
        "generation_command": (
            "scripts/02.rag-rulebook/generate-recognition-sources/script.sh "
            f"--source artifacts --output {DEFAULT_OUTPUTS['artifacts']}"
        ),
        "generation_summary": {
            "artifact_index_schema": index.get("schema"),
            "indexed_artifacts": len(artifacts),
            "term_count": len(terms),
            "excluded_prefixes": list(ARTIFACT_EXCLUDED_PREFIXES),
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


def workflow_paths() -> list[str]:
    paths: list[str] = []
    for path in sorted((ROOT / ".agentic").glob("**/workflows/*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if path.name == "README.md":
            continue
        paths.append(rel)
    return paths


def workflow_canonical_id(path: str) -> str:
    parts = Path(path).parts
    if len(parts) >= 4:
        layer = parts[1]
        stem = Path(path).stem
        return f"{layer}.workflow.{stem}"
    return path


def build_routing_source() -> dict[str, Any]:
    taxonomy = load_yaml(".agentic/01.harness/artifact-metadata/taxonomy.yml")
    routing = load_yaml(".agentic/routing-policy.yaml")
    policy = load_yaml(".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml")

    terms: list[dict[str, Any]] = []
    seen_terms: set[str] = set()

    layer_id_by_slug: dict[str, str] = {
        "chat": "00.chat",
        "harness": "01.harness",
        "rag-rulebook": "02.rag-rulebook",
        "product": "03.product",
        "aws": "04.deploy",
        "deploy": "04.deploy",
        "education": "05.education",
        "shared": "06.shared",
    }

    for layer in taxonomy.get("layers", []):
        if not isinstance(layer, dict) or not isinstance(layer.get("id"), str):
            continue
        layer_id = layer["id"]
        add_term(
            terms,
            seen_terms,
            term=layer_id,
            category="layer-name",
            canonical_id=layer_id,
            evidence_path=".agentic/01.harness/artifact-metadata/taxonomy.yml",
        )
        title = layer.get("title")
        if isinstance(title, str):
            add_term(
                terms,
                seen_terms,
                term=title,
                category="layer-name",
                canonical_id=layer_id,
                evidence_path=".agentic/01.harness/artifact-metadata/taxonomy.yml",
            )

    routing_layers = routing.get("layers", {})
    if isinstance(routing_layers, dict):
        for slug in sorted(routing_layers):
            canonical_id = layer_id_by_slug.get(slug, slug)
            add_term(
                terms,
                seen_terms,
                term=slug,
                category="layer-name",
                canonical_id=canonical_id,
                evidence_path=".agentic/routing-policy.yaml",
            )
            workflow_index = routing_layers.get(slug, {}).get("workflow_index")
            if isinstance(workflow_index, str):
                add_term(
                    terms,
                    seen_terms,
                    term=workflow_index,
                    category="workflow-name",
                    canonical_id=workflow_index,
                    evidence_path=".agentic/routing-policy.yaml",
                )

    for mode in routing.get("mode_order", []):
        if isinstance(mode, str) and mode != "unknown":
            add_term(
                terms,
                seen_terms,
                term=mode,
                category="mode-name",
                canonical_id=mode,
                evidence_path=".agentic/routing-policy.yaml",
            )

    applies_to = policy.get("applies_to", {})
    if isinstance(applies_to, dict):
        for corpus_id in applies_to.get("corpus_ids", []):
            if isinstance(corpus_id, str):
                add_term(
                    terms,
                    seen_terms,
                    term=corpus_id,
                    category="corpus-id",
                    canonical_id=corpus_id,
                    evidence_path=".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml",
                )
        for layer_mode in applies_to.get("layer_modes", []):
            if not isinstance(layer_mode, str):
                continue
            add_term(
                terms,
                seen_terms,
                term=layer_mode,
                category="mode-name",
                canonical_id=layer_mode,
                evidence_path=".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml",
            )
        for workflow in applies_to.get("workflows", []):
            if isinstance(workflow, str):
                add_term(
                    terms,
                    seen_terms,
                    term=workflow,
                    category="workflow-name",
                    canonical_id=workflow,
                    evidence_path=".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml",
                )

    for path in workflow_paths():
        canonical_id = workflow_canonical_id(path)
        add_term(
            terms,
            seen_terms,
            term=path,
            category="workflow-name",
            canonical_id=canonical_id,
            evidence_path=path,
        )
        add_term(
            terms,
            seen_terms,
            term=Path(path).name,
            category="workflow-name",
            canonical_id=canonical_id,
            evidence_path=path,
        )

    terms.sort(key=lambda item: (item["category"], item["term"]))

    return {
        "schema": SOURCE_SCHEMA,
        "source_id": "recognition.generated.routing",
        "version": 1,
        "status": "active",
        "source_kinds": [
            "corpus-id",
            "layer-name",
            "mode-name",
            "workflow-name",
        ],
        "generation_mode": "generated",
        "owner_layer": "02.rag-rulebook",
        "purpose": "Recognize governed layer, mode, corpus, and workflow routing terms from routing policy and retrieval policy sources.",
        "match_priority": 20,
        "used_by_dimensions": [
            "prompt",
            "layer-mode-workflow",
            "corpus-ownership",
        ],
        "source_artifacts": [
            *ROUTING_SOURCE_ARTIFACTS,
            ".agentic/02.rag-rulebook/workflows/default.md",
        ],
        "generation_command": (
            "scripts/02.rag-rulebook/generate-recognition-sources/script.sh "
            f"--source routing --output {DEFAULT_OUTPUTS['routing']}"
        ),
        "generation_summary": {
            "term_count": len(terms),
            "workflow_files": len(workflow_paths()),
            "corpus_ids": len(applies_to.get("corpus_ids", [])) if isinstance(applies_to, dict) else 0,
            "mode_terms": len([term for term in terms if term["category"] == "mode-name"]),
        },
        "terms": terms,
        "validation_rules": [
            "Generated routing terms must retain evidence paths.",
            "Generated routing terms must be regenerated when routing policy, layer taxonomy, retrieval policy, or workflow files change.",
            "Generated routing terms must not include duplicate category/term pairs.",
            "Generated recognition sources must stay deterministic and omit timestamps.",
        ],
        "refresh_policy": {
            "trigger": "Regenerate when routing policy, layer taxonomy, retrieval policy, or workflow files change.",
            "owner": "02.rag-rulebook",
            "review_required_when": [
                "Changing source_kinds.",
                "Changing layer slug to layer ID mappings.",
                "Changing workflow term generation.",
                "Changing corpus or mode source policy.",
            ],
        },
    }


def build_source(source_name: str, index: dict[str, Any] | None = None) -> dict[str, Any]:
    if source_name == "artifacts":
        return build_artifacts_source(index if index is not None else run_artifact_index())
    if source_name == "routing":
        return build_routing_source()
    raise ValueError(f"Unsupported source: {source_name}")


def source_header(source_name: str) -> str:
    if source_name == "artifacts":
        artifact_id = "rag-rulebook.recognition-source.generated.artifacts"
        purpose = "Generated lookup source for exact artifact IDs, paths, schemas, rule IDs, and rule-pack IDs."
        prompt_dimension = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml"
    elif source_name == "routing":
        artifact_id = "rag-rulebook.recognition-source.generated.routing"
        purpose = "Generated lookup source for governed layer, mode, corpus, and workflow routing terms."
        prompt_dimension = ".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml"
    else:
        raise ValueError(f"Unsupported source: {source_name}")

    return f"""# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: {artifact_id}
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: recognition-source
#   purpose: {purpose}
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
#       path: {prompt_dimension}
"""


def render_source(source_name: str, source: dict[str, Any]) -> str:
    return source_header(source_name) + "\n" + yaml.safe_dump(source, sort_keys=False, allow_unicode=False)


def requested_sources(source: str) -> list[str]:
    if source == "all":
        return list(SOURCE_ORDER)
    return [source]


def rendered_sources(source_names: list[str]) -> dict[str, str]:
    index = run_artifact_index() if "artifacts" in source_names else None
    return {
        source_name: render_source(source_name, build_source(source_name, index=index))
        for source_name in source_names
    }


def check_output(path: Path, label: str, rendered: str) -> int:
    if not path.exists():
        print(f"ERROR: generated recognition source is missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    current = path.read_text(encoding="utf-8")
    if current != rendered:
        diff = difflib.unified_diff(
            current.splitlines(),
            rendered.splitlines(),
            fromfile=path.relative_to(ROOT).as_posix(),
            tofile=f"{path.relative_to(ROOT).as_posix()} (regenerated)",
            lineterm="",
        )
        print(f"ERROR: generated recognition source is stale: {label}", file=sys.stderr)
        for line in diff:
            print(line, file=sys.stderr)
        return 1
    print(f"Generated recognition source is current: {path.relative_to(ROOT).as_posix()}")
    return 0


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.print_output:
        source_name = args.source
        rendered = rendered_sources([source_name])[source_name]
        print(rendered, end="")
        return 0

    if args.output is not None:
        source_name = args.source
        rendered = rendered_sources([source_name])[source_name]
        output_path = ROOT / args.output
        if args.check:
            return check_output(output_path, source_name, rendered)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Generated recognition source: {args.output}")
        return 0

    source_names = requested_sources(args.source)
    rendered_by_source = rendered_sources(source_names)

    if args.check:
        failures = 0
        for source_name in source_names:
            path = ROOT / DEFAULT_OUTPUTS[source_name]
            failures += check_output(path, source_name, rendered_by_source[source_name])
        return 1 if failures else 0

    for source_name in source_names:
        output_path = ROOT / DEFAULT_OUTPUTS[source_name]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_by_source[source_name], encoding="utf-8")
        print(f"Generated recognition source: {DEFAULT_OUTPUTS[source_name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

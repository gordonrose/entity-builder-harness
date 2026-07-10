#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-rulebook-index
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: indexing
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate a read-only JSON rulebook index from prototype and numbered corpus rule roots.
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
#     - id: rag-rulebook.script.generate-rulebook-index.readme
#       path: scripts/02.rag-rulebook/generate-rulebook-index/README.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for rulebook indexing.", file=sys.stderr)
    sys.exit(2)


DEFAULT_SOURCE_ROOT = "docs/harness/architecture"
DEFAULT_RULEBOOK_RULES_ROOT = "docs/02.rag-rulebook/rules"
DEFAULT_DEPLOY_RULES_ROOT = "docs/04.deploy/rules"
DEFAULT_MIGRATION_MAP = ".agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml"
INDEX_SCHEMA = "rag-rulebook/rulebook-index/v1"
GENERATOR_VERSION = "prototype-v1"
CURRENT_RULEBOOK_CORPUS_ID = "corpus.02.rag-rulebook"
HARNESS_CORPUS_ID = "corpus.01.harness"
DEFAULT_CORPUS_RULE_ROOTS = (
    (CURRENT_RULEBOOK_CORPUS_ID, DEFAULT_RULEBOOK_RULES_ROOT),
    ("corpus.04.deploy", DEFAULT_DEPLOY_RULES_ROOT),
)
SUPPORTING_SOURCE_ENTRIES = (
    {
        "current_path": ".agentic/01.harness/artifact-metadata/README.md",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "readme",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-metadata-capability"],
            "answers_questions_about": ["how harness artifact metadata is organized"],
            "produces": [],
            "consumes": ["agentic-artifact/v2 metadata headers"],
            "validates": [],
        },
    },
    {
        "current_path": ".agentic/01.harness/artifact-metadata/standard.md",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "standard",
        "source_type": "standard",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-metadata-standard"],
            "answers_questions_about": ["how artifact metadata headers are shaped"],
            "produces": ["agentic-artifact/v2 metadata contract"],
            "consumes": [],
            "validates": [],
        },
    },
    {
        "current_path": ".agentic/01.harness/artifact-metadata/schema.v2.yml",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "schema",
        "source_type": "schema",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-metadata-schema"],
            "answers_questions_about": ["machine-readable artifact metadata fields"],
            "produces": ["agentic-artifact/v2 field contract"],
            "consumes": [],
            "validates": ["agentic-artifact/v2 field shape"],
        },
    },
    {
        "current_path": "scripts/01.harness/artifact-metadata/check-headers/script.sh",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-header-validator"],
            "answers_questions_about": ["how artifact metadata headers are validated"],
            "produces": ["artifact metadata validation report"],
            "consumes": ["agentic-artifact/v2 metadata headers", "agentic-script metadata headers"],
            "validates": ["metadata header shape", "metadata taxonomy values"],
        },
    },
    {
        "current_path": "scripts/01.harness/artifact-metadata/generate-index/script.sh",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-index-builder"],
            "answers_questions_about": ["how the harness is indexed", "how metadata headers become an artifact index"],
            "produces": ["agentic-artifact-index"],
            "consumes": ["agentic-artifact/v2 metadata headers", "agentic-script metadata headers"],
            "validates": ["artifact metadata index"],
        },
    },
    {
        "current_path": "scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["artifact-header-backfill"],
            "answers_questions_about": ["how artifact metadata headers are added and maintained"],
            "produces": ["agentic-artifact/v2 metadata headers"],
            "consumes": ["existing artifact files", "artifact metadata standard"],
            "validates": ["changed metadata headers", "artifact metadata index"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/generate-recognition-sources/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["recognition-source-generator"],
            "answers_questions_about": ["how harness metadata becomes RAG recognition terms"],
            "produces": ["generated artifact recognition source", "generated routing recognition source"],
            "consumes": ["agentic artifact index", "routing policy", "rulebook index"],
            "validates": ["generated recognition source freshness"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/generate-rulebook-index/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["rulebook-index-builder"],
            "answers_questions_about": ["how the rulebook index is built", "how RAG knows source roots and artifacts"],
            "produces": ["rulebook index", "artifacts", "source references", "path mappings", "chunk candidates", "graph edges"],
            "consumes": ["prototype corpus migration map", "rule roots", "metadata headers"],
            "validates": [],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["chunk-generator"],
            "answers_questions_about": ["how the rulebook index becomes retrievable chunks"],
            "produces": ["rulebook chunk set", "retrieval chunks", "citations"],
            "consumes": ["rulebook index"],
            "validates": ["rulebook index before chunk generation"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/build-local-runtime/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["runtime-builder"],
            "answers_questions_about": ["how the local RAG runtime is packaged"],
            "produces": ["local runtime cache", "rulebook index cache", "chunk cache", "compiled retrieval policy"],
            "consumes": ["rulebook index", "rulebook chunks", "compiled retrieval policy", "recognition sources"],
            "validates": ["runtime freshness inputs"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/query-local-context/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["runtime-query"],
            "answers_questions_about": ["how RAG queries the built runtime", "how context packets are produced"],
            "produces": ["context packet", "compact context packet"],
            "consumes": ["local runtime cache", "request text", "session metadata"],
            "validates": ["runtime freshness", "context packet"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["retrieval-selector"],
            "answers_questions_about": ["how RAG uses the index to find content", "how chunks are selected and ranked"],
            "produces": ["selected chunks", "selector trace", "context packet"],
            "consumes": ["rulebook chunks", "compiled retrieval policy", "recognition sources", "request text"],
            "validates": ["selected context packet"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/compile-retrieval-policy/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["retrieval-policy-compiler"],
            "answers_questions_about": ["how retrieval policy dimensions become selector policy"],
            "produces": ["compiled retrieval policy"],
            "consumes": ["retrieval selector policy pack", "retrieval policy dimensions"],
            "validates": ["retrieval policy pack"],
        },
    },
    {
        "current_path": "docs/02.rag-rulebook/source-material/rag-retrieval.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "source-material",
        "source_type": "source-material",
        "retrieval_profile": {
            "retrieval_roles": ["rag-retrieval-source-of-truth"],
            "answers_questions_about": ["how RAG retrieval works", "how source material becomes context packets"],
            "produces": ["RAG retrieval source-of-truth guidance"],
            "consumes": ["repo source material", "artifact metadata", "recognition sources"],
            "validates": [],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/corpus-gaps/02.rag-rulebook/rag-retrieval-source-of-truth.yml",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "corpus-gap",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["rag-retrieval-gap"],
            "answers_questions_about": ["which RAG retrieval source-of-truth coverage is still incomplete"],
            "produces": ["retrieval coverage gap"],
            "consumes": ["RAG retrieval source material"],
            "validates": ["selector fixture coverage expectations"],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/illustrative-example-paths-deprioritized.yml",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "evaluation-fixture",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["example-deprioritization-fixture"],
            "answers_questions_about": ["how illustrative paths are deprioritized"],
            "produces": ["selector proof for example-only paths"],
            "consumes": ["prompt recognition policy"],
            "validates": ["example context deprioritization"],
        },
    },
    {
        "current_path": ".agentic/00.chat/workflows/chat-start.md",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "workflow",
        "source_type": "workflow",
        "retrieval_profile": {
            "retrieval_roles": ["chat-lifecycle-workflow"],
            "answers_questions_about": ["what 00.chat owns", "how chat lifecycle differs from RAG routing"],
            "produces": ["chat session lifecycle context"],
            "consumes": ["opening user message", "session metadata"],
            "validates": ["chat-owned worktree"],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/standards/retrieval-selector-policy-system.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "standard",
        "source_type": "standard",
        "retrieval_profile": {
            "retrieval_roles": ["retrieval-selector-policy-standard"],
            "answers_questions_about": ["how prompt request context drives RAG routing"],
            "produces": ["retrieval selector policy rules"],
            "consumes": ["recognition sources", "request context"],
            "validates": ["selector policy expectations"],
        },
    },
    {
        "current_path": "docs/02.rag-rulebook/source-material/hosted-context-provider-contract.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "source-material",
        "source_type": "source-material",
        "retrieval_profile": {
            "retrieval_roles": ["hosted-context-provider-source"],
            "answers_questions_about": ["how hosted RAG provider contracts work"],
            "produces": ["hosted context provider source guidance"],
            "consumes": ["local RAG runtime", "HTTP service contract"],
            "validates": [],
        },
    },
    {
        "current_path": "docs/02.rag-rulebook/postman/README.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "readme",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["hosted-rag-postman"],
            "answers_questions_about": ["how to test hosted RAG with Postman"],
            "produces": ["Postman collection usage guidance"],
            "consumes": ["hosted RAG HTTP endpoints"],
            "validates": ["service smoke test workflow"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/query-local-context/README.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "readme",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["local-context-query-readme"],
            "answers_questions_about": ["how compact and full context packets are queried locally"],
            "produces": ["query-local-context usage guidance"],
            "consumes": ["local runtime cache", "request text"],
            "validates": ["context packet output"],
        },
    },
    {
        "current_path": "scripts/02.rag-rulebook/commit-gates/script.sh",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["rag-rulebook-commit-gate"],
            "answers_questions_about": ["which RAG rulebook checks run before commit"],
            "produces": ["RAG commit gate result"],
            "consumes": ["recognition sources", "retrieval policy", "selector fixtures", "runtime files"],
            "validates": ["RAG rulebook changes"],
        },
    },
    {
        "current_path": "scripts/repo/commit-gates/script.sh",
        "corpus_id": HARNESS_CORPUS_ID,
        "artifact_type": "script",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["repo-commit-gate"],
            "answers_questions_about": ["how repository-wide commit gates invoke layer checks"],
            "produces": ["repo commit gate result"],
            "consumes": ["layer commit gates"],
            "validates": ["repository changes before commit"],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/standards/retrieval-selector-evaluations.md",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "standard",
        "source_type": "standard",
        "retrieval_profile": {
            "retrieval_roles": ["retrieval-selector-evaluation-standard"],
            "answers_questions_about": ["how retrieval selector fixtures should prove behavior"],
            "produces": ["selector evaluation requirements"],
            "consumes": ["selector fixtures", "context packets"],
            "validates": ["retrieval selector behavior"],
        },
    },
    {
        "current_path": "packages/core/README.md",
        "corpus_id": "corpus.03.product.core",
        "artifact_type": "readme",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["packages-core-overview"],
            "answers_questions_about": ["what packages/core owns"],
            "produces": ["core package orientation"],
            "consumes": ["platform-independent runtime contracts"],
            "validates": [],
        },
    },
    {
        "current_path": "platform/contracts/README.md",
        "corpus_id": "corpus.03.product.platform",
        "artifact_type": "readme",
        "source_type": "source",
        "retrieval_profile": {
            "retrieval_roles": ["platform-contracts-overview"],
            "answers_questions_about": ["what platform/contracts owns"],
            "produces": ["platform contract orientation"],
            "consumes": ["packages/core contracts", "runtime integration contracts"],
            "validates": [],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/request-context.yml",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "standard",
        "source_type": "standard",
        "retrieval_profile": {
            "retrieval_roles": ["request-context-policy"],
            "answers_questions_about": ["how request context influences retrieval"],
            "produces": ["request-context selector signals"],
            "consumes": ["prompt recognition matches", "session metadata"],
            "validates": [],
        },
    },
    {
        "current_path": ".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/evidence-bundles.yml",
        "corpus_id": CURRENT_RULEBOOK_CORPUS_ID,
        "artifact_type": "standard",
        "source_type": "standard",
        "retrieval_profile": {
            "retrieval_roles": ["evidence-bundle-policy"],
            "answers_questions_about": ["how canonical source paths are preserved"],
            "produces": ["required evidence source paths"],
            "consumes": ["question categories", "evidence families"],
            "validates": ["missing evidence gaps"],
        },
    },
)


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
  generate-rulebook-index/script.sh [--pretty]
  generate-rulebook-index/script.sh [--source-root <path>] [--migration-map <path>] [--rulebook-rules-root <path>] [--corpus-rules-root <corpus-id=path>] [--pretty]

Emits a rag-rulebook/rulebook-index/v1 JSON document to stdout.
The command is read-only: it parses current prototype corpus files and prints
the index without moving files or writing generated artifacts.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-root", default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--rulebook-rules-root", default=DEFAULT_RULEBOOK_RULES_ROOT)
    parser.add_argument("--corpus-rules-root", action="append", default=[])
    parser.add_argument("--migration-map", default=DEFAULT_MIGRATION_MAP)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    return args


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        return os.path.normpath(path_obj.as_posix())
    try:
        return path_obj.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path_obj.as_posix()


def repo_path(path: str) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def safe_id(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", ".", str(value or "unknown").lower()).strip(".")
    return cleaned or "unknown"


def content_hash(path: str) -> str:
    return hashlib.sha256(repo_path(path).read_bytes()).hexdigest()


def load_yaml(path: str) -> dict[str, Any]:
    with repo_path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping YAML: {path}")
    return data


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("# "):
        return stripped[2:]
    if stripped.startswith("#"):
        return stripped[1:]
    if stripped.startswith("// "):
        return stripped[3:]
    if stripped.startswith("//"):
        return stripped[2:]
    return line


def parse_metadata_header(path: str) -> dict[str, Any]:
    lines = repo_path(path).read_text(encoding="utf-8").splitlines()[:120]
    for index, line in enumerate(lines):
        if "agentic-artifact:" not in line and "agentic-script:" not in line:
            continue
        if line.lstrip().startswith("<!--"):
            marker = line.replace("<!--", "", 1).strip()
            body_lines: list[str] = []
            for following in lines[index + 1 :]:
                if "-->" in following:
                    before_end = following.split("-->", 1)[0]
                    if before_end.strip():
                        body_lines.append(before_end)
                    break
                body_lines.append(following)
            header_lines = [marker]
            header_lines.extend(f"  {body_line}" if body_line.strip() else body_line for body_line in body_lines)
        else:
            header_lines = [strip_comment(line)]
            for following in lines[index + 1 :]:
                stripped = following.lstrip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    header_lines.append(strip_comment(following))
                    continue
                if not following.strip():
                    break
                break
        parsed = yaml.safe_load("\n".join(header_lines)) or {}
        return parsed.get("agentic-artifact") or parsed.get("agentic-script") or {}
    return {}


def owner_layer_for_corpus(corpus_id: str) -> str:
    parts = corpus_id.split(".")
    if len(parts) >= 3:
        return f"{parts[1]}.{parts[2]}"
    if len(parts) >= 2:
        return parts[1]
    return "unknown"


def artifact_ref_for(rulebook_id: str | None, metadata_id: str | None, path: str) -> str:
    if rulebook_id:
        return f"artifact.{safe_id(rulebook_id)}"
    if metadata_id:
        return f"artifact.{safe_id(metadata_id)}"
    return f"artifact.path.{safe_id(path)}"


def resolve_ref_path(ref: str, owner_path: str) -> str:
    if ref.startswith(("docs/", ".agentic/", "scripts/", "AGENTS.md")):
        return normalize_path(ref)
    candidate = (repo_path(owner_path).parent / ref).resolve()
    return normalize_path(candidate)


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def artifact_type_for_group(group_name: str) -> str:
    if group_name == "layer_rulesets":
        return "layer-ruleset"
    if group_name == "concern_rulesets":
        return "concern-ruleset"
    if group_name == "rule_packs":
        return "rule-pack"
    return "source-guide"


def group_name_for_current_rulebook_path(path: str) -> str:
    if "/rule-packs/" in path:
        return "rule_packs"
    if "/layers/" in path:
        return "layer_rulesets"
    return "concern_rulesets"


def make_source_ref_id(prefix: str, value: str) -> str:
    return f"source.{safe_id(prefix)}.{safe_id(value)}"


def root_id_for_corpus_rules(corpus_id: str) -> str:
    if corpus_id == CURRENT_RULEBOOK_CORPUS_ID:
        return "root.rulebook-rules"
    return f"root.{safe_id(corpus_id)}.rules"


def default_manifest_path_for_corpus(corpus_id: str, rules_root: str) -> str | None:
    if corpus_id == CURRENT_RULEBOOK_CORPUS_ID:
        return ".agentic/02.rag-rulebook/README.md"
    root_readme = f"{rules_root.rstrip('/')}/README.md"
    if repo_path(root_readme).is_file():
        return root_readme
    corpus_readme = str(Path(rules_root).parent / "README.md")
    if repo_path(corpus_readme).is_file():
        return normalize_path(corpus_readme)
    return None


def parse_corpus_rule_roots(args: argparse.Namespace) -> list[dict[str, str]]:
    roots = {corpus_id: path for corpus_id, path in DEFAULT_CORPUS_RULE_ROOTS}
    roots[CURRENT_RULEBOOK_CORPUS_ID] = args.rulebook_rules_root
    for value in args.corpus_rules_root:
        if "=" not in value:
            print("ERROR: --corpus-rules-root must use <corpus-id=path>.", file=sys.stderr)
            sys.exit(2)
        corpus_id, path = value.split("=", 1)
        corpus_id = corpus_id.strip()
        path = path.strip()
        if not corpus_id or not path:
            print("ERROR: --corpus-rules-root requires non-empty corpus id and path.", file=sys.stderr)
            sys.exit(2)
        roots[corpus_id] = path
    return [
        {
            "corpus_id": corpus_id,
            "rules_root": normalize_path(path),
            "root_id": root_id_for_corpus_rules(corpus_id),
        }
        for corpus_id, path in sorted(roots.items())
    ]


def collect_current_rulebook_entries(corpus_id: str, rulebook_rules_root: str) -> list[tuple[str, dict[str, Any]]]:
    root = repo_path(rulebook_rules_root)
    if not root.is_dir():
        return []

    entries: list[tuple[str, dict[str, Any]]] = []
    paths = sorted({*root.rglob("*.yml"), *root.rglob("*.yaml")})
    for path in paths:
        current_path = normalize_path(path)
        yaml_data = load_yaml(current_path)
        metadata = parse_metadata_header(current_path)
        entries.append(
            (
                group_name_for_current_rulebook_path(current_path),
                {
                    "current_path": current_path,
                    "metadata_id": metadata.get("id"),
                    "rulebook_id": yaml_data.get("id"),
                    "title": yaml_data.get("title") or Path(current_path).stem,
                    "proposed_corpus_id": corpus_id,
                    "proposed_target_path": current_path,
                    "migration_status": "current",
                    "reason": f"Current structured rulebook corpus content for {corpus_id}.",
                },
            )
        )
    return entries


def build_index(source_root: str, migration_map_path: str, corpus_rule_roots: list[dict[str, str]]) -> dict[str, Any]:
    git_commit = run_git(["rev-parse", "HEAD"])
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    migration_map = load_yaml(migration_map_path)

    artifacts: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    rule_packs: list[dict[str, Any]] = []
    chunk_candidates: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    source_references: list[dict[str, Any]] = []
    path_mappings: list[dict[str, Any]] = []
    unresolved_references: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    corpus_packages = [
        {
            "corpus_id": entry["corpus_id"],
            "owner_layer": owner_layer_for_corpus(entry["corpus_id"]),
            "status": "proposed",
            "purpose": entry.get("purpose", ""),
            "source_root_ids": ["root.prototype", "root.migration-map"],
        }
        for entry in list_of_dicts(migration_map.get("target_corpora"))
        if isinstance(entry.get("corpus_id"), str)
    ]

    current_corpus_rule_roots = [
        root
        for root in corpus_rule_roots
        if repo_path(root["rules_root"]).is_dir()
    ]
    current_rule_root_by_corpus = {
        root["corpus_id"]: root
        for root in current_corpus_rule_roots
    }
    for package in corpus_packages:
        root = current_rule_root_by_corpus.get(package["corpus_id"])
        if root is None:
            continue
        package["status"] = "current"
        source_root_ids = list(package.get("source_root_ids") or [])
        if root["root_id"] not in source_root_ids:
            source_root_ids.append(root["root_id"])
        package["source_root_ids"] = source_root_ids
        manifest_path = default_manifest_path_for_corpus(package["corpus_id"], root["rules_root"])
        if manifest_path:
            package["manifest_path"] = manifest_path
        package["proposed_root"] = root["rules_root"]

    for root in current_corpus_rule_roots:
        if any(package["corpus_id"] == root["corpus_id"] for package in corpus_packages):
            continue
        package = {
            "corpus_id": root["corpus_id"],
            "owner_layer": owner_layer_for_corpus(root["corpus_id"]),
            "status": "current",
            "purpose": f"Structured rulebook content for {root['corpus_id']}.",
            "proposed_root": root["rules_root"],
            "source_root_ids": [root["root_id"]],
        }
        manifest_path = default_manifest_path_for_corpus(root["corpus_id"], root["rules_root"])
        if manifest_path:
            package["manifest_path"] = manifest_path
        corpus_packages.append(package)

    known_corpora = {entry["corpus_id"] for entry in corpus_packages}
    yaml_entries: list[tuple[str, dict[str, Any]]] = []
    yaml_artifacts = migration_map.get("yaml_artifacts") or {}
    if isinstance(yaml_artifacts, dict):
        for group_name in ("layer_rulesets", "concern_rulesets", "rule_packs"):
            for entry in list_of_dicts(yaml_artifacts.get(group_name)):
                yaml_entries.append((group_name, entry))
    for root in current_corpus_rule_roots:
        yaml_entries.extend(collect_current_rulebook_entries(root["corpus_id"], root["rules_root"]))

    path_to_artifact_ref: dict[str, str] = {}
    artifact_refs: set[str] = set()
    edge_ids: set[str] = set()

    def add_unresolved(ref: str, ref_type: str, owner_ref: str, severity: str, suggested_resolution: str) -> None:
        unresolved_references.append(
            {
                "ref": ref,
                "ref_type": ref_type,
                "owner_ref": owner_ref,
                "severity": severity,
                "suggested_resolution": suggested_resolution,
            }
        )

    def add_edge(
        from_ref: str,
        to_ref: str,
        edge_type: str,
        reason: str,
        source_ref_ids: list[str] | None = None,
    ) -> None:
        base_id = f"edge.{safe_id(edge_type)}.{safe_id(from_ref)}.{safe_id(to_ref)}"
        edge_id = base_id
        counter = 2
        while edge_id in edge_ids:
            edge_id = f"{base_id}.{counter}"
            counter += 1
        edge_ids.add(edge_id)
        graph_edges.append(
            {
                "edge_id": edge_id,
                "from_ref": from_ref,
                "to_ref": to_ref,
                "edge_type": edge_type,
                "reason": reason,
                "source_ref_ids": source_ref_ids or [],
            }
        )

    for group_name, entry in yaml_entries:
        current_path = entry.get("current_path")
        if not isinstance(current_path, str):
            continue
        metadata_id = entry.get("metadata_id")
        rulebook_id = entry.get("rulebook_id")
        artifact_ref = artifact_ref_for(rulebook_id, metadata_id, current_path)
        path_to_artifact_ref[normalize_path(current_path)] = artifact_ref

    def add_artifact(artifact: dict[str, Any]) -> None:
        artifact_ref = artifact["artifact_ref"]
        if artifact_ref in artifact_refs:
            errors.append(f"duplicate artifact_ref: {artifact_ref}")
        artifact_refs.add(artifact_ref)
        artifacts.append(artifact)
        current_path = artifact.get("current_path")
        if isinstance(current_path, str):
            path_to_artifact_ref[normalize_path(current_path)] = artifact_ref
        add_edge(
            artifact_ref,
            artifact["corpus_id"],
            "belongs-to-corpus",
            "Artifact belongs to the corpus selected by the migration map.",
            artifact.get("source_ref_ids", []),
        )
        chunk_id = f"chunk.summary.{safe_id(artifact_ref)}"
        chunk_candidates.append(
            {
                "chunk_id": chunk_id,
                "artifact_ref": artifact_ref,
                "corpus_id": artifact["corpus_id"],
                "content_kind": "artifact-summary",
                "section_path": "artifact",
                "source_path": artifact["current_path"],
                "token_estimate": max(20, len((artifact.get("title") or artifact_ref).split()) * 8),
                "source_ref_ids": artifact.get("source_ref_ids", []),
            }
        )
        add_edge(artifact_ref, chunk_id, "contains-chunk", "Artifact summary is a retrievable chunk candidate.")

    def add_path_mapping(entry: dict[str, Any], artifact_ref: str | None = None) -> None:
        current_path = entry.get("current_path")
        proposed_path = entry.get("proposed_target_path") or entry.get("proposed_path")
        proposed_corpus_id = entry.get("proposed_corpus_id")
        migration_status = entry.get("migration_status")
        if not all(isinstance(value, str) for value in [current_path, proposed_path, proposed_corpus_id, migration_status]):
            return
        mapping = {
            "current_path": current_path,
            "proposed_path": proposed_path,
            "proposed_corpus_id": proposed_corpus_id,
            "migration_status": migration_status,
            "update_requirements": migration_map.get("reference_update_requirements") or [],
        }
        if artifact_ref:
            mapping["artifact_ref"] = artifact_ref
        path_mappings.append(mapping)
        if artifact_ref:
            add_edge(
                artifact_ref,
                proposed_path,
                "proposed-migration-target",
                "Migration map proposes this future path for the artifact.",
            )
            if migration_status == "split-review-required":
                add_edge(
                    artifact_ref,
                    proposed_path,
                    "split-review-needed",
                    "Migration map marks this artifact as mixed concern requiring review before move.",
                )

    for guide in list_of_dicts((migration_map.get("source_material") or {}).get("guides")):
        current_path = guide.get("current_path")
        corpus_id = guide.get("proposed_corpus_id")
        if not isinstance(current_path, str) or not isinstance(corpus_id, str):
            continue
        artifact_ref = artifact_ref_for(None, None, current_path)
        source_ref_id = make_source_ref_id("guide", current_path)
        source_references.append(
            {
                "source_ref_id": source_ref_id,
                "corpus_id": corpus_id,
                "artifact_ref": artifact_ref,
                "source_path": current_path,
                "source_type": "source-guide",
            }
        )
        add_artifact(
            {
                "artifact_ref": artifact_ref,
                "artifact_type": "source-guide",
                "title": Path(current_path).stem,
                "status": "active",
                "corpus_id": corpus_id,
                "current_path": current_path,
                "proposed_path": guide.get("proposed_target_path"),
                "migration_status": guide.get("migration_status", "target-candidate"),
                "source_ref_ids": [source_ref_id],
                "diagnostics": [],
            }
        )
        add_path_mapping(guide, artifact_ref)

    adrs = (migration_map.get("source_material") or {}).get("adrs") or {}
    if isinstance(adrs, dict):
        current_glob = adrs.get("current_glob")
        proposed_corpus_id = adrs.get("proposed_corpus_id")
        proposed_target_pattern = adrs.get("proposed_target_pattern")
        migration_status = adrs.get("migration_status", "target-candidate")
        if isinstance(current_glob, str) and isinstance(proposed_corpus_id, str):
            for absolute in sorted(glob.glob((ROOT / current_glob).as_posix())):
                current_path = normalize_path(Path(absolute))
                filename = Path(current_path).name
                if filename == "README.md":
                    continue
                proposed_path = None
                if isinstance(proposed_target_pattern, str):
                    proposed_path = proposed_target_pattern.replace("<current-filename>", filename)
                artifact_ref = artifact_ref_for(None, None, current_path)
                source_ref_id = make_source_ref_id("adr", current_path)
                source_references.append(
                    {
                        "source_ref_id": source_ref_id,
                        "corpus_id": proposed_corpus_id,
                        "artifact_ref": artifact_ref,
                        "source_path": current_path,
                        "source_type": "adr",
                    }
                )
                add_artifact(
                    {
                        "artifact_ref": artifact_ref,
                        "artifact_type": "adr",
                        "title": Path(current_path).stem,
                        "status": "active",
                        "corpus_id": proposed_corpus_id,
                        "current_path": current_path,
                        "proposed_path": proposed_path,
                        "migration_status": migration_status,
                        "source_ref_ids": [source_ref_id],
                        "diagnostics": [],
                    }
                )
                if proposed_path:
                    add_path_mapping(
                        {
                            "current_path": current_path,
                            "proposed_target_path": proposed_path,
                            "proposed_corpus_id": proposed_corpus_id,
                            "migration_status": migration_status,
                        },
                        artifact_ref,
                    )

    for entry in SUPPORTING_SOURCE_ENTRIES:
        current_path = str(entry["current_path"])
        corpus_id = str(entry["corpus_id"])
        metadata = parse_metadata_header(current_path) if repo_path(current_path).is_file() else {}
        artifact_ref = artifact_ref_for(None, metadata.get("id"), current_path)
        source_ref_id = make_source_ref_id(str(entry["source_type"]), current_path)
        source_references.append(
            {
                "source_ref_id": source_ref_id,
                "corpus_id": corpus_id,
                "artifact_ref": artifact_ref,
                "source_path": current_path,
                "source_type": entry["source_type"],
            }
        )
        add_artifact(
            {
                "artifact_ref": artifact_ref,
                "metadata_id": metadata.get("id"),
                "artifact_type": entry["artifact_type"],
                "title": metadata.get("purpose") or Path(current_path).stem,
                "status": metadata.get("status") or "active",
                "version": metadata.get("version") or 1,
                "corpus_id": corpus_id,
                "current_path": current_path,
                "proposed_path": current_path,
                "migration_status": "current",
                "source_ref_ids": [source_ref_id],
                "retrieval_profile": entry.get("retrieval_profile", {}),
                "diagnostics": [],
            }
        )
        add_path_mapping(
            {
                "current_path": current_path,
                "proposed_target_path": current_path,
                "proposed_corpus_id": corpus_id,
                "migration_status": "current",
            },
            artifact_ref,
        )
        chunk_id = f"chunk.source.{safe_id(artifact_ref)}"
        chunk_candidates.append(
            {
                "chunk_id": chunk_id,
                "artifact_ref": artifact_ref,
                "corpus_id": corpus_id,
                "content_kind": "source-excerpt",
                "section_path": "source-excerpt",
                "source_path": current_path,
                "token_estimate": 1200,
                "source_ref_ids": [source_ref_id],
            }
        )
        add_edge(
            artifact_ref,
            chunk_id,
            "contains-chunk",
            "Supporting source excerpt is a retrievable chunk candidate.",
            [source_ref_id],
        )
        profile = entry.get("retrieval_profile")
        if isinstance(profile, dict) and profile:
            profile_chunk_id = f"chunk.profile.{safe_id(artifact_ref)}"
            chunk_candidates.append(
                {
                    "chunk_id": profile_chunk_id,
                    "artifact_ref": artifact_ref,
                    "corpus_id": corpus_id,
                    "content_kind": "retrieval-profile",
                    "section_path": "retrieval-profile",
                    "source_path": current_path,
                    "token_estimate": 220,
                    "source_ref_ids": [source_ref_id],
                    "retrieval_profile": profile,
                }
            )
            add_edge(
                artifact_ref,
                profile_chunk_id,
                "contains-chunk",
                "Generated retrieval profile is a retrievable chunk candidate.",
                [source_ref_id],
            )

    for group_name, entry in yaml_entries:
        current_path = entry.get("current_path")
        if not isinstance(current_path, str):
            continue
        artifact_ref = path_to_artifact_ref[normalize_path(current_path)]
        corpus_id = entry.get("proposed_corpus_id")
        if not isinstance(corpus_id, str):
            errors.append(f"missing proposed_corpus_id for {current_path}")
            corpus_id = "unknown"
        if corpus_id not in known_corpora:
            add_unresolved(corpus_id, "corpus-manifest", artifact_ref, "error", "Add the corpus to target_corpora.")
        if not repo_path(current_path).is_file():
            errors.append(f"missing YAML artifact: {current_path}")
            yaml_data: dict[str, Any] = {}
            metadata: dict[str, Any] = {}
        else:
            yaml_data = load_yaml(current_path)
            metadata = parse_metadata_header(current_path)

        source_ref_id = make_source_ref_id("artifact", current_path)
        source_references.append(
            {
                "source_ref_id": source_ref_id,
                "corpus_id": corpus_id,
                "artifact_ref": artifact_ref,
                "source_path": current_path,
                "source_type": "rule-pack" if group_name == "rule_packs" else "rule",
            }
        )

        related_ruleset_refs = list_of_strings(yaml_data.get("related_rulesets"))
        required_ruleset_refs = list_of_strings(yaml_data.get("required_rulesets"))
        applies_to_paths = list_of_strings((yaml_data.get("applies_to") or {}).get("paths"))
        source_derivation = yaml_data.get("source_derivation")
        if not isinstance(source_derivation, dict):
            source_derivation = None
        artifact = {
            "artifact_ref": artifact_ref,
            "metadata_id": entry.get("metadata_id") or metadata.get("id"),
            "rulebook_id": entry.get("rulebook_id") or yaml_data.get("id"),
            "artifact_type": artifact_type_for_group(group_name),
            "title": entry.get("title") or yaml_data.get("title"),
            "status": yaml_data.get("status") or "active",
            "version": yaml_data.get("version") or 1,
            "corpus_id": corpus_id,
            "current_path": current_path,
            "proposed_path": entry.get("proposed_target_path"),
            "migration_status": entry.get("migration_status", "target-candidate"),
            "applies_to_paths": applies_to_paths,
            "related_ruleset_refs": related_ruleset_refs,
            "required_ruleset_refs": required_ruleset_refs,
            "source_ref_ids": [source_ref_id],
            "diagnostics": [],
        }
        if source_derivation is not None:
            artifact["source_derivation"] = source_derivation
        add_artifact(artifact)
        add_path_mapping(entry, artifact_ref)

        for path_glob in applies_to_paths:
            add_edge(artifact_ref, path_glob, "applies-to-path", "Ruleset declares this path glob in applies_to.paths.")

        for ref in related_ruleset_refs:
            resolved = resolve_ref_path(ref, current_path)
            target_ref = path_to_artifact_ref.get(resolved)
            if target_ref:
                add_edge(artifact_ref, target_ref, "related-ruleset", "Ruleset declares this related ruleset.")
            else:
                add_unresolved(ref, "related-ruleset", artifact_ref, "warning", f"Resolve or update path: {resolved}")

        for ref in required_ruleset_refs:
            resolved = resolve_ref_path(ref, current_path)
            target_ref = path_to_artifact_ref.get(resolved)
            if target_ref:
                add_edge(artifact_ref, target_ref, "required-ruleset", "Artifact declares this required ruleset.")
            else:
                add_unresolved(ref, "required-ruleset", artifact_ref, "blocking", f"Resolve or update path: {resolved}")

        for index, rule in enumerate(list_of_dicts(yaml_data.get("rules"))):
            rule_id = rule.get("id") or f"{yaml_data.get('id', artifact_ref)}.rule-{index + 1}"
            rule_ref = f"rule.{safe_id(artifact_ref)}.{safe_id(rule_id)}"
            chunk_id = f"chunk.{safe_id(rule_ref)}"
            rules.append(
                {
                    "rule_ref": rule_ref,
                    "rule_id": rule_id,
                    "artifact_ref": artifact_ref,
                    "corpus_id": corpus_id,
                    "title": rule.get("title") or rule_id,
                    "severity": rule.get("severity"),
                    "summary": rule.get("summary"),
                    "section_path": f"rules[{index}]",
                    "source_ref_ids": [source_ref_id],
                    "chunk_candidate_ids": [chunk_id],
                }
            )
            chunk_candidate = {
                "chunk_id": chunk_id,
                "artifact_ref": artifact_ref,
                "rule_ref": rule_ref,
                "corpus_id": corpus_id,
                "content_kind": "rule",
                "section_path": f"rules[{index}]",
                "source_path": current_path,
                "token_estimate": max(40, len(str(rule.get("summary") or rule.get("title") or rule_id).split()) * 10),
                "source_ref_ids": [source_ref_id],
            }
            if source_derivation is not None:
                chunk_candidate["source_derivation"] = source_derivation
            chunk_candidates.append(chunk_candidate)
            add_edge(artifact_ref, rule_ref, "contains-rule", "Ruleset contains this rule.", [source_ref_id])
            add_edge(rule_ref, chunk_id, "contains-chunk", "Rule is a retrievable chunk candidate.", [source_ref_id])

        if group_name == "rule_packs":
            pack_id = yaml_data.get("id") or entry.get("rulebook_id") or Path(current_path).stem
            pack_ref = f"pack.{safe_id(pack_id)}"
            agent_step_ids = [step.get("id") for step in list_of_dicts(yaml_data.get("agent_steps")) if isinstance(step.get("id"), str)]
            required_checks = list_of_strings(yaml_data.get("required_checks"))
            pack = {
                "pack_ref": pack_ref,
                "pack_id": pack_id,
                "artifact_ref": artifact_ref,
                "corpus_id": corpus_id,
                "task_type": yaml_data.get("task_type"),
                "applies_when": list_of_strings(yaml_data.get("applies_when")),
                "required_ruleset_refs": required_ruleset_refs,
                "required_checks": required_checks,
                "agent_step_ids": agent_step_ids,
            }
            rule_packs.append(pack)
            add_edge(artifact_ref, pack_ref, "contains-pack", "Rule-pack artifact contains this task pack.", [source_ref_id])

            for ref in required_ruleset_refs:
                resolved = resolve_ref_path(ref, current_path)
                target_ref = path_to_artifact_ref.get(resolved)
                if target_ref:
                    add_edge(pack_ref, target_ref, "required-ruleset", "Task pack requires this ruleset.", [source_ref_id])

            for index, step in enumerate(list_of_dicts(yaml_data.get("agent_steps"))):
                step_id = step.get("id") or f"step-{index + 1}"
                chunk_id = f"chunk.{safe_id(pack_ref)}.step.{safe_id(step_id)}"
                chunk_candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "artifact_ref": artifact_ref,
                        "pack_ref": pack_ref,
                        "corpus_id": corpus_id,
                        "content_kind": "rule-pack-step",
                        "section_path": f"agent_steps[{index}]",
                        "source_path": current_path,
                        "token_estimate": max(30, len(str(step.get("instruction") or step_id).split()) * 8),
                        "source_ref_ids": [source_ref_id],
                    }
                )
                add_edge(pack_ref, chunk_id, "contains-chunk", "Task pack step is a retrievable chunk candidate.", [source_ref_id])

            for index, check in enumerate(required_checks):
                chunk_id = f"chunk.{safe_id(pack_ref)}.required-check.{index + 1}"
                chunk_candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "artifact_ref": artifact_ref,
                        "pack_ref": pack_ref,
                        "corpus_id": corpus_id,
                        "content_kind": "required-check",
                        "section_path": f"required_checks[{index}]",
                        "source_path": current_path,
                        "token_estimate": max(20, len(check.split()) * 6),
                        "source_ref_ids": [source_ref_id],
                    }
                )
                add_edge(pack_ref, chunk_id, "contains-chunk", "Task pack check is a retrievable chunk candidate.", [source_ref_id])

            for index, source_ref in enumerate(list_of_dicts(yaml_data.get("source_refs"))):
                doc = source_ref.get("doc")
                if not isinstance(doc, str):
                    continue
                source_path = f"{source_root}/guides/markdown/{doc}"
                if not repo_path(source_path).is_file():
                    source_path = doc
                extra_source_ref_id = make_source_ref_id(pack_ref, f"{doc}.{index}")
                source_references.append(
                    {
                        "source_ref_id": extra_source_ref_id,
                        "corpus_id": corpus_id,
                        "artifact_ref": artifact_ref,
                        "source_path": source_path,
                        "source_type": "source-guide",
                        "section": ", ".join(list_of_strings(source_ref.get("sections"))),
                    }
                )
                add_edge(pack_ref, extra_source_ref_id, "cites-source", "Task pack cites this source guide section.", [source_ref_id])

    def duplicate_values(values: list[str]) -> list[str]:
        seen: set[str] = set()
        dupes: set[str] = set()
        for value in values:
            if value in seen:
                dupes.add(value)
            seen.add(value)
        return sorted(dupes)

    for label, values in (
        ("metadata_id", [artifact.get("metadata_id") for artifact in artifacts if artifact.get("metadata_id")]),
        ("rulebook_id", [artifact.get("rulebook_id") for artifact in artifacts if artifact.get("rulebook_id")]),
        ("rule_id", [rule.get("rule_id") for rule in rules if rule.get("rule_id")]),
        ("pack_id", [pack.get("pack_id") for pack in rule_packs if pack.get("pack_id")]),
    ):
        for duplicate in duplicate_values([str(value) for value in values]):
            errors.append(f"duplicate {label}: {duplicate}")

    if any(entry.get("severity") == "blocking" for entry in unresolved_references):
        errors.append("blocking unresolved references exist")

    if not artifacts:
        errors.append("no artifacts indexed")

    logical_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "source_root": source_root,
                "migration_map": migration_map_path,
                "git_commit": git_commit,
                "artifact_refs": [artifact["artifact_ref"] for artifact in artifacts],
                "rule_refs": [rule["rule_ref"] for rule in rules],
                "pack_refs": [pack["pack_ref"] for pack in rule_packs],
                "corpus_rule_roots": corpus_rule_roots,
                "path_mappings": path_mappings,
                "unresolved_references": unresolved_references,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:12]

    input_paths = [migration_map_path]
    input_paths.extend(entry.get("current_path") for _, entry in yaml_entries if isinstance(entry.get("current_path"), str))
    input_paths.extend(entry["current_path"] for entry in SUPPORTING_SOURCE_ENTRIES)
    inputs = []
    for path in sorted(set(input_paths)):
        if repo_path(path).is_file():
            inputs.append({"path": path, "role": "input", "content_hash": content_hash(path)})
        else:
            inputs.append({"path": path, "role": "missing"})

    diagnostics = {
        "ok": not errors,
        "counts": {
            "corpus_packages": len(corpus_packages),
            "artifacts": len(artifacts),
            "rules": len(rules),
            "rule_packs": len(rule_packs),
            "chunk_candidates": len(chunk_candidates),
            "graph_edges": len(graph_edges),
            "unresolved_references": len(unresolved_references),
        },
        "warnings": warnings,
        "errors": errors,
    }

    source_roots = [
        {
            "root_id": "root.prototype",
            "path": source_root,
            "role": "prototype-corpus",
            "migration_status": "current",
        },
        {
            "root_id": "root.migration-map",
            "path": migration_map_path,
            "role": "migration-map",
            "migration_status": "proposed",
        },
        {
            "root_id": "root.harness-artifact-metadata",
            "path": ".agentic/01.harness/artifact-metadata",
            "role": "supporting-source",
            "migration_status": "current",
            "corpus_id": HARNESS_CORPUS_ID,
        },
        {
            "root_id": "root.harness-artifact-metadata-scripts",
            "path": "scripts/01.harness/artifact-metadata",
            "role": "supporting-source",
            "migration_status": "current",
            "corpus_id": HARNESS_CORPUS_ID,
        },
    ]
    for root in current_corpus_rule_roots:
        source_roots.append(
            {
                "root_id": root["root_id"],
                "path": root["rules_root"],
                "role": "corpus-package",
                "migration_status": "current",
                "corpus_id": root["corpus_id"],
            }
        )

    return {
        "schema": INDEX_SCHEMA,
        "index_id": f"index.rulebook.{git_commit[:12]}.{logical_fingerprint}",
        "generated_at": generated_at,
        "source_roots": source_roots,
        "corpus_packages": corpus_packages,
        "artifacts": artifacts,
        "rules": rules,
        "rule_packs": rule_packs,
        "chunk_candidates": chunk_candidates,
        "graph_edges": graph_edges,
        "source_references": source_references,
        "path_mappings": path_mappings,
        "unresolved_references": unresolved_references,
        "diagnostics": diagnostics,
        "provenance": {
            "generator": "scripts/02.rag-rulebook/generate-rulebook-index/script.sh",
            "generator_version": GENERATOR_VERSION,
            "git_commit": git_commit,
            "inputs": inputs,
        },
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    corpus_rule_roots = parse_corpus_rule_roots(args)
    index = build_index(
        normalize_path(args.source_root),
        normalize_path(args.migration_map),
        corpus_rule_roots,
    )
    json.dump(index, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY

#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.build-local-runtime
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Build a local deterministic RAG/rulebook runtime cache from governed repo sources.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.scripts.readme
#       path: scripts/02.rag-rulebook/README.md
#     - id: rag-rulebook.script.build-local-runtime.readme
#       path: scripts/02.rag-rulebook/build-local-runtime/README.md
#     - id: rag-rulebook.script.build-local-runtime.smoke-test
#       path: scripts/02.rag-rulebook/build-local-runtime/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUTPUT_DIR=".cache/02.rag-rulebook"
PRETTY=false

usage() {
  cat <<'EOF'
Usage:
  build-local-runtime/script.sh [--output-dir <path>] [--pretty]

Builds a local deterministic RAG/rulebook runtime cache. The command writes
JSON runtime files under .cache/02.rag-rulebook by default and does not call
the network, use embeddings, or start a server.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --output-dir requires a path." >&2
        exit 2
      fi
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --pretty)
      PRETTY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_executable() {
  local path="$1"

  if [ ! -x "$path" ]; then
    echo "ERROR: required RAG/rulebook command is missing or not executable: $path" >&2
    exit 1
  fi
}

require_executable "scripts/02.rag-rulebook/generate-recognition-sources/script.sh"
require_executable "scripts/02.rag-rulebook/validate-recognition-sources/script.sh"
require_executable "scripts/02.rag-rulebook/validate-recognition-candidates/script.sh"
require_executable "scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
require_executable "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
require_executable "scripts/02.rag-rulebook/validate-rulebook-index/script.sh"
require_executable "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

OUTPUT_DIR="${OUTPUT_DIR%/}"
mkdir -p "$OUTPUT_DIR"

INDEX_FILE="$OUTPUT_DIR/rulebook-index.json"
CHUNKS_FILE="$OUTPUT_DIR/rulebook-chunks.json"
MANIFEST_FILE="$OUTPUT_DIR/manifest.json"
VALIDATION_REPORT_FILE="$OUTPUT_DIR/validation-report.json"

POLICY_REPORT="$TMP_DIR/retrieval-policy-pack.json"
RECOGNITION_SOURCES_REPORT="$TMP_DIR/recognition-sources.json"
RECOGNITION_CANDIDATES_REPORT="$TMP_DIR/recognition-candidates.json"
GENERATED_SOURCES_CHECK="$TMP_DIR/generated-sources-check.txt"
INDEX_VALIDATION_REPORT="$TMP_DIR/rulebook-index-validation.json"

bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --current \
  --json > "$POLICY_REPORT"

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --current \
  --json > "$RECOGNITION_SOURCES_REPORT"

bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh \
  --current \
  --json > "$RECOGNITION_CANDIDATES_REPORT"

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --check > "$GENERATED_SOURCES_CHECK"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh \
  --pretty > "$INDEX_FILE"

bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh \
  --index "$INDEX_FILE" \
  --json > "$INDEX_VALIDATION_REPORT"

bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh \
  --index "$INDEX_FILE" \
  --pretty > "$CHUNKS_FILE"

python3 - \
  "$ROOT" \
  "$OUTPUT_DIR" \
  "$INDEX_FILE" \
  "$CHUNKS_FILE" \
  "$POLICY_REPORT" \
  "$RECOGNITION_SOURCES_REPORT" \
  "$RECOGNITION_CANDIDATES_REPORT" \
  "$GENERATED_SOURCES_CHECK" \
  "$INDEX_VALIDATION_REPORT" \
  "$MANIFEST_FILE" \
  "$VALIDATION_REPORT_FILE" \
  "$PRETTY" <<'PY'
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
index_file = Path(sys.argv[3])
chunks_file = Path(sys.argv[4])
policy_report_path = Path(sys.argv[5])
recognition_sources_report_path = Path(sys.argv[6])
recognition_candidates_report_path = Path(sys.argv[7])
generated_sources_check_path = Path(sys.argv[8])
index_validation_report_path = Path(sys.argv[9])
manifest_file = Path(sys.argv[10])
validation_report_file = Path(sys.argv[11])
pretty = sys.argv[12] == "true"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


FINGERPRINT_INPUTS = {
    "retrieval_policy": [".agentic/02.rag-rulebook/policies"],
    "recognition_sources": [".agentic/02.rag-rulebook/recognition-sources"],
    "recognition_candidates": [".agentic/02.rag-rulebook/recognition-candidates"],
    "corpus_gaps": [".agentic/02.rag-rulebook/corpus-gaps"],
    "source_material": [
        "docs/02.rag-rulebook/source-material",
        "docs/04.deploy/source-material",
    ],
    "structured_rules": [
        "docs/harness/architecture",
        "docs/02.rag-rulebook/rules",
        "docs/04.deploy/rules",
    ],
    "source_derivations": [".agentic/02.rag-rulebook/derivation-reports"],
    "index_inputs": [
        ".agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml",
        ".agentic/02.rag-rulebook/schemas",
        "scripts/02.rag-rulebook/generate-rulebook-index/script.sh",
        "scripts/02.rag-rulebook/validate-rulebook-index/script.sh",
    ],
    "chunk_generation": ["scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"],
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_fingerprint_files(raw_roots: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing_roots: list[str] = []
    for raw_root in raw_roots:
        root_path = Path(raw_root)
        absolute = root_path if root_path.is_absolute() else root / root_path
        if absolute.is_file():
            files.append(absolute)
        elif absolute.is_dir():
            files.extend(path for path in absolute.rglob("*") if path.is_file())
        else:
            missing_roots.append(raw_root)
    return sorted(set(files), key=lambda path: rel(path)), sorted(missing_roots)


def fingerprint_roots(raw_roots: list[str]) -> dict:
    files, missing_roots = iter_fingerprint_files(raw_roots)
    digest = hashlib.sha256()
    digest.update(b"rag-rulebook-fingerprint-v1\n")
    for raw_root in sorted(raw_roots):
        digest.update(f"root:{raw_root}\n".encode("utf-8"))
    for missing_root in missing_roots:
        digest.update(f"missing:{missing_root}\n".encode("utf-8"))
    for path in files:
        relative = rel(path)
        digest.update(f"file:{relative}\n".encode("utf-8"))
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return {
        "algorithm": "sha256-relpath-content-v1",
        "roots": raw_roots,
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "missing_roots": missing_roots,
        "paths": [rel(path) for path in files],
    }


def fingerprint_file(path: Path) -> dict:
    return {
        "algorithm": "sha256-content-v1",
        "path": rel(path),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
    }


index = load_json(index_file)
chunks = load_json(chunks_file)
policy_report = load_json(policy_report_path)
recognition_sources_report = load_json(recognition_sources_report_path)
recognition_candidates_report = load_json(recognition_candidates_report_path)
index_validation_report = load_json(index_validation_report_path)

index_counts = index.get("diagnostics", {}).get("counts", {})
chunk_counts = chunks.get("diagnostics", {}).get("counts", {})

validation_report = {
    "schema": "rag-rulebook/local-runtime-validation-report/v1",
    "ok": all(
        [
            policy_report.get("ok") is True,
            recognition_sources_report.get("ok") is True,
            recognition_candidates_report.get("ok") is True,
            index_validation_report.get("ok") is True,
        ]
    ),
    "reports": {
        "retrieval_policy_pack": policy_report,
        "recognition_sources": recognition_sources_report,
        "recognition_candidates": recognition_candidates_report,
        "generated_recognition_sources_check": generated_sources_check_path.read_text(encoding="utf-8").splitlines(),
        "rulebook_index": index_validation_report,
    },
}

manifest = {
    "schema": "rag-rulebook/local-runtime-manifest/v1",
    "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_sha": git_sha(),
    "runtime_dir": rel(output_dir),
    "files": {
        "rulebook_index": rel(index_file),
        "rulebook_chunks": rel(chunks_file),
        "manifest": rel(manifest_file),
        "validation_report": rel(validation_report_file),
    },
    "recognition_sources": {
        "generated": [
            ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml",
            ".agentic/02.rag-rulebook/recognition-sources/generated/routing.yml",
        ],
        "curated_glob": ".agentic/02.rag-rulebook/recognition-sources/curated/*.yml",
        "freshness": "current",
    },
    "fingerprints": {
        "inputs": {
            name: fingerprint_roots(paths)
            for name, paths in FINGERPRINT_INPUTS.items()
        },
        "runtime_outputs": {
            "rulebook_index": fingerprint_file(index_file),
            "rulebook_chunks": fingerprint_file(chunks_file),
        },
    },
    "counts": {
        "artifacts": index_counts.get("artifacts", 0),
        "rules": index_counts.get("rules", 0),
        "rule_packs": index_counts.get("rule_packs", 0),
        "corpus_packages": index_counts.get("corpus_packages", 0),
        "graph_edges": index_counts.get("graph_edges", 0),
        "chunk_candidates": index_counts.get("chunk_candidates", 0),
        "chunks": chunk_counts.get("chunks", 0),
        "citations": chunk_counts.get("citations", 0),
        "recognition_source_terms": recognition_sources_report.get("counts", {}).get("terms", 0),
        "recognition_candidates": recognition_candidates_report.get("counts", {}).get("candidates", 0),
    },
    "constraints": {
        "local_only": True,
        "network_calls": False,
        "embeddings": False,
        "server_started": False,
    },
    "next_interface": "scripts/02.rag-rulebook/query-local-context/script.sh",
}

indent = 2 if pretty else None
validation_report_file.write_text(json.dumps(validation_report, indent=indent, sort_keys=True) + "\n", encoding="utf-8")
manifest_file.write_text(json.dumps(manifest, indent=indent, sort_keys=True) + "\n", encoding="utf-8")

if not validation_report["ok"]:
    raise SystemExit("local runtime validation failed")

print(f"Built local RAG/rulebook runtime: {rel(output_dir)}")
print(f"  index: {rel(index_file)}")
print(f"  chunks: {rel(chunks_file)}")
print(f"  manifest: {rel(manifest_file)}")
print(f"  validation: {rel(validation_report_file)}")
PY

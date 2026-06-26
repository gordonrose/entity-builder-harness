#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-yaml-syntax
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Parse governed RAG/rulebook and deploy YAML files before narrower validators run.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-yaml-syntax.readme
#       path: scripts/02.rag-rulebook/validate-yaml-syntax/README.md
#     - id: rag-rulebook.script.validate-yaml-syntax.smoke-test
#       path: scripts/02.rag-rulebook/validate-yaml-syntax/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

JSON=false
PATHS=()

usage() {
  cat <<'EOF'
Usage:
  validate-yaml-syntax/script.sh [--json] [--paths <path>...]

Parses governed YAML files under the RAG/rulebook and deploy roots. This is a
syntax gate only; semantic validation remains owned by narrower validators.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --json)
      JSON=true
      shift
      ;;
    --paths)
      shift
      if [ "$#" -eq 0 ] || [[ "$1" == --* ]]; then
        echo "ERROR: --paths requires at least one path." >&2
        exit 2
      fi
      while [ "$#" -gt 0 ] && [[ "$1" != --* ]]; do
        PATHS+=("$1")
        shift
      done
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

if [ "${#PATHS[@]}" -eq 0 ]; then
  PATHS=(
    ".agentic/02.rag-rulebook"
    "docs/02.rag-rulebook"
    "docs/04.deploy"
    ".agentic/aws"
  )
fi

python3 - "$JSON" "${PATHS[@]}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover - surfaced in shell usage
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

emit_json = sys.argv[1] == "true"
roots = [Path(value) for value in sys.argv[2:]]
yaml_files: list[Path] = []
errors: list[dict[str, str]] = []

for root in roots:
    if not root.exists():
        continue
    if root.is_file():
        candidates = [root]
    else:
        candidates = sorted(path for path in root.rglob("*") if path.is_file())
    for path in candidates:
        if path.suffix.lower() in {".yml", ".yaml"}:
            yaml_files.append(path)

for path in sorted(set(yaml_files)):
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append({"path": str(path), "error": str(exc)})

report = {
    "schema": "rag-rulebook/yaml-syntax-validation-report/v1",
    "ok": not errors,
    "files_checked": len(set(yaml_files)),
    "errors": errors,
}

if emit_json:
    print(json.dumps(report, indent=2, sort_keys=True))
elif errors:
    print("YAML syntax validation failed:", file=sys.stderr)
    for item in errors:
        print(f"- {item['path']}: {item['error']}", file=sys.stderr)
else:
    print(f"YAML syntax valid: {report['files_checked']} file(s).")

sys.exit(0 if report["ok"] else 1)
PY

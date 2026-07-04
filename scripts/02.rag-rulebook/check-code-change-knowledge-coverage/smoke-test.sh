#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-code-change-knowledge-coverage.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#   - agentic
#   - architecture
#   kind: script
#   purpose: Smoke test the RAG code-change knowledge coverage gate.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - writes-files
#   used_by:
#   - id: rag-rulebook.script.commit-gates
#     path: scripts/02.rag-rulebook/commit-gates/script.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cd "$TMP_DIR"
git init --quiet --initial-branch=main
git config user.email "agent@example.invalid"
git config user.name "Agent"
mkdir -p scripts/02.rag-rulebook/check-code-change-knowledge-coverage
cp "$SCRIPT" scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
chmod +x scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
echo "# test" > README.md
git add README.md scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
git commit --quiet -m "initial"

git switch --quiet -c chat/2026-07-04-12-00-rag-knowledge-smoke
mkdir -p commitLogs/2026/jul/04/2026-07-04-12-00-rag-knowledge-smoke packages/core docs/harness/architecture/source-material
cat > commitLogs/2026/jul/04/2026-07-04-12-00-rag-knowledge-smoke/README.md <<'LOG'
# Chat Session

<!-- agentic-session
id: 2026-07-04-12-00-rag-knowledge-smoke
branch: chat/2026-07-04-12-00-rag-knowledge-smoke
-->

## Initial Intent

Smoke.
LOG

echo "export type Smoke = string;" > packages/core/index.ts

if bash scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh --current >/tmp/rag-knowledge.out 2>&1; then
  echo "ERROR: expected missing disposition to fail" >&2
  exit 1
fi

cat >> commitLogs/2026/jul/04/2026-07-04-12-00-rag-knowledge-smoke/README.md <<'LOG'

## RAG Knowledge Disposition

Status: covered
Reason: Core contract source was projected.
Evidence:
- docs/harness/architecture/source-material/example.md
Corpus gaps:
- None.
LOG

echo "# source" > docs/harness/architecture/source-material/example.md
bash scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh --current >/dev/null

perl -0pi -e 's/Status: covered/Status: deferred-with-gap/' commitLogs/2026/jul/04/2026-07-04-12-00-rag-knowledge-smoke/README.md
sed -i 's#- None\\.#- .agentic/02.rag-rulebook/corpus-gaps/example.yml#' commitLogs/2026/jul/04/2026-07-04-12-00-rag-knowledge-smoke/README.md
bash scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh --current >/dev/null

echo "RAG code-change knowledge coverage smoke passed."

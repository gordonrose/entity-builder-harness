#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.commit-gates.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the RAG/rulebook commit-boundary validation gate.
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

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/current.out"
SKIP_REPO="$TMP_DIR/skip-repo"
BROKEN_REPO="$TMP_DIR/broken-repo"

bash scripts/02.rag-rulebook/commit-gates/script.sh > "$REPORT_FILE"

grep -q "RAG/rulebook commit gates passed." "$REPORT_FILE" || {
  echo "ERROR: commit gate did not pass in current repo" >&2
  exit 1
}

mkdir -p "$SKIP_REPO/scripts/02.rag-rulebook/commit-gates"
cp scripts/02.rag-rulebook/commit-gates/script.sh "$SKIP_REPO/scripts/02.rag-rulebook/commit-gates/script.sh"
git -C "$SKIP_REPO" init -q

if ! (
  cd "$SKIP_REPO"
  bash scripts/02.rag-rulebook/commit-gates/script.sh
) | grep -q "RAG/rulebook layer absent"; then
  echo "ERROR: commit gate did not skip an absent RAG/rulebook layer" >&2
  exit 1
fi

mkdir -p "$BROKEN_REPO/.agentic/02.rag-rulebook/recognition-sources/generated"
mkdir -p "$BROKEN_REPO/scripts/02.rag-rulebook/commit-gates"
mkdir -p "$BROKEN_REPO/scripts/02.rag-rulebook/validate-retrieval-policy-pack"
cp scripts/02.rag-rulebook/commit-gates/script.sh "$BROKEN_REPO/scripts/02.rag-rulebook/commit-gates/script.sh"
cat > "$BROKEN_REPO/scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exit 0
EOF
chmod +x "$BROKEN_REPO/scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh"
git -C "$BROKEN_REPO" init -q

if (
  cd "$BROKEN_REPO"
  bash scripts/02.rag-rulebook/commit-gates/script.sh
) >/dev/null 2>&1; then
  echo "ERROR: commit gate accepted recognition sources without a validator" >&2
  exit 1
fi

echo "RAG/rulebook commit gate smoke test passed."

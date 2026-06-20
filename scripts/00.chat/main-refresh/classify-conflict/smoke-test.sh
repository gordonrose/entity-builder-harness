#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test deterministic main-refresh conflict classification.
#   domain: main-refresh
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/main-refresh/classify-conflict/script.sh
#   effects: temporary-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/classify-main-refresh-conflict-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name "Test User"

mkdir -p "$REPO/scripts/00.chat/main-refresh/classify-conflict"
cp "$SOURCE_ROOT/scripts/00.chat/main-refresh/classify-conflict/script.sh" "$REPO/scripts/00.chat/main-refresh/classify-conflict/script.sh"

cat > "$REPO/README.md" <<'EOF'
base
EOF
git -C "$REPO" add README.md scripts/00.chat/main-refresh/classify-conflict/script.sh
git -C "$REPO" commit -q -m base
git -C "$REPO" branch -M main

LEGACY_SHARED_ROOT=".agentic/shared"
LEGACY_WORKFLOWS="${LEGACY_SHARED_ROOT}/workflows"
LEGACY_MAIN_UPDATED="${LEGACY_WORKFLOWS}/main-updated.md"
LEGACY_SCRIPT_ROOT="scripts/shared"
LEGACY_CHAT_SCRIPTS="${LEGACY_SCRIPT_ROOT}/chat"
LEGACY_GENERATOR="${LEGACY_CHAT_SCRIPTS}/generate-commit-log-summary.sh"

git -C "$REPO" checkout -q -b chat/test
mkdir -p "$REPO/$LEGACY_WORKFLOWS"
cat > "$REPO/$LEGACY_MAIN_UPDATED" <<'EOF'
Compatibility pointer.
EOF
git -C "$REPO" add "$LEGACY_MAIN_UPDATED"
git -C "$REPO" commit -q -m "chat migration pointer"

git -C "$REPO" checkout -q main
mkdir -p "$REPO/$LEGACY_WORKFLOWS"
cat > "$REPO/$LEGACY_MAIN_UPDATED" <<'EOF'
Legacy workflow with preflight cleanup guidance.
EOF
git -C "$REPO" add "$LEGACY_MAIN_UPDATED"
git -C "$REPO" commit -q -m "main legacy workflow"

git -C "$REPO" checkout -q chat/test
set +e
git -C "$REPO" merge main >/dev/null 2>&1
MERGE_STATUS="$?"
set -e

if [ "$MERGE_STATUS" -eq 0 ]; then
  fail "expected add/add conflict"
fi

OUTPUT="$(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/classify-conflict/script.sh "$LEGACY_MAIN_UPDATED"
)"

if ! printf '%s\n' "$OUTPUT" | grep -q '^type=ownership-migration-conflict$'; then
  fail "ownership migration conflict was not classified"
fi

git -C "$REPO" merge --abort
git -C "$REPO" checkout -q main

mkdir -p "$REPO/$LEGACY_CHAT_SCRIPTS"
cat > "$REPO/$LEGACY_GENERATOR" <<'EOF'
#!/usr/bin/env bash
echo "write commitLogs/README.md"
EOF
chmod +x "$REPO/$LEGACY_GENERATOR"
git -C "$REPO" add "$LEGACY_GENERATOR"
git -C "$REPO" commit -q -m "main generator"

git -C "$REPO" checkout -q chat/test
mkdir -p "$REPO/$LEGACY_CHAT_SCRIPTS"
cat > "$REPO/$LEGACY_GENERATOR" <<'EOF'
#!/usr/bin/env bash
echo "print only"
EOF
chmod +x "$REPO/$LEGACY_GENERATOR"
git -C "$REPO" add "$LEGACY_GENERATOR"
git -C "$REPO" commit -q -m "chat generator"

set +e
git -C "$REPO" merge main >/dev/null 2>&1
MERGE_STATUS="$?"
set -e

if [ "$MERGE_STATUS" -eq 0 ]; then
  fail "expected generator add/add conflict"
fi

OUTPUT="$(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/classify-conflict/script.sh "$LEGACY_GENERATOR"
)"

if ! printf '%s\n' "$OUTPUT" | grep -q '^type=retired-artifact-generator-conflict$'; then
  fail "retired artifact generator conflict was not classified"
fi

echo "main refresh conflict classifier smoke test passed."

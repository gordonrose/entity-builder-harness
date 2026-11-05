#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.classify-conflict.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test deterministic main-refresh conflict classification.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.main-refresh.classify-conflict
#     path: scripts/00.chat/main-refresh/classify-conflict/script.sh
#   effects:
#   - writes-files

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

git -C "$REPO" merge --abort
git -C "$REPO" checkout -q main

METADATA_FILE="docs/04.deploy/metadata-only-conflict.md"
mkdir -p "$REPO/$(dirname "$METADATA_FILE")"
cat > "$REPO/$METADATA_FILE" <<'EOF'
<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.metadata-only-conflict
  version: 1
  created_on: "2026-01-01"
  updated_on: "2026-01-01"
-->
# Metadata-only fixture
EOF
for line in $(seq 1 6000); do
  printf 'metadata-only classifier fixture content %s\n' "$line" >> "$REPO/$METADATA_FILE"
done
git -C "$REPO" add "$METADATA_FILE"
git -C "$REPO" commit -q -m "add metadata conflict fixture"

git -C "$REPO" checkout -q -b chat/metadata-only
sed -i 's/updated_on: "2026-01-01"/updated_on: "2026-01-02"/' "$REPO/$METADATA_FILE"
git -C "$REPO" add "$METADATA_FILE"
git -C "$REPO" commit -q -m "chat lifecycle date"

git -C "$REPO" checkout -q main
sed -i 's/updated_on: "2026-01-01"/updated_on: "2026-01-03"/' "$REPO/$METADATA_FILE"
git -C "$REPO" add "$METADATA_FILE"
git -C "$REPO" commit -q -m "main lifecycle date"

git -C "$REPO" checkout -q chat/metadata-only
set +e
git -C "$REPO" merge main >/dev/null 2>&1
MERGE_STATUS="$?"
set -e

if [ "$MERGE_STATUS" -eq 0 ]; then
  fail "expected metadata-only conflict"
fi

OUTPUT="$(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/classify-conflict/script.sh "$METADATA_FILE"
)"

if ! printf '%s\n' "$OUTPUT" | grep -q '^type=artifact-metadata-date-conflict$'; then
  fail "metadata-only lifecycle conflict was not classified"
fi

git -C "$REPO" merge --abort
git -C "$REPO" checkout -q main

PLAN_INDEX="docs/04.deploy/plans/README.md"
mkdir -p "$REPO/$(dirname "$PLAN_INDEX")"
cat > "$REPO/$PLAN_INDEX" <<'EOF'
<!-- agentic-artifact:
version: 1
-->
# Plans

| Plan | Purpose |
| --- | --- |
| [base.md](base.md) | Base plan. |
EOF
git -C "$REPO" add "$PLAN_INDEX"
git -C "$REPO" commit -q -m "add plan index"

git -C "$REPO" checkout -q -b chat/plan-index
sed -i 's/version: 1/version: 2/' "$REPO/$PLAN_INDEX"
printf '%s\n' '| [chat.md](chat.md) | Chat plan. |' >> "$REPO/$PLAN_INDEX"
git -C "$REPO" add "$PLAN_INDEX"
git -C "$REPO" commit -q -m "add chat plan row"

git -C "$REPO" checkout -q main
printf '%s\n' '| [main.md](main.md) | Main plan. |' >> "$REPO/$PLAN_INDEX"
git -C "$REPO" add "$PLAN_INDEX"
git -C "$REPO" commit -q -m "add main plan row"

git -C "$REPO" checkout -q chat/plan-index
set +e
git -C "$REPO" merge main >/dev/null 2>&1
MERGE_STATUS="$?"
set -e

if [ "$MERGE_STATUS" -eq 0 ]; then
  fail "expected append-only plan-index conflict"
fi

OUTPUT="$(
  cd "$REPO"
  bash scripts/00.chat/main-refresh/classify-conflict/script.sh "$PLAN_INDEX"
)"

if ! printf '%s\n' "$OUTPUT" | grep -q '^type=append-only-plan-index-conflict$'; then
  fail "append-only plan index conflict was not classified"
fi

REAL_GIT="$(command -v git)"
export REAL_GIT
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == ls-files && "${FAIL_READ:-}" == index ]]; then
  echo PRIVATE_GIT_CANARY >&2
  exit 71
fi
if [[ "$1" == show && "$2" == ":${FAIL_READ:-}:"* ]]; then
  echo PRIVATE_GIT_CANARY >&2
  exit 72
fi
exec "$REAL_GIT" "$@"
EOF
chmod +x "$TMP_ROOT/bin/git"
for stage in index 1 2 3; do
  if (cd "$REPO" && PATH="$TMP_ROOT/bin:$PATH" FAIL_READ="$stage" bash scripts/00.chat/main-refresh/classify-conflict/script.sh "$PLAN_INDEX") >"$TMP_ROOT/read.out" 2>"$TMP_ROOT/read.err"; then
    fail "failed conflict read became successful classification"
  fi
  test ! -s "$TMP_ROOT/read.out" || fail "failed read emitted a classification"
  if [[ "$stage" == index ]]; then expected='ERROR: conflict-index-read-failed';
  else expected="ERROR: conflict-stage-read-failed stage=$stage"; fi
  test "$(cat "$TMP_ROOT/read.err")" = "$expected" || fail "failed read lost safe stage attribution"
done
echo "main refresh conflict classifier smoke test passed."

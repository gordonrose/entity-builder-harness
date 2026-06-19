#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/run-governed-script-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/scripts/shared/harness" "$REPO/scripts/shared/git" "$REPO/.agentic/harness/data"
cp "$SOURCE_ROOT/scripts/shared/harness/run-governed-script.sh" \
  "$REPO/scripts/shared/harness/run-governed-script.sh"
cp "$SOURCE_ROOT/.agentic/harness/data/governed-script-allowlist.txt" \
  "$REPO/.agentic/harness/data/governed-script-allowlist.txt"

cat > "$REPO/scripts/shared/git/checkpoint-chat-session-log.sh" <<'EOF'
#!/usr/bin/env bash
printf 'checkpoint %s\n' "$1"
EOF

cat > "$REPO/scripts/shared/git/not-allowed.sh" <<'EOF'
#!/usr/bin/env bash
echo "not allowed"
EOF

(
  cd "$REPO"
  git init -q
  git config user.name "Smoke Test"
  git config user.email "smoke@example.invalid"
  git add .
  git commit -q -m "initial"
)

(
  cd "$REPO"
  bash scripts/shared/harness/run-governed-script.sh --list > "$TMP_ROOT/list.txt"
  bash scripts/shared/harness/run-governed-script.sh \
    scripts/shared/git/checkpoint-chat-session-log.sh ok > "$TMP_ROOT/run.txt"
)

if ! grep -q '^scripts/shared/git/checkpoint-chat-session-log.sh$' "$TMP_ROOT/list.txt"; then
  fail "allowlist did not include checkpoint helper"
fi

if ! grep -q '^checkpoint ok$' "$TMP_ROOT/run.txt"; then
  fail "allowlisted script did not run with arguments"
fi

set +e
(
  cd "$REPO"
  bash scripts/shared/harness/run-governed-script.sh scripts/shared/git/not-allowed.sh
) >/dev/null 2>"$TMP_ROOT/blocked.err"
BLOCKED_STATUS="$?"
set -e

if [ "$BLOCKED_STATUS" -eq 0 ]; then
  fail "non-allowlisted script was allowed"
fi

if ! grep -q "not on the governed allowlist" "$TMP_ROOT/blocked.err"; then
  fail "blocked script failure was not explained"
fi

echo "run governed script smoke test passed."

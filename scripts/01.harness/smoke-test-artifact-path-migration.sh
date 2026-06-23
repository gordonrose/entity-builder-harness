#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Smoke test artifact path migration planning and validation helpers.
#   domain: migration
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/01.harness/workflows/migrate-artifact-paths.md
#     - scripts/01.harness/plan-artifact-path-migration.sh
#     - scripts/01.harness/check-artifact-path-migration.sh
#   effects: read-only

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q

mkdir -p \
  "$REPO/.agentic/01.harness/workflows" \
  "$REPO/scripts/01.harness" \
  "$REPO/docs/00.chat/bootstrap" \
  "$REPO/commitLogs/2026/jun/20/example"

cat > "$REPO/AGENTS.md" <<'EOF'
Use .agentic/01.harness/workflows/change-harness.md.
EOF

cat > "$REPO/.agentic/01.harness/workflows/change-harness.md" <<'EOF'
Consult .agentic/01.harness/standards/example.md.
EOF

cat > "$REPO/scripts/01.harness/example.sh" <<'EOF'
#!/usr/bin/env bash
echo .agentic/01.harness
EOF

cat > "$REPO/docs/00.chat/bootstrap/example.md" <<'EOF'
Bootstrap .agentic/01.harness.
EOF

cat > "$REPO/commitLogs/2026/jun/20/example/README.md" <<'EOF'
workflow: .agentic/01.harness/workflows/change-harness.md
EOF

(
  cd "$REPO"
  PLAN_OUTPUT="$(bash "$SOURCE_ROOT/scripts/01.harness/plan-artifact-path-migration.sh" .agentic/01.harness .agentic/01.harness)"

  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^old_path=.agentic/01.harness$' || fail "plan missing old path"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[routing\]$' || fail "plan missing routing bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[workflow\]$' || fail "plan missing workflow bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[script\]$' || fail "plan missing script bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[bootstrap\]$' || fail "plan missing bootstrap bucket"
  printf '%s\n' "$PLAN_OUTPUT" | grep -q '^\[session-history\]$' || fail "plan missing session-history bucket"

  if bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" .agentic/01.harness .agentic/01.harness >"$TMP_ROOT/check.out" 2>"$TMP_ROOT/check.err"; then
    fail "checker allowed active old-path references without compatibility approval"
  fi

  grep -q 'active old-path references remain' "$TMP_ROOT/check.err" || fail "checker failure did not explain active references"

  bash "$SOURCE_ROOT/scripts/01.harness/check-artifact-path-migration.sh" --allow-active-old-path .agentic/01.harness .agentic/01.harness >"$TMP_ROOT/allow.out"
  grep -q '^artifact_path_migration_check=ok$' "$TMP_ROOT/allow.out" || fail "checker did not pass with explicit compatibility approval"
)

echo "OK: artifact path migration helpers smoke test passed."

#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.upstream.validate-llm-workbench-portability
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run user acceptance tests for provider-neutral llm-workbench installs.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.upstream.validate-llm-workbench-portability.readme
#     path: scripts/00.chat/upstream/validate-llm-workbench-portability/README.md
#   effects:
#   - writes-files
#   - branches
#   - worktrees
#   - commits

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -f "$path" ] || fail "missing file: $path"
}

require_dir_absent() {
  local path="$1"
  [ ! -d "$path" ] || fail "unexpected directory exists: $path"
}

require_grep() {
  local pattern="$1"
  local path="$2"
  grep -Eq -- "$pattern" "$path" || fail "missing pattern '$pattern' in $path"
}

reject_grep() {
  local pattern="$1"
  local path="$2"
  if grep -Eq -- "$pattern" "$path"; then
    fail "unexpected pattern '$pattern' in $path"
  fi
}

reject_tree_grep() {
  local pattern="$1"
  local path="$2"
  if grep -RIEq -- "$pattern" "$path"; then
    fail "unexpected pattern '$pattern' under $path"
  fi
}

require_portable_harness_scripts() {
  local repo="$1"
  local required_path

  for required_path in \
    scripts/01.harness/run-governed-script.sh \
    scripts/01.harness/check-deterministic-process-drift.sh \
    scripts/01.harness/check-governed-script-command-drift.sh \
    scripts/01.harness/artifact-metadata/check-headers/script.sh \
    scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh; do
    require_file "$repo/$required_path"
  done
}

reject_source_maintenance_harness_scripts() {
  local repo="$1"
  local source_only_path

  for source_only_path in \
    scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh \
    scripts/01.harness/artifact-metadata/generate-index/script.sh \
    scripts/01.harness/check-artifact-metadata-headers.sh \
    scripts/01.harness/check-artifact-path-migration.sh \
    scripts/01.harness/check-rule-test-taxonomy.sh \
    scripts/01.harness/plan-artifact-path-migration.sh \
    scripts/01.harness/smoke-test-artifact-path-migration.sh; do
    [ ! -e "$repo/$source_only_path" ] ||
      fail "target contains source-maintenance harness script: $source_only_path"
  done

  reject_tree_grep '\.agentic/01\.harness|scripts/02\.rag-rulebook|\.agentic/02\.rag-rulebook' \
    "$repo/scripts/01.harness"
}

reject_public_adrs() {
  local repo="$1"

  [ ! -e "$repo/docs/00.chat/public-chat-workbench-adrs.md" ] ||
    fail "target contains public ADR export manifest"
  [ ! -e "$repo/docs/harness/architecture/adrs" ] ||
    fail "target contains exported ADR docs"

  if [ -d "$repo/docs" ]; then
    reject_tree_grep 'Architecture Decision Record|ADRs copied|ADR export|see ADR|refer to ADR' \
      "$repo/docs"
  fi
}

make_repo() {
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init --quiet --initial-branch=main
  git -C "$repo" config user.name "llm-workbench acceptance"
  git -C "$repo" config user.email "llm-workbench-acceptance@example.invalid"
}

build_public_workbench() {
  local source_root="$1"
  local workbench_repo="$2"

  make_repo "$workbench_repo"
  bash "$source_root/scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh" \
    --target "$workbench_repo" \
    --apply > "$TMP_ROOT/public-workbench-apply.out"
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/llm-workbench-portability-acceptance.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

WORKBENCH_REPO="$TMP_ROOT/llm-workbench"
bash "$SOURCE_ROOT/scripts/00.chat/upstream/check-llm-workbench-contract/script.sh" \
  > "$TMP_ROOT/source-contract-check.out"
build_public_workbench "$SOURCE_ROOT" "$WORKBENCH_REPO"

require_file "$WORKBENCH_REPO/README.md"
require_file "$WORKBENCH_REPO/package.json"
require_file "$WORKBENCH_REPO/scripts/install.sh"
require_file "$WORKBENCH_REPO/scripts/uninstall.sh"
require_file "$WORKBENCH_REPO/scripts/00.chat/metrics/data/chat-pricing.json"
require_file "$WORKBENCH_REPO/scripts/00.chat/metrics/data/chat-pricing.schema.json"
require_file "$WORKBENCH_REPO/.github/workflows/portability.yml"
require_portable_harness_scripts "$WORKBENCH_REPO"
reject_source_maintenance_harness_scripts "$WORKBENCH_REPO"
reject_public_adrs "$WORKBENCH_REPO"
require_dir_absent "$WORKBENCH_REPO/scripts/00.chat/classification"
require_dir_absent "$WORKBENCH_REPO/.agentic/agentic"
require_dir_absent "$WORKBENCH_REPO/.agentic/01.harness"
require_dir_absent "$WORKBENCH_REPO/.agentic/docs"
require_dir_absent "$WORKBENCH_REPO/.agentic/scripts"
require_dir_absent "$WORKBENCH_REPO/.docs"
require_dir_absent "$WORKBENCH_REPO/.scripts"

if [ -d "$WORKBENCH_REPO/.agentic/00.chat" ] && [ -d "$WORKBENCH_REPO/.agentic/agentic/00.chat" ]; then
  fail "duplicate canonical chat harness trees found in generated public repo"
fi

if grep -RIEq '\.agentic/01\.harness' "$WORKBENCH_REPO/.agentic" 2>/dev/null; then
  fail "public export .agentic surface references missing .agentic/01.harness"
fi

reject_grep 'classify-task|Unknown Metadata|^layer:|^mode:|^workflow:' \
  "$WORKBENCH_REPO/.agentic/00.chat/workflows/chat-start.md"
reject_grep 'classify-task|^layer: \$\{|^mode: \$\{|^workflow: \$\{' \
  "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
reject_grep 'query the RAG/rulebook runtime|\.agentic/02\.rag-rulebook|scripts/02\.rag-rulebook' \
  "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
reject_grep 'scripts/00\.chat/classification|classification behavior|Chat session metadata should include all resolved fields|classify mode|^layer: harness$|^mode: planning$' \
  "$WORKBENCH_REPO/.agentic/shared/workflows/capability-resolution-workflow.md"
reject_grep 'RAG/rulebook|\.agentic/02\.rag-rulebook|scripts/02\.rag-rulebook' \
  "$WORKBENCH_REPO/.agentic/00.chat/checklists/before-commit.md"
reject_grep 'Architecture Rulebook Operating Pack|Future Codex sessions continuing rulebook work|RAG/rulebook machinery now has its own layer|\.agentic/02\.rag-rulebook' \
  "$WORKBENCH_REPO/AGENTS.md"
reject_grep 'scripts/00\.chat/classification' "$WORKBENCH_REPO/scripts/install.sh"
reject_tree_grep '\.agentic/01\.harness/data/openai-chat-pricing\.json|openai-chat-pricing\.json' \
  "$WORKBENCH_REPO/scripts/00.chat"
reject_tree_grep 'RAG/rulebook|\.agentic/02\.rag-rulebook|scripts/02\.rag-rulebook' \
  "$WORKBENCH_REPO/scripts/00.chat/session-log"
reject_grep 'git -C "\$TARGET_REPO" add -A|git -C "\$TARGET_REPO" add --all|git -C "\$TARGET_REPO" add \.' \
  "$WORKBENCH_REPO/scripts/install.sh"
require_grep 'scripts/00\.chat/metrics/data/chat-pricing\.json' \
  "$WORKBENCH_REPO/scripts/00.chat/metrics/estimate-chat-cost/script.js"
require_grep '"default_profile": "portable-unpriced"' \
  "$WORKBENCH_REPO/scripts/00.chat/metrics/data/chat-pricing.json"
require_grep '"estimate_rate_usd_per_1m_tokens": null' \
  "$WORKBENCH_REPO/scripts/00.chat/metrics/data/chat-pricing.json"
require_grep 'exec bash "\$COMMAND_SCRIPT" "\$@"' \
  "$WORKBENCH_REPO/scripts/00.chat/command/dispatcher/script.sh"
reject_grep 'chat command is not executable' \
  "$WORKBENCH_REPO/scripts/00.chat/command/dispatcher/script.sh"
require_grep 'chat_lifecycle_workflow:' \
  "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
require_grep 'latest_context_packet_id:' \
  "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
require_grep 'transcript_provider:' \
  "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"

require_grep 'pbcopy' "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
require_grep 'clip.exe' "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
require_grep 'xclip' "$WORKBENCH_REPO/scripts/00.chat/startup/start-chat-session/script.sh"
require_grep 'stat -f' "$WORKBENCH_REPO/scripts/00.chat/transcript/discover-codex-session-log/script.sh"
require_grep 'stat -c' "$WORKBENCH_REPO/scripts/00.chat/transcript/discover-codex-session-log/script.sh"
require_grep 'ubuntu-latest' "$WORKBENCH_REPO/.github/workflows/portability.yml"
require_grep 'macos-latest' "$WORKBENCH_REPO/.github/workflows/portability.yml"
require_grep 'windows-latest' "$WORKBENCH_REPO/.github/workflows/portability.yml"
require_grep '--dry-run' "$WORKBENCH_REPO/docs/install.md"
require_grep '--apply' "$WORKBENCH_REPO/docs/install.md"
require_grep '--init-commit' "$WORKBENCH_REPO/docs/install.md"
require_grep 'only for repos with no existing `HEAD`' "$WORKBENCH_REPO/docs/install.md"
require_grep 'chat:new -- --json' "$WORKBENCH_REPO/docs/workflows.md"
require_grep 'CHAT_TRANSCRIPT_PROVIDER' "$WORKBENCH_REPO/docs/workflows.md"

(
  cd "$WORKBENCH_REPO"
  bash scripts/00.chat/upstream/check-llm-workbench-contract/script.sh \
    --repo "$WORKBENCH_REPO" \
    --public \
    > "$TMP_ROOT/public-contract-check.out"
  bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all \
    > "$TMP_ROOT/public-check-headers-all.out"
  bash scripts/00.chat/session-log/record-chat-commit/smoke-test.sh \
    > "$TMP_ROOT/public-record-chat-commit-smoke.out"
  node scripts/00.chat/metrics/estimate-chat-cost/script.js 1024 \
    > "$TMP_ROOT/public-default-cost.out"
  CHAT_COST_PROFILE=openai-chat-latest-standard-conservative-output \
    node scripts/00.chat/metrics/estimate-chat-cost/script.js 1024 \
    > "$TMP_ROOT/public-openai-cost.out"
)
require_grep '^estimated_chat_cost: unavailable; no pricing profile selected$' \
  "$TMP_ROOT/public-default-cost.out"
require_grep '^estimated_chat_cost_basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE$' \
  "$TMP_ROOT/public-default-cost.out"
require_grep '^estimated_chat_cost: USD 0\.0307 estimated from estimated_chat_tokens$' \
  "$TMP_ROOT/public-openai-cost.out"

for os_name in linux macos windows wsl; do
  OS_REPO="$TMP_ROOT/os-$os_name"
  make_repo "$OS_REPO"
  LLM_WORKBENCH_TARGET_OS="$os_name" \
    bash "$WORKBENCH_REPO/scripts/install.sh" --dry-run "$OS_REPO" \
    > "$TMP_ROOT/install-$os_name-dry-run.out"
  grep -q '^mode: dry-run$' "$TMP_ROOT/install-$os_name-dry-run.out" \
    || fail "dry-run summary missing for OS target: $os_name"
done

EXISTING_REPO="$TMP_ROOT/existing-target"
make_repo "$EXISTING_REPO"
cat > "$EXISTING_REPO/package.json" <<'JSON'
{
  "name": "existing-target",
  "scripts": {
    "build": "echo build"
  },
  "dependencies": {
    "left-pad": "1.3.0"
  }
}
JSON
printf '# Existing Agent Rules\n\nKeep this line.\n' > "$EXISTING_REPO/AGENTS.md"

bash "$WORKBENCH_REPO/scripts/install.sh" --dry-run "$EXISTING_REPO" \
  > "$TMP_ROOT/existing-dry-run.out"
grep -q '^PACKAGE_ADD_SCRIPT chat ' "$TMP_ROOT/existing-dry-run.out" \
  || fail "existing repo did not plan chat script merge"
grep -q '^PATCH_BLOCK AGENTS.md$' "$TMP_ROOT/existing-dry-run.out" \
  || fail "existing repo did not plan AGENTS.md block patch"

bash "$WORKBENCH_REPO/scripts/install.sh" --apply "$EXISTING_REPO" \
  > "$TMP_ROOT/existing-apply.out"
node -e "const p=require(process.argv[1]); if (p.name !== 'existing-target') process.exit(1); if (p.scripts.build !== 'echo build') process.exit(1); if (!p.scripts['chat:new']) process.exit(1); if (!p.dependencies['left-pad']) process.exit(1)" \
  "$EXISTING_REPO/package.json" || fail "existing package data was not preserved"
require_grep 'Keep this line\.' "$EXISTING_REPO/AGENTS.md"
require_grep 'llm-workbench:start' "$EXISTING_REPO/AGENTS.md"
require_file "$EXISTING_REPO/CLAUDE.md"
require_file "$EXISTING_REPO/.github/copilot-instructions.md"
require_file "$EXISTING_REPO/.cursor/rules/llm-workbench.mdc"
require_file "$EXISTING_REPO/LLM_WORKBENCH.md"
require_file "$EXISTING_REPO/.llm-workbench/install-manifest.tsv"
require_portable_harness_scripts "$EXISTING_REPO"
reject_source_maintenance_harness_scripts "$EXISTING_REPO"
reject_public_adrs "$EXISTING_REPO"
require_dir_absent "$EXISTING_REPO/.agentic/01.harness"

if find "$EXISTING_REPO/.agentic" -path '*/01.harness/*' -o -path '*/01.harness' | grep -q .; then
  fail "installed target contains upstream .agentic/01.harness files"
fi

if grep -RIEq 'Future Codex sessions continuing rulebook work|Architecture Rulebook Operating Pack|RAG/rulebook machinery now has its own layer' \
  "$EXISTING_REPO/.agentic" 2>/dev/null; then
  fail "installed target contains source-specific RAG/rulebook harness guidance"
fi

reject_grep 'RAG/rulebook|\.agentic/02\.rag-rulebook|scripts/02\.rag-rulebook' \
  "$EXISTING_REPO/.agentic/00.chat/checklists/before-commit.md"

if grep -RIEq '\.agentic/01\.harness' "$EXISTING_REPO/.agentic" 2>/dev/null; then
  fail "installed target .agentic surface references missing .agentic/01.harness"
fi

(
  cd "$EXISTING_REPO"
  bash scripts/01.harness/artifact-metadata/check-headers/script.sh \
    --paths scripts/00.chat/startup/start-chat-session/script.sh \
    > "$TMP_ROOT/existing-check-headers.out"
  bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all \
    > "$TMP_ROOT/existing-check-headers-all.out"
)

for adapter in \
  "$EXISTING_REPO/AGENTS.md" \
  "$EXISTING_REPO/CLAUDE.md" \
  "$EXISTING_REPO/.github/copilot-instructions.md" \
  "$EXISTING_REPO/.cursor/rules/llm-workbench.mdc" \
  "$EXISTING_REPO/LLM_WORKBENCH.md"; do
  require_grep '\.agentic/00\.chat/workflows/chat-start\.md' "$adapter"
  require_grep 'Do not assign the whole chat a durable layer, mode, or workflow' "$adapter"
  require_grep 'repo-provided context' "$adapter"
  require_grep 'router if one exists' "$adapter"
  reject_grep 'RAG/rulebook runtime|RAG/rulebook routing|RAG queries' "$adapter"
done

EXISTING_INIT_REPO="$TMP_ROOT/existing-init-target"
make_repo "$EXISTING_INIT_REPO"
printf 'base\n' > "$EXISTING_INIT_REPO/README.md"
git -C "$EXISTING_INIT_REPO" add README.md
git -C "$EXISTING_INIT_REPO" commit --quiet -m "base"
printf 'do not commit me\n' > "$EXISTING_INIT_REPO/unrelated.txt"

if bash "$WORKBENCH_REPO/scripts/install.sh" --apply --init-commit "$EXISTING_INIT_REPO" \
  > "$TMP_ROOT/existing-init.out" 2> "$TMP_ROOT/existing-init.err"; then
  fail "--init-commit unexpectedly succeeded in an existing repo"
fi

require_grep '--init-commit is only for repos with no existing HEAD' "$TMP_ROOT/existing-init.err"
if [ -e "$EXISTING_INIT_REPO/.llm-workbench/install-manifest.tsv" ]; then
  fail "--init-commit wrote install files before rejecting an existing repo"
fi
if git -C "$EXISTING_INIT_REPO" ls-files --error-unmatch unrelated.txt >/dev/null 2>&1; then
  fail "--init-commit committed unrelated file in existing repo"
fi

BLANK_REPO="$TMP_ROOT/blank-target"
make_repo "$BLANK_REPO"
bash "$WORKBENCH_REPO/scripts/install.sh" --apply --init-commit "$BLANK_REPO" \
  > "$TMP_ROOT/blank-apply.out"
git -C "$BLANK_REPO" rev-parse --verify HEAD >/dev/null \
  || fail "blank repo did not receive an install-time initial commit"
require_dir_absent "$BLANK_REPO/.agentic/01.harness"
find "$BLANK_REPO/scripts" -type f -name '*.sh' -exec chmod 0644 {} +

UNBORN_DIRTY_REPO="$TMP_ROOT/unborn-dirty-target"
make_repo "$UNBORN_DIRTY_REPO"
printf 'do not commit me\n' > "$UNBORN_DIRTY_REPO/unrelated.txt"
bash "$WORKBENCH_REPO/scripts/install.sh" --apply --init-commit "$UNBORN_DIRTY_REPO" \
  > "$TMP_ROOT/unborn-dirty-apply.out"
git -C "$UNBORN_DIRTY_REPO" rev-parse --verify HEAD >/dev/null \
  || fail "unborn dirty repo did not receive an install-time initial commit"
if git -C "$UNBORN_DIRTY_REPO" ls-files --error-unmatch unrelated.txt >/dev/null 2>&1; then
  fail "unborn install commit included unrelated pre-existing file"
fi
if [ ! -f "$UNBORN_DIRTY_REPO/unrelated.txt" ]; then
  fail "unborn install removed unrelated pre-existing file"
fi
require_dir_absent "$UNBORN_DIRTY_REPO/.agentic/01.harness"

(
  cd "$BLANK_REPO"
  AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/blank-worktrees" \
  CHAT_COPY_PROMPT=skip \
  CHAT_CLEANUP_EMPTY_BRANCHES=skip \
  CHAT_OPEN_WORKTREE_WINDOW=skip \
    npm run --silent chat:new -- "blank repo first chat startup" \
    > "$TMP_ROOT/blank-chat-new.out"
)

BLANK_LOG="$(find "$TMP_ROOT/blank-worktrees" -path '*/commitLogs/*/README.md' -type f | head -n 1)"
[ -n "$BLANK_LOG" ] || fail "blank repo first chat did not create a session log"
require_grep '^chat_lifecycle_workflow: \.agentic/00\.chat/workflows/chat-start\.md$' "$BLANK_LOG"
require_grep '^latest_context_packet_id:$' "$BLANK_LOG"
require_grep '^transcript_provider:$' "$BLANK_LOG"
reject_grep '^layer:|^mode:|^workflow:|^codex_session_log_path:' "$BLANK_LOG"

BLANK_WORKTREE="${BLANK_LOG%%/commitLogs/*}"
(
  cd "$BLANK_WORKTREE"
  bash scripts/00.chat/session-log/record-chat-commit/script.sh \
    abcdef0 \
    "Portable missing transcript" \
    "Record commit without provider-specific transcript metrics" \
    > "$TMP_ROOT/portable-record.out"
)
require_grep '^estimated_chat_tokens: unavailable; transcript source not supplied by chat$' "$BLANK_LOG"

(
  cd "$BLANK_WORKTREE"
  CHAT_TRANSCRIPT_PROVIDER=mistral \
  CHAT_TRANSCRIPT_BYTES=4096 \
  CHAT_TRANSCRIPT_SOURCE="Mistral CLI transcript bytes" \
    bash scripts/00.chat/session-log/record-chat-commit/script.sh \
      fedcba9 \
      "Manual provider transcript" \
      "Record commit with manual Mistral transcript metrics" \
      > "$TMP_ROOT/manual-record.out"
)
require_grep '^transcript_provider: mistral$' "$BLANK_LOG"
require_grep 'source: Mistral CLI transcript bytes' "$BLANK_LOG"
require_grep '^estimated_chat_cost: unavailable; no pricing profile selected$' "$BLANK_LOG"
require_grep '^estimated_chat_cost_basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE$' "$BLANK_LOG"

cat > "$TMP_ROOT/custom-chat-pricing.json" <<'JSON'
{
  "schema_version": 1,
  "default_profile": "mistral-test",
  "currency": "USD",
  "unit": "1M tokens",
  "source": {
    "url": "acceptance-test fixture",
    "retrieved_at_utc": "2026-07-03T00:00:00Z"
  },
  "profiles": {
    "mistral-test": {
      "provider": "mistral",
      "model": "mistral-test",
      "tier": "acceptance",
      "context": "test",
      "estimate_rate_usd_per_1m_tokens": 10,
      "assumption": "acceptance test fixture"
    }
  }
}
JSON

(
  cd "$BLANK_WORKTREE"
  CHAT_TRANSCRIPT_PROVIDER=mistral \
  CHAT_TRANSCRIPT_BYTES=4096 \
  CHAT_TRANSCRIPT_SOURCE="Mistral CLI transcript bytes" \
  CHAT_COST_PRICING_FILE="$TMP_ROOT/custom-chat-pricing.json" \
  CHAT_COST_PROFILE=mistral-test \
    bash scripts/00.chat/session-log/record-chat-commit/script.sh \
      abcd123 \
      "Custom provider pricing" \
      "Record commit with custom Mistral pricing profile" \
      > "$TMP_ROOT/custom-provider-record.out"
)
require_grep '^estimated_chat_cost: USD 0\.0102 estimated from estimated_chat_tokens$' "$BLANK_LOG"
require_grep '^estimated_chat_cost_basis: profile=mistral-test; model=mistral-test;' "$BLANK_LOG"

bash "$WORKBENCH_REPO/scripts/uninstall.sh" --apply "$EXISTING_REPO" \
  > "$TMP_ROOT/existing-uninstall.out"
reject_grep 'llm-workbench:start' "$EXISTING_REPO/AGENTS.md"
node -e "const p=require(process.argv[1]); if (p.scripts['chat:new']) process.exit(1); if (p.scripts.build !== 'echo build') process.exit(1)" \
  "$EXISTING_REPO/package.json" || fail "uninstall did not remove only workbench package scripts"

echo "llm-workbench portability acceptance suite passed."

#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.upstream.check-llm-workbench-contract
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Statically validate llm-workbench public-beta contract invariants.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.upstream.check-llm-workbench-contract.readme
#     path: scripts/00.chat/upstream/check-llm-workbench-contract/README.md
#   - id: chat.script.upstream.validate-llm-workbench-portability
#     path: scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
#   effects:
#   - read-only

usage() {
  cat <<'EOF'
Usage:
  check-llm-workbench-contract.sh [--repo <repo>] [--public]

Runs fast static checks for the llm-workbench public-beta contract.
EOF
}

REPO=""
PUBLIC_MODE="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      if [ -z "$REPO" ]; then
        echo "ERROR: --repo requires a value." >&2
        exit 2
      fi
      shift 2
      ;;
    --public)
      PUBLIC_MODE="yes"
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

if [ -z "$REPO" ]; then
  REPO="$(git rev-parse --show-toplevel)"
fi

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -f "$REPO/$path" ] || fail "missing file: $path"
}

require_absent_dir() {
  local path="$1"
  [ ! -d "$REPO/$path" ] || fail "unexpected source-only directory: $path"
}

require_absent_file() {
  local path="$1"
  [ ! -e "$REPO/$path" ] || fail "unexpected source-only file: $path"
}

require_grep() {
  local pattern="$1"
  local path="$2"
  grep -Eq -- "$pattern" "$REPO/$path" || fail "missing pattern '$pattern' in $path"
}

reject_grep() {
  local pattern="$1"
  local path="$2"
  if grep -Eq -- "$pattern" "$REPO/$path"; then
    fail "unexpected pattern '$pattern' in $path"
  fi
}

reject_tree_grep() {
  local pattern="$1"
  local path="$2"
  [ -e "$REPO/$path" ] || return 0
  if grep -RIEq -- "$pattern" "$REPO/$path"; then
    fail "unexpected pattern '$pattern' under $path"
  fi
}

require_file ".agentic/00.chat/workflows/chat-start.md"
require_file "scripts/00.chat/startup/start-chat-session/script.sh"
require_file "scripts/00.chat/session-log/record-chat-commit/script.sh"
require_file "scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh"
require_file "scripts/00.chat/metrics/estimate-chat-cost/script.js"
require_file "scripts/00.chat/metrics/data/chat-pricing.json"
require_file "scripts/00.chat/metrics/data/chat-pricing.schema.json"
require_file "scripts/00.chat/command/dispatcher/script.sh"

reject_grep 'classify-task|Unknown Metadata|^layer:|^mode:|^workflow:' \
  ".agentic/00.chat/workflows/chat-start.md"
reject_grep 'classify-task|^layer: \$\{|^mode: \$\{|^workflow: \$\{' \
  "scripts/00.chat/startup/start-chat-session/script.sh"
reject_tree_grep '\.agentic/01\.harness/data/openai-chat-pricing\.json|openai-chat-pricing\.json' \
  "scripts/00.chat"
reject_tree_grep 'RAG/rulebook|\.agentic/02\.rag-rulebook|scripts/02\.rag-rulebook' \
  "scripts/00.chat/session-log"

require_grep 'scripts/00\.chat/metrics/data/chat-pricing\.json' \
  "scripts/00.chat/metrics/estimate-chat-cost/script.js"
require_grep '"default_profile": "portable-unpriced"' \
  "scripts/00.chat/metrics/data/chat-pricing.json"
require_grep '"estimate_rate_usd_per_1m_tokens": null' \
  "scripts/00.chat/metrics/data/chat-pricing.json"
require_grep 'exec bash "\$COMMAND_SCRIPT" "\$@"' \
  "scripts/00.chat/command/dispatcher/script.sh"
reject_grep 'chat command is not executable' \
  "scripts/00.chat/command/dispatcher/script.sh"

if [ "$PUBLIC_MODE" = "yes" ]; then
  require_file "README.md"
  require_absent_dir ".agentic/agentic"
  require_absent_dir ".agentic/01.harness"
  require_absent_dir ".agentic/docs"
  require_absent_dir ".agentic/scripts"
  require_absent_dir ".docs"
  require_absent_dir ".scripts"
  require_absent_dir "scripts/00.chat/classification"
  require_absent_dir "docs/harness/architecture/adrs"
  require_absent_file "docs/00.chat/chat-workbench-public-repo-readiness.md"
  require_absent_file "docs/00.chat/public-chat-workbench-adrs.md"

  for required_path in \
    "scripts/01.harness/run-governed-script.sh" \
    "scripts/01.harness/check-deterministic-process-drift.sh" \
    "scripts/01.harness/check-governed-script-command-drift.sh" \
    "scripts/01.harness/artifact-metadata/check-headers/script.sh" \
    "scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh"; do
    require_file "$required_path"
  done

  for source_only_path in \
    "scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh" \
    "scripts/01.harness/artifact-metadata/generate-index/script.sh" \
    "scripts/01.harness/check-artifact-metadata-headers.sh" \
    "scripts/01.harness/check-artifact-path-migration.sh" \
    "scripts/01.harness/check-rule-test-taxonomy.sh" \
    "scripts/01.harness/plan-artifact-path-migration.sh" \
    "scripts/01.harness/smoke-test-artifact-path-migration.sh"; do
    require_absent_file "$source_only_path"
  done

  require_file "AGENTS.md"
  require_file "CLAUDE.md"
  require_file ".github/copilot-instructions.md"
  require_file ".cursor/rules/llm-workbench.mdc"
  require_file "LLM_WORKBENCH.md"
  require_file "scripts/install.sh"
  require_file "scripts/uninstall.sh"
  require_file "docs/public-beta-contract.md"

  require_grep 'standalone, provider-neutral Git/Bash/npm chat harness' "README.md"
  reject_tree_grep 'close to a standalone public repo|not yet a blind copy operation|remaining work is to create the public repo shell|\.agentic/01\.harness/.*standards and workflows|required by metadata|entity-builder-harness' \
    "docs"
  reject_tree_grep 'Architecture Decision Record|ADRs copied|ADR export|see ADR|refer to ADR' \
    "docs"
  reject_tree_grep 'Works perfectly with every LLM assistant|every possible assistant|every VS Code setup' \
    "docs"
  reject_grep 'Works perfectly with every LLM assistant|every possible assistant|every VS Code setup' \
    "README.md"

  reject_tree_grep '\.agentic/01\.harness' ".agentic"
  reject_tree_grep '\.agentic/01\.harness|scripts/02\.rag-rulebook|\.agentic/02\.rag-rulebook' \
    "scripts/01.harness"
  reject_grep 'scripts/00\.chat/classification' "scripts/install.sh"
  reject_grep 'git -C "\$TARGET_REPO" add -A|git -C "\$TARGET_REPO" add --all|git -C "\$TARGET_REPO" add \.' \
    "scripts/install.sh"

  for adapter in \
    "AGENTS.md" \
    "CLAUDE.md" \
    ".github/copilot-instructions.md" \
    ".cursor/rules/llm-workbench.mdc" \
    "LLM_WORKBENCH.md"; do
    require_grep '\.agentic/00\.chat/workflows/chat-start\.md' "$adapter"
    require_grep 'Do not assign the whole chat a durable layer, mode, or workflow' "$adapter"
    reject_grep 'RAG/rulebook runtime|RAG/rulebook routing|RAG queries' "$adapter"
  done
else
  require_file ".agentic/00.chat/standards/llm-workbench-public-beta-contract.md"
  require_file ".agentic/00.chat/checklists/llm-workbench-public-beta.md"
  require_file "docs/00.chat/llm-workbench-acceptance-matrix.md"
  require_file "docs/00.chat/bootstrap/llm-workbench-template/root/docs/public-beta-contract.md.template"
  require_grep 'standalone, provider-neutral Git/Bash/npm chat harness' \
    "docs/00.chat/bootstrap/llm-workbench-template/root/README.md.template"
  reject_tree_grep 'Works perfectly with every LLM assistant|every possible assistant|every VS Code setup' \
    "docs/00.chat/bootstrap/llm-workbench-template/root"
fi

echo "llm-workbench public-beta contract check passed."

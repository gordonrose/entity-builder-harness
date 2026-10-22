#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.startup.start-chat-session.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-16"
#   updated_on: "2026-10-22"
#   layer: 00.chat
#   domain: startup
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test chat startup creates a separate chat-owned worktree.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.workflows.bootstrap-chat-workbench-repo
#     path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   - id: chat.script.startup.start-chat-session.readme
#     path: scripts/00.chat/startup/start-chat-session/README.md
#   effects:
#   - writes-files
#   - branches
#   - worktrees
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-worktree-session-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init --quiet --initial-branch=main

mkdir -p \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/startup/start-chat-session" \
  "$REPO/scripts/00.chat/worktree/dirty-worktree-check" \
  "$REPO/scripts/00.chat/worktree/ensure-chat-worktree" \
  "$REPO/scripts/00.chat/worktree/open-window" \
  "$REPO/scripts/00.chat/worktree/paths"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$REPO/scripts/00.chat/worktree/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/dirty-worktree-check/script.sh" "$REPO/scripts/00.chat/worktree/dirty-worktree-check/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-chat-session/script.sh" "$REPO/scripts/00.chat/startup/start-chat-session/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh"
chmod +x "$REPO/scripts/00.chat/startup/start-chat-session/script.sh" "$REPO/scripts/00.chat/worktree/dirty-worktree-check/script.sh" "$REPO/scripts/00.chat/worktree/ensure-chat-worktree/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"

printf 'base\n' > "$REPO/README.md"
git -C "$REPO" add README.md scripts
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=skip \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/startup/start-chat-session/script.sh "test chat worktree session" \
    >"$TMP_ROOT/chat-worktree-session.out"

if ! grep -q 'Skipping VS Code window open:' "$TMP_ROOT/chat-worktree-session.out"; then
  fail "startup did not skip VS Code window open by default"
fi

if ! grep -q '^Inspect the new worktree:$' "$TMP_ROOT/chat-worktree-session.out"; then
  fail "startup did not report how to inspect the new worktree"
fi

root_branch="$(git -C "$REPO" branch --show-current)"
if [ "$root_branch" != "main" ]; then
  fail "root branch changed to $root_branch"
fi

chat_branch="$(git -C "$REPO" branch --format='%(refname:short)' | grep '^chat/' | head -n 1)"
if [ -z "$chat_branch" ]; then
  fail "chat branch was not created"
fi

worktree_path="$(
  git -C "$REPO" worktree list --porcelain \
    | awk -v branch="refs/heads/${chat_branch}" '
      /^worktree / { path = substr($0, 10) }
      /^branch / && substr($0, 8) == branch { print path }
    '
)"

if [ -z "$worktree_path" ] || [ "$worktree_path" = "$REPO" ]; then
  fail "chat branch does not have a separate worktree"
fi

grep -Fqx "  cd $worktree_path" "$TMP_ROOT/chat-worktree-session.out" \
  || fail "startup did not provide the command to enter the new worktree"
grep -Fqx "  (cd $worktree_path && npm run chat -- open-window)" "$TMP_ROOT/chat-worktree-session.out" \
  || fail "startup did not provide the command to open the new worktree"

if [ -n "$(git -C "$REPO" diff --cached --name-only)" ]; then
  fail "root worktree has staged changes"
fi

if ! git -C "$worktree_path" diff --cached --name-only | grep -q '^commitLogs/'; then
  fail "chat worktree did not stage the session log"
fi

session_log="$(git -C "$worktree_path" diff --cached --name-only | grep '^commitLogs/.*/README.md$' | head -n 1)"
if [ -z "$session_log" ]; then
  fail "could not find staged session log"
fi

layer="$(sed -n '/<!-- agentic-session/,/-->/s/^layer: //p' "$worktree_path/$session_log" | head -n 1)"
mode="$(sed -n '/<!-- agentic-session/,/-->/s/^mode: //p' "$worktree_path/$session_log" | head -n 1)"
workflow="$(sed -n '/<!-- agentic-session/,/-->/s/^workflow: //p' "$worktree_path/$session_log" | head -n 1)"
chat_lifecycle_workflow="$(sed -n '/<!-- agentic-session/,/-->/s/^chat_lifecycle_workflow: //p' "$worktree_path/$session_log" | head -n 1)"

if [ -n "$layer" ] || [ -n "$mode" ] || [ -n "$workflow" ]; then
  fail "chat startup wrote durable classification fields"
fi

if [ "$chat_lifecycle_workflow" != ".agentic/00.chat/workflows/chat-start.md" ]; then
  fail "chat startup did not record the chat lifecycle workflow: ${chat_lifecycle_workflow:-missing}"
fi

if ! sed -n '/<!-- agentic-session/,/-->/p' "$worktree_path/$session_log" | grep -q '^latest_context_packet_id:$'; then
  fail "chat startup did not initialize latest_context_packet_id"
fi

if ! sed -n '/<!-- agentic-session/,/-->/p' "$worktree_path/$session_log" | grep -q '^latest_context_packet_routing_summary:$'; then
  fail "chat startup did not initialize latest_context_packet_routing_summary"
fi

if ! grep -q '^## Sub-Agent Activity$' "$worktree_path/$session_log"; then
  fail "chat startup did not initialize the sub-agent activity section"
fi

if ! grep -q '^## Context Hygiene$' "$worktree_path/$session_log"; then
  fail "chat startup did not initialize the context hygiene section"
fi

renamed_session_dir="${session_log%/README.md}-renamed"
mv "$worktree_path/${session_log%/README.md}" "$worktree_path/$renamed_session_dir"
git -C "$worktree_path" add -A commitLogs
session_log="$renamed_session_dir/README.md"

if bash -c 'cd "$1" && bash scripts/00.chat/worktree/dirty-worktree-check/script.sh' sh "$worktree_path" >"$TMP_ROOT/default-dirty.out"; then
  fail "default dirty-worktree check accepted the staged session log"
fi
grep -qx 'dirty' "$TMP_ROOT/default-dirty.out" \
  || fail "default dirty-worktree check did not report dirty"

bookkeeping_status="$(bash -c 'cd "$1" && bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping' sh "$worktree_path")"
[ "$bookkeeping_status" = "bookkeeping-only" ] \
  || fail "renamed session log changes were not accepted as bookkeeping-only"

printf 'unrelated work\n' > "$worktree_path/unrelated.txt"
if bash -c 'cd "$1" && bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping' sh "$worktree_path" >"$TMP_ROOT/mixed-dirty.out"; then
  fail "bookkeeping tolerance accepted unrelated worktree changes"
fi
grep -qx 'dirty' "$TMP_ROOT/mixed-dirty.out" \
  || fail "bookkeeping tolerance did not report mixed changes as dirty"

FAKE_BIN="$TMP_ROOT/fake-bin"
mkdir -p "$FAKE_BIN"
cat > "$FAKE_BIN/clip.exe" <<'EOF'
#!/usr/bin/env bash
cat >/dev/null
exit 1
EOF
chmod +x "$FAKE_BIN/clip.exe"

AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
CHAT_CLEANUP_EMPTY_BRANCHES=skip \
CHAT_COPY_PROMPT=copy \
CHAT_OPEN_WORKTREE_WINDOW=skip \
PATH="$FAKE_BIN:$PATH" \
  bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
    bash scripts/00.chat/startup/start-chat-session/script.sh "test clipboard fallback session" \
    >"$TMP_ROOT/chat-worktree-session-clipboard.out" 2>&1

if ! grep -q 'WARNING: Clipboard copy via clip.exe failed; printing prompt instead.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "clipboard failure did not warn before falling back"
fi

if ! grep -q 'Paste this into Codex / Claude / Mistral:' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "clipboard failure did not print the first prompt"
fi

if ! grep -q 'Governed startup bootstrap has already created this chat branch, worktree, and session log.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not explain startup bootstrap boundary"
fi

if ! grep -q 'Default mode after startup bootstrap: read-only until I grant write permission in this chat.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not preserve task write permission boundary"
fi

if ! grep -q "For prompt-level routing, use the current user request, this repo's assistant instructions, and any repo-provided context router if one exists." "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not explain neutral prompt-level routing"
fi

if ! grep -q 'delegate to a sub-agent when the assistant runtime supports it' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not request sub-agent delegation when available"
fi

if ! grep -q 'continue directly as direct-fallback' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not explain direct fallback behavior"
fi

if ! grep -q 'record-sub-agent-activity/script.sh' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not name the sub-agent activity recorder"
fi

if ! grep -q 'Return a summary covering delegation mode, fallback use, files changed, checks run, git actions, blockers, and next step.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not require a delegation summary"
fi

if ! grep -q 'Do not assign the whole chat a durable layer, mode, or workflow.' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt did not preserve durable classification guard"
fi

if grep -q 'query the RAG/rulebook runtime' "$TMP_ROOT/chat-worktree-session-clipboard.out"; then
  fail "first prompt assumes a RAG/rulebook runtime exists"
fi

# Starting an isolated chat must preserve staged, unstaged, and untracked source
# work without carrying a confirmation gate into either startup handoff format.
printf 'staged source work\n' >> "$REPO/README.md"
git -C "$REPO" add README.md
printf 'unstaged source work\n' >> "$REPO/README.md"
printf 'untracked source work\n' > "$REPO/unrelated.txt"
git -C "$REPO" diff --binary > "$TMP_ROOT/source-unstaged.before"
git -C "$REPO" diff --cached --binary > "$TMP_ROOT/source-staged.before"
git -C "$REPO" status --porcelain > "$TMP_ROOT/source-status.before"
cp "$REPO/unrelated.txt" "$TMP_ROOT/source-untracked.before"

for handoff in text json; do
  startup_args=()
  if [ "$handoff" = "json" ]; then
    startup_args+=(--json)
  fi
  AGENTIC_CHAT_WORKTREE_ROOT="$TMP_ROOT/worktrees" \
  CHAT_CLEANUP_EMPTY_BRANCHES=skip \
  CHAT_COPY_PROMPT=skip \
  CHAT_OPEN_WORKTREE_WINDOW=skip \
    bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
      bash scripts/00.chat/startup/start-chat-session/script.sh \
      "${startup_args[@]}" "dirty source $handoff handoff" \
      > "$TMP_ROOT/dirty-$handoff.out"

  if [ "$handoff" = "json" ]; then
    node - "$TMP_ROOT/dirty-json.out" > "$TMP_ROOT/dirty-json.prompt" <<'NODE'
const fs = require('node:fs');
const packet = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (packet.bootstrap_worktree_status !== 'dirty') {
  throw new Error('JSON startup lost the informational source-worktree status');
}
if (!fs.existsSync(packet.chat_worktree + '/' + packet.session_log)) {
  throw new Error('JSON startup did not create the declared chat session');
}
process.stdout.write(packet.first_prompt);
NODE
    prompt_file="$TMP_ROOT/dirty-json.prompt"
  else
    prompt_file="$TMP_ROOT/dirty-text.out"
  fi

  grep -q '^Bootstrap worktree status: dirty$' "$prompt_file" \
    || fail "$handoff startup lost the informational source-worktree status"
  if grep -q 'Blocked: dirty worktree\|Before that response, do not read workflows' "$prompt_file"; then
    fail "$handoff startup still blocks on unrelated source work"
  fi
  grep -q 'chat-start.md#existing-changes' "$prompt_file" \
    || fail "$handoff startup does not route existing work to the preservation policy"

  git -C "$REPO" diff --binary > "$TMP_ROOT/source-unstaged.after"
  git -C "$REPO" diff --cached --binary > "$TMP_ROOT/source-staged.after"
  git -C "$REPO" status --porcelain > "$TMP_ROOT/source-status.after"
  for snapshot in unstaged staged status; do
    cmp "$TMP_ROOT/source-$snapshot.before" "$TMP_ROOT/source-$snapshot.after" \
      || fail "$handoff startup changed source $snapshot state"
  done
  cmp "$TMP_ROOT/source-untracked.before" "$REPO/unrelated.txt" \
    || fail "$handoff startup changed untracked source work"
  [ "$(git -C "$REPO" branch --show-current)" = "main" ] \
    || fail "$handoff startup changed the source branch"

  dirty_chat_branch="$(git -C "$REPO" branch --format='%(refname:short)' --list "chat/*dirty-source-$handoff-handoff")"
  dirty_worktree="$(git -C "$REPO" worktree list --porcelain | awk \
    -v branch="refs/heads/$dirty_chat_branch" \
    '/^worktree / { path = substr($0, 10) } /^branch / && substr($0, 8) == branch { print path }')"
  [ -n "$dirty_worktree" ] && [ "$dirty_worktree" != "$REPO" ] \
    || fail "$handoff startup did not isolate the new chat"
  [ "$(cat "$dirty_worktree/README.md")" = "base" ] \
    || fail "$handoff startup imported tracked source work"
  [ ! -e "$dirty_worktree/unrelated.txt" ] \
    || fail "$handoff startup imported untracked source work"
done

echo "chat worktree session smoke test passed."

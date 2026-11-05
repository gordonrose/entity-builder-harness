#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.remote-promotion.prepare-clean-integration-worktree.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-09-27"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: remote-promotion
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Prove clean remote-promotion worktree preparation accepts only fast-forward candidates.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-promote-to-remote-main
#     path: .agentic/00.chat/workflows/chat-promote-to-remote-main.md
#   effects:
#   - branches
#   - worktrees
#   - commits
#   - writes-files
#   - destructive

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/remote-promotion-prep-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
REMOTE="$TMP_ROOT/origin.git"
mkdir -p "$REPO" "$REMOTE"
git -C "$REMOTE" init --bare -q
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"
git -C "$REPO" remote add origin "$REMOTE"
printf 'base\n' > "$REPO/base.txt"
git -C "$REPO" add base.txt
git -C "$REPO" commit -q -m "initial"
git -C "$REPO" push -q -u origin main
git -C "$REPO" fetch -q origin

git -C "$REPO" switch -q -c chat/2026-09-27-remote-promotion
printf 'candidate\n' > "$REPO/candidate.txt"
git -C "$REPO" add candidate.txt
git -C "$REPO" commit -q -m "candidate"
SOURCE_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
git -C "$REPO" switch -q main

DRY_OUTPUT="$(cd "$REPO" && TMPDIR="$TMP_ROOT" bash "$SOURCE_ROOT/scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh" --dry-run chat/2026-09-27-remote-promotion)"
printf '%s\n' "$DRY_OUTPUT" | grep -q '^result=dry-run$' || fail "dry run did not report success"

OUTPUT="$(cd "$REPO" && TMPDIR="$TMP_ROOT" bash "$SOURCE_ROOT/scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh" chat/2026-09-27-remote-promotion)"
INTEGRATION_WORKTREE="$(printf '%s\n' "$OUTPUT" | sed -n 's/^integration_worktree=//p')"
INTEGRATION_BRANCH="$(printf '%s\n' "$OUTPUT" | sed -n 's/^integration_branch=//p')"
printf '%s\n' "$OUTPUT" | grep -q '^result=prepared$' || fail "real preparation did not report success"
[ "$(git -C "$INTEGRATION_WORKTREE" rev-parse HEAD)" = "$SOURCE_COMMIT" ] || fail "prepared worktree has wrong commit"
[ -z "$(git -C "$INTEGRATION_WORKTREE" status --porcelain)" ] || fail "prepared worktree is dirty"

git -C "$REPO" worktree remove "$INTEGRATION_WORKTREE"
git -C "$REPO" branch -D "$INTEGRATION_BRANCH" >/dev/null

export INTEGRATION_REAL_GIT="$(command -v git)"
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'SH'
#!/usr/bin/env bash
case "$PREP_FAULT:$*" in
  source-reference:*'show-ref --verify --quiet refs/heads/chat/'*|\
  base-reference:*'show-ref --verify --quiet refs/remotes/'*|\
  ancestry:*'merge-base --is-ancestor'*|\
  source-commit:'rev-parse chat/'*|\
  integration-reference:*'show-ref --verify --quiet refs/heads/agentic/'*|\
  created-status:*'status --porcelain'*|created-head:*'rev-parse HEAD'*)
    echo INTEGRATION_NATIVE_CANARY >&2; exit 99 ;;
esac
if [ "$1 $2" = 'worktree add' ]; then
  if [ "$PREP_FAULT" = worktree-create ]; then
    echo INTEGRATION_NATIVE_CANARY >&2; exit 77
  fi
  # Post-creation observation fixtures do not create an actual worktree.
  exit 0
fi
if [ "$PREP_FAULT" = created-head ] && [[ "$*" == *'status --porcelain'* ]]; then exit 0; fi
exec "$INTEGRATION_REAL_GIT" "$@"
SH
chmod +x "$TMP_ROOT/bin/git"
for fault in source-reference base-reference ancestry source-commit integration-reference \
  worktree-create created-status created-head; do
  status=0
  (cd "$REPO"; TMPDIR="$TMP_ROOT" PREP_FAULT="$fault" PATH="$TMP_ROOT/bin:$PATH" \
    bash "$SOURCE_ROOT/scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh" \
    chat/2026-09-27-remote-promotion) > "$TMP_ROOT/fault.out" 2>&1 || status=$?
  expected=2
  [ "$fault" != worktree-create ] || expected=77
  [ "$status" -eq "$expected" ] || fail "$fault returned $status"
  grep -q "stage=$fault;" "$TMP_ROOT/fault.out" || fail "$fault lost stage"
  case "$fault" in
    created-*) grep -q 'worktree-created=yes' "$TMP_ROOT/fault.out" || fail "$fault lost prior effect" ;;
    worktree-create) grep -q 'effect=unknown' "$TMP_ROOT/fault.out" || fail "$fault lost uncertainty" ;;
  esac
  if grep -Eq 'INTEGRATION_NATIVE_CANARY|result=prepared|does not exist|not a fast-forward' "$TMP_ROOT/fault.out"; then
    fail "$fault leaked or misdiagnosed"
  fi
done

printf 'remote update\n' > "$REPO/remote-update.txt"
git -C "$REPO" add remote-update.txt
git -C "$REPO" commit -q -m "main update"
git -C "$REPO" push -q origin main
git -C "$REPO" fetch -q origin

if (
  cd "$REPO"
  TMPDIR="$TMP_ROOT" bash "$SOURCE_ROOT/scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh" chat/2026-09-27-remote-promotion
); then
  fail "non-fast-forward candidate was accepted"
fi

echo "remote promotion preparation smoke test passed."

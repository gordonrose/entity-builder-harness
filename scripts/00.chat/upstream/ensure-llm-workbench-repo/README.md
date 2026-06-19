<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the upstream llm-workbench repository availability helper.
domain: upstream
portability: source-only
used_by:
  - scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh
-->

# Ensure llm-workbench Repo

This capability verifies that the canonical local upstream workbench repository
exists at `/home/owner/projects/llm-workbench`.

It is used by reusable-lesson promotion work, where this repo discovers a chat
harness lesson and `llm-workbench` owns the reusable implementation.

## Files

- `script.sh` is the canonical helper.
- `scripts/shared/chat/ensure-llm-workbench-repo.sh` remains a compatibility
  wrapper for older governed-runner calls.

## Behavior

With `--dry-run`, the helper reports what it would clone without touching the
filesystem.

Without `--dry-run`, it creates the parent directory if needed and clones
`git@github.com:gordonrose/llm-workbench.git` into the canonical local path.

If the target path already exists, it must be a Git repository with the expected
origin URL.

<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.upstream.ensure-llm-workbench-repo.readme
  version: 1
  status: active
  layer: 00.chat
  domain: upstream
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the upstream llm-workbench repository availability helper.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: chat.script.upstream.ensure-llm-workbench-repo
    path: scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh
-->
# Ensure llm-workbench Repo

This capability verifies that the canonical local upstream workbench repository
exists at `/home/owner/projects/llm-workbench`.

It is used by reusable-lesson promotion work, where this repo discovers a chat
harness lesson and `llm-workbench` owns the reusable implementation.

## Files

- `script.sh` is the canonical helper.
- `scripts/shared/chat/ensure-llm-workbench-repo.sh` has been retired. Older
  governed-runner calls should be updated to this canonical path.

## Behavior

With `--dry-run`, the helper reports what it would clone without touching the
filesystem.

Without `--dry-run`, it creates the parent directory if needed and clones
`git@github.com:gordonrose/llm-workbench.git` into the canonical local path.

If the target path already exists, it must be a Git repository with the expected
origin URL.

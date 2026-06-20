<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain verification of main-refresh conflict audit entries.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/verify-conflict-audit/script.sh
  - .agentic/00.chat/workflows/chat-refresh-from-main.md
-->

# Verify Main Refresh Conflict Audit

`script.sh` verifies that known main-refresh conflict paths have matching
entries in a chat session log's `## Main Refresh Conflicts` section.

Use it before applying or promoting a rehearsed refresh that encountered
conflicts. If conflicts are still unresolved, the script can discover them from
the Git index. If conflicts have already been resolved in the preflight
worktree, pass the captured path list explicitly with `--path` or
`--paths-file`.

```bash
bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
  --session-log commitLogs/.../README.md \
  --path docs/example-conflict.md
```

<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.verify-conflict-audit.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain verification of main-refresh conflict audit entries.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.verify-conflict-audit
    path: scripts/00.chat/main-refresh/verify-conflict-audit/script.sh
  - id: chat.workflows.chat-refresh-from-main
    path: .agentic/00.chat/workflows/chat-refresh-from-main.md
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

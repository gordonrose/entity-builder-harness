<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain helper functions for chat session log paths and metadata.
domain: session-log
portability: llm-workbench-required
used_by:
  - scripts/00.chat/session-log/paths/lib.sh
  - scripts/00.chat/session-log/read-current-chat-log/script.sh
-->

# Session Log Paths

`lib.sh` provides shell helper functions for converting chat branch names and
session ids into session-log paths.

The library understands the grouped log layout:

```txt
commitLogs/<year>/<month>/<day>/<session>/README.md
```

It also reads metadata values from the `agentic-session` comment block. Scripts
use these helpers so branch-to-log lookup stays consistent across startup,
commit gates, reporting, recovery, and cleanup.

This library is read-only. It does not create, modify, stage, or commit logs.


<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.record-sub-agent-activity.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the sub-agent activity recorder for durable chat evidence.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.session-log.record-sub-agent-activity
    path: scripts/00.chat/session-log/record-sub-agent-activity/script.sh
  - id: chat.script.session-log.record-sub-agent-activity.smoke-test
    path: scripts/00.chat/session-log/record-sub-agent-activity/smoke-test.sh
-->
# Record Sub-Agent Activity

`script.sh` records delegated work in the current chat session log. Use it after
implementation, test, or git-action work is delegated to a sub-agent, and also
when the assistant runtime has no sub-agent capability and the supervising
agent performs the work directly.

The recorder updates:

- `## Sub-Agent Activity` with the full audit entry
- `## Activity Log` with a short timeline entry

Supported modes are:

- `sub-agent` for real delegated work
- `direct-fallback` when no sub-agent capability is available

This command only writes the current session log. It does not stage files,
commit, merge, push, or approve work.

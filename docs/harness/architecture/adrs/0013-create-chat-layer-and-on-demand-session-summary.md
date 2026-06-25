<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0013-create-chat-layer-and-on-demand-session-summary
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0013 Create Chat Layer And On-Demand Session Summary architecture
  decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0013 Create Chat Layer And On-Demand Session Summary

Status: accepted
Date: 2026-06-17

## Context

Chat lifecycle behavior had grown inside `.agentic/shared/` and shared scripts.
That made chat creation, session tracking, commit checkpoints, main refresh,
cleanup, and reporting harder to reason about as one lifecycle.

The harness also maintained `commitLogs/README.md` as an always-generated
aggregate summary. In practice, the file created merge noise and generated-file
conflicts while providing limited durable value. The individual session logs are
the source evidence.

## Decision

Create `.agentic/00.chat/` as the owner for chat lifecycle governance.

Stop maintaining `commitLogs/README.md` as a tracked generated artifact.
Generate aggregate chat/session summaries only on request through a chat-layer
skill and script output.

Keep existing shared workflow and script paths as compatibility locations while
chat-specific behavior migrates gradually into `.agentic/00.chat/`.

## Consequences

Main refresh no longer needs a special generated-summary conflict path for
`commitLogs/README.md`.

Routine session bookkeeping is limited to the current chat session log.

Future chat lifecycle work has a clear home for workflows, skills, and
eventual shortcuts without overloading `.agentic/shared/`.

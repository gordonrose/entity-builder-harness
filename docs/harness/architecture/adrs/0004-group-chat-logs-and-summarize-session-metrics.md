<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0004-group-chat-logs-and-summarize-session-metrics
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0004 Group Chat Logs And Summarize Session Metrics architecture
  decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0004 Group Chat Logs And Summarize Session Metrics

Status: superseded by ADR 0013
Date: 2026-06-15

## Context

Chat session logs were stored directly under `commitLogs/<session>`. That keeps
early history simple, but it does not scale well as the number of sessions
grows. Session duration was also stored only as raw seconds, which is awkward to
scan for longer chats.

The harness now records basic token estimates and chat duration, so those values
can support lightweight process review if the aggregate statistics are
generated deterministically.

## Decision

New chat session logs are grouped by date under
`commitLogs/<yyyy>/<mmm>/<dd>/<session>/README.md`, using lowercase English
month abbreviations.

Session-log scripts resolve both grouped logs and legacy flat logs so older
branches remain readable during transitions. Chat duration is stored as raw
seconds plus `dd:hh:mm:ss`, for example `694s (00:00:11:34)`.

Superseded: ADR 0013 stops maintaining `commitLogs/README.md` as a tracked
generated artifact. Aggregate chat duration and token consumption statistics
are now generated on request from the individual session logs.

## Consequences

Commit logs become easier to browse as history grows, and future scripts have a
single resolver for session-log paths.

The aggregate summary decision in this ADR was later reversed because the
tracked generated file created merge noise and was less useful than on-demand
reporting.

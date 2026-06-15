# 0004 Group Chat Logs And Summarize Session Metrics

Status: accepted
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

The harness maintains `commitLogs/README.md` with aggregate chat duration and
token consumption statistics. Metrics exclude values more than 3 standard
deviations from the mean for that metric, and the summary records how many
outliers were excluded.

## Consequences

Commit logs become easier to browse as history grows, and future scripts have a
single resolver for session-log paths. The aggregate summary gives quick process
signals without requiring agents to manually inspect every session log.

The checkpoint flow may include both the current session log and
`commitLogs/README.md` because recording a commit can update both files.

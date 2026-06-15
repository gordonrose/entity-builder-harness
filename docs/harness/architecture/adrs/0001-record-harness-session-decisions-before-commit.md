# 0001 Record Harness Session Decisions Before Commit

Status: accepted
Date: 2026-06-15

## Context

Harness changes happen through chat sessions. The current session log captures
startup metadata, but it does not consistently preserve the questions, issues,
decisions, and commit summaries that explain why a harness change happened.

Without a structured session log, a commit-time ADR check would have to infer
architecture decisions from a thin record or from transient chat context.

## Decision

Harness and shared process commits must be preceded by structured session
finalization. The session log records the initial intent, questions and
responses, issues and resolutions, decisions made, commit summaries, ADR
disposition, and basic session metrics.

Before commit, the harness checks that the current chat session has an explicit
ADR disposition:

- ADR needed, with a path under `docs/harness/architecture/adrs/`
- ADR not needed, with a short reason

## Consequences

Harness architecture rationale becomes discoverable after the chat ends.
Commit-time ADR checks can use the session log as evidence instead of relying
on memory. Small changes remain lightweight because the session can explicitly
record that no ADR is needed.

The harness now has one more pre-commit responsibility: keeping the session log
current enough to explain the work being committed.

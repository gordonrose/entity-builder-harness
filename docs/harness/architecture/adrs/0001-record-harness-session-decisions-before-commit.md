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
preparation. The session log records the initial intent, questions and
responses, issues and resolutions, decisions made, commit summaries, ADR
disposition, and basic session metrics.

Before commit, the harness checks that the current chat session has an explicit
ADR disposition:

- ADR needed, with a path under `docs/harness/architecture/adrs/`
- ADR not needed, with a short reason

After each commit, the harness records the commit in the session log and
updates rolling `latest_commit_*` metrics. The latest recorded commit is treated
as the current session endpoint. No explicit "session complete" input is
required.

When `record-chat-commit.sh` leaves the current session log dirty, that expected
bookkeeping update may be committed as its own checkpoint commit. The checkpoint
flow stages and commits only the current session log and `commitLogs/README.md`;
it refuses to run when unrelated files are staged. Agents still need explicit
user approval before creating the checkpoint commit.

## Consequences

Harness architecture rationale becomes discoverable after each recorded commit.
Commit-time ADR checks can use the session log as evidence instead of relying
on memory. Small changes remain lightweight because the session can explicitly
record that no ADR is needed.

The harness now has two commit responsibilities: prepare the session before each
commit, then record the commit afterward so multi-commit chats remain accurate.
If recording the commit dirties the session log, agents can preserve a clean
working tree with a narrow session-bookkeeping checkpoint instead of folding
that bookkeeping into unrelated follow-up work.

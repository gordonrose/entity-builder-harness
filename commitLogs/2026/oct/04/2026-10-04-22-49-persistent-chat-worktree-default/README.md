# Chat Session: 2026-10-04-22-49 persistent-chat-worktree-default

<!-- agentic-session
id: 2026-10-04-22-49-how-do-i-get-new-chat-worktrees-to-stop-defaulting-to-tmp-an
task: how do i get new chat worktrees to stop defaulting to /tmp and create more durable worktrees that won’t get deleted if wsl crashes or there are other events?
branch: chat/2026-10-04-22-49-how-do-i-get-new-chat-worktrees-to-stop-defaulting-to-tmp-an
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-04-22-49-how-do-i-get-new-chat-worktrees-to-stop-defaulting-to-tmp-an-3297659476
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-10-04T21:49:30Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-10-04T23:31:22Z
latest_commit_sha: 517c2d2b
chat_duration: 6112s (00:01:41:52)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

how do i get new chat worktrees to stop defaulting to /tmp and create more durable worktrees that won’t get deleted if wsl crashes or there are other events?

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made



- Decision: Default chat worktrees use persistent per-repository storage
  Rationale: New paths resolve under HOME/projects/.chat-worktrees; an explicit environment or env.local root overrides it.

## Context Hygiene



- Summary: Persistent resolver accepts one Git-registered legacy worktree before choosing a new path.
  Durable evidence: scripts/00.chat/worktree/paths/lib.sh and its smoke test cover path selection, configuration, legacy reuse and diagnostics.

## Activity Log

### 2026-10-04T21:49:30Z - Session started

Initial intent: how do i get new chat worktrees to stop defaulting to /tmp and create more durable worktrees that won’t get deleted if wsl crashes or there are other events?


### 2026-10-04T23:21:16Z - Decision

Decision: Default chat worktrees use persistent per-repository storage

Rationale: New paths resolve under HOME/projects/.chat-worktrees; an explicit environment or env.local root overrides it.


### 2026-10-04T23:21:16Z - Sub-agent activity recorded

Agent: codex

Status: completed

Delegation mode: direct-fallback

Fallback used: yes

Scope: persistent chat worktree default


### 2026-10-04T23:21:16Z - Context hygiene

Summary: Persistent resolver accepts one Git-registered legacy worktree before choosing a new path.

Durable evidence: scripts/00.chat/worktree/paths/lib.sh and its smoke test cover path selection, configuration, legacy reuse and diagnostics.


### 2026-10-04T23:21:16Z - ADR disposition

ADR needed: no

Reason: This is a focused correction to an existing worktree-location policy; ADR 0009 is updated to reflect the new default.


### 2026-10-04T23:27:04Z - Commit summary

Commit: fix(chat): default new worktrees to persistent storage

Summary: Adds persistent per-repository defaults, env.local configuration, registered legacy-worktree reuse, and focused regression coverage.

ADR impact: covered by session ADR disposition


### 2026-10-04T23:31:22Z - Commit recorded

Commit: `517c2d2b`

Message: fix(chat): persist new worktrees outside tmp

Summary: Persistent per-repository defaults now apply to new chats while registered legacy worktrees remain valid.

ADR impact: Updated ADR 0009 default-path wording; no new ADR required.

## Sub-Agent Activity



### 2026-10-04T23:21:16Z - codex

Status: completed
Delegation mode: direct-fallback
Fallback used: yes
Scope: persistent chat worktree default
Files touched: worktree path helpers, startup, ensure, write-location, compatibility callers, docs, and smoke tests
Checks run: focused smoke tests, shell syntax, diff checks; full portability suite in progress
Git actions: none yet
Blockers: none
Next step: complete portability checks, commit, refresh, promote, and push
Summary: Implemented persistent defaults, consistent configuration resolution, legacy registered-worktree reuse, and regression coverage directly because delegated execution is unavailable in this runtime.

## Commits



- Commit: fix(chat): default new worktrees to persistent storage
  Summary: Adds persistent per-repository defaults, env.local configuration, registered legacy-worktree reuse, and focused regression coverage.
  ADR impact: covered by session ADR disposition


- Commit: `517c2d2b`
  Time UTC: 2026-10-04T23:31:22Z
  Message: fix(chat): persist new worktrees outside tmp
  Summary: Persistent per-repository defaults now apply to new chats while registered legacy worktrees remain valid.
  ADR impact: Updated ADR 0009 default-path wording; no new ADR required.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This is a focused correction to an existing worktree-location policy; ADR 0009 is updated to reflect the new default.

## Session Metrics

Raised at UTC: 2026-10-04T21:49:30Z
Latest commit at UTC: 2026-10-04T23:31:22Z
Latest commit SHA: 517c2d2b
Chat duration: 6112s (00:01:41:52)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

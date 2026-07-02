# Chat Session: 2026-07-01-14-29 i-d-like-to-update-my-00-chat-harness-so-it-doesn-t-classify

<!-- agentic-session
id: 2026-07-01-14-29-i-d-like-to-update-my-00-chat-harness-so-it-doesn-t-classify
task: i'd like to update my 00.chat harness so it doesn't classify by mode or layer by default. I'd like that behaviour to live separately inside the RAG rulebook. the chat should be purely about opening session, creating and maintaining temporary branches and worktrees, creating and maintaining commit logs with metrics, and git behaviour. the behaviour that classifies the chat should be abstracted to the RAG. The chat itself should connect to the RAG to pull that categorization for future messages to use as context. how do we go about that?
branch: chat/2026-07-01-14-29-i-d-like-to-update-my-00-chat-harness-so-it-doesn-t-classify
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-01-14-29-i-d-like-to-update-my-00-chat-harness-so-it-doesn-t-classify-2233228654
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-01T13:29:33Z
codex_session_log_path:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

i'd like to update my 00.chat harness so it doesn't classify by mode or layer by default. I'd like that behaviour to live separately inside the RAG rulebook. the chat should be purely about opening session, creating and maintaining temporary branches and worktrees, creating and maintaining commit logs with metrics, and git behaviour. the behaviour that classifies the chat should be abstracted to the RAG. The chat itself should connect to the RAG to pull that categorization for future messages to use as context. how do we go about that?

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

- Whole-chat layer, mode, and workflow classification should no longer be
  durable chat startup metadata.
- Chat startup should own only chat lifecycle state: branch, worktree, session
  log, chat lifecycle workflow, latest context packet references, metrics, and
  git behavior.
- Prompt-level layer, mode, workflow, corpus, and context selection should be
  resolved per prompt by the RAG/rulebook runtime.
- Session route metadata from older logs should remain compatibility
  provenance, not trusted prompt-route authority by default.
- HTTP callers should not be able to mark session routing trusted; governed CLI
  trust requires lifecycle proof fields.

## Activity Log

### 2026-07-01T13:29:33Z - Session started

Initial intent: i'd like to update my 00.chat harness so it doesn't classify by mode or layer by default. I'd like that behaviour to live separately inside the RAG rulebook. the chat should be purely about opening session, creating and maintaining temporary branches and worktrees, creating and maintaining commit logs with metrics, and git behaviour. the behaviour that classifies the chat should be abstracted to the RAG. The chat itself should connect to the RAG to pull that categorization for future messages to use as context. how do we go about that?

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This change updates existing governed chat/RAG workflows, runtime
contracts, fixtures, and commit gates without introducing a new architectural
decision record requirement.

## Session Metrics

Raised at UTC: 2026-07-01T13:29:33Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.

# Chat Session: 2026-07-07-00-13 plan-rag-hardening-gaps-aws-service-selector-fixtures-corpus

<!-- agentic-session
id: 2026-07-07-00-13-plan-rag-hardening-gaps-aws-service-selector-fixtures-corpus
task: plan RAG hardening gaps AWS service selector fixtures corpus gaps subagent delegation runtime identity walkthrough
branch: chat/2026-07-07-00-13-plan-rag-hardening-gaps-aws-service-selector-fixtures-corpus
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-07-00-13-plan-rag-hardening-gaps-aws-service-selector-fixtures-corpus-1727961372
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-06T23:13:23Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-07-07T23:33:31Z
latest_commit_sha: 1ab8d95
chat_duration: 87608s (01:00:20:08)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

plan RAG hardening gaps AWS service selector fixtures corpus gaps subagent delegation runtime identity walkthrough

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised



- Raised: Initial hosted-provider gap was scoped to 00.chat
  Resolution: Replaced the 00.chat gap with a 02.rag-rulebook corpus gap, source material, structured rule, projection manifest entry, selector fixture, and query-context runtime boundary.

## Decisions Made



- Decision: 02.rag-rulebook owns hosted context provider selection
  Rationale: Hosted/local provider selection, bearer auth loading, redaction, fail-closed behavior, and local fallback policy belong behind the RAG rulebook query-context interface; chat/workbench consumes context packets only.

## Activity Log

### 2026-07-06T23:13:23Z - Session started

Initial intent: plan RAG hardening gaps AWS service selector fixtures corpus gaps subagent delegation runtime identity walkthrough


### 2026-07-07T01:49:44Z - Decision

Decision: 02.rag-rulebook owns hosted context provider selection

Rationale: Hosted/local provider selection, bearer auth loading, redaction, fail-closed behavior, and local fallback policy belong behind the RAG rulebook query-context interface; chat/workbench consumes context packets only.


### 2026-07-07T01:49:44Z - ADR disposition

ADR needed: no

Reason: The change applies an existing RAG rulebook layering principle by adding source material, rules, scripts, projection, and fixtures; no new repo-wide architecture decision is introduced.


### 2026-07-07T01:49:59Z - Decision

Decision: 02.rag-rulebook owns hosted context provider selection

Rationale: Hosted/local provider selection, bearer auth loading, redaction, fail-closed behavior, and local fallback policy belong behind the RAG rulebook query-context interface; chat/workbench consumes context packets only.


### 2026-07-07T01:54:15Z - Commit recorded

Commit: `407a7c2`

Message: Add RAG-owned hosted context provider boundary

Summary: Adds the RAG-owned query-context provider boundary, hosted auth/redaction/fallback contract, selector proof, corpus gap, projection records, and commit-gate smoke coverage.

ADR impact: No ADR needed; existing RAG rulebook layering principle applied.


### 2026-07-07T23:33:31Z - Commit recorded

Commit: `1ab8d95`

Message: Retire focused-path RAG request context

Summary: Retires focused-path request context from the RAG selector and provider API, replaces it with exact paths in request text, adds a retirement record, updates fixtures/docs/schemas, and keeps selector/runtime gates passing.

ADR impact: No ADR needed; this removes an ungoverned request-context hint and preserves the existing RAG rulebook ownership model.

## Commits



- Commit: `407a7c2`
  Time UTC: 2026-07-07T01:54:15Z
  Message: Add RAG-owned hosted context provider boundary
  Summary: Adds the RAG-owned query-context provider boundary, hosted auth/redaction/fallback contract, selector proof, corpus gap, projection records, and commit-gate smoke coverage.
  ADR impact: No ADR needed; existing RAG rulebook layering principle applied.


- Commit: `1ab8d95`
  Time UTC: 2026-07-07T23:33:31Z
  Message: Retire focused-path RAG request context
  Summary: Retires focused-path request context from the RAG selector and provider API, replaces it with exact paths in request text, adds a retirement record, updates fixtures/docs/schemas, and keeps selector/runtime gates passing.
  ADR impact: No ADR needed; this removes an ungoverned request-context hint and preserves the existing RAG rulebook ownership model.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The change applies an existing RAG rulebook layering principle by adding source material, rules, scripts, projection, and fixtures; no new repo-wide architecture decision is introduced.

## Session Metrics

Raised at UTC: 2026-07-06T23:13:23Z
Latest commit at UTC: 2026-07-07T23:33:31Z
Latest commit SHA: 1ab8d95
Chat duration: 87608s (01:00:20:08)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

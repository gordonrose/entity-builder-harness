# Chat Session: 2026-07-03 07-15 implement packages core slice 1

<!-- agentic-session
id: 2026-07-03-07-15-can-you-explain-the-architecture-of-my-rag-api-as-it-current
task: Explain the RAG API architecture, then implement packages/core slice 1 and RAG knowledge coverage gates
branch: chat/2026-07-03-07-15-can-you-explain-the-architecture-of-my-rag-api-as-it-current
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-03-07-15-can-you-explain-the-architecture-of-my-rag-api-as-it-current-3800178136
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-03T06:15:00Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-07-04T21:05:22Z
latest_commit_sha: ceb01ff
chat_duration: 139822s (01:14:50:22)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

Explain the deployed RAG API architecture, clarify persistence and runtime
behavior, then begin implementation slice 1 for `packages/core` while keeping
RAG/rulebook context current as platform and core layers are added.

## Session Log

- Session was recovered after the original `/tmp` chat worktree disappeared.
- The restored branch was recreated from current local `main`.
- Lost uncommitted work was reapplied from the recorded conversation summary.

## Questions Asked

- Asked: Should provider adapters for AWS live under infra rather than platform?
  Response: Runtime provider adapter code belongs in platform; deploy resources and cloud topology belong in infra.
- Asked: Should source materials also be updated and versioned when RAG knowledge changes?
  Response: Yes. Source material should be versioned and projected into rules, derivation reports, selector fixtures, or corpus gaps.

## Issues Raised

- Raised: The original chat-owned `/tmp` worktree was missing and the branch had no task commits.
  Resolution: Recreated the chat worktree from current `main` and reapplied the slice.
- Raised: `00.chat` should remain standalone and must not know about `01.harness` or `02.rag-rulebook`.
  Resolution: Moved repo-specific commit checks behind `scripts/repo/commit-gates/script.sh`.

## Decisions Made

- Decision: Start `packages/core` with contract-only capability modules.
  Rationale: The first slice establishes stable shared contracts without provider implementations, app workflows, or infra resources.
- Decision: Keep RAG/rulebook knowledge coverage in the RAG layer and call it through a neutral repo hook.
  Rationale: `00.chat` stays portable while this repo can still require source/rule/selector coverage for knowledge-bearing code changes.
- Decision: Add versioned source material and projection evidence for the initial core contract surface.
  Rationale: Future RAG prompts need current guidance on how to use `packages/core` and where implementation code belongs.

## Activity Log

### 2026-07-04T00:00:00Z - Recovery and implementation

Reapplied the packages/core contract scaffold, repo commit hook, RAG knowledge
disposition recorder, code-change knowledge coverage gate, source projection,
derivation report, selector fixture, and ADR 0023.


### 2026-07-04T21:05:22Z - Commit recorded

Commit: `ceb01ff`

Message: Add packages core contract slice

Summary: Added packages/core contract scaffold plus RAG knowledge coverage gates, source projection evidence, selector fixture, and ADR 0023.

ADR impact: ADR 0023 records the RAG knowledge-disposition policy.

## Commits



- Commit: `ceb01ff`
  Time UTC: 2026-07-04T21:05:22Z
  Message: Add packages core contract slice
  Summary: Added packages/core contract scaffold plus RAG knowledge coverage gates, source projection evidence, selector fixture, and ADR 0023.
  ADR impact: ADR 0023 records the RAG knowledge-disposition policy.

## Main Refresh Conflicts

- None recorded yet.

## RAG Knowledge Disposition

Status: covered
Reason: The packages/core contract slice is covered by source material, rule provenance, source projection, derivation report, selector fixture, and ADR 0023.
Evidence:
- docs/harness/architecture/source-material/packages-core-contract-surface-v1.md
- docs/harness/architecture/rules/layers/packages-core.yml
- .agentic/02.rag-rulebook/source-projections/v1.yml
- .agentic/02.rag-rulebook/derivation-reports/03.product.core/2026-07-04-packages-core-contract-surface-v1.yml
- .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-contract-surface.yml
- docs/harness/architecture/adrs/0023-require-rag-knowledge-disposition-for-code-changes.md
- scripts/repo/commit-gates/script.sh
- scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
- scripts/02.rag-rulebook/record-knowledge-disposition/script.sh
Corpus gaps:
- None.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0023-require-rag-knowledge-disposition-for-code-changes.md
Reason: The task adds a durable commit-boundary policy requiring RAG knowledge disposition for knowledge-bearing code changes while preserving `00.chat` portability.

## Session Metrics

Raised at UTC: 2026-07-03T06:15:00Z
Latest commit at UTC: 2026-07-04T21:05:22Z
Latest commit SHA: ceb01ff
Chat duration: 139822s (01:14:50:22)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- The final Git commit and merge still require `.git` write access.

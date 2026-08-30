# Chat Session: 2026-08-30-14-17 repo-terminology-source-of-truth

<!-- agentic-session
id: 2026-08-30-14-17-do-we-have-a-standard-glossary-for-terminology-used-in-this-
task: do we have a standard glossary for terminology used in this repo anywhere?
branch: chat/2026-08-30-14-17-do-we-have-a-standard-glossary-for-terminology-used-in-this-
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-30-14-17-do-we-have-a-standard-glossary-for-terminology-used-in-this--1970345759
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-08-30T13:17:28Z
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
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

do we have a standard glossary for terminology used in this repo anywhere?

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- The repo had scattered term explanations and controlled vocabularies, but no
  single canonical terminology source.

## Decisions Made

- Add `.agentic/01.harness/standards/repo-terminology.md` as the canonical
  source of truth for repo-wide terminology.
- Keep local artifacts as usage guidance only; repo-wide definitions belong in
  the terminology standard.

## Context Hygiene

- Durable carry-forward: repo-wide term definitions now belong in
  `.agentic/01.harness/standards/repo-terminology.md`; older explanatory docs
  may keep usage prose, but future material edits should replace duplicate
  definitions with references to the terminology standard.

## Activity Log

### 2026-08-30T13:17:28Z - Session started

Initial intent: do we have a standard glossary for terminology used in this repo anywhere?

### 2026-08-30T13:50:28Z - Repo terminology source of truth added

Added a harness terminology standard, linked it from the harness README and the
artifact-placement standard, and regenerated the generated artifact recognition
source so the new standard is discoverable by artifact ID and path.

Validation:

- `generate-recognition-sources --check --source artifacts`
- `validate-recognition-sources --source .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`
- `check-headers --paths` for the changed harness/RAG files
- `git diff --check`

## Sub-Agent Activity

- None recorded yet.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: A terminology standard is a narrow harness governance artifact and does
not introduce a durable architecture tradeoff requiring an ADR.

## Session Metrics

Raised at UTC: 2026-08-30T13:17:28Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.

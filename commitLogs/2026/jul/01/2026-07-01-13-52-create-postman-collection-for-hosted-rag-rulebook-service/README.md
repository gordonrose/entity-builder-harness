# Chat Session: 2026-07-01-13-52 create-postman-collection-for-hosted-rag-rulebook-service

<!-- agentic-session
id: 2026-07-01-13-52-create-postman-collection-for-hosted-rag-rulebook-service
task: Create Postman collection for hosted RAG rulebook service
branch: chat/2026-07-01-13-52-create-postman-collection-for-hosted-rag-rulebook-service
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-01-13-52-create-postman-collection-for-hosted-rag-rulebook-service-4225344386
layer: rag-rulebook
mode: implementation
workflow: .agentic/02.rag-rulebook/workflows/default.md
status: complete
raised_at_utc: 2026-07-01T12:52:53Z
codex_session_log_path:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

Create Postman collection for hosted RAG rulebook service

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

- Add a Postman v2.1 collection under `docs/02.rag-rulebook/postman/`
  for the hosted RAG/rulebook service.
- Keep the collection secret-free by using Postman variables for `baseUrl`,
  `ragToken`, `requestText`, and `maxChunks`.
- Include health, version, compact query, full query, and unauthorized-query
  guard requests.
- Document AWS Secrets Manager lookup for the staging bearer token without
  storing the token in the repo.

## Activity Log

### 2026-07-01T12:52:53Z - Session started

Initial intent: Create Postman collection for hosted RAG rulebook service

### 2026-07-01T13:05:00Z - Postman collection added

Added `docs/02.rag-rulebook/postman/rag-rulebook-service.postman_collection.json`
and companion `README.md`.

Validated the collection with `python3 -m json.tool` and corrected the
unauthorized response assertion to match the service error envelope.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: small API testing/documentation artifact for an already-approved hosted RAG/rulebook service surface.

## Session Metrics

Raised at UTC: 2026-07-01T12:52:53Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- Closeout requested after the hosted service was verified through Postman.

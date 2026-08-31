# Chat Session: 2026-08-30-23-53 prototype-corpus-migration-plan

<!-- agentic-session
id: 2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00
task: is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?
branch: chat/2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00-3903744130
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-08-30T22:53:17Z
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

is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Built the prototype corpus domain-split migration plan.
- Added a harness document-artifact placement standard for future ADRs, guides,
  source material, plans, rules, rule packs, and corpus docs.
- Wired the placement standard into the harness change workflow, harness
  README, artifact standard, terminology hints, and corpus migration plan.
- Refreshed generated artifact recognition sources for the new plan artifact.
- Validated metadata headers, recognition-source freshness, source projections,
  source-material coverage, rulebook index smoke, chunk generator smoke, and
  diff whitespace.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Treat `docs/harness/architecture` as the prototype corpus that should split
  by numbered owner corpus through governed artifact path migration.
- Place the durable migration plan under
  `.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
  because the work is corpus packaging and source-projection coordination.
- Use pointer compatibility for old prototype paths during execution slices;
  do not move corpus files in the planning slice.
- Keep RAG/rulebook as owner of retrieval machinery and its self-corpus, not as
  the destination for every product, deploy, or harness rule.
- Route new document artifacts through
  `.agentic/01.harness/standards/document-artifact-placement.md` so future
  work uses owner-aligned layer and corpus paths instead of extending
  `docs/harness/architecture/**`.
- Treat missing numbered docs roots as governed setup work; create the root
  README, metadata allowlist support, and corpus wiring before placing ordinary
  content there.

## Context Hygiene

- Work performed in the chat-owned worktree:
  `/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00-3903744130`.
- Root checkout had an unrelated `package-lock.json` modification; it was not
  touched in this slice.
- `docs/harness/architecture/**` files were not moved or edited.
- Generated recognition sources were updated because new indexed artifacts were
  added.

## Activity Log

### 2026-08-30T22:53:17Z - Session started

Initial intent: is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?

### 2026-08-30T23:01:35Z - Migration plan built

Created `.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
as the durable, governed plan for splitting the prototype
`docs/harness/architecture` corpus into numbered domain corpus homes. Updated
the RAG/rulebook README, repo plan, existing prototype migration map, and
generated artifact recognition source to reference the new plan.

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `git diff --check`

### 2026-08-30T23:12:40Z - Forward document placement governed

Created
`.agentic/01.harness/standards/document-artifact-placement.md` as the durable
harness rule for placing new document artifacts by owner layer and corpus.
Updated `.agentic/01.harness/workflows/change-harness.md`,
`.agentic/01.harness/README.md`,
`.agentic/01.harness/standards/agentic-artifact-standards.md`,
`.agentic/01.harness/standards/repo-terminology.md`, and
`.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
to make the standard discoverable during future harness and corpus work.

Regenerated recognition sources with:

- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
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
Reason: This slice adds a migration-plan artifact and a harness placement
standard, but does not move durable documentation roots. Actual execution of
the corpus split should add or update an ADR before retiring old prototype
paths because it changes durable documentation layout.

## Session Metrics

Raised at UTC: 2026-08-30T22:53:17Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.

# Chat Session: 2026-07-10-11-50 restore-lost-rag-example-context-deprioritization-work-after

<!-- agentic-session
id: 2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after
task: restore lost RAG example context deprioritization work after crash
branch: chat/2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-10-11-50-restore-lost-rag-example-context-deprioritization-work-after-531603960
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-10T10:50:16Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-07-10T20:34:13Z
latest_commit_sha: dc87092
chat_duration: 35037s (00:09:43:57)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

restore lost RAG example context deprioritization work after crash

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- Previous work was interrupted by a local machine crash and needed to be
  restored and revalidated from the chat worktree.
- RAG retrieval was overweighting paths inside illustrative examples, such as
  `e.g.` or `for example`, as if they were primary request targets.
- Header metadata was useful for identity, but deterministic retrieval-profile
  derivation needed broader artifact coverage and stronger generated signals.

## Decisions Made

- Treat paths and artifact IDs inside illustrative phrases such as `e.g.`,
  `i.e.`, and `for example` as lower-priority example context rather than
  target-specific request anchors.
- Keep authored `agentic-artifact/v2` headers as identity and governance
  metadata. Generate RAG-specific retrieval profiles from the artifact index,
  path conventions, kind, purpose, effects, and stable relationships instead of
  manually training every header.
- Widen the artifact metadata checker and indexer so v2-headered artifacts in
  deploy, AWS, education, and script YAML fixture areas enter the strict index.
- Add a read-only retrieval-profile coverage reporter before any broad header
  migration, so the repo can distinguish header weakness from generator-rule
  weakness.
- Use LLM review only as calibration evidence for deterministic rules. Do not
  add LLM judgment to the normal gate until a separate governed review workflow,
  prompt, sample policy, and rubric exist.
- Treat the final 26 partial coverage records as stable artifact kind contracts
  that can be derived deterministically without authored header edits.
- Coverage no longer indicates a need for an `agentic-artifact/v2` schema
  extension or governed header backfill; future schema work should come from
  retrieval evaluation misses, not from this coverage report.
- ADR needed: no. The work extends existing RAG/rulebook retrieval and artifact
  metadata machinery without changing the accepted architecture boundary.

## Context Hygiene

- Migration context is tracked in
  `.agentic/02.rag-rulebook/plans/artifact-metadata-retrieval-profile-migration.md`.
- The LLM calibration audit is recorded in
  `.agentic/02.rag-rulebook/evaluations/retrieval-profile-coverage/2026-07-10-llm-audit.md`.
- Generated recognition sources were refreshed after adding metadata-bearing
  artifacts.
- Current retrieval-profile coverage is `693` artifacts: `692` strong, `0`
  partial, `0` weak, and `1` excluded.
- Remaining profile-coverage work should move to retrieval-evaluation fixtures
  by question family rather than broad header/schema repair.

## Activity Log

### 2026-07-10T10:50:16Z - Session started

Initial intent: restore lost RAG example context deprioritization work after crash

### 2026-07-10 - Restored and extended RAG retrieval-profile migration

- Restored illustrative example-path deprioritization behavior and fixtures.
- Added generated retrieval-profile support to the rulebook index and chunk
  generation path.
- Added generated selector fixtures for harness indexing and RAG index
  selection questions.
- Aligned artifact metadata checker/indexer scope with v2-headered artifacts.
- Added a migration plan for artifact metadata retrieval profiles.
- Added a read-only retrieval-profile coverage report command.
- Ran an LLM calibration audit and converted stable findings into
  deterministic reporter rules.
- Verified metadata, generated recognition sources, local runtime build, local
  context query, selector fixtures, coverage reporter smoke test, and diff
  hygiene before commit.


### 2026-07-10T14:58:23Z - Commit recorded

Commit: `d73ae37`

Message: feat(rag): generate artifact retrieval profiles

Summary: Restored illustrative example-path deprioritization, added generated artifact retrieval profiles, widened metadata indexing scope, added a retrieval-profile coverage reporter, recorded an LLM calibration audit, and refreshed generated recognition sources.

ADR impact: No ADR needed; extends existing RAG/rulebook retrieval and artifact metadata machinery.


### 2026-07-10T15:04:19Z - Commit recorded

Commit: `7254a98`

Message: feat(rag): enrich retrieval profile kind derivation

Summary: Added deterministic retrieval-profile derivation for readme-like artifacts, ADRs, agent contracts, recognition sources, and source material, reducing partial coverage from 112 to 26 without authored header edits.

ADR impact: No ADR needed; this narrows the existing generated-profile migration with deterministic kind rules.

### 2026-07-10 - Completed remaining retrieval-profile partials

- Added deterministic kind contracts for docs, examples, checklists, corpus
  gaps, plans, prompts, review records, rulesets, state records, skill/index
  records, and related governance records.
- Reduced retrieval-profile coverage from `26` partial artifacts to `0`
  partial artifacts without authored header edits.
- Left the deprecated artifact excluded.
- Updated the migration plan to make question-family retrieval evaluations the
  next slice.


### 2026-07-10T15:27:22Z - Commit recorded

Commit: `4aa0176`

Message: feat(rag): complete retrieval profile coverage derivation

Summary: Added final deterministic kind-contract derivation for the remaining 26 partial retrieval-profile records and updated the coverage reporter smoke test, leaving 692 strong artifacts, 0 partial, 0 weak, and 1 excluded.

ADR impact: No ADR needed; this completes the existing generated retrieval-profile coverage migration without header or schema changes.


### 2026-07-10T17:01:24Z - Commit recorded

Commit: `99f0dd3`

Message: feat(rag): strengthen retrieval evidence bundles

Summary: Added the printable RAG retrieval source-of-truth material with prompt payload, runtime-cache, chunk, context-packet, assembly, and ranking examples; added related corpus gap/projection wiring, selector question-category fixtures, evidence-bundle coverage, generated recognition updates, and packet gap validation support.

ADR impact: No ADR needed; this strengthens existing RAG/rulebook retrieval, source-material, selector, and context-packet machinery without changing the architecture boundary.


### 2026-07-10T17:19:27Z - Commit recorded

Commit: `f89ef56`

Message: feat(rag): expand question evidence routing

Summary: Expanded curated question categories, evidence bundles, and supporting rulebook index entries for chat metrics, worktree recovery, local-main promotion, generated-recognition repair, hosted RAG auth, and packages/core contract questions; made chunk generation tolerate malformed YAML metadata while indexing evidence.

ADR impact: No ADR needed; this extends existing deterministic RAG recognition, evidence-bundle, indexing, and chunk-generation behavior without changing the architecture boundary.


### 2026-07-10T17:30:24Z - Commit recorded

Commit: `c57d011`

Message: test(rag): add chat operations retrieval fixtures

Summary: Added selector fixtures for chat metrics, worktree recovery, sub-agent activity, local-main promotion, hosted auth, prompt/session conflict, generated recognition repair, and packages/core contract retrieval; tightened container governance fixture source-path proof.

ADR impact: No ADR impact; regression coverage for cycle-2 RAG retrieval hardening.


### 2026-07-10T18:18:44Z - Commit recorded

Commit: `bd59a57`

Message: feat(rag): index governed process evidence

Summary: Expanded RAG governed-process indexing, curated question categories, evidence bundles, and ten selector fixtures after Cycle 3 A/B misses. Validation: realistic A/B repair set 10/10 strong, selector fixtures 62/62, RAG commit gates passed.

ADR impact: covered by session ADR disposition


### 2026-07-10T19:07:59Z - Commit recorded

Commit: `a4e55ed`

Message: feat(rag): route source family evidence

Summary: Repaired Cycle 4 A/B source-family gaps by indexing GitHub workflow/deploy infra/RAG service/education ADR/package source families, adding reusable categories and evidence bundles, and adding nine selector fixtures. Validation: Cycle 4 realistic A/B prompts 10/10 strong, selector fixtures 71/71, RAG commit gates passed.

ADR impact: covered by session ADR disposition


### 2026-07-10T20:34:13Z - Commit recorded

Commit: `dc87092`

Message: feat(rag): add operational diagnostic retrieval fixtures

Summary: Added operational-diagnostic RAG question categories, evidence bundles, generated artifact recognition, process-source indexing coverage, ten selector fixtures, and the Cycle 5 migration-plan note after the expanded selector regression reached 81/81 passing fixtures.

ADR impact: No ADR needed; extends existing deterministic RAG recognition, evidence-bundle, fixture, and process-source indexing behavior without changing the architecture boundary.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `d73ae37`
  Time UTC: 2026-07-10T14:58:23Z
  Message: feat(rag): generate artifact retrieval profiles
  Summary: Restored illustrative example-path deprioritization, added generated artifact retrieval profiles, widened metadata indexing scope, added a retrieval-profile coverage reporter, recorded an LLM calibration audit, and refreshed generated recognition sources.
  ADR impact: No ADR needed; extends existing RAG/rulebook retrieval and artifact metadata machinery.


- Commit: `7254a98`
  Time UTC: 2026-07-10T15:04:19Z
  Message: feat(rag): enrich retrieval profile kind derivation
  Summary: Added deterministic retrieval-profile derivation for readme-like artifacts, ADRs, agent contracts, recognition sources, and source material, reducing partial coverage from 112 to 26 without authored header edits.
  ADR impact: No ADR needed; this narrows the existing generated-profile migration with deterministic kind rules.


- Commit: `4aa0176`
  Time UTC: 2026-07-10T15:27:22Z
  Message: feat(rag): complete retrieval profile coverage derivation
  Summary: Added final deterministic kind-contract derivation for the remaining 26 partial retrieval-profile records and updated the coverage reporter smoke test, leaving 692 strong artifacts, 0 partial, 0 weak, and 1 excluded.
  ADR impact: No ADR needed; this completes the existing generated retrieval-profile coverage migration without header or schema changes.


- Commit: `99f0dd3`
  Time UTC: 2026-07-10T17:01:24Z
  Message: feat(rag): strengthen retrieval evidence bundles
  Summary: Added the printable RAG retrieval source-of-truth material with prompt payload, runtime-cache, chunk, context-packet, assembly, and ranking examples; added related corpus gap/projection wiring, selector question-category fixtures, evidence-bundle coverage, generated recognition updates, and packet gap validation support.
  ADR impact: No ADR needed; this strengthens existing RAG/rulebook retrieval, source-material, selector, and context-packet machinery without changing the architecture boundary.


- Commit: `f89ef56`
  Time UTC: 2026-07-10T17:19:27Z
  Message: feat(rag): expand question evidence routing
  Summary: Expanded curated question categories, evidence bundles, and supporting rulebook index entries for chat metrics, worktree recovery, local-main promotion, generated-recognition repair, hosted RAG auth, and packages/core contract questions; made chunk generation tolerate malformed YAML metadata while indexing evidence.
  ADR impact: No ADR needed; this extends existing deterministic RAG recognition, evidence-bundle, indexing, and chunk-generation behavior without changing the architecture boundary.


- Commit: `c57d011`
  Time UTC: 2026-07-10T17:30:24Z
  Message: test(rag): add chat operations retrieval fixtures
  Summary: Added selector fixtures for chat metrics, worktree recovery, sub-agent activity, local-main promotion, hosted auth, prompt/session conflict, generated recognition repair, and packages/core contract retrieval; tightened container governance fixture source-path proof.
  ADR impact: No ADR impact; regression coverage for cycle-2 RAG retrieval hardening.


- Commit: `bd59a57`
  Time UTC: 2026-07-10T18:18:44Z
  Message: feat(rag): index governed process evidence
  Summary: Expanded RAG governed-process indexing, curated question categories, evidence bundles, and ten selector fixtures after Cycle 3 A/B misses. Validation: realistic A/B repair set 10/10 strong, selector fixtures 62/62, RAG commit gates passed.
  ADR impact: covered by session ADR disposition


- Commit: `a4e55ed`
  Time UTC: 2026-07-10T19:07:59Z
  Message: feat(rag): route source family evidence
  Summary: Repaired Cycle 4 A/B source-family gaps by indexing GitHub workflow/deploy infra/RAG service/education ADR/package source families, adding reusable categories and evidence bundles, and adding nine selector fixtures. Validation: Cycle 4 realistic A/B prompts 10/10 strong, selector fixtures 71/71, RAG commit gates passed.
  ADR impact: covered by session ADR disposition


- Commit: `dc87092`
  Time UTC: 2026-07-10T20:34:13Z
  Message: feat(rag): add operational diagnostic retrieval fixtures
  Summary: Added operational-diagnostic RAG question categories, evidence bundles, generated artifact recognition, process-source indexing coverage, ten selector fixtures, and the Cycle 5 migration-plan note after the expanded selector regression reached 81/81 passing fixtures.
  ADR impact: No ADR needed; extends existing deterministic RAG recognition, evidence-bundle, fixture, and process-source indexing behavior without changing the architecture boundary.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The slice extends existing artifact metadata, RAG rulebook indexing,
retrieval selector, generated recognition source, and evaluation machinery. It
does not introduce a new architecture boundary or reverse an accepted decision.

## Session Metrics

Raised at UTC: 2026-07-10T10:50:16Z
Latest commit at UTC: 2026-07-10T20:34:13Z
Latest commit SHA: dc87092
Chat duration: 35037s (00:09:43:57)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

# Chat Session: 2026-08-31-01-11 product-harness-foundation-plan

<!-- agentic-session
id: 2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm
task: Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.
branch: chat/2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm-1609907486
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-08-31T00:11:19Z
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

Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- Can the architecture tutoring session be recorded as a printable Markdown
  handbook and updated as learning continues?
- Should a future, bound platform capability investigate and remediate
  dead-lettered messages while escalating destructive or uncertain actions to
  humans?

## Issues Raised

- This chat branch predates the owner-aligned move of the platform runtime
  plan to `.agentic/03.product/plans/implementation/`. A governed checkpoint
  and refresh from local `main` are required before changing that canonical
  plan.

## Decisions Made

- Create a canonical, printable architecture learning handbook in
  `docs/education/teaching-notes/` and link it from this session log.
- Update the handbook after each completed learning chunk; use this session log
  as the audit trail for the learning activity.
- Treat future DLQ self-healing as a bounded, policy-controlled remediation
  capability: diagnosis and recommendations may be automated, while replay,
  purge, or other consequential actions require explicit allowlists, evidence,
  and human escalation where appropriate.
- Decision: Record RAG knowledge disposition: covered.
  Rationale: The security-module organisation and platform-contract naming
  policy are accompanied by rule-pack, source-material, source-review,
  derivation, projection, retrieval-fixture, and recognition-source evidence.

## Context Hygiene

- The handbook distinguishes current repository evidence from intended
  architecture so incomplete future work is not presented as implemented.
- The canonical runtime plan is on current local `main`; the pending chat
  changes have passed core and rulebook verification before their checkpoint.

## Activity Log

### 2026-08-31T00:11:19Z - Session started

Initial intent: Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.

### 2026-09-01T20:34:55Z - Architecture learning handbook created

Created the canonical printable study note at
`docs/education/teaching-notes/0002-architecture-learning-handbook.md`.
It records completed lessons, repository evidence, misconceptions, study
questions, and a protocol for appending later lesson chunks.

### 2026-09-01T20:49:57Z - Platform-contract topic grouping studied

Classified the current `platform/contracts` surface into proposed natural
topics: errors, names, feature flags, contexts, permissions, routes, jobs,
registry, and app definition. Recorded the proposal in the handbook without
moving any source files.

### 2026-09-01T20:52:06Z - Platform-contract groupings explained

Added a first-time-learner explanation of each proposed platform-contract
topic to the handbook, including what each owns, why it is separate, common
misconceptions, and a route-to-authorization study question. No source files
were changed.

### 2026-09-01T20:55:59Z - Platform-contract dependency direction studied

Added the proposed one-way dependency map for platform contract topics to the
handbook. The lesson explains the distinction between source dependencies and
runtime order, uses an invoice route as an example, and records why cycles are
harmful. No source files were changed.

### 2026-09-01T20:59:58Z - Semantic nomenclature proposal studied

Recorded a proposed semantic naming profile for app-owned routes, jobs, flags,
health checks, and permissions. The proposal keeps tenant, group, role,
provider, and version facts out of stable permission names and identifies the
registry/runtime mount boundary as the place to enforce app ownership prefixes.
No rule or source files were changed.

### 2026-09-01T21:03:11Z - Cross-codebase scanability assessed

Recorded the strongest candidates for semantic scanability beyond platform
contracts, including platform security, runtime, server, and selected core
capabilities. Captured security, operational, compatibility, and over-splitting
risks plus a staged adoption sequence. No source files were changed.

### 2026-09-01T21:40:41Z - Identifier category-prefix convention studied

Recorded the rule of thumb that files, TypeScript types, and explicit fields
should state an identifier's functional category; identifier values should
state stable owner and capability. Configuration keys and error codes need
clear subsystem/subject names in flat operational contexts, but generally do
not need redundant `config` or `error` prefixes. No rule or source files were
changed.

### 2026-09-01T21:45:24Z - Naming-policy home and adoption sequence studied

Identified the existing `platform.contracts-are-the-app-boundary` rule in
`docs/harness/architecture/rules/layers/platform.yml` as the future home for
the semantic naming profile. Recorded why this is a platform-contract standard
rather than core, product-harness, security, or tenancy policy, plus a
document-first and validator-second adoption sequence. No rule or source files
were changed.

### 2026-09-01T21:58:33Z - Platform-contract naming policy codified

Added a source-reviewed semantic identifier naming policy to the existing
platform layer rule. The complete evidence chain includes the source-material
addition, an accepted two-iteration OKF review record, updated derivation
report, refreshed source provenance, and a focused retrieval-selector fixture.
Source projection, coverage, source-review, derivation-report, provenance,
selector, index, chunk, recognition, and diff checks passed. No runtime code or
identifier values were changed; registry-level enforcement remains a future
compatibility-preserving implementation slice.

### 2026-09-01T22:02:31Z - App mount and registry studied

Added a handbook lesson that traces app declarations through the runtime
registry and into the server and worker shells. It distinguishes local
registration checks from cross-declaration validation, explains the
startup-failure boundary, and connects the deferred app-ownership naming check
to the mount context. No runtime source files were changed.

### 2026-09-01T22:09:43Z - Registered jobs and workers studied

Added a handbook lesson that follows a registered job through queue dispatch,
payload validation, optional idempotency, job context, successful execution,
retry, and dead-letter handling. It also records the current in-memory queue's
delayed-delivery limitation and the distinct roles of tenant context and
end-user authorization. No runtime source files were changed.

## Sub-Agent Activity

- None recorded yet.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The checkpoint records focused module organisation, an existing-rule
extension, plans, and educational material. The deferred DLQ remediation idea
will be recorded as a future capability with explicit non-goals, not adopted as
an implemented cross-layer architecture decision in this checkpoint.

## Session Metrics

Raised at UTC: 2026-08-31T00:11:19Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- Printable study handbook:
  [Architecture Learning Handbook](../../../../../docs/education/teaching-notes/0002-architecture-learning-handbook.md)

## RAG Knowledge Disposition

Status: covered
Reason: The checkpoint changes knowledge-bearing core security contract
organisation and the platform contract naming standard. Both are covered by
updated source material, derived rules, review and derivation evidence,
projection records, selector proof, and generated recognition sources.
Evidence:

- `docs/harness/architecture/rule-packs/add-core-module.yml`
- `docs/harness/architecture/rules/layers/packages-core.yml`
- `docs/harness/architecture/source-material/platform-runtime-enterprise-obligations-v1.md`
- `docs/harness/architecture/rules/layers/platform.yml`
- `.agentic/02.rag-rulebook/source-material-reviews/03.product.platform/2026-09-01-platform-contract-identifier-naming.yml`
- `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`
- `.agentic/02.rag-rulebook/source-projections/v1.yml`
- `.agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-contract-identifier-naming.yml`
- `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`

Corpus gaps:

- None.

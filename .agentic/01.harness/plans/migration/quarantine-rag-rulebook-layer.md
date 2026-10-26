<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.migration-plan.quarantine-rag-rulebook-layer
version: 1
status: active
created_on: "2026-10-26"
updated_on: "2026-10-26"
layer: 01.harness
domain: migration
disciplines:
- agentic
- architecture
- sre
kind: migration-plan
purpose: Preserve the existing RAG/rulebook layer while removing it from ordinary platform, harness, and commit work.
portability:
  class: internal
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
-->
# Quarantine the RAG/Rulebook Layer

## Decision

Keep the current RAG/rulebook implementation, its historical evidence, and its
future-rebuild value. Do not let its retrieval runtime, provenance graph, or
validation suite run as an automatic dependency of ordinary platform and
harness work.

The layer becomes dormant by default: RAG work is opt-in and explicitly named;
platform, harness, chat, and ordinary documentation work do not trigger RAG
validation or require a RAG runtime. No RAG files, commands, records, or
deployment history are removed in this plan.

## Evidence

The standard commit hook runs a full artifact-index coverage pass before check
selection. Measured on 2026-10-26, that pass took 14.42 seconds. The selector
then took 26--38 seconds to build representative platform/product impact plans
before executing a local check. RAG review and derivation records occur in
those selected proof references, expanding the graph and its fingerprints.

The elaborate `scripts/02.rag-rulebook/commit-gates` suite is not directly
invoked by the normal chat commit hook. It remains a manual RAG-maintenance
capability. The drag comes from generic repository indexing and dependency
selection treating RAG material as ordinary active commit evidence.

## Target Behaviour

<!-- deterministic-check: allow reason="This table states user-facing routing policy; the selector catalog and commit gates enforce the executable boundaries." -->
| Work | Automatic commit behaviour |
| --- | --- |
| `packages/**`, `platform/**`, apps, ordinary harness work | Run only applicable owner and shared checks; do not traverse or execute dormant RAG evidence |
| RAG/rulebook maintenance explicitly requested by a user | Run the RAG maintenance gate and any selected RAG checks explicitly |
| Full repository integrity audit | Run separately on demand or in CI; it is not part of an ordinary task commit |

## Implementation Slices

1. Define a repository-owned dormant-capability boundary for the four RAG path
   roots. The generic impact selector must not traverse dependency edges into or
   out of a dormant root when the changed path is outside that root. A change
   inside a dormant root remains visible and must require an explicit RAG
   maintenance invocation.
2. Keep the existing `rag-*` repository-input mappings so direct changes to an
   RAG-owned path continue to select their preserved checks. The dormant impact
   boundary makes those mappings unreachable from unrelated work. Consider
   narrowing their broad declared inputs to RAG-owned paths only after an
   explicit RAG-maintenance review establishes that doing so preserves coverage.
3. Move the full `generate-index --all --strict --check-coverage` audit out of
   `scripts/repo/commit-gates` and into a named audit command or CI check. The
   existing staged header and process-drift gates remain at the task commit
   boundary.
4. Remove automatic RAG prompt classification. Requests concerning the dormant
   system route to harness planning or implementation until a future rebuild is
   explicitly activated. The RAG workflow and files remain available for
   deliberate maintenance.
5. Measure the before/after timing for a representative `packages/core` change,
   a harness documentation change, and an explicitly requested RAG change.
   Confirm ordinary work selects no RAG check and explicit RAG maintenance still
   has a documented validation route.

## Non-goals

- Do not delete, rename, archive, or move `.agentic/02.rag-rulebook/`,
  `scripts/02.rag-rulebook/`, `docs/02.rag-rulebook/`, or
  `infra/04.deploy/02.rag-rulebook/`.
- Do not invalidate owner-aligned product and deploy rules whose provenance
  currently points into RAG history.
- Do not weaken the staged header, write-location, commit-log, or applicable
  product/platform verification gates.
- Do not reactivate the retired hosted service or deployment target.

## Validation

Before completing the quarantine, prove all of the following:

- a representative platform or harness impact plan contains no RAG check and
  has no RAG path in its selected proof references;
- explicit RAG maintenance has a documented command and selects its preserved
  checks only when directly requested;
- the normal chat commit preparation continues to run its non-RAG gates;
- the full artifact inventory audit remains runnable as an explicit operation;
- classifier fixtures route dormant-RAG prompts to the harness workflow.

## Recovery

The quarantine is reversible. Removing the dormant boundary and restoring the
normal check mappings reactivates the existing layer. No source history or
runtime implementation is discarded.

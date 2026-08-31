<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standards.document-artifact-placement
version: 1
status: active
layer: 01.harness
domain: governance
disciplines:
- agentic
- architecture
kind: standard
purpose: Define owner-aligned locations for new document artifacts and corpus material.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.change-harness
  path: .agentic/01.harness/workflows/change-harness.md
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
- id: harness.readme
  path: .agentic/01.harness/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Document Artifact Placement Standard

## Purpose

Use this standard when adding or moving document artifacts, including ADRs,
guides, source material, plans, rules, rule packs, READMEs, runbooks, and
curated corpus material.

The goal is to route new documents to the owner-aligned layer or corpus home
instead of extending legacy prototype locations such as
`docs/harness/architecture`.

## Core Rule

Place every new document artifact in the narrowest owner layer that governs or
retrieves it.

Governance artifacts belong under `.agentic/<owner-layer>/`. Human-readable
corpus material belongs under `docs/<owner-layer>/` when that numbered corpus
root exists. If the target root does not exist, create it through a governed
slice before adding ordinary content there.

Do not add new documents under `docs/harness/architecture/**` unless the change
is an approved compatibility pointer, migration update, or reference-preserving
step named by a governed artifact path migration plan.

## Owner Routing

| Owner | Governance home | Corpus or human-doc home |
| --- | --- | --- |
| Chat lifecycle | `.agentic/00.chat/` | `docs/00.chat/` |
| Harness governance | `.agentic/01.harness/` | `docs/01.harness/` after the root is created |
| RAG/rulebook service and self-corpus | `.agentic/02.rag-rulebook/` | `docs/02.rag-rulebook/` |
| Product and runtime contracts | `.agentic/03.product/` | `docs/03.product/` after the root is created |
| Deployment and operations | `.agentic/aws/` | `docs/04.deploy/` |
| Education | `.agentic/education/` | `docs/education/`, or `docs/05.education/` after a namespace decision |
| Cross-layer shared process | `.agentic/shared/` | `docs/06.shared/` after the root is created |

When ownership is ambiguous, stop before creating the artifact. Record the
placement question in the session log and resolve it through the owning
workflow, standard, migration plan, or ADR.

## Artifact-Type Routing

| Artifact type | Default location |
| --- | --- |
| Workflow, standard, checklist, policy, schema, template, agent, gate, hook, or eval | `.agentic/<owner-layer>/` |
| Migration plan | `.agentic/<owner-layer>/plans/migration/` |
| Implementation plan that governs future product, harness, or deploy work | `.agentic/<owner-layer>/plans/implementation/` |
| ADR | `docs/<owner-layer>/adrs/` when it is corpus history; `.agentic/<owner-layer>/adrs/` only when a workflow explicitly owns agentic process decisions there |
| Source material | `docs/<owner-layer>/source-material/` |
| Structured ruleset | `docs/<owner-layer>/rules/` |
| Rule pack | `docs/<owner-layer>/rule-packs/` |
| Runbook or guide | `docs/<owner-layer>/` for human/corpus docs; `.agentic/<owner-layer>/guides/` for agent-facing harness operation |
| Compatibility pointer | The retired source path, with a link to the canonical target and migration plan |

Use `.agentic/01.harness/standards/agentic-artifact-standards.md` to decide
which artifact type should own the rule or procedure. Use this standard to
decide the path once the artifact type and owner are known.

## Migration-Period Rules

`docs/harness/architecture/**` is the current prototype corpus. During its
domain split:

- keep existing files in place until a governed artifact path migration moves
  a concrete source and target pair;
- add only compatibility pointers, migration plans, or reference-preserving
  edits under the old prototype path;
- route new product source material, product rules, and product rule packs to
  the product layer or stop and create the required `docs/03.product/` root
  through the migration plan first;
- route new RAG/rulebook machinery docs to `docs/02.rag-rulebook/` or
  `.agentic/02.rag-rulebook/`, not to the prototype product corpus;
- classify ADRs by the layer that owns the decision before choosing a target
  path.

If a migration slice introduces a new numbered docs root, update the relevant
README, artifact metadata path allowlists, recognition sources, source
projections, indexes, chunks, selector fixtures, and coverage checks in the
same slice.

## Required Checks

Before completing a document-placement change, run the checks named by the
owning workflow. For harness or corpus-facing document additions, include:

```bash
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current
git diff --check
```

Also run source-projection, source-material coverage, rulebook index, chunk,
and retrieval checks when the change affects corpus roots, rules, rule packs,
or source material.

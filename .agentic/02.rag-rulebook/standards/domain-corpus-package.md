<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.domain-corpus-package
version: 1
status: active
layer: 02.rag-rulebook
domain: corpus
disciplines:
- agentic
- architecture
kind: standard
purpose: Define the package shape for modular domain rulebook corpora.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Domain Corpus Package Standard

## Purpose

Define how a domain packages source material, generated rulebooks, indexes, and
retrieval metadata without merging separate domains into one instruction set.

A corpus package is a modular input to the portable RAG/rulebook service.

## Corpus Boundary

Each corpus package should have one clear owner and one clear domain.

Expected domain corpora include:

- harness
- product-apps
- design-system
- deploy
- education

The service may retrieve across multiple corpora, but each corpus should remain
separately named, indexed, cited, and governed.

## Recommended Shape

Use this package shape unless a domain ADR approves another:

```txt
rulebook.<domain>/
  README.md
  manifest.yml
  sources/
  rules/
    layers/
    concerns/
  rule-packs/
  chunks/
  indexes/
  schemas/
  migrations/
```

The folder name is illustrative. The portable service should rely on
`manifest.yml` and artifact metadata rather than hardcoded absolute paths.

## Manifest

Each corpus manifest should identify:

- corpus ID
- domain
- owner layer
- source roots
- generated rule roots
- rule-pack roots
- chunk roots
- index roots
- supported targets
- source-to-rulebook generation policy
- retrieval policy
- migration status

## Source Material

`sources/` contains human-authored or imported source material.

Source material may include Markdown, PDFs converted to Markdown, ADRs,
runbooks, standards, examples, or other curated inputs. Sources should be
citable and stable enough for rule generation.

## Generated Or Curated Rules

`rules/` and `rule-packs/` contain structured YAML used for retrieval and
governance. They may be generated, curated, or mixed, but their status should be
clear.

Rule YAML should keep ideas named, addressable, and extractable. Long YAML is
acceptable when it has structured sections and stable IDs.

## Chunks And Indexes

`chunks/` contains generated retrieval units. Chunks should be derived from
meaningful structure such as rules, checks, source references, task steps, or
evidence requirements.

`indexes/` contains generated maps for artifacts, rules, chunks, graph edges,
source references, and corpus manifests.

Generated chunks and indexes should be reproducible from source material and
rulebook YAML.

## Migration Policy

Do not move existing prototype corpus files into this shape without a governed
artifact path migration.

Before moving files, create a migration plan that names:

- source paths
- target corpus package
- stable artifact IDs
- reference updates
- validation checks
- rollback approach

## First Corpus Candidate

The current `docs/harness/architecture/` tree is the prototype corpus. It
should remain in place until a migration separates harness, product/apps,
design-system, deploy, and education ownership.

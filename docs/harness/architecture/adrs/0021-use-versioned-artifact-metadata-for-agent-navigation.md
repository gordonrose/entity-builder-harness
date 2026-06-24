<!-- agentic-artifact:
owner: harness
kind: adr
purpose: Record the decision to use versioned artifact metadata and stable IDs for agent navigation and future repo indexes.
domain: metadata
portability: source-only
used_by:
  - .agentic/01.harness/artifact-metadata/standard.md
  - .agentic/01.harness/artifact-metadata/README.md
-->

# 0021 Use Versioned Artifact Metadata For Agent Navigation

Status: accepted
Date: 2026-06-24

## Context

The harness uses metadata headers to make scripts, workflows, standards,
architecture docs, and YAML rule artifacts self-describing. The current v1
headers are useful for commit-time checks, but they still mix several concerns:

- `owner` currently behaves like a layer value rather than a person or team
- `domain` carries sub-layer meaning without a taxonomy
- `portability` compresses class and target repo into one string
- `used_by` points at paths, which become brittle when files move
- artifacts do not have stable IDs for indexing or migration reconciliation

The repo is also growing toward multiple reusable targets such as
`llm-workbench`, `entity-builder`, and `design-system-builder`. Future agents
need a compact, trusted map of artifacts so they can navigate and analyze the
repo without reading every file in full.

## Decision

Create a dedicated artifact metadata capability under
`.agentic/01.harness/artifact-metadata/`.

Define `agentic-artifact/v2` as the preferred future metadata schema for
harness artifacts. The v2 schema uses:

- stable artifact `id`
- semantic artifact `version`
- `status`
- numbered `layer`
- extensible `domain`
- controlled `disciplines`
- extensible `kind`
- one-sentence `purpose`
- structured `portability`
- script-specific `effects` when `kind: script`
- ID-first `used_by` references with optional path hints

Keep existing v1 headers valid during migration, including current
`agentic-script` headers. New or materially changed artifacts should prefer v2.
Script migration remains in scope for the metadata project, and v2 script
artifacts require structured parsing and conditional `effects` validation.

Future index generation should use metadata headers to generate current
ID-to-path and metadata indexes. Historical path reconciliation should come
later from Git history after stable IDs are widely adopted.

## Consequences

Agents gain a durable identity model for artifacts that is not tied to paths.

Cross-repo extraction can query portability class and targets instead of parsing
compressed portability strings.

Migrations can update references by artifact ID and use paths as validation
hints rather than brittle source of truth.

The checker and future index generator must support both v1 and v2 during the
migration period.

This decision introduces a new capability home but does not move or retire the
existing compatibility checker or v1 standard. Any future file moves must follow
the governed artifact path migration workflow.

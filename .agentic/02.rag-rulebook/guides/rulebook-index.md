<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.guide.rulebook-index
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: guide
purpose: Teach humans how to understand and use the RAG/Rulebook rulebook index contract.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
-->
# Rulebook Index Guide

## What A Rulebook Index Is

A rulebook index is the catalogue for a corpus.

It does not answer the user's task directly. It tells the RAG/rulebook service
what exists, where it lives, which corpus owns it, which rules it contains,
which chunks can be generated, and which references connect it to other rules.

The context packet is the small evidence bundle returned to the model. The
rulebook index is how the service finds that evidence.

## Why It Comes Before Migration

The current prototype corpus lives under `docs/harness/architecture/`.

The proposed target structure uses numbered corpus packages such as
`corpus.03.product.platform` or `corpus.04.deploy`.

Before moving files, the index needs to prove that current artifacts, rule IDs,
rule-pack dependencies, related rulesets, and path mappings are understood.
After migration, the same index shape should prove that the moved files still
resolve.

That is the difference between a tidy folder move and a safe corpus migration.

## How To Read One

Start with `source_roots`.

These tell you what was scanned: current prototype corpus paths, migration maps,
future corpus package roots, or generated outputs.

Then read `corpus_packages`.

These name the numbered corpora known to the index. A good index should make it
clear whether a corpus is current, proposed, migrated, or deprecated.

Then read `artifacts`.

Artifacts are the files or source objects in the catalogue: source guides,
ADRs, layer rulesets, concern rulesets, rule packs, schemas, guides, standards,
or plans. Each artifact keeps stable IDs separate from current paths.

Then read `rules` and `rule_packs`.

Rules let retrieval target one rule inside a long YAML artifact. Rule packs
connect task intent to required rulesets, checks, and agent steps.

Then read `chunk_candidates`.

These are not necessarily final chunks. They are structured units that can be
turned into retrieval chunks later. They should come from meaningful YAML
structure, not arbitrary character windows.

Then read `graph_edges`.

Edges explain relationships: contains-rule, required-ruleset,
related-ruleset, applies-to-path, proposed migration target, split review, and
similar links.

Finally read `path_mappings`, `unresolved_references`, and `diagnostics`.

Those fields are the safety surface for migration. They show what will move,
what did not resolve, and whether the index is safe to use.

## Field Families

`source_roots` records the inputs to the index.

`corpus_packages` records the knowledge packages and their owner layers.

`artifacts` records the durable source objects and their current or proposed
paths.

For structured rules derived from governed source material, `artifacts` should
carry `source_derivation` so the generated index preserves the source path,
source hash, derivation workflow, and derivation report.

`rules` records individual rule entries inside ruleset artifacts.

`rule_packs` records task packs and their required ruleset dependencies.

`chunk_candidates` records deterministic chunk units for a later chunk
generator.

When a chunk candidate comes from a source-derived rule, it should carry the
same `source_derivation` block so generated chunks can expose the provenance
without reparsing the source YAML.

`graph_edges` records relationships that retrieval can traverse.

`source_references` records citable source locations.

`path_mappings` records current-to-proposed migration paths.

`unresolved_references` records missing or ambiguous links instead of hiding
them.

`diagnostics` records index health.

`provenance` records how the index was generated.

## What Good Looks Like

A good index is deterministic. Running it twice on the same inputs should
produce the same logical result.

A good index separates identity from path. Metadata IDs and rule IDs should
survive a file move.

A good index is graph-aware. Required rulesets and related rulesets are edges,
not just strings buried in YAML.

A good index is migration-aware. It can represent both the current prototype
path and the future corpus package path.

A good index is honest. Unresolved references are reported.

A good index preserves source derivation provenance. If YAML rules were derived
from Markdown source material, the index should retain the source hash and
derivation report path so stale projections can be detected downstream.

## What Bad Looks Like

A bad index treats file paths as durable identity.

A bad index drops unresolved related rulesets or required rulesets.

A bad index flattens every rulebook into one blob of text.

A bad index mixes product, harness, deploy, and shared concerns without naming
corpus ownership.

A bad index depends on embeddings before deterministic parsing works.

A bad index drops source hashes when converting source-derived YAML into chunk
candidates.

## Relationship To The Context Packet

The rulebook index is broad. It knows about many artifacts, rules, edges, and
candidate chunks.

The context packet is narrow. It selects the small subset needed for one user
request.

The retrieval flow should be:

1. Use intent and path metadata to find matching index entries.
2. Expand through required and related graph edges.
3. Select chunk candidates.
4. Trim to budget.
5. Emit a cited context packet.

## Relationship To Migration

Before moving files, generate an index from current prototype paths.

After moving files, generate an index from the new corpus package paths.

Then compare:

- artifact IDs
- rulebook IDs
- rule IDs
- rule-pack IDs
- required ruleset references
- related ruleset references
- source references
- unresolved references
- path mappings

If identity survives and references still resolve, the migration is safe.

If identity changes or references break, stop and fix the migration plan.

## Relationship To Future Validators

A future validator should check that:

- every indexed YAML artifact appears once
- every artifact belongs to a known corpus
- every rule belongs to a known artifact
- every rule pack belongs to a known artifact
- every graph edge resolves
- every unresolved reference is reported
- every path mapping has a migration status
- diagnostics correctly reflect errors and blocking references

The validator should be read-only at first.

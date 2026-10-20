<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.adr.0039-discover-artifacts-by-declared-headers
version: 1
status: active
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 01.harness
domain: metadata
disciplines: [agentic, architecture]
kind: adr
purpose: Make declared artifact headers discoverable independently of required-header placement rules.
portability:
  class: source-only
  targets: []
used_by:
  - id: harness.capability.artifact-metadata
    path: .agentic/01.harness/artifact-metadata/README.md
-->
# 0039 Discover Artifacts By Declared Headers

Status: accepted
Date: 2026-10-20

## Context

The checker and index reused path and extension rules to decide both where
headers were required and where declared headers could be found. A lifecycle
migration therefore missed 48 existing headers in infrastructure YAML,
TypeScript, Python, Dockerfiles and platform documentation. A successful scoped
check did not establish repository-wide coverage. Those missed headers also
contained metadata errors that the old checker never inspected.

## Decision

Discover leading file-level `agentic-artifact` and legacy `agentic-script`
declarations across tracked and unignored working files, independently of
extension and location. Share discovery and parsing between the checker, index
and lifecycle helper. Keep existing required-header placement rules unchanged.
Exclude embedded examples, binary files and symlink targets. Source archives
use a safe filesystem fallback. Staged checks inspect staged blobs and retain
previously declared artifacts in scope when a change removes a header.

Exclude only the three named raw bootstrap scaffolds with unresolved
placeholders; validate their rendered outputs through portability tests. Keep
intentional v2 examples and valid infrastructure templates in the inventory.

Compare declared paths against emitted index entries through an explicit
coverage gate. Fail malformed declarations instead of silently omitting them.
Package the shared discovery dependency with the portable checker. Preserve
lifecycle, stable identity and Git provenance rules from ADR 0038.

## Consequences

Files already claiming to be governed artifacts receive the same validation and
navigation support. Existing headerless files do not acquire new requirements.
Full scans inspect more files, so discovery must safely exclude irrelevant
content and tests must cover both genuine declarations and embedded examples.

The missed batch is repaired and migrated with Git evidence before recognition
inventories are regenerated. Schema compatibility remains unchanged: v1/v2 are
readable, and new or intentionally migrated artifacts use v3. A successful
migration report must distinguish actual legacy examples and raw templates
from coverage gaps.

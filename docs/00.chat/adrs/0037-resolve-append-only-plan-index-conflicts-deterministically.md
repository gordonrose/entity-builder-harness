<!-- agentic-artifact:
schema: agentic-artifact/v2
id: chat.architecture.adr.0037-resolve-append-only-plan-index-conflicts-deterministically
version: 1
status: active
layer: 00.chat
domain: main-refresh
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the deterministic resolution rule for strictly append-only plan-index conflicts during a governed chat refresh.
portability:
  class: required
  targets:
  - llm-workbench
used_by:
- id: chat.standards.main-refresh-conflict-types
  path: .agentic/00.chat/standards/main-refresh-conflict-types.md
- id: chat.script.main-refresh.classify-conflict
  path: scripts/00.chat/main-refresh/classify-conflict/script.sh
-->
# ADR 0037: Resolve Strictly Append-Only Plan-Index Conflicts Deterministically

## Status

Accepted.

## Context

Two independent, valid platform changes can each add a new entry to the same
layer-owned plan index. Git presents this as an authored-document conflict even
when both changes retain the existing table and neither changes the meaning of
an existing row.

Stopping for a routine additive index collision consumes operator time and
encourages informal conflict resolution. Conversely, automatically resolving
arbitrary Markdown conflicts could overwrite an existing plan description or
metadata decision.

## Decision

The main-refresh classifier recognises `append-only-plan-index-conflict` only
when all of the following are true:

- the path is `docs/<numbered-layer>/plans/README.md`;
- base, chat, and incoming versions preserve every pre-existing Markdown plan
  table row;
- each side adds only unique plan rows; and
- non-table content is identical except for the artifact-metadata version.

For that narrow shape, resolution preserves every base and unique added row,
orders added rows lexically, and increases the metadata version once from the
highest incoming version. The conflict classifier, standard, required checks,
and session-log audit make the result reviewable.

Any removed/altered row, malformed/duplicated row, table-shape difference, or
other prose/metadata change remains a normal authored-content conflict and is
not automatically resolved.

## Consequences

Independent plans can be integrated without an unnecessary approval pause when
their only overlap is a mechanically verified append-only index update.

The rule does not authorise merging business, infrastructure, policy, code, or
arbitrary documentation conflicts. It intentionally fails closed beyond the
precise index shape.

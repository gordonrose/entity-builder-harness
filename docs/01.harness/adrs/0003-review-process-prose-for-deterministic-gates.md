<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0003-review-process-prose-for-deterministic-gates
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0003 Review Process Prose For Deterministic Gates architecture
  decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0003 Review Process Prose For Deterministic Gates

Status: accepted
Date: 2026-06-15

## Context

Harness workflows and checklists can drift toward procedural prose that agents
must interpret manually. Some prose is appropriate because it records judgment,
approval boundaries, rationale, or governance. Other prose describes checks
that can be represented more safely as deterministic scripts or gates.

Without a repeatable review, harness updates can add manual procedure where an
executable check would be clearer and less error-prone.

## Decision

Harness process commits must run a deterministic-process drift check over the
staged commit candidate. The check flags operational prose that appears to
describe scriptable file, branch, metadata, command, or gate conditions.

The check is suggestion-only. It does not rewrite files. When it finds likely
drift, the agent must propose one of these responses for approval:

- move the deterministic portion into a script or gate
- keep the prose and add an allow marker with a reason when the prose is
  intentionally human-governed
- defer the finding to a broader harness cleanup task

The same script also supports broader audit modes for a commit, specific paths,
or the whole harness. Audit findings guide cleanup planning but do not
automatically edit files.

## Consequences

New harness process commits are biased toward executable checks where possible,
while approval boundaries and judgment-heavy rules remain prose.

The gate can produce false positives because it uses conservative text
heuristics. Allow markers with reasons make intentional prose explicit instead
of silently normalizing manual procedure.

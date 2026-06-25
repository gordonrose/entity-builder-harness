<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0012-treat-missing-governance-as-stop-condition
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0012 Treat Missing Governance As A Stop Condition architecture
  decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0012 Treat Missing Governance As A Stop Condition

Status: accepted
Date: 2026-06-16

## Context

The harness exists to make agent work governed, auditable, and improvable.
Agents can still encounter necessary actions, recovery paths, workarounds, or
substitutions that are not covered by the current workflow, gate, script, or
standard.

One motivating case was a branch refresh where an ordinary Git recovery pattern
looked reasonable, but the selected workflow did not authorize that recovery
path. The specific operation was less important than the failure mode: agent
judgment filled a governance gap instead of making the gap visible.

## Decision

Missing governance is a stop condition.

If a required action, recovery path, workaround, or substitution is not governed
by the current workflow, gate, script, or standard, agents stop before acting.
They explain the governance gap and ask whether to update the harness instead
of improvising.

This principle belongs in `AGENTS.md` as an always-loaded safety invariant
because it applies across all layers. Detailed recovery paths still belong in
the narrow workflow, gate, script, or standard that owns the action.

## Consequences

The harness treats gaps as design input rather than hidden agent discretion.
Future agents should surface missing process coverage at the moment it matters,
which gives maintainers the choice to add governed behavior or decline the
action.

This makes some work stop earlier than a senior engineer might ordinarily
continue. That is intentional. The repo values governed repeatability over
one-off reasonable recovery when the current harness does not cover the move.

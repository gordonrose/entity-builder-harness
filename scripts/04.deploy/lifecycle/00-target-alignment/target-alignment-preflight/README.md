<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.target-alignment-preflight.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Reserve the capability home for a provider-neutral target-alignment preflight.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.plan.migration.aws-provider-neutral-transition
  path: .agentic/04.deploy/plans/migration/aws-provider-neutral-transition.md
-->
# Target Alignment Preflight

This capability has a provider-neutral workflow and standard, but no executable
validator or provider adapter yet.

It will compare declared local requirements with normalized, safe target facts
before deployable implementation begins, and again before a target mutation.
The first executable implementation is limited to an offline contract validator
and test fixtures. It must not inspect or mutate AWS until a separately
governed provider adapter is designed, tested, and approved.

Read the workflow at
`.agentic/04.deploy/workflows/target-alignment-preflight.md` and the standard
at `.agentic/04.deploy/standards/target-alignment-preflight.md` before adding
that implementation.

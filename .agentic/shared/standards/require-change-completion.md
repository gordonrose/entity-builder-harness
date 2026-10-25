<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standard.require-change-completion
version: 1
status: active
created_on: "2026-10-24"
updated_on: "2026-10-25"
layer: 06.shared
domain: process.change-completion
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Require connected implementation, proportionate authorized verification and honest completion evidence across layers.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: shared.workflows.change-shared-process
  path: .agentic/shared/workflows/change-shared-process.md
-->
# Require Change Completion

A change is complete when its applicable contract, implementation, affected
consumers and required verification agree. A plan, declaration or passing
individual check proves only its own boundary. Report uncovered impact and
missing required proof explicitly instead of treating either as completion.

## Implementation and consumers

Identify affected contracts, configuration, packages, entrypoints, deployment
scopes and downstream consumers in their existing owner records. Update the
supported implementations and compatibility assumptions in the same change.
Use the owning executable discovery and validation controls; an unowned or
unsupported requirement is a gap, not an implicit exclusion. A valid
non-applicability has a reason and does not hide an affected consumer.

## Verification and stage boundaries

Select existing checks in proportion to affected consumers and declared
requirements. Deduplicate identical checks only within the same stage and
input identity. Reuse passing evidence only when its relevant source, inputs,
artifact bindings and freshness still match; a prior static pass cannot
satisfy package, target or live behavior proof. Preserve mandatory checks,
stage ordering and each command's permissions. A selector may identify a
provider or publication check without being allowed to execute it.

Missing implementation blocks the stage that consumes it. Missing proof blocks
the stage that requires that proof. Distinguish static validation, local
runtime tests, actual container qualification, CI and live evidence in the
existing session record and completion report. Name checks, outcomes and safe
evidence references; planned commands and fixtures are not execution evidence.

## Correction and continuation

After failure, retain safe evidence, repair the relevant owner, rerun affected
checks and resume from the first incomplete stage. Broaden verification when
changed impact or unresolved evidence warrants it. Continue independent
authorized work while another operation is blocked. Reconcile an interrupted
operation before repeating a mutation or a completed task; pending, failed and
uncertain outcomes must remain distinct.

## Authoritative specialization

This standard owns cross-layer completion principles only. Deployment
[realization proof](../../04.deploy/standards/operational-realization-gate.md)
owns deployment proof levels, gates and evidence semantics. Product owners own
runtime contracts. Provider owners own concrete inspection, mutation,
permission, reconciliation and recovery procedures. Their workflows reference
these owners rather than copy or redefine them. Session lifecycle, goal
lifecycle and git approval remain with their existing owners.

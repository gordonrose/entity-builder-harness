<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.execution.kanbien-core-platform-bootstrap
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- agentic
- architecture
- security
- sre
kind: execution-plan
purpose: Govern the exact qualification and E0-E7 execution sequence for the isolated kanbien-core-platform bootstrap target.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.plan.implementation.platform-to-target-chain-control
  path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md
-->
# Kanbien Core Platform Bootstrap Execution Plan

## Authority and status

This is the execution authority for the target-specific bootstrap packet. The
generic implementation plan defines reusable rules; explanatory documents under
`docs/` do not authorise execution. A separate approved packet is still
required for any AWS or GitHub mutation.

Current execution status: `E3-qualified; E4 alignment and foundation-output update required before a runtime change set can be created`.

## Completion criterion

The packet is complete only when release B has an accepted receipt proving the
same immutable digest was qualified, selected by the workload, and confirmed
by controlled live verification. A submitted stack, dispatched workflow, or
provider propagation wait is not completion.

## Required sequence

| Gate | Purpose | Evidence required to continue | Failure result |
| --- | --- | --- | --- |
| Q0 | Qualify candidate package | base-image policy, container smoke, safe command diagnostics, dependency proof | rejected package; no workload foundation or deployment |
| Q1 | Qualify delivery authority | static delivery-access coverage and safe live read probes | blocked publication with a safe access diagnostic |
| E2a | Establish package destination only | dedicated immutable ECR destination and target isolation evidence | stop; no runtime foundation |
| E3 | Publish and approve A | digest, ECR scan, SBOM, provenance, custody receipt | rejected package; do not deploy |
| E2c | Establish runtime foundation | approved A receipt, fresh alignment, exact change set | stop; no automatic retry or cleanup |
| E4–E5 | Deploy and accept A | workload digest, private verification, accepted receipt | reject A and stop |
| E6–E7 | Deploy and accept B | same evidence for B and retained A rollback digest | one explicit rollback to A, verify A, then stop |

Provider-controlled conditions use the declared asynchronous-condition record
and its generic validator. They are `waiting-on-external-system`, not packet
completion. A temporary waiver is valid only while its recorded compensating
controls and expiry apply.

## Delegated execution reporting

Delegated workers use `.agentic/01.harness/standards/delegated-execution-state.md`.
Every non-complete report names completed gates, current gate, evidence
reference, next permitted action, and blocking condition.

The delivery-access checks are composed as follows: the fixed target wrapper
supplies the package declaration and destination; the AWS adapter reads the
declared role policy or runs a bounded ECR read probe; the reusable validator
checks the contract against normalized coverage. None of those layers may
silently substitute another target.

## E4 live-control chain

E4 is deliberately split into four fail-closed actions. A package receipt is
necessary, but never enough to mutate a target.

1. The fixed target alignment wrapper derives the candidate digest from the
   qualified receipt, obtains only the declared AWS facts, and passes their
   normalized result through the provider-neutral alignment validator.
2. The foundation must export every value consumed by the runtime template.
   Missing output is an alignment failure, not permission to supply a manual
   identifier. The current foundation needs an output-only reviewed update for
   `VpcId` and `PrivateSubnetIds` before the initial runtime stack can be
   planned.
3. The fixed change-set creator obtains parameters only from that foundation
   and the qualified receipt. It makes exactly one named initial-release
   change set and does not execute it.
4. The fixed deployment control re-reads that change set, confirms its digest,
   source revision, stack and resource boundary, then executes it. The private
   verifier subsequently proves the running task uses the same immutable
   digest. There is no automatic retry or replacement path.

An expired local AWS SSO session is an `authentication-unavailable` alignment
result. It is not evidence that a target fact is missing and must not cause a
fallback to a manually supplied value.

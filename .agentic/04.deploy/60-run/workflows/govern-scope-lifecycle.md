<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.govern-scope-lifecycle
version: 2
status: active
created_on: "2026-10-23"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.scope-lifecycle
disciplines: [agentic, security, sre]
kind: workflow
purpose: Govern addition, succession, activation, reversion, and retirement of target scopes without conflating index edits with provider mutation.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.validate-active-workload-health-recovery
  path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh
-->
# Govern Scope Lifecycle

## Use When

Use when a target adds an operational scope, prepares a successor for an
existing workload, activates a proved successor, reverts an accepted scope, or
retires one. Follow `require-scope-lifecycle-and-workload-ownership.md` and
validate the target lifecycle inventory before provider or release commands.

## Required sequence

1. Inventory every canonical new-framework scope directory. Give each a
   lifecycle state and exact workload ownership matching its workload binding.
   Stop if a scope is unindexed, points outside its own canonical files, or two
   active scopes own one workload.
2. For an independent scope, retain its active state only after its own
   declaration, local/package proof, and release route are complete.
3. For a successor, add it as `candidate` with its active predecessor and the
   overlapping workload identities. Validate both scope contracts and the
   candidate's required local/package checks before any provider mutation.
4. If the candidate fails preflight, deployment, health, or verification, keep
   the predecessor active. Record safe failure evidence through the candidate
   release route; do not flip lifecycle state as a workaround.
5. A supported scope advertises its provider-owned `acceptance.route` in its
   declaration. Declaration coverage validates the complete route template and
   invokes only each command owner's declared read-only argument parser before
   package/deployment operations. This preflight proves the collector, record
   schema/validator, promotion and downstream gates are connected; actual
   receipt inputs remain deferred to the acceptance stage.
6. After the candidate has the required accepted-release evidence, use the
   local `scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.sh`
   with `--scope-contract <path> --write --json`. It invokes the owning record
   validator before making the candidate active and its predecessor
   `accepted-historical` with reciprocal links. It grants no provider authority.
   Re-run the target declaration and release gates; active/historical records
   are validated again by the inventory check.
7. A later reversion is a new governed release/recovery operation. Prepare the
   historical scope as a candidate only when its contract remains compatible;
   require fresh alignment, evidence, and provider-mutation authority. Do not
   equate retained historical evidence with a restored runtime.
8. Retire a historical scope only after no active or candidate scope references
   it, required evidence-retention conditions are met, and its consumers and
   indexes have been updated.

## Stop conditions

Stop when a lifecycle edit would create dual active ownership, a predecessor or
successor is absent or inconsistent, a candidate is missing proof, a reversion
lacks a compatible contract or release authority, or an agent is asked to use
the scope index as an implicit provider-mutation command.

Offline route rehearsals use explicit `evidence_class: simulated` and
`status: rehearsed` in temporary roots. Only `--rehearsal-root` can validate or
promote those temporary records; ordinary validation and promotion require
accepted live evidence. Existing genuine records without this additive field
retain their historical live meaning. Rehearsal success is local runtime
evidence, never container, CI, provider, or production acceptance evidence.

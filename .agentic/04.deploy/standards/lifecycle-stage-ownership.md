<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.lifecycle-stage-ownership
version: 3
status: active
created_on: "2026-10-06"
updated_on: "2026-11-25"
layer: 04.deploy
domain: deployment.lifecycle
disciplines:
- agentic
- architecture
- sre
kind: standard
purpose: Define lifecycle-stage ownership and safe adoption rules for deployment capabilities.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.lifecycle.readme
  path: .agentic/04.deploy/lifecycle/README.md
- id: deploy.scripts.readme
  path: scripts/04.deploy/README.md
-->
# Deployment Lifecycle Stage Ownership

## Requirements

- Before creating or moving a deployment artifact, use
  `deployment-artifact-placement-and-naming.md` to choose its owner home,
  phase, target/scope suffix when applicable, and clear name. Run its placement
  validator for new canonical paths.
- Assign each new deployment capability one primary lifecycle phase from the
  Deployment Lifecycle Map.
- Place new lifecycle-owned scripts beneath that phase's future script home.
- Keep provider-neutral workflow and standard ownership under
  `.agentic/04.deploy/`; a lifecycle phase classifies when a capability is
  used, not its provider authority.
- Keep provider-specific inspection and execution authority in its active
  provider surface until a governed migration says otherwise.
- Do not move an established capability merely to improve lifecycle grouping.
  Use the artifact-path migration workflow, preserve compatibility, and run its
  affected checks first.
- Keep one capability authoritative. A capability may cite upstream or
  downstream phases but must not duplicate their checks or approval gates.
- For a new or intentionally migrated capability, use the objective-oriented
  command, capability, adapter, binding, test and fixture homes in the placement
  standard. A role folder alone is not an owner: its capability objective or
  enclosing cohesive target operation names the focused responsibility. Use the
  standard's retained-system form only for audited legacy families; movement
  never changes their schedules or authority. Existing mixed folders are
  migration inventory evidence, not permission to add further generic files there.

## Workload and machinery boundary

Apply the [shared reuse and delivery objective](../../shared/standards/require-change-completion.md#reuse-simplicity-and-normal-delivery)
before adding a route. Reuse the existing lifecycle owner; extend a shared
capability when needed. A workload supplies its program, configuration,
migrations, identity/access requirements and behaviour proof. Its name alone
does not justify another build, deployment, recovery or acceptance engine.

A new feature does not automatically require a new deployment scope or image.
Choose the app/program and isolation boundary from actual runtime, ownership
and security needs. A legitimately isolated workload still consumes shared
machinery. Do not merge distinct identities, databases or accepted histories
merely to remove files. Conversely, do not retain duplicated execution logic
merely because resources must remain isolated.

Infrastructure additions expose capability contracts through these existing
owners so subsequent applications can declare their use. Review callers and
older rules together; retire superseded machinery through the existing migration
workflow, preserving historical evidence. Proof selection follows the
[realization applicability rules](operational-realization-gate.md#proof-applicability-by-change).

## Stage Assignment

Use the action being proved to choose the phase:

- comparison before implementation: `00-target-alignment`;
- local runtime/configuration preparation: `10-development`;
- compilation or runtime-payload construction: `20-build`;
- non-package deterministic testing: `30-test`;
- final package/image qualification: `40-package`;
- target readiness, change review, or mutation: `50-deploy`; and
- behaviour of an already deployed target: `60-run`.

An offline test of a package belongs in `40-package`; a live smoke check of a
deployed service belongs in `60-run`. A target preflight immediately before a
change set belongs in `50-deploy`; it is distinct from Target Alignment before
implementation.

## Transitional Rule

Existing deploy capabilities remain at their current paths during adoption.
The lifecycle map is an index and placement rule for new work, not blanket
permission to rename existing scripts, PostgreSQL controls, or AWS workflows.

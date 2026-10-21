<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.lifecycle-stage-ownership
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-21"
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

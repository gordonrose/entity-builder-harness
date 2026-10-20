<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.lifecycle.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.lifecycle
disciplines:
- agentic
- architecture
- sre
kind: documentation
purpose: Map provider-neutral deployment capabilities to their primary software delivery lifecycle phase.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.layer.readme
  path: .agentic/04.deploy/README.md
- id: deploy.standards.lifecycle-stage-ownership
  path: .agentic/04.deploy/standards/lifecycle-stage-ownership.md
-->
# Deployment Lifecycle Map

This map gives each deployment capability one primary lifecycle home. It does
not move existing capabilities or change their authority. Existing paths remain
canonical until a separately governed migration moves them.

| Phase | Primary purpose | Future script home |
| --- | --- | --- |
| `00-target-alignment` | Select the intended target and compare declared local requirements with safe target facts before implementation. | `scripts/04.deploy/lifecycle/00-target-alignment/` |
| `10-development` | Establish controlled local runtime and configuration conditions for deployable work. | `scripts/04.deploy/lifecycle/10-development/` |
| `20-build` | Compile, typecheck, assemble runtime payloads, and run build-owned validation. | `scripts/04.deploy/lifecycle/20-build/` |
| `30-test` | Run deterministic unit, integration, and component tests outside the final package. | `scripts/04.deploy/lifecycle/30-test/` |
| `40-package` | Build, scan, attest, and locally exercise a releasable package or container image. | `scripts/04.deploy/lifecycle/40-package/` |
| `50-deploy` | Reconcile target readiness, review change shape, and perform an approved target mutation. | `scripts/04.deploy/lifecycle/50-deploy/` |
| `60-run` | Verify deployed health and behaviour, monitoring, recovery, and operational safety. | `scripts/04.deploy/lifecycle/60-run/` |

`smoke` and `preflight` are not primary phases. A smoke check belongs to the
phase whose artifact or live system it proves; a preflight belongs to the phase
immediately before the action it protects. Target Alignment is separately
numbered because it occurs before development begins.

The first capabilities in `00-target-alignment` are Declaration Coverage and
Target Alignment Preflight. Declaration Coverage proves that a scoped
requirement has a declaration and proof path before Target Alignment compares
that declaration with safe target facts. No established script moves as part of
this map.

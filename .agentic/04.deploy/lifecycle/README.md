<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.lifecycle.readme
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

| Phase | Primary purpose | Script home |
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
that declaration with safe target facts.

## Current Core-Server Route

| Phase | Authoritative instruction |
| --- | --- |
| `00-target-alignment` | [Declaration coverage](../workflows/declaration-coverage.md), then [compare declared requirements with live target](../00-target-alignment/workflows/compare-declared-requirements-with-live-target.md) |
| `20-build` | [Prove runnable program builds](../20-build/workflows/prove-runnable-program-builds.md) |
| `40-package` | [Publish immutable package with custody](../40-package/workflows/publish-immutable-package-with-custody.md) |
| `50-deploy` | [Review and execute target update](../50-deploy/workflows/review-and-execute-target-update.md) |
| `60-run` | [Verify, accept or restore release](../60-run/workflows/verify-accept-or-restore-release.md) and [retain the accepted release](../60-run/standards/retain-accepted-release-for-restoration.md) |

The [fixed AWS bootstrap-runtime procedure](../../aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md)
binds these instructions to existing commands. It covers an already-established
foundation and accepted runtime. The recorded initial creation and A-to-B-to-A
rehearsal are evidence; they are not standing permission to recreate resources
or expand the dependency-free bootstrap boundary.

The [implementation programme](../plans/implementation/platform-to-target-chain-control.md)
tracks further scope work. Its planned persistence foundation is not yet an
approved provider/resource choice for this target.

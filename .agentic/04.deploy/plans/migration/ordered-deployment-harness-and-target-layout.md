<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.ordered-deployment-harness-and-target-layout
version: 1
status: draft
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: migration
disciplines:
- agentic
- architecture
- sre
kind: migration-plan
purpose: Safely make deployment target declarations and target-specific harness routes readable by lifecycle purpose, action, target, and scope without duplicating generic authority.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: harness.workflows.change-harness
  path: .agentic/01.harness/workflows/change-harness.md
- id: deploy.lifecycle.readme
  path: .agentic/04.deploy/lifecycle/README.md
-->
# Ordered Deployment Harness and Target Layout Migration

## Decision

Make deployment paths readable as a sentence:

```text
folder = when or where it is used
file name = what it does
target and scope = what it affects
```

The migration must improve scanability without creating competing sources of
truth. Generic provider-neutral rules remain singular under `.agentic/04.deploy`.
Only target-specific procedures mirror the target and scope layout. AWS-specific
execution authority remains under `.agentic/aws/` until the existing
AWS-to-provider-neutral transition advances.

## Why This Is Needed

The currently proven `kanbien-core-platform` release path has valid controls,
but the current folders lead with artifact type (`workflows`, `standards`,
`schemas`) and several generic filenames use internal vocabulary. A reader
cannot reliably infer either when an instruction applies or what it asks them to
do.

The target definition also groups scope declaration, workload binding,
alignment, and release evidence together. That preserves scope ownership, but
does not show their distinct roles in the release chain at a glance.

## Non-Goals and Protected Work

This is a repository-only migration. It must not:

- mutate AWS, GitHub Environment configuration, ECR, ECS, CloudFormation, or
  cost settings;
- alter accepted release A, its immutable image identity, or rehearsal
  evidence;
- broaden the `bootstrap-runtime` scope to persistence, identity, queues,
  public ingress, or observability delivery;
- move active AWS execution authority from `.agentic/aws/`;
- rewrite `commitLogs/`, generated historical coverage records, or prior plans
  merely to modernise their path references;
- move PostgreSQL Stage 6 work or the existing `kanbien/staging` target.

## Canonical Target Layout

The target's top-level order is a conceptual map, not permission to run steps
out of order. The routed workflow remains the executable sequence.

```text
infra/04.deploy/03.product/targets/kanbien-core-platform/
  00-target/
    target-profile.yml
    README.md

  10-foundation/
    foundation-index.yml
    network.yml
    technical-access.yml
    cost-control.yml
    evidence/
    README.md

  20-scopes/
    bootstrap-runtime/
      00-declaration/
        declaration-contract.yml
        README.md
      10-workload-binding/
        workload-binding.yml
      20-alignment/
        runtime-alignment-contract.yml
      30-release-evidence/
        accepted-release.yml
        rehearsals/

  30-provider-realization/
    aws/cloudformation/
      foundation.yml
      bootstrap-runtime.yml
      tag-bootstrap.yml
      README.md

  40-package-custody/
    github-actions/
      pipeline-index.yml
      core-server-package-custody.delivery-access.yml
      README.md
```

The scope remains the owner of its declaration, binding, alignment, and release
evidence. The numbered child folders make their differing purposes visible
without turning each one into a separate anonymous top-level area.

## Canonical Harness Layout

Provider-neutral harness material becomes lifecycle-first. A phase says when
the instruction is used; a plainly named file says what it does.

```text
.agentic/04.deploy/
  00-target-alignment/
    workflows/
      compare-declared-requirements-with-live-target.md
    standards/
      require-fresh-safe-target-evidence.md
    schemas/
      target-alignment-contract.v1.schema.yml

  20-build/
    workflows/
      prove-runnable-program-builds.md

  40-package/
    workflows/
      qualify-runnable-program-for-packaging.md
      publish-immutable-package-with-custody.md
    standards/
      require-immutable-package-identity.md
    schemas/
      package-custody-receipt.v1.schema.yml

  50-deploy/
    workflows/
      review-and-execute-target-update.md
    standards/
      require-reviewed-bounded-provider-change.md

  60-run/
    workflows/
      verify-live-release.md
      restore-and-verify-accepted-release.md
    standards/
      retain-accepted-release-for-restoration.md

  plans/
    implementation/
    migration/
    execution/
```

This is a target-state goal, not permission to create empty phase folders or
duplicate every existing rule. Existing artifacts move only when their primary
lifecycle phase and new clear action name are established in the reference
inventory below.

Target-bound AWS workflows mirror the relevant target and scope while keeping
their provider authority separate:

```text
.agentic/aws/
  50-deploy/workflows/targets/kanbien-core-platform/
    20-scopes/bootstrap-runtime/
      review-and-execute-ecs-runtime-update.md

  60-run/workflows/targets/kanbien-core-platform/
    20-scopes/bootstrap-runtime/
      privately-verify-release.md
      restore-accepted-release.md
```

If a target-specific AWS procedure spans deploy and run, it may remain one
routed workflow during the transition only when it has explicit sections for
both phases. It must not be copied into both homes.

## Script Boundary

Scripts remain lifecycle-first because that is how commands are invoked:

```text
scripts/04.deploy/lifecycle/
  40-package/targets/kanbien-core-platform/
  50-deploy/targets/kanbien-core-platform/bootstrap-runtime/
  60-run/targets/kanbien-core-platform/bootstrap-runtime/
```

The matching target/scope suffix and `agentic-artifact` references provide the
link to the target declaration. Scripts do not move merely to imitate the
infrastructure tree.

## Authority Rules

- A generic workflow, standard, or schema is authoritative once only. Do not
  copy it per target.
- A target-specific AWS workflow names the matching target and scope in its
  path and points to the generic provider-neutral workflow it instantiates.
- Infrastructure declarations name the governing workflow and executable
  checks through stable metadata references.
- A workflow names the infra declaration and script it governs through its
  metadata references.
- README files explain the tree but do not introduce additional mandatory
  procedure.

## Initial Old-to-New Map

| Current path | Proposed canonical path | Disposition |
| --- | --- | --- |
| `targets/kanbien-core-platform/target-profile.yml` | `targets/kanbien-core-platform/00-target/target-profile.yml` | retired after consumers update |
| `targets/kanbien-core-platform/foundation/` | `targets/kanbien-core-platform/10-foundation/` | retired after consumers update |
| `targets/kanbien-core-platform/scopes/bootstrap-runtime/declaration-contract.yml` | `targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml` | retired after consumers update |
| `targets/kanbien-core-platform/scopes/bootstrap-runtime/workload-binding.yml` | `targets/kanbien-core-platform/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml` | retired after consumers update |
| `targets/kanbien-core-platform/scopes/bootstrap-runtime/runtime-alignment-contract.yml` | `targets/kanbien-core-platform/20-scopes/bootstrap-runtime/20-alignment/runtime-alignment-contract.yml` | retired after consumers update |
| `targets/kanbien-core-platform/scopes/bootstrap-runtime/accepted-release.yml` | `targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml` | retired after consumers update |
| `targets/kanbien-core-platform/scopes/bootstrap-runtime/rehearsals/` | `targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/rehearsals/` | retired after consumers update |
| `targets/kanbien-core-platform/cloudformation/` | `targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/` | retired after consumers update |
| `targets/kanbien-core-platform/pipelines/` | `targets/kanbien-core-platform/40-package-custody/` | retired after consumers update |

The target root itself is not moved. That avoids changing its identity, GitHub
workflow references, or historical target name.

## Harness Rename Map To Be Confirmed by Inventory

The generic files will not all move in one batch. Their proposed action names
are reviewed one by one against their true primary lifecycle phase:

| Current artifact | Candidate action name and phase | Status |
| --- | --- | --- |
| `workflows/target-alignment-preflight.md` | `00-target-alignment/workflows/compare-declared-requirements-with-live-target.md` | first batch candidate |
| `standards/target-alignment-preflight.md` | `00-target-alignment/standards/require-fresh-safe-target-evidence.md` | first batch candidate |
| `workflows/runnable-program-candidates.md` | `20-build/workflows/prove-runnable-program-builds.md` | requires contract-consumer review |
| `standards/runnable-program-candidates.md` | `20-build/standards/require-runnable-program-contract.md` | requires contract-consumer review |
| `workflows/package-custody-and-promotion.md` | `40-package/workflows/publish-immutable-package-with-custody.md` | requires pipeline-consumer review |
| `standards/package-custody-and-promotion.md` | `40-package/standards/require-immutable-package-custody.md` | requires pipeline-consumer review |
| `workflows/release-update-and-recovery.md` | split only if controls remain singular: `50-deploy/workflows/review-and-execute-target-update.md` and `60-run/workflows/restore-and-verify-accepted-release.md` | design decision after consumer review |
| `standards/accepted-release-and-recovery.md` | `60-run/standards/retain-accepted-release-for-restoration.md` | requires recovery-consumer review |
| `.agentic/aws/workflows/kanbien-core-platform-bootstrap-runtime-release.md` | AWS target/scope route described above | provider-specific first batch candidate |

## Reference Inventory and Compatibility

The initial planner run found 236 references to the current
`kanbien-core-platform` target path. Active references include:

- target declaration checkers and release-control scripts;
- target smoke tests and fixture path copies;
- the protected GitHub Actions package workflow;
- provider-neutral schemas and standards that cite a target declaration;
- the AWS target release workflow;
- generated RAG recognition sources.

Historical coverage reports and `commitLogs/` references are audit history and
remain unchanged. Active target paths have no alias or wrapper because YAML
contracts must have one canonical source. Human README pointers may be retained
only if an active human-facing external link requires them.

Before each move, run:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh <old> <new>
```

After all active references in that batch are updated, run:

```bash
bash scripts/01.harness/check-artifact-path-migration.sh \
  --plan .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md \
  <old> <new>
```

## Ordered Batches

<!-- deterministic-check: allow reason="This is a migration sequence whose batch boundaries require human review of active consumers; named scripts own the deterministic checks within each batch." -->
1. **Plan, naming standard, and validator** — this artifact, the placement and
   naming standard, a proposed-path validator with regression fixtures, and
   exact reference manifests. No active path mutation.
2. **Target declaration migration** — move the target declarations and update
   static checkers, scripts, fixtures, GitHub workflow metadata, READMEs, and
   generated recognition sources together. Run all declaration and release
   control smoke tests.
<!-- deterministic-check: allow reason="The AWS workflow move is conditional on the outcome of the preceding target-declaration consumer migration; its documentation and metadata checks are named by that reviewed batch." -->
3. **AWS target workflow migration** — rehome only the core-platform AWS
   workflow to its target/scope path, update provider-neutral references, and
   run its documentation and metadata checks. No AWS action.
4. **Generic harness first batch** — migrate target alignment artifacts after
   all consumers and lifecycle ownership are reviewed.
5. **Generic harness later batches** — migrate runnable-program, package,
   deploy, and run artifacts one cohesive capability at a time. Do not split a
   workflow merely to satisfy a folder name.
6. **Retirement** — retire old active paths only after migration checks show no
   active references and generated indexes are current.

## Required Validation Per Batch

- `git diff --check`;
- artifact metadata header check;
- migration-plan checker for every moved path;
- affected target declaration checker;
- `scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh`;
- affected package and release contract smoke tests;
- generated recognition-source check and validation when paths change;
- no cloud-mutating command and no unplanned GitHub Actions dispatch.

## Recovery

Each batch is a separate commit. If a migration breaks a consumer, restore the
previous path mapping by reverting only that batch; do not alter the accepted
release or invoke a provider operation. The existing accepted release and live
target remain independent of this repository-only path migration.

## ADR Disposition

No new ADR is required for this first planning artifact. The later approved
canonical provider-neutral layout and any public compatibility promise will
require an ADR before the first active generic harness move.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.scripts.readme
version: 18
status: active
created_on: "2026-06-26"
updated_on: "2026-11-26"
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Index deploy-layer executable checks and helpers.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.script.verify-rag-rulebook-deploy-readiness
  path: scripts/04.deploy/legacy/rag-rulebook/verify-rag-rulebook-deploy-readiness/script.sh
- id: deploy.script.verify-platform-shell-deploy-readiness
  path: scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-deploy-readiness/script.sh
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
-->
# Deploy Scripts

Use this folder when checking a candidate, building its package, deploying it,
or checking an already deployed runtime. Those are different jobs: a local
source check does not prove a built image or a live service works. The owning
workflow chooses which commands are needed; this index does not run them all.

## Start with active core-platform work

The current target is `kanbien-core-platform`. Use its existing lifecycle
homes; do not search the retained platform-shell notes below for a core change.

| Your task | Current home | What belongs there |
| --- | --- | --- |
| Check the target declaration and alignment | [00-target-alignment](lifecycle/00-target-alignment/) | Declared requirements and explicitly authorised provider observations; not an automatic deployment. |
| Compile and qualify source locally | [20-build](lifecycle/20-build/) | Runnable-program contracts, composition tests and shared qualification; no cloud work. |
| Assemble, qualify and publish a package | [40-package](lifecycle/40-package/) | Image/payload construction and immutable package custody; publication keeps its own authority. |
| Review and apply an approved target change | [50-deploy core target](lifecycle/50-deploy/targets/kanbien-core-platform/) | Foundation, bootstrap and persistence change preparation/execution. Entity orchestration currently remains in its existing runtime owner, not a second deploy engine. |
| Verify, accept or recover a runtime | [60-run core target](lifecycle/60-run/targets/kanbien-core-platform/) | Bootstrap, persistence and Entity Smoke runtime operations; local source tests remain distinct from live proof. |

For example, an Entity Smoke source change begins at
[its local composition owner](lifecycle/20-build/entity-smoke-composition/).
Its [runtime owner](lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/)
consumes qualified evidence for a separately authorised operation; it does not
need to repeat the whole local suite merely because it is about to use it.

Use the current paths linked here. The
[lifecycle placement standard](../../.agentic/04.deploy/standards/lifecycle-stage-ownership.md)
and [current simplification plan](../../.agentic/shared/plans/implementation/script-library-simplification.md)
own new work and migration. The [P4 source audit](../helpers/audit.md#p4-current-disposition-and-proposed-folder-manifest--2026-11-25)
accounts for all 471 deployment source files. The approved relocation is now
locally implemented: 76 Entity sources occupy capability subfolders within the
same runtime owner, 95 staging sources occupy `legacy/kanbien-staging/`, and two
RAG readiness sources occupy `legacy/rag-rulebook/`. The 31 associated Markdown
companions moved with their legacy families. No deployment source was added or
retired. The programme records qualification and publication evidence; a new
folder does not establish current runtime health or authorize an operation.

The shared import inspector and its fixture now belong to
`scripts/repo/module-structure/`; workspace input selection and its fixture
belong to `scripts/repo/check-selection/`. These helper moves do not change the
deployment-source count.

### Existing active command notes

- `lifecycle/20-build/core-server-persistence-composition/`: compile-once local
  fixtures use independent copied payloads; fast isolation tests cover ordering,
  repetition and failure cleanup without repeating unrelated TLS proofs.

- `lifecycle/00-target-alignment/core-platform-target-declaration/`:
  report-only static coverage check for the planned `kanbien-core-platform`
  target. It proves repository-declaration completeness only and rejects a
  missing, replaced, unowned, or falsely live-ready E0 fact; it does not read
  AWS, GitHub, Docker, credentials, or secrets.

- `lifecycle/20-build/core-server-dependency-boundary/`: local-only report of
  the declared Kanbien core-server compile graph, derived from TypeScript
  imports, workspace manifests, lockfile records, and temporary build output;
  it rejects product, persistence, worker, relay, PostgreSQL, staging-server,
  and AWS-adapter dependencies before packaging.

- `lifecycle/20-build/runnable-program-contract/`: report-only validation of a
  provider-neutral runnable-program, image-command, dependency-boundary, and
  safe-evidence declaration before package construction.

- `lifecycle/40-package/build-core-server-image/`: reuses the declared
  core-server program proof, inspects the compiled payload, then builds a
  local-only dedicated candidate image when Docker is available.

- `lifecycle/40-package/smoke-test-core-server-image/`: proves a forbidden
  payload injection fails closed and, with Docker available, checks the local
  core-server image's liveness, readiness, and safe release-verification
  response.

## Shared controls and helpers

These are used by core-platform work and, in some cases, retained staging too.
A staging caller does not make a shared capability legacy.

- `inventory-deploy-control/`: read-only census of deploy scripts and
  infrastructure files, their callers, declared effects, and catalogue gaps.

- `validate-container-boundaries/`: read-only Dockerfile and container image
  placement validation so deployable images stay under governed `infra/**`
  image directories.

- [operational-realization-gate/](operational-realization-gate/) checks the
  declared operation graph and supplied evidence against its contract. It does
  not acquire fresh provider evidence or authorise cloud changes.

- [shared/](shared/) owns common provider/diagnostic/PostgreSQL/package helpers.
  The [source audit](../helpers/audit.md) identifies real consumers and mixed
  proof dependencies; capability-specific helpers stay with their own owners.

## Retained staging — not the default core working surface

The following commands belong to `kanbien/staging` platform shell, not the
active core target. They are retained, not retired: three staging workflows
still run every four hours. Their scripts now live under
[`legacy/kanbien-staging/`](legacy/kanbien-staging/); package aliases and workflow
callers use that canonical home. Schedules and provider permissions are unchanged.
Shared recovery and
package tests still exercise some staging code; removing that coupling is
recorded work, not an accomplished consequence of this index.

Commands must refuse unsafe deployment execution and must not mutate cloud
state without their owning workflow's explicit authority. These are selected
existing command notes, not an instruction to run the whole retained library.

- `legacy/kanbien-staging/verify-platform-shell-infrastructure/`: catalog-owned aggregate of the
  unchanged static policy in `policy.sh` and its existing child
  verifier/smoke boundaries. Child identity and stage rules govern reuse.

- `legacy/kanbien-staging/build-platform-shell-image/`: local-only Docker image build wrapper for the
  provider-neutral platform shell.

- `legacy/kanbien-staging/smoke-test-platform-shell-image/`: local-only image smoke test for platform
  shell `/livez` and `/readyz`.

- `legacy/kanbien-staging/run-platform-shell-controlled-smoke/`: locally validates, or with explicit
  target approval performs, one fixed protected staging request using an
  in-memory Cognito token and redacted status-only output.

- `legacy/kanbien-staging/provision-platform-shell-negative-authz-client/`: locally validates, or
  with explicit current-chat approval creates the one separately scoped Cognito
  machine client and its named secret for the bounded staging `403` proof.

- `legacy/kanbien-staging/run-platform-shell-negative-authz-smoke/`: locally validates, or after
  post-deployment inspection and explicit current-chat approval performs the
  one fixed valid-token, unmapped-scope staging request that must return `403`.

- `legacy/kanbien-staging/provision-platform-shell-persistence-write-client/`: locally validates, or
  with explicit current-chat approval adds the one reviewed `smoke.write`
  scope, separate confidential machine client, and target-owned secret used
  only by the bounded persistence proof.

- `legacy/kanbien-staging/run-platform-shell-persistence-smoke/`: locally validates, or after the
  reviewed target deployment and explicit current-chat approval makes exactly
  one fixed no-body work-item acceptance request with the separate write-only
  identity. It emits only a safe verdict, status, and duration.

- `legacy/kanbien-staging/run-platform-shell-rate-limit-smoke/`: locally validates, or after current
  approval waits for a fresh fixed window, performs at most the configured
  liveness rate-limit plus one sequential public request, and records
  aggregate-only `429` evidence or an explicit rollover-inconclusive result.

- `legacy/kanbien-staging/run-platform-shell-ingress-smoke/`: locally validates, or after current
  approval performs fixed read-only WAF, listener, and security-group
  inspections plus one public liveness request.

- `legacy/kanbien-staging/run-platform-shell-persistence-admission-probe/`: locally validates, or
  after the reviewed deployment performs exactly one no-body authenticated
  request to the dedicated server-admission route. It is not a persistence
  write: the route returns `204` without invoking the repository, transaction,
  DynamoDB, outbox, SQS, relay, or worker.

- `legacy/kanbien-staging/run-platform-shell-worker-smoke/`: locally validates, or after explicit
  current approval sends exactly two side-effect-free queue messages 75 seconds
  apart, starts only the dormant worker service, observes bounded settlement,
  then always returns it to desired count zero. It proves a consumer boundary
  and a fresh-counter metric observation, not an outbox.

- `legacy/kanbien-staging/run-platform-shell-metric-coverage/`: locally validates, or in a governed
  read-only operation queries only the fixed server coverage/SLO policy or the
  separately fixed worker delivery-counter observation policy. It never accepts
  a caller-supplied metric, label set, query, or alert destination.

- `legacy/kanbien-staging/verify-platform-shell-synthetic-scheduler/`: read-only policy check for the
  temporary GitHub Actions protected-route synthetic workflow and its separate
  one-secret-read IAM role source.

- `legacy/kanbien-staging/verify-platform-shell-deployment-artifact-store/`: read-only policy check
  for the private, encrypted, short-retention S3 store used only when a
  reviewed CloudFormation template is too large for AWS's inline request limit.

- `legacy/kanbien-staging/reconcile-platform-shell-staging/`: fail-closed local and live target
  reconciliation. It verifies declared stack summaries and fresh passive drift
  evidence, artifact-store, and budget controls without provisioning resources;
  its pre-change-set mode also
  requires exactly the reviewed Foundation resource-change scope.

- `legacy/kanbien-staging/verify-platform-shell-deployment-reconciliation/`: static policy check for
  reconciliation source, its dedicated read-only GitHub identity, and the
  validation-before-credentials scheduled workflow.

- `legacy/kanbien-staging/verify-platform-shell-drift-detection-boundary/`: fast source-only check
  that keeps GitHub passive and requires every target CloudFormation resource
  type to have a detector permission-analysis entry before a detector role can
  be designed.

- `legacy/kanbien-staging/verify-platform-shell-deploy-readiness/`: read-only manifest validation for
  product platform shell deployment readiness, including explicit blocker
  coverage for planning-only evidence.

- `legacy/kanbien-staging/verify-platform-shell-deployment-workflow/`: read-only supply-chain gate
  that makes the staging workflow scan, create an SPDX SBOM, and attest the
  immutable image before it can deploy the service stack.

## Dormant RAG / rulebook

The main retained library already has its own home at
[02.rag-rulebook](../02.rag-rulebook/). Its hosted deployment workflow is
disabled. Its two retained deployment-readiness source files now live under
[`legacy/rag-rulebook/`](legacy/rag-rulebook/). No corpus regeneration or hosted
RAG activation was performed.
Keep this explicit maintenance separate from ordinary core-platform work.

- `legacy/rag-rulebook/verify-rag-rulebook-deploy-readiness/`: read-only manifest validation for
  RAG/rulebook GitHub-to-AWS deployment readiness.

<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: aws.plan.kanbien-core-platform-release-rehearsal
  version: 2
  status: draft
  created_on: "2026-10-19"
  updated_on: "2026-10-20"
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - architecture
  - security
  - sre
  kind: deployment-change-plan
  purpose: Define the review-only, bounded rehearsal that creates an isolated Kanbien core platform target, proves release A, then proves one safe update to release B.
  portability:
    class: internal
    targets: []
  used_by:
  - id: aws.workflows.plan-aws-change
    path: .agentic/aws/workflows/plan-aws-change.md
  - id: aws.workflows.execute-approved-aws-change
    path: .agentic/aws/workflows/execute-approved-aws-change.md
  - id: deploy.plan.implementation.platform-to-target-chain-control
    path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md
-->
# Kanbien Core Platform: Release Rehearsal Plan

## Status and authority

This is a **review-only AWS change plan**. It authorises no implementation,
GitHub action, image publication, target creation, AWS mutation, secret read,
or deployment. It prepares the bounded approval packet required by
`.agentic/aws/workflows/plan-aws-change.md` and
`.agentic/aws/workflows/execute-approved-aws-change.md`.

The generic rules for how an agent creates and checks runnable programs,
images, candidate releases, and safe evidence remain under `.agentic`. This
document is deliberately target-specific: it explains the proposed rehearsal
for `kanbien-core-platform` and must not become a generic instruction source.

## Objective

Prove that the repository can safely complete one real image-update cycle for
a new, deliberately isolated target:

```text
absent target
  → create and verify immutable release A
  → retain A as the accepted rollback baseline
  → build one harmless release B update
  → deploy and verify B
  → record safe evidence that B, rather than A, is running
```

The rehearsal succeeds only when the same immutable image digest is locally
qualified, published, selected by the workload, and independently confirmed by
live verification. A successful build or a successful CloudFormation request
alone is not success.

## Fixed safety boundary

| Included | Explicitly excluded |
| --- | --- |
| New `kanbien-core-platform` target and its bootstrap HTTP server | Any change to `kanbien/staging`, its services, data stores, roles, pipelines, or DNS |
| Private server, private internal verifier path, image custody, release A and release B | Public ingress, public DNS, end-user login, Cognito, product applications, queues, worker, relay, DynamoDB, PostgreSQL, or any data migration |
| One dedicated core-server image and candidate receipt | Reuse of staging resources unless a separately reviewed isolation decision expressly permits one named resource |
| A single rollback from a failed B attempt back to accepted A | Automatic retries, automatic repair, repeated deployment loops, or deletion of the new target |

The bootstrap server has no application-service runtime permission. It needs
only the narrow AWS startup and operational access that the selected runtime
requires. It must not acquire database, queue, identity-provider, or public
ingress access merely because those exist elsewhere in the repository.

## Facts that must be confirmed before execution

These are intentionally blank rather than inherited from staging:

| Required fact | Current status | Required evidence before mutation |
| --- | --- | --- |
| AWS account/profile | Unselected | `sts:GetCallerIdentity` using the proposed execution profile |
| Region | Unselected | The named regional deployment plan and service availability check |
| Runtime family | Unselected | Reviewed choice; ECS Fargate is a candidate, not an assumption |
| Network model | Unselected | Private-route design, subnet and egress/endpoints analysis, and verifier reachability design |
| ECR repository | Absent | Dedicated repository, or named shared repository with an isolation decision |
| Delivery identity | Absent | Least-privilege GitHub OIDC trust and policy source, restricted to this repository, branch, and workflow |
| Verifier execution location | Unselected | A design that can reach the private route without exposing the server publicly |
| Cost and cleanup ownership | Unselected | Owner, expected recurring cost, budget/alert treatment, and explicit retirement plan |

If any fact conflicts with the plan or needs an unreviewed permission, the
rehearsal stops. An agent must not borrow staging settings as a shortcut.

## Proposed verification shape to review

A GitHub-hosted runner cannot directly call a private workload route. The
default design to review is therefore a narrowly scoped, one-pass verifier
workload inside the selected private network:

```text
GitHub Actions
  → asks AWS to run the approved one-pass verifier
  → verifier reaches only the core server's internal verification route
  → verifier returns a redacted verdict
  → GitHub Actions writes the candidate receipt
```

The verifier is not an application capability and does not become public. Its
route is owned by the bootstrap-runtime scope. The target-design package must
still select its runtime, task/startup access, network rule, output route, time
limit, cleanup behaviour, and least-privilege policy before it can exist.

The live acceptance decision joins three facts:

```text
workload evidence       → actual immutable image digest selected by AWS
server verification     → safe release/build identity reported by the reached process
package-custody record  → source commit, local qualification, scan, and published digest
```

## Repository work packages

Each package is independently reviewable, committed, and locally checked. No
package creates an AWS resource unless it is explicitly the approved target
creation package later in this plan.

### R1 — Generic governance and report fixtures

Create provider-neutral `.agentic` artifacts for runnable-program changes,
image contracts, package candidates, candidate verification, safe diagnostics,
and their report-only fixtures. They must govern a class of change, not name
Kanbien, AWS, or this target.

**Pass condition:** a fixture proves a missing program record, invalid image
command, unapproved dependency, or unsafe evidence field fails closed with a
safe diagnostic.

### R2 — Clean generic dependency boundary

Move persistence-specific observability integration into
`platform/persistence/src/observability/`. Generic `platform/observability`
must no longer select `platform/persistence`.

Add the planned generic `platform/server/src/configuration/` and
`platform/server/src/verification/` surfaces only where their source, tests,
and public exports are reviewed together.

**Pass condition:** generic observability and the core-server candidate graph
do not include persistence; persistence retains and tests its optional
observability integration.

### R3 — Runnable program and build-owned boundary proof

Add `kanbien-core-server.main.ts` and its factual entry in the runnable-program
registry. It must reuse generic server lifecycle and transport rather than
copying them, select no product app or provider adapter, and expose only the
approved safe release-verification operation.

Add the report-only dependency-boundary capability at:

```text
scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/
```

It derives the actual graph from the program root, TypeScript imports, package
manifests, lockfile, and build output. It also names forbidden roots: staging
server, product app, persistence, worker, relay, PostgreSQL, and provider
adapters.

**Pass condition:** the report identifies both the allowed graph and a fixture
that proves one forbidden dependency is rejected.

### R4 — Package the core image locally

Create the dedicated `infra/04.deploy/03.product/image/core-server/` image
contract and Dockerfile. Add lifecycle-owned package capabilities:

```text
scripts/04.deploy/lifecycle/40-package/build-core-server-image/
scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/
```

The image must have one declared command, non-root runtime user, approved
non-secret defaults, liveness/readiness checks, safe release identity, and a
payload check. It contains neither the broad platform-shell entrypoint nor
unselected code merely because that code is present in the monorepo.

**Pass condition:** a locally built image starts, reports health and safe
release identity, and fails its payload checker when a forbidden program is
introduced.

### R5 — Describe the target and delivery route

Only after R1–R4 are reviewed and merged, add the factual target declaration:

```text
infra/04.deploy/03.product/targets/kanbien-core-platform/
  target-profile.yml
  foundation/
  scopes/bootstrap-runtime/
  pipelines/github-actions/
```

It declares the absent baseline, configuration-name shape, technical access,
private verifier route, release receipt, rollback target, and explicitly
deferred concerns. It also contains the provider declaration or links to its
authoritative AWS CloudFormation source. A new GitHub workflow may build,
scan, attest, and publish the dedicated image, but must not deploy by accident.

**Pass condition:** static target/declaration checks find no unowned required
fact and no dependency, permission, or public route omitted from the declared
scope.

### R6 — Add controlled target mutation and live verification

Add the two distinct capabilities:

```text
scripts/04.deploy/lifecycle/50-deploy/targets/
  kanbien-core-platform/bootstrap-runtime/
    prepare-candidate/
    deploy-candidate/

scripts/04.deploy/lifecycle/60-run/targets/
  kanbien-core-platform/bootstrap-runtime/
    verify-candidate/
```

Preparation obtains fresh, read-only alignment evidence. Deployment performs
only the reviewed target change. Run verification joins the workload digest,
server identity, and package custody record, then writes a safe GitHub Actions
receipt. None may repair drift or launch another deployment automatically.

**Pass condition:** static fixtures prove stale alignment, mismatched digest,
missing receipt fields, and unsafe output fail closed.

### Script placement and target binding

Every executable capability has one primary lifecycle home and one explicit
applicability declaration. The primary home says *when* it is used. The
applicability declaration says *what it is allowed to act on*.

Build and package capabilities are deliberately target-neutral:

```text
20-build/core-server-dependency-boundary/
40-package/build-core-server-image/
40-package/smoke-test-core-server-image/
```

They prove the selected runnable program and image without AWS credentials or
a target choice. They may name the program and image contract, but not an AWS
account, region, resource, or target.

Deploy and run capabilities are target-bound because they inspect or act on a
real destination. They use the target/scope nesting shown in R6 and must state
at least:

```text
lifecycle_stage: 50-deploy or 60-run
target: kanbien-core-platform
scope: bootstrap-runtime
effect: read-only or aws-mutation
authority: the named workflow, declaration, and approved change set
```

A target-bound script takes no free-form target selector. It resolves only its
declared target record. A generic helper may be reused internally, but it is
not itself an operator entrypoint and may not turn a staging script into a
core-platform script by accepting a different flag.

## AWS execution sequence

The following steps occur only after R1–R6 are merged to the branch consumed
by the selected delivery workflow and a separate current-chat execution
approval names the exact account/profile, region, templates, stack names,
roles, images, and rollback path.

| Gate | Operation | Evidence required to continue | Stop / recovery |
| --- | --- | --- | --- |
| E0 | Read-only target inspection | account, region, naming availability, current resource conflicts, quotas, network feasibility, and cost guard | Any ambiguity, unsuitable network route, or overlap with staging stops planning |
| E1 | Review target-foundation change set | Exact additions only; no replacement, deletion, public ingress, or staging resource | Reject/revise the change set; do not execute |
| E2 | Create foundation | E1-approved change set, then safe stack and role outputs | If creation fails, stop with safe evidence; no automatic retry or cleanup |
| E3 | Publish release A | local qualification, scan/SBOM/attestation result, immutable digest, package-custody record | No digest or failed qualification means no deployment |
| E4 | Deploy release A | fresh alignment, reviewed service change set selecting A's digest, accepted rollback state `absent` | If deployment fails, stop; the target remains absent or incomplete, never silently treated as baseline |
| E5 | Verify and accept A | workload digest A, safe server identity A, controlled private verifier verdict, receipt | If any disagree, reject A and stop; do not start B |
| E6 | Publish and deploy release B | one reviewed harmless source change, new locally tested digest B, fresh alignment, service change set | If B fails after service mutation, one explicit rollback to A may be executed |
| E7 | Verify and accept B | workload digest B, safe server identity B, custody B, receipt, and A retained as rollback baseline | If verification fails, roll back once to A, verify A, and stop |

No intentional broken deployment is required for this first rehearsal. We test
rollback readiness by retaining A, proving it remains selectable, and defining
the exact single rollback command/change set. A deliberate failure-and-rollback
exercise is a separate later rehearsal because it changes a healthy live
workload on purpose.

## Release A and B content

Release A is the first minimal core image. It includes only the generic server
and its approved safe verification operation. It does not introduce a product
feature or external dependency.

Release B is one deliberately harmless source change to the safe release
metadata format or declared release marker. It must change the image digest and
be visible to the controlled verifier while preserving liveness, readiness,
and the meaning of the verification operation. It may not be a configuration
only change, tag-only republish, or a change that adds an otherwise excluded
capability.

## Candidate receipt and retained evidence

The initial receipt is a machine-readable GitHub Actions artifact plus a
human-readable job summary. It contains only safe fields:

- target identifier, environment class, and provider region/account alias;
- program and image-contract identifiers;
- source commit and immutable image digest;
- timestamps and check verdicts;
- safe diagnostic code and bounded next action on failure; and
- receipt/run reference and accepted rollback digest.

It never contains secret values, tokens, headers, full URLs, connection
strings, raw provider responses, personal data, private endpoint details, or
application request payloads.

## Approval packet required before AWS execution

Before any sub-agent may mutate AWS, the user must approve a packet containing:

1. target `kanbien-core-platform`, exact AWS account/profile, and exact region;
2. the approved runtime, network, ECR, verifier, logging, and cost decisions;
3. every CloudFormation template and reviewed change set, including resource
   additions and policy diff;
4. the GitHub workflow filename, branch/ref, OIDC role, and immutable release
   A digest;
5. the release A and release B source commits/digests and exact verification
   commands; and
6. the rollback command/change set, one-retry limit, owner, and stop
   conditions.

That approval gives a sub-agent a bounded job. It does not permit it to widen
permissions, substitute a shared resource, read secrets, modify staging,
delete resources, or improvise a recovery path.

## Completion and handoff

The rehearsal is complete only if B is accepted and the receipt proves the
three-way identity match. The handoff records the accepted B digest, retained A
rollback digest, target/stack identifiers, safe receipt references, known
deferred concerns, cost/ownership review, and any work needed before the next
scope—persistence, security, fuller observability, or product capability—is
started.

Otherwise it stops in its last safe state and reports the failed gate, safe
evidence reference, and bounded next decision. It does not claim the target
is aligned, production-ready, or a general platform foundation merely because
one bootstrap-server rehearsal succeeded.

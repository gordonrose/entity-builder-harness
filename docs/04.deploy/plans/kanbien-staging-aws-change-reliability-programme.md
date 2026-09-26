<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.kanbien-staging-aws-change-reliability-programme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- security
- sre
kind: implementation-plan
purpose: Eliminate preventable Kanbien staging AWS deployment and reconciliation failures through explicit dependency contracts and identity-specific proof.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.architecture.adr.0036-separate-active-drift-detection-from-github-reconciliation
  path: docs/04.deploy/adrs/0036-separate-active-drift-detection-from-github-reconciliation.md
-->
# Kanbien Staging AWS Change Reliability Programme

## Objective

Make an AWS change predictable before it reaches a live mutation: the source
declares the exact dependency boundary, a focused check validates that boundary
quickly, the identity that will operate it proves its own safe operations, and
only then does the full repository suite run.

This programme fixes the specific failure mode where an administrator could
perform CloudFormation drift detection but the narrow GitHub OIDC role could
not. It does not use administrator success or IAM simulation as proof for a
different operational identity.

## Current evidence and constraint

The GitHub reconciliation role successfully assumes its declared identity and
performs its scoped reads, but live active drift detection blocked because AWS
requires additional dependent provider reads. The repository has not broadened
that role. No new AWS service, detector role, cost, or target resource is
created by the source implementation in this plan.

## Stage 1 — implemented source guardrails

1. Keep GitHub reconciliation passive: exact `DescribeStacks` evidence,
   artifact-store controls, budget, and caller identity only.
2. Remove active drift detection from the desired GitHub policy and prevent it
   returning through a static policy check.
3. Inventory every resource type in both target stacks. Validation fails if a
   resource type is added without an explicit provider-read-analysis entry.
4. Require fresh `IN_SYNC` stack-summary evidence as an interim, fail-closed
   pre-change guard. It is labelled as interim rather than continuous proof.
5. Require the administrator pre-change path to compare the live GitHub inline
   policy against its reviewed JSON source. This catches source/live IAM drift;
   the GitHub workflow separately proves the operations the role can actually run.
6. Add a small focused target check (`platform:shell:drift-detection-boundary:check`)
   to run during change development; run the full repository gate once after a
   completed slice.
7. Make every live provider operation independently attributable in the safe
   reconciliation result. A grouped control is not sufficient: when one
   declared read is unavailable, the result must name that exact control while
   continuing to suppress provider payloads.

## Stage 2 — detector design and review (not yet authorised to deploy)

1. For each inventory entry, record the authoritative AWS documentation,
   CloudFormation support, required provider read actions, exact resource scope
   or a documented unavoidable unscoped exception, and a safe probe.
2. Produce one separate detector-role policy and one trust policy. GitHub may
   never assume this role. The proposed workload is an EventBridge-scheduled,
   target-scoped Lambda because AWS Config is not a substitute for comparing a
   CloudFormation template with the live stack.
3. Estimate recurring cost for the scheduler, Lambda, logs, and any required
   event/alert path. The plan must state the monthly ceiling before deployment.
4. Create a reviewed CloudFormation change set only. Inspect IAM, tags, log
   retention, schedule, outputs, alarm routing, and rollback before execution.

## Stage 3 — controlled deployment and proof (requires a new explicit AWS approval)

1. Apply the narrowed GitHub reconciliation inline policy and prove the live
   GitHub workflow only uses its declared passive operations. This is a
   no-cost permission removal, separately recorded from the detector deployment.
   The live policy alignment proof has passed. The first identity-specific run
   then blocked at the grouped artifact-bucket read control, so the source now
   reports each artifact-bucket read separately before any permission change is
   considered. The next proof must identify the exact failed operation or pass
   all declared controls; IAM simulation alone is not treated as proof.
2. Execute the reviewed detector change set. It has a separate service role,
   a fixed stack allowlist, and no access to secrets, records, queue messages,
   or workload data.
3. Run one bounded active scan, verify a fresh safe result, and then prove the
   detector's failure signal using a disposable, reversible fault. Restore the
   normal detector configuration and show a healthy subsequent run.
4. Record only check identifiers, timestamps, role purpose, result, and source
   revision. Do not retain provider payloads, resource content, URLs, IDs,
   secrets, headers, or raw error messages.

## Operating rule for every future AWS change

| Moment | Required proof | Why |
| --- | --- | --- |
| While editing | Focused target static check | Catches source, dependency, and policy drift in seconds. |
| Before a change set | Current target reconciliation and exact change-set scope | Prevents a planned mutation against stale or different infrastructure. |
| Before execution | Identity-specific live probe and reviewed rollback | An administrator's success cannot hide a narrow-role failure. |
| After execution | Health/readiness evidence plus changed-control proof | Confirms the deployed state, not just CloudFormation completion. |
| At closeout | One full repository gate and durable safe evidence | Detects cross-layer regression without paying that cost for each edit. |

## Stop conditions

Stop rather than work around a failure if a role needs broader permissions, a
provider requires an unscoped action, the resource inventory changes, an AWS
cost estimate grows beyond its approved ceiling, a live probe exposes sensitive
data, the workload is unhealthy, or rollback is not demonstrably safe.

## Rollback

Stage 1 is source-only and rolls back by reverting its commit. Stage 3 will
define its exact CloudFormation rollback and role-policy recovery before any
AWS mutation is requested; it has no authority in this plan to remove or
replace persistent resources.

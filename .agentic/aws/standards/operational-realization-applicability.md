<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.standard.operational-realization-applicability
version: 3
status: active
created_on: "2026-10-24"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.realization
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Own the bounded provider-specific applicability exception without changing its approval requirements.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# Provider Operational Realization Applicability

The generic [deployment proof standard](../../04.deploy/standards/operational-realization-gate.md) owns contract and proof semantics. This provider surface owns the following operation-specific applicability and approval conditions.

## Entity-smoke read-only execution preflight

The user adopted this bounded rule on 2026-11-08 for the isolated `entity-smoke`
scope on `kanbien-core-platform`; its
[implementation plan](../../04.deploy/plans/implementation/entity-smoke-core-platform.md#approved-entity-smoke-preflight-applicability)
records the source changes. Adoption grants no AWS execution authority and does
not apply to staging, either accepted baseline or other capabilities.

Proving the real task's network/TLS/database identity needs an actual ECS task.
For this scope only, an explicitly approved single preflight RunTask may occur
after source, artifact, semantic-integration, live-read and reviewed change-set
gates pass, but before execution-preflight has passed. This is a narrow ordering
allowance for the observation task, not a passed sixth gate or exemption from
the generic contract/compiler. Preserve the first five gates and their actual
component evidence. Never substitute IAM simulation or a constructed receipt
for successful connection evidence.

The owning controller must enforce these launch and completion boundaries:

- Exact qualified immutable image/source, selected task definition, identity,
  private network, configuration, permission and dependency-incarnation bindings
  are checked against the operation being prepared. No command, credential,
  database endpoint, role or network override is admitted.
- Only explicit `preflight` modes of the existing administration, migration,
  database-proof or isolated restore-reader program, or the private HTTP
  verifier's `ready` mode, are eligible. The bounded expected-unready exception
  below is solely for the declared credential-revocation recovery proof.
  SQL modes use a read-only transaction
  and SELECT-only observations; they cannot bootstrap, migrate, change grants,
  create/edit/delete records or run attempted-write denial probes. HTTP readiness
  cannot create a feature record. The administrator need not acquire runtime
  login access; the runtime probe must retain its own restricted identity.
- One flushed reservation per workload/mode/proof label precedes the sole
  launch. The completion deadline is at most ninety seconds. A lost response,
  missing terminal state, failure or expired task retention never permits
  another submission under that attempt. No automatic task stop, permission
  repair or business-operation replay is granted by this rule.
- Actual terminal task/image/identity, zero exit, exact source-owned success
  result and safe collected evidence are required before the controller marks
  execution-preflight passed. The later operation checks matching immutable
  bindings, freshness (at most the generic 900-second window), and that the
  preflight was created after any prerequisite that changes the relevant state.
  A stale or mismatched receipt blocks it rather than being relabelled fresh.

The existing [task controls](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-control.py),
task evidence/runner and preflight admission implement these boundaries. The
public provider route must consume them before supplying live capability;
helper availability alone is not enforcement or execution approval. Existing
source, package, normal business-operation/recovery gates, concrete approval,
ownership and safe evidence rules remain binding. This rule permits neither
bootstrap/migration writes nor accepted-release promotion.

### Expected-unready recovery observation

The user additionally approved the existing read-only verifier `unready` mode
solely to confirm live-but-not-ready after deliberate runtime-access revocation.
It retains exact concrete approval, all first-five gates, one launch, the
ninety-second bound and real terminal task/log evidence. The owning controller
must bind a successful source-owned administration `revoke-runtime` task receipt
to the selected proof label and unchanged source, image, configuration,
permission contract and dependency incarnation. The observation must be created
after that revocation. Retain this admission before submission and reconcile an
uncertain task without another launch, including through another caller key.

An expected denial is not successful database access. It cannot pass ordinary
execution-preflight or serve as readiness admission for business operations.
The recovery controller must use truthful operation-specific gate evidence;
the ordinary healthy-access graph cannot be marked passed from this result.
After restoring access, a separately reserved successful `ready` observation
is required before recovered feature work. No automatic restoration, permission
change, feature write, extra task launch or AWS execution authority is granted.
The public route remains closed for this operation until those real recovery
predecessors and gates are connected; helper availability alone is insufficient.

## Entity-smoke disposable restore cleanup

The user adopted this bounded rule on 2026-11-09 for `entity-smoke` on
`kanbien-core-platform` only. It grants no AWS execution authority and applies
neither to source data/snapshots, accepted baselines, staging nor other scopes.
The actual restore controller may select the generic v2 disposable-restore
cleanup declaration only for the exact isolated restore template/resource set.
Deletion remains a separately reviewed and explicitly approved operation.

Before its one DeleteStack submission the controller must validate the retained
original successful restored-record read, matching digest and clone incarnation,
original task/plan/gate custody, exact stack incarnation/template/parameters/
physical resources/tags, private reader bindings and terminal jobs. Its reviewed
plan must bind those facts, source/image/permission/dependency identity, all
applicable gates and the truthful delete count. A wrong/missing approved-plan
digest blocks execution. The source database, source snapshot, baseline and
staging resources are never cleanup targets.

Flush one reservation before submission. Lost responses, missing resources or
partial deletion allow observation of that original attempt only, not another
DeleteStack. Retain actual owned absence/inactive-definition observations and
the original successful readback. Acceptance consumes this evidence read-only;
it cannot reserve or delete. Failed/partial restores without successful readback
remain outside this rule and need their own governed recovery decision.

The owning [restore route](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restore-route.py)
and resource control implement the bounds. Local fixtures establish their
exercised protocol behavior, not provider ownership, AWS execution or acceptance.

## Bounded PostgreSQL Stage 6 Applicability

The [Kanbien/staging PostgreSQL restart plan](../plans/implementation/postgresql-stage6-restart-2026-10-03.md)
provides an operation-scoped alternative only after the user explicitly adopts
this applicability change and approves its concrete execution plan. Saving a
draft or applying this instruction change alone grants no execution authority.
Until both approvals exist, the normal requirements below remain effective.

For that approved slice only, its reviewed operation/evidence matrix replaces
whole-route generic contract/compiler migration and full-estate programme
completion as prerequisites. It must cover every actual dependency of the
selected PostgreSQL operation: reviewed source, immutable image and entrypoint,
adapter/target compatibility, identity, safe configuration shapes, TLS/network,
database semantics, queue completion, observability, cost and bounded recovery.
Evidence from a healthy HTTP process does not qualify a relational task.

Existing executable gates remain binding, including applicable realization,
reconciliation, change-shape and candidate/task preflights. A required failure
pauses the affected operation and its dependants while its outcome is reconciled
and relevant code/configuration is repaired within the approved allowance.
Rerun affected checks, prove proportionate prevention, qualify a changed image
and resume from the first incomplete checkpoint. Do not close out merely to
report an ordinary failure that can be safely repaired within that authority.
No failed check is bypassed or manufactured into a pass.

The concrete approval must include the plan's source/configuration repair,
image-publication, reattempt, time, cost and owned-recovery allowances. Passing
source review and renewed operation bindings within them do not require a new
human execution approval per repair. Existing controllers must enforce the
supported identities, checkpoint semantics and cumulative limits before this
route is executable; instruction prose alone is insufficient. Scheduler,
storage, tenant authority and the replacement programme remain deferred.

Preserve consumed labels, terminal outcomes, uncertain-outcome reconciliation,
rollback/restore and verified cleanup. Reuse unchanged artifact evidence only
with unchanged relevant bindings and valid freshness; a failed attempt remains
terminal. A new attempt need not imply a new image, but must use an explicitly
reviewed, supported identity and recovery route within approved limits. Count
all failed or possibly accepted submissions across new labels/images/chats.
Escalate exhausted limits, new effects, broader permissions, persistent-data
repair outside the approved manifest, or inability to reconcile and recover
safely. Expressly approved cleanup of positively owned disposable restores and
reviewed rollback use their recovery allowance without redundant reapproval;
other destructive actions need separate authority.

For every material failure record evidence, cause and earlier-check gap,
correction/verification, proportionate prevention with proof, and resumed
outcome or precise blocker in existing Stage 6/session records. At closeout
provide both PostgreSQL acceptance evidence and those completed records.
Keep evidence safe and append-only. Other capabilities use the normal
contract/compiler route; generic schemas and compiler guarantees are unchanged.


## Bounded Hosted RAG Retirement

For the explicitly approved retirement of `rag-rulebook-staging` in account
`337159794548`, `eu-west-1`, the [hosted staging retirement procedure](../workflows/deploy-rag-rulebook-service.md#hosted-staging-retirement)
provides the operation-scoped proof path. Adoption requires the user's explicit
authority to retire dedicated resources and to add this focused missing control;
the session log records that authority before execution. This grants no authority
for unrelated targets or renewed deployment.

This teardown introduces no new runtime artifact, database semantics, or
business-state migration. Its reviewed live inventory, dependency/owner checks,
local retrieval proof with hosted access denied, live-template comparison,
CloudFormation change-set allowlist and protected-resource before/after checks
replace deployment artifact/entrypoint qualification and whole-route compiler
migration prerequisites for this retirement only. Applicable executable gates,
source checks, explicit approvals, narrow resource ownership and secret handling
remain mandatory. CloudFormation owns resource updates/deletions; retained logs,
scheduled secret deletion and preservation of the shared OIDC provider are
required lifecycle outcomes. Failed/uncertain actions pause their dependants
until reconciled; bounded retries retain terminal evidence and new labels.

The procedure owns exact ordering, deletion scope, retained/pending accounting,
and stop conditions. PostgreSQL applicability, other live targets and generic
realization contracts/compiler guarantees remain unchanged.

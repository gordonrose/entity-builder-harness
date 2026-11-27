<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.disposable-test-environments
version: 1
status: draft
created_on: "2026-11-26"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.test-environments
disciplines: [architecture, security, sre]
kind: implementation-plan
purpose: Preserve production deployment behaviour while planning temporary test environments through shared deployment machinery, with verified cleanup and no retained test application data.
portability: {class: source-only, targets: []}
used_by:
- id: deploy.plans.readme
  path: docs/04.deploy/plans/README.md
-->

# Disposable AWS test environments

The user uses AWS to prove functionality, has no production users, and does not
need application data preserved between test sessions. The intended outcome is
to create the dependencies required by a selected test, prove functionality,
then remove that session's billable resources and application data.

The software factory must still produce production-ready services. Make the
environment temporary, not the product test-only: use the same application
build, infrastructure definitions and deployment machinery, with explicit
environment settings controlling lifetime and data retention.

## Authority and status

The user's `proceed` approved the first proposed increment: a resource and
dependency inventory and a concrete retirement proposal. The subsequent
`yes let's do that` approves revising this plan around production-preserving
profiles and shared test-session controls, then explaining its milestones.
Those completed increments were documentation-only. The user subsequently
adopted the complete overnight mandate with `start the goal`; the existing
[session record](../../../commitLogs/2026/nov/26/2026-11-26-22-09-reducing-aws-bill/README.md)
records its autonomous source, publication and bounded AWS execution authority,
protected resources and stopping conditions. All five implementation milestones
are now authorized within that boundary, but are not yet complete.
Exact source and live changes still follow the existing
[AWS planning](../../../.agentic/aws/workflows/plan-aws-change.md) and
[execution](../../../.agentic/aws/workflows/execute-approved-aws-change.md)
workflows and their executable gates. The adopted goal does not bypass them.

Account: `337159794548`; profile: `kanbien-dev`; region: `eu-west-1` (Ireland).
Targets: `kanbien-core-platform`, legacy `kanbien-staging`, and adjacent legacy
resources identified below. Observations were collected in this chat on
2026-11-26. This is a bounded inventory, not an all-region/account-wide deletion
list. Reobserve exact targets and active work before any later mutation.

## Key milestones

The inventory is complete within its stated limits. The next milestones are:

Current source checkpoint (2026-11-27): lifecycle policy, isolated naming and
template-owned creation, activation and discard settings are locally implemented.
Captured foundation prerequisites include a separately owned network in the source
plan. That plan feeds durable session records and the existing change-set engine;
the prepared registered session, foundation and preparation checks all pass.
The complete impact preview passed without executing broader integration checks.
The live workload command, independent expiry, physical cleanup and successor
sessions are not yet connected. No AWS resource has been changed or retired;
milestones 4–5 and any savings remain unproved.

| Milestone | What it delivers | Done when |
| --- | --- | --- |
| 1. Define the two environment settings | Production stays deployed and keeps data; temporary tests have an explicit end and disposable data | Profile checks distinguish both choices and reject unsafe cleanup requests |
| 2. Create a separate temporary copy | Existing definitions can build the selected service and its dependencies for a test session | The generated resource plan isolates the temporary copy without changing production defaults |
| 3. Automate testing and cleanup | One operation uses normal deployment, prepares data, runs checks, saves results and removes its resources; expiry covers interruption | Local checks cover the full handoff, failures, resumed cleanup and remaining-resource reporting |
| 4. Prove it safely | Rehearse the complete process in an isolated AWS test environment | Fresh creation, testing, removal and recreation pass, including failure cases and production-protection checks |
| 5. Retire today's always-on test resources | Separately reviewed removal of existing core/legacy resources and leftovers | Approved resources are gone and later billing evidence confirms the reduction |

Deliver each milestone in small connected increments under the adopted goal;
routine per-increment approval pauses are waived for this task. The goal's
authority does not waive ownership, source/package proof or live-operation
gates. Writing this plan does not complete milestone 1.

## Production and temporary environments share one system

[ADR 0044](../adrs/0044-use-temporary-instances-of-production-deployments.md)
records the durable lifecycle and independent-worker choices; this plan owns
their implementation milestones and evidence.

The existing [target-profile decision](../adrs/0028-use-client-environment-deployment-target-profiles.md)
already separates deployment choices from application features. Extend that
boundary; do not copy deployment engines or add test-only switches to product
code. The table describes the intended operating behaviour. Local draft readers
now check explicit lifecycle settings. The target profile includes optional
prerequisite bindings for separate instances; its persistent lifecycle selection
and ordinary production preparation are unchanged. The live temporary execution/
cleanup command is not yet implemented or authorized by those fields.

| Behaviour | Production environment | Temporary test environment |
| --- | --- | --- |
| Deployment path | Shared service definitions, build and deployment controls | The same controls and the same selected application build |
| While running | Normal health, security and persistence requirements | The same requirements for the capabilities being proved |
| Lifetime | Remains deployed under its declared service policy | Explicit session end and expiry; the adopted goal allows two hours including startup |
| Application data | Preserved under its production retention policy | Prepared for the test and removed after the session |
| Automatic removal | Not allowed by the test cleanup controller | Allowed only for the exact resources owned by that session |

Existing targets must not become disposable through a missing setting, a name
containing `test`, or an expiry alone. Preserve production defaults; missing or
ambiguous lifecycle/ownership information blocks destructive cleanup. Enforce
the production/shared-resource boundary through scoped execution permissions
and exact resource ownership, not tags alone. Existing shared resources need
their own reviewed retirement; a new session must not adopt them for deletion.

A temporary environment may run the full production arrangement and remove it
afterwards. Cheaper test configurations must record their differences and limit
their claims: one instance cannot prove multi-instance failover. Use the same
build and relevant migrations, identity, networking and observability paths.
Fresh installation tests start empty; upgrade tests prepare representative
previous-version data before applying the upgrade. Persistence and recovery
can be tested within a session without retaining application data afterwards.

A running temporary environment still fails if an expected service disappears.
Completed removal has a separate cleanup check; it is not a global exception
that makes an absent production service healthy. Keep historical release proof
separate from current environment state.

## Cost evidence

Reuse the chat's Cost Explorer evidence: November 1–26 gross usage is about
USD 192.97, covered by credits. November 19–25 shows roughly USD 8/day, or
USD 235–240 per 30 days if that activity persists. These are estimates before
credits, not cash due or a promised post-change bill.

| November 1–26 category | USD | Main known charge type |
| --- | ---: | --- |
| VPC | 61.27 | Interface endpoint hours 53.94; public IPv4 approximately 7.25; endpoint data approximately 0.07 |
| RDS | 40.07 | Database instance hours 31.45; storage/backups approximately 8.63 |
| ECS | 31.77 | Fargate CPU and memory |
| CloudWatch | 22.64 | Metric monitoring; log storage is not this principal charge |
| Load balancing | 15.45 | Almost entirely load-balancer hours |
| ElastiCache | 8.34 | Provisioned cache |
| WAF | 7.80 | Web firewall |
| Secrets Manager | 3.75 | Retained secrets and requests |
| Other categories | About 1.89 | DNS, identity requests, images and object storage |

The figures are category totals, not attribution to individual resource IDs.
For example, the RDS instance total is not the cost of one database. Current
resource counts do not reconstruct their complete month-long billing history.

## Running applications and dependencies

Counts below are desired/running. A zero running count with desired count one
does not represent an intentional shutdown or prove the service is healthy.
Stack names in the core rows begin `kanbien-core-platform-`.
Disposition columns describe these current test deployments, not production
defaults. Existing resources require milestone 5 review and approval; they do
not automatically become disposable when the new profiles are implemented.

| Resource | Observed owner and state | Function/dependency | Proposed disposition |
| --- | --- | --- | --- |
| ECS `kanbien-core-platform-bootstrap-runtime` | Stack `bootstrap-runtime`; 1/1 | Original runtime proof; scope inventory calls it accepted-historical with persistence as successor | First retirement candidate: reconcile historical ownership and current consumers, then stop through its owner |
| ECS `kanbien-core-platform-core-server-persistence` | Stack `core-server-persistence`; 1/1 | Core server/persistence proof; core RDS, private network and collector | Session-only workload |
| ECS `kanbien-core-platform-entity-smoke` | Stack `entity-smoke`; 1/1 | Entity proof; task revision 3 explicitly uses core RDS database `kanbienpersistence` | Session-only workload; cannot delete its shared database independently |
| ECS `kanbien-core-platform-observability-collector` | Stack `core-server-persistence`; 1/1 | Observability delivery for core proof | Run with tests that require that capability; preserve required observability assertions |
| ECS `kanbien-staging-platform-shell` | Stack `kanbien-staging-platform-shell-service`; 1/0 | Older platform shell; relational DB, queues, public ingress and identity configuration | Stop replacement intent when retiring; retain an on-demand proof route if functionality is still supported |
| ECS `kanbien-staging-platform-shell-worker` | Same service stack; 0/0 | Older queue/worker proof | Already dormant; verify queued work before retirement |
| ECS `service-platform` | Live task `kanbien-staging-service-platform:12`; 1/0; source ownership not established here | Older application/brochure; ALB, Redis, secret-backed PostgreSQL and bootstrap identity | Dependency review before retirement; do not classify as unused solely from running count |

Live `list-tasks` returned four RUNNING task ARNs in core and none in staging.
Core services use private subnets without public task IPs. Staging services are
configured for public task IPs. No ECS scalable targets were found in the
earlier same-chat inventory. No EventBridge Scheduler schedules or rules on
the default event bus were returned in this region during this increment;
other event buses, regions and external automation were not audited.

## Supporting resources and retirement conditions

All four databases share VPC `vpc-0063b6c3d2d781f3c` and the private subnet pair
`subnet-07d06ea08281f0665`, `subnet-076e63a204af0a221`.

| Resource | Ownership/evidence | Disposition and condition |
| --- | --- | --- |
| RDS `kanbien-core-platform-persistence` | Available, PostgreSQL 18.3, 20 GiB gp3, deletion protection on; persistence stack | Fresh database for each session, shared by selected core/entity tests; remove only when all consumers finish |
| RDS `kanbien-staging-platform-relational` | Available, PostgreSQL 17.11, 20 GiB gp3, deletion protection on; staging foundation stack | Retire old running instance after mapping retained legacy proof coverage |
| RDS `database-1-recovery-20260906` | Available, PostgreSQL 18.3, 20 GiB gp2, no stack tags/protection | Retirement candidate; actual legacy application host binding remains unresolved |
| RDS `database-1` | `inaccessible-encryption-credentials`, 20 GiB gp2, no stack tags/protection | Separate bounded retirement candidate; establish ownership and supported deletion path for this state; data recovery is not required by the user's chosen policy |
| ECR API endpoint `vpce-0580c18f7aff6a90a` | Core foundation stack | Recreate for private image access when needed; remove after last dependent task finishes |
| ECR Docker endpoint `vpce-0020d67e1a1e003d4` | Core foundation stack | Same session dependency |
| Logs endpoint `vpce-0c5d5cbf615c3517d` | Core foundation stack | Keep until task log/evidence delivery completes, then remove |
| Secrets endpoint `vpce-077a2130bb458bf18` | Core persistence stack | Administration/preparation dependency; determine needed stages from task bindings |
| ALB `kanbien-staging-alb` | ARN suffix `app/kanbien-staging-alb/29ac325385686357`; tagged `ManagedBy=manual-now` | Configured for both `kanbien-staging-app-tg` and `kanbien-stg-platform-shell`; retire only after both routes, DNS and certificate associations are accounted for |
| Public IP allocations `eipalloc-0e9f8c1ec7f20a318`, `eipalloc-0fedd38dce2e0904a` | Attached to `eni-0f10f8ead56ac87ad`, `eni-0fcb445cf298b4fe8`; requester-managed `amazon-elb`, descriptions identify that ALB | Remove via owning ALB lifecycle; do not independently detach/release provider-managed interfaces; verify disappearance afterwards |
| WAF `kanbien-staging-platform-shell` | Regional ID `1ae038e6-c344-4ba4-915c-bdc5439fc689`; staging foundation stack; associated with ALB | Retire association and ACL with legacy ingress, or create for tests proving public-edge protection |
| Cache replication group `kanbien-staging-redis` / node `kanbien-staging-redis-001` | Available; one `cache.t4g.micro` Valkey node; snapshot retention zero; owner declaration unresolved | Task `service-platform:12` Redis hostname matches live node exactly; recreate for that test path, retire after consumer retirement |
| CloudWatch metric publishers | Core foundation enables Container Insights; collector service is running | Reconcile session-aware publishing and alarms; precise share of USD 22.64 per publisher is unverified |

Each interface endpoint is available in both private subnets. The source
configuration establishes intended dependencies, not proof that every test
actually uses all four endpoints. Endpoint hourly billing persists until
deletion: [AWS pricing](https://aws.amazon.com/privatelink/pricing/).

Retain the shared VPC, subnets, security boundaries and S3 gateway endpoint
`vpce-04a01a0590bfd8624` during initial work. The S3 gateway routes are
`rtb-0edd9750b11aa7f2e` and `rtb-05a8253723446a68c`. These are not the four billed
interface endpoints. No available NAT gateway was found in the same-chat
inspection. No unrelated network teardown is proposed.

All four RDS records reference KMS key
`aabb9bc2-91e9-4c00-a7e3-b342b1bdf88d`; `describe-key` reports AWS-managed and
Enabled. Do not infer the cause of the old database's error or propose removing
the shared key. The older application's database host comes from
`kanbien/staging/postgres/admin`; only secret-reference metadata was read.
Resolve that host binding through an approved, non-disclosing dependency check
before finalizing the two unowned database removals.

## Data and storage that a stack deletion can leave behind

The user does not require application data retained between temporary test
sessions; this does not weaken production data protection. This is distinct from
source code, historical acceptance evidence and the minimum records needed to
finish cleanup after an interruption. Those records belong outside the test
database and must not include application payloads or credentials.

Live discovery found 14 available manual RDS snapshots. They are explicit
retirement candidates, not a wildcard deletion instruction:

- `database-1-pre-recovery-20260906`
- `database-1-recovery-20260906-pre-service`
- `kanbien-core-platform-core-server-persistence-snapshot-persistencedatabase-eksbywfsjja5`
- `kanbien-core-platform-entity-smoke-104261dd18363aa576a5600c`
- `kanbien-core-platform-entity-smoke-8f76ed3480e85d60fb60f547`
- `kanbien-core-platform-persistence-recovery-20261023`
- `kanbien-core-platform-persistence-recovery-20261024`
- `kanbien-core-platform-persistence-recovery-20261024-r2`
- `kanbien-core-platform-persistence-recovery-20261024-r3`
- `kanbien-core-platform-persistence-recovery-20261025-r1`
- `kanbien-core-platform-persistence-recovery-20261025-r2`
- `kanbien-core-platform-persistence-recovery-20261026-r1`
- `kanbien-core-platform-persistence-recovery-20261026-r2`
- `kanbien-core-platform-persistence-recovery-20261106-diag01`

Twelve belong to core persistence; two belong to the older databases. Source
templates for core and staging databases use `DeletionPolicy: Snapshot`,
`UpdateReplacePolicy: Snapshot` and `DeletionProtection: true`. Future disposable
test paths must explicitly reconcile these settings and the final-snapshot and
automated-backup choices for session-owned resources. Preserve production
retention defaults. Keep backup and protection behaviour required by the proof
while the temporary service runs; only its reviewed teardown may release those
protections and remove session backups. No temporary application backup should
remain after completed cleanup. This is not permission to disable production
backup/recovery behaviour simply to reduce test cost.

Eleven regional secret metadata records were returned. Two core secrets,
`kanbien-core-platform-persistence-runtime` and
`kanbien-core-platform-persistence-ordinary-migration`, are retained by the
template as cutover history; runtime/migration now use IAM database access.
They are candidates for dependency-checked retirement. Other secrets include
the core administration credential, staging relational credentials, Cognito
test clients, old application bootstrap credentials and one RDS-owned secret.
No blanket secret deletion is proposed. Preserve necessary setup credentials
until their consumer has a proven replacement; use the owning service for the
RDS-owned secret. Secret values were not read.

Staging log groups and publication repositories also have retention policies.
Changing templates does not remove already detached snapshots, logs or secrets.
The removal plan must enumerate them separately. Bound diagnostic log retention
and exclude application payloads; store only necessary test results externally.
Cached images are an explicit cost/startup-speed choice, not application data.
DNS, object/image storage, secrets and the eventual cleanup control can leave a
small residual bill; their exact idle total has not yet been priced.

## Reuse and conflicting assumptions

| Existing owner | Reuse or required correction |
| --- | --- |
| [Deployment target profile](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/00-target/target-profile.yml) | Extend its existing declaration/checking owner with explicit environment lifetime and retention policy. Current profile does not implement these choices; preserve production defaults and fail closed for cleanup. |
| [Core scope inventory](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/scope-index.yml) | Reconcile historical bootstrap service; keep release history separate from session activity. Removing a temporary environment does not erase its release evidence or make missing production services healthy. |
| [Core foundation template](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml) | Currently combines retained cluster/access configuration and billed endpoints. Separate session-owned dependencies from retained shared foundations through the existing definitions; do not delete the whole shared foundation. |
| [Persistence template](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml) | Combines database, secret endpoint, server and collector; desired counts are fixed at one. Preserve running-service defaults and production protection; allow separately owned temporary resources and explicit post-test teardown. |
| [Bootstrap template](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml) | Desired count fixed at one despite historical scope state; reconcile before historical retirement. |
| [Entity template](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml) | Already accepts desired count zero/one; reuse existing controls, but zero tasks does not remove a temporary environment. Rebind database host and IAM `DatabaseResourceId` for every fresh database. |
| [Entity deployment/recovery controls](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/README.md) | Reuse qualified task execution, ownership reservations, controlled stop/start, failure reconciliation and cleanup observations. Current recovery controls are not a general-purpose environment deletion API. |
| [Release succession](../../../scripts/04.deploy/lifecycle/60-run/release-succession/script.py) | Keep immutable accepted evidence and existing locks; a fresh database invalidates database-incarnation-specific evidence and permissions. |
| [Deployment consolidation](../../../.agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md) | Coordinate shared changes with its existing owners and qualification gaps; historical live proof does not qualify modified controllers. |
| [Staging reconciliation](../../../.github/workflows/reconcile-platform-shell-staging.yml) | Declared every four hours and read-only; it does not restart workloads. Reconcile its expected state/retirement reporting and other deployment triggers rather than claim it is an auto-healer. |

The missing capability is a reusable temporary-environment lifecycle across
workload and dependency owners, including resource removal, test data
preparation, independent expiry cleanup and removal verification. It is not
implemented by this document. Extend the owning workflows/contracts and existing
deployment machinery before using that capability; do not invent an ungoverned
CLI cleanup script or a workload-specific execution engine.

## Implementation detail for the five milestones

1. **Define the two environment settings.** Extend the current target profile
   contract and its existing declaration/validation owners, not application
   feature code. Describe environment lifetime, data retention, expiry and
   ownership without duplicating service configuration. Preserve existing
   production behaviour and reject cleanup without an explicit temporary
   policy. Proposed first code increment: the profile contract, its parser and
   affected registered checks, with no live changes or template-default changes.
   Verify valid production/temporary declarations, unchanged existing production
   interpretation, and rejection of unsafe or ambiguous cleanup declarations.
2. **Create a separate temporary copy.** Extend the existing foundation,
   persistence and workload definitions to resolve unique session resource
   identities and bindings, while leaving production defaults intact. Keep
   retained shared resources outside the teardown boundary. Reuse reviewed
   CloudFormation operations; plan both profiles before any live rehearsal.
   Prepare a fresh database through existing migrations/test setup, or load a
   representative prior-version fixture for upgrade proof. Derive fresh IAM
   database resource IDs and connection settings. Verify generated declarations
   isolate temporary resources and preserve production health/retention policy.
   Include all dependencies needed by the selected proof; record any omissions
   from the full production arrangement rather than claiming equivalent proof.
3. **Automate testing and cleanup.** Extend shared deployment/recovery controls
   with a reusable session operation: normal deployment, data preparation,
   functional proof, saved results and exact owned-resource teardown. Use normal
   failure cleanup plus an independently invoked expiry controller outside the
   disposable environment. Initially propose a two-hour session limit including
   provisioning, with explicit extension for longer proof. Keep non-sensitive
   ownership/cleanup records outside the app and exclude production/shared
   resources from cleanup permissions. Initially serialize sessions for a
   shared target; reject overlapping ownership rather than delete another run's
   dependency. Reuse existing locks and execution records, not a parallel engine
   or registry. Once a session ends or expires, reject new creation and deployment
   retries; reconcile in-flight provider operations and any late-created
   resources before declaring cleanup complete. Operations need deadlines,
   bounded retries and reconciliation after uncertain outcomes. Local checks
   must cover the complete handoff and generated records, including partial
   creation, failed tests, expired sessions, post-expiry deployment attempts,
   repeated cleanup and protection-boundary rejection. Failure must report
   remaining resources and alert, never claim successful removal.
4. **Prove it safely.** After qualifying the required controls and satisfying
   their operation gates, use the adopted goal's bounded live authority to rehearse in
   an isolated temporary AWS target: fresh create/test/delete/create, plus
   service restart and data readback within a session. Cover upgrade fixtures
   where migration readiness is claimed. Exercise partial provisioning, failed
   tests, lost runner, expiry, resumed cleanup and attempts to select production
   or another session's resources. Confirm normal production plans and health
   checks remain unchanged. Test rejection safely through local checks and
   permission simulation where supported, never a destructive production trial.
   Record provisioning/test/cleanup durations, unexpected retained resources
   and the intended residual cost. Do not retire the old setup until this passes.
5. **Retire today's always-on test resources.** Resolve the inventory's legacy
   database/cache ownership gaps and refresh exact targets/active consumers.
   Match each exact core and legacy removal and its effects to the adopted
   inventory-bound authority; narrow the list when ownership is uncertain.
   New targets or effects outside that authority need separate approval;
   do not relabel existing shared infrastructure as disposable.
   Retire historical bootstrap first after its checks; close legacy application
   dependencies before ALB/cache/databases; remove known leftover snapshots and
   secrets only through reviewed ownership paths. Verify physical removal,
   then compare underlying charges after billing catches up. The earlier
   milestones alone do not stop today's existing-resource charges.

Normal startup order is dependency network, database/preparation, selected
services, then proof. Shutdown stops producers, settles owned work, collects
bounded evidence, stops consumers, then removes session databases/cache/ingress
and finally private endpoints. Precise ordering comes from each selected graph;
never remove a shared resource while another session or owned operation uses it.

Until rehearsal succeeds, leave the existing setup available. Before live
retirement, prove recreation and retain the exact reviewed source, image and
configuration needed to rebuild the test service. Recovery after an approved
test-data deletion recreates the service and fixture data; it does not restore
discarded application data. A failed recreation returns an explicit failure and
cleanup result. Production rollback and data-recovery protections are unchanged.

## Acceptance and verification budget

### Resumption approval — 2026-11-27

The user explicitly approved cohesive new script-source files over 50 code lines
where needed for this five-milestone goal, keeping the existing review and AWS
safeguards. This resolves the size decision recorded in the historical checkpoints
below, including continued use of the drafted policy helper. It is prior size
approval for subsequent necessary files, not a retrospective claim about the
first draft. Admission follow-up, preparation and source-matched verification
remain required. The implementation and AWS authority boundary is unchanged.

### Session source-plan increment admission — 2026-11-27

Before editing, admit one cohesive read-only helper at
`scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/session-binding/implementation.py`.
Role: helper; owner: provider-neutral target alignment / environment lifecycle.
Purpose: check a temporary session's immutable identity and lifetime separately
from its source-target/package identity. Direct consumer: existing AWS
`preparation-inputs.py`, through a new source-plan-only API. The user has expressly
approved necessary cohesive source files over 50 code lines for this goal.
Extend the existing capability home, not a second registry or execution engine.

The closed `deploy/environment-session-intent/v1` document carries `target`,
`scope`, canonical lowercase UUID-hex `session_id`, integer UTC epoch seconds
`starts_at`/`expires_at`, and explicit `environment_lifecycle`. Reuse the existing
policy reader; require temporary/discard, exact integer clocks (not booleans),
`starts_at <= now < expires_at`, and positive lifetime no greater than either the
declared maximum or the calling operation's approved maximum. The goal's concrete
maximum remains 7,200 seconds; the reusable helper does not hardcode it. Reject
unknown fields, caller-supplied resource names, hashes or ownership claims.
Return frozen checked values, not mutable caller collections.

The existing preparation owner adds `load_session_plan` without widening
`load()` or public fixed-target deployment routes. Keep the source profile and
package custody unchanged. Capture each declaration's bytes once per resolution,
parse and hash those same bytes, and reuse captured documents for projection.
Refactor the existing `read_document`/`_load` path rather than duplicate validation.
Final unchanged-input observation rejects ordinary concurrent edits, not a claim
of an atomic filesystem snapshot or future freshness. Controller source identity
and imported-code qualification remain separate from declaration-byte hashes.
Derive a bounded AWS prefix from the session ID and project shared templates with
the existing CloudFormation helper. Reject the production identity; truncated
names require collision/ownership gates later and do not prove global uniqueness.
Include selected dependencies and preserve source/default templates unchanged.

Named risks and diagnostic inventory: invalid/missing/unknown document fields;
target/scope mismatch; malformed session ID; non-temporary policy; invalid clock
or maximum; future/expired/contradictory/excessive lifetime; unavailable/changed
source; unsupported dependency/projection; production-identity collision. Use
finite value-free conditions preserved through the actual preparation caller;
optional helper import failures must not break the unchanged persistent route.
No provider call, child process, durable write or cleanup authorization belongs
to this helper/consumer. A source plan is not ownership or expiry evidence.

Consumers/proof: extend existing `PreparationInputTests` in
`declaration-coverage/runtime-configuration-test.py`, its registered
`preparation-inputs-regression`, existing catalog/registration fixtures, both
affected declaration input closures and diagnostic review ledger. Prove exact
reasons, nested immutability, same-build/two-instance projection, unchanged
production preparation, forbidden names/hash fields, actual checked-result use,
hash-of-parsed-bytes, changed-during-capture rejection and safe import failure.
No new test runner or recurring check. Primary lane: local change; later normal
package/deploy gates remain. Source/helper/template/test/runtime changes invalidate
proof. Exploratory fixture budget: two minutes; measure before final registered
proof. Existing fixed routes remain available; live session creation stays
unsupported until independent expiry, durable ownership and cleanup are connected.

Reuse considered: policy reader, selected-string projection, path-safe strict
declaration parser, existing preparation fixtures and reservation/change-set
engines. Workload-specific ordinary-update snapshots are not imported upstream;
its separate parse/read mechanism does not supply this read-once boundary.
Existing local reservations are deliberately not claimed as remote expiry.
This increment adds one script-source helper and a guide, with no source moves
or removals and no AWS/control-service deployment.

### Historical independent increments — 2026-11-26

Milestones remain incomplete. The first policy helper and isolated-network
definition are local drafts with exploratory proof, not approved live controls.
The helper's 63-code-line source admission needs the explicit size approval
requested in the session record. Keep it frozen; do not bypass that requirement.
Independent changes to existing owners below remain inside the adopted goal.

1. **Safe startup failure reporting.** Eight controlled import-failure probes
   showed that the new imports can fail before existing reports and disclose a
   native traceback. Change only the existing core checker, preparation reader
   and `PreparationInputTests`: retain a finite unavailable state for the
   M1-added imports, report through existing failure codes, and stop subsequent
   work. Test actual CLI entrypoints with missing, syntax, import and unexpected
   failures; assert exact reports, no sensitive canary/native stderr and no
   child/provider work. Preserve argument-only paths and unrelated import owners.
   This does not authorize or modify the frozen helper, AWS or current profiles.
2. **Checked source parameter projection.** Extend the existing shared AWS
   `cloudformation-template.py` helper and existing `foundation-checks-test.py`,
   not a new parser, script or deployment engine. The role remains a read-only
   source helper: explicitly selected non-secret String defaults/overrides may
   resolve their Ref and string Fn::Sub uses; unsupported or ambiguous selection,
   constraints or substitution fails with value-free reasons. Preserve unselected
   provider/resource references symbolically, reject NoEcho/dynamic values and
   substitution injection, and never mutate the deployable source tree. Actual
   direct consumer planned next is existing preparation-input resolution;
   template-composition fixtures also need the same default projection. Consumers
   requiring literals must still reject unresolved expressions.

For the projection admission, the owning capability is the existing AWS
CloudFormation source-normalization helper; no new folder/file or public command
is introduced. Existing `change_sets` helpers own provider parameter rows and
update preservation, while task-binding owns live identities; neither owns
source defaults, and importing workload controls would reverse dependencies.
Reuse strict `template()` parsing and the existing foundation fixture/registered
`aws-foundation-checks` lane. Named risks are wrong default identity, accidental
secret projection, source mutation and false equivalence of production settings.
Declared helper/fixture/template inputs and runtime identity invalidate proof.
Local exploratory budget: two minutes per focused fixture. Final registered proof
still follows admission review and normal preparation; package/live gates remain
separate. No recurring schedule or automatic cloud execution is added.

The identity increment's before-edit boundary required parameterization only
after helper review. Capture baseline semantic identities before changing any
template, then prove default Resources/Outputs/Conditions unchanged and two
distinct prefixes isolated. Keep the full current protections, IAM/health and
application semantics. Do not use current Git HEAD as an implicit test oracle or
duplicate complete templates as fixtures.

**Identity-only increment admission.** The reviewed projection API now supports
the existing preparation reader, composition checks and declaration validators.
Add `ResourceNamePrefix` to the three existing foundation/persistence/entity
templates with default `kanbien-core-platform`, a maximum of 21 characters and
one lowercase DNS-label segment sequence. Derive the private namespace from it.
Change resource names, ownership tags, private URLs and matching metric dimensions
together; retain shared publication repositories and source/image custody.
Existing public controllers continue to select and check the fixed default;
adding a configurable template is not permission to target another environment.
Their preparation/parameter observations must account for the new parameter
explicitly without accepting arbitrary prefixes. Existing roles remain:
read-only source preparation/validation and governed fixed-target deployment.
No new entrypoint, selection mode, cloud mutation or cleanup authority is added.
Update the existing owner tests and input closures; do not create a second
deployment or verification engine. Preserve the baseline canonical hashes of
Resources/Outputs/Conditions captured from `2220763a` before edits, then assert
default equivalence, constraints and disjoint identities for two prefixes.
Selected template/parser/controller changes invalidate those tests. Exploratory
budget is two minutes per focused existing fixture; final registered proof and
source-matched package/live gates remain separate. The local-public package
qualification helper pin is deliberately stale until its owner is reviewed and
its existing fixture passes; never refresh the pin solely to clear a failure.

**Parent-approved source-pin correction (2026-11-26).** The parent reviewed the
complete CloudFormation helper, recovery wrapper and offline fixture, approving
helper SHA-256 `c4f608b533c5f30cefec7a228a66d4e30047b82fe84251880039450c9dee688b`.
The existing loader and normalization functions are unchanged; new imports are
standard-library only, with no added provider or import-time execution. The
selected-String projection has local proof including regex-recursion rejection.
This supersedes the stale-pin hold only for those reviewed bytes. Refresh only
that persistence-recovery pin and strengthen existing owner-change cases to
require zero Docker calls before rejection; retain all other pins, the core
branch, credential/engine isolation and existing child-stage boundaries. Run the
controlled offline recovery fixture without real Docker, builds or network.
Its result is controller proof, not image qualification. Final registered
`persistence-payload-regression` and diagnostic review remain pending normal
global admission and source freeze.

### Historical local checkpoint — 2026-11-27, before size approval

The identity increment is implemented locally, not deployed. All three default
Resources/Outputs/Conditions fingerprints match the captured baseline; unchanged
parameter defaults also match. Six declaration tests prove default preservation,
two distinct instance names and negative protection/count/type cases. Preparation
has 19 passing tests; the shared foundation/projection fixture has 15. Existing
entity alignment/deployment/composition and observability fixtures pass with
controlled inputs. The source-pin correction passed all 48 offline recovery
cases with zero real Docker calls. These are exploratory results, not final
registered, package or provider qualification.

The checked profile helper remains frozen pending explicit size admission.
Milestones 1 and 2 are partially implemented; neither is accepted. Validated
session ownership, a new-instance creation adapter, independent expiry and
cleanup are still missing. Existing fixed-target controls continue to reject
other names and unsupported temporary profiles. Existing entity stacks without
the new parameter are not assumed compatible; a governed source transition
would need its own review. No application source or existing target profile
changed. No AWS resources were created, changed or deleted, and no savings are
claimed. Final preparation/commit and live execution remain gated.

### Temporary cleanup contract increment admission — 2026-11-27

Extend the existing realization v2 change-shape owner, not a second cleanup
compiler or an incident-specific exception. The adopted overnight goal authorizes
this required governance/controller work; it does not itself establish resource
ownership or make any AWS operation admissible. Existing restore cleanup keeps
its original successful-readback requirement and retained meaning.

Exact owners: `.agentic/04.deploy/standards/operational-realization-gate.md`,
its owning workflow, v2 schema and guide, the AWS applicability standard and
execution workflow, and the existing compiler `script.py` and
`service-graph-test.py` under `scripts/04.deploy/operational-realization-gate/`.
No new script, runner, command, registry or recurring check is proposed.

The closed v2 `temporary_session_cleanup` declaration has a phase and eight
exact-true requirements: explicit temporary/discard policy, exact session
binding, durable positive ownership, closed creation admission, reconciled
in-flight operations, concrete execution approval, excluded protected resources,
and owned teardown changes only. `prepare-discard` admits update only; `delete`
admits delete only. Every other operation class is explicitly forbidden.
It is mutually exclusive with restore cleanup and immutable-definition refresh;
v1, missing/null/extra/false/non-boolean fields and invalid phases/classes reject
through the existing finite `change-shape-invalid` diagnostic.

These flags are declarations, never evidence. The provider controller must
establish exact session/account/region/source/authority/resource incarnations,
effective permission boundaries and fresh owned state. Preparation may only
remove retention/protection on independently proved temporary-owned resources;
it cannot admit unrelated updates. Functional failure stays failed, but does
not strand independently proved-owned resources. Cleanup is a separately labelled
operation, not a transition out of a terminal failed/succeeded attempt. All
eight gates, existing evidence formats/bindings, current normalized counts and
freshness remain unchanged. Unknown effects require reconciliation, not replay.

Reuse `operational-realization-regression` and the actual CLI fixture. The
predicate inventory above drives positive phase cases, independent negatives,
mixed-opt-in/v1 rejection, unchanged old-route admission, count/freshness and
terminal-state protection. Exploratory fixture budget: two minutes; record the
actual duration and select final registered proof after connected review.
Diagnostic review will update only the changed compiler boundary while retaining
unrelated debt. No provider adapter, ownership store, expiry worker or live
deletion is implemented or qualified by this increment.

### Instance definition controls admission — 2026-11-27

Extend shared production-capable declarations rather than duplicate templates.
The existing foundation already references external ECR/OIDC identities; do not
invent ownership of them. Make its publication role explicitly optional with
production enabled by default. New temporary foundations must omit publication
authority. In the persistence definition add bounded zero/one service-count
parameters with existing production counts as defaults, and explicit selection
that omits obsolete password secrets for fresh temporary instances. Do not
remove resources from an existing production stack or weaken its default RDS
protection/snapshot retention. The later independently gated teardown changes
only proved-owned temporary resources.

Owners are the existing foundation/persistence templates, shared CloudFormation
projection reader, actual preparation and fixed-target declaration readers, and
their current declaration/foundation/controller fixtures. Extend only connected
consumers required by these declarations; record exact affected paths and stop
for an unsupported interpretation rather than silently broadening the parser.
No new script, parallel renderer, registry, provider call or product change is
proposed. Source target and package custody remain production identities;
instance identity and selected creation parameters remain separately checked.

Named risks: accidentally copying publication permission, starting consumers
before database preparation, retaining obsolete session credentials, changing
production defaults, unvalidated condition/parameter projection and declaration
or deployed-parameter mismatch. Diagnostics remain existing finite owner errors,
without submitted values. Reuse the existing typed parser/projection and test
owners; preserve unchanged default resource/protection/security semantics with
explicit checked treatment of newly optional conditions and parameters. Every
new branch needs real consumer tests and independent malformed/unsupported
negatives, not merely a passing helper. Two-minute exploratory fixture budget;
record actual timing and defer final registered proof until connected review.
Parent source review rejected a draft reader branch on workload/resource logical
IDs before qualification. The control bindings must instead be declared in the
owning templates and consumed by a generic closed validator: narrow optional
resource groups and bounded service counts, with exact parameter/condition/
resource/output references. This is source-owned configuration, not a new
registry or an implicit resource-type discovery policy. Renamed resource proof
and malformed binding rejection must exercise the actual preparation caller.
Existing live UPDATE routes intentionally remain fail-closed for old deployed
templates missing the new parameters; unchanged source defaults do not establish
that separate migration's compatibility or authorize widening its allowlist.
Catalog input closures and diagnostic/source pins follow reviewed frozen code,
not speculative hashes. Independent expiry, remote ownership and live execution
are still not implemented or admitted by these definition controls.

### Durable admission and instance adapter admission — 2026-11-27

Wrapper/selector extension admission: extend the existing wrapper
`scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/smoke-test.sh`
with only `--environment-sessions-only`, dispatching the existing connected
`environment-sessions-test.py`; preserve all current branches and default behavior.
The existing catalog `scripts/repo/check-selection/checks.yml` owns the new
`aws-environment-sessions` integration/local-runtime development unit and its exact
input-impact alias; `repository_contracts_test.py` verifies dispatch/status, source
closure, selection and changed-input invalidation. This extends existing wrapper
and selector owners, adds no runner/source file, and addresses omitted session
proof or stale reuse, not unrelated preparation checks. Actual child effects are
read-only plus disposable local writes with fake AWS, never live provider access.
Inputs are the fixture, wrapper, session adapter/record/reservation/change-set/CLI
owners, preparation/session-policy readers and the checked session plan's actual
source declarations; runtime identity includes bash, Git, Python and temporary-file
context. Advisory cost is 20 seconds against the parent's measured 14.296-second
connected fixture; the selector-contract exploratory budget is 120 seconds.
The focused selector-contract regression passed in 14.33 seconds wall time
(13.940 seconds reported by unittest), proving the exact input alias/closure,
selection, invalidation, child dispatch and failure preservation without running
the session fixture or contacting AWS; this is exploratory, not prepared proof.
Explicit selector invocation remains available; package/deploy/live expiry and
cleanup proof remain deferred. Parent source review, metadata/preview and the
required independent script-admission review precede preparation/final proof.

Proposed paths in the existing canonical AWS provider-adapter home:
`scripts/04.deploy/shared/provider-adapters/aws/session_records.py` (helper),
`environment_sessions.py` (helper owning checked AWS instance operations), and
`environment-sessions-test.py` (test). These are one connected reusable lifecycle
boundary, not a workload-specific copy, separate registry, generic retry engine
or second command runner. The adopted autonomous goal and explicit cohesive
source-size approval cover their necessary implementation; ordinary admission
review remains required before preparation. Source-only planning stays read-only.

Direct consumers are the instance adapter's foreground creation and sealed-session
cleanup-preparation paths. This first connected increment supports the existing
change-set preparation/execution and resumed observation protocols; it does not
yet implement `DeleteStack`, final physical absence, a live provider factory or
workload-specific controller integration. Both paths use the same remote
admission/reservation record and shared change-set engine; the connected fixture
calls those actual paths. The later
independent expiry invocation must use this same cleanup owner. The adapter is
not live-ready merely because an API exists: normal custody, realization,
effective permissions, observed expiry and exact plan approval remain required.
Do not supply a production-provider capability until these are connected.

Existing capabilities considered: `ImmutableReservationStore` owns immutable
local operation records, `change_sets.py` owns single submissions and observation,
`cli.py` owns one bounded AWS subprocess, and `response.py` owns finite provider
classification. Reuse them. Expose any necessary reservation storage seam at its
owner while preserving existing filesystem behavior/subclasses; do not override
their fixed protocol in an S3 subclass or duplicate it in the new adapter.
Reuse the existing canonical JSON and record-validation mechanics. The new
capability is necessary because local files cannot serialize independent cloud
workers or survive loss of the foreground runner.

One versioned target record atomically contains session admission and immutable
operation intents. Initial retention uses `If-None-Match`; subsequent transitions
use the exact observed `If-Match` identity. Open/expiry checking and reserving an
operation must be one conditional transition, not writes to separate objects.
Sealing preserves all admitted operations. A successor needs positively completed
predecessor cleanup and retained prior version/digest; no historical deletion or
in-place reopening. Require versioning and deletion/unconditional-write protection
before use. Positive exact readback confirms fresh retention; retained intents,
conflicts, lost responses and ambiguous observations are observation-only, not
automatic mutation retries. The independent cleanup identity outlives the creation
identity, whose effective AWS permissions must enforce the creation deadline.
Accepted operations may finish late and must be reconciled before final absence.

The S3 adapter reuses `cli.invoke_json` with bounded private files for object
bodies, explicit owner/profile/region, one AWS attempt and no pager. It never
logs raw objects/credentials, creates buckets or changes their policies. Extend
only operation-specific missing-object/conflict classifications at `response.py`;
denied/malformed/unknown outcomes never become absence. Relevant current semantics:
[conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html),
[object reads](https://docs.aws.amazon.com/cli/latest/reference/s3api/get-object.html),
[object writes](https://docs.aws.amazon.com/cli/latest/reference/s3api/put-object.html).

Named risks and diagnostic inventory: invalid/duplicate/oversized records;
wrong account/region/session/source or predecessor; missing version/ETag;
unprotected storage; unarmed/expired/sealed admission; changed operation intent;
CAS conflicts or uncertain writes; readback mismatch; nonterminal operations;
unreconciled late effects and protected-resource selection. Conditions must be
finite and value-free at the real adapter boundary. Test shared-engine use,
exact request/token binding, a single submission only after confirmed fresh
retention, no submission otherwise, concurrent seal/admission, resumed observation,
historical preservation, failure artifacts and unchanged local reservation use.

Effects are network and bounded private file writes for the two helpers when
explicitly invoked with a qualified provider; the fixture has only disposable
local files/controlled subprocesses and intercepts provider calls. Primary proof
lane is local change through the existing selector, with one focused registered
test unit if no existing aggregate can express this new connected boundary.
There is no new runner, broad scheduling effect or active cloud schedule.
Exploratory fixture budget is two minutes, with measured timings; later package
and runtime consumers remain deferred until actual connected qualification.
Source, companion helpers, fixture, declared control contracts and execution
context invalidate retained proof when changed. Complete live proof remains the
existing realization/provider workflow; no manual ungoverned alternative exists.

### Captured activation and dependency order — 2026-11-27

Next bounded increment: extend the existing source-plan reader and session
operation owners; add no source file, registry, runner or provider factory.
Creation keeps services stopped while their database is prepared. Activation
uses a separately captured projection of the same original definitions, changing
only declared service counts. It is an open, unexpired session operation, not a
cleanup permission or a production configuration switch.

Owners/consumers: `preparation-inputs.py` captures direct dependency edges and a
deterministic dependency-first stack order while already reading workload
bindings. Return immutable `stack_dependencies` and `stack_order` together with
`activation_templates` and `activation_parameters`; retain current creation
fields and exact stack/template pairing. Each selected scope depends on the
session foundation and its declared scopes. A later network/controller increment
still owns wiring the private-network component; these fields do not claim it
is already connected. Do not reread source or infer order from alphabetic names.

Extend the existing template-owned `CreationControls` desired-count row with
one required `active` positive integer in its checked allowed domain. Permit a
nonnegative production default; creation remains zero. This admits the existing
entity service, whose production template default is deliberately zero, without
changing that default. Declare active counts in the persistence and entity
templates, with generic validation and renamed-resource proof rather than
workload/logical-ID branches. Optional roles/secrets remain omitted in both
temporary projections. Persistent readers continue selecting original defaults.

`environment_sessions.py` admits `activation` UPDATE using only the captured
activation template/control map; no caller template/count override. Its checked
preflight must observe completed original creation and database preparation,
exact count-only changes, source/package custody, independent expiry, permissions
and approved effects before submission. This API does not manufacture those
facts. `session_records.py` treats activation like creation for open/time checks,
within the same conditional document and immutable reservation protocol. Reuse
`change_sets.py` unchanged; retained activation selects observation only.

Diagnostic/proof inventory: malformed, missing, boolean, nonpositive or out-of-
domain active count; omitted/misbound service control; dependency cycle/unknown
scope and invalid order; activation count/source/prefix mismatch; optional
permission restoration; sealed/expired activation; unconfirmed preflight;
uncertain submission and resumed observation. Preserve existing finite, value-
free caller failures and sensitive-canary assertions. Extend existing
`PreparationInputTests`, declaration/default-parity assertions and
`environment-sessions-test.py`; retain complete ordinary-route fixtures. Parent
reviews exact behavioral counterexamples and existing diagnostic-ledger rows.
Current registered units/input closures remain the owners; update only actual
changed closure requirements, not another check or scheduling mechanism.

Proof lane is local change, with existing commit/package/live gates pending.
Source helpers/templates/fixtures and their declared runtime invalidate proof.
Exploratory budget is two minutes per affected fixture batch, with final
registered verification after connected review and preparation. Unchanged proof
is reused. Effective service-role binding, live preflight, cleanup deletion,
independent expiry and successor admission remain separate incomplete steps.

### Captured discard preparation — 2026-11-27

Next bounded increment: extend the same preparation reader, source template and
session-operation adapter with captured discard templates and parameters. Add no
module, parser, patch language, check or runner. Existing production and creation
protections remain unchanged; only a sealed temporary/discard operation selects
the removal preparation. This source step does not delete resources or qualify
the live cleanup controller.

Owners: beside `instance_controls` in `preparation-inputs.py`, validate optional
`Metadata.DiscardControls` and derive a deep copy of the already captured stopped
temporary projection. Resource logical identities come from that declaration,
never workload-specific branches. Each row has exactly `type`, `attributes` and
`properties`; each supported transition declares `expected` or exactly-true
`expected_absent`, plus `discard`. Initially allow only RDS DBInstance deletion
and replacement policies to `Delete`, deletion protection to `false`, and
automated-backup deletion to `true`. Match source values with JSON-type equality;
reject unsupported types, paths, expressions, graph/identity/image/IAM changes,
missing resources and mismatched expectations. Preserve backup retention and all
other settings. Declare the four transitions in the persistence template; any
source compaction needed for the existing inline-size bound must preserve its
parsed meaning outside that metadata addition.

Check every surviving projected resource for unresolved or retaining deletion
and replacement policies, including conditional resources and RDS's implicit
snapshot default. Require complete supported RDS discard outcomes. Omitted
legacy secrets are outside that surviving graph. Unknown resource types fail
closed against the reviewed existing source type inventory; this is source
coverage only, not evidence of physical deletion or provider-created children.

Return immutable `discard_templates` and `discard_parameters` for every selected
stack/template pair; parameters are exactly the creation selections (counts zero,
same isolated prefix and excluded optional resources). Reuse captured bytes,
shared CF projection, source hashes and final freshness read. No extra reread or
second source renderer. In `environment_sessions.py`, remove the draft arbitrary
`cleanup_template` override and select only captured discard data. Constructor
closure checks do not replace the required qualified source/preflight comparison.
Reuse durable sealed-only admission, original reservations and observe-only
resumption without changing `session_records.py` or `change_sets.py`.

Proof/diagnostics: extend the existing actual-reader and connected-operation
fixtures for exact four-path changes, unchanged production/creation/activation,
renamed database bindings, immutable complete maps, omitted/duplicate/unowned
maps, wrong zero counts, malformed declarations, JSON-type mismatches, implicit
retention, unsupported resource/path, unresolved conditions, source fingerprint
changes, caller overrides, sealed-only admission and uncertain-response recovery.
Failures remain finite/value-free; no provider work on invalid source. Existing
`preparation-inputs-regression` and `aws-environment-sessions` own final proof.
Exploratory batches have a two-minute budget; reuse unchanged evidence. Reader,
template, fixture, adapter and execution-context changes invalidate affected
receipts. Record parent source review, diagnostic-ledger updates and normal
preparation before final verification. Network wiring, physical-resource
observers, DeleteStack, live preflight and independent expiry remain separate.

### Captured foundation prerequisites — 2026-11-27

Following discard preparation, connect the existing private-network draft through
source-owned foundation prerequisites. Extend the current target profile with
optional `provider.foundation.instance_prerequisites`: a mapping of component
identifiers to exactly `stack`, `template` and `foundation_parameters`. The latter
maps foundation parameter names to that component's output names. The component
name is data, not a workload/name branch. This describes how to create a separate
instance; it neither adopts nor changes the persistent target's existing network.
Ordinary persistent preparation does not select these prerequisites.

Initially support direct foundation suppliers only, with no prerequisite chains,
second dependency framework or new file/runner. The shared preparation reader
owns validation of this optional provider binding. Do not copy the rule into a
fixed target checker that does not consume instance prerequisites. Reject unknown
fields, malformed/escaping references, absent templates/outputs/parameters,
duplicate destination parameters, reserved count/prefix controls, duplicate
stack/template identities and component/scope/foundation name collisions.

Capture the profile and prerequisite templates once through existing source
capture, then extend `stack_names`, `stack_templates`, `stack_dependencies` and
`stack_order`. Return immutable prerequisite component names and exact
consumer-stack/parameter/producer-stack/output rows. Foundation depends on those
components; workload dependency edges retain their current meaning. Use the
same projection loop and add empty `Metadata.CreationControls` to the network
template; its prefix needs no production default. Include its creation/discard
maps but no service-count activation. All new references enter source identity
and final freshness checks. The adapter validates complete component/pair/map
closure while preserving the qualified-preflight trust boundary.

Do not invent network CIDRs or availability zones in source or the closed session
intent. The five existing network inputs remain unresolved in this source plan.
The future immutable execution-input record and actual preflight must validate
canonical private ranges, subnet containment/non-overlap, two available distinct
regional zones, and the approved size/cost boundary. Foundation network inputs
must later resolve from fresh, positively owned prerequisite outputs and the
original creation operation; caller-supplied VPC/subnet identifiers cannot
substitute. Regional AWS-managed S3 prefix-list discovery remains separate.
Neither captured edges nor fake callbacks prove those live facts.

Affected existing owners: target profile, private-network template, preparation
reader/actual-reader fixture, session adapter/connected fixture, foundation
fixture, lifecycle standard, two guides, selector input closure/fixture and
diagnostic ledger. No application code or persistent deployment behavior changes.
Add only the network template to the existing registered session input closure;
the preparation unit already owns the target directory. Extend disposable fixture
source copies explicitly; do not change ordinary `load` just to satisfy a test.
Prove renamed component/output bindings, graph order, immutable captured maps,
finite malformed/unknown/collision failures, exact source fingerprint/read counts,
all-template handoff and unchanged persistent results. Reuse existing checks.

Exploratory batches are bounded to two minutes. Consolidate normal preparation
and final registered proof after this connected source batch is frozen/reviewed,
rather than rerunning unchanged full checks between its edits. Changed reader,
profile/template, adapter, fixture, declared input closure or execution context
invalidates affected proof. Effective ownership, input resolution, creation,
physical removal and independent expiry remain unimplemented live boundaries.

### Final acceptance

The final removed state applies only to explicitly temporary environments:
zero test tasks, no session RDS instances/backups or snapshots, no session
interface endpoints, and no session-owned ALB, WAF or cache. Shared retained
resources are explicitly listed and priced. No retained
application data is required. Source code and non-sensitive proof/cleanup
records remain outside that environment. The live removal manifest must also
cover generated log groups, secrets, detached resources and test schedules.
Production service health, deployment defaults and data protections remain
unchanged, and the test cleanup identity cannot delete production/shared assets.
Proof records identify the tested build/configuration and any differences from
production, rather than treating every successful smoke test as full readiness.

Do not accept a successful functional test as a completed session until cleanup
observations pass. Confirm physical resources first; then compare pre-credit
Cost Explorer data after AWS billing catches up. Budget alerts must measure
underlying spend rather than allowing credits to hide it. No savings are claimed
until changes execute and billing evidence supports the comparison.

For the initial documentation-only revision: reuse unchanged inventory/billing evidence;
perform no new provider discovery or mutations. Budget two minutes for scoped
metadata, links and whitespace checks. Review named risks: weakened production
defaults, mistaken shared-resource deletion, hidden retention costs, misleading
production-equivalence claims, unrecreatable bindings, and confusing proposal
with implementation. Recheck static evidence only when its relevant documents
or link targets change; refresh live observations at the later mutation gate.
No runtime or full-repository tests are needed for prose-only changes.

For implementation, select existing registered checks by affected owners and
measure create, preparation, proof and cleanup durations separately. The
repository's ten-minute normal-delivery budget still applies; slow cold
provisioning must be measured and reconciled with that owner, not silently
exempted or reported as instant startup. The adopted two-hour session expiry is
an upper bound, not a performance target or price guarantee.

Initial documentation-only growth was one plan and two existing Markdown
updates. The active implementation also adds the pending lifecycle helper and
policy guide/standard plus the private-network draft; identity changes reuse
existing templates, readers and tests. No running cleanup service or recurring
execution has been created. Its mechanism and operating cost remain future work.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.disposable-test-environments
version: 1
status: draft
created_on: "2026-11-26"
updated_on: "2026-11-28"
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

Current source checkpoint (2026-11-28): settings and isolated source plans are implemented, but milestones 1–2 still require acceptance through a working service. Milestone 3 now has start/run/cleanup commands, real workload handoffs, independent expiry, per-session cleanup control, versioned evidence, stop-once hung-task cleanup and completed-predecessor replacement. Production defaults and application code are unchanged.

The controller image packaging folders were explicitly approved and their existing-image publication path is implemented. Local proof covers setup recovery, worker qualification, task admission/stop uncertainty and successor CAS; the latest fifteen affected cases passed in 10.365s. The unadmitted-intent correction and hung-task case then passed in 12.832s. The root remains v10 (reserved bound 65,283 / 65,536 bytes); its existing task-state child is v5. The exploratory full controller file hit its 55-second budget, so it is not passing combined proof. A bounded controller unit is being registered instead of embedding it in the slow broad session regression.

Remaining: source admission/review and diagnostic closure, final registered proof, actual image build/publication and protected setup, then live rehearsal. The local Docker engine is unavailable; actual image proof must use the normal hosted publication route with the protected environment intact. Milestones 4–5 have not started: no AWS resource has changed or been retired and no savings are established. GitHub permits the exact approved task branch plus main, with reviewers unchanged; no workflow has been dispatched.

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

### Connected controller implementation admission — 2026-11-27

Historical admission context: root process `68254` was polled live at 16:36 UTC.
It has since ended, so its input freeze is no longer active. Its preparation
check passed and session check failed; neither result covers later source
changes. No provider mutation is part of this implementation batch.

Before-code admission under script-admission v4:

- Proposed paths: `scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py`
  (operation), sibling `aws.py` (helper), and `integration-test.py` (test).
  Owner: deployment runtime / environment sessions, in the explicitly approved
  home. Existing explicit approval covers necessary cohesive files above 50 code
  lines. The command consumes the concrete AWS assembly; foreground and expiry
  workers consume the same command. The fixture exercises that composition using
  controlled provider responses and real reservation/operation owners.
- Purpose and named risks: connect captured dependency order, native workload
  steps, failure-triggered cleanup and independent recovery; prevent duplicate
  sends, activation before prerequisites, deletion before all discard work ends,
  lost functional verdicts and completion from unknown physical observations.
  No existing command owns this complete lifecycle. Reuse unchanged preparation,
  provider invocation, reservation, change-set and workload owners; extend their
  real missing durable handoffs. No additional journal, executor or retry policy.
- Direct consumers and bounded inventory: the command and its fixture consume
  `SessionProvider`, `SessionRecords`, `SessionOperations`, the preparation
  reader's new/existing-session routes, captured task selections, native
  persistence `BoundOperation`/verifier and entity task runner. `aws.py` composes
  existing task CLI adaptation and log readers rather than implementing RunTask.
  Its protected configuration and native authority observations must be connected
  before any live admission; source digests or caller booleans cannot substitute.
- Existing-owner changes: entity task runner/control/steps and their preflight
  admission/evidence readers must retain receipts and required cold-worker packets
  through the current remote task storage, and check authority immediately before
  a new send. `session_records.py` and `environment_sessions.py` own bounded
  completion evidence and successor admission. Their existing fixtures prove
  these extensions. Share any required task-storage artifact slots at that same
  owner, with immutable labels and capacity reserved before creation.
- Compatibility and exclusions: existing persistent/local-file routes remain
  supported unchanged. Product/application code, existing production defaults,
  main, live resources and retained historical proof are untouched. Public
  product-module restructuring is not applicable to these deployment scripts.
  Existing manual deployment stays available; the new live route remains closed
  until concrete storage/worker/permission/expiry qualification passes.
- Execution boundary: the operation's actual children read/write protected
  evidence and invoke scoped AWS mutations only through existing qualified
  senders. The helper performs those same bounded effects on the operation's
  behalf. Local fixtures write disposable files and use synthetic provider
  responses only; they do not inherit live authority. Primary proof lane is local
  integration, with package/deploy and runtime rehearsal still mandatory.
- Inputs/invalidation: controller/helper/fixture, actual imported preparation,
  record/operation/task consumers, selected source declarations, runtime and
  protected configuration. Register through the existing selector after its
  active run ends; no second runner or new cross-capability schedule. Any changed
  relevant identity invalidates its affected proof; preserve unrelated evidence.
- Expected cost: budget eight minutes for new focused controller tests, four for
  affected native task tests and eight for affected record/cleanup tests, measured
  separately with no monolithic rerun after each edit. These are implementation
  budgets, not a completion estimate or normal-delivery timing proof. Independent
  admission review precedes preparation/final registered proof.
- Growth/cost: three proposed script files, no moves/removals; one focused
  controller check through existing integration selection, no additional review
  policy or recurring schedule. Existing review/admission duties apply. Actual
  counts and timings remain pending implementation.

Diagnostic inventory for this batch: preserve finite underlying owner reasons
for missing/invalid source, inaccessible/malformed protected state, rejected or
unknown provider observations, expiry/sealed admission, uncertain reservation,
failed workload evidence and remaining resources. The command reports functional
verdict and cleanup status separately; native exceptions, provider bodies,
credentials and arbitrary supplied values stay private. Source/import/startup
failures need a finite command-level fallback without granting replay. Tests
must assert exact safe reasons and no-send/no-completion counterexamples through
the real caller, not only result shape. New runtime review rows remain partial
until their actual producer/consumer proof is inspected. Existing record/task
diagnostic debt is not erased by this composition.

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
missing resources and mismatched expectations. This historical increment kept
backup retention; the later temporary-zero-retention amendment below supersedes
that choice. Declare the four transitions in the persistence template; any
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

### Existing-session source revalidation — 2026-11-27

The normal source planner intentionally rejects `now >= expires_at`, but sealed
cleanup must still verify its original source after expiry. Resolve that conflict
at the existing lifecycle standard and its actual readers before using cleanup;
never supply a fictional earlier clock or an expiry-bypass flag. This is an
authorized source/governance increment under the adopted goal, not a new live
exception. The preceding source checkpoint is committed as `2d3eea6c`, with its
session bookkeeping in `4341be3a`; AWS remains unchanged.

Extend existing helpers only: `session-binding/implementation.py`, the AWS
`preparation-inputs.py`, `session_records.py` and `environment_sessions.py`.
The first two remain read-only source helpers; the latter two retain their
existing guarded remote-read/reservation/submission roles. Direct consumers are
the preparation reader and fresh sealed discard preconditions; ordinary
production preparation, creation and activation semantics do not broaden.
Reuse the single source capture/projection body, canonical serialization,
conditional record reader and single-submission engine. No new file, parser,
store, check, runner, schedule or source-size exception is needed.

Factor shared intent validation behind named `read` and `read_existing` APIs.
The latter permits an expired original lifetime only for revalidation, while
still checking the actual clock, future start, explicit policy and approved
duration. Add `revalidate_session_plan` around the same capture/renderer. It
reconstructs the narrow original intent and compares the complete freshly
captured plan, not just its source digest. Normalize independently loaded
dataclasses to their fields for canonical comparison without removing existing
tuple-shape checks. Unknown fields/maps and changed graph/order/output rows
cannot be silently dropped during comparison.

Add the record owner's read-only `observe_existing` boundary: actual guarded
versioned read, validated clock, copied original document/version identity, no
initialization or write if absent. Give the adapter explicit qualified source-root
and approved-duration context; missing/invalid context fails before mutation.
The context names an absolute declaration root; its current availability is
checked by fresh recapture, not adapter construction. A missing directory must
not block cold observation-only recovery of a retained operation.
For each fresh `prepare-discard` prepare/execute precondition, observe the
existing sealed record and original binding, call the concrete source revalidator
at that observed clock, then run the remaining qualified preflight. Keep the
existing reservation ordering: rejected fresh preflight retains its intent;
subsequent attempts remain observation-only and cannot replay submission.

Consumer/proof inventory: extend the existing `PreparationInputTests` and
`SessionHandoffTests`, source-binding guide and existing diagnostic owner rows.
The registered `preparation-inputs-regression` and `aws-environment-sessions`
remain the final proof owners; their existing input closure already includes
the affected modules. Check actual import/capture closure before asserting reuse.
No changed check timing or invocation lane is proposed. A bounded admission
follow-up covers the new helper consumer connection before final preparation.

Named diagnostic counterexamples: ordinary planning still rejects exact expiry;
existing revalidation accepts it without changing start/end; malformed clocks,
future start, excessive duration and non-temporary policy reject; missing,
foreign or open records cannot qualify cleanup; source edits during/after the
first capture and caller-modified templates/phase maps/graph/output rows reject
before CloudFormation; supplied hashes cannot replace positive record reads;
expiry cannot initialize a missing record, reopen creation or extend duration;
failed fresh revalidation preserves the reservation and retry observes without
resubmission. Preserve finite supported owner reasons and exclude native errors,
submitted values and sensitive canaries. Actual controller qualification, live
ownership/outputs, roles, immutable execution inputs and independent expiry
remain separate unimplemented boundaries.

Parent owns connected review, governance, guide and diagnostic reconciliation;
delegate binding/preparation/reader tests separately from record/adapter/handoff
tests. Freeze both before final review and normal preparation. Exploratory
batches have a two-minute budget; registered final affected proof has a
three-minute budget against unchanged execution context. Changed helper,
reader, adapter, records, fixture or source binding invalidates affected proof;
retain the preceding unchanged foundation and cleanup-contract evidence.

### Captured execution-input provenance — 2026-11-27

Before the next source edits, inventory found 58 template parameters: nine
creation controls, five preserved defaults and 44 required producer bindings.
Three foundation inputs already use the prerequisite output rows, leaving 41
new recipes on the existing provider bindings. Reuse that mapping rather than
duplicating it. All prior source checkpoint and AWS boundaries remain effective.

Owners/files: extend the existing `preparation-inputs.py` and shared
`cloudformation-template.py`, their `runtime-configuration-test.py` and
`foundation-checks-test.py`, the core target `00-target/target-profile.yml`, both
`20-scopes/{core-server-persistence,entity-smoke}/10-workload-binding/workload-binding.yml`
files, and existing foundation/persistence CloudFormation templates. Extend the
session fixture only for changed captured-plan expectations/negative handoff,
the existing session-binding guide, existing catalog input closure, source-pinned
offline recovery owner and existing diagnostic reviews as required by actual
consumers. No new file, engine, store, check or scheduled execution is proposed.

Add `execution_parameters` maps to selected foundation, prerequisite and workload
bindings. Exact recipe forms are: choice `{kind, contract, field}`; package
`{kind, field}`; source `{kind, field}` or `{kind, field, dependency}`; output
`{kind, output, component}` or `{kind, output, dependency}`; provider
`{kind, contract}`; omission `{kind: omit-if-unused}`. All values are checked
bounded source names, never arbitrary lookup paths or callbacks. Supported
choice contract `private-network/v1` has `vpc_cidr`, `subnet_one_cidr`,
`subnet_two_cidr`, `availability_zone_one` and `availability_zone_two`.
Supported package fields are `image_digest` and `source_revision`; source fields
are `repository_arn`, `repository_uri`, or declared-dependency `database_name`.
The provider recipe selects `aws-regional-s3-prefix-list/v1`, whose actual
observation remains owned by the existing foundation checker. Reject all others.

Return sorted immutable rows in `execution_parameters` (stack, parameter,
recipe-field pairs), `execution_output_sources` (stack, parameter, producer stack,
output), `execution_source_values` (stack, parameter, checked static value) and
`publication_selections` (stack, checked publication-field pairs). The latter
binds pipeline, target, account, region, candidate, package, program and repository
name/URI/ARN; it is not a receipt. Preserve the earlier prerequisite rows rather
than repeating them. An output producer must be a declared dependency ancestor,
not merely an unrelated stack that happens to sort earlier.

The publication selection remains the existing `publication_pipeline`. Add that
selection to foundation for its shared persistence repository reference, without
creating publication resources. Reuse existing publication parsing and captured
account/region/package/program/candidate facts; do not derive repository ARN/URI
from nonexistent receipt fields. Preserve the three persistence image parameters'
intentional use of the same qualified image. The later receipt consumer must use
the existing custody validator and bind target/candidate/package/program/region,
not accept a caller's `qualified` claim. No actual receipt is invented here.

All workloads receive their eight existing network/cluster/log values through
foundation output recipes. Persistence also receives foundation's verifier group.
Entity database endpoint, resource identifier, security group and administrator
secret ARN use its existing named database dependency; database name uses that
checked dependency declaration. Add only four foundation outputs (`VpcCidr`,
`NamespaceId`, `EndpointSecurityGroupId`, `S3ArtifactPrefixListId`) and two
persistence outputs (`PersistenceDatabaseResourceId`,
`PersistenceDatabaseSecurityGroupId`). They expose existing values, not new
resources. Existing production Resources/Conditions/parameters/outputs remain
identical; test the six additive outputs separately without weakening the older
default-parity fingerprints. Keep all projected bodies within the existing
51,200-byte limit; exact parsed parity is required for any formatting compaction.

Foundation's unused `ExistingGitHubOidcProviderArn` receives only the explicit
omission recipe. Its only consuming resource is already excluded from temporary
projection. Extend `project_parameters` with optional `omit_if_unused=()`;
defaults preserve all other callers. The original normalized template must have
no transforms/macros or unsupported dynamic references; the post-condition
template must contain no mention of each selected name outside its own parameter
declaration. Inspect nested keys and values, including metadata, other parameters,
conditions and outputs; conservative substring rejection is intentional. Validate
all candidates before deleting any, never prune unselected parameters, and use
the identical rule for creation/activation and the derived discard body.
This avoids an invented ARN or unrelated shared-identity dependency. AWS's
[parameter requirements](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html),
[substitution forms](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-sub.html)
and [transform behavior](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-section-structure.html)
were checked before choosing this conservative source-only boundary.

Diagnostic/proof inventory: actual reader fixtures must cover complete/disjoint
coverage, malformed recipe alternatives, duplicate/unknown selection, renamed
parameters/components/dependencies, missing/future producer outputs, source edits,
unchanged ordinary loading, exact package selections and no submitted secret
values. The projection fixture covers remaining Ref/Sub/map/metadata/key/string
mentions, macros even in removed resources, unsupported/dynamic references,
selection collisions and unselected-parameter preservation. Full-plan revalidation
must reject changed recipes/omission outputs. Source-only optional binding support
does not preserve incomplete temporary execution plans: missing required producer
coverage now rejects on that draft route; persistent compatibility is retained.

Parent owns connected review, governing prose, guide, registry/ledger reconciliation
and staged proof. Delegate the projection helper/fixture, captured reader/fixture,
and source bindings/additive outputs as non-overlapping owners. Exploratory
focused budget: two minutes per owner; freeze one connected batch before final
preparation and affected registered proof (four minutes), reusing unchanged
evidence. No actual network choice, package publication, immutable execution
envelope, live output resolution, new permission, cleanup or expiry is implemented
by these source declarations. Those remain required M3/M4 work.

### Reserved exact-stack deletion — 2026-11-27

After the input-provenance checks pass, extend the existing shared AWS owners
`environment_sessions.py`, `session_records.py`, `change_sets.py` and their
`environment-sessions-test.py`. Parent maintains this plan, lifecycle standard,
existing session guide and diagnostic rows. No new file, runner, store, check or
live command. This helper/API increment is required to connect the already
governed temporary cleanup `delete` phase; it does not qualify live deletion.

Add `SessionOperations.delete(*, stack, stack_id, observe)` with closed inputs.
Select an existing captured stack/template pair; require the full original
CloudFormation stack ARN with matching account, region and selected stack name.
Bind that ARN, source-plan digest, derived template reference and exact provider
arguments into retained intent. Names/ARN syntax do not prove ownership. The
existing qualified preflight must establish original creation custody, all
reconciled operations, protected exclusions, approved removals and effective
permissions before a fresh request. Partial creation is not proof of absence.

Reuse `change_sets._run` through one thin `delete` entry point: `delete-stack`,
`StackName` equal to the full ARN and the retained `ClientRequestToken`. Extend
the existing reservation/record namespace only with `delete:<stack>:delete`,
not a cross-product of creation/activation/cleanup kinds and arbitrary phases.
Fresh retention requires sealed admission. Fresh preflight uses the concrete
existing-session source revalidator at the observed clock, including after
expiry. Retained/uncertain intent only observes, without source imports, writes,
new preflight or resubmission. No caller role override, retention list, force
mode, deployment configuration or retry is accepted. Fixed qualified cleanup
role context and concrete ownership remain separate unfinished controller work.

Diagnostic inventory: reject missing/extra/wrong-type inputs, foreign stack/ARN
bindings, wrong operation-phase combinations, open admission, altered retained
intent and failed fresh recapture before provider effects. Preserve existing
record causes and finite `delete-stack-submission-uncertain` plus supported CLI
causes; never include raw identifiers or provider errors in failure text. Test
fresh/expired sealed deletion, exact token/argument custody, copied callbacks,
denied/ambiguous submission, malformed observation and cold retained recovery
through the real fake-subprocess handoff. Reuse prior helper fixtures and the
registered session check; existing consumers of prepare/execute stay unchanged.
Exploratory budget two minutes; final affected proof two minutes after normal
preparation and connected/admission review. Source/runtime/input changes
invalidate affected evidence; later complete integration is still required.
AWS [DeleteStack](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DeleteStack.html)
and [DescribeStacks](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeStacks.html)
were checked: accepting deletion starts work and does not establish physical
absence. No completed/successor session, leftover removal or savings claim is
part of this API increment.

### Connected execution inputs and authenticated package acquisition — 2026-11-27

The next connected increment consumes the captured recipes, rather than adding
another declarative map. Extend existing `environment_sessions.py`,
`session_records.py`, `foundation-checks.py`, `cloudformation-template.py` and
`ecr_publication.py`; extend their existing session/foundation/package fixtures.
Parent owns preparation-reader/publication selection, catalogue input closure,
standards, guide and diagnostic reconciliation. All existing fixed production
routes, main-only publication restrictions and receipt schemas remain unchanged.

Session initialization takes closed reviewed network choices and selected
publication run/source identities, not arbitrary receipt files or parameters.
The concrete package acquisition owner below authenticates each distinct
publication once; foundation can reuse its captured workload publication.
Validate canonical RFC1918 IPv4 ranges, subnet containment/non-overlap, and two
distinct available regional standard availability zones through the existing
foundation owner. Reuse regional S3 prefix-list observation and the immutable
ECR repository/scan owners. Keep the qualified image digest distinct from the
selected runnable manifest digest. No secret values or NoEcho parameters enter
retained inputs.

Retain one immutable base envelope in the existing conditional/versioned session
record before provisioning. It binds the source-plan digest, checked choices,
authenticated package facts and provider facts. Downstream outputs cannot exist
at initialization: retain append-once resolved inputs per `(kind, stack)` in
that same object before reserving/submitting each request. Bind requests to the
stable base digest and their own resolved entry, not the digest of a growing
collection. Keep the 65,536-byte limit; do not retain full templates or the source
plan. Existing remote compare-and-set, readback, lost-write uncertainty and
sealed/expiry gates remain. No second store, retry or completion flag.

Replace the draft adapter's caller-supplied `parameters` route with derived
parameters. Creation fills the complete template parameter set from controls,
unchanged defaults, checked choices, qualified publication/source/provider facts
and declared earlier producer outputs. `cloudformation-template.py` owns a
validation-only entry point, reusing its String/integer constraint logic and
supporting only the concrete AWS parameter types used by these templates.
Unsupported types, malformed/default constraints, NoEcho and unresolved dynamic
values reject; provider values retain their required String/list serialization.
This does not project AWS-specific parameter types into template expressions.

Original output ownership must be observed, not supplied through a trust flag:
use retained CREATE preparation/execution intent, exact change-set identity and
description/token, full original stack ID, and correlated successful root event.
Require the owned stack to be ready before reading its declared outputs. Reuse
`change_sets.execution_events` and `foundation-checks.stack_outputs`; a matching
name, caller dictionary or ready foreign stack is insufficient. Partial creation
still needs the separate cleanup custody path and is not made uncleanable by
this successful-output requirement. Update preparation reads the owned deployed
stack, replaces only captured controls and uses the existing
`update_parameter_inputs` to preserve every other value. Retained prepared inputs
and reservations govern execute/recovery without fresh resolution or replay.

New bounded helper admission:

- Path: `scripts/04.deploy/lifecycle/40-package/package-custody-receipt/acquire.py`;
  role helper; owner package custody, not session policy or a new public runner.
  Direct consumer: temporary-session initialization, with existing
  `qualification-test.py` exercising its actual subprocess/provider boundary.
- Named risk: a plausible local receipt or clean ECR image does not authenticate
  which workflow/source produced it. Existing `validate.py` checks receipt shape
  and expected identities; `qualification.py` checks local image qualification;
  neither acquires/authenticates hosted custody. Keep these distinct owners.
- API: `acquire_custody(*, publication, run_id, expected_source_revision,
  aws_provider)` returns the unchanged validated receipt and bounded immutable
  acquisition evidence. Concrete GitHub CLI transport only; no supplied URL,
  receipt path, verifier callback, trust boolean or secret retention.
- Capture source-owned repository/workflow/ref, exact artifact-name prefix and
  receipt member through the existing pipeline index and preparation reader;
  reconcile these facts with existing workflow/publisher declarations. Bind the
  selected workflow bytes at the actual publication revision, not just today.
- Observe the exact completed successful dispatch run/repository/workflow/source;
  list its complete bounded artifact set, select one unexpired matching artifact,
  retrieve by observed ID and verify its advertised archive digest. Read only the
  bounded selected member without extracting the archive; reject duplicate names,
  links, escaping/ambiguous paths, malformed JSON and oversized contents. Reuse
  `validate.py`, then require exact region, source and run reference.
- Verify image provenance through `gh attestation verify` using exact OCI digest,
  source repository/ref/digest, signer workflow and SLSA predicate, authenticated
  registry access and nonempty supported verifier output. The existing workflows
  put attestations in ECR; use the explicit OCI-bundle route and account for its
  repository-name limitation through observed run/repository identity. Certificate
  facts, not arbitrary predicate claims, bind source/run origin. Reobserve stable
  run/artifact identity before accepting. Reuse immutable repository validation
  from `ecr_publication.py` and `ecr-scan.check_image` without publisher-role reuse.
- Effects: bounded external reads and private disposable files only; no image
  publication, workload mutation, installation or permission changes. Proof lane
  local change through controlled subprocess fixtures, with real credential/tool
  and remote evidence qualification still required before live initialization.
  Installed `gh` 2.46.0 lacks attestation verification; fail closed, never silently
  bypass it. Tool upgrade/authentication is later governed setup, not done here.
- Existing manual publication and fixed deployment routes remain available under
  their own contracts. This helper is a necessary new bounded acquisition owner,
  not a second receipt schema or local-image qualifier. User's recorded approval
  covers a cohesive source file above 50 code lines. No new folder or check.

Diagnostic inventory: separate malformed/missing/extra choices or run selection,
invalid/nonprivate/overlapping CIDRs, unavailable/wrong-region/duplicate zones,
unsupported template values, failed acquisition/region/source/digest/scan,
missing/foreign/unready output lineage, altered deployed parameters, changed
source/base/entry, retention conflict/loss and closed admission. Preserve finite
known subordinate causes without raw provider bodies, URLs, parameter contents,
tokens or sensitive canaries. None of these failures permits mutation replay.

Connected fixture acceptance is a complete fake-provider private-network →
foundation → persistence → entity handoff with all required parameters, shared
image selection, durable-before-submit ordering, original-output ownership,
UPDATE preservation, cold recovery and failed-retention/nonreplay cases. Reuse
the existing session, preparation, foundation and custody checks. Exploratory
budget four minutes per owned fixture batch; final focused batch six minutes
after consolidated review and normal preparation. Changes invalidate only their
declared input closure; complete integration/package/live proof remains required.
This increment does not qualify controller permissions, expiry or physical cleanup.

Before implementation, connected inspection found two unused `NoEcho` email
declarations survive the disabled temporary budget/observability groups. A
complete non-secret input envelope cannot supply them. Extend the existing
explicit `omit-if-unused` proof to defaulted/NoEcho declarations too, but only
after every remaining mention has been rejected; a default is not a reason to
retain an otherwise unused declaration. This supersedes the earlier increment's
non-defaulted restriction, not its explicit selection or whole-template proof.
Select these two omissions in the existing foundation/workload bindings. No
ordinary/default projection changes, secret-value exceptions, blanket pruning
or production-default changes. Existing omission tests must reject a surviving
reference and prove defaults remain untouched outside the temporary projection.

Connected-fixture correction admission: the first five-case reader batch ran in
5.622s with two passes and three projection errors; no provider calls occurred.
Inspection established three real causes, not malformed fixture input: the
foundation's default-false budget guard was not selected, persistence uses a
resource-owned secret dynamic reference, and its monitoring condition also
selects a task-definition environment branch. Do not remove production secret
wiring or accept email values into the non-secret envelope to make these pass.

Extend the existing source owner with explicit
`Metadata.TemporaryDefaultConditions` lists in the foundation and persistence
templates. Validate named `Fn::Equals` guards against their existing exact
default-false String declarations with the true/false domain; reject duplicate,
missing, overlapping, default-true, secret or unsupported controls. Only temporary
projection adds these unchanged default values and named guards. Persistent
projection, production defaults and resource definitions stay unchanged.
The shared CloudFormation owner may resolve exact singleton three-element
`Fn::If` expressions for selected literal decisions, then perform its existing
removed-resource and unused-parameter checks. Unknown conditions stay symbolic;
malformed selected branches and condition graphs remain rejected.

The same omission owner may carry an unresolved versionless Secrets Manager
`SecretString` expression in a resource property only: exact scalar `Fn::Sub`,
one declared `AWS::SecretsManager::Secret` logical resource and literal JSON key,
independent of omitted/projected parameters. Reject external/unknown/wrong-type
secret references, SSM/versioned/constructed/malformed expressions, misplaced
plain strings, metadata/output occurrences and surviving references to a removed
secret. Scan original machinery before pruning; never fetch or retain a secret.
Extend existing foundation and actual-reader fixtures for these counterexamples,
unchanged persistent fingerprints and both complete temporary plans. No new
parser, recipe kind, check or runner. The two source-template metadata additions
and existing preparation reader are the only additional owners in this correction.

AWS [ExecuteChangeSet](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_ExecuteChangeSet.html)
removes other change sets, so later cleanup cannot require the original CREATE
description to remain available. Before an update, retain bounded validated
original stack/change-set/description/token/root-event facts in the existing
append-once resolved entry. Later output consumers must cross-check those facts
against retained original CREATE preparation/execution reservations, their exact
argument/base hashes and current stack identity/event evidence. Missing or
mismatched evidence denies use; it is not permission to adopt a same-name stack.
Fixtures must remove the old change set after update and prove later discard
works without weakening foreign-stack/no-replay checks. This revises only the
earlier persistent-description assumption; partial-creation cleanup remains a
separate custody path. Condition and secret syntax follow the AWS
[condition](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-conditions.html)
and [dynamic-reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references-secretsmanager.html)
contracts; local proof does not establish live execution.

Module-structure applicability: these are cohesive existing Python deployment
owners and one admitted package-acquisition helper, not a new TypeScript package,
Core public API or product runtime contract. No public index/export migration is
applicable. Existing source/fixture registration and finite failure owners remain
the consumer and diagnostic boundaries.

### Pre-billable cleanup-record capacity — 2026-11-27

Connected review found a required admission gap: the tested v1-receipt lifecycle
uses 60,931 of 65,536 bytes, but the actual entity publisher emits a v2 receipt
with three local qualification checks, and the accepted v2 schema permits larger
check sets. Rejecting a later cleanup write is not a sufficient capacity guard.
Do not increase the object limit, weaken receipt validation or add another store.

Extend the existing `environment_sessions.py`, `session_records.py` and their
`environment-sessions-test.py` consumer; no new source file or check. Replace
duplicated resolved parameter maps/lists with one complete checked CREATE map,
then a checked observed-map digest for each UPDATE. Reconstruct desired values
and previous-value arguments from the CREATE map and captured phase controls.
Preserve exact noncontrol drift rejection and observation-only cold recovery.
Retain each full stack incarnation once, with original creation request and
validated change-set/root-event digests in append-once evidence. Producer entries
reference these original owners rather than duplicating their proofs. Digests
do not replace original provider validation or exact subsequent comparison.

Explicitly revise the draft record schema; no live v1 session has been created,
so reject old shapes rather than silently reinterpreting them or adding a
compatibility store. The same immutable base captures a closed cleanup shape
derived from the checked source plan: stack names, template references and
supported discard phases. This is the existing session's captured data, not a
second registry or caller-provided byte allowance.

Before every conditional record write, the record owner constructs a virtual
completion of every already admitted CREATE stack, including the CREATE being
reserved now and uncertain/partial creations. Add missing incarnation, bounded
creation evidence, discard input/preparation/execution and exact-stack deletion
slots plus sealed state. Keep actual retained bytes for existing slots; use
conservative maximum serialized sizes for unknown fields. Require the complete
canonical result to fit before CAS/readback can grant submission. Untouched
future graph branches do not reserve resources or consume an allowance. A rejected
next creation/activation must leave the existing admitted stacks cleanable.

Use the existing supported 2,048-byte full StackId bound, fixed 64-character
digests, `es-` plus 32 hexadecimal token characters, and canonical generated UTC
reservation times bounded at 32 characters. Derive exact request/key overhead
from the existing closed operation shapes and captured names; do not use average
fixture sizes or workload-specific stack counts. Enforce the same bounds and
shape when actual entries replace virtual slots. Unknown original ownership
still denies cleanup; sufficient storage is not cleanup authority.

Diagnostic predicates: malformed/stale shape, unsupported identity/time length,
changed append-once incarnation/evidence, mismatched source/base, oversized valid
receipt before first CREATE, next-operation capacity exhaustion with earlier
cleanup retained, and conditional-write conflict/loss. Preserve finite owner
causes and no raw parameters/provider bodies. Actual caller assertions must prove
no billable submission on capacity denial, successful sealed cleanup after a
later denial, source-matched v2 full lifecycle, immutable original requests,
concurrency/CAS preservation and cold recovery without new resolution.

The existing session fixture and registered `aws-environment-sessions` check own
proof. Exploratory affected batch budget four minutes; final focused session
budget three minutes after review/preparation. Existing source/caller checks
reuse only unchanged evidence. This correction guarantees room for the bounded
teardown intents implemented here, not unlimited recovery labels or a physical-
leftover report whose representation is not implemented. The later qualified
controller must bind explicit bounded completion-evidence slots before live
creation; that requirement remains open. No AWS calls, new permissions, expiry
service or physical absence claim are part of this source correction.

### Concrete session CLI transport — 2026-11-27

Admit one helper at
`scripts/04.deploy/shared/provider-adapters/aws/session_cli.py`, owned by the
existing AWS session-adapter capability. Actual consumers are the connected
session operations, their foundation observations and authenticated package
acquisition; the existing session fixture must use it instead of its ad hoc
provider shim. It is not a new public workflow, execution engine or qualified
permission/expiry factory. S3 retention continues through `SessionRecords`.
No new folder, test file, check or cadence is needed. The recorded user approval
covers a necessary cohesive script above 50 code lines.

Reuse `cli.invoke_json` for one subprocess, its finite classification and no-retry
policy. Existing persistence transport is a precedent, not a reusable session
authority owner; do not copy its permissive whitespace-empty response policy.
Bind reviewed profile, region and copied environment; force one AWS attempt,
disabled configured endpoints/pager/autoprompt and bounded process/read/connect
timeouts. No caller CLI flags, query, endpoint, role, retention, force-delete or
rollback override. Serialize only closed operation arguments as JSON, using
bounded private temporary files where needed, not shell interpolation.

The supported operation set is the actual current consumer closure: CloudFormation
create/execute change set, delete stack, describe change set/stack events/stacks;
EC2 availability zones and managed prefix lists; ECR repositories, batch image
retrieval and scan findings. Each operation has an exact argument-key set from
its current caller. Unsupported operations or extra/missing keys reject before
subprocess execution. Future role/service and physical-resource operations need
their own admitted closed expansion; transport success grants no live authority.

Only execute-change-set and delete-stack accept an exactly empty successful body
through the existing `empty-string` policy; whitespace-only, malformed nonempty
JSON and non-object responses reject. Reads require JSON objects. Keep AWS CLI
automatic pagination enabled and reject remaining nonempty continuation tokens.
Translate the existing scan owner's exact `maxResults=1` into `--page-size 1`,
not a result cap. Do not clear tokens or introduce another paginator. The process
deadline bounds elapsed acquisition, not total buffered response bytes/page count;
do not claim otherwise. These policies follow the AWS
[execute](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/execute-change-set.html),
[delete](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/delete-stack.html)
and [pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)
contracts.

Expose one fixed-owner finite transport exception, preserving supported CLI
causes without native output. The session adapter must recognize that concrete
class at foundation/submission boundaries: independently importing `cli.py`
creates a different exception class, so arbitrary `.code` trust or an assumed
shared class identity is insufficient. Reconcile actual acquisition/observer
callers and sensitive-canary assertions in the existing session test.

Proof lane is local change, using the existing fake executable for every AWS
call, including ECR acquisition responses. Assert exact serialization/environment,
unknown-key rejection without invocation, response policy, complete observations,
finite denial/timeout, and durable-before-submit recovery for empty execute/delete
responses. Add the helper to the existing `aws-environment-sessions` input closure
and actual-import registration fixture. Extend diagnostics at these real callers;
do not run network qualification or broaden existing production transport policy.
Affected fixture budget four minutes, final session check three minutes after
consolidated/admission review and preparation. Relevant source/fixture/runtime
changes invalidate only their declared proof. Existing manual fixed deployment
routes remain unchanged; actual live provider/worker qualification remains open.

### Connected delivery-inventory correction — 2026-11-27

The registered package-custody run failed before its missing-engine assertion:
the independent delivery inventory reported the declared private-network template
and the reached session-record helper as unbound. A bounded reproduction traced
both causes to the existing inventory owner: it skips target profiles entirely
and skips non-operational proof fixtures when following executable references.
Adding duplicate workload-specific path inventories would not correct that owner.

Extend `scripts/04.deploy/inventory-deploy-control/delivery_inventory.py` and its
existing `delivery-smoke-test.py`, under the declaration-coverage standard. Resolve
only the reached profile's foundation template and instance-prerequisite template
fields relative to its target root, using the preparation owner's established
convention. Follow actual implementation references from reached executable proof
fixtures. Keep registration, consequential-effect classification and route roots
unchanged; catalogue input membership, comments, unrelated fixtures and arbitrary
profile text must not supply an ownership route. Invalid/escaping template paths
remain gaps. No new script, scope-specific exception, check, schedule or provider
operation is needed; source discovery stays offline and never executes a fixture.

Add connected positive/negative cases for the profile-owned template edge and
proof-fixture-to-provider-module chain, including the new transport only through
its real import. Preserve existing unrelated-input, governance-citation and
non-operational-fixture negative cases. In the existing package `qualification-test.py`,
correct its stale shell smoke path to `legacy/kanbien-staging/smoke-test-platform-shell-image`;
retain the expected unavailable exit 77 and the pre-build coverage gate.

Reuse `delivery-inventory-regression` and `package-custody-regression`. Initial
affected local fixture budget is three minutes for inventory and three minutes
for the package assertion; measure terminal results before any rerun. Inventory
source/fixture/profile convention changes invalidate these affected proofs;
unchanged AWS response/capacity inputs retain their independent evidence. Normal
preparation, current diagnostic coverage and source-matched final checks remain
required. This correction proves dependency discovery, not live qualification,
physical resource removal, expiry or savings.

Before final verification, reconcile the inventory check's exact copied-source
inputs: its connected session fixture reads five AWS session/CLI sources, and
its existing publication fixtures read two target adapters and the shared ECR
owner. Those actual reads must invalidate retained proof. Extend only the existing
catalogue input list and repository-contract registration fixture; do not select
the entire provider directory, add a registry or change lane/cadence/effects.
Budget one minute for the affected registration assertion. Normal preparation
must bind the corrected catalogue before the final focused checks.

### Original custody and reconciled deletion — 2026-11-27

The preceding prepared registered session, delivery-inventory and package-custody
checks all passed in 364.066581s, four seconds over their six-minute observation
budget. Continue the same capability: syntax-valid stack ARNs and qualified
callbacks alone do not implement original ownership or reconciliation.

Extend the existing AWS `environment_sessions.py`, `session_records.py`,
`session_cli.py` and `environment-sessions-test.py`; no new file, wrapper,
execution engine, registry, check or scheduling lane. The existing lifecycle
policy and AWS temporary-cleanup applicability own this behavior. Runtime
consumers are the same session API, record transport and actual fake-provider
fixture; current fixed production controllers remain unchanged. The existing
source-binding guide and diagnostic review rows must reflect the connected
implementation. Local proof does not qualify a live controller or its permissions.

Reconstruct original CREATE requests from immutable inputs and reservations.
Through the existing template/parameter/change-set owners, require the exact
preparation token, full stack and change-set identities, original template,
parameters and source-derived logical-resource/type set. Reject import/nested
effects, substituted identities, duplicates and incomplete observations. Preserve
this original custody before a subsequent UPDATE can invalidate the change set.
Partial creation has separate custody; successful output consumption continues
to require its original successful root event and ready stack. Partial resource
observations may contain only source-declared members; an omitted member is not
proof of physical absence.

Fresh deletion consumes a concrete reconciliation of every previously admitted
creation/activation/discard operation. Use exact token-correlated root events,
bounded timestamps and operation-specific terminal states, not status suffixes.
Unknown, delayed, denied or paginated observations block deletion. The existing
engine may retain a definite not-submitted result only when a precondition fails
before its provider call; interruption or a lost provider response cannot produce
that result. Retained attempts still only observe, never replay automatically.

The existing sealed state admits discard UPDATEs, creating a race with deletion.
Add a one-way deleting state in explicit draft schema v3, atomically with the
first delete reservation. First reconcile required prior discard work before
entering it, then recheck the closed operation set in fresh deletion's precondition.
Reject new creation, activation or discard input/reservation admission thereafter;
seal must never reopen it. Retained operations and exact deletion remain available.
Recheck creation/activation admission immediately before submission. This does not
make a record read and an AWS send atomic: an already reserved uncertain sender
remains blocking, and server-enforced deadlines remain a live prerequisite.

Retain compact, append-once original-custody digests and reservation-bound terminal
outcomes in the same versioned object. Extend its existing virtual completion
reserve before admission; keep the 65,536-byte bound and exact original requests.
These digests do not replace the later physical-ID manifest. Existing schema v2
has no live sessions; do not add a compatibility reader or a second store.

Admit only the required closed reads in the existing transport: get-template with
StackName and TemplateStage=Original, optionally ChangeSetName, and
list-stack-resources with StackName. Preserve exact key sets, full IDs once known,
pagination checks, finite safe errors and no caller role/retention/force override.
AWS documents the [stack states](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Stack.html),
[change-set evidence](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeChangeSet.html)
and [event token lineage](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_StackEvent.html).

Diagnostic predicates and actual-consumer counterexamples: foreign placeholder;
changed original token/template/parameters/type; terminal partial CREATE without
successful functionality; late reserved execution; missing/denied/incomplete
reads; early delete with unfinished discard; seal during preflight; concurrent
discard/delete CAS; changed append-once custody/outcome; lost retention and
capacity exhaustion. Require no provider submission for denial, no replay for
retained intent, exact finite reasons and exclusion of sensitive canaries.
Reuse the existing aws-environment-sessions fixture and catalogue input closure;
reconcile diagnostics and review before normal preparation/final focused proof.
Budget four minutes for affected exploratory cases, then four minutes for the
registered session check; measure overruns without restarting uncertain work.
Source/fixture/transport changes invalidate affected evidence only. Independent
expiry, effective permissions, physical completion, reviewed recovery labels,
successor admission and the workload command remain necessary subsequent work.

### Approved task-branch package publication — 2026-11-27

Read-only inventory and connected design found seven main-only boundaries in the
existing publication path. The adopted goal already authorizes necessary task-
branch/image publication, not a main merge. Extend that same route; do not publish
locally or create a second publisher. Keep production's default ref unchanged.

In the existing pipeline catalogue, add `additional_permitted_source_refs` for
the entity and persistence rows only, containing exactly
`refs/heads/chat/2026-11-26-22-09-reducing-aws-bill`. Their optional
`custody_acquisition.source_ref` selects that ref; omission still means the base
`permitted_source_ref`. No wildcard, tag, duplicate, malformed or unapproved ref
is accepted. Other current pipeline selections and identities remain unchanged.

Reuse the existing `ecr_publication.py` owner for one pure source-policy validator
and its fixed publisher context. Add the pipeline ID to the two static target
`publication.py` bindings; resolve only their source-owned catalogue and compare
the selected workflow, actor and destination against those bindings. Their
existing CLI gains a read-only `validate-source` operation: no provider call,
write, reservation, qualification claim or workload effect. The two existing
GitHub workflows run that gate after the already pinned PyYAML setup and before
project dependency installation, qualification or credential assumption. Keep
protected environment, reservation-before-push, scan, SBOM, attestation and safe
receipt steps intact; their existing workflow guards enforce the new ordering.

Affected readers are `core-platform-target-declaration/script.py`, the existing
AWS `preparation-inputs.py`, and `package-custody-receipt/acquire.py`. Declaration
and preparation consume the shared selection; preparation captures the exact
acquisition ref in the existing publication facts. Acquisition requires that ref
in run/artifact branch and certificate/workflow checks, retaining exact SHA and
invocation binding. Session intent and runtime inputs remain unchanged: selected
run ID and source revision are still the only acquisition inputs. Keep actual
import/copy dependencies complete in existing inventory/check registration; no
new parser, registry, check, schedule, script file or required review is added.

Diagnostic predicates and proof use the existing entity `pipeline-test.py`,
`publication-test.py`, `workflow-test.py`, persistence workflow guard coverage,
preparation `runtime-configuration-test.py`, and package `qualification-test.py`.
Cover unchanged main compatibility, approved exact task ref, renamed composition,
duplicate/malformed/unlisted refs, missing/changed catalogue identities, source
gate bypass/reordering, run/artifact/certificate branch mismatch and source SHA/
workflow mismatch. Rejections precede provider activity; preserve original
finite reasons or define a finite source-policy reason without supplied values.
Uncertain publication remains observation-only, never automatic push replay.

Budget five minutes for affected exploratory cases and six minutes for selected
final focused checks after consolidated review, diagnostic reconciliation and
normal preparation. Measure overruns and retain running handles. Later edits
invalidate only affected input identities; reuse unchanged evidence. This source
increment does not publish anything or qualify live branch/environment access.
The fixed cleanup-controller package, its exact destination/access declaration,
supported provenance-verifier setup and protected live environment observations
remain required subsequent work. Do not loosen the target check's exact pipeline
inventory to admit an undeclared controller or alter protected-environment policy.

### Temporary retention from creation and bound failure policy — 2026-11-27

This connected correction supersedes the earlier protected-initial-creation
approach above. The user explicitly permits discarding all temporary application
data. Existing `Metadata.DiscardControls` therefore select disposal from the
first temporary CREATE and throughout activation, not only during teardown.
Production/default preparation and application code remain unchanged. This
checkpoint preserved running backup retention; the temporary-zero-retention
amendment below supersedes that choice without changing production.
The lifecycle standard and ADR 0044 are reconciled before implementation.

Reuse `preparation-inputs.py::discard_projection` on each original temporary
phase projection once. Capture creation and stopped discard as the same checked
template, and independently apply the same projection to activation. Keep the
closed supported resource/path inventory, exact expected source values and all
unrelated template bytes; do not accept already-modified controls or arbitrary
cleanup templates. Extend `runtime-configuration-test.py` at its actual reader
boundary for initial/active disposable DB settings, unchanged production,
unsupported controls and full-plan revalidation.

The connected consumers are the existing `session_records.py`,
`environment_sessions.py`, `session_cli.py` and `environment-sessions-test.py`.
Version the draft record to v4 and add native boolean `disable_rollback: true`
to its shared non-delete request constructor, used by real requests and virtual
completion capacity. The actual execute transport requires and sends exactly
`DisableRollback=true`; reject missing, false, integer and conflicting
`OnStackFailure` policy. No live old-version records exist and no compatibility
reader, second store, retry engine or provider default is introduced.

Reconcile CREATE_FAILED/UPDATE_FAILED only with that reconstructed policy,
original CREATE custody, exact reserved token, terminal root event and matching
current stack. Accept observed EXECUTE_FAILED only through this connected
reconciliation, not as a standalone proof. Preserve the distinction between
partial-creation cleanup custody and successful output consumption. Require the
actual current discard template and complete stopped values in every executed
terminal state: the counterexample is a failed activation with active counts
when initial/discard template bodies already match.

Allow only the first cleanup-only discard preparation after a positively
reconciled failed activation of an originally successful CREATE. Reuse original
success proof without relaxing ordinary output readiness; preserve all noncontrol
values. Its existing qualified preflight and exact change-set review still
prohibit additions, replacements, unrelated changes or resumed partial initial
creation. Sealing/revalidation and single submission stay mandatory. Unknown or
retained discard attempts remain observation-only; a failed cleanup attempt does
not silently gain another label or replay. Actual physical quiescence, resource
manifest, recovery slots and independently armed expiry remain later obligations.

Concrete review correction: the adapter's old change-set inspection ran during
later reconciliation, not before execution, and allowed arbitrary non-replacing
Modify rows. Reuse that owner before a fresh discard execution, observing an
AVAILABLE change set and deriving the exact changed resource/property keys from
the bound current phase and captured discard. Require only those static direct
property modifications with no replacement, extra changes or ambiguous details.
Reuse applicable existing change-review primitives rather than another parser.
Fixtures must report real differences, not pretend every resource is modified;
extra, missing, dynamic or replacement changes must stop before provider send.

Diagnostic predicates remain in those owners: malformed source controls keep
the preparation reader's finite discard reason; absent or changed record policy
fails closed at record/request validation; substituted provider policy fails
custody reconciliation; missing or mismatched token/root/current state retains
the existing terminal/custody reason; active failed updates report
`discard-required` before deletion admission. Existing caller tests must assert
the exact reason, unchanged record/admission and no outgoing mutation, not just
nonzero status. Preserve safe context and exclude native responses and secrets.

No script file, check, review requirement, schedule, permission or source lane
is added. Existing registered preparation and session checks own this proof;
their actual dependency inputs remain connected. Budget four minutes for the
affected preparation cases and five for session exploratory cases, then inspect
and freeze the complete change, reconcile diagnostic source identities and run
normal preparation before a measured affected registered batch. Reuse unchanged
publication evidence. Report timing overruns and genuine unresolved boundaries;
passing local cases do not qualify the live controller or establish savings.

### Bounded physical identity handoff — 2026-11-27

Next, extend the existing session adapter/record owners, not the fixed-name
restore controller, to retain the physical identities they currently discard.
The existing `_inspect_stack` observation already binds exact original StackId,
CREATE custody and complete `list-stack-resources` responses. Derive a sorted
logical-resource/type index from the captured template, bind its count/digest in
the existing cleanup shape, and retain a source-indexed identity digest for every
resource. Do not prematurely replace the full 117-resource graph with 35 parent
anchors; parent coverage and typed absence still need separate proof.

Use an explicit versioned draft record extension and the existing conditional
ownership write. Per index, distinguish unknown, positively never allocated and
an allocated identity digest; only unknown may advance. Never replace an allocated
incarnation, erase it when a later row is missing, or infer nonallocation from an
empty physical ID, missing row or failed root status. The initial narrow
never-allocated case requires sealed/deleting admission and positively unexecuted
original creation, without an unresolved execution reservation; an open
REVIEW_IN_PROGRESS stack is insufficient. Partial executed failures retain
unknowns. Bind each projection to original custody and
the complete response observation without retaining raw provider bodies.

Fresh exact-stack deletion must capture and retain this manifest through its
existing reconciliation before reservation/send, rejecting changed incarnations
or lost/conflicting retention. The record's delete-reservation gate and immediate
send check require that exact incarnation's manifest; the existing operation-set
digest alone cannot prove its retention. Merge discovery conditionally alongside
custody, keep unchanged observations idempotent and bound observation metadata
rather than append an unlimited history. A manifest fingerprint guards fresh
reservation/send alongside the operation fingerprint. Later discovery must not
rewrite a retained deletion request or prevent its observation-only recovery;
a changed fingerprint may stop an unsent reserved operation, never permit replay.
That case retains an unresolved recovery obligation. Unknown source slots are
explicitly retained; they do not prevent removal of the independently proved-owned
exact stack, but cannot
satisfy later completion or successor admission. Do not add resource-specific
deletion, absence claims or an ownership adoption shortcut in this increment.

The same adapter owns read-only reconstruction from the original unique StackId,
matching each raw physical identifier to its retained digest and exact source
index before any later consumer can use it. Missing/expired/incomplete lineage or
a changed identity remains unknown/rejected, never absent. AWS retains deleted
stack resource information for up to 90 days, not indefinitely; this bounded
recovery dependency must remain explicit. [AWS ListStackResources](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_ListStackResources.html)
Share the source-index projection rather than the whole `_inspect_stack` routine:
deleted-stack reconstruction cannot require its earlier CREATE/UPDATE root to
remain the current stack status. A contradictory allocated row prevents claiming
the graph was never allocated.
There is no asserted universal maximum for a raw physical identifier; digest
retention avoids inventing one. Typed native identities, DB immutable lineage,
generated logs/backups, actual absence and recovery attempts remain subsequent
connected work rather than implied coverage.

Extend `_completion_size` to reserve every indexed identity/observation slot for
each admitted CREATE before granting its submission, using the same actual
representation, expanding every still-unknown slot even in an already retained
partial manifest, then prove the complete serialized fixture bound. Keep 65,536
bytes and preserve earlier cleanup when a later graph exceeds capacity. Existing
`environment-sessions-test.py` covers monotonic discovery, full source membership,
unknown partial rows, exact reconstruction after deletion, missing lineage,
substitution, CAS/lost retention and pre-creation capacity. Finite owner reasons
must reach that actual caller with no provider mutation on rejection. Root owns
consolidated review/diagnostics/preparation before final proof. No new script,
check, store, schedule or provider mutation is admitted; budget five minutes of
affected exploratory tests. Keep full registered session proof for this stable
connected batch rather than rerunning it immediately before known input changes.

### Next cleanup and independent-controller boundaries — 2026-11-27

Read-only inventory found 117 resources across 18 types. Prefer direct native
observations of exact reconstructed identities, not a generalized VPC membership
registry or replacement of the full identity manifest with parent anchors.
Route-table associations support an exact association-ID filter; explicit log
groups support exact-name selection. Keep only the genuinely necessary narrow
relations: a security-group rule's target group (not its referenced source group),
and an ECS service's owning cluster when the cluster has already disappeared.
Those relations require checked source and native pre-deletion evidence; an
opaque CloudFormation rule identity is not assumed to be a native rule ID.
Unknown identities and absent relationship evidence remain unresolved.

The next bounded implementation extends existing `environment_sessions.py`,
`session_cli.py`, `response.py` and their existing session/recovery fixtures.
`session_records.py` may extend only its existing terminal-state vocabulary for
shared delete-event validation; no new record field or completion state is added.
Add read-only native resource observations through the retained original delete
intent and correlated terminal root event. Reuse `execution_events` and the
existing timestamp/identity validation, rather than another event parser.
Direct reads require exact response identities, complete pagination and only
operation-specific documented missing errors. Malformed/denied reads remain
unknown; a different returned resource cannot establish absence. Return safe
logical-resource/type/status observations without raw provider bodies, identifiers
or secrets, and distinguish absent, present, inactive and unsupported/unknown.
No source policy, permission, mutation, completion transition or second store
is added. Security-group rules, ECS service parent coverage, late identity
retention and generated artifacts remain separately required before completion.
Task-definition `INACTIVE` is deregistration, not physical absence or proof that
tasks stopped; preserve that distinction. A scheduled secret deletion is not
absence. Native database absence says nothing about its snapshots/backups.

Diagnostic predicates belong to those existing owners: missing/mismatched delete
intent, token/root/current-state contradiction, invalid native identity, malformed
response, pagination remainder and known provider failure retain distinct bounded
reasons. Existing caller fixtures must assert exact reasons, no native mutation,
no record writes and no false absent result; valid exact observations are separate
positive cases. Budget five minutes for affected exploratory cases, followed by
parent consolidated review and source-matched diagnostic reconciliation. No new
script/check/schedule is planned; closed-read-set additions require the existing
bounded admission delta review. Keep final registered proof for the stable
connected cleanup batch and reuse unchanged publication evidence.

Connected proof correction: `recovery-test.py` is already catalogued, but its
existing budget wrapper selects only particular methods; the new native
classification method would otherwise remain exploratory-only. Extend the
existing runtime-alignment wrapper's `--environment-sessions-only` branch to run
that exact reused taxonomy method before the session fixture, add its source to
the existing `aws-environment-sessions` inputs, and extend the existing
`repository_contracts_test.py` dispatch/failure/fingerprint assertions. Do not
add a check, copy the assertions into another fixture or run unrelated recovery
methods. The added pure test measured 0.023s; budget two minutes for the focused
registration-owner proof. This is actual child-closure correction, not a new
scheduling lane or default full-regression requirement.

Independent-controller inspection confirms there is no complete retained setup
factory yet. Finish the cleanup owner first; then bind one real qualified cleanup
image, retained records and the fixed Standard workflow/CodeBuild project from
ADR 0044. Do not deploy placeholder images or route retained infrastructure
through disposable-session deletion. Both foreground and expiry should invoke
the same versioned workflow; ordinary callers must not receive direct CodeBuild
start, project-update or role-substitution authority. Protect that project's
configuration while a bound session remains outstanding: a workflow version alone
does not freeze the project or its IAM permissions. Authorize the exact workflow
version through the base state-machine ARN and `states:StateMachineQualifier`.
[AWS version authorization](https://docs.aws.amazon.com/step-functions/latest/dg/auth-version-alias.html)
The documented `codebuild:source.buildspec` condition supports only `Null`:
reject override presence, not an invented content-equality condition.
[AWS CodeBuild condition keys](https://docs.aws.amazon.com/codebuild/latest/userguide/action-context-keys.html)
Source/store validity, immutable package qualification, effective permissions,
verified running expiry and live cleanup remain separate unfinished boundaries.

### Complete leftover coverage and new-instance log ownership — 2026-11-27

The direct native-observation increment is frozen and parent-reviewed. Its
affected exploratory batches passed within 205.8677 seconds of the five-minute
budget, including the response taxonomy. It distinguishes exact absence,
inactivity, nonallocation and unresolved observations without mutation or a
completion claim. The reused taxonomy method is now connected to the existing
session wrapper; its registration-owner test passed in 8.679 seconds. Final
registered connected proof remains deferred until cleanup inputs stabilize.

Complete the remaining bounded identity handoff in the existing session adapter,
record owner, closed transport and session fixture; do not introduce another
registry, store or general CloudFormation expression evaluator. Extend the
source-derived cleanup shape with only the narrow additional relationships needed
by its actual consumers, and explicitly version the changed draft record schema.
Bind security-group rules to their target GroupId, not SourceSecurityGroupId,
using only the checked direct Ref forms in the source. Bind ECS services to their
original resolved ClusterArn and verify native service/cluster correspondence
before a parent's disappearance can cover a child. Missing relationships remain
unknown. A removed owned group cannot leave its rules behind, but a referenced
source group's removal does not prove a target rule was removed.
Native rule correspondence must additionally match the actual declared protocol,
ports and peer CIDR/group/prefix fields, using only the literal/direct Ref forms
present in the checked source and existing parameter projection. Unsupported
expressions cannot be guessed or promoted to a general expression interpreter.

Retain an append-once digest of each observed database DbiResourceId at the first
owned native observation and require it for a positively allocated database
before fresh deletion.
After deletion, inspect complete snapshot and retained automated-backup results
and compare immutable lineage, not a reusable database name. Preserve raw matching
identities only inside the authorized cleanup consumer, never public diagnostics.
Native instance absence alone cannot complete database cleanup. Capture the
Cloud Map namespace's hosted-zone ID before deleting its namespace, verify the
private zone/name/VPC relationship, retain its documented bounded identifier,
and use exact GetHostedZone afterwards. Missing capture cannot be reconstructed
from a guessed zone name or namespace absence.
The existing response owner adds only `route53/get-hosted-zone`'s documented
`NoSuchHostedZone` missing code, with the existing operation-specific taxonomy
method covering exact read, wrong mutation/service, denial, expiry and arbitrary
not-found text. Its source is already in the connected session check closure;
no new check or classifier control flow is needed. Budget thirty seconds for
that focused pure method, counted inside the handoff's exploratory allowance.
[AWS GetHostedZone errors](https://docs.aws.amazon.com/Route53/latest/APIReference/API_GetHostedZone.html)
For positively allocated namespaces the zone handoff is likewise a fresh-delete
prerequisite. Preserve the existing unknown-allocation rule: an unresolved slot
does not prohibit deletion of an independently proved-owned exact stack, but
cannot satisfy completion or imply absence of backups/zones. Retain that
uncertainty and report bounded failure if it cannot later be resolved. Positively
never-allocated resources retain their separate proved exemption. This does not
grant speculative native deletion or weaken known-identity capture requirements.

Add an explicit late-identity retention route for closed admission. It must
reconstruct original creation custody and exact stack incarnation, observe that
original StackId, and reuse the existing physical projection and monotonic CAS
merge. It does not require the old pre-delete root status and does not rewrite,
erase or replay a delete request. Unknown slots may become proved identities;
known identities and never-allocated conclusions cannot be replaced. This route
does not recover a lost database lineage or hosted-zone relationship by guessing.
Reserve the actual maximum serialized representation of all admitted additional
fields through the existing completion-capacity owner before CREATE; no arbitrary
headroom allowance. Reprove the full source graph after its resource count changes.

Generated logs will become explicit resources in the existing foundation and
persistence templates: the Container Insights performance group and the two RDS
export groups. Preserve export/insights settings and all application behavior.
Derive names from the existing prefix and order cluster/database creation after
the corresponding groups, without cyclic resource references. New production
instances retain these groups with DeletionPolicy and UpdateReplacePolicy Retain;
leave retention duration unspecified rather than shortening it. Extend the
existing declared DiscardControls reader narrowly for those two LogGroup
attributes, requiring exact expected Retain-to-Delete transitions. Temporary
creation and activation use the same declaration-owned projection, not an
application switch or a second set of workload templates.

This is a new-instance change, not automatic adoption of existing generated logs.
Existing production/legacy deployments remain on their current definitions.
Do not relax the existing create-only or exact budget-update gates, auto-import
matching names, or delete/recreate existing groups. Consuming these new resources
in an existing deployment requires a separately governed, explicitly approved
import-only migration preserving its observed retention/encryption/protection.
No such migration is implemented or authorized by this increment. The current
persistence source is close to the inline template limit: compact YAML formatting
at that same owner while proving parsed semantic equality apart from the admitted
resources/dependencies/metadata; do not increase or bypass the transport limit.

The template/preparation increment owns those two templates, preparation-inputs.py
and its existing runtime-configuration/foundation fixtures. The leftover-handoff
increment owns environment_sessions.py, session_records.py, session_cli.py and
environment-sessions-test.py. Keep edits disjoint, use the existing registered
checks, and reconcile their real input closure at the stable connected boundary.
Budget four minutes for affected template/projection exploratory tests and eight
minutes for affected handoff tests, measuring attempts and retaining unchanged
evidence. Parent review must inspect actual no-write/no-send/identity-mismatch,
lost-retention and capacity assertions, not just totals. Generated-artifact
mutation, bounded recovery, completed-state/successor admission, effective
permissions and the independent live controller remain separate unfinished
boundaries; no new provider mutation is authorized by passing these fixtures.

### Cold recovery and fixed controller composition — 2026-11-27

Read-only tracing found that the current compact record retains a source-plan
digest but not a complete plan. Revalidation requires that typed plan, while the
new-session loader correctly rejects expiry. Do not fabricate a pre-expiry clock
or loosen the new-session reader to run an independent cleanup worker.

The original lifecycle policy's maximum duration can differ from both the actual
session interval and its operator-approved maximum. Retain exactly one scalar,
`base.lifecycle_max_duration_seconds`, captured from the checked original plan.
It is a positive native integer at least as large as the original interval, part
of immutable base hashing and actual capacity accounting; do not guess it during
recovery or introduce a new arbitrary policy limit. Include this field in the
already-changing draft v6 record schema, and require the session adapter's base
comparison to match the typed source intent. Older draft shapes remain rejected.

Extend the existing preparation reader with cold recovery using the positively
observed existing record and its actual observation clock. Reconstruct the exact
original explicit temporary/discard intent, reuse `read_existing` and
`_capture_session_plan`, and verify both the captured source-input digest and the
canonical complete-plan digest before returning the ordinary typed plan. The
actual controller caller must supply the original checked record observation,
not accept a user-supplied digest as ownership. Recovery is source reconstruction,
not admission, expiry rearming, package reacquisition or a record write. Existing
session records/adapter fixtures own the real-caller roundtrip; the preparation
fixture owns changed-policy/source/digest/clock, missing/wrong-type-field and
expired-versus-future-start cases. Budget two minutes for these affected cases,
reusing unchanged projection proof. Coordinate source freeze before connected
session tests rather than invalidating a running batch.

Controller tracing also identified required work that remains unimplemented:
concrete pending/terminal observers (not arbitrary callback dictionaries),
session-bound workload migration/readiness/verifier inputs, a bounded expiry and
completion record, successor admission, reviewed recovery and a real package.
All discard work must finish before the first deletion closes that phase; teardown
is reverse-dependency ordered and cannot infer child absence from a reserved
delete. Foreground and expiry will use the same fixed qualified worker.

The selected permission direction separates deadline-bound creation submitter/CF
execution identities from cleanup identities that survive expiry. Ordinary
callers must lack direct stack writes, CodeBuild start/update/override and role
passing; the worker binds phase-specific service roles to exact requests/custody.
AWS has no ECS desired-count-zero permission condition: the qualified source
and change review enforce stop-only updates. Exact future physical IDs cannot be
enumerated before allocation. A protected, source/custody-bound per-session role
binder therefore needs implementation and operation-specific qualification;
general policy-edit authority or tags alone are not sufficient. This design note
does not claim effective permission proof or authorize an unqualified setup.

The current regional database artifact observer deliberately reports cross-region
backups as unknown. Empty regional results cannot prove global absence. Before
completion is admitted, qualify a concrete source/permission and native-observation
boundary for replication or retain that unresolved result; do not silently omit
it, widen deletion scope or let an unknown observation count as cleanup success.

### Concrete operation and stop reconciliation — 2026-11-27

The existing adapter's terminal-only helpers cannot safely serve a polling
controller: attempting execute while preparation is pending would consume its
exclusive reservation. Extend the existing `SessionOperations` owner in
`scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py` and its
existing `environment-sessions-test.py` fixture after the v6 handoff freezes.
No new file, registry, operation label, recurring check or automatic retry is
needed. The existing session registration remains the proving owner. Reuse
`session_records.py` for already-supported terminal retention, changing that
owner only if the connected implementation demonstrates a necessary correction.

Expose `reconcile_operation(kind=..., stack=..., phase=...)` for the existing
creation/activation/prepare-discard prepare/execute combinations and delete/delete.
Derive every request, token, template and incarnation from the checked plan and
positive record; accept no observation callback or caller-supplied outcome. Return
only operation, finite status/reason, immutable request digest and checked provider
status. Distinguish unreserved, positively not-submitted, authenticated pending,
ready, terminal succeeded/failed and unknown. Absence of an execution event is
unknown, not permission to retry. Invalid inputs, changed intent and identity
contradictions retain existing finite failures; unavailable provider evidence
retains supported uncertainty without raw status reasons or parameter values.

Factor existing request/custody identity checks and correlated latest-root-event
parsing out of `_reviewed_change`, `_event_outcome` and `_inspect_stack`; retain
their strict terminal-only behavior for existing mutation gates. Pending
preparation does not require completed changes, but does require available
identity evidence. Ready requires exact complete source/effects review and
CREATE_COMPLETE/AVAILABLE with no execution reservation. Historical successful
execution is not current readiness. Append only authenticated terminal outcomes
and custody through existing CAS; pending, unknown and unchanged observations do
not write. Never replace retained preparation evidence merely because mutable
ExecutionStatus changed. Connect `_submit` to the concrete observer and recheck
readiness immediately before first execution, keeping stronger discard-effect
checks. Polling ready is advisory, not reusable authorization.

Expose `reconcile_stops()` only for sealed/deleting sessions. Reuse one stopped
template/parameter predicate from `_cleanup_readiness`, returning reverse-order
not-started, never-allocated, stopped, stop-required, pending, blocked or
delete-observation-only rows. It must finish every stop before first deletion,
preserve the atomic delete barrier, avoid no-change discard updates and route
reserved deletes to observation. A failed/uncertain/not-submitted reservation
never receives an automatic replacement label. Existing authenticated first
cleanup after failed activation remains supported; new recovery mutations need
their own admitted predecessor/label authority.

Affected diagnostic predicates and fixture assertions: pending preparation must
not reserve execute or send; lost response followed by missing and later matching
events must not resubmit; failure/expired cold reentry must preserve finite safe
reasons; historical CREATE success cannot override pending/failed activation;
no-op stop and failed-activation stop share the same exact stopped predicate;
one unresolved stop blocks every fresh delete; retention conflict/lost readback
cannot become success. Use the existing fake CLI and real reservation caller,
including sensitive canaries. Budget five minutes of affected exploratory tests;
defer registered full proof until the connected controller inputs stabilize.
Unchanged v6/native/cold-recovery reviews are reused, not rerun indiscriminately.

The observer exploration budget is extended once to 450 seconds after measured
257.963 seconds: five initial methods passed in 26.588 seconds; the next batch
took 231.375 seconds with three passes and one fixture-only failure. The failed
discard-template case hit an unrelated fake-provider native-resource expansion
before the intended CloudFormation response. Correct that fixture routing and
prove the intended predicate. The extension is only for that discard matrix,
definite-not-submitted stop decisions/no replay identified in parent review,
and physical/custody recovery affected by removing eager physical retention from
the new terminal observer. The full 120-resource v7 capacity case already passed
at 54,786 actual / 60,497 conservative completion bytes, including four delete
outcomes; reuse it while record shapes/bounds remain unchanged. Do not rerun the
full suite or the capacity case for these timing/selector corrections.

The eight-case correction batch passed in 193.568 seconds, taking cumulative
exploration to 451.531 seconds (1.531 seconds over its allowance). A final
15-second input-boundary allowance covered only the new closed-keyword guard;
that method passed in 2.135 seconds. Total observer exploration is 453.666
seconds. Parent review is closed against the corrected stopped-state logic and
actual no-send/no-replay assertions; the three migrated historical-result/write
count expectations still require the connected registered proof. No broad or
capacity rerun was performed.

### Retained workload task storage and runtime identity — 2026-11-27

Read-only tracing confirmed that changing cluster names alone is insufficient:
existing task runners use local reservation/admission/receipt files, and their
family, log-group and task-ARN checks retain persistent identities. Temporary
workers must reuse those operation and proof owners with checked runtime bindings
and durable storage. No temporary task may run through a monkeypatched module,
an unchecked CLI override or a local-only journal.

First consolidate the duplicated entity immutable reservation implementation:
extend `shared/provider-adapters/aws/resource_reservation.py` with one overridable
record-construction method, retaining its current default record exactly. Adapt
`lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-control.py`
AttemptStore to that owner, preserving its five-field historical record, exact
canonical key/alias rules, local safety checks, request/time validation and finite
failure vocabulary. Allow explicit injected read/create storage through the
existing shared protocol; only positively confirmed creation grants freshness.
Keep all existing task CLI routes, runtime identities and local defaults unchanged
in this first increment. Remove superseded duplicate write/read/reserve mechanics,
not compatibility formats that have actual retained consumers. Existing
task-control tests prove local parity, aliases, uncertainty, sensitive canaries,
retention-before-send and no replay through the actual caller. Budget three
minutes for affected exploratory proof. No new file/check/cadence; update the
existing metadata consumers and actual registration input closure if needed.
The shared helper's new entity consumer requires its bounded admission delta
review before preparation, not a new recurring review mechanism. Coordinate
source freeze with session tests because the helper is a shared input.

The following connected storage work is required before enabling temporary task
execution. Reuse `task_journal.py`'s predecessor/request/completed-proof decision
as one pure function shared by its existing locked local route and a conditional
storage-backed reservation route. Do not imitate filesystem locks in S3. Extend
`session_records.py` with closed task-step storage adapters: immutable intent and
receipt objects are retained under derived session keys, but only the existing
parent record's CAS, capacity check and positive readback grant fresh launch.
Orphan child objects grant no authority; lost parent writes become observation
only. Attach bounded exact version/digest/length references, retaining existing
receipt formats outside the compact parent. Task IDs derive from the existing
captured workflow's selected step IDs and proof-label rules, not arbitrary caller
keys or speculative retry slots. Admit predecessor advancement only through its
existing completed-proof/explicit-successor rule. Preserve the 65,536-byte parent
bound and existing intent/receipt bounds; measure complete reference and cleanup
reserve before admission rather than assuming the current graph leaves room.

The journal mechanics delta is admitted separately to avoid overlapping the
session-record work: extend existing `shared/provider-adapters/aws/task_journal.py`
and the persistence `task-operation-test.py` fixture only. Extract the existing
request/predecessor/completed-proof choice into one pure owner function, used by
the unchanged locked local reserve and a `reserve_retained(storage, key, ...)`
route. The latter uses checked read/compare-and-reserve callbacks, preserves the
same operation fields and canonical integrity, and grants freshness only after
positive conditional retention; conflict, lost readback or malformed storage
results cannot permit submission. Keep local locking/history/record formats and
existing callers unchanged. Controlled storage assertions must cover request
drift, missing/wrong predecessor, incomplete proof, exact reuse, concurrent/lost
retention and sensitive failures, plus the actual existing local caller cases.
Budget three minutes of affected exploration; no new file/check/selector. Future
BoundOperation and candidate-verifier use is required connected work, not claimed
by this helper-only proof. The session adapter will own atomic head/history and
admission, not this generic decision function. Coordinate source review and
registration closure before the connected batch's final proof.

Runtime composition must use original created-stack custody/current-state checks
to expose requested source-declared outputs, exact physical IDs and captured
templates/parameters. Existing persistence and entity task binding owners consume
that view and check exact cluster, task definition/revision, image, roles, network
and log configuration. Persistent entrypoints keep their current defaults. Add
receipt-store seams to existing completion/preflight owners; never write temporary
receipts into production release evidence. Recheck sealed/expired admission just
before RunTask as well as parent CAS, retaining positive pre-send rejection
without recycling the reservation. Observation and receipt retention survive
expiry; effective IAM deadlines remain mandatory. This is not yet implemented,
and further owner-specific edits must record their exact consumer/test delta
before execution. Reuse existing task, persistence and session registrations.

The next receipt-owner increment is limited to existing persistence
`proof-receipts.py` and `proof-receipts-smoke-test.py`. Its current `persist`
returns a local Path and the acceptance callbacks write into production evidence
before notifying the journal; that must not be the temporary worker's route.
Add optional checked task-ARN-prefix context to the existing make/validate/context
owner, retaining its persistent default and this target's account/region. The
caller must obtain the prefix from the future checked runtime view; accepting a
well-shaped prefix alone grants no execution authority. Apply it consistently to
the task and replacement-successor fields, without copying the receipt schema.

Add `retain(receipt, *, root, storage=None, task_arn_prefix=...)` and
`read(reference, *, root, storage=None, task_arn_prefix=...)`. A reference has
exactly the existing journal facts `path` and raw-byte `sha256`. Local selection
preserves `persist` and its Path consumers. Retained selection must not call
`persist` or touch production evidence: derive the closed label from the checked
proof type/operation/task ID, use storage's `read_receipt(label)` and
`retain_receipt(label, proposed_bytes)` methods, and require positively retained
bounded bytes. Keep the existing formatted JSON/newline and first-receipt rule;
extract its substantive comparator once and share it across both routes. A
changed collection time may reuse the original proof, while changed substantive
facts reject. Storage owns exact child-version/digest retention and session
binding; the receipt owner checks raw hashes, shape, substantive equality and
safe finite failures. Missing, wrong-type, excessive, conflicting or uncertain
storage must not produce an accepted reference. The retained read limit is the
existing 1 MiB receipt boundary; no parent-record limit is increased.

Use the existing receipt fixture for persistent compatibility, temporary-prefix
and foreign-prefix rejection, first-proof reuse, exact raw-byte hash checks,
no local write on retained selection, malformed/lost storage and sensitive
canaries. Budget three minutes of affected exploratory proof. No new file,
receipt format, recurring check or completion claim; actual acceptance callers,
runtime producer and S3 storage remain required connected work. Extend the
existing effects/consumer metadata for the injected-storage boundary and complete
its bounded admission/diagnostic review before final preparation.

### Checked runtime view handoff — 2026-11-27

After the observer increment freezes, extend only the existing
`environment_sessions.py` owner and `environment-sessions-test.py` fixture with
`runtime_view(*, stack, required_outputs)`. This is a concrete evidence handoff,
not a new task engine or permission to launch. Select only a captured stack and
unique requested names declared by its captured template; no caller-supplied
template, parameter, physical ID, phase override or provider dictionary is
accepted. The adapter determines the current admitted phase itself.

Reuse `_owned_stack`/`_successful_stack`/`_inspect_stack` to establish original
successful creation and exact current readiness, including every later retained
operation. Match the captured current-phase template, original non-control
parameters and original stack incarnation. Retain the resulting custody,
outcomes and physical fingerprints through the existing positive CAS owner,
then reconstruct physical IDs through the existing monotonic lineage reader.
Unknown, never-allocated or changed required resources cannot become a runtime
binding. This method may retain evidence but performs no CloudFormation or
workload mutation; failed retention returns no usable view.

Return one copied closed internal view with schema
`deploy/aws-session-runtime-view/v1`, the original six-field `binding`,
`source_plan_sha256`, `account`, `region`, `component`, `stack`, `stack_id`,
current `phase`, `template_reference`, parsed `template`, checked `parameters`,
logical-resource map `resources` (each row exactly `type` and `physical_id`),
the selected `outputs`, original `custody`, and `observed_at` (an exact nonnegative
integer from the existing records clock, never an identity or authority). The current phase
is the latest authenticated non-not-submitted execute among creation,
activation and prepare-discard. Successful historical creation cannot conceal
a pending/failed later phase. Resource IDs and outputs are internal task-binding
inputs, not diagnostic projection. Callers obtain foundation/workload/dependency
views as needed and must not treat one component's view as proof of another.
No view survives a later admission guard as reusable authorization.

The existing fixture must exercise the actual source plan and fake provider:
complete renamed instance, exact phase controls and declared outputs; substituted
stack/resource/template/non-control values; pending or failed activation;
missing/duplicate/unowned output selectors; conflicting/lost evidence retention;
copy isolation and no resource/task submission. Expired/closed observation may
return still-ready evidence but cannot reopen session admission. Budget three
minutes of affected exploration, reusing unchanged native cleanup and full
capacity proof when record shapes do not change. No record-schema, transport,
new-file or check-catalog change is planned for this handoff.

Entity consumers will bind temporary runtime identity inside the existing
immutable request, not merely an optional runner argument: reservation hashes,
preflight comparisons and retained receipt reconstruction must reject swapped
cluster/log-group/stack incarnations. Existing task-binding validators must use
the exact captured parameter/resource closure rather than relaxing persistent
constants to a subset. `task-steps.py` already owns preparation step selection,
keys and packet names; feature steps and delivery label owners retain their
roles. Those executable definitions are not currently captured by the planner.
Their source-bound selection, runtime consumer edits and durable preflight/step
packet storage require a connected owner-specific increment before task launch;
this view alone does not implement or qualify the temporary task route.

### Entity runtime identity consumers — 2026-11-27

The next connected consumer block owns existing entity task-execution
`implementation/task-binding.py`, `task-control.py`, `task-runner.py`,
`task-evidence.py` and `task-steps.py`, plus their existing binding/control/runner/
evidence/route fixtures and the preflight-control fixture. Change the preflight
runtime owner only if its current whole-request immutable comparison loses the
new context; do not duplicate that comparison. The ordinary task CLI and its
live provider gate are not enabled for temporary sessions by this block.

Add an optional closed `runtime` member to the existing immutable task request;
legacy requests omit it and retain exactly their current behavior and five-field
reservation/receipt formats. Its schema is `deploy/aws-task-runtime/v1` with
`session_id`, `source_plan_sha256`, `binding_sha256`, `stack_id`, `cluster_arn`,
`family`, `container_name`, `log_group` and `log_stream_prefix`. The control owner
validates this shape once, using the existing target account/region, finite
native identity bounds, exact digest formats and no wildcard/path substitutions.
`binding_sha256` uses the existing target fingerprint convention over the
original view binding, custody and stack ID; changing observation time does not
change a task's immutable identity. This syntax validation is not provider
ownership or permission. The source-bound constructor below owns its origin.

Expose `CONTROL.runtime(request)` for request-bound identities or unchanged
persistent defaults. Reuse it in request family validation, override container,
exact task ARN/overrides, submit/reconcile/poll cluster, log group/stream and
retained receipt reconstruction. Preserve existing selectors, deadlines,
network restrictions and diagnostic meanings; malformed new context gets one
finite runtime-binding-invalid rejection without echoing supplied fields.
The default submission still passes the same persistent cluster selector, not
an incidental ARN-format change. Returned context must not expose mutation
access to the retained request.

Extend `BINDING.inspect(..., snapshot=None, *, runtime_view=None)` to consume the
concrete view specified above. When selected, require the supplied snapshot,
parameters and logical-resource map to equal that view, account/region/component
to match the existing entity owner, and exact parameter/resource closure derived
from its captured template. Reuse current task-definition, IAM-role and network
validators unchanged, then derive runtime family/container/log configuration
from that checked task definition and cluster from the checked parameters.
No arbitrary subset, copied validator or unchecked new CLI argument is allowed.
`task-steps.request` forwards that checked context into the existing builder;
it cannot synthesize a substitute. Persistent inspection still uses its existing
source and exact constants. The session controller must supply the real view,
fresh final authority and durable storage before this route can run live.

Use existing fixtures to exercise renamed cluster/family/container/log identity
through real binding, control, runner, evidence and preflight consumers. Prove
runtime mutation conflicts with retained intent before send; lost-response
recovery stays in the original cluster; a different session/incarnation cannot
reuse preflight; retained evidence reconstructs the same request-bound container;
and persistent defaults/records remain unchanged. Include finite canaries and
source-closure negatives. Budget four minutes of affected exploratory proof;
no new files, recurring checks, workflow registry or record-store implementation.
Report any actual missing registration input before changing the existing catalog.
Runtime view production, captured finite task selections, remote admission/
receipt/step packets and the qualified controller remain required integration.

Cross-consumer review identifies the same runtime-identity constraint in the
next persistence task integration. Own its closed syntax once in existing
`shared/provider-adapters/aws/tasks.py` as
`runtime_binding(value, *, account, region)`, returning a copied checked map and
raising the existing finite TaskFailure with `runtime-binding-invalid` on bad
input. This helper does not prove source/provider ownership or grant authority.
Entity `CONTROL.runtime` keeps its persistent defaults and selector, delegates
the optional map to that owner and preserves its caller-level failure meaning.
The entity binding producer and existing fixtures use the shared schema above;
no temporary record has been published, so the superseded draft entity-only
schema needs no compatibility reader. Persistence will consume the same helper,
not copy these fields, bounds or checks. Shared task submission/reconciliation
behavior is otherwise unchanged. This adds no source file or recurring check.
The existing entity control fixture must prove actual delegation and unchanged
legacy defaults, in addition to malformed/foreign/overlong identities and
copy isolation. Include this owner in the connected admission review and existing
registration input closure; reuse unaffected task execution proof.

### Persistence retained task consumers — 2026-11-27

Connect the already-reviewed journal and receipt owners to existing persistence
`task-operations.py`, `run-migration/script.py`, `run-administration/script.py`
and `task-operation-test.py`. No ordinary CLI flag or live route is enabled here.
The candidate verifier has a different request contract and remains a required
separate consumer, not silently coerced into the administration schema.

Extend BoundOperation with optional checked runtime, retained storage and finite
step identity. Reuse `tasks.runtime_binding` for the same nine-field context as
entity tasks; include it in the immutable request so changing the cluster,
container, stack, session or source binding cannot reuse an attempt. Legacy
requests omit it and keep their original formats, cluster selector, local locks,
history and receipt fallback. Temporary runtime requires the explicit retained
storage route; it cannot silently fall back to local files. Runtime syntax is
not ownership: the controller must later supply source-checked runtime views.

Extract the existing record validator from its local file reader and use it for
both local and retained reads. The retained route calls `reserve_retained` with
the same request/predecessor/completed-proof decision. It never calls the local
paths/lock owner or historical production-directory scanner. Shared submit,
reconcile and terminal observation code uses the request-bound cluster,
definition and container. Keep any explicit successor authorization callback;
retention alone does not authorize another attempt.

The injected storage protocol adds `retain_task(step_id, expected, task_arn)` and
`retain_proof(step_id, expected, reference)`, each returning the positively
retained exact successor journal record. Only the designated task/proof fields
and existing integrity may change; validate the returned record and compare its
whole intended value before accepting it. The storage adapter owns immutable
child versions, session binding, head CAS and append-once fields. Avoid unchanged
remote saves on every poll. `before_submit(step_id, expected)` must positively
confirm fresh admission immediately before the existing RunTask helper sends;
the eventual session adapter also retains positive pre-send rejection. Any
missing/wrong-type/thrown guard or retention result has a finite safe failure.
After possible launch, storage failure must report uncertainty, never success or
permission to retry. A retained attempt remains observation-only.

Extend the existing migration/administration acceptance and log/image readers
with explicit optional runtime/provider/receipt-storage context, preserving
their existing default calls. Use the checked container/log group/stream and
task prefix; do not patch module globals to run a temporary task. Existing
receipt `make`, `retain`, `read` and substantive comparison remain authoritative.
Local callbacks still receive Path; retained callbacks receive the exact
`{path, sha256}` reference and attach it before any accepted report. Failed-task
proof and safe diagnostic readers retain their current meanings and canary
exclusion. Observation and proof retention remain allowed after session expiry;
fresh launch does not. These seams alone do not supply real S3 or IAM authority.

Use the existing actual-caller fixture with conditional in-memory storage to
prove renamed cluster/container/log routing, no local paths/scans, durable
reservation before send, original-cluster lost-response recovery, request drift,
guard refusal, uncertain task/proof attachment, immutable retained proof reuse,
explicit completed-proof successor and unchanged legacy callers. Named failure
assertions must distinguish blocked-before-send from uncertain-after-send and
exclude sensitive storage/provider text. Budget four minutes of affected
exploration. No new files/checks; reconcile the existing runtime review rows and
registered input closure after the sources stabilize. Real source binding,
session storage, candidate verifier and controller assembly remain required.

Parent and independent review found two connected receiving-boundary gaps in
this block. A callable provider can be falsey, so `provider or aws` must not
replace an explicitly supplied provider with the ambient production connection.
Select the default only for an absent provider on the unchanged persistent
route. Temporary direct log/image readers must reject an absent/non-callable
provider before any read. Malformed runtime currently escapes those readers and
acceptance functions before their finite handling; normalize it at those owners
using their existing tuple/report shapes, without echoing supplied values or
changing legacy defaults. The same four-file inventory remains applicable.
Extend the actual-caller fixture with malformed runtime, missing provider/store/
attachment callback, a falsey callable provider, and foreign terminal-container
counterexamples. Assert no ambient read or receipt write on rejection and finite
canary exclusion. The first 24 affected methods passed in 18.050s; corrections
use the remainder of the existing four-minute exploration allowance. This is
required boundary completion, not a new check or a live execution route.

The correction batch is parent-reviewed against the actual direct-caller
assertions. All nine retained-consumer methods passed in 1.821s (69145, exit 0),
taking this block's exploration to 19.871s. The unchanged 18 legacy/local
methods' proof is reused. Migration is frozen at SHA-256
`eec243c760a10bda782985c5aa5f2eccdd0e8386be7b2dbc6a4aea95dc479ae0`,
administration at `508e76f82f8a41853db424aa894ef57e59d59cca5c949062fdc226bf41574d4d`,
and the fixture at `8ce3b3cdd2099598b61a3bd01d4995110716f3751686dc15df12df88bceb0016`.
Final connected review/preparation remains pending; no AWS effect is established.

### Retained private verifier consumer — 2026-11-27

Extend existing persistence `verify-candidate/script.py` and
`verify-candidate/operation-test.py`, preserving the verifier's own immutable
four-field request, three exact override values, operation schema, record ID,
proof type and predecessor rules. Add optional runtime, explicit provider,
retained storage and finite step identity to `execute_reserved` and thread that
context through its actual observation, completion, image/log and isolation
readers. Legacy entrypoints retain their current arguments, local journal,
locks/history, task selectors and proof formats. No new CLI option or live
temporary route is enabled by this consumer change.

Extract the current operation validator from the local reader for both routes.
Reuse `tasks.runtime_binding`, `task_journal.reserve_retained`, the shared ECS
submission/reconciliation/observation owner and existing receipt make/retain/read
owner. Runtime is part of immutable intent, never merely an optional poll
argument. A temporary route requires the same explicit storage methods and
positive `before_submit` as administration/migration; no local path, production
history scan or ambient provider fallback is permitted. Existing completed-proof
successor semantics remain unchanged. Missing/uncertain retention never permits
resubmission, and observations/receipt retention remain possible after expiry.

Do not copy the exact retained task/proof attachment validator from
`task-operations.py`. Extract that bounded generic decision into existing
`task_journal.py` and make both existing callers use it: copy the original
record, permit only the selected task/proof fields plus recomputed integrity,
require append-once consistency, call the explicit storage method, validate and
compare the complete returned successor, then update caller state. Preserve
each caller's finite failure mapping. The consumer remains responsible for
record/proof semantics; the helper grants neither session nor AWS authority.
This extends the inventory to those two existing files and the existing
`task-operation-test.py` fixture for actual shared-use proof, not a second engine.

Temporary log/image/isolation readers must use the checked cluster, container,
log group and prefix, reject malformed runtime or missing/noncallable provider
finitely before reads, and preserve an explicitly supplied falsey callable.
Keep the verifier's no-direct-database-credential check and exact MODE/RECORD_ID/
FACT override check. Terminal success/failure proof must attach its retained
reference before publication; uncertain attachment must not look accepted.
Reuse the reviewed migration receipt handoff/context helpers where applicable,
while preserving the verifier's distinct legacy log-stream prefix and failure
diagnostic reader. Do not weaken failed-task diagnostics or canary exclusion.

The existing operation fixture proves renamed runtime routing through the real
caller, positive retention before send, final admission refusal, lost-response
original-cluster recovery/no replay, immutable proof reuse after provider-history
expiry, explicit predecessor advancement, uncertain task/proof writes, exact
terminal container and unchanged local CLI behavior. Add shared-use assertions
at both actual attachment consumers and direct-reader negative/provider tests;
update copied fixture dependencies for actual imports rather than module-global
patching. Budget five minutes of affected exploration; no new source file or
recurring check. Source-bound selection, live task/role/network verification,
S3 finite-step storage and the controller remain required connected work.

### Versioned task-child transport — 2026-11-27

The v7 full-cleanup envelope leaves only 5,039 bytes in the parent. Do not put
each task's maximum-length S3 version reference in that parent. The connected
task storage will use one bounded task-state child reference in the existing
parent, with finite source-selected task heads and immutable intent/receipt
references inside that child. This is storage representation, not another
workflow registry. The later parent shape change must reserve its complete
maximum reference before admitting infrastructure and remeasure full cleanup;
the current capacity evidence does not qualify that future shape.

Implement the byte transport first in existing `session_records.py` and its
`environment-sessions-test.py` fixture. Factor the existing private S3 file/CLI
read and conditional-write handling so parent and child routes use one transport,
preserving parent limits, readback, finite failures and all current callers.
Add private immutable-child retain/read methods. Derive keys only from the
configured parent key, original session ID and raw SHA-256; accept no supplied
bucket, key, URL or path. A child reference is exactly raw `sha256`, `version_id`
and `bytes`; retain the existing full 1,024-character version bound. Require
explicit positive expected-owner/version/length/digest checks and immutable
conditional creation plus matching readback. Child payloads are bounded bytes:
intent callers retain the 65,536-byte limit and receipt/task-state callers at
most 1 MiB. Do not deserialize workload payloads or copy their validators here.

The private child methods must check the existing storage guard and positive
parent binding before use. They may retain observation/proof after expiry, but
never open a session or grant launch authority. A child object without a later
positive parent CAS is an orphan, not a reservation. A lost/conflicting child
write is not silently resubmitted; a later explicit observation can recover only
exact positively observed bytes. No parent field/schema change, finite-slot
adapter or live provider call is enabled in this transport-only increment.
Those remain required connected work, including per-operation semantic bounds,
source-selected keys, pre-send rejection retention and the final admission guard.

The private API is `_retain_child(raw, *, max_bytes=LIMIT)`,
`_read_child(reference, *, max_bytes=LIMIT)` and explicit read-only recovery
`_observe_child(raw, *, max_bytes=LIMIT)`. Only the existing intent limit or
1 MiB is selectable. Hash the configured parent key into the derived namespace
so a valid maximum-length parent key cannot overflow S3's key boundary. Recovery
derives the expected digest and length from the original bounded bytes and
returns a positively observed exact reference, or absence only for classified
missing-object evidence. It never creates a child or grants freshness. This is
not an automatic read/retry after an uncertain or conflicting write.

Use the existing fake CLI through real SessionRecords methods to assert exact
version retrieval, full-length version IDs, byte bounds, cross-session/hash/size
substitution rejection, uncertain write/readback and sensitive failure handling.
Prove orphan retention leaves parent bytes/admission unchanged and unchanged
parent conditional writes still distinguish conflict from lost readback. Budget
four minutes of affected exploration; no new file or recurring check. Reconcile
the existing durable-record review row and registration closure after parent
review; final connected registered proof remains pending.

### Source-owned initial task selection — 2026-11-27

The persistence candidate workflow already orders bootstrap identities, confirm
runtime IAM access, apply the ordinary migration, grant runtime application
access, prove effective privilege, then the server-mediated create verifier.
The executable acceptance route currently describes later qualification proofs
but omits that initial setup sequence. Do not copy the prose into the temporary
controller or treat every supported runner operation as launch authority.

Extend existing persistence `00-declaration/acceptance-route-contract.yml` with
an ordered `initial_setup` task selection and its missing ordinary command
templates. Reuse existing proof references for runtime access/effective privilege;
declare the other initial proof contracts beside their existing command owner.
Keep all fifteen release-proof obligations, accepted-record schemas, promotion,
recovery sequence and ordinary-update behavior unchanged. Initial setup proves
a usable candidate, not full release acceptance. Reconcile the candidate
workflow prose to name this executable owner while retaining its human examples.

Existing `60-run/validate-acceptance-route/script.py` owns a pure
`initial_tasks(route, workload_binding)` reader returning copied finite selected
rows. Require exact row fields, unique bounded step/command IDs, declared
run-to-completion workloads and their exact task-definition references, bounded
proof fields and a single ordered before-activation/after-activation boundary.
Resolve referenced proofs at the existing route owner; do not duplicate their
values. Invalid, missing, empty, wrong-type, duplicate or mismatched selectors
raise one finite initial-selection failure without supplied text. The normal
route validator invokes this reader, includes the actual workload binding in
its references and compares initial proof contracts against the same actual
offline command-parser reports it already collects. No extra parser invocation
for an identical command is required.

Use existing `acceptance-route-rehearsal/smoke-test.py` for the actual reader,
structural rejection-before-probe, exact parser contract match, changed/missing
workload or command, copy isolation and unchanged release-proof membership.
Budget three minutes of focused exploration; no new file or check. Source-plan
capture is the next connected consumer: it must capture this contract, reader
and selected executable owners before computing source identity, and reject
missing initial setup at that receiving boundary. Entity's existing step/key/
prerequisite owners remain authoritative for its own selection; do not replace
them with this persistence sequence. Neither static selection nor its hash is
runtime ownership, predecessor proof or AWS permission.

### Captured initial task selections — 2026-11-27

The preceding status-only turn made no implementation progress. Continued
bounded proof now confirms the persistence initial reader and actual offline
command parsers (process 54232, exit 0, 31.387 seconds). The previously lost
initial-reader terminal result was not counted. Production release membership
remains fifteen proofs; initial setup is not release qualification.

Capture the initial task workflow in the existing source plan. Reuse each scope's
declaration `acceptance.route` and add a closed `initial_selection.kind` to those
existing route documents: `ordered-commands/v1` or `entity-smoke-baseline/v1`.
The existing acceptance compiler dispatches only these fixed code-owned readers;
the shared preparation owner must not branch on scope names or import a callable
selected by arbitrary document text. Missing/unknown/wrong-type selection is a
finite initial-selection failure, not an empty runnable workflow. Normal
persistent configuration and CLI behavior stay unchanged.

For entity selection, extend existing task-execution `task-steps.py` with a pure
initial reader. Keep its four preparation STEPS and key function authoritative;
move baseline acceptance names once from `acceptance-evidence.py` to the task
owner, with feature order/conditional observer data owned by existing
`feature-steps.py`. Both acceptance and feature support consume these owners.
Share the baseline preflight-label calculation between task-steps, task-route
and acceptance-evidence, retaining their existing recovery/delivery overlays.
The reader returns source-selected workload, operation, definition, stage,
preflight/operation phase, activation side, key, label and conditional recovery
selection. Resolve task definitions through the existing workload binding and
reject missing/ambiguous/non-task selections. Cover all four preparation tasks
and create/lifecycle/collision/read; the existing observe-create alternative is
conditional, never an automatic replay or another unconditional stage. Existing
runtime prerequisite owners remain required; selection alone grants no launch.

Extend `preparation-inputs.py` to capture the route, fixed compiler/reader import
closure and selected executable owners before hashing inputs. Store copied finite
selections in the captured plan, including dependency scopes in existing order.
Revalidation and cold recovery compare the complete plan as before. Existing
runtime-configuration and session fixtures must copy these actual new inputs;
the registered preparation/route/entity check input closures must include them.
No new source file, task registry, command, scheduler or recurring check is
needed. Task progress remains outside the compact parent record in the next
connected retained-state increment.

Diagnostic/counterexample inventory: malformed kind or selected row fails at the
compiler without provider calls; missing/unreadable source remains the existing
preparation source failure; changed source or copied selections fails complete
plan revalidation; missing/foreign workload or task definition fails source
selection; keys and labels must equal existing native owner results. Actual
reader fixtures prove copy isolation, exact baseline membership and conditional
observer selection, unchanged recovery labels, no broad runner-operation
enumeration and no provider/write effects. Budget five minutes for the connected
affected exploratory tests, reusing unchanged cleanup transport proof. Parent
review and diagnostic records precede final registered proof.

The independent verifier review found a required direct-consumer correction:
`verify-candidate/script.py` temporary `image_digest` must match the returned
task-definition ARN to the requested ARN before accepting its image. Add wrong
and missing ARN cases through actual `accepted_completion`, proving no receipt
or attachment. Keep the legacy path unchanged. This correction uses the existing
operation fixture and runtime failure vocabulary, with a two-minute focused
budget; other frozen verifier evidence remains valid where inputs are unchanged.

The captured-selection implementation is now parent-reviewed and independently
reviewed without required findings at compiler `b76eb2536096183456cfa93662be9f6b58f7637f6a0b361c9e65bba05b1c9cb2`
and preparation `802bbdf92df83fafccd29ca941c8d5b262846a17feaaf748ffb58451be99c152`.
Actual source-plan tests passed (70343, exit 0, 4.354s), the native entity
preparation/activation/feature-observer route and acceptance parity passed
(92484, exit 0, 104.111s), and both existing registration-owner methods passed
(2763, exit 0, 28.987s). Both ordinary route inspections also passed. These are
local exploratory results, not the final combined registered pass or live proof.
The initially empty direct test-module invocation ran no tests and is not counted.

The verifier's direct receipt-reader correction passed four focused methods
(80322, exit 0, 4.091s). Parent inspected the exact-ARN guard and actual wrong/
missing-ARN assertions. Source is `9abbfa094ef0a66c0d08844ca50f9db2e3d374bb85ad4d7103c4d0dce1a7851f`.
Independent diagnostic reconciliation reviewed thirteen stable source identities
in nine existing rows in 309s/360s. All partial statuses, prior evidence, debt,
test registrations and excluded sibling hashes remain unchanged. The existing
validator accepted all 233 rows; allowed-delta/source checks took 0.313s. Ledger
SHA-256 is `5c6f79733d1d4f9a07ddf7f6f29fb37584ba75d743ad72c3801be2eea2d843a1`.
Runtime producer, retained state and their remaining consumer rows are reopened
separately below; no source hash is a claim of effective permissions or cleanup.

### Finite retained task state — 2026-11-27

Extend the existing `session_records.py`, `environment_sessions.py` and
`environment-sessions-test.py` owners; no new storage engine or module. Source
plans now provide finite native selections for every component. Bind their
canonical digest/count into the immutable base and add exactly one nullable
`task_state` child reference in schema `aws-temporary-session/v8`. These are
unpublished local records; no live v7 migration or historical compatibility
route is needed. Keep the 65,536-byte parent and 1 MiB child limits.

The immutable state child binds original session/base/source identity and the
captured finite selection table. Index one slot per captured task, rather than
accepting caller-generated paths, runner operation enumeration or unlimited
retry history. Reuse the existing derived child keys and exact version/digest/
size reads. Slots reference original immutable intent, current journal when
changed, first receipt/owner-derived label and bounded admission evidence.
Missing referenced payloads are unavailable, never empty slots. Initial tasks
have one attempt; reject successors on occupied slots unless a future captured
workflow explicitly admits a bounded successor slot. Existing journal formats,
request validation, receipt semantics and prerequisite checks remain native.

The session adapter selects component/step only from its captured plan and
checks the base digest; it does not accept a replacement selection table,
arbitrary module or resource name. The storage facade reuses actual entity
read/create and persistence read/compare-and-reserve/retain-task/retain-proof/
receipt protocols. Validate selected key, mode, immutable request/session/
source/incarnation and append-only facts, with payload semantics still checked
by existing workload owners. Concrete runtime construction and final authority
remain required before launch; this storage factory cannot establish them.

For a write, positively read the parent/state, compare the exact selected
predecessor, retain bounded payload/state children, then update only the parent
head through its existing If-Match and exact readback. Only that uninterrupted
positive CAS may return fresh True. Conflict, lost acknowledgement/readback or
an orphan child never grant freshness, and are never automatically replayed.
Observation/recovery is separate from reservation. Repeated exact observation
attachments may reuse retained content but cannot reopen an attempt. A cold
adapter reading an existing head always observes nonfresh state.

Fresh reservation and immediate pre-send admission require an open, unexpired
session and the owning protection/authority guard; receipt/task observation
remains possible after expiry/sealing. Do not manufacture launch permission
from the source hash or captured runtime shape. Final qualified source/runtime/
IAM admission still must be connected by the controller. Keep known pre-send
rejection distinct from unknown effect and do not recycle reservations.

Before the first billable creation, reserve the complete parent cleanup envelope
plus the largest serialized child reference, including 1,024 quote/backslash
VersionId characters (2,048 escaped JSON bytes), even when the current head is
short. Prove the full fixed-slot child can hold its bounded reference fields
within 1 MiB. The base keeps digest/count only, not duplicated large selections.
Keep exact native cleanup/resource lineage and all earlier intents unchanged.

Named proof risks: same/different-slot competing CAS, child success/parent loss,
lost readback and cold recovery, missing/foreign child/session/slot, changed
request or receipt, expiry between reserve and submit, successor refusal and
maximum escaped metadata. Use actual journal/reservation consumers with the
existing fake AWS process. Extend the complete 120-resource lifecycle capacity
test through task activity, activation, sealed discard and reverse deletion;
every parent version stays within its bound with earlier intent unchanged.
Budget eight minutes of affected exploratory proof, reuse unchanged child
transport tests, and update existing registration/diagnostic owner records.
Parent review closes the connected boundary before registered proof; no live
execution or cleanup completion is claimed by this increment.

### Shared checked task configuration — 2026-11-27

The preceding status-only turn made no implementation progress; the goal remains
active. Continue the connected runtime producer while retained task-state work
proceeds in its separate three-file boundary. No live AWS operation is admitted
by these local changes.

Reuse the existing AWS `ecs-runtime-configuration.py` owner for source resolution
and observed task revision, role/policy and security-group comparisons. Move the
generic mechanics out of entity `task-binding.py`; retain its public signatures,
selection defaults and diagnostic reasons as thin supported wrappers. Its
current `normalize`, `resolve` and `package_projection` static interfaces remain
unchanged; the runtime resolver has a distinct name. Shared code must not import
entity composition or hardcode its workload prefixes/account/region. This is an
existing Python helper extension, not a new module/index, source file, public
command, registry or scheduling lane. Update its metadata effects/consumers and
obtain the existing bounded admission review before preparation.

The shared runtime entry consumes the existing checked session runtime view and
a source-selected workload binding. Add the missing security-group association
to existing persistence workload rows: migration/administration groups in the
same component, private verifier group in foundation. Resolve selected logical
IDs, never infer them from workload prefixes. Persistence `task-operations.py`
supplies the concrete consumer; migration, administration and verifier retain
their existing native request, reservation and receipt contracts. Preserve
ordinary production defaults and entity compatibility wrappers.

Support only the required captured source forms: Secrets Manager Ref returns
its owned ARN without reading a secret; checked AWS partition; dotted Sub/GetAtt
RDS endpoint, port and resource ID. Observe those RDS attributes by exact owned
instance and compare existing source-selected outputs. Do not accept caller-
invented arbitrary attribute maps. Compare exact task revision, container,
logging and source tags using ECS include TAGS. Derive security-group rules from
both inline declarations and standalone ingress/egress. Related foundation and
persistence views must have identical session, source plan, account and region;
prove the selected foundation output/physical group equals the persistence
parameter. Keep logical IDs scoped to their original stacks. Compare all rules
of the selected group; check required peer ingress without claiming unrelated
peer inventories are completely described. A permissions boundary remains
prohibited unless a subsequent admitted source change supplies its exact owner.

Extend only the closed read requests in `session_cli.py` for required IAM reads
and ECS tags. Reuse existing entity `task-binding-test.py`, persistence
`task-operation-test.py` and current session transport fixtures; root owns their
catalog closure and the session-state agent owns its fixture. No new recurring
check. Proof must reject foreign session/foundation/DB/secret identities, wrong
revision/tags/logging, extra network access and substituted logical selections;
prove actual consumer use and unchanged entity failures/static normalization.
Keep provider raw dictionaries and secrets out of diagnostic text. Reuse finite
binding reasons with exact workload/field/item mapping at persistence's caller.
Allow six minutes of affected exploratory proof; final registered proof follows
parent review and stable inputs. Controller source qualification, effective SQL
privilege and IAM deadline authority remain separate required work, not claims
made by this runtime producer.

The read-only inventory also found migration `image_digest` missing the exact
returned task-definition ARN comparison already corrected in verifier. Reopen
that receiving boundary and its existing task-operation fixture: reject wrong
or missing returned ARN in temporary mode through actual completion, with no
receipt/attachment/relaunch; preserve the legacy path. This is a correction to
existing runtime identity proof, not an optional future improvement.

Retained entity task slots stay selected by captured component/step. The native
AttemptStore path owner aliases several keys, so the retained facade may take a
trusted `key_for_record` callback to that owner. A bounded empty read may return
None, but creation and occupied reads must match its exact native-derived key;
independent selected workload/operation/label/session/custody checks still apply.
An arbitrary transport key cannot select a different slot or grant freshness.

### Shared runtime proof closure correction — 2026-11-27

Extend existing catalog input declarations and its actual-consumer regression,
not the execution engine. Shared runtime configuration changes now select the
existing persistence provider/composition/acceptance/diagnostic checks and entity
base/task/restart/credential checks. Add missing direct source inputs at their
existing owners; do not invent another check or automatically run broad proof
while those sources remain under edit. The named risk is reusing a passing result
after its shared comparison logic changes.

Exploratory process 7376 exposed an older contradictory fixture assumption: it
requires every member of persistence-composition to consume task execution
sources, including PostgreSQL version policy and preparation-input checks that
do not import those owners. The real runtime member does consume them. The run
was deliberately interrupted after more than 160 seconds (exit 130), after
observing those failures and the newly shared comparator's missing diagnostic
catalog input. It was not a pass or an external-operation interruption.
Correct the existing fixture to explicit actual consumer leaves while retaining
parent-selection obligations and mutation/omission assertions. Do not attach
unrelated inputs merely to make every member invalidate. Inspect/reuse unchanged
graph work within that one test invocation; do not cache across source identities
or alter production selection. Budget three minutes for the correction review
and two minutes of affected exploratory proof. Root owns catalog inputs; the
independent reviewer owns only the existing fixture method/metadata.

The retained-state review also found an exact-operation gap: searching all
environment values can mistake an unrelated optional field for the task selector.
Require a native `record_selection` callback deriving the actual selector from
its existing owner, then compare its closed projection to the captured row.
Entity uses CONTROL.OPERATIONS; persistence uses BoundOperation's proof type and
actual selector. The callback must not simply return the selected row. Prove a
wrong operation disguised by an allowed optional field is rejected before any
retention or launch. These are qualified-code seams, not caller-granted authority.
The full 120-resource storage lifecycle test separately rejected concurrently
changed source as intended; rerun only after the runtime producer freezes.

The frozen-source rerun passed: handle 82472, exit 0, 66.998 seconds. Actual
retained task activity, a 1,024-character escaped VersionId, four creations,
two activations, sealed discard and four reverse-order deletions peaked at
57,073 parent bytes; the complete reserved cleanup envelope was 62,786 of
65,536 bytes. Earlier CloudFormation intents remained unchanged. The storage
exploration total is 346.955 of its 480-second budget, including the invalidated
attempt. This is controlled-provider evidence, not AWS removal or completed
independent expiry. The shared-runtime producer and existing consumer batch
also passed 15 tests in 3.076 seconds, with entity delegation/static parity
passing separately in 1.92 seconds. Actual runtime-view-to-workload handoff
and the added transport reads remain the next connected fixture proof.

Close registration against actual imports, not a copied list: the session
fixture now imports entity task-control, persistence task-operations and
proof-receipts plus their shared task/journal owners. The connected runtime
handoff additionally consumes shared ECS runtime configuration and the entity
binding's existing deployment/resource owners. Extend the existing registration
method to inspect those loaded module paths. Persistence's producer fixture
now captures a real source plan; its provider check must fingerprint that
plan's references, including the publication workflow, lifecycle policy/session
binding and acceptance compiler. Add a focused method in the existing repository
contract fixture proving the captured references are covered and changing or
omitting a consumed input changes the retained fingerprint as expected. Reuse
existing checks and impact rules; no new check, runner or source module. Budget
two minutes for these affected registration methods after fixture inputs freeze.

The selection-fixture correction is complete: the four affected source cases
passed in handle 21748, exit 0, 98.593 seconds. Default coverage still contains
all 16 cases; no full-suite pass is claimed. Aggregate selection remains broad,
while fingerprint assertions apply to explicit consuming leaves. The following
status-only turn made no edits; this continuation resumes implementation rather
than treating that report as completion.

Independent producer review found one required diagnostic correction: missing,
non-list or duplicate top-level ECS tags currently inherit the shared entry
sorter's container reason. Tags describe the task definition, not a container.
Extend that existing sorter with optional code/field parameters whose defaults
preserve entity environment/secret behavior; use the existing definition/identity
reason only for task tags. The existing persistence producer fixture must assert
the exact code, workload, field and item for absent, null, wrong-type and duplicate
tags and exclude sensitive canaries, while successful source tags remain covered.
No new diagnostic vocabulary, provider effect or permission is added. Reuse the
producer's six-minute allowance for this small correction, freeze it before the
connected session fixture runs, then refresh only actually reviewed ledger rows.

Correction proof passed: five producer methods in 0.889 seconds (171e14), and
the existing entity binding fixture passed to terminal handle 1664. Shared
producer SHA is `953811dfd35345f14b9193d5ad8fd4002c217d0f4da97b155dc263fcdba22353`;
persistence fixture SHA is
`e575d17aad5543f84e24b21a22b0a957c98f48b3c6d404929a5afa7d6dc6e4cf`.
The independent Senior Prompt Engineer review returned `pass_with_notes` under
script-admission v4, run-agent-review v2, agent-contracts v1,
professional-review-quality v1 and rubric v1. Scores were 5/4/5/4/4/4; the sole
required finding is resolved. Review took 379 seconds, 19 over its 360-second
budget, including final ledger reconciliation. Five reviewed source identities
in five existing rows changed; the old shared static declaration row is now
accurately partial for new runtime diagnostic delivery, with historical adopted
evidence and sibling hashes preserved. All 233 ledger rows and the allowed-delta
check passed; ledger SHA at that checkpoint was
`3d419e8061d599a02012d5edc4fb125fa13f18f6a33181a43693b7f42e507a7b`.

The actual runtime-view handoff then passed two connected methods in 44.299
seconds (42164, exit 0), within its 240-second allowance. Both workload producers
consume unmodified `SessionOperations.runtime_view` results through the real
`SessionProvider` and controlled subprocess, then supply their returned runtime
to the native retained reservations. Exact IAM reads/TAGS, foreign source views,
wrong task/role responses, denied/unknown transport and closed-input rejection
are asserted. Parent reviewed this full path and its controlled-template reply
generation: it proves the handoff, not effective IAM or a live launch. Fixture
SHA is `4180d110b1b562e8b59eea27fa4e1130d5035603aa8a488e8c3e37183b901f4d`.
Two affected catalogue registration methods passed in 12.969 seconds (44962,
exit 0). Actual module imports and captured plan references now invalidate their
existing checks; no check, runner or script-source file was added. These are
exploratory results, not a complete registered integration or package pass.

Next connected owner inventory found no existing complete session command. The
reusable controller belongs under
`scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/`. The user
has now explicitly approved that exact folder; the placement decision is closed.
Existing cohesive-source size approval and autonomous implementation authority
remain in place. Approval does not qualify live execution or change AWS scope.
The controller must reuse native reservations, reconciled stack operations,
runtime/task consumers and reverse cleanup, not introduce a second journal or
retry engine. A new command alone cannot bypass current missing phase-role,
credential-mode, effective-deadline, independent-expiry or completion contracts.

### Native task submission context — 2026-11-27

The next existing-owner inventory found two remaining fixed-cluster assumptions
in entity `task-route.py`: the exact RunTask payload guard and the operator IAM
simulation context. Its native runner already constructs a checked temporary
runtime request, but those guards still compare the persistent cluster. Extend
only this route and its existing `task-route-test.py`: derive the guarded cluster
from `CONTROL.runtime(request)`, preserving the original default for requests
without runtime. Let the existing operator check accept a checked runtime context
and use its exact cluster ARN, with invalid contexts rejected before provider
reads; pass the context from actual prepared/rechecked bindings when present.
Do not add a temporary command switch, replace source/ownership/prerequisite
gates or make a runtime-shaped dictionary an authority grant. Public fixed-stack
preparation remains protected; the future qualified session controller must still
construct its own real authority and source/runtime handoff.

Reuse the existing provider capability, native request validator and effective
operator policy checks; no second RunTask implementation or permission checker.
Named counterexamples are a valid temporary request sent to the persistent or a
different cluster, malformed runtime reaching STS/IAM, mismatched task definition,
denied guard, repeated capability use and an IAM simulation silently retaining
the persistent cluster. Test exact submitted payload/context and no-send behavior
through existing real owners, plus unchanged persistent behavior. Existing finite
task/runtime/operator reasons remain private and retain workload/field attribution
where supported. Budget two minutes for affected exploratory assertions, not the
whole monolithic route suite; final registered task-route proof remains required.
This changes an existing caller's supported runtime context, not its execution
effects or public CLI, and needs no new folder while placement approval is pending.

That increment is implemented. Parent review inspected the exact payload guard,
operator validation, both prepared/rechecked binding call sites and the native
reservation/provider assertions. Wrong-cluster submissions fail before the guard
or send; malformed runtime and mismatched definitions fail before STS/IAM; legacy
payloads and single-use behavior remain unchanged. The two exploratory fixture
sections passed in 1.406 seconds (68156, exit 0), against route SHA
`f5d46068ed8a329f4063666c10da7a73da2e139173aa069c94f74332bb062679`
and fixture SHA
`306b83bed8b28bbee07105c70fcc6d1e3885ae899f7ab7dda22f11b505d713bc`.
Independent Senior Prompt Engineer v1 review found no required corrections under
script-admission v4, run-agent-review v2 and contracts/rubric v1; scores
5/4/5/5/4/4, elapsed 85 of 180 seconds. Only the existing partial task-route row's
reviewed source identity/reason changed; all 233 ledger rows and the allowed-delta
check passed, ledger SHA
`c736e1e2fa11cc07dec49e89b165d92d203ef89d0d22547d4e6b7a293182fdbb`.
No script-source files or recurring checks were added, removed or moved. Full
registered proof and actual qualified temporary-controller authority remain
pending. The subsequent user-requested status turn was no progress toward the
goal, not a pause; this continuation resumes the next incomplete boundaries.

### Controller credential and completion boundary inventory — 2026-11-27

The independent retained-task admission review found no further required source
correction. It confirmed the exact captured selection/native operation checks,
conditional parent adoption, nonfresh cold/uncertain recovery, expiry guards and
reserved capacity. Only records/adapter identities were refreshed in their two
existing partial diagnostic rows, preserving debt and history; all 233 rows and
the allowed-delta invariant passed. Ledger SHA at this checkpoint is
`313fe44c125e62518cdfb50f3e1606d86baf04b52be149096bd86768f00a96c0`.
The Senior Prompt Engineer used script-admission v4, run-agent-review v2 and
agent-contracts/rubric v1, scores 5/4/5/4/4/4, and reused unchanged child transport
review and supplied focused results. Elapsed 258 seconds versus 240 allocated;
final clarification and preservation checks account for the 18-second overrun.
Full controller execution, effective permissions and live expiry remain pending.

Controller inventory identifies a concrete compatibility obligation: both existing
record and operation transports require an explicit named AWS profile. Do not
silently interpret a missing profile as ambient permission. One possible supported
composition preserves those APIs by providing a protected role profile with
`credential_source=EcsContainer`; AWS documents container-sourced role profiles
and CodeBuild's container credential endpoint. This is an inference for the
future qualified worker, not a selected or proved implementation. Actual role
assumption, environment/config protection and phase-specific authority still
require qualification. [AWS CLI role profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html),
[CodeBuild credential environment](https://docs.aws.amazon.com/codebuild/latest/userguide/troubleshooting.html)
An ambient-mode API change is therefore not automatically necessary.

Cross-region automated-backup completion remains unresolved. A future observation
must bind both original source ARN/region and retained database lineage; a database
resource ID is unique only within its source region. Disabled regions and denied
or incomplete observations cannot be silently omitted. No broad resource deletion,
new region activation or outside-region mutation is authorised by this inventory.

### Temporary zero-retention amendment — 2026-11-27

The user's disposable-data goal does not require every functionality run to test
backup recovery. Under the adopted authority for source and owning governance
changes, select zero automated-backup retention from the first fresh temporary
CREATE through activation and discard. Production remains seven days. This
explicitly supersedes the earlier running-retention preservation statements; it
does not adopt existing/restored databases or remove their historical backups.
The current captured functional task selections cover application/database
behavior, not backup/PITR/replication acceptance. Such acceptance needs separately
admitted retention-enabled execution and corresponding cleanup evidence.

Reuse `Metadata.DiscardControls` in the persistence template and the existing
`preparation-inputs.py::discard_projection`, adding only the checked RDS property
`BackupRetentionPeriod: {expected: 7, discard: 0}`. No new renderer, source file,
profile, scanner or check is needed. The existing runtime-configuration fixture
must assert exact integer zero (not `False`), creation/activation/discard agreement,
seven-day production preservation, renamed logical resources, source
fingerprinting and missing/malformed/contradictory control rejection. Existing
session acquisition/runtime/cleanup fixtures remain consumers of the changed
captured source. Reconcile the lifecycle standard, ADR0044 and the bounded
CloudFormation README section before treating this selection as current behavior.
README scope is that retention explanation only; no module export guide applies.

Native observation belongs to the existing session adapter's database-lineage
capture, actual `runtime_view` consumer and existing session fixture. Share the
exact owned identifier/ARN and immutable database reader with lineage capture,
but keep retention policy out of the retained lineage digest and cleanup gate.
The runtime view requires integer-zero native retention and no pending retention
enablement. Omitted optional replication information does not prove absence but
does not veto that narrower current-retention check; present malformed or nonempty
replication information rejects runtime qualification. Omitted pending-modification
information means no pending modifications under the native API contract;
explicit malformed content or a nonzero/boolean pending retention fails. Missing
identity or retention remains an attributable unknown, never absence. Native
identity checks retain existing lineage reasons; current/malformed retention,
pending enablement and observed/malformed replication need finite owner reasons
with no supplied values. Tests must inspect those exact reasons and no send.

Do not reject independently proved-owned deletion merely because current retention
or replication policy is unqualified. Keep those checks at the runtime-view
boundary and assert that the same policy counterexamples still permit ordinary
owned deletion. No runtime-view field, record schema or capacity change is needed
for this immediate observation. Its passing result never changes the separate
cross-region cleanup result from unknown. This qualification does not erase
existing regional snapshot, AWS Backup or automated-backup observations. The
qualified workflow must maintain zero through captured-only updates and disallow
separate replication/direct database mutations; detected outside interference
invalidates its proof. Original zero-retention custody plus this maintained
authority boundary is required before inferring lifetime replication exclusion.
Until that boundary is implemented, cross-region completion remains unknown;
neither a source field nor a caller-supplied boolean can close it.

The current source-only correction has a 180-second exploratory fixture budget;
native handoff proof has a separate 180-second budget after source freeze.
Preserve finite existing discard-control/retention and native-observation reasons,
reject before retention/submission, exclude provider values/canaries, and refresh
only reviewed diagnostic rows. Parent consolidated review precedes final
registered proof. No AWS mutation, new scripts or recurring checks are authorized
by this implementation checkpoint itself; the goal's existing live gates remain.

AWS documents zero as disabling automated backups and requires automated backups
before replication. Selecting zero from creation also avoids a later zero/nonzero
retention switch. [Backup retention](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html),
[Replication prerequisite](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/AutomatedBackups.Replicating.Enable.html).
This is a narrower supported functionality-test arrangement, not a claim of full
production backup equivalence or proof against arbitrary account administrators.

Source implementation and parent review are complete for this increment. The
exact allowed-path/type guard, final all-database retention check, both-scope
phase comparisons, full production comparison and renamed-resource/source
invalidation assertions were reviewed. Six affected reader methods passed in
terminal batches 8948 (three negative methods, 24.933 seconds) and 30751 (three
positive/rename methods, 3.041 seconds). Initial batch 71626 exposed a synthetic
database missing its engine metadata, before reaching the intended retention
counterexample; the fixture was corrected, not the runtime assertion weakened.
Total exploration was 41.559 seconds of test execution / 42.38 seconds wall time,
within 180 seconds. No full registered integration pass is claimed.

Frozen identities: preparation
`5ea4f538bc5d8c9bea4752d653be019ba82a9758d769769e67020897154653b7`,
template `8bc4431afecbef8b964cbc4b912db0093a0344ce157a00f23c92dfdaabc2f1c5`,
fixture `1b69f6d65b4815a7062109c8f2804d105dc7420c3faf19e41a39d1aaa7ce0f53`.
The template is 51,191 raw / 47,865 canonical bytes. Equivalent flow formatting
of the existing prefix declaration preserved the inline bound and all comments;
removing only the new retention metadata reproduces the pre-edit parsed-template
SHA `7dd4eb4110d298dcd07a9e2f7d519014043f7c6846465affe5c28c563ea22132`.
Independent Senior Prompt Engineer v1 review found no required corrections under
script-admission v4, run-agent-review v2, lifecycle v3 and ADR0044 v2; scores
5/4/5/5/4/4, elapsed 102/180 seconds. Only preparation's existing partial
diagnostic identity/reason changed, preserving debt and siblings; all 233 rows
and the allowed-delta check passed. Ledger SHA:
`52b30b30f09db0a1758e4318c410e915feff4313b022be65cf502fbe76eaf7dc`.
The README-writing skill kept the correction scoped to temporary retention and
its production/backup-proof limits; parent prose/source review reconciled its old
protected-creation wording with the actual source. Whitespace checks passed.
No source files or recurring checks were added, removed or moved. Native runtime
qualification is the next connected increment, not completed by these results.

Native runtime qualification is now implemented and parent-reviewed against the
actual runtime/cleanup consumers. Three methods passed on handle 76160 (exit 0,
184.570 seconds). The original 180-second allowance was explicitly extended by
60 seconds for that same running handle; completed cases were not replayed.
Thirteen policy counterexamples reject runtime before retention/submission yet
permit one independently owned deletion each; six identity substitutions reject
both routes. Optional native omission, exact integer types, pending changes,
denied/unknown transport and unchanged cross-region uncertainty are asserted.
No record/view schema or input closure changed. Frozen adapter SHA:
`7065043e4afe0bcef3d55312555b2f8ad808d16b7491cbf43e3d86f0c042a3be`;
fixture `4ae35630aa39a8b1c0c7eecdc046917813c09f526fb9f73a33489292fb85bca9`.
Independent Senior Prompt Engineer v1 review found no required corrections in
96/180 seconds under script-admission v4, run-agent-review v2 and lifecycle v3.
Only the adapter's existing partial diagnostic row changed; 233-row validation
and the allowed-delta check passed. Ledger SHA at that checkpoint:
`b8a806da42617a0da09e90f5da7403105d816c3858dec5774a445bc8cce5ef45`.
The later lifecycle v4 phase-role amendment does not alter these retention rules.
The intervening user-status turn itself was no progress; this terminal proof
changes the next action to phase-role integration. No AWS mutation occurred.

### Captured phase execution roles — 2026-11-27

The existing source plan has no identity binding for separate creation and
cleanup execution roles. Extend the existing target profile with
`provider.session_execution_roles`, schema `deploy/aws-session-execution-roles/v1`,
and exactly `role_name_suffixes: {creation: cfn-create, cleanup: cfn-cleanup}`.
The preparation owner validates exact keys and path-free nonempty alphanumeric/
hyphen suffixes, distinct derived names and the 64-character IAM name bound.
It derives `execution_roles: {creation: <ARN>, cleanup: <ARN>}` from the captured
account and checked session prefix. No user intent, operation or CLI role
override is introduced; ordinary persistent preparation is unchanged.

Consumer inventory: extend target-profile.yml and preparation-inputs.py's real
capture, complete-plan revalidation and record recovery; extend existing
runtime-configuration-test.py. SessionOperations consumes the exact captured
pair, retains it once in the immutable base and compares it on every resumed
operation. session_records.py validates that closed base and advances the draft
record schema from v8 to v9; no live old-format session exists to preserve.
CreateChangeSet sends creation authority for creation/activation and cleanup
authority for discard. Every DeleteStack request and reconstruction of its
arguments digest uses the cleanup role. Reuse the existing change-set sender;
session_cli.py's closed request permits/requires RoleARN only for those two
mutations, never ExecuteChangeSet. Existing session fixtures cover the actual
transport, retained custody, cold recovery, source mutation, no replay and full
120-resource record capacity. No new script, folder, check or schedule is needed.

Native evidence must follow documented APIs: DescribeChangeSet has no RoleARN
response field; keep its unsupported-field guard, not a fabricated equality.
Original submitted arguments and retained request custody bind that selection.
DescribeStacks exposes the associated role; stable successful current execution
must match the expected role for the positively reconciled executed phase.
A later positively observed source/request-bound prepared phase may explain
either previously attached or newly selected role: reservation alone cannot
establish that candidate, and positively not-submitted work cannot add one.
Runtime qualification rejects such a transitional state and requires a successful
current executed phase, not merely historical CREATE success. Do not infer
attachment timing during preparation, pending or failed transitions. For
independently proved-owned REVIEW/failed cleanup, a missing association does not
bar the explicit cleanup-role request; a present foreign association remains
unconfirmed. Cleanup may explicitly supply its role while creation authority is
still attached. None of these observations establishes effective permissions.
[CreateChangeSet](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateChangeSet.html),
[Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Stack.html),
[DeleteStack](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DeleteStack.html),
[DescribeChangeSet](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeChangeSet.html).

Diagnostic inventory: source declaration shape/schema/type failures use finite
`session-execution-roles-invalid`; invalid names/length and duplicate identities
use `session-execution-role-name-invalid` and `session-execution-roles-ambiguous`.
Malformed captured roles, changed retained/source binding and unconfirmed native
successful-role evidence need finite adapter reasons at their actual consumer.
Record malformed-base and closed-transport failures retain their existing codes.
Tests assert exact reasons, supplied-value/canary exclusion and rejection before
retention or send as appropriate; no new vocabulary registry is introduced.
The existing preparation/session registered checks already own these inputs;
verify actual closure rather than adding another runner. Exploratory budgets:
180 seconds for reader cases and 480 seconds for connected adapter/record/CLI
cases, including the existing capacity cycle. Parent consolidated review and
source-matched diagnostic review precede final registered integration proof.

This binds expected identities, not effective permissions: the plan stays
`not-admitted`. The separately qualified protected factory must prove account-
global role-name collision absence, full-session ownership, separation from
workload/protected roles, exclusive allowed stack writers, exact policies and
creation deadlines on submitting and execution identities. PassRole alone is
insufficient because CloudFormation may reuse an attached role. The independent
expiry/controller, protected role provisioning and lifetime backup exclusion
remain incomplete. Folder approval is now resolved by the user's explicit reply;
no IAM mutation, live launch or new authority is granted by this increment.
Read-only authority-owner inventory (132/180 seconds) confirmed no existing
protected factory. Existing source capture, session admission/storage guards,
closed IAM reads and submission mechanics are reusable, but a workload delivery
role, restore-only database role or foundation checker is not that owner. The
next concrete composition belongs in the approved controller home; do not create
unused policy scaffolding or relocate it into a shared helper to bypass approval.

The reader/configuration increment is frozen and parent-reviewed. Review removed
unnecessary acceptance of a role-less older draft before testing: cold recovery
now requires the retained pair. Six affected methods passed on handle 90777
(exit 0, 10.145 seconds / 10.35 seconds wall); a 0.56-second dependency check
confirmed their captured inputs exclude the four concurrently edited adapter
files. Total 10.91 seconds wall within 180; no failed batch or repeated cases.
Assertions cover both scopes, unchanged persistent loading, 64-character names,
case-insensitive collisions, closed declaration/intent inputs, exact finite safe
reasons, capture fingerprints/read counts and changed/missing recovery bindings.
Frozen profile SHA `a5edc9fbffee0b1ea2847c1f08cd92e7e6aa2125bd045f8fb882f4b5c5aa4ff0`;
preparation `1e96e2d3ca26880ab71fb1a84111af37366e02975b3fced6ec4bcbe61fa621fc`;
fixture `ebee629d5ae07abae1c26fa6028ecb762066d818d9c445d725e53218ddc8c594`.
The README-writing skill scoped the existing session-binding guide to these
expected-identity limits and reconciled its stale temporary backup-retention
description with the earlier zero-retention implementation. Its broader module
walkthrough is unchanged. Source declaration and copied identities are not live
authority.

Connected phase-role integration is frozen after parent review of all seven
source/configuration/fixture files named above. The immutable v9 pair, exact
CreateChangeSet/DeleteStack arguments and all three deletion-digest consumers
agree. Native role candidates require positive preparation evidence; stable
runtime and the final discard pre-send check share the same association check.
The parent and independent reviewer identified one assertion-sensitivity gap:
changing the role before execute only tested initial readiness. The existing
test now changes it inside the admission callback, after readiness and original
reservation, and asserts the exact safe denial, no provider submission, retained
`not-submitted`, and repetition without a write or replay. No runtime correction
was needed. This closes the material counterexample without a new test runner.

Thirteen affected methods passed on handles 75708 and 31291 (43.357 and
115.099 seconds). The strengthened existing method passed on 77748 in 17.484
seconds; all handles are terminal exit 0. Cumulative exploratory execution is
175.940/480 seconds, with no failed batch. The full 120-resource cycle retained
57,247 bytes and reserved at most 62,960/65,536, including a 1,024-character child
VersionId; original request identities remained unchanged. Frozen adapter SHA
`4b707513588deb9a3fef0656cec070f6665f65d5c6997a80ae356b9a729a420a`;
records `d1989844f0cda7c4f31bfb385d01d32d6daef75f3fe1e51f0003a5a85578784b`;
CLI `cd14a8f600af490c217883a4d1d886899d043daeb8a37d578f65171ec7a8e0c5`;
fixture `7e85072c813d50dc4a1640f9647db309b91f8a7aa085c2c1c9a3acbfe925ba7d`.
This increment adds/removes/moves no script-source files, recurring checks or
review requirements. It extends existing owners and tests; the source-bound
roles do not qualify effective permissions. Protected factory/controller work
and its pending folder decision are unchanged.

Next stable-boundary proof: complete the existing four diagnostic review rows
and normal metadata preparation, then request registered
`aws-environment-sessions` and `preparation-inputs-regression`. Allocate 30 minutes
wall time for that combined focused run, including selector planning, and retain
its terminal result or explicit incompleteness. The session wrapper dispatches
its full existing suite plus the native-absence fixture, not only the thirteen
affected methods. Its old 30-second advisory estimate is not a timeout or a
current measurement. No further source edits overlap verification; preparation
metadata changes are inspected and source review rebound before execution.
These requested units prove only their local boundary. Full impact selection,
controller integration, package/live proof and the ten-minute delivery budget
remain unestablished, not waived by this checkpoint.

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

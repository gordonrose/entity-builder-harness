<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plans.controlled-recovery-report-2026-10-03
version: 2
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: report
purpose: Record verified recovery evidence, preservation boundaries, and proposed rollback of the later IaaS release-control programme.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.plans.readme
  path: docs/04.deploy/plans/README.md
-->
# Controlled recovery report for 3 October 2026

Local source recovery is prepared and tested; shared recovery is not complete.
Protected Git access works. Existing uncommitted work has been preserved and
verified, a clean baseline checkout is available, and the precise source reversal
is committed locally as `57563af1` on a branch from verified live main.
Renewed AWS access confirms that the
programme's proposed control-plane resources are absent and the reviewed stored
infrastructure templates match the baseline. No AWS resource deletion or
restoration is justified by the current inventory. The owner has now approved
the narrow local recovery exception; preservation refs, durable backups and a
clean baseline checkout have been created. The action table and merge scope
below are the reviewable proposal; shared execution still needs approval.

The intended outcome is the usable source at
`0da085b50aac2b13dfb15aaac9351efea860926e`, with the later programme's operational
changes removed and unrelated work preserved. Historical commits, audit events,
and useful evidence should remain. Deployment is paused. The replacement approach
is a separate proposal in
[the replacement plan](controlled-recovery-replacement-proposal-2026-10-03.md);
none of it has been implemented.

## Verified repository facts

| Item | Verified state and consequence |
| --- | --- |
| Real repository | `/home/owner/projects/entity-builder-harness-001`, remote `gordonrose/entity-builder-harness`. |
| Local integration branch | `main` at `8052929cb947ef3a0199a338a997f8cc8ede3aac`, 74 commits older than the requested baseline. It must not become the shared recovery source. |
| Baseline | `0da085b50aac2b13dfb15aaac9351efea860926e`, committed 27 September 2026 at 23:45:26 UTC; tree `c43e0d28a6ec7726f8511194747d57efba4e246f`. The commit itself checkpoints its session log. |
| Live GitHub main | `ec4744fcb2481365eeb54fb0ecd383b8b63c6e1e`, independently checked with protected `git ls-remote` and the GitHub branches API. The sole remote programme branch has the same tip. |
| Cached remote reference | Local `origin/main` remains `81cf11c867422f5a2b26e04332e4705a1a628462`, 12 commits behind live GitHub. It was not silently refreshed. |
| Programme scope | 40 linear commits after the baseline, with no merges: 424 changed paths, comprising 388 additions and 36 modifications. Review found no unrelated integrated commit in that range. |
| Proposed source inverse | Remove 387 programme additions and restore 36 modified files. Keep the programme's historical session README, so the active source equals baseline while historical evidence remains. |
| Other local work | 13 modified or untracked files in the root worktree concern product consumption governance. Separate storage `542ca170` and tenant-authority `e8810937` branches each contain unique work. All remain untouched. |
| Registered worktrees | 89 after investigation startup; local recovery adds the clean baseline and prepared-source worktrees, making 91. The other 87 registrations still point to absent paths. Nothing was pruned. Their missing working files and activity on other machines cannot be certified. |

The new chat branch is
`chat/2026-10-03-09-44-controlled-recovery-to-0da085b5`, based on the existing local
main. Its workspace is recorded in its session README. It remains the investigation
workspace. The clean baseline and live-main preparation workspaces below are separate.

The original preservation evidence has been copied to durable local storage:
`/home/owner/projects/entity-builder-recovery-2026-10-03/evidence/entity-builder-recovery-evidence-2026-10-03/`.
The earlier temporary copies remain intact.

- `local-starting-state.json`: complete local refs, registered worktrees, status,
  and SHA-256 hashes of the 13 existing changed files.
- `root-uncommitted-files.tar`, `root-unstaged.diff`, `root-staged.diff`: copies of
  current uncommitted work. These copies do not alter or stage the originals.
- `programme-file-manifest.json`: all 424 paths and all 40 commits.
- `programme-source-reversal.patch`: the reviewed Git binary patch applied only in the isolated recovery branch for the 423
  source paths, SHA-256
  `077a0bdd05d61699b0701fc91214a7857ee4244ef3531b0ad30cf1e17c406f6b`.

Independent review reproduced the patch byte for byte and checked path, mode and
blob identities in memory. The applied source commit is
`57563af1f96e8d24de5204f359ae3de7d58c8fb4`, following the committed scope plan
`b12556b7`. All 423 inverse paths match baseline mode/blob or absence; the
programme's historical log remains byte-identical. Application and test results
are recorded below.

## Local preservation completed

The owner approved the one-off historical workspace/ref exception and local
source preparation in the follow-up request. All 13 original changed files and
102 original refs were verified unchanged before preservation. Four new refs
under `refs/recovery/2026-10-03/` retain `root-main` (`8052929c`),
`cached-origin-main` (`81cf11c8`), `verified-live-main` (`ec4744fc`) and
`baseline` (`0da085b5`).

The clean baseline branch is `recovery/2026-10-03-baseline-0da085b5`, checked out at
`/home/owner/projects/entity-builder-recovery-2026-10-03/baseline`. Its status is
empty, HEAD is exactly `0da085b5`, and tree identity is
`c43e0d28a6ec7726f8511194747d57efba4e246f`.

The preparation branch is `chat/2026-10-03-prepare-source-recovery`, initially
based on `ec4744fc`, independently rechecked against GitHub using Git and its
branches API. Its canonical durable workspace is
`/home/owner/projects/entity-builder-recovery-2026-10-03/worktrees/chat_2026-10-03-prepare-source-recovery-1708067929`.
Its session records ownership and the original investigation; supported worktree
configuration is used without changing lifecycle scripts.

The durable recovery directory contains 203 copied evidence/backup files
(approximately 36 MB), including the owner's uncommitted-file archive and the
full GitHub/AWS evidence. `preservation-manifest.json` records their SHA-256
hashes. This is private local storage, not an off-machine backup; private
uncommitted-work archives are excluded from publication.

## What the baseline actually preserves

The baseline already contains the PostgreSQL deployment programme, the existing
operational-realization scripts, candidate-task execution, infrastructure, and
the earlier deployment reliability plan. The later programme expanded existing
directories; removing those whole directories would destroy baseline work.

The baseline readiness manifest says `status: blocked` and
`mutation_authorized: false`. The image publisher is manually dispatched, requires
`refs/heads/main`, and publishes an image without deploying ECS. PostgreSQL
recovery-3 had failed input validation; recovery-4 had not begun. Returning to this
commit restores that unfinished state. Sources:
[baseline readiness](https://github.com/gordonrose/entity-builder-harness/blob/0da085b50aac2b13dfb15aaac9351efea860926e/infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml)
and [baseline target profile](https://github.com/gordonrose/entity-builder-harness/blob/0da085b50aac2b13dfb15aaac9351efea860926e/infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml).

Existing resources to preserve include RDS, DynamoDB persistence, SQS, ECR,
publisher and monitoring roles, Cognito, ALB/DNS, secrets/configuration, foundation
and service stacks, logs, backups, and scheduled monitoring. The database's
loopback-only egress correction also predates the baseline and must remain.

Baseline source records private encrypted RDS with seven-day backup retention,
deletion protection and snapshot policies. DynamoDB persistence contains durable
smoke/outbox records and has retention, deletion protection and point-in-time
recovery. The live inspection below confirms current protections and backup
coverage. It did not read database rows, secret values or queue messages, or test
a restore. No database, stack, secret, queue, role or image deletion is justified.

## Verified GitHub state and remaining history gaps

Live inspection found one environment, `staging`, created and last updated on
1 July 2026. It permits the `main` branch. There are no repository Actions secrets
or variables, no staging secrets, and one staging variable,
`RAG_RULEBOOK_AWS_DEPLOY_ROLE_ARN`, unchanged since 1 July. Values were not exposed.
Both remote branches report unprotected; repository rulesets are empty.

Six image-publication runs occurred after the baseline. All failed; job-step
inspection found that image pushes, both artifact uploads, and both attestation
steps were skipped in every run. Five reached AWS authentication and ECR login;
the first failed before authentication. This verifies what these workflows did,
but does not exclude images or configuration created through other routes.

| Publication run | Failure point |
| --- | --- |
| [36982838978](https://github.com/gordonrose/entity-builder-harness/actions/runs/36982838978) | Platform shell checks, before AWS authentication. |
| [37050923795](https://github.com/gordonrose/entity-builder-harness/actions/runs/37050923795) | Image build, after authentication and ECR login. |
| [37063262648](https://github.com/gordonrose/entity-builder-harness/actions/runs/37063262648) | Image build, after authentication and ECR login. |
| [37066022523](https://github.com/gordonrose/entity-builder-harness/actions/runs/37066022523) | Image build, after authentication and ECR login. |
| [37071477462](https://github.com/gordonrose/entity-builder-harness/actions/runs/37071477462) | Image build, after authentication and ECR login. |
| [37074022425](https://github.com/gordonrose/entity-builder-harness/actions/runs/37074022425) | Image build, after authentication and ECR login; newer than the programme's final recorded attempt. |

The source-validation workflow has 20 runs: 15 passed, 3 failed and 2 were
cancelled. All were attributed to `gordonrose`; this identity cannot distinguish
concurrent agents or terminals. There are no current Actions
artifacts. One 21,816,868-byte Buildx binary cache exists, ID `8406414532`, created
2 October at 08:16:22 UTC, key `buildx-dl-bin-0.37.2-linux-x64`. A shared tool cache
is not an operational release controller; preserve it unless later evidence
establishes a reason to remove it. Keep failed environment deployment records and
workflow runs as audit evidence. No open pull requests, webhooks, deploy keys or
releases were found. The only collaborator is `gordonrose`, with administrator
access. Actions is enabled with all actions allowed; the default workflow token
has read permission and cannot approve pull requests.

Current settings do not prove every prior permission or policy value. Missing
account audit evidence must remain an explicit limitation; do not invent prior
settings or reset protections from assumptions. This is a personal repository;
the security-log API probe returned 404. The owner's security-log UI/export was
not available through this inspection. Read-only API evidence is under
`/tmp/controlled-recovery-github-audit/`.

## Verified live AWS state

AWS sign-in works. Caller identity for `kanbien-dev` confirms account
`337159794548`, using the assigned administrator role. Organizations and both
configured SSO sessions expose only this account. All 17 enabled regions were
included in the regional history/configuration scope; the Kanbien staging target
is in `eu-west-1`. IAM and bucket inventory were checked globally. This covers
the configured access and visible organization, not hypothetical unconfigured
accounts. Inventory observations were collected on 3 October, starting at
09:14 UTC. No secret values, application data, or queue messages were retrieved.

| Subject | Verified current evidence | Rollback treatment |
| --- | --- | --- |
| Programme control-plane table | `kanbien-staging-platform-shell-release-control` returns `ResourceNotFoundException`. | Remove its source declaration; no live table to delete. |
| Programme evidence bucket and policy | `kanbien-staging-platform-shell-release-evidence-337159794548` returns 404 and is absent from the global account bucket list. | Remove its source declaration; no bucket or associated bucket policy to remove. |
| Programme controller role | `kanbien-staging-platform-shell-release-control-controller` returns `NoSuchEntity`. | Remove its source declaration; no live role to remove. |
| Stored infrastructure templates | Foundation, service and deployment-artifact templates match `0da085b5` structurally, including CloudFormation intrinsics: 64, 14 and 2 resources respectively. Their 986 recorded stack events contain no post-baseline stack update. | Preserve all three stacks. Stored-template equality does not by itself prove every live resource is free of drift. |
| Publication permissions | Existing publisher trust and inline policy exactly match both baseline and programme-tip source; no managed policies are attached. All 38 IAM roles predate baseline; none of 15 customer-managed policies was updated afterward. | Preserve roles, OIDC provider and policies. Creation dates are not a complete history of every inline-policy change. |
| Published images | No retained image in any of the three ECR repositories was pushed after baseline. `platform-shell` has 55 image/attestation entries; newest push was 27 September at 23:07:57 UTC. | Preserve pre-existing images. This corroborates the six failed GitHub publication attempts. |
| Existing HTTP runtime | Server desired/running counts are 1/1, task health is `HEALTHY`, and its ALB target is healthy. Worker remains 0/0. Server task definition `:20` and the running task both predate baseline; all nine current target task definitions predate baseline. | Preserve the running service. This is infrastructure health, not a new authenticated application test or candidate qualification. |
| Target RDS and backups | `kanbien-staging-platform-relational` is available, private, encrypted and deletion-protected. Seven-day recovery coverage includes baseline; eight automated snapshots are available. | Preserve database and rolling backups. No database restore or SQL test was performed. |
| Existing DynamoDB and queues | Persistence table is active, deletion-protected, with approximately four items and 35-day point-in-time recovery covering baseline. Four worker/relational queues report zero visible, delayed and inflight messages. | Preserve data and queues. Metadata counts are approximate and do not prove historical data equality. |
| Existing deployment-artifact bucket | Four objects and four null-version entries, no delete markers or post-baseline modification; encryption, public-access blocks, ownership and transport policy match baseline intent. Versioning is not enabled. | Preserve this shared pre-existing bucket. Metadata cannot prove past content equality or exclude transient overwritten/deleted objects. |
| Secrets and parameters | All regional queries succeeded: nine secrets and two SSM parameters, all in `eu-west-1` and all pre-existing. | Preserve. No secret value was read or printed. |

The running application digest is
`sha256:165ccb724989cfeb7a60bcdb4bfaf20f752a8e8dfc1c12efe9220c27488aed7c`.
It matches the current service image parameters and pre-baseline ECR tag
`staging-20260927-10c9c90fad1a-run36357521306`. The commit named by that ECR tag
is an ancestor of the baseline; image provenance was not independently
revalidated. Foundation exports consumed by the service include the
persistence table, relational credential references and relational configuration;
removing the foundation would break these shared dependencies.

The database security group still has exactly one egress rule, to
`127.0.0.1/32`, and PostgreSQL ingress only from the existing server, relay and
worker security groups. RDS reports `rds.force_ssl=1`, with the parameter group
in sync and no pending instance modifications. This is configuration evidence;
no database connection or TLS handshake was tested.

A legitimate post-baseline change must remain: the RDS-managed master secret
rotated on 3 October at 05:09:22 UTC under its seven-day schedule. Secret metadata
and CloudTrail's RDS-service role actions confirm successful rotation. Replacing
that credential with an old value would undo normal database operation, not the
IaaS programme. Preserve normal backups, logs and monitoring history as well.

Existing observation limits matter. The latest retained Foundation drift result
is from 2 October at 21:58 UTC and names one parameter-group `/Parameters REMOVE`
difference. No new drift assessment was run. The inspected 3 October 05:15 UTC
[reconciliation run](https://github.com/gordonrose/entity-builder-harness/actions/runs/37099261022)
passed source/account/artifact-stack-status checks, then stopped at
`artifact-stack-drift-evidence-stale`. Stale evidence does not establish that a
resource changed. A future approved deployment must resolve evidence freshness
and classify actual drift; this inspection does not authorize an active
assessment or manufacture a new observation time.

The account is not uniformly healthy. The unrelated legacy `service-platform`
service is desired 1/running 0 with no registered target; old `database-1` has
inaccessible encryption credentials while its September replacement is
available. These pre-existing resources were left untouched. Current HTTP health
does not complete PostgreSQL Stage 6 or prove a new candidate.

The session preserves sanitized
[target evidence](../../../commitLogs/2026/oct/03/2026-10-03-09-44-controlled-recovery-to-0da085b5/recovery-evidence/aws-target-summary.json)
and [identity/configuration evidence](../../../commitLogs/2026/oct/03/2026-10-03-09-44-controlled-recovery-to-0da085b5/recovery-evidence/aws-identity-summary.json),
including baseline-template comparison hashes and protection metadata.
Detailed supporting records remain under
`/tmp/controlled-recovery-aws-target-audit/` and
`/tmp/controlled-recovery-aws-identity-audit/`.

## AWS history coverage and limits

The management-history window is 27 September 2026 at 23:45:26 UTC through
3 October at 09:20:19 UTC. Management-write queries were paginated to exhaustion
in all 17 enabled regions, including `us-east-1` for global IAM evidence, with
no permission errors. All 2,173 returned events were in `eu-west-1`; the other
16 regions returned none.

| Observed activity | Events | Treatment and attribution |
| --- | ---: | --- |
| Existing ECS runtime lifecycle | 2,103 | Existing service roles, task logs, network interfaces and target registrations; preserve. Much of this is the older service's repeated task churn, not a new programme deployment. |
| Load-balancer-managed network lifecycle | 9 | Existing ELB service role, including address allocation/association; preserve. Specific ALB linkage was not independently established for every event. |
| Cognito token issuance | 32 | Timing and counts match pre-existing synthetic checks, but recorded identity is unknown; this is correlation, not proven actor identity. |
| SSO authentication | 20 | Four sign-in sequences, including the renewed current session; retain audit history. |
| Automatic RDS secret rotation | 5 | RDS service identity and secret metadata corroborate normal rotation; preserve the current credential. |
| Administrator drift assessments | 4 | Changed assessment metadata; preserve as a historical difference with uncertain task attribution. |

One ELB-managed network-interface deletion failed with
`Client.InvalidParameterValue`; the remaining events record no error. No
unclassified management-write event remains. The scan found no infrastructure
stack create/update/delete, task-definition registration, service deployment,
IAM policy change, or ECR publication/deletion/configuration action. Together
with current inventory, this establishes no programme resource rollback target
within the audited management-event scope.

The four successful `DetectStackDrift` calls on 2 October were on the
deployment-artifact stack at 18:33:29 and 19:01:52 UTC, and Foundation at 18:35:42
and 21:58:14 UTC. All used the administrator SSO session `gordon-kanbien`.
That identifies the credential, not the initiating conversation; the reviewed
programme log still recorded earlier assessment approval as pending. Do not
assign these calls to a particular agent from the timestamp alone. Their
assessment records and occurrence cannot genuinely be undone.

Separately, 54 successful GitHub identity assumptions comprise five publisher
sessions and 49 existing monitoring sessions. This corroborates the five failed
image runs that reached AWS credentials. ECR authentication was also confirmed
in the latest image run's bounded time window. General ECR pull and internal
service-authentication reads were not exhaustively traversed in `eu-west-1`;
the complete management-write scan is unaffected.

The existing `kanbien-staging-management-events` trail has logged since
15 May, covers multiple regions and global services, and remains active.
Its selectors include management events but no data events; no CloudTrail Lake
store was found. Regional event history covers 90 days of management events.
Consequently, this audit cannot exclude S3 object changes, DynamoDB item changes,
application/database changes or other unlogged data operations. Events after the
fixed cutoff, ingestion delays, currently disabled regions and unconfigured
accounts remain outside the history claim.
[AWS event-history limitations](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html).

The [saved history summary](../../../commitLogs/2026/oct/03/2026-10-03-09-44-controlled-recovery-to-0da085b5/recovery-evidence/aws-history-summary.json)
contains event identifiers, actors, regional completion and these limits.
Detailed sanitized events remain in `/tmp/controlled-recovery-aws-history-audit/`.
Historical equality of all external data is not established. Preserve unknown
or unrelated changes rather than assigning ownership from their date alone.

## Proposed action inventory and order

The completed inventory/history and tested local inverse narrow the proposal to
shared source recovery. No AWS resource deletion or restoration is justified.
Rows 1–3 are completed local work; rows 4–5 are the proposed shared change;
rows 6–7 are preservation boundaries.

| Order and action | What exists now | Programme ownership evidence | Intended result | Risk or irreversibility | Verification |
| --- | --- | --- | --- | --- | --- |
| 1. Preserve local state — complete | Four new preservation refs; durable evidence and private uncommitted-file archive. | State protection, not programme removal. | Original main, cached/live tips and baseline retained without changing existing refs. | Local storage still needs ordinary machine backup; private archives are not published. | All four exact ref hashes verified; all 13 archived file contents and 203 copied-file hashes verified. |
| 2. Create clean baseline workspace — complete | Separate baseline branch and durable checkout at `0da085b5`. | Exact user-selected commit. | Usable clean source checkout, without disturbing old registrations or work. | Baseline contains unfinished deployment work; a clean checkout is not deployment readiness. | Exact HEAD/tree and empty status verified. |
| 3. Prepare source rollback locally — complete | New branch from `ec4744fc`; source inverse committed as `57563af1`. | Complete 40-commit/424-path manifest; exact 423-path inverse. | Remove 387 programme additions, restore 36 files, retain the historical log and named recovery records. | Any new remote work requires reclassification; local tests cannot prove a live deployment. | Exact source equality, 177 retirement checks, relevant local suites, recognition and commit gates passed. |
| 4. Restore shared deployment source after exact approval | GitHub main and programme branch at `ec4744fc`. | Same reviewed manifest and finalized local diff. | Publish a reviewable rollback branch/PR and use a normal merge; no force push. Keep historical programme branch as evidence. | Shared source changes; push/PR may trigger CI and later scheduled monitoring. These effects must appear in the final approval. No manual deployment dispatch. | Recheck remote immediately before publication; inspect PR diff, checks and merged source; confirm no deployment was dispatched. |
| 5. Retire programme workflow through the source change | Added `release-control-source-validation.yml`; modified pre-existing image publisher. | Both changes lie in the programme range. | Remove programme workflow from active main source; restore baseline publisher. Retain run history. | Old historical runs remain rerunnable by authorized users; avoid rerunning them. | Inspect workflow files at merged SHA and Actions workflow state; review any provider-side disabling separately if needed. |
| 6. Preserve GitHub settings, cache and historical records | July staging settings, no current artifacts, one tool cache, failed runs/deployment records. | No verified programme-owned setting needing restoration. | Existing settings/evidence retained. | Original values for unaudited settings remain unknown. | Repeat metadata inspection and compare the captured inventory. |
| 7. Preserve AWS resources and legitimate lifecycle changes | Proposed controller/table/bucket are absent; stored templates and publisher permissions match baseline; current server/image predate it. Managed credential rotation and backups continue. | Live inventory, baseline comparisons, failed publication jobs and separately classified history. | No AWS resource mutation. Remove the programme's unused source declarations through the Git change; preserve runtime, data, credentials and evidence. | Current inventory is not historical data equality; deleting shared resources or reversing normal rotation would damage preserved work. | Recheck scoped identity/resource absence and relevant changes before any later approved execution; record explicit audit limits. |

The accepted local exception is recorded under
[Missing Governance Stop Condition](../../../.agentic/01.harness/standards/missing-governance-stop-condition.md):
“User approval alone does not create governance for a new class of action.” Its
one-off-exception mechanism covers only these historical workspace/ref
operations and local preparation. The decision and reason are recorded in both
session logs. No permanent harness change or gate bypass was used.

The exact shared scope is repository `gordonrose/entity-builder-harness`,
target `main` at `ec4744fcb2481365eeb54fb0ecd383b8b63c6e1e`, and source branch
`chat/2026-10-03-prepare-source-recovery`. The immutable publication head and
diff digest are recorded in the final review handoff and durable
`merge-proposal.json`; source restoration is `57563af1`, followed only by
reviewed recovery documentation/evidence and session bookkeeping.

Proposed order: recheck both hashes, publish that new branch without force,
open its rollback PR, review resulting CI, and perform a normal merge commit
only for the reviewed head/base. A changed head or advanced main requires
reclassification before execution. Keep all existing branches, including the
programme branch, and request no branch deletion or repository setting change.
After merge, compare the merged source against the approved manifest and
baseline differences, inspect workflow state and confirm no manual publication
or deployment was dispatched.

Both deployment/publication workflows require manual dispatch. Source CI may
run on push/PR while GitHub evaluates the transition. Existing scheduled
reconciliation, synthetic and metric monitoring continues, including AWS
authentication, reads, fixed HTTP checks and possible existing SNS alerts.
That ordinary activity is distinct from an agent-initiated resource change.
This proposal authorizes no AWS mutation, image publication, deployment,
database bootstrap, history erasure, settings reset or replacement implementation.

## Local validation and review status

| Check | Result and limit |
| --- | --- |
| Source inverse | Application check passed; all 423 paths equal baseline mode/blob or absence. Full-tree comparison permits only the exact recovery/history/index files recorded in the linked evidence. Historical programme log unchanged. |
| Retirement references | All 177 planner and 177 post-inverse checker cases passed, covering 387 removals. No active reference remains; historical references are preserved. |
| Deployment checks | Realization, workflow, infrastructure, reconciliation and container-boundary suites passed. Infrastructure includes candidate/preflight, relational-smoke fixtures and PostgreSQL-reference checks. No external calls were made by these suites. |
| Runtime checks | Server and product typecheck, build, runtime and boundary checks passed. |
| Compiled packaging | Existing image-runtime payload check passed. Its first run hit a cross-filesystem temporary rename; setting supported `TMPDIR` inside the worktree resolved it without a source edit. This is not a final container-image execution test. |
| Metadata and commit checks | Final metadata passed for all 969 artifacts, including the recovery documents. Generated recognition and current-source validation passed (7 sources, 2,219 terms), as did normal commit readiness, local links and whitespace checks. |

The earlier missing-workflow recognition error belonged to the old investigation
checkout. It is absent from the correct baseline/live-main catalogue. The
prepared branch uses the existing generator; the final catalogue changes only
for named recovery artifacts, and routing returns to baseline. No absent workflow
was recreated, no unrelated old-workspace governance was repaired, and no failed
check was bypassed.

The review copies are committed on the prepared recovery branch; the original
investigation workspace remains preserved. The report and replacement plan keep
draft status because shared recovery and replacement approval remain outstanding.
Detailed validation records are preserved in the recovery sessions and durable
`evidence/local-validation/` and `evidence/path-migration-audit/`.
The [source-equality record and exact allowed differences](../../../commitLogs/2026/oct/03/2026-10-03-09-44-controlled-recovery-to-0da085b5/recovery-evidence/source-equality.json)
make the deliberate differences from baseline reviewable without excluding
whole log or documentation directories.

## Completion judgment

Local baseline source is available and the ordinary source reversal is prepared,
tested and committed. Shared `main` is not yet restored; it still needs the
reviewed publication/merge approval. The original root work, original refs, AWS
and GitHub configuration have not been changed by this recovery. Protected Git
access, authentication, the local exception and recognition validation are resolved.
Live AWS resource/configuration verification is complete for the stated scope;
historical/data limitations remain explicit.

Even after source restoration, deliberate differences will include preserved
historical programme/recovery records, ordinary revert/merge history, unrelated
local branches/work, normal credential rotation and backups, and irreversible
monitoring/authentication/assessment history. Already consumed build/cloud time
cannot be recovered by reverting source.
Any unverified external differences must be listed separately rather than called
restored.

It is not yet established that deployment work can safely restart. The baseline
itself had unfinished PostgreSQL recovery and failed reconciliation. A later
deployment decision needs current evidence, properly classified drift, an
appropriate image and candidate proof, and a bounded deployment approval. The
existing HTTP target is healthy, but deployment has not resumed.

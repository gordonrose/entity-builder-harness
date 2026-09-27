<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.local-to-proven-deployment-reliability
version: 1
status: draft
layer: 04.deploy
domain: deployment.realization
disciplines:
- agentic
- architecture
- backend
- security
- sre
kind: implementation-plan
purpose: Establish planning and bounded investigation before implementation, then deliver a reusable route from local changes to an independently proven staging release with recoverable execution.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# Local to proven deployment: implementation plan

Prepared: 2026-09-27. Owner: deployment layer; one coordinating implementation
agent owns integration and any approved live execution. Target handoff: the
morning following the authorised implementation run, Europe/Dublin. Record the
actual start and agreed handoff time in UTC before starting; this document does
not start a background job or promise that the full programme fits one evening.

## Outcome and honest scope

Deliver one repeatable path from a local source change to the exact immutable
candidate running in AWS staging, with authenticated application behaviour,
persistence/delivery semantics, actionable failure evidence, and verified
cleanup/recovery. Known regressions must fail before a public rollout.

The joined HTTP-to-durable-delivery demonstration uses the existing DynamoDB
server composition. Qualify PostgreSQL separately through its existing dedicated
bootstrap/migration/acceptance/relay/worker task graph. The inspected server
does not expose PostgreSQL acceptance over HTTP. That additional composition
remains explicitly unqualified; implement it under its own bounded capability
slice before claiming an HTTP-to-PostgreSQL product path works.

The reusable contract remains provider-neutral. The first qualified adapter is
AWS ECS/Fargate for Kanbien staging, account 337159794548, eu-west-1. Azure,
Oracle, other AWS targets, and other providers remain unqualified until their
own adapters pass the same acceptance suite. A schema passing on AWS is not
proof for another provider.

Separate the following results in every status report:

| Result | Required evidence |
| --- | --- |
| Source-ready | Deployment design and prerequisite investigations recorded; reviewed source, clean-environment checks, executable negative cases, and target integration all pass. |
| Staging release proven | The same candidate digest passes private execution, promotion, authenticated application checks, and the declared semantic route. |
| Recovery proven | An approved failure/recovery exercise reaches the declared steady state and proves owned-resource cleanup. |
| Continuous control proven | A producer refreshes drift evidence and its consumer/alert path succeeds over at least two subsequent scheduled cycles. |
| Production-ready | Separate production, data protection, capacity, availability, restore, SLO, and operating requirements are satisfied. Not an overnight claim. |

Never relabel source-ready or a healthy HTTP process as the later results.
The deadline does not permit weakening a gate or manufacturing evidence.

## Change to the working method

The primary intervention is earlier design and discovery. Required checks
support that method; adding more commit or merge checks alone does not deliver
this plan. Apply the method to this reliability programme itself before
implementing its shared tooling, then use it for future deployment-affecting
platform, adapter and infrastructure work.

1. Describe the complete deployed behaviour and its dependency path before
   decomposing work into code tasks. Include the image, every operational
   entrypoint, provider bindings, data/delivery semantics and recovery.
2. Identify what is already qualified and what remains an assumption. Assign
   each material unknown an owner, a falsifiable question, the smallest useful
   experiment, an effort/attempt limit and a decision it will inform.
3. Resolve assumptions that could invalidate the design before substantial
   dependent implementation. Small investigation code is allowed in this
   stage. A deferred assumption must name the work and claims it blocks.
4. Reuse a qualified reference path with explicit limits. Extend one supported
   route through its full lifecycle before multiplying adapters or targets.
5. Implement against that design using shared build/deploy commands. Diagnose
   a failure as a specific failed assumption; change the hypothesis and run
   the cheapest relevant check before repeating an expensive operation.
6. Close work with evidence for the exact deployed release and required
   recovery behaviour. Feed newly discovered failure modes into the reusable
   plan/reference implementation so the next task benefits.

Planning depth follows the change. A new provider, execution model, identity,
network path, stateful dependency or migration needs explicit qualification.
A change within a qualified path records its affected dependencies and checks,
and reuses still-valid evidence. Documentation-only work and ordinary business
logic changes with no deployment-contract impact do not require fresh cloud
experiments. Do not attach the full process to every small edit or commit.

## Repository impact and placement

Keep existing application contracts, product composition, provider/type/service
runtime adapter layout and CloudFormation ownership as the starting point.
No wholesale application rewrite or repository reorganisation is required by
this plan. Changes concentrate on planning, build/deploy tooling and evidenced
runtime defects.

| Surface | Required change and boundary |
| --- | --- |
| `.agentic/03.product/` and `.agentic/aws/` workflows | Connect runtime planning and AWS planning to one reusable deployment-design template and its relevant reference path before implementation. Store rules once and reference them from the existing workflows. |
| `.agentic/01.harness/` | Extend the existing realization standard/schema/workflow and reusable planning shape where they own the generic contract. Keep AGENTS.md small. |
| Build scripts, workspace manifests, TypeScript configuration and image recipes | Consolidate the reachable release dependency graph and isolated artifact checks; migrate affected consumers incrementally. |
| `scripts/04.deploy/` | Extend the existing `operational-realization-gate/` compiler and provider mapping on the refreshed baseline; consolidate deployment execution, diagnostics and recovery. This is the largest tooling refactor. |
| `infra/04.deploy/` | Keep target composition, environment bindings and infrastructure templates here. Add or adjust the candidate boundary and reviewed supporting resources as required. |
| `platform/adapters/`, runtime entrypoints and tests | Make bounded provider, migration, lifecycle and diagnostic fixes; preserve app-facing boundaries unless a demonstrated defect requires a separately explained contract change. |
| `.github/workflows/` and operator documentation | Invoke the shared commands at the appropriate stages and replace obsolete instructions after the qualified path is adopted. |

Deployment orchestration stays with 04.deploy; provider-neutral deployment
schemas do not make it product runtime code. The earlier illustrative
`platform/realization/` tree is not an adopted directory or a required new
package. Use the existing owner paths on the refreshed baseline. Any necessary
committed-file moves or retirements follow the existing artifact-path migration
workflow and preserve required references.

## Baseline, existing work, and workflow ownership

The audit examined worktree 8052929c and later source through 6a435b15. Planning
review is pinned to 0c3e9cd9500f3010ebacc0e6cc1ba9cfd8dd3f1a; that revision adds
session evidence to the same technical baseline. The planning worktree is
older than these later commits. Do not implement blindly against it.

At implementation startup, resolve current remote state through the governed
chat lifecycle, select a clean assigned source worktree, record its exact SHA,
and reconcile work already completed by other sessions. Existing local edits
to production-reference-target-baseline.md and platform-scheduler-v1.md are
owned by other work and must not be absorbed, overwritten, or staged.

Use the current repository versions of these existing owners:

- [Chat startup](../../../00.chat/workflows/chat-start.md) and its referenced
  worktree, refresh, promotion, and git-approval workflows.
- [Harness changes](../../../01.harness/workflows/change-harness.md) for
  contracts, validators, instruction changes, and CI governance.
- [Product/runtime implementation](../../../03.product/workflows/platform-runtime-implementation.md)
  for runtime and adapter code.
- [AWS planning](../../workflows/plan-aws-change.md),
  [inspection](../../workflows/inspect-aws-state.md), and
  [approved execution](../../workflows/execute-approved-aws-change.md).

This plan sequences the audit remedies. It does not replace the architecture
owned by the existing Operational Realization v2 programme. Extend that
programme and its compiler/adapter boundary; do not build a competing release
framework. Its inspected source is
[the v2 programme at the planning baseline](https://github.com/gordonrose/entity-builder-harness/blob/0c3e9cd9500f3010ebacc0e6cc1ba9cfd8dd3f1a/docs/04.deploy/plans/operational-realization-v2-programme.md).
On a refreshed worktree use docs/04.deploy/plans/operational-realization-v2-programme.md.
The older kanbien-staging-image-execution-preflight-v1.md is explicitly
superseded before implementation; treat its useful details as evidence, not
as the governing design. Also integrate the existing AWS-change reliability
programme and the PostgreSQL reference/Stage 6 programme.

## Authority and unattended-work prerequisites

Writing this plan has been authorised. Implementation, commits, promotion,
image publication, repository settings, and cloud execution are separate
action classes. A future implementation instruction authorises its stated
source scope; do not infer external authority from this document.

Before dependent actions, record the authorisation already present in that
execution chat. Reuse valid scoped authority instead of repeatedly asking.
Where authority is absent, finish the independent source work and prepare the
concrete change/rollback bundle before requesting that authority.

| Action | Boundary for the implementation agent |
| --- | --- |
| Source implementation | Once instructed to implement, complete P0a/P0b for the relevant dependencies, edit the capability-owned paths below, add meaningful tests, and update their existing workflows/indexes. Bounded investigation code belongs to P0b. |
| Local commits / merge / push | Apply the existing git approval workflow. Never force push, rewrite history, delete branches, or discard another session's work. Remote promotion must name the reviewed source SHA. |
| GitHub changes | Reading settings/runs is inspection. Changing rulesets, required checks, environments, secrets, or permissions needs explicit scope. |
| Image publication | Use the existing staging ECR identity and immutable digest workflow only when authorised. A publication success is not deployment proof. |
| Candidate onboarding and proof | Review the precise task-definition addition/update, existing role use, network, maximum task count/duration, cleanup, and cost first. No implicit IAM or network repair. |
| Service promotion / rollback | Only the reviewed staging service change and known-good restore through the declared IaC ownership path. |
| Database / delivery / restore proof | Separate bounded synthetic operation scope, identities, attempt labels, data policy, disposable restore ownership, deletion/cleanup authority, and cost. No production data or destructive migration. |
| Drift producer | Separate reviewed identity, permissions, workload/schedule, cost, failure alert, and rollback; not implied by candidate permission. |

<!-- deterministic-check: allow reason="actual cost ceilings require scoped user authority; the implementation will validate the resulting launch record" -->
The launch record must contain the actual approved cost ceilings: incremental
proof spend, recurring additions, and maximum concurrent/duration limits. Do
not infer new authority from historical USD25/month or EUR50/month references.
If live execution is not approved, report source-ready and the exact remaining
approval bundle; do not claim the overnight live objective was achieved.

Check prerequisites early: fresh GitHub/AWS credentials for the expected run
duration, required role assumption, local Docker/Buildx availability, declared
Node/npm/Python/AWS CLI/validator versions, approved target ownership, known-good
release, current stack state, and source/DLQ/worker steady state. Audit-time
kanbien-dev SSO was expired. Authentication renewal needs the operator's normal
interactive process; do not collect credentials in chat or files.

Inspect actual GitHub branch/ruleset checks, environment restrictions/approval,
and OIDC trust. Source declarations are not proof of live GitHub enforcement.
Unavailable settings access is an unresolved evidence gap, not a passed check.

## Work allocation and critical path

One coordinator owns the release manifest, integration, target lock, approvals,
and live changes. Delegate disjoint source work only. Shared schema files,
package.json, target-profile.yml, service templates, and release workflows must
each have one editor; other agents propose changes to that owner.

| Package | Owner lane | Depends on | Required milestone |
| --- | --- | --- | --- |
| P0 Baseline and prerequisites | Coordinator | Launch instruction | Current source/target/authority inventory; no overlapping target operator. |
| P0a Deployment design and reusable planning workflow | Coordinator/harness | P0 | Complete path, qualified-pattern comparison, unknowns and bounded file/refactor map recorded before substantive implementation. |
| P0b Bounded investigations and first reference slice | Coordinator/relevant owner | P0a; authority for each experiment | Design-invalidating unknowns resolved or dependent work explicitly blocked; first supported route and evidence recorded. |
| P1 Build and independent validation | Build/backend | P0a/P0b for its dependencies | Clean-runner PR path and exact-image tests. |
| P2 Trusted evidence and v2 graph | Harness/security | P0a/P0b for its dependencies | Invalid/replayed proof rejected; real target contract integrated. |
| P3 Target controller and recovery | Deploy/SRE | P0a/P0b; P2 interface | Bounded state machine, diagnostics, lock, terminal waits, cleanup. |
| P4 Provider and migration semantics | Backend | P0a/P0b; P1 environment | Real-engine and request/IAM regressions; route-specific proof. |
| P5 Integrated private proof and promotion | Coordinator | P1-P4; live authority | Same candidate proven, promoted, and semantically exercised. |
| P6 Recovery and continuous reconciliation | Coordinator/SRE | P3/P5; relevant authority | Recovery/cleanup evidence; recurring producer and consumer qualified. |
| P7 Adoption, retirement and handoff | Coordinator | Completed packages | Shared path adopted, superseded paths retired, truthful result matrix and executable operator command. |

P1-P4 may run in parallel after the coordinator settles their interfaces and
resolves the assumptions that block each package. Independent work may proceed
while another investigation is blocked. P0b is bounded feasibility work, not a
requirement to finish the new controller before implementing it. Its evidence
cannot substitute for P5's exact integrated candidate proof.
The launch record must name the first coherent source slice and its acceptance
IDs. Completing that slice alone is partial progress unless every required
source-ready check for the integrated candidate also passes.
Do not wait until the end of the evening to discover expired credentials,
missing permissions, overlapping deployments, or an unavailable real engine.
If the time budget contracts, finish a coherent source-ready slice and its
reviewable live bundle. The full live/continuous result remains incomplete.

## P0a: design the complete deployed slice before implementation

Primary surfaces: the existing product/runtime and AWS planning workflows,
existing realization standard/schema/template, and this programme's launch
record. Extend their current owners instead of adding a competing plan system.

Deliver one reusable deployment-design template and a completed instance for
this programme. Its structured runtime graph must reference or populate the
existing v2 contract; do not hand-maintain a second inventory of the same roles,
artifacts and dependencies. Keep human decisions and unknowns alongside those
references. Include these minimum fields because each closes an audited gap:

| Planning item | Required content and purpose |
| --- | --- |
| User-visible outcome and scope | Supported end-to-end route, target, exclusions and observable completion; distinguish HTTP/DynamoDB from task/PostgreSQL. |
| Complete execution path | Build/package graph; server/bootstrap/migration/relay/worker and sidecars as applicable; data/queue, network/TLS, config/secret references, identity for each operation, readiness and telemetry. Mark genuinely inapplicable parts explicitly. |
| Existing reference and difference | Exact qualified reference/version, supported envelope, changed bindings and assumptions. A similar-looking target is not automatically equivalent. |
| Provider constraints | Current authoritative references with review date and the exact assumption they support; supported artifact platform, API/schema, IAM action/resource, engine and lifecycle behaviour as applicable. Record unresolved contradictions. |
| Unknowns and experiments | Assumption ID, impact, confidence/evidence, owner, smallest distinguishing test, prerequisites/authority, time/cost/attempt bound, success/failure observations, fallback or decision, and dependent work. |
| Proposed source changes | Exact owner/file scope, interfaces, reuse/add/refactor/retire classification, compatibility and adoption order. Identify shared-file owners before delegation. |
| Execution and recovery | Idempotency, concurrency, deadlines, failure diagnosis, known-good state, schema compatibility, cleanup ownership and separately scoped authority. |
| Proof plan | For each material claim: check/experiment, environment, identity, expected observation, candidate/target binding and invalidation condition. Choose the cheapest adequate proof. |

Review this instance before substantial implementation. The coordinator must
trace one real request or task through the whole declared path and explain each
dependency edge, including how resources become usable and how failure is
recovered. A populated template or passing schema cannot certify the design.
Record the review decision and unresolved assumptions; reuse existing scoped
user authority instead of introducing a new permission prompt for this review.

Update the existing entry workflows so agents perform this planning when a
change affects deployment dependencies. Provide a short example of a new
adapter and a short example of an ordinary change within a qualified path.
Exercise those two planning scenarios and a documentation-only scenario: new
assumptions must be surfaced, valid reuse must be recognised, and irrelevant
cloud work must not be required. Validate deterministic completeness and
references automatically; keep architectural judgment explicit in the review.

## P0b: resolve the risky assumptions with bounded experiments

Use existing checks and disposable fixtures first; write only the minimal
investigation code needed to answer the question. Retain useful executable
probes in their existing owner when they become regression protection. Live
provider experiments need the relevant scoped authority even when small.

1. Rank unknowns by whether failure would change the architecture, bindings or
   execution sequence, and by how expensive late discovery would be. Resolve
   the highest-impact dependencies first. Every investigation has an explicit
   time/attempt budget before it starts; use stricter existing execution limits.
2. Use current provider documentation and local static/real-engine checks to
   reduce uncertainty cheaply. Use a minimal managed-provider experiment where
   those cannot establish actual identity, network or service behaviour.
   Clearly label fixture evidence and the limits of local substitutes.
3. Select the existing HTTP/DynamoDB path as the first joined reference slice;
   qualify the separate task/PostgreSQL graph as its own slice. Probe uncertain
   seams before expanding implementation. For example, exercise a newly needed
   import from the final-image environment, check the exact API/IAM mapping, or
   test a database connection with the intended TLS and identity boundaries.
4. Record observed results and the resulting design decision. Mark each unknown
   resolved, rejected, or deferred with its blocked dependencies. Lack of live
   authority or an unavailable engine leaves the dependent claim unproven;
   independent source work may continue with that limit reported.
5. Carry accepted findings into the design, reusable reference and proof plan.
   A changed artifact, role, configuration or provider premise invalidates the
   affected result. Do not repeat unchanged experiments whose evidence remains
   applicable merely to satisfy a new commit.

The exit condition is a design with no unresolved architecture-invalidating
assumptions for the next implementation slice, plus an explicit proof plan for
remaining integration claims. It is not a promise to eliminate all runtime
uncertainty or a declaration that the final release is already qualified.

### Breaking a repeated failure loop

<!-- deterministic-check: allow reason="choosing a distinguishing diagnostic experiment requires engineering judgment; controller retry limits remain executable requirements" -->
When a build or deployment fails, record the failed stage, bound inputs,
observations and classification. Collect independent safe diagnostics together.
State the suspected failed assumption and an experiment that distinguishes it
from plausible alternatives before changing code/configuration. Re-run the
smallest check that can validate the proposed fix before another full attempt.

A second expensive attempt that exposes another previously unmodelled
prerequisite triggers a dependency-design review before a third full attempt.
Re-examine adjacent dependencies and update the unknowns register rather than
continuing serial local patches. Exhausting an investigation's declared budget
requires a recorded design/scope decision; it cannot silently renew the budget.
Normal classified transient retries stay inside the controller's bounded policy.
These are engineering review points, not automatic additional approval prompts.

## P1: build and independent validation

Primary surfaces: .github/workflows/, scripts/04.deploy/build-platform-shell-image/,
scripts/04.deploy/smoke-test-platform-shell-image/,
infra/04.deploy/03.product/image/, platform/server/tsconfig*.json, relevant
workspace manifests/test runners, and existing infrastructure verifiers.

1. Define one checked-in toolchain/dependency contract and clean runner setup.
   Install or remove every required external command explicitly. Test with rg
   absent. Missing required tools fail before expensive work, with one useful
   diagnostic. Keep dependencies locked and record resolved base-image digests.
2. Add credential-free PR checks and call the same checks from publication.
   Render the actual CloudFormation template, then run pinned provider-schema
   validation. Validate workflows and policies independently of handwritten
   expected dictionaries. IAM action/resource validation and actual-identity
   authorisation proof remain distinct requirements.
3. Build once for the reviewed target platform. Execute the final image that
   will be published/promoted, without rebuilding a different smoke image.
   Prove required assets, exports, all declared entrypoints, non-root/read-only
   behaviour, startup, signals, and bounded shutdown. Inspect platform/revision
   and verify scan/provenance against the same digest.
4. Run checks in private output/dependency directories. Stop renaming shared
   node_modules and eliminate stale build outputs masking absent emission.
5. Consolidate workspace resolution from package/export/dependency facts.
   First cover the reachable release graph; do not begin a monorepo rewrite.
   A new transitive dependency must not require unrelated handwritten shims.
6. Give each mandatory gate one owner. Preserve appropriate coverage after
   the RAG gate removal; do not reintroduce unrelated corpus work on every edit.
   Run the focused suite while editing and the required integrated suite once
   for the reviewed candidate, rerunning affected checks when inputs change.

<!-- deterministic-check: allow reason="this implementation plan specifies negative fixtures that P1 must implement in executable checks" -->
Accept when missing CA assets, missing transitive aliases/runtime exports,
incorrect platform, undeclared runner tools, invalid CloudFormation properties,
and invalid IAM action fixtures are rejected before public execution.
Do not equate schema or IAM simulation success with real provider behaviour.

## P2: truthful runtime graph and trusted evidence

Primary surfaces on the refreshed baseline: the existing operational-realization
schema/standard/workflow/compiler/fixtures and target-owned adapter/mapping.
Keep provider details outside the generic compiler.

1. Implement v2's complete graph: application and sidecar artifacts, execution
   environment, units, identities, configuration, state, async channels,
   distribution, directed network/dependency edges, health, telemetry, and
   recovery. Genuine empty state/queue collections are valid; fake nodes are not.
2. Bind proof to contract content/version, source SHA, application and sidecar
   digests/platforms, rendered task/configuration hash, target fingerprint,
   actual operational identity, verifier/producer version, trusted run identity,
   attempt, observation time, and expiry. Target-specific evidence may hold
   reviewed hashes/references; generic facts retain their permitted safe shape.
   Validate this binding at the adapter/compiler boundary without adding raw
   endpoints, secrets, task payloads, or SQL to generic documents.
3. Define trusted evidence production and verification. A caller-written YAML
   verdict, fixture, failed CI run, wrong repository/workflow, or modified
   artifact is not proof. Use verified CI evidence/attestation or a narrowly
   controlled collector invoked by the execution controller. Verify observed
   provider facts before normalisation; provenance alone does not prove truth.
4. Require the correct proof kinds for each claim. A live inventory read may
   not replace a transaction/concurrency test or an exact-artifact execution.
5. Model evidence dependencies. Recheck mutable target facts under the target
   lock immediately before mutation; invalidate proof after any relevant
   artifact/configuration/identity/network/schema change. Bound clock skew and
   handle future-dated observations explicitly.
6. Wire the real mutation entrypoint to reject invalid proof before calling a
   mutating provider operation. Retain safe fingerprints and correlation between
   records; tests must show this is enforced beyond the fixture compiler.
7. Before live execution, correct the v2 programme and its owning standard,
   graph, controller and tests to define allowed operational side effects.
   Matching health checks traverse a persistent rate limiter and emit logs and
   metrics. Bound these operational writes while prohibiting business records,
   migrations, queue work and background jobs during G5. No ALB attachment alone
   proves none of those effects. Source-ready requires this policy to agree
   with the tested implementation.

Accept when year-2000, future, unrelated-check, changed-digest/version,
wrong-target/role/producer, fixture, tampered, and replayed evidence fail with
stable codes. Valid evidence must pass for the exact declared candidate only.

## P3: reusable controller, diagnostics, and recovery

Primary surfaces: scripts/04.deploy/, target-profile.yml, target CloudFormation,
release workflows, operational entrypoints, and existing rollback/runbooks.

Replace incident-specific branches with a generic evaluator of a reviewed
per-change manifest. Preserve exact change-scope review as data. Separate
publication, candidate proof, promotion, semantic operation, and recovery.

Required state machine:

    planned -> preflight-passed -> candidate-change-reviewed-and-authorised
      -> candidate-definition-ready -> candidate-started -> candidate-proven
      -> candidate-cleaned -> promotion-change-reviewed-and-authorised
      -> promoting -> deployed
      -> semantic-proof-passed -> steady-state-verified

Every phase also has explicit failed/unknown/cleanup-required outcomes. A lost
response is unknown, not safe to repeat. Persist safe progress and reconcile
the provider before deciding whether an operation already happened.
Authorisation states consume valid scoped approval already recorded; they do
not require a new prompt for each operation within that approved scope.

- Enforce one target mutation owner across local and CI entrypoints. GitHub
  concurrency alone does not coordinate local execution. Use one shared
  controller/lock path with bounded lease renewal, fencing, and reviewed stale
  owner recovery. Inspect the cost/authority of any new lock storage first.
- Claim attempts atomically, use supported idempotency tokens, and pin exact
  task-definition revisions. Avoid check-then-create and latest-family lookup.
- Permit verified same-digest no-op and known-good baseline qualification.
  A failed attempt can need a new reviewed attempt ID without inventing a new
  image. Do not copy the superseded candidate-versus-active contradiction.
- Wait for terminal CloudFormation and ECS deployment/task states. Verify
  desired/running counts, rollout completion, all essential units, application
  readiness and target health. Old healthy tasks must not satisfy a new rollout.
- Prove deployed task definition and running image digest match the approved
  candidate; correlate subsequent application/worker evidence with that release.
- Apply per-call and whole-operation deadlines beneath the workflow timeout.
  Retry classified transient reads only, with bounded backoff. Handle permanent
  denial, missing config, invalid request, and expired auth immediately.
- Emit one shared safe failure envelope: stage, logical operation, allowlisted
  category, retryability, attempt, duration, revision and permitted correlation.
  All bootstrap/migration/relay/worker entrypoints preserve this classification.
- Collect independent safe preflight failures after identity/scope validation.
  Never continue a dependent mutation after failure. Publish partial safe
  evidence on failure/cancellation, not just on success.
- Stop only owned candidate tasks; wait for STOPPED and verify cleanup. Add a
  durable orphan/recovery path for process death and lost create responses.
  A finally block alone is not a cleanup guarantee. Dispose only resources
  positively owned by the approved synthetic proof.
- Normal rollback uses the declared infrastructure ownership path. A reviewed
  emergency ECS restore must include subsequent CloudFormation reconciliation.
  Capture the known-good application/sidecar/configuration release first.

Controller tests must cover duplicate requests, simultaneous operators, lease
expiry, interruption before/after create, lost responses, timeout, delayed logs,
partial success, old healthy deployments, same-digest requests, and orphan
cleanup. No test may mistake requesting cleanup for proving completion.

## P4: provider semantics and schema compatibility

Primary surfaces: persistence adapters/tests, PostgreSQL migrations/bootstrap,
runtime lease identity, and the existing controlled delivery/restore fixtures.

- Retain fast request-construction tests; add real-engine semantic tests for
  transaction rollback, claim/reclaim, stale fencing, concurrent claims,
  conditional conflicts, duplicate delivery, and unused expression values.
  Record which claims still require real managed-provider/IAM proof.
- Use disposable PostgreSQL with TLS and distinct bootstrap/migration/runtime
  identities for the production-relevant boundary. A non-TLS single-identity
  fixture cannot certify those claims. Verify database name, grants, ownership,
  trust bundle, and hostname verification.
- Recompute migration content checksums before database access. Test changed
  SQL with a retained checksum. Define parameter inclusion in migration identity
  and enforce one migration owner/concurrency policy.
- Specify application/schema compatibility through forward and rollback paths.
  G5 does not execute migrations. Prefer compatible expansion and forward repair;
  do not imply application image rollback reverses a database change.
- Keep bootstrap/migration, server, relay, and worker as distinct execution
  graphs. Server startup success cannot qualify those other entrypoints.

The final PostgreSQL route must pass its own proof. An already-proven DynamoDB
route can qualify only that supported route; it cannot close PostgreSQL work.
Record two separate evidence chains: authenticated HTTP-to-DynamoDB delivery,
and task-driven PostgreSQL acceptance-to-delivery. The current relational relay
performs its own acceptance; do not describe that as an HTTP request. A future
HTTP-to-PostgreSQL composition needs explicit implementation ownership, authz,
transaction, network/secret bindings and integration tests before qualification.

## P5: real candidate execution and end-to-end promotion

Begin only after P1-P4 pass for the candidate and relevant live authority exists.
Use the v2 target mapping/controller; do not implement the superseded v1 plan.

1. Inspect current target and known-good release. Diagnose any active drift,
   unhealthy workload, or unresolved previous operation before planning mutation.
   The recorded image-retrieval failure does not by itself identify its cause.
   Distinguish manifest/platform, role access, DNS/network, layer retrieval,
   repository availability, log/secret initialisation, and runtime startup.
2. Review a dormant candidate-boundary change set using the known-good digest.
   It must not unexpectedly change live services, IAM, network, databases,
   queues, routing, DNS, secrets, or alert destinations. Verify baseline
   candidate start, health, controlled stop, and cleanup first.
3. Prepare and review the exact candidate-definition change for the new digest
   before execution; confirm its approved scope, apply it, wait for completion,
   and verify the resulting candidate revision. Preserve v2's G4-before-G5 order
   on every candidate. Then prove the exact digest in the execution boundary. Model execution
   role and task role separately. Verify application/sidecar retrieval, config
   and secret resolution, DNS, egress/endpoint policy, TLS, startup, and health.
   No NAT, endpoint, IAM expansion, or network repair is automatically allowed.
<!-- deterministic-check: allow reason="P2 and P3 must implement these acceptance checks; this plan records their required live-proof sequence before those capabilities exist" -->
4. Verify candidate/promoted equivalence: digests/platform, roles, config/secret
   reference versions, resources, filesystem, network policy, sidecar, health,
   and command. Allow only explicitly listed attachment differences such as
   service/listener membership. Re-prove after a relevant change.
5. Verify the P2/P3 operational-write boundary against the actual candidate.
   Only its declared bounded rate-counter/log/metric effects are allowed;
   business records, migrations, queue work and background jobs remain excluded.
6. Prove collector readiness and a bounded export signal separately from app
   health. Essential plus START ordering does not prove telemetry delivery.
7. Clean up the candidate and retain bound evidence. Recheck mutable facts under
   the lock, review the service-only change set, then promote the same digest.
8. Wait for terminal rollout and verify the running revision/digest, TLS/DNS
   path, public liveness, authenticated readiness, 401/403/authorised success,
   and target health. A CloudFormation success or old 200 response is insufficient.
9. Through separately approved synthetic lifecycles, prove the existing
   authenticated HTTP-to-DynamoDB acceptance/outbox/relay/worker chain and the
   PostgreSQL bootstrap, migration and task-driven acceptance/outbox/relay/worker
   chain. Record which digest/revision executed each leg and the durable terminal
   result. These are two distinct qualified paths, not an HTTP-to-PostgreSQL
   claim. No direct queue injection may stand in for either outbox path. Check
   source and DLQ totals and return workers/tasks to declared steady state.
10. Execute the separately approved private restore/verification/cleanup proof
    if claiming the PostgreSQL recovery milestone. Otherwise mark that milestone
    incomplete. Retain safe statuses/counts/durations and binding fingerprints;
    follow existing restrictions on identifiers, messages, records and SQL.

## P6: recovery and continuous evidence

Prove one harmless candidate failure cannot reach public promotion and still
cleans up. This proves prevention, not live rollback. Separately exercise a
reviewed restore of the known-good release through the normal ownership path,
verify schema compatibility and semantic health, then return to the agreed
release. If live rollback rehearsal is not authorised, label it unproven.

Repair reconciliation lifecycle eligibility: healthy CREATE_COMPLETE and
UPDATE_COMPLETE must be interpreted in context; in-progress, failed, and
rollback states need explicit policy. Test legitimate artifact updates.

Complete the existing separate drift-producer design under its reviewed role,
cost, schedule and alert boundary. Keep the GitHub consumer passive where the
ADR requires it. Distinguish drift, unsupported coverage, stale/missing proof,
and provider/permission failure. Prove producer failure/stale evidence reaches
the declared operator signal. Require fresh pre/post-change evidence and at
least two subsequent scheduled producer/consumer successes without manual
refresh. Two manual dispatches do not prove clock-triggered operation.

GitHub schedule timing, 28-day SLO confidence, billing attribution, HA and
production resilience cannot be guaranteed by the morning deadline. Keep the
corresponding existing readiness blockers visible.

## Acceptance matrix and evidence record

For every row record: source/candidate/target binding, check/producer identity,
command or trusted run reference, start/end UTC, result, safe failure category,
and evidence expiry where applicable. Keep source, staging, recovery and
continuous milestones separate. Missing evidence is unknown, never passed.

| ID | Required proof | Completion rule |
| --- | --- | --- |
| A01 | Fresh baseline, single owner, actual settings and authority | Exact source SHA and verified prerequisites recorded. |
| A02 | Clean runner, declared tools and independent validators | Historical build/schema/action fixtures fail before promotion. |
| A03 | Exact final artifact execution | Broken asset/export/platform/entrypoint fails; valid artifact runs. |
| A04 | Evidence trust and binding | Stale, future, tampered, replayed, fixture and wrong-candidate facts rejected. |
| A05 | Correct proof kinds and actual entrypoint enforcement | Inventory cannot replace semantics; mutation blocked on invalid proof. |
| A06 | Controller concurrency and interruption | One owner; unknown outcomes reconciled; no duplicate effects/orphans. |
| A07 | Provider semantics and migration identity | Real-engine negative/concurrency/TLS/identity/checksum cases pass. |
| A08 | Private candidate equivalence and sidecars | Actual role/network distribution, app health, export and cleanup proven. |
| A09 | Same-digest/no-op and promotion identity | Repeat command is safe; new rollout runs the approved digest/config. |
| A10 | End-to-end semantics by supported route | HTTP/DynamoDB and task/PostgreSQL chains separately reach durable worker completion and steady state; HTTP/PostgreSQL remains unqualified. |
| A11 | Failure diagnostics | Every operational entrypoint classifies injected failures on first run. |
| A12 | Recovery and restore | Approved failure/rollback/restore paths verified with complete cleanup. |
| A13 | Reconciliation lifecycle and ongoing evidence | Healthy updates accepted; two scheduled cycles and failure signal proven. |
| A14 | Worktree/gate maintenance | Root/chat canonical paths agree; mandatory checks cannot silently skip. |
| A15 | Planning before substantive implementation | Reusable template integrated with existing workflows; this programme has a reviewed complete-path instance and bounded source/refactor map; new-adapter, qualified-path and documentation-only scenarios receive appropriate planning depth. |
| A16 | Bounded investigation and failure-loop interruption | Material unknowns have owners, distinguishing experiments, budgets, decisions and blocked dependencies; no unresolved design-invalidating assumption for the implemented slice; repeated discovery of prerequisites triggers a design review before another full attempt. |
| A17 | Reference reuse and adoption | Supported reference/version and qualification limits published; local/CI consumers use the shared path for the qualified scope; superseded paths retired or explicitly time-bounded with an owner; changed assumptions invalidate affected evidence. |

Also fix the audited canonical-worktree identity disagreement and duplicated
gate ownership within their 00.chat/01.harness owners. Protect startup from
both root and existing chat, with default and overridden worktree roots. Avoid
mixing unrelated scheduler/storage/product implementation into this delivery.

## P7: incremental adoption and retirement

Adopt the working method while implementing this programme; a document that
only tells the next agent to plan better does not satisfy A15. Publish the
completed design, experiments and qualified implementation as the first
reference, including the capabilities it supports, constraints, exact source
and evidence references, commands, owner, and conditions requiring requalification.
Use the existing deploy documentation/target owners and reference the source of
truth instead of copying target values into a separate pattern registry.

For each affected build/deploy consumer, record its current entrypoint, intended
shared replacement, compatibility needs, proof, cutover and retirement status.
Prove the shared path, move local and CI consumers onto it, then retire obsolete
implementations through the owning migration workflow. Temporary compatibility
wrappers delegate to the shared implementation and have an owner and removal
condition. Two independent active implementations of the same qualified path
are unfinished consolidation, not additional resilience.

Start with the release graph needed by the first supported Kanbien route, then
the separate PostgreSQL route. Existing unrelated paths remain explicitly
unqualified; migrate them when touched or in named follow-up slices. Extend to
another provider only with its own bindings, constraint investigation and
acceptance evidence. Keep existing application interfaces and adapter locations
unless a demonstrated defect justifies a separately reviewed change.

Place checks where their results inform decisions: planning review before
substantial implementation; focused checks while editing; integrated artifact
checks before publication/promotion; target facts before mutation; semantic
proof after deployment. Reuse applicable results and rerun affected checks when
inputs change. Do not implement this programme by adding the entire suite to
every commit hook or multiplying existing gates.

## Handoff and operating contract

Expose one documented command/workflow interface for validation, preparation,
execution, status/resume, and recovery, backed by existing capabilities where
possible. The implementation chooses names and records exact working commands;
this plan does not present invented commands as existing tools.

Deliver a committed/source-controlled operator guide and safe evidence manifest
through the existing ownership rules. The final report must include changed
files/commits, tested baseline, candidate and deployed bindings, each A01-A17
result, the completed deployment design, unknowns/experiment decisions, reference
and consumer adoption status, failed/recovered attempts, cleanup/steady state,
and exact remaining blockers. Never include secrets or prohibited provider
payloads.

Measure elapsed time from starting work to proven deployment, including planning
and experiments, plus first-attempt release success, failures escaping preflight,
manual interventions, diagnostic-only deployments, phase durations and recovery
time. Track material unknowns resolved before implementation versus discovered
during deployment, and reference reuse versus newly qualified paths. Retain
failed attempts in the denominator, report experimental attempts separately,
and classify external failures. A green release obtained by moving hours of
unreported retries into preflight is not a demonstrated improvement. Compare
subsequent changes with the available audit baseline; do not invent historical
time measurements. One successful evening establishes a qualified path;
sustained reliability needs observations across subsequent changes.

Record delegated work through the existing record-sub-agent-activity command.
Do not claim another agent's checks passed without its returned evidence.

## Ready-to-send implementation instruction

> Implement .agentic/aws/plans/implementation/local-to-proven-deployment-reliability.md.
> Start with P0 against current reviewed remote source and reconcile existing v2
> work. Complete P0a's reusable planning workflow and deployment design, then P0b's
> bounded investigations before substantive dependent implementation. You are the
> coordinating implementation agent. You may make the source, test, and
> documentation changes specified by P0a/P0b/P1-P4/P7 and A14 using the owning
> workflows, and delegate nonoverlapping source work after resolving its blocking
> assumptions and interfaces. Preserve other sessions' files and existing owner
> boundaries. Implement and adopt the shared path; retire superseded paths within
> the qualified scope. Complete the source-ready milestone and prepare the
> concrete integrated staging change, cost, permission, semantic-proof, cleanup
> and rollback bundle.
> Check the current chat for existing git/external authority and use it within
> scope. This instruction alone does not authorise commits, remote promotion,
> publication, GitHub setting changes or AWS mutations. Obtain only missing
> authority for the reviewable bundle before dependent live execution. Once
> authorised, complete P5-P6 without asking again for actions inside that scope.
> Report the A01-A17 evidence matrix, planning/experiment decisions, reference
> adoption and actual remaining state at handoff;
> never convert source-only progress into a live-proof claim.

For an unattended live run, approve the prepared external-action bundle and
renew credentials before leaving the agent. The bundle must enumerate exact
target/roles/change sets, publication/promotion authority, synthetic operations,
cleanup/restore authority, resource and cost limits, attempt/deadline limits,
known-good rollback, detector scope if any, and conditions requiring escalation.
Until that bundle exists, a blanket promise of tomorrow's live completion would
be unsupported.

## Audit traceability and additional gaps

This revision addresses the planning gap raised after the initial audit plan:
explicit complete-path design (P0a), time-bounded discovery before implementation
and repeated-failure review (P0b), proportionate workflow entry conditions and
reuse (P0a/P7), and consolidation/retirement rather than accumulating parallel
tooling (P7). These are acceptance requirements A15-A17, not optional guidance.
The placement table also supersedes the conversational illustrative folder tree.

Historical repairs already present by the planning baseline include the missing
workspace alias (be06e419), DynamoDB member IAM action (7b5c9b78), unused outbox
expression value (ccab0fa3), CloudFormation lifecycle schema (bef454ce), S3 IAM
action names (aa2b6f7a/b0bc9969), RDS certificate packaging (527b77b7), portable
smoke checks (6aeda471), and published platform/revision inspection (e86f10e9).
Preserve those repairs and add cross-boundary regressions; do not redo them.

New planning gaps beyond the initial report are explicitly assigned above:
evidence authenticity (P2), live GitHub enforcement (P0), cross-channel locking
and exact revisions (P3), execution-role artifact distribution (P5), candidate
equivalence/operational writes/sidecars (P5), lost-response cleanup (P3),
same-digest semantics (P3), schema-compatible rollback (P4/P6), and distinguishing
private startup proof from the full bootstrap/migration/delivery graph (P4/P5).
The additional HTTP-to-PostgreSQL composition gap is explicitly excluded from
the two existing-route proof claims rather than hidden inside their acceptance.

The initial audit sampled 96 GitHub runs created 2026-09-24 through
2026-09-27T20:26:14Z: image publication 11 success/4 failure; reconciliation
1 success/14 failure; synthetic and metric coverage 15 successes each; former
RAG checks 35 failures/1 cancellation. This is a workflow outcome sample, not
application availability or engineering time lost. Preserve that distinction.

Provider facts must be checked against current authoritative references during
implementation. Starting references reviewed for the audit:
[CloudFormation provider-schema lint](https://github.com/aws-cloudformation/cfn-lint),
[IAM policy validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html),
[S3 encryption permission](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketEncryption.html),
and [S3 lifecycle permission](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketLifecycleConfiguration.html).

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.local-to-proven-deployment-reliability
version: 3
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
purpose: Refactor the engineering harness and every existing executable and deployment path around independently verified operational completeness, provider-neutral contracts, exact-artifact qualification, and deterministic recoverable execution.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# Engineering and deployment completeness: systemic refactor

Revised: 2026-09-28. Status: implementation plan, not implemented protection.
This revision supersedes the earlier overnight sequence and AWS-reference-only
completion boundary. The user terminated PostgreSQL Stage 6 and replaced the
08:00 deadline with completing and proving the structural fix.

## Confirmed decisions and completion boundary

For Kanbien/staging PostgreSQL Stage 6 only, the [bounded applicability clause](../../../01.harness/standards/operational-realization-gate.md#bounded-postgresql-stage-6-applicability)
is effective only after explicit adoption and approval of its concrete
execution plan. Until then the current requirements remain effective.
This programme's whole-estate adoption and replacement prerequisites do not
apply to the named slice once that route is effective; the programme remains
incomplete and unchanged for other work. The adopted slice uses its bounded
repair/resume and escalation policy for ordinary failures; it does not require
full-programme adoption or a new human approval for every in-scope correction.

The user confirmed all six decisions on 2026-09-28:

| Decision | Required treatment |
| --- | --- |
| Adoption breadth | Cover every existing executable and deployment path before feature work resumes. No untouched legacy-path exemption. |
| Refactor scope | Harness, build/package tooling, CI and internal runtime interfaces may change. Preserve public application contracts unless a change is specifically justified and reviewed. |
| Schedule | Complete and prove the structural fix. The former 08:00 deadline and overnight success dependency are withdrawn. |
| Providers | Qualify all providers already used by the repo. Demonstrate generic portability through a second execution model and adapter conformance tests; do not add a speculative cloud provider. |
| Consolidation | Migrate callers to proven replacements, preserve necessary compatibility during migration, then retire obsolete or duplicate paths. |
| Qualification environments | Plan disposable provider environments with synthetic data. Review their concrete resources, costs and authority before execution. |

The objective is that architecture and code changes arrive at release with a
complete, already-qualified execution design. Release runs a reviewed immutable
plan; it does not discover package contents, secret formats, privileges,
entrypoints or recovery semantics for the first time.

The engineering target is zero avoidable design/configuration defects first
discovered on the intended release target, zero diagnostic-only rebuilds needed
to understand an ordinary failure, and zero unbounded repair/retry loops.
A compiler or review cannot prove arbitrary software free of all defects.
Provider outages, capacity, drift and other external failures remain possible;
the executor must recognise them and reach a defined recoverable state.
Do not promise that the only possible elapsed time is instance creation:
semantic verification, data operations and bounded recovery also take time.
Measure and reduce those phases without removing their proof.

A first reference is an implementation milestone. The programme is complete
only when the entire discovered estate is qualified under the shared method or
has been deliberately retired after equivalent replacement. A missing proof,
unresolved path, temporary independent controller or unqualified provider keeps
the programme incomplete. Feature work resumes only after that closure.

## Starting state: PostgreSQL terminated, not a successful prerequisite

The user-provided final Stage 6 report states that recovery-4 bootstrap failed
before application telemetry; no subsequent migration, relay, worker or restore
ran, the server remained healthy and worker scale was zero. These are reported
facts, not a fresh cloud inspection by this planning revision.

Observed source baseline: `10c9c90f`, including managed-master credential
correction `2775913b`. The former operator's worktree also has six uncommitted
diagnostic/runbook changes. Preserve and review them; neither clean git state
nor a stopped chat establishes current cloud state. This planning worktree is
older and must not become the implementation baseline by accident.

P0 takes a terminal handoff whether the prior attempt failed, was cancelled,
or succeeded: actual source/artifact/operation identities, last observed state,
consumed labels, safe diagnostics, cleanup completed/outstanding, pending cloud
operations and released ownership. Reconcile current target facts read-only.
Do not infer that terminating the agent stopped its remote tasks.

No Stage 6 retry is authorised by this revision. Independent source refactoring
starts without waiting for Stage 6 success. Any later resumption requires the
new per-entrypoint and composed-graph qualification, reconciled state and the
existing explicit AWS execution authority for the concrete operation.

## Why the previous approach was insufficient

| Structural weakness | Required correction |
| --- | --- |
| Healthy server treated as qualification of bootstrap/migration/relay/worker/restore | Independent executable contracts and proofs, followed by proof of their composition. Shared image identity permits reuse only of genuinely shared assertions. |
| Author declares the inventory and then tests that same inventory | Independently extract source, artifact and rendered-infrastructure inventories; reconcile them and reject uncovered or dynamic obligations. |
| Provider fixtures reproduce developer assumptions | Versioned provider-shaped fixtures, real engines and isolated managed-provider qualification, each with explicit limits. |
| More prose and source-pattern checks treated as stronger planning | A complete design, independent counterexample review, executable obligations and tests which deliberately break the claimed protection. |
| Transient console output or current provider status treated as durable history | Trusted, bound, durable phase evidence and a resumable operation journal. |
| Every failure creates a new label/image and another full deployment | Separate artifact/operation/attempt identities; retain failure lineage and reopen the design when a premise fails. |
| Incident logic duplicated across scripts and workflows | One generic operation controller and adapter contract, with provider/target decisions supplied as reviewed data. |
| Only the newest product reference receives the new process | Complete estate inventory, adoption ledger, migration of all supported paths and retirement of superseded callers. |

The existing plan already required separate entrypoints. Its weakness was that
this remained a requirement the agent could claim to satisfy through a partial
reference. This revision makes completeness independently checked and makes
partial adoption an explicit blocker to programme completion.

## One engineering definition of done

Create one reusable standard under `.agentic/01.harness/standards/` (proposed
name `engineering-definition-of-done.md`) and link it from the owning workflows.
The definition applies to architecture, libraries, tools, applications,
adapters and infrastructure through appropriate profiles. This deployment-owned
plan implements and adopts that cross-layer standard; `.agentic/aws/` remains
the repo's existing 04.deploy governance location, not the owner of universal
engineering rules. Keep AGENTS.md a small router.

| State | Evidence required before the state may be claimed |
| --- | --- |
| Design reviewed | Outcome/invariants, complete paths, alternatives, ownership/compatibility, material assumptions, qualification environments, effects and recovery are explicit; independent challenge has no unresolved blocking finding. |
| Code verified | Clean reproducible build, discovered-unit coverage, exact-artifact execution, behavioral and applicable negative/concurrency tests, safe diagnostics and consumer integration pass. |
| Adapter qualified | Supported capability/constraint envelope and provider-shaped inputs are tested against actual semantics; managed-provider claims have isolated provider proof. |
| Release admissible | The exact release graph is covered, proof is trusted and current, target differences are assessed, change/recovery plans are executable, authority and launch prerequisites are satisfied. |
| Deployed and proven | The intended target runs the approved release; each required semantic route and relevant negative/recovery case passes, with durable evidence and declared steady state. |
| Operationally observed | Required scheduled controls, alert delivery and observation windows have actually run. This state cannot be inferred from a one-time deployment. |

Architecture artifacts can finish their own design milestone. Source commits
and integration checkpoints can exist before a feature is operationally done;
otherwise the work required to obtain proof becomes circular. Such checkpoints
remain explicitly incomplete and cannot authorise release or close a capability.
Every capability/change states its required final maturity in advance. A local
tool has local execution obligations; a deployed capability requires its
selected target proof. No author may lower maturity after a failed attempt.

Libraries inherit integration obligations through affected consumers. They do
not require artificial cloud services. Documentation-only changes have an
explicit applicability result and affected-reference checks. Product behavior
changes still need affected behavioral and deployed-path evidence even when
existing provider qualification can be reused.

The feature/platform-consumption decision record supplies product semantics.
Connect the existing root draft to this standard and the runtime graph rather
than making authors fill out another competing questionnaire. Its current
coverage/link checker does not prove actual feature records or their claims;
add instance validation and evidence references as part of adoption.

## Architecture: neutral contracts, execution profiles, provider adapters

Extend the existing Operational Realization programme and compiler. Do not
build a parallel framework or move deployment code into `platform/realization`.
The current schema remains v1 despite later candidate-controller additions;
version the full-graph extension and provide explicit compatibility/migration.

| Boundary | Responsibility |
| --- | --- |
| Generic contract and obligation compiler | Versioned graph, execution profiles, semantic assertions, effect/dependency model, applicability, evidence bindings and completeness. No provider SDK/resource vocabulary. |
| Shared operation controller | Reviewed plan execution, journal, locks/fencing, idempotency, deadlines, observation, classified recovery and evidence lifecycle. |
| Execution-model profiles | Different success/failure semantics for services, finite jobs, event handlers, local tools, infrastructure changes, migration, restore and static artifacts. |
| Provider adapters | Provider schemas/APIs, identity/resource binding, request validation, current-state collection, eventual consistency and provider completion/cleanup checks. |
| Target composition | Reviewed environment/account/region, resource bindings, policy, budgets, configuration and approved differences. |
| Product/runtime code | Business semantics, app-facing contracts and provider-neutral runtime behavior; no infrastructure orchestration. |

Adapters implement the required capabilities for inspect, prepare/plan,
execute, observe, classify failure, reconcile an unknown outcome, and supported
cleanup/compensation. Unsupported capability combinations fail during design or
plan compilation. A provider-neutral name cannot conceal an ECS-only lifecycle.
A service has readiness; a finite job has a semantic terminal result; a function
has an invocation result; a static artifact has publication/integrity/delivery
proof. Not every unit has a health endpoint, database or queue.

A reviewed specification may select among approved targets and operation
profiles. Do not embed one incident, digest or recovery label in each script.
Reject arbitrary unreviewed provider arguments. The adapter accepts a validated,
authority-bound plan and cannot invent permissions, targets or recovery actions.

The graph includes artifacts and assets, executable/administrative units,
sidecars, external services, execution environments, configuration and secrets,
identities, stores/channels, distribution, DNS/network/TLS, health/telemetry,
resource lifecycle and recovery. Edges name phase, expected semantics, effects,
proof obligations and invalidation dependencies. Empty categories are valid
when supported by discovery; fabricated nodes or blanket 'not applicable' are not.

## Workflow and file ownership

Use the current versions of [chat lifecycle](../../../00.chat/workflows/chat-start.md),
[harness change](../../../01.harness/workflows/change-harness.md),
[product/runtime implementation](../../../03.product/workflows/platform-runtime-implementation.md),
[AWS planning](../../workflows/plan-aws-change.md),
[inspection](../../workflows/inspect-aws-state.md) and
[approved execution](../../workflows/execute-approved-aws-change.md).

| Surface | Planned refactor |
| --- | --- |
| `.agentic/01.harness/standards/`, templates and workflows | Own generic definition of done, complete-graph schema, profiles, independent review and evidence rules. Update build-capability and architecture workflows; remove obsolete assumptions that chat startup assigns a permanent task layer/workflow. |
| `.agentic/03.product/` and product rule/check surfaces | Connect architecture/runtime/feature-consumption work to semantic obligations, consumer impact and required maturity. Preserve product/provider boundaries. |
| `.agentic/02.rag-rulebook/`, `.agentic/aws/` and relevant shared/chat workflows | Adopt the same completion contract for existing service/tool/deploy paths; keep each procedure under its actual owner. |
| `scripts/04.deploy/operational-realization-gate/` | Extend existing compiler, discovery, completeness checks and safe evidence validation. Keep generic logic free of provider imports. |
| `scripts/04.deploy/` | Extract shared execution/journal/diagnostic mechanisms from existing controllers; provider-specific adapters remain separate. Retire incident-specific execution logic after migration. |
| Workspace manifests, TypeScript configs, test runners and image recipes | One generated dependency/export/build closure; private outputs; final-artifact tests; declared toolchain. |
| `platform/adapters/`, runtime and deployment composition entrypoints | Contract/semantic tests, inspectable configuration and dependency boundaries, per-entrypoint diagnostics; bounded internal refactoring where needed. |
| `infra/04.deploy/` and target manifests | Rendered-infrastructure inventory, reviewed bindings, isolated qualification targets, profile-specific proof/recovery definitions. |
| `.github/workflows/` and supported local release commands | Invoke the same compiler/controller and evidence checks. Inspect actual required checks, protected environments and credential boundaries, not just YAML. |
| Existing convergence programme and operator docs | One adoption ledger and implementation order; working commands, supported profiles, proof limits, migration and retirement records. |

Do not rename directories or replace CloudFormation simply to look generic.
Select structural changes through the complete design and compatibility review.
A move/retirement follows the existing artifact-path migration workflow and
updates callers, indexes and retrieval references in the same slice.

## P0: preserve state and inventory the entire estate

One coordinator owns integration and release selection. Refresh from reviewed
remote source in an assigned worktree; record exact SHAs and differences.
Preserve the original root/product drafts and the terminated operator's changes.
A dirty worktree is an ownership handoff problem, not permission to discard work.

Inventory all repository-owned executable/build/publication/deployment paths,
not just Kanbien platform shell: package commands, executable exports, process
entrypoints, scripts in every layer, containers/handlers, infrastructure jobs,
scheduled workflows, RAG/rulebook service, website/legacy paths still supported,
provisioning helpers, reconciliation, synthetic monitoring, credential setup,
bootstrap/migration/delivery/restore and recovery commands. Third-party tools
are dependencies with pinned compatibility, not source to refactor arbitrarily.

For each item record owner, callers, execution profile, effects, provider/target,
artifact, required maturity, existing evidence, gaps, replacement and disposition.
Separate active, dormant-but-supported, test-only, historical and retired items.
Test-only classification requires supporting call-graph/build facts. Dormant
paths are not exempt. Retirement requires proving no supported caller remains
and migrating its functionality where needed; it is not a way to hide a gap.

Inspect actual GitHub enforcement, role assumption, build/runner availability,
tool versions and existing target state before estimating execution. AWS
identity was verified during planning; local Docker readiness timed out. Neither
credential lifetime nor a working unattended builder has been established.
Resolve or prove the existing governed CI build path before depending on it.

Deliver the inventory/adoption ledger and a terminal Stage 6 handoff. P0 makes
no new bootstrap attempt. Fresh read-only inspection is required before using
reported cloud state to prepare any later change.

## P0a: complete design and independent challenge

Before substantial dependent implementation, complete a reusable design record
for this refactor and for each materially different capability. Reference the
same machine-readable graph; do not maintain separate hand-written inventories.

Required content:

- User-visible outcome, invariants, final maturity and observable acceptance.
- Public contracts, ownership, compatibility and alternatives considered.
- Complete success and failure paths from build through execution and recovery,
  including administrative tasks, generated inputs and operational dependencies.
- Qualified reference/version, exact differences and supported capability limits.
- Material assumptions with source/date, falsifiable question, dependent work,
  smallest distinguishing experiment, owner and time/cost/attempt budget.
- Source/refactor map, shared-file ownership, migration and retirement sequence.
- Per-claim proof type, adequate environment, producer, expected result and
  evidence invalidation rule.
- Effects, idempotency, concurrency, deadlines, diagnostics, recovery, cleanup,
  permissions and cost posture for the complete operation graph.

Use a separate reviewer, drawing on existing architecture/backend/SRE/security
review roles, for material architecture, identity, state or lifecycle changes.
The reviewer starts from requirements and independently traces success, partial
completion/process loss, duplicate/concurrent execution, recovery and a changed
or unsupported dependency. Record concrete counterexamples and their disposition,
not a bare 'approved'. Bind review to the design revision; material changes
reopen affected findings. This is engineering review, not another user approval
prompt for routine implementation decisions.

The coordinator resolves blocking findings before dependent implementation.
Review and structural completeness are complementary: a valid manifest does
not prove architectural correctness, and a confident reviewer cannot waive
missing executable evidence.

## P0b: bounded qualification of assumptions and failure-loop control

Use static checks, provider documentation and disposable real-engine probes
first. Use isolated managed-provider experiments when local substitutes cannot
establish the claim. Minimal investigation code is allowed before the full
implementation; retain useful probes as regression tests. Experiments themselves
have a reviewed scope, effect boundary, budgets and adequate execution authority.

A design-invalidating unknown blocks its dependent implementation/release, not
unrelated work. Record resolution, rejected approach or explicit blocked scope.
Prototype evidence does not replace later proof for the exact release artifact.

The first release-target failure exposing an unmodelled prerequisite, invalid
provider assumption or missing diagnostic/evidence path moves the affected
capability to `design-reopened`. Stop further dependent expensive attempts.
Preserve diagnostics, reconcile/clean up through the approved recovery path,
check adjacent assumptions, run a distinguishing experiment and obtain an
independent review of the corrected design before resuming.

Persist lineage by capability, design and failed hypothesis across commits,
images, operation labels and chats. Repeated same-cause failures and exhausted
time/cost/attempt budgets also open the circuit. Renaming an attempt, changing
an image or receiving permission cannot reset the lineage. Only classified
external/transient failures use the predeclared bounded retry policy; an unknown
failure is not automatically transient. Investigation has its own finite budget
and must produce a decision rather than becoming a hidden retry loop.

## P1: one build graph and exact-artifact execution

Replace duplicated package aliases/shims with one build resolution contract
from manifests, exports, dependency closure and compiler output. Start with a
small implementation slice, then cover every retained path before programme
closure. A new transitive dependency must not require edits to unrelated runners.

Declare and verify toolchain, lockfiles, validator versions, target platforms
and resolved base artifacts. Use clean private output/dependency directories;
remove stale-output masking and checks that rename shared `node_modules`.
Subprocesses have bounded execution and explicit environments. Interruption or
parallel checks must leave the workspace installation intact.

Build once per release artifact. Run the final image/package after dependency
pruning, with its actual entrypoint/command, assets, user, working directory,
filesystem/resources and applicable shutdown constraints. Publish/promote that
same digest. A host checkout test, a different smoke image, successful import
or an expected missing-CA failure does not qualify executable behavior.

Generate the execution test matrix from P2's reconciled inventory. Add explicit
semantic scenarios, positive completion and meaningful negative cases for each
unit; generation identifies required coverage but cannot invent the assertion.
Validate rendered infrastructure, provider API shapes, workflows and IAM action/
resource contracts with independent validators. Static validation and permission
simulation do not establish actual managed-provider authorization.

## P2: independently complete graph, obligations and trusted evidence

### Discovery and coverage

Derive inventories from independent inputs:

1. Parsed source/package commands: entrypoints, config access, provider-client
   construction, subprocesses, filesystem/network use and executable exports.
2. Built artifacts: actual command/handler metadata, packaged executables,
   dependency closure, runtime assets, platform and sidecars.
3. Rendered infrastructure/workflows: task commands, jobs/triggers, identities,
   injected inputs, volumes, connections, dependencies and recovery operations.
4. Observed execution: actual invocation, artifact, identity, exercised
   dependencies, effects and terminal result.

Reconcile them with the reviewed graph and proof matrix. An undeclared command,
sidecar, asset, secret binding, dependency or supported caller fails completeness.
Source analysis is not omniscient: dynamic launch/configuration requires an
inspectable interface or explicit reviewable mapping and proof. An unresolved
dynamic edge is an obligation, not an automatic pass. Runtime traces supplement
coverage; they cannot prove paths which were never executed.

Derive required proof/fault obligations from unit and dependency profiles.
Require specific semantics, including absence/denial, timeout, partial effects,
duplicates, concurrency, interruption, stale evidence and failed cleanup where
applicable. Applicability rules and any exclusion have independent review.
Mutation-test the coverage checker by introducing an undeclared executable,
missing secret binding, untested sidecar, hidden launch or false nondeployed tag.
Do not let the same hand-maintained expected dictionary define both the system
and the test oracle.

### Evidence

Use a claim-to-evidence compatibility matrix, not a single ascending proof
number: a live inventory read cannot replace a local transaction/concurrency
test, and live server health cannot replace bootstrap proof. Keep the actual
assertion, observation and adequacy of its environment explicit.

Bind receipts to executable/profile, source/build closure, artifact and sidecar
digests, command/config/schema versions, target fingerprint, acting identity,
contract, verifier/producer version, trusted run, operation/attempt, observation
time and expiry. Verify evidence production, integrity and actual observations.
A caller-authored YAML pass or hash is not an attestation. Reject fixtures as
live evidence, untrusted producers, tampering, replay, stale/future time,
wrong targets and mismatched inputs with stable codes.

Persist safe phase observations durably as they occur, including readiness
before stopping a service and terminal job outcome before cleanup. Record
cleanup separately. Consumers use the journal/receipts, not reconstructed
historical health from a stopped task or the survival of terminal stdout.
Evidence-store unavailability has a defined fail-closed/recovery behavior.

Evidence dependency graphs determine invalidation. A role, command, secret
shape/version, image, network, schema or provider-premise change invalidates
its affected claims. Reuse unaffected evidence with a checked equivalence
explanation; a docs-only source SHA change does not require every cloud test.
Current release provenance still points to the actual tested build inputs.

## P3: deterministic controller and recoverable operations

An operation has explicit states, for example:

    planned -> validated -> prepared -> authorised -> executing -> observing
      -> succeeded -> cleanup-verified -> closed

Failure branches include `failed`, `unknown`, `cleanup-required`,
`compensating`, `design-reopened` and `closed-with-failure`. Model resource
state separately from controller state. A dead process or lost response does
not establish whether its external operation happened. Authorisation consumes
existing scoped authority; it does not require a prompt at every phase.

The controller must:

- Acquire a shared local/CI target/resource lock with lease, fencing and
  controlled stale-owner recovery; atomically claim each operation.
- Validate current facts and an immutable approved request before mutation.
  Store intent before effects and observations/results afterward. Reconcile
  uncertain provider outcomes before repeating anything.
- Separate artifact, logical operation, attempt, provider idempotency token and
  recovery identities. Permit supported same-artifact/no-op and reviewed new
  attempts without creating an artificial image solely to obtain a fresh label.
- Use per-call, per-phase and whole-operation deadlines. Retry only declared
  classes within cumulative budgets; authentication, validation and permanent
  denial fail promptly with an actionable category.
- Use profile-specific completion predicates. Finite jobs need semantic outcome;
  services need the actual new revision's readiness; provider acceptance alone
  is not completion. Old healthy instances cannot satisfy a new rollout.
- Emit shared safe failure categories covering loader/startup/configuration,
  artifact distribution, injected inputs, identity, TLS/network, provider request,
  semantic failure, timeout, interruption and evidence/cleanup failure. Capture
  pre-application failures through the execution adapter, not application logs.
- Preserve adapter failure codes. Unknown categories stop for investigation;
  routine diagnosis must not require publishing a new diagnostic image.
- Recover after process loss, lost create response, lease expiry and partial
  success. Clean up only positively owned proof resources, observe completion
  and report leftovers. A `finally` block is not the recovery design.
- Execute only declared compensation/forward repair/restore. An application
  rollback cannot imply reversal of database changes. Preserve known-good
  release and application/schema compatibility through the ownership/IaC path.

Replace the existing Boolean 'mutates live target' with explicit effect classes:
read-only inspection, artifact publication, control-plane resource changes,
operational telemetry/rate counters, synthetic data effects and business or
irreversible effects. Each profile declares allowed/prohibited effects and
bounds. Creating a task is a control-plane mutation; health telemetry is an
operational effect. Neither is automatically a business operation.

Gate real execution, not only an optional checker. Supported local commands,
CI and recovery paths must invoke the same enforcement. Inspect deployed
identity and GitHub controls; a privileged alternative shell path can bypass
repo prose. Plan least-privilege execution credentials and restrict bypasses
through separately reviewed settings/permissions. An emergency exception is
recorded as waived/unproven and never becomes evidence of qualification.

## P4: per-entrypoint semantics and provider-shaped qualification

| Profile | Required proof, adapted to the actual capability |
| --- | --- |
| Local tool/build/publish | Actual invocation, dependency availability, private outputs, deterministic result, interruption/failure behavior, safe file/git/publication effects and usable diagnostics. |
| Long-running service | Exact artifact/config shape, dependency access, readiness, authentication/authorization, declared effects, telemetry and bounded shutdown. |
| Job/worker/event handler | Actual command/handler processes representative synthetic input; durable effect, duplicate/retry/fencing behavior, timeout, acknowledgement and terminal cleanup. |
| Bootstrap/migration | Actual entrypoint with distinct intended identities and provider-shaped inputs; TLS, privileges/grants/ownership, real schema transition, checksum/concurrency rules and compatible application behavior on disposable state. |
| Restore/maintenance | Actual operation on isolated state; specified data/schema invariants, recovery timing, restricted identity, retention and verified cleanup. |
| Infrastructure operation | Independent schema/change validation plus create/update/no-op, partial failure, interruption, unknown outcome, rollback/forward repair and ownership reconciliation. |
| Static artifact/external integration | Published integrity and route/access/configuration proof or actual external request/event semantics, with appropriate authentication, expiry, denial and recovery. No invented service-health requirement. |

For PostgreSQL this explicitly includes bootstrap, migration, acceptance/relay,
worker and restore independently. A no-op/preflight mode proves only what it
executes; it cannot substitute for the real task's SQL, privileges or durable
effects. Execute the actual command against disposable state before admitting
its operation on the intended target.

Provider-shaped fixtures model credential payload separately from endpoint/
configuration payload, and deployment/retrieval/bootstrap/migration/runtime
identities separately. Use realistic privilege restrictions, generated outputs,
TLS chains/hostname checks and managed-service limits. Version their provenance,
authoritative references and deviations. Superuser-only PostgreSQL or permissive
recording clients cannot qualify managed identities or actual API semantics.

Use real-engine tests for transaction rollback, outbox claim/reclaim, conditional
conflicts, unused expression values, stale fencing, concurrent claims and
idempotent delivery. Recompute migration checksums from actual content before
DB access; test changed SQL retaining an old checksum and concurrent runners.
Test forward compatibility and recovery separately from deployment success.

Three evidence environments are deliberately distinct:

| Environment | What it establishes |
| --- | --- |
| Clean local/CI and disposable real engines | Build/inventory completeness, exact-artifact behavior, fixtures, engine semantics and injected faults within stated fidelity limits. |
| Isolated real-provider qualification | Actual managed identity/secret behavior, artifact retrieval, network/TLS/logging, API restrictions, effects and lifecycle using synthetic resources. |
| Intended release target | Current target equivalence, approved change, actual running binding, composed semantic acceptance, recovery/cleanup and selected operating controls. |

New provider-dependent behavior is qualified during implementation, before
release admission. This may require creating isolated infrastructure: plan,
review and authorise that preparation as its own operation with appropriate
preconditions. Do not create a circular requirement to prove a resource before
its first creation. Local/source proof admits the bounded qualification setup;
that setup's observed result supplies provider proof for later target release.

Irreversible/stateful work is rehearsed on disposable clones or synthetic state,
with declared differences. Use a separately approved one-way boundary and
backup/forward-repair plan on the intended target. If faithful rehearsal is
impossible, the unproven assertion remains explicit and cannot receive the
programme's qualified guarantee. No proof operation implicitly uses real data.

## P5: composed qualification and release admission

First qualify one complete service-plus-job reference and a distinct execution
model using the same generic controller. Include bootstrap/migration/restore
profiles; do not let a server demonstration close them. A non-AWS conformance
adapter may test generic boundaries without claiming a new cloud is live-proven.
Then apply the method to every retained provider/path in P0's ledger.

The release graph defines ordering per capability, rather than universally
promoting a server before a database operation. Its reviewed sequence includes
foundation preparation, config/identity distribution, compatible bootstrap or
migration, executable qualification, rollout, semantic acceptance and recovery
as applicable. Every dependency must reach its required state before its consumer.

Before admission, reconcile the final artifact/graph/obligation sets, independent
design review, provider qualification, change classification, target facts,
authority, resources/cost, remaining deadlines and recovery. An unresolved
coverage or design obligation prevents release.

Compare the qualified and intended environments explicitly: artifact/command,
platform, roles/permission boundaries, secret/configuration shape and versions,
network/TLS, resources/filesystem, sidecars, health, data/schema and telemetry.
Only named justified differences may reuse proof. Material differences require
new affected qualification. Validate mutable facts under the execution lock.

Promote the same tested artifacts without rebuilding or silently changing
configuration. Observe the actual new revision and exercise the composed route,
including meaningful denial/failure behavior and durable terminal effects.
Prove telemetry export/alert delivery independently from application health.
Record readiness and cleanup durably. A rollout may affect a live service;
do not claim every failure leaves it untouched.

For the existing references, retain two separate chains:

- Authenticated HTTP -> DynamoDB transaction/outbox -> relay -> queue -> worker
  -> durable completion and declared steady state.
- PostgreSQL bootstrap -> migration -> task-driven acceptance/outbox -> relay
  -> queue -> worker -> durable completion, plus separate isolated restore.

The present server does not implement HTTP-to-PostgreSQL acceptance. Do not
invent that path to claim coverage. A new public composition is a separately
justified capability change. Direct queue injection cannot substitute for the
outbox route under test.

## P6: recovery, drift and ongoing qualification

Demonstrate prevention of bad candidate promotion, recovery after partial
rollout and stateful restore as distinct claims. Exercise controller restart,
lost replies, stale leases, wrong image/configuration, failed migration,
dependency outage, delayed/missing telemetry and failed cleanup in adequate
isolated environments. Perform only approved bounded target rehearsals.

Repair reconciliation lifecycle handling: healthy create/update states,
in-progress operations, rollback and failed states need explicit policies.
Normal rollback follows IaC ownership; emergency out-of-band recovery requires
subsequent ownership reconciliation. Observe terminal resource and data state.

Qualify the drift producer, consumer and failure alert using their reviewed
identities and costs. Require two subsequent scheduled cycles where that is the
selected control requirement. Schedule intervals cannot be shortened solely to
manufacture an observation claim. Long SLO/availability windows remain measured
operational milestones, not implied by successful provisioning.

Version provider/platform compatibility envelopes and requalification triggers.
Provider/schema/toolchain changes, drift or expired evidence require affected
reassessment before another release. Capability support is specific and tested;
provider-agnostic architecture does not mean every provider is interchangeable.

## P7: full-estate adoption, retirement and feature-work restart

Use the existing platform-foundation convergence programme as the workstream
adoption owner, with this method as its delivery contract. Reconcile stale
programme statuses and remove server-proof substitution, fixed incident labels,
new-image-for-every-failure rules and inconsistent preflight-effect definitions.

Known workstream inputs include the root feature-consumption draft, data
governance/storage foundation, scheduler/time, tenant execution authority,
product runtime, RAG/rulebook and all other paths discovered by P0. Preserve
source ownership. Resolve shared manifests/lockfiles, Core/contracts exports,
worker behavior and target/profile/workflow changes through one integrator.

Storage still requires its selected metadata seam, S3 adapter and target proof.
Dynamic scheduling requires a durable schedule repository; a working PostgreSQL
instance does not provide that implementation. Resolve fixed-trigger versus
dynamic proof scope before marking scheduler complete. Tenant authority needs
an authoritative target binding, not only injected fixtures. Qualify actual
existing capability scope and finish necessary integration; do not quietly
expand into unrelated future product features or use a fixture as live proof.

For every retained consumer, record old entrypoint, shared replacement,
compatibility contract, proof, cutover and retirement. Temporary wrappers must
delegate to one implementation and have a removal condition. Retire obsolete
logic and guides after migration, through the owning migration workflow.
Supported dormant paths receive qualification too. Preserve worktree history;
retiring code paths does not authorise deleting branches or user files.

Feature work restarts only when the ledger has no unresolved retained path,
all required acceptance results pass, the shared workflow is adopted by every
supported caller, and the independent closing review confirms the evidence.
A user-approved exception remains an explicit incomplete/waived scope and
cannot silently satisfy this agreed completion boundary.

## Implementation sequence and reviewable milestones

| Milestone | Deliverable and exit condition |
| --- | --- |
| M0 / P0 | Terminal handoff and complete estate/provider/command inventory; preserved source ownership and verified execution prerequisites. |
| M1 / P0a-P0b | Generic definition of done, programme design, independent challenge, resolved critical assumptions, versioned profile/adapter/journal interfaces and approved investigation scope. |
| M2 / P1-P2 | Generated build closure and reconciled executable inventory; exact-artifact matrix, proof-obligation compiler and trusted receipt verification; deliberately omitted units fail. |
| M3 / P3-P4 | Shared controller/journal, safe diagnostics, interruption/recovery tests and per-entrypoint real-engine/fixture semantics pass. |
| M4 / P5-P6 first reference | Isolated provider qualification and approved target proof for complete service/job and relational/restore graphs; no claim of estate-wide completion yet. |
| M5 / P7 | Every existing retained path/provider adopted and qualified; duplicates retired, operating controls proven and final independent acceptance complete. |

Build/inventory, controller and semantic-test work can run in parallel after
M1 settles interfaces and blocking assumptions. Assign one editor to each
shared schema, manifest, lockfile, target profile and workflow. Review tested
commits with their evidence; independently passing branches do not prove their
integration. One coordinator owns all target mutations and release selection.

Use small verified source slices and checkpoints. Final release candidates are
frozen during proof. Any change invalidates affected results and returns to the
appropriate earlier phase. This sequencing is incremental implementation with
a full-estate completion boundary, not permission to leave the rest unqualified.

## Acceptance matrix

A01-A17 retain their audit identifiers with strengthened scope. A18-A25 close
the systemic gaps exposed by the terminated Stage 6 and independent review.
Every row needs an executable check/evidence producer, an adequate environment,
required failure cases, an owner and actual evidence references at closure.
A Markdown checkbox or another agent's assertion is insufficient.

| ID | Acceptance | Required demonstration |
| --- | --- | --- |
| A01 | Baseline, ownership and prerequisites | Current source/target/settings/authority and terminal handoff are recorded; no overlapping operator or assumed credential/runner readiness. |
| A02 | Reproducible build and independent validation | Clean declared toolchain; broken schema/action/tool fixtures fail before target rollout. |
| A03 | Every exact-artifact invocation | All discovered units run their real commands with required assets; broken entrypoint/export/platform/asset fails. |
| A04 | Trusted durable evidence | Stale/future/tampered/replayed/fixture/wrong-input evidence fails; valid receipts survive controller loss. |
| A05 | Proof adequacy and real enforcement | Wrong proof kinds and missing coverage block actual supported execution paths, including recovery. |
| A06 | Concurrency and unknown outcomes | Concurrent owners, lease expiry, process death and lost replies produce no duplicate effects or unexplained orphans. |
| A07 | Provider and migration semantics | Real-engine/TLS/privilege/concurrency/checksum cases pass; unsupported managed semantics fail. |
| A08 | Environment equivalence and sidecars | Each relevant unit's identity/network/config/distribution/telemetry matches its qualified envelope; material differences invalidate evidence. |
| A09 | Artifact versus attempt identity | Same-artifact no-op/recovery behaves correctly; new attempts do not require artificial images or erase history. |
| A10 | Composed semantic routes | Actual supported HTTP/DynamoDB and task/PostgreSQL chains, plus every retained route in the estate, reach durable completion. |
| A11 | First-failure diagnostics | Inject pre-application and application faults for each profile; safe actionable classification appears without a diagnostic rebuild. |
| A12 | Recovery and cleanup | Partial effects, restore/forward repair, cancellation and cleanup reach verified states; requested cleanup alone cannot pass. |
| A13 | Drift and ongoing evidence | Healthy updates accepted, producer/consumer/failure alert demonstrated and required subsequent cycles observed. |
| A14 | Harness/worktree consistency | Canonical root/chat identity, current prompt routing, single gate ownership and mandatory-check execution are verified. |
| A15 | Planning and independent challenge | Material design receives concrete counterexample review; new-provider, changed-path and documentation-only cases receive appropriate obligations. |
| A16 | Failure-loop circuit | First unexpected release design prerequisite and repeated same-cause/budget exhaustion block dependent attempts across new labels/images/chats until reviewed resolution. |
| A17 | Complete adoption and retirement | Every supported caller uses the shared path; replacement and removal evidence exists; no unresolved retained legacy path. |
| A18 | Independent inventory completeness | Introduce unlisted executable, sidecar, dependency, secret binding and dynamic launch; independent discovery/coverage rejects each omission. |
| A19 | Provider-shaped per-entrypoint proof | Credentials-only managed-secret fixtures, distinct privileges and real task commands qualify separately; server health cannot pass another task. |
| A20 | Generic service/provider boundaries | Structurally different execution models pass common conformance; unsupported capabilities fail; every existing provider has its own actual qualification. |
| A21 | Changed-dependency invalidation | Change command, identity, network, schema, asset or configuration; affected proof becomes invalid while unrelated valid evidence can be reused. |
| A22 | Qualification-before-release | An isolated real-provider rehearsal catches managed-service discrepancies; intended target never serves as the first integration environment. |
| A23 | Architecture/code definition of done | Real feature records and affected consumers are checked; false adoption, missing records and unjustified not-applicable claims cannot close a capability. |
| A24 | Enforcement cannot self-certify | Deliberately weakened checks, fabricated receipts and alternate supported command paths are rejected; actual CI/identity controls are inspected. |
| A25 | Whole-programme closure and repeatability | Complete estate ledger, clean-checkout operator execution and at least two representative subsequent changes use the method without design/configuration defects first discovered at target release. |

For A25, use meaningful behavior/configuration changes within supported scope,
not empty redeployments. Count every failed attempt. If an avoidable defect
escapes, diagnose, strengthen qualification and repeat the affected acceptance;
retain the original failure in performance evidence. Two successes demonstrate
repeatability, not a lifetime guarantee.

## Authority, cost and unattended execution

This revision authorises planning work through the user's request. The user
approved the intended refactor scope and qualification-environment design;
that is not an approval of unspecified cloud resources, costs or data actions.
Preserve and reuse authority already granted in the execution conversation.
Do not ask again for routine actions within a concrete approved scope.

Before dependent external work, prepare a reviewable bundle: exact target,
provider operations/resources/roles, change sets, publication/promotion scope,
synthetic inputs, known-good/forward-repair plan, owned cleanup, incremental
proof spend, recurring cost ceiling, concurrency/duration/attempt limits and
escalation conditions. Request only missing authority after the bundle exists.
Earlier USD25/month or EUR50/month references are not this programme's budget.

Source implementation, git publication, image publication, repository settings,
cloud mutation and destructive/data operations remain distinct action scopes.
The earlier git approval covered plan publication; do not infer approval of
arbitrary future runtime commits or production changes from this document.
The planned implementation directive below is not an instruction to start it
merely because an agent reads this file.

Unattended launch needs a functioning runner, recorded continuing execution,
available credentials for the duration and no undiscovered mandatory human
approval. Do not disable protected checks. Missing authority blocks dependent
mutations while independent source work and bundle preparation can continue.
No background implementation or deployment is started by saving this plan.

## Handoff, measurement and implementation directive

Provide working supported interfaces for inventory/validate, prepare, execute,
status/resume and recovery through existing command ownership. Choose and
record actual command names during implementation; this plan does not invent
commands and describe them as available.

The final report contains the complete estate/adoption ledger, independent
design and closing reviews, changed commits on origin, exact artifact/target
bindings, A01-A25 results, provider/environment limits, failed attempts,
recovery/cleanup state, retired paths and reproducible operator instructions.
Retain only permitted safe evidence; never publish secrets, raw provider
payloads, SQL, records, signed URLs or sensitive object/message details.

Measure total request-to-proven-delivery time, including design and experiments;
first-attempt qualified release success; defects escaping each environment;
manual interventions; diagnostic-only builds; failure-loop interruptions;
phase durations; cleanup/recovery time; evidence reuse and full-estate coverage.
Classify external failures separately without deleting them from attempt counts.
Do not hide repeated failures inside 'preflight' or claim historical timings
which were not measured. Control token/compute cost through bounded reviews,
small relevant reads and reusable evidence, not lower acceptance standards.

Ready-to-use directive for a separately launched implementation session:

> Implement this programme from fresh reviewed remote source, preserving all
> other work. Begin with the terminated Stage 6 handoff and full-estate inventory.
> Adopt the generic definition of done and complete independently challenged
> design before dependent refactoring. Resolve critical assumptions with bounded
> experiments. Implement M2-M3, then prepare concrete isolated-provider and
> intended-target execution bundles. Use existing scoped git/external authority
> and obtain only missing authority for prepared bundles. Do not restart Stage 6
> through its superseded process. Qualify every executable and composed route,
> migrate every retained path, retire obsolete paths only after their replacements
> are proven and callers migrated, and demonstrate A01-A25.
> Delegate disjoint source/review work after interfaces are settled; one
> coordinator owns integration and cloud execution. Report actual partial states
> until the full agreed completion boundary is met. Feature work remains paused
> until programme closure; neither a deadline nor an approval converts missing
> evidence into a pass.

## Audit traceability and review limits

The initial audit examined worktree `8052929c` and later source; the previous
published plan was `ff248dfe`, with publication bookkeeping through `a672bd01`.
This revision includes source review at `10c9c90f` plus the terminated operator's
six dirty files. Implementation must reconcile newer source and cloud state.

Preserve existing repairs, including workspace alias `be06e419`, DynamoDB IAM
`7b5c9b78`, outbox expressions `ccab0fa3`, CloudFormation lifecycle `bef454ce`,
S3 IAM `aa2b6f7a`/`b0bc9969`, RDS certificate packaging `527b77b7`, portable
smoke checks `6aeda471`, artifact platform/revision `e86f10e9` and managed-master
credential shape `2775913b`. Convert their failure classes into behavioral
regressions. Source repair is not proof of its deployed behavior.

A read-only local simulation reproduced candidate-controller success followed
by PostgreSQL-gate rejection when stopped metadata lacked the earlier healthy
observation. It proves the controller/consumer mismatch for that scenario,
not the actual historical task outcome. No AWS mutation was performed by that
review. The user's final recovery-4 report remains attributed evidence pending
P0's reconciliation.

Independent build, deployment and harness reviews informed this revision. They
identified incomplete executable discovery, inadequate fixture fidelity,
self-certifying review, stale Stage 6 sequencing, service-specific lifecycle
assumptions and missing full-estate adoption. Their findings are recorded in
the session log; they are planning reviews, not implementation acceptance.

The earlier sample of 96 GitHub runs reported 11 successful/4 failed image
publications, 1 successful/14 failed reconciliations, 15 successful synthetics,
15 successful metric-coverage runs and 35 failed/1 cancelled former RAG checks.
That is a workflow sample, not application availability or engineering time.

Provider constraints require current authoritative references and a review date
at implementation. Existing starting references include
[CloudFormation validation](https://github.com/aws-cloudformation/cfn-lint),
[IAM policy validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html),
[ECS health semantics](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_HealthCheck.html)
and [ECS task-list filters](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ListTasks.html).
Do not turn an AWS-specific observation into a generic lifecycle rule.

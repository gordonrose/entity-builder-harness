<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.consolidate-core-platform-deployment-routes
version: 1
status: draft
created_on: "2026-11-14"
updated_on: "2026-11-15"
layer: 04.deploy
domain: deployment.consolidation
disciplines: [architecture, sre, security]
kind: implementation-plan
purpose: Consolidate the two accepted core-platform deployment routes by reusing common machinery while preserving workload boundaries and evidence.
portability: {class: source-only, targets: []}
used_by:
- id: deploy.inventory.core-platform-deployment-routes
  path: docs/04.deploy/plans/core-platform-deployment-route-inventory.md
-->
# Consolidate core platform deployment routes

## Outcome and current authority

Both `kanbien-core-platform/core-server-persistence` and `entity-smoke` should
use common release machinery with explicit workload inputs, not parallel
implementations of the same release operations. Their resources, database
identities, migrations, application behaviour and accepted histories remain
distinct.

The user authorised this plan and a recorded source inventory on 2026-11-14.
The subsequent user delegation authorises repository implementation and local
verification of these slices. The implementation agent owns source changes;
the parent reviews each bounded slice. On 2026-11-15 the user additionally
approved local checkpoints for the checked migration plan and verified
consolidation/follow-on changes. No push, publication or AWS execution is
authorised by this approval. This plan does not replace the existing
deployment workflows or create new approval gates.

The user's subsequent authorisations add two ordered workstreams to this same
plan: (1) complete deployment consolidation, (2) complete the evidence-reporting
safeguard, then (3) declaration-derived build/packaging with ongoing governance
and enforcement. Neither follow-on makes unfinished consolidation complete or
expands the existing no-push, no-publication and no-AWS authority boundary.

## Current programme: remaining pieces and all 34 lessons

The user has authorised repository remediation in the order below. Full image,
publication and AWS proof remain paused until these corrections are integrated.
Earlier implementation entries are history, not evidence that the complete
delivery lifecycle is reusable or meets its ten-minute budget. The retrospective
lesson guide retains its separate user-led discussion progress.

| Batch | Connected pieces and surviving owners | Completion evidence |
| --- | --- | --- |
| A — Declarations and coordination | Existing target/scope/workload declarations, declaration coverage, build/package and deployment controllers. Replace copied selection and sequencing with shared owners; migrate persistence and entity-smoke together. | Both real consumers use the same implementation; changed declarations reach callers; unsupported selections fail before effects; displaced code and conflicting instructions removed. **In progress, not complete.** |
| B — Capabilities, proof and recovery | Existing provider adapters, realization gate, release succession and acceptance. Generalize supported capabilities, not workload names; distinguish first qualification, ordinary update and capability-changing update. | Initial release, successor, rollback, interrupted operation, expected failure and owned cleanup use the same contracts. Requalification and partially failed updates remain open. |
| C — Fast execution and reliable continuation | Existing selector/cache, custody receipts, operation journals and reporting. Connect stages without repeated work or loss of failure evidence. | Accurate stage status, safe actionable failures, resume without replay, credential-expiry handling and end-to-end timing; no new parallel runner or evidence registry. |
| D — Integrated demonstration | Use the existing consumers and a differently named declared consumer to exercise the connected route. Remove remaining superseded machinery throughout A–C, not only here. | Frozen-source local integration, package and finally live proof; measure the ten-minute target and separately identify actual provider waits/full regression. A renamed fixture alone is insufficient. |

For every batch: inspect actual consumers and conflicting rules; record the
shared owner and justified workload data; refactor callers and remove obsolete
code together; review source and counterexamples; run only affected focused
checks. Do not run full proof after each lesson. Record terminal run results in
the session log, outside frozen verification inputs. No lesson is closed solely
by a rule, a refreshed review hash or a planned test.

The following is engineering disposition, **not a claim that 34 fixes are
complete**. “Historical fix” means the original incident was repaired; reusable
coverage still needs the named batch. Lesson numbers refer to
[the existing retrospective](../../../../docs/education/lesson-plans/0002-entity-smoke-release-retrospective.md).

| Lesson | Current finding and remaining obligation | Batch |
| --- | --- | --- |
| 1 — Complete path upfront | Shared operations exist; connected ordinary delivery and ownership remain incomplete. | A–D |
| 2 — Overclaimed local success | Stage-separated selector reports exist; verify caller summaries do not claim later-stage success. | C, all reporting |
| 3 — Compiler mapping/shim | Declaration-derived workspace build exists; prove new and removed programs through real packaging callers. | A, D |
| 4 — Diagnostic owner | Original identifier corrected; keep catalog-owner checks in applicable feature validation. | A, focused regression |
| 5 — Diagnostic explanation | Do not invent missing foundations; inspect existing definitions and producers before changes. | All source reviews |
| 6 — Feature organization | Existing contract/transport/domain/persistence and per-use-case services are the owner; no second feature template. | A |
| 7 — Circular preflight | Historical bounded exception exists; replace workload-only admission with reusable capability rules. | B |
| 8 — Admin/runtime assumption | Separate runtime proof supported; verify declared principal ownership across consumers. | B |
| 9 — Expected failure | Historical unready exception exists; generic recovery must represent expected failure and subsequent readiness. | B |
| 10 — Restore cleanup | Historical owned-clone exception exists; generalize ownership/readback requirements without broad deletion. | B |
| 11 — Acceptance dirty files | Collector-file exception repaired the incident; verify exact generated evidence versus source changes in the shared route. | B |
| 12 — Controller/image coupling | Controller-only repair was added for the incident; reusable input identity and artifact reuse remain to be proved. | A, C |
| 13 — Tests/controller identity | Audit source manifests and cache inputs; test changes must invalidate test evidence, not unrelated runtime identity. | A, C |
| 14 — Provider response shapes | Existing adapter regressions improved; exercise real caller mappings and uncertain/partial responses. | B |
| 15 — ECR endpoints | Initial incident fixed; dependency alignment must cover declared registry reachability before launch. | B |
| 16 — PostgreSQL assumptions | Preserve separate bootstrap, migration and runtime access checks through shared declared capabilities. | B |
| 17 — Historical/fresh evidence | Existing freshness and immutable-evidence owners remain; prove no historical receipt becomes current health. | B, C |
| 18 — Interrupted recovery | Reservation/journal helpers exist; shared end-to-end reconciliation still incomplete. | B, C |
| 19 — Combining evidence | Successor collection added locally; general reusable acceptance composition remains open. | B |
| 20 — Freshness consumed locally | Move immutable preparation before fresh observation; measure actual remaining validity at execution. | C |
| 21 — Serial investigation | Review connected failures as one batch; parallelize independent read-only checks where useful, without concurrent edits to frozen inputs. | All batches |
| 22 — Feature-specific machinery | Low-level sharing is partial; remove repeated declarations and lifecycle control, not just helper bodies. | A, B |
| 23 — Slow feedback | Selector/cache exist; narrow real proof inputs and replace repeated direct prechecks with matching evidence reuse. | C |
| 24 — Accepted-state fixtures | Test both initial and successor states; do not encode current acceptance as a fixture prerequisite. | B |
| 25 — Copied fixtures | Inventory all callers when contracts change; share reusable fixture builders without erasing independent assertions. | A, B |
| 26 — Stale diagnostic reviews | Existing source-matched review procedure applies; finish review before frozen focused tests. | All batches |
| 27 — Lost failure detail | Selector still has not-retained child details; add bounded safe diagnostics through its existing report owner. | C |
| 28 — Credential lifetime | Plan credential validity against remaining operations; distinguish expiry from provider failure. Polling does not renew an authentication session. | C |
| 29 — Assistant-dependent continuation | Persistent operation evidence exists; one resumable coordinator still needs implementation/proof. | A, C |
| 30 — Repeated approvals | Reuse recorded authority within its actual scope; only new authority or external authentication requires user action. | All batches, C |
| 31 — Unreliable remaining-work reports | This current matrix supersedes broad completion claims; report implementation and proof separately. | All batches, C |
| 32 — Premature pass | Only terminal successful evidence can mark a check passed; started/running/deferred remain distinct. | C |
| 33 — Local execution mistakes | Use governed entrypoints and exact workspace/input identity; cover failure propagation rather than manual command chains. | A, C |
| 34 — User became coordinator | Implementer owns connected review, corrections and continuation; report material decisions and actual outcomes. | All batches |

### Batch A first connected slice: declared ECS template selection

Inspection found `entity-smoke-runtime-configuration.py` repeats workload IDs,
provider references and template selection already owned by workload bindings.
The existing `ecs-runtime-configuration.py` is used by persistence, bootstrap,
staging package projection and entity-smoke package projection. Extend that
owner to select an explicitly declared sibling template per workload; retain
the default template for existing bindings. Point entity-smoke at that owner
and delete the special adapter and its active references. Do not rewrite
historical release evidence or the pinned inventory.

Consumers: declaration coverage/runtime-configuration, entity-smoke workload
binding and declaration impact paths, composition template tests, the existing
declaration-coverage regression/catalog, package-projection callers and the
diagnostic review ledger. Package projection remains single-template and
unchanged. This removes one actual special adapter; it does **not** complete
shared release coordination or Batch A.

Diagnostic predicates: absent per-workload template selects the supplied default;
an explicit template must be a nonempty relative sibling filename, regular and
not symlinked, within the supplied template directory. Reject empty/wrong-type,
absolute/traversing/symlinked or missing selections, duplicate workload IDs and
invalid provider resources before yielding normalized facts. Preserve the
existing caller's `runtime-provider-configuration-invalid` safe projection;
never expose supplied paths, template contents or secret values. Tests must use
two real bindings, a differently named multi-template fixture, invalid-path and
symlink canaries, and unchanged package projection. These checks are planned
until terminal results are recorded.

## Earlier consolidation progress (historical scope)

| Stage | Status | Deliverable |
| --- | --- | --- |
| 0 — Source inventory | Complete | [File-level findings and comparison](../../../../docs/04.deploy/plans/core-platform-deployment-route-inventory.md), pinned to `eecf0c50178ef004f62792aef2835023e492a470` |
| 1 — Runtime payload assembly | Source reviewed; focused checks passed | Both callers use one assembler; full affected integration and actual image qualification remain pending |
| 2 — Remaining common operations | Implementation and parent source review complete; final registered proof pending | Shared package/provider/task/publication/change-set/replacement/snapshot and candidate owners in use; distinct alignment, ordering and restore policies retained; C03 canonical migration and compatibility fixtures complete |
| 3 — Remove superseded implementations | Migrated internals and four obsolete incident executors removed; historical readers preserved | Three historical helper paths are export-only wrappers; cumulative source change is not a net reduction; source accounting and historical compatibility observations are recorded below |
| 4 — Demonstrate reuse | Connected controlled fixture reviewed and passed | Differently named packaged Node workload uses shared reservation, CloudFormation, ECS, snapshot and candidate entrypoints; real PostgreSQL, OCI qualification and AWS proof are not established |

The original bounded helper, reporting and build slices were source-reviewed;
they do not establish completion of the expanded programme above. Their focused
proof is recorded below; complete affected integration and actual local image
qualification remain pending. Final frozen-input run IDs, checkpoint/image identities and
terminal outcomes are recorded in the active
[session log](../../../../commitLogs/2026/nov/06/2026-11-06-17-07-new-chat-session/README.md),
so later execution observations do not require changing verified source inputs.
Earlier dated implementation entries below are chronological history, not
current blockers; in particular, local checkpoint authority was granted and C03
has moved beyond its former committed-plan boundary. No fresh publication or
AWS proof is claimed by this cleanup.

## Reusable delivery reconciliation inventory — 2026-11-15

### Scope, authority and objective

The user authorised this bounded inventory after reviewing the proposed
reusable-delivery rules and asking which existing text or code conflicts with
them. This section records source findings and proposed corrections only. It
does not enact new standards, resume the paused consolidation goal, change
release requirements, authorise provider operations or claim full proof.
The earlier "three workstreams implemented" status covers those original
workstreams, not the additional corrections below.

Inspected checkpoint: `872052b03a239a7ddb8d4fc98cb6cfa7f178497f`; the active
2026-11-06 chat worktree was clean before this document edit. The parent agent
performed the read-only review; no new agent, build, container, CI run or AWS
operation was started. All paths below are relative to the repository root.

The user's objective is reusable machinery, modular ownership, predictable
expansion and a normal delivery lifecycle of at most ten minutes for changes
or additions to features, apps and products. Infrastructure capabilities must
be consumable through that same lifecycle. Report total elapsed time, with
genuinely externally controlled setup/waits and additional full regression
work identified separately. Repeated compilation, unnecessary checks,
orchestration overhead and manual repair are not external-wait exclusions.
The target is not yet proved. Work through the retrospective corrections with
focused checks, then perform consolidated full proof on stable inputs.

### Inspected coverage and limits

| Surface | Inspection performed | Limit of this observation |
| --- | --- | --- |
| Governance | Change completion, test execution, lifecycle ownership, package qualification, realization/evidence reuse, feature creation, deploy/acceptance workflows and AWS applicability rules | Source review, not proof that all callers comply |
| CI | Read delivery-coverage and entity-smoke publication workflows; compared bootstrap, persistence and collector publication entrypoints; searched staging workflow entrypoints | Core-platform path is the detailed case; no hosted executions or complete staging migration audit |
| Build/package | Traced entity-smoke workflow to its builder, shared candidate prechecks, composition suite, Dockerfile and qualification receipt; compared persistence builder | No image builds, cache hit measurements or assurance that host/container compilation can be safely collapsed |
| Selection/cache | Read execution, final revalidation, feedback classification, receipt identity, invalidation reasons and safe reporting code; inspected composition catalog inputs | No empirical cache miss frequency or end-to-end performance measurement |
| Acceptance | Traced entity-smoke collector's exact task/control requirements and scope declaration; read generic succession workflow | Identifies this route's requirements; does not assert every other release repeats this route |
| Historical text | Read incident-retirement notice, current consolidation status and retrospective progress | Historical records are evidence, not instructions to rerun retired operations |

This is a bounded reconciliation inventory, not an exhaustive audit of every
feature, frontend build, provider adapter or CI branch. Those consumers must be
included when a proposed correction changes their shared owner. No absence of
a conflict outside this inspected set is claimed.

### Findings, surviving owners and corrections

<!-- deterministic-check: allow reason="this inventory records observed implementation and proposed corrections; execution and evidence reuse remain governed by existing lifecycle and selector entrypoints, not these table descriptions" -->

| ID | Confirmed source observation and risk | Surviving owner and proposed correction | Focused evidence required before closing the correction |
| --- | --- | --- | --- |
| RD01 — Objective ownership | Shared completion already requires connected consumers and proportionate tests; lifecycle ownership already forbids duplicate capability checks/gates. Neither establishes the user's end-to-end ten-minute objective. Adding copies everywhere would conflict with single ownership. | Put the cross-layer objective in `.agentic/shared/standards/require-change-completion.md`; keep timing/test policy in `.agentic/shared/testing/standards/test-execution.md` and deployment semantics with `.agentic/04.deploy/standards/lifecycle-stage-ownership.md`. Feature/deployment workflows reference those owners. | Review a feature change, new app and new infrastructure capability against one short reuse/impact assessment. Do not pretend a text-presence check proves architectural simplicity. |
| RD02 — Workload-only governance | `.agentic/aws/standards/operational-realization-applicability.md` still restricts read-only preflight, expected-unready observation and disposable-restore cleanup to entity-smoke. A future workload cannot acquire these capabilities merely by using the shared code. | General capability/admission semantics stay with `.agentic/04.deploy/standards/operational-realization-gate.md`; AWS execution conditions stay with the existing applicability standard and provider adapters. Separate reusable rules from incident-specific approval/history; bind new uses to declared ownership and operation scope. | Another declared workload can use the capability; undeclared/widened operations and replay remain rejected. Test actual callers, not just renamed fixtures. Preserve resource protection and execution-authority boundaries. |
| RD03 — Qualification versus ordinary release | `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route.py` requires the exact `A.TASKS` set and seven `CONTROLS`, including replacement, stop/restart, snapshot, restore and cleanup. The scope declaration's server-mediated proof includes replacement. The acceptance workflow explicitly requires replacement/restore for first acceptance. A readiness-only report cannot satisfy these contracts. | Keep declaration/health-recovery owners and shared `release-succession`; define applicability for new platform capability qualification, first workload use of an already-qualified capability, ordinary update and changes invalidating prior proof. Reconcile collector, declarations, acceptance workflow and their tests together. Preserve the historical complete-proof reader. | Exercise each change class: routine changes retain relevant capability proof plus fresh workload evidence; changed permissions/schema/runtime/recovery invalidate the affected proof; missing first-use obligations cannot pass. Do not assume every new feature needs full infrastructure qualification or silently exclude its required tests from the budget. |
| RD04 — Broad suite labelled fast | `scripts/repo/check-selection/checks.yml` labels `entity-smoke-composition` development-eligible with a 60-second estimate. Its `20-build/entity-smoke-composition/smoke-test.sh` compiles fresh output and invokes alignment, administration, task, failure/restart/credential, infrastructure, restore, acceptance and qualification fixtures. It is not just a small composition check. | Keep `checks.yml` as the single catalog and the existing selector as scheduler. Separate focused units from the broad composition/controller aggregate, retaining full required membership. Update the estimate/rationale from measured results after the split. | Changed feature logic selects fast relevant units; controller changes select their tests; integration still includes every former assertion; aggregate child failures propagate. Do not meet the budget by dropping coverage. |
| RD05 — Package prechecks rerun directly | `40-package/build-entity-smoke-image/script.sh` directly runs catalog, app and full composition checks. Its workflow and shared `build-candidate-image/operations.sh` both call delivery inventory. The persistence builder also directly invokes PostgreSQL diagnostics/integration/composition checks. These direct calls do not themselves consult selector receipts. | Keep builders, shared candidate prechecks and selector/cache owners. Route reusable local prerequisites through their registered checks with exact input identity, while retaining distinct container/package proof. Reconcile publication callers as well as local builders. | Matching local evidence avoids duplicate execution; changed relevant input/runtime reruns it; direct package entry cannot skip required prerequisites. Measure both cold and warm paths. The Dockerfile's isolated compilation is a separate trust boundary, not automatically safe to delete. |
| <!-- deterministic-check: allow reason="observational inventory and proposed proof requirements, not an executable procedure or replacement for the existing stage owners" --> RD06 — CI and release boundary | `.github/workflows/delivery-coverage.yml` executes integration selection. Entity-smoke publication independently installs, validates, builds, qualifies, scans and attests, and explicitly does not deploy. These are separate phases, not one measured normal-delivery command. A 35-minute job timeout is a safety ceiling, not measured duration or a conflicting delivery promise. | Preserve CI, package custody and deploy/run owners. Connect one source/artifact-bound delivery identity and timing observation across their existing entrypoints. Define when the clock starts, required stages, interruptions and completion before claiming a result. Do not introduce a second deployment engine or import arbitrary local receipts into CI. | A publication-only run cannot claim delivery; missing/failed deploy or smoke remains incomplete; resumed runs retain gaps and original elapsed time; overlaps are not double-counted; cold installation and repo-controlled setup remain visible. |
| RD07 — Evidence invalidation | `scripts/repo/check-selection/script.py:identity` binds declared inputs, runtime, verification contract and dependency evidence; `local_cache.py` explains misses. Audited `scope_inputs: false` checks already separate impact from proof inputs. The realization standard permits immutable artifact evidence reuse but expires live observations after 900 seconds. This is not a missing reuse policy. | Preserve selector/cache and realization owners. Audit overly broad input declarations and direct callers before narrowing anything. Package `qualification.py` retains image identity, explicit input hashes and projected runtime configuration; it is not interchangeable with local check cache. | Unrelated text edits preserve only genuinely unaffected proof; test/assertion, source, runtime/configuration and dependency changes invalidate the corresponding evidence; stale live observations never become fresh by reusing an immutable receipt. Cache-hit savings remain unmeasured until execution. |
| RD08 — Reporting duplication and semantics | `execution_policy.py` already owns local run reports, stage-separated evidence and per-check estimate overruns. `shared/deployment-operation-diagnostics.py` owns failure/uncertain-operation diagnostics with bounded persistence execution timing, not successful end-to-end delivery reporting. Neither is a generic release executor. | Extend existing local reports and reference package/deploy/run receipts. Do not force success/budget reporting into the failure-diagnostic schema. The previously proposed `shared/delivery-report/` folder is provisional, not an approved file addition; justify any small observation-only adapter only after its cross-stage inputs are defined. | Separate estimate overrun, delivery-budget miss and functional outcome; missing timing yields unknown, never pass; reports cannot grant execution or seed trusted proof; total wall time and evidenced exclusions remain auditable without secrets. |
| RD09 — Useful failure evidence | The test standard forbids raw child output. The selector captures output but stores `not-retained` markers, leaving an exit status without the actual child assertion detail for ordinary leaves. The earlier unexplained failures illustrate the diagnostic cost. | Keep diagnostic definitions/producers and existing safe report projection. Add bounded structured failure details and safe evidence references, with explicit unavailable state for unadapted commands. Do not retain unrestricted stdout/stderr as a shortcut. | A failing child yields actionable safe detail without rerunning it; canary secrets and arbitrary output are rejected; original status survives failed report retention. Registration and aggregate handling must preserve the child failure identity. |
| RD10 — Historical/current text | The AWS applicability standard already explicitly retires the completed incident executors; do not describe them as still-active duplicate deployment commands. The retrospective progress still says lesson 1 / 0 of 34, while chat has discussed later topics. This plan's original implementation status does not cover these new corrections. | Keep historical approvals/receipts and immutable accepted evidence. Update current status/pointers in their existing owners as work progresses; distinguish discussed, understood/confirmed, implemented and verified. This section qualifies the original plan status without rewriting history. | Status review agrees with actual code/evidence and pending work. Never mark lessons understood or full proof complete merely because topics were discussed. No historical evidence deletion or mass document rewrite. |

### Exact source anchors for the next implementation pass

These are owner/caller references, not an instruction to edit every file listed.
The future change set must use the smallest connected subset for each finding.

- RD01/RD02: `.agentic/03.product/feature/workflows/create-feature.md`,
  `.agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md`,
  `.agentic/aws/standards/operational-realization-applicability.md` (sections
  "Completed incident executors are retired", "Entity-smoke read-only execution
  preflight" and its observation/cleanup exceptions).
- RD03: `.agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md`;
  `infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml`
  (`server_mediated_dependency_proof` and health/recovery proof);
  `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route.py`
  (`CONTROLS`, `acceptance-proof-set-incomplete`), `acceptance-evidence.py`,
  `acceptance-controls.py`, and their route/control tests.
- RD04/RD05: `scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh`;
  `scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh`;
  `scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh`;
  `scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh`;
  `infra/04.deploy/03.product/image/entity-smoke/Dockerfile`.
- RD06: `.github/workflows/delivery-coverage.yml` and the four existing
  `publish-kanbien-core-platform-{core-server,core-server-persistence,entity-smoke,observability-collector}.yml`
  workflows; `.agentic/04.deploy/standards/package-qualification.md` and the
  package/deploy/run workflows. Publication remains distinct from deployment.
- RD07/RD08/RD09: `scripts/repo/check-selection/{script.py,execution_policy.py,local_cache.py,checks.yml,mechanics_test.py,README.md}`;
  `scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py`;
  `scripts/04.deploy/shared/deployment-operation-diagnostics.py` and its tests.
- RD10: `docs/education/lesson-plans/0002-entity-smoke-release-retrospective.md`,
  this plan, the existing route inventory and the active session log. The
  lesson plan remains user-led; this inventory does not mark any lesson complete.

### Implementation ordering and acceptance of the follow-up

1. Reconcile proof applicability and objective ownership together (RD01–03).
   Keep new-capability qualification distinct from reuse by a new workload.
   Do not declare a routine route fast by silently reducing required proof.
2. Correct fast feedback, prerequisite invocation and evidence invalidation
   together (RD04–07; retrospective lessons 13 and 23). Reuse existing build,
   selector and custody machinery. Validate complete aggregate coverage and
   cache invalidation with focused fixtures before broader execution.
3. Connect truthful timing and useful safe failures (RD08–09; lesson 27), then
   reconcile current documentation (RD10). No separate scheduler, check catalog,
   approval registry or new deployment controller. No new reporting folder is
   precommitted by this inventory.
4. Review the remaining retrospective lessons for connected corrections; do not
   turn this list into a claim that all 34 lessons are resolved. Once the agreed
   changes are stable, perform the consolidated full proof. Measure a routine
   update and a new workload consuming existing capability; separately account
   for genuine new infrastructure setup and additional regression work.

Safety and correctness checks must remain effective. A budget miss is an
engineering finding, not authority to cancel an uncertain mutation, skip proof
or declare success. Fresh cloud facts, ownership, no-replay protection, data
preservation and acceptance custody are retained. Provider/provisioning and
regression exclusions need evidence; normal repo work is not hidden by starting
the clock after expensive preparation. Exact command/correlation/report schema
design remains follow-up implementation, not an achieved capability.

Inventory deliverable: this existing plan only; no new, moved or removed files,
no runtime or policy edits, no change to paused/full-proof status. Validation is
limited to source review, document metadata, referenced-path checks and diff
hygiene; it does not establish runtime behaviour or a ten-minute release.

Inventory validation: the scoped artifact-header check passed for this file;
`git diff --check` passed; all 22 concrete source-path references in this section
exist and RD01–RD10 are unique. Grouped brace paths are readable shorthand,
not literal file links. The reference checker was corrected to distinguish
the `:identity` symbol suffix from a file path before reporting that pass.
Only this plan is modified; nothing is committed by this inventory step.

### Implementation batch 1 — objective and proof-applicability governance

The user authorised implementation after this inventory and supplied the
AGENTS efficiency principle: assess duplication/reuse and actively reconcile
conflicting older machinery and instructions. That instruction applies now.
The saved AGENTS file in the recorded worktree does not yet contain the quoted
edit; preserve the user's editor/worktree changes rather than overwriting them.

This batch updates existing owners only: shared change completion and test
execution; deployment lifecycle ownership and realization proof; feature
creation/readiness; target update; health/recovery verification; and release
acceptance. RD01 is the implementation target. RD03 receives a single explicit
proof-applicability design rule and a migration boundary, not a bypass of the
currently stricter declarations/collectors. RD02 provider generalisation and
RD03 executable applicability remain pending with RD04–09 implementation.
The rule is deliberately distinct from a claim of achieved performance.

Conflict review: preserve current first-acceptance replacement/restore
requirements, fresh target evidence, explicit operation authority and the
exact collector proof set. Existing evidence reuse is retained, not replaced.
Change the feature workflow's unconditional "run selected local checks" wording
to the existing development/integration distinction; it must not trigger full
integration at each conversational step. Keep all final proof obligations.
No new schema, command, reporting folder, test catalog, registry or approval
step is introduced. No files move or retire in this batch.

Diagnostic applicability: process-only Markdown edits do not add runtime
conditions, diagnostic definitions, producers or readers; no review-ledger
hashes or runtime catalog exports need modification. Source review will check
the linked owner chain and consider three counterexamples: a feature creates
another deployment engine; a new workload claims old capability proof as its
own live proof; a fast-looking report hides required preparation or a failed
acceptance. The rules must reject each without requiring another full proof
during editing. Verification is scoped metadata/link/diff validation and this
source review; runtime and performance proof stay deferred.

Batch result: RD01 governance is implemented in the existing owners and linked
from feature readiness/creation and deployment/run workflows. RD03's assessment
and compatibility boundary are documented; its executable correction and RD02
remain pending, not passed. The first-release recovery/collector rules were not
relaxed. RD04–09 tooling work is not implemented by this documentation batch.
RD10 is reflected here without marking any user-led lesson complete.

Parent source review rejected the three counterexamples above: the shared
reuse section requires an owner/disposition review, realization applicability
requires new-workload proof rather than inherited success, and budget accounting
includes preparation and terminal acceptance with explicit missing-timing state.
These are reviewed governance requirements, not an automatic architecture or
performance checker. Existing metadata validation passed for all ten changed
Markdown files; all sixteen added Markdown links resolve to files/headings;
`git diff --check` passed. No executable source, runtime diagnostic, provider
permission, schema, accepted evidence or AGENTS file changed. The pre-existing
inventory edit is preserved. Full proof remains deferred; no commit, push,
publication, AWS execution or background test was started.

### Batch 2 pre-implementation finding — successor route missing

The user approved the proposed schema/validator/applicability/collector batch.
Tracing its real consumers before editing exposed a material gap in that file
map: entity-smoke does not yet have an ordinary successor delivery route.

- `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route.py:gather`
  requires `accepted_release_id == "none"` and the initial stop/preserve-data
  policy; otherwise it raises `acceptance-subsequent-release-proof-required`.
  This is explicit rejection, not merely an overly large test selection.
- `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/deployment-control.py:prepare`
  permits initial CREATE only when the stack is absent, or activation UPDATE
  after confirming desired count zero with the candidate bindings. It does not
  implement an accepted-running-predecessor to successor image transition.
- The existing persistence `qualify-proof-applicability/script.py` covers a
  restore-verifier-only successor, including one exact historical test-helper
  delta. It is not a general feature-release reuse policy. Keep its historical
  meaning and exact receipt checks; do not widen them by deleting restrictions.

Consequently, changing only proof declarations and the collector would not
produce the promised ordinary feature-release path. Removing the first-release
guard would also admit an unproved predecessor/recovery arrangement. No such
guard, declaration, receipt or executable was changed in this inspection.

Recommended scope extension: connect entity-smoke to the existing shared
successor-update machinery, using the persistence
`scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/`
and shared `scripts/04.deploy/shared/provider-adapters/aws/change_sets.py` as
the source owners to compare/reuse. Include predecessor selection, exact
workload/permission/configuration bindings, compatible-image recovery and
successor acceptance before enabling selective proof. This is a connected
update binding, not permission to create a parallel deployment engine.
Keep initial-release behaviour, historical readers and accepted evidence.

The user subsequently directed refactoring the incorrect first-release-only
implementation and explicitly said to continue. That authorizes the connected
successor-path correction, removal of superseded implementations and focused
local tests; it does not resume full proof or authorize AWS execution. Preserve
historical evidence readers only where actual retained records require them.

### Successor refactor — connected implementation sequence

1. Move existing CloudFormation parameter-preservation policy to the existing
   shared change-set owner, remove its workload-local implementations, and make
   both persistence and entity-smoke use the same checked parameter reader.
   Keep each workload's resource, image, permission and recovery policy at its
   binding. This is preparation for the successor route, not that route itself.
2. Connect accepted-predecessor selection, ordinary update and compatible
   rollback to those shared mechanics. Retain exact ownership and no-replay
   behavior. Do not revive the retired incident-specific source-transition
   executor as a general deployment route.
3. Replace the initial-only orchestration/acceptance assumption with connected
   release verification and applicable proof selection. Keep the historical v1
   acceptance reader for the actual accepted record; do not edit that record or
   admit subsequent releases merely by deleting the first-release guard.
4. Prove the real caller path for A-to-B update, retained-data verification and
   compatible rollback using focused controlled fixtures. Record separately what
   requires image qualification/live proof. No claim of a ten-minute delivery
   target being achieved follows from these fixtures.

Step 1 consumer/diagnostic inventory (tests planned until recorded below):

- The existing persistence `transition-qualified-release` parameter constructor
  and `prepare-candidate:update_parameters_match` have provider-neutral meaning.
  Reuse them in `shared/provider-adapters/aws/change_sets.py`, retaining their
  current callable interfaces for real baseline callers and controller fixtures.
- Entity `deployment-control:exact_parameters` and baseline transition review
  both consume CloudFormation parameter rows. Missing/wrong-type rows, missing
  keys/values and duplicate keys must reject rather than disappear through a
  dict comprehension. ResolvedValue is provider metadata, not an override.
- Safe caller outcomes remain `deployment-provider-parameters-mismatch`,
  `persistence-release-transition-not-reviewable` and
  `persistence-release-transition-update-parameter-inputs-invalid`; the shared
  pure reader returns no private values on failure and grants no operation.
- Untouched parameter values must use UsePreviousValue when constructing an
  update and must match the actual predecessor in review. Candidate-owned
  parameters may change; undeclared/new keys, omissions and drift must reject.
- Extend the existing `controller-regression.py` and
  `deployment-control-test.py` actual consumers, including duplicate/conflicting
  rows, malformed inputs, unchanged parameter preservation and no execution
  after rejection. Existing checks are `persistence-provider-regression` and
  `entity-smoke-composition`; focused fixture results are not whole-check passes.

Steps 2–4 remain incomplete until their connected code and tests are present.

Focused-check finding: the baseline controller suite also assumed the retained
October rollback compatibility record still authorized today's contract. Both
the unchanged HEAD implementation and the working implementation return false;
the owning reader validates the historical archive with
`current_contracts=False` and rejects current use with
`release-succession-compatibility-contract-mismatch`. Correct the controller
fixture to declare its compatibility prerequisite as controlled input and prove
that false blocks before provider access. Keep actual archive integrity and
current-contract rejection in the existing provider CLI fixture, plus its
existing temporary valid/changed-contract compatibility fixture. Do not rewrite
the archive, refresh its hashes, or loosen the production compatibility reader.

Step 1 result (2026-11-15): implemented in the existing shared change-set
module; removed the two workload-local parameter-policy bodies. Persistence
update, rejected-review cleanup and all three completion-observation branches
now reject malformed/ambiguous rows through the same reader as entity-smoke.
Existing callable baseline interfaces remain because five real update
controllers use them; they delegate rather than retain duplicate policy.

- Direct controller fixture: 54 tests passed (7.731s); direct provider CLI
  fixture: 6 tests passed (13.799s). Feature deployment-control and public
  infrastructure-route fixtures passed, including original no-replay cases.
- Registered `persistence-provider-regression`: passed, 58.359741s elapsed,
  38.330646s command execution. Report:
  `.cache/test-runs/20261115T181130Z-c90db15d9bcb44498edc52e207426c3d/report.json`.
  This is requested-local proof, not complete affected integration.
- First registered attempt failed; direct reproduction exposed the stale
  rollback fixture assumption described above. Its report-retention boundary
  additionally returned OSError. The final run used permission to retain local
  evidence in the recorded chat worktree/Git cache and passed. Do not relabel
  the original failed attempt as a pass or infer its retention cause.
- Diagnostic structural review: passed, no findings; metadata headers:
  seven files passed; `git diff --check`: passed.
- No image was qualified, no live operation ran, and no acceptance record or
  provider configuration changed. Full proof remains paused. Successor-route
  implementation and acceptance are still incomplete, as steps 2–4 state.

### Successor refactor — implementation and bounded verification (2026-11-15)

Steps 2–4 now have implementation in the existing infrastructure, task and
acceptance owners. Final source-matched focused verification is in progress;
this entry is not a full integration or live acceptance claim.

- Infrastructure selects the exact typed accepted predecessor, a deterministic
  candidate delivery namespace and the existing shared change-set/reservation
  mechanics. Image update and compatible rollback retain original data/label
  ownership. No new deployment engine or evidence registry was added.
- Review exposed two connected correctness gaps: immutable task-definition
  revisions were counted as updates, and recovery compatibility was only
  checked when requesting rollback. The reviewed successor must report five
  definition replacements and one service update, and establish compatible
  recovery before candidate deployment. Existing refresh policy has a closed
  accepted-predecessor/compatible-rollback alternative; retained stopped-workload
  declarations keep their original meaning. Actual controller validation is
  required; declaration flags are not provider proof.
- Ordinary verification uses four fresh pairs: runtime permissions, lifecycle,
  collision and original-record read. Each uses the existing preflight,
  reservation, completion and gate owners. Its prerequisites bind the actual
  deployment and exact previous tasks. Bootstrap, migration, permission changes
  and long restore proof are not repeated merely for a feature-only change.
- The existing acceptance schema owns the recovery-input paths. Actual immutable
  Git trees establish applicability, including additions, removals and file
  modes. Changed configuration/permissions/database identity or protected
  migration/persistence/runtime/build/dependency inputs reject before update.
  **Affected-capability successor requalification is not implemented by this
  ordinary-update branch.** This is a remaining delivery boundary, not a claim
  that all new functionality can already use the fast path.
- V2 evidence binds exact predecessor candidate/hash/history, deployment,
  current task plan/prerequisites and current runtime. Historical v1 readers
  remain for actual retained evidence. Iterative lineage validation avoids a
  fixed maximum release count and rejects cycles. Promotion checks the selected
  manifest predecessor and current same-candidate proof through shared succession.
- Diagnostic review replaces stale initial-only/cleanup-blocked descriptions,
  retains partial status and records explicit fixture dependencies and missing
  live/requalification evidence. New predicates reuse finite owner failures;
  private paths/provider errors are not forwarded as diagnostic detail.
- The existing command README was source-reviewed using the README skill.
  Its update sequence, recovery arguments, four fresh checks, receipt location
  and unimplemented requalification boundary replace first-only descriptions.
  This is scoped command guidance, not a whole-folder documentation rewrite.

Recorded evidence so far: the shared realization compiler's actual CLI fixture
passed 162 cases with zero provider calls; the actual original
`release-53798ef563be4ce9a8c5b2f0` historical state validates unchanged and
explicitly reports `current_readiness: false`. Focused Git applicability,
successor archive, aggregate and local succession protocols have passed with
their controlled dependencies identified in the source review. The final
connected update/task batch and source-matched registered results are recorded
below when terminal, not inferred from those component results.

Full proof remains paused. No image qualification, publication, AWS mutation or
new accepted release was performed. This command chain is not yet a one-command
delivery orchestrator, and the ten-minute objective is not measured or achieved
by these local fixtures.

Recovery boundary: this ordinary route requires an owned CloudFormation stack
in CREATE_COMPLETE or UPDATE_COMPLETE. It can select the compatible prior image
when application verification fails on a completed deployment; it does not
implement recovery from UPDATE_FAILED or other partial provider transitions.
Those cases remain incomplete, not automatic retry or generic recovery authority.

Final-check accounting: registered `operational-realization-regression` passed
(29.640889s execution / 42.261115s elapsed), report
`.cache/test-runs/20261115T190400Z-376eb24909094e98823b93669980e91c/report.json`.
The first final acceptance command exited zero, but its report correctly remained
`gap`: plan/review edits overlapped the run (`check-input-changed-during-execution`).
That is an orchestration error, not a passing source-matched check. Preserve
`.cache/test-runs/20261115T190852Z-d55c1cac8224468e8ff60913237cfa5b/report.json`.
All task sources are now frozen. The rerun result is recorded in the existing
chat session log, outside this check's inputs, so reporting it does not
invalidate the just-tested documentation. Diagnostic structural review passed
with no findings; scoped metadata checked 39 files and README links/diff checks
passed. None of those structural checks establishes live behaviour.

## Inventory method

1. Pin the source checkpoint and record existing unrelated changes.
2. Enumerate both routes across alignment, build, package, deploy, run and
   acceptance. Include declarations, workflow callers, tests and test selection.
3. Read implementations and imports, not just names. Distinguish shared code,
   exact copies, similar responsibilities with different semantics, and
   legitimate workload data. Record counts with explicit inclusion rules.
4. Classify each component as keep, parameterise, consolidate, or remove after
   callers migrate. Retained historical evidence is never deletion debt.
5. Choose the smallest complete first slice from the findings, including its
   callers, destination, tests, compatibility and rollback. Do not assume that
   the older implementation is automatically the better survivor.

## Preservation boundaries

### B07 update-controller comparison and implementation boundary (2026-11-15)

The five effectful baseline UPDATE consumers are `transition-qualified-release`,
`apply-database-permission-surface`, `apply-private-verifier-route-update`,
`apply-observability-mvp-surface` and `apply-restoration-verifier-surface`.
`prepare-candidate.observe_update` is their existing shared historical reader,
not a sixth mutation controller. Each repeats named-change observation,
conditional creation, bounded review, parameter admission, execution and final
observation. Move that sequence to the existing shared `change_sets.py` owner
and parameter-file submission to the existing baseline `change-set-operations`
binding; retain the individual resource, image, permission and rollback guards.

This is a structural extraction, not an implicit change to operation succession.
These commands' governed interrupted path is explicit read-only `--reconcile`.
Unlike first-time CREATE, image rollback can return to an accepted digest, and
the two rejected-review cleanup commands support removing an unexecuted review
before correction. Applying the CREATE store's fixed-name one-shot reservation
to these paths would disable supported recovery. Preserve these contracts;
do not claim this extraction adds durable normal-invocation replay protection.
Any future automatic-resume/successor protocol must cover those real consumers.

Diagnostic predicates remain at their owners: a failed initial observation
blocks before creation; only exact provider absence selects creation; unsuccessful
submission is uncertain, never retried; unreviewable or already-executing changes
select observation; parameter mismatch blocks execution; final outcomes come
from the existing reader. Preserve existing report schemas/codes and sensitive
parameter exclusion. New local parameter-file errors must distinguish failure
before provider invocation from uncertainty after invocation. Planned proof:
actual five callers, success/timeout/no mutation on unknown observation, retained
rollback support image and non-image parameters, unchanged historical readers,
and different workload names through the common sequence. No AWS execution.

The baseline failed-candidate retirement route is a third distinct policy:
only a never-accepted `ROLLBACK_FAILED` stack with a positively owned protected
RDS instance can advance through unlock and exact-stack deletion. It must not
be substituted for feature first-release stop/preserve, nor for qualified image
rollback. Comparison also confirms that feature `failure-route.policy` already
uses the shared release-succession policy selector under its custody lock;
there is no justification for a second recovery-policy registry. Its bounded
owned-task stop and separate restart/readback are not the baseline RDS unlock
and deletion operation. Preserve these implementations and their typed receipts;
their provider transport already uses the common adapter.

B07 UPDATE extraction is implemented and independently source-reviewed. All
five public commands use `prepare.apply_update` → baseline parameter transport
→ shared `change_sets.reviewed_update`; their five duplicated submission blocks
are removed. No public paths, resource identities or historical readers changed.
The existing controller suite passed 49 tests in 2.715 seconds. The final focused
matrix additionally covers 30 actual-command cases and ten actual `--reconcile`
resumes after lost CREATE/execute responses; it passed in 0.448 seconds.
Four transport/renamed-binding cases prove local failures before/after provider
invocation, preserved provider reason on simultaneous cleanup failure, and no
hardcoded workload in the shared sequence. Provider-CLI regression passed six
tests in 5.163 seconds. Fixture setup initially patched a function-local import
as a module attribute, then exhausted a two-result receipt stub on the second
invocation; both fixture defects were corrected without weakening assertions.
The feature failure-route and restart-route fixtures also passed with controlled
providers and no AWS observation. Registered selector/diagnostic batch closure
is pending; these direct results are exploratory local evidence, not
package qualification, live proof or full consolidation completion.

### B11 incident executor retirement (2026-11-15; verification in progress)

The two incident modules mix historical readers with live one-off executors.
`image-delivery-repair.completed_bootstrap_controller` is consumed by task
completion and acceptance; its exact packet/completion pins must remain.
`recovery_label` is still called in task preparation and checks the original
failure/reservation plus completed endpoint-repair receipt. Its incident launch
selection cannot simply disappear without migrating that caller and the
acceptance label reader. The endpoint repair's `prepare/current/change_shape/
reviewed/submit/run` chain is otherwise owned by its direct CLI and fixture,
not by ordinary deployment commands.

`source-transition.graph` is used by the retained receipt validator, so it is
historical compatibility, not dead execution code. Its `controller/historical/
compatible/validate/read/original_receipt/legacy_context` consumers include
task completion, restore, failure alignment and acceptance. The `inventory/
retain/gates/change/run` chain implements the particular stopped-source UPDATE;
direct fixture calls also use `gates` to synthesize old receipt proof. Retiring
that executor requires migrating those fixtures to independent historical
construction, not weakening or deleting retained-proof assertions.

The remaining incident-specific preflight, label, acceptance refresh and cleanup
selectors are active in task/restore paths and need a separate reader-versus-new-
execution disposition. The AWS operational-realization applicability standard
still describes the bounded repair authority; update its applicable current
instructions alongside retirement while retaining historical context. Preserve
canonical file paths and accepted bytes; this is not authority for an uncommitted
path migration or AWS operation.

First retirement slice: remove the endpoint repair's executor and its exclusive
writer, retain its current canonical module and historical receipt/label readers.
The former CLI must return the finite `image-repair-executor-retired` condition,
`verdict: blocked`, `effect: not-started`, and exit 1 for every invocation without
constructing a provider, reading CLI-supplied paths or retaining any new evidence.
Its fixture must independently create historical inputs, keep source-template
and reader rejection assertions, and prove old CLI modes cannot invoke effects.
Delete obsolete executor-only tests together with that implementation; their
passing results must not be reported as current repair capability. Remaining
incident launch selectors and the source-transition executor remain pending.

The matching source-transition retirement uses
`source-transition-executor-retired` with the same blocked/not-started/exit-1
contract. Remove its provider inventory, writer, gate producer, change review,
UPDATE coordinator and execution-only program pins. Keep the exact graph and
typed readers used to validate historical evidence. Rebuild fixture gate input
through the generic test gate owner, not the removed incident producer; retain
all resource/source/token/pin rejection checks and actual historical read tests.

The retained preflight/refresh/cleanup selectors are read-only compatibility
for the completed incident identity, not future-feature configuration. Keep
their exact custody checks for original-attempt reconciliation, but require a
validated existing reservation before the task, clone or restore-reader route
can execute with that retired proof label. A missing reservation must return
`incident-proof-new-attempt-retired` before enabling provider mutation or
reserving work. Other proof labels retain the ordinary route. Actual-caller
fixtures must prove new attempts are rejected and original reserved attempts
remain reconcilable; historical acceptance is checked without AWS.

Both obsolete executor chains are now removed in place. Their six-mode/invalid-
argument CLI fixtures return finite retired reports without provider creation,
path reads or evidence writes. The endpoint fixture passed in 0.272 seconds;
the source-transition fixture passed in 0.496 seconds after correcting its
generic fixture gate cutoff to stop at controlled execution. Actual full
file-backed historical validation remains exercised, not mocked. Independent
sub-agent review found no blocking correction in this first retirement slice.
The original feature current release still validates offline with
`current_readiness: false`, and the acceptance route/source/aggregate fixtures
passed. The task/clone/restore-reader original-reservation restriction is now
implemented; its connected actual-caller checks are running. No AWS was called.

Those connected checks are now terminal: task-route and the full connected
credential/snapshot/restore fixture passed, including rejection of a new
task/clone/restore-reader under the retired identity and reconciliation of the
actual lost original submissions without another effect. Test/controller
metadata was subsequently aligned; source-matched registered batch closure
remains pending. All four incident executor files remain at their canonical
paths with original typed history readers where required. Their current diff
removes 479 lines and adds 51 lines (net 428 fewer across those four files only);
this is not a whole-consolidation size claim.

The B08 incident-only administrator observation/recovery JavaScript programs
have no ordinary consumer after the source-transition executor removal; only
their fixtures and historical governance reference their paths. Retire their
executable SQL/token/credential paths in place too, retaining canonical files
and original Git/evidence history. They must report their own finite
`administrator-observation-retired` or `administrator-recovery-retired`
condition, blocked/not-started, exit 1, without imports, environment reads,
network or database access. Replace obsolete repair simulations with VM
effect sentinels and actual Node CLI refusal tests. Historical recovery-result
hash readers remain untouched.

Both administrator retirement fixtures passed, including real Node CLI exit 1
and exact finite report plus VM import/environment access sentinels, in
0.455 and 0.437 seconds. Their obsolete SQL recovery simulations were removed
with the retired bodies; no result is claimed as current database capability.

- Do not tear down, merge or rename AWS resources to consolidate source code.
- Preserve the two current accepted-release references and immutable evidence.
  Old receipts must remain readable without regenerating, rewriting or
  re-performing their provider operations.
- Preserve workload/database isolation, least privilege, immutable image
  identity, explicit operation ownership, interruption reconciliation and the
  rule against replaying uncertain mutations.
- Keep feature semantics in app code, feature migrations and feature proof
  assertions. Do not absorb business behaviour into the deployment controller.
- Keep unrelated staging, design-system, education and product code unchanged.
- Treat the original entity-smoke plan as historical context for the accepted
  implementation; do not rewrite it to suggest consolidation already happened.

## Consolidation approach

Use the current lifecycle owners. Separate validated workload facts from the
mechanics consuming them. Reuse existing modules before adding any new shared
module; introduce one only when the two actual consumers demonstrate a common
responsibility. No new deployment framework, scheduler, plugin system or
parallel execution journal is required by this plan.

For each operation, preserve both public callers initially, replace their
duplicated internals with one implementation, prove both callers and then
remove redundant internals. A wrapper is acceptable temporarily; two live
implementations hidden behind a wrapper are not consolidation.

Do not simply replace every hardcoded string with an unrestricted argument.
Validate the workload binding and retain resource ownership checks. Separate
configuration differences from differences in supported operations, such as
first-release recovery versus rollback to an accepted predecessor.

## First implementation slice

Inventory A04 confirms repeated payload assembly. Start here because it is a
complete local operation, addresses the original missing-wrapper class of
failure, and can prove reuse without touching provider execution or accepted
evidence. It is not a claim that packaging accounts for most of the excess code.

| Change | Exact owner and purpose |
| --- | --- |
| Add one common assembler | Proposed home: `scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/`. Separate the assembly implementation and its focused test; no new framework or CLI registry. Confirm module placement under the existing package owner when implementing. |
| Update baseline caller | `scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs` becomes a thin binding/diagnostic adapter. Retain `runtime-contract.mjs` as the baseline entrypoint/wrapper policy and `verify-runtime.mjs` as its independent output check. |
| Update feature caller | `scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs` supplies its exports, JSON assets, wrapper policy, manifest name and diagnostics to the same assembler. Preserve its dry-run mode. |
| Update actual image consumers | Both `infra/04.deploy/03.product/image/{core-server-persistence,entity-smoke}/Dockerfile` files must copy the common module into the build context. Keep image identities, selected dependencies and runtime commands unchanged. |
| Update proof consumers | Baseline `smoke-test-core-server-persistence-image/payload-fixture-test.sh`, feature composition tests, relevant selector inputs and diagnostic review entries must include the extracted module. Audit copied-file fixtures, not just imports in the live checkout. |
| Remove superseded logic | Delete the two independent shim/manifest assembly loops from the callers in the same slice. Retain public entry paths as thin adapters so workflow callers do not change unnecessarily. |

The shared input describes compiled root, selected package exports/assets,
entrypoints, wrapper policy, output manifest and dry-run. Validate paths and
mapping completeness before writing. Share the write/check mechanics while
preserving the baseline's immediate-start wrappers and the feature's
import-safe wrappers with feature diagnostics. Do not silently standardise
those behaviours as a side effect of consolidation.

Leave dependency installation/copying, Docker invocation, publication workflow
guards, TypeScript application code, AWS templates and historical bootstrap
assembly outside this first slice. Both builders already have direct callers
and independent checks; the common assembler must not know either workload's
name or introduce a switch on `entity-smoke` versus `core-server-persistence`.

### First slice proof and stopping point

1. Characterise both current assemblers with controlled compiled payloads.
   Assert exported imports, wrapper behaviour, manifests and failure output.
2. Run the same cases through both thin adapters after extraction. Cover
   missing entrypoint/export, JSON asset handling, invalid/path-escaping input,
   dry-run without writes and safe partial-write diagnostics.
3. Exercise a differently named controlled workload through the common module.
   Only its input mapping may change; no third assembler implementation.
<!-- deterministic-check: allow reason="the existing selector and package owners execute these checks; this task plan records the required evidence and human review boundary, not a second test dispatcher" -->
4. Run the existing baseline payload regression and feature composition checks,
   with selector impact proving that editing the common module selects both
   consumers. Retain independent output checks so producer and test do not
   simply share the same mistaken expectation.
5. Qualify the affected actual images at the package boundary before treating
   the slice as package-ready. This is not permission to publish or deploy;
   local fixture passes alone do not establish image correctness.
6. Record before/after code and test counts, timings and remaining differences.
   Stop this slice with two adapters and one implementation, not three parallel
   implementations. Report the resulting source/package evidence separately.

## Subsequent consolidation slices

Use the inventory IDs to keep each change tied to inspected source. Split a
slice further when its behaviour comparison reveals distinct responsibilities;
do not turn this list into one giant rewrite.

| Order | Inventory | Work and completion boundary |
| --- | --- | --- |
| 2a — Package dependencies and build/publication | A05–A08 | Reuse lock-bound dependency handling with explicit roots, then common build/custody mechanics. Preserve baseline observability and feature publication reservation. Replace duplicated internals as callers migrate. |
| 2b — Provider and task evidence | A01–A02, B03–B04 | Extract shared AWS invocation/response predicates using existing provider helpers. Keep ownership/allowed-operation checks in bindings. Start with the exact one-off ECS override predicate; keep service-task observation separate. |
| 2c — Task submission and completion | B02, B05 | Compare attempt/admission/receipt contracts; use one reserved submission/observation path for administration, migration and verifier tasks. Both original routes must prove lost-response reconciliation without another launch. |
| 2d — Deployment and recovery | B01, B06–B10 | Share change-set execution, replacement, snapshot/restore and owned cleanup mechanics. Preserve distinct first-release stop/preserve and successor rollback policies. |
| 2e — Acceptance and incident retirement | B11, C01, C06–C08 | Consolidate collection around existing release succession. Keep original typed receipt readers; isolate historical pins from ordinary execution and remove obsolete repair effects only after references and compatibility pass. |
| 2f — Shared composition ownership | C03 | Move already-shared baseline-named configuration/role helpers only if the extraction removes accidental workload coupling. Preserve compile/image copy closure and public behaviour. |

Workload declarations, feature behaviour, accepted histories and baseline-only
capabilities in C02, C04, C05 and C07 remain. Do not merge AWS stacks to reduce
file count. Canonical path moves, if needed, belong to the affected slice and
must migrate its consumers; a mass directory reorganisation is not a precursor.

## Verification and removal

Each implementation slice follows the existing owning lifecycle workflow and
[diagnostic coverage workflow](../../../shared/workflows/verify-diagnostic-coverage.md).
Run focused tests for the changed common operation and both callers first;
use the existing test selector for affected integration coverage at the slice
boundary. Documentation inventory does not warrant image builds or AWS proof.

Required counterexamples for execution-related consolidation include wrong
workload/resource identity, mismatched package or source, failed provider
responses, interrupted execution and rejection of an uncertain replay. Tests
must distinguish controlled provider doubles from real AWS evidence.

Before deleting a superseded implementation, search executable imports,
wrappers, package commands, workflow/declaration references, selector units,
fixtures and diagnostic-review records. Migrate active callers; preserve
historical evidence paths or provide explicit read compatibility. Use the
existing [artifact migration workflow](../../../01.harness/workflows/migrate-artifact-paths.md)
when moving canonical paths.

Rollback of a source consolidation means restoring the previous controller
implementation through normal version control, not rolling back application
data or replaying AWS operations. No removal is authorised by an inventory row.

## Completion criteria

- Both current workloads use the same implementation for each operation
  classified as common, with differences expressed as validated inputs.
- Each removed implementation has no active caller; shared code has regression
  coverage through both routes. Report actual executable file/line changes,
  not a promised percentage reduction.
- Existing accepted records still validate with their original immutable
  identities. A new controller version does not silently rebind old evidence.
- A differently named workload of the same private ECS/PostgreSQL shape uses
  existing entry points with its own binding, package, migration and proof
  assertions, without feature-specific controller patches. Start with a
  controlled fixture, not a third permanent AWS stack.
- Measure focused test, package and release-step durations separately. Set
  performance targets from measurements; do not promise a release time from
  file-count reduction alone.
- Report local compatibility, package qualification and live proof separately.
  Acceptance of this cleanup cannot be inferred from the prior AWS proof.

## Governing sources

- [Lifecycle ownership](../../standards/lifecycle-stage-ownership.md)
- [Deployment artifact placement](../../standards/deployment-artifact-placement-and-naming.md)
- [Deploy workflow](../../50-deploy/workflows/review-and-execute-target-update.md)
- [Release observation and acceptance workflow](../../60-run/workflows/verify-accept-or-restore-release.md)
- [Original isolated feature plan](entity-smoke-core-platform.md)

## Implementation record — slice A04

### Consumer and diagnostic review before editing

- Shared owner: `40-package/prepare-runtime-payload/assemble.mjs`, a named
  JavaScript implementation, not a new public TypeScript package or mixed index.
  The public-module responsibility split applies; no Core contracts change.
- Two CLI adapters retain their arguments, workload mappings, success output,
  finite failure code/scope, package/export/entrypoint context and partial-write
  reporting. Baseline manifests precede wrappers and use pretty package JSON;
  feature wrappers precede its manifest and remain import-safe. Neither policy
  is silently standardised. Wrapper sources remain workload-owned inputs.
- Predicates: invalid CLI/mapping/path (`arguments`, no writes); absent compiled
  entrypoint (`compiled-entrypoint`); absent JS export/JSON source
  (`compiled-export`); directory/shim/asset/package-manifest/payload-manifest/
  wrapper I/O failures (their existing stages, possible earlier writes).
  Preserve existing `runtime-preparation-boundary-failed` envelopes, not raw
  filesystem exceptions or supplied roots. New malformed mapping/path inputs
  are rejected without reflecting their values. Native reasons remain unknown;
  extraction is not full diagnostic-vocabulary adoption.
- Connected consumers: both Dockerfiles; baseline independent payload verifier;
  baseline payload fixture; feature composition; bootstrap's existing direct
  preparation diagnostic fixture; selector inputs and review-ledger owners.
  Actual copied-script closures must include the shared implementation.
- Additional connected custody consumers found during review: both publication
  workflows and their exact qualification-command validators enumerate receipt
  inputs. Include the extracted assembler in those future qualification inputs;
  prove omitted-input rejection with each existing workflow fixture. This changes
  no publication authority, runner ordering, accepted receipt or AWS operation.
- Planned proof: controlled real CLI fixtures for both mappings, exact generated
  bytes, wrapper execution versus import, manifest membership, JSON resolution,
  missing input/no-write, partial writes and canary exclusion; shared API cases
  for renamed workload, path escape/symlink rejection and write-free dry-run.
  Existing compiled baseline/feature checks retain independent runtime proof.
- Known package boundary: the feature builder requires clean committed source.
  This delegation permits no commit. Actual image qualification is pending that
  checkpoint; local fixture success will not be represented as package-ready.

### Changes delivered for parent review

Parent review completed on 2026-11-14: the parent inspected the shared body,
both adapter diffs, Docker/qualification-input changes, selector wiring and
counterexample, and workflow omission cases. No blocking correction identified.
A04 implementation inputs are frozen for registered focused and affected local
integration verification; package qualification remains separately pending.

- Added one `prepare-runtime-payload/assemble.mjs` implementation and migrated
  both `build-*/prepare-runtime.mjs` callers. Their independent filesystem
  assembly loops are removed; the public CLI paths and workload policies remain.
- Both Dockerfiles copy the shared module. The controlled fixture materialises
  those actual script-copy declarations; removing the copied common module
  makes the real preparer fail.
- Both publication workflows and their existing validators now bind the common
  module into future qualification receipts. Existing workflow fixtures reject
  omission of that exact input. No workflow was triggered.
- Added the `runtime-payload-assembly` registered local check, its required small
  Bash test dispatcher and `assemble-test.mjs`. The existing runner accepts Bash
  entrypoints, so it dispatches Node without any runner change. Shared-module
  changes select both workload consumers and the existing bootstrap diagnostic
  fixture consumer; declared fingerprints include the new source.
- Transferred the two preparer diagnostic reviews to their shared owner, retaining
  partial-adoption limitations; refreshed the changed validator/test reviews.
  This is not a claim that the legacy CLI envelopes became fully adopted Core
  diagnostic records.

### Verification observed so far

These are exploratory/source-bound results, not final registered integration
receipts. The parent owns the consolidated source review before that handoff.

| Observation | Result |
| --- | --- |
| Controlled assembler/real-CLI fixture | 19 cases passed in 28.434s; initial 18-case pass took 60.591s before batching import probes into one process per workload |
| Existing `runtime-preparation-diagnostic-test.py` | All six tests passed in 13.806s, preserving baseline exact failure envelopes |
| Fresh baseline TypeScript build → preparer → independent `verify-runtime.mjs` | Passed, `persistence-payload-imports-resolved`; duration not measured separately |
| Fresh feature TypeScript build → dependency-boundary → dry-run/preparer → `runtime-test.mjs` | Passed; 258-source compiled closure and controlled mounted HTTP/lifecycle behaviour; no real database/AWS claim |
| New actual-selector shared-input/fingerprint counterexample | Passed in 60.744s |
| Baseline qualification-route fixture | Passed, including omitted-common-input rejection and existing fail-stop cases |
| Feature workflow fixture | Passed, including omitted-common-input rejection; existing 25 workflow and seven foundation negative cases retained |
| Diagnostic structural adoption | Passed: zero findings, 712 discovered sources; retained legacy/partial debt is unchanged in meaning |
| Affected metadata headers / canonical command placement | Passed; the placement validator models command entrypoints, not imported `.mjs` libraries. The new Bash dispatcher has valid `40-package` placement; imported implementation ownership is source-reviewed |
| Full changed-path selector plan | `planned`, zero findings, 42.916s; no checks executed by that planning call; package/deploy/acceptance stages deferred |
| Protected current-reference hashes | Both exactly match the inventory baseline; no accepted-evidence files changed |

Corrections during development: the first selector fixture passed a parsed
catalog where its API requires a path; initial registration incorrectly used a
direct Node command instead of the runner's existing Bash-only contract. Both
were corrected and the real selection/fingerprint case now passes. The new
test-only source was removed from the runtime-adoption source list because the
existing scanner deliberately excludes fixtures. Metadata uses its required
`script` kind. No gates were weakened to accept these mistakes.

### Size and remaining work

Physical implementation lines (including metadata/comments): the two original
preparers totalled 171 lines (84 + 87); the adapters now total 111 (50 + 61),
plus 117 lines in the shared implementation: **228, net +57**. Validation adds
path/collision/symlink protections, so this slice removes repeated mechanisms
but does not claim a net line reduction. The new fixture/dispatcher and selector
counterexamples are proof code, not a third production assembler.

Before closing A04: parent consolidated review; any required corrections; final
registered `runtime-payload-assembly`, `bootstrap-payload-regression`,
`persistence-payload-regression`, `entity-smoke-composition`,
`entity-smoke-publication-contract` and selector repository-contract proof;
then stable-input impact-selected local integration. The full impact report also
retains existing broader owners because the catalog/review ledger changed; they
are not waived by the focused passes above. Actual image qualification needs the
separately authorised committed checkpoint and remains pending.

No source was committed or pushed. No package was published, AWS command run,
resource modified, accepted record rewritten or unrelated lesson plan changed.

Next source slice after A04 review: A05 dependency assembly. Source comparison
shows that the feature's existing installed-lock resolver can be retained and
parameterised with explicit workload-owned roots. Baseline observability needs
its declared OpenTelemetry packages as well as PostgreSQL/RDS signing; dropping
the broad copied SDK/telemetry trees is not safe until both real image import
closures and package qualification prove those selected roots sufficient. No
A05 source changes have been made.

### Reopened A04 review — build-context admission

Further connected-consumer inspection found both `Dockerfile.dockerignore`
files default-deny the new shared assembler. Docker `COPY` declarations alone
do not admit that file to the build context; the earlier copied-script fixture
missed this boundary. Required correction: admit only the shared implementation
and its parent directory in both existing filters, make the fixture consume
those exact context exceptions, and prove removal of either exception prevents
the real copied preparer from running. This is a bounded assertion of the
repository's explicit allowlist, not a general Dockerignore interpreter.
Register both filters as fixture inputs and future qualification inputs, retain
the sensitive/generated exclusions, and require renewed parent review.
Runtime error contracts do not change; the missing build input would have
failed before the existing preparer could initialise its reporter.

The first final registered six-check run was cancelled after approximately
30 minutes on discovery of this required correction, before broad integration.
Its completed trusted receipts remain: `bootstrap-payload-regression` passed
in 23.584022s and `check-selection-repository-contracts` in 659.497481s.
`entity-smoke-composition` was interrupted during its controlled credential
fixture and is **not** a pass. No completed aggregate run report exists for
that cancelled batch. Its later units did not run. No source changes were made
while it ran, and no AWS operation was involved. The frozen changed-path plan
validated with zero findings in 89.521651s: 93 local check instances and 20
later-stage instances deferred. That was planning only, not execution proof.

The correction is now implemented in both filters, both workflow qualification
bindings and their exact validators, omission fixtures, and selector inputs.
The baseline qualification binding also now names its actual Dockerfile;
the feature binding already did. Existing sensitive/generated exclusions and
execution ordering are unchanged. The two validator diagnostic review hashes
were refreshed without changing their adoption status or retained limitations.

Correction checkpoint after interruption reconciliation:

- No processes from the cancelled batch or interrupted correction fixture
  remained. The interrupted fixture had no observed terminal result and is not
  counted as a pass.
- The replacement 23-case assembler/real-CLI run passed in **10.646s**, including
  both missing-context-exception cases for each workload.
- Both workflow suites passed with the additional omitted-context-input cases;
  their individual durations were not measured.
- Diagnostic structural adoption passed with zero findings: 712 discovered,
  134 adopted, 446 reviewed partial/support and 132 retained legacy sources.
- `git diff --check` passed. No aggregate final-run report or image qualification
  is claimed. Renewed parent review precedes final registered verification.

A05 remains comparison only: no dependency-assembler source has been changed.
No commits, publication, AWS calls or accepted-reference changes were made.

Renewed parent review completed on 2026-11-14: both exact context allowlists,
copied-preparer admission/omission assertions, qualification bindings, selector
inputs and this correction record were inspected with no blocking correction.
A04 inputs are frozen again for registered focused verification. Only completed,
input-matching receipts may be reused; the cancelled batch remains incomplete.

### Registered A04 result and remaining recovery binding

The six-check run completed in 834.665s with five passes and one failure. Its
retained report is
`.cache/test-runs/20261114T211150Z-5517e89983bd4c6d9b5aa8dca48c7ce9/report.json`.
Passed: bootstrap payload 23.223s, selector repository contracts 450.124s,
feature composition 260.646s, feature publication 1.141s and shared assembler
11.541s. Baseline persistence payload failed in 35.140s. This is requested-check
evidence, not full impact integration or package qualification.

A direct rerun of only the failed fixture established that compiled imports,
all broken-payload cases, package-stage gates and workflow qualification passed.
The final `local-public-recovery-test.py` rejected the old exact Dockerfile pin
in `qualify-local-public-images.sh` with
`local-public-recovery-owner-review-required`. This additional connected
consumer was missed in A04. The correction refreshes only that reviewed-byte
binding to the Dockerfile already inspected by the parent; it does not relax
owner checks, select another registry, alter engine/credential isolation or
execute Docker. Existing changed-owner/private-image cases remain mandatory.
The wrapper's existing report schema/code and operation effects are preserved;
its diagnostic review hash must follow the pin edit. The bounded recovery
fixture and affected registered persistence check must pass before closure.

After the pin correction, the existing bounded recovery fixture passed all
45 cases with zero real Docker calls, unchanged original configuration and
successful temporary cleanup. Diagnostic structural adoption passed with zero
findings; affected metadata and `git diff --check` passed. Parent review of
this narrow consumer correction and the registered persistence rerun remain
pending. The five successful registered receipts are retained for matching
reuse; no entire-suite replay is assumed necessary.

Parent reviewed the recovery correction on 2026-11-14: Dockerfile SHA-256
`644fe806077b29c4469df70e3828f04685d8263fbb9087bf8a3169166509e733`
matches its shared-assembler COPY change; wrapper changes are only metadata
and that pin, and its reviewed source hash matches. No blocking correction.
Run the affected registered persistence check next. Parent also accepted
stable-batch verification under the change-completion standard: keep per-slice
source reviews and focused checks, and perform full affected integration after
the connected package slices are implemented, reviewed and frozen. This
replaces broad A04-first sequencing without waiving integration or actual-image
qualification. No declaration-derived mapping redesign is added to this plan.

The affected registered persistence rerun passed in 28.587s (54.444s total),
with zero findings. Report:
`.cache/test-runs/20261114T215942Z-06feabc5a0bc4506884f0ba76d08f232/report.json`.
Prior successful receipts remain retained, subject to matching input identity.
A04 source review and focused evidence are established; full impact integration
and actual image qualification are still outstanding at their agreed boundaries.

## Implementation record — slice A05

### Bounded consumers and compatibility before editing

Move the feature's existing installed-lock resolver once to the thematic
`40-package/prepare-runtime-dependencies/` owner. Bind explicit roots, report
schema and error code in two thin callers. This is a small source-owned binding,
not a workload registry or runtime-selectable package list. Preserve feature
`dependencyClosure(repository)` and `prepareDependencies(repository,
destination, dryRun)` exports, its result schema and exact failure envelope.
Baseline selects `pg`, `@aws-sdk/rds-signer` and its four declared OpenTelemetry
roots: API, OTLP metric exporter, resources and SDK metrics. Feature retains its
original two roots. No upgrades, lockfile changes or changes to runtime identity.

Both Dockerfiles must copy the shared resolver and their binding, and both
default-deny context filters must admit the exact shared module. Replace the
baseline manual driver/SDK/telemetry copying with the same resolver, retaining
its independent import verifier. Future qualification input lists, their exact
workflow validators and omission cases must bind both the common resolver and
caller. Refresh the baseline public-recovery Dockerfile pin only after review
of the changed package mechanism. Keep historical receipts unchanged.

Extend existing baseline payload and feature composition fixtures to use their
copied external dependency closure instead of the checkout's `node_modules`.
Keep existing missing-dependency negatives and independent runtime imports.
The focused shared fixture must prove both actual copied CLI closures, expected
root membership, nested version resolution, exclusion of unrelated packages,
dry-run, missing-context failure and a renamed binding with the same resolver.
Retain the existing feature resolver's optional/peer, lock mismatch, symlink,
destination-overlap and diagnostic-canary cases. Register the new focused unit
and both consumers/container obligations in the existing selector; extend the
real selection/fingerprint counterexample, not a separate registry.

### Diagnostic predicate inventory

| Boundary | Preserved observation and reporting | Planned proof |
| --- | --- | --- |
| Installed source/lock | Reject missing/unreadable or malformed manifests, unsupported lock structure, mismatched installed versions, missing required edges, malformed dependency maps and symlinks before copying. Optional absent edges stay absent. Unknown native source failures remain `source/unavailable`, not invented causes. | Existing feature dependency fixture plus both real caller bindings |
| Workload root binding | Nonempty source-owned package-name roots; reject malformed roots before writes. No workload-name branch or arbitrary runtime selector. | Renamed common fixture and invalid-root counterexamples |
| Destination | Existing/overlapping destination or symlink ancestor rejects before writes; never merge into a package tree. | Retained overlap/dangling-symlink cases |
| Copy | Keep nested installed layout; conservative `earlier-writes-possible` after copying starts. No retry, atomicity or source-integrity claim. | Nested actual Node resolution; retain existing mid-copy/concurrency proof limitations |
| CLI/report | Feature keeps `ENTITY_SMOKE_DEPENDENCIES_NOT_PREPARED` and `deploy/entity-smoke-dependencies/v1`. Baseline binding owns `PERSISTENCE_DEPENDENCIES_NOT_PREPARED` and `deploy/core-server-persistence-dependencies/v1`. Fixed phase/reason/effect only; never supplied paths, parser text or private manifest content. The common library preserves known failures to the bound reporter. | Exact actual CLI report with sensitive canaries; malformed arguments/no writes |
| Package consumers | Missing copied helper fails before binding initialisation, not successful preparation. Qualification omission fails its existing owner. Compiled imports must resolve from the selected copied dependencies, not checkout fallback. | Docker-copy/context omissions; workflow input omissions; existing compiled payload/composition checks |

The shared module's implementation and CLI reporter are private tooling, not
a new Core diagnostic vocabulary or public index containing logic. Workload
bindings remain small; the existing partial resolver review transfers with the
algorithm and retains its explicit mid-copy/concurrency/image-proof debt.

### A05 implementation and exploratory evidence

Both Dockerfiles now copy and invoke the same resolver with separate root/report
bindings. Baseline's three manual mkdir/copy commands (including entire SDK and
telemetry namespaces) are replaced by its one bound resolver invocation. The
feature's former resolver body has been removed from its caller. Both default-deny
context filters, future qualification input lists, exact workflow validators and
input-omission fixtures include the new shared source and applicable binding.
Existing compiled baseline and feature fixtures now use their selected external
dependency copies rather than the checkout's `node_modules`.

The new `runtime-dependency-assembly` selector unit runs the shared fixture and
retained feature fixture. Impact/fingerprint inputs cover both actual Docker
script closures, context filters, and both compiled consumers. The existing
actual selector counterexample now checks both shared payload and dependency
sources. No selector algorithm, runtime package version or image identity changed.

| Exploratory check before parent review | Result and limits |
| --- | --- |
| Common dependency dispatcher | Passed 12 Node tests in 2.675s, including the retained 14-case feature fixture; actual copied CLI/context omissions, nested resolution, root selection, canary failures and renamed binding |
| Retained feature dependency fixture separately | Passed in 0.748s |
| Both publication workflow omission suites | Passed; controlled workflow/command checks, not image publication |
| Freshly compiled baseline payload | Passed independent import verification through its selected 52-package copy; no repository `NODE_PATH` fallback |
| Freshly compiled feature payload | Passed actual runtime fixture through its selected 40-package copy; not the complete composition suite or live database proof |
| Actual selector/fingerprint counterexample | Passed one method covering both shared sources in 74.372s |
| Diagnostic coverage | Passed: 715 discovered, 134 adopted, 449 partial/support, 132 retained legacy; zero findings |
| Seven affected implementation/fixture metadata headers; diff whitespace | Passed |

Physical implementation accounting (including metadata/comments): the former
140-line feature resolver is replaced by one 148-line common implementation and
27-/28-line feature/baseline bindings: 203 lines, net +63 across those scripts.
Baseline removes three manual dependency-copy lines in favour of one call; Docker
COPY/context/custody wiring and tests are additional. The new focused fixture and
dispatcher add 129 lines. This consolidates the dependency algorithm and removes
broad namespace copying; it is not a claim of total line-count reduction.

At the initial A05 checkpoint the baseline recovery wrapper deliberately retained
the A04 pin pending review. The A05 Dockerfile hash is
`aa97b62bd238fc604d55bbc48a1d6fc6ffcd67635822d2976da17def85e58908`.
Refresh that exact binding only after review of the changed dependency mechanism,
then run affected registered focused checks. Full impact integration is batched
after connected package slices freeze, as recorded above. Actual image
qualification remains pending an authorised committed checkpoint. No commit,
publication, AWS call, accepted evidence or resource mutation occurred.

Parent subsequently reviewed the complete resolver/bindings, dependency fixtures,
Docker COPY/context changes, isolated compiled consumers, qualification bindings
and selector changes with no blocking correction. The exact Dockerfile hash above
was confirmed. The recovery wrapper's pin is now refreshed without changing any
other admission predicate; its diagnostic source hash is
`dd3aec40aa2ad5355c0dc37a3137c5707c2c489e25832b1ce7fbd4d1c6afaf69`.
The bounded recovery fixture and affected registered focused checks are running
on this reviewed source. Results below must distinguish them from full impact
integration and actual image qualification, which remain pending.

### A05 registered result and fixture-resolution correction

The six-check run completed in 562.301s, with five passes and one failure:
`.cache/test-runs/20261114T225150Z-422809a67c054452b2c5d4f30d07f2d5/report.json`.

| Registered check | Status | Execution seconds |
| --- | --- | ---: |
| `check-selection-repository-contracts` | Passed | 445.782943 |
| `entity-smoke-composition` | Failed | 15.829563 |
| `entity-smoke-publication-contract` | Passed | 1.008871 |
| `persistence-payload-regression` | Passed | 42.108462 |
| `runtime-dependency-assembly` | Passed | 4.144920 |
| `runtime-payload-assembly` | Passed | 10.216237 |

The independently invoked 45-case local-public recovery fixture also passed,
with zero real Docker calls and unchanged stored configuration. Both accepted
reference hashes still match the original inventory.

Direct composition diagnosis identified a missed test consumer: `preflight-test.mjs`
anchored `createRequire` to its repository file, so it replaced checkout `pg.Pool`
while the compiled adapter loaded the new isolated dependency copy. The expected
fake-success case instead returned `persistence.transport-unavailable`. The
preflight fixture now anchors resolution to its compiled payload, and asserts
that `pg` resolves inside the selected copy and is the exact module object loaded
by the compiled PostgreSQL connection adapter. No production behavior, resolver,
dependency root or image input changed in this correction.

A fresh compiled/copied payload running only that corrected preflight fixture
passed exploratorily. Its original transport, permission, cleanup and safe-error
assertions remain. Parent re-review and registered feature-composition rerun are
pending; the failed observation remains retained. The earlier selector receipt
is historical once this fixture or these plan results change, because its declared
inputs include all `scripts/04.deploy`, `.agentic` and `docs`. Its next full current
run belongs to the agreed frozen connected-package integration boundary; do not
silently reuse it as proof of the changed inputs. Other matching leaf receipts
remain eligible only through the existing selector's identity checks.

Parent reviewed the narrow preflight correction: compiled-root resolution,
selected-copy path assertion and actual adapter module-instance equality, with
the original permission/transport/cleanup assertions unchanged. No blocking
correction was identified. The registered composition rerun now follows on frozen
affected inputs. Continue A06 after that check passes; broad integration and
actual image qualification remain pending as agreed.

The corrected registered composition rerun passed: 467.132751s execution,
493.626564s total, retained at
`.cache/test-runs/20261114T230951Z-f443b6e8aac04d73b2e8fca63d145805/report.json`.
The failed earlier observation is not removed. This establishes the focused
A05 correction, not complete affected integration or actual image qualification.

### Connected next-slice comparison while A05 awaits review

A06's two builders both perform declaration coverage, delivery inventory,
health/recovery declaration validation and runnable-program validation before
workload-specific tests and Docker build. Their differences are deliberate
compatibility inputs, not permission to choose one caller's policy for both:

| Boundary | Baseline | Feature |
| --- | --- | --- |
| CLI/source | Nonempty optional tag; no clean-source check in this wrapper; HEAD observed for build labels/argument | Closed feature-tag syntax, non-session clean committed source, exact 40-character SHA |
| Inventory | `python3` | `python3 -B` |
| Additional checks | PostgreSQL diagnostics, integration and composition | Diagnostic catalog, app contract/use cases and feature composition |
| Engine observation | Direct `docker info` | `timeout 30 docker info` |
| Build options | Existing default build options | Explicit load, linux/amd64 and provenance=false |
| Failures/output | Existing persistence diagnostic codes and human build line | Existing feature diagnostic codes and explicit built-not-qualified result |

Extraction must preserve these differences, fail-stop order and argument
boundaries. Both workflow validators pin the executable builder body: baseline
`BUILDER_PREAMBLE`/`DOCKER_BOUNDARY`, feature `BUILD_BODY` through existing
`workflow_guard.protected_script`. Any common build helper must be validated and
qualification-input-bound too; moving gates behind an unchecked source/import
would weaken the route. Baseline `qualification-route-test.py` copies the actual
builder and diagnostic helper, exercises each required failure, and rejects
conditional/uncalled/late/suppressed gates. Its copied closure must migrate with
the helper. Feature `workflow-test.py` checks exact builder and qualifier bodies.
The public-image recovery wrapper also pins the baseline builder bytes. These
are connected A05 review inputs, so no A06 source edit has been made while the
A05 candidate is awaiting review.

B03 comparison confirms that baseline `ecs-task-evidence.py`'s complete override
predicate and feature `task-control.py::exact_task`'s override portion agree:
only one expected container, exact environment names/values, no extra keys or
command/resource/role override, and only absent/empty inference defaults.
Feature ARN/definition/operation checks must remain outside that shared predicate.
The baseline path is a live compatibility adapter for migration, verifier and
restore callers, not a file safe to delete. Its copied consumers include
`verify-candidate/operation-test.py` and the baseline package payload fixture;
those must receive any shared helper in the same slice. This comparison is not
implementation or a task-submission/recovery proof.

### A06 implementation checkpoint — shared candidate build mechanics

The two existing builders now source
`scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh`.
It owns only the four common prechecks and Docker argument assembly. Caller
bindings retain the compatibility differences listed above, including baseline's
two separate HEAD observations and feature's one validated committed revision.
No workload dispatch table, new CLI or deployment authority is introduced.
This host-only helper is not copied into runtime images.

Both existing workflow validators protect the common executable body through
`package-custody-receipt/workflow_guard.py`; both future qualification commands
bind its source. Existing workflow fixtures reject helper/input omission,
suppressed or skipped checks and changed build argument forwarding. The existing
baseline qualification-route fixture copies the actual helper and executes both
actual builders with controlled commands: exact Docker argv, independent gate
ordering, each failure boundary, safe build failure/status, feature source/tag
guards, a workspace path containing spaces, and a differently named binding.
These are local protocol observations, not real Docker or provider proof.

The existing selector registers both package consumers, local publication and
custody checks for common-helper changes. Its fingerprint counterexample now
covers this input too. The recovery fixture copies the new helper and moves its
private-build-argument/secret mutations to the extracted command; it also rejects
changed and missing helper bytes. The recovery wrapper's strict pin remains
unchanged pending parent review, so final recovery verification is not yet valid.

Parent review requested against baseline builder
`9cd4d39daa002180b197c0da56c808ca1143592f8341442e0fbab6a0820437d1`
and helper
`30baed94c4deb5d2a5c378b6afa34d0de2857e42eab37142705095a5c978824c`.
On approval, refresh that exact builder pin, add the helper to the same reviewed
closure, retain the unchanged core recovery branch, and run the affected
registered focused checks. Broad integration stays batched; actual image
qualification still needs an authorised committed checkpoint.

Exploratory actual-builder and both workflow suites pass. Diagnostic coverage
initially found the changed selector-test hash stale; its existing review binding
was refreshed, not exempted. Final diagnostic/metadata and bounded selector
results are still being collected. A06 production scripts total 117 lines versus
the original 93 (32/49-line bindings plus 36-line helper): **net +24 lines**.
The removed duplication is the precheck/build responsibility, not a claimed
overall line reduction. Tests, custody guards and documentation are additional.

The exploratory shared-source selector/fingerprint method passed in 100.837s.
Diagnostic coverage passed with 716 discovered sources, 134 adopted, 450
partial/support and 132 legacy; zero findings. Ten affected metadata headers
passed. A subsequent copied-consumer audit added the common helper to the
baseline payload's declaration/health fixture and the custody suite's two
synthetic repositories. Original assertions remain intact. The bounded custody
child-failure method passed in 1.137s and actual publication-CLI substitution
method passed in 44.805s. These edits do not change the reviewed production
hashes. The baseline payload fixture still awaits its complete registered run
after the reviewed recovery pin is updated.

### Independent next-slice findings during A06 review

Parent review completed: full shared helper, both caller diffs, both workflow
guards and qualification bindings, actual-builder/omission/substitution fixtures,
recovery negatives, copied custody/payload roots, selector inputs and diagnostic
limitations. No blocking correction was identified. The independently confirmed
builder/helper hashes above are now pinned in the existing recovery owner;
the core recovery branch remains unchanged. Bounded recovery and affected
registered focused verification follow; complete integration and actual images
remain pending. B03 follows passing focused checks. Parent agrees A07 remains
compared/not-consolidated rather than forcing a cross-language micro-framework.

A07 already delegates cleanup to the shared Docker cleanup owner. Provisioning
is not otherwise equivalent: baseline uses PostgreSQL16, restricted CREATEROLE
administration and a published host port; feature uses PostgreSQL18.3 with an
explicit fixture-only superuser, internal network, data/restore volumes and a
fsynced cleanup reservation. Their TLS SANs differ, and retained rollback is a
third live TLS setup consumer. Do not merge these policies or introduce a
cross-language TLS mini-framework simply to hide three argument lists. A07 is
compared, not complete. The next proposed small implementation is B03's exact
ECS override predicate, retaining existing caller identity checks.

B03 also needs source-identity and copied-consumer coverage, not only moving the
predicate: feature controller digests currently include their local Python
directory and explicit shared dependencies; an extracted provider helper must
be included in those identities. Existing controller-only repair allowances
must not silently expand to every new shared file. The baseline evidence path
remains a compatibility adapter for migration/verification/restore and accepted
history; both copied fixture roots include its imported helper in their test setup.

B04 comparison found an existing latency mismatch in feature
`script.py::local_checks`: its controller subprocess timeout is 180 seconds for
composition plus secret checks, while observed fresh composition took 467s
(earlier A04 260s). No timeout or execution policy was changed here. Retain this
as a later consumer-boundary issue rather than claiming the local passes prove
the live controller can complete cold verification within its current bound.

### A06 focused verification completed

Retained report: `.cache/test-runs/20261114T233135Z-8744ffc253dc4a568183c5ab4a57e8ab/report.json`.
All three requested checks passed: entity-smoke-publication-contract 1.276955s,
package-custody-regression 143.975109s, persistence-payload-regression 30.556510s.
Total elapsed 206.423140s; command execution 175.808574s. The preceding bounded
recovery fixture passed all 47 cases without real Docker calls or changed stored
configuration. Diagnostic coverage passed after reviewed pin refresh. This is
explicit focused evidence, not full affected integration or actual image proof.

### B03 implementation checkpoint — shared exact ECS overrides

The existing AWS `response.py` now owns the unchanged baseline predicate.
Baseline `ecs-task-evidence.py` is a compatibility import at its historical path;
feature `task-control.py::exact_task` delegates only override comparison. Feature
task ARN, task-definition and startedBy checks and its safe mismatch code remain
unchanged. No attempt journal, request admission, provider call, retry policy or
accepted history was merged. No new implementation module was created.

Feature controller source identity and its existing bounded repair list already
include `response.py`; no authority extension was needed. The copied baseline
payload fixture now includes that owner; its operation fixture already did.
Both composition/payload check input closures include the shared predicate and
compatibility adapter. Selector rules retain existing response consumers and add
both migrated consumers; independent omission/fingerprint cases cover them.

The existing feature task-control fixture constructs renamed-container provider
observations independently of the production override builder and exercises both
actual bindings. Missing/empty inert defaults and reordered/empty environments
pass; malformed rows, duplicate keys, extra rows, altered values, extra containers,
unknown consequential overrides and nonempty inference overrides reject. Existing
identity/no-replay tests remain. Diagnostic reviews preserve safe failure codes
and existing legacy limitations. Production files total 379 lines versus 369
before this slice, net +10 including compatibility imports/metadata; this removes
duplicate comparison responsibility, not net physical lines.

Exploratory proof: task-control and unchanged task-runner fixtures passed;
baseline copied-root operation suite passed 19 tests in 25.780s. Diagnostic
coverage passed (716 discovered, 134 adopted, 451 partial/support, 131 legacy;
zero findings); diff whitespace check passed. The initial focused selector method
failed in 63.005s because this slice duplicated its diagnostic check binding;
parent review independently caught the same duplicate. After removing it the
method passed in 63.677s (session 42796). Parent final source review covered both
actual bindings, independent negatives, copied-consumer closure, selector
fingerprints and diagnostic transfer; no required correction remains. Registered
focused composition/provider/payload verification follows on frozen inputs.
Full affected integration and actual image qualification remain pending. No
cloud/image work was performed.

### B03 focused proof completed

Parent final review and all three registered focused checks passed. Retained
report: `.cache/test-runs/20261114T234403Z-5dc6b7ab3f1945f18a8d10bd180af9b7/report.json`.
Composition 251.354909s; persistence payload 33.667404s; persistence provider
35.600840s. Total 345.648474s; command execution 320.623153s. This is source-bound
local evidence for B03, not package/live acceptance. B04 changes those connected
inputs; do not reuse the B03 receipt as proof of the later implementation.

### B04 implementation checkpoint — one-shot provider invocation

One private `shared/provider-adapters/aws/cli.py` now owns single-process capture,
finite process/service/response classification and JSON decoding. It delegates
service codes to existing `response.py`, dynamically looks up the process runner,
and performs exactly one invocation. It grants no permission and contains no
retry loop or workload-name dispatch. All nine inventoried AWS wrappers now use
it; old duplicated subprocess/JSON bodies are removed. Existing generic non-AWS
alignment command execution remains in its owner.

| Actual caller | Preserved invocation and response policy |
| --- | --- |
| Persistence prepare-candidate | Inventory preflight; CLI 5/20s, process 30s; explicit pager environment; generic JSON; whitespace-empty accepted; finite tuple |
| Persistence run-migration and verify-candidate | CLI 5/20s, process 30s; pager environment; generic JSON; only empty-string accepted; finite tuple; no implicit retry |
| Persistence retire-failed-candidate | CLI 5/20s, process 30s; environment omitted; generic JSON; whitespace-empty accepted; finite tuple |
| Persistence RDS-log-export reconciliation | No CLI timeout flags, process 30s/check=False; environment omitted; empty body rejected; generic nonzero and invalid-JSON codes; existing uncaught process UnicodeError preserved |
| Persistence acceptance collector | Process 30s/check=False/pager environment; dict-only JSON; empty-string accepted; original EvidenceFailure vocabulary and original cause chaining |
| Persistence observability rehearsal | Same process/JSON policy as collector; distinct RehearsalFailure vocabulary and cause chaining |
| Feature alignment | READS admission first; CLI 5/20s, process 30s; exact pager/retry/Python environment; empty body rejected; dict-only; original generic command/observation errors |
| Feature infrastructure Provider and inherited routes | Closed capabilities and effect/prewrite checks; global signing endpoints; CLI 10/20s/process 40s; exact environment; whitespace-empty/dict-only; three read-only process/exact-endpoint timeout attempts but one mutation; original ResourceMissing and finite errors |

Source identity includes the new helper and its response dependency. The bounded
controller-only repair set adds exactly `cli.py`, with accepted/rejected real-Git
fixture cases, not a directory wildcard. Baseline copied verifier, provider CLI
and payload roots include both files. Restore fixture now imports the actual
response owner rather than the infrastructure module's removed internal alias.
No accepted history, current release reference, AWS resource or workload identity
was changed. Bootstrap/foundation wrappers outside these two routes are not
migrated; shared-consumer checks remain selected. Baseline create/deploy/restore
callers that already delegate to preparation retain that transitive path.

All ten existing checks whose declared input closures consume these callers
now cover the CLI/classification inputs; existing unaffected provider consumers
remain selected. A new existing-suite method checks actual selection, fingerprint
change and omission counterexamples. Diagnostic reviews retain caller codes,
original error chaining and legacy limitations; private helper errors are not
claimed to be complete Core diagnostic adoption.

The connected host local-check bound changes from 180 to 900 seconds because
cold composition measured 467s (B03 251s). The exact selector command still owns
trusted same-input receipt reuse and cold execution; no forced rerun or imported
report trust is introduced. Tests assert exact selected identities/options,
retained failure evidence, timeout-unavailable and unrelated-success rejection.
No provider/ECS timeout changes. This is a finite orchestration correction, not
a performance guarantee or a new per-check scheduler.

Exploratory evidence so far: independent seven-caller matrix passed 77 response/
error cases plus inventory rejection in 0.083s; existing copied provider suite
passed 5 tests in 5.311s; enhanced actual feature infrastructure and alignment
fixtures passed (sessions 15530/48164); eight metadata headers and whitespace
checks passed. Parent independently compared HEAD/current nine actual wrappers
across 105 mocked invocation/response/error cases; this remains exploratory, not
registered evidence. Final selector method passed in 68.657s (82429), diagnostic
coverage passed with 717 discovered/134 adopted/452 partial-support/131 legacy
and zero findings (22227), and copied verifier suite passed 19 tests in 26.080s
(69576). Parent final source review covered helper hash/partial diagnostic
classification, both shared dependencies, ten affected obligations, independent
fingerprint omission cases and copied roots. No required correction remains.
B04 source review and exploratory feedback are complete; final registered and
full affected integration remain pending for the connected batch. B02/B05
comparison proceeds without a new user approval.

Nine production wrappers plus the 78-line common helper total 4150 lines versus
4102, net +48; an additional two metadata relationship lines bind response.py to
its new consumer. This consolidates responsibility, not physical line count.
Complete affected integration and actual images remain pending. Per parent
sequencing, following connected provider/task slices use narrow exploratory
feedback and source review; final registered consumers run once that batch is
stable. No source-mismatched pass is reused and no external authority is added.

## B02/B05 connected execution comparison — in progress

The comparison includes four actual consumers, not two workload names:
baseline migration emits a client-token operation ID without durable reservation;
baseline administration has neither reservation nor startedBy/clientToken;
baseline verifier has a locked durable journal, initialization sentinel,
predecessor and retained-completion protocol; feature tasks have immutable
reservations plus preflight/unready admissions and retained proof. Historical
receipt readers and their schemas remain compatible.

Parent approved consolidating shared ECS submit/reconcile/observe mechanics and
reusing the existing verifier journal mechanics for new baseline executions.
New migration/administration executions will reserve before submission and
reconcile uncertainty without replay. Intentional subsequent execution must
bind an expected predecessor; administration's existing `--fresh` spelling will
require that binding rather than bypassing pending/uncertain state. No governed
caller currently supplies `--fresh`. The existing credential-lifecycle caller
does repeat revoke/restore transitions, so it must explicitly select a successor
after retained completion, as its health verifier already does. Actual-caller
tests must prove both duplicate/interrupted rejection and legitimate subsequent
transitions. These intentional new-execution changes are not claims that old
receipts already contain reservation evidence. B02 implementation and parent
source review are now complete; final registered batch remains pending. B05
ordering comparison remains open. No AWS task was authorised or launched.

### B02 caller mapping before acceptance-route migration

The parent re-reviewed the following mapping on 2026-11-15 after an automated
review correctly required it before changing declared phase arguments. No route
file was changed by the rejected attempt. These are current-proof phase callers,
not historical-only readers; each needs an explicit same-operation predecessor:

| Existing declared command | Administration operation | New input owner/name |
| --- | --- | --- |
| migration-state-observation | observe-migration-state | run-administration / migration_state_observation_predecessor |
| effective-privilege | prove-effective-privilege | run-administration / effective_privilege_predecessor |
| runtime-identity-initial-access | confirm-runtime-iam-access | run-administration / runtime_identity_initial_access_predecessor |
| credential-revocation | revoke-runtime | run-administration / credential_revocation_predecessor |
| credential-recovery | restore-runtime | run-administration / credential_recovery_predecessor |
| runtime-identity-access-route | confirm-runtime-iam-access | run-administration / runtime_identity_access_route_predecessor |

The last command shares the confirm-runtime-iam-access operation with the initial
access phase: it must consume that phase's completed operation ID when used
later, not reuse its result as new observation. All six use the existing route
identifier input type and resolver. Initial use supplies none; subsequent use
supplies the same operation's terminal report ID. An identical invocation
reconciles the same successor, never creates another task. Existing acceptance
input documents need the six added references when invoking the updated route;
old proof receipts, accepted records and read-only legacy reconciliation do not.
The route compiler probes real --validate-arguments parsers before effects;
the existing rehearsal builds predecessor values from declared input examples.
Actual-caller tests resolve all six commands and pass initial execution,
same-operation progression, exact retry, wrong predecessor and historical reuse.

Other mapped callers: the credential-lifecycle controller repeats revoke/restore
and now follows its existing verifier successor pattern; workflow examples cover
initial bootstrap/migration/grant and will explicitly document subsequent-use
predecessors. No normal caller supplies the old --fresh flag. That spelling now
requires an explicit predecessor. Historical receipt capture through
controller-fixtures.py and explicit --reconcile-task/--reconcile-operation remain
read-only; they neither require newly manufactured reservations nor become fresh
proof. Failed migration successors additionally require the existing separately
observed REPLAY_PERMITTED database receipt, bound to current definition/image,
post-failure time, deadline and immutable receipt hash.

### B02 source-review and exploratory checkpoint

One shared tasks.py owns submit/reconcile/describe/bounded polling; task_journal.py
extracts the existing verifier lock/atomic-write/predecessor protocol. Baseline
migration and administration now bind to it through task-operations.py; verifier
retains its original schema. Feature retains immutable AttemptStore and exact
preflight/unready admission but uses the same ECS mechanics. The independent
launch/search/poll loops and verifier journal internals were removed from callers.
No general scheduler, permission expansion or third task engine was introduced.

Parent review required and verified three corrections: preserve finite original
provider codes, treat post-submission identity/storage failures as uncertain,
and require the existing replay-permitted database observer after failed
migration. Tests initially exposed a wrong timestamp helper name, and the new
retention-fault case exposed a callback exception being swallowed by the old
receipt error boundary; both were corrected. New callback paths now retain
operation ID and uncertain outcome while legacy no-callback behavior stays.
Poll callers pass clocks explicitly and stop reading after the bounded deadline.

Exploratory results on 2026-11-15: verifier actual CLI/process suite 19 passed
in 26.792s; both feature task-control/runner fixtures passed; final baseline suite
11 passed in 1.475s including six declared phases, before-submit interruption,
lock contention, post-launch/receipt-pointer save failure, wrong observer
image/definition/provenance/time/deadline and no replay. Three retained legacy
administration/safe-log cases passed in 0.077s. The shared-owner selector method
passed in 210.490s across seven new sources, with independent omission/invalidation
counterexamples; that latency is measured feedback overhead, not deployment time.
One earlier direct invocation of a unittest module executed no tests and is not
counted. These are exploratory local results, not registered integration receipts.
The README skill guided the existing continuation guide; source review and all
relative links passed. Source-matched registered checks, complete integration
and image/live qualification remain pending. New shared production modules add
code as well as removing duplicate loops; no net reduction claim is made here.

## A08 parent-owned publication slice — source reviewed

The parent owns publication/custody source while this agent owns B02/B05 and the
shared selector/diagnostic records. The approved comparison proposes one AWS
ECR publication engine with static checked bindings for both workloads. Feature
reservation/result schemas, filenames, role, tag, configuration and safe errors
remain; baseline retains its repository/delivery role/tag and custody/scan
outputs while replacing inline publication with durable single-submit/reconcile
mechanics. Shared engine requirements cover exact qualification and remote
identity, durable reservation/invocation and finite failure output. No arbitrary
caller-selected module or provider authority is introduced.

The two workflow validators will use one reserved-publication guard; existing
`ecr_publication_contract.py` and bootstrap's current guard remain for that
unmigrated consumer. Proof uses actual adapters, a differently named binding,
missing/invalid binding before effects, protected role/repository routing,
lost-response/no-replay, remote digest/source mismatch and safe diagnostics.
Both workflow qualification closures and copied-consumer fixtures must migrate.
The placement checker has no provider-helper kind, so its lifecycle-command
placement check is inapplicable, not recorded as a passing placement verdict.
Source review is complete. Shared ecr_publication.py and both static publication
bindings replace the feature engine and baseline inline push loop; bootstrap's
old command contract remains for its unmigrated consumer. Parent implementation
and agent review covered exact identity, durable intent, one push, lost-response
reconciliation, remote mismatch, diagnostic collector failure and real safe
writer acceptance for both scopes. Publication fixture passes with both adapters
and a renamed binding; workflow/foundation/pipeline negatives pass (25/7/15).
Qualification workflow mutation method passed in 20.622s with twelve additional
baseline reservation/retention negatives. Selectors include shared engine,
baseline binding and real diagnostic writer/contracts. Partial diagnostic review
retains malformed/native-shape and filesystem limitations. Registered connected
verification and actual image/publication proof remain pending.

## B01 parent-owned CloudFormation slice — approved implementation scope

The parent owns the baseline create/deploy-candidate controllers, feature
deployment-control and the ResourceStore extraction; B02 task-control/journal
remains with this agent. Extract the existing immutable ResourceStore mechanics
to one shared owner with checked schema/id-prefix and caller-owned closed request
and path bindings. Preserve the feature reservation schema and filenames behind
its existing wrapper. One shared CloudFormation prepare/execute operation will
coordinate reservation, preconditions, single submission and caller-owned exact
resource/template/tag review and observation. This is not a registry or scheduler.

Migrate baseline CREATE/deploy-candidate and feature prepare/execute. Baseline
new executions gain durable fixed-name reservations and client tokens while
retaining digest-derived change-set names; repeats reconcile rather than submit
again. Historical read-only --reconcile remains usable without manufacturing a
new reservation. Preserve baseline NAMED_IAM/default rollback and diagnostics,
and feature IAM/DO_NOTHING/activation DisableRollback and lineage. Retain only
hashes and approved identities, never parameter values or endpoints, in the
shared store. Existing update/incident readers through prepare.observe_update
remain explicitly tracked for B07/B11; this bounded slice does not establish
their consolidation. No conflict with task source ownership was identified.
Initial CREATE/execute source implementation and agent review are complete.
The extracted resource_reservation.py and change_sets.py serve both routes;
baseline change-set-operations.py is a closed hash-only input binding. Default
CREATE binds Description to its durable token; default execute requires positive
root-stack event token lineage. Review caught a non-AVAILABLE branch incorrectly
using the legacy reader on first default execution; it now passes the reservation
and the independent concurrent-foreign-completion negative passes. Explicit
historical --reconcile remains unchanged. No reset or new-attempt policy was added.
Parent exploratory tests: full controller suite 43 passed in 2.347s before the
final extra negative; three corrected focused cases passed in 0.077s; both
feature resource/deployment fixtures passed in 1.367s. Independently constructed
old feature reservation bytes are reused unchanged. Exact source/repair closure,
selector inputs and partial diagnostic source bindings include both shared owners.
Registered integration and actual provider proof remain pending; six baseline
update/incident consumers still require their later B07/B11 disposition.

## B05 ordering comparison and B06 original-task replacement — source reviewed

B05 comparison distinguishes existing baseline declaration-driven sequence edges
from feature-specific prerequisite packets, physical definition identity,
admission/completion hashes, historical source transitions and activation
generations. Real-access preflight and expected-unready remain distinct policies.
Do not replace these with a second scheduler or a trivial timestamp wrapper;
complete the common ordering disposition with the later route/collector slice.

### B05/B08 comparison disposition — shared effects, distinct proof policies

Actual baseline orchestration is
`P60/rehearse-runtime-credential-lifecycle/script.py::{main,recover,healthy,administer,replace}`:
ready → revoke → replacement → unready → restore → replacement → ready → read.
The observability-pause variant stops after unready; the recovery continuation
first proves unready and never revokes again. `healthy` and `administer` select
explicit predecessor operations through B02; `replace` supplies the actual
administration receipt to B06. Neither replacement can reuse completed intent
as fresh proof. Existing result schemas and historical readers remain.

Feature `E60/credential-steps.py::{initial,prefix,prerequisites,replacement}` is
read-only prerequisite validation, not a subprocess orchestrator. It requires
initial restart and same-record/applied-history proof, then permission-state →
revoke → bounded unready → restore → one replacement → same-record read →
independent permissions. It checks original admission, physical definition,
retained plans/gates and chronology. It intentionally keeps the original service
through revoke/restore and replaces only after restoration. Common task effects
and replacement mechanics already use B02/B06; forcing the two sequences into a
single table would change behavior rather than remove duplicated machinery.

Baseline `acceptance-route-contract.yml::sequence` owns its exposed per-proof
edges, consumed by `P60/collect-acceptance-evidence/script.py::sequence_valid`.
Feature's route exposes one complete-proof and therefore no top-level edges;
`E60/acceptance-controls.py::validate_connections` validates internal task/control
edges and exact negative-revocation admission. Existing declaration/collector
owners remain authoritative. No second scheduler, generic timestamp wrapper or
weaker common readiness policy is introduced.

Proof references: `P60/task-operation-test.py` actual credential successor
caller; `P50/controller-regression.py` actual parent-to-child replacement
admissions and `test_credential_lifecycle_main_keeps_distinct_recovery_order`;
`P60/rehearse-runtime-credential-lifecycle/smoke-test.sh`; feature
`credential-route-test.py` staged route with premature restore, copied
revocation, missing journal, lost negative/replacement and fresh positive-read
counterexamples; `acceptance-aggregate-test.py` altered ordering/identity cases.
The added baseline main fixture covers each existing mode and failure at every
step (0.023 seconds, exploratory). Eleven actual baseline task-operation tests
passed in 0.735 seconds after B10 discovery reuse. Connected registered proof
remains pending. Historical administrator repair is B11 compatibility work.

Parent review read the actual baseline main/recovery sequence and feature
initial/prefix/replacement/prerequisite implementations, plus both collection
ordering validators. The comparison matches those sources. Keeping distinct
proof policies does not retain duplicate effectful machinery: shared B02/B06
owners execute the actual task and replacement operations.

B06 migrates the substantive original-task replacement operation. The baseline
currently prints an original ARN before StopTask but a normal repeat can select
the successor. The feature already reserves its original. Extend the existing
shared ECS task owner with reserve, fresh precondition, one original-only stop,
then caller-owned successor observation. Reuse ImmutableReservationStore through
a closed baseline replacement binding; retain one original/definition per
source/image before submission. Normal repeats observe that original, never
infer a new stop from the currently running task. There is no implicit reset or
new replacement after completion. The acceptance route has one baseline replacement
per candidate; its historical rehearsal uses the explicit capture reader.

Consumer correction before final freeze: the credential lifecycle also calls the
normal replacement command after revoke and restore. A release-only slot would
incorrectly suppress those necessary later replacements. Bind these calls to
their actual retained successful administration receipt using a closed optional
`--after-administration-receipt` input. Validate receipt integrity, owner, operation,
image, terminal result and evidence class; hash that immutable admission into the
slot. The parent passes the receipt produced by its immediately preceding
administration operation. Repeated same admission reobserves its original; a new
revoke/restore receipt identifies a distinct required replacement. No arbitrary
reset, current-task-derived slot or fabricated fresh proof is permitted. Test both
credential transitions through the actual parent/child calls, not only the store.

Keep feature operation-ID stop reasons, guarded provider capability, exact task
and successor time/health checks. Keep baseline literal historical stop reason,
600-second observation policy, image/source binding, exact receipt validation,
explicit reconciliation/capture readers and independently required record read.
Existing receipt schemas and accepted histories stay unchanged. The new baseline
intent is not completion or acceptance evidence. Shared mechanics grant no AWS
authority, retry or workload inference.

Diagnostic boundaries: preserve finite provider timeout/unavailable outcomes,
precondition rejection before submission, pending successor versus unknown
submission, exact original identity and retained receipt conflicts. Native paths,
provider text and private inputs remain excluded. Submission/retention uncertainty
must retain the original identity; it cannot select a second stop. Tests planned
in actual baseline controller fixtures and existing feature resource fixtures:
success, lost response, interrupted prelaunch, changed current successor, repeated
completion, changed source/image/definition, store failure and historical readers.
Registered owners remain persistence-provider-regression, acceptance-route-
regression and entity-smoke-composition; source identity/selector/partial review
closure is required. No live proof or net reduction is claimed before execution.

### B06 verification and connected ownership checkpoint

Parent independently reviewed the final shared replacement, closed admission,
actual credential parent-to-child calls, retained original and chronological
checks; no blocking correction remains. The complete existing controller suite
passed 46 tests in 2.480 seconds with provider doubles. The final two focused
replacement tests passed in 0.201 seconds; the feature resource fixture also
passed. The actual deployment-operation diagnostics fixture passed after its
old malformed identity fixture was corrected to use a valid temporary
reservation and assert structured uncertain timeout evidence. These are
exploratory local results, not retained registered integration or AWS proof.

B06/C03/C01 exact source ownership and partial diagnostic reviews are recorded.
The structural diagnostic check passed with 727 discovered sources and zero
findings. New selector cases bind all three connected consumers and independently
remove inputs to detect stale fingerprint reuse; their final expanded run is
still pending the stable connected batch. Existing earlier selector receipts do
not qualify these changed inputs. Registered integration and actual image
qualification remain pending. No original acceptance files changed.

## B09 snapshot consolidation — comparison and bounded implementation

The baseline normal command currently observes/adopts a named snapshot or creates
one without a durable local intent. Its explicit `--observe-only` is the retained
historical reader. The feature already reserves an exact source incarnation,
record observation and snapshot, rejects preexisting objects, and checks manual
encrypted source/ARN/time/tag identity. These policies are not interchangeable.

Extract one snapshot execution owner beside existing AWS resource operations:
reserve immutable intent, apply the caller's exact absence/ownership precondition,
submit one create, and observe through the caller's typed reader. Reuse the
existing immutable reservation store; do not add a journal framework. A closed
baseline binding retains the fixed snapshot name and source incarnation before
submission and tags new snapshots with exact operation identity. Normal repeated
calls reconcile that intent without another create; changed source or foreign
preexisting object rejects. Keep baseline explicit historical observation and
its status vocabulary, feature original reservation bytes/tags/chronology and
all source database/record protections. Creation grants no restore or deletion
authority. Snapshot disappearance after uncertain submission is not replay
permission; a separately named governed new point is a different operation.

Actual-caller fixtures must cover fresh creation, lost response, interruption,
repeated/missing observation, changed source, preexisting/foreign snapshot,
stale creation time and historical read-only compatibility. Shared source enters
both caller identities, copied fixtures, selector inputs and diagnostic review;
no local fixture is labelled actual AWS snapshot/restore proof.

Implemented and independently source-reviewed: `snapshots.create` is the one
reserved submission owner; the baseline `snapshot-operations.py` binding and
feature `resource-control.create_recovery_point` both call it. Baseline normal
creation now binds source incarnation and positive operation tag/time lineage;
explicit historical `--observe-only` retains its original weaker reader and
cannot manufacture a new reserved proof. Feature tags and reservation format
are unchanged. Three focused actual baseline tests passed in 0.029 seconds,
covering interruption, lost response, changed source, foreign/preexisting
snapshots, stale/altered tags and no replay. The existing feature resource
fixture also passed. An initial preexisting-snapshot fixture used an incomplete
legacy shape; it was corrected to test the intended new lineage rejection.
Registered connected verification and actual snapshot/restore proof are pending.

## B10 isolated restore — provider-realization comparison and first reuse

Baseline restore creates one RDS instance in an existing isolated security group
and uses an existing verifier role with temporary exact-instance IAM authority.
Its cleanup removes that temporary authority and database after checking owned
task settlement. Feature restore creates an eight-resource CloudFormation clone
with distinct roles/network, retains the exact restored reader, and verifies the
complete owned physical resource set before and after stack deletion. Historical
observe-only, source snapshot protection and incident diagnostic readers differ
and must remain explicit. Neither implementation can replace the other by simply
changing a workload name.

First remove an actual duplicate: feature restore prepare/execute still contains
the reserved CloudFormation orchestration now owned by shared `change_sets.py`.
Migrate those two calls to that existing implementation, retaining exact template,
eight-resource review, snapshot/parameter/tag identity, DO_NOTHING policy,
positive root-event lineage, reservation bytes and finite failure vocabulary.
Use actual restore-control fixtures, including lost responses and altered
ownership; no new execution framework or restore authority. Then complete the
remaining direct-RDS/task/cleanup comparison and document each retained policy or
additional common operation. This first extraction alone does not complete B10.

The baseline restore's verifier-family discovery also duplicates the shared ECS
family/status listing, pagination rejection, exact described-task set and
startedBy filtering. Extract that discovery inside the existing shared task
owner; keep exact-one reconciliation as its existing caller's policy. Baseline
restore retains explicit maximum 100/no-pagination CLI options and allows zero,
multiple or all-operation observations for its existing cleanup/diagnostic
decisions. This does not change launch authority, legacy operation IDs, task
retention policy or introduce a generic deployment scheduler.

Both extractions are implemented and independently source-reviewed. Feature
`prepare_restore` and `execute_restore` now use shared reserved change-set
operations; their old duplicate submission blocks are removed. The complete
existing restore-control fixture passed, preserving eight-resource ownership,
lost-response handling, original-reader and cleanup negatives. Shared
`tasks.observed_tasks` now owns listing/complete description; existing
`reconcile_task` still applies exact operation filtering and exact-one cardinality.
Baseline `verifier_tasks` supplies its original maximum-100/no-pagination CLI
policy and returns only the existing ARN projection. Two actual discovery and
reconciliation tests passed in 0.077 seconds, including foreign/missing/duplicate
descriptions, pagination, oversized lists and provider failure. Feature task
control passed; baseline task operations passed 11 tests in 0.735 seconds;
baseline restore smoke passed 24 tests in 0.732 seconds (0.841 seconds command).

Remaining restore differences are intentionally retained after source comparison,
not hidden behind a generic callback scheduler. Baseline `restore`,
`temporary_restore_identity_policy`, `temporary_restore_identity_policy_stable`,
`temporary_restore_identity_policy_effective`, `verify` and `cleanup` own a direct
RDS clone, older in-flight IAM-enable compatibility, an exact-instance temporary
IAM grant, CloudTrail stabilization/simulation and grant/database cleanup.
Feature `reviewed_change`, `validate_reader`, `cleanup_identity`,
`observe_cleanup` and `cleanup_restore` own an eight-resource stack, original
readback and complete physical-map absence. These are distinct resource and
authority policies. Both now reuse provider transport, snapshots, change sets,
ECS observation/identity and release succession where those operations match.
The historical baseline observation path does not acquire feature automatic
resume guarantees. No source database/snapshot deletion authority changed.

### C06 connected source and verification closure

Exact source/repair lists include the new snapshot owner. Selector fingerprints
include shared task/snapshot operations and actual restore/copied payload callers;
the copied baseline payload fixture now includes `tasks.py`. Partial diagnostic
reviews cover shared snapshot execution, baseline snapshot binding, reviewed
UPDATE callers and the changed task/restore consumers without asserting complete
Core diagnostic adoption. Structural coverage passed with 729 discovered sources
and zero findings. The expanded selector method first failed in 32.704 seconds:
a duplicated `tasks.py` input made the catalog contract invalid. The duplicate
was removed without weakening selection or fingerprint assertions. The next run
failed in 446.692 seconds: two actual callers selected the task owner but did not
include it in their fingerprint inputs. Exact `tasks.py` inputs were added to
`restore-connection-diagnostics` and `persistence-payload-regression`; no negative
assertion was removed. The expanded method then passed in 348.005 seconds.
Per-method memoization caches only unchanged real repository fingerprints;
catalog validation and temporary source mutation/omission probes remain real.
This is not a production selector cache or a latency guarantee. Structural
diagnostic coverage again passed (729 sources, zero findings).

Parent reviewed B11 retirement, its retained readers, actual-caller rejection of
new attempts under the frozen incident identity and reconciliation of original
lost submissions. Seven changed source hashes and partial diagnostic reviews
were updated; retired entrypoints do not claim Core diagnostic adoption. The
connected payload wrapper and shared owner inputs are registered. These outcomes
are exploratory: the final connected registered batch, full affected integration,
image qualification and live acceptance remain unfinished. No registered batch
was started before the parent began the independent reporting slice; selector
implementation is a global check input, so even a payload unit would become stale.

## Stage 4 connected controlled workload — bounded implementation

Parent approved a single disposable `ledger-probe` fixture through existing
shared entrypoints. It supplies its own package, SQL migration, private ECS
binding and workload assertions. The actual assembler builds its isolated
runtime package; controlled task submission executes that package rather than
inventing successful result messages. Shared immutable reservation, CloudFormation,
task and snapshot operations connect package identity to retained proof hashes;
the existing release-succession constructor consumes those hashes in memory.
Prove interrupted submission/no replay, changed package or task identity and
altered retained proof rejection. Integrate with the existing payload fixture
command and exact selector inputs, not a new test/deployment framework.

This is controlled shared-entrypoint reuse, not arbitrary deployment through
the two existing static target CLIs. SQL execution is a deliberately finite
database double, not PostgreSQL qualification; provider responses are controlled,
not AWS evidence. Do not retain/promote the synthetic candidate or label it live.
Actual package qualification remains separately pending a committed checkpoint.
Declaration-derived arbitrary workload adoption remains workstream 3.

Implementation and parent source review are complete for this controlled scope.
`connected-workload-test.py` first passed two cases in 1.692 seconds. The existing
payload wrapper, now invoking both fixtures, passed its 23 original Node cases
in 10.711 seconds and two connected Python cases in 2.214 seconds. Missing
package, actual program failure, foreign task definition, changed package bytes,
altered proof bytes and altered candidate image are independently rejected.
Lost write response reconciliation performs one write, not a second submission.
These direct results are not registered receipts or deployment qualification.

## Final source comparison and accounting checkpoint (2026-11-15)

A01 alignment callers now share AWS invocation through B04. Baseline
`prepare-candidate.foundation_outputs`, `infrastructure_parameters` and
`validate_receipt` retain baseline foundation/package policy; feature alignment
`inspect`, `database_facts` and `image_delivery_policy` retain stricter private
network, endpoint, database incarnation and image-delivery facts. Their output
acceptance and ordered observations differ. Parent accepted retaining these
predicates rather than introducing flag-heavy dispatch for individual reads.
A02 already uses the common ECS normalizer and keeps workload selection in its
binding. A03 keeps workload compilation/assertions; C03 removes the accidental
baseline application dependencies. A07 already uses common Docker cleanup;
PostgreSQL versions, role setup, private-network/volume and TLS proof policies
remain deliberately separate. This resolves the earlier proposed extra
lifecycle extraction by comparison; it does not complete actual image proof.

C03's dependency extraction is implemented, but the canonical configuration,
role-credential and operation-diagnostics ownership migration remains pending.
The [prepared migration plan](../migration/shared-persistence-entrypoints.md)
maps all current callers and retains three old-path export wrappers for direct
and historical references. Its required committed-plan checkpoint has not been
authorised; no canonical move or commit has occurred.

Measured before that migration-plan addition and these final record edits,
tracked diffs plus authorised untracked files contain: operational/source/config
76 files, +3176/-1897 (net +1279); tests 32 files, +2496/-446 (net +2050);
governance/docs 8 files, +3389/-203 (net +3186). Test classification uses test or
fixture filenames plus named regression files; documentation includes agentic,
docs, README, check catalog and diagnostic review files. Operational counts
include two test dispatchers and are not pure production-logic counts. The
unrelated education lesson file is excluded. This snapshot is not a claim of
overall reduction. Four retired incident executors alone remove a net 428 lines;
new baseline durable execution, compatibility and proof coverage add code.

## C03 parent-owned composition ownership — comparison/proposal

The comparison found actual coupling, not merely baseline names: feature
administration imports baseline configuration, which imports baseline composition
and its application/PostgreSQL runtime just to choose requirements and assemble
configuration. The proposed neutral entrypoints/shared/persistence owner contains
configuration, role-credential and operation-diagnostics. Separate configuration
implementation selection from baseline composition's createRuntime; retain the
actual baseline runtime factory. Preserve exported diagnostic IDs/detail schemas,
environment names/defaults, credentials, TLS and role policy.

Before canonical moves the parent will follow artifact migration and decide
compatibility from exact consumers. Migrate actual callers, compiler and Docker
copy/ignore/payload closure, dependency-boundary checks, catalogue exporter,
selectors and diagnostic reviews. Do not add unnecessary compatibility facades
or rewrite accepted historical evidence. The feature borrowed-source test admits
seven baseline files today; removing that accidental compilation closure is a
measurable outcome. No C03 source implementation is claimed at this checkpoint.

## C03 configuration selection dependency boundary — parent owned

The inspected feature closure currently borrows seven baseline entrypoint files.
`entity-smoke/administration.ts` imports the 262-line configuration binding;
that binding imports baseline composition only for implementation selection,
requirements and assembly. Composition additionally imports the baseline app,
PostgreSQL runtime and diagnostics. The 144-line shared-in-use role helper imports
operation diagnostics, which also imports configuration. This is an actual
unnecessary runtime dependency, not merely a naming inconsistency.

First extract configuration-only implementation selection into
`infra/04.deploy/03.product/entrypoints/shared/persistence/configuration-implementation.ts`.
The current configuration binding consumes that selection and its narrow type.
Baseline composition consumes the same selection and alone adds `createPool`
and `createRuntime`. Preserve existing callable exports, diagnostic identifiers
and schemas, environment bindings/defaults, TLS, role and credential policies.
No existing canonical path is moved or removed in this extraction.

Connect both exact Docker COPY/context allowlists, fresh compiler/payload closure,
the feature dependency-boundary assertion, the existing baseline configuration
fixture, catalog export and test-selector inputs. Remove the four obsolete
baseline composition/app/PostgreSQL/diagnostics source allowances and copies
from the feature image once its compiler proves they are no longer required.
The feature test must explicitly reject their reintroduction, not merely accept
a newly generated list. Existing declaration dependency approvals remain intact.

The broader thematic relocation of current configuration/role/operation-diagnostic
files is not claimed by this change. The artifact-path migration workflow and
standard require a committed migration plan before canonical moves; current
authority does not include a commit. Inventory and independent extraction can
continue without that move. Choose compatibility and complete any necessary
path migration at its properly authorised checkpoint; do not add speculative
facades or rewrite accepted evidence.

The configuration-only extraction is implemented. Fresh feature compilation and
dependency observation passed with 255 source files; the four baseline application
modules are absent and explicitly forbidden. The existing isolated runtime fixture
passed using its prepared two-root external dependency closure. Both actual image
COPY/context declarations include the shared source; focused negative assertions
reject omission of the feature COPY, file allowance or either new parent allowance.

Baseline fresh compilation and configuration regression passed all 577
failure-before-pool cases, including the unchanged published catalog, TLS and
migration deadline assertions. The destination-port counterexample initially
failed because its injected selector still targeted the old composition import;
the fixture now intercepts the configuration-only selector, preserving its
original rejection assertions. Baseline payload/copy-closure negatives, package
stage fixtures, actual-builder controlled qualification and 47 local-public
recovery cases passed without any Docker-engine or AWS operation. The recovery
pin was reviewed and updated for the added configuration COPY: baseline Dockerfile
SHA-256 `85a5fb144d452cd75b455d2c6cc6ab295736a021d52b3fbefeb31bb198f622f6`.
The feature Dockerfile is
`768ed1ae54aa71edd82bfe3c30cd49a15bee19252fa588995aa2936f5f977a44`.
These are exploratory local results, not image qualification or final registered
evidence. Independent sub-agent source review found no blocking correction after
reading both configuration callers, original diagnostics, load-cache and selector
counterexamples, fresh source closure and exact image contexts. Selector/source
closure, diagnostic review bindings and the connected final verification batch
remain required.

## C01 candidate construction — parent owned

Both current collectors already delegate history/current validation and promotion
to `60-run/release-succession/script.py`. Keep that owner and the distinct typed
receipt, freshness, provider observation and historical validators. The remaining
shared construction is the proof-set hash, exact release identity, candidate
release envelope and proof count. Add one pure `candidate_document` function to
that existing owner and use it from both collectors. No new ledger, proof schema,
promotion API or provider operation is introduced. Preserve each existing
caller's YAML field order and exact serialized bytes for equivalent inputs;
do not rewrite accepted evidence. Prove both actual callers against independently
constructed previous representations and retain all negative/retention tests.
Include renamed workload, source/image/contract/proof changes and invalid input
cases. Selector/source and diagnostic closure plus independent review are part
of this slice; local tests alone do not qualify a release.

Both collectors now use that constructor. The baseline fixture independently
reconstructs its previous document and compares exact YAML bytes; the feature
fixture does the same for six source/image/contract/proof variations and exercises
a renamed target/workload. Both actual callers are observed invoking the shared
constructor and reject its failure without falling back. Existing succession
regressions, baseline retained/fresh acceptance checks (including 20 negative
current observations), and feature aggregation/source-boundary/route tests passed.
These are controlled local checks, not provider proof. Independent C01 source
review found no blocking correction after reviewing construction, both actual
collectors, prior-format byte comparisons, identity variants and failure paths.
The entity controller digest and its exact controller-only repair allowlist now
include the shared succession implementation; parent review confirmed this does
not admit runtime/package changes. Matching closure tests and connected registered
verification are still pending.

Remaining collector policy comparison: baseline `parse_proof_receipts`,
`sequence_valid` and `validate_record` consume individual typed task receipts,
declared proof edges, qualified rollback/support-image compatibility and separate
observability proof. Feature `acceptance-controls.validate_connections` consumes
the composite archive, exact task/control admission graphs, preserved-record
digest, initial-stop/restart, expected-unready revocation and eight-resource
restore lineage. These are distinct assertions and accepted formats, not two
implementations of candidate construction. Preserve both validators and their
negative tests; candidate envelope/identity and succession already use the one
shared owner. A generic callback collector would not remove a shared operation
and could obscure those policies. Parent source review confirms this disposition.

Read-only original evidence validation also passed for baseline `accepted-release.yml`
and feature current release `release-53798ef563be4ce9a8c5b2f0`; feature reports
`current_readiness: false`. Neither check queries current AWS health. The protected
current-reference hashes remain respectively
`02bfafd548967031922e3d99ad57c4f1a221f9b3acff5b3c0c0ec67710dac453`
and `77055d8fbeabc53190c22d1b64de5238432a1913948b10bec9a1a4a1f0464cf5`.

## C08 current-status correction — parent owned

The feature execution README incorrectly described live acceptance, image proof
and restored-reader wiring as unfinished. The bounded correction links the
original current reference/history, records the 2026-11-12 acceptance, identifies
the original plan as historical context, and separately states that subsequent
consolidation is not yet image-qualified/deployed/accepted. It also removes stale
unfinished/draft prose where the actual connected route and original retained
proof establish implementation. Existing command authority, freshness, typed
proof boundaries and original plan/history files are unchanged.

The parent used the README skill/standard, read the full guide and compared its
changed claims with the accepted reference/history, actual task-stage binding,
restore reader consumer and current offline validator. All 71 local link targets
exist and `git diff --check` passed. No example executions, AWS requests or
full module/export-guide rewrite were required for this status correction.
Further active guidance changes remain owned by their implementation slices.

## Queued authorised follow-on — evidence reporting

After the consolidation programme, extend the existing check-selector summary
and retained report to distinguish requested local checks, full affected local
integration, package qualification, live-target proof and acceptance. This is
the user's subsequently authorised follow-on, not an A04 addition. Use existing
statuses, input matching, stage owners and report storage; preserve absent,
failed, interrupted, stale and deferred evidence explicitly. Explicit selection
must not imply complete impact coverage. Missing later-stage proof must not
fail an otherwise successful local command or create publication/AWS authority.

Expected owners: `scripts/repo/check-selection/{execution_policy.py,script.py}`,
existing mechanics/repository-contract tests and README, and the shared
change-completion standard, with affected registrations/diagnostic reviews.
Implement a small projection, not a new ledger, framework, scheduler or gate.
No automatic extra suites, commits or external operations are authorised.
Keep this queued until consolidation is complete, except genuinely independent
work at a precisely reported authority limit; never call unfinished
consolidation complete to begin the follow-on. The educational lesson file is
outside this task and remains untouched.

At the precisely recorded C03 committed-plan and package-checkpoint authority
limit, the parent is independently implementing this reporting projection. The
producer is the existing `plan()` to `execution_policy` path; consumers are JSON
CLI output, `render()`, `safe_run()` retained `report.json`/`summary.txt`, mechanics
tests, README and the shared completion standard. Distinguish requested-local,
complete affected-local-integration, package, live-target and acceptance views.
Preserve selected rows' statuses/exit codes and missing, deferred, stale and
interrupted observations. Explicit, development, commit-only or empty selection
cannot imply complete affected integration. External stages remain owned and
not evaluated by this selector; no imported proof, extra suite, store, exit-policy
change or external effect is authorised. Assertions cover actual impact versus
partial selection, failed/negative-exit/input-changed rows, omitted stages,
matching reuse, safe retained output and legacy reports lacking the new field.
Consolidation is still incomplete; its registered batch is deferred while these
global selector inputs change, not reported as passed or waived.

### Reporting safeguard source-review checkpoint (2026-11-15)

Parent implementation is now independently source-reviewed across
`execution_policy.py`, `script.py`, five added mechanics cases, three extended
existing cases, README and the shared completion standard. The projection is
attached only after existing final input revalidation; it neither executes
additional checks nor reads external proof. Integration coverage requires a
nonempty declared-impact selection, the integration boundary, passing selected
local observations and no findings. Explicit, development, commit-only and
empty cases remain incomplete; package/live/acceptance always remain unevaluated
by this owner. Existing report rows preserve original statuses and exits.

Review identified and implementation corrected two edges: retention failure now
recomputes the returned summary after adding its finding; global catalog drift
now projects local stale observations without altering original check statuses
or external-stage results. Counterexamples exercise actual unsafe-directory
retention and CLI catalog mutation as well as independent global findings.
Other cases cover absent pending proof, failed command, signal interruption,
input mutation, deferred/unselected stages, matching cache reuse, no external
operations, saved finite summaries and old reports lacking the additive field.
The existing raw-output privacy and report-import rejection tests remain intact.
No further blocking source correction was identified.

Only reviewed `execution_policy.py`, `script.py` and `mechanics_test.py` source
hashes were refreshed in the existing diagnostic ledger; support/partial statuses
and remaining debt are unchanged. First four new tests passed in 7.636 seconds;
the parent's remaining three focused cases passed in 5.978 seconds. The last
reviewed test-only addition asserts blocked requested-local status and incomplete
integration when a prerequisite cannot run; its final source hash is included.
Parent scoped metadata, six README local links and whitespace checks also passed.
No registered or broad verification is claimed by this review.

The subsequent stable registered focused run passed with zero findings:
`check-selection-mechanics` in 232.480205 seconds and
`runtime-payload-assembly` in 11.3964 seconds. Its retained observation is
`.cache/test-runs/20261115T015447Z-e4cf5238719745f6bf46b75815f5bd62/report.json`.
Independent inspection confirms requested-local pass, affected local integration
`not-established` for this explicit selection, and package/live/acceptance
`not-selected` with `not-evaluated` coverage. This closes these focused checks
on their matching inputs, not the full affected integration or deployment goal.
Later shared build/selector edits must revalidate rather than assume this receipt
remains current. C03 canonical migration still awaits its committed-plan authority.

## Third workstream — declaration-derived build and packaging

### Declaration/compiler slice — agreed boundary before implementation

After the reporting slice's focused registered pass, workstream 3 begins with
one neutral `scripts/repo/workspace-build` owner, not a deployment-only import
for product tests. Parent owns `declarations.mjs` and declaration fixtures;
the implementation agent owns `compile.mjs` and compiler fixtures. Caller
migration follows API review; no third shim writer is authorised.

`loadWorkspaceGraph(root)` discovers root workspace patterns segmentwise without
symlink traversal. `deriveWorkspaceInputs(graph, {roots,
includeRootDevDependencies: false, allowedPackages?})` resolves selected runtime
closure, adding development edges only from explicitly selected test roots.
It returns package export maps to compiled JS/JSON, compiler paths to source
TS/JSON, selected public TS export roots, external dependency names, selected
manifest paths and package names. Package name, exports and dependencies remain
owned by manifests; discovery does not approve dependencies or provider access.

Predicate inventory: reject malformed workspace/manifest shape, duplicate names,
unsupported export forms, missing or escaping targets, unavailable internal
dependencies and closure outside explicitly allowed packages. Errors expose
finite reasons, not supplied paths/manifest values. This resolver writes nothing.
Source files and mapping targets are repository-relative. Optional root lockfile
workspace-link records distinguish removed internal packages from external
dependencies without guessing names into paths. Initially support only current
exact string `.ts`/`.json` export targets; reject conditional, wildcard or
type-only export shapes. Nonempty selected workspace optional/peer dependency
maps fail with an explicit unsupported-kind reason; none of the current 21
workspace manifests uses them. This does not remove the existing installed
external-dependency resolver's optional/peer support. Native filesystem and JSON
failures become finite `WorkspaceDeclarationError.code` outcomes.
Compiler preparation additionally validates selected project and finite supported
compiler overrides, preserves original include/files/compiler mode/options,
derives only selected aliases through a unique temporary extending tsconfig,
and invokes the existing installed compiler once. Explicit payload mode adds
all selected public TypeScript exports; missing exports cannot be silently
filtered to obtain a successful package. Distinguish prelaunch rejection,
compiler failure and uncertain interruption/output effects. Cleanup touches
only its owned temporary configuration; it must not erase arbitrary output.

Consumer inventory: 21 workspace manifests, 69 tsconfigs, 27 explicit mapping
objects (213 alias entries), 21 shim-writing consumers plus the diagnostic
exporter's inline assembly. Routes include the three declared core-platform
programs, legacy platform-shell, workspace runtime tests and diagnostic export.
Collector binary and dormant Python/RAG packaging are distinct dispositions, not
Node adoption. No frontend bundler or design-system package is present in this
recorded worktree; IDE tabs do not establish additional source here.

Actual declaration gaps: platform-server's supported `./main` is missing from
its exports; test-only imports require development dependencies for product
kanbien-platform (core/contracts), app platform-smoke (platform-runtime) and
platform observability (platform-security). A source AST inventory found no
missing internal runtime dependencies in workspace `src` files. Root npm command
names and aggregate ordering remain compatible; exact child-command regression
assertions change with migrated compiler calls, not by dropping obligations.
Runnable declaration package roots/approval binding is specified below before
production callers migrate; existing logical approval IDs are not all package
names. Existing payload assembler and installed dependency resolver remain the
surviving mechanisms. Fixtures must prove add/change/remove discovery, boundary
rejection, real compiler option/exit preservation, selected exports, fresh output
and differently named isolated execution; final registered and package proof
remain separate.

Program binding decision before parent edits: retain canonical YAML and current
approval/observed/forbidden IDs. Add `dependency_bindings` in the existing
runnable-program index, mapping each approval ID to either one workspace package
or explicit external packages. Programs add only `build.typescript_project`;
there is no independent package-root list. The reader derives roots from existing
approved IDs, rejects missing bindings and requires transitive workspace/external
closure to stay within those declarations. Parent owns the index/schema and
`runnable-program-contract/build-inputs.mjs` reader/fixtures. Tests cover renamed
programs, unknown packages/IDs, unapproved transitive and external dependencies,
malformed/unsafe input and all three actual programs. This supplies package-name
binding without changing earlier approval IDs or granting discovered dependencies.

No Node YAML parser was present. Use exactly pinned build-tool devDependency
`yaml` 2.9.1 with its locked integrity, rather than a bespoke parser, parallel
registry or JSON-only body imposed on the canonical YAML file. Parent reviewed
the official parser API and registry metadata. Strict single-document parsing
rejects parser errors/warnings and aliases; native parse text is not reported.
Existing Python YAML consumers remain supported; dependency installation runs
no lifecycle scripts. Installed runtime dependency closure is still owned by
the existing lockfile resolver, not by this declaration reader.

Status: independent local implementation active after the reporting safeguard's
focused proof, while the first workstream's committed-plan/package authority
limits remain explicit. This does not declare consolidation complete or waive
its remaining proof. Workspace test/check compiler callers have migrated below;
image/program compiler callers remain under the separate parent-owned slice.

### Declaration/compiler exploratory checkpoint

The parent-owned neutral runtime extraction API and predicates are specified
under “Neutral runtime-package mechanism” below; that is the single full
mechanism record, not a second implementation proposal.

Parent's program-binding reader passed seven direct cases and compiled all three
actual declared programs with payload exports in fresh temporary output:
bootstrap 9.476 seconds, persistence 9.469 seconds and feature 9.405 seconds.
Nine scoped metadata files passed. These are compiler observations, not runtime,
OCI-image or live-target qualification. Agent review of the full reader, seven
fixtures, declaration bindings and schema guide found no blocking correction.

Next reviewed implementation boundary: neutral workspace CLI selects the nearest
discovered workspace owner of an explicit `--project`; `--development` alone
includes that root's development dependencies. It reuses `compileProject` and
exposes finite prelaunch/compile failure codes, effect and numeric diagnostics,
never rejected arguments or native text. Reject duplicate/unknown arguments and
projects outside discovered workspaces before invocation. Migrate only existing
workspace alias-bearing runtime/integration/check configs and their npm child
commands; preserve command names/order and all config options except obsolete
`paths`. Payload tests request every public export. Parent retains the three
program configs, shell image config and diagnostic config. No shim changes until
the shared owner is ready. Exact-command/copied-script consumers must migrate
with actual caller tests; no broad verification during connected source edits.

Expanded census correction: searching only `writePackageShim` missed inline
writers in platform contracts, ECS Fargate and DynamoDB rate-limiter runtime
dispatchers. The current migration inventory is 21 workspace runtime/integration
dispatchers, three deployment preparer/boundary callers and one diagnostic
exporter, 25 caller sites total, excluding the surviving shared assembler.
Retain the rate-limiter's independent JSON export equality assertion.

Parent's declaration resolver passed 13 direct cases in 0.356 seconds after
review corrected null-selection handling and symlink-root traversal. Agent
review found no remaining required correction in the resolver. Manifest changes
add the missing server export and three test-root dependency sets, with matching
lock records; no runtime implementation bodies changed.

Compiler adapter first passed six direct cases in 8.477 seconds. Parent review
then found two real gaps: moving the config changed implicit Node type lookup,
and generic failure discarded useful compiler diagnostic codes. The corrected
eight-case suite passed in 18.560 seconds: real inherited CommonJS compilation,
ESNext declaration-only mode, relocated Node types, actual entity runtime
compilation, private temporary config and exact process arguments, prelaunch
rejection, actual TS2322 without source/path disclosure, and process interruption
cleanup. Numeric diagnostic codes are bounded to 32; original output text is not
retained. Existing output ownership stays with the caller, so this is not yet
proof of fresh package output across all routes.

A final root-alias review found the adapter could canonicalise a symlink before
the resolver checked it. The adapter now preserves the supplied resolved root
for project canonical-path rejection. The targeted prelaunch test passed in
0.535 seconds, rejecting symlink roots without invoking a compiler. The fixture
metadata kind was corrected to `script`. Parent accepted the corrected compiler
source review. These direct exploratory passes are not registered full-impact,
image qualification or live proof. Remaining caller/shim migration, governance
enforcement and final matching-input verification remain pending.

The 22 migrated workspace compiler children were then invoked with fresh
temporary outputs: 21 passed, PostgreSQL integration failed with TS2307, total
125.374 seconds using two concurrent compilers. Read-only TypeScript diagnostics
traced the missing modules to its existing relative entrypoint import, whose
configuration/operation diagnostics import platform-config, platform-server and
platform-workers. The integration test also imports app-platform-smoke directly
by relative source path. Add these four existing test-only dependencies to the
PostgreSQL adapter's devDependencies and matching lock entry; do not add them to
runtime/image dependencies. This closes a declaration gap hidden by old aliases;
the earlier package-specifier AST census did not cover relative cross-owner
imports. Retest this failed project without repeating the 21 matching passes.
Independent baseline comparison confirms all 22 configs otherwise preserve
every field, and npm names/order/other scripts and child tails are unchanged.
The initial comparison probe misindexed the project token; its corrected
read-only probe passed without source changes. The four dev dependencies and
lock entry are now corrected; only the failed integration compiler was rerun,
passing in 11.408 seconds. This does not turn earlier exploratory observations
into matching registered receipts after manifest changes.

The neutral CLI's five focused tests passed in 0.532 seconds, including actual
repository commands, nearest renamed/nested workspace selection, explicit test
dependency selection, prelaunch rejection and finite actual CLI output. The
repository assertion discovers migrated commands and rejects any workspace
runtime/integration/check config retaining handwritten paths. Twenty-two maps
(137 alias entries) and compiler child commands migrated; declaration-only
library commands, npm names/order, child runner tails and all other config
fields remain unchanged. Five non-workspace-image/diagnostic maps remain with
the parent-owned migration. Parent source review of this connected caller slice
is pending. Two initial CLI patch approval reviews timed out without applying;
the parent applied the reviewed patch, and subsequent normal scoped edits worked.

### Ownership and inventory

Inventory existing repository build routes, their handwritten mappings and
connected consumers before selecting migration slices. Package `package.json`
owns package name, public exports and dependencies. Existing runnable-program
declarations own the selected program and its approved dependency boundary.
Existing deployment configuration owns deployment settings. Discovering a
package or dependency does not authorise its use, deployment or cloud access.

Derive compiler/runtime mappings and required package inputs from those owners
through the existing shared build/package mechanisms. Correct incomplete
manifests where old scripts currently supply missing facts. Explicitly declare
assets and dynamic requirements that cannot be derived; do not silently omit
them or infer authority from discovery. Preserve legitimate frontend/backend
build differences. Remove superseded handwritten copies only after their
consumers migrate and compatibility is proved.

### Governance and enforcement

Extend the existing product public-module standard, runnable-program standard,
build/package/feature workflows and their executable validators/test selector.
The rules must remain enforceable for newly discovered packages and programs,
not only a list manually updated for this feature. Cover missing/unsupported
declarations, unresolved dependencies, bypass routes and changes to shared
machinery selecting its affected consumers. Local declaration checks do not
require live AWS proof; external qualification remains with its existing owner.

### Required evidence and honest adoption boundary

Prove add, change and remove behavior with existing workloads and a differently
named fixture: adding a declaration requires no shared-controller fork; changed
exports update compiler/package mappings; removals leave no stale files in fresh
outputs and unresolved consumers reject clearly. Prove isolated packaged
execution without borrowing checkout dependencies. Retain meaningful independent
assertions rather than validating generated output against itself.

Record route-by-route adoption, remaining exceptions, exact source removals and
verification in this plan and the existing inventory. A successful `test-entity`
example does not establish repository-wide adoption. Preserve accepted histories,
source/package identity and current workload boundaries. No new framework,
scheduler, deployment system, automatic approval or external execution is part
of this authorisation. The parent's educational lesson remains outside this task.

### Neutral runtime-package mechanism — parent implementation boundary

Workspace-dispatcher migration boundary: extract the CLI's pure nearest-workspace
owner lookup to `declarations.mjs`, shared by CLI and runtime dispatchers, so no
runner duplicates package names or imports compiler execution merely to select
its owner. Derive each runner's existing workspace project with root-only dev
dependencies, then call `prepareWorkspaceRuntime`; retain discovery filters,
ordering, failure exit and the rate-limiter's independent JSON value checks.
Supply actual minimal manifests/source export declarations and inert compiled
dependency files in infrastructure discovery fixtures, rather than bypassing
the new required-input checks. These fixtures still execute real test processes
and preserve missing/stale/symlink/discovery negatives; they are not application
or deployment qualification. Native selection failures remain finite declaration
errors, with CLI owner-missing compatibility mapped at its boundary.

Extract only the existing package-shim planning/check/write responsibility into
`scripts/repo/workspace-build/runtime-packages.mjs`. The current deploy assembler
remains at its canonical path and owns wrappers, payload manifest and ordering;
it calls the neutral mechanism instead of retaining a second shim writer. This
is a responsibility extraction, not the pending C03 canonical artifact move.
Workspace test runners can then use the same mechanism without depending on a
deployment-layer module. The diagnostic exporter has deferred JSON asset-copy
semantics; migrate that caller only after preserving that ordering explicitly.

API: `planRuntimePackages` validates package/export/path shape and output
collisions, returning outputs and compiled inputs; `assertRuntimePackageInputs`
checks each required file; `writeRuntimePackages` creates the shims/assets/package
manifests; `prepareWorkspaceRuntime` combines declaration selection and those
operations for callers without deployment wrappers. Preserve current deploy
failure phases, location fields, bytes and entrypoint-before-export validation.
Native read/write failures retain finite reasons and known earlier-write state;
invalid/escaping/symlinked inputs and missing files fail before writes. Exact
shared outputs also participate in existing global wrapper/manifest collision
checks. No network, process execution, compiler selection or recursive output
deletion belongs in this mechanism. Existing assembler regression and actual
neutral-caller imports must prove the extraction; no image qualification is
established by those local tests.

### Shared runtime mechanism and dispatcher exploratory checkpoint

Agent reviewed the neutral helper and full migrated deployment assembler.
Review corrected JSON default/named export suffixes and root/ancestor symlink
rejection before adoption. Five real isolated helper cases passed in 0.655
seconds. Extended assembler checks initially passed 30 of 31 in 11.104 seconds;
the old collision fixture was corrected to the actual root-JSON/index.json
collision and its targeted rerun passed in 0.431 seconds. Full final rerun and
actual image qualification remain pending. The program compile wrapper and two
new fixtures were also source-reviewed without a blocking finding; the combined
nine-case build-input suite passed in 0.529 seconds. Its first fixture patch hit
an approval-service BadRequest before execution, then applied on retry.

All 21 workspace runtime/integration dispatchers now use the shared writer;
their package maps and local shim functions are removed. Pure project-owner
selection is shared in declarations, not a package-name list or compiler import
inside runtime dispatchers. The existing source-led discovery, child ordering,
timeouts, exit policies and rate-limiter JSON equality assertion are retained.
Fourteen declaration and five CLI tests passed together in 0.564 seconds.

The discovery fixture now supplies real minimal selected manifests and source
JSON plus inert compiled dependency exports; it does not bypass required-input
validation. All five existing discovery scenarios exercised each of 20 migrated
runtime runners and Core (105 successful scenario outcomes across the runs).
The first direct batch passed 16 owners then stopped because the probe supplied
the default expected child exit 7 to PostgreSQL, whose existing test explicitly
expects 1. No source correction was needed. The corrected PostgreSQL invocation
and remaining four owners passed in 15.623 seconds. This fixture proves runner
behavior, not the inert dependencies' application behavior.

The actual migrated `app:entity-smoke:test` and
`platform:adapter:aws:security:dynamodb-rate-limiter:test` commands both passed,
including actual feature/unit assertions and the JSON-export comparison. No
duration was captured for these two commands. Disposable PostgreSQL integration
execution, broad matching-input verification, selector/diagnostic closure and
remaining deployment/diagnostic callers remain pending; no AWS calls occurred.

### Program caller migration and early declaration diagnostics

All three program configs now remove only their handwritten aliases; their local
and Docker compiler callers use the shared declaration-bound compiler. Fresh
actual CLI compiles passed in 10.074, 11.774 and 11.055 seconds (bootstrap,
persistence, feature). Their three runtime preparers now use declared exports;
all passed on those outputs. The feature independently observed 255 source files
and its approved dependency boundary passed. These are local results, not image
qualification. Qualification input lists and remaining callers still need migration.

The copied-Docker fixture passed 38 of 39 cases in 16.051 seconds. Its missing
JSON-asset case exposed earlier declaration rejection losing the old package and
export context through the preparer's generic catch. Before correction: attach
only checked package/export identities to declaration export-source failures;
the three preparers report the declaration phase, finite owned reason and this
location before writes. Do not echo rejected target paths or native errors.
Keep existing assembly-stage report shapes unchanged. Update the actual missing
asset and malformed-manifest caller assertions to these exact earlier findings,
and retain no-write/privacy assertions; do not weaken them to generic arguments.
The existing declaration fixture proves source-missing/symlink alternatives and
will additionally assert this safe location. Source review and matching registered
evidence remain required; this note does not claim diagnostic adoption complete.

Correction implemented: checked declaration export-source failures retain a
frozen package/export location. All three preparers preserve the declaration
phase and owned finite reason; ordinary assembly errors keep their old shape.
The two affected actual preparer cases passed in 2.053 seconds; the 24 declaration
and program-binding cases passed together in 0.618 seconds. The 39-case preparer
batch is not yet a single fully passing final receipt (38 passed before the
correction, followed by the two targeted passing cases). Full whitespace check
passed. The fresh program outputs remain at the owned local temporary directory
`/tmp/program-caller-migration-kR1SjO` for connected preparation checks.

Both existing publication workflow receipts and their exact guards now bind the
neutral declaration/compiler/runtime helpers, program reader/compiler command
and canonical program index. Independent omitted-source counterexamples were
extended too. Baseline qualification-route and feature workflow fixtures passed;
the latter reported 25 workflow and seven foundation negative cases. No Docker
engine, publication or AWS execution occurred. The bootstrap Docker context also
admits its new shared runtime helper. Final source review, selector input closure,
metadata revision refresh, diagnostic ledger and matching integration remain open.

Remaining parent WS3 caller work is not hidden by these results: installed
dependency roots still need declaration derivation; legacy platform-shell and
diagnostic-export projects and shims still have handwritten mappings. The latter
must preserve deferred JSON copying until catalogue compatibility succeeds.
For those two broad legacy projects, derive roots from their existing explicit
TypeScript root-file declarations, not every discovered workspace or server
runtime dependency widening; review unowned target-root semantics before edits.
Agent-owned workspace dependency enforcement and all-workstream final proof
remain open. C03's committed migration-plan boundary is unchanged.

Legacy project-selection implementation decision: use the installed TypeScript
parser's explicit root files from the existing `files`/`include` declarations;
do not walk resolved imports to discover additional approved roots. Select their
workspace owners through the shared graph, then follow those owners' declared
runtime dependencies. Only the callers' existing target-entrypoint prefix may
contain unowned explicit roots. Missing/invalid projects, symlink/escaping roots,
unowned roots outside that prefix and empty workspace selection reject with
finite reasons before compilation or shims. Program-approved ID selection stays
separate. Add a shared project-selection helper and extend the existing neutral
compiler command, not a second compiler or package registry. Prove renamed
workspace add/change/remove, transitive declared closure versus unapproved import
observations, original root options, no writes, and actual legacy/diagnostic roots.
The diagnostic exporter will retain its catalogue-selection list (semantic
definition ownership, not a package map) and deferred JSON-copy rule.

### Workspace dependency enforcement boundary (before implementation)

The existing module-structure check will consume a neutral workspace-build
dependency inspection operation; no new check registry or dependency approval
ledger is introduced. Discover source and test files from the actual workspace
manifests, use TypeScript literal-import resolution for package specifiers and
relative cross-owner edges, and reject undeclared runtime dependencies. Tests
may use their own declared development dependencies; imported deployment
entrypoints must stay within the selected test closure. Repository-owned tooling
keeps its dependencies in the root manifest, not every importing test package.
All discovered declarations remain observations, never automatic approval.

First inventory findings, then correct only justified declarations; do not widen
runtime permissions to make a check green. Preserve existing module/index and
configuration exceptions and validators. New findings use finite codes plus the
existing safe relative-path/line report convention. Literal/static analysis is
not a proof of arbitrary computed imports or runtime loading. Focused renamed
workspace fixtures must cover direct and relative bypasses, runtime versus test
development edges, root tooling, additions/removals and unsupported/missing
declarations. Existing module-structure command/regression and selector input
closure are the enforcement consumers; diagnostic review remains partial until
the connected source, findings and caller tests are reviewed.

Initial read-only inventory parsed 528 files and 2,593 literal import observations,
with nine computed loads outside this check's proof. Four findings identify three
existing test-only relative-import gaps: SQS configuration tests use platform
configuration, ECS runner-quality tests use Core helpers, and two observability
integration tests use platform persistence. Correct those three development
dependencies and matching lock workspace records only. No runtime dependency or
existing architectural allowance is widened. Parent review additionally caught
runtime-to-test-helper laundering and unowned source symlink traversal; both are
rejected, with owner-relative test roots (not arbitrary `src/fixtures` names).
The original eight focused cases passed in 0.990 seconds; the corrected eleven
cases passed in 1.820 seconds. The inventory findings are unchanged after those
corrections. Connected module-command/selector proof remains pending.

### Declaration-derived package check context (before implementation)

Inspection corrected the initial input-gap diagnosis: the current selector
already follows package manifest edges upstream, but its permissive independent
manifest reader can skip malformed inputs and includes transitive development
edges indiscriminately. Package check commands are routed through the diagnostic
wrapper, not directly through npm. Preserve that command owner and add a bounded
read-only npm-command projection sharing its real case dispatch, not a copied
unit mapping or a general shell interpreter.

The neutral workspace build owner will follow supported literal npm-script
chains and their actual compiler projects, derive selected workspace and project
input references with the existing declaration resolver, and reject unsupported
command shapes or unavailable declarations. The existing Python selector will
add these per-check inputs and impact rules before choosing obligations. Root
workspace/lock data and discovered manifest identities are discovery inputs;
revalidation must reject a changed manifest inventory or content rather than
reuse a stale closure. Unrelated workspace source is not added to every unit.
Existing conservative non-package impact rules remain; no new planner, evidence
store or approval registry. Tests must prove actual wrapper projection without
npm execution, renamed direct/transitive selection, unrelated source exclusion,
manifest add/change/remove and finite failed observations. Final registered
verification remains deferred until this connected owner is stable.

### Legacy shell, catalogue and external-root adoption — 2026-11-15

The legacy shell and diagnostic catalogue projects now select workspace owners
from their explicit TypeScript project roots and use the declared runtime
dependency closure. They do not approve discovered imports or widen the server
package's dependencies. Their handwritten compiler paths and package-shim maps
are removed. The shell's npm command and exact default-deny Docker helper inputs
use the neutral compiler and runtime assembler. Its existing cwd-relative output
contract remains intact. The actual npm image-build passed; the actual preparer
failure/presence tests passed six cases in15.141seconds. These are local compiler
and payload-fixture results, not OCI qualification or a new AWS proof.

Catalogue generation retains its semantic catalogue selections and existing
version/freshness gate. Its explicit generation mode permits a missing declared
JSON output, but never a missing TypeScript export, present non-file or symlink.
Ordinary compiler/package callers remain strict by default. Shared assembly can
defer JSON copying; final copying still validates every asset and occurs only
after successful compatibility/freshness. The fixture confirms a conflicting
catalogue cannot replace retained runtime JSON. This preserves regeneration of
deleted exported catalogues instead of making the generator require its own
outputs. The project now explicitly includes the product public source because
the existing target-delivery catalogue imports it; the former alias/shim already
named that dependency. The initial derived compile correctly failedTS2307 until
that project root was made explicit; no import-derived approval was introduced.

The combined declaration, project-selection, runtime-package and CLI regression
batch passed33cases in2.304seconds. The actual catalogue compiler and exporter
`--check` passed. Its disposable regeneration/staleness/version-conflict fixture
passed in42.917seconds. These results precede the final connected selector and
registered verification batch; they do not establish completion of workstream3.

Both installed external-dependency adapters now obtain their roots from the
canonical selected program's external bindings. The shared installed-lock
resolver still owns versions, nested/optional/peer resolution and safe copying;
it evaluates a declaration supplier once per preparation and rejects invalid
bindings before writing. No second dependency registry or lock resolver was
added. Actual copied-adapter/installed-tree tests passed12cases in3.945seconds;
the subsequently added differently named root add/change/remove and malformed
binding test passed in1.472seconds. Read-only actual installed-tree preparation
resolved52packages for the PostgreSQL baseline and40for entity-smoke, with no
output directory created. Root reports are now deterministically sorted.

Pending: parent/sub-agent source review of these newest changes, actual shell
runtime isolation and Docker-context guard coverage, documentation/metadata and
diagnostic review refresh, automatic check-input integration, the stable full
affected registered verification, the previously requested local checkpoint for
the canonical persistence path migration, and required packaging qualification.
Accepted live release records remain untouched; none of this local evidence
qualifies a newly consolidated image.

### Follow-on proof and bootstrap observer — 2026-11-15

The previous pending paragraph is historical: parent/sub-agent review of the
legacy shell, catalogue and external-root adapters found no required correction.
The actual compiled shell isolation verifier completed successfully and restored
the repository workspace links. The container context check passed six Dockerfiles
and six ignore files with zero findings after moving exact helper exceptions
before the existing final sensitive-file denials. Scoped metadata passed17files;
whitespace checks passed. No sensitive-file denial was weakened.

The complete actual copied-CLI assembly/dependency batch passed51tests in16.305s.
This includes canonical external-root addition/change/removal, malformed input,
missing helper/index context, export assets and partial-write diagnostics. It is
local filesystem/Node proof, not actual image qualification.

The bootstrap runtime fixture now uses the same canonical program reader and
runtime-package assembler; its actual retained compiled runtime passed. The
initial invocation accidentally named a nonexistent temporary output directory;
it failed with a finite missing-source error and no writes, then passed against
the inspected existing compiler output. No failed observation was counted as a
pass or used to justify replaying an external operation.

The remaining bootstrap Python observer no longer maintains package roots or
guesses export paths. It invokes the existing program reader once with fixed
arguments and a30-second bound, then independently walks source imports,
manifest dependencies and compiled output. Approved declarations remain distinct
from observations. Reader timeout/unavailability/rejection/malformed projection
produce separate safe finite codes. Six focused tests passed in1.328s, including
a differently named package/export, moved export, removed export, a declared but
unobserved dependency, malformed canary/no writes and outside-source rejection.
The actual bootstrap dependency report passed against the retained real compiler
output. The focused fixture is registered in the existing bootstrap smoke suite;
independent review and full connected invocation remain pending.

The structural diagnostic inventory found22stale reviews and11new unreviewed
WS3files. Parent-owned reviewed declarations/runtime/adapters have now received
source-matched partial/support records with exact test owners and explicit debt;
active agent-owned selector/compiler enforcement records await stable review.
Remaining completion obligations are unchanged: final connected enforcement,
stable affected registered verification, the already-requested local checkpoint
for canonical persistence paths, and required package qualification. No new
commit, publication, AWS operation or accepted-history change occurred.

### Agent enforcement and selected-input checkpoint — 2026-11-15

The module dependency inspection is now connected to the existing module gate
and regression wrapper. Its actual command passed with zero findings across
529 source files, 2,600 literal imports and nine computed loads explicitly
outside static proof. The existing regression plus eleven new declaration
counterexamples passed; the combined command took 9.293 seconds. Two selector
input/omission tests passed in 0.594 seconds after an initial counterexample
identified the missing app-manifest regression selection. Twenty-one runtime
dispatcher discovery/child-execution bodies compare unchanged against HEAD after
excluding their removed shim helper; no discovery behavior was deliberately
rewritten. The earlier AST comparison command failed because it still included
the deleted helper, then the corrected comparison passed without source edits.

The diagnostic verification wrapper now exposes its actual npm script and
explicit lifecycle policy through a read-only projection. The new neutral
`check-inputs.mjs` follows closed literal npm chains and their existing compiler
projects; `workspace_context.py` binds this result to existing selector checks.
No second unit map, planner, store or package-name registry was added. Direct
and transitive source closures, root-only development dependencies, project
configurations and discovery manifests become selected proof inputs. Discovery
manifests enter fingerprints after upstream source traversal, avoiding accidental
inclusion of every unrelated workspace's source. Root `.npmrc`, project/script
changes and newly discovered package declarations trigger this observation.

Parent review caught loss of `--ignore-scripts` semantics in the first projection.
The corrected projection distinguishes explicit ignored hooks from inherited npm
configuration. Inherited configuration is observed using one fixed, bounded
`npm config get ignore-scripts` call and rechecked in the existing runtime
identity windows. Unsupported hooks are skipped only when npm would skip them;
ordinary hooks and nested npm script chains remain observed. A changed effective
configuration prevents execution or cache qualification. No npm script is run by
the observation itself. Unsupported command syntax fails closed rather than
being interpreted as a general shell program.

Focused results: six Node context cases passed in 3.219 seconds; three actual
selector cases passed in 12.128 seconds; wrapper no-execution projection passed
in 0.111 seconds; configuration drift rejection passed in 1.482 seconds. The
later selector/registration pair, including `.npmrc` impact, passed in 14.772
seconds. Earlier fixture runs failed because the synthetic catalog omitted its
required Node installation declaration and then mismatched wrapper effects;
both fixture declarations were corrected without weakening production checks.
An earlier wrapper case named a nonexistent security selector and was corrected
to the real Cognito selector; the three other command/lifecycle tests had passed.

The generic runnable-program command now validates declared workspace builds
through the same fixed read-only Node projection used by the compiler and
bootstrap observer. Pure `validate(document)` and legacy contracts without build
fields retain structural behavior; declared build/binding records cannot opt out
of manifest/export/transitive approval checks. The child invocation has a fixed
owner and argv, no shell, a 30-second bound and finite safe failure projection.
The existing smoke wrapper now runs the program reader and generic enforcement
fixtures. Ten reader cases passed in 1.359 seconds, three generic enforcement
cases in 1.745 seconds, and the full program contract smoke passed. These are
declaration checks, not compilation or live proof. The standalone reader CLI
also supplies actual Node builtin identities for the independent bootstrap
observer, avoiding another handwritten package/builtin map.

The neutral compiler rejects nonempty effective handwritten `paths` mappings
with `compiler-aliases-must-be-derived` before invoking TypeScript. Parent review
corrected the test to put the alias in an inherited base configuration; that
case passed in 0.786 seconds. Compiler modes not routed through this shared
mechanism are not silently reconfigured. The governed package-check projector
also rejects inherited aliases in plain `tsc` commands before execution. Parent
review accepted this closure; all seven context cases passed in 3.322 seconds
on the final source. Earlier terminal output was unavailable after compaction,
so closed handles were reconciled before this bounded repeat; no live run was
restarted. Owning product/build standards and the build workflow now name both
enforcement paths and their declaration-only/Bundler scope limits explicitly.

Shared declaration/compiler/project/runtime/CLI/context fixtures are executed by
the existing runtime-payload regression, not merely listed as input hashes.
Dependency-inspector fixtures run through module-structure regression; program
reader/checker fixtures run through runnable-program smoke reached by the
existing bootstrap regression. Catalog input/runtime declarations include the
shared sources, actual manifest/project consumers and installed TypeScript/YAML
owners. Scoped metadata passed 20 files. The README skill guided the bounded
generic-checker explanation update; source review retains the distinction
between structural validation, build-input validation, compilation and package
qualification. Full affected registered verification and the authority-limited
canonical migration/image qualification remain pending. No AWS, Git checkpoint,
publication or accepted-history mutation was performed.

Independent bootstrap review caught an inherited namespace assumption: an
unapproved import outside`@kanbien`could be ignored. The corrected observer now
requires every nonrelative import to be a real Node builtin, a selected public
workspace export or an approved external package. Node supplies its own builtin
list through the shared projection; no second catalogue was handwritten.
Generic subprocess failures are also contained. The expanded9case fixture
passed in2.015seconds and the actual retained-output report still passed.

The complete bootstrap smoke command then completed successfully:10program
reader/CLI tests,3generic contract-reader tests, actual fresh bootstrap compile
and runtime execution, forbidden compiled-import rejection, existing malformed
manifest/lock observations and9binding cases. Agent source review found no
remaining required correction. This is current local compiled proof, not OCI
qualification. The scoped README update follows the readable-README skill;
its source review and relative-link check passed. Parent diagnostic review for
the corrected bootstrap source is now source-matched with the added exact test.

Final selector admission exposed an actual wrapper integration error before
registered execution: the added `non_npm` description calls changed the exact
default/base aggregate bodies. The existing aggregate gate correctly rejected
both as `verification-aggregate-wrapper-invalid`. The correction moves only the
finite no-args/base/catalog description response before those branches and
restores their original exact execution bodies; the validator is unchanged.
An actual-catalog regression passed in 0.338 seconds, including independent
undeclared-child and helper-call insertion rejections for each branch. Three
actual wrapper description/aggregate/command-preservation cases passed in
0.642 seconds, including malformed description arguments and no child effects.
The first targeted test command used a nonexistent test class and failed before
execution; correcting the command to `DiscoveryTests` required no source change.
The final read-only context projection covered 20 registered package checks and
23 discovery inputs successfully. Seven scoped metadata headers and whitespace
checks passed. These observations do not replace the final registered batch.

### Registered batch and cache correction — 2026-11-15

Parent revalidated the recorded Nov6 worktree and frozen sources. The six-check
plan and the full impact plan for 233 changed task paths admitted with no findings.
Structural diagnostic adoption passed 740 sources with no findings. The two
accepted release-evidence trees remain unchanged.

Registered report
`.cache/test-runs/20261115T085349Z-d280fa99c45d4ce692d2bd164ea167eb/report.json`
retains four passes: bootstrap dependency boundary 19.989 seconds, module
regression 4.593 seconds, module check 4.955 seconds and runtime payload 42.670 seconds.
Mechanics failed in 254.337 seconds. Its separate visible diagnostic run completed
150 tests in 289.009 seconds with 50 failures and one error: the writer includes
`workspace_npm_ignore_scripts` in receipt hashes, but the cache reader's strict
field list omits it. Valid new receipts therefore cannot be reused; the privacy
test's error is a missing rejected receipt, not exposed private output.

Parent deliberately interrupted only the verified local repository-contracts
process with SIGINT after 1047.343 seconds; its exit -2 is an interruption, not a
proven assertion failure or pass. The runner records this as failed. Prior full
passes took 445.783–763.705 seconds, versus the advisory 360 seconds. Preserve this
overrun and original report; neither is final matching proof after correction.
The correction must add the field to strict verification, classify changed npm
lifecycle policy as a runtime change, and prove matching reuse plus changed and
tampered policy rejection. No old hash mismatch may be accepted as a fallback.

The independent completion audit identified two remaining WS3 workflow handoffs.
The feature-creation and package-publication workflows now point to the existing
manifest/public-module and runnable-program build owners, preserving actual
image qualification and current execution authority. This is process routing;
it adds no runtime predicate, diagnostic vocabulary, new gate or registry.
Scoped validation is pending. C03, checkpoint-bound image qualification, full
affected verification and final performance/accounting remain open.

Interim physical-line accounting includes untracked code and tests, excludes
documentation/configuration, and selects `.py/.js/.mjs/.ts/.tsx/.sh` files. Across
deployment scripts and product entrypoints, 88 tracked changed files add 2814 and
remove 2648 lines; 29 new files add 3582 lines, net 3748 more. Across all changed code,
120 tracked files add 3625 and remove 3745 lines; 44 new files add 5736 lines, net 5616 more.
These are not production-only counts or a claim of repository shrinkage; final
accounting must be refreshed after the remaining corrections and migration.

### Connected verification corrections — 2026-11-15

The corrected registered mechanics suite passed in308.930 seconds, retained at
`.cache/test-runs/20261115T090435Z-329f8d878c1045cea069b992301d6b39/report.json`.
Feature/package workflow handoff metadata and local link/anchor checks passed.
The actual interrupted report preserves `observation: interrupted` and does
not establish affected integration or later-stage coverage.

The connected ten-check report is
`.cache/test-runs/20261115T092108Z-6b17f00fea474da0b2651487b25ac324/report.json`.
Seven passed: acceptance route, deployment operation diagnostics, feature
acceptance controls, feature composition, feature publication, release succession
and runtime dependency assembly. Package custody, persistence payload and
persistence provider failed. Direct local reproductions established:

- Shared publication's directory-only Python import hides its exact file edge
  from the existing delivery inventory tracer. Both adapters must expose the
  actual shared module path, with real-caller tracing and removed-edge negatives;
  preserve `delivery-consumer-unbound` rather than weakening inventory admission.
- The provider CLI disposable fixture omits the newly shared `tasks.py`, causing
  FileNotFoundError before its cleanup JSON result. Copy that real dependency and
  assert usable output before parsing; preserve all unknown/pending/absent task
  cases and no-delete assertions. This is fixture wiring, not new AWS authority
  or a production diagnostic change.
- Local public-image recovery still pins the earlier two Dockerfile versions.
  Parent reviewed the full current Dockerfiles and compiler/dependency callers:
  the changes select shared declaration-derived local build operations and copied
  payload dependencies; public base images, locked npm install without lifecycle
  scripts, runtime trust bundle, nonroot execution and credential-isolation
  contracts are retained. Refresh only these reviewed owner pins, retaining exact
  changed-owner rejection and all remote-engine/credential-isolation negatives.
  This does not qualify an actual image or relax `local-public-recovery-owner-review-required`.

The repository-contract registered check also failed, exit1 after1594.396 seconds,
at `.cache/test-runs/20261115T092621Z-6833a3a3cce74022a3e6651bede4cad0/report.json`.
Its cause remains unestablished because raw child output is not retained; use
visible exploratory assertions before another registered invocation. All previous
processes are terminal; affected source review is reopened for the corrections.
The current236-path impact plan passed with no findings, without executing checks.
None of these reports establishes complete integration or package/live acceptance.

Parent reviewed the three corrections and their actual consuming paths. The
provider CLI suite now passes all6 tests (6.113 seconds); local public-image
recovery passes all47 controlled cases with no real Docker calls or stored
configuration change. Two actual publication-adapter trace/missing-edge cases
pass (0.862 seconds), the existing three-binding publication fixture passes
(0.147 seconds), and the original unavailable-engine qualification test passes
(57.166 seconds) through actual delivery inventory before its Docker double.
The shared publisher's execution body is unchanged; only its real-consumer
metadata and adapter file edges change. Scoped metadata4/4 and whitespace pass.
Five source review hashes and their four existing explanations are refreshed
after this review without widening diagnostic-adoption status. Full matching
registered verification remains required after repository-contract diagnosis.

The corrected five-check registered batch now passes with no findings:
`.cache/test-runs/20261115T094228Z-edeb55b1a11949338537528ae7e6a739/report.json`.
Durations: delivery inventory37.615s, feature publication2.003s, package custody
194.795s, persistence payload44.190s, provider46.654s (whole run357.830s).
This is requested-local proof, not complete affected integration.

Visible repository-contract diagnosis passed the first two selection methods,
then failed the alignment-suite exact-input assertion: its expected declaration
suite set omits the catalog's shared `cli.py`, `response.py` and `tasks.py` inputs.
Correct the test expectation to retain these real helper dependencies, not the
catalog or equality assertion. No production selection, diagnostic condition or
permission changes. Audit the remaining exact-input assertions together before
another complete registered run; preserve the observed560.743s diagnostic cost.

The grouped34 non-planner contract assertions exposed just one further stale
exact set: bootstrap target controls omitted its shared `cli.py` dependency.
Parent added that input without weakening equality. Independent agent source
audit of the other exact-set fixtures found no further omissions. The remaining
seven planner methods were deliberately excluded from this16.330s diagnostic
batch; two had already passed in the visible fail-fast run. This grouping avoids
repeating expensive selection plans merely to find inexpensive stale assertions;
it does not replace the required complete registered repository-contract suite.

### All-change checkpoint fixture correction — 2026-11-15

The user approved committing all current paths. The commit-boundary run retained
at `.cache/test-runs/20261115T134455Z-545b323b27a14413a802f25a7fd68234/report.json`
passed45 required checks and failed only `active-workload-health-recovery-regression`;
103 later/integration obligations were deferred, not passed. Its real target
inventory validation succeeds. Its disposable copy advertises live acceptance
while moving the canonical current reference to `/tmp`; the existing reader
correctly rejects `acceptance-state-current-reference-invalid` without provider
queries. This is a fixture ownership mismatch, not a failed live acceptance.

Correct only the copied lifecycle/ownership fixtures to remove their acceptance
declarations, following the existing `copied_scope` health-only convention.
Retain real-target acceptance validation and explicitly prove a copied live
reference is rejected before fixture isolation. Preserve all lifecycle, secret,
ownership, successor and unrelated-scope assertions. No production reader,
diagnostic identifier, accepted record or permission changes are required.
The affected test owner remains the existing registered health/recovery check;
its result and matching-input commit-gate reuse must be observed before commit.

The parent reviewed the fixture-only diff. The original smoke wrapper then
passed in31.844 seconds, including the new copied-current-reference rejection;
its source SHA256 is `ef5224fb6ba29b6c7d985de61827d69b8af9e9342bf1cb1b4181089e56822057`.
This direct result proves the corrected fixture, not full integration or image
qualification. Commit-boundary verification follows against the staged bytes.

### Committed checkpoint and canonical migration review — 2026-11-15

User instruction to commit everything superseded the earlier plan-only staging
boundary. Commit `29e5f1a3ee9f1e1f6014e12859d23f2f826e0c4e` contains all240
then-current paths, including the educational lesson explicitly included by that
instruction; bookkeeping commit `d74dac68` records the result. The final commit
gate passed46 checks with103 integration/later-stage checks deferred and no
findings, retained at
`.cache/test-runs/20261115T135443Z-c46262409d9e497babd1aec3341be33c/report.json`.
The working tree was clean after both commits. Nothing was pushed or published;
no AWS operation occurred. The C03 migration plan is now committed, so its
canonical migration is authorised without a new checkpoint workflow.

The parent reviewed the three new shared implementation bodies against that
checkpoint: only their expected relative import paths change; configuration,
credential handling and diagnostic contracts remain identical. Both Dockerfile
diffs replace the three helper COPY paths and update metadata, without changing
base images, installation, user, trust or runtime settings. The exporter selects
canonical modules and retains its published catalogue filenames. Remaining
caller/fixture changes are still under agent implementation and final review;
source-match checks alone do not prove image closure.

The existing succession reader validates baseline current release
`release-570327efbb91af717da6da13`; the feature acceptance-state reader validates
`release-53798ef563be4ce9a8c5b2f0`, reporting `current_readiness: false` as expected
for an offline observation. Both complete30-release-evidence trees remain
byte-identical to inventory checkpoint `eecf0c50`. An initial parent invocation
incorrectly passed a succession history document to the legacy typed baseline
record validator and received `accepted-release-schema-invalid`; selecting the
existing succession reader corrected the invocation, with no code or evidence
change. These checks establish retained historical compatibility, not new live
health, publication or qualification of the consolidated images.

Parent review also covers the actual caller imports, compiler declaration,
selector inputs, compatibility fixture, missing-COPY/allowlist counterexamples,
canonical diagnostic fixture injection paths and scoped README links. The
existing diagnostic ledger transfers implementation sources and definitions to
canonical paths without promoting adoption or erasing debt; three export-only
wrappers have their own support entry. Structural validation passes with743
discovered sources,134 adopted,482 partial/support and127 legacy-debt sources,
and no findings. The recovery wrapper's exact Dockerfile pin is now
`acd1b6d74a552f8700f296989a6003a3080439b6bed291636bfc3d00465c190c`;
its bounded47-case regression passes with no real Docker calls or stored-client
configuration changes. A prior payload invocation reached this fixture before
the pin refresh and failed there; that failure is not an image qualification.

Current code accounting against `eecf0c50`, including the three new canonical
files, covers185 changed executable/source files (`py`, `js`, `mjs`, `ts`,
`tsx`, `sh`): +10208/-4390, net +5818 lines. The deployment-only subset under
scripts/04.deploy and infra/04.deploy is136 files, +7176/-3278, net +3898.
These counts include test/fixture code and exclude documentation/configuration;
they are a point-in-time measurement before the final catalog fixture addition,
not a claim of net repository shrinkage or a release-time improvement.

The agent completed C03 and explicitly froze all inputs after its focused
observations; no child process remains active. The migration plan records the
full commands' boundaries, compatibility disposition,18 input-invalidation
cases and isolated catalogue proof. Parent final review also accepts the one
missing explicit PostgreSQL catalogue root, its actual project-selection
assertions and three canonical impact-case additions. Fresh isolated export
passes with declared external dependencies and no NODE_PATH; all existing
published catalogue bytes remain unchanged. There are no outstanding source
review corrections and no stale diagnostic bindings. The whole task now enters
normal preparation and final registered verification on stable inputs. C03's
focused passes are not yet full integration or actual image qualification.

### Successor control and task implementation inventory

The existing infrastructure controller reuses release-succession current/history
and compatibility readers. Explicit expected predecessor must match current.
Stable proof label retains workload/data ownership; deterministic delivery ID
binds predecessor, candidate source/image/custody, contracts and dependency.
The isolated cache is not authority: resource requests, task keys, plans and
completion evidence also bind delivery identity. Actual initial v1 readers stay.

Existing deployment-control/resource-control add UPDATE and rollback phases
through shared change-set reservation/submission, preserving non-image parameters
and previous template. Review admits only all five task definitions and ECS
service image-reference changes. Rollback uses current controller custody plus
separate retained package and current-contract compatibility covering all five
workloads; no acceptance advancement. Task-route replaces CREATE-only ownership
with completed delivery reservation/current observed resources. Existing task
selection will use delivery-derived lifecycle label and stable original-read
label. Parent-owned acceptance selects fresh permission/lifecycle/read proof and
explicit recovery-capability applicability; equal template is insufficient.

Predicates needing exact finite reasons: missing/mismatched predecessor, invalid
delivery shape/hash, foreign custody/compatibility/workloads, changed non-image
parameters or template, unsafe change resources/details, foreign reservation and
post-submission uncertainty. Existing safe reports preserve owner codes and
operation effects; private provider/parameter contents are never retained. This
remains partial finite-adapter coverage. Planned actual-caller tests cover update
and rollback success/lost responses, duplicate rejection, changed lineage,
omitted workload coverage, foreign completion and unchanged initial readers.
Existing entity composition owns focused fixtures; full proof/AWS stay paused.

### Successor control and task implementation checkpoint

Implemented in the existing infrastructure/deployment/resource/task owners,
not another deployment engine. Stable workload label and deterministic delivery
namespace are both bound in retained requests, reviewed plans and completion
packets. Initial v1 readers and old reservation bytes remain supported. Normal
update and rollback preserve the previous template and every non-image/source
parameter. Both now validate the separately retained predecessor package and
current-contract compatibility for all five workload roles before planning or
mutation. The actual selected graph permits exactly one service update and five
immutable task-definition replacements; its hash is retained in the v2 plan.

The first implementation counted all six changes as updates. Source review
caught that false accounting before any AWS execution. The existing generic
refresh declaration was stopped-workload-only, so the parent extended its closed
variant for accepted predecessor plus compatible rollback; no stopped-workload
predicate was bypassed. Current fixtures assert truthful replacement counts.

Current local, controlled-provider checks completed successfully:

- Full `infrastructure-route-test.py`: update, lost response/reconciliation,
  distinct rollback, actual generic gates, missing/invalid compatibility before
  any mutation, and original create/activation/transport regressions.
- Full `deployment-control-test.py` and `resource-control-test.py`: shared
  submission and reservation, changed inputs/change details, safe retention,
  old envelope compatibility, and initial/recovery cases.
- Full baseline `controller-regression.py`: 54 cases, 2.631 seconds, confirming
  the extracted pure reservation predicate preserves other subclasses.
- Full `task-route-test.py`: actual successor prerequisite ordering, all eight
  preflight/operation tasks, real runner/collector/gates/completion and actual
  acceptance `capture_task` v2; original initial/replacement/recovery cases and
  transport regressions also pass. Typed predecessor/applicability, source
  custody and provider results remain controlled. Missing/stale prerequisites,
  changed delivery/request/prerequisite hashes, repeated launch and original
  record/lifecycle label confusion are rejected.
- Whitespace check passes. Six source bindings refreshed under four existing
  partial diagnostic owners, retaining their limitation/debt statements.

These are direct focused fixture results, not the registered acceptance check,
full affected integration, image qualification, real SQL/AWS proof or promotion.
The superseded task diagnostic handle became unavailable without a retained
terminal result and is not counted; the complete current task fixture above was
subsequently observed terminal zero. No accepted evidence was rewritten.
Supported ordinary rollback starts from the exact owned CREATE_COMPLETE or
UPDATE_COMPLETE stack; recovery of a partially failed CloudFormation transition
is not claimed by this image-only route. Parent acceptance/source eligibility
and registered proof remain independently required. Full proof and AWS remain
paused; no commit, push, publication or cloud mutation was performed.

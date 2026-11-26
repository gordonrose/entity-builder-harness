<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.inventory.verification-diagnostics-timeouts
version: 1
status: draft
created_on: "2026-11-21"
updated_on: "2026-11-26"
layer: 04.deploy
domain: deployment.consolidation
disciplines: [architecture, sre]
kind: inventory
purpose: Audit verification cost, missing diagnostic causes and timeout or resume failures, and rank subtractive corrections.
portability: {class: source-only, targets: []}
used_by:
- id: deploy.plan.consolidate-core-platform-deployment-routes
  path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
-->
# Verification diagnostics and timeout audit

Audit date: 21 November 2026. Source: `725f17e64974496e449f1c3afe8a8faaad0790a5`.

## Conclusion

The live entity-smoke proof succeeded: all 25 phases completed and release
`release-98f40c26981890ef5fac0e7d` was accepted at 18:44:29 UTC on 21 November.
The final successful read task stopped at 12:01:48 UTC. The roughly 6 hours
43 minutes between that read and acceptance were not additional feature proof.

Remaining delivery defects include regression suites invoked during live
preparation, duplicated child tests, broad invalidation, lost diagnostic causes
and inconsistent deadline/resume behavior. They contradict the verification
efficiency rule. Corrections should remove work at its owner, not create a new
verification framework.

The evidence does not show that every check was useless or the receipt cache
was broken. Real permission, packaging, signing and recovery defects were found.
It does show unacceptable delivery cost and inadequate testing of the actual
collector-to-acceptance handoff.

This audit proposes changes; it does not implement them or claim the ten-minute
deployment target has been achieved. No new AWS proof was needed for the audit.

## Scope and evidence

The census covers 3,531 tracked files, 178 registered checks (154 local,
8 package, 4 deploy, 12 acceptance), 175 package scripts and 13 CI jobs.
Lexical scans found 380 timeout-related files and 202 files with verification
invocations. These include tests, comments and dormant governance—not 380 faulty
timers or 202 duplicate checks.

- [Declaration and source candidate inventory](verification-diagnostics-timeout-inventory.tsv):
  all registered commands and candidate source lines at the audited commit.
- [Run summaries](verification-diagnostics-timeout-runs.tsv): 220 retained reports
  from 19–21 November, with source identities, outcomes and timings.
- [Session chronology](../../../commitLogs/2026/nov/06/2026-11-06-17-07-new-chat-session/README.md):
  incidents, repairs and acceptance.
- [34-lesson roadmap](../../education/lesson-plans/0002-entity-smoke-release-retrospective.md):
  remains the user-led learning record; this audit does not mark lessons reviewed.
- [Consolidation plan](../../../.agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md):
  existing implementation context.

The scan covers tracked Python, shell, JS/TS, YAML and JSON, excluding generated
files, lockfiles, proof receipts, docs and commit logs. Historical records were
examined separately. High-cost paths and the latest delivery were traced through
callers; not every lexical match received a behavioral review. Dependency
defaults and unretained invocations are not exhaustively recoverable.

Coverage includes chat/harness, core/platform/apps, build/package/run/acceptance,
target declarations and CI. Dormant rulebook references are not counted as
active deployment work. Confirmed findings and review candidates are separated.

## Measured costs

The 220 reports contain 35,855 seconds of command invocation time (9.96 hours),
3,237 seconds planning, 1,967 fingerprinting, 2,776 runtime identity and 469
receipt validation. Nested and overlapping invocations mean these totals must
not be added to calculate wall-clock delay or described as entirely wasted.
The later promotion check started during this audit is outside that frozen sample.
It was stopped after the user objected to repeated verification. The agent had
started a broad run instead of first recognizing existing verification and
incidental environment invalidation. This repeated the very failure under audit.
The stopped run is not a passing gate. Existing completed verification was used
for the explicitly requested promotion; merge bd8e81db publishes checkpoint
725f17e6 without changing its source tree.

| Check | Executions | Summed minutes | Longest invocation | Failed |
| --- | ---: | ---: | ---: | ---: |
| Selector repository contracts | 11 | 176.4 | 32.2 min | 1 |
| Entity-smoke composition suite | 16 | 143.8 | 27.3 min | 5 |
| Selector mechanics | 5 | 30.5 | 8.8 min | 0 |
| Ordinary-update regression | 12 | 23.3 | 3.8 min | 0 |
| Package custody regression | 7 | 22.5 | 5.3 min | 1 |
| Acceptance-route regression | 11 | 17.3 | 3.1 min | 2 |
| Entity-smoke acceptance controls | 18 | 8.6 | 0.9 min | 0 |

There were 597 local-runner and 2,803 cache-derived entries. No successful check
with the same check ID and evidence key executed twice in the retained sample.
That argues against indiscriminate cache reruns. It does not detect identical
child scripts hidden inside different top-level suites.

The final checkpoint selection contained 110 entries: 10 executed, 27 reused,
73 deferred—not 110 new tests. Commands took 109 seconds, plus selection and
identity overhead. A separate cached-only selection still incurred about
19 seconds of overhead.

Of 18 explicit failed check rows, 15 lacked usable retained failure detail
(`unsupported-format`); three diagnostic-adoption failures retained structured
detail. Blocked and uncertain entries are different outcomes.

## Verification findings

### V1 Regression execution inside live preparation

**Confirmed, still present.** Entity-smoke's
[`local_checks`](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/orchestration/commands/script.py)
runs composition and secret-dependency checks with a 900-second wrapper.
Infrastructure, restart, credential, snapshot and failure routes call it.
The task route was corrected in `8a39ed56`; sibling callers remain.

The session records cold work exceeding the former 180-second wrapper and a
later 900-second wrapper timeout. Preparation consumed database-preflight
validity before the intended action.

**Correction:** qualify relevant source before the live sequence. Operational
preparation must consume matching qualification evidence, not run regressions.
Preserve relevant live identity/access checks. Correct all sibling callers and
their shared contract together.

### V2 Broad invalidation and oversized fast checks

**Confirmed cost; input-level edits remain to be designed.**
[`checks.yml`](../../../scripts/repo/check-selection/checks.yml) gives
repository-contract tests inputs spanning governance, docs, deployment, infra,
core and platform. Acceptance controls also depend on broad deployment trees.
Review-record identity includes material that can change during preparation.

Composition is marked for development with an expected 60 seconds, yet reached
1,640 seconds. Repository contracts expect 360 seconds but reached 1,932.
These are not effective fast-loop budgets.

**Correction:** narrow inputs to consumed contracts, split cheap selection tests
from expensive whole-repository fixtures, and prepare metadata before qualifying.
Retain identity checks for genuinely relevant changes; do not reuse stale proof.

During the requested promotion, the chat-startup receipt supplied a concrete
additional example: its source digest and resolved tool identities matched the
19 November receipt, but the whole PATH hash differed. The current PATH includes
a temporary coding-environment directory. This forced a new execution without
a source or declared-tool change. The retained comparison establishes this for
that check, not every cache miss. Prefer a stable declared execution environment
and actual resolved-tool identity over incidental temporary PATH segments;
retain deliberate tests whose behavior genuinely depends on command lookup.

### V3 Identical child tests have two suite owners

**Confirmed duplication.**
[Composition](../../../scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh)
and [acceptance controls](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/commands/acceptance-control-test.sh)
both run the same restore-control, acceptance-control and acceptance-route
Python tests. Different outer receipt identities do not deduplicate them.

**Correction:** one registered owner for those child tests, referenced through
existing dependencies; remove duplicate direct calls. Keep actual packaged
runtime assertions distinct from controller unit assertions.

### V4 Additional build and CI verification paths

**Review candidates, not all proven redundant.** Image building directly checks
diagnostic catalog, application and composition alongside selector preparation.
Package scripts combine typecheck, build and tests that may repeat dependency
preparation. CI inventory checks can overlap selected work.

**Correction:** map direct commands to existing proof owners. Reuse identical
source proof; retain actual artifact tests. Compare production and test compiler
inputs before deleting either. Use existing shared publication helpers rather
than adding another controller.

### V5 Orchestration overhead and silent children

**Confirmed.** The [selector](../../../scripts/repo/check-selection/script.py)
captures child output until completion and gives child execution no own timeout.
Repeated entry also repeats fingerprint/receipt work. A check-start event can
be followed by minutes of silence.

**Correction:** remove unnecessary nested orchestration, expose bounded progress
and existing phase timings, and cancel owned process trees. Preserve drift
detection around actual execution. No second cache or status registry is needed.

### V6 Script topology obscures ownership and duplication

**Confirmed structural problem.** The scripts tree contains 888 tracked files:
541 belong to deployment, including 368 under the newer lifecycle hierarchy.
Approximately 235 paths are test-like and 182 are READMEs. Most files carry
artifact metadata, but there is no concise human capability view distinguishing
public commands, reusable implementations, provider adapters, target bindings,
tests, fixtures and transitional machinery.

Deployment currently mixes a flat workload-specific command surface
(`run-platform-shell-*`, `verify-platform-shell-*`) with the stage-oriented
`lifecycle/00-target-alignment`, `20-build`, `40-package`, `50-deploy`
and `60-run` hierarchy. Within those stages, generic capability code and
target/workload implementation are interleaved. A large generic
`targets/.../entity-smoke/script.py`, for example, owns local qualification,
AWS access, infrastructure planning, ownership checks and helpers used by
several operational routes. Its path does not reveal those responsibilities.

The existing delivery census proves registration and reachability; it does not
prove that one capability has one implementation owner or expose semantically
overlapping commands. Numerous local READMEs do not provide that cross-cutting
answer.

Commit preparation for this audit reproduced the selection problem without
executing the plan: five documentation and inventory paths expanded into a
large deployment check graph and more than 300,000 characters of planning
output, including persistence acceptance and composition checks. This audit
commit does not change runtime, infrastructure or deployment behavior. The
expansion is retained as evidence of overbroad relationships; those regressions
were not rerun merely to publish the report that identifies the defect.

**Correction:** classify every script as public command, shared capability,
provider adapter, target binding, test, fixture or obsolete transition. Define
the destination structure before behavioral remediation, then migrate each
capability as its remediation is implemented and remove superseded paths in the
same slice. Generate a human capability/owner/effects/test inventory from the
existing metadata. Add blocking placement and single-owner enforcement only
after the existing tree has been migrated, avoiding a permanent legacy
exception list or a second parallel script hierarchy.

## Missing diagnostics

### D1 Command boundaries discard useful causes

**Confirmed.** The selector's structured failure projection is restricted to
the diagnostic-coverage owner. Other failures commonly become
`unsupported-format`. It projects stdout, while some tools emit diagnostics
on stderr. Safe wrappers can retain only generic summaries.

**Correction:** adapt existing diagnostic contracts at command boundaries.
Retain recognized safe phase, code, exit/signal and location fields from either
stream. Keep redaction; do not retain arbitrary provider output. Test the real
wrapper and reporter together.

### D2 AWS classifications lose actionable distinctions

**Confirmed gap.** The [CLI adapter](../../../scripts/04.deploy/shared/provider-adapters/aws/cli.py)
and [response classifier](../../../scripts/04.deploy/shared/provider-adapters/aws/response.py)
collapse some failures to generic unavailable results. Plain SSO refresh errors
need not match native service-error syntax. Uncertain cleanup retained no useful
native cause.

**Correction:** preserve safe categories for expired credentials, transport
timeout, provider rejection and uncertain submission, plus operation identity.
Unknown must remain unknown; absence of detail cannot prove non-submission.

### D3 Real acceptance handoff was not adequately covered

**Confirmed incident, repaired in `2d53f461`.** Generated proof files reached a
nested prerequisite reader without the generated-evidence allowance; a typed
acceptance failure was lost at the public boundary. Passing local tests had not
established this complete path.

**Correction:** keep one compact integration test using actual collection,
generated files and acceptance readers, including representative failures.
Remove duplicate mocked assertions that purport to cover this handoff.

### D4 PostgreSQL reported a phase but not its cause

**Confirmed limitation.** Clone preflight reported `pool_connect` and
`persistence.unclassified-failure.v2` without a useful provider code. This
located the failure but did not establish timeout versus authentication,
network or another connection problem.

**Correction:** review safe normalization of real driver error shapes at the
connection boundary. Do not retroactively label this a confirmed timeout.

### D5 Structural diagnostic review is not runtime coverage

Review inventory: 45 adopted, 153 partial, 27 support records. Review-hash
freshness does not prove that a caller retains actionable causes. Use the
[existing diagnostics backlog](../../../.agentic/shared/plans/implementation/diagnostics-backlog.md)
for implementation follow-up, not another authoritative backlog or blanket gate.

### D6 Parent readiness can overstate child evidence

**Confirmed code mismatch, not a claim that the accepted receipt lied.**
The shared [ordinary-update coordinator](../../../scripts/04.deploy/lifecycle/60-run/release-succession/ordinary-update.py)
hardcodes `current_readiness: true` on success. Corrected acceptance may
legitimately return false when accepting historical proof.

**Correction:** propagate actual child evidence. Acceptance, service health and
a fresh database read are different claims; test the complete return path.

## Timeout and restart findings

Execution deadlines, evidence freshness, credential expiry, leases and retention
have different meanings. Increasing every timer or deleting every bound would
hide faults and risk replay.

| Area | Finding | Correction or necessary protection |
| --- | --- | --- |
| Local proof | Both former 180-second and later 900-second wrappers were exceeded. | Remove tests from live preparation instead of enlarging this timer again. |
| AWS reads | Up to three permitted read attempts with roughly 40-second outer bounds can overrun a 90-second observer. | Pass the remaining deadline inward; do not extend read retry policy to mutations. |
| ECS observation | Poll deadline and task-duration limit are distinct. | Resume observation of the same task; never relaunch merely because the observer expired. |
| Preflight | Its 900-second window was consumed by controller work. | Bind admission/reuse to relevant state; keep tests outside the live window. |
| Final read | Completed historical proof aged during closeout. Promotion's age-only renewal was removed in `e0a8d2b1`; collection still has a fresh-final path. | Reconcile collector/promotion semantics; do not demand new historical evidence solely because time passed. |
| Package readiness | [Verifier](../../../scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs) permits 80 attempts of up to 2 seconds plus 250 ms waits inside a 45-second Docker call. | One deadline propagated inward. This mismatch does not prove the cause of every package failure. |
| Clone cleanup | Response uncertain, stack remained; bounded same-token recovery completed. Native cause was lost. | Keep original token, exact owned target and terminal deletion proof; no automatic fresh mutation. |
| Replacement reservation | [Task adapter](../../../scripts/04.deploy/shared/provider-adapters/aws/tasks.py) reserves before a precondition outside guarded dispatch; a pre-dispatch failure stranded continuation. | Distinguish known-not-submitted from submission-unknown durably. |
| SSO | Credentials expired and interactive renewal was needed. Polling does not extend maximum session lifetime. | Inspect lifetime before long stages, use supported refresh and durable resume. |
| WSL restart | Temporary operator helpers were lost; journals survived. Path/serialization mistakes added delay. | Depend on the existing durable operation store, not improvised /tmp scripts. |
| CI | Publication maxima are 30–35 minutes; some jobs have no declared timeout. | Justify job bounds and cancellation; maxima are not measured deploy durations. |
| Runtime | PostgreSQL connection/statement/idle, HTTP request/handler/shutdown and readiness timers protect different resources. A Promise race may not cancel underlying work. | Preserve justified limits and propagate cancellation where possible. |
| Queue/retention | Visibility, leases and retention are not deployment execution budgets. | Review separately; shortening them does not prove faster delivery. |
| Whole release | Coordinator duration restarts each invocation and reports `delivery_budget: not-established`. | Persist stage/start/wait timings across resume; the ten-minute target is not yet enforced. |

## Delivery chronology and responsibility

| Period | Recorded event | Interpretation |
| --- | --- | --- |
| 19 November | Integration took 4,280 seconds with fixture/catalog/control failures; later run roughly 59 minutes. | Substantial machinery repair, not all feature validation. |
| 20 November | Integration roughly 6,130 seconds; expired preflight, observation timeouts and stranded replacement state. | Local orchestration consumed the live window. |
| 21 November before noon | Clone read and cleanup recovery finished; all 25 phases completed. | Useful recovery evidence, weakened by poor diagnostics/resume design. |
| 21 November 12:01–18:44 UTC | Final read finished; handoff, freshness and checkpoint work delayed acceptance. | Predominantly closeout machinery, not grounds for repeating business proof. |

These runs overlap other activity and must not be summed as independent wall
time. Earlier records show real package mapping, PostgreSQL permission, signing
and restore-control defects. Those justify focused assertions, not whole-suite
repetition at each step.

Concrete useful failures in the session record include the packaged PostgreSQL
bootstrap's SQLSTATE 0LP01 from a circular ADMIN self-grant (around line 6518),
and read-only Route53/IAM/Budgets requests signed for the wrong region (around
line 6754). The first was found by engine-backed qualification; the second by
actual provider planning and diagnostic comparisons, not the earlier local
fixtures. Subsequent focused tests protected those specific corrections.
Neither incident establishes that the earlier full local suites were sufficient
or that repeating them later added value.

Agent mistakes contributed materially: serial fixes instead of caller-wide
review, overstating local evidence, repeatedly accepting costly machinery as a
prerequisite, poor credential/runtime planning and confusing progress reports.
These were not tasks the user should have needed to discover or supervise.

## Ranked subtractive remediation

| Order | Existing owner | Remove or replace | Focused success evidence |
| --- | --- | --- | --- |
| 1 | Shared Run qualification and target consumers | Regression execution inside live preparation; age-only historical proof renewal | Matching qualification reused, changed inputs rejected, zero local suites during live plans. |
| 2 | Selector catalog and suite wrappers | Duplicate children, unrelated inputs, oversized fast fixtures | One owner per test; invalidation matrix and measured warm/cold runs. |
| 3 | Command diagnostics/provider adapters | Lossy generic wrapping of known safe causes | Real boundary tests retain safe causes from both streams without secrets. |
| 4 | Operation journal/task and cleanup adapters | Stranded states and ad hoc restart scripts | Resume before dispatch, under uncertainty and after success without duplicate mutation. |
| 5 | Coordinator/observers/package verifier | Conflicting deadlines, per-invocation-only timing | Deadline reaches children; owned processes cancel; timings survive resume. |
| 6 | Collector/acceptance/coordinator standards | Contradictory readiness claims and duplicated handoff validation | One coherent collect/accept path; historical proof is not labelled current readiness. |

Update each owning workflow with its implementation and remove contradictory
instructions. No new runner, approval registry, diagnostic framework or evidence
database is proposed.

Use small local failure-path tests during these corrections, then one measured
ordinary update end to end. Keep deliberate restore/replacement experiments and
full regression suites separate from the ten-minute ordinary-delivery target.
Report wall time and provider-dependent waits separately; local overhead is not
cloud delay.

## Remaining uncertainty

Records cannot recover the native cleanup/clone connection causes, all manual
invocations, or exact total token/delay attribution. Candidate overlap across
all compiler/package/CI combinations needs input-level comparison before deletion.
This is a repository-wide inventory and evidence-led audit of major paths, not
formal verification of every timer.

The next implementation should start with ranked item 1. Neither the proposed
corrections nor all 34 learning discussions are claimed complete.

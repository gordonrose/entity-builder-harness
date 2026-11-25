<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.plan.script-library-simplification
version: 22
status: draft
created_on: "2026-11-23"
updated_on: "2026-11-25"
layer: 06.shared
domain: governance
disciplines: [agentic, architecture, sre]
kind: implementation-plan
purpose: Deliver an understandable script library and a measured reliable verification-to-promotion path through bounded evidence-backed milestones.
portability: {class: source-only, targets: []}
used_by:
- id: repo.report.helpers-audit
  path: scripts/helpers/audit.md
-->

# Script-library simplification programme

## Read this first

This is the single implementation plan for the chat's script-library goal.
Revision 17 withdrew the previous claim that M1–M7 meant the programme was
complete. Revision 18 incorporates the requested complete 690-source-file
review. Revision 19 records the approved P1 ownership repair and passing focused
proof. Revision 20 records P2's selection/context corrections and measured
verification below. Earlier implemented work is retained; end-to-end acceptance
and publication remain open.

The goal is understandable, manageable scripts and fast normal repository work,
with enough evidence to protect the action being taken. This supports the
repository's software-factory strategy: reusable deterministic capabilities
perform work; models choose and connect them. This programme does not build the
entire software factory, finish the application scheduler, or redesign products.

The 2026-11-24 request authorises an audit and this plan update. It does not
start implementation of the revised milestones. A subsequent execution goal
selects the next milestone and supplies its authority. Existing explicit
approvals persist within their scope; do not ask again for an authorised step.
Stop at each milestone for the user's briefing and questions unless they
explicitly change that checkpoint arrangement.

## Current state and evidence limits

The source audit used the recorded November 21 chat worktree:
`/home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-11-21-20-00-phase-1-deployment-script-topology-classification-and-migrat-2261287032`.

Session authority:
`commitLogs/2026/nov/21/2026-11-21-20-00-deployment-script-topology-inventory/README.md`.

At audit start:

- Chat head: `33f479b12453db7f09e2c2cfbc77cecd55952145`.
- Local main and cached origin/main: `13f16e1f10afc313ee3c55ddd854ffb1b9249876`.
- Six commits ahead, zero behind; ten changed paths; source and root clean.
- No remote fetch was made during this audit. Reobserve before integration.
- Last retained promotion report: 20 selected entries, 14 blocked, six
  deferred, zero executed/reused. The sole finding was an uncovered changed
  diagnostic test. Selection preparation took 11.21 seconds; this was not a
  slow behavioral test failure.
- Current inventory: 901 tracked script-area files, including 185 Markdown,
  690 source files (tests and fixtures included), and 26 other data/config files.
- Current catalogue: 184 checks, 107 static routing rules, 227 diagnostic
  review records. A check is a registered command, not a file or one assertion.

The current source findings, counts, exact owners and limitations are in
[scripts/helpers/selection-audit.md](../../../../scripts/helpers/selection-audit.md#2026-11-24-cross-repository-audit).
The initial audit inspected execution/selection/governance chains and important
implementation boundaries. The subsequent full-body review is recorded in
[the source ledger](../../../../scripts/helpers/audit.md#complete-script-source-review--2026-11-24):
one record per tracked source file, including tests, embedded programs and
historical code. This is static evidence, not execution proof, a formal security
assessment or a guarantee of no remaining defects. Remote branch protection,
live state, cold/warm timings and external dependency behavior remain unproved.
P4's source-reading prerequisite is now supplied; approved destinations, final
disposition choices and implementation remain outstanding.

### Preserve this earlier work

| Earlier milestone | Retained achievement | What it does not establish |
| --- | --- | --- |
| M1/M2 | Deferred broad checks, scoped selection, representative local proofs, split Entity Smoke route checks. | All entrypoints agree; every accumulated branch file is covered; normal promotion is fast. |
| M3 | Human review of 34 structurally nominated helper candidates. | Every embedded helper in the script estate was audited. |
| M4/M5 | Persistence task-evidence functions moved to their target binding with a caller-supplied report extension. | Shared diagnostics have no remaining persistence dependency; every historical caller was correctly migrated. One reader required a subsequent repair. |
| M6 | Existing script-admission standard added. | Layout migration or contradiction-free enforcement is complete. |
| M7 | Focused selection mechanics and reuse of unchanged subject evidence implemented. | The actual branch is merge-ready. Its shared diagnostic test still lacks a direct routing rule. |

Historical commands and measurements remain in the helper audits and session
log. They are evidence at their recorded revisions, not current passing proof.

## Completion contract

The programme is complete only when all the following are supported by evidence:

1. Each ordinary action has an explained required check set; broad housekeeping
   cannot enter it through an unrelated rule, review record or deferred parent.
2. Changed implementations, tests, fixtures, declarations and renamed/deleted
   inputs have their real owner or an explicit justified non-applicability.
   "No selected checks" is not automatically a success.
3. Commit, integration, remote automated verification, package and deployment
   callers agree on their responsibilities. Differences are intentional and
   recorded. Passing one does not claim the others passed.
4. Approved folder migrations are complete with active callers and historical
   evidence readers preserved. Remaining files have an explicit retain decision
   or an openly unaccepted/deferred item; "all cleaned up" cannot hide either.
5. Existing successful evidence is reused when its actual inputs still match.
   Local source proof, built-image proof and live observations stay distinct.
6. Required checks pass on the full candidate containing the intended base.
   The authorised changes reach local main and remote main, with hashes and
   outcomes recorded. If either is not authorised/available, report that
   milestone as ready or blocked, not delivered.
7. The user can find active commands, identify their owner and purpose, and
   explain what runs for an ordinary change from the existing documentation.

An unchanged source file alone does not justify reuse: its dependencies,
configuration, runner, test assertions or relevant runtime may have changed.

## Owners and vocabulary

A capability is a group of files doing one job. A check is a command that
provides evidence for a named risk. Selection chooses checks; evidence reuse
decides whether a selected check already has a matching successful result.

Use the existing owners:

| Concern | Existing authority |
| --- | --- |
| Selection and dependencies | `scripts/repo/check-selection/checks.yml`, `script.py` |
| Trusted local evidence | `scripts/repo/check-selection/local_cache.py` |
| Results, timing and summaries | `scripts/repo/check-selection/execution_policy.py` |
| Diagnostic adoption/review relationships | `scripts/repo/diagnostic-coverage/script.py`, `reviews.v1.json` |
| Chat, worktree, commit, refresh and promotion | `.agentic/00.chat/`, `scripts/00.chat/`, `scripts/repo/commit-gates/` |
| Remote automated checks | `.github/workflows/delivery-coverage.yml` and relevant publication workflow |
| Workspace build and package preparation | `scripts/repo/workspace-build/`, `scripts/04.deploy/lifecycle/40-package/` |
| Human audit decisions | `scripts/helpers/audit.md`, `selection-audit.md` |
| Path moves | Existing layer migration plans and `.agentic/01.harness/workflows/migrate-artifact-paths.md` |
| New scripts | `.agentic/01.harness/standards/script-admission.md` |

No second registry, scheduler, evidence store, general wrapper layer or global
dependency classifier is part of this plan. Existing catalogues remain execution
authority; audit tables are review records.

## Desired operating policy

P2 must reconcile these requirements with the existing standards and code
before changing gates. The table is a target, not a claim already implemented.

| Action | Required decision and work | Work kept separate |
| --- | --- | --- |
| Code editing | Focused feedback for changed behavior and direct affected contracts; report any remaining integration obligations. | Unrelated architecture census and provider operations. |
| Build | Compile/assemble declared inputs and validate build output requirements. | Whole-repository hygiene and live proof. |
| Commit | Existing staged-content, session, metadata and commit-boundary checks; PostgreSQL-version policy remains at commit. | Broad integration suites unless explicitly required by the changed boundary. |
| Merge | Whole candidate versus its selected base; required affected local behavior and direct consumer contracts. | Unrelated hygiene and package/live execution. |
| Push | Confirm verified candidate, destination, remote freshness and normal history advance; reuse matching local proof. | Re-running identical proof because Git transport is occurring. |
| Package | Bind local qualification to the immutable candidate and prove actual packaged contents/behavior. | Repeated source suites with unchanged valid evidence. |
| Deploy/recover | Consume qualified artifact, check fresh target conditions, apply and observe through the existing operation owner. | Local architecture scans; undeclared tests or silent repair by smoke checks. |
| Runtime smoke | Prove deployed identity and essential behavior. | Full regression and build work. |
| Periodic full regression | Retain broad architecture/topology/regression commands and failures for deliberate execution. | Automatic normal-work execution; adding a nightly scheduler in this programme. |

A build-tool, selector or hygiene-check implementation change still needs its
own focused proof. A directly affected consumer may legitimately need broader
proof. Record the risk and cost; never remove it merely to make counts smaller.

## Common execution procedure for every milestone

### Scope control after the full review

The source ledger is not an instruction to repair every issue before merging.
Use its finding identifiers to make bounded change packets:

- P1 repairs the current candidate's missing ownership edge only.
- P2 fixes normal selection and evidence correctness, including the newly found
  changed-path context omission in reusable evidence. Do not rely on a cached
  partial Core test result as proof of the full Core suite.
- P3 repairs the integration handoff and publishes the authorised checkpoint.
- P4 proposes/approves layout using the completed review; do not repeat all
  690 reads if the recorded source snapshot is unchanged.
- P5 handles actual repeated build/package proof and its trust boundaries.
- P6 handles approved owner changes. Source-inferred defects in retained
  staging/RAG commands become prerequisites to relying on or modifying the
  affected behavior, not unrelated global merge gates. Unrelated findings in
  the same owner remain retained risks. Record a user's
  explicit deferral rather than claiming those owners safe or fixed.

Within each packet distinguish confirmed source contradictions, suspected
runtime consequences, and measured behavior. Only the last supports performance
or operational-success claims. Never execute an unfamiliar test merely to see
what it does: this audit found tests that mutate the checkout, move installed
dependencies, open fixed ports, or can reach cloud commands.

### Procedure

1. Resolve the session/worktree from the session log and use its explicit path
   for task commands. The environment's November 6 cwd is not this chat's home.
   Read status/diff first; preserve unrelated changes.
2. Read the milestone's named owners, then record one bounded change packet in
   this plan or the existing audit: exact files, real callers, named risk,
   expected required/deferred checks, proof command, compatibility and recovery.
   Use source/imports/callers, not a directory label, as evidence.
3. Review the complete packet before final testing. Fix conflicting active
   instructions and callers at their owner. Keep new discoveries in this plan,
   not a parallel plan or a chain of speculative enhancements.
4. Implement only that packet. New files need metadata; a new source file over
   50 code lines excluding metadata needs prior approval. Do not fragment code
   into meaningless files to evade that rule.
5. Run the smallest existing proof that rejects the named bad outcome. Extend
   an existing test only for a real missing behavioral assertion. Do not write
   tests for prose changes or add a suite that mirrors the implementation.
   Before invoking that proof, inspect its recorded child effects and isolation:
   serial execution can also overwrite checkout fixtures, inherit credentials,
   or strand renamed dependencies. Use its supported isolated route; if none
   exists, resolve that bounded safety issue before execution. Do not substitute
   an arbitrary live command or run every test to discover what it does.
6. Prepare metadata/verification inputs with the existing workflow. Inspect the
   full branch selection before executing expensive integration proof. A focused
   example is supplementary, never a substitute for the accumulated candidate.
7. Record terminal results, actual executions/reuse, timings, remaining risks,
   and next step. Keep successes tied to their original inputs. Review later
   edits for affected invalidation instead of rerunning everything.
8. Brief the user at the milestone boundary and stop there. The next milestone
   needs their explicit go-ahead. Within an authorised milestone, continue
   ordinary fixes without repeatedly asking permission.

Use a report record with these fields, not a new file format or database:

~~~text
Milestone / bounded step / status:
Source head, selected base ref and hash, dirty input paths:
Files and consumer inventory:
Named risk and intentionally deferred risks:
Expected required-now / later-stage / explicit-only checks:
Observed complete selected set and explanations of differences:
Proof command, terminal result, run reference, executed/reused counts:
Planning/setup/execution/total time; advisory estimate met or missed:
Correction made or precise blocker; next incomplete step:
Git approval and actual commit/merge/push outcomes:
~~~

## Milestone P1 — Restore complete ownership of the current candidate

**Outcome:** the current branch has no unknown executable inputs, and its
required work is visible before a promotion attempt. This is the first
implementation milestone, not another repository-wide test sweep.

1. Reproduce the current finding with the full-diff plan in the command
   reference below. Preserve the result and distinguish dependency access
   failures from catalogue findings.
2. In `checks.yml` add the missing direct `repository_inputs` edge from
   `scripts/repo/diagnostic-coverage/smoke-test.py` to the existing
   `diagnostic-catalog-readers` runner. Its declared consumed inputs alone do
   not create this trigger. Do not restore every diagnostic review as a caller.
3. Update the existing real-catalogue expectation in
   `repository_contracts_test.py`,
   `test_actual_runtime_and_runner_changes_select_independent_proof`.
   Require the actual owner and reject unrelated runtime expansion. Execute
   this existing method, not the whole slow collection.
4. Review every entry in the full branch plan. Name which changed path or
   prerequisite requires it; record genuinely expected extra checks. Require
   an explained complete set, not only a small required/forbidden subset.
5. Measure the existing reader runner when execution is appropriate. It
   compiles diagnostic roots and runs broad reader tests; the small routing
   edit does not make that command small. If its cost blocks the objective,
   record its concrete compilation/test responsibilities for P2/P5.
6. Correct the earlier plan/audit interpretation that "test assertions do not
   change runtime" meant the changed test needs no verification owner.

**Owners:** `checks.yml`, `repository_contracts_test.py`, existing selection
audit. Inspect `diagnostic-coverage/verify.sh` and the review rule producer;
do not change their behavior without a new explicit substep.

**Proof:** existing focused actual-catalogue method, existing promotion
mechanics command, then the real full candidate plan. The latter must have
no uncovered input. The actual required behavioral checks still have to pass
before P3; a plan alone cannot satisfy them.

**Exit:** full selected set explained; no coverage gap; required proof costs
and any blocked checks named. No claim of merge readiness yet.
**Recovery:** inspect the existing runner and ownership edge; do not create a
new runner, mark the path documentation, or waive the uncovered input.

### P1 approved change packet — 2026-11-24

- Authority: the user approved P1 with "go" after the two-file increment was
  explained. Stop for briefing at this milestone; P2 remains unstarted.
- Source: HEAD `33f479b12453db7f09e2c2cfbc77cecd55952145`, selected cached base
  `13f16e1f10afc313ee3c55ddd854ffb1b9249876`. The existing plan, two audits and
  session log were already dirty. Preserve them; no Git publication is part
  of this packet.
- Files: add one direct `repository_inputs` mapping in `checks.yml`; strengthen
  the existing real-catalogue method in `repository_contracts_test.py`.
  Consumers: the selector's direct branch/path planning, existing diagnostics
  `verify.sh --unit catalog`, and the existing test facade. The wrapper already
  compiles diagnostic roots, checks generated exports and runs this test file.
  Its command and receipt input closure remain unchanged.
- Named risk: a changed executable test is unowned even when its runner happens
  to be selected through a different changed source. Required assertion: that
  test selects `diagnostic-catalog-readers`, excludes unrelated runtime owners
  and has no uncovered-input finding. Existing general predicates and diagnostic
  code meanings do not change; this is verification registration/test support.
- Baseline reproduced: full committed-candidate plan exited 1 with exactly
  `changed-input-uncovered` for the diagnostic test. It selected 20 entries
  (14 pending, six deferred), executed/reused none and took 16.756 seconds
  internally (about 18 seconds including invocation). Disposable evidence:
  `/tmp/script-p1-before.wnCul5.json`.
- Proof: run the existing focused real-catalogue method, the six existing
  promotion-mechanics methods, then replan the full committed diff and pending
  source paths separately. Full-candidate output remains provisional because
  this packet is uncommitted. Record every selected owner and its trigger.
- Verification budget: approximately one minute per focused command; report
  overruns and continue to terminal result. Inspect and measure the registered
  reader only after its fixture effects/input requirements are understood;
  defer broad consumer corrections to P2/P5 with exact reasons.
- Recovery: remove/correct only the new mapping/assertion if disproved, keeping
  unrelated changes. No new runner, runtime behavior, cloud action or fixture
  framework is introduced.

### P1 completion evidence — 2026-11-24

P1 is complete locally. One direct rule now routes the shared diagnostic test
to its existing reader runner. The existing catalogue assertion requires that
owner and rejects unrelated Core/server/product/composition expansion. Its
bootstrap-declaration case also contained a stale expectation for broad
mechanics; it now requires the already-established focused promotion owner and
rejects broad mechanics. Production selection beyond the added rule is unchanged.

Parent self-review checked both source diffs against the packet and actual
wrapper/readers; no new predicates, diagnostic meanings, module exports or
runner were introduced. Test assertions remain verification support, but a
changed test still needs its real verification owner. The previous empty-set
expectation did not prove that ownership and is corrected rather than waived.

| Evidence | Terminal outcome |
| --- | --- |
| Existing actual-catalogue method | Passed, 30.409 seconds, after the stale bootstrap assertion was corrected. The first exploratory run failed only that bootstrap case; the new diagnostic ownership case passed. |
| Existing six promotion-mechanics methods | All passed, 6.896 seconds. These direct fixture results do not seed registered integration proof. |
| Registered `diagnostic-catalog-readers` | Passed, one executed / zero reused; 67.510 seconds execution, 88.070 seconds total. It compiled actual roots, checked exports and ran existing reader/adoption/wrapper tests. |
| Full committed branch plan with current catalogue | Planned, zero findings, 20 entries: 14 pending local / five deferred local / one deferred package. Internal planning 9.020 seconds. Required behavior remains pending except the separately executed reader. |
| Pending two-source-path preview | Planned, zero findings, 55 entries / 54 unique identities, 26.298 seconds. This ordinary route differs materially from direct recorded promotion and remains P2 evidence, not acceptance. |

The complete 20-entry trigger inventory is in the P1 section of the existing
selection audit. In particular, reviewed test references select delivery access,
payload assembly and module-index owners; a deferred Entity aggregate still
selects a candidate child. Those explained expansions remain P2 work. No broad
suite was run merely because it appeared in a planning report. Existing known
time estimates total 4,450 seconds but are incomplete and include deferred rows;
they do not establish an actual 74-minute run or an accepted delivery budget.

Reader run reference:
`.cache/test-runs/20261124T235427Z-8d22ce3bc853403186dbcee5db34a8d6/report.json`.
Disposable plan references: `/tmp/script-p1-after.ghiP43.json` and
`/tmp/script-p1-pending.U2gKxI.json`. Pending preview invocation was corrected
after argument parsing rejected combining mutually exclusive `--paths`/`--ci`;
that rejected invocation executed no checks. Final source/header/whitespace and
candidate-plan confirmation are recorded in the session log.

All evidence uses the pinned HEAD/base above with current dirty contents.
There was no commit, merge, push or live operation. The two changed source files
are an explicit delta to the 690-file audit snapshot; that historical snapshot's
digest is not a claim that these newer bytes were part of the earlier reading.
P2 requires user approval at this checkpoint.

## Milestone P2 — Make selection and evidence rules coherent

### Approved execution packet — 2026-11-25

Post-publication completion follow-up: source checkpoint aa294fd0 (task commit
ccdfd5cb) passed the actual root readiness gate in 1293 seconds, 42 local command
instances passed (35 executed/seven reused), zero findings; six broad checks and
nine later-stage operations remained deferred. It was merged/pushed normally as
21365c767f4b94ba4e6e4d2ac22d048ab6ed8bf1, verified directly on remote main.
No source qualifications are to be repeated merely for this completion record.

The governed source-identical completion refresh exposed a real empty-diff
selector defect: an implicit empty changed-path list is rejected as an invalid
explicit task context. The parent incorrectly invoked apply before consuming
that preliminary failure. Apply advanced the chat to e78e50d1, whose tree equals
published main exactly, then its post-check failed. Both branches/worktrees are
clean; main/remote are unaffected, the preflight remains retained, and no source
was lost or overwritten. Record this sequencing error, not a passing refresh.

Bounded correction: normalize an implicit empty impact context to no context;
keep explicitly supplied empty aggregate context invalid. Extend the existing
real CI fixture to prove both flag spellings run no commands and do not claim
complete affected integration for an empty diff. Only script.py/mechanics_test.py
and their existing review records change as executable support. The existing
promotion dispatch also includes this actual-CI method, so the regression runs
through the normal registered owner rather than an extra test layer. Use normal
prepared commit/proof. The existing clean preflight may fast-forward to the
reviewed child commit: it must preserve the recorded base and source ancestry,
have an identical tree to the tested active candidate, and pass its normal
selector before retrying apply/cleanup. No patch copying, history rewrite or
new recovery engine is allowed. Finish the completion publication before P4.

The user approved P2 with "ok proceed" after its selection, chain-reaction and
saved-result responsibilities were explained. Work in the recorded November 21
worktree; preserve all P1 and audit changes. No commit/publication or cloud
authority follows from this packet. Stop for the P2 milestone briefing.

Implement step 9 first so ambiguous subset receipts cannot qualify later proof.
Starting owners: `script.py`, `local_cache.py` and the existing changed-context
method in `mechanics_test.py`. Bind normalized effective changed paths or full
execution into both preparation and result identities; propagate it through
the existing aggregate binding. Preserve keys for non-context-sensitive checks.
Reject legacy context-sensitive receipts lacking this contract. Existing
fixture proof must cover same-context reuse, different subsets, full execution,
outside-owner paths and aggregate child context. No new runner/cache is needed.

Then reconcile cadence/member expansion, diagnostic review triggers versus
consumed evidence, report decisions, and actual local/CI callers at the owners
below. Record named risks and exact required/deferred routes before narrowing
selection. Existing metadata/review records must be updated only for source
actually reviewed. Use focused existing cases, final actual-candidate planning
and representative consumer cases; execution cost targets are advisory, with
terminal outcomes retained. Product behavior and live deployment remain outside
this verification-policy change.

**Outcome:** retained work cannot leak into normal execution, real consumers
remain protected, and all normal callers follow one explained policy.

Work in these bounded substeps, retaining existing APIs unless a concrete
consumer requires a change:

1. Write the selection truth table in the existing test-execution standard:
   ordinary commit, integration, explicit request, aggregate request and future
   periodic execution. Resolve the current `candidate/hygiene/deferred`
   mismatch. Today direct promotion drops hygiene while ordinary integration
   can execute it. Make any intentional difference visible.
2. Correct dependency expansion in `script.py`: an automatically deferred
   aggregate cannot select candidate children solely by membership.
   Independently selected children remain required; explicitly requested
   aggregates retain complete members and failure propagation. Extend the
   existing deferred-check mechanics fixture only as needed.
3. Audit the repeated diagnostic-review relationships for the shared reader
   test, `mechanics_test.py` and `repository_contracts_test.py`.
   Separate review evidence references from inputs the command actually
   consumes, within `review_rules`, `review_bindings`, `reviews.v1.json`
   and the existing proof-input construction. Reconcile trigger AND receipt
   invalidation edges together. Remove the temporary filename exception only
   after the general ownership rule covers its case.
4. Preserve positive/negative proof: changing a real producer still selects
   affected readers; changing a test selects its runner; modifying a consumed
   input invalidates reuse; unrelated documentary evidence does not.
   Do not remove all test paths, review contracts, or dependencies globally.
5. Update `execution_policy.py` to distinguish required-now, later-stage,
   explicitly retained and not-applicable work. Report required success
   independently of deferred rows. Estimates count commands due to execute;
   unknown estimates remain unknown. Ownership gaps must retain all useful
   findings before expensive preparation of checks that cannot run.
6. Compare local promotion and `.github/workflows/delivery-coverage.yml`
   selection against the same pinned base/candidate. Reconcile the difference
   between `--ci --changed-only` and `--ci` at their owners. Do not merely
   copy the narrower flag into CI: preserve real direct consumers, shared
   contracts, deletion/rename handling and configuration impact. The current
   selector does not require its supplied head hash to match checkout HEAD;
   enforce that identity at the owning selection/integration boundary and
   distinguish pending-path previews from final committed-candidate proof.
7. Resolve delivery census placement with its named risk: detecting newly
   unregistered delivery entrypoints. Today promotion and CI unconditionally
   run it while selector documentation suggests deferral. Keep it where that
   risk warrants it; narrow only with a documented complete trigger covering
   additions, removals and declarations. Reconcile active prose either way.
8. Exercise the representative matrix below using the same mechanisms normal
   callers use. Retain full explicit routes for deferred checks; document
   required task preparation for explicit aggregate commands.
   Acceptance reuse for context-sensitive runners must wait for step 9's
   identity correction and old-receipt invalidation proof; selection previews
   alone may be inspected earlier. Do not accept the known ambiguous receipts.

9. Bind the actual context passed to a context-sensitive runner into its
   preparation and result identity. `script.py` currently fingerprints the
   `changed_path_context` boolean but supplies a separate changed-path list in
   `REPO_CHECK_CHANGED_PATHS`. `packages/core/tests/run-runtime-tests.mjs`
   uses that list to run a subset, while an unset value runs the full suite.
   In `script.py` and `local_cache.py` (including receipt revalidation and
   aggregate child preparation identities), normalize the effective context and
   distinguish partial/full execution. Cover identical source bytes with two
   different subsets, subset-to-full, same-context reuse and an outside-Core
   change. Existing generic receipts must not silently qualify the new contract;
   use the existing identity/version mechanism, not a second cache.
10. Trace the selected command's real child/import graph, not just catalogue
    members. Current examples: shared recovery tests import staging fixtures;
    generic diagnostics tests import a persistence restoration controller;
    export smoke combines archive checks with public dispatcher/ownership
    integration. Keep true direct-consumer assertions; transfer unrelated
    fixture ownership only as an approved bounded packet. Do not mark an
    aggregate lean solely because it selects one command.

**Proof:** reuse mechanics and actual-catalogue cases for ownership, deferred
aggregate children, independent children, real consumer changes, deletions,
failure propagation and reuse. Execute relevant existing cases; broad selector
regression is not automatically a prerequisite for every edit.

**Exit:** truth table, implementation, CI and public documentation agree;
actual candidate plan plus representative cases have no unexplained checks or
unknown inputs; required evidence passes or P2 remains incomplete.
**Recovery:** correct the recorded producer/consumer owner. A new risk expands
that bounded inventory; an unrelated enhancement becomes an explicit backlog
item. Never silently rename a failing check "hygiene."

### P2 completion evidence — 2026-11-25

P2 is complete at its bounded implementation/selection-proof boundary. It does
not establish complete affected integration or publication. The user approved
this milestone and resumed it after the editor crash; no new worktree or goal
was created. The exact 13 changed owners, complete selected set, retained/manual
routes, consolidated self-review, corrections and findings are in the current
P2 section of `scripts/helpers/selection-audit.md` (revision 9).

**What changed:** ordinary commit/integration retain broad maintenance checks
without executing them; a deferred parent cannot activate unrelated children.
Actual consumed dependencies still select/invalidate their proof. Local and
protected CI callers follow one consumer policy; contained commit preparation
stays bounded. Context-sensitive proof binds normalized actual changed paths
or full execution, including nested children; old ambiguous receipts are not
accepted. Reports distinguish required-now, retained and later-stage work, and
unknown estimates remain unknown. Supplied checkout identity and clean
committed-candidate execution are enforced. Product behavior is untouched.

**Review and sensitivity:** the parent reviewed actual source diffs, input and
caller closure, diagnostic predicates and counterexamples. Existing cases reject
subset/full collisions, lost shared-input invalidation, citation overreach,
deferred-child leakage, mismatched checkout, dirty execution and false success
from retained rows. Source-matched records were refreshed only for the six
reviewed files; partial/support debt remains. Fixture corrections supplied an
explicit catalogue owner, kept PostgreSQL database proof at package stage and
ignored generated counters without exempting real untracked source. The final
help-only correction changed no selection algorithm, and its owner was rechecked.

| Evidence | Terminal result |
| --- | --- |
| Existing 20 context/review/aggregate/reporting cases | Passed, 47.412 seconds. |
| Six existing commit/lockfile/catalogue/prose cases | Passed, 10.277 seconds. |
| Existing actual-path routing method, 14 real-path examples | Passed, 164.988 seconds. Pure selection evidence, not source freshness or runtime acceptance. |
| Registered promotion and reader owners | Passed; two executed / zero reused, zero findings; 119.290 seconds total. Promotion 4.346 seconds; reader 96.404 seconds. |
| Unchanged registered replay | Passed; zero executed / two reused; 10.589 seconds total, zero command seconds. |
| Final help-only correction | Registered promotion passed again, reader reused; zero findings; 15.359 seconds total / 4.171 seconds child execution. |
| Local `--ci --changed-only` versus protected `--ci` | Identical keys/status/dependencies/decisions, zero findings; 32 instances / 31 IDs: 17 required, six retained, nine later-stage; 21.306 / 21.249 seconds. |
| Accumulated-plus-pending named-path preview | Zero findings; 19 paths, 35 instances: 21 required, five retained, nine later-stage; about 50 seconds; no execution. Different catalogue comparison base, not a CI-policy disagreement. |
| Independent physical delivery census | Passed; 521 entrypoints, six routes, zero gaps; about 12 seconds. Selector route discovery is not this census. |
| Full diagnostic adoption scan | Failed; 27 stale reviews and three unreviewed files, all sources AND records unchanged from HEAD. Retained as known P3 pre-commit preparation, not silently refreshed or waived. |

Registered run evidence (ignored local observations, not portable authority):

- Initial final owners:
  `.cache/test-runs/20261125T005919Z-63e4f429c91946b192a1a8562e4f7fb9/report.json`.
- Unchanged replay:
  `.cache/test-runs/20261125T010045Z-c8628a330eae46759426158661051cd7/report.json`.
- Final help correction:
  `.cache/test-runs/20261125T010239Z-5fb87b5a035445e1bd78c93f40ec3990/report.json`.

The crash-interrupted runs and initial failing fixture runs remain incomplete/
failed observations, not passes. Explicit checks prove their requested boundary,
not all 17/21 planned local obligations. Full mechanics/repository contracts,
full affected integration, package/live proof, remote freshness and publication
were not performed. Current previews remain dirty and provisional; P3 must
replan and prove the exact committed candidate. No ten-minute delivery claim is
made. Metadata/whitespace and source-review freshness for the six edited sources
are checked separately from the retained global adoption failure.

No new source files or broad machinery were added. P1 and the helper audit are
preserved; no fixtures were moved. Actual nested staging/restore/test imports
remain named P5/P6 ownership/cost work. The README-writing guidance kept the
command documentation tied to source rather than inventing a new procedure.

Stop for the P2 briefing. **P3 has not started and requires explicit approval**;
no commit, merge or push is authorised by this milestone.

## Milestone P3 — Finish and publish a reliable promotion path

### Approved execution packet — 2026-11-25

The user approved P3 with "proceed" after the P2 briefing named publication as
the next milestone. This authorises its bounded implementation and governed
commit/local merge/normal push outcome; no history rewrite, unrelated cleanup,
cloud operation or task-worktree switch is authorised. Root main is a clean
integration target. A fresh `git fetch origin` succeeded; local and remote main
remain 13f16e1f10afc313ee3c55ddd854ffb1b9249876. Preserve all pending P1/P2/audit
work, and stop at the P3 milestone briefing before P4.

First bounded owner repair: workspace report plus worktree path helper preserve
missing registration rows while strict selected-target verification remains;
rehearsal pins its chosen base in the existing preflight branch's Git metadata
and application consumes that exact commit; lifecycle baseline/rename reads and
log-deletion parsers distinguish failed observations from absence. Existing
local-merge, refresh, lifecycle and deletion smoke fixtures are the proof owners.
No portable-install reconstruction or additional execution registry is needed.
Reconcile corresponding workflow wording and source-matched diagnostic reviews.

Diagnostic predicate/consumer review for this packet: successful registration
with missing directory becomes an absent report row ONLY in reporting mode;
failed Git/metadata observations remain unavailable and strict target actions
still reject. An absent preflight base, non-hash base or base outside the
rehearsed ancestry blocks before fast-forward; local main is not substituted.
Lifecycle distinguishes successful empty HEAD inventory from failed inventory,
content and rename observations; all failures stop planning before writes.
Deletion distinguishes parser negative (1) from failure (>1), rejects protected
logs and suppresses native parser text. Candidate-code bootstrap requires the
same Git repository, exact registered target branch and clean implementation;
root/target clean-state and post-proof drift checks remain. Existing fixed
failure vocabulary and partial diagnostic status are retained; no new product
catalogue, provider effects or automatic mutation replay is introduced.

Exploratory proof: all four existing owner smoke tests passed. The local-merge
fixture additionally passed clean candidate bootstrap/dirty implementation
rejection. The real selector/cache refresh fixture passed against a newer
non-main base and reused its two affected local commands (2.408 seconds). Its
stale expectation for unchanged runnable-program proof was corrected without
adding that command to the selection. Final registered proof follows stable
metadata/reviews. Engineering budget for the final integration invocation is
ten minutes; overruns remain observations, not permission to kill valid work.

P2's tentative classification of all 30 adoption findings as publication
blockers is corrected by actual caller inspection: every source was already
identical on accepted main, and the full adoption census is explicitly retained
under the approved P2 policy, not invoked by commit preparation/extension.
Only current changed sources need fresh task reviews; any actual gate failure
still blocks its operation. Refresh the reviewed P3 gate/application records
and other edited-source records, not all accepted-baseline debt. The unchanged
missing catalog/helper/binding reviews stay visible maintenance debt rather than
an unrelated product-review campaign before publication. No mandatory gate was
removed or given an ignored nonzero result.

Inspect the candidate/main verifier/helper versions before the real gate; any
required bootstrap correction belongs to that same existing command/workflow.
Source-review the 30 known adoption findings before refreshing their records;
do not infer adoption from a matching hash. Run full candidate proof only after
implementation, review and task preparation stabilize; preserve terminal results
and reuse unchanged proof. This is an integration task, not a new broad script
reorganisation.

**Outcome:** this chat's verification improvements reach main and remote, with
one traceable attempt and matching evidence. Folder migration is not a
precondition.

P2 pre-merge observation (2026-11-25): the full diagnostic adoption scan reports
27 stale source reviews and three unreviewed sources. All 30 source files and
their review records are unchanged from HEAD; P2's six refreshed source records
are not among them. Do not mass-refresh these hashes. Before committing, use
the existing source-review/adoption workflow to reconcile the current candidate
and the actual gate's requirements. The three missing records are for
`scripts/helpers/catalog.py`, `scripts/repo/commit-gates/script.sh` and the
Core Server Persistence `deployment-diagnostics/binding.py`. The complete safe
finding list is retained in the P2 section of `scripts/helpers/selection-audit.md`.
This is a known publication preparation issue, not permission to skip a gate or
expand P2 into unrelated runtime changes.

1. Reconcile `report-chat-workspaces/script.sh` with its caller policy.
   The current report aborts on an unrelated missing October worktree.
   Report unavailable rows and complete the inventory where possible, while
   the selected chat's readiness check still rejects an unavailable target.
   Define the exit-status consequence in the workflow; do not ignore a
   nonzero result or prune unrelated worktrees.
2. Check refresh consistency in `rehearse-refresh-from-main` and
   `apply-rehearsed-refresh`. The former accepts a chosen base; the latter
   currently validates against local `main` after applying. Preserve the
   chosen base identity through rehearsal, proof, application and retry.
   Reuse existing fixtures for a stale local main and a source already
   advanced before a failed follow-up.
   Also inspect the real handoff, not just rehearsal replay fixtures: the
   existing replay fixture does not exercise the selector with a non-main base.
3. Choose one governed integration route. A clean root uses the local-main
   workflow. The current remote-promotion alternative is ONLY for a root
   containing unrelated work; global inventory failure is not that condition.
   If a broader alternative is needed, update its owning workflow explicitly.
4. Follow the existing before-commit checklist and preparation commands.
   Raw Git commits do not automatically run the repository's workflow gates:
   no installed hook was observed. Stage only reviewed task paths, record the
   commit, and checkpoint the current session through its existing owner.
   Inspect the lifecycle/deletion observers actually invoked on this route.
   R-15/R-07 identify failed Git/parser observations treated as absence: correct
   that bounded fail-closed behavior before relying on those observations.
   Do not expand this into a whole metadata/session rewrite.
   Source reading found a separate exported-installation defect: portable
   before-verification calls metadata/index commands excluded from that export,
   while its smoke fixture supplies stubs. This repo contains those commands;
   do not make portable-install repair an unrelated publication prerequisite.
   If this packet changes the exported route, prove the real generated file
   set without substituting those missing commands.
5. Reobserve the intended remote/base after authorisation, refresh if needed,
   and inspect the complete candidate plan after commits/checkpoints/refresh.
   Run required local checks once through the trusted selector, capturing a
   bounded summary and terminal outcome. Reuse matching receipts on the gate.
6. For any independently authorised integration checkout, state dependency
   setup and existing `--reuse-from-worktree` use explicitly. A fresh worktree
   has no automatic dependency installation or trusted cache. Never manually
   copy report JSON into the evidence store or share mutable compiled outputs.
7. Before invoking the readiness gate, identify the version of every script and
   helper it will execute. Relative root commands run main's older code; even
   an absolute candidate verifier currently imports helpers from its caller's
   root. Compare those files with the candidate. Run the repaired inventory
   reporter from the active chat, and use the existing root gate unchanged if
   its behavior is compatible. If it lacks a required repair, amend the owning
   workflow and existing command to support the reviewed, committed candidate
   implementation while preserving the root as the integration target. Keep
   code/helper versions coherent and validate the registered repository and
   candidate identity. Document the exact supported invocation before using
   it. Do not copy task files into main, bypass its safeguards, or add a
   parallel gate. This bootstrap is part of P3, not a surprise at merge time.
8. Run the actual readiness gate from its required directory. The root checkout
   is used only for the authorised integration operation; task editing remains
   in the recorded chat worktree. An eligible result permits the already
   authorised merge/push; it does not itself grant external authority.
9. Merge and push through the existing workflows. Verify the promoted source
   is contained in local main and the observed remote main. If a normal push
   is rejected because the remote moved, refresh/requalify affected inputs;
   never force or restart completed unrelated work.

**Owners:** `scripts/00.chat/reporting/report-chat-workspaces/`,
`worktree/paths/lib.sh`, `main-refresh/`, `local-merge/`,
`remote-promotion/`; corresponding workflows and before-commit checklist.
Inspect their existing smoke tests before selecting the smallest proof.
The exact readiness entrypoint is
`scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh`;
the route owners are `.agentic/00.chat/workflows/chat-promote-to-main.md` and
`chat-promote-to-remote-main.md`. Never substitute a guessed command name.

**Exit:** required full-candidate verification passed; source/main/remote hashes
and command results recorded; no uncertain operation or required process left
running. Report first-pass time, retries, planning and reused/executed checks.
A PR/manual-only CI workflow is not proof that a direct main push triggered CI.
Branch protection must be observed if the chosen remote route relies on it.

**Recovery:** use the failure table below. Missing external authority or access
can block publication, but does not justify a false "delivered" status.
**User checkpoint:** brief this usable release before broad reorganisation.

### P3 published checkpoint and completion record — 2026-11-25

The implementation checkpoint is delivered: task ccdfd5cb and qualified source
aa294fd0ac95814740935e6f78108366c88625d9 reached local and observed remote main
at 21365c767f4b94ba4e6e4d2ac22d048ab6ed8bf1 through a normal no-ff merge/push.
The merged tree exactly matched the qualified source tree. Root and source
were clean, main had not moved after a fresh fetch, and no force/history rewrite,
unrelated cleanup, task-worktree switch or cloud operation was performed.

The actual readiness gate passed on its FIRST source-qualification attempt:
42 required local command instances, 35 executed/seven reused, zero findings;
six retained checks and nine later-stage operations stayed deferred. Gate wall
time was 1293 seconds; selector time 1286.388 seconds, command time 1218.685,
planning 16.884, fingerprints 15.702, runtime identity 31.867 and receipt checks
2.773 seconds. This MISSES the ten-minute target; no fast-delivery claim follows.
Largest commands: task route 345.079 seconds, credential route 242.064,
persistence composition 114.088, restart route 99.317, acceptance regression
81.986 and Entity composition base 70.860. P5 retains this concrete connected-
fixture/qualification cost work; passing does not mean the bloat is resolved.
Evidence: .cache/test-runs/20261125T014918Z-83ac0867f7ea4dda88c013ff0ab43137/report.json.

The source-identical completion refresh then exposed the empty-diff false gap
and the sequencing mistake recorded above. The bounded implicit-context fix
passed three existing context/CI cases (6.718 seconds); the existing registered
promotion owner now includes the actual-CI case and passed in 12.293 seconds.
Evidence: .cache/test-runs/20261125T020047Z-e9ae7ad69121401ebac8d0006a1801f5/report.json.
This completion follow-up carries that fix and these records together. When read
from accepted main, it is published too; do not repeat P3 merely to insert a
self-referential future commit hash. Observe actual Git containment instead.

Existing helpers/audit work is retained; no new source files, registry, scheduler
or wrapper framework were added. Unchanged accepted-baseline adoption debt and
actual nested legacy fixtures remain explicit, not silently fixed or newly
universal blockers. Full retained suites, package/live proof and remote CI
execution are not claimed. The PR/manual-only workflow is not evidence of CI
running after this direct main push.

Stop for the user briefing/questions. P4 is the next implementation milestone
and requires explicit approval; this completion does not authorise migration.

## Milestone P4 — Complete a source-backed capability disposition

**Outcome:** a finite, reviewable set of retained capabilities and approved
moves covers the current script estate.

1. Refresh the tracked-file census and classify source versus docs/data;
   include untracked work separately. The historical 713 number and the
   generator's current 715-file denominator are not counts of runnable checks.
2. Consume the completed 690-file source ledger in `scripts/helpers/audit.md`.
   Reconcile current tracked source names and changed bytes against its pinned
   head; review only additions, changed files and newly affected callers.
   Use roles: operation, helper, test, fixture, wrapper, selector. Preserve
   mixed responsibilities; no path/filename is a semantic verdict.
3. Record owner, purpose, live consumers, execution stage, named risk, proof
   route, invalidating inputs and retain/split/move/isolate decision. Flag
   unknown groups visibly; do not mark complete until the fixed inventory has
   no unexplained group. This is not 690 separate refactoring tasks.
4. Use the existing topology projector/catalogue only to find candidates.
   Their path/filename heuristics do not establish ownership, obsolescence or
   deletion authority. The helper generator also embeds old metadata dates;
   review its output lifecycle before regenerating, and preserve human audits.
5. Update active navigation using existing README/index owners. Make
   kanbien-core-platform easy to find and label legacy staging and RAG.
   Staging still has three four-hour scheduled cloud workflows; RAG's workflow
   is disabled. Navigation isolation does not authorise stopping those jobs.
6. Refresh existing deployment migration inventories and propose exact
   folder/subfolder destinations with source-file counts at each leaf.
   Separately count tests/fixtures/data where useful. Reconcile the total and
   show real shared consumers. The legacy destination is not yet specified:
   submit that concrete choice for approval before moving anything.
7. Freeze the finite migration manifest at this checkpoint. Every current
   group is retained as-is or has an explicit approved change. Later additions
   follow admission; new discoveries update this manifest with user review.
8. Include non-obvious consumers discovered by the complete review: embedded
   rulebook source catalogues; byte-pinned public-image recovery scripts;
   controller/template hashes in operation reservations; historical Entity
   source-transition receipts; wrapper tests that import other test programs;
   and fixed source/installed-dependency fixtures. Separate active staging
   release control from historical modes inside the same file. A retained
   fixture-named RAG selector is actual query implementation, not test data.

**Target shape:** owner/domain/capability, with focused implementation,
bindings, tests and fixtures subfolders only when helpful. Preserve existing
canonical homes until an approved move changes them. `scripts/helpers/`
holds audit material; it is not a universal runtime helper library.
Use `src/` for product runtime responsibility according to its product owner,
not because a script happens to have functions.

**Exit:** complete disposition coverage and approved concrete migration scope;
source-backed reasons, counts, public compatibility and unknowns resolved.
**Recovery:** preserve unclassified code and audit its consumers. Size alone
never establishes bloat or removal.

## Milestone P5 — Remove repeated qualification at build/package boundaries

**Outcome:** an unchanged candidate is qualified once per required evidence
boundary; package and deployed behavior retain their own checks.

1. Trace one real Entity Smoke route from source checks through
   `publish-kanbien-core-platform-entity-smoke.yml`,
   `build-entity-smoke-image/script.sh`, shared
   `build-candidate-image/operations.sh`, composition runner, custody receipt,
   qualification capture and live binding. Then compare Core Server Persistence
   as the second real consumer before extracting any shared mechanism.
2. Record commands and actual consumed inputs. Today publication invokes local
   qualification, and image build again calls diagnostic/feature proof and the
   composition aggregate. Existing reuse may remove some cost: measure which
   commands actually execute before declaring all calls redundant.
3. Allocate each operation once: compile, local behavior, image construction,
   actual image behavior, custody validation, target alignment and live smoke.
   Reuse existing builder/selector/custody owners. Change callers together;
   a required public standalone builder must still enforce its prerequisites.
4. Resolve qualification capture's `local-runner` requirement deliberately.
   It currently rejects a `trusted-worktree-cache` row. Do not relax it by
   trusting uploaded JSON; validate any supported reuse through the existing
   trusted runner and custody source/artifact binding.
5. Prove the entire local handoff using existing controlled fixtures:
   matching source/artifact accepted; wrong source, stale proof, missing
   required check, failed child and wrong image rejected. Inspect generated
   payloads and receipts. Source compilation is not actual container proof.
6. Measure cold setup and warm reuse separately. Retain actual container checks
   at their owning stage. Cloud publication/deployment requires its own
   authority; do not launch it merely to claim this refactor finished.
7. Capture one immutable source identity for the whole build. The persistence
   builder currently reads HEAD separately for the image label and build
   argument; its fixture accepts different values. Correct the owner and that
   expectation before claiming coherent package identity. Recheck consumed
   inputs around the operation, not every unrelated repository file.
8. Keep receipt validation distinct from execution evidence. The qualification
   reader validates recorded fields/file hashes; mandatory proof authority also
   comes from the protected workflow producer and target required-check set.
   Prove missing mandatory input/check, arbitrary supplied receipt, wrong image
   and valid trusted reuse through the complete producer-to-reader handoff.
9. Inventory fixture side effects before enabling parallelism: runtime-payload
   verification renames repository `node_modules/@kanbien`; some tests use
   fixed checkout fixtures or port 4318. Give each invocation an isolated
   existing fixture/work directory and explicit environment before overlapping
   them. Do not use parallel execution to hide unsafe shared state.
10. Separate immutable validation from fresh observations in runtime callers.
    Ordinary update hashes broad deployment/governance trees before each step;
    accepted-history readers and nested `prepare` functions repeat proof work.
    Count actual calls first. Cache only unchanged source/history proof inside
    an explicitly scoped operation; keep current custody, resource ownership,
    permissions, and immediately-before-mutation checks fresh. Preserve original
    reservations and reconcile uncertain outcomes without replay.

**Owners:** the paths above plus
`20-build/capabilities/local-qualification/entity-smoke-proof/`,
`60-run/targets/kanbien-core-platform/entity-smoke/bindings/local-qualification/entity-smoke-proof/`,
`40-package/package-custody-receipt/` and their existing tests.

**Exit:** explained before/after call chain; fewer repeated executions where
duplication was established; failure and artifact identity preserved. Record
unmeasured live timing as not established.
**Recovery:** retain the existing safe prerequisite until the replacement
handoff has equivalent evidence; never remove it because an earlier log passed.

## Milestone P6 — Execute only the audited migration manifest

**Outcome:** approved capabilities have one clear home, coherent contents and
working consumers. Take one group at a time; brief and stop after each agreed
group if it is the user's checkpoint unit.

Use the existing path-migration workflow and layer-owned migration plan.
Before a move, inventory full paths, basenames, symbols, relative imports,
dynamic loaders, `parents[n]`, `DIRECTORY`, shell source paths, package
aliases, Docker copy inputs, fixtures, metadata, review records, current
fingerprints and historical readers. A literal-string search is necessary but
insufficient. Preserve accepted records byte-for-byte.

Priority packets, subject to P4's approved manifest:

| Packet | Proposed change | Connected consumers and prerequisite |
| --- | --- | --- |
| Architecture import inspection | Move `workspace-build/dependencies.mjs` and `dependencies-test.mjs` to existing `repo/module-structure/`. | `module-structure/check.mjs`, `smoke-test.sh`, catalogue inputs, repository contract expectations and relative declarations import. Keep broad scan explicitly retained. |
| Selector build-input projection | Move `workspace-build/check-inputs.mjs` and `check-inputs-test.mjs` to existing `repo/check-selection/`. | `workspace_context.py` PROJECTOR, relative compiler/declaration imports, catalogue. Hidden caller: `40-package/prepare-runtime-payload/script.sh` executes the test. Decide and prove its correct runner ownership before the move. |
| Retained legacy families | Move one staging-only script family to the exact approved legacy home. Keep RAG isolated in its approved home. | Keep workflow files directly in `.github/workflows/` so they remain discoverable. Preserve public commands, schedules, permissions, provider identities, effects and manual inputs while updating script references. No operational retirement authorised by a path move. |
| Entity Smoke history prerequisite | Make current and historical source resolution survive the proposed layout. | `entity-smoke/script.py`: fixed parent depth, sibling imports, flat `source_paths`, `historical_source_digest`, `retained_controller`. Prove old Git-object evidence still validates before moving the controller OR any production source included in its flat source enumeration/digests. |
| Entity Smoke operational groups | Use the existing 76-path manifest in `.agentic/04.deploy/plans/migration/entity-smoke-runtime-script-topology.md`, refreshed to current code. | Move a small cohesive group with its imports/tests/callers. Current discovery must include every moved source; retained old receipts must remain readable. Do not execute all 76 moves mechanically. |
| Remaining mixed content | Implement only high-value split/merge decisions proved in P4. | The diagnostics task split remains credited, but generic diagnostics still reads persistence vocabulary. Investigate that real dependency before promising complete independence or adding another extension interface. |

For each packet: approve destination/compatibility, update the existing migration
plan, move connected files once, update active consumers, run existing migration
checker plus focused behavior and full-diff selection, then review counts and
coupling. Remove a compatibility path only when its concrete consumer obligation
is gone and removal is authorised. Preserve historical logs.

**Exit:** every approved manifest row delivered or explicitly removed from
scope by the user; no active dangling caller, lost behavior or broken historical
reader; source counts reconcile. No need to move sound code just for symmetry.
**Recovery:** inspect the bounded diff and propose a scoped reversal through the
owning workflow; never reset the entire worktree or discard unrelated changes.

## Milestone P7 — Codify the proven rules and close the programme

1. Reconcile the existing script-admission standard, test-execution standard,
   change-completion standard, owning workflows and public command guides.
   Remove contradictory active guidance rather than layering exceptions.
2. Require a short admission record: real need, existing owner considered,
   primary role, consumers, named risk, execution boundary, invalidation,
   proposed home and expected cost. One file need not have every role folder.
   Keep metadata and the 50-line approval rule. Do not introduce another gate
   for every new prose rule.
   Reconcile actual effects with the governed runner before claiming safe
   automatic admission: `run-governed-script.sh` has a separate line parser,
   ignores inline effects and omits `aws-mutation` from its prohibited class.
   Use the existing metadata parser and canonical taxonomy; prove inline/list
   equivalence, unknown effects and unrelated lists without invoking providers.
   An approval flag is not evidence that the user approved a cloud operation.
3. Demonstrate an ordinary new/changed capability through the existing authoring
   workflow. The model should find the home and runner from current owners
   without inventing a new execution system. Reuse an actual task or disposable
   fixture; no speculative product capability is required.
<!-- deterministic-check: allow reason="future milestone scope and accepted consumer evidence require user/reviewer judgment; existing selector and publication gates own executable proof" -->
4. Re-run the representative matrix on the completed layout, then inspect and
   prove the actual final branch against its selected main base. Use cached
   matching evidence; collect cold/warm costs only where not already established.
5. Publish the final authorised changes by P3's proven procedure. Record
   delivered and deferred outcomes separately, including live checks not
   performed and the unscheduled broad checks still available manually.
6. Give a plain-English map of active commands, what runs when, retained
   legacy areas, the named manual checks, and how a future script is admitted.

**Exit:** every completion-contract item has evidence, the user can navigate
the result, and authorised local/remote delivery is complete.
**Deferred separately:** nightly scheduler, automatic issue triage, full live
regression campaign, retirement of staging/RAG, and unrelated product features.

## Representative acceptance matrix

Run selection probes in a batch, not after every edit. Use existing fixture
coverage for negative cases; no new broad matrix framework is needed.

| Change | Required decision evidence | Must expose |
| --- | --- | --- |
| Documentation/session only | Existing metadata/process checks and explicit non-applicability. | Accidental source-test expansion. |
| Catalogue rule or selector source | Focused selector mechanics and actual affected routing. | Unexpected catalogue-wide expansion; changed verification contracts still invalidate their own proof. |
| Shared diagnostic reader test | Its actual reader runner. | Unowned input; unrelated runtime selection or receipt invalidation. |
| Entity Smoke feature source | App behavior/composition and real affected consumer boundaries. | Unrelated staging/RAG and wholesale provider fixture expansion. |
| One deployment route or publication controller | Existing controlled route/receipt proof. | Wrong sibling routes or hidden aggregate execution. |
| Workspace manifest/lock/declaration | Affected dependency/build contracts from real dependencies. | Blanket exemption and entire-repo rerun are both unacceptable. |
| Shared helper | Helper's existing proof plus real direct consumer boundary. | A helper's directory name mistaken for its consumer set. |
| New, renamed or deleted source | Owning check or a visible coverage gap. | Silent disappearance from routing/source fingerprints. |
| Deferred aggregate input | No children solely from automatic deferred membership. | Independently selected children preserved; explicit full group still works. |
| Warm replay / one changed input | Reuse unchanged successful evidence; rerun affected proof only. | Arbitrary report import, stale runtime, configuration or assertion reuse. |
| Same bytes, different selected test subset | Context-sensitive proof is reused only for equivalent coverage. | Subset-to-full or subset-to-other-subset cache collision; an unchanged input tree is not sufficient. |
| Refresh with stale local main | Same selected base through rehearse/apply/prove. | Already-applied mutation mistaken for an unstarted attempt. |
| Package / retained controller | Exact source/image/custody binding; old historical readers preserved. | Repeated source tests, wrong artifact acceptance, broken pre-move evidence. |

## Commands and failure recovery

Always use the recorded worktree explicitly. Resolve real full hashes before
substituting placeholders; this block is a recipe, not a claim it has run.

~~~bash
git status --short
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count origin/main...HEAD
git diff --name-status --no-renames origin/main HEAD
~~~

Before commit, use the current working-tree variant to include pending edits:
`git diff --name-status --no-renames origin/main`, and list untracked files
separately with `git ls-files --others --exclude-standard`. Pin the intended
base and inspect both lists. The selector's `--ci` discovers paths ONLY from
the committed base-to-head diff; reading current files does not add newly dirty
or untracked paths to that list. Inspect pending paths through the existing
`--paths <exact-pending-paths> --boundary integration --json` route and follow
the existing preparation/commit workflow separately. That preview is not a
substitute for the final committed-candidate plan.

P2 now rejects a supplied HEAD_SHA that differs from checkout HEAD. A dirty
base-to-head plan is explicitly a working-tree preview; executing that committed
candidate route requires a clean worktree, including non-ignored untracked
source. Final acceptance still requires the exact committed diff; pending-path
previews and focused proof do not establish that acceptance.

Full candidate plan (no test execution, but runtime/input probing still occurs):

~~~bash
BASE_SHA=<selected-base-full-sha> HEAD_SHA=<candidate-full-sha> \
  bash scripts/repo/check-selection/script.sh \
  --ci --changed-only --boundary integration --json
~~~

Compare the CI plan once for P2 with the same hashes and `--ci --json`;
do not run both forever after their policy is reconciled.

Existing bounded routing diagnostic:

~~~bash
python3 -B scripts/repo/check-selection/smoke-test.py \
  SelectionTests.test_actual_runtime_and_runner_changes_select_independent_proof
bash scripts/repo/check-selection/smoke-test.sh --unit mechanics-promotion
~~~

The first command is an existing focused executable entrypoint and does not
run product tests. Direct fixture success does not seed full integration proof.
For registered final proof, use the existing selector command with
`--execute-local` only after the required set is explained. Explicit aggregate
requests may require the existing matching `--task-paths ... --record-preparation`
step; inspect the owner's requirements, then execute with the same task context.
Do not invent context text or copy another worktree's receipt.

| Observation | Required action |
| --- | --- |
| Permission/OSError writing active worktree evidence | Request the environment's permission for that exact worktree operation; do not switch to November 6 or call it a product failure. |
| Uncovered changed file | Find and connect its real runner; replan full diff. Selecting that runner through another file does not cover the missing ownership edge. |
| Unexpected required check | Trace static rule, scope, review edge and aggregate parent; record reason and fix its actual owner if incorrect. |
| Unrelated missing worktree | Complete diagnostic inventory under P3's reconciled policy; preserve unrelated registration and independently verify target. |
| Genuine check failure | Inspect retained finite findings and relevant runner; repair the named risk, preserve other receipts, rerun affected work. |
| Advisory duration exceeded | Report elapsed time and progress; continue to terminal result. Estimate alone is not cancellation authority. |
| Actual process timeout/interruption/lost result | Mark incomplete, inspect process and outputs, preserve completed proof, resume first incomplete operation; do not assume failure or success. |
| Rehearsal/apply stopped | Read actual branch head and retained preflight before another mutation; apply may already have advanced the chat. |
| Base/source changed | Recompute candidate impact and invalidate affected proof, preserving matching results. |
| Remote moved / push rejected | Fetch and governed refresh; normal push only, never force. |
| Historical path mismatch | Fix historical resolution from immutable Git objects; do not rewrite accepted receipts. |
| Newly discovered legacy/helper defect | Record source evidence, affected owner and invocation risk. Do not add it to an unrelated merge's required set. Resolve before affected invocation/change, or obtain explicit deferral. |
| New external effect or material design choice | Prepare concrete options and evidence, continue independent authorised work, ask only for missing authority/decision. |

Costs are measured from first invocation including preparation, installs,
compilation and retries. Existing targets are approximately one minute for
ordinary feedback, a few minutes for checkpoint verification, and ten minutes
for supported end-to-end delivery. They are engineering targets, not established
performance or automatic process timeouts. Distinguish functional pass from
budget met/missed/not established. A local audit cannot establish live delivery
timing.

## Goal handoff for Sol

### Use the full review without creating a new backlog avalanche

Read the audit's overview and only the current packet's file rows/findings.
The full source ledger is available for hidden callers and migration impacts;
it is not a request to reread or rewrite the repository on every turn.

| Packet | Exact starting owners | Required evidence / stop boundary |
| --- | --- | --- |
| P1 routing repair | `checks.yml`, `repository_contracts_test.py`, F01/F05 | Existing actual-catalogue case and whole candidate plan; no uncovered source, no claim that planning is execution. |
| P2 proof identity | `script.py`, `local_cache.py`, `mechanics_test.py`; R-01 | Same context reuses; different subset/full cannot reuse incompatible proof; old context-free evidence cannot qualify new contract. No Core algorithm rewrite needed. |
| P2 selection closure | Same selector, `execution_policy.py`, diagnostic `review_rules`/`review_bindings`; F02–F04, R-02/R-03 | Deferred parents do not cause normal child runs; independent children and explicit aggregate still work; real consumed input changes invalidate proof. |
| P3 promotion handoff | Reporting/session resolver, refresh/rehearsal/apply, existing local-main gate; F09–F13/F22, R-12/R-13 | Correct target/base/code version, full candidate proof, post-child state recheck, actual authorised publication; no global worktree cleanup. |
| P3 normal precommit observation | `artifact-metadata/update-lifecycle/script.sh`, `session-log/check-commitlog-deletions/script.sh`; R-15/R-07 | Distinguish absent from failed Git/parser observation, fail before writes or protected deletion. Bound any repair to the invoked owner; no broad metadata rewrite. |
| P4/P6 movement prerequisites | Existing migration manifests, actual caller rows, D-13/U07/F19 | Exact destination approval; current and retained history resolve; byte-pinned recovery qualification has a supported requalification path. No blind rename. |
| P5 package handoff | Existing builders, `build-candidate-image/operations.sh`, custody producer/readers; D-05/D-14/D-15 | One source identity, counted compile/proof calls, actual container boundary retained, accepted trusted proof not merely valid JSON. |
| Conditional operational repair | Specific behavior in D-16, L-15/L-18/L-22, and runtime findings | Before relying on or modifying the affected behavior, resolve its named intent, unknown-outcome or cleanup risk. Unrelated findings in the same owner remain retained risks. This does not authorise cloud calls or globalize legacy checks. |
| P7 admission | Existing metadata parser, `run-governed-script.sh`, admission/effects standards; R-16/U08 | Actual helper/child effects represented; no path or header shortcut grants destructive/cloud authority. |

Other findings remain explicit retained risks until the affected packet is
approved. Examples include portable export preservation, dormant RAG freshness,
metrics accounting, broad structural-parser quality, and standalone legacy
service monitors. Do not quietly label them fixed; do not make unrelated fixes
conditions for P1/P3. If a new finding genuinely compromises the proof or
operation currently being performed, update that bounded packet here with the
evidence and necessary correction, then continue within existing authority.

The executor needs this plan, its linked current audit, session log and the
current milestone's source owners. It should not need to reconstruct the chat.

Suggested programme goal text (starts with the next incomplete milestone and
retains milestone checkpoints):

> Deliver the programme in
> `.agentic/shared/plans/implementation/script-library-simplification.md`.
> Use the session-recorded November 21 worktree and first reobserve the pinned
> baseline. Start with the next incomplete milestone identified in the progress
> table, only after its explicit approval. This authorises that milestone's bounded
> implementation and local verification; preserve unrelated work. Follow the
> common execution procedure, complete every step, and update this same
> plan/audit with actual evidence. At each milestone, stop, brief me in plain
> English and answer my questions; continue to the next only when I approve it.
> Do not introduce a new registry, scheduler, wrapper layer or broad test suite.
> Do not treat fixtures or a zero-check plan as full candidate acceptance.
> Continue through routine in-scope corrections without asking me again.
> Honour already-recorded approvals within their scope; ask only for genuinely
> missing authority, a new source file over 50 code lines, or an unresolved
> material choice. Commit, merge, push, cloud operations and retirement each
> require explicit authority; planning their steps is not that authority.
> Do not create a parallel plan or claim the overall programme delivered while
> publication or other acceptance remains incomplete.

For a resumed goal, replace the starting identifier with the actual next
incomplete milestone. Approval of one milestone does not silently approve new
cloud operations, legacy retirement, or a different folder design.

## Progress to update in place

| Milestone | Status at this revision | Next concrete action |
| --- | --- | --- |
| Audit and revised plan | Completed as documentation/source audit only. | User reviews plan and chooses execution milestone. |
| P1 Current candidate ownership | Complete locally: direct owner connected and P1 proof recorded. | Preserved; P2 was subsequently approved. No publication claimed. |
| P2 Consistent selection | Complete locally at its bounded selection/implementation boundary: focused and registered owners passed, warm reuse proved, both CI callers agree. Full affected integration/publication not claimed. | Brief user and stop. P3 requires explicit approval; retain the 30 pre-existing adoption findings. |
| P3 Reliable published checkpoint | Delivered via main/remote 21365c76: exact source qualification passed, 42 local command instances, seven reused. Empty-diff follow-up correction and completion evidence are included in this record. | Brief user and stop; P4 requires approval. The 21m33s source gate missed the cost target; retain P5 measurement work and baseline adoption debt. |
| P4 Complete capability disposition | Full 690-file source review supplied; folder approval and final migration scope unfinished. | Reconcile only changed sources, resolve proposed decisions and approve finite migration manifest. |
| P5 Build/package handoff | Existing machinery retained; duplication/cold reuse unmeasured. | Trace and measure one complete local qualification-to-package call chain. |
| P6 Approved migrations | One historical diagnostics split retained. | Execute only newly approved packets after their prerequisites. |
| P7 Standards and final acceptance | Historical admission rule retained; reconciliation incomplete. | Close proven rules, acceptance matrix and final authorised publication. |

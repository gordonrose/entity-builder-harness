<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.reusable-aws-scheduling
version: 1
status: draft
created_on: "2026-11-26"
updated_on: "2026-11-27"
layer: 03.product
domain: platform.scheduling
disciplines: [architecture, backend, security, sre]
kind: implementation-plan
purpose: Track cost-conscious PostgreSQL scheduling with bounded Lambda dispatch and execution, independent platform proof and Entity Smoke integration.
portability: {class: source-only, targets: []}
used_by:
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# Reusable AWS scheduling implementation plan

## Read this first

This is the implementation handoff and progress record for scheduling work,
including execution by Sol 6.1. The user selected **A2** after reviewing operating
costs: PostgreSQL stores each reminder, a short Lambda dispatch pass finds due
work once a minute, and a queue invokes a Lambda worker. Reuse the existing
schedule store, due pass, outbox, SQS adapter and durable worker machinery.

**Current authority (2026-11-27 09:18Z):** the user explicitly resumed the goal
with "do not stop just finish the goal". Continue autonomously through the full
live proof; the previous overnight cutoff and proposed 08:20 extension no longer
apply. The existing US$10 proof-spend ceiling, US$25/month forecast ceiling,
two proof scopes, synthetic-only irreversible deletion, governed main publication
and shared-network compatibility limits remain unchanged. Do not pause for an
invented new time limit or stop at a local checkpoint. Genuine external blockers
and missing authority still follow the existing workflows.

Historical overnight authority: on 2026-11-26 the user approved the drafted overnight
goal with **start with those limits**. Proceed autonomously on this A2 goal,
without per-increment teaching approvals, from 23:20:22Z through
2026-11-27T07:20:22Z; pause unfinished work at that deadline. The approved
additional proof-spend ceiling is US$10; projected combined incremental cost
must stay within US$25/month including fixed costs and 100,000 jobs/month.
Small-proof completion must occur within five minutes after due time; deliberate
interruption recovery within ten minutes after restoration. These are proof
budgets, not production guarantees. Necessary local runtime/harness/package
work, scoped additive migrations, narrow AWS resources and activation are
authorized through their owning workflows. Irreversible deletion is restricted
to positively identified synthetic records created for this proof. Preserve
shared resources, pre-existing data and accepted history. Calendar/DST is excluded.

The draft's branch-only publication restriction was superseded by the user's
explicit reply **Authorize governed merge and push to main for this scheduler
work** on 2026-11-26. Governed integration/publication is authorized after all
required checks. Preserve both main-only publisher protections; no force push,
history rewrite, unrelated integration or bypass is authorized.

On 2026-11-27 at resumption (04:46Z), the user explicitly approved the bounded
reusable Lambda packaging, qualification and activation helpers/tests, including
new source files over50code lines and new capability folders where no owner
exists. Each file still needs its existing admission record, owner, review and
proof; this is not authority for unrelated script growth. The user also approved
governed shared-network compatibility work preserving existing staging apps'
queue and security-group access before scheduler deployment. These approvals
supersede the pending-authority statements recorded earlier below, not their
technical safety/proof gates. Existing proof/spend ceilings and the07:20:22Z
deadline remained unchanged for that run; its final half-hour was reserved for
safe closeout. The explicit continuation above supersedes that time cutoff.

**Earlier implementation status (2026-11-27, 06:33Z checkpoint):** bounded
dispatch, durable external worker delivery, targeted atomic Entity Smoke cleanup
and independent baseline proof code are implemented locally. The final native
PostgreSQL test passed, including continuation, independent database identities,
targeted cleanup, surviving controls and retry. Registered payload, image-contract,
provider-control and scheduling-acceptance fixture checks passed at their local
boundaries. Complete integration is not established: four declared run proofs
(dispatch and worker in each scope), trusted deployment/acceptance evidence,
partial migration-state observation and actual finished-image qualification
remain missing. The cost ceiling is not yet demonstrated. No AWS resources or
shared database rows have been changed, and this overnight work remains
uncommitted. Final review corrected executable imports, observer lock handling
and baseline migration-profile acceptance. Corrected native PostgreSQL and
composition/access fixtures pass. Both registered acceptance checks pass against
the final two-file profile correction; final evidence is recorded below.
The overnight goal was paused and the full checkpoint preserved; the user's
09:18Z continuation now authorizes resuming the remaining implementation and
governed live delivery. All previously unproven boundaries remain unproven.

### Current integration checkpoint — 2026-11-27 13:42Z

Staged whitespace correction: ten previously untracked files each lost exactly
one extra terminal newline; root compared every byte against the reviewed index.
No code, data or assertion changed. Six existing source-review hashes were
refreshed only after this equivalence check. Controller script identity is now
`f096f9060f96d5f6a77ad957af8c3828e5fc987e872b040882397934e0fbe152`, wrapper
`3b078a4ba1a3161637da8ff2c78aeb00188590197bbb63708bdf6df2347fa20b`, and smoke
fixture `6f76002e188934ca221899f51d9dcfc3dbb5e931d9779eb4dcae9cd78b8a9a4a`.
The original nine-check run21296 passed in65.454s, with six reused and three
executed checks; affected hash-bound evidence must revalidate after this trim.

Continuation: governed preparation49023 passed with no lifecycle changes or
selector findings. The complete affected local preview35674 covered281 paths,
with no uncovered inputs or effect mismatches; later package/live obligations
remain pending. Registered focused run68020 retained eight passing checks and
one failed acceptance fixture in
`.cache/test-runs/20261127T141759Z-a0fab82b3bfa44328cb694272479ef1c/report.json`
(100.020s total;77.075s execution). Direct reproduction51318 showed exactly two
obsolete expectations: the implemented production reader now rejects fabricated
proof as provenance-not-confirmed instead of being unavailable. Root reviewed
the actual delegate and live-only envelope guard. The single fixture correction
retains both replacement-code canaries and adds explicit missing-reader rejection;
no production behaviour or acceptance requirement is weakened. Final reviewed
`release-succession/scheduling-proof-test.py` identity is
`fb8b17ffb83208b1b567e62752d87a071f9ab55be7059450efc98750c88c84db`.
This supersedes that fixture's earlier reviewed identities below. Reprepare the
corrected candidate and rerun its affected registered proof before staging;
unchanged passing receipts remain reusable through the existing selector.

Runtime implementation and controlled native recovery fixtures are implemented;
this is not live AWS acceptance. The final connected credential/snapshot/restore
fixture (session49222) passed, including original failed-reader cleanup planning
and wrong-approval rejection. The lower cleanup fixture separately passed missing
cost authority, active/forged failure rejection and lost-delete reconciliation
without a second delete. The existing realization-gate fixture passed174 cases.
Accepted recovery snapshots remain retained and must be priced monthly.

Root's source review updated15 existing diagnostic responsibility rows with
truthful partial/support status and current source identities; native-control
review integration is in progress. The shared provider/runtime/acceptance check
input closure now contains the same124 dependencies; its actual fingerprint
invalidation counterexample passed in1.503s. Earlier native workload measurement
must be repeated once after final source freeze because its input context changed.

Two verification simplifications preserve the required outcome: duplicate
delivery reuses the completed minute-delivery original, and untouched/future
control observations bracket that actual purge, rather than every later recovery
case. Their17 connected case/scope/composition tests passed in14.341s. Real
five-minute retention and one-minute restoration remain unchanged. Canonical
activation now also joins each scope's accepted recovery snapshot and source
database identity to the exact snapshot priced in the retained cost evidence;
the focused acceptance join test passed in1.783s, including valid-but-different
snapshot/source rejection. These are controlled local tests, not provider proof.

The finite successful live route currently requires132 one-off ECS tasks:
35 core and97 Entity, including required native preflights and canonical
requalification, excluding retries/freshness renewals. Existing task execution
evidence gives an Entity median41.867s over37 historical originals; this does
not guarantee current latency. A two-hour complete route is not established.
With the explicit conservative worksheet assumptions (4GiB images, one email
subscription,20GiB source/7backup days, two two-hour clones, two snapshot UTC
dates), a three-hour window gives12.14USD if all tasks reserve immediately, or
10.34USD with Entity reservations evenly spread. These are illustrative
reservation estimates, not observed spend or an admitted executable schedule.
Do not claim the10USD proof or25USD monthly limit is proven. HTTP/service
replacement overlap, dynamic task revisions and actual route timing remain
part of the existing cost review. No cloud/shared-database mutation, staging,
commit, merge or push has occurred in this continuation.

Required final correction inventory (no optional feature expansion):

- Existing `scheduling-control/script.py` and native task census seams:
  an active cost intent must never allow an unselected revision to bypass
  accounting merely because `required=False`. The existing core rollback and
  replacement verifier revisions and Entity isolated restore-reader revision
  must be authenticated through their real native owners and included in the
  same original/cost-companion census. Unknown originals retain their obligation;
  unrelated historical work must not be adopted. No new journal, generic family
  allowlist, altered package provenance or permission expansion is authorized.
  Existing no-intent native routes retain their prior optional-budget behaviour.
  `plan_review` owns this correction and existing smoke/census counterexamples.
  Execution authority remains with each existing native task owner and its
  current stack/request/realization checks. The cost guard accounts that exact
  validated request and authenticates its retained original; it must not add a
  second rollback-transition qualification system. The same cost companion
  retains the exact revision/request, and admitted original IDs extend the
  existing census across later stack revisions. Caller validation must precede
  reservation; unknown/missing/conflicting originals still block new paid work.
- Existing `scheduling-control/proof.py`: native Entity task reservations use
  UTC `+00:00`, but maintenance pricing accepts only `Z`. Accept both genuine UTC
  representations at this cost boundary while retaining the original timestamp;
  reject naive, nonzero-offset and malformed values. Missing core timestamps
  still explicitly reserve the complete original budget window. Prove the real
  post-reservation recalculation and census path, not only a constructed parser.
- The newly authored100-task parsing cap is smaller than the required132-task
  route. Set the two maintenance/projection parsing bounds to256, with boundary
  tests. This is bounded data capacity, not permission to launch256 tasks or to
  exceed10USD. Every original must still pass the unchanged cumulative monetary
  gate. `time_model_review` owns this change and the existing proof tests.

After these corrections freeze, reuse unchanged proof and run the affected
registered checks through the existing preparation workflow. Publication,
disabled deployment, real runtime cases, recipient-confirmed alert delivery,
measured cost and both canonical live acceptances remain required.

Final correction disposition: the inventory above is now implemented and frozen.
The existing native owners retain execution authority; the shared cost owner
accounts admitted rollback/replacement and restore-reader revisions through
their original records and exact cost companions. Its focused native-census
test passed in3.73s and full controller smoke passed in6.44s. Genuine UTC
`+00:00` reservations are accepted without changing retained timestamps, and
the bounded census capacity is256;20 cost/resource tests passed in0.082s,
including rejection under the unchanged10USD ceiling. No new journal or
second deployment authorizer was introduced. Diagnostic source reviews now
cover these corrections and their native consumers; final ledger validation
and governed preparation are the next integration boundary. AWS identity was
confirmed read-only as account337159794548 using declared profile
`kanbien-dev` and region`eu-west-1`. No provider resources or shared database
rows have changed. The requested20USD one-off ceiling is still unapproved;
10USD proof and25USD/month limits remain binding.

Preparation92785 completed lifecycle updates and structural checks, then failed
closed on three uncovered declaration inputs and the foundation fixture's
effect-metadata mismatch. Correct their existing check registrations and actual
fixture consumers; no new check or execution framework is needed. The final
post-preparation review found23 source identity changes caused solely by
`updated_on` metadata; reconstructing each prior date reproduced its exact
reviewed hash. Refresh only these identities, preserving inherited unrelated
debt. Fetch28221 completed and confirmed origin/main is already an ancestor of
this chat HEAD (6 ahead,0 behind); no main refresh is currently needed.

Read-only current AWS baseline (2026-11-27T14:01:50Z, native Provider session56491):
core HTTP, Entity HTTP and the enabled collector each already run one256CPU/
512MiB task, with no pending deployment. Their recurring costs are existing
baseline, not additional scheduler units. The shared SQS endpoint and all eight
planned scheduler alarms are absent. New fixed monthly allowances remain
20.968USD including two retained20GiB recovery snapshots, leaving4.032USD for
measured variable extras under25USD. Reserve temporary deployment overlap
separately; two extra HTTP tasks over a conservative three-hour window add
0.074055USD at the existing model rate. This is prospective allowance, not
observed spend. Collector overlap applies only if its reviewed change changes
that service. No AWS mutation was used to establish these facts.

Preparation correction closed: root reviewed the five changed files. The
existing managed-image fixture now validates both real delivery contracts
against their actual workflow and IAM-policy owners; the existing declaration
fixture checks the changed subject schema against its compiler. Exact catalog
input/invalidation and foundation effect-parity assertions passed in0.448s;
the two connected consumer fixtures each passed in0.052s. No new check or
runtime capability was added. The reviewed catalog is
`89964f014573a663d8a6e46dffa88f06121492f4ceb9fd3d6091fa55bb4bbe13`.

The required six-script admission continuation was completed by Senior Prompt
Engineer (`plan_review`): **pass_with_notes**,4.38/5, no required correction.
It applied run-agent-review v2, script-admission v4, SPE role/rubric v1,
agent-contracts v1 and the existing professional-review/report requirements.
Hierarchy/drift scored5; deterministic boundary/context/learnability/testability
scored4. Approximately five minutes exceeded the one-minute target for required
instruction and actual source/caller checks. Existing domain proof was reused;
no tests or cloud calls were repeated. This covers the six additions after the
earlier14-file admission boundary; current script-source growth is20 added,
0 removed,0 moved. Existing additional checks remain integration-selected;
no automatic cloud execution or new recurring review framework is introduced.

Exact reviewed new identities (relative to `scripts/04.deploy/lifecycle/`):

```text
cdacd1be3fc1a55546095d884578c08f6e1bf30316a43769c35335cac1a4f74e 50-deploy/capabilities/scheduling-control/admission.py
c7fd62183ba3ee9be3363516159a0c7ecfc984955d56b11d49c17457167f468c 50-deploy/capabilities/scheduling-control/proof.py
95afb0ae377fb6a7cb56965d9736ddd253f4e9c6edb48c6b322089b4e65dc101 50-deploy/capabilities/scheduling-control/proof-test.py
1884b12d11779dca0edfd5f3a07051abb8c089aca1d5d253db3a0f0e4ddcd92c 50-deploy/capabilities/foundation-access-update/script.py
2c7e54a50942c455ead113b6787101d8e68aa968d8b43e72e15cd0421a202966 50-deploy/capabilities/foundation-access-update/smoke-test.py
8dd44fec430dda5bfd86c4ddca31bed8935ac5f3485560220fc1636f52f2adb1 40-package/package-custody-receipt/github-artifact.py
```

Their controller/caller identities are `bef190863d7a12b858023f3d113886a9255c5d3144b25db526f4fa240a265173`
(`scheduling-control/script.py`) and
`601cdebb233583d13302e4e81aae8948f0ea212f8a40dd20da4f9d27a6a9b572`
(`scheduling-control/smoke-test.py`), plus the catalog above. Final preparation
and staged comparisons remain required. Local integration has an advisory
30-minute verification budget; any overrun/failure remains explicit and cannot
waive required checks. Package and live acceptance remain separate and pending.

### Final-review correction inventory — 2026-11-27 06:07Z

Additional baseline-proof correction inventory (06:23Z): Entity's existing
`acceptance-evaluation/implementation/acceptance-evidence.py` validates the
`migration` task's `apply` operation but not its newly supported migration
profile. Preserve the current baseline-only meaning by requiring that
`PERSISTENCE_MIGRATION_PROFILE` is absent from the validated request environment;
absence is the existing baseline encoding. Reject a scheduling packet with the
finite `acceptance-migration-profile-mismatch` and item `migration`, without
raw values. Extend existing `acceptance-evaluation/tests/acceptance-control-test.py`
using its actual archive/gate/admission/receipt producers: valid baseline passes;
fully rebound scheduling-profile request/observed overrides/receipt/completion
fails at this exact reader. Existing operation names, accepted history,
publication, provider effects and scheduling-migration hardblocks are unchanged.
Two existing files only; scheduler_inventory owns them. Focused proof estimate
under 30s; root owns final review/diagnostic record and tests after source freeze.

Independent review found a concrete trust-boundary error: the new scheduling
acceptance helper loaded its custody validator and evidence-owner Python from a
caller-selected receipt/data root. A copied evidence directory could therefore
replace the validator. Reuse the existing core reader's `IMPLEMENTATION_ROOT`
convention, not another plugin or verification mechanism.

- `scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py`:
  pin executable imports to this helper's implementation tree. Supplied roots
  remain declaration/evidence data only. Preserve the existing bounded
  `owner-unavailable` / `provenance-not-confirmed` failure meanings.
- `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.py`:
  reject an invalid simulated root before invoking the scheduling helper;
  preserve historical HTTP acceptance and class separation.
- Existing `release-succession/scheduling-proof-test.py`: exercise the actual
  core reader with copied declarations and malicious replacement modules.
  Assert that replacement code never runs, live qualification still fails with
  the missing trusted owner, and invalid rehearsal roots fail before validation.
  Controlled successes may patch the helper in tests only; no production
  callback or executable-path injection is added.

Root owns plan and diagnostic review updates; plan_review owns these three files.
Focused proof budget: 15 minutes including correction/review; use the existing
registered `scheduling-acceptance-contracts` unit after freeze. No new scripts,
provider calls, deployment, migration or mutation-gate changes are authorized by
this correction. Earlier source-admission approval remains limited to its
reviewed source; affected identities and final review must be refreshed.

**First release:** durable one-off UTC scheduling with bounded, demand-driven
execution, independently proven on core-platform and through Entity Smoke.
Calendar recurrence, timezone resolution and daylight-saving policies remain M8.
There is no runtime EventBridge schedule-management adapter in this release.

## Outcome and architectural boundaries

### 2026-11-27 final bounded source-admission review and proof checkpoint

Final observation correction inventory (06:14Z): existing
`shared/persistence/scheduling-administration.ts` starts a repeatable-read
transaction before a blocking advisory-lock query. Waiting can retain the
pre-wait snapshot. Reuse the existing baseline observer's fail-fast
`pg_try_advisory_xact_lock` pattern; require exactly one row and literal `true`
before reading state. Contention and malformed results must fail using the
existing finite administration diagnostics, with rollback/release and original
failure preservation. The grant path remains read-committed and is unchanged.
Consumers remain both administration entrypoints and their strict complete-state
readers; no result schema or operation vocabulary changes. Extend existing
Entity composition/access fixtures and the native PostgreSQL integration fixture
to prove busy-lock rejection, no post-rejection state reads and success after
release. Root reviews before final proof. Budget 15 minutes, no new files.
This removes waiting-induced staleness, not concurrent application writes; the
receipt remains a captured snapshot, not activation authority. PostgreSQL 18's
[snapshot rule](https://www.postgresql.org/docs/18/transaction-iso.html) and
[nonwaiting lock operation](https://www.postgresql.org/docs/18/functions-admin.html)
support this distinction. The larger distinct partial-prefix operation remains
unimplemented and must not be implied by this correction.

Senior Prompt Engineer (`harness.agents.senior-prompt-engineer`) completed the
bounded admission review at 05:58:07Z: **pass_with_notes**, 4.38/5, no critical
source-admission blocker. Rules: run-agent-review v2, script-admission v4,
SPE role/rubric v1, agent-contracts v1, professional-review quality v1 and report
template v1. Elapsed 15m04s (about nine active minutes; remainder awaited source
freeze/evidence), exceeding the one-minute pilot because multiple new owners and
their real consumers were reviewed. No suites or cloud calls were repeated by
the reviewer. Scores: hierarchy 5, deterministic boundary 4, drift 5, context 4,
learnability 4, testability 4. The subsequent import-root correction reopened
affected source review, which root closed against the corrected source and its
counterexample tests. This decision does not qualify images or deployment.

Necessity/reuse, placement, metadata/authority, selection and proportionate proof
were satisfied at that reviewed boundary. Missing README headers, M7 registration
and Entity historical/current source-custody dependency were corrected. Existing
release proof sets retain both Lambda custody receipts and the typed qualification
bundle, while keeping HTTP as the primary image. Controlled fixture evidence
cannot replace the missing trusted live producer/reader. Four missing run-proof
declarations remain a real complete-selection gap.

Evidence reused rather than rerun:

- Header check: 115 files passed, zero grandfathered; changed-input deterministic
  drift passed. The direct-interpreter fixtures passed in 11.227s; actual managed
  payload input-closure counterexample passed in 2.809s.
- Registered payload, image-contract and provider-control fixtures passed:
  `.cache/test-runs/20261127T055628Z-3698109d66584a338467b4e914b03f51/report.json`.
  Total 18.529s, command execution 4.732s. This is requested-check coverage only.
- Registered scheduling acceptance contracts passed before the import correction:
  `.cache/test-runs/20261127T060014Z-872557eb6a8b45c0a13b6f43292ec658/report.json`;
  command execution 25.177s, within the 30s estimate. It proves controlled
  collector/reader cases, not live provenance. Corrected inputs require a new pass.
- Final native PostgreSQL command (`platform:adapter:aws:persistence:postgresql:integration`,
  terminal session 80490) passed against the frozen administration helper
  `ed3bb3bed6cf1c4044f55fa7d174b69ab0b88b1b5cce314bea21166f22f4ceef`.
  It exercised actual independent database identities, continuation, targeted
  deletion, surviving controls and retries. Its disposable engine/directory were
  cleaned up successfully. No shared database was touched. Docker remains
  unavailable, so this is not finished-image qualification.
- Final coverage compiler found two stale task test identities, now source-reviewed
  and refreshed, plus 60 findings in unchanged HEAD files. Those inherited reviews
  were not refreshed. Whole-repository diagnostic adoption is not claimed.
- Full Entity task-route fixture was stopped at its 10m08s investigation budget
  without an assertion failure; that result is incomplete, not passed. Focused
  migration-profile/task-control cases passed. Do not repeat that whole suite
  unchanged without addressing its verification cost.

Frozen source identities reviewed by the SPE (later import correction supersedes
only its affected helper/reader/test identities):

```text
b8105cbb79f16adcfc7c321aa4a6cfff336a97bd1b702100394160ecbae101de scripts/repo/check-selection/checks.yml
aceb331e018ffd9b85897f88a7b97885cc05e2491f6606c8d1f3d4f23d18df52 scripts/repo/check-selection/repository_contracts_test.py
07ca93534481d48e72ae618e7761016fa28a5ebcd795eb48ffa83354eeeb3e86 scripts/repo/check-selection/script.py
b80cbe3d4544591832727c231803841bc71c007d1a3f1802809f66b45d79a1ab scripts/repo/check-selection/mechanics_test.py
bb791f00205596344c227d67fc0e9c76647b19a53e23997ffeb1745e7f0199bf scripts/04.deploy/inventory-deploy-control/delivery_inventory.py
4f11e07c2566374c72fc0ccdf04e91b3a1699fcb7834cb9fce684c46f6c2ddc8 scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py
e8936664e59dd3c1706cb48a922923c8d81d5e81b9be20d8012f68fd6e14b88a scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py
689980542b49852979e8ae5bff8d82ffd362c8804c629a618a11f63a6bc94d61 scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py
ff1612858fef549fc2d97e6823d172ec9b77d92a712e20e82e7008c95bf535fe scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
004a4d1936ef3118eda870fe583f162010b7ae87b0cd1750b11d451dcc4b085b scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.sh
58ba864997061a8253f9afc4e4830b522f2b87481e358616ef595bd0343c5c45 scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/smoke-test.py
e715b0b5ff4ead3f0ed516abbf4e0d2df561b4e2f2b334986e68eb07dd0334bb scripts/04.deploy/shared/scheduling-database-state.py
e5a5f8e34d909150317deaeefa517949bfd5ddf2edd787759ae12efbba9b5b72 scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py
6b47c6ca8cd632a5c1e841a48790ec9b5dd5a5189c23490b74f5392e44a8010e scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof-test.py
82fdd8fe29c7047eaba0d0fac2060bc027babc3c8cc0b009213cf01bea6651d7 scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py
7988fe06a9a64ca1bbfe88038e4d3c6f7446004f58c97895ca4c3bdf32af58ca scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
13bb3e272c046db19cecc9e2ab29624663a42b5fe7d3026c02bd5ffa22f5162a scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-updates.py
fe7c7fabbc28b164b0fafa31d9223f840110b334125ca09ba35011560c2c39bc scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.py
c0d79b95b273da059b112501a7a562f101d0df4a029352a06cf74df268229323 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-route.py
d47e32c1a89b1fa4537138d3f7554ab56dacfaa1e6e3a3dc4c1745666370d159 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-state.py
b06e73495b1065a243f99165dd0be4f972d50a362e1054c38247a38f60257138 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/orchestration/commands/script.py
8ad0c63cf8ab87de975ca5a0ef5ee47e238a8307c0f43e1427a9f618aae06931 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/infrastructure-route-test.py
af6511c77bf3f6559d58dd78ad53e9c3b9fdcb14b825613cc088f23db8edca45 infra/04.deploy/03.product/image/scheduling-lambda/README.md
6722b2d9aefb5b733a85d85493c0132514d2e2a5ebddd4134e028cbad20cc691 scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/README.md
```

### Final corrected proof checkpoint — 2026-11-27

Root reviewed the completed correction diffs, actual consumers and sensitive
failure boundaries before the final focused checks. All contributing agents
froze their inputs. Earlier evidence above remains historical; the following
supersedes only the affected boundaries:

- Executable import-root and simulated-root corrections passed the registered
  `scheduling-acceptance-contracts` check at
  `.cache/test-runs/20261127T061121Z-eb70c6894ab64f15b28e6b2241c6bdbe/report.json`
  (12.502s command execution). Actual malicious copied modules never execute;
  the absent trusted runtime producer still rejects qualification.
- After the baseline migration-profile correction, registered
  `entity-smoke-acceptance-controls` and `scheduling-acceptance-contracts` both
  passed in
  `.cache/test-runs/20261127T063236Z-81fd1704cefe444f80ae87a5ab6b8d09/report.json`.
  Execution was 65.109s and 17.466s respectively. The first exceeded its 15s
  advisory estimate; this is not a delivery-time measurement or a reason to
  weaken assertions. The new real archive/request/receipt/admission case also
  passed alone in 9.56s. These are requested local checks, not full integration,
  package qualification or live acceptance.
- Corrected nonwaiting-lock observation passed the native PostgreSQL 18.6
  owner (`npm run platform:adapter:aws:persistence:postgresql:integration`,
  terminal session10309). A second connection held the real lock; observation
  rejected within the two-second bound before state reads and a new observation
  succeeded after release. Targeted cleanup, control survival, continuation,
  independent identities and retry assertions also passed. Disposable engine
  and directory cleanup passed; no shared database was used. The corresponding
  Entity composition/access fixtures passed after normal compilation, runtime
  preparation and dependency assembly (sessions70883 and68599). Controlled
  access fixtures are not effective RDS permission proof.
- The first composition preparation attempt (76879) stopped before compilation
  because the default temporary filesystem was full. Reusing the established
  external `TMPDIR=/var/tmp/scheduler-dispatch-proof.3hVWbH` resolved preparation;
  no source workaround or assertion change was made.
- Final diagnostic freshness compilation took10.355s: zero findings in the
  changed task paths,60 findings in unchanged HEAD sources. Overall verdict is
  still failed; unrelated hashes were not refreshed. Whole-repository diagnostic
  adoption and complete affected integration remain unestablished.
- Final read-only impact preview over all224 remaining task paths took96.905s.
  Its verdict is `gap`: four distinct missing run proofs (dispatch and worker
  for each scope), each reported both at its declaration and aggregate boundary.
  No checks executed in that preview. The missing routes are real completeness
  blockers, not exclusions; earlier local passes are retained at their own
  source/evidence boundaries rather than relabelled complete integration.

Corrected source identities:

```text
a7c38317137ab8965530565ae0bae65b547777f31b22450ae83762263dfe9de6 scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py
eb98527c36ce2ec407af69f6fe550ee9d75ce05f0fd8c2c209b854c0e3d69ba5 scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof-test.py
a5d2aad7935b5cb5336226c057aa4ae6f78a9b5c2abd4c531bac3e71605b92f2 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.py
bf8e3d305307d2b2e7316df7e62093515710cc18a513b7627c47f702f9c4badc infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration.ts
38a6791385bf0102745691704c524a0c8ecbfed7db45b52e88476d2dc4bd529a scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/access-control-test.mjs
af363e4dc8f0b9ef9e0c4bdcb16d2a1bf6d792d5a479682b301dc9fb5741352a platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-persistence-adapter-integration.test.ts
68878b45ffe03d5c2a586cf301104288fba0df927c03babc0b77601b0b125b0f scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-evidence.py
9b7027b2f9b1b6d96788449d0d4fd373dfb76625ec06ff2e836086ce24fc7c0d scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/tests/acceptance-control-test.py
```

Independent final destructive-path source review (`plan_review`, about eight
minutes, no repeated tests/provider calls) found no list/sweep fallback. The job
resolves the stored reference, validates message/outbox/schedule identity and
due time, and the feature selects only the named entity. The final conditional
DELETE rechecks exact identity, archived/deleted state, deletion generation and
strict expiry. Restore/redelete races cannot turn this into a broad purge.
Processing fences guard attempt settlement, not the deletion transaction;
single-row conditional deletion makes replay safe. Do not claim generic
exactly-once execution or multitenant policy proof: Entity Smoke is schema-scoped
and tenantless. This review does not replace the still-missing live synthetic
seed/observer and control-survival proof.

Products and their selected apps may have their own images and deployment
targets. They reuse shared platform code, contracts and delivery machinery;
they do not need to inherit the core-platform image or run on its target.

- Shared platform modules own provider-neutral scheduling and job mechanics.
- Provider adapters own AWS/database translation.
- Products select apps through public mounts; apps/features own job meaning.
- Target composition selects adapters, configuration, identities and resources.
- `kanbien-core-platform` proves the machinery with harmless durable work.
- Entity Smoke proves application/feature integration with five-minute cleanup.
- Both proofs consume the same implementation, not copied scheduler engines.

Keep the bare `kanbien-core-server` minimal. Use the existing target-owned
persistence acceptance pattern for baseline scheduling proof; do not revive the
retiring staging deployment or assume `apps/platform-smoke` is a mandatory
dependency. Retirement of old products/apps is not part of this plan.

An outbox is the database-backed list of work waiting for delivery. A dispatcher
checks PostgreSQL for due reminders, hands them to the outbox, and sends pending
outbox work to the job queue. A worker runs the selected app's registered job.
Acknowledging a queue message permits its removal; accepting a minute trigger
is not proof that dispatch or the application job completed.

## Resume location and source baseline

Inspected source baseline: `67d4d652bc1e3053dd513d1cc9864b65e6209ad2`.
The worktree was clean before this documentation change.

- Branch: `chat/2026-11-22-16-40-platform-scheduling-and-entity-smoke-retention-cleanup`.
- Recorded worktree:
  `/home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-11-22-16-40-platform-scheduling-and-entity-smoke-retention-cleanup-649761195`.
- [Originating session record](../../../../commitLogs/2026/nov/22/2026-11-22-16-40-platform-scheduling-and-entity-smoke-retention-cleanup/README.md).

For this conversation use its recorded worktree explicitly, never the tool's
default deployment worktree. For a new conversation follow governed chat startup
and use that conversation's recorded worktree containing the required source.
This historical path is not authority to hijack another chat's worktree.
Do not automatically merge, rebase, commit or push.

The session records earlier local verification and the main refresh. Those
results are historical evidence, not proof of this future implementation.
The previously observed full `/tmp` is an environment issue to recheck only if
it affects the next operation; do not delete unrelated temporary work to fix it.

## Decisions and approval record

Independent app/product images and targets remain agreed direction. After the
regional estimate, the user selected A2 on 2026-11-26. A1 (minute ECS tasks and
idle workers) and B (individual AWS schedules) are unselected alternatives;
their prior comparisons below remain historical evidence, not implementation
instructions. The following table owns the current direction.

| ID | Decision | Proposed first-release choice | State |
| --- | --- | --- | --- |
| D1 | Authority for individual reminders | PostgreSQL owns due instants and durable reminder state; infrastructure owns a fixed minute wakeup | A2 selected |
| D2 | Delivery and execution | Fixed EventBridge trigger to bounded Lambda due scan and relay; one job SQS queue to a bounded Lambda worker per scope | Selected topology; Lambda support still needs proof |
| D3 | Operating cost | No per-minute ECS task; standard on-demand functions, no provisioned concurrency/pollers by default; itemized cost gate below | US$10 additional proof spend; US$25/month combined incremental ceiling at 100,000 jobs/month approved |
| D4 | Creation and recovery | Atomic feature/reminder writes; later minute passes catch overdue reminders and unsent outbox work; no separate provider registration or maintenance loop | Selected reuse direction; bounds pending |
| D5 | Precision and completion delay | Never before the stored due instant; declare a measured live completion deadline rather than promising exact execution time | Small live proof: five minutes after due, recovery ten minutes after restoration; not a production guarantee |
| D6 | First job scope | Existing metadata-only registered jobs in isolated proof scopes; no arbitrary job arguments or tenant scheduling | Proposed |
| D7 | Update and cancellation | Preserve create/read scope; decide internal cancellation and blocked-record recovery at the database handover boundary; no promise to retract already queued work | Resolve before affected implementation; general public editing deferred |
| D8 | Retry, poison records and overlap | One durable retry authority, safe repeated effects, explicit terminal/blocked outcomes and governed recovery | Settle exact state/settlement contract at M0 |
| D9 | First calendar rule | M8 owns local-calendar intent, timezone/DST resolution and durable occurrence generation into this path; no provider adapter presumed | Deferred |
| D10 | Execution authority | Autonomous bounded overnight A2 goal; existing governance still applies | Approved 2026-11-26; explicit follow-up permits governed merge/push to main after required checks |

Record approved changes with date, approving instruction/reference, affected
milestones and rationale. Never convert a proposal into an approval by changing
a table cell alone. Do not leave unresolved production semantics for the
implementing model to guess.

### Selected A2 first release flow

```text
Feature change + reminder committed together in PostgreSQL
                                    |
Fixed EventBridge minute wakeup     |
  |                                 |
  v                                 v
Bounded Lambda dispatcher ----> select due reminders
  |                            atomic reminder/outbox handover
  |
  +---- existing relay ----> job SQS ----> Lambda worker
                                              |
                                              v
                                 registered application job
                                              |
                                              v
                                  durable completion/failure
```

Lambda runs a bounded function when invoked; this plan does not keep dedicated
worker containers running while idle. Its managed SQS connection polls and
deletes successful messages. Our adapter reports which messages must retry; it
must not start a competing receive loop. Queue polling still has request costs.

One job queue per scope preserves the existing outbox-reference envelope and
publication-after-send rule. HTTP can create a durable reminder without cloud
scheduler credentials. The dispatcher can send jobs but cannot purge entities;
the worker receives only its own scope's jobs and approved application effects.

Each pass must progress existing outbox backlog even when it finds no new due
reminders. Overlapping ticks, late invocations and retries are expected: database
handover and publication claims prevent duplicate durable work while handlers
remain safe to repeat. Work count, elapsed time, database calls and job execution
are bounded. A missed invocation is recovered by a later pass, not lost because
its exact minute was missed.

The minute cadence is not an exact execution promise. Healthy lateness includes
trigger precision, cold starts, scan/queue delay and work bounds; outage recovery
also depends on backlog and capacity. No runtime Scheduler CRUD, registration
reconciliation, notification queue/function, separate five-minute maintenance
function or private Scheduler API endpoint is required by A2. The fixed trigger
and its permissions remain governed infrastructure, not app-owned AWS resources.

### Operating-cost gate

Optimize recurring infrastructure spend, not merely initial implementation
effort. A2 is selected from the initial comparison; M0 must validate its actual
region, network requirements, workload and bounds against the following
scenarios. A lower estimate is not a throughput or live-budget acceptance.

| Scenario | Required estimate |
| --- | --- |
| Idle month, no business jobs | Minute dispatcher invocations, empty queue polling, retained resources, logs/metrics and any new fixed network/database charges |
| 10,000 and 100,000 job occurrences/month | Due scans, handovers, relay and worker requests/duration, database queries/connections and storage |
| Burst, retry and outage recovery | Peak concurrency, queue/backlog drain, repeated provider calls and failed-message retention |
| Higher-volume crossover | At least 20 million occurrences/month, plus the target's forecast, compared with a correctly sized reused ECS/service alternative |

These are arithmetic cost scenarios, not instructions to generate that load or
permission for a cloud benchmark.

Use a 30-day model and distinguish occurrences from stored schedules. Compare
both incremental cost above today's accepted deployment and fully allocated
shared-resource cost; an existing PostgreSQL service is not free merely because
another scope currently pays for it. Keep human development cost separate.

Include the fixed EventBridge triggers, job queues and their failure destinations,
Lambda requests and billed duration/initialization, recovery attempts, PostgreSQL capacity/storage,
network transfer/access, image storage, logs/metrics and alarms. Record free-tier
availability across the account; show totals both without allowances and with
the genuinely available allowance. Do not hide fixed NAT gateway, interface
endpoint or database-proxy charges inside a nominally serverless design.

Baseline arithmetic, not a quote for this target:

- The superseded one-minute ECS design starts 43,200 checks in 30 days; a fresh
  Linux Fargate task's one-minute minimum gives at least 720 task-hours. It does
  not prove what a reused already-running service would cost.
- A2's minute tick means 43,200 dispatcher invocations per scope/month before
  retries, or 86,400 across both proof scopes. Include scan base time and
  per-occurrence handover/relay duration; on-demand execution is not zero idle cost.
- AWS currently advertises 14 million Scheduler invocations/month free, then
  $1/million beyond the allowance; this does not include job execution or grant
  each app its own free tier. See the dated pricing references below.
- Calculate function compute from measured invocations × billed seconds ×
  memory in GB × the selected region/architecture rate. Include dispatcher and
  worker work, retries and initialization; do not assume zero-duration jobs.

The approved overnight goal sets a US$25 combined incremental monthly ceiling
(including fixed charges and the 100,000-job scenario), US$10 additional proof
spend, proof completion within five minutes after due time and recovery within
ten minutes after restoring the deliberate interruption. These proof limits
are not production guarantees. M6 must have a complete estimate
and no unexplained fixed-cost addition before live authorization. M7 measures
actual idle behavior, duration, requests and connections; distinguish a monthly
projection from a fully observed monthly bill. Cost alarms alert; they do not
automatically cap spend. Never drop durable work to satisfy a budget.

Default proposals: no provisioned function concurrency or dedicated provisioned
queue pollers, no new always-running scheduler/worker, no new NAT/proxy solely
for this proof without a reviewed estimate. Bound function concurrency and DB
pools together. If safe Lambda access to the existing database needs expensive
new infrastructure, revisit the measured comparison before implementation;
do not silently switch runtimes or weaken private-access controls.

### Initial operating cost estimate

**Current selection:** the user selected the A/Lambda alternative, now called
A2, after this comparison. Its modeled subtotal is $17.18/month idle, $17.36
at 10,000 occurrences and $18.99 at 100,000, across both scopes without free
allowances. Those are projections with the exclusions below, not approved
budgets. The original A1/ECS and B estimates are retained as comparison evidence;
their topology and runtime adapter work are not operative requirements.

#### Target baseline and freshness

This estimate uses repository declarations and historical accepted evidence,
not a live inventory or an AWS bill. The declared profile is `kanbien-dev`,
region `eu-west-1`, target `kanbien-core-platform`; both proof scopes are included.

- [Target profile](../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/00-target/target-profile.yml)
  selects Ireland. Accepted pointers predate this estimate; they do not prove
  today's running counts, unused account allowances or database headroom.
- [Persistence template](../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml)
  declares private single-AZ PostgreSQL 18, `db.t4g.micro`, 20 GiB GP3, IAM
  authentication and seven-day backups. Entity Smoke uses the same database.
- [Network declaration](../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/network.yml)
  prohibits broad internet egress. Existing templates declare ECR, Logs and
  Secrets Manager private connections, but not SQS/Scheduler connections or a
  database proxy. This is not proof no shared alternative exists live.
- [Budget declaration](../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/budget-control.yml)
  records a $100/month target budget. It does not establish unused headroom or
  authorize increasing that budget.

A private connection here means an interface VPC endpoint: an AWS service
connection with an hourly charge in each selected availability zone. Assume
two zones, consistent with retained private-subnet evidence but not freshly
verified placement. B's in-VPC registration calls need Scheduler access; relay
and explicit queue API calls need SQS access. These connections are shared by
both scopes, not charged once per function or once per scope. Managed queue
polling/invocation itself does not require an extra Lambda interface endpoint.
See [Scheduler private access](https://docs.aws.amazon.com/scheduler/latest/UserGuide/vpc-interface-endpoints.html)
and [SQS private access](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-internetwork-traffic-privacy.html).

#### Regional prices and model inputs

USD, 30 days/720 hours, on-demand x86 functions, before tax, credits or discounts.
The following public regional price lists were read on 2026-11-26:

| Item | Rate | Regional source |
| --- | --- | --- |
| Lambda requests | $0.20/million | [Lambda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSLambda/20261125205755/eu-west-1/index.json) |
| Lambda duration | $0.0000166667/GB-second, first paid tier | Same Lambda source |
| Standard SQS requests | $0.40/million, first paid tier | [SQS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSQueueService/20261125150123/eu-west-1/index.json) |
| Scheduler invocations | $1/million after available allowance | [Scheduler](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSEvents/20261125150123/eu-west-1/index.json) |
| Private interface endpoint | $0.011/zone-hour and $0.01/GB, first data tier | [VPC](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/20261125055256/eu-west-1/index.json) |
| Fargate Linux x86 | $0.04048/vCPU-hour plus $0.004445/GB-hour | [ECS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/20261125150250/eu-west-1/index.json) |

`N` means total completed original schedule occurrences across both scopes,
not N per scope. Historical B base model: one small message per batch, one-second total
billed duration at 512 MB for delivery, worker and maintenance; no retries,
continuations or failures. Duration includes initialization, not just handler
time. These are explicit sizing assumptions, not measured application timings.
Post-commit registration runs in the existing HTTP process; there is no invented
registration Lambda invocation. API create/get/delete calls are not Scheduler
firings, though their network/HTTP resources still count.

For B, five-minute maintenance gives 17,280 invocations/month across both scopes:

```text
Scheduler invocations = N + 17,280
Lambda invocations   = 2N + 17,280
Lambda GB-seconds    = N + 8,640
SQS requests         = 6N + 2,592,000 empty-poll allowance
Endpoint fixed cost = 2 services × 2 zones × 720h × $0.011 = $31.68
```

The empty-poll allowance assumes five readers per mapping, twenty-second waits
and four primary queues. It is a conservative sensitivity, not an AWS guarantee;
at busy volumes it overstates full-month empties. AWS can optimize idle polling
towards two readers, but not when the mapping's maximum concurrency setting is
enabled. Do not remove a database-safety limit merely to obtain that saving.
Unconsumed failure queues have no empty polling charge.
[AWS SQS mapping scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html)

#### Historical B monthly infrastructure subtotal

Includes Scheduler, Lambda, SQS and new endpoint hours only. Other costs below
are deliberately outside this subtotal; these are not total monthly bills.

| Total occurrences/month | No free allowances remaining | All listed allowances available | No allowances, five-second worker instead |
| --- | ---: | ---: | ---: |
| 0 | $32.88 | $32.32 | $32.88 |
| 10,000 | $33.09 | $32.34 | $33.42 |
| 100,000 | $34.93 | $32.56 | $38.26 |
| 20,000,000 | $442.22 | $420.95 | $1,108.88 |

The allowance sensitivity applies 14 million Scheduler invocations, one million
Lambda requests, 400,000 Lambda GB-seconds and one million SQS requests once to
the combined workload. Actual remaining account allowance is unknown. Both
endpoint services remain chargeable; no free allowance is assumed for them.
Sources: [Scheduler pricing](https://aws.amazon.com/eventbridge/pricing/),
[Lambda pricing](https://aws.amazon.com/lambda/pricing/),
[SQS pricing](https://aws.amazon.com/sqs/pricing/).

At 100,000 occurrences, 10% extra complete-path work adds about $0.20 to the
no-allowance base subtotal; real retries affect different stages and can cost
more. Batching can reduce requests but does not divide job compute by batch size.
Twenty million is an arithmetic sensitivity, not demonstrated capacity: repeated
cleanup scans, burst concurrency, provider quotas, continuation jobs, storage
growth and PostgreSQL CPU/connection limits must be measured independently.

#### Fair low-volume alternative comparison

All rows cover both scopes with the same two-zone assumption, no free allowances,
and exclude the same additional/shared costs below.

| Design | Idle | 10,000 occurrences | 100,000 occurrences |
| --- | ---: | ---: | ---: |
| Unselected A1: minute ECS tasks plus idle ECS workers | at least $51.58 | at least $51.59 | at least $51.70 |
| Selected A2: minute Lambda scans and Lambda workers | $17.18 | $17.36 | $18.99 |
| Unselected B: individual AWS schedules and Lambda pipeline | $32.88 | $33.09 | $34.93 |

Original A1 assumes two scanner tasks/minute, two always-on workers and each
0.25 vCPU/0.5 GB. Its 2,880 minimum task-hours cost $35.55, plus a shared SQS
endpoint in two zones ($15.84); startup beyond the Fargate minimum adds cost.
Its two worker long polls assume one reader each; task/worker capacity is not
claimed to sustain the high-volume scenario.

A2 needs only the SQS endpoint for these runtime calls. It uses 86,400
fixed Scheduler invocations, `N + 86,400` Lambda invocations, `N + 43,200`
GB-seconds and `3N + 1,296,000` SQS requests. This includes one second of scan
base time per minute AND one second of handover/relay work per occurrence,
plus the one-second worker; it does not price database scanning as free.
Bounded batches, overlap and actual duration still need proof.

Selected A2 retains database-owned timing and its calendar/DST engineering
responsibility, deferred to M8. Unselected B buys managed per-schedule timing
and a provider calendar path, not a proven lowest bill. Different B registration placement
could reduce endpoint needs, but adds coordination boundaries and is not costed
or selected here. Do not weaken private networking or adopt a different flow
without reviewing reliability and cost together.

#### Additional and allocated costs

- Existing PostgreSQL is not another mandatory instance: its declared size is
  approximately $14.78/month at on-demand rates ($0.017 × 720h + 20 × $0.127
  storage), excluding CPU-credit excess, extra backups, traffic and growth.
  Allocation of that baseline to scheduling is undecided; count only incremental
  resizing/storage in extra spend, but show the allocated share in a full-cost
  report. [RDS regional prices](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/20261126153047/eu-west-1/index.json)
- Retained images cost $0.10/GB-month; logs cost $0.57/GB ingestion and
  $0.03/GB-month stored; standard alarm metrics cost $0.10/month. For illustration,
  2 GB retained images, 1 GB ingested/stored logs and six alarm metrics add $1.40,
  not a guarantee that production telemetry fits that allowance.
  [ECR prices](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECR/20261125150217/eu-west-1/index.json),
  [CloudWatch prices](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonCloudWatch/20261125150240/eu-west-1/index.json)
- Add actual endpoint bytes, cross-zone transfer, custom metrics/log queries,
  selected encryption-key charges, additional shared HTTP work, DB rows/indexes,
  WAL/backups and any capacity increase. No new NAT or proxy is assumed.
- The existing network/HTTP/observability baseline is shared, not zero cost.
  A fully allocated total needs live resource counts and an allocation policy;
  this estimate does not establish either or current $100-budget headroom.
- One-zone endpoints halve their fixed charge, but that changes availability
  and possibly cross-zone traffic. It is a sensitivity, not the selected saving.
- Temporary qualification, restore tests and fault tests are separate execution
  costs, not steady-state operating spend.

**M0 disposition:** A2 and the overnight limits above are approved. The historical
subtotal is still not a complete live estimate. Confirm network placement,
current bill/headroom and billed durations before their consuming stages;
no milestone is complete merely because this arithmetic was checked.

## Governing instructions

This plan coordinates work; it does not replace owning workflows or grant their
authority. At each milestone read the applicable owner and its required inputs.

| Work | Existing owner |
| --- | --- |
| Session/worktree | [Chat startup](../../../00.chat/workflows/chat-start.md) and the active session record |
| Runtime and public boundaries | [Platform runtime workflow](../../workflows/platform-runtime-implementation.md), including its required ADR reads |
| Feature changes | [Feature workflow](../../feature/workflows/create-feature.md) and applicable feature/entity skill |
| Configuration | [Runtime settings standard](../../standards/config-runtime-settings.md) |
| Public modules | [Module structure standard](../../standards/public-module-structure.md) |
| Completion and reuse | [Change completion](../../../shared/standards/require-change-completion.md) |
| Failure reporting | [Diagnostic coverage](../../../shared/workflows/verify-diagnostic-coverage.md) |
| Verification | [Test execution](../../../shared/testing/standards/test-execution.md) |
| New script admission | [Script admission](../../../01.harness/standards/script-admission.md) |
| Program composition | [Runnable program workflow](../../../04.deploy/20-build/workflows/prove-runnable-program-builds.md) |
| Package custody | [Immutable publication workflow](../../../04.deploy/40-package/workflows/publish-immutable-package-with-custody.md) |
| Target changes | [Review target update](../../../04.deploy/50-deploy/workflows/review-and-execute-target-update.md) |
| Acceptance and recovery | [Verify or restore release](../../../04.deploy/60-run/workflows/verify-accept-or-restore-release.md) |
| AWS authority | [Plan AWS change](../../../aws/workflows/plan-aws-change.md) and [execute approved change](../../../aws/workflows/execute-approved-aws-change.md) |

Before code changes follow Educate While Execute unless the user has explicitly
authorized autonomous execution. A missing governed operation, unresolved
ownership, or required expansion of authority stops the affected action; use the
owner to resolve it rather than improvising a CLI command or exception.

## Existing implementation and reuse inventory

All paths in this table existed at the inspected baseline. Recheck affected
owners on resume; proposed new paths appear separately in M1/M5.

| Owner | Existing implementation | Disposition |
| --- | --- | --- |
| Core time | `packages/core/src/shared/time/{contracts,date-time,clock}.ts` | Reuse Clock, fixed/system clocks and UTC timestamp representation |
| Core IDs | `packages/core/src/shared/uuid/{contracts,generator}.ts` | Reuse UUID generator; no second ID mechanism |
| Job contracts and selection | `platform/contracts/src/jobs.ts`; `platform/runtime/src/registry.ts` | Resolve only selected public app mounts and registered jobs |
| Reminder contract | `platform/persistence/src/scheduling.ts` | Reuse durable one-off reminder ownership; extend cancellation/blocked state only for agreed semantics |
| Callable due pass | `platform/persistence/src/schedule-delivery.ts` | Reuse `runOnce()`, `listDue` and handover; compose bounded scan/relay rather than replace them |
| PostgreSQL reminder store | `platform/adapters/aws/persistence/postgresql/src/scheduling.ts` | Reuse row-lock and atomic outbox handover; extend required guards through immutable migrations |
| Outbox delivery | `platform/persistence/src/relay.ts` | Reuse durable claim/send/publication-marker sequence |
| Durable execution | `platform/persistence/src/processing.ts`; PostgreSQL `src/processing.ts` | Reuse leases, fencing, retries and completion |
| Transaction ownership | `platform/persistence/src/transaction.ts`; PostgreSQL `src/transactions.ts` | Extend participation deliberately; not a drop-in feature transaction today |
| Worker | `platform/workers/src/{worker,main,types,queue}.ts` | Reuse execution/processing; expose bounded record execution for Lambda, not an in-memory requeue or a copied worker |
| SQS | `platform/adapters/aws/queue/sqs/src/{queue,worker}.ts` | Reuse sends and codecs; add managed-function batch translation, do not run manual polling alongside Lambda mapping |
| Feature rules | `apps/entity-smoke/features/test-entity/domain/retention.ts` | Preserve feature-owned five-minute elapsed rule |
| Feature registration | `apps/entity-smoke/src/persistence/app.mount.ts` | Preserve `entity-smoke.test-entity.purge-expired`; fix failure propagation |
| Feature composition | `infra/04.deploy/03.product/entrypoints/entity-smoke/runtime.ts` | Existing HTTP composition stores reminders; it does not run the pipeline |
| Baseline proof | `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts` | Reuse target-owned harmless acceptance pattern |
| Build and delivery | Existing workspace builders, image builders, provider controls and scope bindings named in M5/M6 | Extend shared owners; no app-specific execution engine copies |

The job name is not necessarily its queue message type. Resolve
`PlatformJobRegistration.messageType`; do not infer equality from the current
Entity Smoke convention. Existing outbox metadata and the relay's
`{outboxEntryId}` envelope do not provide arbitrary job arguments.

### Current implementation and remaining delivery gaps

Bounded due-reminder handover/relay, durable worker attempts and retry timing,
SQS batch settlement and separate baseline/Entity Lambda compositions are now
implemented. Entity deletion and reminder creation are atomic; handler failures
propagate and purge/save operations guard against stale state. Controlled tests
and the recorded native PostgreSQL proofs exercise these mechanisms. Their
recorded boundaries do not establish finished-image or AWS acceptance, and the
current combined verification report still governs integration readiness.

Reusable Lambda packaging and activation-control source now exists; its source
admission is not permission to invoke an unqualified release. Remaining delivery
gaps are actual managed-runtime image qualification; additive migration-prefix
and effective scheduling-role permission proof; immutable version/queue/trigger
binding; separate disablement/recovery controls; and scheduler alert evidence.
The relevant scope exclusions must be amended deliberately, not erased wholesale.
Shared-VPC compatibility work is explicitly authorized but still needs governed
proof preserving existing staging consumers. The operating-cost ceiling needs a
measured forecast. No automatic AWS scheduling, live cleanup or calendar/DST
capability is claimed. M1–M4 evidence below replaces the obsolete initial gap list.

## Milestone dashboard

### First remaining implementation handoffs (not completed work)

#### Connected phase-specific scheduler admission — inventory before edits

Proposed path: `scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/admission.py`
Role: helper
Owner and capability: existing scheduling-control, not a second deployment engine
Purpose: derive disabled-resource, preflight and activation facts from existing authenticated package/task owners and actual provider observations
Direct consumers: existing scheduling controller and its fixed acceptance reader
Named risks: forged or stale readiness, shared private-DNS access loss, unqualified activation, uncertain mutation replay, unbounded spend
Proof lane: deploy/run; existing scheduling-provider-controls fixture, live proof remains separate
Execution boundary and actual child effects: local and network reads through the existing Provider; no independent mutation, provider, store, registry or runner
Relevant inputs and evidence invalidation: controller/helper/bindings/realization contracts, package source/digests/configuration, actual VPC/security-group/IAM/queue/database identities, retained task/invocation evidence and cost facts
Expected cost and measurement: controlled fixture target10seconds, conservative30second check budget; measure live reads separately
Retained manual/deferred route: mutation remains closed until actual phase gates and provider-owned ordering rule exist; no passed boolean substitutes
Existing capability considered: current package/task custody readers, generic realization compiler, CloudFormation normalizer, shared change-set and reservation engines
Reuse decision: one fact-composition helper and existing fixture; preserve original controller as the effect owner
Why a script is necessary: the three phases need different genuine prerequisites, absent from the current unconditional hardblock

The connected controller must preserve non-owned UPDATE parameters, admit only
control toggles during activation, select retained execution before refreshing
live inputs, bind fixed original intent rather than arbitrary retry labels, and
verify exact deployed template/parameters/resources after original-token terminal
completion. AWS transport must not silently retry mutations. Network creation
requires a full-VPC current consumer inventory and preservation of actual legacy
roles/security groups/queue access. Unknown consumers block private DNS.
No stopped staging service is scaled or repaired. Real same-runtime worker
GetQueueAttributes proves endpoint transport; it does not claim old staging
application execution. Initial proof spend and measured monthly forecast are
separate gates; timeout limits and local test time are not billed-duration proof.

The user explicitly approved the disabled-deployment/read-only-test ordering
rule on 2026-11-27. Adopt that narrow rule at its provider owner; this approval
does not waive source, package, network, database, cost or realization checks.
No provider mutation has occurred.

Exact provider adoption surfaces: new
`.agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/50-runtime/deploy-disabled-scheduling.md`,
the existing operational-realization applicability standard, both scopes'
`00-declaration/scheduling-realization-contract.yml`, and each existing
`10-workload-binding/scheduling-binding.yml` realization-contract reference.
Use the existing realization compiler/gates, not another gate engine.
The same source-owned scheduling CloudFormation template may add a false-default
`DenyDispatcherSend` proof control: only SendMessage from that scope's own
dispatcher to its own new job queue. Its controlled-failure test is ordinary
governed execution after readiness, not another preflight exception. Both
automatic controls remain disabled during this deliberate fault; restore the
exact normal queue policy before activation/acceptance. Preserve every other
parameter and use existing immutable operation/reconciliation machinery.

#### Same-runtime read-only connection proof — inventory before edits

Reuse `entrypoints/shared/scheduling/invocation.ts`, its existing diagnostics,
the core composition `runtime-test.mjs`, and managed-image qualification/runtime
API fixtures. Add a closed `scheduling-preflight/v1` request before application
composition. It authenticates with the unchanged function's own PostgreSQL IAM
identity, uses a read-only transaction for identity/schema/table checks, and
for the worker only resolves regional SQS DNS and performs GetQueueAttributes
on its own queue. The dispatcher receives no extra queue permission. Return
bounded identity/route facts, no rows/secrets; normal dispatch never serves as a
connection probe. Reject malformed preflight and short deadline before resource
creation, sanitize SQL/DNS/SDK errors, always close owned resources. Tests must
prove zero job composition/schedule/outbox writes, correct role/schema/queue,
wrong facts and raw-error privacy. Actual Lambda invocation custody and endpoint
ENI matching belong to the outer controller, not this returned JSON alone.
No automatic control, business data, recurrence or DST changes in this slice.

Preflight diagnostic predicate inventory: closed request and actual invocation
identity, remaining-time budget, connected database session identity, effective
schema/table SELECT access, bounded DNS result, own-queue ARN, and cleanup.
The target-owned `scheduling-target.preflight-failed` definition distinguishes
predicate rejection from a thrown dependency observation at those finite checks;
existing adapter diagnostics remain preserved by the final invocation reporter.
No provider errors, SQL rows or internal addresses enter diagnostics. The private
receipt projects only source/request/function/selected database identities and
a canonical DNS-address-set digest; the controller must authenticate invocation
custody and independently compare current endpoint identities. Planned focused
proof: existing `scheduling-composition`, plus existing managed image Runtime API
qualification. Returned JSON alone is not accepted deployment evidence.

#### Connected synthetic runtime operations — inventory before edits

Reuse existing target administration/verifier owners, not app features or a
generic SQL console: entrypoints shared/persistence/{scheduling-administration,
configuration,operation-diagnostics}.ts, core persistence administration main,
entity-smoke/{administration,verification,diagnostics}.ts, Entity verifier main, and existing
core/Entity composition runtime-test.mjs. Core seeds only the existing harmless
job with an externally reserved Core UUID and checked UTC due time. Both scopes
observe exact selected IDs in a read-only transaction; report finite physical
presence and schedule/outbox/processing state, not business rows or SQL. Entity
uses actual HTTP create/reconcile/archive/delete/restore, retains actual UUID
and full-facts digest before mutation, and discovers the unique reminder by
exact entity/deletion generation. Never override app identity or sweep rows.
Existing task/result custody and strict readers must connect before live use.
Tests cover loss/reconciliation, wrong IDs/facts, no broad query, privacy and
stale generation; native/live proof remains distinct. Existing operation
diagnostics retain original errors and unknown mutation effects.

Connected task custody inventory: core run-administration, proof-receipts,
task-operations and task-operation-test; Entity existing task-control/evidence/
route/steps and their request/result/route fixtures; both scope declaration
operation selectors; shared release-succession/scheduling-proof.py for the
closed seed/snapshot DTO. Preserve existing immutable task submission and
original-log custody. Reserve exact proof UUID/due before core seed; Entity
retains the real creation UUID and fact digest and uses that same creation label
for subsequent lifecycle operations. Finite source-owned observation names
distinguish before/after/recovered/duplicate/restored/not-yet-due reads; mutation
uncertainty never permits a fresh creation label. Extend existing Entity
verification, the new scheduling diagnostic v2 and existing fixture with a
bounded real HTTP scheduling-restore operation; unchanged diagnostic v1 remains
fixed. Initial source-only TS success does not claim this connected task or
restoration proof has passed. Existing registered task/acceptance tests must
reject mismatched reserved selection, stale generations and missing original
logs before provider execution. No new runner or generic SQL operation.

Reuse Entity orchestration `feature-steps.py` original-terminal reader for the
fixed scheduling-create selection as well as its unchanged baseline default.
The existing task stage, not an arbitrary caller operation, chooses that
selection. This preserves original reservation identity/order during lost-create
reconciliation. Snapshots may privately retain the exact existing public
outbox-to-queue serializer result for one completed selected entry; the duplicate
proof sends that retained envelope, never a reconstructed business payload.
The restored-control verifier keeps archive/delete/restore together inside the
real recovery window and retains the original deletion generation for later
observation. Lost original evidence must not cause another deletion.

Untouched-control completion uses those same owners: the fixed Entity
`scope-isolation` case allows only create/reconcile and exact subject-ID
observation, with no deletion generation. Its observer omits the due filter but
keeps the ID predicate and LIMIT 2 and requires no reminder to exist; it is not
a broad inventory or arbitrary query. Preserve all generation-bound deletion
cases. The existing DTO and native task/archive tests cover missing original
creation evidence, an unexpected reminder, and forbidden delete/restore in this
case. No new files, app behavior or retention policy. Focused tests budget two
minutes excluding the shared compiled payload; record actual elapsed time.

Packaging closure correction: the existing Entity composition
`dependency-boundary.mjs` and Entity image `Dockerfile.dockerignore` must admit
the already copied shared `scheduling-administration.ts` and core persistence
IAM-authentication helper. Reuse those owners; no duplicate implementation or
new image is introduced. The focused Entity composition proves the exact
compiled closure; managed-image qualification remains separate.

#### Fresh database readiness — connected reader inventory

Reuse core `run-migration/script.py`, `run-administration/script.py` and
`task-operation-test.py`, Entity `acceptance-evidence.py` and its existing
acceptance-control fixture, and shared `scheduling-database-state.py`. Factor
existing original ECS/log reconciliation and authenticated maintenance custody;
do not accept historical JSON integrity as live readiness. Each scope reader
joins the actual current task definition, source/image and database incarnation
to distinct ordered state/grant/prove receipts newer than the controller's
retained preparation boundary. All observe the same complete seven-migration
manifest; the final observation must show zero waiting/outbox/processing rows
before the first synthetic proof. Historical prefix/apply lineage remains a
separate final-acceptance requirement. Only finite comparison of already
authenticated facts is shared; provider provenance stays with each existing
owner. Counterexamples: missing original logs, stale tasks, wrong database or
image, reordered receipts, incomplete manifest and unrelated pending work.
No new scripts, database mutations or activation authority are added here.

#### Connected controller phase admission — next existing-owner increment

Continue in scheduling-control/{script.py,admission.py,smoke-test.py}, current
bindings/realization contracts and provider ordering workflow as needed. Reuse
the immutable reservation and shared change-set engines. Fixed source-owned
phase and preflight slots must resolve original uncertain execution before any
fresh reads or retry; known-completed refresh and historical validation have
different freshness rules. Validate network-context IAM conditions as well as
queue policies, and distinguish initial compatibility inventory from preserved
consumer readback after endpoint creation. Fresh database readiness and priced,
enforced proof-cost limits remain independent required inputs. The existing
focused provider-control test owns wrong-phase, replay, stale-readiness,
parameter preservation and changed-network counterexamples. No new script or
provider permission is implied.

#### Core scheduling acceptance lineage — connected producer inventory

Extend existing run-administration/script.py, run-migration/script.py,
proof-receipts.py, task-operation fixtures, shared profile/input schema and
core collector/updates/readers. Reuse authenticated maintenance custody and
current database-incarnation observation; factor rather than copy their checks.
Scheduling-only retained context carries source_revision, image_digest and
dependency_incarnation_sha256. A real apply also binds prefix_receipt_sha256.
The explicit scheduling profile retains original prefix and optional apply
documents in existing proof_set; complete-state manifest and binding must match,
with genuine apply after a partial prefix and no fabricated apply for complete
prefix. No-profile historical acceptance remains unchanged. Test actual archive
handoff, changed source/database, missing/foreign receipt and chronology.
Entity scheduling qualification is deliberately successor/requalification-only
with its actual expected predecessor; initial baseline qualification is not
silently reinterpreted as a seven-migration scheduling bootstrap.

Run-proof registration extends the existing core collect-acceptance-evidence
parser and Entity acceptance-route parser with
`--require-qualification-profile scheduling-a2-v1`. Reject a missing/different
input-manifest profile before provider reads; preserve unflagged history and
ordinary HTTP acceptance. Existing shared scheduling-proof-test owns this
counterexample. Two declared run checks use those canonical collectors with the
mandatory profile; both scheduler program requirements reference that scope's
same canonical check. This names the required live route without claiming it
has run, and never aliases ordinary HTTP proof to scheduler acceptance.

#### Runtime proof and operating-cost composition — script admission

Independent acceptance review found two semantic errors in the existing proof
reducer, not in the application scheduler: it expected exactly five minutes
instead of the application's `max(deletedAt + five minutes,
restoreEligibleUntil) + one millisecond`, and it allowed protected-row snapshots
taken entirely after the demonstrated purge. Correct only `proof.py` and its
existing `proof-test.py` consumers: reuse the authenticated lifecycle facts and
require control snapshots to bracket the actual minute-delivery purge, using
its authenticated outbox creation and durable completion times. A future row
uses the real five-minute policy and one-minute restore window; it must not
be artificially kept future throughout the later interruption tests. Existing
finite retention/control rejection codes remain the caller explanation. Add
ordinary/extended-recovery boundary counterexamples and a post-purge-only
control counterexample, including the complete acceptance fixture. These are
local proof corrections; no app policy, provider effect or new registry changes.
The same review found canonical live acceptance did not call the existing
read-only actual wiring observer. Reuse it before consuming the remaining
acceptance evidence; an actual configuration mismatch must reject at the final
reader even if historical templates and packets match. Its controller owner
also checks actual reserved concurrency against the unchanged source contract.
The focused boundary fixture must prove the observer's failure reaches the
canonical caller before cost evidence is accepted. Historical readers remain
offline and cannot grant live activation.
Correction evidence: fifteen focused durable-case, control-join and complete
acceptance-composition tests passed in17.224seconds. The new live-reader wiring
rejection fixture passed in1.522seconds after correcting its overbroad Store
mock; the real original-reservation validator remains exercised. These are
controlled local results, not AWS execution or final registered integration.

Connected proof-efficiency correction: reuse the completed minute-delivery
original for duplicate delivery, rather than seed another job. `proof.py`
requires that exact delivery selection, unchanged durable state and an actual
later duplicate send/worker skip; `script.py` authenticates the minute case at
the existing effect boundary. Existing native `duplicate` observation slots
already support this. Extend their existing tests to reject a substituted
original and post-purge-only controls. No application policy or execution
authority changes. This removes three core maintenance tasks and four Entity
operations (each with its own preflight) from the planned live route.

The controller now imports the canonical acceptance/native resource readers
already covered by the runtime-proof input closure. Reuse that exact bounded
closure for all three scheduling checks in `checks.yml`, removing the narrower
provider-only list. The existing repository-contract test must prove shared
membership, dependency invalidation and affected-check routing. No new check,
root wildcard or registry is added; old cached results are invalidated by the
changed input contract. Focused proof and catalog tests have a two-minute
development budget; complete registered verification waits for source freeze.

User explicitly authorized cleanup of only disposable database copies and
snapshots newly created for this scheduler proof, after success or confirmed
terminal failure, with original identities, no active/unresolved dependents and
retained evidence. Existing backups/source database/unrelated resources remain
protected. Implement that rule at existing recovery/resource owners. Reserve a
two-hour priced cleanup target for each new disposable database clone within
the unchangedUS$10 total; it is not an AWS TTL or deletion authority. Successful
snapshots adopted as recovery backups remain protected and their ongoing full
allocated storage is included in the monthly forecast. Clean up
promptly when eligible, retain charged reservations without refunds, and count
actual longer-lived obligations rather than capping liability at the target.
Missed cleanup targets block new paid work and require escalation; verified safe
cleanup remains possible. No live resource has been created by this increment.

Connected runtime evidence inventory: extend existing shared scheduling
`composition.ts`, `invocation.ts` and the scheduling section of core composition
`runtime-test.mjs`. Reuse the safe logger and actual dispatcher/worker result.
Emit bounded dispatch counts and successful worker outcome/attempt, with a digest
of the authoritative outbox identity (never payload, row facts or raw ID), tied
to actual request, immutable function version and source. Missing/invalid runtime
identity or logging failure must omit evidence without changing business work.
These are private observation records, not new diagnostic definitions or a
second execution engine. Prove real success/duplicate correlation, failed work
not labelled success, metadata omission, raw-canary exclusion and logger failure
preserving completion. The provider reader must still reconcile original AWS
logs, billed reports and exact selected database observations; logged JSON alone
does not prove automatic trigger or durable business outcome.

Automatic-trigger attribution also extends the existing FixedTick input and
its exact provider readback with AWS's documented schedule ARN, scheduled time,
execution ID and attempt placeholders. Dispatch observation projects only the
checked schedule/time/attempt and execution-ID digest; malformed or absent
metadata is omitted without selecting work or preventing a due pass. Match
actual source-owned Scheduler target/input and group InvocationAttemptCount
alongside original Lambda logs and database state. Neither caller-controlled
event text nor an enabled schedule alone establishes automatic execution.
No new environment value, provider permission or trigger is added.

The reserved controlled-failure invocation additionally uses the existing
Lambda ClientContext channel with only its original proof-operation UUID.
`invocation.ts` emits a best-effort start record tied to actual source, numeric
function version and AWS request. This is not a success record, job selector or
permission to retry. A missing record leaves the original invocation unknown.
The compiled composition fixture proves an actual failed dispatch keeps its
failure, omits a completion claim and is not prevented/replayed by malformed
optional metadata. Compile and controlled fixture passed after this addition;
no AWS invocation is implied.

Retained case composition extends the existing `proof.py`/`proof-test.py` owner:
join the complete original control sequence with immutable component custody,
native selected-row snapshots, original runtime windows and Scheduler metrics.
Bind every task to the source/image/database incarnation and every invocation
to its actual version. Native task/phase owners reobserve provider evidence for
live collection; their pure readers are historical checks only. Reuse original
core state/grant/permission journal receipts through the existing administration
reader, rather than rerun grants or add a second permission evidence format.
The same packet reader now supports those three closed preparation operations;
its native controller fixture passed in0.669seconds. Missed-tick and failed-send
reducers require observed retained work before recovery; thirteen focused
runtime/case/automatic-trigger tests passed in0.317seconds. Canonical full
acceptance, measured monthly cost and operational alert delivery remain open.

The remaining fixed acceptance join and command exposure belong to the existing
controller and proof helper, not another executable runner or evidence registry.
Its closed cases must reject missing controls, changed source/image/database,
foreign/modified original tasks, early purge, absent automatic execution,
unexplained pending work, duplicate effects and incomplete cost/alert proof.
Retain shared packets once within the existing bounded qualification bundle;
content references are internal deduplication, not another durable registry.

Proposed paths: `scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof.py` and `proof-test.py`
Roles: helper and focused controlled test
Owner/capability: existing scheduler provider control and its canonical runtime acceptance reader
Purpose: compose independently retained task/invocation/control evidence, calculate explicit paid-cost projections, and reject incomplete or foreign runtime claims
Consumers: existing controller's phase admission and fixed validate_acceptance_evidence API; existing shared scheduling-proof reader
Risks: fabricated or partial success, cross-release/database evidence, guessed compute costs, omitted fixed charges, unbounded proof spend
Proof lane: focused local contracts; real runtime acceptance remains a distinct provider-owned route
Effects: helper read-only composition; actual provider effects remain existing controller/reservations; tests controlled and local
Inputs/invalidation: exact helper/test/controller/selected task owners, immutable source/images, actual invocation reports and retained source-bound cost facts
Budget: focused fixture estimate10seconds; no new recurring AWS job or independent runner
Reuse: existing scheduling-proof envelope/profile, task receipt custody, provider observations, Core IDs, immutable reservation writer and paid-rate worksheet
Why new helper: provider acceptance and cost composition have no existing implementation; foundation budget validation does not prove this scheduler's incremental ceiling
Approval: prior explicit bounded deployment helper/test additions, including >50lines; no extra AWS authority inferred

**Additional authority, 2026-11-27:** user explicitly approved "Authorize the
narrow rule and read-only permission update" for the existing publisher's
`ecr:DescribeRepositories` check. This covers a narrow provider-owned harness
rule and governed foundation UPDATE for that action on the existing repository;
all unrelated permissions, shared resources, spend and synthetic-data limits
remain unchanged. No live update has yet occurred.

Foundation script admission, before creation:
Proposed paths: `scripts/04.deploy/lifecycle/50-deploy/capabilities/foundation-access-update/script.py` and `smoke-test.py`
Roles: operation and test respectively
Owner and capability: governed foundation delivery-observation-access UPDATE, not runtime bootstrap or budget control
Purpose: admit only the reviewed `ecr:DescribeRepositories` addition on the existing image repository and prove safe reconciliation
Direct consumers: narrow provider-owned foundation update workflow and its explicit operator invocation; existing core-persistence/scheduler publication prerequisite
Named risks: unowned IAM widening, lost parameters, resource replacement, duplicate uncertain submission, false terminal success and unsafe diagnostics
Proof lane: package/deploy operation; focused local integration test `foundation-access-update-contracts`
Execution boundary and actual child effects: plan/observe use provider reads; approved prepare/execute submit only the exact reviewed CloudFormation UPDATE; tests use controlled provider responses and disposable reservation files
Relevant inputs and evidence invalidation: controller/test, technical-access declaration/reader, foundation template, exact workflow/applicability rule and consumed shared helper identities
Expected cost and measurement: local test budget30seconds estimated; measure actual run; no recurring AWS action added
Retained manual/deferred route: permission update is unavailable until reviewed committed source and prerequisite evidence pass; unknown outcomes observe original intent only
Existing capability considered: budget/bootstrap/scheduling controllers cannot own this delta; reuse unchanged cloudformation-template/change_sets/resource_reservation/cli/response/foundation-checks and deployment-operation diagnostics
Reuse decision: new bounded owner with existing engines, two scripts and a small guide; no extra wrapper/registry
Why scripts are necessary: no existing governed owner preserves all foundation parameters while allowlisting this exact nonreplacing permission delta

The new narrow workflow and provider applicability adoption follow the user's
explicit approval above; ordinary realization restrictions and retired incident
exceptions remain unchanged. Preserve all nine existing parameters through
UsePreviousValue, including the private alert setting. Actual original-template
equality, unchanged resource/role identities, one Modify/DeliveryRole/nonreplacing
change and original execution token's terminal readback are required. Bounded
script-size/folder authority is the prior explicit approval, not this record.

The deployment controller currently validates only the shape of caller-supplied
package receipts. Its public mutation route remains closed. The next connected
correction reads the exact successful protected-main publication run and its
immutable artifact from GitHub, then compares the downloaded custody document
with the selected local receipt. Both scheduler scopes consume the same helper.
The shared `package-custody-receipt/validate.py` remains the schema owner;
`build-managed-handler-image/publication.py` remains the source-owned repository,
workflow and program binding. `qualification.py` remains the managed-runtime
proof owner. Neither an arbitrary JSON verdict nor a matching local file hash
becomes publication authority. Existing workflows and mutation hardblocks remain
unchanged until database, network, cost and realization admission also connect.

Proposed path: `scripts/04.deploy/lifecycle/40-package/package-custody-receipt/github-artifact.py`
Role: helper
Owner and capability: existing package-custody receipt capability
Purpose: read and validate a successful main-branch workflow artifact through GitHub's authenticated read API
Direct consumers: scheduling-control qualified-pair for core-server-persistence and entity-smoke
Named risk: forged, foreign, expired, duplicate or stale-run local receipts accepted as qualified packages
Proof lane: package/deploy; controlled-provider assertions in existing scheduling-provider-controls local check
Execution boundary and actual child effects: bounded `gh api` GETs only; in-memory archive reads, no extraction, publication or provider mutation
Relevant inputs and evidence invalidation: source-owned publication binding, workflow run/source/artifact identity and archive digest, receipt validator and managed-image qualification shape
Expected cost and measurement: local fixture under10seconds estimated; live lookup at most one run/list/download chain per selected package, record measured time
Retained manual/deferred route: public deployment mutation remains blocked until complete trusted admission; no manual bypass
Existing capability considered: package receipt schema/qualification/workflow guards and shared ECR publisher; legacy readiness readers do not authenticate these custody artifacts
Reuse decision: extend existing custody capability with one bounded helper, reuse existing controller test and catalogue identity
Why a script is necessary: archive provenance is a distinct reusable read boundary absent from the existing receipt schema validator

Prior bounded helper/folder/>50-line approval covers this helper; no new folder
or recurring check is proposed. Existing test/check inputs must include all
consumed helper, producer and qualification owners. Diagnostic predicates are
missing/wrong binding, unavailable or malformed API response, unsuccessful or
foreign workflow/source, wrong/duplicate/expired artifact, digest/size mismatch,
unsafe or duplicate archive member and selected receipt mismatch. Emit fixed
custody-owned codes, propagated through the controller's existing safe result;
never expose API bodies, credentials, URLs, archive contents or native errors.
Fixtures will exercise the actual qualified-pair caller and prove rejection
before AWS mutation; they do not constitute live publication evidence.

API references inspected for the read contract:
[GitHub artifact API](https://docs.github.com/en/rest/actions/artifacts) and
[workflow-run API](https://docs.github.com/en/rest/actions/workflow-runs).

#### Connected scheduling acceptance profile — resumed inventory before edits

Continuation review, 2026-11-27: the final connected reader remains in the
existing scheduling-control `proof.py`, exposed by its existing controller;
the canonical acceptance profile is still the only release qualification owner.
It joins original disabled/control phases, typed native archives, original
queue/failure effects, automatic invocation evidence, whole-scope work counts,
connection checks, measured cost and the existing alert receipt. Missing or
unused originals, mismatched source/incarnation, pre-send duplicate observations
and unowned pending work must reject. Original archive deduplication preserves
every reconstructed native record within the existing two-MiB bundle bound;
it is not a second evidence store. New focused joins reuse native readers and
their tests, not copies of task authenticity rules. Runtime proof remains
incomplete until both actual canonical acceptance routes succeed.

Current local evidence: archive codec23 tests passed in11.91s total; connected
selection/runtime semantics21 tests passed in0.956s; cost/pricing19 tests passed
in0.350s. The price freshness check now distinguishes a freshly fetched current
offer from its potentially older AWS publication date. Actual existing alarm
history was read to confirm the provider's millisecond timestamp shape; no alert
was sent and no AWS/shared-database write occurred. Independent review found
resource-policy-only queue access and subnet network ACLs missing from shared
network preservation; their owning admission checks are being corrected.
Fresh isolated restore is still required by changed recovery inputs. The
original proof budget currently lacks its snapshot/clone lifetime accounting;
existing protected-snapshot rules require an explicit narrow cleanup decision
before live creation. No assumed expiry or caller-written price can waive it.

The seven-migration scheduling continuation cannot satisfy the old baseline
history observer. Select the explicit `scheduling-a2-v1` qualification profile
before preparing/collecting tasks and retain that choice in custody; no-profile
historical HTTP evidence keeps its exact legacy interpretation. The logical
migration-state proof slot then uses `observe-scheduling-state` and
`PERSISTENCE_SCHEDULING_STATE_CONFIRMED`, with complete manifest/table ownership
state, never a prefix receipt. A later acceptance observation has a distinct
controlled stage/attempt identity, not the earlier preparation receipt.

Reuse/consumer inventory: shared `60-run/release-succession/scheduling-proof.py`
and `validate-acceptance-route/script.py`; both acceptance-route declarations;
persistence accepted-release schema and Entity acceptance-record schema; core
collect-acceptance-evidence, acceptance-updates and validate-accepted-release;
Entity acceptance-route/evidence/steps/controls/state, credential-steps and
recovery-history/recovery-steps, plus the existing replacement-route parser
that passes the selected profile into credential recovery. Coordinate existing core receipt and Entity
task-route/task-steps owners with the migration implementation. Reuse the strict
shared scheduling-state reader. No new script or execution engine is proposed.

Changed recovery inputs still require real credential/recovery/restore
requalification. Retained profile, task stage/operation, manifest, qualified
image/source, predecessor and timestamps must agree. Effective access remains
a separate proof; empty-work inventory is a preactivation gate, not a blanket
rule after synthetic work. Missing runtime evidence producer remains blocked.
Extend existing shared/core/Entity acceptance, credential and actual task route
tests: unchanged historical baseline, scheduling rejects baseline/prefix/wrong
manifest/image/scope/preparation replay, stripped profile fails, recovery uses
the same selected operation. Budget focused development runs at five minutes
per affected test group; record measured elapsed time and consolidate registered
verification after source freeze. No local fixture is live acceptance.

#### Connected scheduling migration admission — resumed inventory before edits

Reuse core `run-migration/script.py`, `task-operations.py`, `proof-receipts.py`
and `task-operation-test.py`; Entity `task-route.py`, `task-steps.py` and the
existing actual-route fixture; the shared strict scheduling-state reader and
existing package custody owners. No new execution engine or script is proposed.
Core's currently capture-only `--qualified-receipt` must authenticate the current
maintenance image/source and bind the actual observer/migration definitions and
database incarnation, not merely accept receipt syntax. Its `BoundOperation`
needs an optional pre-reservation authorization callback used obligatorily by
new scheduling submissions; existing exact reservations retain original
admission and reconcile without requiring a fresh observation.

Entity selects a distinct `scheduling-migration` stage, only migration/apply with
the scheduling profile. It consumes the real retained prefix packet, completion
and preflight admission for the exact qualified current maintenance deployment.
Its preflight remains read-only. Baseline migration and acceptance formats stay
unchanged; neither partial history nor scheduling apply may satisfy baseline
acceptance. The later complete-state and effective-access observations supply
scheduler readiness, not an unqualified success log.

Required predicates/tests: missing/wrong-scope/stale/image/source/incarnation
or manifest mismatch reject before reservation; a complete prefix selects read
confirmation, never a fresh apply; a lost response reconciles the original
request without a second launch. An explicit recovery observation requires a
positively terminal failed prior apply and immutable predecessor custody. Reuse
existing observation-renewal/AttemptStore/history owners; never change proof
labels ad hoc or relabel an old observation fresh. Keep that recovery route
blocked if its exact governed selection is not yet proven. Unknown/pending
effects cannot authorize retry. Extend existing proof-policy/reader owners only
where the connected preserved-admission contract requires it; no parallel
recovery registry. Planned proof: existing core task-operation and Entity real
initial/successor route tests, bounded development runs before consolidated
registered verification. All finite errors retain their current safe controller
context; no raw task, credential, row or provider payload becomes a diagnostic.

1. **Observe an accepted migration prefix.** Add a distinct read-only
   `observe-scheduling-prefix` operation, reusing the adapter runner's exact
   ordered-ID/checksum comparison. Both targets need the shared observer,
   dispatch/configuration and source-owned minimum (core 2, Entity 1). Existing
   full-state observation must still require all seven migrations. Proposed
   closed `migration_prefix` data: schema
   `kanbien/scheduling-migration-prefix/v1`, `manifest_sha256`,
   `manifest_migration_count`, `minimum_applied_migrations`,
   `applied_migrations`, `applied_prefix_sha256`, `state`. Hashes are lowercase
   SHA-256 of the same source-owned ordered IDs/checksums. Require
   minimum <= applied <= total; state is partial exactly when applied < total;
   a complete prefix hash equals the full hash. Result code:
   `PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED`. Bind source, task, scope, database
   and observation provenance through existing task receipts. Reject absent,
   short, gapped, unknown, duplicate or changed history; use a nonwaiting lock
   and retain runner revalidation before writes. Do not read scheduler tables
   before their migrations exist. Existing owners: adapter migrations/index,
   shared administration/configuration, both target manifest/administration
   owners, shared `scheduling-database-state.py`, core administration/receipt
   readers, Entity task-control/evidence/route/steps and existing fixtures.
   Entity needs an explicit read-only route with bootstrap custody/preflight,
   not a circular completed-migration prerequisite. This connected prefix slice
   is now implemented: adapter/runtime, both composition fixtures and the real
   disposable PostgreSQL integration passed after resumption (native session
   51604, including lock/prefix assertions and engine/directory cleanup).
   No shared database changed. The later apply authorization remains in progress.
2. **Finish administration and migration declaration/receipt closure.** Both
   scope declarations still omit the three implemented scheduling administration
   operations; Entity additionally lacks their effect/route wiring. Core's CLI
   accepts them, so it must not be called fully governed/live-ready yet. Add the
   actual declared connections with qualified maintenance-image custody before
   use. Before scheduling migrations can be enabled, bind their expected profile
   and manifest into the correct acceptance proof rather than treating any
   `apply` receipt as baseline migration. Keep present scheduling-profile hard
   blocks until this connected work and fresh prefix observation are proven.
3. **Supply trusted deployment admission.** The public scheduling controller
   deliberately stops before constructing the AWS provider. Its real admission
   must bind protected-workflow artifact custody, exact images/source/config,
   fresh endpoint and existing-app queue/security-group compatibility, complete
   database/grant/work-inventory observations and an itemized <=US$25 monthly
   forecast. Self-consistency observation is not qualification. Missing/stale/
   wrong-scope facts must reject before prepare and be rechecked at execution;
   uncertain submission must observe the original operation, never resubmit.
4. **Apply the exact foundation IAM update through an owning route.** Source adds
   only `ecr:DescribeRepositories` for the existing repository. The budget-only
   foundation controller, runtime bootstrap controller and scheduler-stack
   controller cannot safely apply it. Extend a governed foundation UPDATE owner
   to preserve all parameters, admit only this nonreplacing DeliveryRole delta,
   retain immutable intent and reconcile uncertain execution. Do not issue an
   inline IAM mutation or repurpose the budget controller.
5. **Qualify, publish and prove the live chain.** Finish actual image qualification
   and the four run-proof routes/trusted runtime producer, complete integration,
   then use authorized governed main publication and disabled deployment.
   Account for six selected artifacts where needed: four Lambda images plus
   the updated core and Entity HTTP/maintenance images containing migration,
   permission and atomic-reminder programs. Old maintenance images are not proof
   of these new operations.
   Activate only after readiness/cost gates; create positively owned synthetic
   proof rows, observe automatic completion/control survival and interruption
   recovery, and retain independent accepted evidence. Current source fixtures
   do not establish any of these live outcomes.

### Exact owner map for the next prefix-observation increment

The final read-only inventory (`time_model_review`, under five minutes) confirmed
these existing owners. This is proposed work, not a new implemented operation.
Do not create a second comparison or route framework.

```text
platform/adapters/aws/persistence/postgresql/
  src/migrations.ts                       reuse validateContinuation/manifestRejection
  src/index.ts                            expose the scoped read-only comparison
  tests/contract/postgresql-persistence-adapter-runtime.test.ts
  tests/integration/postgresql-persistence-adapter-integration.test.ts

infra/04.deploy/03.product/entrypoints/
  shared/persistence/scheduling-administration.ts
  shared/persistence/configuration.ts
  shared/persistence/operation-diagnostics.ts   review/reuse existing failure handling
  kanbien-core-server-persistence-administration.main.ts
  kanbien-core-server-persistence-postgresql.ts
  kanbien-core-server-persistence-migration.main.ts
  entity-smoke/administration.ts
  entity-smoke/postgresql.ts
  entity-smoke/migrations.ts

scripts/04.deploy/shared/scheduling-database-state.py
scripts/04.deploy/lifecycle/20-build/
  entity-smoke-composition/access-control-test.mjs
  core-server-persistence-composition/configuration-test.mjs
scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/
  core-server-persistence/run-administration/script.py
  core-server-persistence/proof-receipts.py
  core-server-persistence/task-operation-test.py
  core-server-persistence/proof-receipts-smoke-test.py
  entity-smoke/task-execution/implementation/task-control.py
  entity-smoke/task-execution/implementation/task-evidence.py
  entity-smoke/task-execution/implementation/task-route.py
  entity-smoke/task-execution/implementation/task-steps.py
  entity-smoke/task-execution/tests/task-control-test.py
  entity-smoke/task-execution/tests/task-evidence-test.py
  entity-smoke/task-execution/tests/task-route-test.py

infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/
  core-server-persistence/00-declaration/declaration-contract.yml
  entity-smoke/00-declaration/declaration-contract.yml
```

Core's accepted minimum is2; Entity's is1 even though its current default
baseline manifest contains4 entries. Scheduling manifests contain7. Fresh
disposable-schema creation must remain separate from opt-in continuation.
The observer must not invoke `requireCompleteState()` or query tables/columns
that a permitted partial prefix has not yet created. The writer still validates
the exact ordered history under its own lock before applying any suffix.

**Route trap:** Entity `task-steps.py` currently selects acceptance prerequisites
for delivery-bound operations before ordinary stage handling. Those prerequisites
require completed deployment/application proofs. Its initial-recovery and
ordinary feature routes also require restart/application-read or activation
state. None is a valid prerequisite for this earlier metadata inspection. Add
one explicit narrow observation branch that retains custody, binding, preflight
and approval checks; do not weaken the other routes. Actual controlled-route
proof must accept a valid partial journal without complete scheduling tables,
application rows or acceptance receipts, while rejecting that same observation
as authority for migration or activation. Keep the core `run-migration/script.py`
and Entity scheduling migration hardblocks until the later connected admission
work is implemented and proven.

Current growth/cost checkpoint: 14 new script-source files (helpers and tests
included), zero removed or moved; 12 new catalog identities (six local units,
four image-qualification and two deployment observations). They run only through
affected/explicit stage selection; no automatic cloud task or new recurring
agent review was installed. The existing admission-review requirement was used.
Managed payload/image/provider checks executed in 4.732s combined; corrected
acceptance contracts in 12.502s. Full affected integration, image qualification
and end-to-end delivery time remain unmeasured/incomplete. Earlier broad runs
exceeded the ten-minute budget; do not hide that behind focused check timings.

This table owns the current summary. Milestone checklists own acceptance detail;
the progress log owns chronology. The active session owns branch/worktree,
authority references, commits and pending operation identifiers. Link evidence
instead of copying whole reports into multiple records.

| ID | Outcome | Depends on | Status | Owner | Evidence and next action |
| --- | --- | --- | --- | --- | --- |
| M0 | Detailed design, cost budgets, authority and consumer inventory | A2 and overnight limits approved | In progress | Root | Main integration, shared-network preservation, disabled-first deployment and narrow proof-resource cleanup authorized; actual cost admission remains unfinished |
| M1 | Reusable bounded due dispatcher and outbox delivery | Agreed M0 design for affected slice | In progress | Root | Bounds, mapping, references and invalid-row isolation have focused local proof; complete integration remains blocked |
| M2 | On-demand SQS/Lambda durable execution | M0; shared M1 contracts | In progress | scheduler_inventory | Direct worker, persisted retry and native batch have registered local proof; finished managed-runtime image and AWS proof remain |
| M3 | Safe Entity Smoke mutation and purge | M0; shared transaction contracts | In progress | time_model_review | Atomic delete/reminder, targeted purge and full-snapshot save guards implemented; focused app proof passed |
| M4 | Complete local chain on real PostgreSQL | M1–M3 | In progress | time_model_review | Corrected real-engine connected and composition/access fixtures passed; native proof routes now implemented; final source-matched affected integration remains pending |
| M5 | Explicit baseline and feature function packages | M4 | In progress | plan_review / scheduler_inventory | Source admission approved; registered payload/image-contract fixtures pass; actual finished images remain unqualified because local Docker is unavailable |
| M6 | Reusable target realization and activation controls | M0; final M5 shape | In progress | plan_review / scheduler_inventory | Controller, disabled connection proof and native capture routes implemented; final enablement, proof-resource cost/cleanup and exact existing S3-route observation are being completed; no live deployment |
| M7 | AWS baseline and feature acceptance | M5–M6; actual authority | In progress | plan_review / Root | Connected evidence assembler/readers and local complete-case fixtures implemented; independent review corrections have focused proof; actual images, AWS execution, recipient-confirmed alert and measured cost acceptance remain outstanding |
| M8 | Calendar/timezone/DST scheduling | M7; separate design | Deferred | Unassigned | No recurrence capability claimed |

An assigned executor may parallelize independent reviewed scopes; shared contract
changes need a single owner. Freeze contributors' verification inputs before
final integration, as required by the existing completion standard.

## M0 Confirm design and scope

**Goal:** remove architectural and authority ambiguity before implementation.

- [ ] Preserve D1 and the operating-cost objective; resolve remaining D2–D8
  details, especially per-pass bounds, overlap/backlog policy, cancellation,
  Lambda suitability and numeric cost/lateness/recovery budgets,
  retry authority, poison-record disposition and work/deadline bounds.
- [ ] Complete the operating-cost scenario worksheet above with actual region,
  shared infrastructure, network requirements and forecast; record assumptions
  and the decision if a required fixed-cost resource changes the comparison.
- [x] Record A2 local build intent and the latest design-first instruction.
  Obtain agreement for the exact first code increment; do not treat build intent
  as an autonomous-increment waiver or package/cloud authority.
- [ ] Read the owning workflows and required ADR/configuration references.
- [x] Keep the fixed trigger, queues, roles and functions infrastructure-owned
  under ADR 0027. Reminder create/read/state changes remain database operations;
  no runtime AWS schedule-resource CRUD exception is needed for A2.
- [ ] Record affected producers, consumers, public contracts, adapters, config,
  diagnostics, schemas, programs, images, permissions and proving checks here.
- [ ] Reconcile stale scheduler status in the existing runtime plan without
  deleting historical proof or treating old deferrals as implementation.
- [x] Record ADR disposition through the existing process.
- [ ] Assign coherent milestone owners and verification budgets.

**Exit evidence:** dated decision entries with authority reference, resolved
contracts and bounded consumer/proof inventory. No runtime change is required
to complete this design milestone.

**Deliberately unchanged:** existing schedules, accepted releases, source
behaviour, infrastructure and calendar scheduling.

### First bounded local increment — complete, locally verified

**2026-11-26 authority:** the user's latest `yes` approves this concrete slice
after the design walkthrough. It does not authorize the remaining milestones,
cloud changes or an autonomous-increment waiver.

**Bounded consumer and diagnostic inventory (before implementation):**

- New provider-neutral `createPlatformScheduleDispatcher` composes the existing
  `PlatformScheduleDelivery` and `PlatformOutboxRelay` ports. The first actual
  consumer is the connected persistence runtime proof; no deployed entrypoint
  consumes it yet. The public index remains re-export-only.
- Construction captures `maximumRelayAttempts` once, accepts integers 1–100,
  and reuses Core's finite-number config reader. A new closed persistence-owned
  configuration record identifies missing/type/finite/integer/range failures;
  no submitted setting value is reported.
- Each invocation checks an optional synchronous `shouldContinue` callback
  before the existing due pass and each relay attempt. Counters are invocation
  local. The due pass retains its existing 100-row bound unchanged; no hard
  deadline or interruption of an in-flight dependency is claimed.
- Due-pass failure stops this invocation before relay. Existing backlog is
  attempted after a successful due pass even when it found zero new reminders.
  Due-store poison-record isolation and independent draining remain M1 debt.
- Returned failures and thrown values retain their exact identity. A separate
  closed boundary record observes continuation/due/relay failure and only the
  effects actually established. Existing diagnostic capture/selection/delivery
  helpers preserve selected source evidence and isolate failing reporters.
- Ordinary stop, attempt limit, idle, contention, send failure and publication
  marker failure remain distinct outcomes. Only `published` increments the
  published count. Idle is an observation, not proof of an empty global backlog.
- Update existing diagnostic definitions/aggregate, generated persistence JSON,
  source-matched review ledger, public export/type proof and module README.
  Existing stores, relay, clocks, IDs, registry and consumers need no changes.
- Prove send-failure then retry after lease expiry with no newly due reminder,
  bounded attempts/stopping, exact failure identities, diagnostic disclosure and
  reporter-failure isolation. The connected controlled-store fixture is not
  proof of real PostgreSQL transaction atomicity or AWS delivery.

**Verification budget:** 10 minutes for focused registered runtime/catalogue
checks after source review; inspect declared impact before selecting any wider
checks. Reuse unchanged evidence and report uncovered integration obligations.

**Goal:** one local call checks due reminders and then attempts existing outbox
delivery. It proves the connection without a timer, Lambda or live queue.

**Implemented file scope:** new `platform/persistence/src/schedule-dispatch.ts`,
public `src/index.ts`, new integration and type-level schedule-dispatch tests,
existing `src/diagnostics.ts`, its generated `contracts/diagnostics.v1.json`,
the persistence README and existing diagnostic review ledger.
`relay.ts` and `schedule-delivery.ts` remain unchanged.

**Smallest proposed change:** compose the existing due pass and relay with an
explicit small work bound and cooperative stop checks. A wrapper cannot enforce
a hard deadline inside an unbounded dependency; document that boundary and the
required dependency timeouts instead of claiming it can. Keep errors and result dispositions visible;
relay pending work even when no reminder becomes due. Inventory the existing
consumer/test signatures before choosing the exact API. Do not silently grow
this into the entire M1 acceptance surface.

**Proving check:** a focused controlled-clock test establishes that a due
reminder can enter the outbox and be sent, and that a later call drains pending
outbox work when there are no newly due reminders. Use connected controlled
stores; unrelated private in-memory maps do not establish complete-chain proof.

**Not changing yet:** Entity Smoke transactions/purge, schemas, cancellation,
the Lambda worker, packaging, clocks/IDs, actual SQS, fixed triggers or AWS.
The design was presented and this bounded implementation is approved.

## M1 Complete reusable bounded dispatch

### Overnight implementation inventory — 2026-11-26

The approved goal covers the following connected increments. This inventory
supersedes the earlier first-slice-only execution boundary, not its historical
verification claims. Root owns this plan, session, public persistence scheduling
contracts and the shared diagnostic review ledger. Contributors record exact
consumer and diagnostic additions here before expanding their assigned scope.

- Dispatch/schedule owner: `platform/persistence/src/{scheduling,schedule-delivery,schedule-dispatch}.ts`,
  their public exports/tests and PostgreSQL scheduling/migration owners. Add
  per-reminder cooperative limits and selected registered-job resolution; reuse
  the existing outbox and leases. Invocation stopping is not dependency cancellation.
  A typed optional Core `RecordReference` subject on the reminder names one
  entity; no arbitrary arguments or change to queue `{outboxEntryId}` is needed.
  Add immutable migrations, retain legacy reads and fail closed for subjectless
  cleanup. This supersedes the earlier assumption that cleanup needs no target.
- Worker owner: `platform/workers/src/{worker,types}.ts`, owned configuration and
  diagnostics/tests; `platform/adapters/aws/queue/sqs/src/` batch translation;
  processing types/store plus PostgreSQL and DynamoDB implementations. Reuse one
  handler/claim/completion pipeline for polling and direct delivery. Add durable
  retry-not-before state rather than a competing local retry authority. Match
  envelope identity/type/version/tenant against the selected durable outbox.
  Only durable succeeded completion permits acknowledgement; lease contention,
  retry delay, terminal failure and uncertain completion retain the message.
  Managed SQS redrive owns terminal transfer; never manually poll/delete Lambda
  records. Counterexamples cover mixed batches, identity mismatch, lease loss,
  retry restart, completion uncertainty and native message-ID duplication.
- Entity owner: existing `apps/entity-smoke/features/test-entity/` deletion,
  reminder, purge and repository files; app public mount and Entity Smoke
  PostgreSQL composition. Use existing `withPostgreSqlTransaction` with one
  acquired client for entity mutation and reminder. Remove the scheduled broad
  sweep: resolve reminder subject, require the matching deletion generation,
  assess Core eligibility and condition the final DELETE on the same facts.
  No proof-only IDs or ambient allowlists. Prove rollback, stale lifecycle,
  untouched unrelated rows and failure propagation. Preserve HTTP role's denied
  DELETE; later worker identity permissions are separately declared and proved.
- Deployment owner: existing runnable-program/image/publication/custody and AWS
  capability controls, plus thin bindings for the two approved scopes. Inventory
  exact additions before edits; add reusable Lambda support and governed additive
  activation instead of weakening ECS image-only update rules. Local construction
  is authorized; publication and cloud activation remain gated by prerequisites.
- Diagnostic predicates belong at their existing operation boundaries: checked
  config rejection; due selection/handover/stop; durable identity mismatch;
  claim/retry/completion uncertainty; native batch translation; transaction
  rollback/commit uncertainty; conditional purge and provider control evidence.
  Preserve source reports and failure identity, avoid sensitive row/payload data,
  and add exact counterexamples to existing owners/catalogues. Root updates the
  shared review ledger only after source and tests stabilize.

Verification budget: focused affected checks during each connected increment;
allow ten minutes for the final selected local integration batch, investigate
overruns rather than rerun unchanged inputs. Reserve at least thirty minutes
before the eight-hour limit for live-resource reconciliation and handoff. Real
PostgreSQL, finished images and live acceptance remain separate mandatory gates.
No existing due record is eligible for live processing merely because it exists:
inventory pre-existing schedule/outbox identities before enabling the new path,
and stop activation if their preservation cannot be demonstrated.

Dispatch mapping/blocked-record decision: root will add
`platform/persistence/src/schedule-jobs.ts` to translate selected public job
registrations into outbox metadata; preserve the registered message type (not
the job name), reuse the schedule's existing UUID as its one-outbox identity,
and retain Core constructors. Missing selected jobs return an explicit unavailable
mapping, never an invented handler. Extend the existing schedule store with a
durable `blocked-job-unavailable` state and bounded block/release operations;
handover must serialize with blocking and cannot deliver a blocked reminder.
Only an explicit reviewed repair may release that state after job wiring is
fixed. General cancellation/editing remains deferred (D7); the feature's actual
mutation guard handles already queued obsolete reminders. This adds an immutable
schedule-state migration and source/real-engine counterexamples for unknown jobs,
known later jobs, repeated repair, and block/handover races. Newly observed
mapping rejection has its own safe diagnostic; existing v1 field vocabularies
remain unchanged. The explicit PostgreSQL invalid-row path below now has
controlled transaction tests, including a full bounded page; actual-engine
verification is still required. Blocking an unknown valid job alone does not
establish arbitrary corrupt-row recovery.

Shared consumer decision: add `platform/persistence/src/schedule-reference.ts`
and its existing-discovery runtime tests/export. Both proof jobs will resolve
the queue's outbox reference through the same scoped durable stores, checking
envelope identity/type/version/tenant, schedule identity/job/handoff and due
time before invoking application work. Dependency throws remain unchanged;
local rejection uses a value-free `persistence.schedule-delivery-reference-rejected`
definition with finite field/reason/effect detail. Entity-specific subject and
retention policy stay in the feature. This replaces, rather than duplicates,
the common validation currently inside its job transport.

Baseline consumer: add the placement-validated
`infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-scheduling.app.ts`.
Its public mount registers a harmless persistence proof job and reuses the
existing acceptance-record capability/table. The reminder UUID and a digest of
its immutable identity/job/due time give repeat delivery the same harmless
write. Only created/already-existing matching records count as success;
conflict, unavailable and uncertain outcomes retain the delivery. Extend the
existing baseline diagnostic catalogue and composition test owner; no parallel
proof database, direct private feature imports or ungoverned live route.

Corrupt-record recovery decision: the due runner explicitly opts into bounded
invalid-row blocking on `listDue`; ordinary reads retain fail-closed behavior.
The PostgreSQL adapter locks at most the requested due rows, preserves every
invalid row's original fields, changes only its state to `blocked-invalid-row`,
and commits before reporting that isolation succeeded. Healthy selected rows
are returned normally; subsequent passes can reach later rows. No invalid row
is treated as delivered. Resume first locks and revalidates the repaired row;
an invalid blocked row cannot be made waiting by a failed resume. Extend the
new, not-yet-applied control migration and public state union. Source predicates
remain in existing stored-row diagnostics; a new value-free isolation diagnostic
reports only confirmed blocking. Prove bad-oldest/healthy-next/backlog progress,
bounded all-bad scans, rollback and unrepaired resume. This is not automatic
repair of user data, nor permission to alter live pre-existing rows for proof.

Documentation/review inventory: update the existing `platform/persistence/README.md`,
`platform/workers/README.md` and `platform/adapters/aws/queue/sqs/README.md` with the
new scheduling/reference/retry exports, direct durable execution, native batch
settlement and their test/live-proof boundaries. Preserve unrelated guides and
correct obsolete future-adapter and whole-pass stopping claims. The existing
PostgreSQL telemetry type deliberately excludes schedule-specific operations;
add block/resume to that exclusion rather than widening historical command
diagnostic definitions. No runtime telemetry emission changes are required.

Migration consumer audit: the existing baseline migration/administration route
owns an exact two-entry history and must retain its empty-only replay protection.
Add `kanbienCoreServerSchedulingMigrationManifest` to the existing baseline
PostgreSQL composition owner: it preserves those two checksums and appends
schedule/handoff/subject/retry/control migrations. It is input for the new
bounded additive-prefix route, not silently substituted into the old route.
The retiring `kanbien-platform-postgresql-migration.main.ts` is a concrete
consumer of the changed processing adapter: append only its retry-column
migration and derive success count from that manifest, preserving the original
two migration bodies. No legacy-target deployment is authorized by this change.

Consolidated review corrections (2026-11-27, root with independent agent review):
the invalid-row transaction now uses one bounded bulk UPDATE, with exact
returned-ID/count matching and rollback on mismatch, rather than one query per
bad row. The controlled 100-row case asserts four round trips including commit
or rollback. Scheduled-only statement/client query timeouts are 3s/4s; worker
and due phases reserve 45s, relay 35s in a 60s function. The modeled slow paths
include reconnect/reconciliation and queue time, not merely the happy path;
these bounds are not a hard AWS latency guarantee. The real composition fixture
exposed a new baseline diagnostic outside its catalogue namespace; corrected it
to `kanbien-core-server.acceptance.scheduling-proof-not-completed` before final
catalogue generation and registration proof. Existing legacy migration fixtures
now assert the appended retry migration as well as the new count.

Direct-store hardening remains a separate, pre-existing boundary: callers that
forge an `ISODateTime` can supply malformed `asOf` to `handoverDue`; its existing
date comparison is not an independent validator. The actual due runner first
uses Core's date conversion, and the added invalid-Date counterexample asserts
no selection or handover occurs. Do not claim arbitrary untyped store callers
are validated by this proof. The real-engine invalid-row fixture currently uses
one bad row; full-page cardinality/rollback proof is controlled-driver evidence.

**Goal:** find due reminders, hand them atomically to the existing outbox and
relay pending work in one bounded provider-neutral operation.

**Existing owners:** `platform/persistence/src/{scheduling,schedule-delivery,relay}.ts`,
`platform/contracts/src/jobs.ts`, `platform/runtime/src/registry.ts` and the
PostgreSQL scheduling/outbox implementations. Reuse existing IDs, clocks, error
contracts, claims and diagnostics. Do not create another reminder store.

**Implemented composition file:** `platform/persistence/src/schedule-dispatch.ts`,
with its public export and focused tests. It connects the existing due pass and
relay with attempt limits and stopping between calls. The remaining M1 work must
extend the existing due pass only where needed for safe per-reminder bounds.
No runtime Scheduler adapter or provider registration state is added.

### Due selection and delivery

- [ ] Resolve each reminder's job through the selected runtime's public mounts;
  use its registered message type rather than equating job name and message type.
- [x] Reuse `listDue`, the callable due pass and `handoverDue`. Keep the stored
  millisecond due instant, including the current offset-to-UTC normalization.
- [ ] Recheck due time and permitted schedule state inside handover. Preserve
  row-lock/transaction semantics so concurrent passes create one durable outbox
  record and retries reuse its recorded identity.
- [x] Run the existing relay against pending outbox work even when there are no
  new due reminders. Publish only after the job queue accepts the envelope.
- [ ] Allocate bounded progress to both due selection and relay. An endless
  stream of due reminders must not consume every pass before old outbox work
  is attempted. Preserve completed handovers if a later item fails.
- [ ] Keep errors, partial progress, contention, send failure and marker failure
  visible; a fulfilled call or unchanged count is not proof of successful dispatch.

### Bounds and overlapping invocations

- [ ] Agree explicit due-item, relay-attempt and elapsed-time limits. Check the
  remaining budget between operations, not only between whole 100-item batches.
  Reuse existing deadline/cancellation facilities rather than a new timing engine.
- [ ] Give database and queue calls their own enforced timeout/cancellation
  contracts. A wrapper checking time before a call cannot stop an unbounded
  dependency; a timed-out wait does not prove an underlying write was cancelled.
- [ ] Stop starting work before the Lambda deadline with cleanup margin. On an
  uncertain write/send, preserve durable identity and let claims/retry reconcile
  it; do not report rollback or success without evidence.
- [ ] Treat minute ticks, delayed triggers, retries and concurrent invocations as
  potentially overlapping. Do not rely on invocation order or a single Lambda
  instance; existing database transactions and outbox leases own exclusion.
- [ ] Prove progress beyond the existing 100-item lookup boundary across bounded
  passes. If arrival rate exceeds safe drain capacity, alert on oldest work age
  and backlog; do not drop work or make a completion-deadline claim.
- [ ] A missed tick is repaired by scanning all eligible overdue work next time,
  not by requiring equality with a particular minute. Use injected clocks and
  a stable pass cutoff; host local timezone must not decide eligibility.

### Cancellation and blocked records

- [ ] Resolve D7 before implementing cancellation. If cancellation ships, persist
  it and serialize it against handover: cancellation committed before handover
  prevents delivery. Document the exact boundary and prove the race.
- [ ] Do not claim cancellation can retract an already published queue message.
  Stronger cancellation after handover requires a separate worker/feature guard;
  Entity Smoke still checks lifecycle and retention at the actual mutation.
- [ ] Unknown jobs or malformed records must not execute, disappear or starve
  all later work. Extend the existing store with an explicitly approved blocked/
  terminal disposition and governed repair route where necessary.
- [ ] Preserve originating diagnostic causes and distinguish candidate lookup,
  handover, relay claim, send and publication-marker failures.
- [ ] Keep general schedule editing, arbitrary job arguments and tenant-specific
  scheduling outside this first release.

**Acceptance checks:**

- [ ] Before-due, exactly-due and overdue boundaries; equivalent Z/offset inputs.
- [ ] Registered job mapping rejects unknown jobs and respects the selected scope.
- [ ] Repeated/concurrent passes create one durable handover.
- [ ] More than 100 due reminders and an existing outbox backlog both progress.
- [x] No newly due reminders still permits relay of pending work.
- [ ] Failure after handover, queue-send success with marker failure, restart and
  duplicate delivery recover without losing committed work or false success.
- [ ] Count/deadline stops, non-returning or late-returning dependencies and
  expired leases retain uncertain work under its original identity.
- [ ] Poison records cannot indefinitely starve healthy reminders or relay work.
- [ ] Agreed cancellation races and already-queued limitations are demonstrated.
- [ ] Missed/overlapping ticks and capacity limits match the stated recovery policy.

**Exit:** focused source/contract proof; real database concurrency and rollback
remain M4, finished Lambda programs M5 and live trigger behavior M7.

**Deliberately unchanged:** live resources, calendar recurrence, general editing
and application retention policy.

## M2 Connect SQS to on-demand durable execution

**Goal:** invoke existing worker mechanics for bounded Lambda batches, with
reliable retry/settlement and no permanently running worker process.

**Existing owners:** `platform/workers/src/{main,worker,types,queue}.ts`,
`platform/persistence/src/processing.ts`, PostgreSQL processing and
`platform/adapters/aws/queue/sqs/src/worker.ts`.

- [ ] Use/extend a provider-neutral transport boundary; AWS SDK calls stay in
  the adapter and target composition, not generic workers.
- [ ] Expose bounded record execution using the existing shell/processing path.
  Lambda's managed SQS mapping owns polling and deletion. Translate incoming
  records and partial batch failures at the provider boundary; do not run the
  manual SQS receive loop or treat in-memory re-enqueue as durable execution.
- [ ] Keep dispatch separate from job execution. Successful job records must
  not be retried solely because another batch record failed; unknown or
  uncertain outcomes must not be omitted from the failed-record response.
- [ ] Select one durable retry authority and preserve attempts across restarts.
  SQS receive count includes contention and is not automatically handler attempts.
- [ ] Make actual retry delays, visibility and database lease durations coherent
  with function timeout and bounded job runtime. Specify deadline/termination
  handling; reject unsupported long jobs rather than silently truncating them.
- [ ] Bound purge batches and function concurrency against DB connection capacity.
  If a bounded job needs continuation, record a durable next delivery before
  completing it; no unawaited work after a function returns and no lost remainder.
- [ ] Match queue identity/type/version to the durable record and selected job.
- [ ] Define terminal failure and failed-message queue delivery, including
  crash/uncertainty between recording failure, sending and acknowledgement.
- [ ] Stop taking new work during shutdown and leave unfinished work recoverable.
  Function freeze/termination cannot be assumed to run a graceful shutdown hook.

| Observed outcome | Settlement contract |
| --- | --- |
| Durable completion succeeded | May acknowledge |
| Duplicate already durably completed | May acknowledge without another business effect |
| Active claim held by another worker | Defer; do not count as successful execution |
| Retryable handler failure | Persist retry state and arrange delayed redelivery |
| Completion write failed or uncertain | Do not acknowledge as success |
| Invalid message or terminal failure | Use declared durable diagnostic/failure path; no silent loss or endless unowned retry |

**Acceptance checks:**

- [ ] Crash before execution and after business effect but before completion.
- [ ] Completion succeeds but acknowledgement fails; redelivery is safe.
- [ ] Active/expired claims, contention, lease loss and duplicate deliveries.
- [ ] Retry delays really apply; attempts survive restart.
- [ ] Terminal failure is retained and its queue disposition is recoverable.
- [ ] Foreign-scope or mismatched envelope cannot execute.
- [ ] Shutdown is bounded and does not mark unfinished work complete.
- [ ] Mixed-success batches, fresh/warm invocations, deadline termination,
  duplicate native SQS message IDs and connection/concurrency limits are proved.
  Preserve the durable envelope identity, not the provider-assigned message ID.

**Exit:** reusable transport-driven execution proof. Do not claim exactly-once
effects: a crash after the handler effect can run the handler again.

**Deliberately unchanged:** app business rules, AWS provisioning and recurrence.

## M3 Make Entity Smoke retention safe

**Goal:** prevent lost reminders, false success and deletion based on stale state.

**Existing files:**

```text
apps/entity-smoke/src/persistence/app.mount.ts
apps/entity-smoke/features/test-entity/
  domain/retention.ts
  domain/services/dependencies.ts
  domain/services/delete-test-entity.ts
  domain/services/remember-expired-purge.ts
  domain/services/purge-expired-test-entities.ts
  persistence/repository.ts
  persistence/relational/contracts.ts
  persistence/relational/repository.ts
```

### Atomic entity change and reminder

- [ ] Extend existing transaction ownership so entity change and reminder share
  one physical database transaction and connection. No AWS call participates.
- [ ] Check current lifecycle preconditions and actual affected rows before
  committing the reminder.
- [ ] Roll back both writes on failure; reconcile unknown commit outcomes rather
  than blindly generating a second operation.
- [ ] Prove stale/missing entity, failure before/after each write and concurrent
  lifecycle changes.
- [ ] Add immutable migrations through the existing runner where needed; do not
  rewrite applied migrations/checksums or run migrations on server startup.

The current atomic writer stages participant writes and lineage/outbox facts;
it is not already a drop-in entity-plus-reminder transaction. Review its actual
callers and extend the owned capability deliberately. Two separate pool calls
inside an outer function are not atomic.

### Conditional purge and honest job failure

- [ ] Carry the assessed deletion timestamp or equivalent lifecycle version to
  the repository mutation.
- [ ] Recheck archived/deleted state and assessed deletion identity/time at the
  actual delete; reject a stale candidate after restore or re-deletion.
- [ ] Keep the eligibility cutoff feature-owned; do not place the five-minute
  rule in the generic PostgreSQL adapter.
- [ ] Mirror semantics in the in-memory repository and prove the real SQL race.
- [ ] Translate unsuccessful service `Result` at the app mount into the existing
  handler-failure contract; prove it through worker execution.
- [ ] Repeated purge after an uncertain completion is harmless.

Preserve `entity-smoke.test-entity.purge-expired`, existing IDs/clocks and the
strict elapsed rule: eligible only after 300000ms; reminder due at +300001ms.
No general tenant retention engine, legal-hold capability or arbitrary job-input
protocol is added. Missing legal-hold support limits this to the synthetic proof.

**Exit:** focused feature and transaction contract checks, with real-engine
acceptance completed in M4 before live activation.

## M4 Prove the connected chain on PostgreSQL

**Goal:** prove actual transactions and concurrency with a controlled clock.

2026-11-27 exploratory real-engine proof passed through the existing
`core-server-persistence-composition/postgresql-integration-check.sh` owner.
Its existing native fallback used installed PostgreSQL18.6; no new database
runner or installation was needed. The first run failed in the retained
read-only reconciliation fixture: `Pool.query()` discards an errored connection,
so the intentionally rejected write lost the transaction and savepoint.
The fixture now retains one checked-out client, preserves the expected rejection
and all privilege assertions, and verifies `transaction_read_only` remains on
after savepoint recovery. The rerun passed in approximately30s, including
schedule concurrency/invalid-row handling, Entity atomicity/guarded retention
and baseline durable completion. Engine and directory cleanup both passed.
This is real database evidence, not AWS/SQS or finished-image acceptance;
final prepared registered evidence remains separate. Fixture SHA-256:
`4c6dac4474df3d32be97c66be2a2e83c6bda598e9ae0e57a87275bd4510dda98`.

The connected fixture was then extended through the public Entity Smoke app,
production SQS encoding/batch/visibility adapters and real PostgreSQL stores.
Controlled transport captures sends; it does not claim live SQS delivery.
The existing owner passed after compilation in terminal session `31123`,
including engine and directory cleanup. The fixture now proves strict due-time
handover, reference-only transport, targeted cleanup, harmless duplicate and
restored deliveries, a real rejected DELETE, persisted retry time across worker
reconstruction, no early claim, successful retry and unchanged control rows.
The preceding run `51649` failed because its test incorrectly expected an extra
visibility update for an early retry. Source comparison with production fixed
that expectation: a busy durable claim stays unacknowledged without another
visibility update. The exact busy code, unchanged stored retry state and entity
are now asserted. No runtime behavior was changed to satisfy the fixture.
Root reviewed the complete connection and production result mapping;
`plan_review` separately reviewed its semantic boundaries. Final fixture hash:
`12c5be1790d535469229f89011962f1ece1fa1a337f0406061a495b5045c1959`.
The added existing SQS workspace devDependency and normal offline lock update
took 0.498 seconds without external dependency upgrades. All contributors have
frozen their inputs for final preparation and registered verification.
This exploratory run does not replace that final proof, finished-image proof
or target permissions and automatic AWS acceptance.

Consolidated acceptance review reopened only this existing integration fixture
for four missing real-engine assertions: schedule transition failure after the
outbox insert must roll both changes back; failed durable completion after a
successful Entity deletion must remain unacknowledged and recover after lease
expiry; equal identities in two disposable schemas must remain isolated; and
two actual due passes must converge on one outbox handover. Existing controlled
worker tests and concurrent store calls were useful but did not establish these
exact connected claims. `time_model_review` owns this bounded fixture change,
with `plan_review` reviewing its acceptance sensitivity. Reuse public stores,
worker and due-pass factories plus finally-cleaned SQL faults inside exclusively
owned disposable schemas. Production code, package declarations and runtime
diagnostic definitions remain unchanged. Fixed phase labels retain safe failure
attribution. The existing PostgreSQL integration owner is the proving check;
budget approximately ten minutes for correction before its bounded native run.
Prepared review and affected verification reopen after this source change.

All four assertions now pass through the existing native owner, terminal
session `87836`: 28.80 seconds including compilation, engine startup and
cleanup; native assertions remain within the runner's existing 20-second cap.
The handover trigger first observes its inserted outbox row, then raises 40001;
both records roll back and a clean retry creates exactly one delivery. Two
public due passes converge on one handover. Identical reminder/outbox IDs in
two schemas retain independent due states, publication and processing claims.
An actual purge followed by a failed completion UPDATE retains the original
claim and failed native item; replay at lease expiry completes as a missing-row
no-op. Only the existing fixture changed; root reviewed all four assertions and
their absence-guarded cleanup. Final fixture SHA-256:
`4d722c033bb8ef330cfa0867e66f9be2875ea8ece9b1bd7552ad5e76bba80bb0`.
The preceding fourteen-item acceptance review took 263 seconds. Independent
four-delta review by `plan_review` passed against that exact hash in approximately
20 seconds, with no remaining concrete local M4 gap. Final prepared affected
verification follows; deployed permissions, images and cloud proof remain open.

Extend existing owners rather than build a parallel qualification harness:

```text
platform/persistence/tests/
platform/adapters/aws/persistence/postgresql/tests/
platform/workers/tests/
apps/entity-smoke/tests/test-entity/integration/
scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/
scripts/04.deploy/lifecycle/20-build/capabilities/local-qualification/entity-smoke-proof/
```

The PostgreSQL schedule contract fixture currently mocks statements. The
in-memory reminder store has a private outbox map; combining it with an unrelated
outbox store is not complete-chain proof. Use the existing disposable real
PostgreSQL qualification route for shared persisted state and rollback.

- [ ] Create, archive and logically delete a synthetic entity; confirm entity
  and reminder commit together.
- [ ] Before eligibility and at exactly +300000ms no physical deletion occurs.
- [ ] At +300001ms a controlled due pass, relay and worker can finish cleanup.
  This local eligibility boundary is not a promise of millisecond execution from
  a minute wakeup.
- [ ] Restart components between stages; persisted work remains recoverable.
- [ ] Two concurrent due passes produce one outbox handover.
- [ ] Failure after outbox insert rolls back schedule state and insert.
- [ ] Exercise each atomic delete/reminder failure boundary.
- [ ] Restore/re-delete between candidate selection and purge preserves the
  new retention window.
- [ ] Active, unarchived, restored and not-yet-due records remain untouched.
- [ ] Duplicate execution, failed completion and failed acknowledgement recover.
- [ ] A failed cleanup never reports successful job completion.
- [ ] Prove bounded backlog progress, permissions and schema/queue isolation.
- [ ] Prove missed/overlapping ticks, count/deadline stops, agreed cancellation,
  poison-record disposition and recovery of pending outbox without newly due work.
- [ ] Exercise M2's production shared batch handler/adapter locally against real
  PostgreSQL and controlled provider/transport doubles, including partial failures.
  Target composition entrypoints and finished runtime invocation are M5 proof;
  do not make this milestone depend on artifacts first introduced in M5.

Record transport doubles as controlled transport proof, not live SQS evidence.
Use injected time instead of real five-minute sleeps in ordinary tests.

**Exit:** complete local chain and real database acceptance evidence, including
failure cases. Finished-image and AWS proof remain separate.

## M5 Package explicit baseline and feature functions

**Goal:** package shared mechanics as Lambda-compatible artifacts with independent
app composition, explicit handlers and least-privilege identities.

### Lambda packaging admission and current boundaries

#### Resumed bounded admissions — 2026-11-27 04:46Z

The explicit user approval above covers the following new source files, including
more than50code lines, and the new `40-package/build-managed-handler-image/`
capability folder. Existing `managed-handler.mjs` and `managed-handler-test.mjs`
admission records below remain their pre-creation inventory. Root owns the
shared plan/catalog/review ledger; the packaging contributor owns these files.

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/script.sh
Role: operation
Owner and capability: 04.deploy / 40-package / build-managed-handler-image
Purpose: build one checked declared managed program using existing compiler, payload and candidate-image helpers
Direct consumers: protected-main scheduler publisher; manual package qualification
Named risk: wrong source, handler or base is packaged
Proof lane: package/deploy; focused local argument/selection regression
Execution boundary and actual child effects: Docker build, dependency reads, local writes and network; no AWS deployment
Relevant inputs and evidence invalidation: selected program/source, lockfile, Docker inputs, payload/compiler/build helpers
Expected cost and measurement: estimated2–5minutes per selected image; measure actual build and image bytes
Retained manual/deferred route: finished-image qualification and publication remain separate mandatory stages
Existing capability considered: build-candidate-image/operations.sh, workspace-build, prepare-runtime-payload and prepare-runtime-dependencies
Reuse decision: new bounded operation composing existing mechanics
Why a script is necessary: current build wrappers select HTTP/process candidates, not declared managed handlers
```

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py
Role: operation
Owner and capability: existing approved managed-handler image capability above
Purpose: invoke the actual packaged AWS runtime client/handler against a local Runtime API fixture
Direct consumers: scheduler publisher and manual finished-image qualification
Named risk: package has wrong bootstrap/export, unsafe initialization/errors, deadline or batch behavior
Proof lane: package/deploy
Execution boundary and actual child effects: local Docker/loopback HTTP, disposable files/processes; no provider or shared database access
Relevant inputs and evidence invalidation: exact image identity, handler declaration, qualifier, Runtime API fixture and selected environment
Expected cost and measurement: estimated under30seconds per image for invocations, excluding build/startup; measure real result
Retained manual/deferred route: actual database/SQS effects and network/grant proof remain live acceptance
Existing capability considered: current finished HTTP-image checks and package-custody qualification.py
Reuse decision: new managed-runtime qualification at the existing package proof boundary
Why a script is necessary: HTTP startup or direct function imports cannot prove official runtime-client invocation
```

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/runtime-api-fixture.mjs
Role: fixture
Owner and capability: managed-handler image qualification
Purpose: supply native invocation events/deadlines to the official runtime client and observe its responses
Direct consumers: qualification.py only
Named risk: wrong initialization, warm invocation, deadline, batch or private-error behavior survives finished-image checks
Proof lane: package/deploy
Execution boundary and actual child effects: isolated local process and loopback HTTP in read-only/network-none container with owned tmpfs
Relevant inputs and evidence invalidation: fixture, image, selected declaration and synthetic configuration
Expected cost and measurement: under30seconds per selected image; bounded waits and exact cleanup
Retained manual/deferred route: source/real-engine tests and later AWS behavior remain separate
Existing capability considered: existing container fixtures and source composition runner
Reuse decision: focused runtime protocol fixture; keep actual handler/runtime-client unchanged
Why a script is necessary: native deadlines and warm invocations cannot be asserted by the existing HTTP process fixtures
```

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification-test.py
Role: test
Owner and capability: managed-handler image qualification/publication selection
Purpose: prove exact program/image selection, bounded protocol and fail-closed handling through controlled command results
Direct consumers: owning local regression and package route
Named risk: wrong handler/candidate, failed proof or ambiguous provider state is treated as qualified publication
Proof lane: local change; finished-image proof remains separate
Execution boundary and actual child effects: synthetic command/transport responses and disposable files; no Docker/AWS publication
Relevant inputs and evidence invalidation: qualifier, fixture, publication binding, declarations and fake responses
Expected cost and measurement: estimated under5seconds; measure after implementation
Retained manual/deferred route: actual image and live effects cannot be replaced by these fixtures
Existing capability considered: existing package qualification/custody and publication tests
Reuse decision: one focused test owner for this capability, no general verification engine
Why a script is necessary: existing HTTP fixtures do not exercise managed-handler selection and native runtime responses
```

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/publication.py
Role: operation
Owner and capability: managed-handler package publication binding
Purpose: bind the selected declared program to existing ecr_publication.Publisher and scope ECR destination
Direct consumers: protected-main publish-kanbien-core-platform-scheduling.yml
Named risk: publication bypasses qualification/custody or publishes to a different scope/source
Proof lane: package/deploy
Execution boundary and actual child effects: existing immutable publication/reservation, Docker/ECR network and safe evidence files; no workload mutation
Relevant inputs and evidence invalidation: program/image/candidate declarations, fixed scope destination, qualification/source identity and existing publisher
Expected cost and measurement: existing publication/scan cost plus actual image bytes; measure hosted run
Retained manual/deferred route: failed/uncertain publication uses existing reservation reconciliation, never a new blind push
Existing capability considered: ecr_publication.Publisher and both existing HTTP publication bindings
Reuse decision: thin selected-program binding; retain main-only protection and existing publication engine
Why a script is necessary: existing bindings are deliberately fixed to HTTP programs and must not falsely qualify handlers
```

The new workflow is a separate caller of existing publication mechanics, not a
second publisher or a relaxation of protected-main source, scan, SBOM or
provenance requirements. No qualified receipt may be emitted for unproved
mandatory image behavior. Additional file admissions must precede their creation.

#### Scheduling activation controller admission — 2026-11-27 04:56Z

The explicit bounded script and shared-network approvals cover this reusable
capability before its new files are created:

```text
Proposed paths: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/{script.py,script.sh,smoke-test.py}
Roles: script.py operation (~450 lines); script.sh operation wrapper (<40 lines); smoke-test.py test (~220 lines)
Owner and capability: 04.deploy / 50-deploy / scheduling-control
Purpose: prepare, review, execute and observe declared scheduling network/scope CloudFormation changes
Direct consumers: core-server-persistence and entity-smoke scheduling bindings; governed manual activation
Named risks: shared SQS endpoint breaks legacy apps; wrong release/schema/principal activated; uncertain changes replayed; failed stack reported healthy
Proof lane: focused local fake-provider tests; real changes and acceptance remain deploy-only
Execution boundary and actual child effects: existing AWS CLI/change-set/reservation engines, local evidence writes, AWS network/IAM/Lambda/SQS/Scheduler/alarms mutation only after governed review
Relevant inputs and evidence invalidation: controller, bindings/templates, selected source/image custody, database readiness, live resource observations and reviewed change set
Expected cost and measurement: fake-provider tests under10seconds; live steps measured separately and constrained by existing goal cost/time limits
Retained manual/deferred route: qualified image, verified database grants, compatibility and cost evidence required before enabling; ambiguous provider state is observe-only
Existing capability considered: AWS cli/change_sets/resource_reservation, package custody validation and existing target update workflows
Reuse decision: bounded composition of existing provider controllers; no second deployment engine, manifest registry or fake HTTP binding
Why scripts are necessary: no existing controller owns managed-handler scope and shared SQS endpoint compatibility activation
```

The dedicated endpoint security group and exact four legacy role/queue routes
preserve existing staging access without editing legacy queues/IAM or broadening
the existing endpoint group. Separate tick/worker controls default disabled.
Release-specific immutable Lambda versions are source/configuration bound.
New binding declarations are data owned by existing foundation/scope directories.
Neither a boolean nor hand-written success JSON substitutes for missing readiness,
cost or live compatibility evidence. Additional new script admissions remain due
before creation.

#### Scheduling acceptance helper admissions — resumed 2026-11-27 work

Keep the existing HTTP primary image and canonical release identity. Its existing
`proof_set` hash binds additional typed scheduler evidence and both managed-image
custody receipts. Do not introduce a second release registry or a multi-image
release-schema migration. An explicit optional `scheduling-a2-v1` qualification
profile requests the additional proof; historical HTTP-only records remain
valid HTTP evidence, never scheduler acceptance. Every selected proof must be
validated by its actual producer/reader and bound to the same owned subjects,
images, source and timeline; caller-authored success flags cannot satisfy it.

```text
Proposed path: scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py
Role: helper
Owner and capability: existing reusable acceptance/release proof semantics
Purpose: validate and retain typed A2 evidence and two exact managed-image custody receipts
Direct consumers: existing core acceptance collector and Entity acceptance route, including retained readers
Named risk: omitted, stale, wrong-subject or tampered evidence is accepted as scheduler qualification
Proof lane: local change and runtime acceptance
Execution boundary and actual child effects: local bounded reads and immutable evidence retention; no cloud or Git mutation
Relevant inputs and evidence invalidation: primary identity, selected profile, declarations, typed producer evidence, package receipts, custody validator and actual caller source
Expected cost and measurement: under10seconds focused local proof; under5seconds semantic retention excluding existing custody validation
Retained manual/deferred route: actual independently observed timed AWS/DB behavior remains mandatory and unproved
Existing capability considered: candidate_document, proof_set, immutable_write and both existing scope collectors
Reuse decision: shared typed proof helper; existing canonical collectors and release schemas stay authoritative
Why a script is necessary: existing generic proof hashes cannot establish scheduler-specific evidence meaning
```

```text
Proposed path: scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof-test.py
Role: test
Owner and capability: existing reusable acceptance/release proof semantics
Purpose: prove actual caller and retained-reader rejection of incomplete or altered scheduler evidence
Direct consumers: registered bounded scheduling acceptance contract check
Named risk: added evidence is unchecked, silently optional or falsely retroactive for historical HTTP records
Proof lane: local change
Execution boundary and actual child effects: disposable local fixtures only; no provider access
Relevant inputs and evidence invalidation: helper, actual collectors/readers, profile schema and existing custody/release validators
Expected cost and measurement: under15seconds estimated, record actual run
Retained manual/deferred route: fixture verdicts cannot substitute for live scheduler acceptance
Existing capability considered: existing core and Entity acceptance-control fixtures and actual candidate_document hashing
Reuse decision: bounded shared helper test with real caller adapters, no new execution wrapper
Why a script is necessary: one cross-scope helper needs one coherent set of missing/tampered/wrong-scope counterexamples
```

#### Shared state-reader admission — resumed 2026-11-27 work

```text
Proposed path: scripts/04.deploy/shared/scheduling-database-state.py
Role: helper
Owner and capability: existing 04.deploy shared bounded task-proof readers
Purpose: validate the exact value-free scheduling database-state projection from both maintenance entrypoints
Direct consumers: existing core persistence proof receipts and Entity Smoke task evidence
Named risk: malformed/private fields or missing work counts become trusted readiness evidence
Proof lane: local change and runtime smoke
Execution boundary and actual child effects: pure finite dictionary validation; no I/O or provider calls
Relevant inputs and evidence invalidation: shared reader, TS state producer, both existing task readers and their fixtures
Expected cost and measurement: under1second within each existing task-reader fixture; measure actual run
Retained manual/deferred route: captured state is not activation authority or end-to-end acceptance
Existing capability considered: core proof-receipts.py and Entity task-evidence.py have separate envelope owners but no shared scheduling state reader
Reuse decision: shared small validator with two real consumers; extend existing operation/receipt routes, no new runner
Why a script is necessary: duplicate shape validation in two independent controllers would drift and wrongly accept missing safety counts
```

#### Additional reused-owner helper admissions — 2026-11-27 05:02Z

```text
Proposed path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py
Role: helper
Owner and capability: existing AWS target-alignment provider adapters
Purpose: bind immutable package qualification to selected declared Lambda runtime/environment/IAM/VPC configuration
Direct consumers: package qualification configuration_fingerprint and existing immutable Publisher
Named risk: accepted image proof silently reused against changed function configuration
Proof lane: package/deploy; local controlled counterexamples in managed-handler qualification-test.py
Execution boundary and actual child effects: YAML/source reads only; no AWS
Relevant inputs and evidence invalidation: scheduling.yml, scope/purpose selection and helper source
Expected cost and measurement: under1second projection; measured in caller fixture
Retained manual/deferred route: actual finished-image and live proof remain required
Existing capability considered: ecs-runtime-configuration.py and qualification.configuration_fingerprint
Reuse decision: Lambda-specific projection at the existing provider adapter owner; no weakening or replacement of ECS projection
Why a script is necessary: the ECS projection cannot truthfully describe managed Lambda functions
```

```text
Proposed path: infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration.ts
Role: target-runtime helper, not a new deployment script
Owner and capability: existing 04.deploy persistence maintenance composition
Purpose: share scope policy, narrow scheduling grants and actual role SQL permission probes
Direct consumers: two existing administration entrypoints and existing real-PostgreSQL fixture
Named risk: inherited escalation, cross-schema access, history/DDL access, missing-table mistaken for expected denial
Proof lane: package/runtime-maintenance; native-engine disposable proof
Execution boundary and actual child effects: SQL roles/grants only under selected admin operation; rollback-bounded permission probes
Relevant inputs and evidence invalidation: immutable manifest, role/table policy, helper and consumers
Expected cost and measurement: under60seconds native-engine proof; measure actual runtime
Retained manual/deferred route: complete history and independently checked effective-role evidence required before activation
Existing capability considered: role-credential, AdministrationObservation, existing PostgreSQL transaction/client and manifest owners
Reuse decision: one policy-driven helper shared by existing maintenance routes; no new runner or capability folder
Why source is necessary: existing HTTP-only grants cannot safely serve distinct dispatcher/worker identities
```

Retained Entity Smoke acceptance inspection: release-98f40c26981890ef5fac0e7d
names source19b0fd3ff1a36dd247de4d820742d2e68bdc9727, whose manifest contains
one checksummed feature migration. The later HEAD manifest has four entries;
neither fact proves current live history. The continuation boundary must use
the accepted minimum and then validate every observed prefix/checksum under
the existing lock. No hard-coded assumption that four were deployed is allowed.

Declaration reuse decision before edits: the existing scope proof compiler
assumes every requirement concerns its one HTTP program/image. Extend that
owner with optional exact requirement `subjects` (program ID, image ID and
image-contract path). Missing subjects retain the old behavior; present subjects
must resolve one-to-one through the existing runnable index and managed image
family, and every selected check must cover every declared subject. Reject
empty/duplicate/unknown/mismatched subjects and HTTP-only proof substitutions.
Update the existing change-impact schema, guide and compiler fixtures; no new
registry, parallel compiler or scheduling-specific bypass is introduced. The
missing business-acceptance route remains a real gap, not not-applicable.

Delivery census reuse decision: its existing proof-command reader only admits
`bash`, although the check catalog already executes direct Node and Python
checks. Extend that same reader with closed interpreter/suffix pairs
(`bash`/`.sh`, `node`/`.mjs|.js`, `python3`/`.py`), retaining argv injection,
source-existence, declared-effects, stage and aggregate checks. Add positive and
negative cases to its existing fixture; do not add no-op shell wrappers.
The broad provider wrapper keeps its conservative network/write effects in
catalog declarations even when an explicitly read-only observation is selected.
Self-consistency observation remains insufficient as qualified target acceptance.

The bounded preview exposed the same Bash-only assumption in the actual
check-selection `validate_check` reader (the declaration report preserved that
reader's finding). Extend this existing selector predicate and its mechanics
fixture with the same closed interpreter/suffix contract already used by the
census; retain source containment, injection rejection, effects and
applicability. This is one command contract at two existing readers, not a new
wrapper or selector. No check timing, permissions or deployment authority changes.
The preview also exposed an unquoted comma in the new provider-check rationale;
quote that YAML scalar without changing selection. Finally, the managed payload
fixture copies actual program source exports and manifests: include that exact
four-program read closure in its existing check inputs and assert coverage in
the existing repository-contract test. Estimated focused correction proof is
under 20 seconds; full selection remains blocked by missing live run-proof routes.

M7 source-identity review found that Entity orchestration's existing
`source_paths` explicitly names its release-succession dependencies. Extend that
same owner to bind `scheduling-proof.py` when present in the selected immutable
revision, following its historical optional-source convention. Older accepted
revisions must retain their exact old identity; absence cannot qualify a new
scheduling profile. Add a focused actual-owner counterexample, not a new source
registry or historical evidence rewrite. The absent trusted live-proof reader
still blocks scheduling acceptance independently.

Database continuation reuse decision before edits: extend the existing adapter
migration runner with an opt-in minimum accepted prefix policy checked under its
existing advisory transaction lock. Existing callers keep their behavior. Reject
unknown/missing-middle IDs or changed checksums before applying a suffix; accept
only exact valid partial/full prefixes and reconcile completed work without
replay. Target callers supply the accepted prefix derived from retained evidence,
not a filename ordinal or unverified live-state assumption. Existing adapter
contract/native-engine tests own concurrency, rollback, partial suffix and
resumption proof. No second transaction engine or ad-hoc target SQL is introduced.

2026-11-27 bounded Senior Prompt Engineer review: **pass_with_notes**, 4.38/5,
172 seconds including required governance reads; no edits, suites or cloud calls
by the reviewer. Scope: the existing-owner extensions below, managed-program
validation, composition route, diagnostic wrapper, two check registrations and
their direct callers/tests. No critical/high finding remains in that scope.
The sole required correction moved the diagnostic catalog `tsconfig.json` input
from a deferred aggregate to its existing local reader. Its focused regression
passed in 0.393s and covers direct/stale selection, source-prefix coverage,
fingerprint invalidation and the omitted-input counterexample. The reviewer did
not observe the final full candidate preview; preparation/integration remain
required. Wrapper help omits several unit names including Lambda (nonblocking).
30s/120s estimates remain advisory until registered timing is recorded.

Review rubric: instruction hierarchy 5, deterministic boundary 4,
drift/contamination resistance 5, context budget 4, human learnability 4,
testability 4. Necessity and placement reuse existing compiler, assembler,
fixture, wrapper and selector owners. No new executable script file or capability
folder is admitted by this review; pending new packaging/controller sources
still require explicit approval. Controlled proof is not PostgreSQL-engine,
finished-image or live AWS proof. After preparation, inspect changed portions,
refresh affected identities and compare with the staged candidate.

Final reviewed SHA-256 identities (relative paths):

```text
1fb248d15312828969a11273e2029dba5305d876985e8be033b7d6c5c7645f61 .agentic/03.product/plans/implementation/reusable-aws-scheduling.md (before this review record)
29ed11b06c6d944df5aaa274905e8db3c1651343db63cec758d55715671b097d scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py
ba20fc8313355c96b971788a466dda915ef19071a1e4ec3a6c86ac3ec24ed6e6 scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/smoke-test.sh
9982d20c92378ec56a9862315528e011715f2d6d4afc767b354405d1d91a53a8 scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs
14b2d048255ba616511df14d7bf8fdedbea3c8c915c45afcf8ba4f0f2a4318b7 scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
ea2de5129b13eeddd83f7b0cb49e99d7307d4a961513bf98e4267b7a0ae8e98b scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs
26d87ac4b2d534e592c2766b991bdcc2a3b6ab265ebf6c1e8f5305309f990cd4 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs
86fda00c4b8ad3d7b46fa434056a6e852e877b61f4399e4bf04dee5e19403413 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs-test.mjs
7571720cadba31f12ae67d3435cdbb25d524f26acf011a235eb1df03b2fa1e97 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-validation-test.py
db9f4aaef4d0239c4acf52556a9cc57b2829b8cf4717cfd993861178810bc60e scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py
255f88565cb51d40a7c67522e6f41957f6c55c52e16ea91231aaa37abf17d28c scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh
c17f1e5c6e75e5fcb5d2ab6f62dfaddce6b033902381ae885c15718f2149643b scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/program-fixture.mjs
1583b6a9d758ef1020e2ee5a04a806d2974bff0dcee1e21bb79aa2099743e440 scripts/repo/check-selection/checks.yml
9b1a1b61a09c06dcdfc1b1b0b121ecc6ef35179ea5dea26d4a205e4a6f09938b scripts/repo/check-selection/repository_contracts_test.py
e8bc5000f28ef6aa9b1f8d9f8f4d92b231816521e2e7bcbde103b2614688f70a scripts/repo/diagnostic-coverage/verify.sh
1bf62bb5b72e39b31efc05242c5e0aa307dc1b2227f29f8bb961fa1a40f9eb50 scripts/repo/diagnostic-coverage/smoke-test.py
ff7f608bcbde9922d85713c4a2bb8710df8882d6323b164ba6ec5ae7f4a3e1d9 scripts/repo/diagnostic-coverage/tsconfig.json
34aa07011196e4b7b53cd082f3fc843ae51323eddf56b49602de3919d7e90188 package.json
a4bd41aa1d3cce006981c0fea6207d962533e0496c2c4fdb746c6dcaffe44da2 platform/adapters/aws/runtime/lambda/package.json
5f436bd5e7a613b8638548b6a0a0371864d6088542b638244a0558c96c0508f7 infra/04.deploy/03.product/entrypoints/runnable-program-index.yml
```

ADR disposition: ADR 0027 continues to own adapter placement and separates
runtime adapters from infrastructure provisioning. A2 follows that boundary,
but its durable choice of database reminders with short-lived execution is a
separate architecture decision. It is recorded in
[ADR 0044](../../../../docs/03.product/adrs/0044-use-database-reminders-with-bounded-job-execution.md).
The session's updated disposition supersedes the earlier ownership-only
assessment; accepting this design does not qualify or authorize the draft
shared-network endpoint.

Implemented existing-owner admission (before commit preparation):

- `scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/{smoke-test.sh,runtime-test.mjs}`
  remain the wrapper/test owners. Their explicit `--scheduling` route compiles
  one declared managed worker and uses existing package assembly for controlled
  dispatch/worker proof. Consumer: the new `scheduling-composition` local
  integration check, not HTTP image qualification. Risk: correct shared code
  wired to the wrong app, identity, source or acknowledgement. Effects: local
  compilation and disposable fixtures only; no AWS/database or Git operation.
  Inputs/invalidation: declared source closure, selected program, runtime/test
  files and existing assemblers. Advisory budget 120s; actual focused command
  passed, full registered timing is still pending. Reuse extends the existing
  owner and leaves its no-flag HTTP route unchanged; no new script is created.
- `scripts/repo/diagnostic-coverage/verify.sh` remains a literal unit wrapper;
  its new Lambda case invokes the existing root npm script with ignore-scripts.
  `scripts/repo/check-selection/checks.yml` remains the only selector, with
  `lambda-runtime` and `scheduling-composition` bound to their actual inputs.
  Existing `repository_contracts_test.py` proves declared effects, dependency
  closure and the matching source-selection rule. Risk: omitted runtime proof
  or unrelated rechecks. These are affected-capability local integration units,
  not a new universal cross-capability scheduler or periodic task. Budget:30s
  for the Lambda unit and120s for composition; no new aggregate or automatic
  cloud work. Runtime/tool/config/source changes invalidate their existing
  selector receipts. Later image/deployment proof remains separately mandatory.
- Runnable declaration and placement validators extend their current canonical
  owners for four managed programs; their existing helper/fixture roles and
  local-only effects remain intact. Positive/negative cases reject unsafe
  handler selection before build effects. The shared dependency fixture now
  supplies the selected source required by that same real reader, not a second
  implementation. These changes add no script source files or capability folders.

The normal offline npm install restored the already-locked Lambda workspace
link after registered runtime identity rejected its absence. Both manifest
hashes remained unchanged; no manual link or identity bypass was used. The
blocked initial registered batch is retained as failed setup evidence.

The first direct commit preparation exposed eight additional input gaps that
the broader dependency graph had hidden. A second bounded SPE review passed
with notes in32s, score4.54/5 (hierarchy5, deterministic boundary4, drift5,
context4, learnability4, testability5). Existing owners now actually inspect
all four isolated handler projects and the two draft templates, and their
consumed inputs are directly selected. Catalog assets select their existing
reader rather than only a deferred aggregate. Real PostgreSQL qualification
binds its added app/composition dependencies without moving out of package
stage. Three focused mapping cases passed1.75s; the managed-project fixture
passed0.47s; static provider positive/negative cases passed. A production
direct-preparation preview found zero gaps across143 inputs/47selected checks
in9.05s, but wrote no receipt and does not replace final preparation.
No new script source or capability folder was added. Final reviewed identities:

```text
51ee00a27eecd8caf5985b426651e40ae672153e7e5373a31ddb7f46c422ebe0 scripts/repo/check-selection/checks.yml
65b0c6d4be365cd52af794e8c3b38b29e731dadf8765299527e04586c0b4d66d scripts/repo/check-selection/repository_contracts_test.py
d2fa3cdf22f86c5f24cceb9ddeb47dc1bd08a7ba2354758c58dd43f7ca841650 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs-test.mjs
e07608fdb417fa6d10d6dfed9787d3ea595d0e75991d57a284dfd5e8cc848ad6 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh
```

Root inspected the prior preparation's source changes: task-owned diagnostic
identities differed only in their required lifecycle date, verified by
reconstructing that prior date and matching the reviewed SHA-256. Only those
task identities were refreshed. The bounded dispatcher and new selection
fixtures were separately reviewed; unrelated historical ledger debt remains.

The final M4 caller adds nine consumed inputs to the existing PostgreSQL
qualification owner: the SQS adapter, five Entity Smoke runtime dependencies
and three shared persistence dependencies. The command, package stage and
effects remain unchanged. `plan_review` reviewed its own two-file mapping delta
under run-agent-review v2, script-admission v4, the SPE role/rubric v1 and
agent-contracts/professional-quality v1: pass with notes, 4.54/5; hierarchy 5,
deterministic boundary 4, drift 5, context 4, learnability 4, testability 5.
Substantive review took 55 seconds, excluding the preceding governance reread.
Root separately inspected the input mappings and exact fixture assertions.
Two focused tests passed in 0.643 seconds. No critical, high or medium finding
remains; the low residual is manually maintained import closure with explicit
selection fixtures. This is not independent authorship or live proof. Final
preparation must follow the connected fixture's freeze. Reviewed identities:

```text
5936ff28915ccf0de7746b8eca8b907eca9630be4b9c99e47bca0ed9a0cb42bf scripts/repo/check-selection/checks.yml
ef70032282f638727930074fe906983034c476a93114d62e1462a10c2652666b scripts/repo/check-selection/repository_contracts_test.py
```

### Combined verification correction batch — 2026-11-27 01:42Z

The prepared seven-unit refresh passed in64.84s (five trusted reused results,
PostgreSQL connection diagnostics33.256752s and scheduling composition10.862243s
executed). Observation:
`.cache/test-runs/20261127T011928Z-e5ef0fbbec2b4a17bf9839c10ee1056b/report.json`.
This is requested-check-only proof. The following complete affected local run
finished with60passed,7failed,4blocked and28deferred in1147.46s, exceeding its
ten-minute advisory budget. Observation:
`.cache/test-runs/20261127T013845Z-a5b91cf47da448d78f324ae3f1247d1b/report.json`.
Child execution accounted for1065.923832s; fingerprinting42.372131s, planning
22.400239s and runtime identity13.852298s. No complete integration pass is claimed.
The runner deliberately retains unsupported shell output as unavailable rather
than copying arbitrary output. Controlled existing-owner replays establish the
following correction inventory before edits; no generic reporting engine is added.

- `core-server-dependency-boundary/binding-test.py`: declare the source and
  compiled entrypoint already created by the fixture. Its9-case replay failed
  seven cases prematurely with `program-build-inputs-rejected` in1.871s.
- `prepare-runtime-payload/assemble-test.mjs`: copy the real source files for
  its existing explicit entrypoint map, matching the actual Docker input.
  Its39-case replay failed15 cases with `program-build-source-unreadable` in
  11.542s before writes. Keep all omission negatives and precise failure assertions.
- `declaration-coverage/runtime-configuration-test.py`: duplicate the candidate
  matching the selected image, not the last array element. The new scheduler
  candidates invalidated that position assumption. The isolated20-test replay
  failed only `candidate-ambiguous` in96.68s. The production resolver is correct.
- `kanbien-platform-postgresql-migration.main.ts`: restore migration-list
  construction inside the existing observed invocation block. Its moved list
  drops `persistence.boundary-observed/v1` when the real target schema predicate
  throws. Existing `verifyPostgreSqlCompositionBindings` detects exactly this;
  retain its two-record expectation, no new definition or replay. The normal
  shell image build passed16.53s; its payload verifier failed96.07s at this
  assertion. The earlier broad-entrypoint hypothesis did not explain the failure;
  do not broaden or narrow the compiler as a speculative repair.
- `verify-platform-shell-postgresql-reference/script.sh`: use the existing
  TMPDIR-aware temporary-file facility instead of hardcoded `/tmp`. The unchanged
  wrapper reproduced ENOSPC in0.331s; `/tmp` is full. Do not remove unrelated data.
- Negative-authorization and persistence-write-client fixtures failed9.776s and
  9.091s at the existing offline delivery-inventory gate, before fake provider
  invocation. The exact6.39s inventory replay identifies two task-created
  `delivery-consumer-unbound` findings: the scheduling and scheduling-network
  templates have static checks but no executable qualification/activation route.
  This is incomplete M5/M6, not baseline debt or stale generated data. Real
  deployment support still awaits explicit script admission. Do not invent
  bindings to the HTTP/ECS controller, exempt draft status, relocate the files
  or remove assertions to obtain a green result.

These are corrections at existing owners, with no new script files, folders,
execution lanes or recurring checks. Runtime/diagnostic meanings remain fixed;
the migration correction restores their actual delivery. Review that source and
refresh only its existing diagnostic ledger identity after correction. Existing
registered checks own final proof. Reopen only affected reviews/preparation,
finish the correction batch, then freeze and reuse matching evidence. Current
local results are not container qualification, cloud readiness or acceptance.

Correction review: root inspected the full affected delta and consumer paths;
`plan_review` independently passed the bounded correction review in50s with no
must-fix finding. The selected-image ambiguity owner passed its focused method
in0.64s. All contributors are finished and code inputs frozen before preparation.
No additional script admission is needed for these ordinary bug fixes: existing
roles, owners, consumers, effects and lanes are unchanged. The static reference
helper has a new source-matched `support` review, not runtime adoption. Exact
reviewed source identities (diagnostic ledger retains the two executable owners):

```text
5461a7145ade7d10d9ff87fbd8828fdeed7a2b0aa7fe2a30f739018a1f3b5b22 binding-test.py
094621c595bb17020db019f5ffea6122a555ae1ff4604afe3dad1c68564a1ca2 assemble-test.mjs
ce23fbc7877e57dc4eb1a0901e963120590b354bba93a7181325c66876b4dfc6 runtime-configuration-test.py
6a97dbfe862a5e2e0fb3f7a881fd162140b92d745173c26bea01ed3c7c3fe398 kanbien-platform-postgresql-migration.main.ts
7172163a9713c751a16342fa3608e9358b0d7fcbc75b73eb045bc8044fd5ef13 verify-platform-shell-postgresql-reference/script.sh
```

Verification budget for the correction: eight minutes for registered affected
units with matching-result reuse, then two minutes for the existing real-engine
owner. Unchanged inventory failures are already established and must not be
replayed merely to rediscover the missing delivery route. These budgets are not
authority to skip checks or terminate uncertain operations.

The corrected eight-unit run completed in 453.29 seconds, within its eight-minute
budget: seven passed, with only `platform-shell-payload` still failing. Observation:
`.cache/test-runs/20261127T015711Z-9c53df7e1615434884913b9469f618e9/report.json`.
The existing payload verifier then reproduced the exact remaining assertion in
82.37 seconds: migration manifest construction ran before selecting the runner's
`apply` method, unlike the original expression. Restore the original evaluation
order by retaining the constructed list inside the call argument; keep the
observed try, original receiver, manifest-derived result count and every existing
failure assertion. No extra factory or diagnostic meaning is introduced.
Final source identity:
`b58008d3337a8e7564dbade2d4ceffce5e2b93072878ea4a79ac827fd86e284b`.
Only its matching diagnostic review identity changes. Prepare this correction
and rerun the owning registered payload/diagnostic checks (four-minute budget),
then the real-engine owner (two-minute budget). Other unchanged passing results
remain evidence at their recorded boundaries; no full integration pass is claimed.
Separate read-only review confirms legacy restore verification selects only the
two original migration IDs. Its count is not the failing assertion, but neither
does that historic proof establish the new retry-column/runtime compatibility.

Final correction disposition: `plan_review` independently confirmed the exact
source and preserved expression/receiver/error behavior in an81-second read-only
audit. Governed preparation passed in49.88s with no findings. Registered
`platform-shell-payload` and `diagnostic-catalog-readers` both passed in187.33s
(97.545137s and68.238639s respectively), within the four-minute budget. Observation:
`.cache/test-runs/20261127T020456Z-2e46f4fe36ac4da4a63876214af49a4b/report.json`.
This requested-check-only run does not replace complete affected integration.

The prepared real-engine owner then passed in27.06s, including native
PostgreSQL18.6 startup, all assertions and confirmed engine/directory cleanup.
The connected fixture identity remains
`4d722c033bb8ef330cfa0867e66f9be2875ea8ece9b1bd7552ad5e76bba80bb0`.
This owner is catalogued in the package/CI lane, not executable by the local
selector; its direct governed invocation proves disposable database behavior,
not container qualification or CI/live acceptance. Earlier added assertions now
cover actual handover rollback after insert, two simultaneous public due passes,
identical IDs in separate schemas and uncertain completion after a committed
purge followed by lease-fenced recovery. The production SQS adapter uses controlled
transport in this local fixture; no live SQS delivery is claimed.

Remaining blockers are unchanged: explicit new-script size/folder admission,
shared-VPC compatibility authority and its governed proof, finished Lambda
packaging/qualification, the two executable delivery routes, and a measured
forecast within the existing cost ceiling. No required operation is left running.
No staging, commit, push, AWS mutation or shared-database write has occurred.
The final handoff text also passed a20-second independent read-only review.

Growth/cost across this overnight delta: zero script-source files added, removed
or moved; existing helpers and tests were extended. Two registered units were
added, `lambda-runtime` and `scheduling-composition`, selected by their declared
inputs; no new recurring agent-review requirement was introduced. The existing
real-database unit now covers the connected app and transport inputs. The
19-minute combined run exceeded its ten-minute budget and remains a failed
observation; targeted correction timings above do not establish a delivery
speedup. Image, hosted-runner and AWS operating costs remain unmeasured.

The selected implementation uses four separately declared candidates: dispatcher
and worker for each scope. One shared Dockerfile and assembler may build them,
but the existing single-program custody receipt must bind the selected handler
truthfully. The managed runtime is the official AWS Node.js 22 image, verified
as linux/amd64 at
`public.ecr.aws/lambda/nodejs@sha256:468c53b1f8cdc6678e5377ccb87c73cf00005b0bad0ba1d03de8d89589b591f7`.
Registry manifest verification is not image qualification.

The existing neutral program validator now distinguishes a process command
from a managed handler. The latter declares its compiled module and exported
function, accepts only the exact derived handler token, and leaves provider
bootstrap proof to packaging. Existing process restrictions remain unchanged.
The placement validator lacked kinds for its established entrypoint/image
homes; the bounded owner correction adds those exact shapes and negative cases,
not a general path exception.

Proposed script admission, before file creation:

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler.mjs
Role: helper
Owner and capability: existing 40-package prepare-runtime-payload owner
Purpose: assemble one declared managed handler using the existing workspace payload and installed-dependency owners
Direct consumers: shared scheduling-lambda Dockerfile; four separately declared scheduling candidates
Named risk: package invokes a different handler or includes dependencies outside its approved program
Proof lane: package/deploy; focused helper regression during local change
Execution boundary and actual child effects: local declaration reads and payload writes only; no provider calls, Docker publication or deployment
Relevant inputs and evidence invalidation: selected runnable declaration, source entrypoint, workspace manifests, compiled files, installed lockfile closure, helper and existing assembler/resolver sources
Expected cost and measurement: one selected payload traversal; focused synthetic regression estimated under 5 seconds, measured after implementation
Retained manual/deferred route: finished-image runtime qualification remains separate and mandatory
Existing capability considered: prepare-runtime-payload/assemble.mjs, prepare-runtime-dependencies/prepare.mjs, workspace-build and runnable-program-contract/build-inputs.mjs
Reuse decision: extend existing capability with a bounded managed-handler binding
Why a script is necessary: existing wrappers start HTTP processes; they do not expose a declared function to the managed runtime
```

```text
Proposed path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler-test.mjs
Role: test
Owner and capability: existing 40-package prepare-runtime-payload owner
Purpose: prove exact handler selection, compiled export preservation and fail-closed arguments using disposable local payloads
Direct consumers: owning local/package check; no new automatic cross-capability selector
Named risk: wrong export, process/handler substitution, extra command tokens or unsafe target path passes assembly
Proof lane: local change, then selected package qualification
Execution boundary and actual child effects: read source plus write isolated temporary fixtures; no account, network, Git or cloud effects
Relevant inputs and evidence invalidation: helper, program reader, payload assembler, runtime package resolver and controlled fixtures
Expected cost and measurement: estimated under 5 seconds excluding compilation; report actual elapsed execution
Retained manual/deferred route: actual AWS runtime-interface image proof is not replaced by fixture success
Existing capability considered: current payload and runnable-program tests
Reuse decision: new focused regression beside the existing owner; reuse its fixture/assembly interfaces
Why a script is necessary: controlled handler-export counterexamples are absent from current HTTP-wrapper tests
```

New script source above 50 code lines remains pending explicit prior size
approval; general goal authority is not treated as that approval. The existing
`build-inputs.mjs` will expose a checked runtime-entry projection for this
consumer rather than introduce another manifest reader. Its owning tests must
reject missing or malformed handler metadata while preserving process inputs.

Runtime diagnostic inventory: the Lambda bridge owns invalid remaining-time
facts and returned failed relay statuses. Persistence failures and raw throws
retain their original identity internally, without replay. Final entrypoint
reporting must select the source catalogs and replace any arbitrary thrown
message before it reaches the AWS runtime logger. Event contents, identifiers,
credentials and provider responses must not become diagnostic detail. Budget
checks are cooperative between calls; dependency timeouts still bound work
already running. Registration, compilation, focused runtime tests, finished
images, custody and live acceptance remain distinct progress states.

**Existing owners:**

M5 target-composition pre-code inventory (scheduler_inventory, 2026-11-26):

Checked-value follow-up (2026-11-27): expose the IAM reader's already validated
region alongside username/token, so target queue/IAM relationships never reread
the raw environment. Existing callers retain their token behavior. The existing
core persistence composition runner gains a named `--scheduling` mode for the
new candidate; it reuses declared package preparation, not a new script owner.
The scheduled-only statement timeout is 3000 ms (client timeout 4000 ms); other
purposes remain unchanged. Tests model the worker's eight-query reconciliation
path and seven-query failed-handler/reconnect/visibility path against its 45s
reserve; real network and packaged-runtime proof remain separate gates.

- Own new `shared/scheduling/configuration.ts`, `diagnostics.ts`, `composition.ts`
  and `invocation.ts` beneath the existing entrypoint owner, plus four thin
  `kanbien-core-server-persistence-scheduling-{dispatch,worker}.handler.ts` and
  `kanbien-entity-smoke-scheduling-{dispatch,worker}.handler.ts` entrypoints.
  The deployment reviewer owns their build/program/candidate declarations;
  the root owns the baseline public app and shared diagnostic review ledger.
- Reuse public PostgreSQL configuration, IAM-token and certificate readers,
  production app mounting, Core clock/UUID/worker lease identity, bounded
  persistence dispatcher, durable worker, SQS codec/batch/queue and Lambda
  deadline adapters. No second decoder, registry, poller or job engine is added.
  Public app factories own business work. A shared invocation owner supplies
  cleanup and the final managed-runtime error boundary for both scopes.
- Configuration predicates distinguish missing/wrong-type/blank/invalid source
  values through existing checked readers. Target relationships additionally
  enforce fixed schema and distinct purpose-specific database identity, IAM
  reference/username agreement and queue URL/ARN/region consistency before any
  pool/client construction. Test-only authentication inputs stay behind the
  existing explicit local-qualification policy; deployment declarations must
  reject them. Dependency budgets and batch size must match provider declarations.
- Diagnostic producers preserve selected source evidence through initialization,
  mount, dispatch, worker and cleanup. A new finite target boundary definition
  supplies scope, purpose, phase and known effect only. Raw exceptions, SQL,
  event bodies, native IDs, queue addresses, account identifiers and credentials
  are excluded from final runtime logs and thrown messages. Generated catalogue
  export and review registration remain coordinated with their existing owners.
- Planned proof extends existing composition fixtures with actual mount/handler
  calls, configuration rejection before resource construction, durable-success
  acknowledgement only, bounded callbacks, original source diagnostic retention,
  safe outer failures and exactly-once cleanup attempts. Relevant registered
  composition/runtime checks and managed-image qualification remain separate.
  Source-level handler tests do not prove the runtime-interface image or AWS.
  No new script over 50 code lines is introduced by this composition slice.
- Approved deadline extension: the existing PostgreSQL connection factories
  also set the driver's `query_timeout` to the checked statement timeout plus
  1000 ms for server error/response settlement. This bounds a lost response;
  it does not establish whether a remote mutation committed. Both password and
  token pools reuse the same rule; existing callers retain their server deadline.
  The existing shared persistence configuration gains a `scheduled` purpose
  selecting one pool connection and the same runtime connection/query policy.
  Existing purposes are unchanged. Pool-construction contract assertions and
  target configuration fixtures must distinguish missing or copied deadlines.

```text
infra/04.deploy/03.product/entrypoints/
  kanbien-core-server-persistence.app.ts
  kanbien-core-server-persistence.main.ts
  entity-smoke/runtime.ts
  runnable-program-index.yml
infra/04.deploy/03.product/image/
  core-server-persistence/
  entity-smoke/
```

**Proposed new paths, not existing files at this baseline:**

```text
infra/04.deploy/03.product/entrypoints/
  kanbien-core-server-persistence-dispatch.handler.ts
  kanbien-core-server-persistence-worker.handler.ts
  kanbien-entity-smoke-dispatch.handler.ts
  kanbien-entity-smoke-worker.handler.ts
infra/04.deploy/03.product/image/
  core-server-persistence-scheduling/
  entity-smoke-scheduling/
```

Confirm names through the owning program/placement rules before creation.
Each handler selects configuration, identities, adapters and public mounts,
then invokes shared machinery. These are composition boundaries, not four
implementations. Multiple function roles may share a scoped immutable image
with different handlers and IAM roles; apps need not share another app's image.

Existing ECS command/image acceptance does not prove Lambda compatibility.
The target must explicitly select the on-demand event-function runtime, not a
long-running or provisioned Lambda variant. Reuse normal builders and package
custody while extending their supported runtime contract, not a bespoke bypass.

- [ ] Reuse the target-owned baseline acceptance pattern for a harmless job
  recording durable, delivery-specific completion.
- [ ] Use Entity Smoke's actual registered feature job for the second proof.
- [ ] Declare each program's command, observed/approved dependencies,
  configuration, identity and lifecycle independently, including Lambda handler
  and runtime-interface requirements, timeouts and event-source mapping.
- [ ] Keep HTTP dependency boundaries narrow; approve background dependencies
  for the programs that actually use them, not blanket removal of exclusions.
- [ ] Update Dockerfiles, default-deny contexts, exact payload allowlists,
  image/realization contracts and package declarations.
- [ ] Qualify the compiled handlers through the actual Lambda-compatible runtime
  interface from finished images, including mixed batches, initialization,
  deadline failures and warm invocation. Merely importing a handler is not proof.
- [ ] Prove runtime-compatible least-privilege user/filesystem behavior and
  no-source/no-secret guarantees; do not assume the ECS launcher runs unchanged.
- [ ] Sharing an image must not grant its HTTP process migration or purge power.

Reuse `scripts/repo/workspace-build/`, runtime package/dependency assembly,
`scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh`
and existing core-server-persistence/entity-smoke builders and image smoke checks.
No handwritten alias map, application-specific build engine or inherited
core-platform base image is required.

**Exit:** meaningful finished-function-image proof for both compositions, with
distinct handler/identity boundaries. Publication is not yet claimed.

## M6 Extend reusable deployment support

**Goal:** expose this capability through normal target declarations and shared
delivery controls, not one-off manual deployment instructions.

### Overnight source inventory and remaining activation gates

Historical discovery record: the shared-network authority described below as
pending was subsequently granted explicitly by the user. The current approved
owner is `deploy-disabled-scheduling.md`; the implementation now preserves the
identified legacy roles/queues through a dedicated endpoint group and full-VPC
inventory. These earlier paragraphs explain the discovered risk, not a current
authority block. Live preservation proof, cost admission and final runtime
acceptance remain required. No creation is authorized merely by this note.

The new provider-owned `cloudformation/scheduling.yml` is one shared declaration
instantiated separately for each scope. It declares digest-bound dispatcher and
worker images, independent IAM/DB identities, a retained job queue/DLQ, private
network rules, and an initially disabled minute trigger and worker mapping.
Function timeout is 60 seconds, queue visibility 360 seconds, worker batch one,
dispatcher concurrency one and worker concurrency two. Neither the template nor
its local structural check proves package qualification or grants activation.

`cloudformation/scheduling-network.yml` is a separate, once-per-target addition
consuming the existing VPC, two approved private subnets and endpoint security
group. It adds only an SQS interface endpoint restricted to the four scoped
queue ARNs. It does not alter the create-only foundation, add a Scheduler API
endpoint/NAT, or duplicate a shared endpoint for each scope. The controller must
first reconcile any equivalent existing endpoint, actual route and policy. If
absent, the two-AZ addition is the previously estimated US$15.84/month; current
account/region facts and the complete US$25 combined ceiling still gate execution.

Independent review found a pre-CREATE shared-network safety gate: private DNS
for this SQS endpoint affects the entire existing VPC, even while both scheduler
triggers are disabled. A policy restricted to these four queues can therefore
break another workload using the regional SQS hostname. Before creating or
updating the endpoint, the governed controller must inventory existing SQS
consumers/routes and prove their access is preserved. Unknown impact blocks
creation. Do not broaden its queue policy or replace shared routing without an
approved ownership decision; isolated explicit endpoint routing is an alternative
design, not implemented support. No existing VPC impact has been measured and
the current draft template is not approved for direct execution.

Fresh read-only inventory through the AWS inspection workflow confirmed this
is a real shared-consumer conflict. The declared kanbien-dev/eu-west-1 identity
matches; foundation and persistence stacks are UPDATE_COMPLETE. The existing
private database is PostgreSQL18.3, db.t4g.micro,20GiB gp3, single-AZ with IAM
authentication and seven-day backups. Selected private subnets are in1a/1b,
without default internet/NAT routes. Existing endpoints cover S3, ECR API/Docker,
Logs and Secrets Manager, but not SQS. The VPC also contains staging ALB/Redis,
databases and service bindings. Four staging queues already exist:
`kanbien-staging-platform-shell-worker` and its DLQ, and
`kanbien-staging-platform-relational-smoke` and its DLQ.
Their regional SQS consumers remain source-defined even though the staging
worker is currently scaled to zero. The draft endpoint policy excludes them;
endpoint ingress may also exclude their security groups. A separate request
for governed shared-network compatibility authority is pending. No endpoint
creation, policy broadening or custom-endpoint workaround is authorized by
this finding. The SQS-specific official guide currently requires private DNS;
generic endpoint-hostname guidance is not sufficient proof for a workaround.

A read-only compatibility design would use a dedicated SQS endpoint security
group, not broaden the group protecting ECR, Logs and Secrets Manager. Resolve
the existing worker/relay groups and four task-role ARNs from staging foundation
outputs, preserve their exact source-queue actions, and export the new SQS group
to the two scheduler scopes. Both relational tasks use the worker network.
Existing groups already permit outbound HTTPS. No existing IAM, queue policy or
service changes are proposed, and no direct DLQ permissions are inferred.
The two sender roles retain SendMessage only; the two consumer roles retain
ReceiveMessage, DeleteMessage, ChangeMessageVisibility and GetQueueAttributes
on their own source queue. This is an unapproved design, not an implementation.
It still needs governed live compatibility proof: existing delivery proof labels
are single-use, the relational proof includes unrelated migrations/restores,
and staging's server is currently desired/running 1/0. Repairing or scaling
staging is outside this goal. Static policy checks alone cannot close that gap.
One dedicated group adds no endpoint-hour charge, but existing staging traffic
routed through the endpoint must enter the incremental data-cost forecast.

Monitoring source review found an existing notification destination in
`core-server-persistence.yml`: the target-owned
`kanbien-core-platform-observability-alerts` topic and its private email setting.
No new recipient is needed, but its present subscription/delivery state remains
unverified. Existing observability apply/validate/receipt owners are explicitly
closed to the two PostgreSQL alarms and cannot qualify scheduling unchanged.
Native missing-invocation, dispatcher-error, queue-age and DLQ-visible alarms
would require eight single-metric alarms across both scopes, about $0.80/month.
That is $0.20 above the earlier six-alarm allowance: the illustrative 31-day
envelope becomes about $25.01 before unmeasured database and notification costs.
This is not permission to exceed the $25 ceiling or remove a required signal.
The existing target-wide $100 budget is not this goal's incremental cost guard.
Source review took approximately 90 seconds; no alarm declarations, recipients
or resources changed. A cost-compliant design plus governed fault/notification/
recovery proof remains required; queue age alone does not detect every stuck
database reminder, and partial-batch failures are not Lambda invocation errors.

Current official Ireland price lists confirm paid rates of$0.20/million Lambda
requests,$0.0000166667/GB-second,$0.40/million Standard SQS requests,
$1/million Scheduler invocations, and$0.011/AZ-hour plus$0.01/GB for the
interface endpoint. The existing100k-job scenario remains about$20.39/30days
without free tiers. An illustrative larger envelope is$24.28/30days
(about$24.81/31days): at most300k billed Lambda GB-seconds including initialization
and retries,250k invocations,2million SQS requests,4GB ECR,2GB logs,10GB endpoint
traffic,six standard alarms and$0.20 transfer allowance. These assumptions are
not a measured ceiling. Image/log sizes,durations,retries and incremental
database storage/CPU-credit charges remain unmeasured. The earlier six-alarm
envelope is historical: current source declares four alarms per scope, eight
combined. Its conservative 31-day subtotal is approximately US$25.01 before
unknown extras, so that envelope does not satisfy the US$25 ceiling. Actual
alarm delivery is unproven. At60seconds for every normal invocation, Lambda compute alone could
reach about$93.20/30days. Actual proof must establish an acceptable forecast
before activation, not rely on timeout/concurrency as a$25hard cap.
Official region price lists (published2026-11-25, checked2026-11-27):
[Lambda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSLambda/current/eu-west-1/index.json),
[SQS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSQueueService/current/eu-west-1/index.json),
[Scheduler](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSEvents/current/eu-west-1/index.json),
[PrivateLink](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/eu-west-1/index.json).

The baseline administration route currently accepts an empty migration journal
or its exact two-entry manifest. Do not silently substitute the new scheduler
manifest there. Activation needs a separately reviewed additive-prefix route
that preserves the old entries/checksums, applies only the known suffix, records
resumable evidence and rejects unknown, changed or partially inconsistent state.
Distinct scoped dispatch/worker grants and effective denial proofs must precede
enablement; the HTTP role must remain unable to hard-delete feature rows.

Disabled tick/mapping defaults are not a complete safety barrier: authorized
manual invocation, existing in-flight work, IAM/network creation and private
DNS changes are separate effects. RDS IAM connect grants authentication, not
SQL access; effective SQL grants/denials still need proof. Inventory and protect
all pre-existing reminders, outbox entries and entity rows before any invocation,
not just before automatic activation. The shared scoped DLQ receives native job
redrive, Scheduler failure events and Lambda asynchronous failure envelopes;
recovery must identify the format before any return to the job queue. No blind
whole-DLQ redrive is authorized.

Reusable packaging/qualification and activation-controller source has now been
admitted under the explicit bounded approval. Remaining implementation gates
include trusted deployment admission, actual managed-runtime invocation proof, selected
image/digest/source binding, schema/grant reconciliation, failure/recovery proof
and operational alerts. Existing hosted publication workflows provide a Docker
engine route, but their current HTTP image proof is not Lambda qualification.
The prior pending script-size/folder approval was superseded by the explicit
04:46Z continuation approval recorded above. Local template checks are not AWS
validation or live acceptance, and M6 remains in progress.

Read-only acceptance review identified these concrete counterexamples for the
admitted implementation; this is preparation, not completed delivery support:

- Migration continuation must distinguish the accepted prefix, a complete or
  partially applied approved suffix, unknown IDs, changed checksums and a missing
  prefix. Concurrent migration and lost controller responses must reconcile the
  same operation, not replay committed statements under a new identity.
- Prove the identity table below through actual operations in both schemas,
  including inherited roles. A failed connection or missing table is not a
  permission-denial proof; HTTP must save a deletion/reminder but cannot purge,
  dispatcher cannot edit feature rows, and worker cannot alter schema/history.
- Earlier unqualified function targets and `$LATEST` failure configuration were
  replaced in source by published dispatch/worker versions. Actual deployment
  must still bind source, digest, handler,
  published function version, queue, trigger, mapping and failure destination
  in one observed release. Reject mixed versions, wrong handlers/queues and
  rollback to code unable to read current durable state.
- Separate `TickEnabled` and `WorkerEnabled` settings now exist in source.
  Prove a queued message and active lease survive disabling new activity;
  distinguish disabled receives from quiescence, and retain identities on resume.
- A scheduler alert receipt must bind the actual release/scope, signal,
  transition, confirmed subscription, observed notification and recovery.
  Historical alerts or subscription confirmation alone do not prove delivery.
- Finished-image qualification must invoke the packaged managed-runtime handler,
  including malformed events, depleted time, pre-resource configuration failure,
  batch settlement, safe outer errors and shutdown failure. A direct function
  import, HTTP bootstrap or baseline image containing app-only dependencies
  must not satisfy that boundary.

**Affected target families:**

```text
infra/04.deploy/03.product/targets/kanbien-core-platform/
  20-scopes/core-server-persistence/
  20-scopes/entity-smoke/
  30-provider-realization/aws/cloudformation/
    core-server-persistence.yml
    entity-smoke.yml
  40-package-custody/github-actions/
```

- [ ] Declare one fixed minute EventBridge trigger and dispatcher function per
  scope, one job queue with its worker function/mapping, and their failure
  destinations. Infrastructure owns the fixed trigger; individual reminders
  remain database rows, not separately provisioned AWS schedules.
- [ ] Add reusable Lambda realization, package activation, version binding,
  mapping control, verification and rollback at the existing provider/delivery
  owners. This support is new work, not inferred from existing ECS tasks.
- [ ] Declare migrations/grants, private network/service access, configuration,
  cost, health, failure, recovery and acceptance evidence.
- [ ] Complete the region-specific cost worksheet for all scenarios, including
  existing versus new networking, DB capacity/proxy, empty queue requests and
  logs. Review any fixed-cost addition and numeric budgets before live mutation.
- [ ] Configure bounded function concurrency/DB pools, retention and cost alerts.
  Do not enable provisioned concurrency/pollers or an idle ECS fallback by default.
- [ ] Deliberately review Entity scope's current queues/workers and hard-purge
  exclusions before enabling those capabilities.
- [ ] Preserve accepted release histories; do not edit old receipts to claim
  qualification of the new capability.
- [ ] Extend the governed initial-capability activation route. Current
  ordinary-update is image-only and cannot authorize new queues/IAM/migrations.
- [ ] Add tests at shared owners for both baseline and feature bindings, plus
  cross-scope rejection. Workload facts are inputs, not duplicate controllers.
- [ ] Define safe disablement for new reminders, minute triggers, dispatch/relay,
  worker mappings and in-flight work separately.
  Keep durable queued work and migration compatibility during rollback.
- [ ] Admit genuinely new scripts under the existing standard, including
  consumer/risk/effect/cost record and required folder/size approval.

| Identity | Intended authority |
| --- | --- |
| HTTP app | Feature operations and atomic reminder creation; no Scheduler API, role passing or feature purge |
| Dispatcher function | Scoped due selection/handover, outbox delivery and job-queue send; no feature purge |
| Job function | Its queue settlement, durable processing and explicitly approved app effects; no cross-scope access |
| Migration/administration | Structural changes and grants, separately invoked |
| Fixed EventBridge trigger | Invoke only the approved dispatcher function/version binding, with scoped failure destination |

Reuse the existing AWS `change_sets.py`, `tasks.py`, `task_journal.py`,
`resource_reservation.py` and `cli.py` under
`scripts/04.deploy/shared/provider-adapters/aws/`, existing diagnostics,
`scripts/04.deploy/lifecycle/60-run/release-succession/` and scope-owned
activation/acceptance controls. Placement follows current capability/provider/
target-binding owners; do not invent another approval ledger or deployment engine.
Extend provider support for functions at that owner; `tasks.py` ECS support does
not magically implement Lambda operations. If an owner cannot govern the needed
operation, update the harness through its workflow before execution, not by
issuing ad-hoc AWS CLI commands. HTTP, dispatcher and worker must each have the
private DB and AWS API access their actual calls require. Reuse approved shared
endpoints; A2's runtime calls need SQS access but no Scheduler API endpoint.
The target must distinguish trigger submission failure from Lambda execution
failure and next-tick recovery; target acceptance is not dispatch completion.

**Exit:** declarations, reusable control changes and local negative proofs are
complete. This is not permission to mutate AWS.

## M7 Qualify and activate on AWS

**Goal:** obtain separate live baseline and feature acceptance.

Follow package custody and the current AWS plan/execute/acceptance owners.
Resolve the actual authority covering each effect; do not assume saving this
plan grants it or demand redundant approvals already covered by an explicit
bounded end-to-end instruction.

- [ ] Qualify finished packages; publish immutable source/digest/scan/custody.
- [ ] Obtain fresh account/region/target/scope, dependency, network, cost,
  permission and accepted-predecessor alignment.
- [ ] Review the exact resource and permission change through the governed route.
- [ ] Keep new minute triggers disabled until stores, functions, permissions and
  controls are ready. Inventory existing pending reminders and prove that their
  due times and identities survive activation without duplicate handover.
- [ ] Apply approved additive migrations/grants through their separate identities.
- [ ] Verify the fixed-trigger/function binding, job mapping and actual handler
  results; apply scoped version/digest bindings before enabling the trigger.
- [ ] Enable the approved path and prove a stored reminder reaches the harmless
  baseline job through minute dispatch, the existing outbox and the job queue.
- [ ] Prove actual Entity Smoke cleanup after the five-minute boundary, using
  explicitly owned synthetic records only.
- [ ] Prove duplicate/overlap safety, missed-tick recovery, failure between
  handover and publication, agreed cancellation and backlog/failed-delivery
  recovery under the approved live fault scope.
- [ ] Observe an agreed idle window and measured load: no minute-by-minute ECS
  launches or dedicated worker service, no unintended provisioned capacity;
  count minute dispatch/polling and measure function duration, connections and logs.
- [ ] Project monthly cost from observations with assumptions and free-tier
  treatment explicit; compare with M0/M6 ceilings. Report any miss before acceptance.
- [ ] Collect source/image/command/role-bound completion and recovery evidence;
  accept only through the canonical release owner.

EventBridge accepting a dispatcher invocation proves only target acceptance,
not successful scanning or job completion. Retain dispatch outcome, oldest due
reminder age, outbox publication, durable worker completion, backlog age and
failed-message signals. Prove both trigger-delivery and function-execution
failure visibility, because a submitted invocation can fail later.

Disabling the schedule does not stop queued jobs. Image rollback cannot
resurrect purged data. Reconcile an uncertain operation under its original
identity instead of blindly launching it again. Preserve baseline/user data.

**Exit:** both accepted live proof chains are evidenced, or the exact incomplete
boundary is reported without a completion claim.

## M8 Calendar scheduling and timezones

**Status:** deferred design milestone, not a hidden requirement to finish M0–M7.

An instant is one point in time stored as UTC. An elapsed duration such as five
minutes does not need a local timezone. A calendar intention such as daily
09:00 in Europe/Dublin needs a named zone and a recurrence policy. A date-only
value is not automatically midnight in the server's zone.

Before implementation decide:

- [ ] Add app-owned calendar intent and distinct occurrence identities to the
  selected database scheduling path. Separate recurrence calculation from the
  minute dispatcher that releases already resolved due instants.
- [ ] First supported rule, preferably daily at a named local time rather than
  unrestricted cron/RRULE.
- [ ] Missing/repeated local time policy, missed runs, catch-up and overlap.
- [ ] Update/cancel/version semantics and stale-delivery rejection.
- [ ] Timezone preference ownership and override precedence.
- [ ] Whether local preview/resolution is needed and its timezone-data strategy.
- [ ] Any expansion into tenant-specific schedules or durable job arguments.

A2 does not provide calendar scheduling merely by running every minute. For M8,
select and govern a suitable timezone-aware calculation library, its timezone
data/version updates and the offered gap/repeated-time policies; reuse existing
Core time contracts without hand-writing timezone tables or a cron engine.
Persist each computed occurrence with stable identity and atomically advance
the recurrence cursor so crashes cannot skip or duplicate an occurrence. Define
bounded catch-up, overlap, cancellation/version races and database growth.

The fixed AWS wakeup does not decide application DST policy. Do not silently
adopt EventBridge's missing-time skip/repeated-time once-only rules or promise
provider calendar behavior. Any later move to individually managed AWS schedules
requires a new approved ownership/migration decision and reliable coordination;
the unselected B notes are not authority to add that adapter now.

Compatibility constraints:

- Reuse Core offset support and UTC normalization.
- Core `TimeZoneId` is syntax-only; its tests intentionally accept
  `Mars/Unknown`. Validate concrete zone support at the selected implementation,
  not through an unreviewed global Core change.
- Current `isoDateTime` can normalize invalid calendar dates via `Date.parse`;
  existing consumers explicitly test rollover behaviour. Add a reviewed strict
  calendar-input boundary or govern a Core compatibility change.
- Store local recurrence intent separately from delivered UTC occurrence instants.
- Preserve millisecond due instants when storing and comparing generated occurrences.
- Local preview and occurrence generation must use the same approved timezone
  rules/data version and policy; host timezone must not change their result.

Required proofs before claiming recurrence/DST support:

- [ ] Dublin missing 01:30 on 2026-03-29 and repeated 01:30 on 2026-10-25.
- [ ] Non-DST and fractional-offset zones; host timezone independence.
- [ ] Twenty-four elapsed hours differs from the same local time tomorrow at DST.
- [ ] Invalid leap dates and unsupported zones rejected at the correct boundary.
- [ ] Month/year boundaries and explicitly chosen month-end policy.
- [ ] Unsupported gap/fold policy rejected rather than approximated.
- [ ] Stable identity for retries of one occurrence; distinct identities for
  different legitimate occurrences.
- [ ] Atomic occurrence creation/cursor advancement across crashes, update/cancel
  and late-delivery races, bounded outage catch-up and retained-row cleanup.

## Verification and evidence

Use the [existing check selector](../../../../scripts/repo/check-selection/README.md).
Do not run every listed package check after each edit. Relevant existing owners
include `platform-persistence-runtime`, `platform-workers-runtime`,
`sqs-queue-runtime`, `entity-smoke-runtime`, `runnable-program`, payload/
dependency assembly and the affected scope composition/acceptance checks.
The actual catalog and changed inputs, not this list, determine selection.
Register focused dispatcher, Lambda batch/packaging and fixed-trigger realization
checks through existing owners as those capabilities are implemented. Existing
SQS/ECS checks alone cannot establish their behavior.

Command shapes below contain placeholders, not paste-ready paths. First follow
the existing chat-owned preparation workflow before final verification.

```bash
bash scripts/repo/check-selection/script.sh --paths <actual-changed-paths> --development --execute-local --explain
bash scripts/repo/check-selection/script.sh --paths <actual-changed-paths> --explain
```

- Name each risk and the assertion that rejects a plausible wrong implementation.
- Budget each verification batch; record elapsed time and overrun honestly.
- Reuse evidence only while source, inputs, tools/artifact bindings and required
  freshness remain valid; state what invalidates each reused result.
- Close consolidated source/diagnostic review and freeze contributors' inputs
  before final integration; source changes reopen affected evidence.
- Distinguish controlled transport tests, real PostgreSQL, finished-image,
  publication, live-target and acceptance proof.
- Keep five-minute waits out of ordinary tests; live proof has its own deadline.
- Do not weaken tests, fabricate freshness or call deferred proof passed.
- Measure the complete normal delivery path before claiming its ten-minute
  engineering budget is met.
- Record script additions/removals/moves, recurring check/review effects and
  measured/unknown costs under the existing completion standard.

### Final first-release acceptance

Prepared seven-unit local verification passed on 2026-11-27 in 216.10 seconds:
`dynamodb-persistence-runtime`, `lambda-runtime`, `platform-persistence-runtime`,
`platform-workers-runtime`, `postgresql-connection-diagnostics`,
`scheduling-composition` and `sqs-queue-runtime`. Retained observation:
`.cache/test-runs/20261127T010726Z-2ae71754fe564f378eb7d4bf5bf6f69c/report.json`.
This is requested-check-only proof, not complete affected integration or any
package/live acceptance. The subsequent M4 fixture corrections reopen only
affected input identities; reuse the unchanged passing units through the trusted
selector. Budget the eventual full affected local pass at ten minutes and record
any overrun without skipping required checks.

- [ ] PostgreSQL owns individual reminders/due timing; infrastructure owns fixed wakeups.
- [ ] No runtime Scheduler CRUD adapter, provider registration or notification stage exists.
- [ ] Entity change and reminder commit together with actual write checks.
- [ ] Missed/overlapping ticks, overdue backlog and agreed cancellation semantics
  have tested bounded recovery under stable identity.
- [ ] Due handover and outbox insertion are atomic and permitted-state guarded.
- [ ] Dispatcher and relay are bounded and recover pending work without new reminders.
- [ ] Real SQS delivery drives on-demand functions and existing durable workers.
- [ ] Retry, acknowledgement and terminal failure form one coherent contract.
- [ ] Feature failures cannot become successful worker completion.
- [ ] Restore/re-delete races cannot cause early physical deletion.
- [ ] Baseline and Entity Smoke share implementation, not copied machinery.
- [ ] Programs/images/configuration/permissions/declarations agree.
- [ ] Local, real-engine and finished-image proofs pass.
- [ ] Authorized AWS baseline and feature acceptance both pass.
- [ ] Disablement, in-flight work and recovery are demonstrated.
- [ ] No dedicated idle scheduler/worker or per-minute ECS check was introduced.
- [ ] Idle/expected-load cost and latency budgets have evidence, including network,
  DB, queue polling and minute scans; monthly estimates are not claimed as bills.
- [ ] Documentation truthfully separates one-off and deferred calendar support.
- [ ] No duplicate IDs/clocks/registries/outbox/deployment engine or mandatory
  core-platform base-image dependency was introduced.

## Progress logging and handoff

Use this plan and the existing active session record, not a new progress database,
script or registry. At each meaningful checkpoint:

1. Update the dashboard status and owner. Use `Not started`, `In progress`,
   `Blocked`, `Complete` or `Deferred`; keep `Awaiting approval` for an actual
   undecided authority/design gate.
2. Tick only acceptance items supported by the required stage of evidence.
   Partial local progress is not package/live completion.
3. Append a concise dated entry below identifying milestone, authority,
   source/files, review, evidence, remaining work and next action.
4. Put branch/worktree, commits, unresolved operations and authority references
   in the active session; point it to this plan rather than duplicating milestones.
5. On handoff, identify the next incomplete item and any running process or
   uncertain remote operation. Reconcile it before retrying.

Suggested entry shape, using only applicable fields:

```text
Date/time UTC:
Milestone and status:
Executor/reviewer:
Authority or decision reference:
Source revision and changed paths:
Completed change and acceptance items:
Evidence by stage: command/report, outcome, elapsed time, reuse/invalidation:
Review corrections and disposition:
Remaining gap/blocker and pending operation/process:
Next permitted action:
Growth/cost statement when script or recurring-check scope changes:
```

Do not mark a milestone complete with only a prose claim or successful task
submission. The evidence must support its exit criteria. If the user pauses or
replaces the task, record that accurately and follow the current instruction.

### 2026-11-26 Plan recorded

The entries through Initial cost estimate recorded below preserve the decisions
and evidence at those checkpoints. The later A2 selection supersedes their
operative next actions and does not invalidate their recorded arithmetic.

- Status: draft saved for handoff; M0 awaits design and implementation approval.
- Scope: this plan and the existing runtime plan's scheduler discovery/status
  text; session bookkeeping points to the plan. No runtime or cloud changes.
- Baseline: `67d4d652bc1e3053dd513d1cc9864b65e6209ad2`.
- Inventory: prior read-only runtime, deployment and time-model reviews identified
  atomic-write, result-propagation, purge-race and queue-driving gaps above.
- Documentation review: root self-review and independent plan_review completed;
  the parent plan's remaining future-tense storage wording was corrected. No
  implementation or live proof follows from this review.
- Structural verification evidence: see the originating session's
  Scheduler plan documentation verification entry for final commands, outcomes
  and timings. Budget: two minutes; named risks are invalid metadata, broken
  handoff links, missing milestones and contradictory process/command guidance.
- Growth/cost: no script source added, removed or moved; no new automated check,
  recurring review requirement or progress machinery. Documentation verification
  is scoped to metadata, links, process/command drift and whitespace.
- Next action: review D1–D8 and authorize the desired implementation boundary,
  then assign M0. Saving this plan does not grant that authority.

### 2026-11-26 Operating-cost revision

- Authority: user said operating costs are the priority and asked to revise the
  plan after comparing A and B. Selected B for planning; code/cloud authority
  remains absent and M0 remains open for detailed budgets/runtime approval.
- Replaced the periodic ECS due-scanner/idle-worker proposal with individual AWS
  schedules, a runtime EventBridge adapter and proposed on-demand Lambda/SQS
  execution. Adapter work moved into M1; calendar rules remain M8.
- Added registration recovery, provider lifecycle/version handling, Lambda
  packaging/realization proof and an idle/expected-load/burst cost gate. Preserved
  atomic entity intent, safe purge, outbox/worker reuse and independent proofs.
- Source remains the recorded baseline; no implementation milestones are checked.
  The parent runtime-plan summary is reconciled with this direction.
- Review: root self-review and independent plan_review covered the complete plan
  and linked summary. Corrected obsolete polling wording, uncertain-registration
  recovery, M4/M5 proof order and maintenance role-passing authority. Added the
  ADR 0027 ownership reconciliation before implementation. Structural evidence belongs in the session
  log under Scheduler operating-cost plan verification. Structural check budget:
  three minutes, excluding this prose design review; no cloud or runtime tests.
- Growth/cost: documentation only; no script source or recurring checks changed.
  Future capability-specific proof is part of implementation, not installed now.
- Next action: resolve M0's numeric cost/lateness/recovery and function-runtime
  decisions, then obtain implementation authority; do not restart the A/B debate.

### 2026-11-26 Initial cost estimate recorded

- User authorized the next estimation step with "proceed"; no implementation or
  AWS account mutation was authorized or performed.
- Recorded regional public price-list evidence, repository-only target baseline,
  two-scope idle/10k/100k/20m scenarios, free-allowance and duration sensitivities,
  missing full-cost inputs and the cheaper unselected A/Lambda comparison.
- Corrected the inference that B is necessarily cheapest: private endpoint hours
  dominate its low-volume subtotal. The selected direction remains B pending
  the user's trade-off; implementation authority and numeric budgets remain open.
- Review/evidence: root arithmetic and source review, scheduler_inventory target
  inventory and plan_review count/comparison review. Final documentation checks
  are recorded in the session under Scheduler cost estimate verification.
- Documentation only; no scripts, runtime, deployed resources, commits or pushes
  changed. No newly installed recurring checks or reviews. Structural budget:
  three minutes, excluding price research and prose review.

### 2026-11-26 A2 selected and first design requested

- User selected A2 and requested its machinery, then asked to see the design
  before code. Local build intent is recorded; the bounded first increment
  awaits agreement, and no autonomous-increment or cloud authority is inferred.
- Current milestones now reuse PostgreSQL reminders and the callable due pass,
  add bounded dispatch/relay and one queued Lambda worker per scope, and retain
  atomic entity/reminder writes, purge safety and independent baseline/app proof.
- Runtime Scheduler CRUD, provider registration, notification infrastructure and
  the separate maintenance function are removed from operative scope. A1/B cost
  and progress evidence remains historical. Calendar/DST work remains M8.
- This revision changes the two linked plans only. No implementation milestone
  is complete; no runtime, deployment, session log or test execution is changed
  by this delegated documentation edit. Root owns final review and scoped checks.
- Next action: explain proposed `schedule-dispatch.ts` and the existing owners
  it composes, then obtain agreement for that exact local code increment.

### 2026-11-26 First bounded dispatcher implementation

- Authority: user `yes` after the first-slice design. Implemented only the
  provider-neutral composition and its exports, diagnostic definitions/derived
  JSON, tests, README and existing review record. No deployed caller yet.
- Reuse review: existing due pass, transactional store port, relay, shared
  numeric reader, IDs, clocks and guarded diagnostic delivery are retained.
  The README's obsolete future-adapter claims were corrected at their owner.
  No script-source file, dependency, registry, test runner or recurring check
  was added; the existing runtime discovery includes the new tests.
- Source review: root reviewed the whole change and delegated test file;
  plan_review independently reviewed implementation/failure semantics.
  Corrections consolidated before final checks: use only the checked numeric
  result; constructor configuration evidence travels on the thrown TypeError,
  while runtime boundary observations use the optional diagnostic callback.
- Material counterexamples: zero new reminders must not suppress old-outbox
  retry; an earlier publication must not be replayed after a later store failure;
  send/marker failure must not count as publication; count bounds must count
  attempts; a later config read must not replace its captured checked value;
  diagnostic builder/selection/sink faults must not replace original errors or
  lose selected source evidence. Exact assertions live in the connected
  schedule-dispatch runtime test and public type-level test.
- Deliberate limits: fail-fast due errors, no partial counters on failed
  Results, no interruption inside existing dependency calls, no real-database
  or cloud proof. Full M1 job resolution/fairness/deadline and later milestones
  remain open. There is no operational cost change until a target consumes this.
- Generated persistence catalogue is source-derived using the existing
  exporter; historical definitions remain unchanged. After input freeze and
  governed preparation, the registered `platform-persistence-runtime` and
  `diagnostic-catalog-readers` checks both passed. The focused selector took
  198.319 seconds (159.127 seconds executing checks), within its ten-minute
  budget. Evidence is retained in
  `.cache/test-runs/20261126T223133Z-e7f2a1f67015471ba5d88a55e6a6a937/report.json`.
- Initial declared-impact local verification took 1,871.461 seconds, exceeding
  the ten-minute estimate. The chosen fallback TMPDIR was inside the
  repository because `/tmp` was full; this violates existing acceptance-rehearsal
  and dependency-destination isolation guards. The acceptance failure was
  reproduced; source review also establishes the conflicting destination for
  Entity Smoke composition and the persistence payload fixture. Keep those guards
  unchanged. Corrected proof used external `/var/tmp` scratch and reused
  successful results only where the existing runner validated their inputs.
- The initial scope-inventory check also failed. Its three retained acceptance
  records passed individual read-only validation; no record-content regression
  was reproduced. Its parent folds child failures and a 30-second timeout into
  one finding, so timeout was plausible but not proven. The unchanged aggregate
  passed in the corrected final run. No safety guard, receipt or scope was edited.
- Final path-selected integration passed: 25 required local results, 21 reused
  and four executed, no findings or pending required checks; coverage is
  `complete-declared-impact`. The corrected selector took 352.682 seconds,
  including 265.412 seconds executing checks. Retained observation:
  `.cache/test-runs/20261126T231150Z-bf04d910176a49e0b3552232069ca39c/report.json`.
  Four retained hygiene checks and ten later-stage obligations remain deferred,
  not passed. This is not package qualification, real-database atomicity, live
  target readiness or AWS acceptance proof.
- Proof reuse is invalidated by changes to each registered check's declared
  source, runtime/configuration identity or verification contract. Only progress
  records changed after final integration; runtime and diagnostic inputs stayed
  frozen. The existing metadata check and whitespace review cover those final
  record edits without replaying unchanged runtime checks.
- First approved slice is complete; M1 and all later implementation milestones
  remain open. Next proposed increment: add a cooperative stop between individual
  reminders inside the existing due pass, with its tests, before Lambda wiring.
  Obtain agreement for that boundary; do not silently start it.

## Vendor references

External behaviour reviewed on 2026-11-26. Recheck the relevant official
contract before implementing provider-dependent behaviour.

- [EventBridge Scheduler overview](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html):
  target delivery is at least once; target acceptance is not app completion.
- [Schedule types and DST](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html):
  60-second invocation precision; missing local cron times skipped, repeated
  local cron times invoked once; a rate day is elapsed 24 hours.
- [Templated targets](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-templated.html):
  target operation and execution-role permissions must match the chosen target.
- [Schedule deletion](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule-delete.html):
  retained for historical B lifecycle analysis, not A2 runtime implementation.
- [CreateSchedule API](https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html):
  retained for historical B registration analysis; A2 uses an infrastructure-owned
  fixed trigger rather than runtime creation of individual AWS schedules.
- [Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) and
  [partial batch failures](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html):
  managed polling/settlement and record-level retry behavior.
- [SQS mapping scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html):
  polling and concurrency choices have request and capacity consequences.
- [Lambda container images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html):
  runtime-interface requirements differ from ordinary ECS commands.
- [EventBridge pricing](https://aws.amazon.com/eventbridge/pricing/),
  [Lambda pricing](https://aws.amazon.com/lambda/pricing/) and
  [Fargate pricing](https://aws.amazon.com/fargate/pricing/): reference assumptions
  for the operating-cost worksheet; verify region, runtime variant and account
  allowances when producing the implementation estimate.

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.iaas-release-control-progress
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre, agentic]
kind: plan
purpose: Track accepted IaaS delivery outcomes and a fixed remaining acceptance backlog with explicit changes between runs.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->

# IaaS release-control progress ledger

## Active scope — B02, 2026-09-30

The user requested an [MVP with backlog-first intake](iaas-release-control-mvp.md).
M1–M5 are now the active delivery queue for one controlled AWS staging path.
New checks are deferred unless an evidenced blocker, unsafe-effect or material-
drift risk requires them. The R1–R8 register below remains the full-roadmap
baseline; it is not all prerequisite work for this scoped MVP. No R checkpoint
is marked complete or exempt by deferral. B02 retained 16 accepted deliveries;
B03 adds three bounded components; B04 accepts the selected store conformance
component. Their exact boundaries are recorded below.

## Current position — P16 passed; P17 build-export refusal, 2026-10-02

P01–P15 remain source-closed on `main` at their recorded refusal and contract
boundaries. P16 run `37067617564` passed on exact revision `11bf851d`: 2,212
tests in 75 suites, zero failures and metadata validation for 73 files. Earlier
P16 runs `37064889309` and `37061953789` passed on superseded revisions.

P17 run `37066022523` installed bubblewrap and passed source checks, OIDC,
ECR login and locked input acquisition, then refused the mandatory namespace
probe with `local-build-isolation-unavailable`. No image was pushed and no
service changed. A later review found two more deterministic host defects before
the next attempt: the selected AppArmor package version `.9` is absent from
Ubuntu's signed stable Noble indexes, and the runner's classic Docker store
cannot provide the distinct image manifest and configuration digests required
by the handoff. The private qualifier also could not see the Buildx action's
per-user plugin or separate builder.

The bounded repair uses signed-index-available AppArmor package `.8`, whose
extracted profile bytes match the reviewed `.9` profile. The package and
profile SHA-256 checks and mandatory sandbox probe remain. On the disposable
runner, the workflow refuses an existing daemon configuration, selects and
verifies the containerd image store before base acquisition, uses the
same-daemon Docker builder, and exposes the action-selected Buildx binary to
the qualifier's otherwise empty Docker configuration. Exact Docker and Buildx
versions are checked before qualification. Existing source, image, scan and
attestation gates stay in place. Fresh P16 and P17 must prove this revised
source; local validation is not hosted evidence. The selected blueprint binding
is repinned.

The repaired source was merged at `efbd4c99998c8aa7217e28a7c9323df686252703`.
P16 main run `37070417080` passed on that exact revision: 2,214 tests in
75 suites, zero failures and 73 metadata files. P17 run `37071477462` passed
the revised host, source and AWS input steps but refused during the image build
with `local-container-image-id-invalid`. Buildx reported command success;
the qualifier then found no valid image ID file. No image was published and no
service changed. The current follow-up distinguishes a missing/empty image ID
from absent build manifest/configuration metadata and accepts a configuration
digest only when bound by the Buildx manifest descriptor annotation. It does
not treat an unverified ID as successful. Fresh P16 and P17 are required.

P18 remains open even if P17 publishes: the current publisher does not create
the signed scan predicate or observed build-material statement required by the
artifact-admission verifier. No successful P18 admission is claimed from a
workflow result alone. P19 remains partial: a fresh administrator-only assessment on 2026-10-02
verified the expected account and Foundation stack, then classified one
`RelationalDatabaseParameterGroup` `remove` difference as the reviewed
representation signature with effective TLS still required. The historical
egress correction is complete. CloudFormation remains drifted, so passive
readiness still blocks; classification does not clear P19. A reviewed treatment
and fresh passive reconciliation are required.

M1–M4 remain partial and M5 open. Next: verify and commit the build-export
classification repair, run P16 on its exact merged revision, then attempt P17 once. P18 producer work
and P19 drift treatment determine whether P20 can be reviewed. Scope change:
none; no new P-row or AWS resource change.

## Phase 1 — fixed MVP closure ledger

**Current closure state: P01–P15 source-closed at their recorded source
boundaries; P16 passed for `efbd4c99` and must be rerun for the current P17
repair; P19 partially observed; 0/33 live-proven.** The 20 accepted U01–U20 delivery units are
prerequisite credit and are not counted again. This is the only completion
ledger for the MVP. It ends when the existing PostgreSQL Stage 6 route is safe
to propose for its own execution approval; it does not execute or complete
Stage 6 itself.

The former L01–L49 draft is withdrawn. It incorrectly made optional
full-programme architecture a prerequisite for this MVP. It provides no
completion credit and must not direct further work.

| ID | Fixed closure check | Depends on | Evidence required to close | Status at B05 | Approval boundary |
| --- | --- | --- | --- | --- | --- |
| P01 | Freeze the selected staging release graph: resources, commands, task profiles, owners and recovery routes. | U17 | Compiler rejects an unowned, hidden or changed selected subject. | Complete — source on `main` | Source authorized |
| P02 | Bind current baseline separately from the intended source, image and task revisions. | P01 | Swapped, missing or mutable identity is refused. | Complete — source on `main` | Source authorized |
| P03 | Define the closed qualification-operation input, including authority expiry, cost/attempt limit and cleanup route. | P02 | Extra, unsafe or missing fields fail validation. | Complete — source on `main` | Source authorized |
| P04 | Admit only current, complete 17-gate evidence; refuse source-only, stale or absent authority. | P03 | Positive and tampered admission fixtures pass and fail as expected. | Complete — source refusal on `main` | Source authorized |
| P05 | Record separate start and stop intent before a selected provider effect. | P03, U20 | Adapter fixture cannot issue either effect before its intent exists. | Complete — source on `main` | Source authorized |
| P06 | Bind one request token and validate returned task, cluster, revision and image; emit redacted evidence only. | P05 | Lost-response and wrong-identity fixtures fail without a second request or leaked handle. | Complete — source on `main` | Source authorized |
| P07 | Recover intent after restart, fence an expired writer and reopen scope only after verified closure. | P05–P06 | Restart, expiry and unresolved-outcome fixtures fail closed. | Complete — source on `main` | Source authorized |
| P08 | Add the minimum selected journal/evidence-store infrastructure contract, with exact region, encryption, retention and recovery settings. | U20, approved policy | Template/schema tests reject a broadened resource or changed retention/recovery setting. | Complete — source on `main` | Source complete; creation separate |
| P09 | Add the least-privilege selected IAM contract for the journal and evidence operations. | P08 | Negative policy fixtures reject unrelated resources or broad actions. | Complete — source on `main` | Source complete; IAM application separate |
| P10 | Implement bounded authenticated selected AWS transport and immutable evidence readback. | P08–P09 | Malformed, denied and unknown responses fail closed; mismatched evidence is refused. | Complete — source on `main` | Source complete; live transport separate |
| P11 | Route the existing candidate start/observe/stop wrapper through P04–P10. | P04–P10 | Direct candidate effect without admission/intent is refused in focused tests. | Complete — source on `main` | Source complete; live receipts separate |
| P12 | Route the existing relational bootstrap, migration, relay, worker and restore wrappers through the same boundary. | P04–P10 | Focused caller tests refuse a direct relational effect or replay. | Complete — source on `main` | Source complete; live receipts separate |
| P13 | Refuse every other selected legacy mutation route and document the supported release/recovery command. | P11–P12 | Static caller test finds no permitted selected-path bypass. | Complete — source on `main` | Source complete; release remains blocked |
| P14 | Wire the protected hosted workflow to the supported immutable command and inputs. | P13 | Workflow tests reject mutable refs, unbound image and alternate command. | Complete — source on `main` | Source prepared; hosted run separate |
| P15 | Run the focused source regression and record the release-control evidence for P01–P14. | P01–P14 | Relevant positive and negative tests pass at one recorded source revision. | Complete — source evidence on `main` | Source evidence recorded; hosted validation separate |
| P16 | Run the prepared hosted source-validation workflow once on the reviewed revision. | P14–P15 | Hosted check passes with pinned actions, locked dependencies and timeout. | Partial — run `37070417080` passed at `efbd4c99`; rerun required for current P17 repair | Hosted run approval |
| P17 | Publish the exact reviewed image without a substitute rebuild. | P16 | Registry digest, source revision and build receipt agree. | Blocked — run `37071477462` refused invalid build-export image ID before publication; classification repair awaits P16/P17 qualification | Publication approval |
| P18 | Admit the published image with current SBOM, scan and provenance/signature receipts. | P17 | Missing, stale or mismatched receipt blocks admission. | Open — signed scan and observed-material producer integration required | Hosted/publication approval |
| P19 | Refresh passive target reconciliation: selected account, region, identities and drift. | Current AWS access | Fresh read-only report binds the target and rejects stale drift. | Partial — account/artifact observed; fresh known parameter-group drift classification and TLS check passed, but passive verdict remains blocked | Read-only approval |
| P20 | Generate and review the immutable selected change/effect, cost, rollback and cleanup plan. | P17–P19 | Unexpected resource, permission, destructive action, cost or scope blocks the plan. | Open — read-only AWS | Change-plan approval |
| P21 | Provision the approved minimum journal/evidence resources and selected permissions. | P08–P10, P20 | Inspection proves exact account/region, encryption, retention and permissions. | Open — AWS effect | Resource/IAM approval |
| P22 | Prove competing-writer refusal, restart recovery and evidence readback against the provisioned store. | P21 | Live receipts show one writer only and unresolved outcomes fail closed. | Open — AWS effect | Controlled recovery approval |
| P23 | Produce the current target-readiness report: identity, IAM, configuration/secret shape, network/TLS, dependencies, capacity/cost and evidence path. | P18–P22 | Each required check is current and a missing prerequisite blocks readiness. | Open — AWS read/validate | Read-only or no-effect approval |
| P24 | Prove the exact candidate image can start, identify itself, become healthy and end with a terminal receipt. | P23 | Receipt binds image, task revision, identity, health and terminal state. | Open — AWS task | Candidate-task approval |
| P25 | Run the existing bootstrap no-effect preflight. | P23 | Identity, configuration shape, network/TLS and evidence path pass without mutation. | Open — AWS no-effect | Specific approval |
| P26 | Run the existing migration no-effect preflight. | P23 | Current migration prerequisites pass without database mutation. | Open — AWS no-effect | Specific approval |
| P27 | Run the existing relay no-effect preflight. | P23 | Queue, network/TLS and evidence prerequisites pass without relay effect. | Open — AWS no-effect | Specific approval |
| P28 | Run the existing worker no-effect preflight. | P23 | Queue permissions and evidence prerequisites pass without settlement. | Open — AWS no-effect | Specific approval |
| P29 | Run the existing isolated restore no-effect preflight. | P23 | Restore identity, access, TLS and observation path pass without restore mutation. | Open — AWS no-effect | Specific approval |
| P30 | Compile one current, immutable readiness record from P24–P29 and the approved change plan. | P20, P24–P29 | Missing, stale or wrong-release proof prevents an execution proposal. | Open — source/read-only | No effect; execution remains separate |
| P31 | Rehearse controlled candidate start, health observation and stop through the provisioned control path. | P22, P30 | AWS receipts show intent, exact identity, health, stop and cleanup. | Open — AWS effect | Candidate/recovery approval |
| P32 | Apply the reviewed service change and prove healthy promotion plus the declared rollback or forward-repair route. | P20, P31 | Only reviewed effects occur and the declared healthy final state is verified. | Open — AWS effect | Service/recovery approval |
| P33 | Close the rehearsal: prove denial/unknown-outcome handling, alert receipt, final target health, cost/ownership reconciliation, cleanup and safe evidence retention. | P31–P32 | Reconciliation and receipts show no unresolved operation or unapproved ongoing cost. | Open — AWS effect/read | Recovery, monitoring and cleanup approval |

### Fixed finish line and change control

**Phase 1 is live-proven only when P01–P33 are closed.** It provides one
repeatable controlled release path and makes the existing Stage 6 task graph
eligible for a separately approved execution proposal. PostgreSQL Stage 6 is
then completed against its own product-plan criteria; its five actual database
operations are intentionally not disguised as incomplete IaaS-MVP rows.

The 33 IDs, their closure tests and this finish line are fixed. A defect belongs
inside its existing P-row only when it prevents that row from passing. A newly
discovered item goes to Phase 2 by default. Moving it into Phase 1 requires a
recorded demonstrated blocker or unsafe-effect/drift path, the smallest remedy,
and the user’s approval of a dated ledger revision. An agent cannot add a row,
test or acceptance condition merely because it seems prudent.

At every run, report: P-rows attempted and closed; exact evidence and source
revision; the remaining count by status; the one next reachable row; every
external approval awaiting action; and `scope change: none` or the approved
revision. Row counts measure closed acceptance checks, not equal-sized effort;
external approval and AWS execution time are reported separately rather than
turned into a false delivery estimate.

## Phase 2 — complete IaaS release-control programme

Phase 2 begins only after Phase 1 is live-proven or after the user explicitly
reprioritizes it. It is the remaining complete scope of the original plan, not
hidden MVP work. Its detailed acceptance criteria stay in the stable
[fixed remaining acceptance backlog](#fixed-remaining-acceptance-backlog) and
the [original implementation plan](../../../.agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md).

| Phase 2 area | Complete scope retained for later |
| --- | --- |
| R1 | Whole-estate coverage, action/default/tool semantics and remaining contracts. |
| R2 | All artifact families, dependency closure and command/runtime qualification. |
| R3 | General durable operation control, controller bootstrap and broader recovery. |
| R4 | AWS adapter coverage for all supported profiles and environment permutations. |
| R5 | General release decisions, policy gates and workflow coverage. |
| R6 | Repository-wide caller migration, wrapper retirement and documentation conversion. |
| R7 | Wider staging qualification beyond the selected MVP graph. |
| R8 | Scheduled assurance, dashboarding, periodic recovery and the 28-day observation window. |

No Phase 2 row blocks P01–P33 unless it is formally promoted under the change
control rule above. Other providers remain Phase 2/future work.

## Historical position — baseline B01, 2026-09-30

**16 delivery units accepted; seven accepted since the 15–20 estimate.**
The latest implementation checkpoint is `2b940bd4a2df364b3348151abc2c938f28b859cd`.
These units establish tested source and local execution capabilities. A complete
controlled AWS deployment is still unavailable. No full-programme completion
percentage or remaining-slice forecast is established by these counts.

The [implementation plan](../../../.agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md)
remains authoritative for requirements. This ledger is its progress index.
It preserves those requirements and the source-only authorization boundary.
The 17 release acceptance gates, implementation phases, delivery slices and
remaining checkpoints below are different measures and must not be conflated.

| Remaining milestone | Accepted capability credited | Status at B01 |
| --- | --- | --- |
| R1 — Account for the estate and finish contracts | Compiler, collectors, caller graph, contract checks | Partial |
| R2 — Qualify exact artifacts and their effects | Locked real builds, earlier local containers/jobs, compiler-derived exports, verifier conformance | Partial |
| R3 — Make operation control durable in production | Local durable records/locks and real interruption recovery | Partial |
| R4 — Integrate AWS operations and prerequisites | Existing scripts available for reuse; no new AWS adapter qualification accepted | Open |
| R5 — Connect release decisions and workflows | Matrix compiler, result-consumption refusals, prepared source CI | Partial |
| R6 — Complete existing-caller migration | Generated adoption proposals and caller graph | Partial |
| R7 — Qualify the staging release graph | Local proofs supply inputs; no live target qualification accepted | Open |
| R8 — Establish continuous assurance | Requirements defined; activation and observation unproven | Open |

All eight milestones remain open at programme level. Partial means specific
accepted work exists, not an estimated percentage. Checkpoint completion within
a milestone is progress and must be reported even before the milestone closes.

## Accepted delivery register

These accepted scopes stay credited. An invalidated receipt requires a named
requalification action; it does not erase the implemented capability or create
a new delivery unit merely for rerunning it. Evidence proves its recorded source
and environment, not every later revision.

| ID | Accepted outcome | Durable evidence | Remaining milestone helped |
| --- | --- | --- | --- |
| U01 | Versioned release definition and ordered 17-stage compiler | [Plan acceptance](../../../.agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md#8-immediate-next-slice) | R1, R5 |
| U02 | Independent source discovery and initial adoption proposal | [Discovery record](release-control-source-adoption/README.md) | R1, R6 |
| U03 | Finding triage and selected staging caller coverage | [Triage record](release-control-source-adoption/2026-09-29-triage-and-callers/README.md) | R1, R6 |
| U04 | Repeatable source validation and authority-consumption guard | [Validation record](release-control-source-adoption/2026-09-29-source-validation/README.md) | R1, R5 |
| U05 | Selected operation contracts and dependency observations | [Contract record](release-control-source-adoption/2026-09-29-operation-contracts/README.md) | R1, R3 |
| U06 | Structural workspace build/artifact accounting | [Structural build record](release-control-source-adoption/2026-09-29-workspace-builds/README.md) | R2 |
| U07 | Locked real compiler execution and selected runtime tests | [Locked build record](release-control-source-adoption/2026-09-29-locked-builds/README.md) | R2 |
| U08 | Exact local final-container startup, health, shutdown and cleanup | [Container record](release-control-source-adoption/2026-09-29-local-containers/README.md) | R2 |
| U09 | Reusable packaged finite-job conformance | [Finite-job record](release-control-source-adoption/2026-09-29-finite-jobs/README.md) | R2, R3 |
| U10 | Independent bootstrap/migration effects against disposable dependencies | [Effect record](release-control-source-adoption/2026-09-29-dependency-effects/README.md) | R2 |
| U11 | Genuine offline cryptographic artifact-evidence verification | [Admission record](release-control-source-adoption/2026-09-29-artifact-admission/README.md) | R2 |
| U12 | CloudFormation structural references and unresolved provider inputs | [Reference record](release-control-source-adoption/2026-09-29-infrastructure-references/README.md) | R1 |
| U13 | Local durable journal, evidence, leases and fencing | [Store record](release-control-source-adoption/2026-09-30-control-store/README.md) | R3 |
| U14 | Aggregate caller graph and adoption-delta reconciliation | [Caller record](release-control-source-adoption/2026-09-30-estate-callers/README.md) | R1, R6 |
| U15 | Durable finite-operation recovery after real process interruption | [Recovery record](release-control-source-adoption/2026-09-30-finite-recovery/README.md) | R3 |
| U16 | Compiler-derived package exports replacing three handwritten maps | [Export record](release-control-source-adoption/2026-09-30-workspace-exports/README.md) | R1, R2 |
| U17 | Current selected-target blueprint: 13 subjects, nine task groups, all 17 gates and immutable source bindings | [MVP acceptance](release-control-source-adoption/2026-09-30-mvp-selected-path/README.md) | M1; R1, R5 |
| U18 | Same-host exact qualified-image publication handoff and bounded selected publisher drift controls | [MVP acceptance](release-control-source-adoption/2026-09-30-mvp-selected-path/README.md) | M2; R2, R5 |
| U19 | Fixed task database preflight, passive AWS inspection and immutable deployed task revision binding | [MVP acceptance](release-control-source-adoption/2026-09-30-mvp-selected-path/README.md) | M3 and part of M4; R4 |
| U20 | Versioned selected operation and conditional shared-store/evidence conformance, with no live authority | [Store conformance record](release-control-source-adoption/2026-09-30-selected-store-conformance/README.md) | R3, R5; MVP M4 |

U10–U16 account for the seven deliveries since the earlier estimate: two artifact/
effect capabilities, three discovery/build relationship capabilities, and two
durable-control/recovery capabilities. AWS integration and live qualification
were not delivered by those local proofs. The old 15–20 and subsequent 12–17
forecasts were not based on a stable task decomposition and are superseded as
progress measures. There is no defensible conversion from seven accepted units
to seven equal units removed from those forecasts.

## Fixed remaining acceptance backlog

IDs below stay stable between runs. These are acceptance checkpoints, not a
new estimate of slices, days or equal amounts of effort. A batch can finish
several checkpoints; a checkpoint can require several bounded delivery units.
Each table states what must become true, rather than allowing an indefinite
"more foundation work" queue. Existing supported paths and plan profiles bound
the subject set; unsupported findings remain visible until resolved or excluded
with evidence. New scope requires an explicit change entry.

Status is `open`, `partial` or `complete`. Complete requires contract/schema,
implementation, positive/negative checks, wrapper where needed, documentation,
local verification, evidence and session entry appropriate to that checkpoint.
A document alone cannot close an execution or authority checkpoint. Source
preparation and live activation must be reported separately where both occur.

Dependencies on a milestone mean its relevant interface or accepted prerequisite,
not every live qualification in that milestone. In particular, source-complete
release-command support enables the narrow R3.3 bootstrap; bootstrap execution
then enables its self-hosted successor and later hosted/live acceptance. Neither
requires a future fully qualified release as its own starting authority. External
authorization remains separately required, so this does not invent a bootstrap
exemption from safety checks.

### R1 — Estate coverage and remaining contracts

Plan trace: Phase 0; Phase 1; Phase 2; readiness decisions 3, 4, 6, 7.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R1.1 / partial | Versioned supported-estate catalog and handoff cover every existing active/dormant supported path, with accountable owner and reviewed migrate/retire/temporary-compatible/historical disposition. Exclusions have caller/build proof; temporary paths have expiry. New discoveries join a visible delta. | U02/U03/U12/U14; owner decisions required. Current cloud observations belong to R7.1. |
| R1.2 / partial | All supported workflow action instances resolve to immutable source/metadata and entrypoints/hooks; supplied inputs, omitted inputs/defaults, outputs, conditions, permissions and environment are reconciled. Unproved action/tool behavior remains a named obligation. Changed/missing material is refused. | U05; source acquisition only, no action execution or hosted activation. Next delivery unit. |
| R1.3 / partial | Remaining script/process launches, package/build callers, generated inputs, workflow boundaries and source infrastructure/configuration/identity edges reconcile with the declared graph. Both product and RAG rulebook image/task/sidecar families, image command inheritance and rendered infrastructure imports/parameters are explicitly included. No unresolved supported source gap or undocumented exclusion remains; final-image/provider subjects are assigned downstream. Hidden-caller/false-exemption mutations fail. | R1.1/R1.2; U12/U14/U16. Later runtime/provider proof is not inferred from source syntax. |
| R1.4 / partial | All four record schemas, version migration, the fixed static-artifact/inspection/service/finite-job/queue-consumer/infrastructure/migration/restore/scheduled profile families, adapter protocol, scope-compatible evidence/identity rules and every required cross-cutting contract have valid/invalid fixtures. Includes risk, configuration, compatibility, migration, capacity, telemetry, diagnostics, cleanup, exceptions, lifecycle, governance resolver and failure injection. Independent review covers every Phase 1 exit scenario. | U01/U04/U05/U13; reuse existing schemas. Reviewed interim governance baseline and named accountability cannot be invented. Runtime enforcement belongs to R3/R5. |

### R2 — Exact artifact and task qualification

Plan trace: Phase 3; supported artifact obligations from Phase 2.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R2.1 / partial | Current final image/artifacts are rebuilt and qualified using the accepted compiler-derived exports, pinned toolchain/base/platform/dependency closure and exact produced digest. Entrypoint, payload/assets, user, working directory, environment shape, readiness, shutdown and cleanup receipts match those bytes. Stale outputs and source fallbacks are refused. | U07/U08/U16. U16 changed generated bytes: renew affected container proof; historical U08 receipt does not qualify them. |
| R2.2 / partial | Every supported executable in the catalog has its actual packaged command and independent semantic completion proof, including server, bootstrap, migration, relay, worker and restore; sidecars/dependencies and provider-shaped inputs are accounted for. Mixed-version/API/queue/schema/cache/flag compatibility and expand/migrate/backfill/validate/contract safety have required recovery tests. | R1.3/R1.4/R2.1; U09/U10. Disposable local proof remains distinct from managed-provider proof. |
| R2.3 / partial | Real candidate artifacts have a produced SBOM with component completeness checked against the qualified artifact/dependency inventory, vulnerability scans, provenance, resolved base identity and required signatures from accepted producers. Missing or unresolved component coverage fails admission. Trust identities, thresholds, exceptions, freshness and scanner versions are reviewed inputs. Promotion preserves the exact qualified digest and rejects altered/stale material. | U11 verifies cryptographic checking only. Producer/trust policy needs review; publishing/promoting externally requires approval. R5 consumes these receipts. |

### R3 — Durable operation control and bootstrap

Plan trace: Phase 4; readiness decisions 1, 2, 5, 8; Phase 1 interruption rules.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R3.1 / partial | Production journal/lease/fence and evidence-store implementations preserve immutable intent, authenticated safe evidence and recovery across competing hosts, stale owners, interrupted writes and store failure. Encryption/access, retention, backup/restore, outage and cost policies are qualified. | U13/U15 local reference is accepted. Provider-store source conformance and actual service qualification are separate; resource creation needs approval. |
| R3.2 / partial | All declared execution profiles use the shared engine's bounded deadlines/retry budgets, safe diagnostics, no-effect preflight and reviewed fault-injection/restoration. Unknown outcomes, interrupted cleanup, failed evidence storage and stale authority cannot lead to replay or successful closure. | U09/U13/U15; R1.4/R3.1 and adapter capabilities. Extend the existing engine. |
| R3.3 / open | One-time controller bootstrap uses the governed build/change-set path with narrow authority; the succeeding controller release runs through the controller and bootstrap authority expires. Safe handoff, ownership, cleanup and evidence remain traceable. | R2/R3.1/R5; source design first, bootstrap execution only with explicit target approval. No claim of full target qualification from bootstrap. |

### R4 — AWS adapter and environment integration

Plan trace: Phase 5; fixed migration steps 5–7.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R4.1 / open | AWS inspection/plan operations and staging composition reconcile existing CloudFormation, ECR, ECS, IAM, RDS, SQS and CloudWatch/SNS facts. IAM action/resource constraints, wildcard exceptions, consistency and safe observation methods are explicit. Account/region, lifecycle, governance, quota/capacity and cost bindings are complete. | R1/R2/R3 interfaces; reuse existing target sources. Source fixtures first; current provider facts require scoped inspection. |
| R4.2 / open | Service, infrastructure-change, finite-job, queue-consumer, migration, restore and scheduled profiles use normalized adapter execute/observe/classify/reconcile/cleanup behavior. Lost response, denial, timeout and wrong scope fail correctly. Existing reconciliation/image/smoke/restore commands retain compatible public entrypoints. | R3/R4.1; source conformance first. Disposable AWS qualification must declare resources, expiry, cost ceiling and teardown before approval. |
| R4.3 / open | Candidate runtime proof and per-task no-effect preflight validate actual artifact/command, identity, input/secret schema, authority, network/TLS/certificate/domain, dependency endpoints, backup/configuration lifecycle, required encryption posture, quotas, regional limits, subnet capacity and observation path. Each server/bootstrap/migration/relay/worker/restore profile is covered. | R2/R3/R4.1/R4.2; fixtures do not establish live IAM or bootstrap readiness. Live qualification is recorded in R7. |

### R5 — Release decisions and workflows

Plan trace: Phase 6; bootstrap/readiness policy inputs.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R5.1 / partial | One release command exposes validate/plan/realize/verify through the existing compiler/engine. Immutable composition/source/digest/operation graph, release lock/state ledger and all 17 ordered gates control advancement. Local and workflow callers share the decision; subprocess success cannot supply authority. | U01/U04; R1–R4. Includes evidence invalidation and safe immutable change summaries. |
| R5.2 / open | Policy enforcement consumes every R1.4 contract and reviewed RPO/RTO, retry/time budgets, evidence retention, restore cadence, observation window and recurring/disposable cost ceiling. Risk, privilege, data handling/residency, budget, destructive scope, capacity, recovery, lifecycle/decommission and exception gates fail closed. Break-glass expires, triggers reconciliation and blocks ordinary releases until closed or replaced by reviewed design; it cannot turn a failed proof into a pass. Unresolved prior cleanup blocks further disposable spending; externally owned resources and legal holds constrain lifecycle/cleanup actions. | Named owners/approvers and existing platform policy inputs; no silently chosen RPO/RTO, costs, trust or accepted-risk thresholds. |
| R5.3 / partial | Prepared source validation passes its first hosted run; release workflows invoke the same command with proven commit/digest binding, protected environment, OIDC, required checks and evidence upload. All supported workflow/adapters consume the common authority decision. | Existing source CI is prepared, not hosted acceptance. Publication, hosted activation and protection changes need explicit approval. Source changes may proceed beforehand. |

### R6 — Existing-caller migration and retirement

Plan trace: Phase 7; Phase 2 adoption matrix; fixed migration steps 8–9.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R6.1 / partial | Every supported profile family in the adoption catalog has old/new normalized behavior and scope equivalence, with actual callers migrated to the shared command or an explicitly temporary wrapper. Includes static checks, images/services, finite tasks, infrastructure, schedules, persistence/outbox, recovery and legacy supported targets. | U03/U14; R1 catalog and R4/R5 implementations. A generated pending proposal is not adoption. |
| R6.2 / open | Runbooks, package commands, target/workflow docs, commit templates and incident/break-glass procedures point to the authoritative command/evidence. Caller proof and reviewed equivalence justify each wrapper/duplicate retirement; historical evidence stays retained. No undocumented independent mutation route or unresolved adoption row remains. New components must enter through composition/profile/target/proof/lifecycle declarations from their first slice. | R6.1. Destructive removal remains subject to the user's approval boundary. No automatic deletion or legacy-resource change. |

### R7 — Staging qualification and usable deployment

Plan trace: Phase 8; Phase 0 live handoff; readiness decisions 5, 7, 8.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R7.1 / open | Fresh read-only target reconciliation, candidate runtime proof and per-task no-effect preflight pass, including artifact trust, IAM, costs, governance, drift, quotas/capacity and recovery. Reviewed immutable graph, resource/effect inventory, named authority, expiry and cleanup/cost plan are ready for specific approval. | R1–R6 relevant prerequisites. Completion makes a candidate reviewable; it does not grant approval. |
| R7.2 / open | After explicit approval, the staging graph demonstrates every required task's effects and safe evidence, plus wrong-scope denial, throttling, routing/WAF, alarm receipt, interruption, idempotency, relay/worker settlement, restore, rollback and cleanup. Finite-task terminal receipts precede cleanup. Independent reconciliation proves worker scale, resource ownership, steady state and approved ongoing cost. | R7.1 plus actual target authorization. PostgreSQL Stage 6 can execute only as the reviewed governed release graph; local fixtures cannot authorize resumption. |

Candidate readiness for PostgreSQL requires the plan's fixed migration steps
1–6 and passing candidate runtime proof and per-task no-effect preflight for
bootstrap, migration, relay, worker and restore.
Its controlled live execution belongs to R7, rather than being an independent
shortcut around qualification. R8's 28-day observation is a later programme
completion condition, not a waiting period before that approved execution.

### R8 — Continuous assurance

Plan trace: Phase 9; Phase 8 observation window; completion criteria 8–9.

| ID / B01 status | Completion criterion | Dependencies / boundary |
| --- | --- | --- |
| R8.1 / open | Scheduled reconciliation, bounded synthetics and periodic recovery rehearsals run through the controller; dashboard and alerts cover missing telemetry, drift, evidence expiry, failed control/cleanup, unclosed operations, lifecycle-policy breaches, IAM/network/certificate, image patch state, budget, backup/restore, capacity and expiring exceptions. Cadences/owners and upgrade-triggered requalification are defined and tested. Alert delivery is verified; missing telemetry prevents a false-green result. | R5–R7; activation requires approval. Safe evidence only. |
| R8.2 / open | The configured 28-day operational window and required rehearsals have actual observations, classified recoverable failures and no unexplained gaps. Exceptions are closed/expired with restored controls; lifecycle records have no orphaned resources, costs or improperly retained data. | R8.1 and elapsed observation time. A coding batch or one release rehearsal cannot substitute. |

## B01 subject boundaries and evidence currency

R1 coverage starts from the supported roots and source catalog in the accepted
U14 caller review: **403 sources, 220 remaining source findings, 350 separate
graph-boundary findings, and 403 pending adoption rows** at that snapshot.
These are distinct measures; the finding counts must not be added together or
compared with the original 169 as a defect burn-down. They are not a new scan
after U16. Every later comparison must bind one source snapshot, classify
added/changed/removed subjects and distinguish resolved findings from newly
observable ones. A current inventory and owned disposition for every row are
required to close R1; regenerating pending rows does not count as adoption.

R1.2 covers all supported workflow actions, not only the selected publication
workflow used for early implementation. R1.3/R2 cover both existing deployable
image families and all execution subjects they reveal, including long-running
relay/worker and telemetry sidecars. The accepted product catalog is a starting
input, not an exclusion of other supported paths. No Azure, Oracle or Snowflake
adapter implementation is added by this ledger; mixed-provider contract checks
remain requirements of the existing neutral model.

Implementation credit for U01–U16 is retained. U16 has accepted exact local
compiler/export evidence; the older final-container and dependency-effect
receipts prove their own recorded revisions. R2.1/R2.2 must renew affected proof
for the candidate under review. U13/U15 prove local reference behavior; they do
not become distributed-store evidence by renaming their status. A current proof
may expire while its implementation remains accepted; report both states.

## What each run must report

Before implementation, name the checkpoint IDs and concrete subcriteria the
batch intends to finish. Work stays attached to those IDs until accepted.
Record evidence at the tested source checkpoint; do not relabel older evidence
as current after an invalidating change.

| Field | Required report |
| --- | --- |
| Starting position | Baseline/revision, accepted-unit count, selected checkpoint status and outstanding subcriteria |
| Delivered | User-visible capability, stable IDs/subcriteria completed, exact evidence/check results and commit |
| Implementation versus qualification | Report source/local acceptance separately from current-artifact evidence, hosted execution and live-provider qualification; identify the exact input revisions each receipt proves |
| Remaining within selected IDs | Explicit unmet criteria; partial work is credited without marking the whole checkpoint complete |
| Requalification / repair | Invalidated receipt or defect, affected criterion and replacement evidence; no extra slice credit for routine repair |
| Scope / forecast change | Added/removed requirement, original plan reference, reason and effect on forecast; zero if unchanged |
| Next batch | Named IDs, acceptance boundary and dependency that completing them unlocks |
| Stop / approval / allowance | Real stop condition or none; external/policy approval still required; latest user-reported allowance and whether it is observable |

A newly discovered existing requirement is an estimating correction; a newly
requested capability is a scope change. Record which occurred. Do not add an
unbounded "remaining coverage" task, silently split IDs, or remove an unsatisfied
criterion to make the count fall. Subtasks retain their parent ID. A changed
baseline gets a dated delta with old/new criteria and reason; original evidence
and B01 remain available in Git history.

Elapsed time, test counts and lines changed are supporting information, not
completion measures. No percentage or finish-date promise follows from counting
these unequal checkpoints. A future forecast must name the exact checkpoints,
remaining effort assumptions, unknowns and required approvals. The October 3
target does not waive acceptance; the operational window necessarily extends
beyond it. No new numerical forecast is asserted in B01.

## Run deltas

| Run | Accepted deliveries | Acceptance progress | Scope / estimate change | Next |
| --- | --- | --- | --- | --- |
| Earlier estimate, after U09 | 9 | Source compiler, selected coverage, locked builds, container and finite-job foundations accepted | 15–20 rough estimate lacked a fixed decomposition | Effects/trust, coverage and durable controls |
| Implementation through U16 | 16 (+7) | U10–U16 accepted as registered above; broader AWS/orchestration/live milestones remain open | Original work within coverage/contracts and local-versus-production integration was underestimated; 12–17 was not a tracked forecast | R1.2 |
| B01 reporting correction | 16 (+0) | Fixed backlog, acceptance criteria, dependency/approval boundaries and accepted evidence register established; no implementation gate newly passed | No programme scope change; both numerical forecasts superseded as progress measures | R1.2 action material and input/default reconciliation |
| B02 MVP scope revision | 16 (+0) | M1–M5 and backlog-first intake adopted; no implementation gate newly passed | User-directed scope reduction for the first usable target path; full R requirements remain deferred/open where outside that path | M1 selected target/release blueprint and compiler acceptance |
| B03 selected MVP source acceptance | 19 (+3) | U17–U19 accepted; actual local image and database proof renewed; passive target attempt blocked on stale drift | No milestone expansion; mutable selected publisher/task bindings repaired within M2/M4; shared operating policy approved for source implementation | Selected operation/shared-store seam, then common execution/caller integration and approved hosted/target acceptance |
| B04 selected store source acceptance | 20 (+1) | U20 accepted: versioned records, conditional snapshots/events, exact evidence readback, 58 new tests and full 2,173-test regression passed | No milestone or programme expansion; live shared execution remains open | One existing candidate start/observe/stop through durable controller, authenticated transport and selected-caller boundary |
| B05 MVP ledger correction | 20 (+0) | The fixed P01–P33 closure ledger replaces the withdrawn L01–L49 draft; Phase 2 preserves R1–R8 | Reporting correction only; no new milestone, runtime implementation or numerical forecast | P01–P15 source integration, then P16–P33 hosted and target qualification |

## Historical next unit at B01 — superseded by B02

Current next unit is M1 in the linked MVP scope. The following R1.2 queue entry
records the earlier full-programme sequence; it no longer directs the next run.

**R1.2: immutable workflow action material and input/default reconciliation.**
Extend the existing action collector, operation contracts, schema/fixtures,
public wrapper and documentation. Bind immutable action material and executable
entrypoints/hooks; reconcile caller-supplied inputs and action defaults;
retain unsupported tool/network/behavior/identity and owner obligations.
Positive and tampered/missing/default-mismatch cases must pass focused local
verification and independent source review. No hosted action execution,
publication or provider mutation is included. Completion must update this
ledger with exact supported subjects and any R1.2 criteria still outstanding.

R2.1's image requalification is explicitly queued under its existing acceptance
criterion. It must bind U16's changed outputs before those outputs are used in
later artifact or target acceptance. It is not a newly invented delivery slice.

At B01, no external or policy stop blocked the then-next source unit; the
reported allowance rule was 26% remaining with a 20% stop. This is historical.
For B03 the user explicitly replaced that rule with a roughly three-hour maximum
ending by 21:10 UTC and accepted M4 operating policy for source implementation.
Specific AWS mutations and hosted activation still require approval.

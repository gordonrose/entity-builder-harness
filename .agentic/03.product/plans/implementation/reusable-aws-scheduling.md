<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.reusable-aws-scheduling
version: 2
status: draft
created_on: "2026-11-26"
updated_on: "2026-11-28"
layer: 03.product
domain: platform.scheduling
disciplines: [architecture, backend, security, sre]
kind: implementation-plan
purpose: Track A2 scheduling, support cleanup, retained evidence and remaining live proof.
portability: {class: source-only, targets: []}
used_by:
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# Reusable AWS scheduling implementation plan

## Current task and authority

The user authorized continuing toward the first harmless live baseline and
directed detailed cost checks to follow that bounded proof. Scope/image identity
is now independent of upfront cost admission; final measured acceptance remains.
The approved AGENTS marker and stale Entity test-fixture correction are complete.
Complete affected local integration passed, and the verified source was normally
fast-forwarded to remote main, most recently at `5fd130b328c3a5b116472055a77d1bbbbbf4fc5b`.

The lease-owner, real AWS response and generated-proof classification corrections
are committed and verified. Both protected publications passed on that source:
maintenance `46128392054` and four managed images `46128394666`. Actual runtime
container qualification and scans passed, but read-only ECR inspection found the
Lambda package is an OCI index with extra BuildKit attestation metadata, not the
direct image required by [AWS's Lambda image guide](https://docs.aws.amazon.com/lambda/latest/dg/nodejs-image.html).
Current increment: add `--provenance=false` to the existing managed builder and
prove its actual shell-to-Docker arguments for all four programs in the existing
test. Keep separate signed GitHub provenance/SBOM records and every security gate.
Rebuild through protected publication, verify the actual manifest, then use the
existing native owners for the first automatic harmless baseline. Do not deploy
the incompatible index, rewrite receipts or replace original operations.
The approved narrow
foundation repository-read permission update completed through its original
operation after a bounded controller/API-response correction; no attempt or
intent was replaced. No scheduler resources or database changes have yet been
deployed. The full goal remains incomplete; local checks and package publication
are not live acceptance or permission to leave either scheduler enabled.

Reuse immutable phase records, native task owners and package custody; add no
alternate engine, proof registry or budget runner. Unrelated work, changed
identities, uncertain effects and unqualified packages remain rejected. Current
run identities and exact evidence are in the existing session log. Preserve
the checked source while its packages qualify; session/plan notes do not change
runtime inputs. Calendar/timezone/DST work remains excluded.

Use the active Nov22 scheduler worktree recorded in
[the session log](../../../../commitLogs/2026/nov/22/2026-11-22-16-40-platform-scheduling-and-entity-smoke-retention-cleanup/README.md),
rather than the unrelated Nov21 tool working directory.
Implementation commit: `6c4e0fa89b51e01d23d775bcc21fdf7b1dd6143b`.
HEAD at cleanup start was `1d045e5f26ecca19aa7c64df12a2755e9e4890fa`;
the earlier task paths are preserved in committed history.

Earlier plan/history remains in that commit and the session log. A complete
pre-condensation working copy, including uncommitted verification records and
the cleanup consumer inventory, is retained for recovery at
`/tmp/scheduler-support-cleanup.hieiXV/reusable-aws-scheduling.before.md`.
The temporary copy is not an acceptance record.

## Outcome and boundaries

A fixed minute AWS EventBridge trigger invokes a bounded Lambda pass.
PostgreSQL owns one-off reminders. Due reminders hand over atomically to the
existing outbox, the existing relay sends to SQS, and Lambda invokes the durable
worker, which records completion. Reuse existing IDs, clocks, stores and workers.
The job registry includes only jobs selected by the application composition.

Independent proof scopes: `core-server-persistence` and `entity-smoke` on
`kanbien-core-platform`. Products/apps may own independent images and targets;
the baseline proves reusable machinery and Entity Smoke proves feature wiring.

Entity Smoke owns its five-minute elapsed retention policy. Purge must target
the exact record/deletion version and preserve restored, untouched and not-yet-due
controls under retries/overlap. Only positively identified proof-created synthetic
rows may be irreversibly deleted. Recurrence, timezones and DST remain excluded.

## Existing owners and disposition

| Boundary | Keep/reuse owner |
| --- | --- |
| Time and IDs | `packages/core/src/shared/{time,uuid}/` |
| Job selection | `platform/contracts/src/jobs.ts`; `platform/runtime/src/registry.ts` |
| Reminders and dispatch | `platform/persistence/src/{scheduling,schedule-delivery,schedule-dispatch}.ts` |
| Outbox and execution | `platform/persistence/src/{relay,processing,transaction}.ts`; `platform/workers/src/` |
| Relational stores | `platform/adapters/aws/persistence/postgresql/src/` |
| AWS queue/runtime | `platform/adapters/aws/queue/sqs/`; `platform/adapters/aws/runtime/lambda/` |
| Feature retention | `apps/entity-smoke/features/test-entity/` |
| Composition | `infra/04.deploy/03.product/entrypoints/shared/scheduling/` and scope handlers |
| Packaging | `scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/` |
| Reviewed AWS effects | `scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/` |
| Acceptance | Existing scope collectors and `scripts/04.deploy/lifecycle/60-run/release-succession/` |

Immutable reservations, uncertain-operation reconciliation, qualified source/image
binding, scoped IAM, shared-network preservation, cost admission and canonical
acceptance remain necessary. This table does not establish that every line of
the deployment/proof implementation is necessary.

## Authorized cleanup and consumer review

- Remove the duplicate native PostgreSQL benchmark runner and its separate
  measurement receipts from `scheduling-control/proof.py` and `proof-test.py`.
  Remove the receipt output from the PostgreSQL integration test; retain its
  actual storage/WAL allowance assertions in the ordinary test suite.
  Cost reporting keeps actual AWS billing/metrics, image sizes, price inputs,
  source binding, the $25 rejection and immutable report reuse. Storage allowances
  remain explicit workload assumptions, not live AWS storage measurements.
- Remove database readiness from shared-network creation. Keep complete network
  compatibility, identity, cost and change review. Each disabled scope creation
  retains its own database gate. Update `script.py`, `smoke-test.py` and the
  existing disabled-deployment workflow together.
- Condense repeated hashes, superseded estimates and chronological transcripts
  from this plan while retaining requirements, evidence and open blockers.
- Reconcile existing diagnostic reviews after source self-review. Add no scripts,
  diagnostic definitions, check IDs, progress stores or recurring reviews.

Existing proving checks: `scheduling-provider-controls`,
`scheduling-runtime-proof-contracts` and `postgresql-disposable-diagnostics`.
Final focused verification planning budget: ten minutes. Complete affected
integration and live acceptance remain distinct stages.

Remaining support cannot safely be deleted wholesale. Both final proofs and
combined costs belong to this goal. Their coupling into reusable activation,
full release/recovery requalification and old-image compatibility need an
owner-level redesign before more removal. No safety requirement is waived here.

## Current evidence

| Stage | Status |
| --- | --- |
| Dispatcher, worker, Entity transaction/purge | Implemented; focused local tests passed |
| Real PostgreSQL chain, isolation and conditional deletion | Cleanup standalone native rerun passed with engine/directory cleanup; first concurrent run timed out |
| Six finished images and publication | First core maintenance failed access-contract validation; worker failed runtime qualification; dispatcher published but scan rejected HIGH findings. No qualified custody receipt. Remaining Entity jobs cancelled before start; Entity maintenance still pending |
| Complete affected local integration | 100 passed / 37 later-stage or hygiene obligations deferred; exact checked source promoted to remote main |
| Publisher repository-read permission | Original foundation update completed and verified; publisher-identity access still requires its actual workflow probe |
| AWS scheduler/network and shared database changes | None performed by this work |
| Automatic runtime, both canonical acceptances, received alarm and affordable measured operation | Missing |

Retained reports:
- `.cache/test-runs/20261127T151716Z-dab1ef067948450caffd794825362ff6/report.json`:
  broad integration, 92 passes/eight failures/37 deferred, 2,511.423 seconds.
- `.cache/test-runs/20261127T154608Z-880c7692e37944a39d9df9a037912c51/report.json`:
  correction run, eight passes/three failures, 877.060 seconds.
- `.cache/test-runs/20261127T162558Z-bc8666ce0a1941f8b852ffb9ae1c853b/report.json`:
  acceptance-route/provider passed; repository contracts failed. Two catalog/test
  dependency omissions were subsequently corrected with focused proof; final
  registered revalidation remains outstanding.
- `.cache/test-runs/20261127T162050Z-15c3f82960aa48e9963f1796047526a6/report.json`:
  foundation permission contracts passed locally; permission update not executed.

Reports prove their named boundaries only. Reuse requires unchanged actual inputs.

## Unresolved cost and compatibility

The user explicitly moved detailed cost checks after the first bounded proof.
US$10 is therefore a reporting target, not an enforced pre-run cap; no claim of
proven affordability or a hard spending cap is made. The US$25 combined monthly
gate at 100,000 jobs remains required before leaving the schedulers enabled.
The original overnight cutoff was superseded by explicit continuation.

The earlier $20.968 infrastructure subtotal omitted other forecast components.
Under the existing one-percent retry model with one email subscription, about
$0.226 remains for image storage and measured Lambda compute before additional
CPU charges. This is source-based arithmetic, not proven live affordability.
Do not describe the earlier $4.032 subtraction as available headroom.

The full route counted 132 temporary tasks (35 core/97 Entity), before the new
compatibility extension. Native preflights and canonical requalification cause
that count; scheduling itself does not require it. Same-date/staggered two-hour
examples might fit $10 before extra compatibility tasks, but executable timing
and complete compatibility costs are unproved. These historical full-route
worksheets are not prerequisites for the newly authorized bounded first proof.

Entity accepted source `19b0fd3ff1a36dd247de4d820742d2e68bdc9727` has an
administration observer requiring one migration-history row; the new layout has
seven. That observer is incompatible. This does not prove the old application or
rollback read is incompatible. The authorized compatibility extension is unbuilt.
It must define meaningful proof for all five old workload identities.
The controller now retains each maintenance selection in its own immutable phase
intent and authenticates that scope through the existing native owner. Initial
creation takes its qualified Lambda receipts directly, without the other scope
or a cost intent. Post-proof cost capture retains the original network start time
instead of resetting the accounting window. The Entity compatibility extension
and later recovery-resource admission remain separate unfinished work; this
first-proof correction does not establish full live acceptance.

## Required live acceptance for the original goal

- Real automatic trigger -> due reminder -> outbox -> queue -> harmless baseline
  job -> durable completion.
- Entity atomically stores its reminder, survives before five minutes and purges
  only the selected synthetic row afterward.
- Untouched, restored and not-yet-due controls survive; retries/overlap do not
  duplicate destructive effects.
- Controlled missed-trigger and send-failure cases recover. Prove completion
  within five minutes after due and recovery within ten minutes after restoration.
- Both canonical records bind actual source, immutable image/function and
  database identities, runtime evidence, received alarm and combined cost.
- Final governed acceptance leaves both schedulers enabled within limits.

## Governance and historical approvals

Follow shared change completion, diagnostic coverage and test execution; immutable
package publication; target review/update; verify/accept/restore; and AWS plan/
execute workflows. This plan does not grant permission to change their safeguards.

Prior approvals covered governed scheduler main integration, bounded packaging/
control scripts, shared-network compatibility preserving staging, ECR
DescribeRepositories access, disabled-first deployment/read-only probes,
cleanup limited to positively identified newly created proof clones/snapshots,
and the Entity compatibility extension. They do not restart deployment during cleanup.
Before effects revalidate declared account `337159794548`, profile `kanbien-dev`,
region `eu-west-1`.

## Progress log

- First hosted package attempt exposed missing old core access declarations,
  a worker failure whose case context was discarded, and four HIGH rpm/rpm-libs
  findings in the official runtime. Source corrections reuse the existing probe,
  declarations, qualifier/fixture/tests and Dockerfile. AWS advisory
  [ALAS2023-2026-3430](https://alas.aws.amazon.com/AL2023/ALAS2023-2026-3430.html)
  supplies the targeted fixed release; the base pin and severity gate remain.
  Direct local tests pass; actual patched image/runtime proof remains missing.
  Both first workflow runs are terminal; preserve the failed dispatcher image
  and original run identities. Do not rerun their operations or treat publication
  without clean scan/custody as qualified evidence.

- 2026-11-28: The approved five-path foundation correction passed seven direct
  controlled-provider groups and both registered checks (35.526s, one reused).
  Existing workflow now admits checked controller-only descendants while keeping
  original intent/hash/reservations untouched. No scripts/checks/permissions or
  AGENTS edits added by that correction. Full local integration passed100/37
  deferred at source96f7434c, and the clean isolated promotion copy reused all100
  checks. A fresh final gate also passed100/37 deferred before normal main push.
  Foundation plan2597aba9 resumed its original change set and completed with
  unchanged resource/policy identities except the approved repository read.
  Protected publication runs46115891798 (core maintenance) and46115895513
  (managed images) select this exact source. Normal environment approvals were
  submitted under existing publication authority using the configured reviewer;
  no protection settings were changed. Actual image qualification, publication,
  runtime and canonical acceptance must still be collected; neither dispatching
  these workflows nor this progress record establishes those outcomes.

- 2026-11-27 20:50UTC: Cost-ordering correction is locally verified. Scope/image
  identity is retained in original phase records, initial creation authenticates
  the selected Lambda receipts directly, and native reservation/shutdown no
  longer require an upfront cost intent. Both realization declarations now make
  the spend-envelope input optional; final measured monthly acceptance remains.
  Scoped preparation passed without metadata byte changes. All four registered
  checks passed with zero findings in392.407seconds (307.693seconds executing
  commands), within the ten-minute final-pass budget. Report:
  `.cache/test-runs/20261127T204958Z-1fbbcae8b19f4cad8dd862f12b7d6f3c/report.json`.
  Whole-task commit preparation is blocked only at its current observed stage:
  AGENTS.md:106's unchanged teaching bullet is flagged by the prose heuristic.
  User subsequently approved the single explanatory comment; it is now applied
  immediately before the teaching checklist. All teaching instructions and the
  original EOF formatting are unchanged. Whole-task preparation resumes next.
  No commit, push, publication, AWS mutation or shared-database write occurred.
  No process remains running. Complete affected integration and live proof remain
  outstanding; these focused results do not establish release readiness.

- 2026-11-27: User authorized support cleanup. Existing work and a complete prior
  working-plan recovery copy preserved. Duplicate benchmark execution/receipt
  machinery removed; ordinary storage/WAL assertions retained. Shared network
  no longer depends on both databases; scope readiness remains. Self-review is
  complete across the cost capture/replay callers and both scope admission paths.
- Cleanup verification: metadata/process preparation passed. Four registered
  checks passed in 196.764 seconds (143.613 seconds executing commands):
  scheduling-provider-controls, scheduling-runtime-proof-contracts,
  scheduling-acceptance-contracts and diagnostic-catalog-readers. Report:
  `.cache/test-runs/20261127T173046Z-87d6c74f0e5146a4b7d67fcdd223c14d/report.json`.
  The first concurrent native run reached all successful assertions but failed
  its unchanged 20-second runner deadline; engine/directory cleanup passed.
  One unchanged standalone rerun then exited zero with all semantic assertions
  and cleanup passed. This does not prove concurrency caused the initial timeout.
  The existing pool-listener warning remains; it was not suppressed or treated
  as a new cleanup requirement. Whitespace checks pass; runtime review hashes
  remain unchanged after verification. No new/removed/moved script files, check
  IDs or required reviews. No speedup or complete affected integration is claimed.
  The larger acceptance/recovery framework remains coupled to current required
  proofs and is not certified minimal. No AWS, shared data or main changes.

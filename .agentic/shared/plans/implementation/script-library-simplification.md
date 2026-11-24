<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.plan.script-library-simplification
version: 14
status: draft
created_on: "2026-11-23"
updated_on: "2026-11-24"
layer: 06.shared
domain: governance
disciplines: [agentic, architecture, sre]
kind: implementation-plan
purpose: Govern a measured simplification of script responsibilities, topology, and verification selection without weakening meaningful evidence.
portability: {class: source-only, targets: []}
used_by:
- id: repo.report.helpers-audit
  path: scripts/helpers/audit.md
-->

# Script-library simplification programme

## Outcome

Make the repository's script library understandable and sustainable without
trading away meaningful quality evidence. The programme addresses two linked
problems together:

1. files that combine generic mechanics with target- or workload-specific
   policy; and
2. verification selection that expands from a local change into unrelated work.

The immediate priority is a fast, reliable normal path: retain only the proof
needed for code changes, commits, merges, builds, packages, and deployments.
Broad or periodic verification is retained but deferred until the normal path
is demonstrably lean. This plan is not authority to move, delete, weaken, or
run scripts. Each change remains a separately approved bounded capability
slice.

## Evidence baseline

- `scripts/helpers/catalog.py` read 713 existing non-Markdown script files and
  identified 34 modules with strong helper signals.
- Thirty-two of the 34 candidate modules have been audited in
  `scripts/helpers/audit.md`. Existing deployment and workspace-build
  mechanisms are mostly retained in their owner area; the audit also identifies
  two ownership mismatches and keeps Cognito provisioning as retained legacy
  work, separate from kanbien-core-platform lifecycle work.
- `scripts/04.deploy/shared/deployment-operation-diagnostics.py` mixes general
  retained-operation diagnostics with roughly 250 lines of
  core-server-persistence-only runtime evidence. Its generic report validator
  currently calls the target-specific task-failure validator, so a direct file
  move would preserve the coupling rather than remove it.
- Existing topology work already provides a read-only, source-backed planning
  view: `scripts/04.deploy/inventory-deploy-control/script.sh --topology`.
  It is not a runtime registry and must stay that way.
- Existing script-layout policy is owner layer, domain, then capability:
  `docs/01.harness/adrs/0017-organize-scripts-by-owner-domain-and-capability.md`.

## Target model

Each executable capability has one owner, one purpose, and one home:

```text
scripts/<owner-layer>/<domain>/<capability>/
  implementation/     # only when an implementation has several focused parts
  bindings/            # target/provider connection kept separate from mechanics
  tests/               # proofs of named risks
  fixtures/            # controlled inputs for those proofs
  script.py|script.sh  # public operation, when one exists
  README.md            # only when a newcomer needs an explanation
```

Not every capability needs every subfolder. A small, single-purpose operation
should remain small. A `shared/` location is reserved for a mechanism with
evidence of more than one real consumer; it is never a holding area for work
that has not yet been classified.

Legacy or dormant work remains retained in its own named area. It must not be
selected, presented, or made a dependency of active kanbien-core-platform work
unless an explicit consumer requires it.

## Role model and scheduling

Every script is classified by its actual responsibility. A file may contain
several functions, but it must not silently combine incompatible roles.

| Role | Responsibility | Direct execution policy |
| --- | --- | --- |
| Operation | Performs a declared local, package, deploy, or runtime action. | Runs only at its named lifecycle stage or explicit command. |
| Helper | Supplies mechanics to an operation. | Never selected directly. |
| Test | Proves one named risk for its owning capability. | Selected by the capability and its declared direct inputs. |
| Fixture | Supplies controlled test input. | Never selected directly. |
| Wrapper | Provides a stable public route to an operation or test. | Runs only when that route is requested. |
| Selector | Computes an execution plan from declared relationships. | Plans work; it is not normal deployment work. |

Verification follows the smallest relevant lane:

| Lane | Required evidence | Excluded by default |
| --- | --- | --- |
| Author/local change | Changed capability's focused proof. | Repository-wide hygiene. |
| Commit | Focused proof plus a direct consumer proof only when a shared boundary changed. | Broad architecture and periodic scans. |
| Merge/push | Changed capabilities and their real direct integration boundaries. | Package, provider, and runtime proofs unless their inputs changed. |
| Package/deploy | Frozen local qualification evidence plus stage-specific custody or environment proof. | Broad source hygiene already evidenced locally. |
| Runtime smoke | Deployed identity and essential behaviour. | Local build, package, and architecture scans. |
| Scheduled hygiene | Broad topology, architecture, dependency, and regression checks. | No claim that it is required for every iteration. |

Shared-helper changes must select the helper's own proof and each *declared
direct* consumer boundary. If that set is large, the audit treats it as evidence
to split the helper or narrow its contract; it is not permission to select the
entire repository.

## One audit record, not another registry

The catalogue remains generated evidence. The audit is the human decision
ledger. It records one row per module/capability, not one task per function or
file. Each record contains:

- role, owner, and lifecycle relationship;
- actual responsibility and real callers;
- named risk and the proof that addresses it;
- lane in which that proof belongs;
- inputs that invalidate prior successful evidence; and
- disposition: retain, split, move, merge, isolate as legacy, or retire.

The audit does not decide runtime selection. Existing governed selection remains
the execution authority until an approved replacement is demonstrated. Do not
introduce a parallel global catalogue, wrapper, or scheduler merely to hold
these audit decisions.

## Programme milestones

### M1 — Map and slim normal verification selection

Classify every check currently eligible for normal selection as essential to a
named lane, focused to one capability, deferred hygiene, or an
obsolete/duplicate candidate. Start with checks that are already known to scan
broad repository areas, including module structure. Remove confirmed hygiene
from normal commit and merge selection while retaining its script and a manual
route. Do not create a scheduler in this milestone.

**Complete when:** each normal lane has an explicit, small proof set; no broad
architecture, topology, catalogue, or periodic regression scan is selected by
an unrelated ordinary change; and retained deferred checks remain directly
runnable for review.

**Current status:** complete. Six confirmed broad scans are now retained as
explicit-only checks, with focused selector proof. The selection audit also
classified the largest remaining candidate contracts as named capability or
direct package-consumer proof, rather than treating their input counts as a
reason to disable them.

The mapping repaired three direct-routing omissions: candidate
preparation now selects its persistence control proof, and PostgreSQL adapter
work now selects both persistence composition and its package-stage container
proof. The remaining Core fan-out is a declared direct package-consumer
boundary, not hygiene leakage. It cannot be narrowed safely without an
approved cross-package source-to-consumer capability; keep it visible as a
separate design constraint rather than disguising it as a selector fix.

### M2 — Prove the lean lanes with representative changes

<!-- deterministic-check: allow reason="assessing whether selected proof still addresses a named risk requires source and consumer judgment; the selector proves declared mechanics but cannot infer adequacy of an unrecorded risk" -->
Use a product-code change, a deployment-script change, and a build/package
change to prove that selection chooses only focused evidence and declared
direct consumer boundaries. Check that each lane still blocks its named risk
without triggering broad hygiene.

**Complete when:** before/after selected-check count, executed-check count,
duration, named risks, invalidation rules, and exclusions are recorded from
actual runs. A faster run without equivalent decision evidence fails this
milestone.

**Current checkpoint:** complete. The selector now distinguishes a workload
scope being relevant from every proof in that scope being relevant. For an
ordinary source change, development feedback selects only proofs whose declared
inputs directly include that source. A scope declaration, scope index, or
catalogue change still retains the complete scope proof. The M2 record in
`scripts/helpers/selection-audit.md` gives the before/after counts, executed
commands, bounded durations, direct-risk evidence, and the remaining Entity
Smoke aggregate boundary.

**Follow-on correction (2026-11-24):** Entity Smoke now keeps its existing
combined composition suite as a deferred, explicit local-qualification or
maintenance proof. Ordinary route work selects the shared base proof and the
affected route fixture(s); route fixtures that import another fixture select
that direct dependency. The full suite still runs the routes in
parallel when explicitly requested. Its 60-second estimate was replaced by
route-level advisory estimates; an estimate overrun is recorded for redesign,
not treated as an automatic cancellation.

**Timing evidence (2026-11-24):** The selector's existing runner records an
estimate overrun in the execution-policy report without changing a successful
check's passed status or exit result. A disposable fixture now proves that
behaviour directly. There is intentionally no new selector timeout: any future
hard stop must be separately governed as a genuine stuck-process safeguard,
not derived from `expected_seconds`.

### M3 — Finish the current evidence-based helper audit

Complete the two remaining catalogue candidates, then pause the broad audit.
Classify at capability/module level first; inspect individual functions only
when a module demonstrably mixes responsibilities. The audit informs future
work but is not a prerequisite for M1 or M2.

**Complete when:** all 34 current candidates have a role, owner, lifecycle
relationship, caller evidence, and disposition.

**Current status:** complete. `scripts/helpers/audit.md` now records all 34
catalogue candidates. It confirms that structural exports do not themselves
justify a shared move, identifies deployment-operation diagnostics as the one
mixed-responsibility boundary for M4, and records two future bounded ownership
relocations without authorising either migration.

### M4 — Design the first mixed-responsibility boundary

Design the general-report versus core-server-persistence evidence boundary in
the deployment diagnostics module. Decide whether the general report removes
`task_failure` or accepts a caller-owned validator. Map all consumers and
backward-compatible report consequences before modifying code.

**Complete when:** an approved interface, consumer migration order, focused
proofs, and rollback path exist. No extraction occurs merely because it is
described here.

**Current status:** complete. The chosen interface is a caller-owned extension
profile: the shared report engine has no target extensions by default, while a
Core Server Persistence binding supplies the sole `task_failure` validator.
`scripts/helpers/audit.md` records the consumer map, canonical target home,
migration order, focused proof set, and bounded rollback route. No code moved.

### M5 — Migrate bounded capability units

Move only audited units whose target home, callers, tests, fixtures, and public
routes are known. Update all consumers together, prove the canonical path, and
retire compatibility paths when a concrete consumer no longer needs them.

**Complete when:** each migrated capability has one canonical home, no silent
old-path consumer, and focused proof at its new boundary.

**Current status:** complete for the audited Core Server Persistence deployment
diagnostics unit. The persistence-only readers now have one target-owned home,
all six known callers use it, and the shared report engine accepts no target
field unless that binding supplies its explicit `task_failure` validator. The
existing diagnostics regression now runs the separated shared and binding
proofs; it is still one declared check, not a new selection system. The audit
records the exact paths, evidence, and retained historical-report boundary.

### M6 — Establish future script admission

Turn the proven model into a small harness standard and templates. Before a new
script is created, its author must state its role, owner, purpose, consumer,
named risk, execution lane, reuse assessment, and whether an existing
capability can own it. New broad selectors, wrappers, or registries require
explicit approval.

**Complete when:** the standard supports new capability work without adding a
second scheduling system or creating speculative scripts.

**Current status:** complete. `.agentic/01.harness/standards/script-admission.md`
now requires a short, existing-record admission decision before a new script is
created: role, owner and capability, purpose, direct consumers, named risk,
proof lane, existing capability considered, reuse decision, and why a script
is needed. It makes no automatic path decision while the folder migration is
incomplete: current canonical capability homes are extended conservatively,
and a new owner/domain/capability folder needs an explicit approved proposal.
It prohibits a second selector, wrapper layer, scheduler, or registry without
explicit approval, and it points back to the existing metadata and path-
migration standards rather than duplicating them.

## Measurement and acceptance

For every completed slice, retain a small before/after record:

- modules and consumers affected;
- selected and executed checks by lane;
- elapsed time and evidence reused;
- risks proved and risks deliberately deferred to scheduled hygiene;
- source changes that invalidate reused evidence; and
- remaining coupling or legacy work.

The programme succeeds only if both conditions hold:

1. the selected proof still addresses every named change risk; and
2. unrelated checks are no longer required for ordinary local iteration.

## Guardrails

- Do not declare a script shared solely because it appears in a shared folder.
- Do not replace source-backed consumer evidence with guesses based on paths.
- Do not split a module before its public contract and callers are known.
- Do not reduce verification by hiding, caching, or relabelling an unresolved
  failure as a pass.
- Do not disable an unclassified check merely because it is slow. First record
  its named risk, current lane, direct callers, and deferred/manual route.
- A deferred hygiene check must not remain silently selected by an ordinary
  code, commit, merge, package, or deployment path.
- Do not make dormant RAG, staging, or platform-shell work a dependency of
  kanbien-core-platform work.
- Do not make the generated catalogue or audit ledger a mandatory commit,
  merge, package, deploy, or runtime gate.
- Preserve the user's rule that every new file has a metadata header and that
  a new source file exceeding 50 lines of code requires approval.

## M7 — Preserve unchanged proof when promotion selection changes

**Approved follow-on scope:** the local merge verifier already supplies the
exact branch diff to direct selection. The remaining blocker is proof reuse:
the selector currently adds its own implementation files to every selected
check's evidence inputs. A selector change therefore invalidates unrelated
application proof and can turn a narrowly selected promotion into a long
sequence of unrelated reruns.

**Named risk:** a changed selector could choose the wrong proof, while an
unchanged application proof could be rerun merely because the selection engine
changed. Both need evidence, but they are different risks.

**Consumers and retained route:**

- `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh`
  invokes the exact-diff promotion selector.
- `scripts/repo/check-selection/script.py` owns evidence identities and reuse.
- `check-selection-mechanics` remains the explicit, complete selector/cache
  regression route for periodic or deliberate review.

**Bounded change:** stop treating the selector implementation as an input to
every unrelated subject proof. Register a small focused promotion-selection
proof, using existing fixture tests, for selector changes. It must prove exact
branch-diff routing, hygiene deferral, no catalogue-consumer expansion, and
reuse of proof whose direct subject inputs did not change. It does not alter
application/package/deployment proof inputs, create a scheduler, or add a
second selector/wrapper system.

**Complete when:** an unchanged selected subject proof reuses its matching
receipt after a selector-only edit; a selector edit still selects and runs the
focused promotion-selection proof; the full mechanics suite remains directly
runnable but is deferred from ordinary promotion; and focused fixture evidence
passes.

**Evidence and review:**

- `mechanics-promotion` ran its six direct fixture cases in 4.7 seconds. It
  proved exact-diff routing, catalogue and review-ledger containment, hygiene
  deferral, explicit deferred execution, and reuse after a selector-only edit.
- The focused actual-catalogue contracts proved that selector paths select the
  new focused proof while the complete mechanics suite stays deferred.
- The registered `check-selection-promotion` command passed in 4.8 seconds.
- Metadata headers and whitespace passed for all seven changed artifacts.
- Source review confirmed that subject fingerprints still include their own
  declared code, configuration, command and direct catalogue inputs; only the
  previously global selector-engine additions were removed. A command that
  actually consumes selector files must continue to declare them directly.

**Current status:** complete.

## Current completion boundary

Milestones M1–M7 are complete. This programme still does not authorise a
repository-wide folder migration, a new scheduler, a registry, or changes to
the separate workspace-build ownership mismatches.

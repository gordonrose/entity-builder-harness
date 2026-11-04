<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.workflow.verify-diagnostic-coverage
version: 14
status: active
created_on: "2026-10-27"
updated_on: "2026-11-04"
layer: 06.shared
domain: diagnostics
disciplines: [architecture, security, sre, agentic]
kind: workflow
purpose: Govern diagnostic responsibility review and enforce code-owned contracts for all coding work.
portability: {class: source-only, targets: []}
used_by:
- id: repo.agents
  path: AGENTS.md
- id: shared.standard.require-change-completion
  path: .agentic/shared/standards/require-change-completion.md
-->
# Verify diagnostic coverage

Use with the owning coding workflow for new services, integrations, capabilities,
features, refactors and executable tooling. The runtime implementation owns
schemas and meaning. This workflow owns review, adoption and proof selection.
Follow the [safe diagnostic standard](../standards/require-safe-diagnostic-record.md).

For confirmed future work found during an agreed diagnostic review, or a request
to update the Diagnostics backlog, use its
[maintenance workflow](maintain-diagnostics-backlog.md).
Recording follow-up work does not waive active task requirements below.

## Review responsibilities before editing

Use the consumer inventory required by the
[change-completion standard](../standards/require-change-completion.md#implementation-and-consumers).
Before implementation, add a diagnostic predicate inventory to that same task
plan or session record for affected configuration reads, attribute checks,
outgoing calls and connections, routes, jobs, lifecycle and recovery operations.
Do not introduce a second tracking system or runtime vocabulary registry.

For each applicable decision or call boundary, identify:

- the exact observed condition and alternatives, including distinguishable
  missing, empty, wrong-type, rejected, thrown and unknown outcomes;
- the owning runtime definition/code/version reference and required safe
  location fields, with sensitive evidence explicitly excluded;
- the effect actually known, producer and preservation/delivery consumers,
  public projection and compatibility requirement;
- exact behavior/type test references and registered check identities, marking
  planned tests as planned until they exist and pass.

Apply the [context and consumer obligations](../standards/require-safe-diagnostic-record.md#context-and-consumer-obligations)
in that same inventory. For each operation, name the required context facts,
which owner supplies each, the actual interface/construction path requiring them,
and the final reporter or governed lookup carrying them. Review the real caller
path, including failures before normal reporter initialization. Identify existing
shared checks/wrappers before proposing another; a supplied Core import is not
proof a checked result or diagnostic reaches its consumer.

For [supported reason preservation](../standards/require-safe-diagnostic-record.md#supported-reason-preservation),
establish the bounded operation set and existing deferrals before corrections.
Extend this same inventory with each actual check/returned reason, item,
mapping, selected code/version/catalogue, wrappers, final error-handling caller
and exact assertion. For each proposed correction, record the owning layer/file,
existing shared mechanism considered and reuse or justified local responsibility.
Distinguish normal supported-reason coverage from diagnostic-processing fallback
and delivery proof; identify compatibility-only helpers and actual production
callers. Do not substitute a catalogue enumeration for the operation inventory.

For a structural refactor, separate preserved contracts from any proposed error,
context or diagnostic change. Agree required compatibility decisions before
implementing altered responses or report fields. Config's original failure
formats and source-throw semantics are not replaced by teaching examples.

For module-local catalogues, apply the
[catalogue export requirements](../standards/require-safe-diagnostic-record.md#module-local-catalogue-exports).
In this same inventory identify executable definitions, local generated JSON,
public TypeScript/JSON exports, retained aggregate readers and affected package
shims. Prove exact selected membership, stale/conflicting export rejection and
real public asset resolution; preserve existing reader-family restrictions.
Use the existing generator and reader fixtures, not a second catalogue registry.

For configuration changes, apply the
[configuration checking responsibilities](../../03.product/standards/config-runtime-settings.md#configuration-checking-responsibilities).
In this same inventory, name each used input's treatment, reuse/exception
decision, checked-result consumer and exact caller assertions rejecting bypass.
Apply the existing context obligations at the real reporting boundary. A fresh
review hash or a permitted source location is not proof of checked-result use.

For implementation selection and loading, also apply the configuration standard's
[ownership requirements](../../03.product/standards/config-runtime-settings.md#dependency-requirements-implementation-selection-and-composition).
Include the selected constructor's real consumer and distinguish unsupported
selection, source failure, invalid contents and later operation evidence in this
same inventory. Keep supplied selection strings outside records.

For shared reason-name changes, apply the
[shared names and versioned selections standard](../standards/require-safe-diagnostic-record.md#shared-names-and-versioned-selections).
In this same inventory, identify each affected code/version's explicit selection,
direct and indirect readers, type-only consumers and justified no-change decisions.
Keep old definitions fixed and prove fixture-only vocabulary growth cannot widen
them; use the existing compatibility and actual caller/reader fixtures.

For reusable validation constraints, apply the
[constraint ownership rules](../../03.product/standards/public-module-structure.md#reusable-configuration-constraint-ownership).
In the existing inventory, name the selected owner and affected consumers,
inspect existing equivalents and record the applicability decision before adding
or moving a rule. Prove actual shared use with a bounded wiring/behaviour counterexample:
matching today's endpoints alone cannot distinguish reuse from copied bounds.
This is a source-review/fixture duty, not a universal clone-detection claim.

Review each distinguishable condition within combined guards; one inventory row
per coarse return or file is not sufficient. Independent conditions must remain
separate observations where supported. Name unsupported evidence and uncovered
boundaries instead of guessing root causes. For a process-only change, record
why no runtime predicate or diagnostic contract changes.

Keep provider-neutral definitions upstream in core, capability packages and apps.
Adapters supply evidence; target composition supplies bindings. Use the existing
descriptor, validation, profile, audit, security and deployment contracts rather
than replacing them with a parallel logging framework.

## Implement and prove connected behavior

1. Reuse the owning definition if it already represents the supported failure;
   repair mapping, selection, registration or caller loss at its actual owner.
   Only add/change a definition when needed, following versioning rules. Use
   the Core constructor/parser; keep arbitrary values outside diagnostic detail.
2. Produce records at the actual decision/call boundary. Preserve them through
   wrappers. Register app catalogs through the public app mount. Deliver records
   only through an approved internal reporter; keep profile opt-outs effective.
3. Upgrade consumers before emitting an additive field. Retain historical reader
   support and public response shapes. Do not rewrite retained evidence.
4. Test exact predicates and alternatives, rejection before side effects,
   uncertainty, safe wrapper propagation, malformed input, sensitive canaries and
   disclosure boundaries. No diagnostic should grant automatic mutation replay.
5. Update `scripts/repo/diagnostic-coverage/reviews.v1.json` with the reviewed source
   SHA-256, owner, status, definitions, exact test references and registered local
   check identities. `adopted` requires accuracy, disclosure, preservation and
   uncertainty proof. Use `partial` with concrete remaining debt when a whole file
   is not adopted. Use `support` only for contract/verification plumbing without
   an operational failure boundary. Do not refresh hashes without reviewing code.

For changed consumer context, extend existing type/runtime/caller fixtures to
reject missing required context and inappropriate operation/item/stage bindings,
including a well-formed but wrongly attributed report. Prove actual wrapper and
delivery preservation, unchecked-input rejection before dependent work, sensitive
canary exclusion and reporter-failure isolation. Cover single/multiple input
successes, setting failures, sourcing failures and prevented checks where the
operation supports them; do not change iteration or invent continuation for tests.
Use existing registered owners and bounded counterexamples, not an import-regex
rule, parallel registry or general-purpose program-analysis framework. Name which
guarantees TypeScript, runtime checks, behavior tests and source review establish;
do not describe planned controls or source-hash freshness as semantic enforcement.

The immutable initial baseline `d94da2b9401d3abcf86618b5d497e9b93903490a`
permits unchanged legacy files while reporting them as debt. New or changed
executable code without a fresh review fails. Discovery covers ordinary code,
all configured workspace source roots, target entrypoints and scripts; it does
not depend on scope/deployment registration. Dormant RAG roots and verification
fixtures are excluded from runtime adoption, not from their owning test rules.

## Source review handoff

Apply the [consolidated source review](../standards/require-change-completion.md#consolidated-source-review)
before the final focused pass. Reconcile the actual implementation with both
inventories, including wrappers, startup reporting, catalog selection, adapter
test setup and compiled payload consumers. Apply the shared counterexample
review to exact accepted, defaulted and rejected meanings, including code,
definition version, observed condition, source and effect where applicable.
Check relevant sides of delivery boundaries, including failure before startup
completes, and preservation through wrappers and consumers. A schema-valid
record, expected count or unchanged business result alone does not prove that
the observation is true or delivered at the required boundary. Resolve required
omissions as one correction batch before preparation and final focused tests.
Preserve genuine failure investigation; do not relabel unresolved diagnostic
requirements as optional enhancements to obtain a freeze.

Reconcile each supported reason with its normal-failure real-caller assertion
and applicable counterexample under the standard above, before accepting
fallback-only proof. Mark in-scope unproved paths incomplete. Record explicit
no-change/compatibility/deferral decisions; source hashes, packet existence and
schema validity alone do not close these rows. Apply the existing stable-input
verification sequence rather than repeatedly executing unchanged suites.

## Gates and completion

After normal metadata preparation, validate the impact plan before expensive
execution and run the structural adoption check:

```bash
bash scripts/repo/check-selection/script.sh --paths <changed-paths> --json
bash scripts/repo/diagnostic-coverage/script.sh
```

For final focused verification, follow the shared
[verification and reuse rules](../standards/require-change-completion.md#verification-and-stage-boundaries)
using the [registered-unit command interface](../../../scripts/repo/check-selection/README.md).
After required focused checks pass and verification inputs are frozen, complete
the impact-selected local checks:

```bash
bash scripts/repo/check-selection/script.sh --paths <changed-paths> --execute-local --json
```

The direct `scripts/repo/diagnostic-coverage/verify.sh` command remains a supported
complete diagnostic aggregate. A separate invocation is not required when the
selected `diagnostic-runtime-contracts` check already supplies matching proof.
Focused unit selection alone never establishes complete change impact.

The base aggregate now composes the separate catalog/reader check and eleven
package units. Use affected startup fixtures as the catalog-declared focused
prerequisites before broad diagnostic verification. Default and explicit broad
requests require matching prepared-task context; they cannot bypass ordering by
requesting an aggregate's members. Review-ledger changes retain whole-ledger
structural validation, while semantic additions, removals and owner transfers
select both former and current proof owners. An absent ledger in a valid base
means initial adoption; unavailable or malformed comparison data is a gap.

The structural check blocks commits; runtime contract/export verification runs
at integration. Review-linked registered checks are selected by the existing
selector, including for non-deployed services. CI and local-main promotion use
that selector. Its permissions and stage rules still apply.

Missing ownership, missing executable contracts, stale exports, stale reviews,
unknown check identities or failing proof block completion at the affected
boundary. Repair the owning source/consumer or report the precise blocker; do
not loosen schemas, hide debt or replace behavior tests with source regexes.
Structural checks verify registration and freshness, not the truth of human
coverage claims. Review behavior tests for completeness.

Record local tests, actual container qualification and live proof separately in
the session log. Existing accepted images and cloud resources are untouched
unless the user authorizes their owning deployment workflow.

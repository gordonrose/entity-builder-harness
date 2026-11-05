<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standard.require-change-completion
version: 10
status: active
created_on: "2026-10-24"
updated_on: "2026-11-05"
layer: 06.shared
domain: process.change-completion
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Require connected implementation, proportionate authorized verification and honest completion evidence across layers.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: shared.workflows.change-shared-process
  path: .agentic/shared/workflows/change-shared-process.md
-->
# Require Change Completion

A change is complete when its applicable contract, implementation, affected
consumers and required verification agree. A plan, declaration or passing
individual check proves only its own boundary. Report uncovered impact and
missing required proof explicitly instead of treating either as completion.

Coding work also follows [diagnostic coverage](../workflows/verify-diagnostic-coverage.md).
Completion includes the affected diagnostic definitions, error propagation,
consumers and tests; a catalog without producers or a producer without its
reader is incomplete.

For README additions or edits, follow the
[readable-README standard](require-readable-readmes.md) using the
[README-writing skill](../skills/write-readme.md). Keep the task's scope and
verification proportionate; this does not require unrelated documentation work.

## Implementation and consumers

For new modules, public-surface changes and refactoring, apply the
[public module structure standard](../../03.product/standards/public-module-structure.md).
Record its applicability and implementation ownership in the existing inventory;
follow its bounded treatment of legacy code rather than silently waiving the
rule or expanding an unrelated fix into a repository-wide cleanup.

Before implementation, record a bounded consumer inventory in the existing task
plan or session record and reconcile their existing owner records. Cover affected
contracts, configuration, packages, entrypoints and deployment scopes, including
producers, wrappers, readers, catalog registration, adapters, package dependencies,
test setup and compiled payloads. Name owning paths, compatibility requirements
and proving checks. Update supported implementations in the same change; record
non-applicability with a reason. Discovery supports, but does not replace,
reviewing connected behavior.
Use the owning executable discovery and validation controls; an unowned or
unsupported requirement is a gap, not an implicit exclusion. A valid
non-applicability has a reason and does not hide an affected consumer.

## Consolidated source review

Exploratory tests are allowed during implementation. Before declaring a final
focused verification pass, the designated reviewer must review the whole change
against the consumer inventory and applicable requirements, including the
diagnostic predicate inventory. The parent owns this review for delegated work;
without delegation or a separate reviewer, perform and record an explicit
self-review. Collect required corrections in one consolidated list rather than
feeding enhancements into an announced final test pass.

For each material behavioral guarantee changed by coding work, identify a
plausible incorrect outcome and the exact assertions that would reject it.
<!-- deterministic-check: allow reason="choosing material counterexamples and assessing assertion sensitivity requires source-review judgment" -->
Check that those assertions distinguish the claimed behavior from that
counterexample; schema validity, counts or successful business output alone
may not do so. Where test sensitivity is uncertain, demonstrate it with a
bounded counterexample and record the result. Keep this review proportionate
to the change: it does not require a mutation campaign for every edit or
behavior tests for documentation-only changes. Use the existing inventories
and plan or session record rather than a separate tracking system.

Close required corrections and finish affected consumers, generated artifacts,
metadata preparation and source-matched reviews before final focused testing.
Record the inventory references, reviewer, correction disposition and reviewed
task paths in the existing plan or session record. An unresolved requirement or
affected consumer, or an unresolved gap in rejecting a material counterexample,
blocks this handoff; a passing exploratory test does not close it. Source review
does not grant git, deployment or other external authority.

## Verification and stage boundaries

Before broad verification or image qualification, complete implementation and
affected-consumer changes required by the applicable requirements, close the
consolidated source review, pass final focused tests, and validate the existing
selector plan without executing broad checks. Record the focused commands and
outcomes and obtain confirmation from every contributing agent that verification
inputs will remain unchanged. Do not launch these checks while any agent is
still editing their inputs. Any subsequent input change reopens affected review
and preparation before retrying the affected verification.

Select existing checks in proportion to affected consumers and declared
requirements. Deduplicate identical checks only within the same stage and
input identity. Reuse passing evidence only when its relevant source, inputs,
artifact bindings and freshness still match; a prior static pass cannot
satisfy package, target or live behavior proof. Preserve mandatory checks,
stage ordering and each command's permissions. A selector may identify a
provider or publication check without being allowed to execute it.

Where a suitable registered verification unit exists, use the trusted selector
for final focused verification. Compose aggregate checks from reusable registered
units rather than repeating their commands, while retaining full impact
selection and stage-specific proof. Direct commands remain allowed for
exploratory testing but do not seed trusted reuse. Where no suitable unit exists,
record that limitation and still complete the required proof. When adding or
changing units or aggregates, include owning regressions for complete membership,
child-failure propagation, matching-result reuse and invalidation after relevant
source, runtime or verification-contract changes.

Declare applicable focused prerequisites and aggregate members in the existing
check catalog. The selector orders and revalidates those prerequisites before
starting broad commands, including explicit requests and default wrappers; a
failed, missing, ambiguous or changed prerequisite blocks that command. Impact,
CI and all-input selection provide their own task context. Explicit broad work
requires the matching prepared task; caller-supplied paths or environment text
are not preparation evidence. Nested aggregates use an execution-scoped binding
in the same private preparation mechanism, which expires on completion/failure
without replacing lifecycle preparation. Aggregate wrappers must dispatch only
their declared catalog members, not undeclared executable children. Ordinary
exploratory shell commands prove their own boundary; this gate does not claim to
control arbitrary commands outside the registered runner.

Commit and integration scheduling are separate from execution effects and
package, deployment and acceptance boundaries. Expensive local behavioral
checks may be deferred from commits only when CI and direct local-main
promotion enforce them against the combined result. The existing trusted local
cache may transfer matching receipts between registered worktrees of the same
repository; final input and runtime identities must still match.

Missing implementation blocks the stage that consumes it. Missing proof blocks
the stage that requires that proof. Distinguish static validation, local
runtime tests, actual container qualification, CI and live evidence in the
existing session record and completion report. Name checks, outcomes and safe
evidence references; planned commands and fixtures are not execution evidence.

## Correction and continuation

After failure, retain safe evidence, repair the relevant owner, rerun affected
checks and resume from the first incomplete stage. Broaden verification when
changed impact or unresolved evidence warrants it. Continue independent
authorized work while another operation is blocked. Reconcile an interrupted
operation before repeating a mutation or a completed task; pending, failed and
uncertain outcomes must remain distinct.

A genuine failure or newly discovered required consumer reopens the affected
inventory and source review. Keep unrelated enhancements in a separate task;
neither freeze nor a correction list permits leaving a required fix unresolved.

For inadequately explained failures discovered during authorised work, use the
[diagnostic discovery procedure](../workflows/verify-diagnostic-coverage.md#when-work-uncovers-an-inadequately-explained-failure).
It determines the correction or escalation path; recording necessary in-scope
work in a backlog does not satisfy this completion requirement.

## Authoritative specialization

This standard owns cross-layer completion principles only. Deployment
[realization proof](../../04.deploy/standards/operational-realization-gate.md)
owns deployment proof levels, gates and evidence semantics. Product owners own
runtime contracts. Provider owners own concrete inspection, mutation,
permission, reconciliation and recovery procedures. Their workflows reference
these owners rather than copy or redefine them. Session lifecycle, goal
lifecycle and git approval remain with their existing owners.

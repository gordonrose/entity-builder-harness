<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.testing.workflow.write-and-verify-tests
version: 2
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 06.shared
domain: testing
disciplines: [agentic, architecture]
kind: workflow
purpose: Guide owner-led test authoring and verification using existing runners, diagnostic proof and completion controls.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
- id: shared.testing.standard.test-design
  path: .agentic/shared/testing/standards/test-design.md
-->
# Write and verify tests

Use when adding or changing tests alongside the owning implementation workflow.
Read the [test-design standard](../standards/test-design.md) and
[execution standard](../standards/test-execution.md). This procedure
does not authorise implementation changes for an answer-only request or replace
session, permission, git or environment governance.

## 1. Establish the contract and owner

Read the changed behaviour's contract, implementation, direct consumers and
existing tests. For Core, Platform or app work, use the
[product testing index](../../../03.product/tests/README.md) to find the
owner's evidence requirements. Use the existing
[shared taxonomy](../../../../docs/06.shared/rules/concerns/ci-quality.yml)
to describe the relevant test types and categories.

Locate the current runner, file discovery, fixtures, compiler setup and suitable
registered checks. Inspect real commands and configuration rather than assuming
that a file named `*.test.ts` runs automatically. Keep existing test locations
and runners unless a separate approved migration changes them.

If the behaviour contract or required governance is absent or ambiguous, stop
at that gap and ask for direction under the owning workflow. Do not invent a
contract by encoding a convenient expectation in a test.

## 2. Plan the smallest sufficient proof

Extend the existing task/session consumer inventory, not a new test ledger.
For each material changed guarantee, identify its owner, relevant cases,
observable outcome/effects, proving test and verification command or check ID.
Include affected consumers when the guarantee crosses their boundary.

For example, if nullable input is accepted but omitted input is rejected,
plan separate cases asserting those outcomes. If rejection must precede
persistence, also assert that the write dependency was not called. This is an
illustration, not a new rule that all attributes must be nullable or required.

For diagnostic changes, extend the predicate inventory and follow the
[diagnostic workflow](../../workflows/verify-diagnostic-coverage.md). Its
diagnostic review records remain authoritative; do not create parallel records.
State what needs a real dependency, container or live environment, and whether
that proof is authorised and available. A fake is not a substitute for it.

## 3. Write and exercise focused cases

Inspect the catalog's feedback declarations and the impact plan. Use
`--paths <changed paths> --development --execute-local --explain` for declared
local feedback, or focused existing runner cases while authoring tests. Retain
pending check IDs. Missing feedback metadata means unclassified, not permission
to omit an integration requirement. Expected durations are estimates, not skips.

Use the existing owner helpers and runner conventions. Build isolated fixtures,
control nondeterminism and exercise the claimed public boundary. Assert exact
contract outcomes and relevant positive or prevented effects; include the
negative and failure cases selected in the plan.

Run focused exploratory checks while developing. Confirm intended cases are
discovered, compiled from current sources when applicable, executed and able
to report failure. Inspect negative type assertions with their actual compiler
check. Review new fixtures and expected-output changes rather than accepting
them automatically. Apply the standard's resource cleanup and external-service
safeguards before exercising integrations.

## 4. Review the complete change

Follow the [consolidated source review](../../standards/require-change-completion.md#consolidated-source-review).
Check planned guarantees against actual assertions, including the plausible
wrong outcomes they reject. Reconcile consumers, diagnostics, fixtures and
generated artifacts. Close required corrections before final focused proof;
use the existing task/session record for the review and its limits.

## 5. Verify stable inputs and report the boundary

Follow the [existing verification sequence](../../standards/require-change-completion.md#verification-and-stage-boundaries)
and [registered-check interface](../../../../scripts/repo/check-selection/README.md).
Use suitable registered units for final focused verification. If no suitable
unit exists, record the limitation and complete required proof as the completion
standard directs. This workflow neither registers new checks automatically nor
bypasses broad-check prerequisites or permissions.

Record actual commands/check IDs, outcomes, exercised boundaries and remaining
required proof. Keep failed, pending and uncertain results distinct. If a
failure requires a correction, reopen the affected review and rerun affected
proof according to the completion standard; do not label earlier exploratory
passes as verification of changed inputs.

Documentation-only edits use proportionate metadata, link and source/clarity
checks. They do not require new runtime tests or diagnostic review hashes.
Passing those checks establishes the documentation slice, not conformance of
all existing tests or readiness for deployment.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.testing.standard.test-design
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 06.shared
domain: testing
disciplines: [agentic, architecture]
kind: standard
purpose: Require precise, deterministic and honestly scoped tests without duplicating owner-specific evidence requirements.
portability: {class: source-only, targets: []}
used_by:
- id: shared.testing.workflow.write-and-verify-tests
  path: .agentic/shared/testing/workflows/write-and-verify-tests.md
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Test design

Apply when adding or changing tests. Use the
[writing workflow](../workflows/write-and-verify-tests.md) to apply this standard.
This does not require a repository-wide test rewrite, a new framework or a new
physical test layout.

## Ownership and scope

Find the requirements for the behaviour's owner. For Core, Platform and app
work, use the [product testing index](../../../03.product/tests/README.md).
Use the existing [shared CI taxonomy](../../../../docs/06.shared/rules/concerns/ci-quality.yml)
for test types, categories and their roles; do not invent a competing vocabulary.
A type describes the proof boundary; a category describes what it proves.
Select relevant cases from the owner's requirements and the change's risks,
not a fixed checklist of every type and category for every function.

Keep the closest precise proof with its owner. Add consumer or integration
proof when the guarantee crosses a boundary. A fake-backed repository test can
prove the caller's decisions, but cannot establish real database behaviour.
Startup success cannot establish CRUD, migration or lifecycle correctness.

## Cases and assertions

- Give each case a descriptive name or label identifying its condition and
  expected behaviour, using the owning runner's existing format.
- Make setup, the operation and the expected outcome distinguishable. Test
  through the supported public boundary where that is the claimed contract;
  do not expose private implementation details solely to make them testable.
- Assert the promised value or failure and relevant effects, including work
  that must not happen. For an invalid create request, an expected validation
  failure does not by itself prove that no repository write occurred.
- Cover accepted, rejected and boundary cases required by the contract.
  Distinguish missing, null and empty values where the contract does. Do not
  alter production semantics merely to simplify fixtures or assertions.
- Keep expected results independent of the implementation under test. Calling
  the same validator to compute an expected answer can reproduce its mistake.
  Counts, truthiness and broad snapshots must not replace precise assertions
  on the material contract.
- Apply the existing [assertion-sensitivity review](../../standards/require-change-completion.md#consolidated-source-review):
  identify a plausible wrong outcome and the exact assertion rejecting it.
  Follow that owner's bounded-counterexample guidance when sensitivity is
  uncertain; this is not a requirement for universal mutation testing.

## Fixtures, dependencies and lifecycle

- Reuse suitable owner-provided helpers at supported dependency boundaries.
  Use valid defaults, then vary the condition being tested. Keep mutable
  fixtures isolated between cases and avoid copying production decision logic
  into fakes. A fake must model the dependency behaviour the case relies on.
- Control time, identifiers, randomness and scheduling through supported seams
  where deterministic values matter. Tests of actual system clocks or UUID
  generation should assert their real contracts, not arbitrary exact values.
  Avoid timing sleeps when explicit completion or synchronisation is available.
- Await asynchronous work and surface failures to the runner. Restore mocks
  and global state, close resources and clean test-owned temporary data even
  when assertions fail. Cleanup failures must remain visible.
- Keep external dependencies explicit. Local tests must not silently fall back
  to live credentials, shared data or production services. Real-service proof
  follows the owning environment and permission workflow, with isolated data
  and governed cleanup; this standard grants no deployment or deletion authority.

## Discovery and proof limits

Use the owning runner's existing file conventions and configuration. Establish
that the command discovers and executes the intended cases, and that compiled
tests use current sources rather than stale output. A successful command with
no relevant cases is not evidence. Type-level rejection needs its owning
compiler assertions, not a runtime test or a successful package build alone.

For diagnostic behaviour, follow the existing
[diagnostic workflow](../../workflows/verify-diagnostic-coverage.md), including
its real-caller, accuracy, propagation, disclosure and failure-isolation proof.
Do not introduce a second diagnostic registry or treat a schema-valid record as
proof that its explanation is correct.

Do not hide an in-scope failure by skipping a case, weakening its assertion or
regenerating expected output without reviewing the contract. Record proof
boundaries honestly: fake, local runtime, container and live AWS evidence are
different. Follow the existing
[completion and verification rules](../../standards/require-change-completion.md)
for review, check selection, freshness and reporting. These prose requirements
guide authoring and review; metadata or taxonomy validation does not enforce
assertion quality or demonstrate their adoption by existing tests.

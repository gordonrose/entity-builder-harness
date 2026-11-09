<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.tests.readme
version: 6
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: documentation
purpose: Locate existing product test requirements by Core, Platform and app ownership.
portability: {class: source-only, targets: []}
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
-->
# Product test requirements

When changing a Core value, a Platform runtime capability or an app feature,
first find the testing requirements owned by that layer. This folder gives
those existing requirements separate homes. Actual tests and their runners
remain in their owning packages, apps and products.

| Owner | Source scope | Canonical requirements |
| --- | --- | --- |
| Core | `packages/core/**` | [core/standards/test-requirements.yml](core/standards/test-requirements.yml) |
| Platform | `platform/**`, including adapters and test helpers | [platform/standards/test-requirements.yml](platform/standards/test-requirements.yml) |
| App | `apps/**` and `products/**`, including feature behaviour and composition | [app/standards/test-requirements.yml](app/standards/test-requirements.yml) |

Each YAML standard retains its existing `test_taxonomy`: test types and their
roles, minimum evidence, categories to prove and weak substitutes to reject.
Platform and app standards also retain their existing named testing rules.
The shared [CI quality rules](../../../docs/06.shared/rules/concerns/ci-quality.yml)
still define the common test vocabulary, category meanings and substitute limits.

For example, changing UUID validation belongs to Core: its standard names
accepted/rejected inputs and type-level compatibility as evidence. Changing
registration or shutdown belongs to Platform; wiring a mounted feature into an
app belongs to the app standard. A cross-layer change may need more than one
owner's proof. Reading these requirements does not establish that the required
cases exist or pass.

## Writing and reviewing tests

Use the shared [test-design standard](../../shared/testing/standards/test-design.md)
for how a case should be written: precise assertions, isolated fixtures,
controlled dependencies and honest proof boundaries. Follow the
[writing and verification workflow](../../shared/testing/workflows/write-and-verify-tests.md)
to inspect the owner, plan cases, write them using existing runners, review
their assertions and verify the finished change.

<!-- deterministic-check: allow reason="explains the division of responsibility between linked standards; it adds no executable process" -->
The owner standards above still say **what must be proved**. The shared guidance
says **how to construct and verify that proof**; it references the existing
taxonomy, completion and diagnostic rules rather than replacing them. For
example, a Core nullable-value test must distinguish null from omission if its
contract does; a fake-backed app test cannot establish real database behaviour.

## Where tests live

The shared [execution standard](../../shared/testing/standards/test-execution.md)
owns **when to run proof**. Feedback decisions are visible in the existing
[check catalog](../../../scripts/repo/check-selection/checks.yml); the
[selector guide](../../../scripts/repo/check-selection/README.md#development-feedback)
shows read-only inventory, fast development selection and full integration.
Owner requirements and test types are unchanged. Generated run observations live
in ignored `.cache/test-runs/`, not a new test ledger in chat logs.

The [layout standard](standards/test-layout.md) distinguishes capability, theme
and test type. Tests stay with their owner: `packages/core/tests/`, each
`platform/<capability>/tests/` or adapter's `tests/`, and each app/product's
`tests/`. They are not collected into a new repository-wide execution tree.

For example, Core date-time behaviour lives in
`packages/core/tests/shared/time/unit/`, with compile-pass/fail assertions in
the sibling `type-level/` group. An app's mounted test-entity workflow lives in
`apps/entity-smoke/tests/test-entity/integration/`. Provider-port translations
use `contract/`; real database behaviour uses `integration/`. Source/package
boundary checks live in `test-infrastructure/static-validation/`; regressions
for the test runners themselves live in `test-infrastructure/unit/`.
Runtime suffixes identify execution mode, not test type. A public import alone
does not make a case a contract test. Create only groups with actual cases.

The [coordinated migration plan](../plans/migration/product-test-layout.md)
maps the remaining 166 original paths across 21 owners. The earlier
[time](../plans/migration/core-shared-time-tests.md) and
[UUID](../plans/migration/core-shared-uuid-tests.md) plans retain their pilot
evidence. Each existing runner discovers source runtime tests recursively and
maps them to compiled output. It rejects missing output and zero cases,
propagates child failures, and excludes stale compiled-only/type-only fixtures.
Owner-local disposable regression drivers exercise this discovery. The shared
fixture is test-only infrastructure, not a production testing framework.

## Migration and verification

The [migration plan](../plans/migration/owner-specific-test-requirements.md)
records the exact source sections, retained legacy pointers and compatibility
choices. The original layer files continue to own their other architecture
rules; the extracted testing bodies live only here.

The existing [taxonomy checker](../../../scripts/01.harness/check-rule-test-taxonomy.sh)
reads its seven configured owners from the shared CI file. Its three product
entries now point here. An explicit maintenance check is:

```bash
bash scripts/01.harness/check-rule-test-taxonomy.sh --self-test
```

This checks taxonomy structure, vocabulary, evidence wording and its rejection
fixtures. It does not execute product tests or prove assertion quality. The
checker remains dormant in ordinary verification, as recorded in the
[diagnostics closeout](../../shared/plans/implementation/governed-diagnostic-coverage.md).
That requirement extraction changed no npm command or runner. The subsequent
layout migrations update test locations, compiler discovery, runner discovery
and their existing command/reference consumers; command identities remain.

The shared [change-completion standard](../../shared/standards/require-change-completion.md)
and [diagnostic workflow](../../shared/workflows/verify-diagnostic-coverage.md)
retain their existing responsibilities for assertion sensitivity, diagnostic
proof, focused verification and reporting.

The layout migration preserves existing cases; it is not a test-quality retrofit
or proof of complete production coverage. Runner consolidation is deliberately
out of scope. Local/fake-backed tests do not prove disposable-database, container
or AWS behaviour. `entity-smoke-runtime` now registers the feature's typecheck
and source-led runtime suite. It is development feedback and reusable local
proof, not real-database, packaged-image or AWS acceptance. Historical migration
limitations remain in the coordinated plan; diagnostic partial debt is unchanged.

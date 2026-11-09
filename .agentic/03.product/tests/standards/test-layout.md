<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.tests.standard.layout
version: 2
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: standard
purpose: Keep product tests owner-local and distinguish capability, theme, test type and execution mode.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Product test layout

Apply to new test groups and explicitly approved migrations in Core, Platform
and apps/products. Existing unmigrated tests remain discoverable in their
current locations; a narrow fix does not require reorganising the package.
Use the [owner requirements](../README.md) for required evidence and the
[shared design standard](../../../shared/testing/standards/test-design.md)
for assertion quality. Layout does not establish coverage.

## Capability, theme and test type

Keep tests under the owning package/app/product's `tests/` folder. Use
`tests/<capability>/<theme>/<test-type>/` where both capability and theme
clarify ownership; omit redundant levels for a small owner. App feature tests
may use the feature as their capability. Do not invent empty groups or require
every source file to have a matching test file.

For example, Core's shared time tests live at:

```text
packages/core/tests/shared/time/
  unit/
    date-time-runtime.test.ts
    clock-runtime.test.ts
    request-context-runtime.test.ts
  type-level/
    time-types.test.ts
```

Choose the test type by what the case proves, using the existing
[CI taxonomy](../../../../docs/06.shared/rules/concerns/ci-quality.yml).
`unit/` covers isolated owned behaviour; `contract/` covers agreed interfaces
and compatibility; `integration/` exercises collaborating components through
their actual boundary. Importing a public export alone does not make a test
a contract test. `type-level/` is the filesystem spelling of taxonomy ID
`type_level`: compile-pass, compile-fail, inference and narrowing assertions.
Use hyphenated folder spellings for underscore taxonomy IDs:
`type_level` becomes `type-level/` and `static_validation` becomes
`static-validation/`. These are filesystem spellings, not new test types.

Create a type directory only when real cases belong there. A file with mixed
proof types should be split during its approved migration, not labelled a
contract test merely because some assertions concern public types.

## Execution, fixtures and helpers

In the migrated owners, `*-runtime.test.ts` is compiled and executed by the existing
runtime command; `*-types.test.ts` is checked by the existing no-emit compiler.
These suffixes describe execution, not proof type: runtime can include unit,
contract or integration cases. Preserve each owner's supported suffix/command
contract until its own approved migration adapts it.

Keep fixtures and helpers at the narrowest common owner: inside the relevant
type folder for local use, or beside the type folders when shared by that
theme. Name support files without executable-test suffixes. Helpers must not
execute cases on import or become production dependencies. Do not move reusable
Platform test helpers out of their existing `platform/testing` owner.

## Migration and discovery safeguards

Follow the [path migration workflow](../../../01.harness/workflows/migrate-artifact-paths.md)
for existing cases. Inventory assertions, table inputs, negative type checks,
fixtures, imports and active references before moving them. Record retained
legacy groups and compatibility decisions; do not duplicate cases via wrappers.

Update both compilation and execution discovery. Prove nested cases run once,
type-only fixtures are not executed, stale compiled-only tests are not selected,
missing compiled tests fail, and child failures remain nonzero. Keep existing
flat tests working during staged migration. Do not replace or consolidate
other owners' runners as an incidental part of this pilot.

Use the [writing workflow](../../../shared/testing/workflows/write-and-verify-tests.md)
for source review and verification. The migrated owners implement these mechanics;
layout and discovery migration does not establish complete behavioural coverage
or replace an owner's separate real-service, container or live proof.

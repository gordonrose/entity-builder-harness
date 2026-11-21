<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.migration.product-test-layout
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: migration-plan
purpose: Migrate existing Core, Platform, app and product test ownership and discovery without changing production behaviour.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Product test layout migration

## Scope and compatibility

One coordinated migration across the 21 existing test owners. Preserve existing
assertions, table inputs, type expectations, test ordering within each suite,
fixtures and owner bootstrap semantics. Existing time/UUID and runner-unit groups
already follow the layout and stay in place. Split the remaining mixed shared
JSON, identity, message and result fixtures into their thematic groups.

The table below is the pre-edit source/destination inventory. Type is selected
from the exercised boundary, not the runtime suffix: Core isolated primitives
and in-memory implementations are unit tests; cross-capability diagnostic and
provider-port translation suites are contract tests; coordinators, mounted
apps, product workflows and real database tests are integration tests.
Support data used to construct a contract does not itself imply a second test
type. Compile-only files are type-level; source/package boundary checks belong
to test-infrastructure/static-validation (taxonomy static_validation).
No empty test-type folders or wholesale test-quality retrofit is required.

Compatibility choice for moved files: retired, with active references updated.
Owner tests/ directories and runner entrypoints remain supported. No forwarding
wrappers or copied executable suites. Historical commitLogs and retirement
evidence retain their original references. Earlier active plans and READMEs
must point to the current tests or explicitly explain their historical scope.

## Consumer inventory and implementation

- Retain each runner's package shims, exported JSON checks, environment choices
  and command identity. Extend its own discovery to map nested source fixtures
  to compiled output, ignoring stale compiled-only files and failing on missing
  output, zero cases and child failures. Preserve special compiled ESM/CJS roots.
  Do not consolidate runners or add a new test framework.
- Extend owner runtime compiler globs and exact integration/type fixture paths;
  preserve owner rootDir, dependencies and public package boundaries.
- Move relative imports and import.meta-relative file references to equivalent
  targets; update exact paths in npm commands, shell/tools, review test entries,
  compiled payload fixtures and docs. Keep provider/runtime sources unchanged
  except a strictly necessary test-path consumer correction reviewed separately.
- Preserve all diagnostic source hashes/statuses unless an owning executable
  reference consumer actually changes. Test-only files stay excluded from
  runtime adoption. Reconcile path-only review-source changes explicitly.
- The unfinished entity-smoke runner has no suitable registered check. Repair
  its local bootstrap/discovery within test plumbing, run direct proof with that
  limitation recorded, and do not claim missing feature production proof.
- Inventory normal, assertion-failure and missing/stale output paths for every
  changed discovery owner. Use the existing Core runner regressions and bounded
  owner substitutions to reject omitted nested tests, duplicate membership,
  swallowed child failures and accidental type-only execution.

## Planning, verification and recovery

Run the existing migration planner for each source/destination pair before
retirement, retain bounded reference summaries and classify historical versus
active references. Validate each pair after the move with this plan. Review
relative/compiled forms separately; a full-path checker cannot prove them.

Capture each original suite, including its imports, and compare expected
path-adjusted target text after moving. For split shared groups compare assertion
and negative-type multisets plus fixture/table source. Review all path-sensitive
literal changes. Preserve the existing suite's internal order and side effects.
Metadata and path checks alone do not prove semantic equivalence.

After source review and stable preparation, execute all suitable registered
package units and affected tooling regressions using the selector. Run type-only,
boundary and runtime discovery through each real owner. Real disposable PostgreSQL
proof follows its existing workflow and environment availability; never fall
back to a live database or cloud credentials. Container/provider/live acceptance
is not granted by this migration. Record the existing 23 feature diagnostic
review findings separately from new migration regressions.

Recovery reverses only the inventory moves/reference corrections from pre-edit
content, preserving prior uncommitted work. Do not reset Git, remove broad caches,
commit or mutate cloud state. No ADR is needed for internal test paths with no
public API or owner-layer change. A genuine out-of-scope production issue is
reported, not silently fixed as part of relocation.

## File inventory

Pre-edit suite hashes and the remaining mixed shared fixtures are retained in
`commitLogs/2026/nov/06/2026-11-06-17-07-new-chat-session/test-layout-baseline.json`.
All 166 original paths were planned with the canonical planner before retirement.
Seven supplementary plans cover the PostgreSQL executable protocol fixture and
six isolated helpers/validators refined from provisional integration placement
to unit placement. Historical commit logs are intentionally not rewritten.

Self-review covers all 21 owners' source/compiled roots, npm entrypoints, compiler
globs, package shims, imports, boundary commands, diagnostic-review references,
selector declarations and documentation. Production module structure is not
changed; the shared fixture is test-only infrastructure owned by Core's existing
runner regressions. The entity-smoke bootstrap and product app shim are necessary
test plumbing corrections, not production features.

Preservation comparison: 162 relocated files match their expected path-adjusted
bytes; two are deliberately split into result/message/JSON/identity
groups. Their combined 56 non-import/non-log statements and five negative type
expectations match the originals exactly. The PostgreSQL fixture's metadata
date subsequently changes, not its assertions or version. Existing time/UUID cases
remain unchanged. Runtime logging now identifies the split groups.

CloudWatch verification exposed one additional mixed fixture: a runner self-test
inside the lifecycle contract suite supplied compiled-only files while discovering
sources from the real checkout. Extract its three existing cases into the owner's
test-infrastructure unit driver, retain every status/output/stderr assertion, and
run the child in its isolated fixture directory with matching source stubs. All
SDK/diagnostic cases remain in the lifecycle suite. No production code changes.
This correction reopens CloudWatch proof; other owner results are not upgraded.

The full product check also exposed a stale boundary-test allowlist from the
earlier entity-smoke implementation. The product manifest and package dependencies
already compose both public app roots, as permitted by the owning platform/runtime
workflow; the test still allowed only platform-smoke. Correct this test-only
consumer to recognise exactly those two roots, assert both dependencies, and
explicitly reject undeclared apps, app internals, Core and Platform imports.
Keep all existing boundary assertions and production files unchanged. This is
the fourth reviewed non-pure move, alongside the two shared splits and CloudWatch
extraction. Rerun product proof and any wider registered consumer invalidated by
the changed test input; retain the original failed report as evidence.

Material wrong outcomes and rejecting assertions are in the reusable
`packages/core/tests/test-infrastructure/helpers/runtime-runner-fixture.ts`:
duplicate/omitted nested cases fail the exact ordered output assertion; stale or
type-only execution exits with fixture codes 91–93; missing compilation must
fail before any output; zero cases must fail; symlinks must fail before execution;
a child failure must stop later cases and retain the owner's existing nonzero
contract (PostgreSQL normalises to 1; other owners preserve 7). Each owner calls
this fixture against its actual runner. Selector repository-contract tests also
reject a removed shared-helper input, preventing reuse after fixture changes.

Required corrections closed during source review: the JSON type-check invocation
belongs with its JSON declarations; PostgreSQL keeps its original child timeout
and failure-code normalisation; six isolated helpers use unit folders; imported
test helper changes are bound by existing verification units. Existing package
shims, runtime roots and exported JSON checks remain. No test assertion or
negative expectation was weakened. Source/clarity review of README changes
separates authoring requirements, current layout and unproved cloud behaviour.

Final owner checks, path checks, metadata and diagnostic scans are recorded in the
session log. The known 23 entity-smoke/product diagnostic-review findings remain
outside this migration; full-tree acceptance is not claimed. No suitable entity
unit is registered, so its direct type/runtime proof is explicitly separate.

| Source | Destination | Proof type |
| --- | --- | --- |
| `packages/core/tests/audit-runtime.test.ts` | `packages/core/tests/audit/unit/audit-runtime.test.ts` | unit |
| `packages/core/tests/audit-types.test.ts` | `packages/core/tests/audit/type-level/audit-types.test.ts` | type-level |
| `packages/core/tests/authn-runtime.test.ts` | `packages/core/tests/authn/unit/authn-runtime.test.ts` | unit |
| `packages/core/tests/authn-types.test.ts` | `packages/core/tests/authn/type-level/authn-types.test.ts` | type-level |
| `packages/core/tests/authz-runtime.test.ts` | `packages/core/tests/authz/unit/authz-runtime.test.ts` | unit |
| `packages/core/tests/authz-types.test.ts` | `packages/core/tests/authz/type-level/authz-types.test.ts` | type-level |
| `packages/core/tests/config-runtime.test.ts` | `packages/core/tests/config/unit/config-runtime.test.ts` | unit |
| `packages/core/tests/config-types.test.ts` | `packages/core/tests/config/type-level/config-types.test.ts` | type-level |
| `packages/core/tests/core-boundaries.test.mjs` | `packages/core/tests/test-infrastructure/static-validation/core-boundaries.test.mjs` | static-validation |
| `packages/core/tests/diagnostic-delivery-fixture.ts` | `packages/core/tests/diagnostics/helpers/diagnostic-delivery-fixture.ts` | helpers |
| `packages/core/tests/diagnostic-delivery-runtime.test.ts` | `packages/core/tests/diagnostics/contract/diagnostic-delivery-runtime.test.ts` | contract |
| `packages/core/tests/diagnostic-delivery-types.test.ts` | `packages/core/tests/diagnostics/type-level/diagnostic-delivery-types.test.ts` | type-level |
| `packages/core/tests/diagnostic-record-runtime.test.ts` | `packages/core/tests/diagnostics/contract/diagnostic-record-runtime.test.ts` | contract |
| `packages/core/tests/diagnostic-record-types.test.ts` | `packages/core/tests/diagnostics/type-level/diagnostic-record-types.test.ts` | type-level |
| `packages/core/tests/diagnostics-runtime.test.ts` | `packages/core/tests/diagnostics/unit/diagnostics-runtime.test.ts` | unit |
| `packages/core/tests/diagnostics-types.test.ts` | `packages/core/tests/diagnostics/type-level/diagnostics-types.test.ts` | type-level |
| `packages/core/tests/events-runtime.test.ts` | `packages/core/tests/events/unit/events-runtime.test.ts` | unit |
| `packages/core/tests/events-types.test.ts` | `packages/core/tests/events/type-level/events-types.test.ts` | type-level |
| `packages/core/tests/files-runtime.test.ts` | `packages/core/tests/files/unit/files-runtime.test.ts` | unit |
| `packages/core/tests/files-types.test.ts` | `packages/core/tests/files/type-level/files-types.test.ts` | type-level |
| `packages/core/tests/foundation-diagnostics-runtime.test.ts` | `packages/core/tests/diagnostics/contract/foundation-diagnostics-runtime.test.ts` | contract |
| `packages/core/tests/foundation-diagnostics-types.test.ts` | `packages/core/tests/diagnostics/type-level/foundation-diagnostics-types.test.ts` | type-level |
| `packages/core/tests/i18n-runtime.test.ts` | `packages/core/tests/i18n/unit/i18n-runtime.test.ts` | unit |
| `packages/core/tests/i18n-types.test.ts` | `packages/core/tests/i18n/type-level/i18n-types.test.ts` | type-level |
| `packages/core/tests/localization-runtime.test.ts` | `packages/core/tests/localization/unit/localization-runtime.test.ts` | unit |
| `packages/core/tests/localization-types.test.ts` | `packages/core/tests/localization/type-level/localization-types.test.ts` | type-level |
| `packages/core/tests/logging-runtime.test.ts` | `packages/core/tests/logging/unit/logging-runtime.test.ts` | unit |
| `packages/core/tests/logging-types.test.ts` | `packages/core/tests/logging/type-level/logging-types.test.ts` | type-level |
| `packages/core/tests/monitoring-metric-diagnostics-runtime.test.ts` | `packages/core/tests/monitoring/unit/monitoring-metric-diagnostics-runtime.test.ts` | unit |
| `packages/core/tests/monitoring-runtime.test.ts` | `packages/core/tests/monitoring/unit/monitoring-runtime.test.ts` | unit |
| `packages/core/tests/monitoring-types.test.ts` | `packages/core/tests/monitoring/type-level/monitoring-types.test.ts` | type-level |
| `packages/core/tests/persistence-runtime.test.ts` | `packages/core/tests/persistence/unit/persistence-runtime.test.ts` | unit |
| `packages/core/tests/persistence-types.test.ts` | `packages/core/tests/persistence/type-level/persistence-types.test.ts` | type-level |
| `packages/core/tests/queues-runtime.test.ts` | `packages/core/tests/queues/unit/queues-runtime.test.ts` | unit |
| `packages/core/tests/queues-types.test.ts` | `packages/core/tests/queues/type-level/queues-types.test.ts` | type-level |
| `packages/core/tests/security-diagnostics-runtime.test.ts` | `packages/core/tests/security/unit/security-diagnostics-runtime.test.ts` | unit |
| `packages/core/tests/security-diagnostics-types.test.ts` | `packages/core/tests/security/type-level/security-diagnostics-types.test.ts` | type-level |
| `packages/core/tests/security-runtime.test.ts` | `packages/core/tests/security/unit/security-runtime.test.ts` | unit |
| `packages/core/tests/security-types.test.ts` | `packages/core/tests/security/type-level/security-types.test.ts` | type-level |
| `packages/core/tests/shared-runtime.test.ts` | `packages/core/tests/shared/contract/unit/results-runtime.test.ts` | unit |
| `packages/core/tests/shared-types.test.ts` | `packages/core/tests/shared/contract/type-level/results-types.test.ts` | type-level |
| `packages/core/tests/tenancy-runtime.test.ts` | `packages/core/tests/tenancy/unit/tenancy-runtime.test.ts` | unit |
| `packages/core/tests/tenancy-types.test.ts` | `packages/core/tests/tenancy/type-level/tenancy-types.test.ts` | type-level |
| `packages/core/tests/validation-runtime.test.ts` | `packages/core/tests/validation/unit/validation-runtime.test.ts` | unit |
| `packages/core/tests/validation-types.test.ts` | `packages/core/tests/validation/type-level/validation-types.test.ts` | type-level |
| `platform/adapters/aws/auth/cognito/tests/cognito-adapter-boundaries.test.mjs` | `platform/adapters/aws/auth/cognito/tests/test-infrastructure/static-validation/cognito-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/auth/cognito/tests/cognito-adapter-runtime.test.ts` | `platform/adapters/aws/auth/cognito/tests/contract/cognito-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/auth/cognito/tests/cognito-adapter-types.test.ts` | `platform/adapters/aws/auth/cognito/tests/type-level/cognito-adapter-types.test.ts` | type-level |
| `platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-boundaries.test.mjs` | `platform/adapters/aws/observability/cloudwatch/tests/test-infrastructure/static-validation/cloudwatch-otel-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-runtime.test.ts` | `platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-lifecycle-runtime.test.ts` | `platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-lifecycle-runtime.test.ts` | contract |
| `platform/adapters/aws/persistence/dynamodb/tests/dynamodb-persistence-adapter-boundaries.test.mjs` | `platform/adapters/aws/persistence/dynamodb/tests/test-infrastructure/static-validation/dynamodb-persistence-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/persistence/dynamodb/tests/dynamodb-persistence-adapter-runtime.test.ts` | `platform/adapters/aws/persistence/dynamodb/tests/contract/dynamodb-persistence-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/persistence/postgresql/tests/postgresql-diagnostics.test.ts` | `platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-diagnostics-runtime.test.ts` | integration |
| `platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-boundaries.test.mjs` | `platform/adapters/aws/persistence/postgresql/tests/test-infrastructure/static-validation/postgresql-persistence-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-integration.test.ts` | `platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-persistence-adapter-integration.test.ts` | integration |
| `platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-runtime.test.ts` | `platform/adapters/aws/persistence/postgresql/tests/contract/postgresql-persistence-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/queue/sqs/tests/sqs-adapter-boundaries.test.mjs` | `platform/adapters/aws/queue/sqs/tests/test-infrastructure/static-validation/sqs-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/queue/sqs/tests/sqs-adapter-runtime.test.ts` | `platform/adapters/aws/queue/sqs/tests/contract/sqs-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/queue/sqs/tests/sqs-configuration-runtime.test.ts` | `platform/adapters/aws/queue/sqs/tests/unit/sqs-configuration-runtime.test.ts` | unit |
| `platform/adapters/aws/queue/sqs/tests/sqs-configuration-types.test.ts` | `platform/adapters/aws/queue/sqs/tests/type-level/sqs-configuration-types.test.ts` | type-level |
| `platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-boundaries.test.mjs` | `platform/adapters/aws/runtime/ecs-fargate/tests/test-infrastructure/static-validation/ecs-fargate-adapter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-runtime.test.ts` | `platform/adapters/aws/runtime/ecs-fargate/tests/contract/ecs-fargate-adapter-runtime.test.ts` | contract |
| `platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-types.test.ts` | `platform/adapters/aws/runtime/ecs-fargate/tests/type-level/ecs-fargate-adapter-types.test.ts` | type-level |
| `platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-boundaries.test.mjs` | `platform/adapters/aws/security/dynamodb-rate-limiter/tests/test-infrastructure/static-validation/dynamodb-rate-limiter-boundaries.test.mjs` | static-validation |
| `platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.ts` | `platform/adapters/aws/security/dynamodb-rate-limiter/tests/contract/dynamodb-rate-limiter-runtime.test.ts` | contract |
| `platform/config/tests/configuration-loading-runtime.test.ts` | `platform/config/tests/integration/configuration-loading-runtime.test.ts` | integration |
| `platform/config/tests/evidence-runtime.test.ts` | `platform/config/tests/integration/evidence-runtime.test.ts` | integration |
| `platform/config/tests/platform-config-boundaries.test.mjs` | `platform/config/tests/test-infrastructure/static-validation/platform-config-boundaries.test.mjs` | static-validation |
| `platform/config/tests/platform-config-runtime.test.ts` | `platform/config/tests/integration/platform-config-runtime.test.ts` | integration |
| `platform/config/tests/platform-config-types.test.ts` | `platform/config/tests/type-level/platform-config-types.test.ts` | type-level |
| `platform/contracts/tests/diagnostic-context-runtime.test.ts` | `platform/contracts/tests/contract/diagnostic-context-runtime.test.ts` | contract |
| `platform/contracts/tests/platform-contracts-boundaries.test.mjs` | `platform/contracts/tests/test-infrastructure/static-validation/platform-contracts-boundaries.test.mjs` | static-validation |
| `platform/contracts/tests/platform-contracts-runtime.test.ts` | `platform/contracts/tests/contract/platform-contracts-runtime.test.ts` | contract |
| `platform/contracts/tests/platform-contracts-types.test.ts` | `platform/contracts/tests/type-level/platform-contracts-types.test.ts` | type-level |
| `platform/contracts/tests/registration-diagnostics-runtime.test.ts` | `platform/contracts/tests/contract/registration-diagnostics-runtime.test.ts` | contract |
| `platform/health/tests/diagnostics-runtime.test.ts` | `platform/health/tests/integration/diagnostics-runtime.test.ts` | integration |
| `platform/health/tests/platform-health-boundaries.test.mjs` | `platform/health/tests/test-infrastructure/static-validation/platform-health-boundaries.test.mjs` | static-validation |
| `platform/health/tests/platform-health-runtime.test.ts` | `platform/health/tests/integration/platform-health-runtime.test.ts` | integration |
| `platform/health/tests/platform-health-types.test.ts` | `platform/health/tests/type-level/platform-health-types.test.ts` | type-level |
| `platform/observability/tests/configuration-runtime.test.ts` | `platform/observability/tests/integration/configuration-runtime.test.ts` | integration |
| `platform/observability/tests/configuration-types.test.ts` | `platform/observability/tests/type-level/configuration-types.test.ts` | type-level |
| `platform/observability/tests/diagnostics-runtime.test.ts` | `platform/observability/tests/integration/diagnostics-runtime.test.ts` | integration |
| `platform/observability/tests/metric-diagnostics-runtime.test.ts` | `platform/observability/tests/integration/metric-diagnostics-runtime.test.ts` | integration |
| `platform/observability/tests/metric-lifecycle-diagnostics-runtime.test.ts` | `platform/observability/tests/integration/metric-lifecycle-diagnostics-runtime.test.ts` | integration |
| `platform/observability/tests/platform-observability-boundaries.test.mjs` | `platform/observability/tests/test-infrastructure/static-validation/platform-observability-boundaries.test.mjs` | static-validation |
| `platform/observability/tests/platform-observability-runtime.test.ts` | `platform/observability/tests/integration/platform-observability-runtime.test.ts` | integration |
| `platform/observability/tests/platform-observability-types.test.ts` | `platform/observability/tests/type-level/platform-observability-types.test.ts` | type-level |
| `platform/observability/tests/readiness-diagnostics-runtime.test.ts` | `platform/observability/tests/integration/readiness-diagnostics-runtime.test.ts` | integration |
| `platform/observability/tests/security-diagnostics-runtime.test.ts` | `platform/observability/tests/integration/security-diagnostics-runtime.test.ts` | integration |
| `platform/persistence/tests/diagnostic-delivery-runtime.test.ts` | `platform/persistence/tests/integration/diagnostic-delivery-runtime.test.ts` | integration |
| `platform/persistence/tests/leasing-configuration-runtime.test.ts` | `platform/persistence/tests/integration/leasing-configuration-runtime.test.ts` | integration |
| `platform/persistence/tests/leasing-configuration-types.test.ts` | `platform/persistence/tests/type-level/leasing-configuration-types.test.ts` | type-level |
| `platform/persistence/tests/maintenance-configuration-runtime.test.ts` | `platform/persistence/tests/unit/maintenance-configuration-runtime.test.ts` | unit |
| `platform/persistence/tests/platform-persistence-boundaries.test.mjs` | `platform/persistence/tests/test-infrastructure/static-validation/platform-persistence-boundaries.test.mjs` | static-validation |
| `platform/persistence/tests/platform-persistence-observability-runtime.test.ts` | `platform/persistence/tests/integration/platform-persistence-observability-runtime.test.ts` | integration |
| `platform/persistence/tests/platform-persistence-observability-types.test.ts` | `platform/persistence/tests/type-level/platform-persistence-observability-types.test.ts` | type-level |
| `platform/persistence/tests/platform-persistence-runtime.test.ts` | `platform/persistence/tests/integration/platform-persistence-runtime.test.ts` | integration |
| `platform/persistence/tests/platform-persistence-types.test.ts` | `platform/persistence/tests/type-level/platform-persistence-types.test.ts` | type-level |
| `platform/runtime/tests/context-diagnostics-runtime.test.ts` | `platform/runtime/tests/unit/context-diagnostics-runtime.test.ts` | unit |
| `platform/runtime/tests/diagnostics-runtime.test.ts` | `platform/runtime/tests/integration/diagnostics-runtime.test.ts` | integration |
| `platform/runtime/tests/lifecycle-diagnostics-runtime.test.ts` | `platform/runtime/tests/integration/lifecycle-diagnostics-runtime.test.ts` | integration |
| `platform/runtime/tests/lifecycle-diagnostics-types.test.ts` | `platform/runtime/tests/type-level/lifecycle-diagnostics-types.test.ts` | type-level |
| `platform/runtime/tests/mount-boundary-diagnostics-runtime.test.ts` | `platform/runtime/tests/integration/mount-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/runtime/tests/platform-runtime-boundaries.test.mjs` | `platform/runtime/tests/test-infrastructure/static-validation/platform-runtime-boundaries.test.mjs` | static-validation |
| `platform/runtime/tests/platform-runtime-runtime.test.ts` | `platform/runtime/tests/integration/platform-runtime-runtime.test.ts` | integration |
| `platform/runtime/tests/platform-runtime-types.test.ts` | `platform/runtime/tests/type-level/platform-runtime-types.test.ts` | type-level |
| `platform/runtime/tests/registration-diagnostics-runtime.test.ts` | `platform/runtime/tests/integration/registration-diagnostics-runtime.test.ts` | integration |
| `platform/security/tests/configuration-predicate-diagnostics-runtime.test.ts` | `platform/security/tests/unit/configuration-predicate-diagnostics-runtime.test.ts` | unit |
| `platform/security/tests/jwt-configuration-runtime.test.ts` | `platform/security/tests/unit/jwt-configuration-runtime.test.ts` | unit |
| `platform/security/tests/jwt-configuration-types.test.ts` | `platform/security/tests/type-level/jwt-configuration-types.test.ts` | type-level |
| `platform/security/tests/platform-security-boundaries.test.mjs` | `platform/security/tests/test-infrastructure/static-validation/platform-security-boundaries.test.mjs` | static-validation |
| `platform/security/tests/platform-security-runtime.test.ts` | `platform/security/tests/integration/platform-security-runtime.test.ts` | integration |
| `platform/security/tests/platform-security-types.test.ts` | `platform/security/tests/type-level/platform-security-types.test.ts` | type-level |
| `platform/security/tests/security-certificates-runtime.test.ts` | `platform/security/tests/unit/security-certificates-runtime.test.ts` | unit |
| `platform/security/tests/security-certificates-types.test.ts` | `platform/security/tests/type-level/security-certificates-types.test.ts` | type-level |
| `platform/security/tests/security-operation-diagnostics-runtime.test.ts` | `platform/security/tests/unit/security-operation-diagnostics-runtime.test.ts` | unit |
| `platform/security/tests/security-operation-diagnostics-types.test.ts` | `platform/security/tests/type-level/security-operation-diagnostics-types.test.ts` | type-level |
| `platform/server/tests/builtin-evidence-runtime.test.ts` | `platform/server/tests/integration/builtin-evidence-runtime.test.ts` | integration |
| `platform/server/tests/configuration-omissions-runtime.test.ts` | `platform/server/tests/unit/configuration-omissions-runtime.test.ts` | unit |
| `platform/server/tests/configuration-runtime.test.ts` | `platform/server/tests/integration/configuration-runtime.test.ts` | integration |
| `platform/server/tests/diagnostics-runtime.test.ts` | `platform/server/tests/integration/diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/health-diagnostics-runtime.test.ts` | `platform/server/tests/integration/health-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/metric-diagnostics-runtime.test.ts` | `platform/server/tests/integration/metric-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/platform-server-boundaries.test.mjs` | `platform/server/tests/test-infrastructure/static-validation/platform-server-boundaries.test.mjs` | static-validation |
| `platform/server/tests/platform-server-runtime.test.ts` | `platform/server/tests/integration/platform-server-runtime.test.ts` | integration |
| `platform/server/tests/platform-server-types.test.ts` | `platform/server/tests/type-level/platform-server-types.test.ts` | type-level |
| `platform/server/tests/process-boundary-diagnostics-runtime.test.ts` | `platform/server/tests/integration/process-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/request-boundary-diagnostics-runtime.test.ts` | `platform/server/tests/integration/request-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/request-observation-runtime.test.ts` | `platform/server/tests/integration/request-observation-runtime.test.ts` | integration |
| `platform/server/tests/security-diagnostics-runtime.test.ts` | `platform/server/tests/integration/security-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/startup-configuration-diagnostics-runtime.test.ts` | `platform/server/tests/integration/startup-configuration-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/transport-configuration-diagnostics-runtime.test.ts` | `platform/server/tests/unit/transport-configuration-diagnostics-runtime.test.ts` | unit |
| `platform/server/tests/transport-diagnostics-runtime.test.ts` | `platform/server/tests/integration/transport-diagnostics-runtime.test.ts` | integration |
| `platform/server/tests/transport-diagnostics-types.test.ts` | `platform/server/tests/type-level/transport-diagnostics-types.test.ts` | type-level |
| `platform/testing/tests/config-evidence-runtime.test.ts` | `platform/testing/tests/integration/config-evidence-runtime.test.ts` | integration |
| `platform/testing/tests/diagnostics-runtime.test.ts` | `platform/testing/tests/unit/diagnostics-runtime.test.ts` | unit |
| `platform/testing/tests/mount-boundary-diagnostics-runtime.test.ts` | `platform/testing/tests/integration/mount-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/testing/tests/platform-testing-boundaries.test.mjs` | `platform/testing/tests/test-infrastructure/static-validation/platform-testing-boundaries.test.mjs` | static-validation |
| `platform/testing/tests/platform-testing-runtime.test.ts` | `platform/testing/tests/integration/platform-testing-runtime.test.ts` | integration |
| `platform/testing/tests/platform-testing-types.test.ts` | `platform/testing/tests/type-level/platform-testing-types.test.ts` | type-level |
| `platform/workers/tests/builtin-evidence-runtime.test.ts` | `platform/workers/tests/integration/builtin-evidence-runtime.test.ts` | integration |
| `platform/workers/tests/context-boundary-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/context-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/delivery-boundary-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/delivery-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/health-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/health-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/lifecycle-boundary-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/lifecycle-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/lifecycle-boundary-diagnostics-types.test.ts` | `platform/workers/tests/type-level/lifecycle-boundary-diagnostics-types.test.ts` | type-level |
| `platform/workers/tests/metric-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/metric-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/platform-workers-boundaries.test.mjs` | `platform/workers/tests/test-infrastructure/static-validation/platform-workers-boundaries.test.mjs` | static-validation |
| `platform/workers/tests/platform-workers-process-runtime.test.ts` | `platform/workers/tests/integration/platform-workers-process-runtime.test.ts` | integration |
| `platform/workers/tests/platform-workers-runtime.test.ts` | `platform/workers/tests/integration/platform-workers-runtime.test.ts` | integration |
| `platform/workers/tests/platform-workers-types.test.ts` | `platform/workers/tests/type-level/platform-workers-types.test.ts` | type-level |
| `platform/workers/tests/process-boundary-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/process-boundary-diagnostics-runtime.test.ts` | integration |
| `platform/workers/tests/retry-configuration-runtime.test.ts` | `platform/workers/tests/integration/retry-configuration-runtime.test.ts` | integration |
| `platform/workers/tests/retry-configuration-types.test.ts` | `platform/workers/tests/type-level/retry-configuration-types.test.ts` | type-level |
| `platform/workers/tests/startup-configuration-diagnostics-runtime.test.ts` | `platform/workers/tests/integration/startup-configuration-diagnostics-runtime.test.ts` | integration |
| `apps/entity-smoke/tests/test-entity-runtime.test.ts` | `apps/entity-smoke/tests/test-entity/integration/test-entity-runtime.test.ts` | integration |
| `apps/platform-smoke/tests/configuration-validation-diagnostics-runtime.test.ts` | `apps/platform-smoke/tests/integration/configuration-validation-diagnostics-runtime.test.ts` | integration |
| `apps/platform-smoke/tests/diagnostics-runtime.test.ts` | `apps/platform-smoke/tests/unit/diagnostics-runtime.test.ts` | unit |
| `apps/platform-smoke/tests/platform-smoke-boundaries.test.mjs` | `apps/platform-smoke/tests/test-infrastructure/static-validation/platform-smoke-boundaries.test.mjs` | static-validation |
| `apps/platform-smoke/tests/platform-smoke-runtime.test.ts` | `apps/platform-smoke/tests/integration/platform-smoke-runtime.test.ts` | integration |
| `apps/platform-smoke/tests/platform-smoke-types.test.ts` | `apps/platform-smoke/tests/type-level/platform-smoke-types.test.ts` | type-level |
| `products/kanbien-platform/tests/kanbien-platform-boundaries.test.mjs` | `products/kanbien-platform/tests/test-infrastructure/static-validation/kanbien-platform-boundaries.test.mjs` | static-validation |
| `products/kanbien-platform/tests/kanbien-platform-runtime.test.ts` | `products/kanbien-platform/tests/integration/kanbien-platform-runtime.test.ts` | integration |
| `products/kanbien-platform/tests/kanbien-platform-types.test.ts` | `products/kanbien-platform/tests/type-level/kanbien-platform-types.test.ts` | type-level |
| `packages/core/tests/compatibility/v0-public-contracts.test.ts` | `packages/core/tests/compatibility/type-level/v0-public-contracts.test.ts` | type-level |

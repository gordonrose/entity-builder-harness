<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.shared-rate-limit-configuration
version: 1
status: active
created_on: "2026-11-02"
updated_on: "2026-11-04"
layer: 03.product
domain: security
disciplines: [architecture, security, agentic]
kind: plan
purpose: Complete DIAG-005 by sharing equivalent numeric rate-limit checks without changing caller policy or diagnostic contracts.
portability: {class: source-only, targets: []}
used_by:
- id: shared.plan.diagnostics-backlog
  path: .agentic/shared/plans/implementation/diagnostics-backlog.md
-->
# Shared rate-limit configuration — DIAG-005

## Authority and preservation

User authorised DIAG-005; inventory began 2026-11-01T23:59:15+00:00
(Europe/Dublin). Same recorded Oct27 chat worktree across midnight. No goal,
delegation, installation, network/cloud/deployment or Git mutation. Broader
integration remains at the stable batch boundary; use the two existing focused
security/adapter registered units, not the full repository aggregate.

Platform security owns the equivalent positive-whole-number predicate and safe
companion construction in src/rate-limit-configuration.ts. One public assertion
preserves the direct constructors' RangeError and primary/companion order; a
public failure-record helper lets the adapter's existing environment parser
reuse the predicate/report after its unchanged Number conversion, keeping its
different returned-error contract. Neither function reads a source or calls a
clock, store or provider. Logical fields and direct-option names are finite;
unchecked invalid names fail safely without echoing the supplied name.

Preserve Number.isInteger semantics, including existing positive integers above
the safe-integer range; no new maximum. Preserve wrong-type/non-finite/fractional/
non-positive distinctions and short-circuiting without coercing rejected values.
In-memory snapshots all three options before validation, retains nullish defaults
and bucket-capacity support. Adapter reads table/limit/window in its current
order, stops at the first failed guard, retains all four environment reads and
its existing numeric spellings/missing-value policy. Algorithms, SDK setup,
table/region guards, clock/storage behavior and security definitions stay intact.

## Connected file and predicate inventory

| Owner/consumer | Decision and proof |
| --- | --- |
| platform/security/src/rate-limit-configuration.ts | Cohesive new numeric predicate/report/assertion owner, using existing security definitions, finite logical names and safe runtime guards. |
| platform/security/src/rate-limiting.ts | Replace its local assertion with owning relative import; keep snapshots/defaults/check order and limiter mechanics unchanged. |
| platform/security/src/index.ts | Re-export the two supported helpers; remain export-only. |
| platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts | Preserve all eleven public names as re-exports. Move existing implementation to rate-limiter.ts, replacing duplicated numeric work only. |
| platform/adapters/aws/security/dynamodb-rate-limiter/src/rate-limiter.ts | Existing adapter implementation; use public security assertion and failure record. Number conversion, environment errors, table/region/provider specifics remain local. |
| scripts/repo/module-structure/legacy.v1.json | Remove only this now-clean adapter index allowance; do not refresh any pin or weaken structure policy. This bounded cleanup is part of the authorised relevant refactor. |
| platform/security/tests/configuration-predicate-diagnostics-runtime.test.ts | Retain complete matrix, legacy errors/diagnostic literals, snapshots/defaults/no-coercion/clock order; add public-helper and actual in-memory wiring counterexamples. |
| platform/security/tests/platform-security-types.test.ts | Public helper arguments and forbidden name/field type counterexamples. |
| platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.ts | Retain numeric/environment/limiting/clock/provider tests; add actual adapter helper-call wiring and forced failure before dependent work. |
| Existing security/adapter boundary tests and tsconfigs/package manifests | New local source files are included by existing globs; supported package exports/dependencies unchanged. Run owning registered checks. |
| platform/security/src/diagnostics.ts, Core security and generated catalogs | No definition/name/version/schema changes. Exact security catalog hash and existing caller literals prove preservation. Core text parsing is inapplicable to numeric inputs and remains untouched. |
| Other adapters, server/worker and target callers | Public limiter exports/signatures preserved; no deep imports/private paths found by whole-repo search. No retiring-target runtime/deployment work. |
| .agentic/03.product/standards/config-runtime-settings.md and public-module-structure.md | Existing DIAG-003 reuse/ownership and index requirements apply. Do not duplicate these general requirements. Add only a short owner-specific security direction to the existing Platform workflow if needed. |
| Security package/source and adapter READMEs | Bounded file/export explanation and concrete numeric example using README-writing skill; no unrelated whole-guide rewrite. |
| scripts/repo/diagnostic-coverage/reviews.v1.json | Review changed/new executable owners, preserve statuses/debt; actual wiring and existing predicates are proof, not hashes alone. |
| Backlog and session | Close only DIAG-005 with evidence and activity journal; keep DIAG-006/007 separate. |

Predicate alternatives: numeric success; wrong-type (including object/symbol/
bigint without coercion); NaN/positive and negative infinity; positive/negative
fractions; zero/negative integers. Direct constructors throw existing messages
and records. Adapter environment converts text first, preserving acceptance of
whitespace, hexadecimal, exponent and leading-sign/zero spellings. Missing/empty
sources stay local. New helper name guards reject uncontrolled context before
formatting a RangeError or constructing diagnostic detail.

## Sequence and gates

1. Complete shared implementation, connected adapter cleanup, fixtures and
   bounded documentation/harness guidance. No source moves outside the inventory.
2. Consolidated self-review: compare original exported adapter names and unchanged
   named function bodies, exact errors/record literals, read order and actual
   helper use. A copied local checker must fail injected call/failure assertions.
3. Prepare affected metadata/reviews and pass cheap module-structure/adoption.
4. Run registered platform-security-runtime and
   security-shared-rate-limit-diagnostics, including their types, declarations,
   runtime and package boundaries. These are affected package units, not the
   complete repo test suites. Capture output and timing, print concise verdicts.
5. Check catalog bytes, README links, public exports and scoped whitespace.
   Record outcomes/limits and close all eight DIAG-005 criteria when proved.

## Outcome and activity journal

Consolidated self-review completed before final focused tests. The two helper
forms share one predicate, enforce finite logical context at runtime and retain
the existing direct/returned failure distinction. All existing test matrices
remain; new injection assertions reject copied local checks and ignored returned
failure. The read order, no-coercion and no-dependent-work assertions remain.
All eleven adapter public names are retained. Fourteen original named adapter
bodies compare byte-for-byte after only normalising the shared assertion's name;
only the environment numeric helper intentionally changes internally. Algorithms,
provider calls and original table/region guards are among the retained bodies.

Cheap preparation passed: existing module checker (41 indexes, 22 remaining
legacy allowances, no findings); two governed headers; ten README links/anchors;
security catalog byte hash. Reviewed three changed and two new runtime source
hashes in the existing ledger, preserving adoption statuses/debt. No agent is
editing these verification inputs. Final registered package proof passed; no remaining required correction.

Registered command:

bash scripts/repo/check-selection/script.sh --checks platform-security-runtime security-shared-rate-limit-diagnostics --execute-local --json

Both units executed and passed with zero findings. Security took 25.573253 s;
adapter took 30.997610 s. Runner elapsed was 78.879848 s (79.215 s including the
measuring wrapper): 56.570863 s child commands, 6.701803 s planning, 13.316607 s
runtime identities, 0.410670 s fingerprints, 1.750256 s receipt validation and
0.129862 s other work. These units include types, declaration builds, runtime
fixtures and dependency/provider boundary tests. No full repo suite ran.

Existing baseline hashes prove all eleven adapter exports and fourteen unchanged
named bodies; security catalog bytes remain identical. Existing runtime fixtures
preserve exact primary/related details and error messages for all numeric classes,
nullish defaults, first-error/read order, table/region handling, Number grammar,
SDK isolation and limiting/clock semantics. New direct public-helper type/runtime
cases reject unknown names safely; actual compiled-caller substitution proves
shared use and failure handling rather than coincidentally equal output.

This closes all eight DIAG-005 criteria. The specific shared owner/reuse direction
is in the existing Platform workflow, while general DIAG-003 obligations stay in
their existing standard. No new check framework or governance document kind.
The adapter index's allowance was removed, not refreshed; 22 unrelated legacy
indexes remain. No source edit is needed in public package manifests, existing
build globs, literal diagnostic readers or retiring-target callers. They retain
the same public interface. New files are compiled through existing dependency
imports/globs; actual adapter package proof exercises the changed public index.

README-writing skill applied to a bounded two-helper/file-map update; ten links
and anchors and the exact displayed report matched source/test literals.
Source-matched adoption passed without findings (536 discovered; the remaining
190 legacy and 240 partial/support files remain explicit debt, not completion).
Scoped whitespace passed. Broad integration/deployment proof remains deferred
under the user's stable-batch scope; local package proof is not a live claim.

Activity: inventory started 23:59:15 UTC on Nov1; connected implementation,
fixtures and documentation were completed by 00:04:33 UTC on Nov2. Consolidated
source review, hashes/structural checks and metadata preceded final package
execution; both registered checks completed by 00:07:57 UTC. Closure documentation
followed. No runtime test failed. One read-only attempt to capture full source
bodies exceeded the tool output limit and failed JSON parsing; replaced it with
small export/body-hash inventory without repeating a test. Some discovery/report
output was still unnecessarily verbose; summarise selected fields next time.
No broad-suite retry, installation, Docker, cloud, deployment or Git mutation.

Runner latest-report SHA-256 at completion:
56436c8ae56f00f6a2f48b3435983372b035aea6e26223669c7c63caf5fe1e1c.
This local latest-report is mutable; the runner's keyed receipts are the reuse
source of truth, not a copied JSON report.

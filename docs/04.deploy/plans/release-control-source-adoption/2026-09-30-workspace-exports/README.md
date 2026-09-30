<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-workspace-export-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record compiler-backed package-export and runtime evidence with explicit source-only authority and remaining qualification limits.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->

# Compiler-backed workspace export review — 2026-09-30

The sixteenth delivery unit is complete within its source and local execution
boundary. The three existing image/server/product generators now derive their
runtime package forwarding files from current workspace declarations and actual
compiler emission. They share one implementation instead of three maintained maps.

The [full normalized build](local-build-result.json),
[current-source receipt review](current-source-review.json), and
[verification summary](verification-summary.json) retain exact accepted identities.
These are unsigned local evidence, with release eligibility, operation permission,
whole-estate closure and provider qualification blocked.

## Acceptance

| Check | Exact result |
| --- | --- |
| Fresh hash-locked CPython canonical verifier | Exit 0; 1,834 tests / 57 suites |
| Legacy smoke and provider/network core boundaries | Passed |
| Canonical metadata check | 61 files passed |
| Genuine pinned compiler fixtures | 44 passed; no skips |
| Genuine direct-command compiler fixtures | 5 passed; no skips |
| Distinct canonical plus genuine cases | 1,883 passed |
| Existing all-seven locked build wrapper | Exit 0; all seven passed; empty stderr |
| Selected runtime runners and image preparation | Two runners and one generator passed |
| Independent current-source receipt verification | Passed; 54 consumer refusals checked |

Node 22.23.3, bundled npm 10.9.9, TypeScript 5.9.3 and the existing exact package
lock/verified dependency closure were used. Execution retained the existing
isolated filesystem, private network namespace and bounded-command restrictions.
No container image was built or started by this unit.

## Export accounting

Every runtime receipt accounts for all 38 discovered declarations. Outside a
selected compilation is an explicit remaining obligation, never an exemption.
The image-only server-main alias has separate source-bound evidence.

| Selected runtime | Compiled files | Declared exports selected / outside | Alias | Generated files | Final artifact files |
| --- | ---: | ---: | ---: | ---: | ---: |
| Server tests | 82 | 27 / 11 | 0 | 37 | 119 |
| Image preparation | 137 | 37 / 1 | 1 | 57 | 194 |
| Product tests | 157 | 38 / 0 | 0 | 58 | 215 |

Image preparation now includes `@kanbien/core/files`, `@kanbien/core/localization`
and `@kanbien/core/security`, which were omitted by its handwritten map even
though the compiler produced them. The current-source review explicitly joins
those declarations, source digests, actual outputs and generated forwarding bytes.

The existing server runner selected only
`platform/server/tests/platform-server-runtime.test.js`; the product runner
selected only `products/kanbien-platform/tests/kanbien-platform-runtime.test.js`.
Other emitted test files are not claimed as executed. Two of the seven compiler
configurations are no-emission checks. Static prediction findings remain open.

## Source changes and compatibility

The existing compiler observer records callback-provided output origins in a new
closed observation identity. A new independent export collector, projection
contract and reconciliation contract bind declarations to unique actual CommonJS
outputs. The existing local runtime validates the complete disjoint union of
compiler output and generated files, with a fixed internal driver and a shared
Node helper. Safe public output and all source authority refusals remain in place.

Existing image preparation and server/product test entrypoints remain. Direct
commands now require the documented Linux, pinned Node/TypeScript and Python
validation prerequisites. They freshly re-emit in memory to check existing
output, accepting only an initial compiler tree or the exact prior generated
files. Saved projection flags, stale output, unsafe paths and unknown leftovers
are refused. This direct route does not qualify the installed dependency closure.

Legacy observations remain readable historical formats. The existing container
receipt's embedded build schema was updated to accept the new closed observations;
its Python consumer remains delegated to the common build validator. The old
structural artifact parser retains inert compatibility fixtures and refuses the
new observation-dependent generator. It does not invent a static successful map.

## Failures retained and repaired

The first all-seven attempt passed every compiler, server runtime and image
preparation, then refused product runtime. TypeScript had classified a correctly
resolved npm workspace package as an external library. The narrow repair requires
its exact declared repository path, repository input kind/current digest and
unique actual emission instead of rejecting that classification flag. A genuine
workspace-link fixture reproduces the flag and executes the generated package;
actual external targets and invalid source/emission relationships remain refused.

The first clean verifier caught an existing tampering test's obsolete fixture
path. Its path now uses the shared fixture's `main_output`; the exact artifact
mutation rejection remains unchanged. All 41 payload tests passed after repair.
Both failed attempts remain preserved in owned scratch, with hashes recorded in
the verification summary. Fresh normal-wrapper and complete canonical reruns
supply the accepted evidence above.

## Identities and remaining work

- Build result: `sha256:d728989d9ac3c36c3b6ecd43e5c32e683884798405e92a5b33f325b22a207a2b`.
- Current-source review: `sha256:69962b8d25d9d5a0014ec86e060c32c70357d048cddd1b43b7181107fa468daa`.
- Canonical log SHA-256: `7230c1cd8538a3733f7ebb8deb7a954a9009ac78ffa014d73ec2f7a40d48422b`.

The independent review freshly checks source, runner, toolchain contract, package
lock, selected graph and all 40 reviewed file hashes. It reconstructs the selected
source snapshot and export relationships; recorded output fingerprints remain
producer evidence. It does not rerun commands or independently reinstall packages.

Changed generated bytes need renewed final-artifact qualification. Historical
container receipts are retained and do not qualify this output. This unit does
not prove action behavior, live dependencies, IAM, bootstrap, production stores,
AWS targets or owner adoption. PostgreSQL Stage 6 remains paused.

Next delivery unit: immutable action material and input/default reconciliation
through the existing action collector and operation contracts. Remaining work
includes executable behavior, production supply-chain policy/evidence, durable
provider stores, AWS adapters/preflight, orchestration/adoption and approved
target qualification. No external configuration or resource was changed.

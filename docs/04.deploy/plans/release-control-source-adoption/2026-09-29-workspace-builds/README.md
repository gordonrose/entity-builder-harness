<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-workspace-build-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record bounded workspace build inputs and synthetic local artifact accounting while retaining actual compiler and runtime proof obligations.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Workspace build source review — 2026-09-29

The sixth source unit extends the existing realization gate. The
[build summary](build-summary.json) and [independent inventory](build-inventory.json)
account for **seven builds, 209 source records, 6,596 bindings and 3,958 dependency
edges**, retaining 46 unresolved findings. Earlier dated review snapshots are
unchanged. These build findings have a different scope from whole-estate intake;
their counts cannot be subtracted to claim estate closure.

| Selected configuration | Output mode | Candidate files | Prediction |
| --- | --- | ---: | --- |
| `products/kanbien-platform/tsconfig.check.json` | No emission | 0 | Bounded |
| `platform/server/tsconfig.check.json` | No emission | 0 | Bounded |
| `platform/server/tsconfig.runtime-test.json` | JavaScript | 82 | Bounded |
| `products/kanbien-platform/tsconfig.json` | Declarations | 2 | Unresolved |
| `platform/server/tsconfig.image.json` | JavaScript | 137 | Unresolved |
| `platform/server/tsconfig.json` | Declarations | 3 | Unresolved |
| `products/kanbien-platform/tsconfig.runtime-test.json` | JavaScript | 157 | Unresolved |

A bounded prediction is a supported source interpretation. It is not a compiler
receipt or a passing build. The other rows retain partial candidate sets for
review, never complete artifact membership. Remaining findings include ambient
types, external imports, scoped baseUrl lookup, Node10 workspace resolution,
incremental/composite output and sources outside rootDir. All seven builds
retain compiler/toolchain and exact-artifact proof requirements. Import cycles
are observed rather than assumed to be defects.

Three existing generators are recognized as source data. The image generator
describes 54 generated files and 35 export forwards; the server test runner
describes 29 files and 21 exports; the product runner describes 38 files and
26 exports. Exact audited helper/scaffold identities delimit this grammar.
Changed surrounding behavior is unsupported until reviewed. Each current test
runner selects one immediate runtime-test file. The product build's additional
compiled platform tests are not automatically selected by its runner.

## Actual files versus source predictions

The [synthetic artifact result](synthetic-artifact-result.json) exercises the
public capability using the inert checked-in fixture. Its JavaScript file is
handwritten test data, not genuine compiler output. Local file accounting is
complete; provenance is unproven, source closure and qualification are blocked,
and authorization is false.

The optional artifact mode records actual file bytes, compares membership with
current source candidates, validates recognized shim bytes/targets and observes
selected runtime-test membership. It never executes the compiler, generators,
test runner or artifact. Modified ordinary JavaScript bytes change the recorded
artifact digest; structural matching alone cannot prove those bytes implement
the source. Unknown predictions cannot complete artifact accounting.

This worktree contains no installed TypeScript compiler or actual output tree.
No real compiled artifact was qualified in this unit. The next unit needs an
isolated locked compiler/build path, genuine output receipts and exact runtime
execution evidence.

## Reproduce source review

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --builds --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --expect-inventory-digest sha256:4463320d73478704c1b16cc60e44083e9466b865464eb8344873fb1b99f0b06b
```

Expected exit is **1** with the complete inventory and its open findings.
Changing an observed source or collector invalidates the supplied identity.
The multi-megabyte inventory is a review output, not an accepted input document;
public compilation always recollects sources. No public inventory-file option
or release-result admission is provided for this producer.

The existing artifact command adds a build ID and local artifact directory to
these flags; see the [gate README](../../../../../scripts/04.deploy/operational-realization-gate/README.md).
Closed versioned schemas, 49 collector tests, 50 artifact tests and 19 public CLI
tests cover source correctness, mutation detection and rejection boundaries.
Full clean verification is recorded in the implementation plan and session log.

## Estate intake and next delivery unit

The [estate inventory](current-inventory.json), [open triage](current-triage.json)
and [triage result](current-triage-result.json) contain **312 sources and 200 open
findings**: 195 assigned to Phase 2 and five to Phase 3. Nine new sources are
seven implementation/test modules and two schemas; the seven modules explain
the increased finding count. No prior finding or adoption obligation is waived.
Classification is complete while coverage remains blocked and authority false.

Recorded identities:

- Build inventory: `sha256:4463320d73478704c1b16cc60e44083e9466b865464eb8344873fb1b99f0b06b`.
- Collector: `sha256:5ca0cf3c424742f685ed7cbebc65076b91811d193e9a68600b7760c725933ebc`.
- Estate inventory: `sha256:d6a176de9214c5de15542aa9647629bc8d9a2f509f7edbdb6d0f0ea577845dea`.

Next: qualify a reviewed isolated TypeScript toolchain/build path and reconcile
actual compiler resolution/emission with these predictions. Bind source, lock,
toolchain, generated shims and selected tests to immutable genuine output, then
exercise exact commands. Broader operation semantics/adoption, authenticated
evidence/authority, provider adapters and live target qualification remain later.
The full seventeen-stage matrix remains mandatory.

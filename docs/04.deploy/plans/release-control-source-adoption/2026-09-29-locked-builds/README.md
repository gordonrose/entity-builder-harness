<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-locked-build-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record genuine locked local compiler and selected runtime evidence with explicit source-only authority and remaining container qualification limits.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Locked Local Build Review — 2026-09-29

The seventh delivery unit is complete within its local execution boundary.
The existing operational-realization capability now verifies and runs the
selected Node/npm/TypeScript toolchain and dependency closure, binds actual
compiler inputs and outputs to source identities, and exercises the existing
two selected runtime-test runners and image shim generator in isolated copies.
No application, TypeScript configuration or deployment workflow repair was
needed. Existing source-analysis interfaces and authority restrictions remain.

The [full normalized result](local-build-result.json) is the exact successful
all-seven wrapper output. The [verification summary](verification-summary.json)
records counts, identities, selected test files and verification-log hashes.
These are unsigned local review evidence, not admitted attestations or release
permission. The implementation accepts no saved success receipt as authority.

## Recovery and storage

A WSL restart cleared the original tmpfs worktree and its uncommitted seventh
slice. The six completed slices survived in commits `094d6418` and `27d81529`.
Git connectivity and all 112 saved file objects (10,382,194 bytes) verified.
The task branch was restored from its saved index into persistent ext4 storage;
recorded tool patches recovered the draft, which was reviewed and tested again.
Only this worktree registration was repaired. The canonical persistent folder
uses the existing `AGENTIC_CHAT_WORKTREE_ROOT` override; a friendly
`iaas-release-control-plane` symlink points to it. Build scratch must also be
outside the checkout on persistent disk. No other checkout or branch changed.

## Exact acceptance results

| Check | Result |
| --- | --- |
| Clean Python source validation | Exit 0; 677 tests in 21 suites |
| Legacy smoke and provider/network core boundary checks | Passed |
| Clean validation metadata headers | 39 files passed |
| Real compiler fixtures with verified Node and TypeScript | Exit 0; 33 tests, zero skipped |
| Distinct tests across the two runs | **710 passed** |
| Genuine all-seven build wrapper | Exit 0; seven passed, no local execution findings |
| Existing selected runtime-test runners | Two passed; one immediate test file selected by each |
| Existing image shim generator | Passed; no container built |
| Actual kernel isolation probe | Read-only inputs; external route unavailable; private loopback works |

The canonical source check includes the new 35 orchestration, 55 toolchain,
37 runtime-helper and 42 binding tests, alongside the previous 508 tests.
Compiler fixtures separately exercise the actual pinned compiler; absent tools
or skipped fixtures cannot count as that acceptance proof.

| Configuration | Observed inputs | Resolution records | Emitted files | Extra versus static prediction |
| --- | ---: | ---: | ---: | ---: |
| `platform/server/tsconfig.check.json` | 267 | 672 | 0 | 0 |
| `platform/server/tsconfig.json` | 272 | 662 | 4 | 1 |
| `platform/server/tsconfig.runtime-test.json` | 256 | 668 | 82 | 0 |
| `platform/server/tsconfig.image.json` | 1085 | 3030 | 137 | 0 |
| `products/kanbien-platform/tsconfig.check.json` | 284 | 728 | 0 | 0 |
| `products/kanbien-platform/tsconfig.json` | 245 | 560 | 3 | 1 |
| `products/kanbien-platform/tsconfig.runtime-test.json` | 1106 | 3145 | 157 | 0 |

Each configuration used its own fresh snapshot. The two extra outputs are
`.cache/tsconfig.tsbuildinfo` from the separate declaration builds; their bytes
are recorded. No predicted output was absent. These counts describe the selected
compiler invocations, including two checks configured not to emit files.
Four static predictions still report `unresolved`, and fresh discovery retains
46 findings; successful execution does
not erase source-discovery findings or establish whole-repository coverage.

The server test artifact contains 82 compiled and 29 generated files (111 total).
Its existing runner selects only
`platform/server/tests/platform-server-runtime.test.js`. The product artifact
contains 157 compiled and 38 generated files (195 total); its existing runner
selects only `products/kanbien-platform/tests/kanbien-platform-runtime.test.js`.
Other emitted test files are not represented as executed. Image preparation
contains 137 compiled and 54 generated files (191 total) and selects no tests.

## Identity and execution controls

Node **22.23.3**, bundled npm **10.9.9**, TypeScript **5.9.3**, 61 external
package distributions and 20 workspace links are locked and byte-verified.
Public acquisition is explicit and separate from offline installation and
execution. The host requires Linux x86_64, glibc >=2.28 and bubblewrap support;
this does not pin the operating-system image or final container supply chain.

Compiler snapshots contain only selected sources and verified dependencies.
Runtime snapshots contain compiled artifacts, reviewed generators and verified
dependencies, with no source fallback. Read-only mounts protect inputs;
private network namespaces provide loopback without an external route.
Explicit environments exclude host credentials and Node hooks. Missing sandbox
support fails closed. Time, CPU, output and file limits bound reviewed commands;
this is not a general hostile-program resource scheduler.

The contracts and runner reject unsafe paths/fields, modified dependencies,
missing or swapped compiler/runtime receipts, wrong generators, stale source
identities and incorrect selected-test membership. Successful process exit
alone is insufficient. Numeric diagnostics and hashes are recorded instead of
raw command output. The common consumer rejects this result producer for all
purposes. Every result retains `authorized: false` and blocked source closure,
release eligibility, operation authorization and qualification.

- Result: `sha256:4724812c2efbf86e344519ec90ef1633b19402d360cf9571758f297aa342fcb9`.
- Source: `sha256:9df10ec0208757194ea38d68f11df0baee80be9807713ed138453e10e03fde50`.
- Runner: `sha256:b929a551c1fbfb5ec19000124a8b0b31c004cc220f3431be1420a27ec266dab3`.
- Build inventory: `sha256:e27f35678005a52bc6924835097672c3a71152126a8a2c3315d25f6b552f2b57`.
- Selected caller graph: `sha256:40bf4c1259ebf3a1136bca8db48b2fde221524fea97e306c47266ed415ef6717`.

Independent read-only review validated all nested receipt digests and current
source/runner/inventory/graph identities after relocation. All 3,515 observed
input rows matched current source bytes or verified dependencies. Rehashing 61
cached distributions and reconstructing 7,188 installed-file fingerprints
reproduced the dependency identity. All seven build IDs, output comparisons and
selected runtime memberships matched fresh discovery; every audit exited 0.

## Reproduction

From this branch's repository root, choose an existing persistent scratch
directory outside the checkout and a separate package-cache directory. The
first command is the explicit public-download phase; subsequent execution is
offline. Acquisition can safely resume an exact verified partial cache without
overwriting existing entries.

```bash
bash scripts/04.deploy/operational-realization-gate/verify-local-build.sh \
  --source-root . --acquire-cache /persistent/path/build-package-cache
bash scripts/04.deploy/operational-realization-gate/verify-local-build.sh \
  --source-root . --package-cache /persistent/path/build-package-cache \
  --scratch-root /persistent/path/build-scratch
TMPDIR=/persistent/path/build-scratch \
  bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh \
  --python /usr/bin/python3
RELEASE_CONTROL_NODE=/verified/node/bin/node \
  RELEASE_CONTROL_TYPESCRIPT_ROOT=/verified/typescript/package \
  RELEASE_CONTROL_REQUIRE_TYPESCRIPT_TESTS=1 \
  TMPDIR=/persistent/path/build-scratch \
  python3 -B scripts/04.deploy/operational-realization-gate/test_typescript_observer.py
```

Compiler fixture paths must refer to the verified pinned distributions; their
identity/version checks reject incompatible tools. The accepted run used the
persistent `iaas-release-control-recovery` directory beside the restored worktree
for caches, verified tools, scratch and raw local logs. These private host paths
are not part of the normalized result or its identity. A diagnostic
`--configuration` subset cannot substitute for the all-seven acceptance run.

## Repairs and remaining delivery queue

An initial clean verification was interrupted by an edit to its executing smoke
script; it was rejected and rerun from frozen files. The accepted clean run
passed all 677 tests. The first genuine build run passed four configurations and
failed three: Node10/baseUrl resolution probes containing `node:` were rejected
too early. The observer now treats unsupported existence probes as absent
without filesystem access, while explicit unsafe reads and writes still fail.
Positive and negative real-compiler regressions were added; all 33 fixtures and
the complete seven-build rerun then passed. Transport interruptions during
public cache acquisition were handled by bounded retries and verified resume,
without changing pins. Draft runtime link arguments and cross-receipt bindings
were corrected and covered by focused negative tests.

The next delivery unit is isolated final-container construction and exact-command
qualification for this selected artifact: bind its build inputs, base image,
constructed image digest, startup verifier and selected runtime commands to
fresh evidence under the same authority boundary. First hosted source validation
is a separate acceptance step after approved publication; action availability,
Python setup, wheel installation and the timeout remain unproven on GitHub.
Publication and required-check activation are not authorized by local success.

Wider Phase 2 adoption, dynamic and remote-action semantics, authenticated
evidence admission, durable operation controls, provider adapters/stores and
explicitly approved live qualification remain open. PostgreSQL Stage 6 remains
later. Earlier dated estate counts are historical snapshots, not current coverage
claims. No source finding, seventeen-stage gate or later qualification duty has
been waived. No local stop condition remains; external publication and provider
mutation remain outside this completed unit.

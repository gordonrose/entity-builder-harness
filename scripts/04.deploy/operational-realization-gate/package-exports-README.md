<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.readme.operational-realization-package-exports
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: readme
  purpose: Explain fresh compiler-bound package export reconciliation, direct compatibility and retained source obligations.
  portability: {class: reusable, targets: [entity-builder]}
  used_by:
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Compiler-bound workspace exports

The existing locked local build now connects a workspace export declaration to
its actual TypeScript input, actual emitted JavaScript bytes, deterministic
runtime package shim and observed runtime artifact. The image preparer, server
runtime tests and product runtime tests share one generator; their handwritten
package maps are removed.

`package_export_inventory.py` independently discovers every package manifest and
literal export. Its public inventory hashes declaration values and preserves all
original source findings. `package_exports.py` joins that inventory to the
versioned compiler emission observation and constructs a closed projection and
reconciliation receipt. `workspace-runtime.mjs` validates that projection and
materializes exactly its expected shim bytes. `local_runtime.py` supplies the
isolated runner and compares the complete resulting artifact tree.

## Scope and refusal

The collector accepts literal executable source targets and literal package
subpaths. Conditions, wildcards, arrays, traversal, duplicate packages, ambiguous
emissions, declarations as executable targets, source drift, changed output
bytes and unsupported manifest entry fields block. Reserved or conflicting
subpaths, including `node_modules` segments in any case, block before generation.
All new schemas are closed and versioned; a self-consistent checksum alone does
not establish the declaration-to-output relationship.

Every discovered export remains in the reconciliation denominator. An export
outside the selected compiler configuration is explicitly recorded as outside
that compilation, with no output claim. An export selected by an observed input
or runtime resolution must have one actual executable emission. Its absence
cannot be hidden by filtering the observed outputs. This proves the selected
configuration; it does not qualify every repository package or implementation.

The existing `@kanbien/platform-server/main` image entry is an executable alias,
not a manifest export. Its separate evidence route requires the exact maintained
configuration mapping, entrypoint import, compiler resolution, source bytes and
actual emission. If the manifest later declares that subpath, the declaration
route applies instead. Neither route grants ownership or business approval.

## Existing callers

The ordinary repository commands keep their entrypoints:

```sh
npm run platform:server:test
npm run product:kanbien-platform:test
node scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs
```

Use the repository's existing build commands to produce the selected outputs
before invoking the image preparer. Direct callers require Node **22.23.3**,
TypeScript **5.9.3**, and Python with the gate's declared validation dependencies
installed. The invoked Node executable is checked through the running parent
process; there is no caller-selected executable argument or tool download.
These stricter prerequisites are intentional. Direct compatibility checks
versions and current bytes; only the locked build separately proves the complete
package dependency closure.

A direct generator always performs genuine read-only compiler re-emission to
compare existing outputs. It accepts a first compiler-only tree or an exact
repeat containing the freshly computed generated shims. Missing, altered,
partial or unknown leftovers fail; the verifier does not rebuild or overwrite
them. Public generators reject all arguments, including saved projection paths.

The isolated locked build compiles once and supplies a fixed, source-bound
internal driver. Its one-use handoff is available only through the shared module
API, not public arguments, environment selection or the presence of a saved
file. The parent independently derives the expected projection and verifies
compiler, generator, helper, driver, input and complete artifact bytes before
and after execution. Old mapless observations remain readable but cannot satisfy
this proof or be repackaged as a modern locked result.

## Evidence and limits

`source-package-export-inventory/v1` preserves every declaration and original
source obligation. `local-workspace-export-projection/v1` is internal normalized
input for deterministic runtime generation. `local-package-export-reconciliation/v1`
binds the independent source inventory, export inventory, compiler observation,
configuration, projection and current implementation/schema policy. Its exact
rows distinguish selected emissions, exports outside that compilation and the
fixed executable alias. It records all expected generated file hashes and sizes.

`local-workspace-runtime-observation/v1` includes that reconciliation, shared
helper and driver fingerprints, copied projection digest, selected runtime tests
and every resulting artifact fingerprint. Modern runtime artifacts must be
exactly the disjoint union of observed compiler outputs and generated shims;
unknown `node_modules` files do not receive an exception. The enclosing locked
build ties the observation to its source snapshot and verified toolchain.

All these results remain source/local evidence. Release eligibility, operation
authorization, qualification and whole-estate closure stay blocked. Compilation
cannot clear executable behavior, workflow/tool boundaries, dependency trust,
owner review or provider/bootstrap obligations. The historical structural-only
artifact parser retains its inert grammar tests and deliberately refuses the
new observation-dependent generator rather than inventing predicted maps.

## Focused verification

```sh
python3 -B -m unittest discover -s scripts/04.deploy/operational-realization-gate -p 'test_package_exports*.py'
python3 -B -m unittest discover -s scripts/04.deploy/operational-realization-gate -p test_workspace_runtime.py
python3 -B -m unittest discover -s scripts/04.deploy/operational-realization-gate -p test_local_runtime.py
python3 -B -m unittest discover -s scripts/04.deploy/release-control/discovery -p test_build_artifacts.py
```

`test_package_exports_direct.py` requires the existing verifier-provided
`RELEASE_CONTROL_NODE` and `RELEASE_CONTROL_TYPESCRIPT_ROOT`; set
`RELEASE_CONTROL_REQUIRE_TYPESCRIPT_TESTS=1` to make missing prerequisites fail.
It compiles small fixtures with the actual toolchain, runs the direct Node test
runner twice, and rejects source, manifest and unknown-output drift without
repairing files. Synthetic observation fixtures separately test adversarial
joins; the real Node renderer tests execute all three consumer shapes. The
canonical clean verifier and full locked repository build remain integration
acceptance steps, not claims made by synthetic fixtures.

The next delivery obligation is to reconcile the emitted relationships into
reviewed estate coverage without erasing executable or ownership blockers, then
continue the accepted control-plane/provider qualification queue. No new
provider, release decision or environment mutation is introduced here.

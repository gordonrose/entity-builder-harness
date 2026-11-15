<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.runnable-program-contract.readme
version: 2
status: draft
created_on: "2026-10-19"
updated_on: "2026-11-15"
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- agentic
- architecture
- security
- sre
kind: capability-readme
purpose: Describe the report-only checker for runnable-program and package-candidate contracts.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.workflow.runnable-program-candidates
  path: .agentic/04.deploy/20-build/workflows/prove-runnable-program-builds.md
-->
# Runnable Program Contract Checker

Before packaging a program, this offline checker verifies that its declared
dependencies are approved and its image command selects the right entrypoint.
It emits only a safe JSON report. It does not inspect source imports itself,
build an image, access a network, publish a package, read a target, or mutate
anything.

```bash
bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh \
  --contract path/to/runnable-program-contract.yml --json

bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh
```

The caller supplies the observed dependency list; the existing source-boundary
checks independently inspect imports. For programs with a `build` declaration,
[`script.py`](script.py) also calls the fixed read-only
[`build-inputs.mjs`](build-inputs.mjs) reader. That reader resolves approved IDs
through the contract's `dependency_bindings`, then derives package names,
exports and transitive dependencies from workspace manifests. For example, if
an approved application acquires an unapproved workspace dependency, the
command reports `workspace-dependency-not-approved` before any compilation.
Legacy contracts without build fields retain their structural checks and do
not require Node. `validate(document)` remains the pure structural function;
the command additionally calls `validate_declared_builds` for declared builds.

The reader can also project one program's checked inputs for the existing
compiler and independent import observers:

```bash
node scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs \
  --program kanbien-core-server
```

This returns repository-relative compiler/export mappings and the approved
workspace/external owners, not source contents or a qualification receipt.
The generic checker bounds each reader call to 30 seconds and suppresses raw
child failures. [`compile.mjs`](compile.mjs) is a separate build command: only
that command invokes the shared compiler. A passing declaration check does not
prove that the package compiles, runs in isolation, or works on AWS.

The checker fails closed with stable codes for missing program records, invalid
image commands, unapproved dependencies, and unsafe evidence field names.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.core-server-dependency-boundary.readme
version: 2
status: draft
created_on: "2026-10-19"
updated_on: "2026-11-15"
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the deterministic local dependency-boundary proof for the Kanbien core server runnable program.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.workflow.runnable-program-candidates
  path: .agentic/04.deploy/20-build/workflows/prove-runnable-program-builds.md
-->
# Core Server Dependency Boundary

This capability proves the local compile boundary of the one declared
`kanbien-core-server` program. It is build-stage only: it does not build a
container, contact AWS or GitHub, select a target, read secrets, publish a
package, or mutate a target.

```bash
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh --json
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh
```

`script.sh` first validates the factual program contract with the generic
runnable-program checker. It then compiles only the declared program into a
temporary directory and emits one safe JSON report. The report derives the
graph from four inputs: TypeScript imports, workspace package manifests, the
lockfile, and compiled JavaScript output.

For example, an import of `@kanbien/platform-server/main` must resolve to the
public source declared by that workspace's `package.json`; this checker no
longer guesses the filename from the import. The shared
[program reader](../runnable-program-contract/build-inputs.mjs) connects the
[program declaration](../../../../../infra/04.deploy/03.product/entrypoints/runnable-program-index.yml)
to workspace names, exports and approved external packages. Node itself supplies
the list of built-in modules. The Python checker reads that information once
through a fixed local command, bounded to30seconds, without running a compiler
or package lifecycle script at that step.

Those declarations say what is allowed, not what the code uses. The checker
still follows literal imports and manifest dependencies independently, then
compares what it found with the program's declared observations. An unused
approved dependency cannot manufacture a passing observation. An unapproved
import fails regardless of its package namespace, and a removed public export
cannot fall back to a guessed directory. The
[binding tests](binding-test.py) exercise these cases with a differently named
temporary package, alongside the real compile/runtime smoke suite.

The contract remains the reviewed approval boundary. The report never widens
it: a newly observed package, product app, persistence package, worker,
relay, PostgreSQL path, staging server, or AWS adapter fails closed. The
temporary compiled output is removed after each command and is not evidence to
commit.

This is a bounded static import check, not analysis of arbitrary computed
imports or dynamic module loading. A successful local report is not container
qualification or evidence that the program is deployed. Reader failures return
finite codes without native output; a failed or unavailable reader cannot yield
a successful dependency report.

`build.sh` is deliberately separate for local inspection and test fixtures. It
requires an explicit caller-owned temporary output directory and contains no
target, registry, provider, or credential settings.

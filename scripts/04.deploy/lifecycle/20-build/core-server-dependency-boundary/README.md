<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.core-server-dependency-boundary.readme
version: 1
status: draft
created_on: "2026-10-19"
updated_on: "2026-10-20"
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
  path: .agentic/04.deploy/workflows/runnable-program-candidates.md
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

The contract remains the reviewed approval boundary. The report never widens
it: a newly observed package, product app, persistence package, worker,
relay, PostgreSQL path, staging server, or AWS adapter fails closed. The
temporary compiled output is removed after each command and is not evidence to
commit.

`build.sh` is deliberately separate for local inspection and test fixtures. It
requires an explicit caller-owned temporary output directory and contains no
target, registry, provider, or credential settings.

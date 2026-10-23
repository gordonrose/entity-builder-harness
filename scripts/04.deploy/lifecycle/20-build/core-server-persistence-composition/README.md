<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.core-server-persistence-composition
version: 1
status: draft
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.core-server-persistence
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the local proof for the future persistence-capable core-server composition.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.plan.implementation.platform-to-target-chain-control
  path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md
-->

# Core-server persistence composition proof

This check proves only a local, provider-neutral composition boundary. It compiles `kanbien-core-server-persistence.app.ts`, injects a fake persistence runtime, and verifies that:

- `/livez` remains live when a dependency is unavailable;
- `/readyz` reflects the injected dependency's readiness;
- persistence acceptance operates through the server using stable, safe outcomes;
- the successor retains bootstrap release verification; and
- shutdown closes the injected runtime.

It deliberately does **not** select PostgreSQL, read credentials, construct a provider adapter, build an image, change a target declaration, or prove a cloud deployment. Those are later gated persistence-scope work.

Run locally:

```bash
bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
```

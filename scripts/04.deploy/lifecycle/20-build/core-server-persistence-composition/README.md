<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.core-server-persistence-composition
version: 2
status: draft
created_on: "2026-10-23"
updated_on: "2026-10-25"
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

The server behavior proof injects a fake persistence runtime. Configuration tests validate the target-selected PostgreSQL settings using synthetic credentials and a fake driver. Neither part connects to a database, builds an image, or proves a cloud deployment.

Run locally:

```bash
bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
```

The same check also validates the compiled runtime payload and the target-owned
configuration shared by server, migration, and restored-record entrypoints.
Sixty invalid-input cases prove rejection before pool creation using a fake
driver; the positive configuration case preserves the 240-second migration
statement deadline. These are local runtime tests, not database or container
qualification.

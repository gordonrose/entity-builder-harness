<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.core-server-persistence-composition
version: 2
status: draft
created_on: "2026-10-23"
updated_on: "2026-10-30"
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

The acceptance matrix also runs the real PostgreSQL target binding against a
fake query pool through the HTTP server. It checks unchanged SQL counts, public
statuses and bodies, failed create/read/delete observations and each create
reconciliation result. A matching row proves current contents, not which call
wrote it. Failed calls retain their own location plus the selected source
primary/eight companions; reconciliation is a separate informational record.
Request observations use the route's operational-log permission, selected
catalogs and existing reporter. Record IDs, digests, queries and native messages
are excluded from diagnostics. Observer failure cannot add queries or change
the selected result. Pool lifecycle delivery is additionally proved by the
compiled process fixture in the platform-shell payload check, including the
actual target callback binding and original cleanup rejection identity.

Acceptance request predicates now also have a separate app-owned diagnostic
catalog. The fixture distinguishes body shape, ID/digest missing/type/format and
query missing/array/type/format, checks original body getter order and first
failure, preserves ignored extra fields, and proves every rejection avoids
persistence. The real HTTP composition emits only logical predicate facts;
callback/logger failures cannot replace its existing400 response. Configuration
and database-operation readers do not accept these request records.

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

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.smoke-test-core-server-persistence-image.readme
version: 3
status: draft
created_on: "2026-10-23"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.core-server-persistence
disciplines: [security, sre]
kind: capability-readme
purpose: Explain the disposable TLS PostgreSQL package qualification for the persistence candidate.
portability: { class: internal, targets: [] }
used_by:
  - id: deploy.command.smoke-test-core-server-persistence-image
    path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh
-->
# Persistence Image Package Smoke

This package-stage test starts disposable local Docker resources only: a TLS
PostgreSQL container and the candidate image. It proves the migration program,
server process, TLS driver path, readiness, a server-mediated record operation,
and that the runtime database principal cannot execute structural DDL.

It does not use AWS, target secrets, target networking, or target data. A
missing Docker engine is a failure for this command; the protected hosted image
workflow is the required qualification route when a developer workstation lacks
Docker.

Before container qualification, the build checks every generated workspace
export and loads the four guarded compiled entrypoints without starting them.
The Docker build repeats import resolution against the assembled dependency
payload, so missing external driver dependencies cannot be hidden by the
workstation's installed packages.

The local negative fixture command is:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh
```

It rejects missing wrappers, package subpath exports, the PostgreSQL driver,
entrypoint exports, and compiled shim targets. It does not replace the
container qualification command or published-digest custody evidence.

The payload regression also exercises the publication workflow's actual
qualification block and image-builder shell with controlled command boundaries.
The builder owns declaration coverage, scope health, runnable-program validation
and composition; publication invokes it once before container qualification and
provider credentials. Each required check still stops progression on failure.
These local tests do not execute CI, publish an image or establish package custody.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.smoke-test-core-server-persistence-image.readme
version: 4
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


## Local public-image recovery

When native qualification fails because the workstation Docker credential helper
is unavailable, an explicitly authorized local recovery can isolate the client
configuration for this package's public images:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualify-local-public-images.sh --tag kanbien-core-server-persistence:local-public-recovery --port 39456
```

The wrapper resolves the effective Docker context or host before isolation,
requires a local Unix socket, and compares the original engine ID with the
isolated connection before building and after each stage. It clears inherited
Docker, Buildx and BuildKit selectors, then pins the same socket and the default
local builder. It invokes the existing governed image build followed by the
existing image smoke, preserving their preflights and stopping on failure.
Child failure exits retain the original numeric status.

The private temporary Docker configuration contains only empty anonymous
`auths` entries for Docker Hub and `gcr.io`; it contains no credentials,
credential-helper settings or copied normal configuration. These entries
suppress Docker's automatic native-helper discovery. The temporary directory
is removed on success, failure or interruption; stored configuration, credentials,
context selection and daemon settings are not changed. Raw configuration and
socket/engine identifiers are not printed by this wrapper.

This optional recovery accepts only the reviewed canonical builder, smoke,
Dockerfile and image-contract bytes. It derives and validates their public
frontend, Node, pinned distroless and PostgreSQL image declarations. Any owner
change fails with `local-public-recovery-owner-review-required`; review those
changes and deliberately update the wrapper's reviewed hashes before using this
recovery again. The normal package commands remain available independently.
Private registries, alternate builders, arbitrary build flags and publication
are outside this procedure. A successful run is local container qualification,
not CI, published custody or live target proof.

The payload suite includes `local-public-recovery-test.py`, which substitutes
controlled Docker and command boundaries and proves binding, ordering, failure
status, original-configuration preservation and temporary cleanup without
contacting an engine. Docker's documented selection and configuration behavior
is described in [Docker CLI configuration](https://docs.docker.com/reference/cli/docker/)
and [Build tool variables](https://docs.docker.com/build/building/variables/).
Anonymous entries prevent auto-detection as implemented by
[Docker's configuration loader](https://github.com/docker/cli/blob/master/cli/config/config.go)
and [ContainsAuth](https://github.com/docker/cli/blob/master/cli/config/configfile/file.go).

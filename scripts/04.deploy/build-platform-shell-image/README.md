<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.build-platform-shell-image.readme
version: 3
status: active
created_on: "2026-07-10"
updated_on: "2026-11-15"
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the local platform shell image build wrapper.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.script.build-platform-shell-image
  path: scripts/04.deploy/build-platform-shell-image/script.sh
-->
# Build Platform Shell Image

`script.sh` builds the local platform shell container image from the governed
infra image boundary:

```text
infra/04.deploy/03.product/image/Dockerfile
```

The command builds a local image only. It does not publish, deploy, call AWS,
or mutate GitHub.

The Dockerfile intentionally has two image stages. The build stage uses the
full Node image needed for package installation and TypeScript compilation. The
final stage uses the minimal, non-root Distroless Node 22 runtime. Only the
compiled payload and production dependencies cross that boundary; package
management tools, a shell, and general operating-system utilities do not ship
in the image that ECS runs.

Before a container engine is available, the deployable JavaScript payload can
also be checked without Docker:

```bash
npm run platform:server:image-runtime-check
```

That check starts the compiled entrypoint with the non-secret public-target
configuration and temporarily hides local `@kanbien` workspace links. It proves
the runtime resolves generated compiled-package shims, rather than silently
falling back to TypeScript source files. It does not contact AWS or call the
DynamoDB rate-limit table.

The compiled product includes both `platform-smoke` and `entity-smoke`.
`platform/server/tsconfig.image.json` compiles their public roots and reachable
feature code. The npm build command uses the shared workspace compiler: it reads
those explicit source roots, finds their package owners, and follows their
declared runtime dependencies. Compiler aliases and public export paths come
from the package manifests, not a second map in this image's TypeScript config.
[prepare-runtime.mjs](prepare-runtime.mjs) uses the same project selection and
shared runtime assembler to create CommonJS shims and copy declared JSON assets.
All declared compiled exports must exist before assembly starts writing. The
payload check resolves
`@kanbien/app-entity-smoke` through that generated shim while workspace links are
hidden, and requires the compiled app root and feature exports to exist. A
missing declaration, shim or compiled target fails local packaging proof. This
legacy multi-application project retains its explicit source scope; it does not
add all those applications to the server package's runtime dependencies. The
newer isolated runnable programs select their inputs through the canonical
runnable-program contract instead.

This establishes package inclusion, not durable feature persistence. The
entity's PostgreSQL binding, migration executor, target-scoped live checks and
AWS execution approval are separate feature/deployment requirements. Starting
the server with its readiness contribution does not prove entity CRUD on AWS.

If `DOCKER_CONFIG` is unset, the script uses
`.cache/04.deploy/docker-config` so Docker CLI metadata remains writable in
sandboxed local shells.

## Usage

```bash
bash scripts/04.deploy/build-platform-shell-image/script.sh
```

Optional flags:

```bash
bash scripts/04.deploy/build-platform-shell-image/script.sh --tag entity-builder-harness/03.product/platform-shell:local
bash scripts/04.deploy/build-platform-shell-image/script.sh --base-image node:22-bookworm-slim
bash scripts/04.deploy/build-platform-shell-image/script.sh --runtime-image gcr.io/distroless/nodejs22-debian12:nonroot
bash scripts/04.deploy/build-platform-shell-image/script.sh --require-digest-base
bash scripts/04.deploy/build-platform-shell-image/script.sh --no-cache
```

`--require-digest-base` requires both the build and runtime image references to
be pinned by digest. The official GitHub deployment workflow resolves both
tags to digests before it invokes this script. Local tags remain convenient for
development, but they are never deployment evidence.

For local qualification with only the declared public base images, a disposable
`DOCKER_CONFIG` may contain anonymous `auths` entries for Docker Hub and gcr.io
when the host's native credential helper is unavailable. Keep stored Docker
configuration untouched, bind the same observed local Unix-socket engine
before and after the command, and remove the temporary configuration afterward.
Use the existing builder and smoke commands; do not substitute publication,
remote engines, private registries, or target credentials in this recovery.

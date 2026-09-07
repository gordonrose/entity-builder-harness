<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.build-platform-shell-image.readme
version: 1
status: active
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

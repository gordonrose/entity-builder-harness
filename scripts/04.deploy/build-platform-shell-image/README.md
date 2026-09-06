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
bash scripts/04.deploy/build-platform-shell-image/script.sh --require-digest-base
bash scripts/04.deploy/build-platform-shell-image/script.sh --no-cache
```

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.image.core-server.readme
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
kind: guide
purpose: Explain the dedicated local image boundary for the Kanbien core bootstrap server.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.build-core-server-image
  path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh
-->
# Core Server Image

This is a dedicated, local-only candidate image for the declared
`kanbien-core-server` runnable program. It is separate from the broad platform
shell image so it cannot silently package persistence, workers, product apps,
AWS adapters, or existing staging entrypoints.

The image contains compiled JavaScript for the approved core program and its
approved Platform dependencies, plus generated CommonJS package shims. It
contains no source TypeScript, secrets, target configuration, cloud credentials,
or publish/deploy instructions.

Its one exec-form command is:

```text
node artifacts/kanbien-core-server.main.js
```

It runs as the non-root `node` user. Its non-secret defaults are `NODE_ENV`,
`HOST`, `PORT`, and a safe source revision supplied at build time. The local
smoke test checks `/livez`, `/readyz`, and `/internal/release-verification`.

Build and smoke commands live under the package lifecycle phase:

```bash
bash scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh
bash scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh
```

Neither command publishes an image, uses cloud credentials, selects an AWS
target, or deploys anything.

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.image.core-server-persistence.readme
version: 1
status: active
created_on: "2026-10-26"
updated_on: "2026-10-26"
layer: 04.deploy
domain: deployment.package-candidates
disciplines: [architecture, security, sre]
kind: guide
purpose: Describe the bounded PostgreSQL-backed server package context.
portability: { class: internal, targets: [] }
used_by:
- id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
  path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile
-->
# core-server-persistence image

The repository root is the build context, protected by the adjacent default-deny `Dockerfile.dockerignore`. The contract declares the runnable program, non-root user, port 3000, health routes and pinned runtime. The finished-image smoke verifies TLS database operations, enabled metric export and cleanup. Build source revision labels and publication custody receipts bind provenance.

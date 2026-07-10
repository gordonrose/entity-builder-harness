<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.image.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the container image packaging boundary for the platform runtime shell.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.readme
  path: infra/04.deploy/03.product/README.md
-->
# Image

This directory owns the provider-neutral container packaging boundary for the
platform runtime shell.

The image packages `platform/server/src/main.ts`, which starts the platform
server shell with no product app mounted yet. This proves container startup,
liveness, and readiness before AWS runtime-family selection.

## Files

- `Dockerfile` builds the platform shell image.
- `Dockerfile.dockerignore` protects the repo-root build context with a
  default-deny allowlist.

## Local Build

```bash
bash scripts/04.deploy/build-platform-shell-image/script.sh
```

The build wrapper validates container-boundary hygiene before invoking Docker.
Local development builds may use a tag-based Node base image. Use
`--require-digest-base` when you want the local guard to reject tag-only base
images, but do not treat that flag as production readiness.

## Local Smoke Test

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh
```

The smoke test builds the image, runs the container on loopback, and verifies:

- `GET /livez`
- `GET /readyz`

## Runtime Boundary

The image sets:

- `NODE_ENV=production`
- `HOST=0.0.0.0`
- `PORT=3000`

The image runs as the base image's non-root `node` user. Packaged source files
are root-owned and non-writable by the service user. The image smoke test runs
with a read-only root filesystem, all capabilities dropped,
`no-new-privileges`, and a bounded `/tmp` tmpfs.

## Still Blocked Before Deployment

This image boundary is not enough to deploy to AWS. Deployment remains blocked
until the repo has:

- selected AWS runtime family
- target account/profile, region, and environment
- immutable built image digest
- digest-pinned production base image
- SBOM, vulnerability scan, and provenance or attestation policy
- ECR repository and push workflow or governed equivalent
- task/service or runtime-specific resource plan
- DNS/TLS or equivalent HTTPS boundary
- rollback target and operational alarms
- deploy-readiness manifest with real non-secret evidence


<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.image.readme
version: 4
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
platform runtime shell. A target-specific entrypoint may compose a provider
adapter; that selection does not make `platform/server` provider-specific.

The image packages the Kanbien Platform target entrypoints. Its Docker default
starts the public server, while a target may override the command to start the
non-public worker from the same compiled, immutable image. Both entrypoints
mount the same product shell; only the target chooses an authentication or
queue provider adapter.

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

The worker never uses the Dockerfile's HTTP health check. Its ECS task
definition overrides the command with the compiled worker target entrypoint,
does not publish a port, and owns SQS polling, acknowledgement, release, and
graceful shutdown at the target boundary.

The same image also contains the compiled, target-specific one-pass relay
entrypoint. The staging source now has a dedicated relay task definition that
overrides the default command to run it, but it deliberately has no ECS service
or scheduler. The entrypoint itself does not choose a long-running topology.
It receives explicit target configuration and least-privilege DynamoDB/SQS
access only when the reviewed CloudFormation change set is applied. The sealed
payload verifier exercises only its safe configuration/startup path.

The compiled-runtime payload verifier also calls the target persistence
composer with a recording DynamoDB client. That source-only check verifies
that the smoke work-item row, lineage fact, and outbox obligation become one
intended transaction without falling back to TypeScript workspace sources. It
also starts the compiled relay and durable-worker configuration paths with safe
fixtures. It does not open an AWS connection or prove a real table, queue,
relay task, or worker task.

## Still Blocked Before Deployment

This image boundary is not enough to deploy to AWS. Deployment remains blocked
until the repo has:

- ECS Fargate target account/profile, region, environment, cluster, and service
- immutable built image digest
- digest-pinned production base image
- SBOM, vulnerability scan, and provenance or attestation policy
- ECR repository and push workflow or governed equivalent
- task/service or runtime-specific resource plan
- DNS/TLS or equivalent HTTPS boundary
- rollback target and operational alarms
- deploy-readiness manifest with real non-secret evidence

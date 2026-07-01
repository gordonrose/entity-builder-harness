<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.image.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the container image packaging boundary for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: infra.04-deploy.02-rag-rulebook.readme
  path: infra/04.deploy/02.rag-rulebook/README.md
-->
# Image

This directory owns the first container packaging boundary for the
RAG/rulebook service.

The image packages the existing local HTTP service without moving service
source code out of `.agentic/02.rag-rulebook/service/`. Runtime source stays in
the `02.rag-rulebook` layer; deployment packaging lives here under `infra/`.

## Files

- `Dockerfile` builds the service image.
- `Dockerfile.dockerignore` defines the denylist that keeps secrets, Git
  internals, caches, logs, build outputs, and local credentials out of the
  image build context. It is default-deny with explicit allowlist entries for
  the runtime source closure copied by the Dockerfile.

## Local Build

```bash
bash scripts/02.rag-rulebook/build-service-image/script.sh
```

The build wrapper validates container-boundary hygiene before invoking Docker.
Local development builds may use a tag-based Node base image. Use
`--require-digest-base` when you want the local guard to reject tag-only base
images, but do not treat that flag as production readiness by itself.

## Local Smoke Test

```bash
bash scripts/02.rag-rulebook/smoke-test-service-image/script.sh
```

The smoke test builds a fresh local runtime cache, builds the image, runs the
container on loopback, mounts the runtime cache read-only, and verifies:

- `GET /health`
- `GET /version`
- unauthenticated `POST /context/query` is rejected
- authenticated `POST /context/query` returns a compact context packet

## Runtime Boundary

The image sets:

- `RAG_REPO_ROOT=/app`
- `RAG_RUNTIME_DIR=/app/.cache/02.rag-rulebook`
- `HOST=0.0.0.0`
- `PORT=3000`

Non-loopback binds require both `RAG_ALLOW_NON_LOOPBACK=1` and
`RAG_SERVICE_TOKEN`. The image smoke test supplies a temporary token. Hosted
deployment must replace this with governed secret management.

The image runs as the base image's non-root `node` user. Packaged source files
are root-owned and non-writable by the service user. Generated runtime material
stays outside the image during local smoke tests by mounting the runtime cache
read-only, and the image smoke test runs with a read-only root filesystem,
all capabilities dropped, `no-new-privileges`, and a bounded `/tmp` tmpfs.

The image copies the validation source closure needed by the current local
runtime query path, including `02.rag-rulebook` service/scripts/docs content
and the `01.harness` workflow paths referenced by recognition-candidate
validation. If future validation records reference new source roots, the image
copy list and Dockerfile-specific ignore allowlist must be updated together.

## Still Blocked Before Deployment

This image boundary is not enough to deploy to AWS. Deployment remains blocked
until the repo has:

- digest-pinned production base image
- immutable built image digest
- SBOM, vulnerability scan, and provenance or attestation policy
- ECR repository and push workflow
- ECS task definition and service target
- ALB/TLS or equivalent HTTPS boundary
- protected GitHub environment and OIDC trust
- deploy-readiness manifest with real non-secret evidence
- rollback target and operational alarms

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.shared.container-image-management
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
- security
kind: source-material
purpose: Define production-grade container image placement, ownership, provenance, and anti-sprawl source material for deployable services.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.rules.shared.container-image-management
  path: docs/04.deploy/rules/shared/container-image-management.yml
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
-->
# Container Image Management Source Material

Container images are deployable infrastructure artifacts. They package runtime
code, operating-system dependencies, entrypoints, users, ports, health checks,
and file-system assumptions into a form that cloud runtimes can execute.

Because images are deployment artifacts, their definitions belong under
`infra/**`, not inside application source, platform runtime code, harness
process files, or documentation-only folders.

## What This Source Covers

This source defines how this repo creates, places, validates, and evolves
container image definitions so deployment code does not sprawl across the repo.

It covers:

- Dockerfile placement.
- Image directory shape.
- Build context ownership.
- `.dockerignore` requirements.
- Image naming.
- Base image pinning.
- Runtime user and permissions.
- Secrets and sensitive files.
- Health and smoke-test expectations.
- Image provenance, SBOM, scans, and attestations.
- Drift and contamination controls.

It does not define a specific service image. Service-specific image files
belong under that service's deploy track in `infra/**`.

## Why This Needs Governance

Ungoverned container files create hidden production behavior. A Dockerfile in a
random folder can silently:

- use a different build context from the reviewed deployment model
- copy secrets, local caches, session logs, or generated artifacts into an image
- run as root without justification
- bypass the local runtime freshness gate
- publish images without traceable source, SBOM, scan, or attestation evidence
- diverge from ECS task definitions and deploy-readiness manifests
- increase token cost because agents must rediscover which container files are
  real and which are stale experiments

Container governance should make the expected image boundary obvious to humans
and cheap for agents to retrieve.

## Canonical Placement

Dockerfiles for deployable services must live under:

```text
infra/<deploy-layer>/<deploy-track>/image/Dockerfile
```

For the first RAG/rulebook service image, the canonical path is:

```text
infra/04.deploy/02.rag-rulebook/image/Dockerfile
```

The image boundary must include a README, a Dockerfile, and the effective
ignore file for the declared build context:

```text
infra/<deploy-layer>/<deploy-track>/image/
  README.md
  Dockerfile
  .dockerignore              # required when image/ is the build context
  Dockerfile.dockerignore    # allowed when repo root is the build context
```

The image directory may later include image-specific test fixtures, but those
fixtures must be non-secret and must not duplicate service source code.

## Ownership Boundaries

Container image definitions are infra implementation artifacts.

Required ownership split:

- `infra/**/image/` owns Dockerfile placement, declared build context, copy
  boundary, runtime user, exposed port, entrypoint, and image-specific ignore
  rules.
- service source code remains in the owning service layer.
- `scripts/<layer>/` owns deterministic build and smoke-test commands.
- `docs/04.deploy/` owns deploy source material and generated rules.
- `.github/workflows/` may build, scan, attest, publish, and deploy images, but
  the image definition itself must remain under `infra/**`.
- `docs/04.deploy/rules/**` owns the RAG-readable rules that agents retrieve.

Do not put Dockerfiles under `.agentic/**`, `docs/**`, `scripts/**`,
`apps/**`, `platform/**`, `packages/**`, or the repo root unless a future
reviewed exception updates this source and the validator.

## Build Context

The build context must be explicit in the deterministic build script or deploy
manifest.

The effective ignore file must match the declared build context:

- if the image directory is the build context, `infra/**/image/.dockerignore`
  is the effective ignore file.
- if the repo root is the build context, either the repo-root `.dockerignore`
  or `infra/**/image/Dockerfile.dockerignore` must provide the effective
  protection for that build.

For service images that need repo files outside the image directory, the build
script may use the repo root as the build context only when the effective
ignore file prevents accidental inclusion of:

- `.git/`
- `.cache/`
- `commitLogs/`
- local environment files
- session logs
- credentials
- secret files
- node dependency folders not required by the final image
- temporary output
- unreviewed generated runtime caches

The Dockerfile should copy the smallest practical set of files needed to build
and run the service. It must not copy the whole repo by default unless the
reason is documented and the ignore file blocks unsafe paths.

## Image Naming

Image names should be deterministic and tied to the deploy track.

Preferred service image name shape:

```text
<repo-or-product>/<deploy-track>/<service-name>
```

For the first RAG/rulebook service:

```text
entity-builder-harness/02.rag-rulebook/rag-rulebook-service
```

ECR repository names may use the provider's required slug format, but the
deploy-readiness manifest must preserve the logical image identity, ECR
repository, image digest, and source commit.

Do not use a floating tag as the deployment identity. Tags may exist for human
navigation, but staging and production deployment must use image digest.

## Base Image Policy

Production or staging images must use a reviewed base image policy.

The preferred policy is:

- use a minimal official or trusted base image
- pin the base image by digest for production deployment
- name the runtime version
- avoid installing package managers or compilers into the final runtime stage
  unless justified
- rebuild when the base image digest changes
- record base image digest in image provenance

Development images may use a version tag while the image is still local-only,
but deployment remains blocked until the deploy-readiness manifest records the
production base-image evidence.

## Runtime User And Permissions

Images should run as a non-root user in the final runtime stage.

If a service cannot run as non-root, the image README or deploy-readiness
manifest must record:

- why root is required
- what files or ports require it
- what compensating controls exist
- when the exception should be reviewed

The final image should not include writeable application source directories
unless the service needs local runtime writes and the write path is explicitly
bounded.

## Secrets And Sensitive Data

Images must not contain secrets.

The Dockerfile and build context must not copy:

- `.env` files
- AWS credentials
- GitHub tokens
- SSH keys
- local SSO caches
- production config values
- private keys or certificates
- chat transcripts with sensitive values
- generated runtime caches that embed environment-specific data

The service should receive secrets at runtime through the approved secret store
or environment injection path named by the deploy-readiness manifest.

## Health And Smoke Tests

Every deployable image must have a deterministic smoke test before deployment.

For HTTP services, the smoke test should prove:

- the container starts
- `/health` responds
- `/version` responds
- a representative read-only request succeeds where safe
- failure output is concise and actionable
- logs do not expose secrets

The RAG/rulebook service image must also prove that the runtime freshness check
has passed before `/context/query` is treated as deploy-ready.

## Provenance, SBOM, Scans, And Attestations

Container images intended for staging or production must produce or reference:

- source commit SHA
- Dockerfile path
- build context
- base image digest
- image digest
- SBOM
- vulnerability scan result and severity threshold
- artifact attestation or governed signed-provenance fallback
- workflow run id
- corpus package hash when the service serves generated RAG material

Deployment is blocked when provenance evidence is missing or cannot be linked
to the exact image digest being promoted.

## Drift, Gaps, And Contamination Controls

Container definitions can drift from deployment rules, ECS task definitions,
and runtime expectations. The repo should block or warn when:

- a Dockerfile exists outside an approved infra image directory
- a Dockerfile lacks a sibling README
- a Dockerfile lacks an effective ignore file for the declared build context
- the deploy-readiness manifest names a Dockerfile that does not exist
- the ECS task definition port differs from the service port
- an image build script uses a different Dockerfile than the manifest
- a deployment workflow builds a Dockerfile path not allowed by the validator
- production deploys use floating tags without digest proof

These checks reduce token cost because agents can trust the container boundary
instead of scanning the whole repo for competing Dockerfiles.

## Required Variables For Deployable Images

A deployable image must eventually name:

- `service_id`
- `deploy_track`
- `image_name`
- `dockerfile_path`
- `build_context`
- `dockerignore_path`
- `base_image`
- `base_image_digest`
- `container_port`
- `runtime_user`
- `entrypoint`
- `health_endpoint`
- `smoke_test_command`
- `image_digest`
- `ecr_repository`
- `sbom_path_or_evidence_id`
- `scan_result_path_or_evidence_id`
- `attestation_path_or_evidence_id`
- `provenance_verifier_command`

Local-only images may leave deploy-only values unknown, but staging and
production deploy-readiness checks must fail closed until those values are
known.

## Update Rules

When adding or changing a Dockerfile:

1. Confirm the path is under `infra/<deploy-layer>/<deploy-track>/image/`.
2. Update the image README if the runtime, port, user, build context, or copy
   boundary changes.
3. Update deterministic build and smoke-test scripts.
4. Update deploy-readiness manifest references.
5. Run the container boundary validator.
6. Run local service or image smoke tests.
7. Do not deploy until image digest and provenance evidence are recorded.

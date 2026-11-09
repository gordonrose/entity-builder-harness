<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.entity-smoke.image.readme
version: 1
status: draft
created_on: "2026-11-09"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.entity-smoke
disciplines: [architecture, security, sre]
kind: documentation
purpose: Explain the isolated feature image build context, runtime, health and qualification boundaries.
portability: {class: internal, targets: [kanbien-core-platform]}
used_by:
- id: infra.04-deploy.entity-smoke.image.contract
  path: infra/04.deploy/03.product/image/entity-smoke/image-contract.yml
-->
# Entity-smoke image

This image runs the synthetic test-entity feature so its record can be checked
after process replacement. It also packages separate migration, administration,
private HTTP verifier and database-proof programs. The target selects their
commands and identities; packaging them together does not give the server
administrative access or run migrations automatically.

| File | Responsibility |
| --- | --- |
| [Dockerfile](Dockerfile) | Compile the selected app/Core/Platform sources, prepare their runtime exports and installed dependencies, then copy that payload into the pinned Node22 distroless runtime. |
| [Dockerfile.dockerignore](Dockerfile.dockerignore) | Default-deny repository-root build context; admit selected sources and reapply credential, local-tooling and generated-output exclusions. |
| [image-contract.yml](image-contract.yml) | Declare the program, non-secret defaults, pinned base, health paths and required image evidence. |
| [realization-contract.v2.yml](realization-contract.v2.yml) | Describe the separate programs, identities and database/server relationships; declarations alone do not prove access. |

## Build and runtime

Run from the repository root, after source preparation, required checks and a
committed checkpoint:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action \
  scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh
```

The build command checks declarations and payload wiring before Docker. The
build stage installs locked dependencies with lifecycle scripts disabled. The
runtime stage uses `USER nonroot`, defaults to private exposure and listens on
`0.0.0.0:3000`. Its default command starts the compiled feature server without
a shell. Database settings and authorised task credentials are supplied at run
time, not baked into the shared image. The bundled RDS CA certificate is public.

The build command binds the committed SHA to the image revision label and
`PLATFORM_SOURCE_COMMIT_SHA`. A local tag is not publication custody. The
[publication workflow](../../../../../.github/workflows/publish-kanbien-core-platform-entity-smoke.yml)
separately requires the immutable digest, vulnerability scan, SBOM and provenance
attestations before recording a qualified custody receipt.

## Health and qualification

External checks use `/livez` for liveness, `/readyz` for readiness and
`/internal/release-verification` for release identity. Process liveness does not
establish database access. No public ingress is added by this image.

After building, use the existing
[finished-image qualification guide](../../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/README.md).
It exercises the packaged programs against disposable TLS PostgreSQL, including
the feature lifecycle, denied permissions, replacement and recovery. Local
qualification does not establish AWS IAM access or RDS snapshot restoration;
those remain with the [target proof controls](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/README.md).

<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.image.core-server-persistence-observability-collector.readme
version: 1
status: active
created_on: "2026-10-26"
updated_on: "2026-10-26"
layer: 04.deploy
domain: deployment.package-candidates
disciplines: [architecture, security, sre]
kind: guide
purpose: Describe the bounded collector package context.
portability: { class: internal, targets: [] }
used_by:
- id: infra.04-deploy.03-product.image.core-server-persistence-observability-collector.dockerfile
  path: infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile
-->
# core-server-persistence-observability-collector image

The repository root is the build context. The adjacent default-deny `Dockerfile.dockerignore` admits only the component manifest. The pinned builder assembles a static collector in a scratch image, user 65532. The non-secret qualification config enables the health extension and local OTLP receiver; startup, component selection, vulnerability scan and custody checks run before publication. The image contract records source and artifact provenance.

The finished-image qualification sends a real OTLP readiness metric through the shipped receiver, processors and EMF exporter. It checks the emitted metric value and dimensions locally. A mismatched-selector negative proves that accepting OTLP alone cannot qualify the package. The test changes the output sink to local stdout; it does not claim CloudWatch delivery or live permissions.

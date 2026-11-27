<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.scheduling-lambda.readme
version: 1
status: draft
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.package-candidates
disciplines: [architecture, security, sre]
kind: guide
purpose: Explain the shared declared Lambda image recipe and its unfinished qualification boundary.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.image.scheduling-lambda-contract
  path: infra/04.deploy/03.product/image/scheduling-lambda/image-contract.yml
-->
# Scheduling Lambda image recipe

This recipe packages one declared scheduling function for AWS Lambda. A
dispatch image checks stored reminders; a worker image handles the resulting
queue deliveries. Core proof and Entity Smoke use separate program declarations
and separate images built with the same recipe.

- [Dockerfile](Dockerfile) compiles only the selected declared program, reuses
  the shared payload/dependency assemblers, then copies the result onto the
  digest-pinned official Node 22 Lambda runtime. It runs as `10001:10001` and
  exposes `handler.handler`, not an HTTP port.
- [Dockerfile.dockerignore](Dockerfile.dockerignore) admits build inputs while
  excluding repository history, local dependencies, credentials and tests.
  Source TypeScript is used only in the builder stage.
- [image-contract.yml](image-contract.yml) records the runtime, isolation and
  qualification requirements. Exact program, image and candidate identities
  remain in the existing runnable index, not a second registry here.

See the [command guide](../../../../../scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/README.md)
for the build example, actual-runtime check and publication path. A source
import check or a controlled Docker fixture is not a finished-image pass.
No deployment or live AWS qualification is implied by this folder's existence.

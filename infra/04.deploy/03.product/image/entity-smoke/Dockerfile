# syntax=docker/dockerfile:1.7
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: infra.04-deploy.entity-smoke.image.dockerfile
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [architecture, security, sre]
#   kind: dockerfile
#   purpose: Package the isolated feature runtime and bounded migration, administration and private proof tasks.
#   portability: {class: internal, targets: []}
#   used_by:
#   - id: infra.04-deploy.entity-smoke.image.contract
#     path: infra/04.deploy/03.product/image/entity-smoke/image-contract.yml
ARG BUILD_NODE_IMAGE=node:22-bookworm-slim
ARG RUNTIME_NODE_IMAGE=gcr.io/distroless/nodejs22-debian12@sha256:afa48e2ae1100924bfb069244f4ef70c0f9c061654c669da6b7faa7881c1ec7f
FROM ${BUILD_NODE_IMAGE} AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY packages/core/ ./packages/core/
COPY platform/config/ ./platform/config/
COPY platform/contracts/ ./platform/contracts/
COPY platform/health/ ./platform/health/
COPY platform/observability/ ./platform/observability/
COPY platform/persistence/ ./platform/persistence/
COPY platform/runtime/ ./platform/runtime/
COPY platform/security/ ./platform/security/
COPY platform/server/ ./platform/server/
COPY platform/adapters/aws/persistence/postgresql/ ./platform/adapters/aws/persistence/postgresql/
COPY apps/entity-smoke/ ./apps/entity-smoke/
COPY infra/04.deploy/03.product/entrypoints/entity-smoke/ ./infra/04.deploy/03.product/entrypoints/entity-smoke/
COPY infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke*.ts ./infra/04.deploy/03.product/entrypoints/
COPY infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke.tsconfig.json ./infra/04.deploy/03.product/entrypoints/
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-composition.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-composition.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts
COPY scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs ./scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs
COPY scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-dependencies.mjs ./scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-dependencies.mjs
RUN npm ci --ignore-scripts \
 && node_modules/.bin/tsc --project infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke.tsconfig.json --outDir /payload/artifacts --incremental false \
 && node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root /payload/artifacts --dry-run \
 && node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root /payload/artifacts \
 && node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-dependencies.mjs /app /payload/node_modules
FROM ${RUNTIME_NODE_IMAGE}
ARG SOURCE_COMMIT_SHA=local-uncommitted
LABEL org.opencontainers.image.title="kanbien-entity-smoke"
WORKDIR /app
COPY --chown=nonroot:nonroot --from=build /payload/artifacts/ ./artifacts/
COPY --chown=nonroot:nonroot --from=build /payload/node_modules/ ./artifacts/node_modules/
COPY --chown=nonroot:nonroot platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt ./assets/rds-eu-west-1-bundle.crt
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000 PLATFORM_DEPLOYMENT_EXPOSURE=private PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA}
EXPOSE 3000
USER nonroot
CMD ["artifacts/kanbien-entity-smoke.main.js"]


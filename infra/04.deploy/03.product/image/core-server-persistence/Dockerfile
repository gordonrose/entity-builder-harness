# syntax=docker/dockerfile:1.7
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
#   version: 1
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [architecture, security, sre]
#   kind: dockerfile
#   purpose: Build the reviewed private PostgreSQL-backed core-server candidate with its TLS trust bundle.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: infra.04-deploy.03-product.image.core-server-persistence.contract
#     path: infra/04.deploy/03.product/image/core-server-persistence/image-contract.yml
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
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.tsconfig.json ./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.tsconfig.json
COPY scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs ./scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs
RUN npm ci --ignore-scripts \
 && node_modules/.bin/tsc --project infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.tsconfig.json --outDir /payload/artifacts --incremental false \
 && node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs --compiled-root /payload/artifacts \
 && mkdir -p /payload/node_modules \
 && cp -a node_modules/pg node_modules/pg-connection-string node_modules/pg-pool node_modules/pg-protocol node_modules/pg-types node_modules/pg-int8 node_modules/pgpass node_modules/postgres-array node_modules/postgres-bytea node_modules/postgres-date node_modules/postgres-interval node_modules/split2 node_modules/xtend /payload/node_modules/ \
 && NODE_PATH=/payload/node_modules node -e 'require("pg")'
FROM ${RUNTIME_NODE_IMAGE}
ARG SOURCE_COMMIT_SHA=unknown
LABEL org.opencontainers.image.title="kanbien-core-server-persistence"
WORKDIR /app
COPY --chown=nonroot:nonroot --from=build /payload/artifacts/ ./artifacts/
COPY --chown=nonroot:nonroot --from=build /payload/node_modules/ ./artifacts/node_modules/
COPY --chown=nonroot:nonroot platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt ./assets/rds-eu-west-1-bundle.crt
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000 PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA} PERSISTENCE_POSTGRES_CA_PATH=/app/assets/rds-eu-west-1-bundle.crt
EXPOSE 3000
USER nonroot
CMD ["artifacts/kanbien-core-server-persistence.main.js"]

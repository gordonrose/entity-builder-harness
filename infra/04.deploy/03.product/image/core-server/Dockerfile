# syntax=docker/dockerfile:1.7

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: infra.04-deploy.03-product.image.core-server.dockerfile
#   version: 1
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: dockerfile
#   purpose: Build only the declared Kanbien core bootstrap server runnable-program payload for local qualification.
#   portability:
#     class: internal
#     targets: []
#   used_by:
#   - id: deploy.command.build-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh

ARG BUILD_NODE_IMAGE=node:22-bookworm-slim
ARG RUNTIME_NODE_IMAGE=node:22-bookworm-slim

FROM ${BUILD_NODE_IMAGE} AS build
WORKDIR /app

COPY package.json package-lock.json ./
COPY packages/core/ ./packages/core/
COPY platform/config/ ./platform/config/
COPY platform/contracts/ ./platform/contracts/
COPY platform/health/ ./platform/health/
COPY platform/observability/ ./platform/observability/
COPY platform/runtime/ ./platform/runtime/
COPY platform/security/ ./platform/security/
COPY platform/server/ ./platform/server/
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts ./infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts
COPY infra/04.deploy/03.product/entrypoints/kanbien-core-server.tsconfig.json ./infra/04.deploy/03.product/entrypoints/kanbien-core-server.tsconfig.json
COPY scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs ./scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs

RUN npm ci --ignore-scripts \
  && node_modules/.bin/tsc \
    --project infra/04.deploy/03.product/entrypoints/kanbien-core-server.tsconfig.json \
    --outDir /payload/artifacts \
    --incremental false \
  && node scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs \
    --compiled-root /payload/artifacts

FROM ${RUNTIME_NODE_IMAGE}
ARG SOURCE_COMMIT_SHA=unknown

LABEL org.opencontainers.image.title="kanbien-core-server"
LABEL org.opencontainers.image.description="Local-only Kanbien core bootstrap server candidate"

WORKDIR /app
COPY --chown=node:node --from=build /payload/artifacts/ ./artifacts/

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA}

EXPOSE 3000
USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:' + (process.env.PORT || 3000) + '/livez').then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"]

CMD ["node", "artifacts/kanbien-core-server.main.js"]

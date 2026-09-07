# syntax=docker/dockerfile:1.7

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: infra.04-deploy.03-product.image.dockerfile
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - architecture
#   - sre
#   kind: dockerfile
#   purpose: Package the platform runtime shell server entrypoint as a local smoke-testable container image.
#   portability:
#     class: internal
#     targets: []
#   used_by:
#   - id: deploy.script.build-platform-shell-image
#     path: scripts/04.deploy/build-platform-shell-image/script.sh
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh

# The build image is deliberately separate from the image that is deployed.
# Build tooling needs a package manager; the running server does not.
ARG BUILD_NODE_IMAGE=node:22-bookworm-slim
ARG RUNTIME_NODE_IMAGE=gcr.io/distroless/nodejs22-debian12:nonroot

FROM ${BUILD_NODE_IMAGE} AS build
ARG SOURCE_COMMIT_SHA=unknown

LABEL org.opencontainers.image.title="platform-shell"
LABEL org.opencontainers.image.description="Provider-neutral Kanbien platform runtime shell"

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    dumb-init \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/ ./apps/
COPY packages/ ./packages/
COPY platform/ ./platform/
COPY products/ ./products/
COPY infra/04.deploy/03.product/entrypoints/ ./infra/04.deploy/03.product/entrypoints/
COPY scripts/04.deploy/build-platform-shell-image/ ./scripts/04.deploy/build-platform-shell-image/

RUN npm ci --ignore-scripts \
  && npm run platform:server:image-build \
  && npm prune --omit=dev --ignore-scripts \
  && rm -rf /app/node_modules/@kanbien

FROM ${RUNTIME_NODE_IMAGE}
ARG SOURCE_COMMIT_SHA=unknown

LABEL org.opencontainers.image.title="platform-shell"
LABEL org.opencontainers.image.description="Provider-neutral Kanbien platform runtime shell"

WORKDIR /app

COPY --chown=nonroot:nonroot --from=build /app/.cache/ ./.cache/
COPY --chown=nonroot:nonroot --from=build /app/node_modules/ ./node_modules/

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA}

EXPOSE 3000

USER nonroot

# Exec form is required because the distroless runtime intentionally has no shell.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:' + (process.env.PORT || 3000) + '/livez').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"]

# The Distroless base image already declares /nodejs/bin/node as ENTRYPOINT.
CMD [".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js"]

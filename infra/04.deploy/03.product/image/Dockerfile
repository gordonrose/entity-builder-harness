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

ARG NODE_IMAGE=node:22-bookworm-slim
FROM ${NODE_IMAGE}
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
COPY packages/ ./packages/
COPY platform/ ./platform/
COPY scripts/04.deploy/build-platform-shell-image/ ./scripts/04.deploy/build-platform-shell-image/

RUN npm ci --ignore-scripts \
  && npm run platform:server:image-build \
  && rm -rf node_modules \
  && chown -R node:node /app/.cache \
  && find /app -path /app/.cache -prune -o -type d -exec chmod 0755 {} + \
  && find /app -path /app/.cache -prune -o -type f -exec chmod 0644 {} + \
  && find /app/.cache -type d -exec chmod 0755 {} + \
  && find /app/.cache -type f -exec chmod 0644 {} +

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA}

EXPOSE 3000

USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:' + (process.env.PORT || 3000) + '/livez').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", ".cache/platform-shell-image-build/platform/server/src/main.js"]


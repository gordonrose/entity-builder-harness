# syntax=docker/dockerfile:1.7

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: infra.04-deploy.02-rag-rulebook.image.dockerfile
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - architecture
#   - sre
#   kind: dockerfile
#   purpose: Package the existing RAG/rulebook local HTTP service as a container image.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   used_by:
#   - id: rag-rulebook.script.build-service-image
#     path: scripts/02.rag-rulebook/build-service-image/script.sh
#   - id: rag-rulebook.script.smoke-test-service-image
#     path: scripts/02.rag-rulebook/smoke-test-service-image/script.sh

ARG NODE_IMAGE=node:22-bookworm-slim
FROM ${NODE_IMAGE}
ARG SOURCE_COMMIT_SHA=unknown

LABEL org.opencontainers.image.title="rag-rulebook-service"
LABEL org.opencontainers.image.description="RAG/rulebook context packet HTTP service"

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    dumb-init \
    python3 \
    python3-yaml \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json ./package.json
COPY .agentic/ ./.agentic/
COPY .github/workflows/ ./.github/workflows/
COPY infra/ ./infra/
COPY scripts/ ./scripts/
COPY docs/ ./docs/

RUN mkdir -p /app/.cache \
  && (RAG_REPO_ROOT=/app RAG_SOURCE_COMMIT_SHA="${SOURCE_COMMIT_SHA}" bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
      --output-dir /app/.cache/02.rag-rulebook \
      --pretty >/tmp/rag-rulebook-runtime-build.log \
    || { cat /tmp/rag-rulebook-runtime-build.log >&2; exit 1; }) \
  && chown node:node /app/.cache \
  && find /app -path /app/.cache -prune -o -type d -exec chmod 0755 {} + \
  && find /app -path /app/.cache -prune -o -type f -exec chmod 0644 {} + \
  && find /app/.cache -type d -exec chmod 0755 {} + \
  && find /app/.cache -type f -exec chmod 0644 {} + \
  && rm -f /tmp/rag-rulebook-runtime-build.log

ENV NODE_ENV=production
ENV RAG_REPO_ROOT=/app
ENV RAG_RUNTIME_DIR=/app/.cache/02.rag-rulebook
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:' + (process.env.PORT || 3000) + '/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", ".agentic/02.rag-rulebook/service/server.mjs"]

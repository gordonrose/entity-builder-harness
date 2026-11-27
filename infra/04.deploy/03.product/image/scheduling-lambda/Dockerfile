# syntax=docker/dockerfile:1.7
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.image.scheduling-lambda
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: image-declaration
#   purpose: Assemble one declared managed Node handler on the immutable official Lambda runtime.
#   portability: {class: reusable, targets: [entity-builder]}
#   used_by:
#   - id: deploy.image.scheduling-lambda-contract
#     path: infra/04.deploy/03.product/image/scheduling-lambda/image-contract.yml
ARG BUILD_NODE_IMAGE=node:22-bookworm-slim
ARG RUNTIME_NODE_IMAGE=public.ecr.aws/lambda/nodejs@sha256:468c53b1f8cdc6678e5377ccb87c73cf00005b0bad0ba1d03de8d89589b591f7
FROM ${BUILD_NODE_IMAGE} AS build
WORKDIR /app
ARG PROGRAM_ID
COPY package.json package-lock.json ./
COPY packages/core/ ./packages/core/
COPY apps/entity-smoke/ ./apps/entity-smoke/
COPY platform/ ./platform/
COPY infra/04.deploy/03.product/entrypoints/ ./infra/04.deploy/03.product/entrypoints/
COPY scripts/repo/workspace-build/ ./scripts/repo/workspace-build/
COPY scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs ./scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs
COPY scripts/04.deploy/lifecycle/20-build/runnable-program-contract/compile.mjs ./scripts/04.deploy/lifecycle/20-build/runnable-program-contract/compile.mjs
COPY scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs ./scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs
COPY scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler.mjs ./scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler.mjs
COPY scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare.mjs ./scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare.mjs
RUN npm ci --ignore-scripts \
 && node scripts/04.deploy/lifecycle/20-build/runnable-program-contract/compile.mjs --program "$PROGRAM_ID" --outDir /payload/artifacts --incremental false \
 && node scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler.mjs --program "$PROGRAM_ID" --compiled-root /payload/artifacts \
 && node scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler.mjs --program "$PROGRAM_ID" --destination /payload/node_modules \
 && NODE_PATH=/payload/node_modules node -e 'const p=require("/payload/artifacts/runtime-payload.json");const r=require("node:module").createRequire("/payload/artifacts/handler.js");for(const n of p.required_imports)r(n);if(typeof r("./handler.js").handler!=="function")process.exit(1)'
FROM ${RUNTIME_NODE_IMAGE}
ARG PROGRAM_ID
ARG SOURCE_COMMIT_SHA=unknown
LABEL org.opencontainers.image.title="managed-node-handler" org.kanbien.program=${PROGRAM_ID}
WORKDIR /var/task
COPY --from=build /payload/artifacts/ ./
COPY --from=build /payload/node_modules/ ./node_modules/
COPY platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt /app/assets/rds-eu-west-1-bundle.crt
ENV NODE_ENV=production PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA} PERSISTENCE_POSTGRES_CA_PATH=/app/assets/rds-eu-west-1-bundle.crt
USER 10001:10001
CMD ["handler.handler"]

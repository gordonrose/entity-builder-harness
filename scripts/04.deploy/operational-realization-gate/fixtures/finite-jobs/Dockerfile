# Inert fixture image for the existing release-control runner's self-verification.
ARG RUNTIME_NODE_IMAGE
FROM ${RUNTIME_NODE_IMAGE}
ARG SOURCE_COMMIT_SHA
WORKDIR /app
COPY --chown=nonroot:nonroot jobs/ ./jobs/
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000
ENV PLATFORM_SOURCE_COMMIT_SHA=${SOURCE_COMMIT_SHA}
USER nonroot
ENTRYPOINT ["/nodejs/bin/node"]
CMD ["jobs/task.cjs", "success"]

# syntax=docker/dockerfile:1.7
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: infra.04-deploy.03-product.image.core-server-persistence-observability-collector.dockerfile
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: dockerfile
#   purpose: Build a minimal, source-pinned OTel collector for target-private custody.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.pipeline.kanbien-core-platform.observability-collector-package-custody
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml

# Go 1.26.10 contains the security fixes missing from the prior vendor image.
# The digest pins the reviewed multi-platform official builder source; the
# target requires Linux/AMD64 during package qualification.
FROM docker.io/library/golang@sha256:27f2d3b83cfc5803c8078f8e730af0f7c431bf067afaec8f60a36fb763187cba AS build

ARG OTELCOL_VERSION=0.163.0
ENV CGO_ENABLED=0
WORKDIR /src
# Go may resolve a module version through its upstream VCS metadata.  Git is
# build-only and is deliberately absent from the scratch runtime image.
RUN apk add --no-cache git
COPY infra/04.deploy/03.product/image/core-server-persistence-observability-collector/builder-config.yaml ./builder-config.yaml
RUN go install go.opentelemetry.io/collector/cmd/builder@v${OTELCOL_VERSION} \
 && builder --config=builder-config.yaml

# The collector is a statically built Go binary.  Scratch reduces both the
# runtime attack surface and OS package vulnerability inventory; retain only
# the system trust roots needed for AWS HTTPS delivery.
FROM scratch
LABEL org.opencontainers.image.title="kanbien-core-platform-observability-collector"
LABEL org.opencontainers.image.description="Minimal OTLP-to-CloudWatch-EMF collector"
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /output/kanbien-observability-collector /otelcol
USER 65532:65532
# Unlike the previous vendor wrapper, the upstream collector requires an
# explicit configuration provider.  This is non-secret target configuration.
ENTRYPOINT ["/otelcol", "--config=env:AOT_CONFIG_CONTENT"]

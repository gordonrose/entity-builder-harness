# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: infra.image.environment-session-controller.dockerfile
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: dockerfile
#   purpose: Package fixed controller code with pinned Python and AWS CLI rather than executable session ZIPs.
#   portability: {class: reusable, targets: [entity-builder]}
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-environment-session-controller
#     path: .github/workflows/publish-kanbien-core-platform-environment-session-controller.yml
FROM public.ecr.aws/aws-cli/aws-cli:2.36.50@sha256:ff70588020463219cee72a7b44396c19ed73bcb10eabc62c4468e8df0f2ae241 AS awscli
FROM python:3.13-slim-bookworm@sha256:1284ed9f6807edb3fb05db99bce501971395b964ea445bc6d19d4eb5712ffeb6
COPY --from=awscli /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws
WORKDIR /opt/controller
COPY infra/04.deploy/03.product/image/environment-session-controller/requirements.txt /tmp/controller-requirements.txt
RUN python3 -m pip install --no-cache-dir --require-hashes -r /tmp/controller-requirements.txt
COPY scripts/ scripts/
COPY infra/04.deploy/ infra/04.deploy/
COPY .github/workflows/ .github/workflows/
COPY platform/ platform/
COPY packages/core/contracts/ packages/core/contracts/
COPY apps/platform-smoke/contracts/ apps/platform-smoke/contracts/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 AWS_PAGER="" AWS_MAX_ATTEMPTS=1 AWS_EC2_METADATA_DISABLED=true
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/python3", "-I", "-B", "/opt/controller/scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py"]

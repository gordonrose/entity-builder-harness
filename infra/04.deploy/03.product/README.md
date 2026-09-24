<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.readme
version: 4
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the product deploy implementation track for the platform runtime shell.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.readme
  path: infra/04.deploy/README.md
-->
# 03.product

This deploy track contains product-layer deployment implementation artifacts.

The first artifact is the provider-neutral platform shell image boundary. It
packages the local platform server entrypoint so the shell can be built and
smoke-tested before AWS deployment readiness.

`entrypoints/kanbien-platform-persistence.ts` is the first target-specific
persistence composition root. It selects the DynamoDB persistence adapter and
defines the harmless platform-smoke work-item row without making the smoke app
or generic Platform modules provider-specific. The compiled image verifier
exercises this composition with a recording client and proves one intended
three-write transaction locally. It does not select live staging values,
contact AWS, or make a staging persistence capability ready.

The same composition root also assembles the selected DynamoDB outbox and
processing stores for a target relay and worker. The target-specific
`kanbien-platform-relay.main.ts` entrypoint performs one bounded relay pass;
the worker entrypoint opts into durable processing only when its target
configuration supplies the selected persistence values and a lease shorter
than SQS visibility. The local smoke test proves acceptance -> relay -> queue
envelope -> durable completion -> duplicate skip. The staging CloudFormation
source now defines separate least-privilege relay and worker identities, task
configuration, non-public networking, logs, and persistence-transition metric
catalogue. The relay is a task definition only—there is no service, schedule,
or live AWS proof until a reviewed change set and a separately approved
one-shot run occur.

The first AWS planning runtime family is recorded in
`aws-runtime-family.decision.yml`: ECS Fargate. That decision is planning-only
and does not authorize AWS mutation, DNS changes, image publishing, or
production exposure.

Deployment readiness is profile-driven by client and environment. Product
platform shell targets use:

```text
targets/<client>/<environment>/deploy-readiness.yml
```

The first scaffolded target is
`targets/kanbien/staging/deploy-readiness.yml`. It records the platform shell
readiness proof as blocked until source identity, GitHub-to-AWS identity,
immutable image provenance, ECS target resources, AWS
account/region/network/ingress details, operations ownership, deployment
smoke, and rollback proof are selected for that exact target.

This track does not create cloud resources. AWS planning and execution remain
governed by `.agentic/aws/` workflows.

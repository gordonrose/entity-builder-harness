<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.adr.0028-use-client-environment-deployment-target-profiles
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- architecture
- sre
kind: adr
purpose: Record client/environment deployment target profiles as the deploy-time selection boundary.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.source-material.03-product.platform-shell-runtime-family
  path: docs/04.deploy/source-material/03.product/platform-shell-runtime-family.md
- id: deploy.rules.03-product.platform-shell-runtime-family
  path: docs/04.deploy/rules/03.product/platform-shell-runtime-family.yml
- id: product.workflow.platform-runtime-implementation
  path: .agentic/product/workflows/platform-runtime-implementation.md
-->
# ADR 0028: Use Client Environment Deployment Target Profiles

## Status

Accepted.

## Context

The platform will need to deploy different client work into different source
repositories, cloud providers, AWS accounts, Azure subscriptions, regions,
runtime families, and operational boundaries.

If those choices are hardcoded into app feature code or provider-neutral
platform runtime code, each client or cloud target would force product
refactors. That would make the app layer depend on deployment topology and
would undo the provider-neutral contract boundary recorded in ADR 0027.

The first product platform shell target is a Kanbien staging profile on AWS
ECS Fargate, but that target must not become the global platform assumption.

## Decision

Deployment target selection is profile-driven.

Each deployable client/environment target is represented by a target profile
under the deploy track:

```text
infra/04.deploy/03.product/targets/<client>/<environment>/
```

Target profiles name:

- client identity;
- environment identity;
- source control provider, repository, ref, commit, and workflow identity;
- cloud provider and account, subscription, or tenant identity;
- runtime family and provider adapter;
- readiness proof and blockers for that exact target.

The platform and app contract stay provider-neutral. Apps declare needs through
public contracts, app manifests, and mount modules. Platform/deploy composition
selects the target profile and provider adapter that satisfy those needs.

## Consequences

A new client, repo, AWS account, Azure subscription, region, or runtime family
should require a new target profile and, where necessary, a governed provider
adapter. It should not require changes to ordinary app feature code.

Readiness proof becomes target-specific. The same platform shell can have a
blocked Kanbien staging profile, a later Kanbien production profile, and future
client profiles with different source repositories or cloud providers.

Provider adapters remain organized by provider, adapter type, and service name:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

Infra remains responsible for cloud resources, networking, IAM, DNS, TLS,
registries, queues, secrets, logs, alarms, cost controls, and rollback
mechanisms.

## Non-Goals

This ADR does not authorize cloud mutation, DNS changes, IAM changes, image
publishing, production exposure, or GitHub environment changes.

This ADR does not make AWS ECS Fargate part of the app contract.

This ADR does not require all clients to use the same repository, cloud
provider, account, region, or runtime family.

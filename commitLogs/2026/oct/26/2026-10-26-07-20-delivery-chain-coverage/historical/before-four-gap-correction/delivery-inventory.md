# Delivery coverage inventory

Revision: `3db60130493a1ad7af4bbe5c6f0adf9715e6b96c`; input digest: `eb5076a8666929f9f48c7c43d80b75824aa58ab78dbdaf3a67d22793820aa331`.

419 entrypoints; 6 requirement scopes; 0 gaps. Source coverage: **covered**.

| Kind | Count |
| --- | ---: |
| ci-workflow | 9 |
| command | 184 |
| image-definition | 5 |
| package-command | 77 |
| provider-binding | 2 |
| provider-template | 27 |
| regression-command | 86 |
| runnable-program | 20 |
| scope | 6 |
| target | 3 |

| Requirement scope | Classification | Declaration coverage |
| --- | --- | --- |
| rag-rulebook-local-delivery | supported | covered |
| kanbien-staging-platform-shell-server-baseline | supported | covered |
| kanbien-staging-operational-controls | supported | covered |
| kanbien-staging-relational-delivery | supported | covered |
| kanbien-core-platform-bootstrap-runtime | supported | covered |
| kanbien-core-platform-core-server-persistence | supported | covered |

## Executable delivery chains

| Scope | Requirement | Package proof | Target proof | Acceptance/run proof |
| --- | --- | --- | --- | --- |
| rag-rulebook-local-delivery | rag-rulebook.local-service-package | rag-local-query-regression, rag-local-service-regression, rag-local-image | N/A: No supported external deployment target belongs to this local execution route. | N/A: Finished-image and local-service tests own disposable local acceptance; there is no remote release history. |
| kanbien-staging-platform-shell-server-baseline | platform-shell.runtime-image | shell-image-smoke | shell-runtime-alignment | N/A: This declaration concerns the source and current target boundary; packaged behavior and running health are required by the runtime-image and http-health requirements. |
| kanbien-staging-platform-shell-server-baseline | platform-shell.immutable-package-identity | shell-image-smoke | shell-runtime-alignment | N/A: This declaration concerns the source and current target boundary; packaged behavior and running health are required by the runtime-image and http-health requirements. |
| kanbien-staging-platform-shell-server-baseline | platform-shell.http-health-boundary | shell-image-smoke | shell-runtime-alignment | shell-ingress-smoke |
| kanbien-staging-platform-shell-server-baseline | platform-shell.required-app-configuration | shell-image-smoke | shell-runtime-alignment | N/A: This declaration concerns the source and current target boundary; packaged behavior and running health are required by the runtime-image and http-health requirements. |
| kanbien-staging-platform-shell-server-baseline | platform-shell.rollback-declaration | N/A: This declaration concerns the source and current target boundary; packaged behavior and running health are required by the runtime-image and http-health requirements. | shell-runtime-alignment | N/A: This declaration concerns the source and current target boundary; packaged behavior and running health are required by the runtime-image and http-health requirements. |
| kanbien-staging-operational-controls | platform-shell.authentication-proof-identities | N/A: This operation runs through the repository CLI; its local subprocess regression and current target observations own behaviour, rather than the application image. | shell-runtime-alignment | shell-negative-authz-smoke, shell-persistence-smoke |
| kanbien-staging-operational-controls | platform-shell.controlled-worker-delivery | shell-image-smoke | shell-runtime-alignment | shell-worker-smoke, shell-persistence-delivery-proof |
| kanbien-staging-operational-controls | platform-shell.observability-and-ingress | shell-image-smoke | shell-runtime-alignment | shell-metric-coverage, shell-ingress-smoke, shell-rate-limit-smoke |
| kanbien-staging-operational-controls | platform-shell.provider-control-reconciliation | N/A: This operation runs through the repository CLI; its local subprocess regression and current target observations own behaviour, rather than the application image. | shell-runtime-alignment | shell-deployment-reconciliation |
| kanbien-staging-relational-delivery | platform-shell.relational-programs | shell-image-smoke | shell-runtime-alignment | shell-postgresql-relational-smoke |
| kanbien-core-platform-bootstrap-runtime | runtime-implementation-and-release-proof | bootstrap-container | bootstrap-target-alignment | bootstrap-acceptance |
| kanbien-core-platform-core-server-persistence | runtime-implementation-and-release-proof | persistence-container | persistence-target-alignment | persistence-acceptance |

## Workflows and images

| Entrypoint | Classification | Requirement scopes |
| --- | --- | --- |
| `.github/workflows/delivery-coverage.yml` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery, rag-rulebook-local-delivery |
| `.github/workflows/deploy-platform-shell-staging.yml` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `.github/workflows/deploy-rag-rulebook-staging.yml` | retired | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `.github/workflows/platform-shell-staging-metric-coverage.yml` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `.github/workflows/platform-shell-staging-synthetic.yml` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `.github/workflows/publish-kanbien-core-platform-core-server-persistence.yml` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |
| `.github/workflows/publish-kanbien-core-platform-core-server.yml` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |
| `.github/workflows/publish-kanbien-core-platform-observability-collector.yml` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |
| `.github/workflows/reconcile-platform-shell-staging.yml` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `infra/04.deploy/02.rag-rulebook/image/Dockerfile` | supported | kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery, rag-rulebook-local-delivery |
| `infra/04.deploy/03.product/image/Dockerfile` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence, kanbien-staging-operational-controls, kanbien-staging-platform-shell-server-baseline, kanbien-staging-relational-delivery |
| `infra/04.deploy/03.product/image/core-server/Dockerfile` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |
| `infra/04.deploy/03.product/image/core-server-persistence/Dockerfile` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |
| `infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile` | supported | kanbien-core-platform-bootstrap-runtime, kanbien-core-platform-core-server-persistence |

## Gaps

None.

The JSON view contains every discovered command, workflow, program, image, target, binding and template, its registration sources, input hashes and requirement chains. This is source coverage, not live proof.

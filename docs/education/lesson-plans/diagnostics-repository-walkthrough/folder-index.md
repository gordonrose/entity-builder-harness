<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.folder-index
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Index every touched folder and its diagnostic lesson.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Complete folder curriculum

[Course start](README.md) · [Every-file checklist](file-index.md)

All 187 folders directly containing original changed files are listed once. The groups organize learning, not a claim that the original implementation was rewritten into these modules. Read the worked example first; then proceed at your pace.

## The diagnostic language

Core defines provider-independent facts and their allowed shapes. It must remain usable without a server, AWS account or particular database.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L001 — packages/core](lessons/001-packages-core.md) | 1 |
| ☐ | [L002 — packages/core/contracts](lessons/002-packages-core-contracts.md) | 1 |
| ☐ | [L003 — packages/core/src](lessons/003-packages-core-src.md) | 2 |
| ☐ | [L004 — packages/core/src/diagnostics](lessons/004-core-src-diagnostics.md) | 4 |
| ☐ | [L005 — packages/core/src/validation](lessons/005-core-src-validation.md) | 1 |
| ☐ | [L006 — packages/core/tests](lessons/006-packages-core-tests.md) | 31 |

## Configuration: tell absence from invalidity

Configuration code turns supplied settings into values the workload can use. A setting is a logical requirement; its environment-variable name belongs to the caller that binds it.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L007 — packages/core/src/config](lessons/007-core-src-config.md) | 5 |
| ☐ | [L008 — platform/config](lessons/008-platform-config.md) | 1 |
| ☐ | [L009 — platform/config/contracts](lessons/009-platform-config-contracts.md) | 1 |
| ☐ | [L010 — platform/config/src](lessons/010-platform-config-src.md) | 2 |
| ☐ | [L011 — platform/config/tests](lessons/011-platform-config-tests.md) | 4 |

## Shared results and identifiers

Shared primitives give other Core modules a small common vocabulary for success, failure and identifier validation.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L012 — packages/core/src/shared](lessons/012-core-src-shared.md) | 2 |

## Identity and tenant construction

Authentication asks who a caller is; authorization asks what they may do; tenancy identifies the operating context. These modules construct those representations.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L013 — packages/core/src/authn](lessons/013-core-src-authn.md) | 3 |
| ☐ | [L014 — packages/core/src/authz](lessons/014-core-src-authz.md) | 2 |
| ☐ | [L015 — packages/core/src/tenancy](lessons/015-core-src-tenancy.md) | 3 |

## Audit records and projection

Audit code builds records of actions and offers recorder ports. A port is an interface into which another implementation can be supplied.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L016 — packages/core/src/audit](lessons/016-core-src-audit.md) | 3 |

## Events, handlers and publication

Event helpers create event representations and invoke existing event-related callbacks. Their responsibility is distinct from transport delivery.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L017 — packages/core/src/events](lessons/017-core-src-events.md) | 3 |

## File capabilities

Core file helpers represent and operate on file-related data through supplied storage behavior; they do not choose an AWS bucket.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L018 — packages/core/src/files](lessons/018-core-src-files.md) | 3 |

## Internationalization and localization

Internationalization prepares code to handle languages; localization supplies locale-specific formatting or messages.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L019 — packages/core/src/i18n](lessons/019-core-src-i18n.md) | 3 |
| ☐ | [L020 — packages/core/src/localization](lessons/020-core-src-localization.md) | 3 |

## Monitoring primitives and logging

Core exposes health, metrics, tracing and logging abstractions that implementations can fulfill. Metrics count or measure; traces describe work across spans; logs retain individual events.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L021 — packages/core/src/logging](lessons/021-core-src-logging.md) | 3 |
| ☐ | [L022 — packages/core/src/monitoring](lessons/022-core-src-monitoring.md) | 11 |

## Platform registration contracts

Contracts define how apps declare routes, jobs, permissions, configuration, observability profiles and diagnostic catalogs without importing runtime implementations.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L023 — platform/contracts](lessons/023-platform-contracts.md) | 1 |
| ☐ | [L024 — platform/contracts/contracts](lessons/024-platform-contracts-contracts.md) | 1 |
| ☐ | [L025 — platform/contracts/src](lessons/025-platform-contracts-src.md) | 15 |
| ☐ | [L026 — platform/contracts/tests](lessons/026-platform-contracts-tests.md) | 4 |

## Application mounting and lifecycle

Runtime mounts apps into a registry, builds request/job contexts and coordinates startup and shutdown.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L027 — platform/adapters/aws/runtime/ecs-fargate](lessons/027-aws-runtime-ecs-fargate.md) | 1 |
| ☐ | [L028 — platform/adapters/aws/runtime/ecs-fargate/src](lessons/028-runtime-ecs-fargate-src.md) | 1 |
| ☐ | [L029 — platform/adapters/aws/runtime/ecs-fargate/tests](lessons/029-runtime-ecs-fargate-tests.md) | 4 |
| ☐ | [L030 — platform/runtime](lessons/030-platform-runtime.md) | 1 |
| ☐ | [L031 — platform/runtime/contracts](lessons/031-platform-runtime-contracts.md) | 1 |
| ☐ | [L032 — platform/runtime/src](lessons/032-platform-runtime-src.md) | 7 |
| ☐ | [L033 — platform/runtime/tests](lessons/033-platform-runtime-tests.md) | 6 |
| ☐ | [L034 — platform/testing](lessons/034-platform-testing.md) | 1 |
| ☐ | [L035 — platform/testing/src](lessons/035-platform-testing-src.md) | 1 |
| ☐ | [L036 — platform/testing/tests](lessons/036-platform-testing-tests.md) | 3 |

## HTTP transport and request handling

The server resolves configuration, starts a listener, admits transport requests, creates context, authenticates/authorizes, invokes handlers and writes responses.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L037 — platform/server](lessons/037-platform-server.md) | 1 |
| ☐ | [L038 — platform/server/contracts](lessons/038-platform-server-contracts.md) | 1 |
| ☐ | [L039 — platform/server/src](lessons/039-platform-server-src.md) | 5 |
| ☐ | [L040 — platform/server/src/configuration](lessons/040-server-src-configuration.md) | 3 |
| ☐ | [L041 — platform/server/src/verification](lessons/041-server-src-verification.md) | 2 |
| ☐ | [L042 — platform/server/tests](lessons/042-platform-server-tests.md) | 17 |

## Health: public status and private evidence

Health checks tell the workload and its callers whether dependencies and lifecycle state are ready. Public detail is a separate disclosure contract.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L043 — platform/health](lessons/043-platform-health.md) | 1 |
| ☐ | [L044 — platform/health/contracts](lessons/044-platform-health-contracts.md) | 1 |
| ☐ | [L045 — platform/health/src](lessons/045-platform-health-src.md) | 3 |
| ☐ | [L046 — platform/health/tests](lessons/046-platform-health-tests.md) | 3 |

## Shared security observations

Security owns reusable meanings for trust material, TLS, tokens, claims, permissions, headers/CORS and rate-limiter checks. CORS is the browser cross-origin response policy.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L047 — packages/core/src/security](lessons/047-core-src-security.md) | 6 |
| ☐ | [L048 — platform/adapters/aws/auth/cognito/src](lessons/048-auth-cognito-src.md) | 1 |
| ☐ | [L049 — platform/adapters/aws/auth/cognito/tests](lessons/049-auth-cognito-tests.md) | 2 |
| ☐ | [L050 — platform/adapters/aws/security/dynamodb-rate-limiter](lessons/050-aws-security-dynamodb-rate-limiter.md) | 1 |
| ☐ | [L051 — platform/adapters/aws/security/dynamodb-rate-limiter/src](lessons/051-security-dynamodb-rate-limiter-src.md) | 1 |
| ☐ | [L052 — platform/adapters/aws/security/dynamodb-rate-limiter/tests](lessons/052-security-dynamodb-rate-limiter-tests.md) | 2 |
| ☐ | [L053 — platform/security](lessons/053-platform-security.md) | 1 |
| ☐ | [L054 — platform/security/contracts](lessons/054-platform-security-contracts.md) | 1 |
| ☐ | [L055 — platform/security/src](lessons/055-platform-security-src.md) | 10 |
| ☐ | [L056 — platform/security/tests](lessons/056-platform-security-tests.md) | 8 |

## Persistence meaning and coordination

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L057 — packages/core/src/persistence](lessons/057-core-src-persistence.md) | 9 |
| ☐ | [L058 — platform/persistence](lessons/058-platform-persistence.md) | 1 |
| ☐ | [L059 — platform/persistence/contracts](lessons/059-platform-persistence-contracts.md) | 1 |
| ☐ | [L060 — platform/persistence/src](lessons/060-platform-persistence-src.md) | 9 |
| ☐ | [L061 — platform/persistence/src/observability](lessons/061-persistence-src-observability.md) | 3 |
| ☐ | [L062 — platform/persistence/tests](lessons/062-platform-persistence-tests.md) | 4 |

## PostgreSQL: provider evidence

The PostgreSQL adapter implements Platform persistence against a relational database and binds connection, credentials, queries and transactions.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L063 — platform/adapters/aws/persistence/postgresql](lessons/063-aws-persistence-postgresql.md) | 4 |
| ☐ | [L064 — platform/adapters/aws/persistence/postgresql/src](lessons/064-persistence-postgresql-src.md) | 14 |
| ☐ | [L065 — platform/adapters/aws/persistence/postgresql/tests](lessons/065-persistence-postgresql-tests.md) | 5 |

## DynamoDB persistence

This adapter stores Platform records, outbox entries, claims and lineage using DynamoDB commands and existing transaction semantics.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L066 — platform/adapters/aws/persistence/dynamodb](lessons/066-aws-persistence-dynamodb.md) | 2 |
| ☐ | [L067 — platform/adapters/aws/persistence/dynamodb/src](lessons/067-persistence-dynamodb-src.md) | 8 |
| ☐ | [L068 — platform/adapters/aws/persistence/dynamodb/tests](lessons/068-persistence-dynamodb-tests.md) | 2 |

## Worker processing and queue delivery

Workers receive jobs, validate payloads, coordinate durable claims, invoke handlers and settle delivery. Queue adapters implement transport operations.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L069 — packages/core/src/queues](lessons/069-core-src-queues.md) | 3 |
| ☐ | [L070 — platform/workers](lessons/070-platform-workers.md) | 1 |
| ☐ | [L071 — platform/workers/contracts](lessons/071-platform-workers-contracts.md) | 1 |
| ☐ | [L072 — platform/workers/src](lessons/072-platform-workers-src.md) | 9 |
| ☐ | [L073 — platform/workers/tests](lessons/073-platform-workers-tests.md) | 11 |

## SQS transport evidence

The SQS adapter binds generic queue messages and workers to AWS receive, send, delete and related command behavior.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L074 — platform/adapters/aws/queue/sqs](lessons/074-aws-queue-sqs.md) | 1 |
| ☐ | [L075 — platform/adapters/aws/queue/sqs/src](lessons/075-queue-sqs-src.md) | 5 |
| ☐ | [L076 — platform/adapters/aws/queue/sqs/tests](lessons/076-queue-sqs-tests.md) | 1 |

## Diagnostics for telemetry itself

Platform observability wraps logging, metrics, traces and readiness observation; it does not itself choose every provider or backend.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L077 — platform/observability](lessons/077-platform-observability.md) | 2 |
| ☐ | [L078 — platform/observability/contracts](lessons/078-platform-observability-contracts.md) | 1 |
| ☐ | [L079 — platform/observability/src](lessons/079-platform-observability-src.md) | 16 |
| ☐ | [L080 — platform/observability/tests](lessons/080-platform-observability-tests.md) | 10 |

## The existing OpenTelemetry adapter

The CloudWatch observability adapter connects the provider-neutral ports to the already-present OpenTelemetry SDK and selected export behavior.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L081 — platform/adapters/aws/observability/cloudwatch](lessons/081-aws-observability-cloudwatch.md) | 3 |
| ☐ | [L082 — platform/adapters/aws/observability/cloudwatch/src](lessons/082-observability-cloudwatch-src.md) | 3 |
| ☐ | [L083 — platform/adapters/aws/observability/cloudwatch/tests](lessons/083-observability-cloudwatch-tests.md) | 4 |

## The sample app owns its feature meaning

Platform-smoke is a real example app that mounts routes/jobs and exercises persistence-backed work-item acceptance.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L084 — apps/platform-smoke](lessons/084-apps-platform-smoke.md) | 1 |
| ☐ | [L085 — apps/platform-smoke/contracts](lessons/085-apps-platform-smoke-contracts.md) | 1 |
| ☐ | [L086 — apps/platform-smoke/src](lessons/086-apps-platform-smoke-src.md) | 2 |
| ☐ | [L087 — apps/platform-smoke/src/persistence](lessons/087-platform-smoke-src-persistence.md) | 2 |
| ☐ | [L088 — apps/platform-smoke/tests](lessons/088-apps-platform-smoke-tests.md) | 5 |

## Core-server composition and one-shot programs

Entrypoints assemble concrete settings, catalogs, adapters, reporters and programs. A one-shot program performs a task such as migration or verification and exits.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L089 — infra/04.deploy/03.product/entrypoints](lessons/089-04-deploy-03-product-entrypoints.md) | 30 |
| ☐ | [L090 — infra/04.deploy/03.product/entrypoints/contracts](lessons/090-03-product-entrypoints-contracts.md) | 6 |
| ☐ | [L091 — products/kanbien-platform/tests](lessons/091-products-kanbien-platform-tests.md) | 1 |
| ☐ | [L092 — scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition](lessons/092-lifecycle-20-build-core-server-persistence-composition.md) | 8 |

## Assembled image and payload safety

Build and image tooling turns source into a runnable artifact. The payload is the compiled files and dependencies actually included in that artifact.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L093 — infra/04.deploy/03.product/image/core-server-persistence](lessons/093-03-product-image-core-server-persistence.md) | 1 |
| ☐ | [L094 — scripts/04.deploy/build-platform-shell-image](lessons/094-scripts-04-deploy-build-platform-shell-image.md) | 7 |
| ☐ | [L095 — scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary](lessons/095-lifecycle-20-build-core-server-dependency-boundary.md) | 3 |
| ☐ | [L096 — scripts/04.deploy/lifecycle/20-build/runnable-program-contract](lessons/096-lifecycle-20-build-runnable-program-contract.md) | 2 |
| ☐ | [L097 — scripts/04.deploy/lifecycle/40-package/build-core-server-image](lessons/097-lifecycle-40-package-build-core-server-image.md) | 4 |
| ☐ | [L098 — scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image](lessons/098-lifecycle-40-package-build-core-server-persistence-image.md) | 2 |
| ☐ | [L099 — scripts/04.deploy/lifecycle/40-package/package-custody-receipt](lessons/099-lifecycle-40-package-package-custody-receipt.md) | 3 |
| ☐ | [L100 — scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage](lessons/100-provider-adapters-aws-iam-policy-coverage.md) | 1 |
| ☐ | [L101 — scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image](lessons/101-lifecycle-40-package-qualify-retained-persistence-rollback-image.md) | 1 |
| ☐ | [L102 — scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image](lessons/102-lifecycle-40-package-smoke-test-core-server-image.md) | 1 |
| ☐ | [L103 — scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image](lessons/103-lifecycle-40-package-smoke-test-core-server-persistence-image.md) | 5 |
| ☐ | [L104 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody](lessons/104-targets-kanbien-core-platform-core-server-package-custody.md) | 1 |
| ☐ | [L105 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access](lessons/105-kanbien-core-platform-core-server-package-custody-validate-delivery-access.md) | 1 |
| ☐ | [L106 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody](lessons/106-targets-kanbien-core-platform-core-server-persistence-observability-collector-package-custody.md) | 2 |
| ☐ | [L107 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody](lessons/107-targets-kanbien-core-platform-core-server-persistence-package-custody.md) | 1 |
| ☐ | [L108 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access](lessons/108-kanbien-core-platform-core-server-persistence-package-custody-validate-delivery-access.md) | 1 |
| ☐ | [L109 — scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract](lessons/109-lifecycle-40-package-validate-delivery-access-contract.md) | 2 |
| ☐ | [L110 — scripts/04.deploy/smoke-test-platform-shell-image](lessons/110-scripts-04-deploy-smoke-test-platform-shell-image.md) | 1 |
| ☐ | [L111 — scripts/04.deploy/validate-container-boundaries](lessons/111-scripts-04-deploy-validate-container-boundaries.md) | 2 |

## Target declarations and provider observation

Alignment tooling compares declared target requirements and observed provider conditions before build or deployment.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L112 — scripts/04.deploy/inventory-deploy-control](lessons/112-scripts-04-deploy-inventory-deploy-control.md) | 4 |
| ☐ | [L113 — scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration](lessons/113-lifecycle-00-target-alignment-core-platform-target-declaration.md) | 2 |
| ☐ | [L114 — scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage](lessons/114-lifecycle-00-target-alignment-declaration-coverage.md) | 3 |
| ☐ | [L115 — scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecr-read-access](lessons/115-provider-adapters-aws-ecr-read-access.md) | 1 |
| ☐ | [L116 — scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment](lessons/116-provider-adapters-aws-runtime-alignment.md) | 2 |
| ☐ | [L117 — scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/inspect-runtime-alignment](lessons/117-targets-kanbien-core-platform-inspect-runtime-alignment.md) | 1 |
| ☐ | [L118 — scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access](lessons/118-targets-kanbien-core-platform-verify-delivery-role-access.md) | 1 |
| ☐ | [L119 — scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement](lessons/119-lifecycle-00-target-alignment-validate-artifact-placement.md) | 2 |
| ☐ | [L120 — scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration](lessons/120-lifecycle-00-target-alignment-validate-observability-mvp-declaration.md) | 2 |
| ☐ | [L121 — scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence](lessons/121-lifecycle-00-target-alignment-validate-provider-condition-evidence.md) | 2 |
| ☐ | [L122 — scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration](lessons/122-lifecycle-00-target-alignment-validate-secret-dependency-declaration.md) | 2 |
| ☐ | [L123 — scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment](lessons/123-lifecycle-00-target-alignment-validate-target-alignment.md) | 2 |

## Deployment controllers and evidence readers

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L124 — .agentic/04.deploy/60-run/schemas](lessons/124-04-deploy-60-run-schemas.md) | 1 |
| ☐ | [L125 — .agentic/04.deploy/60-run/standards](lessons/125-04-deploy-60-run-standards.md) | 1 |
| ☐ | [L126 — .agentic/04.deploy/schemas](lessons/126--agentic-04-deploy-schemas.md) | 2 |
| ☐ | [L127 — scripts/04.deploy](lessons/127-scripts-04-deploy.md) | 1 |
| ☐ | [L128 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime](lessons/128-targets-kanbien-core-platform-bootstrap-runtime.md) | 2 |
| ☐ | [L129 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set](lessons/129-kanbien-core-platform-bootstrap-runtime-create-change-set.md) | 1 |
| ☐ | [L130 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate](lessons/130-kanbien-core-platform-bootstrap-runtime-deploy-candidate.md) | 1 |
| ☐ | [L131 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence](lessons/131-targets-kanbien-core-platform-core-server-persistence.md) | 2 |
| ☐ | [L132 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface](lessons/132-kanbien-core-platform-core-server-persistence-apply-restoration-verifier-surface.md) | 1 |
| ☐ | [L133 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set](lessons/133-kanbien-core-platform-core-server-persistence-create-change-set.md) | 1 |
| ☐ | [L134 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate](lessons/134-kanbien-core-platform-core-server-persistence-deploy-candidate.md) | 1 |
| ☐ | [L135 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate](lessons/135-kanbien-core-platform-core-server-persistence-prepare-candidate.md) | 1 |
| ☐ | [L136 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface](lessons/136-kanbien-core-platform-core-server-persistence-reconcile-rds-log-export-surface.md) | 1 |
| ☐ | [L137 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate](lessons/137-kanbien-core-platform-core-server-persistence-retire-failed-candidate.md) | 1 |
| ☐ | [L138 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget](lessons/138-kanbien-core-platform-foundation-provision-target-budget.md) | 2 |
| ☐ | [L139 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement](lessons/139-kanbien-core-platform-bootstrap-runtime-rehearse-accepted-workload-replacement.md) | 2 |
| ☐ | [L140 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault](lessons/140-kanbien-core-platform-bootstrap-runtime-rehearse-private-verifier-fault.md) | 2 |
| ☐ | [L141 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence](lessons/141-targets-kanbien-core-platform-core-server-persistence.md) | 4 |
| ☐ | [L142 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal](lessons/142-kanbien-core-platform-core-server-persistence-acceptance-route-rehearsal.md) | 1 |
| ☐ | [L143 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence](lessons/143-kanbien-core-platform-core-server-persistence-collect-acceptance-evidence.md) | 3 |
| ☐ | [L144 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore](lessons/144-kanbien-core-platform-core-server-persistence-rehearse-isolated-database-restore.md) | 2 |
| ☐ | [L145 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness](lessons/145-kanbien-core-platform-core-server-persistence-rehearse-observability-readiness.md) | 2 |
| ☐ | [L146 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle](lessons/146-kanbien-core-platform-core-server-persistence-rehearse-runtime-credential-lifecycle.md) | 1 |
| ☐ | [L147 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement](lessons/147-kanbien-core-platform-core-server-persistence-rehearse-server-replacement.md) | 1 |
| ☐ | [L148 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration](lessons/148-kanbien-core-platform-core-server-persistence-run-administration.md) | 1 |
| ☐ | [L149 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration](lessons/149-kanbien-core-platform-core-server-persistence-run-migration.md) | 1 |
| ☐ | [L150 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate](lessons/150-kanbien-core-platform-core-server-persistence-verify-candidate.md) | 2 |
| ☐ | [L151 — scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping](lessons/151-lifecycle-60-run-validate-persistence-diagnostic-mapping.md) | 2 |
| ☐ | [L152 — scripts/04.deploy/reconcile-platform-shell-staging](lessons/152-scripts-04-deploy-reconcile-platform-shell-staging.md) | 3 |
| ☐ | [L153 — scripts/04.deploy/shared](lessons/153-scripts-04-deploy-shared.md) | 5 |
| ☐ | [L154 — scripts/04.deploy/shared/provider-adapters/docker](lessons/154-shared-provider-adapters-docker.md) | 2 |
| ☐ | [L155 — scripts/04.deploy/verify-platform-shell-deploy-readiness](lessons/155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) | 3 |

## Rules for future changes

The harness tells agents what complete work requires, who owns it, which compatibility boundaries to preserve and what proof must be recorded.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L156 — .](lessons/156-repository-root.md) | 2 |
| ☐ | [L157 — .agentic/01.harness/workflows](lessons/157--agentic-01-harness-workflows.md) | 1 |
| ☐ | [L158 — .agentic/03.product](lessons/158--agentic-03-product.md) | 1 |
| ☐ | [L159 — .agentic/03.product/workflows](lessons/159--agentic-03-product-workflows.md) | 1 |
| ☐ | [L160 — .agentic/shared/standards](lessons/160--agentic-shared-standards.md) | 2 |
| ☐ | [L161 — .agentic/shared/workflows](lessons/161--agentic-shared-workflows.md) | 2 |
| ☐ | [L162 — .github/workflows](lessons/162--github-workflows.md) | 1 |
| ☐ | [L163 — docs/03.product/rules/core/concerns](lessons/163-rules-core-concerns.md) | 1 |
| ☐ | [L164 — docs/03.product/rules/core/layers](lessons/164-rules-core-layers.md) | 1 |
| ☐ | [L165 — docs/03.product/rules/platform/concerns](lessons/165-rules-platform-concerns.md) | 1 |
| ☐ | [L166 — docs/03.product/rules/platform/layers](lessons/166-rules-platform-layers.md) | 1 |

## Executable adoption and compatibility checks

The diagnostic-coverage tools discover relevant code, validate source-matched owner reviews and export runtime-owned definitions for other languages.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L167 — scripts/repo/diagnostic-coverage](lessons/167-scripts-repo-diagnostic-coverage.md) | 10 |

## Verification ownership and safe reuse

The check selector maps changed inputs to required checks and reuses prior passing results only when their source/runtime/contract identity still matches.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L168 — scripts/04.deploy/verify-platform-shell-deployment-workflow](lessons/168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) | 1 |
| ☐ | [L169 — scripts/04.deploy/verify-platform-shell-infrastructure](lessons/169-scripts-04-deploy-verify-platform-shell-infrastructure.md) | 2 |
| ☐ | [L170 — scripts/repo/check-selection](lessons/170-scripts-repo-check-selection.md) | 9 |

## Tooling and bounded imported exceptions

Chat/export/metrics tools and metadata utilities support agent work. Some are owned upstream by llm-workbench rather than by this repo.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L171 — bin](lessons/171-bin.md) | 2 |
| ☐ | [L172 — scripts/00.chat/export](lessons/172-scripts-00-chat-export.md) | 1 |
| ☐ | [L173 — scripts/00.chat/export/create-worktree-bundle](lessons/173-00-chat-export-create-worktree-bundle.md) | 1 |
| ☐ | [L174 — scripts/00.chat/metrics/estimate-chat-cost](lessons/174-00-chat-metrics-estimate-chat-cost.md) | 1 |
| ☐ | [L175 — scripts/00.chat/session-log/record-chat-commit](lessons/175-00-chat-session-log-record-chat-commit.md) | 1 |
| ☐ | [L176 — scripts/01.harness](lessons/176-scripts-01-harness.md) | 3 |
| ☐ | [L177 — scripts/01.harness/agents/validate-harness-agents](lessons/177-01-harness-agents-validate-harness-agents.md) | 3 |
| ☐ | [L178 — scripts/01.harness/artifact-metadata](lessons/178-scripts-01-harness-artifact-metadata.md) | 1 |
| ☐ | [L179 — scripts/01.harness/artifact-metadata/backfill-v2-headers](lessons/179-01-harness-artifact-metadata-backfill-v2-headers.md) | 2 |
| ☐ | [L180 — scripts/01.harness/artifact-metadata/generate-index](lessons/180-01-harness-artifact-metadata-generate-index.md) | 2 |
| ☐ | [L181 — scripts/01.harness/artifact-metadata/update-lifecycle](lessons/181-01-harness-artifact-metadata-update-lifecycle.md) | 2 |
| ☐ | [L182 — scripts/01.harness/metrics/compare-task-token-consumption](lessons/182-01-harness-metrics-compare-task-token-consumption.md) | 1 |

## History, decisions and qualification records

Plans, decisions and session records preserve why work was done and what evidence actually exists. They are not application runtime.

| Covered | Lesson / exact folder | Files |
| --- | --- | ---: |
| ☐ | [L183 — .agentic/03.product/plans/implementation](lessons/183-03-product-plans-implementation.md) | 2 |
| ☐ | [L184 — .agentic/shared/plans/implementation](lessons/184-shared-plans-implementation.md) | 1 |
| ☐ | [L185 — commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage](lessons/185-oct-27-2026-10-27-08-24-governed-diagnostic-coverage.md) | 1 |
| ☐ | [L186 — commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909](lessons/186-27-2026-10-27-08-24-governed-diagnostic-coverage-local-artifact-qualification-20261028-163909.md) | 3 |
| ☐ | [L187 — docs/03.product/adrs](lessons/187-docs-03-product-adrs.md) | 2 |

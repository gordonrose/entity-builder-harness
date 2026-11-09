<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.file-index
  version: 2
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Account for every changed file without omissions.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Every changed file

[Course start](README.md) · [Folder curriculum](folder-index.md)

The frozen inventory is **584 original paths**. Every path below has exactly one file entry in the linked lesson. “Covered” starts unchecked: preparing material is not the same as teaching it. Source links open current files; compare the baseline using the teaching guide. Exact baseline/current SHA-256 identities are embedded in each lesson's course-source-sha256 comments.

## L001 — packages/core

[Open folder lesson](lessons/001-packages-core.md)

- [ ] [packages/core/README.md](../../../../packages/core/README.md) — modified; before `b69ccb1dffb3`, snapshot `51988064fc78`.

## L002 — packages/core/contracts

[Open folder lesson](lessons/002-packages-core-contracts.md)

- [ ] [packages/core/contracts/diagnostics.v1.json](../../../../packages/core/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `2f7e1ce7faa1`.

## L003 — packages/core/src

[Open folder lesson](lessons/003-packages-core-src.md)

- [ ] [packages/core/src/diagnostic-catalog.ts](../../../../packages/core/src/diagnostic-catalog.ts) — added; before `absent`, snapshot `221afd9c1c67`.
- [ ] [packages/core/src/index.ts](../../../../packages/core/src/index.ts) — modified; before `6a426dcac432`, snapshot `b8475d296f5f`.

## L004 — packages/core/src/diagnostics

[Open folder lesson](lessons/004-core-src-diagnostics.md)

- [ ] [packages/core/src/diagnostics/definition.ts](../../../../packages/core/src/diagnostics/definition.ts) — added; before `absent`, snapshot `c6844ffe6edf`.
- [ ] [packages/core/src/diagnostics/index.ts](../../../../packages/core/src/diagnostics/index.ts) — modified; before `ffc294face8a`, snapshot `cb5e30e2f379`.
- [ ] [packages/core/src/diagnostics/record.ts](../../../../packages/core/src/diagnostics/record.ts) — added; before `absent`, snapshot `87092521a24b`.
- [ ] [packages/core/src/diagnostics/schema.ts](../../../../packages/core/src/diagnostics/schema.ts) — added; before `absent`, snapshot `2894b65e61fa`.

## L005 — packages/core/src/validation

[Open folder lesson](lessons/005-core-src-validation.md)

- [ ] [packages/core/src/validation/index.ts](../../../../packages/core/src/validation/index.ts) — modified; before `43ee5d75ad30`, snapshot `9be4026d135b`.

## L006 — packages/core/tests

[Open folder lesson](lessons/006-packages-core-tests.md)

- [ ] [packages/core/tests/audit/unit/audit-runtime.test.ts](../../../../packages/core/tests/audit/unit/audit-runtime.test.ts) — modified; before `829f0d536bec`, snapshot `db1dc7c1efe5`.
- [ ] [packages/core/tests/audit/type-level/audit-types.test.ts](../../../../packages/core/tests/audit/type-level/audit-types.test.ts) — modified; before `4274801d6291`, snapshot `7e2bd52bad71`.
- [ ] [packages/core/tests/authn/unit/authn-runtime.test.ts](../../../../packages/core/tests/authn/unit/authn-runtime.test.ts) — modified; before `6c99e72a8ecd`, snapshot `174ae8d2ff58`.
- [ ] [packages/core/tests/authn/type-level/authn-types.test.ts](../../../../packages/core/tests/authn/type-level/authn-types.test.ts) — modified; before `6f73c9253083`, snapshot `5d0a57348fb3`.
- [ ] [packages/core/tests/config/unit/config-runtime.test.ts](../../../../packages/core/tests/config/unit/config-runtime.test.ts) — modified; before `5cf6a556da83`, snapshot `fbb162e20f81`.
- [ ] [packages/core/tests/config/type-level/config-types.test.ts](../../../../packages/core/tests/config/type-level/config-types.test.ts) — modified; before `c9b685ef236c`, snapshot `e03fab581c83`.
- [ ] [packages/core/tests/diagnostics/contract/diagnostic-record-runtime.test.ts](../../../../packages/core/tests/diagnostics/contract/diagnostic-record-runtime.test.ts) — added; before `absent`, snapshot `0b59205fd3e7`.
- [ ] [packages/core/tests/diagnostics/type-level/diagnostic-record-types.test.ts](../../../../packages/core/tests/diagnostics/type-level/diagnostic-record-types.test.ts) — added; before `absent`, snapshot `28d03fa4e417`.
- [ ] [packages/core/tests/events/unit/events-runtime.test.ts](../../../../packages/core/tests/events/unit/events-runtime.test.ts) — modified; before `8092a2d8b910`, snapshot `4e7f023044d4`.
- [ ] [packages/core/tests/events/type-level/events-types.test.ts](../../../../packages/core/tests/events/type-level/events-types.test.ts) — modified; before `ba17957aefda`, snapshot `fbf26acf6fa8`.
- [ ] [packages/core/tests/files/unit/files-runtime.test.ts](../../../../packages/core/tests/files/unit/files-runtime.test.ts) — modified; before `795670270a75`, snapshot `2711529e5ed9`.
- [ ] [packages/core/tests/files/type-level/files-types.test.ts](../../../../packages/core/tests/files/type-level/files-types.test.ts) — modified; before `01383bc3b6a2`, snapshot `5d8fafa62a8d`.
- [ ] [packages/core/tests/diagnostics/contract/foundation-diagnostics-runtime.test.ts](../../../../packages/core/tests/diagnostics/contract/foundation-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `23b71bb75ee7`.
- [ ] [packages/core/tests/diagnostics/type-level/foundation-diagnostics-types.test.ts](../../../../packages/core/tests/diagnostics/type-level/foundation-diagnostics-types.test.ts) — added; before `absent`, snapshot `f954c00858dd`.
- [ ] [packages/core/tests/i18n/unit/i18n-runtime.test.ts](../../../../packages/core/tests/i18n/unit/i18n-runtime.test.ts) — modified; before `c33bd0267f15`, snapshot `ddcb3da4669f`.
- [ ] [packages/core/tests/i18n/type-level/i18n-types.test.ts](../../../../packages/core/tests/i18n/type-level/i18n-types.test.ts) — modified; before `f4add4391af7`, snapshot `777d16b25f87`.
- [ ] [packages/core/tests/localization/unit/localization-runtime.test.ts](../../../../packages/core/tests/localization/unit/localization-runtime.test.ts) — modified; before `ec05d5fdb4a8`, snapshot `1108f97ed83e`.
- [ ] [packages/core/tests/localization/type-level/localization-types.test.ts](../../../../packages/core/tests/localization/type-level/localization-types.test.ts) — modified; before `b75bcd1bf498`, snapshot `2c7bd20e0788`.
- [ ] [packages/core/tests/logging/unit/logging-runtime.test.ts](../../../../packages/core/tests/logging/unit/logging-runtime.test.ts) — modified; before `71df9ec476d6`, snapshot `5d235dbe6a46`.
- [ ] [packages/core/tests/logging/type-level/logging-types.test.ts](../../../../packages/core/tests/logging/type-level/logging-types.test.ts) — modified; before `183753d5e4da`, snapshot `26de5f3c6a09`.
- [ ] [packages/core/tests/monitoring/unit/monitoring-metric-diagnostics-runtime.test.ts](../../../../packages/core/tests/monitoring/unit/monitoring-metric-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `3ef495deceac`.
- [ ] [packages/core/tests/monitoring/unit/monitoring-runtime.test.ts](../../../../packages/core/tests/monitoring/unit/monitoring-runtime.test.ts) — modified; before `17f19935a461`, snapshot `c000a471de6b`.
- [ ] [packages/core/tests/monitoring/type-level/monitoring-types.test.ts](../../../../packages/core/tests/monitoring/type-level/monitoring-types.test.ts) — modified; before `e9b2730cb30f`, snapshot `4440bdbb8583`.
- [ ] [packages/core/tests/persistence/unit/persistence-runtime.test.ts](../../../../packages/core/tests/persistence/unit/persistence-runtime.test.ts) — modified; before `a8f302c9dc79`, snapshot `b6f58f413a84`.
- [ ] [packages/core/tests/persistence/type-level/persistence-types.test.ts](../../../../packages/core/tests/persistence/type-level/persistence-types.test.ts) — modified; before `3ccff62e8e28`, snapshot `3f900e6ee423`.
- [ ] [packages/core/tests/queues/unit/queues-runtime.test.ts](../../../../packages/core/tests/queues/unit/queues-runtime.test.ts) — modified; before `e458bdde5388`, snapshot `459933e58f11`.
- [ ] [packages/core/tests/queues/type-level/queues-types.test.ts](../../../../packages/core/tests/queues/type-level/queues-types.test.ts) — modified; before `24d88bf2ce58`, snapshot `59f2a7dd8b31`.
- [ ] [packages/core/tests/security/unit/security-diagnostics-runtime.test.ts](../../../../packages/core/tests/security/unit/security-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `e6ad0c89e2a7`.
- [ ] [packages/core/tests/security/type-level/security-diagnostics-types.test.ts](../../../../packages/core/tests/security/type-level/security-diagnostics-types.test.ts) — added; before `absent`, snapshot `78795d5b426e`.
- [ ] [packages/core/tests/tenancy/unit/tenancy-runtime.test.ts](../../../../packages/core/tests/tenancy/unit/tenancy-runtime.test.ts) — modified; before `b0d7dae41ebb`, snapshot `52393f855618`.
- [ ] [packages/core/tests/tenancy/type-level/tenancy-types.test.ts](../../../../packages/core/tests/tenancy/type-level/tenancy-types.test.ts) — modified; before `fe2951951749`, snapshot `f8c1d59091d2`.

## L007 — packages/core/src/config

[Open folder lesson](lessons/007-core-src-config.md)

- [ ] [packages/core/src/config/diagnostics.ts](../../../../packages/core/src/config/contract/reporting/diagnostics.ts) — added; before `absent`, snapshot `b92302c9f586`.
- [ ] [packages/core/src/config/index.ts](../../../../packages/core/src/config/index.ts) — modified; before `134c5d34d3d9`, snapshot `fbe2e20fe76b`.
- [ ] [packages/core/src/config/issues.ts](../../../../packages/core/src/config/contract/reporting/setting-issues.ts) — added; before `absent`, snapshot `3ff221fa7ab5`.
- [ ] [packages/core/src/config/schema.ts](../../../../packages/core/src/config/domain/validation/settings.ts) — added; before `absent`, snapshot `7dfbd1ca81bc`.
- [ ] [packages/core/src/config/source-observation.ts](../../../../packages/core/src/config/contract/reporting/sourcing-issues.ts) — added; before `absent`, snapshot `88cffdd9ed05`.

## L008 — platform/config

[Open folder lesson](lessons/008-platform-config.md)

- [ ] [platform/config/README.md](../../../../platform/config/README.md) — added; before `absent`, snapshot `7772c06afa96`.

## L009 — platform/config/contracts

[Open folder lesson](lessons/009-platform-config-contracts.md)

- [ ] [platform/config/contracts/diagnostics.v1.json](../../../../platform/config/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `a5e67c5f7eef`.

## L010 — platform/config/src

[Open folder lesson](lessons/010-platform-config-src.md)

- [ ] [platform/config/src/diagnostics.ts](../../../../platform/config/src/diagnostics.ts) — added; before `absent`, snapshot `9c8be0da060b`.
- [ ] [platform/config/src/index.ts](../../../../platform/config/src/index.ts) — modified; before `9cc880eddf5e`, snapshot `82ae867017a4`.

## L011 — platform/config/tests

[Open folder lesson](lessons/011-platform-config-tests.md)

- [ ] [platform/config/tests/integration/evidence-runtime.test.ts](../../../../platform/config/tests/integration/evidence-runtime.test.ts) — added; before `absent`, snapshot `3e64d578f816`.
- [ ] [platform/config/tests/integration/platform-config-runtime.test.ts](../../../../platform/config/tests/integration/platform-config-runtime.test.ts) — modified; before `c0324fed6952`, snapshot `d35cf87fcf13`.
- [ ] [platform/config/tests/type-level/platform-config-types.test.ts](../../../../platform/config/tests/type-level/platform-config-types.test.ts) — modified; before `1075680e1c6e`, snapshot `bb262c896491`.
- [ ] [platform/config/tests/run-runtime-tests.mjs](../../../../platform/config/tests/run-runtime-tests.mjs) — modified; before `3d3b9312a274`, snapshot `6a6c3dfd7478`.

## L012 — packages/core/src/shared

[Open folder lesson](lessons/012-core-src-shared.md)

- [ ] [packages/core/src/shared/diagnostics.ts](../../../../packages/core/src/shared/diagnostics.ts) — added; before `absent`, snapshot `d7da5d3f3917`.
- [ ] [packages/core/src/shared/index.ts](../../../../packages/core/src/shared/index.ts) — modified; before `c488153546e4`, snapshot `dccf47177790`.

## L013 — packages/core/src/authn

[Open folder lesson](lessons/013-core-src-authn.md)

- [ ] [packages/core/src/authn/diagnostics.ts](../../../../packages/core/src/authn/diagnostics.ts) — added; before `absent`, snapshot `b9303495cc2d`.
- [ ] [packages/core/src/authn/index.ts](../../../../packages/core/src/authn/index.ts) — modified; before `b2facf296fa6`, snapshot `a105338985fa`.
- [ ] [packages/core/src/authn/observations.ts](../../../../packages/core/src/authn/observations.ts) — added; before `absent`, snapshot `b51e96a46406`.

## L014 — packages/core/src/authz

[Open folder lesson](lessons/014-core-src-authz.md)

- [ ] [packages/core/src/authz/diagnostics.ts](../../../../packages/core/src/authz/diagnostics.ts) — added; before `absent`, snapshot `6c09c6bd1998`.
- [ ] [packages/core/src/authz/index.ts](../../../../packages/core/src/authz/index.ts) — modified; before `d2510247978d`, snapshot `3a7c6eff4461`.

## L015 — packages/core/src/tenancy

[Open folder lesson](lessons/015-core-src-tenancy.md)

- [ ] [packages/core/src/tenancy/diagnostics.ts](../../../../packages/core/src/tenancy/diagnostics.ts) — added; before `absent`, snapshot `e630ae6f0b93`.
- [ ] [packages/core/src/tenancy/index.ts](../../../../packages/core/src/tenancy/index.ts) — modified; before `aa481f90dcd5`, snapshot `9947c756945c`.
- [ ] [packages/core/src/tenancy/observations.ts](../../../../packages/core/src/tenancy/observations.ts) — added; before `absent`, snapshot `316ee3de2f0c`.

## L016 — packages/core/src/audit

[Open folder lesson](lessons/016-core-src-audit.md)

- [ ] [packages/core/src/audit/diagnostics.ts](../../../../packages/core/src/audit/diagnostics.ts) — added; before `absent`, snapshot `0a0269cf6bf5`.
- [ ] [packages/core/src/audit/index.ts](../../../../packages/core/src/audit/index.ts) — modified; before `40125a44cdc8`, snapshot `94d7ab158c3f`.
- [ ] [packages/core/src/audit/observations.ts](../../../../packages/core/src/audit/observations.ts) — added; before `absent`, snapshot `ef646b217050`.

## L017 — packages/core/src/events

[Open folder lesson](lessons/017-core-src-events.md)

- [ ] [packages/core/src/events/diagnostics.ts](../../../../packages/core/src/events/diagnostics.ts) — added; before `absent`, snapshot `b895e61b119e`.
- [ ] [packages/core/src/events/index.ts](../../../../packages/core/src/events/index.ts) — modified; before `0484ad2c9c88`, snapshot `0262d3c361c5`.
- [ ] [packages/core/src/events/observations.ts](../../../../packages/core/src/events/observations.ts) — added; before `absent`, snapshot `12f87119e13c`.

## L018 — packages/core/src/files

[Open folder lesson](lessons/018-core-src-files.md)

- [ ] [packages/core/src/files/diagnostics.ts](../../../../packages/core/src/files/diagnostics.ts) — added; before `absent`, snapshot `32124370b9da`.
- [ ] [packages/core/src/files/index.ts](../../../../packages/core/src/files/index.ts) — modified; before `d9b9dceb7081`, snapshot `ede565db39e0`.
- [ ] [packages/core/src/files/observations.ts](../../../../packages/core/src/files/observations.ts) — added; before `absent`, snapshot `6cb5cb5b9d6c`.

## L019 — packages/core/src/i18n

[Open folder lesson](lessons/019-core-src-i18n.md)

- [ ] [packages/core/src/i18n/diagnostics.ts](../../../../packages/core/src/i18n/diagnostics.ts) — added; before `absent`, snapshot `3669d26e4270`.
- [ ] [packages/core/src/i18n/index.ts](../../../../packages/core/src/i18n/index.ts) — modified; before `1cefbddbf664`, snapshot `ba2290086c56`.
- [ ] [packages/core/src/i18n/observations.ts](../../../../packages/core/src/i18n/observations.ts) — added; before `absent`, snapshot `f45ca540413f`.

## L020 — packages/core/src/localization

[Open folder lesson](lessons/020-core-src-localization.md)

- [ ] [packages/core/src/localization/diagnostics.ts](../../../../packages/core/src/localization/diagnostics.ts) — added; before `absent`, snapshot `22588f093cf5`.
- [ ] [packages/core/src/localization/index.ts](../../../../packages/core/src/localization/index.ts) — modified; before `a4b32bd96ea9`, snapshot `182af6c41eeb`.
- [ ] [packages/core/src/localization/observations.ts](../../../../packages/core/src/localization/observations.ts) — added; before `absent`, snapshot `495ee4ba6544`.

## L021 — packages/core/src/logging

[Open folder lesson](lessons/021-core-src-logging.md)

- [ ] [packages/core/src/logging/diagnostics.ts](../../../../packages/core/src/logging/diagnostics.ts) — added; before `absent`, snapshot `4eb5712864c0`.
- [ ] [packages/core/src/logging/index.ts](../../../../packages/core/src/logging/index.ts) — modified; before `353fcb48f035`, snapshot `96b7706a8290`.
- [ ] [packages/core/src/logging/observations.ts](../../../../packages/core/src/logging/observations.ts) — added; before `absent`, snapshot `62e0d6cf3ebe`.

## L022 — packages/core/src/monitoring

[Open folder lesson](lessons/022-core-src-monitoring.md)

- [ ] [packages/core/src/monitoring/README.md](../../../../packages/core/src/monitoring/README.md) — modified; before `8422442cdec6`, snapshot `e1ec6a9f3b66`.
- [ ] [packages/core/src/monitoring/boundary-diagnostics.ts](../../../../packages/core/src/monitoring/boundary-diagnostics.ts) — added; before `absent`, snapshot `8a73fc23cd35`.
- [ ] [packages/core/src/monitoring/diagnostics.ts](../../../../packages/core/src/monitoring/diagnostics.ts) — added; before `absent`, snapshot `2c548e828d6f`.
- [ ] [packages/core/src/monitoring/health.ts](../../../../packages/core/src/monitoring/health.ts) — modified; before `d8b688effc9b`, snapshot `ab4ce21db2b3`.
- [ ] [packages/core/src/monitoring/identifiers.ts](../../../../packages/core/src/monitoring/identifiers.ts) — modified; before `e5763d735134`, snapshot `d5bf230b9621`.
- [ ] [packages/core/src/monitoring/index.ts](../../../../packages/core/src/monitoring/index.ts) — modified; before `13c1c0fe954a`, snapshot `ffe77bb7d4c6`.
- [ ] [packages/core/src/monitoring/metrics.ts](../../../../packages/core/src/monitoring/metrics.ts) — modified; before `075004433c32`, snapshot `5a079e3e78cd`.
- [ ] [packages/core/src/monitoring/observations.ts](../../../../packages/core/src/monitoring/observations.ts) — added; before `absent`, snapshot `f309ddce1f04`.
- [ ] [packages/core/src/monitoring/signals.ts](../../../../packages/core/src/monitoring/signals.ts) — modified; before `fdf193bf92e1`, snapshot `de10b47b88bb`.
- [ ] [packages/core/src/monitoring/tracing.ts](../../../../packages/core/src/monitoring/tracing.ts) — modified; before `c229af9ff0e7`, snapshot `2539cc0f49f8`.
- [ ] [packages/core/src/monitoring/validation.ts](../../../../packages/core/src/monitoring/validation.ts) — modified; before `8a2b18808ebb`, snapshot `662f595a8fe4`.

## L023 — platform/contracts

[Open folder lesson](lessons/023-platform-contracts.md)

- [ ] [platform/contracts/README.md](../../../../platform/contracts/README.md) — modified; before `b117f11e9d3c`, snapshot `af8ab5e16e78`.

## L024 — platform/contracts/contracts

[Open folder lesson](lessons/024-platform-contracts-contracts.md)

- [ ] [platform/contracts/contracts/diagnostics.v1.json](../../../../platform/contracts/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `35b4b27d7974`.

## L025 — platform/contracts/src

[Open folder lesson](lessons/025-platform-contracts-src.md)

- [ ] [platform/contracts/src/README.md](../../../../platform/contracts/src/README.md) — modified; before `a121ca021b29`, snapshot `3cf76c650f33`.
- [ ] [platform/contracts/src/app.ts](../../../../platform/contracts/src/app.ts) — modified; before `b6e7f52f34a6`, snapshot `4c8017ed88ab`.
- [ ] [platform/contracts/src/contexts.ts](../../../../platform/contracts/src/contexts.ts) — modified; before `20118697c84c`, snapshot `4ebc474f4c5e`.
- [ ] [platform/contracts/src/diagnostics.ts](../../../../platform/contracts/src/diagnostics.ts) — added; before `absent`, snapshot `3886a190984c`.
- [ ] [platform/contracts/src/errors.ts](../../../../platform/contracts/src/errors.ts) — modified; before `086a88aad718`, snapshot `7d342e94136f`.
- [ ] [platform/contracts/src/flags.ts](../../../../platform/contracts/src/flags.ts) — modified; before `4fa18629c4a7`, snapshot `fe7928c6871c`.
- [ ] [platform/contracts/src/identifiers.ts](../../../../platform/contracts/src/identifiers.ts) — modified; before `8f3e2c754442`, snapshot `0d5161448184`.
- [ ] [platform/contracts/src/index.ts](../../../../platform/contracts/src/index.ts) — modified; before `71c1b6a16d6c`, snapshot `1c220d4ca429`.
- [ ] [platform/contracts/src/observability-profiles.ts](../../../../platform/contracts/src/observability-profiles.ts) — modified; before `b2980aff4174`, snapshot `ff42d03ec65d`.
- [ ] [platform/contracts/src/observability.ts](../../../../platform/contracts/src/observability.ts) — modified; before `7f458afc59f9`, snapshot `0bf81646c676`.
- [ ] [platform/contracts/src/operational-events.ts](../../../../platform/contracts/src/operational-events.ts) — modified; before `9d31e69d2350`, snapshot `8c067ad28cb0`.
- [ ] [platform/contracts/src/operational-observations.ts](../../../../platform/contracts/src/operational-observations.ts) — added; before `absent`, snapshot `56e732966a10`.
- [ ] [platform/contracts/src/registration-diagnostics.ts](../../../../platform/contracts/src/registration-diagnostics.ts) — added; before `absent`, snapshot `2f10b6d7cbe2`.
- [ ] [platform/contracts/src/routes.ts](../../../../platform/contracts/src/routes.ts) — modified; before `6561429872ba`, snapshot `bc3971d3de06`.
- [ ] [platform/contracts/src/validation.ts](../../../../platform/contracts/src/validation.ts) — modified; before `120b8e608291`, snapshot `7f7bee889d06`.

## L026 — platform/contracts/tests

[Open folder lesson](lessons/026-platform-contracts-tests.md)

- [ ] [platform/contracts/tests/contract/platform-contracts-runtime.test.ts](../../../../platform/contracts/tests/contract/platform-contracts-runtime.test.ts) — modified; before `b1c1949fe36b`, snapshot `62bdc70a38bf`.
- [ ] [platform/contracts/tests/type-level/platform-contracts-types.test.ts](../../../../platform/contracts/tests/type-level/platform-contracts-types.test.ts) — modified; before `33cd48c21df0`, snapshot `50604d633dc4`.
- [ ] [platform/contracts/tests/contract/registration-diagnostics-runtime.test.ts](../../../../platform/contracts/tests/contract/registration-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `f7903da2c37d`.
- [ ] [platform/contracts/tests/run-runtime-tests.mjs](../../../../platform/contracts/tests/run-runtime-tests.mjs) — modified; before `b404ff35dcbc`, snapshot `aa81015a3d23`.

## L027 — platform/adapters/aws/runtime/ecs-fargate

[Open folder lesson](lessons/027-aws-runtime-ecs-fargate.md)

- [ ] [platform/adapters/aws/runtime/ecs-fargate/README.md](../../../../platform/adapters/aws/runtime/ecs-fargate/README.md) — modified; before `20eeccb96f7a`, snapshot `9a6d30cf2787`.

## L028 — platform/adapters/aws/runtime/ecs-fargate/src

[Open folder lesson](lessons/028-runtime-ecs-fargate-src.md)

- [ ] [platform/adapters/aws/runtime/ecs-fargate/src/index.ts](../../../../platform/adapters/aws/runtime/ecs-fargate/src/index.ts) — modified; before `7e737254ee7c`, snapshot `6b49a26710f4`.

## L029 — platform/adapters/aws/runtime/ecs-fargate/tests

[Open folder lesson](lessons/029-runtime-ecs-fargate-tests.md)

- [ ] [platform/adapters/aws/runtime/ecs-fargate/tests/test-infrastructure/static-validation/ecs-fargate-adapter-boundaries.test.mjs](../../../../platform/adapters/aws/runtime/ecs-fargate/tests/test-infrastructure/static-validation/ecs-fargate-adapter-boundaries.test.mjs) — modified; before `5cb2f87a073f`, snapshot `dcff0570d957`.
- [ ] [platform/adapters/aws/runtime/ecs-fargate/tests/contract/ecs-fargate-adapter-runtime.test.ts](../../../../platform/adapters/aws/runtime/ecs-fargate/tests/contract/ecs-fargate-adapter-runtime.test.ts) — modified; before `12cc1cd72778`, snapshot `b9eb0962f8c6`.
- [ ] [platform/adapters/aws/runtime/ecs-fargate/tests/type-level/ecs-fargate-adapter-types.test.ts](../../../../platform/adapters/aws/runtime/ecs-fargate/tests/type-level/ecs-fargate-adapter-types.test.ts) — added; before `absent`, snapshot `6640dfb8e405`.
- [ ] [platform/adapters/aws/runtime/ecs-fargate/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/runtime/ecs-fargate/tests/run-runtime-tests.mjs) — modified; before `1e2bc3a149a3`, snapshot `c326b9923157`.

## L030 — platform/runtime

[Open folder lesson](lessons/030-platform-runtime.md)

- [ ] [platform/runtime/README.md](../../../../platform/runtime/README.md) — modified; before `866512a7ec68`, snapshot `12271d520507`.

## L031 — platform/runtime/contracts

[Open folder lesson](lessons/031-platform-runtime-contracts.md)

- [ ] [platform/runtime/contracts/diagnostics.v1.json](../../../../platform/runtime/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `1eff9471a561`.

## L032 — platform/runtime/src

[Open folder lesson](lessons/032-platform-runtime-src.md)

- [ ] [platform/runtime/src/README.md](../../../../platform/runtime/src/README.md) — modified; before `9b526a323545`, snapshot `0433503b65c4`.
- [ ] [platform/runtime/src/contexts.ts](../../../../platform/runtime/src/contexts.ts) — modified; before `449d30964ec3`, snapshot `fa23cc35fcf8`.
- [ ] [platform/runtime/src/diagnostics.ts](../../../../platform/runtime/src/diagnostics.ts) — added; before `absent`, snapshot `e4aad0d37882`.
- [ ] [platform/runtime/src/errors.ts](../../../../platform/runtime/src/errors.ts) — modified; before `b1860ff2fd29`, snapshot `b59207cf8b13`.
- [ ] [platform/runtime/src/index.ts](../../../../platform/runtime/src/index.ts) — modified; before `4240f00d1db6`, snapshot `864ae5fbde20`.
- [ ] [platform/runtime/src/lifecycle.ts](../../../../platform/runtime/src/lifecycle.ts) — modified; before `dbc41e516537`, snapshot `a23dee92a56d`.
- [ ] [platform/runtime/src/registry.ts](../../../../platform/runtime/src/registry.ts) — modified; before `0f2efc78f465`, snapshot `d4ac8c2b156b`.

## L033 — platform/runtime/tests

[Open folder lesson](lessons/033-platform-runtime-tests.md)

- [ ] [platform/runtime/tests/unit/context-diagnostics-runtime.test.ts](../../../../platform/runtime/tests/unit/context-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `fcedc48d6f53`.
- [ ] [platform/runtime/tests/integration/diagnostics-runtime.test.ts](../../../../platform/runtime/tests/integration/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `ddbf62eb3e52`.
- [ ] [platform/runtime/tests/integration/lifecycle-diagnostics-runtime.test.ts](../../../../platform/runtime/tests/integration/lifecycle-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `ea2da30646fa`.
- [ ] [platform/runtime/tests/type-level/lifecycle-diagnostics-types.test.ts](../../../../platform/runtime/tests/type-level/lifecycle-diagnostics-types.test.ts) — added; before `absent`, snapshot `2eae7841fc08`.
- [ ] [platform/runtime/tests/integration/mount-boundary-diagnostics-runtime.test.ts](../../../../platform/runtime/tests/integration/mount-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `1a3f827e694d`.
- [ ] [platform/runtime/tests/integration/registration-diagnostics-runtime.test.ts](../../../../platform/runtime/tests/integration/registration-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `31ccf7705ea2`.

## L034 — platform/testing

[Open folder lesson](lessons/034-platform-testing.md)

- [ ] [platform/testing/README.md](../../../../platform/testing/README.md) — modified; before `67a5d1a9ac34`, snapshot `e8e14ebbfd8b`.

## L035 — platform/testing/src

[Open folder lesson](lessons/035-platform-testing-src.md)

- [ ] [platform/testing/src/index.ts](../../../../platform/testing/src/index.ts) — modified; before `7d23303274c7`, snapshot `a31e2211acd2`.

## L036 — platform/testing/tests

[Open folder lesson](lessons/036-platform-testing-tests.md)

- [ ] [platform/testing/tests/integration/config-evidence-runtime.test.ts](../../../../platform/testing/tests/integration/config-evidence-runtime.test.ts) — added; before `absent`, snapshot `f9c58a991d69`.
- [ ] [platform/testing/tests/unit/diagnostics-runtime.test.ts](../../../../platform/testing/tests/unit/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `8710f42a9a53`.
- [ ] [platform/testing/tests/integration/mount-boundary-diagnostics-runtime.test.ts](../../../../platform/testing/tests/integration/mount-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `373aa1183e56`.

## L037 — platform/server

[Open folder lesson](lessons/037-platform-server.md)

- [ ] [platform/server/README.md](../../../../platform/server/README.md) — modified; before `24a7202bf1c6`, snapshot `dbc9c670260a`.

## L038 — platform/server/contracts

[Open folder lesson](lessons/038-platform-server-contracts.md)

- [ ] [platform/server/contracts/diagnostics.v1.json](../../../../platform/server/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `3daad86145aa`.

## L039 — platform/server/src

[Open folder lesson](lessons/039-platform-server-src.md)

- [ ] [platform/server/src/README.md](../../../../platform/server/src/README.md) — modified; before `2c322297a61b`, snapshot `739e6d415f37`.
- [ ] [platform/server/src/diagnostics.ts](../../../../platform/server/src/diagnostics.ts) — added; before `absent`, snapshot `53174bc250c7`.
- [ ] [platform/server/src/index.ts](../../../../platform/server/src/index.ts) — modified; before `01851429fc67`, snapshot `3e97d703e3ba`.
- [ ] [platform/server/src/main.ts](../../../../platform/server/src/main.ts) — modified; before `31ab47c49aaf`, snapshot `0f0dac955368`.
- [ ] [platform/server/src/transport.ts](../../../../platform/server/src/transport.ts) — modified; before `7a143e8f9b20`, snapshot `7956c666bb7d`.

## L040 — platform/server/src/configuration

[Open folder lesson](lessons/040-server-src-configuration.md)

- [ ] [platform/server/src/configuration/README.md](../../../../platform/server/src/configuration/README.md) — modified; before `a0cc28449bad`, snapshot `520a2b84c91c`.
- [ ] [platform/server/src/configuration/index.ts](../../../../platform/server/src/configuration/index.ts) — modified; before `a0c2bbf3e27b`, snapshot `62e2c1075cfe`.
- [ ] [platform/server/src/configuration/runtime.ts](../../../../platform/server/src/configuration/runtime.ts) — modified; before `783566041994`, snapshot `535035e195c5`.

## L041 — platform/server/src/verification

[Open folder lesson](lessons/041-server-src-verification.md)

- [ ] [platform/server/src/verification/README.md](../../../../platform/server/src/verification/README.md) — modified; before `916fd0594a46`, snapshot `edaaf624f2a7`.
- [ ] [platform/server/src/verification/release.ts](../../../../platform/server/src/verification/release.ts) — modified; before `81e1506e5404`, snapshot `24d589b5fbe0`.

## L042 — platform/server/tests

[Open folder lesson](lessons/042-platform-server-tests.md)

- [ ] [platform/server/tests/integration/builtin-evidence-runtime.test.ts](../../../../platform/server/tests/integration/builtin-evidence-runtime.test.ts) — added; before `absent`, snapshot `4eed68a6744f`.
- [ ] [platform/server/tests/unit/configuration-omissions-runtime.test.ts](../../../../platform/server/tests/unit/configuration-omissions-runtime.test.ts) — added; before `absent`, snapshot `0a09f9c408a1`.
- [ ] [platform/server/tests/integration/configuration-runtime.test.ts](../../../../platform/server/tests/integration/configuration-runtime.test.ts) — added; before `absent`, snapshot `4f3d5d5e1693`.
- [ ] [platform/server/tests/integration/diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `16efca98a600`.
- [ ] [platform/server/tests/integration/health-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/health-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `d1fa87cf8783`.
- [ ] [platform/server/tests/integration/metric-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/metric-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `6244f93d4087`.
- [ ] [platform/server/tests/integration/platform-server-runtime.test.ts](../../../../platform/server/tests/integration/platform-server-runtime.test.ts) — modified; before `de02d2ea1a76`, snapshot `70f5a32ab3f2`.
- [ ] [platform/server/tests/type-level/platform-server-types.test.ts](../../../../platform/server/tests/type-level/platform-server-types.test.ts) — modified; before `b2f1b07ab1b6`, snapshot `24026805419e`.
- [ ] [platform/server/tests/integration/process-boundary-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/process-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `660ccd044300`.
- [ ] [platform/server/tests/integration/request-boundary-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/request-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `b106c0023662`.
- [ ] [platform/server/tests/integration/request-observation-runtime.test.ts](../../../../platform/server/tests/integration/request-observation-runtime.test.ts) — added; before `absent`, snapshot `e62a8310278d`.
- [ ] [platform/server/tests/run-runtime-tests.mjs](../../../../platform/server/tests/run-runtime-tests.mjs) — modified; before `5391e040aa6e`, snapshot `5f47db0d7359`.
- [ ] [platform/server/tests/integration/security-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/security-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `2ef392548ae3`.
- [ ] [platform/server/tests/integration/startup-configuration-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/startup-configuration-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `b4e91f9a2461`.
- [ ] [platform/server/tests/unit/transport-configuration-diagnostics-runtime.test.ts](../../../../platform/server/tests/unit/transport-configuration-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `718af6a2c060`.
- [ ] [platform/server/tests/integration/transport-diagnostics-runtime.test.ts](../../../../platform/server/tests/integration/transport-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `960f1629e53d`.
- [ ] [platform/server/tests/type-level/transport-diagnostics-types.test.ts](../../../../platform/server/tests/type-level/transport-diagnostics-types.test.ts) — added; before `absent`, snapshot `8a160652e83a`.

## L043 — platform/health

[Open folder lesson](lessons/043-platform-health.md)

- [ ] [platform/health/README.md](../../../../platform/health/README.md) — added; before `absent`, snapshot `f073c8520b20`.

## L044 — platform/health/contracts

[Open folder lesson](lessons/044-platform-health-contracts.md)

- [ ] [platform/health/contracts/diagnostics.v1.json](../../../../platform/health/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `6e742fd01065`.

## L045 — platform/health/src

[Open folder lesson](lessons/045-platform-health-src.md)

- [ ] [platform/health/src/diagnostics.ts](../../../../platform/health/src/diagnostics.ts) — added; before `absent`, snapshot `9d52c0d1e644`.
- [ ] [platform/health/src/index.ts](../../../../platform/health/src/index.ts) — modified; before `461f6cd99849`, snapshot `956ec4768a29`.
- [ ] [platform/health/src/public-details.ts](../../../../platform/health/src/public-details.ts) — added; before `absent`, snapshot `67a39a20b7c1`.

## L046 — platform/health/tests

[Open folder lesson](lessons/046-platform-health-tests.md)

- [ ] [platform/health/tests/integration/diagnostics-runtime.test.ts](../../../../platform/health/tests/integration/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `9e4477bd88d5`.
- [ ] [platform/health/tests/integration/platform-health-runtime.test.ts](../../../../platform/health/tests/integration/platform-health-runtime.test.ts) — modified; before `320592b3a152`, snapshot `975f98bbb518`.
- [ ] [platform/health/tests/type-level/platform-health-types.test.ts](../../../../platform/health/tests/type-level/platform-health-types.test.ts) — modified; before `6409f41f9464`, snapshot `fd8d80cb011f`.

## L047 — packages/core/src/security

[Open folder lesson](lessons/047-core-src-security.md)

- [ ] [packages/core/src/security/classification.ts](../../../../packages/core/src/security/classification.ts) — modified; before `a49e486c3e9e`, snapshot `22feb385debc`.
- [ ] [packages/core/src/security/diagnostics.ts](../../../../packages/core/src/security/diagnostics.ts) — added; before `absent`, snapshot `073dc471ecd4`.
- [ ] [packages/core/src/security/hashing.ts](../../../../packages/core/src/security/hashing.ts) — modified; before `faf561ed3630`, snapshot `21a4f7c1239b`.
- [ ] [packages/core/src/security/index.ts](../../../../packages/core/src/security/index.ts) — modified; before `aad5c6f54180`, snapshot `c38bad954714`.
- [ ] [packages/core/src/security/policy.ts](../../../../packages/core/src/security/policy.ts) — modified; before `897375937476`, snapshot `24d7cecc96c8`.
- [ ] [packages/core/src/security/secrets.ts](../../../../packages/core/src/security/secrets.ts) — modified; before `53a1cde1529f`, snapshot `ffab575c0f21`.

## L048 — platform/adapters/aws/auth/cognito/src

[Open folder lesson](lessons/048-auth-cognito-src.md)

- [ ] [platform/adapters/aws/auth/cognito/src/index.ts](../../../../platform/adapters/aws/auth/cognito/src/index.ts) — modified; before `5792fa63bda5`, snapshot `e1295f8c1fb9`.

## L049 — platform/adapters/aws/auth/cognito/tests

[Open folder lesson](lessons/049-auth-cognito-tests.md)

- [ ] [platform/adapters/aws/auth/cognito/tests/contract/cognito-adapter-runtime.test.ts](../../../../platform/adapters/aws/auth/cognito/tests/contract/cognito-adapter-runtime.test.ts) — modified; before `b87b563bedb8`, snapshot `c310a82f1174`.
- [ ] [platform/adapters/aws/auth/cognito/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/auth/cognito/tests/run-runtime-tests.mjs) — modified; before `fa3aa27f00e0`, snapshot `c3f7ace1d565`.

## L050 — platform/adapters/aws/security/dynamodb-rate-limiter

[Open folder lesson](lessons/050-aws-security-dynamodb-rate-limiter.md)

- [ ] [platform/adapters/aws/security/dynamodb-rate-limiter/README.md](../../../../platform/adapters/aws/security/dynamodb-rate-limiter/README.md) — modified; before `4df287ee1096`, snapshot `3c405b128b67`.

## L051 — platform/adapters/aws/security/dynamodb-rate-limiter/src

[Open folder lesson](lessons/051-security-dynamodb-rate-limiter-src.md)

- [ ] [platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts](../../../../platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts) — modified; before `f1d73a5a5d41`, snapshot `d1a15ec917f8`.

## L052 — platform/adapters/aws/security/dynamodb-rate-limiter/tests

[Open folder lesson](lessons/052-security-dynamodb-rate-limiter-tests.md)

- [ ] [platform/adapters/aws/security/dynamodb-rate-limiter/tests/contract/dynamodb-rate-limiter-runtime.test.ts](../../../../platform/adapters/aws/security/dynamodb-rate-limiter/tests/contract/dynamodb-rate-limiter-runtime.test.ts) — modified; before `30c2e43843ae`, snapshot `6498ec0117ad`.
- [ ] [platform/adapters/aws/security/dynamodb-rate-limiter/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/security/dynamodb-rate-limiter/tests/run-runtime-tests.mjs) — modified; before `f771db529dd4`, snapshot `baeff4ab64ad`.

## L053 — platform/security

[Open folder lesson](lessons/053-platform-security.md)

- [ ] [platform/security/README.md](../../../../platform/security/README.md) — modified; before `9c4f8394a48c`, snapshot `b1ff537fbb35`.

## L054 — platform/security/contracts

[Open folder lesson](lessons/054-platform-security-contracts.md)

- [ ] [platform/security/contracts/diagnostics.v1.json](../../../../platform/security/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `93d9c25b5980`.

## L055 — platform/security/src

[Open folder lesson](lessons/055-platform-security-src.md)

- [ ] [platform/security/src/README.md](../../../../platform/security/src/README.md) — modified; before `e81f5a802c81`, snapshot `98416d23b416`.
- [ ] [platform/security/src/authentication.ts](../../../../platform/security/src/authentication.ts) — modified; before `f9d3a942202c`, snapshot `f2ae1c6a9978`.
- [ ] [platform/security/src/authorization.ts](../../../../platform/security/src/authorization.ts) — modified; before `da7000f2c638`, snapshot `4af20c124b67`.
- [ ] [platform/security/src/certificates.ts](../../../../platform/security/src/certificates.ts) — added; before `absent`, snapshot `e43a02071dea`.
- [ ] [platform/security/src/diagnostics.ts](../../../../platform/security/src/diagnostics.ts) — added; before `absent`, snapshot `77f0648756fd`.
- [ ] [platform/security/src/errors.ts](../../../../platform/security/src/errors.ts) — modified; before `be6488e1e8d1`, snapshot `930618f945fd`.
- [ ] [platform/security/src/headers.ts](../../../../platform/security/src/headers.ts) — modified; before `37eeba3e342c`, snapshot `64fc1a492e49`.
- [ ] [platform/security/src/index.ts](../../../../platform/security/src/index.ts) — modified; before `7ef7d79fffb8`, snapshot `0cd02a8a5919`.
- [ ] [platform/security/src/jwt.ts](../../../../platform/security/src/jwt.ts) — modified; before `77d2b85e5cb7`, snapshot `6753e05211f7`.
- [ ] [platform/security/src/rate-limiting.ts](../../../../platform/security/src/rate-limiting.ts) — modified; before `73f2caabae02`, snapshot `3c8e49899cdb`.

## L056 — platform/security/tests

[Open folder lesson](lessons/056-platform-security-tests.md)

- [ ] [platform/security/tests/unit/configuration-predicate-diagnostics-runtime.test.ts](../../../../platform/security/tests/unit/configuration-predicate-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `9e3e614c7f1d`.
- [ ] [platform/security/tests/integration/platform-security-runtime.test.ts](../../../../platform/security/tests/integration/platform-security-runtime.test.ts) — modified; before `9dec2b26a0d5`, snapshot `656fa494b677`.
- [ ] [platform/security/tests/type-level/platform-security-types.test.ts](../../../../platform/security/tests/type-level/platform-security-types.test.ts) — modified; before `54e6f96116b0`, snapshot `347f362a4f07`.
- [ ] [platform/security/tests/run-runtime-tests.mjs](../../../../platform/security/tests/run-runtime-tests.mjs) — modified; before `ba1885c92f51`, snapshot `b9d6ee7ae819`.
- [ ] [platform/security/tests/unit/security-certificates-runtime.test.ts](../../../../platform/security/tests/unit/security-certificates-runtime.test.ts) — added; before `absent`, snapshot `4ee807f9a200`.
- [ ] [platform/security/tests/type-level/security-certificates-types.test.ts](../../../../platform/security/tests/type-level/security-certificates-types.test.ts) — added; before `absent`, snapshot `198ce55865cf`.
- [ ] [platform/security/tests/unit/security-operation-diagnostics-runtime.test.ts](../../../../platform/security/tests/unit/security-operation-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `56402af826f0`.
- [ ] [platform/security/tests/type-level/security-operation-diagnostics-types.test.ts](../../../../platform/security/tests/type-level/security-operation-diagnostics-types.test.ts) — added; before `absent`, snapshot `8d167037ab82`.

## L057 — packages/core/src/persistence

[Open folder lesson](lessons/057-core-src-persistence.md)

- [ ] [packages/core/src/persistence/README.md](../../../../packages/core/src/persistence/README.md) — modified; before `4f72d4c74c39`, snapshot `f47b1c8befcb`.
- [ ] [packages/core/src/persistence/diagnostics.ts](../../../../packages/core/src/persistence/diagnostics.ts) — added; before `absent`, snapshot `eb4601f92783`.
- [ ] [packages/core/src/persistence/errors.ts](../../../../packages/core/src/persistence/errors.ts) — modified; before `9f632da9e0f3`, snapshot `4eddea3edc2d`.
- [ ] [packages/core/src/persistence/in-memory.ts](../../../../packages/core/src/persistence/in-memory.ts) — modified; before `c9bb0ce9552a`, snapshot `22303ff5115c`.
- [ ] [packages/core/src/persistence/index.ts](../../../../packages/core/src/persistence/index.ts) — modified; before `d80c0a18dac3`, snapshot `d32939ed1747`.
- [ ] [packages/core/src/persistence/lifecycle.ts](../../../../packages/core/src/persistence/lifecycle.ts) — modified; before `5919f73f1139`, snapshot `14ff1e5b70a7`.
- [ ] [packages/core/src/persistence/lineage.ts](../../../../packages/core/src/persistence/lineage.ts) — modified; before `60e8192b4dbb`, snapshot `6c10356e36a2`.
- [ ] [packages/core/src/persistence/outbox.ts](../../../../packages/core/src/persistence/outbox.ts) — modified; before `c50f99d639f6`, snapshot `67beed2467ac`.
- [ ] [packages/core/src/persistence/pagination.ts](../../../../packages/core/src/persistence/pagination.ts) — modified; before `aba5fc086b24`, snapshot `68e2ddd26627`.

## L058 — platform/persistence

[Open folder lesson](lessons/058-platform-persistence.md)

- [ ] [platform/persistence/README.md](../../../../platform/persistence/README.md) — modified; before `6d6978c7d8f6`, snapshot `d2256c29d209`.

## L059 — platform/persistence/contracts

[Open folder lesson](lessons/059-platform-persistence-contracts.md)

- [ ] [platform/persistence/contracts/diagnostics.v1.json](../../../../platform/persistence/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `97e421823361`.

## L060 — platform/persistence/src

[Open folder lesson](lessons/060-platform-persistence-src.md)

- [ ] [platform/persistence/src/diagnostics.ts](../../../../platform/persistence/src/diagnostics.ts) — added; before `absent`, snapshot `b92176a8437e`.
- [ ] [platform/persistence/src/errors.ts](../../../../platform/persistence/src/errors.ts) — modified; before `952b0f5be7c9`, snapshot `32d26a7fbcb8`.
- [ ] [platform/persistence/src/index.ts](../../../../platform/persistence/src/index.ts) — modified; before `77052907ce39`, snapshot `b72f477f8737`.
- [ ] [platform/persistence/src/lineage.ts](../../../../platform/persistence/src/lineage.ts) — modified; before `00bbcb240471`, snapshot `4e1d8891257e`.
- [ ] [platform/persistence/src/outbox.ts](../../../../platform/persistence/src/outbox.ts) — modified; before `ebe17d3a1f74`, snapshot `299ccb0c1929`.
- [ ] [platform/persistence/src/processing.ts](../../../../platform/persistence/src/processing.ts) — modified; before `d95320dbfff5`, snapshot `6abf139a42fd`.
- [ ] [platform/persistence/src/relay.ts](../../../../platform/persistence/src/relay.ts) — modified; before `f21fcf9c5892`, snapshot `111e69b8567e`.
- [ ] [platform/persistence/src/transaction.ts](../../../../platform/persistence/src/transaction.ts) — modified; before `53b71a9bcce5`, snapshot `3a263fce516f`.
- [ ] [platform/persistence/src/types.ts](../../../../platform/persistence/src/types.ts) — modified; before `72ade7cb6560`, snapshot `41c9d5dfca23`.

## L061 — platform/persistence/src/observability

[Open folder lesson](lessons/061-persistence-src-observability.md)

- [ ] [platform/persistence/src/observability/README.md](../../../../platform/persistence/src/observability/README.md) — modified; before `a8e71a6944f0`, snapshot `4300399901d6`.
- [ ] [platform/persistence/src/observability/integration.ts](../../../../platform/persistence/src/observability/integration.ts) — modified; before `edb05fa3604e`, snapshot `99ccab8803e0`.
- [ ] [platform/persistence/src/observability/port.ts](../../../../platform/persistence/src/observability/port.ts) — modified; before `9c34bb5a93de`, snapshot `0acdc8983d09`.

## L062 — platform/persistence/tests

[Open folder lesson](lessons/062-platform-persistence-tests.md)

- [ ] [platform/persistence/tests/integration/platform-persistence-observability-runtime.test.ts](../../../../platform/persistence/tests/integration/platform-persistence-observability-runtime.test.ts) — modified; before `d1d7caa8d4d1`, snapshot `deb7caaf5086`.
- [ ] [platform/persistence/tests/type-level/platform-persistence-observability-types.test.ts](../../../../platform/persistence/tests/type-level/platform-persistence-observability-types.test.ts) — modified; before `74e9697ea6ef`, snapshot `9ac46a3652b9`.
- [ ] [platform/persistence/tests/integration/platform-persistence-runtime.test.ts](../../../../platform/persistence/tests/integration/platform-persistence-runtime.test.ts) — modified; before `2e7352906e63`, snapshot `3659d3919357`.
- [ ] [platform/persistence/tests/type-level/platform-persistence-types.test.ts](../../../../platform/persistence/tests/type-level/platform-persistence-types.test.ts) — modified; before `5b02a1df9f0d`, snapshot `a51f9b28d725`.

## L063 — platform/adapters/aws/persistence/postgresql

[Open folder lesson](lessons/063-aws-persistence-postgresql.md)

- [ ] [platform/adapters/aws/persistence/postgresql/README.md](../../../../platform/adapters/aws/persistence/postgresql/README.md) — modified; before `70c8896b40d8`, snapshot `da8afc8cf6b7`.
- [ ] [platform/adapters/aws/persistence/postgresql/package.json](../../../../platform/adapters/aws/persistence/postgresql/package.json) — modified; before `6fdf974febbf`, snapshot `78b98d00369c`.
- [ ] [platform/adapters/aws/persistence/postgresql/tsconfig.integration-test.json](../../../../platform/adapters/aws/persistence/postgresql/tsconfig.integration-test.json) — modified; before `305264e093c5`, snapshot `9e87c2eef862`.
- [ ] [platform/adapters/aws/persistence/postgresql/tsconfig.runtime-test.json](../../../../platform/adapters/aws/persistence/postgresql/tsconfig.runtime-test.json) — modified; before `2fd3f2ee3cd9`, snapshot `247260cbf1fe`.

## L064 — platform/adapters/aws/persistence/postgresql/src

[Open folder lesson](lessons/064-persistence-postgresql-src.md)

- [ ] [platform/adapters/aws/persistence/postgresql/src/config.ts](../../../../platform/adapters/aws/persistence/postgresql/src/configuration/index.ts) — modified; before `34706b351ec3`, snapshot `580b5dd0fd5d`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/connection.ts](../../../../platform/adapters/aws/persistence/postgresql/src/connection.ts) — modified; before `eab912af3d66`, snapshot `d0f7999b100d`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/credentials.ts](../../../../platform/adapters/aws/persistence/postgresql/src/credentials.ts) — added; before `absent`, snapshot `2efa25256b1a`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/errors.ts](../../../../platform/adapters/aws/persistence/postgresql/src/errors.ts) — modified; before `6c99cf706073`, snapshot `feb839681435`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/index.ts](../../../../platform/adapters/aws/persistence/postgresql/src/index.ts) — modified; before `94536fabd2f3`, snapshot `660aaa404fd5`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/lineage.ts](../../../../platform/adapters/aws/persistence/postgresql/src/lineage.ts) — modified; before `19a795f9e02c`, snapshot `fa993e157715`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/migrations.ts](../../../../platform/adapters/aws/persistence/postgresql/src/migrations.ts) — modified; before `acc80dd1c4b7`, snapshot `7fb3f48ed9d4`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/observations.ts](../../../../platform/adapters/aws/persistence/postgresql/src/observations.ts) — added; before `absent`, snapshot `aab3848e93e3`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/outbox.ts](../../../../platform/adapters/aws/persistence/postgresql/src/outbox.ts) — modified; before `b93daa5a7088`, snapshot `6086246d7667`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/processing.ts](../../../../platform/adapters/aws/persistence/postgresql/src/processing.ts) — modified; before `79f4066771dc`, snapshot `f771105cfaf5`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/rds-iam-authentication.ts](../../../../platform/adapters/aws/persistence/postgresql/src/rds-iam-authentication.ts) — modified; before `ead3700f877c`, snapshot `771067c81692`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/records.ts](../../../../platform/adapters/aws/persistence/postgresql/src/records.ts) — modified; before `09df11ef256b`, snapshot `75a00e9c37e2`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/telemetry.ts](../../../../platform/adapters/aws/persistence/postgresql/src/telemetry.ts) — modified; before `ec215519b819`, snapshot `8becfb13770a`.
- [ ] [platform/adapters/aws/persistence/postgresql/src/transactions.ts](../../../../platform/adapters/aws/persistence/postgresql/src/transactions.ts) — modified; before `cccbc723c73d`, snapshot `5e4e37140b48`.

## L065 — platform/adapters/aws/persistence/postgresql/tests

[Open folder lesson](lessons/065-persistence-postgresql-tests.md)

- [ ] [platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-diagnostics-runtime.test.ts](../../../../platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-diagnostics-runtime.test.ts) — modified; before `0566d3f2097c`, snapshot `d68f6077a049`.
- [ ] [platform/adapters/aws/persistence/postgresql/tests/test-infrastructure/static-validation/postgresql-persistence-adapter-boundaries.test.mjs](../../../../platform/adapters/aws/persistence/postgresql/tests/test-infrastructure/static-validation/postgresql-persistence-adapter-boundaries.test.mjs) — modified; before `791d2d2b9ccb`, snapshot `e167dff6fe7e`.
- [ ] [platform/adapters/aws/persistence/postgresql/tests/contract/postgresql-persistence-adapter-runtime.test.ts](../../../../platform/adapters/aws/persistence/postgresql/tests/contract/postgresql-persistence-adapter-runtime.test.ts) — modified; before `f27f4bb4773e`, snapshot `d05caa067a69`.
- [ ] [platform/adapters/aws/persistence/postgresql/tests/run-local-integration-tests.mjs](../../../../platform/adapters/aws/persistence/postgresql/tests/run-local-integration-tests.mjs) — modified; before `ec78ef91e968`, snapshot `b64ca537aa99`.
- [ ] [platform/adapters/aws/persistence/postgresql/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/persistence/postgresql/tests/run-runtime-tests.mjs) — modified; before `8be2269fc839`, snapshot `ed8b5eb7196b`.

## L066 — platform/adapters/aws/persistence/dynamodb

[Open folder lesson](lessons/066-aws-persistence-dynamodb.md)

- [ ] [platform/adapters/aws/persistence/dynamodb/README.md](../../../../platform/adapters/aws/persistence/dynamodb/README.md) — modified; before `d7ef3579f16e`, snapshot `82b66256cc8c`.
- [ ] [platform/adapters/aws/persistence/dynamodb/tsconfig.runtime-test.json](../../../../platform/adapters/aws/persistence/dynamodb/tsconfig.runtime-test.json) — modified; before `78136121e9c3`, snapshot `726141ba1c78`.

## L067 — platform/adapters/aws/persistence/dynamodb/src

[Open folder lesson](lessons/067-persistence-dynamodb-src.md)

- [ ] [platform/adapters/aws/persistence/dynamodb/src/client.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/client.ts) — modified; before `20064bb8a1e5`, snapshot `13257ad08f9b`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/configuration.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/configuration/index.ts) — modified; before `2bfdc125745d`, snapshot `5d018bc2b321`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/lineage-store.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/lineage-store.ts) — modified; before `d7007e7b02a9`, snapshot `65c77c9ff10c`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/observations.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/observations.ts) — added; before `absent`, snapshot `760f13874d94`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/outbox-store.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/outbox-store.ts) — modified; before `7e2dc0eff61a`, snapshot `2f7bc314e8bb`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/processing-store.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/processing-store.ts) — modified; before `b35e250246b3`, snapshot `c7a5b40b6614`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/records.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/records.ts) — modified; before `ee1d6a8f60f2`, snapshot `12d5e70dd5ff`.
- [ ] [platform/adapters/aws/persistence/dynamodb/src/transactions.ts](../../../../platform/adapters/aws/persistence/dynamodb/src/transactions.ts) — modified; before `4683cb7441b6`, snapshot `f92d9e948a1d`.

## L068 — platform/adapters/aws/persistence/dynamodb/tests

[Open folder lesson](lessons/068-persistence-dynamodb-tests.md)

- [ ] [platform/adapters/aws/persistence/dynamodb/tests/contract/dynamodb-persistence-adapter-runtime.test.ts](../../../../platform/adapters/aws/persistence/dynamodb/tests/contract/dynamodb-persistence-adapter-runtime.test.ts) — modified; before `6a6994bf4324`, snapshot `626fa68ebf7d`.
- [ ] [platform/adapters/aws/persistence/dynamodb/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/persistence/dynamodb/tests/run-runtime-tests.mjs) — modified; before `fa2782e9d4b1`, snapshot `d562a59c1677`.

## L069 — packages/core/src/queues

[Open folder lesson](lessons/069-core-src-queues.md)

- [ ] [packages/core/src/queues/README.md](../../../../packages/core/src/queues/README.md) — modified; before `ea7ca48ff3fe`, snapshot `e9bc7b4cb593`.
- [ ] [packages/core/src/queues/diagnostics.ts](../../../../packages/core/src/queues/diagnostics.ts) — added; before `absent`, snapshot `4d844f751df3`.
- [ ] [packages/core/src/queues/index.ts](../../../../packages/core/src/queues/index.ts) — modified; before `4e1d1222c4a5`, snapshot `9516f274cee4`.

## L070 — platform/workers

[Open folder lesson](lessons/070-platform-workers.md)

- [ ] [platform/workers/README.md](../../../../platform/workers/README.md) — modified; before `8eb68e511e60`, snapshot `195585c3739b`.

## L071 — platform/workers/contracts

[Open folder lesson](lessons/071-platform-workers-contracts.md)

- [ ] [platform/workers/contracts/diagnostics.v1.json](../../../../platform/workers/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `7e489d5cb752`.

## L072 — platform/workers/src

[Open folder lesson](lessons/072-platform-workers-src.md)

- [ ] [platform/workers/src/README.md](../../../../platform/workers/src/README.md) — modified; before `bd0d6c8afc50`, snapshot `775798b0a861`.
- [ ] [platform/workers/src/configuration-diagnostics.ts](../../../../platform/workers/src/configuration-diagnostics.ts) — added; before `absent`, snapshot `75d9d8e25e2c`.
- [ ] [platform/workers/src/diagnostics.ts](../../../../platform/workers/src/diagnostics.ts) — added; before `absent`, snapshot `1da8ce51783e`.
- [ ] [platform/workers/src/errors.ts](../../../../platform/workers/src/errors.ts) — modified; before `5ebc819906c4`, snapshot `65f4633cd489`.
- [ ] [platform/workers/src/index.ts](../../../../platform/workers/src/index.ts) — modified; before `028a734dd30a`, snapshot `d1c69543f320`.
- [ ] [platform/workers/src/main.ts](../../../../platform/workers/src/main.ts) — modified; before `018100c2d924`, snapshot `8936ae008152`.
- [ ] [platform/workers/src/queue.ts](../../../../platform/workers/src/queue.ts) — modified; before `80ec9e3e885d`, snapshot `05f8e2903f40`.
- [ ] [platform/workers/src/types.ts](../../../../platform/workers/src/types.ts) — modified; before `92393387b714`, snapshot `d4ab39fe5779`.
- [ ] [platform/workers/src/worker.ts](../../../../platform/workers/src/worker.ts) — modified; before `b58c67246703`, snapshot `22c76da0ff51`.

## L073 — platform/workers/tests

[Open folder lesson](lessons/073-platform-workers-tests.md)

- [ ] [platform/workers/tests/integration/builtin-evidence-runtime.test.ts](../../../../platform/workers/tests/integration/builtin-evidence-runtime.test.ts) — added; before `absent`, snapshot `a21b87d15d9b`.
- [ ] [platform/workers/tests/integration/context-boundary-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/context-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `44ae2c092287`.
- [ ] [platform/workers/tests/integration/delivery-boundary-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/delivery-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `59f52fe03127`.
- [ ] [platform/workers/tests/integration/health-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/health-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `2b05ab6dcdc7`.
- [ ] [platform/workers/tests/integration/lifecycle-boundary-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/lifecycle-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `03d16e67deac`.
- [ ] [platform/workers/tests/type-level/lifecycle-boundary-diagnostics-types.test.ts](../../../../platform/workers/tests/type-level/lifecycle-boundary-diagnostics-types.test.ts) — added; before `absent`, snapshot `dce641501bd0`.
- [ ] [platform/workers/tests/integration/metric-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/metric-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `7f2b5da4392b`.
- [ ] [platform/workers/tests/integration/platform-workers-runtime.test.ts](../../../../platform/workers/tests/integration/platform-workers-runtime.test.ts) — modified; before `be99b44ad628`, snapshot `7871efd0b3c3`.
- [ ] [platform/workers/tests/type-level/platform-workers-types.test.ts](../../../../platform/workers/tests/type-level/platform-workers-types.test.ts) — modified; before `f875680f735a`, snapshot `6945a1c3c289`.
- [ ] [platform/workers/tests/integration/process-boundary-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/process-boundary-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `30cb89e4456d`.
- [ ] [platform/workers/tests/integration/startup-configuration-diagnostics-runtime.test.ts](../../../../platform/workers/tests/integration/startup-configuration-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `c3d75f03ff26`.

## L074 — platform/adapters/aws/queue/sqs

[Open folder lesson](lessons/074-aws-queue-sqs.md)

- [ ] [platform/adapters/aws/queue/sqs/README.md](../../../../platform/adapters/aws/queue/sqs/README.md) — modified; before `b66544d98cb8`, snapshot `aabbbf2e1730`.

## L075 — platform/adapters/aws/queue/sqs/src

[Open folder lesson](lessons/075-queue-sqs-src.md)

- [ ] [platform/adapters/aws/queue/sqs/src/errors.ts](../../../../platform/adapters/aws/queue/sqs/src/errors.ts) — modified; before `45f617446c2f`, snapshot `3a3fbc0c1ec1`.
- [ ] [platform/adapters/aws/queue/sqs/src/messages.ts](../../../../platform/adapters/aws/queue/sqs/src/messages.ts) — modified; before `8645347637b9`, snapshot `faf54888473e`.
- [ ] [platform/adapters/aws/queue/sqs/src/observations.ts](../../../../platform/adapters/aws/queue/sqs/src/observations.ts) — added; before `absent`, snapshot `ac3e768f3c69`.
- [ ] [platform/adapters/aws/queue/sqs/src/queue.ts](../../../../platform/adapters/aws/queue/sqs/src/queue.ts) — modified; before `2a05d514ada2`, snapshot `c263565d5073`.
- [ ] [platform/adapters/aws/queue/sqs/src/worker.ts](../../../../platform/adapters/aws/queue/sqs/src/worker.ts) — modified; before `7d8cd194a5d8`, snapshot `5161a9a496c3`.

## L076 — platform/adapters/aws/queue/sqs/tests

[Open folder lesson](lessons/076-queue-sqs-tests.md)

- [ ] [platform/adapters/aws/queue/sqs/tests/contract/sqs-adapter-runtime.test.ts](../../../../platform/adapters/aws/queue/sqs/tests/contract/sqs-adapter-runtime.test.ts) — modified; before `563c7eb1e4b9`, snapshot `1637677e74f4`.

## L077 — platform/observability

[Open folder lesson](lessons/077-platform-observability.md)

- [ ] [platform/observability/README.md](../../../../platform/observability/README.md) — modified; before `82b25b73df98`, snapshot `ec5341c11675`.
- [ ] [platform/observability/tsconfig.runtime-test.json](../../../../platform/observability/tsconfig.runtime-test.json) — modified; before `def0379ff1ae`, snapshot `2a15208c6539`.

## L078 — platform/observability/contracts

[Open folder lesson](lessons/078-platform-observability-contracts.md)

- [ ] [platform/observability/contracts/diagnostics.v1.json](../../../../platform/observability/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `481a99d57cfd`.

## L079 — platform/observability/src

[Open folder lesson](lessons/079-platform-observability-src.md)

- [ ] [platform/observability/src/README.md](../../../../platform/observability/src/README.md) — modified; before `f50eb902d651`, snapshot `05e8ebb86046`.
- [ ] [platform/observability/src/boundary-definitions.ts](../../../../platform/observability/src/boundary-definitions.ts) — added; before `absent`, snapshot `4cd36a6483f5`.
- [ ] [platform/observability/src/boundary-observation.ts](../../../../platform/observability/src/boundary-observation.ts) — added; before `absent`, snapshot `65c4eba8703b`.
- [ ] [platform/observability/src/configuration.ts](../../../../platform/observability/src/configuration.ts) — added; before `absent`, snapshot `5d10687ffb94`.
- [ ] [platform/observability/src/diagnostic-log.ts](../../../../platform/observability/src/diagnostic-log.ts) — added; before `absent`, snapshot `14174749d943`.
- [ ] [platform/observability/src/diagnostics.ts](../../../../platform/observability/src/diagnostics.ts) — added; before `absent`, snapshot `f26126c88d1b`.
- [ ] [platform/observability/src/index.ts](../../../../platform/observability/src/index.ts) — modified; before `58539213b207`, snapshot `b4acb0d5c60c`.
- [ ] [platform/observability/src/logging.ts](../../../../platform/observability/src/logging.ts) — modified; before `2d7ba79ba5e6`, snapshot `04e3dd7ebcfb`.
- [ ] [platform/observability/src/metric-diagnostics.ts](../../../../platform/observability/src/metric-diagnostics.ts) — added; before `absent`, snapshot `8cff130c4441`.
- [ ] [platform/observability/src/metric-lifecycle-diagnostics.ts](../../../../platform/observability/src/metric-lifecycle-diagnostics.ts) — added; before `absent`, snapshot `f0461a0f37c9`.
- [ ] [platform/observability/src/metric-series-configuration.ts](../../../../platform/observability/src/metric-series-configuration.ts) — added; before `absent`, snapshot `54219151ed79`.
- [ ] [platform/observability/src/metrics.ts](../../../../platform/observability/src/metrics.ts) — modified; before `c16c0a94b9d9`, snapshot `1e4274c00508`.
- [ ] [platform/observability/src/normalization.ts](../../../../platform/observability/src/normalization.ts) — modified; before `6784b333d328`, snapshot `36d692014649`.
- [ ] [platform/observability/src/readiness-diagnostics.ts](../../../../platform/observability/src/readiness-diagnostics.ts) — added; before `absent`, snapshot `524d8cd19dad`.
- [ ] [platform/observability/src/readiness-observation.ts](../../../../platform/observability/src/readiness-observation.ts) — modified; before `48ffae8dac2f`, snapshot `92c2f4116524`.
- [ ] [platform/observability/src/tracing.ts](../../../../platform/observability/src/tracing.ts) — modified; before `6614ba5f5fe2`, snapshot `9e162b08d91e`.

## L080 — platform/observability/tests

[Open folder lesson](lessons/080-platform-observability-tests.md)

- [ ] [platform/observability/tests/integration/configuration-runtime.test.ts](../../../../platform/observability/tests/integration/configuration-runtime.test.ts) — added; before `absent`, snapshot `5233a37fe377`.
- [ ] [platform/observability/tests/type-level/configuration-types.test.ts](../../../../platform/observability/tests/type-level/configuration-types.test.ts) — added; before `absent`, snapshot `299f6e0564af`.
- [ ] [platform/observability/tests/integration/diagnostics-runtime.test.ts](../../../../platform/observability/tests/integration/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `b88fe2c25312`.
- [ ] [platform/observability/tests/integration/metric-diagnostics-runtime.test.ts](../../../../platform/observability/tests/integration/metric-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `06dbbff10e93`.
- [ ] [platform/observability/tests/integration/metric-lifecycle-diagnostics-runtime.test.ts](../../../../platform/observability/tests/integration/metric-lifecycle-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `e4592b27efcc`.
- [ ] [platform/observability/tests/integration/platform-observability-runtime.test.ts](../../../../platform/observability/tests/integration/platform-observability-runtime.test.ts) — modified; before `209783bb27e1`, snapshot `c17b96c5dcdd`.
- [ ] [platform/observability/tests/type-level/platform-observability-types.test.ts](../../../../platform/observability/tests/type-level/platform-observability-types.test.ts) — modified; before `4c1b14ccf3d9`, snapshot `96c744e6c4b3`.
- [ ] [platform/observability/tests/integration/readiness-diagnostics-runtime.test.ts](../../../../platform/observability/tests/integration/readiness-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `276ec367602b`.
- [ ] [platform/observability/tests/run-runtime-tests.mjs](../../../../platform/observability/tests/run-runtime-tests.mjs) — modified; before `914ab43e05cc`, snapshot `6a894883e305`.
- [ ] [platform/observability/tests/integration/security-diagnostics-runtime.test.ts](../../../../platform/observability/tests/integration/security-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `715859cbcebc`.

## L081 — platform/adapters/aws/observability/cloudwatch

[Open folder lesson](lessons/081-aws-observability-cloudwatch.md)

- [ ] [platform/adapters/aws/observability/cloudwatch/README.md](../../../../platform/adapters/aws/observability/cloudwatch/README.md) — modified; before `3cfd1fae3a54`, snapshot `46098cfd63f8`.
- [ ] [platform/adapters/aws/observability/cloudwatch/package.json](../../../../platform/adapters/aws/observability/cloudwatch/package.json) — modified; before `9f88e96b5562`, snapshot `3e12ce179aa9`.
- [ ] [platform/adapters/aws/observability/cloudwatch/tsconfig.runtime-test.json](../../../../platform/adapters/aws/observability/cloudwatch/tsconfig.runtime-test.json) — modified; before `ca58d05df31a`, snapshot `74ea0b569f79`.

## L082 — platform/adapters/aws/observability/cloudwatch/src

[Open folder lesson](lessons/082-observability-cloudwatch-src.md)

- [ ] [platform/adapters/aws/observability/cloudwatch/src/configuration.ts](../../../../platform/adapters/aws/observability/cloudwatch/src/configuration.ts) — added; before `absent`, snapshot `37d8dfa29e12`.
- [ ] [platform/adapters/aws/observability/cloudwatch/src/index.ts](../../../../platform/adapters/aws/observability/cloudwatch/src/index.ts) — modified; before `c2050120b721`, snapshot `00a57ce96a56`.
- [ ] [platform/adapters/aws/observability/cloudwatch/src/lifecycle-observation.ts](../../../../platform/adapters/aws/observability/cloudwatch/src/lifecycle-observation.ts) — added; before `absent`, snapshot `32f50621d1a0`.

## L083 — platform/adapters/aws/observability/cloudwatch/tests

[Open folder lesson](lessons/083-observability-cloudwatch-tests.md)

- [ ] [platform/adapters/aws/observability/cloudwatch/tests/test-infrastructure/static-validation/cloudwatch-otel-adapter-boundaries.test.mjs](../../../../platform/adapters/aws/observability/cloudwatch/tests/test-infrastructure/static-validation/cloudwatch-otel-adapter-boundaries.test.mjs) — modified; before `ca3593dc7a89`, snapshot `90c2380548e1`.
- [ ] [platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-adapter-runtime.test.ts](../../../../platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-adapter-runtime.test.ts) — modified; before `7ef94c20fd8b`, snapshot `afa01f710833`.
- [ ] [platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-lifecycle-runtime.test.ts](../../../../platform/adapters/aws/observability/cloudwatch/tests/contract/cloudwatch-otel-lifecycle-runtime.test.ts) — added; before `absent`, snapshot `5d9fc0ed4a94`.
- [ ] [platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs](../../../../platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs) — modified; before `fb2f575ac2e8`, snapshot `2e6b4f57516d`.

## L084 — apps/platform-smoke

[Open folder lesson](lessons/084-apps-platform-smoke.md)

- [ ] [apps/platform-smoke/README.md](../../../../apps/platform-smoke/README.md) — modified; before `bc78efbfd7c9`, snapshot `d5dbd90da9b7`.

## L085 — apps/platform-smoke/contracts

[Open folder lesson](lessons/085-apps-platform-smoke-contracts.md)

- [ ] [apps/platform-smoke/contracts/diagnostics.v1.json](../../../../apps/platform-smoke/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `1edfd9d8d3c5`.

## L086 — apps/platform-smoke/src

[Open folder lesson](lessons/086-apps-platform-smoke-src.md)

- [ ] [apps/platform-smoke/src/app.mount.ts](../../../../apps/platform-smoke/src/app.mount.ts) — modified; before `f220b1bf2a94`, snapshot `973f430f09e1`.
- [ ] [apps/platform-smoke/src/diagnostics.ts](../../../../apps/platform-smoke/src/diagnostics.ts) — added; before `absent`, snapshot `136f899a4c8e`.

## L087 — apps/platform-smoke/src/persistence

[Open folder lesson](lessons/087-platform-smoke-src-persistence.md)

- [ ] [apps/platform-smoke/src/persistence/README.md](../../../../apps/platform-smoke/src/persistence/README.md) — modified; before `e9ea8ec46640`, snapshot `ebf006fbd1f0`.
- [ ] [apps/platform-smoke/src/persistence/acceptance.ts](../../../../apps/platform-smoke/src/persistence/acceptance.ts) — modified; before `c572b9afed00`, snapshot `cdbddd767072`.

## L088 — apps/platform-smoke/tests

[Open folder lesson](lessons/088-apps-platform-smoke-tests.md)

- [ ] [apps/platform-smoke/tests/integration/configuration-validation-diagnostics-runtime.test.ts](../../../../apps/platform-smoke/tests/integration/configuration-validation-diagnostics-runtime.test.ts) — added; before `absent`, snapshot `6685b96d9c2e`.
- [ ] [apps/platform-smoke/tests/unit/diagnostics-runtime.test.ts](../../../../apps/platform-smoke/tests/unit/diagnostics-runtime.test.ts) — added; before `absent`, snapshot `64160e122b94`.
- [ ] [apps/platform-smoke/tests/integration/platform-smoke-runtime.test.ts](../../../../apps/platform-smoke/tests/integration/platform-smoke-runtime.test.ts) — modified; before `fa99972bb2d2`, snapshot `f1fa2682b5dd`.
- [ ] [apps/platform-smoke/tests/type-level/platform-smoke-types.test.ts](../../../../apps/platform-smoke/tests/type-level/platform-smoke-types.test.ts) — modified; before `dc2f08594d7c`, snapshot `c6c130d7c85e`.
- [ ] [apps/platform-smoke/tests/run-runtime-tests.mjs](../../../../apps/platform-smoke/tests/run-runtime-tests.mjs) — modified; before `22340e26fc3c`, snapshot `201e6fbe3cc9`.

## L089 — infra/04.deploy/03.product/entrypoints

[Open folder lesson](lessons/089-04-deploy-03-product-entrypoints.md)

- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts) — modified; before `02d60dadac77`, snapshot `b3719acab819`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts) — modified; before `25c7e1b5f339`, snapshot `140ae1093ae2`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts) — added; before `absent`, snapshot `51c84fde6ae3`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts) — modified; before `e87bad76b7a3`, snapshot `66dfd9070874`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts) — modified; before `527617057385`, snapshot `d68ea7cc3dba`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts) — added; before `absent`, snapshot `063b0f38be40`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts) — modified; before `9c7375d504bf`, snapshot `a2fa024e4085`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts) — modified; before `5fb9b66ff5d9`, snapshot `9929ddccce9a`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts) — modified; before `19f0541ac538`, snapshot `7f32f0735c78`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts) — modified; before `a2dffd55551b`, snapshot `d3a9a0e4e322`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts) — modified; before `73d0ff2c86b8`, snapshot `e69a49d1df7d`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts) — modified; before `bdc0e213f39f`, snapshot `3ee4e579a60c`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts) — modified; before `6216c8c7480f`, snapshot `999fb12d9fd2`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts) — modified; before `e80a45b54260`, snapshot `31b80219c3f2`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts) — added; before `absent`, snapshot `08beaa5495c1`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.ts) — added; before `absent`, snapshot `5868014059b0`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts) — modified; before `af94286aee54`, snapshot `bf274867e5ea`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts) — modified; before `545d1c1da6c6`, snapshot `43816f8a952b`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts) — modified; before `a2a99d4e2411`, snapshot `4e80a21b5877`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts) — modified; before `3307db04e9b4`, snapshot `89ecd516d28c`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts) — added; before `absent`, snapshot `b0e4f7ff4f92`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts) — modified; before `98402fd7e96f`, snapshot `83523d64135e`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-relay.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-relay.main.ts) — modified; before `fa1ef323cb35`, snapshot `da55104535f9`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts) — modified; before `9d0ccad10c18`, snapshot `0f9994c4ce0c`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts) — modified; before `90b5810de090`, snapshot `a6c61609eaeb`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-worker.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-worker.main.ts) — modified; before `343bbcf65d1a`, snapshot `b820e9fc230e`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts) — modified; before `d5259d03c0b5`, snapshot `9a52af9dc67c`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts) — modified; before `24ce0a06e3dd`, snapshot `6e970686fe92`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.ts) — modified; before `ef7fb68b26b7`, snapshot `ac8083d3cbe8`.
- [ ] [infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts) — modified; before `4610927ad950`, snapshot `13463992fb3b`.

## L090 — infra/04.deploy/03.product/entrypoints/contracts

[Open folder lesson](lessons/090-03-product-entrypoints-contracts.md)

- [ ] [infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json) — added; before `absent`, snapshot `94cc3cfd7447`.
- [ ] [infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json) — added; before `absent`, snapshot `9d6be401e15f`.
- [ ] [infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json) — added; before `absent`, snapshot `8d1689d49c48`.
- [ ] [infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json) — added; before `absent`, snapshot `34bf22de6af2`.
- [ ] [infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-diagnostics.v1.json) — added; before `absent`, snapshot `70557f78b2a6`.
- [ ] [infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-postgresql-operation-diagnostics.v1.json](../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-postgresql-operation-diagnostics.v1.json) — added; before `absent`, snapshot `2879a47277b3`.

## L091 — products/kanbien-platform/tests

[Open folder lesson](lessons/091-products-kanbien-platform-tests.md)

- [ ] [products/kanbien-platform/tests/run-runtime-tests.mjs](../../../../products/kanbien-platform/tests/run-runtime-tests.mjs) — modified; before `d3964b4d610b`, snapshot `da45c70d41f8`.

## L092 — scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition

[Open folder lesson](lessons/092-lifecycle-20-build-core-server-persistence-composition.md)

- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/README.md](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/README.md) — modified; before `a657f760b530`, snapshot `f75a2b878163`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs) — modified; before `88f7b9fa681e`, snapshot `e33bd13b9bfa`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-isolation-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-isolation-test.mjs) — added; before `absent`, snapshot `c3c28e67d651`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs) — added; before `absent`, snapshot `ea2de5129b13`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/observability-runtime-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/observability-runtime-test.mjs) — modified; before `ecee98dc715e`, snapshot `6df6e44d5172`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs) — modified; before `f157857c4247`, snapshot `9a4b77aa29d6`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs) — modified; before `708e9ceff8c5`, snapshot `1b1897b9c820`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh) — modified; before `eb275046d0a3`, snapshot `ddb3788fa0e9`.

## L093 — infra/04.deploy/03.product/image/core-server-persistence

[Open folder lesson](lessons/093-03-product-image-core-server-persistence.md)

- [ ] [infra/04.deploy/03.product/image/core-server-persistence/Dockerfile](../../../../infra/04.deploy/03.product/image/core-server-persistence/Dockerfile) — modified; before `04c63efcd995`, snapshot `bb0afb316878`.

## L094 — scripts/04.deploy/build-platform-shell-image

[Open folder lesson](lessons/094-scripts-04-deploy-build-platform-shell-image.md)

- [ ] [scripts/04.deploy/build-platform-shell-image/check-source.sh](../../../../scripts/04.deploy/build-platform-shell-image/check-source.sh) — modified; before `34ffb556445d`, snapshot `766d24c213dc`.
- [ ] [scripts/04.deploy/build-platform-shell-image/configuration-diagnostic-test.mjs](../../../../scripts/04.deploy/build-platform-shell-image/configuration-diagnostic-test.mjs) — added; before `absent`, snapshot `aa7bfc954bb3`.
- [ ] [scripts/04.deploy/build-platform-shell-image/delivery-diagnostic-test.mjs](../../../../scripts/04.deploy/build-platform-shell-image/delivery-diagnostic-test.mjs) — added; before `absent`, snapshot `167696658905`.
- [ ] [scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs](../../../../scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs) — modified; before `cd6eba6a4002`, snapshot `130a02008092`.
- [ ] [scripts/04.deploy/build-platform-shell-image/process-diagnostic-test.mjs](../../../../scripts/04.deploy/build-platform-shell-image/process-diagnostic-test.mjs) — added; before `absent`, snapshot `19b50f8499bf`.
- [ ] [scripts/04.deploy/build-platform-shell-image/script.sh](../../../../scripts/04.deploy/build-platform-shell-image/script.sh) — modified; before `149a9ab97468`, snapshot `f568dc67f05f`.
- [ ] [scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs](../../../../scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs) — modified; before `01b7a2c4f3c7`, snapshot `acac4de90d66`.

## L095 — scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary

[Open folder lesson](lessons/095-lifecycle-20-build-core-server-dependency-boundary.md)

- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/runtime-test.mjs](../../../../scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/runtime-test.mjs) — modified; before `4cc31fddef84`, snapshot `e6926e1df92a`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.py](../../../../scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.py) — modified; before `fb58983f2f89`, snapshot `4b8cc9e3a99a`.
- [ ] [scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh) — modified; before `7f004d912417`, snapshot `1301be4acf88`.

## L096 — scripts/04.deploy/lifecycle/20-build/runnable-program-contract

[Open folder lesson](lessons/096-lifecycle-20-build-runnable-program-contract.md)

- [ ] [scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py](../../../../scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py) — modified; before `8cbe09a0f183`, snapshot `fadf78cd71ae`.
- [ ] [scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh) — modified; before `82ea2e0a07c9`, snapshot `252dc4005ac4`.

## L097 — scripts/04.deploy/lifecycle/40-package/build-core-server-image

[Open folder lesson](lessons/097-lifecycle-40-package-build-core-server-image.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs) — modified; before `6bb01f75b65f`, snapshot `397d43925c12`.
- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py) — added; before `absent`, snapshot `9b4f55d8afc8`.
- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh) — modified; before `ff93bc6dfc35`, snapshot `7f0405755571`.
- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py) — modified; before `d3b6f6fbf712`, snapshot `932b20900f35`.

## L098 — scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image

[Open folder lesson](lessons/098-lifecycle-40-package-build-core-server-persistence-image.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs) — modified; before `fadd19cca852`, snapshot `91a5dd6eb3ae`.
- [ ] [scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh) — modified; before `f6ff3fbb1f9c`, snapshot `140e3e9a7383`.

## L099 — scripts/04.deploy/lifecycle/40-package/package-custody-receipt

[Open folder lesson](lessons/099-lifecycle-40-package-package-custody-receipt.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py](../../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py) — modified; before `5ed894a8fb17`, snapshot `dfac6f1b8b15`.
- [ ] [scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification-test.py](../../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification-test.py) — modified; before `f8285e291db6`, snapshot `4de97d110d4b`.
- [ ] [scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py](../../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py) — modified; before `400b6d5dcf8f`, snapshot `d1e8092e6959`.

## L100 — scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage

[Open folder lesson](lessons/100-provider-adapters-aws-iam-policy-coverage.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage/script.py](../../../../scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage/script.py) — modified; before `001c7dd8a026`, snapshot `1e386d4a89cd`.

## L101 — scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image

[Open folder lesson](lessons/101-lifecycle-40-package-qualify-retained-persistence-rollback-image.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image/script.sh) — modified; before `e7f305dfe549`, snapshot `fe4f0bd630d0`.

## L102 — scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image

[Open folder lesson](lessons/102-lifecycle-40-package-smoke-test-core-server-image.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh) — modified; before `a5685fed636d`, snapshot `1582a2d15511`.

## L103 — scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image

[Open folder lesson](lessons/103-lifecycle-40-package-smoke-test-core-server-persistence-image.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/local-public-recovery-test.py](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/local-public-recovery-test.py) — modified; before `62db94da5695`, snapshot `d6464568e17e`.
- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh) — modified; before `00b5a574b1a4`, snapshot `9ffb772b65cd`.
- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualification-route-test.py](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualification-route-test.py) — modified; before `35eea9b31a21`, snapshot `d6e70fe36e66`.
- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualify-local-public-images.sh](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/qualify-local-public-images.sh) — modified; before `6cda71f47c13`, snapshot `764e7f0cfa9f`.
- [ ] [scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh) — modified; before `78e99448743d`, snapshot `b547af68c16e`.

## L104 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody

[Open folder lesson](lessons/104-targets-kanbien-core-platform-core-server-package-custody.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py) — modified; before `de4a6f390812`, snapshot `d15a585d8bdf`.

## L105 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access

[Open folder lesson](lessons/105-kanbien-core-platform-core-server-package-custody-validate-delivery-access.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access/script.sh) — modified; before `621a4c5b6a39`, snapshot `48f309e76ee4`.

## L106 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody

[Open folder lesson](lessons/106-targets-kanbien-core-platform-core-server-persistence-observability-collector-package-custody.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh) — modified; before `ce70744ae438`, snapshot `4b634b97ad6e`.
- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/verify-workflow.py](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/verify-workflow.py) — modified; before `355b9d29e535`, snapshot `7e46e93d3ff8`.

## L107 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody

[Open folder lesson](lessons/107-targets-kanbien-core-platform-core-server-persistence-package-custody.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/verify-workflow.py](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/verify-workflow.py) — modified; before `7c076014e579`, snapshot `932ce40af282`.

## L108 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access

[Open folder lesson](lessons/108-kanbien-core-platform-core-server-persistence-package-custody-validate-delivery-access.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access/script.sh](../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access/script.sh) — modified; before `71875b28fc07`, snapshot `eb5774b07c71`.

## L109 — scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract

[Open folder lesson](lessons/109-lifecycle-40-package-validate-delivery-access-contract.md)

- [ ] [scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.py](../../../../scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.py) — modified; before `9cfc1f2beb34`, snapshot `f986d5c5918a`.
- [ ] [scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/smoke-test.sh) — modified; before `97ed21220dc8`, snapshot `2eb2fe1d4f87`.

## L110 — scripts/04.deploy/smoke-test-platform-shell-image

[Open folder lesson](lessons/110-scripts-04-deploy-smoke-test-platform-shell-image.md)

- [ ] [scripts/04.deploy/smoke-test-platform-shell-image/script.sh](../../../../scripts/04.deploy/smoke-test-platform-shell-image/script.sh) — modified; before `837084685a44`, snapshot `366f2039666a`.

## L111 — scripts/04.deploy/validate-container-boundaries

[Open folder lesson](lessons/111-scripts-04-deploy-validate-container-boundaries.md)

- [ ] [scripts/04.deploy/validate-container-boundaries/script.sh](../../../../scripts/04.deploy/validate-container-boundaries/script.sh) — modified; before `90ccf9cd6789`, snapshot `92f385cac53e`.
- [ ] [scripts/04.deploy/validate-container-boundaries/smoke-test.sh](../../../../scripts/04.deploy/validate-container-boundaries/smoke-test.sh) — modified; before `d1cc7229f32c`, snapshot `4dcdeab6e5e3`.

## L112 — scripts/04.deploy/inventory-deploy-control

[Open folder lesson](lessons/112-scripts-04-deploy-inventory-deploy-control.md)

- [ ] [scripts/04.deploy/inventory-deploy-control/README.md](../../../../scripts/04.deploy/inventory-deploy-control/README.md) — modified; before `2c855f3fb024`, snapshot `cd69b0dabd11`.
- [ ] [scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py](../../../../scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py) — modified; before `6d3e65d47bfa`, snapshot `9c060a8cc6b5`.
- [ ] [scripts/04.deploy/inventory-deploy-control/delivery_inventory.py](../../../../scripts/04.deploy/inventory-deploy-control/delivery_inventory.py) — modified; before `470ec9f0a1ae`, snapshot `aaca02f68213`.
- [ ] [scripts/04.deploy/inventory-deploy-control/smoke-test.sh](../../../../scripts/04.deploy/inventory-deploy-control/smoke-test.sh) — modified; before `f2807329479f`, snapshot `747301b85604`.

## L113 — scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration

[Open folder lesson](lessons/113-lifecycle-00-target-alignment-core-platform-target-declaration.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py) — modified; before `7361d7efabdc`, snapshot `bdcf1ac4092f`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/smoke-test.sh) — modified; before `4ac582d00606`, snapshot `8412de03ccdb`.

## L114 — scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage

[Open folder lesson](lessons/114-lifecycle-00-target-alignment-declaration-coverage.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py) — modified; before `4a367df94612`, snapshot `796d1d155214`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py) — modified; before `ca4163507473`, snapshot `fac762e656f6`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py) — modified; before `8ed8641f1755`, snapshot `666cd462eb80`.

## L115 — scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecr-read-access

[Open folder lesson](lessons/115-provider-adapters-aws-ecr-read-access.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecr-read-access/script.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecr-read-access/script.sh) — modified; before `223587001796`, snapshot `29e2f5e89682`.

## L116 — scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment

[Open folder lesson](lessons/116-provider-adapters-aws-runtime-alignment.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py) — modified; before `37839e7b4faf`, snapshot `1a210b0509a4`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/smoke-test.sh) — modified; before `b6e83cee29df`, snapshot `5ccab4bb90da`.

## L117 — scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/inspect-runtime-alignment

[Open folder lesson](lessons/117-targets-kanbien-core-platform-inspect-runtime-alignment.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/inspect-runtime-alignment/script.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/inspect-runtime-alignment/script.sh) — modified; before `3147eaa35aa6`, snapshot `afdfe0b05b59`.

## L118 — scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access

[Open folder lesson](lessons/118-targets-kanbien-core-platform-verify-delivery-role-access.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access/smoke-test.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access/smoke-test.py) — added; before `absent`, snapshot `4e172f0bc01f`.

## L119 — scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement

[Open folder lesson](lessons/119-lifecycle-00-target-alignment-validate-artifact-placement.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py) — modified; before `c634fffd4aca`, snapshot `b8bc65505b9f`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/smoke-test.sh) — modified; before `81489b5b4cd0`, snapshot `13bfd7b654dc`.

## L120 — scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration

[Open folder lesson](lessons/120-lifecycle-00-target-alignment-validate-observability-mvp-declaration.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.py) — modified; before `71a84cc5135e`, snapshot `78257701427e`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/smoke-test.sh) — modified; before `b129565589f0`, snapshot `538dff849e07`.

## L121 — scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence

[Open folder lesson](lessons/121-lifecycle-00-target-alignment-validate-provider-condition-evidence.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.py) — modified; before `3ebb1c703363`, snapshot `0bb847039dee`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/smoke-test.sh) — modified; before `bf974725bcd0`, snapshot `d8053fd25ea2`.

## L122 — scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration

[Open folder lesson](lessons/122-lifecycle-00-target-alignment-validate-secret-dependency-declaration.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.py) — modified; before `f4c7d98d6aaa`, snapshot `9bedac569719`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/smoke-test.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/smoke-test.py) — modified; before `c323b2e8fb33`, snapshot `b350ded23a3b`.

## L123 — scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment

[Open folder lesson](lessons/123-lifecycle-00-target-alignment-validate-target-alignment.md)

- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.py](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.py) — modified; before `9857fd32fab5`, snapshot `d353d61e094e`.
- [ ] [scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/smoke-test.sh) — modified; before `3f991db29461`, snapshot `f8929713823a`.

## L124 — .agentic/04.deploy/60-run/schemas

[Open folder lesson](lessons/124-04-deploy-60-run-schemas.md)

- [ ] [.agentic/04.deploy/60-run/schemas/persistence-diagnostic-mapping.v1.schema.yml](../../../../.agentic/04.deploy/60-run/schemas/persistence-diagnostic-mapping.v1.schema.yml) — modified; before `7b861a2c4b14`, snapshot `629ed5ecae49`.

## L125 — .agentic/04.deploy/60-run/standards

[Open folder lesson](lessons/125-04-deploy-60-run-standards.md)

- [ ] [.agentic/04.deploy/60-run/standards/require-persistence-diagnostic-mapping.md](../../../../.agentic/04.deploy/60-run/standards/require-persistence-diagnostic-mapping.md) — modified; before `1923d872a0be`, snapshot `7a0fa0194f8c`.

## L126 — .agentic/04.deploy/schemas

[Open folder lesson](lessons/126--agentic-04-deploy-schemas.md)

- [ ] [.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.guide.md](../../../../.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.guide.md) — modified; before `07db56105c60`, snapshot `7d001a458836`.
- [ ] [.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml](../../../../.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml) — modified; before `d6acea39517e`, snapshot `3886a64cf82a`.

## L127 — scripts/04.deploy

[Open folder lesson](lessons/127-scripts-04-deploy.md)

- [ ] [scripts/04.deploy/README.md](../../../../scripts/04.deploy/README.md) — modified; before `ff4b799fd42f`, snapshot `d33e3762816b`.

## L128 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime

[Open folder lesson](lessons/128-targets-kanbien-core-platform-bootstrap-runtime.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deployment-cli-regression.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deployment-cli-regression.py) — modified; before `a7f21fb8ccc7`, snapshot `7dbdb7e8f814`.
- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh) — modified; before `ac0de46a92eb`, snapshot `01abf2a37169`.

## L129 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set

[Open folder lesson](lessons/129-kanbien-core-platform-bootstrap-runtime-create-change-set.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.py) — modified; before `d2265454af04`, snapshot `1127701b3da2`.

## L130 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate

[Open folder lesson](lessons/130-kanbien-core-platform-bootstrap-runtime-deploy-candidate.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py) — modified; before `ad34756a4332`, snapshot `8bff7332e10f`.

## L131 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence

[Open folder lesson](lessons/131-targets-kanbien-core-platform-core-server-persistence.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py) — modified; before `f4d07a55c8b8`, snapshot `eeaee2fa43bb`.
- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh) — modified; before `6db83e1e635a`, snapshot `7d17abb0efff`.

## L132 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface

[Open folder lesson](lessons/132-kanbien-core-platform-core-server-persistence-apply-restoration-verifier-surface.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py) — modified; before `63d78a93ea74`, snapshot `62e8f3fbfaff`.

## L133 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set

[Open folder lesson](lessons/133-kanbien-core-platform-core-server-persistence-create-change-set.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py) — modified; before `82e4a016d68c`, snapshot `380fa7e4189a`.

## L134 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate

[Open folder lesson](lessons/134-kanbien-core-platform-core-server-persistence-deploy-candidate.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.py) — modified; before `6eaec1796902`, snapshot `19e293585666`.

## L135 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate

[Open folder lesson](lessons/135-kanbien-core-platform-core-server-persistence-prepare-candidate.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py) — modified; before `a451b4fd0bed`, snapshot `d72562d05297`.

## L136 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface

[Open folder lesson](lessons/136-kanbien-core-platform-core-server-persistence-reconcile-rds-log-export-surface.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface/script.py) — modified; before `8076f9d4214e`, snapshot `3bd516584519`.

## L137 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate

[Open folder lesson](lessons/137-kanbien-core-platform-core-server-persistence-retire-failed-candidate.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.py) — modified; before `a2630fc71aee`, snapshot `11309d992a55`.

## L138 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget

[Open folder lesson](lessons/138-kanbien-core-platform-foundation-provision-target-budget.md)

- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py) — modified; before `47b2e7f0a82e`, snapshot `ba0ad7978ea3`.
- [ ] [scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/smoke-test.sh) — modified; before `536629f80a36`, snapshot `a5354e3bf6ee`.

## L139 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement

[Open folder lesson](lessons/139-kanbien-core-platform-bootstrap-runtime-rehearse-accepted-workload-replacement.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.py) — modified; before `e00bbb09f1d2`, snapshot `04f6b51e4b05`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/smoke-test.sh) — modified; before `376f23cdb54c`, snapshot `0363dc17b9f0`.

## L140 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault

[Open folder lesson](lessons/140-kanbien-core-platform-bootstrap-runtime-rehearse-private-verifier-fault.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.py) — modified; before `ff74961452b4`, snapshot `5265e2898c35`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/smoke-test.sh](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/smoke-test.sh) — modified; before `a439dee1f2d5`, snapshot `30156aacc204`.

## L141 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence

[Open folder lesson](lessons/141-targets-kanbien-core-platform-core-server-persistence.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts-smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts-smoke-test.py) — modified; before `e45920544aa9`, snapshot `2d5efb1faf34`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py) — modified; before `75fab145c836`, snapshot `6726d526d375`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts-smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts-smoke-test.py) — modified; before `b5245cd69cb6`, snapshot `105a82dc46ef`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py) — modified; before `3558d0650671`, snapshot `95c479947e44`.

## L142 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal

[Open folder lesson](lessons/142-kanbien-core-platform-core-server-persistence-acceptance-route-rehearsal.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.py) — modified; before `7f84531ea475`, snapshot `9bc7a4a679bb`.

## L143 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence

[Open folder lesson](lessons/143-kanbien-core-platform-core-server-persistence-collect-acceptance-evidence.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/current-observations-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/current-observations-test.py) — modified; before `bf28e98e8c9c`, snapshot `98a4cdd208fe`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py) — modified; before `8c67fada10f2`, snapshot `1971a9a6b5af`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/smoke-test.py) — modified; before `4e40e2f57454`, snapshot `33da429b1c80`.

## L144 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore

[Open folder lesson](lessons/144-kanbien-core-platform-core-server-persistence-rehearse-isolated-database-restore.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/diagnostic-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/diagnostic-test.py) — modified; before `cd430f19bb54`, snapshot `ab727cb20604`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.py) — modified; before `5150852bd249`, snapshot `75d636a4ba77`.

## L145 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness

[Open folder lesson](lessons/145-kanbien-core-platform-core-server-persistence-rehearse-observability-readiness.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.py) — modified; before `4c08164ab266`, snapshot `b7e5ea37058c`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/smoke-test.py) — modified; before `c915fd43b524`, snapshot `391090307517`.

## L146 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle

[Open folder lesson](lessons/146-kanbien-core-platform-core-server-persistence-rehearse-runtime-credential-lifecycle.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.py) — modified; before `9f3d5f39493b`, snapshot `b49ff513c9bd`.

## L147 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement

[Open folder lesson](lessons/147-kanbien-core-platform-core-server-persistence-rehearse-server-replacement.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.py) — modified; before `66383ce746a7`, snapshot `c8c78ec169ae`.

## L148 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration

[Open folder lesson](lessons/148-kanbien-core-platform-core-server-persistence-run-administration.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.py) — modified; before `e9e357949ffe`, snapshot `f4ac6033ee28`.

## L149 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration

[Open folder lesson](lessons/149-kanbien-core-platform-core-server-persistence-run-migration.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.py) — modified; before `f895a34794f0`, snapshot `0d198e1a0922`.

## L150 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate

[Open folder lesson](lessons/150-kanbien-core-platform-core-server-persistence-verify-candidate.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/operation-test.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/operation-test.py) — modified; before `3cc5ffeb4349`, snapshot `d5935723bc26`.
- [ ] [scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py) — modified; before `3f7aeb9c7cbb`, snapshot `d4811bc006e4`.

## L151 — scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping

[Open folder lesson](lessons/151-lifecycle-60-run-validate-persistence-diagnostic-mapping.md)

- [ ] [scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.py](../../../../scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.py) — modified; before `8ab72f0083a6`, snapshot `395c2c340520`.
- [ ] [scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.py](../../../../scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.py) — modified; before `f64b03d9a834`, snapshot `7c14207823a5`.

## L152 — scripts/04.deploy/reconcile-platform-shell-staging

[Open folder lesson](lessons/152-scripts-04-deploy-reconcile-platform-shell-staging.md)

- [ ] [scripts/04.deploy/reconcile-platform-shell-staging/release-control-test.py](../../../../scripts/04.deploy/reconcile-platform-shell-staging/release-control-test.py) — modified; before `502bfe852583`, snapshot `694cc007e3ca`.
- [ ] [scripts/04.deploy/reconcile-platform-shell-staging/release_control.py](../../../../scripts/04.deploy/reconcile-platform-shell-staging/release_control.py) — modified; before `57d70bd61b79`, snapshot `f6dbe6cef117`.
- [ ] [scripts/04.deploy/reconcile-platform-shell-staging/script.py](../../../../scripts/04.deploy/reconcile-platform-shell-staging/script.py) — modified; before `0d9e2ef0b8df`, snapshot `207dfbff64fd`.

## L153 — scripts/04.deploy/shared

[Open folder lesson](lessons/153-scripts-04-deploy-shared.md)

- [ ] [scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py](../../../../scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py) — modified; before `b125972ccddf`, snapshot `abc1f56f0102`.
- [ ] [scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh](../../../../scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh) — modified; before `4a7411d63871`, snapshot `526f5829ecef`.
- [ ] [scripts/04.deploy/shared/deployment-operation-diagnostics.py](../../../../scripts/04.deploy/shared/deployment-operation-diagnostics.py) — modified; before `e3bb62c2d8d0`, snapshot `1f8df4d2695b`.
- [ ] [scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh](../../../../scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh) — modified; before `22b6972b7fa3`, snapshot `fb8e6a03a1f8`.
- [ ] [scripts/04.deploy/shared/safe-command-diagnostics.sh](../../../../scripts/04.deploy/shared/safe-command-diagnostics.sh) — modified; before `e071dd8db44e`, snapshot `3eb4218560e1`.

## L154 — scripts/04.deploy/shared/provider-adapters/docker

[Open folder lesson](lessons/154-shared-provider-adapters-docker.md)

- [ ] [scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup-test.py](../../../../scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup-test.py) — modified; before `3f2b0873652a`, snapshot `11c262c1dea8`.
- [ ] [scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py](../../../../scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py) — modified; before `801e705e3fe2`, snapshot `d8bb8a64d8b2`.

## L155 — scripts/04.deploy/verify-platform-shell-deploy-readiness

[Open folder lesson](lessons/155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md)

- [ ] [scripts/04.deploy/verify-platform-shell-deploy-readiness/release-evidence-test.py](../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/release-evidence-test.py) — modified; before `31fe45f93ebd`, snapshot `ea439bd88ba9`.
- [ ] [scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py](../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py) — modified; before `a452262e49cf`, snapshot `069128169b96`.
- [ ] [scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh](../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh) — modified; before `f2f11698dc50`, snapshot `9c0fc6daa806`.

## L156 — .

[Open folder lesson](lessons/156-repository-root.md)

- [ ] [AGENTS.md](../../../../AGENTS.md) — modified; before `b501345e152f`, snapshot `011224843510`.
- [ ] [package-lock.json](../../../../package-lock.json) — modified; before `f04ecd0bd319`, snapshot `7f5d040377f2`.

## L157 — .agentic/01.harness/workflows

[Open folder lesson](lessons/157--agentic-01-harness-workflows.md)

- [ ] [.agentic/01.harness/workflows/change-harness.md](../../../../.agentic/01.harness/workflows/change-harness.md) — modified; before `c094da83f36b`, snapshot `fec0cc4773e8`.

## L158 — .agentic/03.product

[Open folder lesson](lessons/158--agentic-03-product.md)

- [ ] [.agentic/03.product/README.md](../../../../.agentic/03.product/README.md) — modified; before `d15484d85522`, snapshot `cdafda8d29e1`.

## L159 — .agentic/03.product/workflows

[Open folder lesson](lessons/159--agentic-03-product-workflows.md)

- [ ] [.agentic/03.product/workflows/platform-runtime-implementation.md](../../../../.agentic/03.product/workflows/platform-runtime-implementation.md) — modified; before `a9758b740adc`, snapshot `d56b0a560a13`.

## L160 — .agentic/shared/standards

[Open folder lesson](lessons/160--agentic-shared-standards.md)

- [ ] [.agentic/shared/standards/require-change-completion.md](../../../../.agentic/shared/standards/require-change-completion.md) — modified; before `0219d93cea7c`, snapshot `5054c0a1de1f`.
- [ ] [.agentic/shared/standards/require-safe-diagnostic-record.md](../../../../.agentic/shared/standards/require-safe-diagnostic-record.md) — modified; before `751396ce7299`, snapshot `f251f21908ad`.

## L161 — .agentic/shared/workflows

[Open folder lesson](lessons/161--agentic-shared-workflows.md)

- [ ] [.agentic/shared/workflows/README.md](../../../../.agentic/shared/workflows/README.md) — modified; before `8899e6f2ef59`, snapshot `2ab354b3ab06`.
- [ ] [.agentic/shared/workflows/verify-diagnostic-coverage.md](../../../../.agentic/shared/workflows/verify-diagnostic-coverage.md) — added; before `absent`, snapshot `f9f253d94a2a`.

## L162 — .github/workflows

[Open folder lesson](lessons/162--github-workflows.md)

- [ ] [.github/workflows/deploy-platform-shell-staging.yml](../../../../.github/workflows/deploy-platform-shell-staging.yml) — modified; before `82c6743ea8d0`, snapshot `f8f0e7d0220e`.

## L163 — docs/03.product/rules/core/concerns

[Open folder lesson](lessons/163-rules-core-concerns.md)

- [ ] [docs/03.product/rules/core/concerns/validation-api-errors.yml](../../../03.product/rules/core/concerns/validation-api-errors.yml) — modified; before `0d8bb6aa229b`, snapshot `a9e10d2633d2`.

## L164 — docs/03.product/rules/core/layers

[Open folder lesson](lessons/164-rules-core-layers.md)

- [ ] [docs/03.product/rules/core/layers/packages-core.yml](../../../03.product/rules/core/layers/packages-core.yml) — modified; before `90b947c93c35`, snapshot `b71d28fe0a85`.

## L165 — docs/03.product/rules/platform/concerns

[Open folder lesson](lessons/165-rules-platform-concerns.md)

- [ ] [docs/03.product/rules/platform/concerns/config-runtime-settings.yml](../../../../.agentic/03.product/standards/config-runtime-settings.md) — current standard; original file snapshot modified; before `ef8dad5efaef`, snapshot `f7a6e1d68db3`.

## L166 — docs/03.product/rules/platform/layers

[Open folder lesson](lessons/166-rules-platform-layers.md)

- [ ] [docs/03.product/rules/platform/layers/platform.yml](../../../03.product/rules/platform/layers/platform.yml) — modified; before `86a9b46e542b`, snapshot `fb17a8262de3`.

## L167 — scripts/repo/diagnostic-coverage

[Open folder lesson](lessons/167-scripts-repo-diagnostic-coverage.md)

- [ ] [scripts/repo/diagnostic-coverage/README.md](../../../../scripts/repo/diagnostic-coverage/README.md) — added; before `absent`, snapshot `42987320686d`.
- [ ] [scripts/repo/diagnostic-coverage/compatibility.mjs](../../../../scripts/repo/diagnostic-coverage/compatibility.mjs) — added; before `absent`, snapshot `6c6f122d44c8`.
- [ ] [scripts/repo/diagnostic-coverage/export-catalogs.mjs](../../../../scripts/repo/diagnostic-coverage/export-catalogs.mjs) — added; before `absent`, snapshot `2185b24cc727`.
- [ ] [scripts/repo/diagnostic-coverage/reviews.v1.json](../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) — added; before `absent`, snapshot `96de849ef347`.
- [ ] [scripts/repo/diagnostic-coverage/runtime_contract.py](../../../../scripts/repo/diagnostic-coverage/runtime_contract.py) — added; before `absent`, snapshot `988a78b07cc3`.
- [ ] [scripts/repo/diagnostic-coverage/script.py](../../../../scripts/repo/diagnostic-coverage/script.py) — added; before `absent`, snapshot `c1ba759cb167`.
- [ ] [scripts/repo/diagnostic-coverage/script.sh](../../../../scripts/repo/diagnostic-coverage/script.sh) — added; before `absent`, snapshot `e4236904073e`.
- [ ] [scripts/repo/diagnostic-coverage/smoke-test.py](../../../../scripts/repo/diagnostic-coverage/smoke-test.py) — added; before `absent`, snapshot `b45bebf78761`.
- [ ] [scripts/repo/diagnostic-coverage/tsconfig.json](../../../../scripts/repo/diagnostic-coverage/tsconfig.json) — added; before `absent`, snapshot `af453384cf12`.
- [ ] [scripts/repo/diagnostic-coverage/verify.sh](../../../../scripts/repo/diagnostic-coverage/verify.sh) — added; before `absent`, snapshot `575c6dc698fe`.

## L168 — scripts/04.deploy/verify-platform-shell-deployment-workflow

[Open folder lesson](lessons/168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md)

- [ ] [scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh](../../../../scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh) — modified; before `671796a7bc0e`, snapshot `c5efa01284a7`.

## L169 — scripts/04.deploy/verify-platform-shell-infrastructure

[Open folder lesson](lessons/169-scripts-04-deploy-verify-platform-shell-infrastructure.md)

- [ ] [scripts/04.deploy/verify-platform-shell-infrastructure/policy.sh](../../../../scripts/04.deploy/verify-platform-shell-infrastructure/policy.sh) — added; before `absent`, snapshot `7eb05f6474dc`.
- [ ] [scripts/04.deploy/verify-platform-shell-infrastructure/script.sh](../../../../scripts/04.deploy/verify-platform-shell-infrastructure/script.sh) — modified; before `b4c33c039aad`, snapshot `1938d4044951`.

## L170 — scripts/repo/check-selection

[Open folder lesson](lessons/170-scripts-repo-check-selection.md)

- [ ] [scripts/repo/check-selection/README.md](../../../../scripts/repo/check-selection/README.md) — modified; before `f2d56a3220c0`, snapshot `651679fde3a2`.
- [ ] [scripts/repo/check-selection/checks.yml](../../../../scripts/repo/check-selection/checks.yml) — modified; before `35a899d9c4d7`, snapshot `775fe24f6e8f`.
- [ ] [scripts/repo/check-selection/local_cache.py](../../../../scripts/repo/check-selection/local_cache.py) — modified; before `c106163dd9d6`, snapshot `85e3b5e9943c`.
- [ ] [scripts/repo/check-selection/mechanics_test.py](../../../../scripts/repo/check-selection/mechanics_test.py) — added; before `absent`, snapshot `ded337142759`.
- [ ] [scripts/repo/check-selection/repository_contracts_test.py](../../../../scripts/repo/check-selection/repository_contracts_test.py) — added; before `absent`, snapshot `621e4734266d`.
- [ ] [scripts/repo/check-selection/script.py](../../../../scripts/repo/check-selection/script.py) — modified; before `fec7a069b29e`, snapshot `db8bacf3a592`.
- [ ] [scripts/repo/check-selection/smoke-test.py](../../../../scripts/repo/check-selection/smoke-test.py) — modified; before `f9ad8a4116c3`, snapshot `fab4945d0136`.
- [ ] [scripts/repo/check-selection/smoke-test.sh](../../../../scripts/repo/check-selection/smoke-test.sh) — modified; before `ae1354f8ee8d`, snapshot `ec50c4dd1a8f`.
- [ ] [scripts/repo/check-selection/test_support.py](../../../../scripts/repo/check-selection/test_support.py) — added; before `absent`, snapshot `391fd7ce3b0e`.

## L171 — bin

[Open folder lesson](lessons/171-bin.md)

- [ ] [bin/llm-workbench-ownership.js](../../../../bin/llm-workbench-ownership.js) — modified; before `438ac0bd0543`, snapshot `d16272528e38`.
- [ ] [bin/llm-workbench.js](../../../../bin/llm-workbench.js) — modified; before `704235ecc417`, snapshot `352d8cc0579f`.

## L172 — scripts/00.chat/export

[Open folder lesson](lessons/172-scripts-00-chat-export.md)

- [ ] [scripts/00.chat/export/smoke-test.sh](../../../../scripts/00.chat/export/smoke-test.sh) — modified; before `75d6bd3bcefc`, snapshot `f40d3ea910d2`.

## L173 — scripts/00.chat/export/create-worktree-bundle

[Open folder lesson](lessons/173-00-chat-export-create-worktree-bundle.md)

- [ ] [scripts/00.chat/export/create-worktree-bundle/script.js](../../../../scripts/00.chat/export/create-worktree-bundle/script.js) — modified; before `4c212a57b295`, snapshot `bf7d74614157`.

## L174 — scripts/00.chat/metrics/estimate-chat-cost

[Open folder lesson](lessons/174-00-chat-metrics-estimate-chat-cost.md)

- [ ] [scripts/00.chat/metrics/estimate-chat-cost/script.js](../../../../scripts/00.chat/metrics/estimate-chat-cost/script.js) — modified; before `9dd2b27de8e7`, snapshot `2dc02eaa6188`.

## L175 — scripts/00.chat/session-log/record-chat-commit

[Open folder lesson](lessons/175-00-chat-session-log-record-chat-commit.md)

- [ ] [scripts/00.chat/session-log/record-chat-commit/smoke-test.sh](../../../../scripts/00.chat/session-log/record-chat-commit/smoke-test.sh) — modified; before `54987f402b67`, snapshot `40092389fbe4`.

## L176 — scripts/01.harness

[Open folder lesson](lessons/176-scripts-01-harness.md)

- [ ] [scripts/01.harness/check-artifact-path-migration.sh](../../../../scripts/01.harness/check-artifact-path-migration.sh) — modified; before `11055e5e9715`, snapshot `e2f9362befd8`.
- [ ] [scripts/01.harness/plan-artifact-path-migration.sh](../../../../scripts/01.harness/plan-artifact-path-migration.sh) — modified; before `cd126929d86a`, snapshot `80fef3bd513a`.
- [ ] [scripts/01.harness/smoke-test-artifact-path-migration.sh](../../../../scripts/01.harness/smoke-test-artifact-path-migration.sh) — modified; before `99838526820c`, snapshot `f93a5142947b`.

## L177 — scripts/01.harness/agents/validate-harness-agents

[Open folder lesson](lessons/177-01-harness-agents-validate-harness-agents.md)

- [ ] [scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js](../../../../scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js) — added; before `absent`, snapshot `e043b1cff7c5`.
- [ ] [scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh](../../../../scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh) — added; before `absent`, snapshot `7f2774b941b3`.
- [ ] [scripts/01.harness/agents/validate-harness-agents/script.js](../../../../scripts/01.harness/agents/validate-harness-agents/script.js) — modified; before `bc055247eba8`, snapshot `89ad78f572b3`.

## L178 — scripts/01.harness/artifact-metadata

[Open folder lesson](lessons/178-scripts-01-harness-artifact-metadata.md)

- [ ] [scripts/01.harness/artifact-metadata/header_discovery.py](../../../../scripts/01.harness/artifact-metadata/header_discovery.py) — modified; before `7746893ec239`, snapshot `d3c1e3ddb34c`.

## L179 — scripts/01.harness/artifact-metadata/backfill-v2-headers

[Open folder lesson](lessons/179-01-harness-artifact-metadata-backfill-v2-headers.md)

- [ ] [scripts/01.harness/artifact-metadata/backfill-v2-headers/diagnostic-test.py](../../../../scripts/01.harness/artifact-metadata/backfill-v2-headers/diagnostic-test.py) — added; before `absent`, snapshot `363327af5edd`.
- [ ] [scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh](../../../../scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh) — modified; before `dd3e6ad8b33d`, snapshot `a2fe9c24021e`.

## L180 — scripts/01.harness/artifact-metadata/generate-index

[Open folder lesson](lessons/180-01-harness-artifact-metadata-generate-index.md)

- [ ] [scripts/01.harness/artifact-metadata/generate-index/script.sh](../../../../scripts/01.harness/artifact-metadata/generate-index/script.sh) — modified; before `b193d8703483`, snapshot `ebba2c19dff6`.
- [ ] [scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh](../../../../scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh) — modified; before `f3b95327f19f`, snapshot `12fc01ed4789`.

## L181 — scripts/01.harness/artifact-metadata/update-lifecycle

[Open folder lesson](lessons/181-01-harness-artifact-metadata-update-lifecycle.md)

- [ ] [scripts/01.harness/artifact-metadata/update-lifecycle/script.sh](../../../../scripts/01.harness/artifact-metadata/update-lifecycle/script.sh) — modified; before `57aa491d2633`, snapshot `c66d3f29558b`.
- [ ] [scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh](../../../../scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh) — modified; before `f838062ebe95`, snapshot `fdb099a9b340`.

## L182 — scripts/01.harness/metrics/compare-task-token-consumption

[Open folder lesson](lessons/182-01-harness-metrics-compare-task-token-consumption.md)

- [ ] [scripts/01.harness/metrics/compare-task-token-consumption/script.js](../../../../scripts/01.harness/metrics/compare-task-token-consumption/script.js) — modified; before `0863867f40be`, snapshot `859daf2e0e45`.

## L183 — .agentic/03.product/plans/implementation

[Open folder lesson](lessons/183-03-product-plans-implementation.md)

- [ ] [.agentic/03.product/plans/implementation/security-capabilities-follow-on.md](../../../../.agentic/03.product/plans/implementation/security-capabilities-follow-on.md) — added; before `absent`, snapshot `7a5ea10acc0c`.
- [ ] [.agentic/03.product/plans/implementation/telemetry-implementation-follow-on.md](../../../../.agentic/03.product/plans/implementation/telemetry-implementation-follow-on.md) — added; before `absent`, snapshot `fa12595fde34`.

## L184 — .agentic/shared/plans/implementation

[Open folder lesson](lessons/184-shared-plans-implementation.md)

- [ ] [.agentic/shared/plans/implementation/governed-diagnostic-coverage.md](../../../../.agentic/shared/plans/implementation/governed-diagnostic-coverage.md) — added; before `absent`, snapshot `d223bd07603b`.

## L185 — commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage

[Open folder lesson](lessons/185-oct-27-2026-10-27-08-24-governed-diagnostic-coverage.md)

- [ ] [commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md) — added; before `absent`, snapshot `7ce5cac56ae3`.

## L186 — commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909

[Open folder lesson](lessons/186-27-2026-10-27-08-24-governed-diagnostic-coverage-local-artifact-qualification-20261028-163909.md)

- [ ] [commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/core-image.json](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/core-image.json) — added; before `absent`, snapshot `e232eeacb7c6`.
- [ ] [commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/persistence-image.json](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/persistence-image.json) — added; before `absent`, snapshot `7efec7e70115`.
- [ ] [commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/shell-image.json](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/shell-image.json) — added; before `absent`, snapshot `c4fbeddc3ee4`.

## L187 — docs/03.product/adrs

[Open folder lesson](lessons/187-docs-03-product-adrs.md)

- [ ] [docs/03.product/adrs/0043-own-diagnostic-contracts-in-runtime-code.md](../../../03.product/adrs/0043-own-diagnostic-contracts-in-runtime-code.md) — added; before `absent`, snapshot `7eea7a1f77a7`.
- [ ] [docs/03.product/adrs/README.md](../../../03.product/adrs/README.md) — modified; before `4a1c3b56fc01`, snapshot `eae312b0ef52`.

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-source-adoption
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Preserve pending source adoption review work for the bounded independent discovery unit.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.script.operational-realization-source-coverage
  path: scripts/04.deploy/operational-realization-gate/source_coverage.py
-->
# Pending source adoption review

The [2026-09-29 triage and staging caller review](2026-09-29-triage-and-callers/README.md)
preserves this baseline and records a separate current snapshot. This earlier
ledger remains pending and is not current acceptance evidence after source edits.

This is a source migration planning snapshot, not an operational ledger or
proof of estate closure. Every entry in [ledger.json](ledger.json) is pending;
`release-control-programme` is the intake owner until an accountable path owner
reviews it. No path is automatically classified as reviewed or retired. The
contract is `source-adoption-ledger/v1`.

The existing gate's `--discover --source-root .` command produced this snapshot
on 2026-09-28. Its exit status was **1**, as required when discoveries include
unresolved source semantics. The companion `--ledger-template` mode generates
the same pending shape; generation does not satisfy coverage.

- Sources: **273**.
- Observations: **1054**.
- Unresolved source findings: **169**.
- Inventory identity: `sha256:5d65b23fd91153270172bf9ba9ee6ef2a32283eaf67278250f26b6988063203a`.
- Collector revision: `sha256:fba3e024de55ae3cb0040c3fc4d892d19009e6971e93b39570970e7cc577c1e0`.

| Finding | Count |
| --- | ---: |
| `container-command-inherited` | 2 |
| `container-image-unresolved` | 2 |
| `image-command-unsupported` | 2 |
| `image-entrypoint-inherited` | 1 |
| `opaque-executable` | 111 |
| `opaque-export-target` | 20 |
| `opaque-image-build` | 2 |
| `resource-type-unsupported` | 23 |
| `source-alias-unsupported` | 1 |
| `workflow-action-unresolved` | 5 |

These counts are unique source/code findings, not a claim that each source contains
a defect. Many are intentionally opaque scripts or provider grammars. The full
safe inventory was retained at `/tmp/release-control-source-discovery-3owu6lvi/inventory.json`
for this local review; that temporary artifact is not durable programme evidence.
Reproduce it with the existing command instead of depending on that path.

## Next review unit

Expand collector/caller coverage for the observed opaque paths, starting with
package/deploy commands and their production callers. Establish supported source
semantics and explicit profile classification with mutation tests; prove any
retirement or test-only exclusion. Assign reviewed per-path owners/dispositions
only with that evidence. Unsupported resource/image grammar needs independently
tested support; no disposition can suppress its finding.

The ledger binds source bytes, collector revision and complete inventory. Any
source edit makes this snapshot stale. Generate a new pending candidate in a
separate file, compare changes, and review before replacing a reviewed ledger.
Phase 2 stays open until the actual estate reconciles. Later artifact proof may
be implemented once its own source inputs/callers are accounted for; its absent
receipts must not create a circular discovery prerequisite. All required source
and evidence gates still block release eligibility until satisfied. No external
effects are authorized by this document. This dated snapshot remains unchanged;
a later inventory may contain additional implementation sources and findings.

## Path index

The ledger contains each path identity and content digest. This index links its
hashed identities back to safe relative source paths for human review. All
listed dispositions remain `migrate`, review status `pending`.

| Source path | Ledger source ID |
| --- | --- |
| `.github/workflows/deploy-platform-shell-staging.yml` | `sha256:3f05e48f2c4c2526779420e73f006256170a2ad941547b56835dd7d5aa05c966` |
| `.github/workflows/deploy-rag-rulebook-staging.yml` | `sha256:d4781f048ddd3f5c131e665888e3297d3d6b3d5aa5ca3779851bf81a1c92e5eb` |
| `.github/workflows/platform-shell-staging-metric-coverage.yml` | `sha256:c692ee8ee428d711b6c72a8f0e9901ac322a5745cbf68998f30cc1bdacceea99` |
| `.github/workflows/platform-shell-staging-synthetic.yml` | `sha256:92fbfc286b934aee831187a0580b1e6164b306a70cd603519852af7e5f2eaab9` |
| `.github/workflows/reconcile-platform-shell-staging.yml` | `sha256:b85eff166445775ea9d1264bcc7835b69097788af278e81d82a4094d68d2b3f3` |
| `apps/platform-smoke/package.json` | `sha256:38a0e8bbf97631804765d2097240ebba6e79f4dae26a5d38a6a3a7f72c0eb8ac` |
| `apps/platform-smoke/src/index.ts` | `sha256:aa63aa0a004ef0dbf9af6ab6469fb237114b676aa5da9370502223d3ceaa2a10` |
| `infra/04.deploy/02.rag-rulebook/README.md` | `sha256:c7242b8da4da08a0bd1e060bf7e336d5560d0cd8a2d26371283d8ce17e5aa490` |
| `infra/04.deploy/02.rag-rulebook/ecs-fargate/README.md` | `sha256:b0e52d8eac85df28199c7b43f3b630f4fd5651ea8181c345fb01235839fe3e92` |
| `infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/README.md` | `sha256:f2f47abf66af996bc5c191c445cc3695fddae5c95f8e611c4488af3880b8b61b` |
| `infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/foundation.yml` | `sha256:1eed3be0069eac2266368c8ed7fec3af7295d9cfa89dda23414c0a5169ae48b9` |
| `infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/github-oidc-bootstrap.yml` | `sha256:c4c74ae1d70a8488f3becea6126ee1c8dc2fa8e145782cec2032313335d46378` |
| `infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/service.yml` | `sha256:76d2c4ef66c657b8bc277e8c8bf1c49495cef3e7ca8fef8b79de2fb612a90be3` |
| `infra/04.deploy/02.rag-rulebook/environments/staging/deploy-readiness.yml` | `sha256:67e8497342bda3d286cd605cb3dc70a673c19cbd24a42a8b53816332381a5585` |
| `infra/04.deploy/02.rag-rulebook/github-actions/README.md` | `sha256:294b9d548f00a4599efc390fc73900ac6d6181ee3dbcb29fa1a58f6114948f3e` |
| `infra/04.deploy/02.rag-rulebook/image/Dockerfile` | `sha256:31095d6136be60f6577e77a0134c0c6dc941791c5ca0093ebff64aa0acd89b6d` |
| `infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore` | `sha256:131a30cd2c1bd08d4080028bee8857d3a64e93fdb4120383e2e4e3a95517a62b` |
| `infra/04.deploy/02.rag-rulebook/image/README.md` | `sha256:63af4618422f147e464ad0a6749bc0db53798fec01613a11f52cb9971a1fe1f9` |
| `infra/04.deploy/03.product/README.md` | `sha256:8e8260d5435fcab5036347c27adbdfc4fc6e8cd4c31ea0da5d3d60c3a74e7e8c` |
| `infra/04.deploy/03.product/aws-runtime-family.decision.yml` | `sha256:dc487291d1884bf4f1b4756785003fb151143fe3620aac72267386bb9ad0f7df` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts` | `sha256:1e24245d420a4f135da420028b03c89a1b333a4f2a8206fc5f401159a4dbd5b1` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts` | `sha256:c7667ecb73173b5e19f12be5a5d7f8e463501534825026e40f61e0a87727cd67` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts` | `sha256:87e72daaaf63714a69f9414f8fc145d4cd8a2c25000e0ef644295d353fb3934c` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts` | `sha256:1cffafa2e991206e04a2785920161a9b0a04b796bff413d70681a8b6a04432f8` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts` | `sha256:382b4aacca6384a881c112954a95bff9f4d099421d4215ee6385687834753ca7` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-relay.main.ts` | `sha256:74a8c4e8170ad5673b0a03b8cbca8297d779be815fed267b84f52f9d43da87f7` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts` | `sha256:e4d808c051eaed8254bd3539ebaf88bad51413ec3a6392cd0bca5d9b56620be1` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts` | `sha256:dfe6cd4aa7ebc3042068cfc794f88a561be9733664bbdcb15729cc07f4454503` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-worker.main.ts` | `sha256:c49a4956a2a363b7532411815d4f83da3ab72cb1b12562bab176c85ad0500946` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts` | `sha256:1a533cb63648eafb250fa7581a548824ce8e8a32802f19c1cf844c364d77a5e5` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts` | `sha256:7916c3c5b83691d6060a54286607bc12f7216ce3b5963703720f1adffd86e76d` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.ts` | `sha256:db52e96819c5f5355437dafc40ca1d2c3f7a8cc0273660a096bc3e73b5c582ab` |
| `infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts` | `sha256:390e70a9b661e430198844056764efc5eee9428af1b1852b142dc1d4dcd6aa6a` |
| `infra/04.deploy/03.product/image/Dockerfile` | `sha256:b25a61816390089668455327a89d69eb06c13f68a475c58017dac1cfe090972d` |
| `infra/04.deploy/03.product/image/Dockerfile.dockerignore` | `sha256:2d16c2d850740114a3331c52d19f0997f6f2f7d72ff880bd0a081352fedfe3b8` |
| `infra/04.deploy/03.product/image/README.md` | `sha256:32e9a05f17235a45e3b972890d0d75a66f82a896c24cb2aceb60a6c63eb98ed5` |
| `infra/04.deploy/03.product/platform-shell.deploy-blueprint.yml` | `sha256:dfa4a4a6643e2199536ec8d39f1f96969a92a0ca4de498e5ffa221f19d349d6b` |
| `infra/04.deploy/03.product/targets/README.md` | `sha256:ff9499b46bcd7bdc324905e838234172912c6f466ba13f0efc4492ca23155480` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/README.md` | `sha256:1828978b7dbd3867f9cec198b0a987371672e8ed5f4ba8722eb788f20030dea1` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/deployment-artifact-store.yml` | `sha256:c7ffb7d675ae05fbde1963926dc334f36c03a4cff1c6550fed9102f5d61435f0` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation.yml` | `sha256:b9a41b2ebddc90e9b423721497837f011dfbba371b1f9c2289d839c322332fe8` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/README.md` | `sha256:c6a02cc792f0b2888084e94c1c6277bba620b1378354903d188952ceba93533a` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/alerting.yml` | `sha256:e0d10def591ce212a175b634ca888539380e463b41fbe989862885df79faa54a` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/cost-controls.yml` | `sha256:f079513fb4c4b65e3fc5aada994a7ebcc0725f63ab210af27c2b48216dbc2d0f` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/edge-protection.yml` | `sha256:fee9bb8d1c860a155e4b249800145ea9da00abbdcbfc1f98a2a846919a20afad` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/logging.yml` | `sha256:a919db419c85712e62cd0a92aa8c556ef94d8b5a3343d404c82b142e7f9ae054` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/observability-metrics.yml` | `sha256:4596904ae13e6126877b7f5161cdd96b682d24daf5858dd2e35b05c9d5580b22` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/outputs.yml` | `sha256:5b215bfee9fccdad15a5ae3378ef7b2b0f5abe6674867730b3c03e032c184fe7` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/persistence.yml` | `sha256:03bb671c17be754cfecd134ab4333efaf9a1315f49ec259278554d6141dae850` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/public-ingress.yml` | `sha256:a889a41eca68c44fd8ef4cced16ea01397b60b88e603af531009fb75c53cf3b9` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/public-tls.yml` | `sha256:6c9e3f053f04abef9237ec705491b0e72d11d6c9d33647d402e38e01bed2bd52` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/rate-limiting.yml` | `sha256:a5a869aabc52fdb1b18f517d78188701d7d6e6e9bd2aea4728aa875eb613c7fa` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relational-access.yml` | `sha256:c1092a27aef7ddaf4fae4f3ae778cd5908d3cc93c2e3e0956425916308aaf2ba` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relational-operations.yml` | `sha256:3c4a49626d59d077072511eb01fc04ab3168d35be90115f3d9cb56f16d17be0a` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relational-persistence.yml` | `sha256:390fa4cd50c521cb8cf5dea4e8af221bcea6a44e26956fde3710c4747f0e2a47` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relational-work-queue.yml` | `sha256:7dc6b15ae59575941fe48333bafdc01700bf4b5cae498b5cc71710943348ea5e` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relational-workload-configuration.yml` | `sha256:acff194fa2f52a25cae64ef249e45540c55c4238a5832c822931af66d3efcaf8` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/relay-workload-iam.yml` | `sha256:378f08ba525c455da0e49a18a96bd67cc2c777d4009a4f23d029b44c8b1c8442` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/template.yml` | `sha256:224729c9a4c444380d0c122f102c805256f8ededeae5508039f33fe4cb1713e7` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/work-queues.yml` | `sha256:6099eb54d77a8d17d2fa4b299918cd09cd4f1c4e9f0ec8323865096301b40236` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/worker-workload-iam.yml` | `sha256:45842cd31b5fac9902a36fac7dc5d0eaa71e872f98081a9d32079a62b3358996` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/workload-iam.yml` | `sha256:4e68fd5fb08fc38e6e6112468caef0cd473b47bd83d35a8b39f4f53aa0c0c77e` |
| `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml` | `sha256:00762f855f10d786339071154d067c40471048580263e41cb1d77a4ae78498ba` |
| `infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml` | `sha256:f3a10f76e6d05edd87dfbc479d793e38c7704797d26bc7112a7311d99f94d737` |
| `infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/README.md` | `sha256:ad67b1966ec74138057827eab97d315a73eab80e3ab44f88fd546a04dbd7042b` |
| `infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/administrator-active-foundation-assessment-contract.yml` | `sha256:473b91d9ccb6b0a2717987ec133a60a757720b429f8505e42489a37b410bf578` |
| `infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/resource-read-contract.yml` | `sha256:5c0e2ceebb6b92bd4e5dbdcc19da1db855ea29cb1c5a91f75c4bb1a07dfde571` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/README.md` | `sha256:7d1bdc86e0c3b219dfc9c0adaf6b41ed7cd5b2628639a75a69e0b4ba1770f213` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/README.md` | `sha256:3fd3d833ba6346c1cb2fbc632236562542ba5cac1e759f1697bb3f965ca3fbe7` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-deploy-policy.json` | `sha256:7975414d2da8ec7774542cee57de367d5404e9834161bceb20ea27493354c73c` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-deploy-trust.json` | `sha256:5000dcf6472239e30cf78cf45c0798374a85b8b78359d5efbf65e06cea51d5dc` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-metric-coverage-policy.json` | `sha256:1aa9b5daf24b6128ee12eabe62b80c0b380104fcf6ad20741b072d1caf41f1da` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-metric-coverage-trust.json` | `sha256:9126d4f7094713a7881a9b4f5bd2b84be95b5008d9ad1c733d1f1f06bbff6e7f` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json` | `sha256:1eb2e1f257736d101c0827690a262a89bc5042904236cc47cd97271a81f03a32` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json` | `sha256:a7ee8fb8546db86750b960ead1d8a15bf834bca3c6987208ada7de40cd58b686` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-synthetic-policy.json` | `sha256:24f26f6561a0fc4f221071a36fe349244ce8c6e11650cd4542ba36ed8e84569a` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-synthetic-trust.json` | `sha256:ea982df3d8234daf2104ea7f67187e601c8725beff7107fe25f8dbe058d33176` |
| `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/reconciliation-operation-authorization-contract.yml` | `sha256:9913f511be435cf3ef1c2b5715c74e7edc75bde7848161fa3e9ef3372be28e6b` |
| `infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml` | `sha256:c062cbe006a321fcd83a7da35ff7549229412281b0f2972d3b7fb6840d8af9e9` |
| `infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml` | `sha256:26c08ed268e27e01cce303b2fd04b6e666719b43c47074835b59b144bff175cc` |
| `infra/04.deploy/README.md` | `sha256:9510bc89ac6c79587d1b8656043114fe4176ce80ee7166efb6810b3667392d87` |
| `infra/04.deploy/contracts/release-control/v1/README.md` | `sha256:226ac2850ec245d345e5cbb7f833d487cfa9bf118bf3958323cfd05df9c4170d` |
| `infra/04.deploy/contracts/release-control/v1/acceptance-matrix.schema.yml` | `sha256:c7e91005de99bdc24fa3ea35f98cd82d5f8fd7e5e11d9cab664cb7e3d7433a22` |
| `infra/04.deploy/contracts/release-control/v1/release-definition.schema.yml` | `sha256:219cd10f5afc97f8d70b8abb89565b36578182b7e30716403393251ee0594d4f` |
| `infra/04.deploy/contracts/release-control/v1/source-adoption-ledger.schema.yml` | `sha256:804264274f062af8f961c58ab90d7d1d8d5a1abecdd626c8c5b8a19d64425b41` |
| `infra/04.deploy/contracts/release-control/v1/source-composition.schema.yml` | `sha256:11d1217cf29d9f1b3ff7acd2bd240c5b2e80ec6f226e63bd502cbee08b55cba4` |
| `infra/04.deploy/contracts/release-control/v1/source-inventory.schema.yml` | `sha256:7e3fe18e7a43a33d56ca35ed619d9efce698aef5385e8a8c60623e5b2bcfbc6e` |
| `package.json` | `sha256:7ae45ad102eab3b6d7e7896acd08c427a9b25b346470d7bc6507b6481575d519` |
| `packages/core/package.json` | `sha256:0b810c38f3c138a3d5e44854edefd5eb966617ca84e62f06511f60acc40546c7` |
| `packages/core/src/audit/index.ts` | `sha256:087cd09ada4bddb507d08d1cccb7a780d24719e2b4d02be7458835a4781cbe67` |
| `packages/core/src/authn/index.ts` | `sha256:84c2e9e8a3bf25daea23580e54e966af5130dca0470cc38f4f0bd119f020732e` |
| `packages/core/src/authz/index.ts` | `sha256:e6f167a88a9e147aca053c393a2e2a53e35c6977d3ba3dedb06a585e0018d8f2` |
| `packages/core/src/config/index.ts` | `sha256:27b7db7614f866e140ad5f341bc933dc03e4711bd70d1ebccd1ba97276a941d2` |
| `packages/core/src/diagnostics/index.ts` | `sha256:c9e003eb1027387f8565c28ee9518b883f0046ba49fcee909b739485833d2399` |
| `packages/core/src/events/index.ts` | `sha256:03c79f5260456dae9c6e77d46e2f0dac0d91d76277dd5fd247f97bf0e9610776` |
| `packages/core/src/files/index.ts` | `sha256:2e418b3dddb401c8d99c6b321e06b8719274a9946a0fc321733ba99ec278460e` |
| `packages/core/src/i18n/index.ts` | `sha256:d5013f8b3510cb61b899ff9dc39c911e16d066afacb1e12f54fbf762567a71aa` |
| `packages/core/src/index.ts` | `sha256:9a4ceebe7c6f86856371906c3f061d3b56b7457022b05179884a113e7ced67e8` |
| `packages/core/src/localization/index.ts` | `sha256:75a90ddafa7a3782707d97aa5dfaab9a095aeeacac7337eec473de80b7565ec6` |
| `packages/core/src/logging/index.ts` | `sha256:567a4d1f534fb72a11ad27bc05176e77694c2c5a79a6b60208f50985538bc17a` |
| `packages/core/src/monitoring/index.ts` | `sha256:35d86056c28ac48c68bd9b0426a2db71cc751d14d718306794f1d9ee3bc54601` |
| `packages/core/src/persistence/index.ts` | `sha256:caef9db9f66e37a909087ae732b6084afca0cba38bda3268f563615afbbc9839` |
| `packages/core/src/queues/index.ts` | `sha256:775d4520bbaf9fa4ac7a0d3272ba8b8cc868bc77ccbaeca35eb141099fffee16` |
| `packages/core/src/security/index.ts` | `sha256:7569ab92399f4190106560f2d3c08a7593db415f98e23dedbbfb9a14939517c1` |
| `packages/core/src/shared/index.ts` | `sha256:ac007824a2428f7b8a10cd579307f9cb03408fe0f60cc82d3784d06979eb32f2` |
| `packages/core/src/tenancy/index.ts` | `sha256:40d2468cc132088124e04f1737be523148d8c5585c4043c43081951857f2c205` |
| `packages/core/src/validation/index.ts` | `sha256:8a14383158b693fecaa0cf8b69a3069c678200708ce7d900995e4a8afa0b6f32` |
| `platform/adapters/aws/auth/cognito/package.json` | `sha256:a688ffcc467b9f4903a2a9c1196b27008d1a11152fc5f57b10c494ca073c9f30` |
| `platform/adapters/aws/auth/cognito/src/index.ts` | `sha256:0cd27e174ccdec1138aa2bef237e7e341f01a7482fe24192b96e1350cb52ca70` |
| `platform/adapters/aws/observability/cloudwatch/package.json` | `sha256:4d26f14dddc6c6a35e6fa6a60ca4a866347994f71a3488e9dff2ac77f30dba26` |
| `platform/adapters/aws/observability/cloudwatch/src/index.ts` | `sha256:e7b91da96f4d073528197290913c6fbd1681c4d97a9c08db58f76699c8f15fdc` |
| `platform/adapters/aws/persistence/dynamodb/package.json` | `sha256:c4a345edb8100d0161ea0ebdc24ad79dbc2879fed4e74b39dcca3dd7cb33820c` |
| `platform/adapters/aws/persistence/dynamodb/src/index.ts` | `sha256:ab8cd5ca0f8c174aea5300a335fcdeceb82c22cc90f7edb62f476d37c91837f0` |
| `platform/adapters/aws/persistence/postgresql/package.json` | `sha256:78ac78055d8fe395afce0fd87a4d33678b3359458549beda0abacbd21df3f143` |
| `platform/adapters/aws/persistence/postgresql/src/index.ts` | `sha256:f200ae06a6d68e70f9d89c4dbe5ba8f6a9480a023b1bf5f21843ba691823bf04` |
| `platform/adapters/aws/queue/sqs/package.json` | `sha256:b5f22889fb72b9acdb988e45c0ffb76410d83285e6f8c970e21fbd478e1741c2` |
| `platform/adapters/aws/queue/sqs/src/index.ts` | `sha256:92f0ac02ba4d81dc9fd9789fbe71e875d09217e246e8372b2038c1910d248fd4` |
| `platform/adapters/aws/runtime/ecs-fargate/package.json` | `sha256:ac03990910b036878362b68f27465dffc60a49596666055b91e7addfb47c3561` |
| `platform/adapters/aws/runtime/ecs-fargate/src/index.ts` | `sha256:966d5208799ca05c17d94b754bae9c1ed7bc337dc84efcffdf0aa10b02133af3` |
| `platform/adapters/aws/security/dynamodb-rate-limiter/package.json` | `sha256:a657097108c5d2a57645f1c1b1abb9eef15cf1de9ab1b6b37d450cfd90da09c2` |
| `platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts` | `sha256:1459c153672a62754aa8613a9c6097530066581bae7ec02be382c75888176fc2` |
| `platform/config/package.json` | `sha256:199e0e753f98a74871e331158cac63b24db256978ebe78d686e09c4169634d41` |
| `platform/config/src/index.ts` | `sha256:63440a1f5bd6e8a3bd917df9133b977aaf5a1ea51e70388028a6138610c7a479` |
| `platform/contracts/package.json` | `sha256:278f5dc417b8788029f275cdbe0ece39982b6b4a72cae77228dc7e22f35e7306` |
| `platform/contracts/src/index.ts` | `sha256:b6342cedb2fac70212355e9d58e81b95d7b26bc9373131d30a88ba6707cac672` |
| `platform/health/package.json` | `sha256:8e0c29770ac892e44a764f67be34a4f2c755e3c0f884ea82aabd6fb07a74a829` |
| `platform/health/src/index.ts` | `sha256:0053995c4a5e11a2ededebab4aae2a045c33167ae1d1470a742c8f19543d7c5b` |
| `platform/observability/package.json` | `sha256:3ce0b97c2cd0ee9bb36b0fb45f5f2f42b26adc8bcb7e288c5b9dc010f458ebce` |
| `platform/observability/src/index.ts` | `sha256:d7d2af38a4ad388f384c0ee41b1cb90c56f0fe475f743398cfc358980874eb94` |
| `platform/persistence/package.json` | `sha256:36282760504d0ee3c40d6b34ccc1510bdb2454d093e1388761fb0f1082bb4b89` |
| `platform/persistence/src/index.ts` | `sha256:520e4b096b20e89a0388fda176f7fbd6d6caac85054ee9ad4c66fb5acd820ff8` |
| `platform/runtime/package.json` | `sha256:d9512e9e98472f5ac30031363e3c7b88a0fa362ee8402fd641b917bf9b1acbd6` |
| `platform/runtime/src/index.ts` | `sha256:ff34ad8c43a11c03fa5f30d17dbe59fb14e92e1ee2b02cc79bd8ddd18fcc1b20` |
| `platform/security/package.json` | `sha256:4abd8f999861b52624e751ecad112c944334d82f4493646dd84fa2bb3ff43e33` |
| `platform/security/src/index.ts` | `sha256:aa9b82173fe30fa1e5b6c308665dcc60601f4d852bf53fca6f91e138e41aacb9` |
| `platform/server/package.json` | `sha256:b85fd8354c02d843e012f9b39352aaa65266adeffa079da04cc7f0ad06ae7938` |
| `platform/server/src/index.ts` | `sha256:a58570bbefa16b5181acab08843f7395317c077c48443e66b083f82d61d0e4ba` |
| `platform/testing/package.json` | `sha256:13091c1331241b5a7ea33f9034ae8ca1443bc94934e1c00ace43d7510c3e28b3` |
| `platform/testing/src/index.ts` | `sha256:cbb3a7d4d560290f321e502e83bf0ca991871fc4431bfb38dbbedf627e179ccb` |
| `platform/workers/package.json` | `sha256:c9767a20389019c03608e97f5ce1c82660431a9900f982fc5fa3acc0827fb941` |
| `platform/workers/src/index.ts` | `sha256:cdb241624716eb1d142e9d5feb51c673710095d484861546bd1a78a131a34413` |
| `platform/workers/src/main.ts` | `sha256:f3853d6ca0d6e9b60a37ad22c17ed79a45fc602233a60ab9460ceaf0bc409ce7` |
| `products/kanbien-platform/package.json` | `sha256:b33f18ba12aed9147829d4c355b69989d8dcfb571d04e0a3c8f616ee1b08d71e` |
| `products/kanbien-platform/src/index.ts` | `sha256:2407aad8295119e43a116ffff569573e171faad13bbf3e5277f19544392a3c03` |
| `scripts/04.deploy/README.md` | `sha256:23a621b0e4c4eced8c2d73e5dd96310a9a9a635ab67767aa83fd3c1eb0fc84bf` |
| `scripts/04.deploy/assess-platform-shell-artifact-drift/README.md` | `sha256:8b366fa245ce47500fee160236ace9bca97ba22cafe3e63c25fff9bd37d08b0b` |
| `scripts/04.deploy/assess-platform-shell-artifact-drift/script.py` | `sha256:438444c907ac3a6637faa2e5b83d3cd64f0fd8dc935425837b17f8a92b175c54` |
| `scripts/04.deploy/assess-platform-shell-artifact-drift/script.sh` | `sha256:f241a5b9018c225e03bd2b2e559176154ecf541836b50240b8bf751fcfec827d` |
| `scripts/04.deploy/assess-platform-shell-artifact-drift/smoke-test.sh` | `sha256:858cad9e15a3778062549650f9c47144e9ae5abada29100975cd9631a4c61ae4` |
| `scripts/04.deploy/assess-platform-shell-foundation-drift/README.md` | `sha256:d7b684fac041bcac9645d703225598db777caf077eab871e0cfca25504088855` |
| `scripts/04.deploy/assess-platform-shell-foundation-drift/script.py` | `sha256:e44c525eb7f85c0c7123b4b2a185a83394f890d5df55cbfe14f32d5c5af755fc` |
| `scripts/04.deploy/assess-platform-shell-foundation-drift/script.sh` | `sha256:6e27bbf8c886eb0c38b090c978c8735f28c6f47df37886ac6c33abd392d8b9d2` |
| `scripts/04.deploy/assess-platform-shell-foundation-drift/smoke-test.sh` | `sha256:dde4413cbc993fa95497b40bf2bdb9e283e59bd2e3bb0bf4d4fed15b7ffe0ba1` |
| `scripts/04.deploy/assess-platform-shell-service-drift/README.md` | `sha256:e351865b42c482cfec54ae227baa9f08da84081ceef8748c10ce7176483e8690` |
| `scripts/04.deploy/assess-platform-shell-service-drift/script.py` | `sha256:3445966e89eae34f80ea9c815cbbc01db3e2b0c95b99558dc5c0d9c303e7dd34` |
| `scripts/04.deploy/assess-platform-shell-service-drift/script.sh` | `sha256:103b3b3b6a913433e4520bb7da60b34bf44639a8ebdf5ee1f9bc45692a83f334` |
| `scripts/04.deploy/assess-platform-shell-service-drift/smoke-test.sh` | `sha256:13aa2c3d020f0638fa6601ee482dc77759a1d1efc4ac565da61a4ce4ed734dee` |
| `scripts/04.deploy/build-platform-shell-image/README.md` | `sha256:5e5bc6b158e46b5d8b475dfb7c6deaabe5361d1a822903bc61226eef10330310` |
| `scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs` | `sha256:f96f746e3d69e513f4808772eab47499a9553e1062818b2c7c9e718a3e374c80` |
| `scripts/04.deploy/build-platform-shell-image/script.sh` | `sha256:3d30c3ca35b91943a02f7fbfe20ca3b050e27b772f4afb710e243397bd714e90` |
| `scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs` | `sha256:8698280fad345a7615a88b42a9eb31abb26637807bd0fc21b67b7412e9fd9e95` |
| `scripts/04.deploy/operational-realization-gate/README.md` | `sha256:c4389a113c823e25636bc600d864c805861b5e4127749353f6275ff5bf206f51` |
| `scripts/04.deploy/operational-realization-gate/release_compiler.py` | `sha256:f688110fcff42be6711a93f2bafaf2e96aa120f1d23f21dde323c78e34de5cb1` |
| `scripts/04.deploy/operational-realization-gate/requirements.txt` | `sha256:386c866f813b09a30d1401cd334e20c51c8852dcca799d7d0615e9e32b0d9d18` |
| `scripts/04.deploy/operational-realization-gate/script.py` | `sha256:52a0142bc3a4b52bf2f715375dc1bd424a61ca352f5caea92170144b3610b7c6` |
| `scripts/04.deploy/operational-realization-gate/script.sh` | `sha256:54a9513e6cc43f167df70ce3a9165375f5c6297e79caebc57128ee78d3da4e02` |
| `scripts/04.deploy/operational-realization-gate/smoke-test.sh` | `sha256:092b87d198010fe8bcf914e859ebc01ce7514ec2f6a7c1915249793efdde886c` |
| `scripts/04.deploy/operational-realization-gate/source_coverage.py` | `sha256:29feeb32d8bd219f71f2373535f2c59ab14b228f23b022f5f98c2519fe7bd982` |
| `scripts/04.deploy/operational-realization-gate/test_release_compiler.py` | `sha256:470829e9fac720c15b9a3cbae8a8c80319b89b17df57769966ec507c52744293` |
| `scripts/04.deploy/operational-realization-gate/test_source_coverage.py` | `sha256:5d08cb5a04b596c4e890570f1a268f62a1411f1e20e189b0887a49cdfdcc676d` |
| `scripts/04.deploy/provision-platform-shell-negative-authz-client/README.md` | `sha256:b6c4c2202dc4d7260b0266f8fb08395d5dd9d16f0c055dc702c7bde59c93a39b` |
| `scripts/04.deploy/provision-platform-shell-negative-authz-client/script.py` | `sha256:c65eb2ead139b1fc2b4ef20439fcd12a66ee3691ea78c9273d29d9136c3bacdc` |
| `scripts/04.deploy/provision-platform-shell-negative-authz-client/script.sh` | `sha256:19f179bfe32e3a4cf094ca237942276ff0b15079e279e6c63af81d7d53d03de1` |
| `scripts/04.deploy/provision-platform-shell-negative-authz-client/smoke-test.sh` | `sha256:1e01dfbe569ec5b8242c8cd3b43b8a3b5c3bb5503228e72ba58ec782bf81099d` |
| `scripts/04.deploy/provision-platform-shell-persistence-write-client/README.md` | `sha256:a8db942c35d8dc4cceed53418027ee74de2e7759e3fd573e6b2161d56c312826` |
| `scripts/04.deploy/provision-platform-shell-persistence-write-client/script.py` | `sha256:e8a7356d8e2535bf1fbb71344b91a3dcb3af84e26cfb19aaef745743ce5310d3` |
| `scripts/04.deploy/provision-platform-shell-persistence-write-client/script.sh` | `sha256:9f10d71eb1588e0642cf089835ff1be8e76ca4cf7aec4bf1764c45bb99c26470` |
| `scripts/04.deploy/provision-platform-shell-persistence-write-client/smoke-test.sh` | `sha256:93c99731dbca5a2ff80e8760b5278308a27e32fb0aa219a1d0263df7e60779b8` |
| `scripts/04.deploy/reconcile-platform-shell-staging/README.md` | `sha256:b09a920ab8d896b75a29dc60f368b3d726d7506ed1ae6d696f2b36ed8184e455` |
| `scripts/04.deploy/reconcile-platform-shell-staging/script.py` | `sha256:eabeae85ec128e627ece5fe7d11335b899e4135453d2a95199cc9b3770f7cfb0` |
| `scripts/04.deploy/reconcile-platform-shell-staging/script.sh` | `sha256:333ee84a7107a80660832d8d0d605ce6e12667f5e7688acd9ea028ee70ede63c` |
| `scripts/04.deploy/reconcile-platform-shell-staging/smoke-test.sh` | `sha256:70fc088fb53d098f8dbadad56ebddbec36886ab388a4d35a3c041895ea5b50fb` |
| `scripts/04.deploy/release-control/README.md` | `sha256:a4c270f2cae33f5b41ede3ac94ff6a9a840cb8c3897d21a0029c1bd86b7c16d9` |
| `scripts/04.deploy/release-control/compiler.py` | `sha256:b365742bb34218348dca88f5404c09315687bcdf6f6fda902c6395cda802f1a9` |
| `scripts/04.deploy/release-control/discovery/README.md` | `sha256:fad212dac9acfef20d042904c3299851e05cbb41a7092c7d6a3f8d9aa1039c60` |
| `scripts/04.deploy/release-control/discovery/source_inventory.py` | `sha256:33bfa65e7e5879695da6e18e40d82f25c06133a9e21653f2be137e2f7754bade` |
| `scripts/04.deploy/release-control/discovery/test_source_inventory.py` | `sha256:3dc4d1311e1d53f88ec959d247b83411d9369511721d6c11a75f26bd95704df5` |
| `scripts/04.deploy/render-platform-shell-foundation-template/README.md` | `sha256:f62ae8f39ba734f2132421cf7c06922bf0e517c35c635f6d51da4d21228f8d11` |
| `scripts/04.deploy/render-platform-shell-foundation-template/script.sh` | `sha256:514c9c279827abf7be6ca075c8f438bff717069668b70b72d56c9d93f505dcbd` |
| `scripts/04.deploy/run-platform-shell-candidate-execution-preflight/README.md` | `sha256:5ec5ead55eb8fba8663b50f0ee89520c1c6ef56684c1f0f83ffef7f6d309b407` |
| `scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py` | `sha256:61595196531b81e815f25e20c5d516430cbe0040f8836e3459700cc4e9ddcf90` |
| `scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh` | `sha256:7dc254a5bde2573470c39c03829eb80a2cda0fcb2239eefa37e39c41bfb56598` |
| `scripts/04.deploy/run-platform-shell-candidate-execution-preflight/smoke-test.sh` | `sha256:de96dd15bf796db6085543990dddf9e6e54ec5cb1a812c1eb2a591015c608f0a` |
| `scripts/04.deploy/run-platform-shell-controlled-smoke/README.md` | `sha256:dbb48fae991c844c0e72b661f81fcb97d5608182776618cfefec2c9dc2b7e483` |
| `scripts/04.deploy/run-platform-shell-controlled-smoke/script.py` | `sha256:7ed9be065db12a12568fe72f68e13fde1fce32924d0344aa847d0888b3b248c0` |
| `scripts/04.deploy/run-platform-shell-controlled-smoke/script.sh` | `sha256:7dd0cb88c49fb9abb86532449d20bbad5bc0d443e78500a7cc494286307969da` |
| `scripts/04.deploy/run-platform-shell-controlled-smoke/smoke-test.sh` | `sha256:946bdc20dfa67af6a4015c6c92611857c7601c7afa94a13942048ee95dcc3b8c` |
| `scripts/04.deploy/run-platform-shell-ingress-smoke/README.md` | `sha256:18a4282a420405dd161995c29e078579c099b1c0c5bb02db8a8189d9dc15e25f` |
| `scripts/04.deploy/run-platform-shell-ingress-smoke/script.py` | `sha256:a418266886e448e550e8548daba93de2e32aacda7420d9bca7331ca3abcbc71d` |
| `scripts/04.deploy/run-platform-shell-ingress-smoke/script.sh` | `sha256:36f198eaf10b4ae6affb3381b7ec42ec37882bd9ad8752424bb07da50b427b2f` |
| `scripts/04.deploy/run-platform-shell-ingress-smoke/smoke-test.sh` | `sha256:a1749081351333ba4d7d8483c4bae959e4dcacf3f65911efd5c893aa767c319d` |
| `scripts/04.deploy/run-platform-shell-metric-coverage/README.md` | `sha256:57175d46ad2938586ce8a8fa0d1d55585572aad5146bbce3369022b5b94790e0` |
| `scripts/04.deploy/run-platform-shell-metric-coverage/script.py` | `sha256:d730fca466ec3c147406eb4bad802fe60cd78ddf779814e5262b2efea214c410` |
| `scripts/04.deploy/run-platform-shell-metric-coverage/script.sh` | `sha256:94cff67cc8ab741f5dd598fc24a0445da279f145d3c7af51e863bb3b8ec701c3` |
| `scripts/04.deploy/run-platform-shell-metric-coverage/slo-evaluation-test.py` | `sha256:56c4dcd0b083cbc192f846a306a63e8923d2602b4ea66e412327a12035a445ab` |
| `scripts/04.deploy/run-platform-shell-metric-coverage/smoke-test.sh` | `sha256:b67c3b83ba4260a6776d4db5dc29db78e8e3983478be51dfd34dd4ef5a02454a` |
| `scripts/04.deploy/run-platform-shell-negative-authz-smoke/README.md` | `sha256:1c66c368df8a510b8a19121284091af92efc1ff28ccdae1ff65d0e757f8a43e2` |
| `scripts/04.deploy/run-platform-shell-negative-authz-smoke/script.py` | `sha256:7b9af033a8a8a0ebc282bf56ebe77a39fcdb01aac55424288555f2779fe24f81` |
| `scripts/04.deploy/run-platform-shell-negative-authz-smoke/script.sh` | `sha256:5571782ce435bf24cb60209228932bc3dbbbeb2a93dd04f91c10c18c9bfb3c56` |
| `scripts/04.deploy/run-platform-shell-negative-authz-smoke/smoke-test.sh` | `sha256:6c19f7a18b91c98fd4b360deda18bd3896fde92a32b84fb2e6e94246add19177` |
| `scripts/04.deploy/run-platform-shell-persistence-admission-probe/README.md` | `sha256:b23a50e9056706761231730e2f3414d89be35aea8d1281580416c73f289e10eb` |
| `scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py` | `sha256:9b44d854642da7d3ef235b3d44105b51ba818a857ed33a0f26266850e378c145` |
| `scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh` | `sha256:92c9304ad0b999597751fe1298014deff47cf7977613d0e4b203daa8372c545e` |
| `scripts/04.deploy/run-platform-shell-persistence-admission-probe/smoke-test.sh` | `sha256:f3cffaab188f8bc0496723427bce40159aad056e09f8a36f7fa3fb6816afb992` |
| `scripts/04.deploy/run-platform-shell-persistence-delivery-proof/README.md` | `sha256:ebbd6d7f68a744263cdeb077d412bb58564770c23afff8475dc7c5e1ae5b9373` |
| `scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.py` | `sha256:4fa7e2c502084df3a0aaeb8645acce17f9c3ad667a7d3b9990ad6d20b9824633` |
| `scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.sh` | `sha256:cfef54ce89338b54330e420e21fc1eade5df7fd686ccbccab5831b8253a6918a` |
| `scripts/04.deploy/run-platform-shell-persistence-delivery-proof/smoke-test.sh` | `sha256:b9764b5313d9387a8ebbbf53911da419a92d18d914307b8920256ba47bf6a5ce` |
| `scripts/04.deploy/run-platform-shell-persistence-smoke/README.md` | `sha256:941f33da59be7063f0ebf985a0015e4d50e038579aeecd031f3643b049c420c2` |
| `scripts/04.deploy/run-platform-shell-persistence-smoke/script.py` | `sha256:109285874d47c341857e557d14a5483a1159fe34e7ed33c5aa4c2d2da19673af` |
| `scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh` | `sha256:d01a4de51f43cdc7564d70505c0c9e57be550f90fdbfe4d413f8cb6e676cea6f` |
| `scripts/04.deploy/run-platform-shell-persistence-smoke/smoke-test.sh` | `sha256:031a6e00c3ef0e20b800615670c99e172b1dab38c9647531d2ecb100557dd820` |
| `scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md` | `sha256:3f1e52c6d247bc011120fff3763436068654ec3525282aa53694de7403635150` |
| `scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py` | `sha256:1a7683126d3d26d41b924117f056e9c069bd1017dad1320d5dc3e0aabeabffeb` |
| `scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh` | `sha256:b42f699b8146c490a13730c7ab2cb5a3f24967bd33175bb2562473cc59ebb1af` |
| `scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/smoke-test.sh` | `sha256:729a8c14516dd5431b876f7589254d740c600b295575223b1c736fa2ed60d23d` |
| `scripts/04.deploy/run-platform-shell-rate-limit-smoke/README.md` | `sha256:e78f9a3fc2ccbdeb78160e075a5f51e21e905f9a558fa6db7f37d282e2006287` |
| `scripts/04.deploy/run-platform-shell-rate-limit-smoke/script.py` | `sha256:966e4362d566c50a596791db66a623be33fed25b1558e109a66e85f76279ea3b` |
| `scripts/04.deploy/run-platform-shell-rate-limit-smoke/script.sh` | `sha256:9b6d56f5e873b58ed46b9ccf9b7476ae1a6b6fa7a2690a57b95033a531fc4419` |
| `scripts/04.deploy/run-platform-shell-rate-limit-smoke/smoke-test.sh` | `sha256:23f1e9639027b5993dbd7be078d443c29966495e34879d8ffb3b4732e639caaa` |
| `scripts/04.deploy/run-platform-shell-worker-smoke/README.md` | `sha256:c6d9a46b71bffc631df918fcb2b1ca0eabd245beb4ac27366b5d75207fdcd674` |
| `scripts/04.deploy/run-platform-shell-worker-smoke/script.py` | `sha256:477fa26cfa7fc5398885738659a84777b10076ceb7d80bd5bba8ea0b8eeb1e50` |
| `scripts/04.deploy/run-platform-shell-worker-smoke/script.sh` | `sha256:e226f9c6fef33728ead249ebbdbbc7f43fca91602599a2e60f3b67fcbafe5266` |
| `scripts/04.deploy/run-platform-shell-worker-smoke/smoke-test.sh` | `sha256:42afeb979956a11186c143604b485f2a841592bdb9990d74e85048918be81419` |
| `scripts/04.deploy/smoke-test-platform-shell-image/README.md` | `sha256:b15520dc76220af9efeb200f6738d17b5dc695f0b7a5d991d7c995506ae4b778` |
| `scripts/04.deploy/smoke-test-platform-shell-image/script.sh` | `sha256:53c3909939b1d98f479d919ae218d5de0969cde1b58ae544bc3a85b057b48c03` |
| `scripts/04.deploy/validate-container-boundaries/README.md` | `sha256:07853d4e86e10de495def48951c69f8796837489f1b3a3fed161a33e68cebe33` |
| `scripts/04.deploy/validate-container-boundaries/script.sh` | `sha256:f86a33e9db8f1b547ed77a5c1645a46a59b4b66730e6e2a107724eaba2d38da0` |
| `scripts/04.deploy/validate-container-boundaries/smoke-test.sh` | `sha256:78f7aa4429599ae4685690d7dcde6338d657906f7610a9eb89e82a803640de2e` |
| `scripts/04.deploy/verify-platform-shell-deploy-readiness/README.md` | `sha256:f6b8d78a254090625c2b2793c46844468856dd619ad756675a2b9cc3a81b032c` |
| `scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh` | `sha256:d7f9bf6ec4ae199a50fe289d6585bd6c31f54fb724d928750bd9024f22222b7b` |
| `scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh` | `sha256:396a32a9a70e13638a55b88c5c714b3dfc527a46575b842593181b32aa63f0e6` |
| `scripts/04.deploy/verify-platform-shell-deployment-artifact-store/README.md` | `sha256:6c3ee46b31d25b07958e00be59e2f40b528a2aeb1633e8adeb51c5de5aa7c8a1` |
| `scripts/04.deploy/verify-platform-shell-deployment-artifact-store/script.sh` | `sha256:470f9726e7bc02272f6c6ec7cf2cc3bc2bc25a283a9e39e4cb79ffd05e4ff1e9` |
| `scripts/04.deploy/verify-platform-shell-deployment-artifact-store/smoke-test.sh` | `sha256:14dc01d551bd5b31a9d19693c0a4bf9ce473c77e99dc7499f9b8265a04b6bc48` |
| `scripts/04.deploy/verify-platform-shell-deployment-reconciliation/README.md` | `sha256:85436f5bc99fc99961c95424a6e6da13fd64f71f2329c0868a80a2d990d2746c` |
| `scripts/04.deploy/verify-platform-shell-deployment-reconciliation/script.sh` | `sha256:3bc7c812cf6b744fd2676a6c2521ce0fcce8fb41041bcacce663882c33f2cd20` |
| `scripts/04.deploy/verify-platform-shell-deployment-reconciliation/smoke-test.sh` | `sha256:2f57caf00648904e6fd4fceeee21b0609cdda8b9b23f1aa0330c2ee4568c8de5` |
| `scripts/04.deploy/verify-platform-shell-deployment-workflow/README.md` | `sha256:fdcb2d8cc856c9377d3f69a3063cd1e25e1c8a23c88bbd3d89b680e6ba639a3f` |
| `scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh` | `sha256:186fae47bbb5a3fa7f200fe360d17e515bf7f77b63b98b26052d9b48493c2435` |
| `scripts/04.deploy/verify-platform-shell-drift-detection-boundary/README.md` | `sha256:949936a4f677af3aded7d2cc686341f156e11aa3f4803d6e11c20a5a7f7ea37c` |
| `scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.py` | `sha256:e3c64cb28cebe03072fa18ee662786a102fb093d02b227493a564ef4a1be68fc` |
| `scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.sh` | `sha256:c5682a8de94807c5b03d05adfde74c8be48bbfbe593430ef9fb283817dc27697` |
| `scripts/04.deploy/verify-platform-shell-drift-detection-boundary/smoke-test.sh` | `sha256:03a9c5ba19c02ec0a813922d578692af2f68a624ef240933d53b1d1de695484e` |
| `scripts/04.deploy/verify-platform-shell-infrastructure/README.md` | `sha256:c0cade5ac4b22b54f5f69668a809ba6e2aed62c396dc30ada736c7a64d48e144` |
| `scripts/04.deploy/verify-platform-shell-infrastructure/script.sh` | `sha256:427293b3560d2a5c9b6b6e431905a65165b4f541c754eaf40c584044c6a0309e` |
| `scripts/04.deploy/verify-platform-shell-metric-coverage/README.md` | `sha256:8041fb0f5599391992017141657428ac495852f60a28258f8be1769a6dc06b19` |
| `scripts/04.deploy/verify-platform-shell-metric-coverage/script.sh` | `sha256:9dd6b875b0aeffdcb0276567b9e69ce26f8347ed7e5f563958e901c3c0b67797` |
| `scripts/04.deploy/verify-platform-shell-metric-coverage/smoke-test.sh` | `sha256:8777be07fb929ec91a2f5e86f9a8115bb35fac330387684732ab5f1e718fc0d5` |
| `scripts/04.deploy/verify-platform-shell-observability-prerequisites/README.md` | `sha256:1412afb86af38fda105223ebf7512238c1aadbad990a3ee6bb0ce22114bf5ab3` |
| `scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh` | `sha256:d4fa5ad3eaaa3e82de00d1c32a2d2ba83e291b32b1c59ed6a773b1bec1678ab3` |
| `scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.py` | `sha256:edccd8dee7435e498c440a49364ba3bd96418c24f76f4ffd90286890273f9f11` |
| `scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.sh` | `sha256:25d94e858f70e7453509fd1fb33f0ad0a0ff99e6db6acfca18f7cac6592a51ff` |
| `scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/smoke-test.sh` | `sha256:a8ea03911ff147055a15534b8890e1896bc0e4675a3ede88ed30df7930d0b1a9` |
| `scripts/04.deploy/verify-platform-shell-postgresql-reference/README.md` | `sha256:a6d46c337ae1d636acdd7d821a1565fe19411f530738db63e3ca2fdb7fed7b10` |
| `scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh` | `sha256:723a9fe7279781110cf3c5ccec3751ad847bbf5c4c946df8247fc209c88a49c3` |
| `scripts/04.deploy/verify-platform-shell-postgresql-reference/smoke-test.sh` | `sha256:fc04080ba98ef0902c158ea674094c16362a0596a8555a2070383a3bbe9ca0d7` |
| `scripts/04.deploy/verify-platform-shell-synthetic-scheduler/README.md` | `sha256:421f84b9a2e6359aa7aac9d3b147eb3bb48167ac0441e8b3c98cc0a765f0d8b2` |
| `scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh` | `sha256:1c73caf81225139c48501aa084fd411ea39e7fe90f353414cfbc40c910926e8e` |
| `scripts/04.deploy/verify-platform-shell-synthetic-scheduler/smoke-test.sh` | `sha256:df99f7cf9f5893f899321170ffe298a5e405247d758786e6108626b9d803c1d1` |
| `scripts/04.deploy/verify-rag-rulebook-deploy-readiness/README.md` | `sha256:ee0245b4cab9e3682ddf044187bbe6da9253b763c5fda72eca349f804fd0d2b1` |
| `scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh` | `sha256:90c32ef75c80e519d94bcadf8272529bc8ab086b0233d1b3cc4276d9b6d007a4` |
| `scripts/04.deploy/verify-rag-rulebook-deploy-readiness/smoke-test.sh` | `sha256:7b8da4bbdaa9b99918f345a5003ab097de3f3e3a94dc21a055537581d758886a` |

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-staging-caller-triage
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record finding assignments and source-only caller accounting for staging image publication.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.script.operational-realization-caller-coverage
  path: scripts/04.deploy/operational-realization-gate/caller_coverage.py
-->
# Staging image-publication source review — 2026-09-29

These are dated source planning snapshots. They contain no runtime receipts or
operation authority. Source profile review records intent and intake ownership;
actual effects, identity, argument variants and runtime suitability need later
proof. Every source result remains unauthorized and qualification stays blocked.

## Finding intake

[Baseline triage](baseline-triage.json) preserves the earlier 273-source,
169-finding snapshot: 164 Phase 2 assignments and five Phase 3 assignments.
[Current triage](current-triage.json) separately records the fresh inventory.
All entries remain `open`, owned for intake by `release-control-programme`.
Neither document approves an adoption disposition or suppresses a source finding.

The fresh snapshot contains **282 sources and 175 findings**: 170 Phase 2 and 5 Phase 3 assignments. No current diagnostic is assigned to live provider proof. Both classifications validated as `complete` with coverage `blocked`.

The added findings come from implementation/test files introduced in this unit:

- `scripts/04.deploy/release-control/discovery/test_caller_inventory.py`: `opaque-executable`.
- `scripts/04.deploy/operational-realization-gate/test_caller_coverage.py`: `opaque-executable`.
- `scripts/04.deploy/operational-realization-gate/finding_triage.py`: `opaque-executable`.
- `scripts/04.deploy/release-control/discovery/caller_inventory.py`: `opaque-executable`.
- `scripts/04.deploy/operational-realization-gate/caller_coverage.py`: `opaque-executable`.
- `scripts/04.deploy/operational-realization-gate/test_finding_triage.py`: `opaque-executable`.

The historical adoption ledger remains a dated pending snapshot. It is now stale
against current source and must not be used as current acceptance evidence.

Current inventory: `sha256:b50cc819a263180b3eaa286e67f3f81e52ed69b66377413ae9bf70f289dd5486`.

## Selected caller boundary

The selected `.github/workflows/deploy-platform-shell-staging.yml` publishes an
image. It does not deploy ECS or CloudFormation. The collector independently
records all 23 workflow steps and follows the literal checks into 14 root package
commands and nine explicit script targets. Dynamic blocks remain whole opaque
subjects; their internal targets are not claimed to be completely enumerated.

[Caller graph](staging-caller-graph.json) binds 11 source files, 54 subjects and
53 invocation edges. [Reviewed source bindings](staging-caller-review.json) cover
every subject and edge with a declared profile and intake owner. Their validation
returned `accounting_verdict: accounted`, `qualification_verdict: blocked`, and
`authorized: false`. That result proves exact accounting against the declared
collector boundary, not whole-estate or runtime closure.

Graph identity: `sha256:8002a0aa2c45a5657ab5c0a4c114afb12e5279c7df6a77fa4f26f5dc4d5f3cb4`.

Accounting identity: `sha256:1850d1b2e412742d61fae091a923753bbb56efa5e6b383f644c2e227e827e4af`.

| Unresolved caller boundary | Count |
| --- | ---: |
| `caller-opaque-command` | 13 |
| `caller-script-body-unresolved` | 9 |
| `caller-tool-behavior-unresolved` | 7 |
| `caller-workflow-action-unresolved` | 9 |

All 38 boundaries remain owned pending source-closure obligations. External
steps include setup, authentication and attestation actions whose implementation
has not been admitted as evidence. Opaque scripts/tools require further caller
and behavior work. This report does not prove global caller absence or permit
any test-only/historical/retirement exemption.

The caller inventory explicitly binds four files under production-reachable
test directories. Their directory name cannot exclude them from this graph:

- `platform/server/tests/run-runtime-tests.mjs`
- `platform/server/tests/platform-server-boundaries.test.mjs`
- `products/kanbien-platform/tests/run-runtime-tests.mjs`
- `products/kanbien-platform/tests/kanbien-platform-boundaries.test.mjs`

## Reviewed subjects

`finite-job` expresses finite workflow/check invocation intent; it does not
prove termination or benign effects. `inspection` identifies intended checks;
`static-artifact` identifies build/publication work. Each needs its applicable
later release evidence. No source subject is classified as a service rollout.
Tool roles follow their reviewed immediate caller's source intent; actual tool
identity and effects remain unresolved. Every row's intake owner is
`release-control-programme`.

| Source subject | Reviewed profile | Subject ID |
| --- | --- | --- |
| `platform/server/tests/platform-server-boundaries.test.mjs` | `finite-job` | `sha256:ccfab06ba945b1f8bfd8c0c2a627b28647fcbbaf28e103a794d35205f4270a39` |
| `platform/server/tests/run-runtime-tests.mjs` | `finite-job` | `sha256:f6edb88420847aa57b18500d095c957091a888006ab29e5a80d82ad07f1aed26` |
| `platform:server:boundary` | `finite-job` | `sha256:dc0ca9f99c6ac9768b2a75d37833a60f73e355e5edafe515cdf6e5c69eac5f29` |
| `platform:server:build` | `static-artifact` | `sha256:d4894e957c757b3884f3514f6d07bd3b600ac859aac26843d66d07e179be9a9e` |
| `platform:server:check` | `finite-job` | `sha256:ce2424501b77cc9d169486fd5526ab2d55192707c394d52ad3382bf4325be17d` |
| `platform:server:image-build` | `static-artifact` | `sha256:6454fb0f36d75a3c716dc919a5249e68e8bb0a629e94362e4ddc98ca3ef9b6e6` |
| `platform:server:image-runtime-check` | `finite-job` | `sha256:e650758fdd60eded55f86be1f8cbb2d55e3a866d5e279648d35c0dc0fe626275` |
| `platform:server:test` | `finite-job` | `sha256:402399233e7e5920e1ad9d873eaa53a0367b11de1f7caaee76a01e275371eb12` |
| `platform:server:typecheck` | `inspection` | `sha256:262ba80d6b8e2d2c2cbfc7c5f9141a71801c97b786523a94c1823882e1eb8166` |
| `platform:shell:deployment-workflow:check` | `inspection` | `sha256:5b234962936e9dea9f5d1b95aad7b795d36ed88cb613c3bade4e8509843ce8ec` |
| `platform:shell:infrastructure:check` | `inspection` | `sha256:4521711dea82f61f3c0d81216ec42ad3a3d85d98b59e45f9c4f55d6cbe646b9c` |
| `product:kanbien-platform:boundary` | `finite-job` | `sha256:fa967975e29929d9fca4d9b4f569abf4e90331759adfd7856f3a968caf71c613` |
| `product:kanbien-platform:build` | `static-artifact` | `sha256:3bc5cd958dac69020b0099ec03e0bb5d598d8e6d7d4d2c8dc38ece749f12872c` |
| `product:kanbien-platform:check` | `finite-job` | `sha256:a25e640bdf248f6860578fbeb8f66194b1679e3c0e3167a220a5b90c6b1b5675` |
| `product:kanbien-platform:test` | `finite-job` | `sha256:2fb412cd234e03a9edfc2073f77aeadea4e3a355d010dfad0fbac416a7fe1de2` |
| `product:kanbien-platform:typecheck` | `inspection` | `sha256:d6dfa58c9e6aa1c77eaba9f5e0d0f32af86d2fb4d840a4f933bfd58c1632ed80` |
| `products/kanbien-platform/tests/kanbien-platform-boundaries.test.mjs` | `finite-job` | `sha256:5d5511b6a21ecdf074f580368a741f7da00a98fc71d957ffafa2d30a23ee368c` |
| `products/kanbien-platform/tests/run-runtime-tests.mjs` | `finite-job` | `sha256:f87fa1eccb37df1b48b2cd5abcfbf54cc99e9763ffd1b937f48355681802cf4c` |
| `scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs` | `static-artifact` | `sha256:63616853b64ac765c644c6b6a5bb24d19c8911655e49d14c0d41b24f9a2a9d6c` |
| `scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs` | `finite-job` | `sha256:7f22adcb7e3d8959353c7efb3584e98794021423e1a2f0e1822d96523ec6d381` |
| `scripts/04.deploy/validate-container-boundaries/script.sh` | `inspection` | `sha256:6787d3938fec9dd1582bb0733b59a58421968fef9c3adc784d46d9dbe0706eb9` |
| `scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh` | `inspection` | `sha256:9829cbe40d399e45aba5cd9d96762cfbcbd731bafbeca4f3e4756824d42b902e` |
| `scripts/04.deploy/verify-platform-shell-infrastructure/script.sh` | `inspection` | `sha256:4787a318bf7eed5b31d5216dfd1d5bfa72ee0ae804830e51fc06e6ebe674230e` |
| `staging-image-publication` | `static-artifact` | `sha256:5699472a545af246d69ac940a00d28180e3536ce08736a250ebbf70435329e50` |
| `tool-41e1fb2e0e63` | `inspection` | `sha256:41e1fb2e0e634a3999af27e9f00d5d66e86d0b54e5ed178d7e255372cf11e032` |
| `tool-42e879c2aeae` | `inspection` | `sha256:42e879c2aeaed821a4dee5a5429dd93dfa1e4c55b5c5e8c97e8a2227cb7559e4` |
| `tool-93441140dc3a` | `finite-job` | `sha256:93441140dc3aab665517e87c2f86142efe908f4a7938f771b03ec1d2f99163cb` |
| `tool-94414466cae2` | `static-artifact` | `sha256:94414466cae2e68ac1d3d1eeb1e7e83f298022583d437c7c1e5a625b766a51e2` |
| `tool-c393348ece9b` | `static-artifact` | `sha256:c393348ece9b7bcc15e0de34a49480b68308e00d5105b280267cfa6aedbc10c4` |
| `tool-d3fd3d4440fb` | `static-artifact` | `sha256:d3fd3d4440fb56ff1fc653adcdf4d12166729f33e8fd01ae248de7aba5171ccb` |
| `tool-df6bde212d9e` | `finite-job` | `sha256:df6bde212d9ea2bf14dce75df0332408ca7c2102e0d111f34bd01e9564270285` |
| `workflow-step-01` | `finite-job` | `sha256:7263d10b26ba7668e836ff25b0853a7ce671744e5e0c7bfee893428e096498a5` |
| `workflow-step-02` | `inspection` | `sha256:8b1beac9b39ea6e7cafca590f46fb6710ed68de02f3447c2cc39ef0b2e916bb3` |
| `workflow-step-03` | `finite-job` | `sha256:9d65b01e58c2890a4460d70c72b4556ab9a98a8b93ed722658c4224f673f4fae` |
| `workflow-step-04` | `finite-job` | `sha256:24c0e3b82cd8fabc9a06b8b4ccc9ff773600e869a59e52c4d0d87fc04f40bd7d` |
| `workflow-step-05` | `finite-job` | `sha256:c2fa387043c4a8f21ea7f5459e3479164ac1cca5f3137003fe41e5b1d91228b3` |
| `workflow-step-06` | `finite-job` | `sha256:e91d3221910d13f02561f650dec5cad6ff33473a0062077c52b512e0c1646c70` |
| `workflow-step-07` | `finite-job` | `sha256:8dd1e6d2fdc008bac73f09bae2f82b233ab27470e789bacaf022eb5c9935be29` |
| `workflow-step-08` | `finite-job` | `sha256:7999fb76318c069163d83216a8a2ca59454973322906a52d3d4b2c2f279af8ab` |
| `workflow-step-09` | `inspection` | `sha256:bd01419d62eeb92910a13bdf90803d7960aa2bcaaeaaf5adb1dffcf3efa94b1e` |
| `workflow-step-10` | `finite-job` | `sha256:cf94785e573d7dd90f57b0b8290e6eb97316987468435466b007bf5dce7ec09b` |
| `workflow-step-11` | `finite-job` | `sha256:4bb640b171cae5a4e9ac9e026f518031aaacb203ae5c7193fbd6004c2247ca68` |
| `workflow-step-12` | `inspection` | `sha256:6223060f33546d0a0c168c88326a7f45d2e8d7b6167971ea8ba5cee4c7d66ef7` |
| `workflow-step-13` | `finite-job` | `sha256:0497c5b261f7b510002eb5e555f4321f17e21c64f00a76c87e35a57e8d109de8` |
| `workflow-step-14` | `inspection` | `sha256:2d165c8199a7c167a2a1c4b696b99d14e63e254145fdea2ac7883b822d038c01` |
| `workflow-step-15` | `static-artifact` | `sha256:8afdaf3acb4f5d76941d3e416352393ca166d9ddcb23330b92edc90ee190fcfb` |
| `workflow-step-16` | `static-artifact` | `sha256:8b9175e8e0081561900cfcb368666ae42bbb1e0c3bdcb1414e6dc3bcb26ccff0` |
| `workflow-step-17` | `inspection` | `sha256:efffd54f8262e1938d14b5d8a99a66cf58538b5cfc20a369a9e6438df66c5ee0` |
| `workflow-step-18` | `inspection` | `sha256:061f9be9e60d37e0dbe20a2df10eb5a38ace7b2b904a55558825d8f8abb90f69` |
| `workflow-step-19` | `inspection` | `sha256:65f189ae32f52281890db1dc140906a59120e771c09aca91852c113f852f2a72` |
| `workflow-step-20` | `static-artifact` | `sha256:705d717a848c8c5fd1b41510ec30f671f2e4e2e5f2052bc38e8e82b5c048b265` |
| `workflow-step-21` | `static-artifact` | `sha256:7ceefb48892031f380138cdb8b761dbd050ef0ff81c4f27aa67fe121c2879f19` |
| `workflow-step-22` | `static-artifact` | `sha256:2cde9b5f60ea919e2e7440284e51f7878703a2acfa7e67014b06f54772c25799` |
| `workflow-step-23` | `finite-job` | `sha256:dcc582f1559f8f1554994b929cc11331e15c5e800652fc38ffb71f6676b95d4b` |

## Reproduction and next unit

From the repository root, use the existing gate with `--triage --source-root .
--finding-triage docs/04.deploy/plans/release-control-source-adoption/2026-09-29-triage-and-callers/current-triage.json`.
It returns 0 only for complete classification; coverage still reads `blocked`.
Use `--callers --source-root . --workflow .github/workflows/deploy-platform-shell-staging.yml
--caller-review docs/04.deploy/plans/release-control-source-adoption/2026-09-29-triage-and-callers/staging-caller-review.json`
for source accounting. It returns 0 only for current complete review; qualification
still reads `blocked`. Any source/policy/collector change invalidates the relevant
snapshot. The public commands recollect source; they do not trust the saved graph.

Next delivery unit: extend caller/operation contracts for the nine selected
script terminals and external workflow actions, with explicit profile/argument
variants, build/import closure and mutation tests. Use the current open triage
as the queue; account for other operation families separately. Artifact proof
implementation can proceed when its required source inputs are accounted for,
while absent receipts still block release eligibility. No AWS adapters/stores,
PostgreSQL Stage 6 or live target operation is part of this source unit.

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.selected-release-blueprint
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the selected staging source blueprint, its public compilation command and remaining qualification boundaries.
portability: {class: internal, targets: [kanbien/staging]}
used_by:
- id: deploy.script.operational-realization-gate
  path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Selected staging release blueprint

The existing Operational Realization Gate compiles the actual selected
`kanbien/staging` source declarations into a provider-neutral realization
contract, immutable release definition and seventeen ordered acceptance
obligations. This is a source compilation capability within
[M1 of the MVP](../../../docs/04.deploy/plans/iaas-release-control-mvp.md).
It does not finish M1's caller/permission/recovery review or authorize an operation.

The target-specific source reader lives in
[`selected_blueprint.py`](../release-control/selected_blueprint.py). It uses the
existing container-profile collector and delegates neutral validation to
[`release_compiler.py`](release_compiler.py). It makes no provider requests and
executes no target, container, workflow or selected source command.

## Public command

From the repository root, provide the source revision and immutable candidate
image digest being proposed for review:

```bash
npm run deployment:realization:validate -- \
  --blueprint infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml \
  --source-root . \
  --source-revision "$RELEASE_SOURCE_REVISION" \
  --image-digest "$RELEASE_IMAGE_DIGEST" \
  --release-id staging-source-review-001 \
  --json
```

`RELEASE_SOURCE_REVISION` must contain a full 40- or 64-character hexadecimal
revision, and `RELEASE_IMAGE_DIGEST` must contain `sha256:` followed by 64
hexadecimal characters. These variables supply declarations. This command does
not prove that the revision exists, matches the source tree, produced that image,
or identifies an image available in the target registry. The result explicitly
retains `source_revision_status: declared` and `artifact_identity_status: declared`.
Use a new release identity when its immutable inputs change; this source command
is not a global release-ID registry.

Every flag except `--json` is required. Output is always JSON. Duplicate flags,
abbreviations, positional arguments and flags from other gate modes are refused.
Exit 0 means only that the selected source blueprint compiled. Exit 1 emits a
fixed safe diagnostic without source text, parser details, private paths or
tracebacks. The existing gate shell wrapper and package command remain the
public entry point.

## What the compilation checks

Three target files define the proposal:

- `target-release-blueprint.v1.yml` selects logical operations, source profiles,
  immutable source fingerprints, owner, risk reference and the two companion files.
- `target-realization.v1.yml` uses the existing neutral graph, identity,
  configuration, dependency, observation and recovery model.
- `target-acceptance-policy.v1.yml` declares all seventeen gate requirements and
  per-operation evidence overrides.

They live under
`infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/`.
The closed versioned blueprint schema lives under
`infra/04.deploy/contracts/release-control/v1/`.

Compilation freshly reads the selected files and checks every declared source
fingerprint. It requires the target profile, readiness declaration, image recipe,
service template, foundation composition and its fragments, package/lock files,
selected deployment workflow, OIDC policy sources and selected product command
source paths. The blueprint additionally pins the selected supporting callers
and build inputs listed in its source bindings. Missing, changed, duplicate,
unsafe or symlinked inputs fail; files read during compilation are checked again
before completion. The neutral contract and acceptance policy join that read
snapshot and their digests bind the generated release.

The current service template contributes thirteen container obligations across
nine task definitions: candidate and deployed server, regular relay and worker,
five relational tasks, and four telemetry sidecars. The image's default server
command must match its selected operation. Exact command hashes, declared task
and execution-role expression hashes, source identity and container configuration
hashes are retained without copying raw provider configuration into output.
External sidecar image digests come from the immutable source declarations.

These are container-level proof subjects. Containers sharing a task definition
are not independently dispatchable provider operations; later adapters must
preserve their common task boundary. The `execution_group_digest` hashes the
complete source task definition, so co-scheduled containers share the same group
binding. It does not prove a provider execution. Dependencies in this source proposal must
be reviewed before they become an execution schedule. Pinning a workflow or
script does not establish complete transitive behavior or caller closure.

The existing compiler validates every artifact/unit reference, ordered operation
dependency, symbolic command, recovery/cleanup binding and all seventeen gate
rows. Every operation remains represented at every stage: 221 generated
operation requirements for the current thirteen subjects. Multiple commands in
one product image have distinct logical artifact IDs bound to that same proposed
image digest.

The result binds the input blueprint, actual selected source snapshot, loaded
schema identities, generated definition and maintained compiler/collector/public
wrapper implementation. Changed bindings invalidate the previous result. A
successful old JSON document is historical evidence, not a reusable permission.

## What remains unproved

All output keeps `authorized: false`, release/operation/qualification decisions
blocked, `policy_review: required` and `identity_proof: pending`. Every command's
qualification remains pending. Gate verdicts remain `not-started`; there is no
passed gate or generated `not-applicable` exemption. Stage 17 retains its actual
28-day observation obligation rather than receiving credit from compilation.

The owner identifier is checked against the existing target profile. That name
is not owner approval. Risk labels, evidence ages, attempt limits, recovery
routes and policy windows in the new assets are review proposals, not newly
approved production policy. Permission descriptions and role-reference hashes
are source bindings, not current IAM authorization. The existing official-main,
approved publication and protected-environment requirements remain unchanged;
local images are not declared deployable merely by supplying their digest.

Telemetry sidecars currently inherit their image command. Their immutable image
reference is represented, while actual inherited command and runtime behavior
remain unqualified. Server health cannot satisfy a relational task, worker,
relay, sidecar, restore or cleanup obligation. Current source checks do not prove
provider state, target availability, semantic effects or durability of live evidence.

## Verification and next boundaries

Focused source checks use the existing test modules:

```bash
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p 'test_selected_blueprint.py'
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p 'test_blueprint_cli.py'
```

They cover actual source projection and independent recompilation, changed or
missing source/commands/identities, graph coverage, immutable sidecar bindings,
strict CLI input, schema failures and safe error/authority output. They perform
no provider operation. Parent integration also runs the ordinary realization
checks and records the exact tested source and evidence.

M2 refreshes the current final image and selected actual-command/effect/trust
proofs. M3 connects existing provider inspection, effect planning, candidate
runtime proof and per-task no-effect preflight. M4 supplies the reviewed execution
decision, enforceable writer exclusion, durable intent/evidence and recovery
through the shared command. M5 requires explicit scoped approval before the live
staging rehearsal. This source capability does not authorize publication,
provider mutation or PostgreSQL Stage 6 resumption.

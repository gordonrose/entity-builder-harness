<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.selected-admission
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the selected baseline/candidate admission compiler and its source-only authority boundary.
portability: {class: internal, targets: [kanbien-staging]}
used_by:
- id: deploy.script.selected-admission-cli
  path: scripts/04.deploy/operational-realization-gate/selected_admission_cli.py
-->

# Selected staging admission compiler

This is an additional mode of the existing Operational Realization Gate. It
compiles a closed, source-only admission request from a saved baseline selected
blueprint result and a freshly compiled candidate blueprint result. It does not
call AWS, GitHub, a registry, or a deploy command.

The result binds baseline and candidate separately: release ID and digest, source
revision, target-composition digest, and artifact-binding digest. Reusing a
release ID for changed content is refused. The candidate’s complete 17-stage
matrix is copied into safe stage/binding summaries, and every selected operation
receives a closed request containing its owner, profile, identity, symbolic
command, recovery/cleanup route, exact artifact binding, source/target
composition bindings, approved source-policy cost/attempt/window values, and
`authority_status: not-granted`.

Run it through the existing package command:

```sh
npm run deployment:realization:validate -- \
  --selected-admission \
  --baseline-result path/to/selected-baseline-result.json \
  --blueprint infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml \
  --source-root . \
  --source-revision "$RELEASE_SOURCE_REVISION" \
  --image-digest "$RELEASE_IMAGE_DIGEST" \
  --release-id staging-candidate-review-001 \
  --json
```

The baseline must be a complete result from the selected blueprint compiler. The
candidate is always freshly compiled from the supplied source root. Duplicate or
abbreviated flags, missing inputs, malformed baseline results, changed source
bindings, unsafe fields, incomplete/out-of-order gates and a same-ID rebound all
fail with fixed safe diagnostics.

`verdict: compiled` does **not** mean eligible to release. Every successful
result retains `authorized: false`, blocked release eligibility, blocked
operation authorization and blocked qualification. Its two findings state that
current evidence and independently verified authority are unavailable. The
result can never be passed to `require_execution_authority`; that function
always refuses. Future hosted/evidence work must replace those two findings with
verified receipts through the selected control boundary, rather than treating a
source result or CLI exit status as permission.

Focused verification:

```sh
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p 'test_selected_admission.py' -v
```

Next delivery unit: P05–P07 durable intent, request reservation, restart
recovery and writer fencing. No provider store, caller mutation route, hosted
workflow, image publication or target operation is implemented here.

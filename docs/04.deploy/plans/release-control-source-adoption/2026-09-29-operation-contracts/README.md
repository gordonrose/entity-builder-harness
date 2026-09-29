<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-operation-contract-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record reviewed selected operation source inputs while retaining semantic and runtime proof obligations.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Selected operation source review — 2026-09-29

This fifth-unit candidate extends source accounting for the staging image
publication workflow. The earlier baseline, triage/caller and validation
snapshots remain unchanged historical records. No inspected script or action
was executed and no remote action implementation was fetched.

The [operation inventory](operation-inventory.json) independently contains
**25 subjects, 25 incoming invocations, 1,495 observations and 731 dependency
relationships**, binding 238 source records. Its subject set is nine scripts,
nine external action instances and seven build-tool invocations. Conservative
literal references can include assertions/comments; they are observed source
candidates, not proof of execution or complete language semantics.

The [reviewed contracts](operation-contracts.json) acknowledge every subject,
invocation, observation and dependency. Owner, operation ID and declared profile
match the current [caller review](staging-caller-review.json). All unknown
argument variants remain blocked, with mandatory completion/failure/recovery
requirements and later evidence obligations.

The [result](operation-result.json) reports contracts complete, source closure
blocked, qualification blocked and authorization false. The operation collector
retains 135 findings; combined with the earlier caller graph, 148 distinct
subject/code findings remain visible. These counts describe a different scope
and vocabulary from estate triage and cannot be subtracted from its findings.

## Reviewed source intent

The [caller graph](staging-caller-graph.json) is byte-for-byte equal to the fourth
unit's selected graph: 54 subjects, 53 edges, 11 source records. The selected
workflow, package commands and scripts have not changed. Existing declared
profiles were retained; this review adds input/dependency accounting and proof
obligations, without asserting that the profiles describe verified runtime
effects.

All nine current script invocations have empty trailing arguments:

| Script | Source-observed purpose and outstanding boundary |
| --- | --- |
| `platform/server/tests/run-runtime-tests.mjs` | Writes generated package shims and runs dynamically enumerated built tests; actual built contents and process behavior need proof. |
| `platform/server/tests/platform-server-boundaries.test.mjs` | Reads manifest/source files for boundary checks; recursive filesystem and language semantics remain unresolved. |
| `products/kanbien-platform/tests/run-runtime-tests.mjs` | Prepares generated shims and invokes selected built tests; artifact membership and behavior remain unqualified. |
| `products/kanbien-platform/tests/kanbien-platform-boundaries.test.mjs` | Reads product manifest/source boundaries; directory naming does not make it excludable from production callers. |
| `scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs` | Generates package shims from literal and computed mappings; compiler emission and runtime resolution need exact-artifact proof. |
| `scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs` | Inspects built entrypoints, starts processes and temporarily changes workspace links; effects and restoration require later proof. |
| `scripts/04.deploy/verify-platform-shell-infrastructure/script.sh` | Runs child checks and embedded source analysis; arbitrary shell/Python behavior and dynamic inputs stay unresolved. |
| `scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh` | Reads workflow/target/build declarations and enforces intended publication ordering; policy execution and opaque code remain unqualified. |
| `scripts/04.deploy/validate-container-boundaries/script.sh` | Inspects Dockerfile placement and ignore coverage; dynamic repository enumeration remains unresolved. |

Only the container-boundary wrapper explicitly parses its CLI options. For the
other eight, this contract restricts reviewed source invocations to their current
empty argv; it does not assert that the executable rejects extra arguments.

The seven independently reached `tsc -p` invocations select the server's
check/build/runtime-test/image configurations and the product's
check/build/runtime-test configurations. Local configuration inheritance,
explicit member sets and supported import candidates are bound. Compiler defaults,
aliases, emission and unsupported resolution remain obligations.

## External actions

| Instance | Source intent | Remaining proof |
| --- | --- | --- |
| `actions/checkout@v4` | Select repository bytes; explicit credential persistence disabled | Mutable reference, action defaults and implementation |
| `actions/setup-node@v4` | Select Node tooling | Mutable reference, downloaded tooling and defaults |
| `actions/setup-python@v5` | Select Python tooling | Mutable reference, downloaded tooling and defaults |
| `docker/setup-buildx-action@v3` | Prepare image build tooling | Mutable reference, implementation and implicit defaults |
| `aws-actions/configure-aws-credentials@v4` | Establish declared cloud identity | Mutable reference, effective permissions and identity behavior |
| `aws-actions/amazon-ecr-login@v2` | Authenticate registry access | Mutable reference, credential handling and defaults |
| `anchore/sbom-action@v0` | Generate declared SBOM output | Mutable reference, exact tool/artifact behavior and defaults |
| `actions/attest@v4` — provenance | Attest the selected image digest | Mutable reference, subject binding and registry effects |
| `actions/attest@v4` — SBOM | Attest the selected image and SBOM | Mutable reference, shared subject/output binding and registry effects |

The action helper records 58 action-specific observations, including 19 explicit
input values and three upstream-output expressions. Conditions and inherited
context are hashed. The five publishing-related instances are conditional;
the workflow's declared OIDC/attestation permissions still apply at job scope.
The condition is not evidence that effective permissions were reduced.
All nine mutable-reference, nine default-input and nine remote-implementation
findings remain. A future SHA pin alone will not close the latter two.

## Reproduce the review

Recorded identities:

- Operation inventory: `sha256:d1c0635578ca8aabb1ada74338269f3c7fafc15d2fb7319393679deca453fe09`.
- Operation contracts: `sha256:5ed901a5ad03fb03539520926a3458a3500447f9c127f29f7235180176c92052`.
- Caller graph: `sha256:40bf4c1259ebf3a1136bca8db48b2fde221524fea97e306c47266ed415ef6717`.

```bash
candidate=docs/04.deploy/plans/release-control-source-adoption/2026-09-29-operation-contracts
gate=scripts/04.deploy/operational-realization-gate/script.sh

bash "$gate" --operations --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review "$candidate/staging-caller-review.json" \
  --operation-contracts "$candidate/operation-contracts.json"

bash "$gate" --consume-result "$candidate/operation-result.json" \
  --purpose source-analysis -- --operations --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review "$candidate/staging-caller-review.json" \
  --operation-contracts "$candidate/operation-contracts.json"
```

Both return zero only for unchanged complete source accounting. Changing the
consumer purpose to `release-eligibility` or `operation-authorization` returns
one with blocked authority. To independently regenerate observations, use
`--operations --source-root . --workflow ...` without declarations; its exit
one retains unresolved findings. Saved inventories are review artifacts only,
and the larger operation map is never accepted as public compilation input.

## Estate intake and next unit

[Current estate inventory](current-inventory.json), [open triage](current-triage.json)
and [triage result](current-triage-result.json) are separately refreshed. New
analysis modules are still opaque to the original estate collector. Operation
contracts do not suppress those findings, approve adoption exclusions or close
Phase 2 whole-estate coverage.

The fresh estate snapshot has **303 sources, 1,111 observations and 193 open
findings**: 188 Phase 2 assignments and five Phase 3 assignments. The eight added
findings are the eight new implementation/test modules. Classification remains
complete, coverage blocked and authorization false.
Inventory identity: `sha256:42222803bc99d027d8772cc00c8e141c123eebfefeee40457b441bb71db60d68`.

Next: deepen supported semantic/build-import coverage for dynamic script inputs,
workspace resolution and external action implementation boundaries. Exact-artifact
qualification for this image-publication family can proceed as its source
inputs become known; required receipts remain blocking until produced. Wider
adoption, evidence admission, authenticated authority and provider/live work
remain later. The full seventeen-stage matrix remains mandatory.

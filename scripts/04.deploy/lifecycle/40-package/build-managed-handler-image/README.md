<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.managed-handler-image
version: 1
status: draft
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.package-candidates
disciplines: [architecture, security, sre]
kind: guide
purpose: Explain declared managed-handler packaging, actual-runtime qualification and immutable publication without implying deployment.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.command.build-managed-handler-image
  path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/script.sh
-->
# Managed handler images

A scheduled tick and a queue delivery need callable functions, not an HTTP
server. This folder builds a declared function into an image and checks that
AWS's own Lambda runtime can load and invoke it. It does not create schedules,
deploy functions, change database permissions, or activate a worker.

## Files and responsibilities

- [script.sh](script.sh) selects one existing runnable program and delegates the
  Docker operation to the shared candidate-image builder.
- [qualification.py](qualification.py) checks the image identity, starts owned
  disposable containers, verifies their results and removes them even on
  failure. `qualify(image, program)` returns a finite report; `read_contract()`
  validates this image family's configuration; `inspect_image()` and
  `validate_result()` reject incomplete runtime evidence. `command()` captures
  tool failures without printing raw output.
- [runtime-api-fixture.mjs](runtime-api-fixture.mjs) supplies controlled events
  over a loopback Lambda Runtime API. It starts the image's official
  `/lambda-entrypoint.sh`; it does not import a substitute handler. The finished
  production handler receives the events through AWS's runtime client.
- [publication.py](publication.py) supplies the four reviewed program bindings
  to the existing immutable publisher. `binding(program)` chooses the existing
  scope's role and repository; an unknown program is rejected. The shared
  publisher still owns main-only source checks, reservation and uncertain-push
  reconciliation.
- [qualification-test.py](qualification-test.py) checks these boundaries with
  controlled Docker responses. Passing it is **not** evidence that an image ran.

The [shared image recipe](../../../../../infra/04.deploy/03.product/image/scheduling-lambda/Dockerfile)
and its [contract](../../../../../infra/04.deploy/03.product/image/scheduling-lambda/image-contract.yml)
are separate from these command owners. The
[managed payload helper](../prepare-runtime-payload/managed-handler.mjs) reuses
the existing declaration reader, public package assembler and dependency copier.
`prepareManagedHandler()` adds only the selected exported function's wrapper;
`runManagedHandler()` adds the finite command-line failure boundary.

## One worked example

Run from the repository root, on a machine with a working Docker engine:

```bash
bash scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/script.sh \
  --program kanbien-core-server-persistence-scheduling-dispatch \
  --tag kanbien-core-server-persistence-scheduling-dispatch:qualification
python3 scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py \
  --program kanbien-core-server-persistence-scheduling-dispatch \
  --image kanbien-core-server-persistence-scheduling-dispatch:qualification \
  --report /tmp/core-dispatch-managed-qualification.json
```

Use a fresh report path: the command refuses to overwrite existing evidence.
The builder reads the selected program's source and permitted dependencies from
the [runnable index](../../../../../infra/04.deploy/03.product/entrypoints/runnable-program-index.yml).
The payload helper writes `handler.js`, exporting the declared `handler`
function. The official Node 22 Lambda base calls it as `handler.handler`.

Qualification first rejects missing configuration, then uses synthetic local
configuration with no reachable database or AWS credentials. A dispatch
invocation with only 30 seconds remaining must stop before work; a second
invocation checks reuse of the same runtime process. Worker images additionally
check empty batches, malformed records, insufficient time, an unavailable
database, oversized batches and safe errors. The unavailable-database case uses
a valid registered job message against closed loopback port 1; it must retain
the delivery, not report success. Production currently accepts one record per invocation;
rejecting a larger batch is deliberate, not a mixed-success proof.

A successful report includes the immutable local image ID, source revision,
case names, image bytes and elapsed seconds. A failed command emits a finite
code and cannot supply a passed report. Raw provider output, queue bodies and
credentials are not report fields. Containers are non-root, read-only except
for `/tmp`, and have no external network. Their cleanup is required before the
command can return success.

## Publication and limits

```text
runnable declaration -> selected compile -> shared payload -> Lambda image
                                                          |
                                               actual runtime invocation
                                                          |
protected-main workflow -> existing publisher -> immutable image + custody
```

The [hosted workflow](../../../../../.github/workflows/publish-kanbien-core-platform-scheduling.yml)
uses the same recipe for independent core proof and Entity Smoke dispatch/worker
images. It records qualification before publication, uses each scope's existing
publisher role, requires the ECR vulnerability scan, and retains provenance and
package-custody evidence. The
[Lambda configuration projection](../../00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py)
binds that evidence to the selected scope/purpose and the complete declarative
template, including transitive permission and network configuration. Editing
any of that template invalidates its earlier configuration fingerprint.

Local checks:

```bash
node --test scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/managed-handler-test.mjs
python3 scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification-test.py
```

The actual image check has not been established merely by adding this code.
It does not prove live IAM, PostgreSQL access, queue acknowledgement, recovery
timing, or business deletion. Those remain separate evidence in
[the scheduling implementation plan](../../../../../.agentic/03.product/plans/implementation/reusable-aws-scheduling.md).
The existing HTTP maintenance images are still needed for migration and role
administration; these Lambda images do not replace them. Future products can
reuse the payload and image operations after declaring their own program and
reviewed runtime cases; the current scope-specific proof bindings do not grant
automatic deployment authority.

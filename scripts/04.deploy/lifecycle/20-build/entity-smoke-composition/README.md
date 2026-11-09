<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.readme.entity-smoke.composition
version: 1
status: draft
created_on: "2026-11-08"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.entity-smoke
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the isolated feature's fast compiled wiring proof and distinguish controlled local results from database, image and AWS qualification.
portability: {class: internal, targets: []}
used_by:
- id: deploy.test.entity-smoke.composition.wrapper
  path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
-->
# Entity-smoke composition checks

Before building an image, we need to know that the public `test-entity` app can
be wired to the selected PostgreSQL adapter, register its diagnostics and serve
the private command route. This folder checks that wiring without Docker,
PostgreSQL or AWS. Database responses and the lifecycle clock are controlled
test inputs, not evidence of durable storage.

## Run it

From the repository root:

```bash
bash scripts/repo/check-selection/script.sh \
  --checks entity-smoke-composition --execute-local --explain
```

The registered local check compiles fresh output, opens loopback HTTP listeners
and removes only its own temporary build directory. It does not launch provider
tasks, create a database, publish an image or approve a deployment. The selector
retains a safe run report under ignored `.cache/test-runs/`; the session log
records durable outcomes. This explicit selection proves this check, not every
affected repository check.

During development, changes to the app or this composition select the check
through [the existing catalogue](../../../../repo/check-selection/checks.yml).
The app's own type and use-case tests remain a separate `entity-smoke-runtime`
unit. Expected runtime is an estimate, not a changed timeout or permission to
skip slower proof.

## Files and execution

1. [smoke-test.sh](smoke-test.sh) compiles the
   [isolated project](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke.tsconfig.json)
   into a newly allocated temporary directory.
2. [dependency-boundary.mjs](dependency-boundary.mjs) reads TypeScript's resolved
   source closure and compares its owners with the selected runnable-program
   record. Every source must have fresh compiled output. The reviewed boundary
   admits the feature, Core, generic Platform packages and PostgreSQL, but rejects
   staging/product, workers and the CloudWatch adapter. It does not claim that
   this source observation is an actual image SBOM.
3. The [runtime preparer](../../40-package/build-entity-smoke-image/prepare-runtime.mjs)
   checks required compiled exports before writing public package shims and five
   executable wrappers. Its dry-run precedes actual preparation.
4. [runtime-test.mjs](runtime-test.mjs) loads those public compiled packages,
   injects controlled dependency responses, then starts the real Platform HTTP
   server on temporary loopback ports. External Node dependencies still come
   from the checkout; actual image isolation remains a separate proof.
5. [access-control-test.mjs](access-control-test.mjs) checks the actual
   administrator's fixed-runtime-role revocation and restoration with controlled
   SQL responses. It rejects widened identities, failed session termination,
   remaining sessions and an unconfirmed access state. Each uncertain write is
   attempted once. [database-proof-test.mjs](database-proof-test.mjs) checks the
   separate runtime-login proof: six structural/delete/history probes must be
   denied and rolled back; an unexpectedly allowed operation fails immediately.
   The restore reader uses a read-only snapshot and must retrieve the original
   generated ID and all original facts. Missing, duplicated or changed records
   fail without writes. These are controlled responses, not effective real
   PostgreSQL privilege or RDS restoration observations.
6. The [dependency preparation fixture](../../40-package/build-entity-smoke-image/dependency-test.mjs)
   calls the image's [dependency copier](../../40-package/build-entity-smoke-image/prepare-dependencies.mjs)
   against disposable installed-package trees. It verifies required and optional
   dependencies, preserves nested versions, excludes unrelated SDK packages and
   rejects malformed manifests, lock mismatches, symlinks and overlapping
   destinations before copying. The copier follows the installed dependency
   declarations rooted at `pg` and `@aws-sdk/rds-signer`; it does not copy every
   package sharing their namespaces. A dry-run reports `planned` without writing.
   A failed CLI report contains only its fixed code, phase, reason and effect,
   never the supplied path or parser exception. This is not package provenance
   or a vulnerability scan.
7. [template-test.py](template-test.py) parses the draft provider templates with
   the existing CloudFormation syntax adapter, then checks its private network,
   role/secret separation, immutable image, container controls, initial stopped
   service and disabled automatic rollback. Nine unsafe runtime-template
   variants and ten unsafe isolated-restore variants must fail. Parsed parameter
   patterns must accept actual delivery shapes and reject over-escaped forms.
   Shared image environment may not leak database settings into the HTTP verifier.
   The restore
   template binds a new private database to the owned snapshot and gives its
   reader only that database's runtime-login permission, with no administrator
   secret or source-database route. This is a local structural fixture, not AWS validation,
   live alignment or a provider mutation preflight.
   It also validates the image's actual
   [v2 runtime source graph](../../../../../infra/04.deploy/03.product/image/entity-smoke/realization-contract.v2.yml)
   through the shared compiler and compares its five program entrypoints with
   the real task definitions and source files. Two binding counterexamples
   reject a wrong task command and a structurally valid but incorrect claim
   that the HTTP-only verifier connects directly to storage. Image digests remain
   runtime-bound; no normalized live facts are created. Six workload nodes use
   those programs: the runtime, migration, administration, HTTP verifier,
   source-database privilege probe and separate restored-database reader. The
   last two share an executable but have different task definitions, identities
   and database destinations. Controllers and acceptance remain separate work.
8. The [task-control fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/task-control-test.py)
   calls the [internal task primitive](../../60-run/targets/kanbien-core-platform/entity-smoke/task-control.py)
   with a simulated provider. Before its sole submission, an exclusive,
   synchronously flushed file reserves the exact inputs and operation identity.
   A lost response requires observation of that same task, including its
   definition and overrides. Empty or unavailable observations never trigger
   another submission. A different caller key cannot submit another create for
   the same proof label. This does not provide AWS authority: the owning route
   must still enforce declaration, custody, fresh alignment and approved changes
   before supplying a provider capability.
9. The [evidence fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/task-evidence-test.py)
   and [runner fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/task-runner-test.py)
   check terminal task/image/source identity, complete operation steps, timing and
   safe diagnostics from code-generated catalogues. Retained receipts are reused
   unchanged as historical evidence, not relabelled as fresh provider state.
   A deadline authorizes neither an implicit stop nor another launch. The
   [qualification-control fixture](../../40-package/smoke-test-entity-smoke-image/qualification-control-test.mjs)
   uses simulated Docker responses to reject unowned cleanup and preserve
   reservations when absence cannot be observed; it does not qualify an image.
10. The [alignment fixture](../../00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py)
    supplies controlled observations to the real read-only alignment consumer.
    Twenty counterexamples reject mismatched engine, public placement, TLS/IAM
    posture, wrong dependency ownership, missing private secret delivery,
    unqualified image and incorrect budget. It verifies that retained output
    excludes endpoints and credential references. The actual command requires
    qualified custody, matching committed source and complete declarations before
    provider reads; this local fixture establishes none of those live facts.
11. The [resource-control fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/resource-control-test.py)
    checks owned runtime replacement, controlled stop/start and snapshot
    reservation. A stopped-task request is not proof that the task stopped;
    STOPPING, incomplete observations and changed inputs block success. A
    preexisting snapshot cannot become adoptable on resume. The healthy
    stop/start rehearsal is not an emergency failure-stop controller.
12. The [deployment-control fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/deployment-control-test.py)
    calls [deployment-control.py](../../60-run/targets/kanbien-core-platform/entity-smoke/deployment-control.py)
    against the actual main template and simulated provider responses. It
    admits exactly thirty own resource additions with no running server, then
    a separate desired-count-only activation. Lost create/execute responses
    reconcile without resubmission. Template drift, deletion, replacement,
    wrong dependency/image and missing execution lineage reject. The existing
    resource store has an explicit pre-record deployment binding; it does not
    invent an original-record digest before the feature creates anything.
13. The [restore-control fixture](../../60-run/targets/kanbien-core-platform/entity-smoke/restore-control-test.py)
    checks exact isolated-restore change review, execution lineage and original
    record reader completion before owned cleanup. Missing observations do not
    establish absence, and a stopping reader blocks deletion. These internal
    controls require a genuinely gated public route with concrete approval;
    they are not standalone AWS commands or accepted-release records.

These are executable checks, not public runtime exports. The separate
[target source folder](../../../../../infra/04.deploy/03.product/entrypoints/entity-smoke/)
owns the deployed implementations; the tests exercise those implementations
rather than an alternate verifier.

## What the assertions establish

For a create request with an invalid boolean, the actual HTTP route returns
400 before a repository write. A valid request returns 201, and get/list/edit
operate through the public feature services. The lifecycle cases distinguish
archive from logical deletion, check restoration inside and outside the
60-second recovery window, and assess purge eligibility. Hard purge is rejected.
The test clock advances; it does not wait a minute or change production policy.

For a simulated PostgreSQL duplicate-ID failure, creation returns the feature
conflict without retrying or dropping a selected source diagnostic/companion.
An update conflict or another constraint failure is not mislabelled as an ID
collision. Simulated TLS failure retains its security companion through the
actual app/server reporter, without exposing the input canary.

The private verifier creates a labelled record, retains a digest containing the
original ID and facts, and reads it through real local HTTP. Missing or changed
facts fail; the read phase never recreates them. Release metadata and storage
are controlled here, so this is not release custody or restart persistence proof.
The `observe-create` phase can reconcile a committed create whose response was
lost: it validates the known facts under the reserved label and returns their
original ID-bound digest without creating anything. Its eventual controller
must first establish that the reserved create task is terminal and retain this
observation before starting replacement or restore proof.

The administrative observer uses one read-only snapshot and the migration
runner's actual advisory-lock key. Controlled observations distinguish absent
state eligible for a new submission, complete checksum-matching applied state,
an active lock, inconsistent history and unavailable evidence. It never applies
migrations. Its production caller must establish that the earlier migration task
has stopped and retain a fresh task receipt before any replay decision; these
controller requirements are not implemented merely by passing the local fixture.

## Remaining proof

The [approved implementation plan](../../../../../.agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md)
tracks the candidate declaration's remaining acceptance connections, provider controls, actual restricted-role
PostgreSQL qualification, image/scan/SBOM/custody, replacement, isolated restore
and live AWS acceptance. The generated-ID declaration variant governs expected
behaviour. The reservation primitive now has executable local proof, but is not
yet connected to a complete gated live controller. Existing accepted scopes and
images are not changed by this local test.


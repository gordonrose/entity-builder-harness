<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.readme.finite-recovery
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: readme
  purpose: Explain typed local inert recovery, interruption proof, refusal states and its authority boundary.
  portability: {class: reusable, targets: [entity-builder]}
  used_by:
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Durable recovery of the inert finite fixture

This capability extends the existing `container_engine.Engine` and
`LocalControlStore`. It proves recovery of the fixed `jobs/task.cjs success`
fixture, its exact image, run nonce, profile digest, random ownership token,
resource name and observed container ID. It does not qualify product commands,
prove business effects, authorize a provider operation or close source coverage.
Every normalized result retains `authorized: false`, blocked release/operation/
qualification/source verdicts, `semantic_verdict: unverified` and an empty
`product_profile_updates` list.

## Source and contract map

| Surface | Responsibility |
| --- | --- |
| `finite_recovery_contracts.py` and `finite-recovery-*.schema.yml` | Closed attempt, observation, controller result, conformance and error records. |
| `operation_actions.py` and `operation-action-record.schema.yml` | Typed attachment content, atomic intent preparation, durable consumed action reservations, composite operation/action revisions and immutable observation content. |
| `finite_recovery_engine.py` | Existing Engine isolation and transport with one total action deadline, exact identity reconstruction, bounded local logs and no automatic dispatch retry. |
| `finite_recovery_controller.py` | Existing operation lifecycle, current lease/fence checks, safe terminal reconciliation and cleanup. |
| `finite_recovery_conformance.py` | Real killed/reopened private processes against an existing inert image; independent payload and final absence checks. |
| `test_operation_actions.py`, `test_finite_recovery_*.py` | Deterministic positive, negative, crash-window, cache invalidation and authority-boundary tests. |

The operation and the full immutable attempt attachment commit in one SQLite
transaction before any attempt create/start request. Each action reservation
commits before the Engine call. Its budget remains spent after a lost response
or killed process. An observation can attach only to its exact current ticket,
claim and operation revision; a later reservation makes an earlier response
stale. Current clock, lease, fencing, revision and resource checks are never
cached. Only deterministic validation of immutable content uses a bounded cache
keyed by canonical bytes and the freshly checked runtime/schema fingerprint.

The typed action store has its own required format discriminator and source/
schema binding. Reopening a plain Unit A database or a database bound to changed
code fails before a writable open. There is no automatic migration. These are
single-host private-directory fixtures; hashes are integrity checks, not
independent authentication, encryption or protection from a malicious same-UID
host process.

## Fixed fixture budgets and reconciliation

The fixture policy permits one create and one start, at most 32 inspections,
three log reads and three cleanup reservations. It uses a 15-second operation
budget, three-second leases, two-second total action budgets and a further
30-second bounded recovery window. Each action also respects the current lease
and terminal deadline. Fractional remaining time flows through the shared
Engine transport without resetting the deadline for each internal Docker call.
The recipe uses `--pull=never`, no network, read-only root, nonroot identity,
fixed memory/CPU/PID limits, no capabilities, no host mounts and bounded local
logs. Ordinary Engine create calls retain disabled logs.

After takeover the claim is reconciliation-only:

- An unresolved consumed create followed by absence remains unknown; no new
  create or start is issued and no successful cleanup/closure is inferred.
- An exact created container with no start reservation may be cleaned and
  abandoned as a failed, never-started fixture. The controller first records
  that identity and the verified cleanup; a negative lookup alone is insufficient.
- A consumed start followed by a created or absent container remains unknown.
  The controller neither repeats start nor treats this uncertainty as completion.
- An exact exited container, correct terminal envelope and matching image,
  nonce/profile/owner permit completion reconciliation, followed by owned cleanup.
- A lost cleanup response is reconciled by fresh exact name and ID lookup.
  Cleanup retries require a fresh observation. Once cleanup was reserved,
  the attempt cannot subsequently start.
- A restart after cleanup verification refreshes absence evidence under the new
  fence before closing. Expired budgets remain expired; failure does not extend them.

Every inspect verifies both exact name and, once known, exact ID. A renamed,
replaced or foreign container cannot produce a false absence or be removed.

## Commands and evidence

The public entry point is the existing gate wrapper:

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --finite-recovery-conformance --source-root /absolute/source \
  --scratch-root /absolute/private-disk-scratch --image-id sha256:...
```

The implementation does not build or pull an image. The public image argument
must equal the source-owned `finite-recovery-image.lock.json` full-image pin.
That lock binds the previously accepted finite-job receipt bytes, qualified
source revision, immutable base, recipe and payload; it is not caller-supplied.
Receipt/recipe/source drift or any other image ID fails before Engine creation.
This local image pin does not claim public registry availability or provide an
acquisition path on another host. An unavailable image fails closed. A fresh
controlled fixture build must be qualified and repinned as a reviewed source
change; copying a desired image ID is not qualification.
The complete immutable image identity pins interpreter and all other layers,
not only `/app` contents. It independently inspects
the selected immutable image and uses the existing payload inventory collector
to compare actual fixture bytes before attempting recovery. Use the already
reviewed inert fixture image. The inventory collector remains its own bounded
existing capability; transactional action guarantees apply to the finite
attempts that follow.

Conformance checks normal completion and kills private child processes after
intent commit, create reservation, create effect before its observation, start
effect before its observation, terminal observation, cleanup effect, and cleanup
verification. The consumed-create/absence case intentionally retains an unknown
operation while proving that no resource or replay was introduced. All other
cases require exact cleanup and closure. No case promotes release eligibility.

Each run preserves an implementation snapshot, per-case immutable attempt,
private SQLite store and normalized result, then writes `conformance-result.json`
only after all cases pass. A failed run stays available for diagnosis and is not
relabeled as passing. Its source snapshot permits inspecting the exact store
format later without silently moving that database to newer code.

```bash
cd scripts/04.deploy/operational-realization-gate
python3 -B -m unittest test_operation_actions test_finite_recovery_engine \
  test_finite_recovery_controller test_finite_recovery_conformance
python3 -B -m unittest test_container_engine test_finite_job_engine
```

Next delivery unit: continue package-export/compiler coverage and remaining
implementation/action semantics. Production durable stores, AWS adapters and
live target qualification remain behind their separately approved readiness
gates. Local recovery receipts are refused for every common-consumer purpose.

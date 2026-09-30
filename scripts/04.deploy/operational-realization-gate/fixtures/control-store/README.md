<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.control-store
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Document local durable-control fixtures, verification and explicit trust boundaries.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.script.control-store-conformance
  path: scripts/04.deploy/operational-realization-gate/control_store_conformance.py
-->
# Local durable control-store conformance

This unit extends the existing Operational Realization Gate with an explicitly
local reference store. It records immutable intent before fixture effects,
serializes conflicting scopes and retains full typed evidence across process
interruption. It does not grant execution authority or qualify a cloud store.

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --control-store-conformance --scratch-root /owned/private/scratch
```

The command requires an existing owned root that is not writable by other users.
It creates a unique private child; it never opens an existing deployment store or
accepts an arbitrary command, target, policy override or preverified result. Output
is one normalized JSON receipt. Failures use `control-store-error/v1`, including
when dependencies or schemas cannot load; paths and raw exceptions are excluded.
The common source-result consumer rejects this producer for all purposes.

Local test database files remain under the supplied scratch root, with no secrets
or cloud inputs. They are retained for inspection; this is not a production
retention or deletion policy. The normalized receipt can be retained in Git.

## Contract and API

`LocalControlStore(existing_private_directory)` offers these typed operations:

- `prepare(intent)`: persist the immutable source/profile/artifact/environment,
  idempotency, policy-digest, recovery-route and global resource-scope bindings.
- `claim(operation_id, owner_nonce)`: atomically acquire all declared scopes and
  return their new fencing generations. Another operation with any overlapping
  unresolved scope stays blocked even after the old lease expires.
- `renew(claim, expected_revision)`: extend a current claim using revision CAS.
  An execution lease can never extend the immutable whole-operation deadline.
- `advance(claim, expected_revision, event, evidence_digest=None)`: record a closed
  allowed transition. `effect-intent` is committed before the fixture effect.
- `put_evidence(claim, typed_document)`: persist the full safe document and its
  journal reference in one transaction. It is bound to operation, release, profile,
  artifact, attempt, exact current scope fences, observed journal revision and time.
- `read(operation_id)` and `read_evidence(operation_id, digest)`: validate and return
  the journal and actual evidence content. Hash-only unavailable content fails.

Scope identity is the canonical digest of provider namespace, target and resource;
release/profile/operation IDs do not change it. This unit admits only the explicit
`local-fixture` provider namespace. Real provider adapters must later normalize and
prove the complete shared-resource scope set; this fixture API cannot discover
undeclared overlap on its own.

Claim expiry moves unresolved work to `unknown` and grants reconciliation only.
Neither a restart, a new lease, nor a verified absence silently permits a new effect.
A completed observation may be reconciled into success. Success/failure retains its
resource scopes until a current fenced post-completion cleanup observation proves
zero owned resources and the operation is explicitly closed. Closing preserves
scope generations so a subsequent release cannot reuse a stale fence.

Observation admission follows the operation phase: effect observations follow an
intent, absence belongs to current reconciliation, and cleanup observations follow
success/failure. Consuming evidence requires its latest journal attachment; changing
revision, attempt, scope fence or time validity requires a fresh observation. Closing
rehashes the actual current-fence cleanup evidence. Historical evidence remains
retrievable after freshness expires, but cannot authorize a current transition.

Every transaction records the highest valid observed host time. A rejected expired
claim commits that high-water mark while rolling back its work. A later backward
clock cannot restore its former lease. The store also binds the host boot ID and
schema revision fingerprint. Reopening after a boot change or schema revision
change is blocked and requires future explicit recovery/migration work.

## Explicit fixture policy

`control_store_fixtures.py` contains all positive fixture documents and the synthetic
policy: lease 1,000 ms, whole operation 10,000 ms, call budget 500 ms, maximum two
attempts, evidence lifetime 5,000 ms. Conformance uses an explicit synthetic clock
starting at 1,000,000 ms so expiry and rollback are deterministic. These numbers are
fixture inputs, not production defaults or an agreed retention/RPO policy.

The policy is immutable and digest-bound. Unit A only records a call budget; it does
not execute or time provider calls, implement retries, or reconnect the container
engine. Retry/recovery behavior requires the next unit's reconcile-before-retry
integration and real process interruption cases around actual finite engine effects.

## Verification and evidence

Run focused verification:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate -p 'test_local_control_store.py' -v
```

The canonical launcher additionally registers journal, conformance and CLI suites.
The registered suites exercise invalid/unsafe schemas and fields, immutable intent,
resource conflicts across releases, atomic multi-scope claims, revisions, fence
persistence, stale owners, deadline/lease corruption, clock rollback, missing/corrupt
content, phase/attempt/fence/time-bound evidence, cleanup and safe path handling.

The public conformance runs ten cases, including seven actual child processes and
three `SIGKILL`s: durable intent before an effect, durable effect plus evidence,
rollback of an uncommitted transaction, competing claimants, competing revisions,
reconciliation-only expiry, cross-release conflict, generation preservation after
close, persisted expired-clock rejection, and missing evidence content rejection.
A fixture effect is one fixed file created exclusively and fsynced; it is not a
container or cloud resource. Normalized per-case facts record child/killed counts,
accepted claims, rejected actions, durable effects, and validated evidence documents.

The receipt binds seven actual helper/wrapper files, the four loaded schema byte digests,
explicit fixture policy, actual SQLite runtime version, verified DELETE/FULL mode,
and its own normalized content digest. It states the real
observation timestamp separately from the synthetic fixture timeline. It always has
`authorized=false`, blocked release/operation authority, and blocked qualification.

## Limits and next delivery unit

SQLite rollback-journal mode is local filesystem, same-host coordination. Existing non-DELETE journal modes are refused without migration. The host, kernel, clock and
same-UID processes are trusted; this is not an adversarial or distributed lock service.
The code rejects unsafe symlink components and non-private database files, bounds
records, storage pages and journal length, and reports classified errors. It does not
prove host reboot, power-loss recovery, remote filesystem behavior, encryption,
independent authentication, retention, RPO or durable cloud store operations. Journal
hashes detect ordinary corruption; they are not signatures against a malicious host.

A fence prevents stale journal transitions. It does not cancel a provider request
already in flight. A future adapter must enforce the provider-side identity and
reconciliation boundary, and must never infer permission from a subprocess exit code.

Next delivery unit: connect this control-store API to the existing finite container
engine, persist owned resource identities before creation, reconcile after actual
process interruption before retry, enforce the immutable budgets, and require real
cleanup observations before releasing resource scopes. No AWS adapter, cloud store,
production admission policy, or PostgreSQL Stage 6 work is included or waived.

The rollback-journal choice avoids relying on the host library having the fixes for
the [documented WAL-reset issue](https://www.sqlite.org/wal.html#walreset). It is a
local reference-store implementation choice; no host package upgrade is performed.

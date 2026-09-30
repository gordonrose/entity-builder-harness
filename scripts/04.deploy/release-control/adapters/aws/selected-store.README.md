<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.guide.aws-selected-store
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: guide
purpose: Explain the selected shared record request seam, fixture evidence and remaining controller and live qualification boundaries.
portability: {class: internal, targets: [kanbien/staging]}
used_by:
- id: deploy.script.aws-selected-store
  path: scripts/04.deploy/release-control/adapters/aws/selected_store.py
-->

# Selected shared store — source conformance

This adapter extends the existing realization gate's record contracts with a
conditional AWS request seam. It does not run a controller, contact AWS, create a
store or authorize an effect. Its only transport is an explicitly supplied private
fixture callback; there is no default SDK, CLI, credentials path or live transport.
The existing local SQLite v1 store and its conformance behavior stay intact.

`selected_operation.py` owns the new v2 pure record/transition rules and reuses the
existing journal canonicalization and schema loader. `SelectedStore.apply` calls
those rules before constructing any write. It does not copy the local store's
state machine or claim that the new selected conformance snapshots are compatible
with local v1 records. The record remains `selected-operation-conformance`, the
operation approval is `not-granted`, and every result blocks release and operation
authority. A persisted `reserved` record is never a provider dispatch ticket.

One transaction writes the selected scope snapshot, operation snapshot and new
append-only event, while checking the global store generation. Every existing
snapshot uses its complete previous digest and generation as a compare-and-swap
condition. Competing owners, stale revisions, stale fences and stale restored
store generations cannot overwrite a newer snapshot in the fixture transport.
The event key is unique to operation and revision. Intent, ownership, renewal,
reservation and observation therefore share one conditional boundary. Fixed table
keys use partition `selected-control/v2/kanbien/staging` and sort keys `generation`,
`scope`, `operation/<operation-id>` and `event/<operation-id>/<revision>`.

The proposed source resource names match the operating-policy specification:
`kanbien-staging-platform-shell-release-control` and
`kanbien-staging-platform-shell-release-evidence-337159794548`, in eu-west-1.
They do not assert that those resources exist. Evidence keys are restricted to
`kanbien/staging/operations/<generation>/<operation-id>/<content-sha256>.json`.
Bootstrap must establish the reviewed generation item before any record write;
this adapter cannot initialize it, change it, release it or clear a conflicting
scope. Reusing the scope for another operation after closure is intentionally a
later controller decision, not implemented by this seam.

Evidence is a closed `selected-operation-evidence/v2` fixture record. It contains
operation/generation, prior record digest, image digest, bounded observation time,
assertion and verdict. It accepts no secrets, raw logs, provider bodies or authority
fields. Upload uses S3 `If-None-Match: *`, expected bucket owner, AES256 encryption
and an explicit SHA-256 checksum. The returned non-null version is read back by
that exact version, then its checksum, size, encryption, canonical bytes and
binding are verified. An observation or cleanup event can link evidence only
when this readback matches the exact prior snapshot, image, assertion and time.
The immutable version reference is retained in the journal event. S3 upload and
DynamoDB linking are two separate operations: an unlinked object cannot advance
the operation or grant authority. A lost journal acknowledgement may hide a
committed transition; it requires quarantine and reconciliation, not an assumption
of failure or replay.

No request is automatically retried. A transport can raise `ConditionalConflict`
only for a proven, wholly rejected conditional write. All other mutation failures
are unknown outcomes. Malformed mutation acknowledgements also quarantine the
instance. **That quarantine flag is process-local.** It does not establish durable
unknown-outcome recovery after a process restart. A newly constructed instance
can inspect committed snapshots; the pure record rules still forbid spending the
same reservation twice, and no instance can grant execution authority. A future
controller must durably handle lost responses, stale credential lifetimes and
in-flight effects before resuming. Read errors never become evidence of absence.

Normalized fixture transports use service/operation/region/parameters request
objects with only `TransactGetItems`, `TransactWriteItems`, `PutObject` and
`GetObject`. Read responses are closed and bounded before record decoding. A
future live transport must additionally prove credentials/target identity, bound
network response bytes and deadlines, disable unreviewed retries, normalize SDK
metadata, and classify definite rejection conservatively. The current tests do
not prove actual AWS request acceptance, encryption, retention, one-writer IAM,
point-in-time recovery, S3 version retention, hosted execution or cloud durability.

Focused verification uses the existing gate's test environment:

```bash
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p test_selected_store.py -v
```

Positive and negative fixtures cover atomic competing writers, generation and
snapshot corruption, consumed reservations, expiry, unknown responses before and
after commit, stale owners, exact immutable evidence, failed/missing/stale evidence,
unsafe fields, upload success with lost journal acknowledgement, and authority
refusal. They include a full inert prepare/claim/reserve/observe/cleanup/close
sequence. No live resources or actual candidate task are involved.

Next delivery is the approved controller and caller boundary: current authority
admission, real clock/credential/evidence checks, scope lifecycle, durable dispatch
and interruption recovery, immutable effect identity, independent observations,
cleanup and legacy caller refusal. CloudFormation/IAM/cost review, bootstrap
approval and live conformance remain separate. This unit completes neither M4 nor
the staging rehearsal.

The request design follows the official [DynamoDB transaction API](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html),
[S3 conditional upload API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html)
and [S3 versioned read API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html).
Every submission uses a new DynamoDB request token so a previous success cannot
be replayed from the service's ten-minute idempotency cache instead of checking
the current compare-and-swap conditions. There is no automatic submission retry;
the compare-and-swap conditions and append-only key remain mandatory. This is a
store-submission token, separate from any future provider-effect idempotency token.
A provider-effect token must remain bound to the durable intent after an unknown
response; changing it to evade provider deduplication is never a recovery strategy.

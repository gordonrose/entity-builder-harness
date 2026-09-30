<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.guide.selected-operation
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: guide
purpose: Explain selected operation conformance records, approved source policy and the remaining provider authority boundary.
portability: {class: internal, targets: [kanbien-staging]}
used_by:
- id: deploy.script.selected-operation
  path: scripts/04.deploy/operational-realization-gate/selected_operation.py
-->

# Selected operation record seam

This extends the existing realization gate with a versioned record/transition
seam for the fixed Kanbien staging candidate operation. It does not start tasks,
call AWS, acquire production authority, or qualify a shared store. Every record
retains `authorized: false`, blocked release eligibility and blocked operation
authorization. The approved operating policy permits source implementation;
it does not approve a particular operation. `require_execution_authority`
therefore always refuses, including valid records with a declared deadline.

The handwritten source policy projection fixes a bounded subset of the approved
executor, retention/recovery, authority, lease, attempt, clock and cost values.
It is a conformance projection, not full enforcement of the operating policy:
encryption, retention-after-closure, actual regional placement, current costs,
authenticated identity and real clock uncertainty are not verified here. Its digest, selected target,
release/source/image/blueprint identities, store generation, operation identity
and declared authority deadline are immutable across transitions. They are
conformance declarations, not authenticated live receipts. No flag, raw token,
command, secret, provider body or unsigned source result is an authority input.

`operation_journal._parse_schema` now accepts an explicit `version` parameter,
limited to v1/v2. Its default remains v1; existing local schemas, records and
SQLite behavior are unchanged. The new v2 schemas use the same bounded reader,
duplicate-key checks, closed-object checks, local schema identity checks,
remote-reference refusals, canonical encoding and SHA256 helper. The selected
loader registers only the record, backend evidence and backend event schemas.

The pure `validate_transition(before, after, event=..., now_ms=...)` function
validates proposed snapshots; it performs no storage or effects. The injected
AWS store conformance adapter consumes it and supplies conditional storage and
independent evidence readback. Matching a formatted observation digest here
is insufficient: the backend must bind it to exact prior-record/image/operation,
expected assertion, current time and immutable evidence bytes before linking it.

Supported conformance events are `prepare`, `claim`, `renew`, `reserve`,
`mark-unknown`, `reconcile`, `observe`, `verify-cleanup`, `close`, and `block`.
A reservation consumes the single effect attempt before an external adapter
could act; it fixes request digest, owner/fence, time and credential deadline.
Normal observations require a current lease and budget. Closure requires the
ordered observation and cleanup states. Time moving backwards, short remaining
call budget, stale owner/fence/revision, changed identity and duplicate attempts
are refused. `fixture_record` and `next_record` construct inert test snapshots;
they are not a release command or a live execution controller.

After a lost response, `mark-unknown` preserves the reservation and spent attempt.
It may record this stricter diagnostic state after lease expiry. A different owner
can take a reconciliation-only lease after expiry, but cannot observe success,
replay an effect or claim cleanup through this seam. Even waiting for the declared
credential deadline does not clear uncertainty. The proof that old writers are
excluded and actual provider effects are terminal/absent belongs to the later
reviewed controller/authority adapter. This unit deliberately provides no such
clearing transition or reusable scope transition. It also performs no live clock
verification or controller orchestration. `block` also retains ownership evidence and attempt history;
the backend keeps the target scope occupied rather than treating it as reusable.

Run the focused local contracts with the existing gate Python dependencies:

```sh
python3 -B -m unittest discover -s scripts/04.deploy/operational-realization-gate -p 'test_selected_operation.py'
```

The canonical smoke wrapper registers this suite and the injected-backend
suite. No new public execution wrapper is needed for an internal shared seam.
Physical fixtures include one valid inert record and a forbidden authority claim.
Tests also exercise v1 compatibility, schema safety, policy/identity mutation,
expiry, interruption quarantine, cleanup ordering and source-result refusals.

Next delivery unit: integrate authenticated per-operation authority and current
source/artifact/provider observations into this same boundary; implement/prove
old-writer and unknown-effect reconciliation before exposing any live operation.
Shared AWS store creation, OIDC identity qualification, exact effect permissions,
existing caller migration, live interruption/restore rehearsal and all remaining
M4/M5 criteria remain open. No source test can substitute for those proofs.

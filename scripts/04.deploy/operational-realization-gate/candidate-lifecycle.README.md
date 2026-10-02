<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.candidate-lifecycle
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the selected candidate start-stop durable intent profile and its source-only boundary.
portability: {class: internal, targets: [kanbien-staging]}
used_by:
- id: deploy.script.candidate-lifecycle
  path: scripts/04.deploy/operational-realization-gate/candidate_lifecycle.py
-->

# Selected candidate lifecycle profile

This internal profile extends the existing durable action store; it is not a new
deployment framework or a public execution command. It accepts only the
candidate-server request from a valid selected-admission result and binds it
to one candidate image, cluster digest and task-revision digest.

Before an adapter can make either selected provider effect, it must obtain a
durable start or stop reservation from OperationActionStore. The reservation
event digest is the one request token. The adapter must recheck its lease,
composite revision and reservation immediately before dispatch through
action_budget; a repeated start, a stale writer, an expired lease or a lost
response is refused.

A returned observation contains only digests: the opaque task ID digest, cluster
digest, task-revision digest and image digest. The first task identity is fixed
for the attempt; stop must report the same task. A wrong identity or any
unrecognised field fails before it is recorded. Raw task identifiers,
credentials, endpoints and provider responses have no field in the contract.

The profile persists its attachment and reservations in the existing private,
single-host local-conformance store. It demonstrates restart recovery, fencing
and verified closure mechanics only. It always retains blocked release and
operation authority. It cannot call AWS or any provider, and
require_execution_authority always refuses. P08–P10 must add the selected
durable provider store, permissions and authenticated transport before a real
adapter can consume this protocol.

Focused verification:

```sh
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p 'test_candidate_lifecycle.py' -v
```

Next delivery unit: P08, the minimum selected journal/evidence-store
infrastructure contract. No infrastructure creation is included.

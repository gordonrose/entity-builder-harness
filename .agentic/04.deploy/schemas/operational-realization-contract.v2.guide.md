<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.operational-realization-contract.v2
version: 2
status: active
created_on: "2026-11-08"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: guide
purpose: Explain explicit synchronous workload relationships and direct-storage absence in realization contract v2 without granting provider permissions or weakening proof.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.schema.operational-realization-contract.v2
  path: .agentic/04.deploy/schemas/operational-realization-contract.v2.schema.yml
-->
# Realization contract v2: a client is not a database user

A private verifier can ask a feature server to create an entity without owning
the server's database credential or connection. Its real graph is:

`verifier → private-call connection → server → data connection → store`

Select `schema: operational-realization-contract/v2` to describe this graph.
The [v2 schema](operational-realization-contract.v2.schema.yml) extends the
retained [v1 field families and evidence format](../../01.harness/templates/operational-realization-contract.v1.guide.md).
Existing v1 contracts keep their previous admission rules and are not migrated
automatically. The numeric `version` is the document's own revision, not the
format discriminator.

## Describe the actual relationships

A connection's source is still its owning execution unit. Its destination can
now also be another execution unit, not only a store or channel. Declare both
`verifier → private-call` and `private-call → server` edges and bind the
connection in the verifier's `connections` list. An undeclared server, missing
edge, wrong component kind or another unit's connection is rejected.

`state_stores` means direct storage use. The verifier declares
`state_stores: []`; the server declares its store and a matching owned connection
to that store. An empty list says there is no direct relationship. A missing
list, null or a string does not. Adding a pretend store to the verifier fails
unless it also declares a real direct connection; omitting a store actually
reached by its connection also fails. A direct graph edge cannot bypass the
list. A callee's dependency is not a grant of database permission to its caller.

A unit with no outgoing connections explicitly declares `connections: []`.
A capability with no stores may declare top-level `state_stores: []` as well.
Every declared identity, configuration shape, artifact and recovery relationship
is still required. No queue or synthetic store is needed to satisfy the schema.

## Keep declarations separate from proof

For a separately governed disposable-restore cleanup, `change_shape` may opt in
with `disposable_restore_cleanup`. Declare its four fields from the
[schema](operational-realization-contract.v2.schema.yml) as true;
allow only `delete` and forbid exactly `create`, `update`, `replace` and
`broaden-permission`. Missing/null/false/extra fields reject. Without this explicit
v2 opt-in, delete remains prohibited, including for all retained v1 contracts.
This is not general teardown permission. The provider controller still needs the
original successful readback, positively owned disposable resources and explicit
concrete execution approval, protecting source and shared resources. All gates,
current normalized change counts and input-bound evidence remain required.

For the verifier, permissions and network reachability must be proven against
its own provider identity and private server route. The compiler cannot derive
effective permission from a logical category or a graph alone. Transport
security is still explicitly `verified` or `not-applicable`; this change does
not certify plaintext transport or waive the provider owner's network/TLS rules.

The existing evidence helper follows the connection to the called server and
its downstream components. Changed server configuration, store permissions or
image changes the dependent caller's evidence binding. The caller's identity
declaration is not modified. Exact immutable artifact proof can be reused only
where its existing stage-specific inputs still match; current observations and
every required component must still be present and valid.

Run the existing compiler with `--validate-contract` for graph validation.
Then use its unchanged normalized-facts format for the eight ordered gates.
Passing graph validation does not qualify an image, prove database semantics,
read AWS, approve a mutation or advance accepted state. Use the owning
[realization workflow](../workflows/operational-realization-gate.md).

The private-call regression is exercised through the actual compiler CLI in
[service-graph-test.py](../../../scripts/04.deploy/operational-realization-gate/service-graph-test.py).
Its facts are simulated and do not become live deployment receipts.

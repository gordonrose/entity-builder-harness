<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.script.operational-realization-gate.readme
  version: 3
  status: active
  created_on: "2026-09-27"
  updated_on: "2026-11-09"
  layer: 04.deploy
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: readme
  purpose: Map the source, boundary, inputs, and safe outputs of the Operational Realization Gate compiler.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Operational Realization Gate Compiler

Before a private verifier can call a feature server, we need an accurate map
of that call and the server's separate storage access. This compiler checks
the declared graph and its supplied proof; it does not discover dependencies,
grant permissions or perform a deployment.

## Source map

| File | Responsibility |
| --- | --- |
| `script.py` | Generic compiler for graph completeness, proof levels, gate order, lifecycle safety, strict normalized evidence, and provider leakage. It uses no provider SDK, CLI, resource type, or adapter import. |
| `script.sh` | Repository-root command wrapper. |
| `smoke-test.sh` | Deterministic positive and negative contract fixtures plus the core-boundary scan. |
| `service-graph-test.py` | Runs the actual compiler CLI against v2 service calls and explicit empty direct-storage lists, unsafe alternatives, retained v1 admission and downstream evidence invalidation. All observations are simulated. |
| `evidence-reuse-test.py` | Exercises freshness and immutable proof reuse through the actual CLI; no provider observations. |
| `fixtures/` | Safe, provider-neutral examples. They are tests of compiler behavior, not live target specifications. |

## Commands

```bash
npm run deployment:realization:validate -- --contract path/to/contract.yml --validate-contract
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml --through recovery
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml --through execution-preflight
npm run deployment:realization:test
```

Use `--through execution-preflight` before a proposed controlled execution;
the compiler then requires passing evidence for every preceding gate. The
compiler emits only a stable result schema, contract ID, validation scope,
verdict, and safe finding codes. It does not open a network connection or
invoke a provider.

## Choosing the contract version

Existing `operational-realization-contract/v1` declarations keep their previous
rules. Select [v2](../../../.agentic/04.deploy/schemas/operational-realization-contract.v2.guide.md)
for `verifier → connection → server → connection → store`. The verifier's
`state_stores: []` says it does not access storage directly. The server declares
its store and matching connection. The compiler rejects a missing list, an
invented direct store, another unit's connection or an undeclared destination.
Explicit empty outgoing connection and top-level store lists are also valid in
v2; they do not waive artifact, identity, configuration or recovery declarations.

The [private-service fixture](fixtures/private-service-contract.v2.yml) is a
complete invented example, not the deployed feature's contract. Contract-only
validation returns a passed result with `scope: contract` and no findings. It
does not establish any of the eight proof gates. Supplying simulated facts
tests compiler behaviour, not provider state. In a real chain, a provider-owned
adapter must prove the verifier's separate identity/network boundary and all
other declared components.

Changing the called server's configuration, permissions, connection, store or
image invalidates dependent verifier evidence through the existing transitive
binding. It does not copy the server's permissions into the verifier identity.
All existing gate ordering, freshness, immutable binding and reviewed recovery
requirements remain enforced. The regression uses the actual CLI to reject
stale dependent evidence and separately proves unchanged artifact-gate reuse.

## Adapter boundary

An isolated restore is disposable only after the original restored record has
been read successfully and its resources are positively owned. For that
separately governed cleanup, v2 accepts the exact
`change_shape.disposable_restore_cleanup` declaration described in the
[schema guide](../../../.agentic/04.deploy/schemas/operational-realization-contract.v2.guide.md).
It allows only `delete`, while create/update/replace/permission broadening remain
forbidden. Missing, incomplete, false or extra fields fail `change-shape-invalid`;
ordinary v2 and all v1 declarations still forbid delete. The CLI fixture tests
both alternatives and rejects forbidden counts or missing gate evidence.

The declaration does not prove ownership/readback or approve deletion. The
provider-owned controller must require those facts and separate concrete
execution approval. All existing normalized evidence and ordering checks remain.

A provider adapter is responsible for converting a provider inspection or plan
into one of the two normalized input documents. The compiler accepts only
generic component bindings, check IDs, UTC timestamps, gate verdicts, recovery
attempt relationships, and operation-class counts. Unknown fields—including
raw provider data and secret-like names—fail closed. Adapter code must live
outside this directory and must be tested independently.

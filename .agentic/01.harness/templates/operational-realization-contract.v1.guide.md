<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.guide.operational-realization-contract.v1
  version: 2
  status: active
  layer: 01.harness
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: guide
  purpose: Explain how to declare and safely evidence a provider-neutral Operational Realization contract.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: harness.schema.operational-realization-contract.v1
    path: .agentic/01.harness/templates/operational-realization-contract.v1.schema.yml
  - id: harness.workflow.operational-realization-gate
    path: .agentic/01.harness/workflows/operational-realization-gate.md
-->
# Operational Realization Contract v1 Guide

## Mental model

The contract is a provider-neutral map of one capability's real execution
route. It declares what runs, under which identity, with which safe
configuration shape, across which typed connections, state stores and work
channels, and how a terminal attempt can be recovered without replay.

The generic contract contains stable IDs and safe categories only. A
provider-specific adapter independently inspects a target and emits normalized
facts that bind each declared component and gate to a check ID and UTC
timestamp. It must never put a provider response, endpoint, credential,
request body, row, message, or raw value into those facts.

## Field families

| Family | What it answers | Safety rule |
| --- | --- | --- |
| Artifact and execution unit | What exact reviewed payload runs and which components it uses. | Artifact reference is content-addressed; every unit reference has a graph edge. |
| Identity, configuration, and connection | Who runs and what it may safely connect to. | Declare permission categories and field names, never credential or endpoint values. Connection source must be an execution unit; destination is a declared state store or channel, with an explicit directional edge for each end. |
| State and asynchronous work | Where durable state lives and who produces or consumes work. | State and channel relationships are explicit. A channel needs producer, consumers, delivery semantics, acknowledgement, and idempotency boundary. |
| Lifecycle and recovery | What happens after success, failure, or a stop. | A terminal attempt never reopens. Recovery has a new immutable attempt label and a failed/stopped predecessor. |
| Evidence and change summary | Why it is safe to proceed. | Exact allowlisted fields only: stable IDs, check IDs, UTC timestamps, passed verdicts, and aggregate operation counts. |

## Good and bad evidence

Good normalized gate evidence has only a gate name, stable check ID, UTC
timestamp, and verdict. Good component evidence also names the declared
component ID and its generic kind. A good recovery record names a failed or
stopped predecessor attempt and a different recovery attempt label.

Write a YAML timestamp as a quoted UTC string, for example
`"2026-09-27T00:00:00Z"`, so the input remains the exact safe string the
compiler verifies rather than a YAML date value.

Bad evidence contains an endpoint, token, raw error, provider response, task
identifier, SQL, request body, message, or record value. The compiler rejects
unknown fields and unsafe field names so it cannot silently become a data
transport channel.

## How to use it

1. Copy the template and replace every placeholder with stable,
   provider-neutral identifiers.
   A unit that does not produce or consume asynchronous work must declare
   `async_channels: []`; it must not claim a channel merely to satisfy the
   schema.
2. Run `npm run deployment:realization:validate -- --contract <path>
   --validate-contract` before any target operation is proposed.
3. Have the target-owned adapter emit only normalized facts and a normalized
   change summary. Run the compiler through the exact next gate.
4. Treat a compiler failure as a stop for that gate. Do not alter a fact,
   identity, or live target merely to make a result pass.

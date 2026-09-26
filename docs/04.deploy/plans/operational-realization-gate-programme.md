<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.plan.operational-realization-gate-programme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: plan
  purpose: Stage the provider-neutral harness that proves complete operational realization before live deployment work.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: deploy.plans.readme
    path: docs/04.deploy/plans/README.md
-->
# Operational Realization Gate Programme

## Objective

Replace deployment-time discovery with a reusable, provider-neutral proof gate.
The gate treats a capability as a connected execution graph rather than a
collection of individually valid source files or cloud resources.

## Scope

This programme owns generic contracts, validation, evidence sequencing, and
adapter boundaries. It does not create provider resources, broaden a target
role, or replace target-specific deployment authority.

## Delivery stages

| Stage | Outcome | Completion evidence |
| --- | --- | --- |
| 1 | Versioned contract, standard, workflow, template, and schema define complete execution graphs. | Static schema and template check. |
| 2 | Generic compiler rejects unknown assumptions, undeclared edges, unsafe retries, insufficient proof, and provider leakage. | Deterministic fixtures. |
| 3 | Normalized-facts/change-summary boundary prevents provider SDKs and resource types entering generic code. | Core boundary test and documented adapter handoff. |
| 4 | Provider-specific target programmes map their existing collectors into an adapter without changing the generic core. | Target-owned realization contract and safe adapter evidence. |
| 5 | One controlled capability proof passes all gate stages, including labelled recovery. | Append-only safe evidence and target readiness update. |

## PostgreSQL relational-reference migration

The current Kanbien staging relational-reference Stage 6 must not resume from a
direct target-specific retry. It first migrates into Stage 4 of this programme:
its source describes the full route in a realization contract, target
collectors become a separate adapter that emits normalized facts/change
summaries, and the compiler passes before a new target-specific execution plan
is requested. Existing source and live evidence may be cited only where its
contracted proof level is satisfied; it is not grandfathered as a bypass.

## Guardrails

- The core never receives credentials, provider responses, endpoint values,
  task identifiers, request bodies, records, or queue messages.
- A provider adapter cannot confer live authority; the target execution
  workflow remains separately approved.
- A failed first execution is terminal. A recovery uses a new label and all
  prerequisite gate evidence, never an implicit replay.
- No source plan implies provider mutation authority.

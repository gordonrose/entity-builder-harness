<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.target-alignment-preflight
version: 1
status: draft
created_on: "2026-10-06"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- agentic
- architecture
- security
- sre
kind: standard
purpose: Define the provider-neutral safety and comparison requirements for target alignment before deployable work begins.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.workflow.target-alignment-preflight
  path: .agentic/04.deploy/00-target-alignment/workflows/compare-declared-requirements-with-live-target.md
- id: deploy.script.target-alignment-preflight.readme
  path: scripts/04.deploy/lifecycle/00-target-alignment/target-alignment-preflight/README.md
-->
# Require Fresh, Safe Target Evidence

## Purpose

Target Alignment Preflight compares declared local requirements with safe,
fresh facts from the selected deployment target. It happens after task framing
selects a target and before implementation of deployable work begins. It is
repeated immediately before a target mutation because target state can change
while work is in progress.

It consumes a Declaration Coverage result and its bounded declaration contract.
It must not invent target assertions outside that covered contract.

This standard does not grant provider access or target-mutation authority. A
provider-specific adapter owns how facts are collected and must retain the
provider's existing inspection and approval controls.

## Requirements

The comparison must declare an expected local value, an observed target fact,
its collection time, a bounded freshness period, and one of these outcomes:
`match`, `mismatch`, `missing`, or `unknown`.

`mismatch`, `missing`, and `unknown` fail closed. A stale fact is `unknown`.
No output may contain secret values, tokens, request or response bodies, raw
provider responses, customer data, or an unrestricted resource inventory.

Every preflight must compare these baseline assertions:

| Assertion | Local declaration | Target fact |
| --- | --- | --- |
| right destination | provider, account or tenancy boundary, region, environment | selected provider identity and location match |
| right application | service or workload identity | selected workload matches the declared application |
| known healthy baseline | accepted starting health policy | current health is within that policy |
| allowed deployment route | approved publisher and target-mutation route | route and identity remain available and scoped |
| package destination | artifact store and immutable-reference policy | package destination exists and applies the declared protection |
| required access | least-privilege action and resource contract | declared inspection/deployment identity remains aligned |
| required settings | configuration-key and secret-reference shape | required references are present; values are never read or emitted |
| change safety | rollback or recovery declaration | a declared recovery path remains usable for the proposed change |
| freshness and drift | evidence-age and drift policy | evidence is fresh and any required drift status is acceptable |

The preflight may add dependency assertions only when the selected work affects
that dependency. Examples include identity, ingress, database, queue, cache,
or observability checks. It must not make unrelated provider reads merely
because they are available.

## Local-Target Boundary

Alignment means the local requirements and the target contract agree. It does
not mean a laptop duplicates a cloud environment. Local checks establish the
declared runtime, package shape, configuration-reference shape, and supported
release route; target checks establish that the named destination currently
accepts those requirements.

## Provider Adapter Boundary

A provider adapter must:

- accept only the selected target and the declared assertion set;
- make bounded read-only calls under its provider's inspection workflow;
- normalize results to assertion IDs, outcomes, freshness, and safe finding
  codes;
- reject caller-supplied arbitrary resource queries, routes, credentials, or
  secret reads; and
- stop before a provider mutation or an ungoverned recovery action.

AWS inspection remains governed by `.agentic/aws/workflows/inspect-aws-state.md`.
An AWS adapter may be introduced only for a fixed declared assertion set. It
must normalize provider output before the generic validator receives it, and a
target wrapper must bind the profile, region, account, stack and resource names
without accepting user-supplied selectors.

## Evidence

Retain only a safe summary: target profile or contract reference, source
revision, assertion IDs, outcomes, timestamps, freshness result, provider
adapter version, and a non-secret evidence reference. Session logs may record
that summary but are not the source of the workflow or standard.

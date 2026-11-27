<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.adr.0044-use-database-reminders-with-bounded-job-execution
version: 1
status: active
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 03.product
domain: scheduling
disciplines: [architecture, security, sre]
kind: adr
purpose: Record durable database reminders, bounded execution and independent application composition for the first reusable scheduler.
portability: { class: source-only, targets: [] }
used_by:
- id: product.plan.reusable-aws-scheduling
  path: .agentic/03.product/plans/implementation/reusable-aws-scheduling.md
-->
# ADR 0044 Use Database Reminders With Bounded Job Execution

## Status

Accepted design, following the user's A2 selection on 2026-11-26.
Implementation and deployment acceptance remain tracked in the
[scheduler implementation plan](../../../.agentic/03.product/plans/implementation/reusable-aws-scheduling.md).

## Context

The repository already has PostgreSQL persistence, an outbox for recording work
that must be delivered, and workers for executing registered application jobs.
The scheduler needs to reuse these pieces without making ordinary app features
depend on an AWS service or an always-running scheduling process.

A job definition says what code can run. A reminder is a durable database row
saying which job should run and when. Keeping these separate lets each deployed
application register only its own supported jobs while retaining reminders
across restarts and temporary delivery failures.

The initial application example deletes a specifically identified synthetic
Entity Smoke record after its retention and recovery periods have elapsed.
The platform baseline performs harmless work independently of that feature.
The choice prioritizes operating cost with an existing database, but additional
private networking, execution duration and traffic still affect that cost.

## Decision

PostgreSQL holds one-off reminders and their delivery state. Application state
changes and creation of a required reminder share one database transaction.
When a reminder becomes due, another transaction records its outbox obligation
and delivery state together. The existing relay sends pending obligations to
the queue, including obligations left by interrupted earlier passes.

The AWS realization uses a fixed infrastructure-owned EventBridge Scheduler
trigger to invoke a short-lived Lambda dispatcher. SQS invokes a separately
composed Lambda worker for queued jobs. This is A2: database timing with
short-lived execution. It is not an AWS schedule resource for every reminder;
ordinary application code therefore needs no EventBridge schedule CRUD adapter.

Delivery may repeat. The existing durable processing record owns attempts,
retry timing, leases and completion. Queue acknowledgment follows confirmed
durable success; an uncertain result stays eligible for safe recovery.
Application operations also guard their effects: Entity Smoke checks the exact
record and deletion generation at the final conditional delete. This design
does not promise exactly-once execution.

Each invocation has bounded work and cooperative deadline checks. Dependency
timeouts bound work already in progress. Invalid reminders and unavailable jobs
have explicit blocked states instead of indefinitely preventing later work.
Recovery preserves recorded state rather than treating memory or an external
queue delivery count as the sole retry authority.

Apps expose jobs through their public mount, with app and feature ownership in
job names. Deployment composition selects the relevant app definitions and
provider adapters; a platform module does not contain every product's business
logic. The baseline and Entity Smoke have independent images and runtime
identities. Neither requires an application to inherit a core-platform image
or target.

The first slice schedules absolute instants, normalized to UTC through existing
Core time contracts. An elapsed retention duration is not a local calendar
recurrence. Timezone rules, daylight-saving transitions and recurring calendar
schedules remain a separate design.

## Consequences

The durable reminder, outbox and processing records make interruption and
repeated delivery inspectable without introducing a second work registry or
retry store. A fixed wake-up interval also means dispatch is not an exact
second-level alarm; due time and actual completion time are distinct.

Short-lived execution removes the need for a dedicated idle scheduling service.
It is not unconditionally the cheapest option: private endpoint charges,
database capacity, logs, queue traffic and function duration must fit the
target's cost budget. The implementation plan owns measured assumptions and
acceptance limits, rather than freezing current prices into this decision.

[ADR 0027](0027-use-provider-type-service-adapter-layout.md) continues to govern
adapter placement and infrastructure ownership. Network, IAM, functions and
triggers belong to deployment. A new private endpoint must preserve other
consumers of shared networking; a disabled trigger does not make a VPC-wide DNS
change harmless. The currently drafted shared endpoint is not authorized for
creation merely by accepting A2.

## Non Goals

This decision does not establish a general tenant retention policy engine,
authorize deletion of unrelated data, or implement calendar scheduling.
It does not replace package qualification, live runtime proof, scoped cloud
authorization, or the independent acceptance process.

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.03-product.platform-target-alerting-policy
version: 1
status: active
layer: 04.deploy
domain: infra.observability
disciplines:
- architecture
- security
- sre
kind: source-material
purpose: Define the canonical, target-owned alarm-policy convention for product platform services.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.rules.03-product.platform-target-alerting-policy
  path: docs/04.deploy/rules/03.product/platform-target-alerting-policy.yml
-->
# Platform Target Alerting Policy

## Purpose

This standard makes an alarm policy understandable in one place before a
cloud template, console, or incident has to be searched. It applies to a
product platform deployment target that exposes a service or background
runtime and therefore needs an operational response to failure.

It does not choose CloudWatch, an email provider, a paging tool, or an alarm
threshold for every future target. Those are target decisions. It defines the
minimum evidence a target must record when it does choose an alarm.

## Source of Truth and Catalogue

Each deployment target owns exactly one canonical alarm catalogue at:

```text
infra/04.deploy/03.product/targets/<client>/<environment>/target-profile.yml
  observability.alarms
```

The repository-wide target index at
`infra/04.deploy/03.product/targets/README.md` links to every target catalogue
and its implementation/runbook. It is an index, not a second policy store: it
must never repeat thresholds, dimensions, or delivery settings.

CloudFormation, Terraform, or another infrastructure implementation translates
the target policy into provider resources. A static or deployment-time check
must compare the implementation with the policy before the target is treated
as ready. A provider console is evidence of live state, not the canonical
policy source.

## Required Alarm Definition

Every item in `observability.alarms` must answer these questions:

| Field | Question answered | Why it is required |
| --- | --- | --- |
| `id` and `purpose` | What concern is this rule for? | A stable identifier prevents duplicate, ambiguous alarms. |
| `signal` | What metric and exact resource dimensions are evaluated? | An alarm without dimensions can monitor an unrelated service in a shared account. |
| `condition` | What measurement, comparison, threshold, and unit mean unhealthy? | A number alone has no operational meaning. |
| `evaluation` | For how long, and what does missing data mean? | This controls noise and prevents silent blind spots. |
| `response` | Who receives it, how urgent is it, and which runbook is used? | An unowned alarm is a dashboard decoration, not an operational control. |
| `implementation` | Which IaC owner creates it and what is its provider identity? | This permits deterministic policy-to-resource drift checks. |

If a signal depends on optional telemetry, the target must declare that in
`observability.telemetry_prerequisites`, name the check that proves it, and
block the dependent infrastructure update when the prerequisite is absent.

## Ownership and Boundaries

- The target profile owns the complete policy for that client and environment.
- The stack that owns a metric's resource dimensions owns the provider alarm
  resource. A shared ALB alarm may therefore live in a foundation stack while
  an ECS service alarm lives in a service stack.
- `packages/core` may name provider-neutral health and monitoring signals, but
  it must not define provider alarms, thresholds, notification destinations, or
  incident routes.
- Platform code emits safe operational telemetry through its contracts and
  adapters. Infrastructure provisions concrete alarm and delivery resources.
- A runbook owns safe first diagnosis. It must not ask an operator to copy raw
  request bodies, credentials, tokens, customer records, prompts, or other
  sensitive payloads into a ticket or repository record.

## Definition Rules

An alarm policy must:

- use a stable, semantic `id`, not a provider-generated identifier;
- select bounded dimensions that identify the intended resource;
- name the statistic, comparison operator, threshold source/value, and unit;
- name period length, evaluation periods, datapoints to alarm, and
  `treat_missing_data` explicitly;
- use a named severity from the target's supported vocabulary and a named,
  owned notification destination;
- link a version-controlled runbook; and
- name the stack, logical resource, provider alarm name, and human-safe
  description used to verify the implementation.

An alarm policy must not:

- put tokens, credentials, raw requests/responses, customer data, prompts,
  transcripts, or signed URLs in an alarm description, tag, dimension, or
  notification payload;
- use tenant, user, request, trace, session, email, IP address, or unbounded
  route values as a metric dimension;
- treat a syntactically valid provider alarm as proof that its source metric,
  notification route, or operator response exists; or
- silently lower or remove an alarm because its prerequisite has not yet been
  provisioned. Record a blocking readiness gap instead.

## Lifecycle

1. Define the concern and required signal in the target profile.
2. Confirm the telemetry prerequisite and notification destination through
   read-only preflight evidence.
3. Implement the provider resource in the stack that owns the dimensions.
4. Run a policy-to-IaC drift check before deployment.
5. Verify live state and notification delivery without recording sensitive
   delivery details in the repository.
6. Review thresholds, ownership, runbook, and retention when the service's
   traffic, topology, or risk changes.

## Non-Goals

This standard does not make every alert a paging event, prescribe a universal
threshold, or replace application logs, traces, audit records, security
records, capacity planning, budget alarms, or human incident judgement.

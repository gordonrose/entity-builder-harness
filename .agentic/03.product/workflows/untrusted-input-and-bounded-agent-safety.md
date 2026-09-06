<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.workflow.untrusted-input-and-bounded-agent-safety
version: 1
status: active
layer: 03.product
domain: security
disciplines:
- architecture
- security
- agentic
kind: workflow
purpose: Govern product changes that introduce untrusted-input interpreter boundaries or bounded agent capabilities.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.architecture.rules.concerns.untrusted-input-and-bounded-agent-safety
  path: docs/03.product/rules/concerns/untrusted-input-and-bounded-agent-safety.yml
- id: product.plan.product-harness-foundation
  path: .agentic/03.product/plans/implementation/product-harness-foundation.md
-->
# Untrusted Input and Bounded Agent Safety Workflow

## Use When

Use this workflow before adding or materially changing code that:

- accepts untrusted data at an interpreter boundary, such as a query, process,
  template, browser-rendering, file-path, deserialization, network, or dynamic
  execution boundary;
- introduces an LLM, agent, prompt, retrieval flow, automated remediation, or
  model-facing tool;
- lets an automated capability read or change tenant, customer, financial,
  identity, security, infrastructure, or other sensitive data; or
- changes the authority, approval, audit, rate-limit, retry, or kill-switch
  behaviour of such a capability.

This workflow governs local product/runtime design and proof. It does not
authorize cloud mutation, production credentials, provider selection, tenant
policy changes, or deployment actions.

## Required Inputs

Before implementation, record the following in the change plan or task
evidence:

1. The named capability and its exact business purpose.
2. Every untrusted input source and the boundary where it is parsed, rendered,
   queried, executed, retrieved, or given to a model.
3. The verified principal, service identity, tenant, product, environment, and
   permission/resource-policy context the capability requires.
4. Each proposed tool or action: structured input schema, read/write scope,
   data classification, permitted resource types, tenant scope, and expected
   output classification.
5. Whether each action is read-only, reversible, or consequential, plus its
   allowlist, idempotency/replay, timeout, rate-limit, audit, kill-switch, and
   approval requirements.
6. The focused negative tests that will prove hostile content, malformed input,
   denied authority, cross-tenant requests, sensitive-data handling, and absent
   approval cannot produce an unsafe result.

## Required First Move

1. Read [the canonical concern rule](../../../docs/03.product/rules/concerns/untrusted-input-and-bounded-agent-safety.yml).
2. Read the applicable identity, tenancy, audit, dependency, and provider
   boundary rules.
3. Identify the current capability maturity. Do not present a planned platform
   seam as a usable general agent runtime or approval service.
4. State the bounded file scope and the exact negative proof expected.
5. Stop if a required authority, tenant, resource policy, approval, audit, or
   safe-tool seam is absent; record a bounded platform/product gap instead.

## Design Rules

- Treat untrusted content as data. Retrieved text can inform a proposal but
  cannot modify policy, verified context, tenant scope, permissions, tool
  definitions, approval requirements, or higher-priority instructions.
- Keep interpreter boundaries typed: validate at entry, parameterize database
  operations, encode output for its destination, and do not route untrusted or
  model-generated text into general code, command, query, template, file,
  network, or infrastructure execution.
- Give an agent a narrow named purpose and the least set of declared tools.
  Separate investigation from state-changing capability.
- A tool independently validates typed arguments and verified principal,
  service, tenant, permission, resource, and product policy. It must deny if a
  required fact is absent; it must never trust a model assertion of authority.
- Filter retrieval before the model sees content. Preserve provenance, minimize
  prompt/tool data, and redact values according to classification policy.
- Treat financial, destructive, cross-tenant, security/identity-policy,
  infrastructure, and data-export actions as human-approved unless an explicit
  later policy establishes a narrower automated case.

## Required Proof

<!-- deterministic-check: allow reason="selecting the narrowest relevant proof requires human assessment of the changed trust boundary; package scripts enforce the selected checks" -->
Run the narrowest tests and checks that demonstrate the changed boundary.
Relevant proof must include positive and negative cases:

- hostile retrieved text cannot select an undeclared tool, elevate its task, or
  widen an authenticated principal's authority;
- malformed model/tool or ordinary caller arguments are rejected before any
  side effect;
- unauthorized identity, service, tenant, group, role, permission, or
  resource context is denied by the tool itself;
- another tenant's data cannot be retrieved, inferred from tool output, or
  affected by an action;
- secrets and unnecessary sensitive values do not enter prompts, tool results,
  logs, or safe errors; and
- missing approval, timeouts, retries, rate limits, kill switches, and audit
  failures have the declared safe outcome where the change makes them relevant.

## Stop Conditions

Stop and record a bounded gap rather than improvise if:

- a model would need arbitrary code, query, shell, file, network, cloud, or
  administrator access;
- verified principal, service, tenant, permission, resource, or approval facts
  cannot reach the proposed tool boundary;
- a retrieval path cannot filter access before exposing material to the model;
<!-- deterministic-check: allow reason="whether an approval or allowlist path is sufficient requires product and risk judgment; no generic script can determine that policy fact" -->
- the action is cross-tenant, financial, destructive, policy-changing,
  infrastructure-changing, or data-exporting and no explicit approval/allowlist
  path exists;
- the required negative proof cannot be run and no governed gap record can
  explain what is missing; or
- the request would require production cloud mutation, real credentials, or a
  provider/runtime decision outside approved target composition.

## Output

Close a change with:

- the input/trust-boundary map;
- the declared tools and their least-privilege scope;
- authority, tenant, resource-policy, and approval decisions;
- prompt/retrieval data-minimization and provenance treatment;
- adversarial and ordinary negative proof results;
- audit, rate-limit, timeout, retry, and kill-switch evidence where relevant;
- current gaps and work intentionally deferred; and
- confirmation that no raw secret, customer payload, or production credential
  was added to code, prompts, logs, fixtures, or harness material.

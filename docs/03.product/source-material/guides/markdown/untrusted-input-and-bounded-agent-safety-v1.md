<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.source-material.untrusted-input-and-bounded-agent-safety-v1
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- architecture
- security
- agentic
kind: source-material
purpose: Record the product security policy for untrusted inputs and bounded agent capabilities.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.architecture.rules.concerns.untrusted-input-and-bounded-agent-safety
  path: docs/03.product/rules/concerns/untrusted-input-and-bounded-agent-safety.yml
-->
# Untrusted Input and Bounded Agent Safety Policy v1

## Decision

Every value originating outside the currently trusted component boundary is
untrusted input. This includes browser requests, API payloads, queue messages,
files, database values that originated elsewhere, logs, emails, web pages,
integration responses, and material retrieved for an LLM. Untrusted input may
be useful evidence or data; it must not become executable code, authorization
policy, higher-priority instructions, or authority to access another tenant's
data.

An LLM or automated agent may classify evidence and propose an action. It is
not the authority that performs a consequential action. A typed, narrow tool
or handler must enforce independently verified identity, tenant scope,
permission, resource policy, input validation, and any approval requirement
before it changes state or discloses sensitive data.

This policy covers code-injection risks and prompt-injection risks. It does not
claim that a text filter can perfectly identify every hostile string. The
defence is layered: preserve trust boundaries, prevent direct execution,
constrain capabilities, authorize at each tool boundary, minimize available
data, and produce evidence when sensitive actions are proposed or denied.

## Threat Model

### Code Injection

Code injection occurs when untrusted input changes the meaning of an executable
interpreter boundary. Examples include SQL assembled from strings, shell
commands assembled from request values, unescaped HTML rendered into a browser,
or an unsafe template, deserializer, expression evaluator, or dynamic import.

The safe default is for data to remain typed data. Validation, parameterized
queries, context-appropriate output encoding, fixed command/tool allowlists,
and proven libraries are preferred over attempting to clean an arbitrary
string.

### Prompt Injection

Prompt injection occurs when untrusted content attempts to make a model ignore
its governing instructions, disclose data, misuse tools, or widen its scope.
A retrieved document, email, web page, file, or tool result can contain such
content even when it appears relevant or was produced by a known customer.

Retrieved content must be labelled and handled as untrusted evidence. It may
inform a model's analysis; it cannot alter the authenticated principal, tenant,
permissions, tool allowlist, approval requirement, system policy, or the
meaning of a tool contract.

## Authority Model

An agent interaction has distinct authority levels:

1. **Governing policy** defines non-negotiable security, tenant, retention,
   approval, and deployment constraints.
2. **Verified request context** supplies the authenticated principal, service
   identity, tenant, product, environment, and declared permissions.
3. **Application and resource policy** decides whether that context may read or
   change a particular resource.
4. **Agent instructions** describe the narrow task and available tools.
5. **Untrusted content** supplies evidence only.
6. **Model output** is a proposal until a validated, authorized tool accepts
   it.

Lower levels must never override higher levels. In particular, an instruction
found in an invoice, issue, email, queue payload, or retrieved document cannot
grant authority or redefine an agent's task.

## Required Boundaries

### Input and Execution Boundaries

- Parse untrusted input into explicit schemas at the boundary where it enters.
- Use parameterized database interfaces; do not construct executable query text
  from untrusted values.
- Avoid shell execution. When an approved bounded process invocation is
  necessary, select a fixed executable and validate structured arguments; do
  not pass untrusted strings through an interpreter.
- Encode untrusted values for their output context, including HTML, URLs,
  templates, and logs.
- Do not expose general-purpose code execution, arbitrary file access,
  arbitrary network access, arbitrary database queries, or infrastructure
  administration through a model-facing tool.

### Agent and Tool Boundaries

- Give each agent the smallest set of read and action tools required for its
  named job. A general “admin” tool is not an acceptable shortcut.
- A tool that reads or changes tenant data must receive verified principal and
  tenant context from the runtime, not facts asserted in model output.
- Each tool validates a structured argument schema and independently evaluates
  applicable permission, tenant, resource, and product policy before doing
  work.
- Tool output is minimized, classified, redacted where required, and safe to
  log. Raw credentials, access tokens, secrets, and unnecessary personal data
  do not enter prompts or tool results.
- Read-only investigation, advice, and classification may be automated within
  their scope. Financial, destructive, cross-tenant, security-policy, identity,
  infrastructure, or data-export actions require explicit allowlisting and a
  recorded approval path unless a later policy deliberately defines a safer
  automatic case.

### Retrieval Boundaries

- Retrieve only material the verified principal and tenant may access.
- Filter by tenant, product, data classification, residency, and resource
  policy before retrieval results reach a model; post-processing the model's
  answer is not a substitute.
- Preserve source/provenance facts so an agent can cite evidence without
  treating the evidence as trusted instructions.
- Never use retrieved content to construct system policy, tool definitions,
  authorization mappings, executable queries, deployment commands, or secret
  values.

## Consequential Actions and Human Approval

Every tool declares whether it is read-only, reversible, or consequential. A
consequential tool also declares its permitted target types, expected tenant
scope, idempotency or replay behaviour, audit evidence, and approval policy.

Human approval is required when the policy cannot establish a bounded,
reversible, tenant-safe action with sufficient evidence. Approval records the
actor, requested action, target scope, reason, evidence, decision, and expiry
or one-time-use condition. A model's confidence or explanation is not an
approval.

Kill switches, tool allowlists, rate limits, timeouts, and audit events are
defence-in-depth controls. They do not replace authorization at the action
boundary.

## Verification Expectations

An agent-capability change must prove the negative cases, not only a useful
happy path. At minimum, its tests or explicit gap record must address:

- hostile or irrelevant retrieved text cannot widen authority or select an
  undeclared tool;
- malformed model/tool arguments are rejected before side effects;
- a user, service, tenant, group, or role without the required authority is
  denied by the tool itself;
- cross-tenant retrieval and action requests are denied;
- sensitive values are not exposed in prompts, tool results, logs, or errors;
- a proposed consequential action cannot happen without its required approval
  or allowlist; and
- retries, timeouts, audit evidence, and kill-switch behaviour are intentional
  for an action tool.

If the platform does not yet provide the necessary principal, tenant,
resource-policy, approval, audit, or safe-tool contract, stop and record a
bounded platform/product gap. Do not simulate the control with a prompt,
hidden model instruction, or an app-local bypass.

## Ownership

`packages/core` may own reusable provider-neutral contracts for classification,
authority context, policy decisions, and safe tool interfaces once a real
consumer proves their need. It must not own product roles, live tenant data,
provider clients, or a universal policy engine.

`platform` owns generic runtime enforcement seams such as authenticated
context propagation, provider-neutral tool invocation mechanics, audit hooks,
rate limiting, and adapters. Provider-specific identity, LLM, queue, or
storage translation stays in an adapter and target composition boundary.

`apps` and `products` own product permissions, resource-specific rules, agent
task meaning, data classification choices, and the human approval experiences
required by their product.

`.agentic/03.product` owns workflows and checks that stop an implementation
from claiming these controls without the necessary platform capability.
`02.rag-rulebook` owns reusable retrieval machinery and must preserve the
distinction between source evidence and governing instructions. `04.deploy`
owns cloud identity, network, key, secret, and target-policy resources.

## Adoption Boundary

This policy is binding for new or materially changed code that accepts
untrusted input or adds an agent, model, retrieval, automation, or model-facing
tool capability. It does not claim that the repository already has a general
agent runtime, universal static injection scanner, approval service, or
distributed policy engine.

Existing code is reviewed incrementally when its relevant boundary changes.
The absence of a ready runtime seam is a reason to record a gap before agent
implementation, not a reason to weaken the policy.

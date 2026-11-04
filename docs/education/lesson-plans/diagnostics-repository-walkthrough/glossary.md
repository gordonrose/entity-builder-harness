<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.glossary
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Explain diagnostic and repository terms in plain language.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Terms we will use

[Course start](README.md)

You do not need to learn this list before the course. We will explain a term when we first need it.

## Diagnostic

A structured observation intended to help identify what happened and what to investigate next. It is not necessarily a log line, a root-cause verdict or proof of recovery.

## Observability

The broader ability to understand system behavior using logs, metrics, traces, health and related evidence. This project improved diagnostic adoption within an observability system that already existed.

## Predicate

A yes/no condition the code checks: for example, whether a setting is present. A precise reason must follow a condition actually evaluated.

## Boundary

A place where code calls something whose behavior it does not fully control: a provider, callback, clock, logger or parser. A boundary failure identifies location; it does not automatically establish root cause.

## Definition / schema

A definition names a diagnostic and its meaning; its schema states which detail shapes/values are allowed. A TypeScript type alone does not validate runtime data.

## Record

One observation referring to a definition by code and version, with validated detail.

## Closed / finite / allowlist

Only declared fields or allowed values are accepted. A free-form string is not automatically safe just because it is short.

## Classification

The definition's declared category, severity and recovery guidance. It must not invent a more specific supported cause than the producer actually observed.

## Catalog

The explicitly selected collection of diagnostic definitions that a caller/reporter/reader understands.

## Primary and companions

The main source diagnostic plus bounded related observations. Retaining a local boundary observation must not erase valid upstream evidence.

## Own data property / getter

An own data property stores a value directly on an object. A getter runs code when read; diagnostics avoid executing arbitrary getters merely to inspect exception evidence.

## Port / adapter

A port is a small interface, such as Logger or a persistence writer. An adapter implements that interface for a concrete provider.

## Composition / binding

Wiring reusable pieces into a concrete app or target: settings, adapters, selected catalogs and reporters. This is where exact environment names belong.

## Entrypoint / one-shot program

An entrypoint starts a program. A one-shot task does a bounded operation, such as migration or verification, then exits rather than serving HTTP indefinitely.

## Throw / rejection / returned failure

A synchronous exception, a promise rejection and an ordinary failure result are different execution paths. Diagnostics preserve whichever the original API uses.

## Thenable

An object with a then function that behaves like an asynchronous result. Observing its rejection must not make business code wait or replay work.

## Effect / uncertainty

What is known about progress or side effects. “Invoked but did not return” is weaker than “never invoked” and does not prove rollback.

## Correlation ID

A bounded identifier connecting related observations. It is not a reason to expose user or tenant IDs, and must not become a high-cardinality shared metric label.

## Cardinality

The number of different label values a metric can produce. User IDs or raw URLs can create enormous series counts and disclose private data.

## TLS / certificate / trust

TLS protects a connection. A certificate carries identity/key assertions. Parsing its syntax is only one step; peer identity, trust chain and policy checks are separate.

## JWT / JWKS / CORS

A JWT is a structured token. JWKS is a set of public verification keys. CORS is a browser cross-origin response policy. None is interchangeable with a general authorization policy.

## IAM / RDS

AWS identity-and-access management and its managed relational database service. Target IAM token authentication is not the same thing as an injected administrator password.

## Outbox / relay / settlement

An outbox persists work for later delivery. A relay forwards it. Settlement records acknowledgement/release/disposition; failure there may occur after successful business handling.

## Idempotency / fencing

Idempotency avoids repeating an effect for the same operation. Fencing uses a token/version to reject stale actors. Diagnostics describe existing mechanisms; they do not invent new guarantees.

## Import closure / payload

Import closure is the complete set of files/dependencies needed by an entrypoint. The payload is what the runnable artifact actually includes, which may differ from files present in a checkout.

## Gate / focused check / impact-selected check

A gate is a required verification decision. A focused check proves one owner; an impact-selected run gathers all obligations affected by the specified paths. Neither means “run every test twice.”

## Receipt / fingerprint / reuse

A receipt records an observed result tied to exact inputs. A fingerprint identifies those inputs. Reuse is valid only when the required identities and freshness rules still match.

## Counterexample / sensitivity test

A deliberately wrong or incomplete implementation/fixture that should make the intended assertion fail. It tests whether a check detects the particular mistake, not merely whether tests can fail.

## Source-matched review / legacy / partial

A reviewed responsibility record bound to actual source identities. Legacy/partial/support are contextual classifications, not interchangeable measures of correctness or counts of defects.

## ADR / harness

An architecture decision record explains a chosen design. The harness is the repo's agent-governance workflows and executable controls; it governs work rather than becoming the runtime vocabulary.

## D1 / B01–B14 / C01–C36

Project planning labels: approved scope baseline, ordered delivery batches and capability/responsibility groups. They are not runtime error codes. Read current scope amendments before interpreting historical pending entries.

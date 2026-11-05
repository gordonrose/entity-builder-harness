# Platform Server Source Map

This directory implements `@kanbien/platform-server`. External consumers use
the package root. `index.ts` is the deliberate public barrel; `main.ts` and
`transport.ts` are internal process implementation details even though the
approved image build supplies a runtime shim for `main.ts`.

| File | Main question it answers | Why it is separate |
| --- | --- | --- |
| `configuration/` | “Which generic process settings may come from an environment?” | Runtime configuration and safe release identity stay typed, visible, and testable. |
| `verification/` | “Which release metadata may a verifier receive?” | Safe application identity is separate from workload and package-custody proof. |
| `index.ts` | “Given a valid mounted app registry, which policy steps may run a route handler?” | Request policy and app adaptation should remain readable without Node socket details. |
| `transport.ts` | “How do untrusted Node HTTP bytes become a bounded, cancellable platform request?” | Listener limits, socket state, and connection draining are transport mechanics, not route policy. |
| `main.ts` | “How does a generic server process start and stop?” | Process wiring should not force the generic HTTP layer to choose apps or providers. |

## `index.ts` — policy pipeline and route adaptation

`createPlatformServerShell` mounts the supplied apps, validates their complete
registry and configuration, checks that required tenant/authorizer seams are
available, creates lifecycle control, and compiles route patterns. It exposes
two paths: `handle` for deterministic tests or non-Node hosts, and `listen`
for the Node transport.

Configuration rejection reports the exact transport field/relationship, schema
position and explicitly selected Core/app evidence before listening. Failed
registration reports contract-owned predicates without starting lifecycle work.
The default reporter selects built-in and mounted app catalogs; an injected
reporter retains precedence. Catalog-selection failures use the fixed contract
catalog, not the invalid selection itself. Reporting is optional and cannot
change existing failure codes, public details, thrown identity or retry policy.

Failed mounting can select catalogs registered before the app throws. Runtime
observers deliver lifecycle/state evidence at the actual boundary, including
unsuccessful shutdown Results the process historically ignores. Context
construction observes its own clock/normalization location; selected source
evidence remains independent. Tenant/resource guards report only the predicate
that actually failed, preserving short-circuit getter reads. Parameter decoding
still throws its original URIError; diagnostics do not create a new HTTP policy.
Transport response-writing and process-log failures preserve the original
throw and cleanup order. No success is inferred from an attempted close.

The optional request-context `onDiagnostic` callback uses that matched route's
operational-log permission, selected built-in/app/target catalogs and existing
default or injected reporter. It is absent for opted-out and metric-only routes.
Each observation is independently validated/copied and correlated to that request;
an own location can be reported alongside all nine source records without
packing a tenth record into a companion list. Unknown/malformed records are
excluded before injected sinks; unavailable or throwing sinks do not change the
handler result. No diagnostic is copied into the HTTP response, and a successful
reconciliation does not erase an earlier observation or fabricate an error response.

The request path owns exact-origin CORS, standard security headers, pre-auth
rate-limit checks, health endpoints, route matching, authentication, broad
permission authorization, tenant derivation, request context, input validation,
optional resource authorization, handler execution, safe response/error
mapping, and provider-neutral operational evidence. It deliberately cannot
select Cognito, Redis, an app, or an AWS service.

For a matched app route, the mounted registry resolves its observability
profile before route policy runs. The profile decides whether that capability
may emit an operational log, metric, trace, or request/response latency timer,
and projects only the approved canonical facts: capability, action, server
execution context, HTTP method/status, outcome, and bounded error class. The
server does not add raw path parameters, request or correlation IDs, principals,
tenants, headers, bodies, stable route names, or error objects after this
projection. An explicit route opt-out emits no capability telemetry.

An application handler that safely returns a known failure may attach only a
stable `PlatformResponse.observability.errorClass`. The server turns it into a
profile-projected error class for logs, metrics, and traces, but never copies
that internal fact to the HTTP response. Messages, provider payloads, request
data, credentials, and identifiers are not a substitute for this class.

Some server events have no identifiable app route: an unsupported HTTP method,
a malformed request URL, or a health check, for example. Those retain separate
generic platform-operational evidence; they are not labelled as an app
capability. In contrast, an admission or JSON-parsing failure for a known route
uses that route's profile, because it is still an attempt to use that
capability. Tracer, logger, and metric failures are best effort and cannot
alter the response. This package does not expose trace context to app handlers,
receive remote parent context, choose sampling, or export anything.

The profile-governed completion count is named
`platform.server.request.outcome`; the declared latency timer is named
`platform.server.request_response_latency`. They intentionally have different
names, so a target metrics backend never receives a counter and timer under the
same metric identity.

Platform-owned response headers remain authoritative. This prevents an app
handler from replacing the request ID, CORS decision, content-security policy,
or other shared security header while still allowing a harmless app-specific
header.

## `transport.ts` — converting hostile network input into a bounded request

This file is the first code to see raw Node HTTP input. It limits header bytes,
header count, body bytes, header/request/handler time, in-flight work, and
requests per socket. It rejects unsupported HTTP methods rather than treating
them as `GET`, validates a declared content length before reading a body, and
accepts non-empty JSON bodies only with a JSON content type.

It runs transport admission before it reads the body. Therefore a request
rejected by the rate limiter does not consume JSON parsing or app-handler
capacity. The listener creates a request ID when the upstream value is absent
or malformed, passes an abort signal into the request context, maps transport
failures through the shared safe error path, and closes gracefully: stop new
connections, allow current work a bounded time, then abort/close remaining
connections.

A handler timeout is not permission to forget a still-running promise. The
listener aborts its signal and returns a safe timeout response, but retains the
request's concurrency slot until that handler settles. This protects capacity
when an app handler fails to honour cancellation; the handler should still
honour the signal so its own downstream work can stop promptly.

The peer address comes from Node's socket only. Proxy-header interpretation is
not safe as a generic helper because it requires target-specific proof of which
ingress is trusted.

## `main.ts` — generic lifecycle host, not product composition

`startPlatformServerProcess` supplies generic environment/config collection,
starts the lifecycle before listening, turns a listen failure into a stable
startup result, and begins lifecycle draining before listener shutdown. It also
installs signal handlers for the process host.

It takes an injected app list, authentication hook, rate limiter, and transport
options. A product/deployment entrypoint is responsible for supplying any of
those target-selected pieces. That separation lets the same server mechanics
host a different product or provider without generic platform code learning
about either one.

It may also receive an optional Core `Metrics` port from that entrypoint. This
is an injection socket rather than an AWS decision: the generic server can emit
the same profile-governed points with the in-memory test sink, a no-op sink, or
a target-selected adapter. The Kanbien staging entrypoint is the only current
consumer that selects the CloudWatch OpenTelemetry adapter and owns its bounded
flush/shutdown lifecycle.

## `configuration/` and `verification/` — process facts without target selection

`configuration/` resolves only generic server settings from an injected
environment: the configuration record, listener settings, CORS and health
exposure, and a bounded release identity. `verification/` returns that identity
in a safe response shape. Neither folder selects a route, product, provider,
target, secret source, image digest, or deployment outcome. A later internal
verifier must combine this response with independent workload and
package-custody evidence.

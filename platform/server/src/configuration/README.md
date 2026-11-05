# Server Configuration Source Map

This folder makes the generic server's runtime configuration visible and
testable. It does not choose a product, provider, target, or secret source.

| File | Responsibility |
| --- | --- |
| `runtime.ts` | Collects the generic process settings from an injected environment: configuration record, listener host/port, CORS, health exposure, and safe release identity. |
| `index.ts` | Deliberate public configuration exports. |

Target scopes decide which settings are required and how they are supplied.
This code only defines their generic process behaviour and prevents unsafe
release metadata from becoming verification evidence.

`resolvePlatformServerRuntimeConfiguration` retains its configuration-only API.
Its additive `WithDiagnostics` companion resolves the same configuration plus
four listener/health observations, ordered host, port, liveness exposure, readiness
exposure, followed by any CORS and release-identity omission observations. It accepts optional process host/port overrides with the same precedence
as process startup, including an ephemeral port zero. Both APIs share one resolver.

Records describe selection, not listener success. Missing/empty optional settings
select existing defaults at info severity. A supplied invalid port or unsupported
health exposure that actually selects a default warns. Shadowed environment
values never produce misleading fallback warnings. Port failure precedence is
NaN, nonfinite, noninteger, below one, above 65535; accepted Number spellings are
unchanged. Host strings are not trimmed or syntax-validated. Readiness defaults to
authenticated only when an authentication hook exists; the actual selected
public/authenticated policy is safe controlled evidence.

The process reports through the existing diagnostic reporter and caller logger
before mounting; sink failure is best effort. Neither observation records nor the
started event contain raw listener hosts. Existing numeric bound port and safe
release metadata remain in the started event. Configuration values remain
available internally through the existing config source, never copied into
diagnostic detail. CORS origin omission follows the existing nonempty predicate;
an empty normalized allowlist records omission without treating it as rejection.
Release omission distinguishes missing, empty and the existing format rejection.
No origin grammar, duplicate rule or new release policy is added.
The server runtime unit owns pure/type,
real HTTP, disclosure and sink-failure tests; compiled bootstrap, persistence and
shell checks own target propagation and payload proof.

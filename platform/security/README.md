# Platform Security

`platform/security` provides provider-neutral runtime security mechanisms:
authentication hooks, generic JWT/JWKS verification, claim-to-permission
translation, exact-origin browser protection, security headers, rate limiting,
certificate-content parsing and shared security diagnostic definitions.

It does not select an identity provider, define app roles or tenant groups,
decide resource-level business authorization, or provision cloud security
resources. Those responsibilities belong to adapters, apps/products, and
infrastructure respectively.

## Boundary

Consumers import `@kanbien/platform-security`. Source may depend only on Node
cryptography, public `@kanbien/core` contracts, and local topic files. It must
not name provider identity systems, import app code or infrastructure, or turn
product policy into a generic platform rule. The package’s boundary test
enforces those restrictions.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/errors.ts` | Stable, safe platform-security error vocabulary. | `npm run platform:security:check` |
| `src/diagnostics.ts` | Versioned certificate, peer, credential, mapping, policy and limiter records using Core security reasons; closed record extraction and private exception preservation. | `npm run platform:security:check` |
| `src/certificates.ts` | Parse complete certificate blocks without file access or a claim of peer trust. | `npm run platform:security:check` |
| `src/authentication.ts` | Authentication result/hook contracts, bearer parsing, JWT authentication hook, and Core-principal bridge. | `npm run platform:security:check` |
| `src/jwt.ts` | Generic RS256 JWT verification, JWKS fetching/cache, and claim-time validation. | `npm run platform:security:check` |
| `src/jwt-contract.ts` | Existing JWT options, token/key and verifier interfaces, shared without implementation cycles. | `npm run platform:security:check` |
| `src/jwt-configuration/` | Check verifier instructions before returning a verifier; safe configuration reports and stable checked copies. | `npm run platform:security:check` |
| `src/authorization.ts` | Generic permission check and configured claim-to-permission mapping. | `npm run platform:security:check` |
| `src/headers.ts` | Security headers and exact-origin CORS policy construction. | `npm run platform:security:check` |
| `src/rate-limit-configuration.ts` | Shared positive-whole-number check and safe configuration reports for rate limiters. | `npm run platform:security:check` |
| `src/rate-limiting.ts` | In-memory rate limiter, safe rate-limit keys, and rate-limit errors. | `npm run platform:security:check` |
| `src/index.ts` | Deliberate public package exports only. | `npm run platform:security:check` |

The [source map](src/README.md) explains why these boundaries exist and which
topic may depend on another. The public package import remains unchanged; the
topic files are not public subpath APIs.

The [JWT configuration guide](src/jwt-configuration/README.md) explains startup
checks separately from checking an incoming token. Invalid instructions throw a
fixed configuration exception from the direct verifier factory; they are not
reported as an invalid user token. Existing valid defaults and verifier return
types remain. The additional public JSON asset is
`@kanbien/platform-security/jwt-configuration/diagnostics.v1.json`; it is generated
from the same definitions retained in the full security catalogue.

## Shared number checks for rate limiters

A limiter needs numbers such as “allow 100 requests” and “count them over 1000
milliseconds.” Both the in-memory implementation and the shared-store adapter
need these numbers to be whole and greater than zero. They now use the same
check in [rate-limit-configuration.ts](src/rate-limit-configuration.ts), through
these two public names:

- `securityRateLimitPositiveIntegerFailureRecord(field, value)` returns
  `undefined` when the number passes, or a safe diagnostic describing the
  observed failure. The field is `limit`, `window` or `bucket-capacity`, not
  an environment-variable name or its supplied value. A caller uses this form
  when it needs to return its own error rather than throw one.
- `assertPlatformRateLimitPositiveInteger(name, value)` uses that same check.
  It returns nothing on success; on failure it throws the existing `RangeError`
  with its primary diagnostic followed by the specific problem report. The name
  is `limit`, `windowMs` or `maxBuckets`, matching the direct constructor's
  option. It is not an arbitrary name supplied by an external request.

For example, code outside this package can ask:

`securityRateLimitPositiveIntegerFailureRecord("limit", 0)`

The helper sees that 0 is a whole number but is not greater than zero. It returns:

```json
{"schema":"core/diagnostic-record/v1","code":"security.configuration-predicate-invalid","definitionVersion":1,"detail":{"field":"limit","reason":"not-positive","phase":"configuration","effect":"rejected"}}
```

For `1`, it returns `undefined`. For the text `"1"`, it reports `wrong-type`:
this helper does not convert text. The adapter first converts its environment
text with its existing `Number(...)` operation, then asks the shared helper to
check that number. The in-memory limiter already receives numbers. Neither
helper reads a clock or contacts a store, and success does not prove either
will work. The check keeps the existing acceptance of positive integers above
JavaScript's safe-integer range; it adds no new maximum.

The `undefined` return therefore needs handling: when a report is returned,
stop the dependent work and preserve that report. The two existing caller
fixtures test this, including a substituted shared failure. They also preserve
each caller's read order, defaults and original error wording. Unknown helper
names/fields are rejected with fixed `TypeError` messages, not echoed in errors.
Future rate-limit implementations can reuse these helpers with the same meaning;
this is not a universal numeric policy for every module.

The [Platform workflow](../../.agentic/03.product/workflows/platform-runtime-implementation.md)
owns this reuse instruction and links to the general configuration standard.
The [predicate fixture](tests/configuration-predicate-diagnostics-runtime.test.ts)
and [adapter fixture](../adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.ts)
prove the actual shared calls. Other files' detailed export walkthroughs are
outside this bounded README update.

## Certificate diagnostics and ownership

Core security owns provider-neutral reasons. This package owns executable
definitions and certificate-content parsing through Node's established
`X509Certificate` implementation. Adapters translate positively observed
verification evidence; target composition owns certificate sources and bindings.
Source-setting failures remain configuration errors, file access remains a file
operation, and transport failures are not evidence of failed certificate trust.

`validateCertificateAuthorityContent` checks syntax only. Success reports how
many complete certificate blocks were parsed; it does not establish certificate
lifetime, CA role, chain trust, revocation, hostname match or handshake success.
Its default `compatible-complete-blocks` policy retains existing acceptance,
including ignoring surrounding text and unfinished markers outside complete
blocks. An explicit `strict-markers` policy rejects unfinished or unmatched
certificate markers while still allowing surrounding comments. The persistence
target keeps compatibility mode; stricter production rejection requires a
separate compatibility decision and qualification. Complete malformed blocks
identify a one-based `blockNumber` through `security.certificate-block-invalid`.
Peer-verification constructors accept
observed reasons but do not inspect raw exceptions or perform verification.

Records exclude certificate bodies, subjects, issuers, keys, paths, endpoints and
native errors. Consumers explicitly select `platformSecurityDiagnosticCatalog`
through the existing reporter; these APIs activate no production logging and
provide neither incident classification nor durable audit delivery. The
PostgreSQL adapter maps observed verification codes into related security
records; the owning persistence record retains the operation and observed call
boundary. Explicitly composed catalogs control internal delivery. Source-read
failures remain configuration-source observations, not peer-trust failures.

## Request security observations

Core exports the immutable `securityOperationReasons` contract. Platform owns
each executable `security.<operation>.<reason>` version 1 definition in the
existing security catalog. Reasons have separate classifications; ordinary CORS
decisions and ignored optional time claims are informational, not incidents.
Records describe the observed check and leave application effects unassessed.

Authentication preserves the first case-insensitive authorization header and
first array value, including the existing bearer whitespace acceptance. Missing,
unsupported and malformed input remain distinct from verifier rejection or a
component throwing. JWT records identify the exact failed segment/header,
signature, issuer, required-claim index or time predicate without copying values.
Wrong-type optional `nbf` and `iat` remain accepted as before, with explicit
ignored observations. Expiry and clock-skew boundaries are unchanged.

JWKS records separate transport, unsuccessful HTTP status, JSON decoding,
key-set shape, skipped-key predicates, unreadable entries, key conversion and a
completed lookup without a usable matching key. Key indices refer to the fetched
array. Existing cache, exception and lookup behaviour remains: no refresh,
rotation recovery, retry or deadline is added. Failed fetches can carry bounded
TLS companions from native verification codes in that invocation's cause chain;
transport failure or error text alone does not establish a TLS failure. No
revocation capability is added. Other provider SDK connections remain outside
this migration unless their adapter supplies actual verification evidence.

Authorization records use zero-based indices into configured value mappings,
then exact-claim mappings, or into the required/granted permission list. They
do not contain claims, groups or permission inventories. Mapping observations
do not change granted permissions, including mixed-type arrays previously
filtered. At most seven observations plus an explicit omitted-count record are
retained when truncation is necessary. Merged omission counts saturate at
`Number.MAX_SAFE_INTEGER`; that sentinel means at least that many, not an exact
larger count. App-owned tenant/resource policy remains
separate; the server can report an actual resource denial, not invent its cause.

The server explicitly selects the security catalog and delivers copied,
validated failure records through the internal reporter. Route operational-log
opt-outs still apply. `securityDecisionDiagnostics: true` additionally selects
CORS, preflight, authenticated mapping/time and protected-header override
observations. Normal successful checks do not log by default. Method-independent
requests require every matching path's route to permit operational logs, so
preflight cannot bypass a sole opt-out or a mixed-profile path's opt-out.

CORS distinguishes absent, present-empty, allowed and non-allowlisted origin. A non-allowlisted
origin omits browser permission headers; it does not prevent handler execution.
Preflight records the registered-path check actually performed, not method/header
validation that does not exist. Protected-header records contain only an approved
header name. These observations describe server construction, not headers after
a proxy, and introduce no new policy validation or rejection.

In-memory limits distinguish quota exhaustion from bucket-capacity exhaustion.
The shared-store adapter distinguishes quota from store failure and configuration
failure. Invocation wrappers add transport/principal boundary and key category,
never addresses, token hashes, principal IDs or store keys. Existing HTTP status,
retry output and accounting order remain unchanged. Target startup retains
adapter configuration records through its wrappers and selects the same catalog
for early internal reporting, before route profiles exist.

Limiter clock evaluation observes the existing `clock.now().getTime()` expression
before bucket accounting or a shared-store invocation. A throw retains the fixed
`security.rate-limit-clock-failed` record, without reading its message, time or
cause, guessing whether the clock call or projection failed, or diagnosing peer
trust. The invocation wrapper keeps its historical dependency-failed primary and
adds this validated companion. Both producers rethrow the original value;
private WeakMap retention works for mutable and frozen objects. Primitive and
function throws have no retained local observation, and the wrapper's existing
replacement of such throws is unchanged. Successful evaluation returning NaN
keeps its previous behavior; no timestamp rejection, retry or clock call is added.

Focused proof lives in `tests/security-operation-diagnostics-{runtime,types}.test.ts`,
Core security diagnostic tests, server `tests/security-diagnostics-runtime.test.ts`,
the two adapters' runtime suites and the compiled shell payload fixture. This is
coverage of those existing mechanisms, not sessions, cookies, CSRF, secrets,
tenant isolation, durable audit or every future integration.

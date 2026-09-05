# Platform Security Source Map

This directory implements `@kanbien/platform-security`. Consumers use the
package root; they do not import topic files directly. The
[package README](../README.md) owns the package boundary and verification
route.

`index.ts` is a deliberate public barrel. It re-exports the supported existing
API after the source split, but it does not expose internal helpers merely
because another topic file uses them.

| File | Owns | Why the boundary matters |
| --- | --- | --- |
| `errors.ts` | `PlatformSecurityError` and its stable codes. | Authentication, authorization, JWT, and rate limiting can report a common safe error shape without importing one another’s mechanisms. |
| `authorization.ts` | Permission matching and configured claim-to-permission mappings. | It translates identity facts into declared permissions; it does not verify a token or decide product roles. |
| `jwt.ts` | JWT/JWKS types, verification, signing-key conversion/cache, and token-claim validation. | Cryptographic parsing and validation remain together, separate from provider configuration and app policy. |
| `authentication.ts` | Authentication-hook contract, denied default, principal bridge, bearer parsing, and JWT-hook composition. | The server receives one provider-neutral authentication result instead of JWT or provider details. |
| `headers.ts` | Security-header and CORS vocabulary plus exact-origin policy construction. | Browser transport protection is independent of identity and request-rate accounting. |
| `rate-limiting.ts` | Rate-limit contract, in-memory implementation, key derivation, and failure shape. | It can reuse safe header parsing while keeping throttling state and token hashing separate from authentication decisions. |
| `index.ts` | Approved public exports only. | Callers keep one stable import even when internal responsibilities evolve. |

## Detailed guide to the files

The table is a map for finding a file. This section explains the reasoning
behind each boundary: what belongs there, what deliberately does not, and how
the pieces cooperate during a protected request.

### `errors.ts` — one safe language for security failures

This file defines `PlatformSecurityError` and its stable error codes. It gives
the rest of the package a shared way to say “this token is invalid,” “this
mapping grants an undeclared permission,” “access is forbidden,” or “the rate
limit was reached.” Callers and tests can inspect the code without parsing a
human-readable sentence.

It does not decide whether a token is invalid or whether a permission is
missing. JWT verification, authorization, and rate limiting each make their
own decision; they use this shared shape to report it safely. The details field
must contain concise, allowlisted facts useful for the decision—not a raw
token, password, cookie, full request, or provider diagnostic payload.

### `authorization.ts` — generic permission mechanics, not business policy

This file answers the narrow reusable question: “Does this verified caller have
the permission this route requires?” It also translates configured claim values
such as roles or scopes into the app-declared permission vocabulary and checks
that a target mapping cannot grant a permission that mounted apps never
declared.

It deliberately does not define what an accountant, customer-service
representative, Benelux group, or invoice means. Those are product policy and
resource-authorization questions. The platform may confirm that a caller has
`billing.invoice:read`; the product decides whether that permission, tenant,
group membership, and the specific invoice allow the action.

### `jwt.ts` — proving that a token is trustworthy

This file owns the generic JWT/JWKS mechanics. It decodes the three JWT
segments, checks the expected signing algorithm and key ID, obtains a matching
public key from JWKS, verifies the signature, and validates issuer, time, and
required-claim rules. It caches usable signing keys inside the verifier
instance so repeated token checks do not repeatedly fetch the same key.

This is verification machinery, not an identity-provider integration. The file
knows generic concepts such as a JWKS URL, an RS256 signature, `iss`, `sub`,
and expiry. It does not know a provider’s environment variables, user-pool
name, group-claim convention, or deployment target; an adapter and target
composition supply those choices.

### `authentication.ts` — turning verified identity facts into a principal

This file defines the platform’s common authentication result and hook. A
server can ask one provider-neutral question—“authenticate this request”—and
receive either a denied result or verified facts: permissions, principal ID,
principal type, subject, claims, scopes, and an optional rate-limit key.

`createJwtBearerAuthenticationHook` composes two earlier mechanisms: it gets a
Bearer token from request headers, asks a JWT verifier to validate it, then
uses the authorization mapping to derive permissions. The principal bridge
creates a Core `Principal` only when all required identity facts are present.
That fail-closed rule prevents an object that merely says `authenticated: true`
from being mistaken for a complete accountable identity.

The low-level header and bearer-token readers are exported only for sibling
source files such as rate limiting. They are intentionally absent from the
public barrel, so external callers do not depend on this internal arrangement.

### `headers.ts` — browser-facing transport protection

This file builds the defensive HTTP headers that apply consistently to browser
responses, including content-type protection, frame denial, referrer policy,
and a restrictive content-security policy. It also constructs CORS policy.

The important CORS rule is exact origin matching: a request origin must be in
the configured allowed-origin list before the response receives an
`access-control-allow-origin` value. CORS is not authentication or
authorization—it is a browser transport rule. A permitted origin still needs a
valid identity and permission, while a non-browser client does not gain
permission merely because it can send an HTTP request.

### `rate-limiting.ts` — bounded request pressure without exposing secrets

This file owns the rate-limit decision contract and the deterministic
in-memory implementation used by the current platform shell and tests. It
counts requests within a time window and returns either an allowed decision or
a denied decision with a retry-after duration.

It also derives a safe key. A verified authentication result can supply a
stable principal key. Otherwise, a Bearer token is hashed before it is used as
a key; the raw token is never used as a loggable identifier. If no usable token
is available, the code falls back to a forwarded or real IP address, then to an
anonymous bucket. This is an operational safeguard, not a finished distributed
production rate-limit store; selecting a shared store belongs to a later
adapter and deployment slice.

### `index.ts` — the one public doorway

`index.ts` is a barrel: a deliberate list of contracts and functions that the
rest of the repository may import from `@kanbien/platform-security`. It keeps
the public surface stable while allowing the implementation files to be
organised by responsibility.

The barrel is intentionally selective. A helper being exported from one topic
to another inside this directory does not make it public. That is how the
package avoids accidentally turning parsing details, caches, or future
refactoring constraints into permanent external promises.

## Dependency direction

`errors.ts` is foundational. `authorization.ts` and `jwt.ts` use that error
vocabulary independently. `authentication.ts` composes the JWT verifier and
authorization mapping into an authentication hook. `rate-limiting.ts` may use
the narrowly scoped bearer/header parsing helpers from `authentication.ts` to
avoid copying parsing rules. `headers.ts` is independent. Finally, `index.ts`
exports the approved public contracts.

The source-level helper exports used between topic files are intentionally not
re-exported by `index.ts`. They are implementation details, not a promise that
external callers may depend on that exact parsing arrangement.

## What this split does not change

The split does not add a provider, change JWT algorithms, alter permission
semantics, create tenant/group policy, loosen CORS, or select a production
rate-limit store. It makes already-existing responsibilities easier to locate
while tests prove the same public behaviour.

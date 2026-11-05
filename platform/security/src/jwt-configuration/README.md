# Checking token-verifier instructions

Before an application can check a signed access token, it needs to know whose
tokens it accepts, where to obtain public signing keys, and which extra facts
the token must contain. It also needs a clock and an allowed clock difference.
This folder checks those instructions **before a usable verifier is created**.
It does not inspect a token, fetch keys, call the clock or prove an identity
service is reachable. Token checking remains in [jwt.ts](../jwt.ts).

## What each file does

| File | Job |
| --- | --- |
| [index.ts](index.ts) | Exposes the functions/types below without implementing them. The security package root exposes them too. |
| [contract/requirements.ts](contract/requirements.ts) | Owns the default clock tolerance, permitted logical item/reason names and the checked-result type derived from the existing JWT contract. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Defines the approved configuration-failure packet and constructs bounded reports with safe rule/value positions. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | Generated copy of that definition for other languages and tools; not a second manually maintained list. |
| [contract/reporting/errors.ts](contract/reporting/errors.ts) | Constructs a fixed configuration exception and recognises errors made by that constructor, not errors with a similar message. |
| [domain/validation.ts](domain/validation.ts) | Checks supplied instructions using applicable Core readers and issue collection, then returns a stable checked copy or the safe failure. |

The existing public JWT interfaces now live once in
[jwt-contract.ts](../jwt-contract.ts), including the verifier, claim requirements,
key document and supplied fetcher. The older JWT file still exposes those types
for compatible imports. Neither contract depends on the checking implementation.

## One incorrect value

Illustrative code outside this module:

```typescript
import { validateJwtVerifierConfiguration } from "@kanbien/platform-security";

const result = validateJwtVerifierConfiguration({
  issuer: "identity-service-A",
  jwksUri: "https://identity.example.invalid/keys",
  clockSkewSeconds: NaN,
});
```

The caller supplies the expected issuer, key address and clock tolerance. `NaN`
is a numeric value meaning “not a number”; it cannot be used as a duration.
The validator checks the text and address, uses Core to establish the numeric
failure, and puts the logical item and reason into its own approved report.
`result.ok` is `false`; `result.error.code` is
`PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID`. Its `diagnosticRecord.detail` is:

```json
{
  "phase": "verifier-construction",
  "effect": "verifier-not-created",
  "issues": [{ "setting": "clock-tolerance", "reason": "not-finite" }],
  "truncated": false
}
```

No supplied issuer, address, token or expected claim value is copied into that
report. The packet has code `security.jwt-configuration-invalid`, version 1.

## Several instructions that pass

```typescript
const result = validateJwtVerifierConfiguration({
  issuer: "identity-service-A",
  jwksUri: "https://identity.example.invalid/keys",
  requiredClaims: [
    { claim: "token_use", equals: "access" },
    { claim: "client_id", oneOf: ["application-A", "application-B"] },
  ],
});
```

Here `result.ok` is `true`. Its value contains those instructions with a
60-second clock tolerance because none was supplied. The nested claim list is
copied and frozen; later edits to the original instructions do not change the
verifier's accepted identities. Passing this check does not establish that any
particular incoming token matches the rules.

If two independent instructions are wrong, both problems are collected in check
order. A bad claim rule has `index`, its zero-based position; a bad entry within
`oneOf` also has `attributeIndex`, its position within that list. At most 32
issues are retained using Core's existing collector. `truncated: true` means
additional problems were found but not included—not that those problems passed.
A source getter throwing stops checking and retains that exception rather than
pretending its contents were missing or invalid.

## How this fits into the repo

```text
Target / adapter supplies verifier instructions
                 |
                 v
createJwksJwtVerifier (jwt.ts)
                 |
                 v
validateJwtVerifierConfiguration (this folder)
   Core readers + security requirements + bounded reports
                 |
       +---------+----------+
       |                    |
  checked copy          failed result
       |                    |
  create verifier       fixed configuration exception
       |                    |
  later verify(token)   caller handles failure / approved reporting
```

The direct factory still returns a verifier on success; it does not suddenly
return an `{ ok: ... }` object. The environment-loading adapter caller retains
its existing returned-error interface by translating only a recognised owned
configuration exception. No verifier is returned on rejection. Whether a whole
process stops or a diagnostic is stored remains the calling program's job.

## Public names and rules

- `validateJwtVerifierConfiguration(options)` returns a checked stable copy or
  `JwtConfigurationFailure`. Use it when coordinating verifier configuration;
  ordinary callers can use `createJwksJwtVerifier`, which already calls it.
- `CheckedJwtVerifierConfiguration` describes that successful copy, with the
  defaulted numeric tolerance and explicit readonly claim list. It is not a
  promise that injected dependencies will work later.
- `jwtDefaultClockSkewSeconds` is 60. Supplied tolerances must be finite and
  non-negative; zero and fractions are valid. No new maximum is invented.
- `jwtConfigurationDiagnostic` describes the closed failure packet;
  `jwtConfigurationDiagnosticCatalog` selects that one definition. The whole
  security catalogue contains it too: register the selected local catalogue or
  the aggregate, not both under their common owner.
- `jwtConfigurationError(record)` checks the packet and constructs the fixed
  `TypeError`; `isJwtConfigurationError(value)` recognises those owned errors.
  A matching message/code on an unrelated exception is not sufficient.
- `JwtConfigurationFailure` describes the checker's failed result, containing
  its fixed code and diagnostic record. Supplied configuration values are absent.

Issuer comparison remains exact; an issuer need not be a URL. Missing, empty,
blank and surrounding-whitespace text are distinct problems. The built-in key
fetcher requires an absolute HTTPS address; a trusted supplied fetcher may use
another nonblank source identifier. Its `fetch` and a supplied clock's `now`
must be callable, but construction never invokes them. Their method receivers
and later internal state are retained, without freezing caller-owned objects.

Claim rules need one comparison form, not both: `equals` or a nonempty `oneOf`.
Expected values are text, finite numbers or booleans. Zero, false and empty
expected text are valid and are never coerced. Omitted/empty requirements add
no extra claim checks; the verifier's built-in signature/issuer/time/subject
checks still run. Explicit null is invalid configuration, not omission.

The [configuration standard](../../../../.agentic/03.product/standards/config-runtime-settings.md#token-verifier-construction)
owns governance. [Runtime tests](../../tests/jwt-configuration-runtime.test.ts)
prove exact failures, actual constructor use, checked snapshots and valid token
behaviour; type and reader fixtures cover public compatibility and JSON access.
The JSON asset is public at
`@kanbien/platform-security/jwt-configuration/diagnostics.v1.json`.
These are reusable tools for current and future adapters—not a new token
provider, runtime secret loader, redirect policy or live deployment proof.

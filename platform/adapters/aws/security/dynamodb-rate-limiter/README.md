# AWS DynamoDB Shared Rate-Limit Adapter

This package translates the provider-neutral PlatformRateLimiter port into an
AWS DynamoDB fixed-window counter. It never stores a raw bearer token or a raw
principal/client identifier: the table key is a versioned SHA-256 hash.

| File | Responsibility |
| --- | --- |
| [src/index.ts](src/index.ts) | Expose the existing eleven public functions, constant and types; no implementation lives here. |
| [src/rate-limiter.ts](src/rate-limiter.ts) | Build the limiter, read its inputs, and make conditional DynamoDB counter updates. |
| tests/ | Prove expiry, retry timing, hashed keys, configuration rejection, and dependency boundaries. |

Infra owns the DynamoDB table, TTL configuration, encryption, task IAM policy,
and resource lifecycle. This adapter owns only the runtime translation.

Clock evaluation precedes the store call. A thrown `clock.now().getTime()` keeps
its original value and, for object throws including frozen errors, retains the
shared security `security.rate-limit-clock-failed` observation. The outer limiter
observer preserves it as a companion to its existing dependency-failed primary;
this is not evidence of a store call or peer-trust failure. Primitive/function
throws cannot retain local evidence through the object-only WeakMap route.
Existing NaN timestamp behavior, counter accounting, expiry and retries remain
unchanged; no additional clock or store call is made.

## Where number checks happen

The adapter may receive text such as `"0x10"` from an environment variable.
It keeps its existing conversion, `Number("0x10")`, producing 16. It then calls
Platform security's shared numeric helper, which confirms that 16 is a whole
number greater than zero. A rejected number returns the adapter's existing
configuration error with the shared specific diagnostic attached. Missing or
empty text is still handled here, before conversion.

Direct constructor options already contain numbers. Their `limit` and
`windowMs` go through the shared assertion, which throws the original
`RangeError` and ordered diagnostics if either fails. The adapter checks its
table name first, then limit, then window, as before. No helper calls the store
or creates an SDK client. Defaults, environment-variable names, text conversion,
error envelopes and counter behavior remain here rather than in Core.

```text
Environment text -> this adapter's Number conversion -> shared numeric report
Direct numbers ------------------------------------> shared numeric assertion
                                                        |
                         Platform security: one predicate, existing safe reports
```

The [shared helper guide](../../../../security/README.md#shared-number-checks-for-rate-limiters)
explains its two public functions and exact output. Existing consumers keep the
same package import. Other exported adapter functions/types are unchanged;
a complete export walkthrough is outside this bounded documentation update.

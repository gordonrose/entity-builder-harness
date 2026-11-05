# Platform Health

`@kanbien/platform-health` aggregates registered Core health checks and keeps
liveness independent from dependency readiness. `src/index.ts` owns summaries,
HTTP status mapping and the existing public projection; `src/diagnostics.ts`
owns the closed `health` diagnostic catalog. The generated
`contracts/diagnostics.v1.json` supplies other-language readers.

An optional `diagnostics` reporter observes returned degraded/unhealthy checks,
synchronous invocation throws, asynchronous rejection, projection failures and
an unready lifecycle input. Check positions are zero-based indices in the
registration array. Observations do not infer dependency causes, cancellation
or recovery. Existing check invocation order, concurrent waiting, summary
fields and HTTP statuses remain. Valid upstream primary/related records are
reported internally only after a nonhealthy result or projection failure;
ordinary healthy results do not emit stale failure fields. The reporter must
explicitly select their owning catalogs. Rejection, absence and sink failure
are not proof of delivery and cannot alter the health outcome.

The next observation follows the reported boundary: use `index` to inspect the
registered check, distinguish its invocation/rejection from public projection,
and inspect lifecycle state separately when aggregation receives false. A
catalog rejection calls for checking selected definitions and reporter output;
it does not establish successful emission or a dependency cause.

Public detail is a Health-owned disclosure contract in `src/public-details.ts`,
not a general-purpose redactor. A present message becomes a fixed summary for
healthy/degraded/unhealthy status. Present metadata keeps only own data fields
`dependency` (ready/not-ready/unknown) and `config` (missing/present); all other
keys/values and accessor fields are omitted without enumeration or coercion.
Thrown/rejected checks return fixed failure metadata, never exception properties.
Adding a public field/value requires an explicit policy and tests. The user
approved this message/metadata compatibility change; status, HTTP mapping,
identity/timestamps/duration and optional field presence remain unchanged.
Internal selected diagnostics retain their independent structured evidence;
withheld public strings are not relocated into internal logs.

Source dependencies are Core, Platform contracts and provider-neutral
observability. Health does not select providers or add probe deadlines.
`npm run platform:health:check` proves types, runtime behavior, build and import
boundaries; server, worker and target composition tests prove actual delivery.

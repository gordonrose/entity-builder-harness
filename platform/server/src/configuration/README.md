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

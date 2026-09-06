# Platform Security

`platform/security` provides provider-neutral runtime security mechanisms:
authentication hooks, generic JWT/JWKS verification, claim-to-permission
translation, exact-origin browser protection, security headers, and rate
limiting.

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
| `src/authentication.ts` | Authentication result/hook contracts, bearer parsing, JWT authentication hook, and Core-principal bridge. | `npm run platform:security:check` |
| `src/jwt.ts` | Generic RS256 JWT verification, JWKS fetching/cache, and claim-time validation. | `npm run platform:security:check` |
| `src/authorization.ts` | Generic permission check and configured claim-to-permission mapping. | `npm run platform:security:check` |
| `src/headers.ts` | Security headers and exact-origin CORS policy construction. | `npm run platform:security:check` |
| `src/rate-limiting.ts` | In-memory rate limiter, safe rate-limit keys, and rate-limit errors. | `npm run platform:security:check` |
| `src/index.ts` | Deliberate public package exports only. | `npm run platform:security:check` |

The [source map](src/README.md) explains why these boundaries exist and which
topic may depend on another. The public package import remains unchanged; the
topic files are not public subpath APIs.

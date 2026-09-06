# AWS DynamoDB Shared Rate-Limit Adapter

This package translates the provider-neutral PlatformRateLimiter port into an
AWS DynamoDB fixed-window counter. It never stores a raw bearer token or a raw
principal/client identifier: the table key is a versioned SHA-256 hash.

| File | Responsibility |
| --- | --- |
| src/index.ts | Build the limiter, validate target configuration, and make conditional DynamoDB counter updates. |
| tests/ | Prove expiry, retry timing, hashed keys, configuration rejection, and dependency boundaries. |

Infra owns the DynamoDB table, TTL configuration, encryption, task IAM policy,
and resource lifecycle. This adapter owns only the runtime translation.

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material.hosted-context-provider-contract
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
- sre
kind: source-material
purpose: Define the RAG rulebook-owned hosted context provider contract, local auth config boundary, redaction, and fallback behavior.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.rules.concerns.hosted-context-provider-contract
  path: docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml
- id: rag-rulebook.script.query-context
  path: scripts/02.rag-rulebook/query-context/script.sh
-->
# Hosted Context Provider Contract

## Purpose

The RAG rulebook layer owns context-provider selection. A caller should ask the
RAG rulebook layer for a validated context packet; it should not know whether
the packet came from a hosted service, a local runtime cache, an AWS secret, or
a development fallback.

This keeps chat/workbench lifecycle code focused on session ownership and user
workflow, while `02.rag-rulebook` owns retrieval configuration, hosted auth,
provider fallback, redaction, stale-runtime checks, and packet validation.

## Stable Interface

The stable local interface is:

```text
scripts/02.rag-rulebook/query-context/script.sh
```

That command is the context-provider boundary for local callers. It accepts
request text, optional session provenance, packet format, and chunk budget.
Exact paths should be included in request text until typed request anchors are
governed. It returns a validated context packet or a clear governance/auth/runtime
gap.

Callers must treat the returned packet as evidence for the next prompt, not as
permission to mutate files, commit, deploy, or bypass lifecycle gates.

## Provider Modes

The provider mode is owned by `02.rag-rulebook`.

- `hosted` calls the hosted RAG/rulebook service.
- `local` delegates to the local runtime cache through
  `scripts/02.rag-rulebook/query-local-context/script.sh`.
- `auto` may choose hosted when hosted configuration and auth are present, or
  local when hosted configuration is absent and local fallback is governed.

If `hosted` is explicitly selected, missing or rejected auth must fail closed.
It must not silently fall back to local RAG.

## Local Configuration Boundary

The local default config path is:

```text
~/.config/rag-rulebook/rag.env
```

This file is machine-local and must not be committed. It may contain:

```text
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=https://rag.kanbien.com
RAG_RULEBOOK_AUTH_MODE=bearer
RAG_RULEBOOK_AWS_PROFILE=gordon-kanbien
RAG_RULEBOOK_AWS_REGION=eu-west-1
RAG_RULEBOOK_TOKEN_SECRET_ARN=arn:aws:secretsmanager:...
RAG_RULEBOOK_TOKEN=...
RAG_RULEBOOK_LOCAL_FALLBACK=dev-only
```

The token value is allowed only in the local user config file or in the local
process environment. It must not be written to repo files, fixtures, session
logs, context packets, command output, generated artifacts, or screenshots.

When possible, durable docs and examples should prefer secret references such
as `RAG_RULEBOOK_TOKEN_SECRET_ARN` rather than raw token values.

## Hosted Auth Behavior

Hosted requests use:

```text
Authorization: Bearer <token>
Content-Type: application/json
```

The command must support a local token value and may resolve a token from AWS
Secrets Manager when an ARN/profile/region reference is present. The resolved
token is runtime-only and must not be logged.

If hosted auth is missing, the command must report an auth-missing gap and stop.
If the hosted service returns `401`, the command must report an auth-rejected
gap and stop. Network errors should be reported as hosted-provider runtime gaps.

## Redaction

The following values are secret-bearing and must be redacted from diagnostics:

- `RAG_RULEBOOK_TOKEN`
- `Authorization`
- bearer token values
- full env file contents
- temporary curl config files that contain an authorization header

Diagnostics may include the provider mode, base URL host, config path, profile,
region, secret ARN, HTTP status, packet schema, and gap IDs.

## Fallback Policy

Local fallback is governed fallback, not a convenience side path.

Explicit `hosted` mode never falls back.

Explicit `local` mode delegates to the local runtime cache and inherits local
freshness checks.

`auto` mode may use local fallback only when fallback is explicitly configured
and the fallback reason is governed. A missing hosted token can use local only
when `RAG_RULEBOOK_LOCAL_FALLBACK=dev-only`. A rejected hosted token does not
fall back, because that indicates credential drift or access failure.

## Expected Gaps

The provider boundary should use stable gap IDs:

- `gap.rag-rulebook.hosted-context-provider-auth-missing`
- `gap.rag-rulebook.hosted-context-provider-auth-rejected`
- `gap.rag-rulebook.hosted-context-provider-runtime-error`
- `gap.rag-rulebook.hosted-context-provider-local-fallback-blocked`
- `gap.rag-rulebook.hosted-context-provider-contract-partial`

These gaps belong to `02.rag-rulebook`, not `00.chat`.

## Coverage Status

This source material defines the intended RAG-owned provider contract. The
structured rulebook, derivation report, selector fixtures, script entrypoint,
and smoke tests are the implementation proof for this slice.

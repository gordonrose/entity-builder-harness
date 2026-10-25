<!-- agentic-artifact:
schema: agentic-artifact/v3
id: rag-rulebook.script.query-context.readme
version: 1
status: active
created_on: "2026-07-07"
updated_on: "2026-10-25"
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
- sre
kind: capability-readme
purpose: Explain the RAG-owned hosted/local context provider query command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.query-context
  path: scripts/02.rag-rulebook/query-context/script.sh
- id: rag-rulebook.rules.concerns.hosted-context-provider-contract
  path: docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml
-->
# Query Context

`script.sh` is the RAG/rulebook context-provider boundary. Callers provide
request text and optional context signals; the script chooses the governed
provider and returns a validated context packet.

Callers should not know about AWS, bearer tokens, Secrets Manager, or local
provider env files. Those details belong to `02.rag-rulebook`.

## Current Repository Configuration

The `rag.kanbien.com` deployment is retired. Use explicit local retrieval for
this repository, including when old hosted authentication fields remain in a
private client config. Keep those values private; local mode does not resolve
the secret or contact the hosted endpoint.

## Provider Modes

- `--provider hosted` calls the hosted RAG/rulebook service and fails closed if
  bearer auth is missing or rejected.
- `--provider local` delegates to
  `scripts/02.rag-rulebook/query-local-context/script.sh` and inherits local
  runtime freshness checks.
- `--provider auto` uses hosted when hosted config and auth are available. It
  may use local only when hosted config is absent or
  `RAG_RULEBOOK_LOCAL_FALLBACK=dev-only` explicitly permits local development
  fallback.

If no provider is supplied, the script uses `RAG_RULEBOOK_PROVIDER` from config
or defaults to `local`.

## Local Config

The default local config path is:

```bash
~/.config/rag-rulebook/rag.env
```

The file must not be group- or world-readable. Use permissions such as `0600`.

Set the provider explicitly in the private config:

```bash
RAG_RULEBOOK_PROVIDER=local
```

When updating an existing file, change only this provider assignment and
preserve authentication values and its private permissions. Do not display,
copy into evidence, or commit those values. Avoid `auto` for this retired
repository deployment because retained hosted auth could select hosted mode.

The reusable provider still supports separately governed hosted services via
`RAG_RULEBOOK_BASE_URL`, `RAG_RULEBOOK_AUTH_MODE`, `RAG_RULEBOOK_AWS_PROFILE`,
`RAG_RULEBOOK_AWS_REGION`, `RAG_RULEBOOK_TOKEN_SECRET_ARN`, and
`RAG_RULEBOOK_TOKEN`. Their presence does not override explicit `local` mode.

## Usage

Build the local runtime, then query it through the provider boundary:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
bash scripts/02.rag-rulebook/query-context/script.sh \
  --provider local \
  --request-text "Explain the RAG provider contract in docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml" \
  --pretty
```

Omit `--provider local` only when the private config explicitly selects local
(or no provider config exists, so the command defaults to local). Rebuild the
runtime when freshness checks report changed inputs.

## Security

The script must not print `RAG_RULEBOOK_TOKEN`, `Authorization`, bearer token
values, or full env file contents. It uses a temporary curl config for hosted
requests and deletes it after the request.

Stable gap IDs:

- `gap.rag-rulebook.hosted-context-provider-auth-missing`
- `gap.rag-rulebook.hosted-context-provider-auth-rejected`
- `gap.rag-rulebook.hosted-context-provider-runtime-error`
- `gap.rag-rulebook.hosted-context-provider-local-fallback-blocked`

## Effects

Hosted mode performs a network request. Local mode is read-only and delegates
to the existing local runtime cache query path.

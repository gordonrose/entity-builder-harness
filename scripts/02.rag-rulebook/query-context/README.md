<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.query-context.readme
version: 1
status: active
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

Example variable names:

```bash
RAG_RULEBOOK_PROVIDER=hosted
RAG_RULEBOOK_BASE_URL=https://rag.kanbien.com
RAG_RULEBOOK_AUTH_MODE=bearer
RAG_RULEBOOK_AWS_PROFILE=gordon-kanbien
RAG_RULEBOOK_AWS_REGION=eu-west-1
RAG_RULEBOOK_TOKEN_SECRET_ARN=arn:aws:secretsmanager:...
RAG_RULEBOOK_TOKEN=...
RAG_RULEBOOK_LOCAL_FALLBACK=dev-only
```

Do not commit real token values.

## Usage

```bash
bash scripts/02.rag-rulebook/query-context/script.sh \
  --request-text "Explain the RAG provider contract" \
  --provider hosted \
  --format compact \
  --pretty
```

Local mode:

```bash
bash scripts/02.rag-rulebook/query-context/script.sh \
  --provider local \
  --request-text "Explain the RAG provider contract in docs/02.rag-rulebook/rules/concerns/hosted-context-provider-contract.yml" \
  --pretty
```

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

<!-- agentic-artifact:
schema: agentic-artifact/v2
id: docs.02-rag-rulebook.postman.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: service-api
disciplines:
- agentic
- architecture
- sre
kind: guide
purpose: Explain how to import and use the hosted RAG/rulebook service Postman collection without committing secrets.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: docs.02-rag-rulebook.postman.collection
  path: docs/02.rag-rulebook/postman/rag-rulebook-service.postman_collection.json
-->
# RAG Rulebook Postman Collection

Import `rag-rulebook-service.postman_collection.json` into Postman to test the
hosted RAG/rulebook service.

## Variables

Set these collection variables after import:

- `baseUrl`: defaults to `https://rag.kanbien.com`
- `ragToken`: staging bearer token from AWS Secrets Manager
- `requestText`: default prompt for context-query smoke tests
- `maxChunks`: default selected chunk count

Do not commit a real `ragToken`. Keep it in your local Postman environment or
collection variable value only.

## Token Lookup

Use AWS CLI to fetch the staging token locally:

```bash
SECRET_ARN="$(
  aws cloudformation describe-stacks \
    --profile gordon-kanbien \
    --region eu-west-1 \
    --stack-name rag-rulebook-staging-foundation \
    --query "Stacks[0].Outputs[?OutputKey=='ServiceTokenSecretArn'].OutputValue | [0]" \
    --output text
)"

aws secretsmanager get-secret-value \
  --profile gordon-kanbien \
  --region eu-west-1 \
  --secret-id "$SECRET_ARN" \
  --query SecretString \
  --output text
```

## Requests

The collection includes:

- `GET /health`: unauthenticated readiness check
- `GET /version`: unauthenticated service metadata check
- `POST /context/query compact`: authenticated compact context packet query
- `POST /context/query full`: authenticated full context packet query
- `POST /context/query unauthorized check`: verifies the auth guard rejects
  requests without a bearer token


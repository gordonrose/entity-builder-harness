<!-- agentic-artifact:
schema: agentic-artifact/v3
id: docs.02-rag-rulebook.postman.readme
version: 1
status: active
created_on: "2026-07-01"
updated_on: "2026-10-25"
layer: 02.rag-rulebook
domain: service-api
disciplines:
- agentic
- architecture
- sre
kind: guide
purpose: Explain how to use the local RAG/rulebook service Postman collection without committing secrets.
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
local RAG/rulebook HTTP service. The former `rag.kanbien.com` deployment is
retired. Normal harness retrieval uses the local provider directly and does
not need an HTTP server.

## Local Setup and Variables

Build the local runtime and start the loopback service using
`scripts/02.rag-rulebook/run-local-service/README.md`. For the collection's
authenticated and unauthorized checks, provide a private local
`RAG_SERVICE_TOKEN` to that process, then configure the matching `ragToken` in
Postman. Do not retrieve the retired staging service token.

- `baseUrl`: defaults to `http://127.0.0.1:3000`
- `ragToken`: your local service token, kept private in Postman
- `requestText`: default prompt for context-query smoke tests
- `maxChunks`: default selected chunk count

Do not commit a real `ragToken` or copy it into evidence.

## Requests

The collection includes:

- `GET /health`: unauthenticated readiness check
- `GET /version`: unauthenticated service metadata check
- `POST /context/query compact`: authenticated compact context packet query
- `POST /context/query full`: authenticated full context packet query
- `POST /context/query unauthorized check`: verifies the auth guard rejects
  requests without a bearer token


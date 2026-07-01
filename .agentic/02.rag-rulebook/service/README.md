<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.service.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
kind: service-readme
purpose: Describe the layer-owned local RAG/rulebook HTTP service MSP skeleton.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
effects:
- read-only
used_by:
- id: rag-rulebook.script.run-local-service
  path: scripts/02.rag-rulebook/run-local-service/script.sh
- id: rag-rulebook.script.run-local-service.smoke-test
  path: scripts/02.rag-rulebook/run-local-service/smoke-test.sh
-->
# RAG Rulebook Service

Layer-owned HTTP service skeleton for the first RAG/rulebook MSP.

The service exposes the provider-agnostic context-packet API surface:

- `GET /health`
- `GET /version`
- `POST /context/query`

The service does not implement a second retrieval engine. `/context/query`
delegates to `scripts/02.rag-rulebook/query-local-context/script.sh`, which
loads the built local runtime, checks runtime freshness, and returns a
validated context packet.

Build the local runtime before starting the service:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

Start locally:

```bash
bash scripts/02.rag-rulebook/run-local-service/script.sh
```

Smoke test:

```bash
bash scripts/02.rag-rulebook/run-local-service/smoke-test.sh
```

The local service binds to `127.0.0.1` by default. Non-loopback binding requires
an explicit unsafe-development opt-in and `RAG_SERVICE_TOKEN`; hosted or shared
network use requires a separate reviewed authentication and authorization
design.

This directory belongs under `.agentic/02.rag-rulebook/` because it is the
RAG/rulebook layer's reusable service machinery. Product `apps/` and
`platform/` concepts remain architecture/corpus concepts until a governed
product-layer implementation exists.

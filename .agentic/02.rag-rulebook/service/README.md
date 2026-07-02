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

`POST /context/query` requires `requestText` or `request_text`. The optional
`session` object may carry lifecycle provenance such as `id`, `branch`,
`worktree`, `latestContextPacketId`, and
`latestContextPacketRoutingSummary`. `session.layer`, `session.mode`, and
`session.workflow` are untrusted legacy routing hints only; callers should omit
them for prompt-first context resolution instead of sending fake chat-level
routing. HTTP clients cannot mark session routing hints trusted. Only governed
local session resolution may use the selector CLI's trusted-routing path, and
that path requires lifecycle proof fields before it will run.
The service validates these optional fields for size, control characters, and
basic shape, but it does not verify that client-supplied branch or worktree
values are the active governed chat. Packets mark this lifecycle context as
unverified provenance. Side-effect authorization must still verify chat
ownership through the consuming workflow before acting.

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

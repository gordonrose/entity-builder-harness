<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.run-local-service.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain how to run the local RAG/rulebook HTTP service MSP skeleton.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.run-local-service
  path: scripts/02.rag-rulebook/run-local-service/script.sh
- id: rag-rulebook.script.run-local-service.smoke-test
  path: scripts/02.rag-rulebook/run-local-service/smoke-test.sh
-->
# Run Local RAG Rulebook Service

Starts the thin local HTTP service for the first MSP API surface.

The service expects a built local runtime cache. Build it first:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

Then start the service:

```bash
bash scripts/02.rag-rulebook/run-local-service/script.sh
```

Options:

- `--runtime-dir <path>` selects the runtime cache. Default:
  `.cache/02.rag-rulebook`
- `--host <host>` selects the bind host. Default: `127.0.0.1`
- `--port <port>` selects the port. Default: `3000`
- `--allow-non-loopback` allows binding beyond loopback. It requires
  `RAG_SERVICE_TOKEN` and is still local-development only.

The service exposes:

- `GET /health`
- `GET /version`
- `POST /context/query`

This command starts a local process only. It does not deploy to AWS, mutate
GitHub, build containers, publish corpus packages, or expose MCP tools.

Do not bind to `0.0.0.0` or a private network interface without an explicit
token and a reviewed access boundary. Hosted service authentication and
authorization are separate MSP work and are not provided by this local skeleton.

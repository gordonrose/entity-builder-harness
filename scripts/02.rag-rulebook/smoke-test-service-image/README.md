<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.smoke-test-service-image.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
- sre
kind: capability-readme
purpose: Explain the local hardened container image smoke test for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.smoke-test-service-image
  path: scripts/02.rag-rulebook/smoke-test-service-image/script.sh
-->
# Smoke Test Service Image

`script.sh` builds and runs the local RAG/rulebook service image, mounts a
fresh local runtime cache read-only, and verifies:

- `GET /health`
- `GET /version`
- unauthenticated `POST /context/query` is rejected
- authorized `POST /context/query`

The container is run with a read-only root filesystem, all capabilities
dropped, `no-new-privileges`, and a bounded `/tmp` tmpfs for temporary query
packet files.

It does not push to a registry, call AWS, mutate GitHub, or deploy.

Use `--allow-skip-without-engine` only for environments where Docker is not
expected or the Docker daemon is not reachable. Release and deploy readiness
checks should require a real Docker engine.

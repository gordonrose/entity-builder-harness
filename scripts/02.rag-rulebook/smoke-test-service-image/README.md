<!-- agentic-artifact:
schema: agentic-artifact/v3
id: rag-rulebook.script.smoke-test-service-image.readme
version: 1
status: active
created_on: "2026-07-01"
updated_on: "2026-10-26"
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

`script.sh` builds and runs the local RAG/rulebook service image and verifies
the runtime cache assembled inside that image:

- `GET /health`
- `GET /version` matches the built source revision and ready packaged runtime
- unauthenticated `POST /context/query` is rejected
- authorized `POST /context/query`
- queries for excluded local tool configuration expose missing-evidence gaps and reasons

The built tag is resolved to an immutable image ID before execution. The command
emits HTTP results and fingerprints read from the image's runtime manifest.
A passing qualification record is emitted only after container absence is observed.

The container is run with a read-only root filesystem, all capabilities
dropped, `no-new-privileges`, and a bounded `/tmp` tmpfs for temporary query
packet files.

It does not push to a registry, call AWS, mutate GitHub, or deploy.

Use `--allow-skip-without-engine` only for environments where Docker is not
expected or the Docker daemon is not reachable. Release and deploy readiness
checks require a real Docker engine. An explicit unavailable-engine skip exits
77 and cannot count as passing qualification.

No host runtime cache is mounted over the packaged cache. The builder invokes
the shared delivery inventory before Docker operations, so missing route
registration blocks before an expensive build. Container cleanup uses the
existing Docker adapter and must observe absence; incomplete cleanup fails,
and an earlier build/query failure retains its original exit status.

`wiring-test.py` exercises the actual wrapper and cleanup interfaces with
disposable process fixtures. The local-service smoke suite runs these cheap
regressions before HTTP tests. Fixtures do not replace this finished-image test.

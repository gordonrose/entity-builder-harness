<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.build-service-image.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
- sre
kind: capability-readme
purpose: Explain the deterministic local image build wrapper for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.build-service-image
  path: scripts/02.rag-rulebook/build-service-image/script.sh
- id: rag-rulebook.script.smoke-test-service-image
  path: scripts/02.rag-rulebook/smoke-test-service-image/script.sh
-->
# Build Service Image

`script.sh` builds the local RAG/rulebook service image from the governed image
boundary:

```text
infra/04.deploy/02.rag-rulebook/image/Dockerfile
```

The build context is the repo root. The effective ignore file is:

```text
infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore
```

The command does not publish the image, call AWS, mutate GitHub, or deploy.

## Usage

```bash
bash scripts/02.rag-rulebook/build-service-image/script.sh
```

Useful options:

- `--tag <tag>` chooses the local image tag.
- `--base-image <image>` passes the Node base image to the Dockerfile.
- `--require-digest-base` requires the base image to be pinned by digest for
  local supply-chain hygiene checks.

Local smoke builds may use a tag-based base image. Staging and production
deployments require additional deploy-readiness evidence beyond this local
build wrapper, including immutable image digest, corpus identity, SBOM/scan,
and provenance or attestation policy.

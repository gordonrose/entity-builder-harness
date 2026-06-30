<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.image.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the container image packaging boundary for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: infra.04-deploy.02-rag-rulebook.readme
  path: infra/04.deploy/02.rag-rulebook/README.md
-->
# Image

This directory will own the container packaging boundary for the
RAG/rulebook service.

The container must package the existing local HTTP service without moving
service source code out of `.agentic/02.rag-rulebook/service/`.

Required future proof:

- deterministic build command
- `.dockerignore` coverage for secrets, git internals, caches, and local logs
- non-root runtime user where supported by the base image
- read-only service behavior by default
- `/health`, `/version`, and `/context/query` smoke tests
- immutable image digest recorded before deployment


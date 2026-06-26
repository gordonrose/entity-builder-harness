<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.corpus.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: corpus-readme
purpose: Define the RAG-readable deploy corpus package boundary for deployment source material and rules.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.standard.domain-corpus-package
  path: .agentic/02.rag-rulebook/standards/domain-corpus-package.md
- id: rag-rulebook.corpus-gap.04-deploy.mcp-server-deployment
  path: .agentic/02.rag-rulebook/corpus-gaps/04.deploy/mcp-server-deployment.yml
-->
# 04.deploy Corpus

This directory is the RAG-readable deploy corpus package for `corpus.04.deploy`.

The governing workflows for deploy work live under `.agentic/aws/`. This
directory contains source material and future structured rules that the
RAG/rulebook service can index, chunk, cite, and evaluate.

Use this corpus for infrastructure, release, runtime environment, GitHub
deployment, AWS deployment, observability, rollback, and deployment stop
condition knowledge.

Deploy knowledge is organized by deploy track:

- `source-material/shared/` for deploy knowledge reused by multiple targets
- `source-material/00.chat/` for LLM Workbench and chat harness deployment
- `source-material/02.rag-rulebook/` for RAG/rulebook and MCP server deployment
- `source-material/03.product/` for product and application deployment

Structured deploy rules live under matching tracks in `rules/`.

These are not separate owning layers. `04.deploy` owns deployment governance;
the track name identifies the system being deployed.

Do not store secrets, credentials, tokens, private keys, or live sensitive
runtime data here.

<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: rag-rulebook.script.record-knowledge-disposition.readme
  version: 1
  status: active
  layer: 02.rag-rulebook
  domain: session-log
  disciplines:
  - agentic
  - architecture
  kind: readme
  purpose: Document the RAG knowledge disposition session-log recorder.
  portability:
    class: reusable
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: rag-rulebook.script.record-knowledge-disposition
    path: scripts/02.rag-rulebook/record-knowledge-disposition/script.sh
-->
# Record Knowledge Disposition

Records how a code change is represented in the RAG/rulebook knowledge system.

Examples:

```bash
bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh covered \
  "Updated source material and selector proof for packages/core." \
  docs/harness/architecture/source-material/packages-core-contract-surface-v1.md

bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh no-impact \
  "Changed implementation details only; no retrieval guidance changed."

bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh deferred-with-gap \
  "Runtime behavior changed before source material was available." \
  .agentic/02.rag-rulebook/corpus-gaps/03.product/example.yml
```

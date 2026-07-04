<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: rag-rulebook.script.check-code-change-knowledge-coverage.readme
  version: 1
  status: active
  layer: 02.rag-rulebook
  domain: validation
  disciplines:
  - agentic
  - architecture
  kind: readme
  purpose: Document the code-change knowledge coverage gate for RAG/rulebook-aware commits.
  portability:
    class: reusable
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: rag-rulebook.script.check-code-change-knowledge-coverage
    path: scripts/02.rag-rulebook/check-code-change-knowledge-coverage/script.sh
-->
# Code Change Knowledge Coverage

This gate detects knowledge-bearing code changes and requires the current chat
session log to record a `## RAG Knowledge Disposition` section.

Knowledge-bearing paths currently include:

- `packages/core/**`
- `platform/**`
- `apps/**/app.mount.ts`
- `apps/**/app.manifest.ts`
- `infra/**`
- `.github/workflows/**`

Use the RAG-owned recorder:

```bash
bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh covered "<reason>" <evidence-path>...
bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh no-impact "<reason>"
bash scripts/02.rag-rulebook/record-knowledge-disposition/script.sh deferred-with-gap "<reason>" <corpus-gap-path>...
```

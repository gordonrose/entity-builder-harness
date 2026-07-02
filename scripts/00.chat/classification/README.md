<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.classification.readme
  version: 1
  status: active
  layer: 00.chat
  domain: classification
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Document the legacy chat task classifier retained outside startup routing.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.classification.classify-task.readme
    path: scripts/00.chat/classification/classify-task/README.md
-->
# Legacy Classification Scripts

These scripts are legacy compatibility artifacts. Chat startup no longer uses
them to classify a whole chat or to choose a durable layer, mode, or workflow.
Prompt-level classification and context selection now belong to the
RAG/rulebook runtime.

Do not add new startup routing behavior here. If prompt routing needs to change,
update the RAG/rulebook selector, fixtures, and context packet contract instead.

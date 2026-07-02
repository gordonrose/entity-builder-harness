<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.classification.classify-task.readme
  version: 1
  status: active
  layer: 00.chat
  domain: classification
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Document the legacy task classifier that is no longer used by chat startup.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.classification.classify-task
    path: scripts/00.chat/classification/classify-task/script.sh
-->
# Legacy Classify Task

`script.sh` reads a task summary and prints legacy routing metadata:

- `Layer`
- `Mode`
- `Workflow`
- `Reason`

Chat startup no longer calls this script and must not treat its output as
session metadata. New prompt-level classification, workflow selection, corpus
selection, and context-packet routing belong to the RAG/rulebook runtime.

`check-fixtures.sh` verifies the classifier against `fixtures.tsv`. Update the
fixtures only when maintaining this legacy compatibility behavior. Do not add
new prompt-routing policy here.

This capability does not grant write permission, create a branch, choose the
current prompt route, or decide that unclear governance is safe.

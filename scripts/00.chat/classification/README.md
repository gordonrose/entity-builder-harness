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
  purpose: Explain task classification scripts for chat startup routing.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.classification.classify-task.readme
    path: scripts/00.chat/classification/classify-task/README.md
-->
# Classification Scripts

Classification scripts turn a human task summary into chat session routing
metadata. Startup uses that metadata to choose the layer, mode, and workflow
before the next agent starts work.

The classifier is deliberately lightweight. It does not replace human judgment
when governance is unclear; it gives startup a first deterministic answer and
lets the workflow stop if the result is missing or ambiguous.


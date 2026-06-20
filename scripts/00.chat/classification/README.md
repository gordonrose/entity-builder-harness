<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain task classification scripts for chat startup routing.
domain: classification
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/classification/classify-task/README.md
-->

# Classification Scripts

Classification scripts turn a human task summary into chat session routing
metadata. Startup uses that metadata to choose the layer, mode, and workflow
before the next agent starts work.

The classifier is deliberately lightweight. It does not replace human judgment
when governance is unclear; it gives startup a first deterministic answer and
lets the workflow stop if the result is missing or ambiguous.


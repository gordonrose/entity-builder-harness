<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain chat metric helper scripts.
domain: metrics
portability: llm-workbench-required
used_by:
  - scripts/00.chat/metrics/estimate-chat-cost/README.md
  - scripts/00.chat/session-log/record-chat-commit/README.md
-->

# Metrics Scripts

Metrics scripts provide derived chat metadata such as estimated token cost.
They support session logs and reports; they are not billing systems.

Estimates should be transparent about their assumptions. When exact model
pricing or token splits are unavailable, scripts should record the basis and
avoid pretending to be precise.


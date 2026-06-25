<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.metrics.readme
  version: 1
  status: active
  layer: 00.chat
  domain: metrics
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain chat metric helper scripts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.metrics.estimate-chat-cost.readme
    path: scripts/00.chat/metrics/estimate-chat-cost/README.md
  - id: chat.script.session-log.record-chat-commit.readme
    path: scripts/00.chat/session-log/record-chat-commit/README.md
-->
# Metrics Scripts

Metrics scripts provide derived chat metadata such as estimated token cost.
They support session logs and reports; they are not billing systems.

Estimates should be transparent about their assumptions. When exact model
pricing or token splits are unavailable, scripts should record the basis and
avoid pretending to be precise.


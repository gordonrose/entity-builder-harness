<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.metrics.estimate-chat-cost.readme
  version: 1
  status: active
  layer: 00.chat
  domain: metrics
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain chat cost estimate metadata generation.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.metrics.estimate-chat-cost.script-js
    path: scripts/00.chat/metrics/estimate-chat-cost/script.js
  - id: chat.script.session-log.record-chat-commit
    path: scripts/00.chat/session-log/record-chat-commit/script.sh
-->
# Estimate Chat Cost

`script.js` converts an estimated token count into session-log cost metadata.

The estimate is intentionally conservative and records its basis. Transcript
byte-derived token estimates do not split input, cached input, and output
tokens, so the output tells readers what assumption was used rather than
presenting the number as exact billing.

This capability does not call external pricing APIs. It reads local pricing
profile data when available and otherwise emits unavailable metadata with a
reason.

By default it reads `scripts/00.chat/metrics/data/chat-pricing.json`, a
chat-owned local profile store bundled for standalone installs. Set
`CHAT_COST_PRICING_FILE` to point at an organization-maintained pricing file and
`CHAT_COST_PROFILE` to select a profile when local pricing needs to differ from
the bundled snapshot. The bundled default profile is provider-neutral and marks
cost unavailable until a concrete pricing profile is selected.

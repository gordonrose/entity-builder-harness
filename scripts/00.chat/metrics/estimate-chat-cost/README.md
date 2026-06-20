<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain chat cost estimate metadata generation.
domain: metrics
portability: llm-workbench-required
used_by:
  - scripts/00.chat/metrics/estimate-chat-cost/script.js
  - scripts/00.chat/session-log/record-chat-commit/script.sh
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


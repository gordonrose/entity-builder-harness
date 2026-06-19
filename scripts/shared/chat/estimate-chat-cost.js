#!/usr/bin/env node
// agentic-script:
//   owner: 00.chat
//   purpose: Compatibility wrapper for chat cost estimation metadata.
//   domain: metrics
//   portability: llm-workbench-compatibility
//   used_by:
//     - scripts/00.chat/session-log/record-chat-commit/script.sh
//   effects: read-only

require('../../00.chat/metrics/estimate-chat-cost/script.js');

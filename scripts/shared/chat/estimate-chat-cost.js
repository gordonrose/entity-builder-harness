#!/usr/bin/env node
// agentic-script:
//   owner: 00.chat
//   purpose: Compatibility wrapper for chat cost estimation metadata.
//   domain: metrics
//   portability: llm-workbench-compatibility
//   used_by:
//     - scripts/shared/git/record-chat-commit.sh
//   effects: read-only

require('../../00.chat/metrics/estimate-chat-cost/script.js');

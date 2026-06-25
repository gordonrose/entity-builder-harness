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
  purpose: Explain task summary classification into layer, mode, and workflow.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.classification.classify-task
    path: scripts/00.chat/classification/classify-task/script.sh
  - id: chat.script.startup.start-chat-session
    path: scripts/00.chat/startup/start-chat-session/script.sh
-->
# Classify Task

`script.sh` reads the opening task summary and prints the session routing
metadata used by chat startup:

- `Layer`
- `Mode`
- `Workflow`
- `Reason`

The output is intentionally simple text so shell startup can consume it without
extra dependencies.

`check-fixtures.sh` verifies the classifier against `fixtures.tsv`. Update the
fixtures when a new durable routing phrase should be recognized.

This capability does not grant write permission, create a branch, or decide
that unclear governance is safe. If the classifier cannot produce a reliable
route, the chat startup workflow must stop and ask for clarification or harness
coverage.


<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.bootstrap.readme
  version: 1
  status: active
  created_on: "2026-06-20"
  updated_on: "2026-10-20"
  layer: 00.chat
  domain: bootstrap
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain bootstrap scripts for preparing a portable chat workbench repo.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - id: chat.script.bootstrap.audit-chat-bootstrap-file-set.readme
    path: scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/README.md
-->
# Bootstrap Scripts

Bootstrap scripts help separate the portable chat workbench from this source
repo. They answer a practical question: which files are required when creating
or refreshing a standalone `llm-workbench` style repository?

Bootstrap is not normal chat startup. It is source-to-upstream packaging work.
It must avoid source-specific product files, session logs, transcripts, local
paths, and deployment material.

Use this domain when preparing the public workbench file set, validating that no
required script is missing, or checking whether a script is merely a validation
candidate.


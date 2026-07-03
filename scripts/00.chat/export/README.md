<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.export.readme
  version: 1
  status: active
  layer: 00.chat
  domain: export
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain chat worktree export capabilities.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.commands.readme
    path: .agentic/00.chat/commands/README.md
  - id: chat.script.command.readme
    path: scripts/00.chat/command/README.md
-->
# Export Scripts

Export scripts create portable review bundles from chat-owned worktrees.

Use this domain when the user needs to hand the active chat worktree, or only
its changed files, to another model, engineer, or verification environment.
The export capability owns the selection and manifest semantics. Zip is only
the default transport format for the resulting bundle.


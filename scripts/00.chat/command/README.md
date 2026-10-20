<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.command.readme
  version: 1
  status: active
  created_on: "2026-06-20"
  updated_on: "2026-10-20"
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain canonical chat command entrypoints.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.commands.readme
    path: .agentic/00.chat/commands/README.md
  - id: chat.script.command.dispatcher.readme
    path: scripts/00.chat/command/dispatcher/README.md
-->
# Command Scripts

Command scripts are the canonical implementation behind public `npm run chat:*`
shortcuts. They keep the human command surface stable while allowing the actual
capabilities to live in domain folders such as `startup`, `closeout`, or
`reporting`.

The command domain is mostly routing. A command entrypoint should delegate to a
capability script rather than duplicating the capability's logic.

Spaced human commands may be normalized by the dispatcher. For example,
`download repo` routes to `download-repo`, while `download repo diff` routes to
`download-repo-diff`.

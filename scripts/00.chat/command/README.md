<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain canonical chat command entrypoints.
domain: command
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/commands/README.md
  - scripts/00.chat/command/dispatcher/README.md
-->

# Command Scripts

Command scripts are the canonical implementation behind public `npm run chat:*`
shortcuts. They keep the human command surface stable while allowing the actual
capabilities to live in domain folders such as `startup`, `closeout`, or
`reporting`.

The command domain is mostly routing. A command entrypoint should delegate to a
capability script rather than duplicating the capability's logic.


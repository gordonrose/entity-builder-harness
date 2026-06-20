<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain how the chat closeout prompt is built and handed to terminal users.
domain: closeout
portability: llm-workbench-required
used_by:
  - scripts/00.chat/closeout/build-closeout-prompt/script.sh
  - scripts/00.chat/command/close/script.sh
-->

# Build Closeout Prompt

`script.sh` builds the governed prompt used when a human runs the public close
command. The prompt is meant for the next agent turn: it asks the agent to
inspect the chat worktree, run the right gates, commit approved work, and
record the commit.

The script tries to copy the prompt to the clipboard for terminal convenience
and prints it when clipboard copy is unavailable. Clipboard behavior is not the
governance contract; the prompt content is.

This capability does not stage files, commit, merge, push, or decide whether
work is complete.


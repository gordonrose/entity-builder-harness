<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the portable chat bootstrap file-set audit.
domain: bootstrap
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
-->

# Audit Chat Bootstrap File Set

`script.sh` reports the script and support-file set needed to bootstrap the
portable chat harness into another repository.

The audit starts from public chat commands, chat workflows, shared process
artifacts, and the governed runner. It follows script references from those
seed surfaces and separates results into:

- required scripts and support files
- validation and compatibility candidates
- unclassified candidates

The audit does not copy files. It is an evidence tool for the bootstrap
workflow. A clean result means the portable set is understood; it does not mean
the public repository shell, install script, license, or smoke test has already
been created.


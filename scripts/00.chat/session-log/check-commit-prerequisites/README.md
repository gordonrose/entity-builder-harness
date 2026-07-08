<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.check-commit-prerequisites.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain how commit prerequisite checks verify workflow and gate references
    before chat commits.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.session-log.check-commit-prerequisites
    path: scripts/00.chat/session-log/check-commit-prerequisites/script.sh
  - id: chat.script.session-log.check-commit-prerequisites.smoke-test
    path: scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
-->
# Check Commit Prerequisites

`script.sh` verifies that the current chat session points at real governance
artifacts before a task commit proceeds.

It is a structural readiness check. It does not decide whether the code change
is good. It checks that the session log, declared workflow, canonical checklist,
and referenced gate scripts are present so the commit boundary is governed by
real files rather than stale documentation.

## Mental Model

A chat session is only committable if its process map still resolves.

The session log names a workflow. The workflow and before-commit checklist name
scripts that should exist. If any of those links are broken, the agent might be
following a workflow that cannot actually run.

This gate catches that problem before the task commit.

## Checks

The script verifies:

- current branch is a `chat/*` branch
- matching session log exists
- session metadata includes a `workflow`
- declared workflow file exists
- canonical `.agentic/00.chat/checklists/before-commit.md` exists
- executable script references in the workflow and checklist point to real
  `.sh` files
- the optional repository extension hook at `scripts/repo/commit-gates/script.sh`
  may be absent in a base install

Directory prose such as `scripts/00.chat/` is ignored; only script-looking
references ending in `.sh` are treated as gate references.

## What This Does Not Do

- It does not run every referenced gate.
- It does not inspect code quality.
- It does not stage, commit, merge, or push.
- It does not validate ADR disposition content.
- It does not replace `prepare-chat-session-before-commit`; it is one gate that
  the readiness coordinator runs.

## Validation

`smoke-test.sh` builds a throwaway chat repo and verifies that:

- a valid workflow/checklist setup passes
- prose directory references are not mistaken for missing scripts
- the optional repository extension hook may be referenced without being present

Run the canonical smoke test with:

```bash
bash scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh
```

## Compatibility

The old shared path remains available:

```bash
scripts/00.chat/session-log/check-commit-prerequisites/script.sh
```

That file is now a compatibility wrapper around the canonical implementation.

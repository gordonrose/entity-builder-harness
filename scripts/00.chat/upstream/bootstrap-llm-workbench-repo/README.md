<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the dry-run planner for bootstrapping the public llm-workbench repo.
domain: upstream
portability: llm-workbench-required
used_by:
  - scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
-->

# Bootstrap llm-workbench Repo

This capability plans how the portable chat workbench would be materialized
into a target Git repo.

The first implementation is dry-run only. It does not copy files, merge
`package.json`, or write into the target repo. It produces an action plan that
can be reviewed before any apply mode exists.

## Files

- `script.sh` inspects a target repo and prints the bootstrap plan.
- `smoke-test.sh` exercises empty, existing-package, preserved-shared-file, and
  conflicting-package-script scenarios in throwaway repos.

## Behavior

The planner classifies target paths as:

- `CREATE` when the workbench would add a missing file
- `SAME` when the target already matches the source or template
- `CONFLICT` when a target file exists with different content
- `PACKAGE_ADD_SCRIPT` when an existing `package.json` is missing a workbench
  `chat:*` script
- `PACKAGE_SAME_SCRIPT` when an existing `package.json` already has the
  expected script
- `PACKAGE_CONFLICT_SCRIPT` when an existing `chat:*` script points somewhere
  else
- `PACKAGE_PRESERVE_SCRIPT` when an existing unrelated package script should be
  left alone
- `PRESERVE` when an unrelated target-owned file under `.agentic/shared` or
  `scripts/shared` should be left alone

Conflicts make the dry-run exit non-zero. That lets future workflows use the
planner as a gate before an apply step.

## Usage

```bash
bash scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh \
  --target /path/to/llm-workbench \
  --dry-run
```

## Boundaries

The planner requires the target to already be a Git repo. It does not create
the upstream repo, clone it, commit, or push.

It deliberately treats `package.json` as structured data and merges only the
workbench-owned `chat:*` command surface. It preserves unrelated package fields
and scripts.

<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.upstream.bootstrap-llm-workbench-repo.readme
  version: 1
  status: active
  layer: 00.chat
  domain: upstream
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the dry-run planner for bootstrapping the public llm-workbench repo.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.upstream.bootstrap-llm-workbench-repo
    path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
-->
# Bootstrap llm-workbench Repo

This capability plans how the portable chat workbench would be materialized
into a target Git repo.

It always produces a plan first. In `--dry-run` mode it writes nothing. In
`--apply` mode it refuses to write when the plan contains conflicts, then copies
missing files and merges workbench-owned `chat:*` scripts into `package.json`.

## Files

- `script.sh` inspects a target repo, prints the bootstrap plan, and can apply
  a clean plan.
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

Apply mode uses the same conflict detection. It only writes after the plan is
clean.

## Usage

```bash
bash scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh \
  --target /path/to/llm-workbench \
  --dry-run
```

After reviewing a clean plan:

```bash
bash scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh \
  --target /path/to/llm-workbench \
  --apply
```

## Boundaries

The planner requires the target to already be a Git repo. It does not create
the upstream repo, clone it, commit, or push.

It deliberately treats `package.json` as structured data and merges only the
workbench-owned `chat:*` command surface. It preserves unrelated package fields
and scripts.

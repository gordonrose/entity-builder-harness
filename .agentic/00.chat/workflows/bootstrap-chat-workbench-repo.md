# Bootstrap Chat Workbench Repo Workflow

## Use When

Use this when seeding an upstream chat workbench repo such as `llm-workbench`
from a source repo that already contains the chat harness.

## Purpose

Create the first portable chat harness baseline in an upstream workbench repo
so future upstream reusable lesson chats can run there normally.

This workflow uses `.agentic/shared/standards/upstream-repo-bootstrap.md`.

## Required Gates

Before writing to the upstream repo, inspect:

```bash
git -C <upstream-repo> status --short
git -C <upstream-repo> remote -v
find <upstream-repo> -maxdepth 2 -type f
```

If the upstream repo is not empty, list target paths that would be added or
overwritten and ask for explicit approval before writing.

## Portable Chat File Set

Initial candidate paths:

- `AGENTS.md` as an upstream template, not a direct source-repo copy
- `.agentic/00.chat/`
- `.agentic/shared/checklists/`
- `.agentic/shared/gates/`
- `.agentic/shared/standards/`
- `.agentic/shared/workflows/` entries required by chat startup, commit, and
  promotion compatibility
- `scripts/chat/`
- `scripts/shared/chat/`
- `scripts/shared/git/`
- `scripts/shared/harness/` gates required by chat startup, commit, classifier,
  governed script, and deterministic process checks
- `docs/harness/architecture/adrs/` entries that explain the portable chat
  architecture

## Required Exclusions

In addition to the shared standard exclusions, do not copy:

- `.agentic/product/`
- `.agentic/education/`
- `.agentic/aws/`
- product `src/`, `tests/`, or app docs
- source repo `commitLogs/`
- source repo-specific open tabs, transcripts, or local worktree paths

## Bootstrap Prompt Shape

When preparing the first upstream bootstrap chat, use:

```txt
Task: Bootstrap llm-workbench with the portable chat harness

Source repo: <absolute-path>
Upstream repo: <absolute-path>
Workflow: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
Standard: .agentic/shared/standards/upstream-repo-bootstrap.md

Goal:
Create the first portable chat harness baseline in llm-workbench.

Portable file set:
<paths>

Required exclusions:
<paths and categories>

Boundaries:
Inspect both repos before writing.
Do not copy source-repo-specific product, deployment, customer, or session
history into llm-workbench.
Ask before writing upstream files.
Ask before committing.
Do not push unless explicitly approved separately.
```

## Stop Conditions

Stop if:

- the upstream repo is not the intended repo
- the upstream repo has existing files whose ownership is unclear
- the portable file set cannot be separated from source-specific material
- a required compatibility script or workflow is missing
- bootstrap would require push, destructive cleanup, or history rewrite


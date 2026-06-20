<!-- agentic-artifact:
owner: 00.chat
kind: workflow
purpose: Govern bootstrapping the portable chat workbench into an upstream repo.
domain: bootstrap
portability: llm-workbench-required
used_by:
  - .agentic/shared/standards/upstream-repo-bootstrap.md
  - scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
-->

# Bootstrap Chat Workbench Repo Workflow

## Use When

Use this when seeding an upstream chat workbench repo such as `llm-workbench`
from a source repo that already contains the chat harness.

## Purpose

Create the first minimal usable open-source chat workbench repo so engineers can
read, install, test, and run the portable chat harness from the upstream repo.

This workflow uses `.agentic/shared/standards/upstream-repo-bootstrap.md`.

## Required Gates

Before writing to the upstream repo, inspect:

```bash
git -C <upstream-repo> status --short
git -C <upstream-repo> remote -v
git -C <upstream-repo> rev-parse --verify HEAD || true
git -C <upstream-repo> branch --show-current || true
find <upstream-repo> -maxdepth 2 -type f
```

Then run the portable script file set audit from the source repo:

```bash
bash scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
```

If the upstream repo is not empty, list target paths that would be added or
overwritten and ask for explicit approval before writing.

If `HEAD` does not exist, treat the upstream repo as an empty bootstrap target.
The initial branch must be `main` unless the user explicitly approves a
different branch name.

## Portable Chat File Set

Initial candidate paths:

- `AGENTS.md` as an upstream template, not a direct source-repo copy
- `.agentic/00.chat/`
- `.agentic/shared/checklists/`
- `.agentic/shared/gates/`
- `.agentic/shared/standards/`
- `.agentic/shared/workflows/` entries required by chat startup, commit, and
  promotion compatibility
- `package.json` chat command scripts as an upstream template, not a direct
  source-repo copy
- `scripts/00.chat/` canonical chat capability scripts required by the audit
- `scripts/shared/harness/` gates required by chat startup, commit, classifier,
  governed script, and deterministic process checks
- `docs/harness/architecture/adrs/` entries that explain the portable chat
  architecture
- `docs/harness/architecture/chat-workbench-public-repo-readiness.md`

Do not copy the source repo `README.md` directly. It describes the source repo,
not the upstream workbench.

## Minimal Open-Source Product Shell

The first bootstrap must include enough product surface to test the repo as an
outside engineer would use it:

- `README.md` as a public workbench overview
- `LICENSE` when the user has chosen a license
- `.gitignore` for local/editor/runtime clutter
- `docs/concepts.md`
- `docs/install.md`
- `docs/workflows.md`
- `docs/adapting-to-your-repo.md`
- `examples/minimal-repo/`
- `scripts/install.sh`
- `scripts/uninstall.sh`
- `tests/smoke-test-install.sh`

The install smoke test must install the workbench into a throwaway Git repo,
verify the public command surface works, and verify the first chat startup
creates the target repo's own `commitLogs/`.

Use `scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh` to distinguish
required scripts from candidate unreferenced scripts before copying scripts
into the upstream repo.

Use `docs/harness/architecture/chat-workbench-public-repo-readiness.md` to
separate files that can be copied as-is from files that must be transformed for
the public repo.

## Required Exclusions

In addition to the shared standard exclusions, do not copy:

- `.agentic/product/`
- `.agentic/education/`
- `.agentic/aws/`
- product `src/`, `tests/`, or app docs
- source repo `commitLogs/`
- source repo-specific open tabs, transcripts, or local worktree paths

## Initial Commit For Empty Repos

For an empty upstream repo:

1. Copy the approved portable file set and starter public files.
2. Add the minimal open-source product shell.
3. Verify `npm run chat:list` works.
4. Verify `tests/smoke-test-install.sh` passes against a throwaway repo.
5. Create the first upstream commit only after explicit commit approval.
6. After the first commit exists, verify a normal chat can be started in the
   upstream repo.

Do not create or copy `commitLogs/` during bootstrap. The first upstream chat
startup creates the upstream repo's first session log.

## Bootstrap Prompt Shape

When preparing the first upstream bootstrap chat, use:

```txt
Task: Bootstrap llm-workbench with the portable chat harness

Source repo: <absolute-path>
Upstream repo: <absolute-path>
Workflow: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
Standard: .agentic/shared/standards/upstream-repo-bootstrap.md

Goal:
Create the first minimal usable open-source chat workbench in llm-workbench.

Portable file set:
<paths>

Minimal product shell:
<README, docs, examples, install scripts, smoke test>

Required exclusions:
<paths and categories>

Initial Git state:
<empty repo or existing HEAD>

Starter public files:
<README, LICENSE decision, gitignore>

Boundaries:
Inspect both repos before writing.
Do not copy source-repo-specific product, deployment, customer, or session
history into llm-workbench.
Ask before writing upstream files.
Ask before committing.
Do not push unless explicitly approved separately.
Do not copy source commitLogs; first upstream chat startup creates commitLogs.
```

## Stop Conditions

Stop if:

- the upstream repo is not the intended repo
- the upstream repo has existing files whose ownership is unclear
- the upstream repo has no `HEAD` and the initial branch is not agreed
- the portable file set cannot be separated from source-specific material
- a required compatibility script or workflow is missing
- starter public files are missing or would misrepresent the upstream repo
- the install smoke test is missing or cannot prove a throwaway repo can use
  the workbench
- bootstrap would require push, destructive cleanup, or history rewrite

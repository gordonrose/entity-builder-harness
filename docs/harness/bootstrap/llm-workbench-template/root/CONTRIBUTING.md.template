# Contributing

Thanks for taking an interest in `llm-workbench`.

This repo is a portable chat harness for governed agentic development. The
main goal is to make chat startup, worktree use, commit gates, refreshes, and
reusable lesson promotion repeatable enough that another engineer can install
the harness into their own Git repo and understand what will happen.

## Good First Contributions

Good early contributions are usually small and inspectable:

- clearer onboarding docs
- safer install or uninstall behavior
- better smoke tests
- clearer names for scripts, workflows, or concepts
- fixes where a documented command no longer matches the script it describes

Avoid broad rewrites unless there is an issue or discussion that explains the
new shape. The harness is intentionally explicit, so small changes are easier
to review and safer for downstream repos.

## Before Changing Harness Behavior

If a change affects chat startup, branch/worktree handling, commit gates,
refresh from `main`, local merge readiness, install/uninstall, or reusable
lesson promotion, update the relevant docs and tests in the same change.

At minimum, check:

```bash
npm run chat:list
npm run test:install
```

If you add or move a script, keep its nearby README current. The README should
teach a new reader what the script does, when it runs, what it writes, and what
approval boundaries it respects.

## Pull Requests

Please include:

- what changed
- why it changed
- how you tested it
- any behavior that downstream repos should notice

Do not include private repo paths, local transcripts, API keys, customer data,
or project-specific secrets in issues or pull requests.

## Style

Prefer plain Bash and Markdown unless a stronger reason exists. Keep public
docs educational: assume the reader is new to this harness and explain the
purpose of each moving part before asking them to rely on it.

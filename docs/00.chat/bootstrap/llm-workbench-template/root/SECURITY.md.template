# Security Policy

`llm-workbench` is local developer tooling. It works with Git repositories,
shell scripts, worktrees, and generated session logs, so security reports are
especially important when they involve command execution, file writes, path
handling, or accidental disclosure of private repo data.

## Reporting A Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report security concerns privately to the maintainer instead. Include:

- the affected command, script, workflow, or install path
- the operating system and shell, if relevant
- steps to reproduce
- whether the issue can write files, execute commands, expose private data, or
  bypass an approval boundary

If GitHub private vulnerability reporting is enabled for this repo, use that.
Otherwise, contact the maintainer directly through the contact route listed on
the GitHub profile or repository.

## Scope

Examples of in-scope issues:

- command injection or unsafe shell quoting
- install/uninstall writing outside the requested target repo
- scripts deleting, rewriting, pushing, or overwriting work without approval
- private paths, transcripts, or secrets being copied into a public install
- incorrect conflict detection during bootstrap or install

Examples that are usually out of scope:

- a target repo's own product code
- local machine compromise unrelated to this harness
- unsupported modifications made after installation

## Safety Principle

The harness should prefer refusal over surprise. If a script cannot prove that
an operation is scoped, reversible, or explicitly approved, it should stop and
explain the boundary rather than guessing.

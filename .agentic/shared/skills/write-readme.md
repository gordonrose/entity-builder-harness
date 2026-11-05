<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.skill.write-readme
version: 1
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 06.shared
domain: documentation
disciplines: [agentic, architecture]
kind: skill
purpose: Guide bounded source-backed README authoring using the canonical readable-README standard.
portability: {class: source-only, targets: []}
used_by:
- id: shared.standard.require-change-completion
  path: .agentic/shared/standards/require-change-completion.md
- id: harness.readme
  path: .agentic/01.harness/README.md
-->
# Write a README

## Trigger and required context

Use when creating or revising a repository README, including an added walkthrough
of a module file. This is authoring guidance, not authority to change runtime
code, migrate rules, install tools or expand a narrow edit into a documentation
sweep. Answer-only questions do not themselves request file changes.

Read the [readable-README standard](../standards/require-readable-readmes.md)
completely before authoring. For a source-module guide or export walkthrough,
also read the [module template](../templates/module-readme.md) completely and
adapt it to the agreed scope. Existing repo governance and the recorded chat
worktree still apply.

## Procedure

1. Establish the audience, folder and requested files/sections. Read the existing
   README and relevant source. Inventory direct files and public exports in the
   existing task/session record. Separate locally implemented exports from
   re-exports and follow their actual definitions. Preserve unrelated prose.
2. Inspect actual callers and relevant tests. Identify inputs, checking/rule
   owners, function locations, returned results and later consumers. Establish
   current behaviour rather than inferring it from names or planned features.
3. Read the relevant existing governance and executable checks before describing
   requirements or enforcement. Identify referenced backlog tasks and pending
   ownership migrations. Do not create new domain requirements in the README.
4. Draft the explanation from a concrete problem through the source-backed
   sequence. Apply the standard's clarity and coverage requirements. Adapt the
   template without copying authoring placeholders into a finished guide.
   Link already explained exports instead of reproducing their walkthroughs.
5. Review the complete task edit as a reader and against source. Close misleading
   wording, skipped steps, unsupported claims and missing in-scope names before
   final verification. A narrowly scoped edit can leave other files' detailed
   export sections explicitly deferred.
6. Perform the standard's proportionate checks. Prefer existing tooling and
   small in-memory/disposable example checks to new general-purpose validators.
   Record actual results, untested claims and scope limits in the existing
   session/task record. Preserve failures honestly; do not loosen assertions
   simply to obtain a passing example.

## Output

Return links to the changed README and any requested supporting artifacts,
what coverage was added, actual verification and remaining limits. Do not imply
that a prose change implements pending runtime or harness work.

## Discovery adapter

The native Codex entry point is
[.agents/skills/write-readme/SKILL.md](../../../.agents/skills/write-readme/SKILL.md).
It contains discovery metadata and a pointer, not a second copy of this
procedure. Shared completion guidance and the harness index also link here, so
the instructions can be followed by agents that do not use Codex discovery.

Codex's repository skill scan is documented in
[official skill documentation](https://learn.chatgpt.com/docs/build-skills),
reviewed on 2026-11-01. The adapter is configured for that scan; checking its
format and links does not establish that a particular running client loaded it.
If discovery is unavailable, read this canonical procedure explicitly and report
the limitation rather than claim a successful automatic-invocation test.

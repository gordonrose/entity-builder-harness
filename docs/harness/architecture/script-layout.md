<!-- agentic-artifact:
owner: harness
kind: doc
purpose: Explain the current script layout after the chat harness script migration.
domain: scripts
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/README.md
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# Script Layout

This document describes the current script layout. For the migration history,
see ADR 0017.

## Current Shape

Chat lifecycle scripts live under:

```txt
scripts/00.chat/<domain>/<capability>/
```

Shared harness governance scripts live under:

```txt
scripts/01.harness/
```

That split is intentional:

- `scripts/00.chat/` owns chat startup, commands, reporting, session logs,
  recovery, worktrees, main refresh, local merge checks, and upstream bootstrap
  support.
- `scripts/01.harness/` owns cross-layer harness checks such as metadata,
  deterministic process drift, governed command drift, and the governed script
  runner.

Do not add new chat lifecycle scripts under `scripts/shared/chat/` or
`scripts/shared/git/`. Those were compatibility locations from the earlier
layout and are now retired.

## Capability Folders

Each capability folder should contain the files that help a reader understand,
run, and test that capability:

- `script.sh`, `script.js`, or `lib.sh` for the implementation
- `smoke-test.sh` or another focused validation file when behavior needs proof
- `README.md` explaining the purpose, inputs, effects, and boundaries

Domain folders also have a `README.md` that explains how the capabilities in
that domain fit together.

## Public Surface

Humans should usually use `package.json` `chat:*` scripts. Those package
scripts delegate to canonical `scripts/00.chat/...` paths.

Harness workflows, checklists, standards, and gates should point directly at
canonical `scripts/00.chat/...` paths or at `scripts/01.harness/...` when
the behavior is genuinely shared governance.

## Historical Paths

Historical documents may mention retired paths, but should do so as migration
history:

- say what previously lived there
- name the current canonical path or say the behavior was retired
- avoid runnable examples that make the old path look current

Negative tests may create retired paths in throwaway repositories when they are
proving the governed runner rejects old compatibility surfaces.

